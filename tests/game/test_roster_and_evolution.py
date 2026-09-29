import os
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from poketokenbar.game.companion import CompanionEngine
from poketokenbar.game.companion.hatching import ALL_STRAIN_SPECIES_IDS
from poketokenbar.game.models import ItemKind, Rarity, MonState, PokemonBalance
from poketokenbar.game.storage import StorageManager
from poketokenbar.tui.app import PokeTokenBarTUI as AppState
from poketokenbar.tui.router import CommandRouter
from poketokenbar.tui_tabs.companion import render as render_companion_tab
from poketokenbar.tui_tabs.bank import render_bank_tab
import re

ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*[mK]')


class TestRosterAndEvolution(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._temp_dir = tempfile.TemporaryDirectory()
        cls._temp_state_file = Path(cls._temp_dir.name) / "test_state.json"
        cls._old_state_file = os.environ.get("PTB_STATE_FILE")
        os.environ["PTB_STATE_FILE"] = str(cls._temp_state_file)

    @classmethod
    def tearDownClass(cls):
        cls._temp_dir.cleanup()
        if cls._old_state_file is not None:
            os.environ["PTB_STATE_FILE"] = cls._old_state_file
        else:
            os.environ.pop("PTB_STATE_FILE", None)

    def setUp(self):
        StorageManager.save_state(StorageManager.default_state())
        self.engine = CompanionEngine()

    def test_get_roster_species_ids(self):
        """Verifies get_roster_species_ids includes active mon, active/inactive/graduated dex, and expeditions, excluding evolved."""
        # 1. Active mon: Charmander (4)
        mon = MonState(
            base_id=4,
            path_ids=[4, 5, 6],
            planned_path_ids=[4, 5, 6],
            stage_index=0,
            used_at_stage=0,
            rarity=Rarity.COMMON,
            total_forms=3
        )
        self.engine.set_active_mon(mon)

        # 2. Dex entries:
        # 1: Bulbasaur (inactive)
        # 2: Ivysaur (evolved) -> should NOT be in roster
        # 3: Venusaur (graduated)
        self.engine.state["dex"] = [
            {"species_id": 1, "status": "inactive"},
            {"species_id": 2, "status": "evolved"},
            {"species_id": 3, "status": "graduated"},
        ]

        # 3. Expedition: Pikachu (25)
        self.engine.state["expeditions"] = [
            {"sp_id": 25, "area": "forest"}
        ]

        roster_ids = self.engine.get_roster_species_ids()
        self.assertIn(4, roster_ids)
        self.assertIn(1, roster_ids)
        self.assertNotIn(2, roster_ids)  # Evolved form must NOT be in roster
        self.assertIn(3, roster_ids)
        self.assertIn(25, roster_ids)

    def test_hatch_pre_evolution_when_evolved_form_owned(self):
        """Eggs should hatch into pre-evolutions (Charmander) if not in roster, even if Charizard is in roster."""
        # Player has Charizard (6) in roster
        self.engine.state["dex"] = [
            {"species_id": 4, "status": "evolved"},
            {"species_id": 5, "status": "evolved"},
            {"species_id": 6, "status": "graduated"},
        ]
        self.engine.set_active_mon(None)
        roster_ids = self.engine.get_roster_species_ids()
        self.assertNotIn(4, roster_ids)
        self.assertIn(6, roster_ids)

        # Pick candidate with starter guarantee
        sp_id, rarity, chain_ids, is_leg = self.engine._pick_species(tier_guarantee="starter")
        # Ensure that Charmander (4) is selectable and not disqualified by owning Charizard (6)
        # Let's directly verify candidate filtering with custom list
        with patch("poketokenbar.game.companion.hatching.BASE_SPECIES_STARTERS", [(4, "Charmander", 45, False)]):
            sp_id, rarity, chain_ids, is_leg = self.engine._pick_species(tier_guarantee="starter")
            self.assertEqual(sp_id, 4)
            self.assertEqual(chain_ids, [4, 5, 6])

    def test_evolution_halted_when_evolved_form_in_roster(self):
        """Evolution must halt if the immediate next evolutionary stage exists in the active Roster."""
        # Active Charmander (4)
        mon = MonState(
            base_id=4,
            path_ids=[4, 5, 6],
            planned_path_ids=[4, 5, 6],
            stage_index=0,
            used_at_stage=0,
            rarity=Rarity.COMMON,
            total_forms=3
        )
        self.engine.set_active_mon(mon)

        # Charmeleon (5) already in active Roster
        self.engine.state["dex"] = [
            {"species_id": 5, "status": "inactive"},
        ]

        target_xp = PokemonBalance.phase_threshold(mon.rarity, mon.total_forms, 0, self.engine.current_difficulty)
        # Give enough XP to evolve
        mon.used_at_stage = target_xp + 500_000
        events = self.engine._check_growth(mon, is_active=True)

        # Charmander should NOT have evolved into Charmeleon because Charmeleon is in roster
        self.assertEqual(self.engine.active_mon.current_id, 4)
        self.assertEqual(self.engine.active_mon.stage_index, 0)
        self.assertEqual(self.engine.active_mon.used_at_stage, target_xp)  # Capped at threshold

    def test_evolution_allowed_when_only_final_form_in_roster(self):
        """Charmander can evolve to Charmeleon if Charmeleon is not in roster, even if Charizard is in roster."""
        # Active Charmander (4)
        mon = MonState(
            base_id=4,
            path_ids=[4, 5, 6],
            planned_path_ids=[4, 5, 6],
            stage_index=0,
            used_at_stage=0,
            rarity=Rarity.COMMON,
            total_forms=3
        )
        self.engine.set_active_mon(mon)

        # Charizard (6) in roster, but Charmeleon (5) is NOT in roster
        self.engine.state["dex"] = [
            {"species_id": 6, "status": "graduated"},
        ]

        target_xp = PokemonBalance.phase_threshold(mon.rarity, mon.total_forms, 0, self.engine.current_difficulty)
        mon.used_at_stage = target_xp + 100_000
        events = self.engine._check_growth(mon, is_active=True)

        # Charmander should evolve into Charmeleon (5)
        self.assertEqual(self.engine.active_mon.current_id, 5)
        self.assertEqual(self.engine.active_mon.stage_index, 1)

        # Now, attempt to evolve Charmeleon (5) to Charizard (6)
        mon = self.engine.active_mon
        stage1_target_xp = PokemonBalance.phase_threshold(mon.rarity, mon.total_forms, 1, self.engine.current_difficulty)
        mon.used_at_stage = stage1_target_xp + 100_000
        self.engine.set_active_mon(mon)
        events2 = self.engine._check_growth(mon, is_active=True)

        # Charmeleon (5) should NOT evolve to Charizard (6) because Charizard is in roster!
        self.assertEqual(self.engine.active_mon.current_id, 5)
        self.assertEqual(self.engine.active_mon.stage_index, 1)
        self.assertEqual(self.engine.active_mon.used_at_stage, stage1_target_xp)

    def test_stone_evolution_halted_when_target_in_roster(self):
        """Evolution stone use must fail if the target evolved form is in the active Roster."""
        # Active Pikachu (25)
        mon = MonState(
            base_id=25,
            path_ids=[25, 26],
            planned_path_ids=[25, 26],
            stage_index=0,
            used_at_stage=0,
            rarity=Rarity.UNCOMMON,
            total_forms=2
        )
        self.engine.set_active_mon(mon)
        self.engine.state["inventory"] = {"thunder_stone": 1}

        # Raichu (26) in Roster
        self.engine.state["dex"] = [
            {"species_id": 26, "status": "inactive"}
        ]

        ok, msg = self.engine.use_item("thunder_stone")
        self.assertFalse(ok)
        self.assertIn("active Roster", msg)
        self.assertEqual(self.engine.active_mon.current_id, 25)

        # Now mark Raichu as evolved (or remove from roster)
        self.engine.state["dex"][0]["status"] = "evolved"
        ok2, msg2 = self.engine.use_item("thunder_stone")
        self.assertTrue(ok2)
        self.assertEqual(self.engine.active_mon.current_id, 26)

    def test_full_roster_safeguards_and_cash_conversion(self):
        """When player has a full Living Roster, buy_egg is blocked and obtained eggs convert to tokens."""
        self.assertFalse(self.engine.is_roster_full())

        # Populate roster with all strain species IDs
        full_dex = [{"species_id": sid, "status": "graduated"} for sid in ALL_STRAIN_SPECIES_IDS]
        self.engine.state["dex"] = full_dex
        self.assertTrue(self.engine.is_roster_full())

        # Attempt to buy egg
        self.engine.state["used_since_install"] = 500_000_000
        self.engine.state["spent_tokens"] = 0
        ok, msg = self.engine.buy_egg(Rarity.RARE)
        self.assertFalse(ok)
        self.assertIn("Your Roster is completely full", msg)

        # Obtain egg via obtain_egg -> should convert to cash
        init_spent = self.engine.state.get("spent_tokens", 0)
        ok_obs, msg_obs, cash = self.engine.obtain_egg("legendary")
        self.assertTrue(ok_obs)
        self.assertEqual(cash, 100_000_000)
        self.assertIn("converted into 100.0M tokens", msg_obs)
        # spent_tokens should decrease by 100M (giving 100M tokens)
        self.assertEqual(self.engine.state.get("spent_tokens", 0), init_spent - 100_000_000)

        # Uncommon egg conversion
        ok_u, msg_u, cash_u = self.engine.obtain_egg("uncommon")
        self.assertEqual(cash_u, 45_000_000)
        self.assertIn("converted into 45.0M tokens", msg_u)

    def test_bank_cd_commands_open_and_claim(self):
        """Verify 'open <amt> <days>' and 'claim [id|all]' work in Bank CD subtab."""
        app = AppState()
        app.engine = self.engine
        app.current_tab = 10
        app.bank_subtab = "cd"
        self.engine.state["used_since_install"] = 500_000_000
        self.engine.state["spent_tokens"] = 0

        # 1. Bare open usage
        CommandRouter.dispatch(app, "open")
        self.assertIn("Usage: open <amt> <3|7|14>", app.message)

        # 2. open 10m 7
        CommandRouter.dispatch(app, "open 10m 7")
        self.assertIn("Opened 7-Day CD", app.message)
        self.assertEqual(len(self.engine.state.get("term_deposits", [])), 1)

        # 3. Backward compatible: cd open 5m 3
        CommandRouter.dispatch(app, "cd open 5m 3")
        self.assertIn("Opened 3-Day CD", app.message)
        self.assertEqual(len(self.engine.state.get("term_deposits", [])), 2)

        # 4. Mature the first CD and claim
        self.engine.state["term_deposits"][0]["matured"] = True
        CommandRouter.dispatch(app, "claim")
        self.assertIn("Claimed", app.message)

    def test_72_column_layout_compliance_with_in_roster_tag(self):
        """Verifies that [IN ROSTER] tag fits within 72 columns on companion tab."""
        mon = MonState(
            base_id=4,
            path_ids=[4, 5, 6],
            planned_path_ids=[4, 5, 6],
            stage_index=0,
            used_at_stage=1_000_000,
            rarity=Rarity.COMMON,
            total_forms=3
        )
        self.engine.set_active_mon(mon)
        # Put Charmeleon in roster
        self.engine.state["dex"] = [{"species_id": 5, "status": "inactive"}]

        app = AppState()
        app.engine = self.engine
        app.current_tab = 1

        buf = io.StringIO()
        summary = app.tracker.get_summary()
        with patch("sys.stdout", buf):
            render_companion_tab(app, summary)

        output = buf.getvalue()
        self.assertIn("[IN ROSTER]", output)
        for line in output.split("\n"):
            clean_line = ANSI_REGEX.sub('', line)
            self.assertLessEqual(len(clean_line), 72, f"Line exceeds 72 chars: '{clean_line}' (len={len(clean_line)})")

        # Test Bank CD tab layout compliance as well
        app.current_tab = 10
        app.bank_subtab = "cd"
        buf2 = io.StringIO()
        with patch("sys.stdout", buf2):
            render_bank_tab(app)

        output2 = buf2.getvalue()
        for line in output2.split("\n"):
            clean_line = ANSI_REGEX.sub('', line)
            self.assertLessEqual(len(clean_line), 72, f"Bank CD Line exceeds 72 chars: '{clean_line}' (len={len(clean_line)})")

    def test_black_market_egg_deal_respects_reserves_and_full_roster(self):
        """Black Market egg deals must queue in reserves if companion is active and block when full."""
        # 1. Active companion present -> egg goes to pending_eggs
        mon = MonState(base_id=25, path_ids=[25], planned_path_ids=[25], stage_index=0, used_at_stage=0, rarity=Rarity.UNCOMMON, total_forms=1)
        self.engine.set_active_mon(mon)
        self.engine.state["used_since_install"] = 100_000_000
        self.engine.state["spent_tokens"] = 0

        import datetime
        today_str = datetime.date.today().isoformat()
        egg_deal = {"id": 1, "name": "Rare Egg", "type": "egg", "egg_tier": "rare", "price": 10_000_000, "stock": 1}
        dummy_deals = [{"id": i, "name": f"Item {i}", "type": "item", "item_key": "berry_oran", "price": 1_000, "stock": 1} for i in range(2, 8)]
        bm = {
            "is_open": True,
            "natural_open": True,
            "duration_days": 1,
            "deals_date": today_str,
            "deals": [egg_deal] + dummy_deals
        }
        self.engine.state["black_market"] = bm

        ok, msg = self.engine.buy_black_market_deal("1", 1, confirm=False)
        self.assertTrue(ok)
        self.assertIn("Added to your Egg Reserves", msg)
        self.assertEqual(self.engine.state.get("pending_eggs"), ["rare"])

        # 2. When roster is completely full, purchase is blocked
        full_dex = [{"species_id": sp, "status": "inactive"} for sp in ALL_STRAIN_SPECIES_IDS]
        self.engine.state["dex"] = full_dex
        self.assertTrue(self.engine.is_roster_full())
        self.engine.state["black_market"]["deals"][0]["stock"] = 1

        ok2, msg2 = self.engine.buy_black_market_deal("1", 1, confirm=False)
        self.assertFalse(ok2)
        self.assertIn("Roster is completely full", msg2)

    def test_rocket_authority_respects_roster_and_expeditions(self):
        """Rocket authority candidate selection must respect active mon, dex, and expeditions."""
        self.engine.state["rocket_rank"] = "Commander"
        mon = MonState(base_id=1, path_ids=[1], planned_path_ids=[1], stage_index=0, used_at_stage=0, rarity=Rarity.COMMON, total_forms=1)
        self.engine.set_active_mon(mon)
        self.engine.state["dex"] = [{"species_id": 4, "status": "inactive"}]
        self.engine.state["expeditions"] = [{"sp_id": 7, "target": 1_000_000}]

        roster_ids = self.engine.get_roster_species_ids()
        self.assertIn(1, roster_ids)
        self.assertIn(4, roster_ids)
        self.assertIn(7, roster_ids)

        # Authority delivery duplicate rejection
        self.engine.state["pending_authority_delivery"] = 4  # Charmander already in dex
        ok, msg = self.engine.handle_authority_delivery("keep")
        self.assertFalse(ok)
        self.assertIn("already exists in your active Roster", msg)

    def test_red_battle_rewards_respect_roster_duplicates(self):
        """Mt. Silver battle must not duplicate Mew or Arceus if already in active roster."""
        from poketokenbar.game.combat.red_battle import RedBattleHandler
        red = RedBattleHandler(self.engine)

        # 1. Arceus duplicate check
        self.engine.state["dex"] = [{"species_id": 493, "status": "graduated"}]
        st = {
            "player_team": [25, 196, 143, 3, 6, 9],
            "player_active_index": 0,
            "player_hps": [1000] * 6,
            "player_max_hps": [1000] * 6,
            "red_team": [{"id": 493, "name": "Arceus", "hp": 5000000, "max_hp": 5000000, "type": "normal", "moves": ["Judgment"]}],
            "red_active_index": 0,
            "red_hps": [1],
            "red_max_hps": [5000000],
            "status": "battle",
            "arceus_phase": True,
            "turn_log": []
        }
        red._save_state(st)
        ok, log = red.execute_turn(0)
        self.assertIn("Arceus already in Roster", log)

        # 2. Mew duplicate check
        self.engine.state["red_wins"] = 0
        self.engine.state["dex"] = [{"species_id": 151, "status": "inactive"}]
        st2 = {
            "player_team": [1, 2, 3],
            "player_active_index": 0,
            "player_hps": [1000] * 3,
            "player_max_hps": [1000] * 3,
            "red_team": [{"id": 25, "name": "Pikachu", "hp": 1000, "max_hp": 1000, "type": "electric", "moves": ["Thunder"]}],
            "red_active_index": 0,
            "red_hps": [1],
            "red_max_hps": [1000],
            "status": "battle",
            "arceus_phase": False,
            "turn_log": []
        }
        red._save_state(st2)
        ok2, log2 = red.execute_turn(0)
        self.assertIn("Mew already registered in Pokédex", log2)

    def test_switch_egg_integration(self):
        """Switch egg must load from nursery reserves without modal prompts."""
        mon = MonState(base_id=25, path_ids=[25], planned_path_ids=[25], stage_index=0, used_at_stage=0, rarity=Rarity.UNCOMMON, total_forms=1)
        self.engine.set_active_mon(mon)
        self.engine.state["pending_eggs"] = ["legendary"]
        self.engine.state["egg_tier"] = None

        # When user switches to egg, it loads from reserves
        ok, msg = self.engine.select_active_from_dex("egg")
        self.assertTrue(ok)
        self.assertIn("Switched active companion to Incubating Egg", msg)
        self.assertEqual(self.engine.state["egg_tier"], "legendary")
        self.assertEqual(self.engine.state["pending_eggs"], [])

    def test_rocket_boss_squad_selection_and_validation(self):
        """Verifies Strike Squad selection requiring 3 distinct Pokémon and rejecting expeditions."""
        from poketokenbar.game.combat.rocket_battle import RocketBattleHandler

        # Setup roster companions: 1 (Bulbasaur), 4 (Charmander), 7 (Squirtle), 25 (Pikachu), 143 (Snorlax)
        self.engine.state["dex"] = [
            {"species_id": 1, "status": "inactive"},
            {"species_id": 4, "status": "inactive"},
            {"species_id": 7, "status": "inactive"},
            {"species_id": 25, "status": "inactive"},
            {"species_id": 143, "status": "inactive"},
        ]
        # Put Squirtle (#7) on an expedition
        self.engine.state["expeditions"] = [{"sp_id": 7, "area": "Viridian Forest", "target": 5_000_000, "progress": 0}]
        self.engine.state["rocket_alliance_accepted"] = True
        self.engine.state["rocket_ops"]["op_3"]["status"] = "active"

        handler = RocketBattleHandler(self.engine)

        # 1. Parse by species IDs
        ok, squad = handler.parse_squad_selection(["1", "4", "25"])
        self.assertTrue(ok)
        self.assertEqual(squad, [1, 4, 25])

        # 2. Parse by '#' prefixed IDs
        ok, squad = handler.parse_squad_selection(["#1", "#4", "#25"])
        self.assertTrue(ok)
        self.assertEqual(squad, [1, 4, 25])

        # 3. Parse by roster 1-based indices
        ok, squad = handler.parse_squad_selection(["1", "2", "4"])
        self.assertTrue(ok)
        self.assertEqual(squad, [1, 4, 25])

        # 4. Parse by species names
        ok, squad = handler.parse_squad_selection(["bulbasaur", "charmander", "pikachu"])
        self.assertTrue(ok)
        self.assertEqual(squad, [1, 4, 25])

        # 5. Reject fewer than 3
        ok, err = handler.parse_squad_selection(["1", "4"])
        self.assertFalse(ok)
        self.assertIn("exactly 3", err)

        # 6. Reject more than 3
        ok, err = handler.parse_squad_selection(["1", "4", "25", "143"])
        self.assertFalse(ok)
        self.assertIn("exactly 3", err)

        # 7. Reject duplicate choices
        ok, err = handler.parse_squad_selection(["1", "1", "4"])
        self.assertFalse(ok)
        self.assertIn("duplicate", err.lower())

        # 8. Reject companion currently on expedition
        ok, err = handler.parse_squad_selection(["1", "4", "7"])
        self.assertFalse(ok)
        self.assertIn("expedition", err.lower())

        # 9. Reject non-existent companion
        ok, err = handler.parse_squad_selection(["999", "1", "4"])
        self.assertFalse(ok)
        self.assertIn("not found", err.lower())

        # 10. Test start_boss_battle with custom squad
        ok, msg = handler.start_boss_battle("3", custom_squad=[1, 4, 25])
        self.assertTrue(ok)
        st = handler._get_state()
        self.assertEqual(len(st["player_team"]), 3)
        self.assertEqual(st["player_team"], [1, 4, 25])

        # 11. start_boss_battle rejects custom squad with member on expedition
        ok_fail, msg_fail = handler.start_boss_battle("3", custom_squad=[1, 4, 7])
        self.assertFalse(ok_fail)
        self.assertIn("expedition", msg_fail.lower())

        # 12. auto_assemble_squad produces exactly 3 members and excludes expedition
        squad_auto = handler.auto_assemble_squad(size=3)
        self.assertEqual(len(squad_auto), 3)
        self.assertNotIn(7, squad_auto)

    def test_rocket_boss_tactical_log_one_line_and_72_column_layout(self):
        """Verifies Tactical Battle Log is rendered strictly on a single line with <= 72 column compliance."""
        from poketokenbar.tui_tabs.rocket import render_rocket_tab, handle_rocket_command
        from poketokenbar.game.combat.rocket_battle import RocketBattleHandler

        self.engine.state["rocket_alliance_accepted"] = True
        self.engine.state["rocket_ops"]["op_3"]["status"] = "active"
        self.engine.state["dex"] = [
            {"species_id": 1, "status": "inactive"},
            {"species_id": 4, "status": "inactive"},
            {"species_id": 25, "status": "inactive"},
        ]

        handler = RocketBattleHandler(self.engine)
        ok, _ = handler.start_boss_battle("3", custom_squad=[1, 4, 25])
        self.assertTrue(ok)

        app = AppState()
        app.engine = self.engine
        app.rocket_subview = "ops"

        # Capture rendered combat output
        trap = io.StringIO()
        with patch("sys.stdout", trap):
            render_rocket_tab(app)
        output = trap.getvalue()

        # Check single-line Tactical Battle Log
        lines = output.split("\n")
        battle_log_lines = [l for l in lines if "Tactical Battle Log:" in ANSI_REGEX.sub("", l)]
        self.assertEqual(len(battle_log_lines), 1, "Tactical Battle Log must appear on exactly one line!")

        # Verify no multi-line wrapping below Tactical Battle Log
        for l in lines:
            clean = ANSI_REGEX.sub("", l)
            self.assertLessEqual(len(clean), 72, f"Line exceeds 72 cols: '{clean}' (len={len(clean)})")

        # Verify Strike Squad display
        squad_lines = [l for l in lines if "Strike Squad (1-3):" in ANSI_REGEX.sub("", l)]
        self.assertEqual(len(squad_lines), 1, "Strike Squad must appear on a single line!")

        # Test command handling in ops view
        handler.run_away()
        # When typing 'fight' with no args, prompt user to select 3 Pokémon
        handle_rocket_command(app, "fight")
        self.assertIn("Usage: fight <id1> <id2> <id3>", app.message)

        # When typing 'fight 1 4 25', battle begins
        handle_rocket_command(app, "fight 1 4 25")
        self.assertIn("Engage", app.message)

    def test_expeditions_and_rocket_battle_mutual_exclusion(self):
        """Verifies mutual exclusion: Pokémon in Rocket battle cannot do expeditions, and vice-versa."""
        from poketokenbar.tui_tabs.expeditions import render_expedition_picker
        from poketokenbar.tui_tabs.roster import render_roster_tab
        from poketokenbar.game.combat.rocket_battle import RocketBattleHandler

        self.engine.state["dex"] = [
            {"species_id": 1, "status": "inactive"},
            {"species_id": 4, "status": "inactive"},
            {"species_id": 25, "status": "inactive"},
            {"species_id": 143, "status": "inactive"},
        ]
        self.engine.state["rocket_alliance_accepted"] = True
        self.engine.state["rocket_ops"]["op_3"]["status"] = "active"

        # 1. Start Rocket boss battle with [1, 4, 25]
        handler = RocketBattleHandler(self.engine)
        ok, _ = handler.start_boss_battle("3", custom_squad=[1, 4, 25])
        self.assertTrue(ok)

        # Engine helper must identify active Rocket battle combatants
        active_combatants = self.engine.get_rocket_battle_active_pokemon_ids()
        self.assertEqual(active_combatants, {1, 4, 25})

        # 2. Cannot dispatch a Pokémon in Rocket battle on an expedition (single dispatch)
        ok_single, msg_single = self.engine.dispatch_expedition("1", "viridian")
        self.assertFalse(ok_single)
        self.assertIn("tactical combat with Team Rocket", msg_single)

        # 3. Batch dispatch skips Pokémon in Rocket battle
        ok_batch, msg_batch = self.engine.dispatch_expedition("all", "viridian")
        self.assertTrue(ok_batch)
        self.assertIn("Dispatched 1 Pokémon (Snorlax)", msg_batch)
        self.assertIn("in Rocket battle", msg_batch)

        # 4. Cannot select companion in Rocket battle as active
        ok_sel, msg_sel = self.engine.select_active_from_dex("1")
        self.assertFalse(ok_sel)
        self.assertIn("tactical combat with Team Rocket", msg_sel)

        # 5. App multi-select toggle skips companions in Rocket battle
        app = AppState()
        app.engine = self.engine
        app._toggle_selection_indices([1, 4])
        self.assertIn("in Rocket battle", app.message)
        self.assertEqual(len(app.selected_expedition_targets), 0)

        # 6. Expedition Picker UI shows Rocket Btl status
        trap_picker = io.StringIO()
        with patch("sys.stdout", trap_picker):
            render_expedition_picker(app)
        picker_out = ANSI_REGEX.sub("", trap_picker.getvalue())
        self.assertIn("Rocket Btl", picker_out)

        # 7. Roster tab shows [ROCKET BTL] badge
        trap_roster = io.StringIO()
        with patch("sys.stdout", trap_roster):
            render_roster_tab(app)
        roster_out = ANSI_REGEX.sub("", trap_roster.getvalue())
        self.assertIn("[ROCKET BTL]", roster_out)

    def test_rocket_armory_chrono_and_mist_charge_targets(self):
        """Verifies Chrono Accelerator target is 25M and Morale Mist target is 15M."""
        self.engine.state["rocket_rank"] = "Operative"
        self.engine.state["rocket_story_unlocked"] = True
        self.engine.state["install_baseline_set"] = True
        self.engine.state["used_since_install"] = 0

        # Check targets
        info_chrono = self.engine.get_armory_charge_info("chrono")
        self.assertEqual(info_chrono["target"], 25_000_000)
        self.assertEqual(info_chrono["charges"], 3)

        info_mist = self.engine.get_armory_charge_info("mist")
        self.assertEqual(info_mist["target"], 15_000_000)
        self.assertEqual(info_mist["charges"], 3)

        # 1. Test Chrono Accelerator: 25M per charge
        ok_ch, msg_ch = self.engine.use_rocket_armory_item("chrono")
        self.assertTrue(ok_ch)
        self.assertEqual(self.engine.get_armory_charge_info("chrono")["charges"], 2)

        # 24,999,999 tokens: not recharged yet
        self.engine.process_usage(24_999_999)
        info_ch_prog = self.engine.get_armory_charge_info("chrono")
        self.assertEqual(info_ch_prog["charges"], 2)
        self.assertEqual(info_ch_prog["progress"], 24_999_999)

        # +1 token (25M total delta): recharges to 3
        self.engine.process_usage(25_000_000)
        info_ch_full = self.engine.get_armory_charge_info("chrono")
        self.assertEqual(info_ch_full["charges"], 3)
        self.assertEqual(info_ch_full["progress"], 0)

        # 2. Test Morale Mist: 15M per charge
        ok_m, msg_m = self.engine.use_rocket_armory_item("mist")
        self.assertTrue(ok_m)
        self.assertEqual(self.engine.get_armory_charge_info("mist")["charges"], 2)

        # 14,999,999 tokens delta (from 25M to 39,999,999): not recharged yet
        self.engine.process_usage(39_999_999)
        info_m_prog = self.engine.get_armory_charge_info("mist")
        self.assertEqual(info_m_prog["charges"], 2)
        self.assertEqual(info_m_prog["progress"], 14_999_999)

        # +1 token (from 25M to 40M, exactly 15M delta): recharges to 3
        self.engine.process_usage(40_000_000)
        info_m_full = self.engine.get_armory_charge_info("mist")
        self.assertEqual(info_m_full["charges"], 3)
        self.assertEqual(info_m_full["progress"], 0)

    def test_obtain_egg_when_active_mon_present(self):
        """Eggs obtained when active mon is present go to egg_tier in Roster (or pending_eggs if egg_tier is occupied)."""
        mon = MonState(
            base_id=4,
            path_ids=[4, 5, 6],
            planned_path_ids=[4, 5, 6],
            stage_index=0,
            used_at_stage=0,
            rarity=Rarity.COMMON,
            total_forms=3
        )
        self.engine.set_active_mon(mon)
        self.engine.state["egg_tier"] = None
        self.engine.state["pending_eggs"] = []

        # 1. Obtain egg when active mon is present and egg_tier is None -> Goes to egg_tier
        ok, msg, cash = self.engine.obtain_egg("normal")
        self.assertTrue(ok)
        self.assertIsNone(cash)
        self.assertIn("Added to Roster", msg)
        self.assertEqual(self.engine.state.get("egg_tier"), "normal")
        self.assertEqual(self.engine.state.get("pending_eggs"), [])

        # 2. Obtain second egg when egg_tier is already held -> Goes to Egg Reserves
        ok2, msg2, cash2 = self.engine.obtain_egg("rare")
        self.assertTrue(ok2)
        self.assertIsNone(cash2)
        self.assertIn("Added to your Egg Reserves", msg2)
        self.assertEqual(self.engine.state.get("egg_tier"), "normal")
        self.assertEqual(self.engine.state.get("pending_eggs"), ["rare"])

    def test_gacha_egg_reward_with_active_mon(self):
        """Gacha awards eggs into Roster or Egg Reserves with proper result messaging."""
        mon = MonState(
            base_id=25,
            path_ids=[25, 26],
            planned_path_ids=[25, 26],
            stage_index=0,
            used_at_stage=0,
            rarity=Rarity.UNCOMMON,
            total_forms=2
        )
        self.engine.set_active_mon(mon)
        self.engine.state["egg_tier"] = None
        self.engine.state["pending_eggs"] = []
        self.engine.state["used_since_install"] = 500_000_000
        self.engine.state["spent_tokens"] = 0

        # Mock gacha pull table to return standard egg
        with patch("poketokenbar.game.minigames.gacha.pull_gacha_multi", return_value=[("RARE", "🥚 1x Standard Egg Tier", "egg", "normal")]):
            ok, res_text = self.engine.play_gacha(10)
            self.assertTrue(ok)
            self.assertIn("(Added to Roster)", res_text)
            self.assertEqual(self.engine.state.get("egg_tier"), "normal")
            self.assertEqual(self.engine.state.get("pending_eggs"), [])

        # Pull another egg while egg_tier is held -> Queued in Egg Reserves
        with patch("poketokenbar.game.minigames.gacha.pull_gacha_multi", return_value=[("RARE", "🥚 1x Standard Egg Tier", "egg", "normal")]):
            ok2, res_text2 = self.engine.play_gacha(10)
            self.assertTrue(ok2)
            self.assertIn("(Queued in Egg Reserves)", res_text2)
            self.assertEqual(self.engine.state.get("egg_tier"), "normal")
            self.assertEqual(self.engine.state.get("pending_eggs"), ["normal"])

    def test_egg_reserves_roster_rendering_and_column_limit(self):
        """Roster tab displays held egg and egg reserves within strict 72-column limit."""
        from poketokenbar.tui_tabs.roster import render_roster_tab
        app = AppState()
        app.engine = self.engine
        app.engine.state["egg_tier"] = "normal"
        app.engine.state["pending_eggs"] = ["normal", "uncommon", "legendary"]

        trap = io.StringIO()
        with patch("sys.stdout", trap):
            render_roster_tab(app)

        output = trap.getvalue()
        clean_lines = [ANSI_REGEX.sub("", line) for line in output.splitlines()]

        self.assertTrue(any("Incubating Normal Egg" in l for l in clean_lines))
        self.assertTrue(any("Egg Reserves (3):" in l for l in clean_lines))

        # Strict 72-column check
        for line in clean_lines:
            self.assertLessEqual(len(line), 72, f"Line exceeds 72 columns: {line}")

    def test_engine_init_auto_promotes_pending_egg(self):
        """CompanionEngine.__init__ auto-promotes pending eggs into empty egg_tier on load."""
        # Set state file to have null egg_tier and 5 pending eggs
        st = StorageManager.default_state()
        st["egg_tier"] = None
        st["pending_eggs"] = ["normal", "normal", "uncommon", "normal", "normal"]
        StorageManager.save_state(st)

        loaded_engine = CompanionEngine()
        self.assertEqual(loaded_engine.state.get("egg_tier"), "normal")
        self.assertEqual(loaded_engine.state.get("pending_eggs"), ["normal", "uncommon", "normal", "normal"])

    def test_hatch_egg_auto_promotes_next_pending_egg(self):
        """When an incubating egg hatches, the next egg from reserves is auto-promoted to egg_tier."""
        self.engine.set_active_mon(None)
        self.engine.state["egg_tier"] = "normal"
        self.engine.state["egg_usage"] = PokemonBalance.EGG_HATCH_THRESHOLD
        self.engine.state["pending_eggs"] = ["rare"]

        mon, events = self.engine.hatch_egg()
        self.assertIsNotNone(self.engine.active_mon)
        self.assertEqual(self.engine.state.get("egg_tier"), "rare")
        self.assertEqual(self.engine.state.get("pending_eggs"), [])
        self.assertTrue(any("Rare Egg placed in Roster reserves" in e for e in events))

    def test_select_egg_with_specific_tier_from_reserves(self):
        """select_active_from_dex can switch active companion to held egg or swap to specific tier from reserves."""
        mon = MonState(
            base_id=4,
            path_ids=[4, 5, 6],
            planned_path_ids=[4, 5, 6],
            stage_index=0,
            used_at_stage=0,
            rarity=Rarity.COMMON,
            total_forms=3
        )
        self.engine.set_active_mon(mon)
        self.engine.state["egg_tier"] = "normal"
        self.engine.state["pending_eggs"] = ["rare"]

        # Swap to 'rare' egg
        ok, msg = self.engine.select_active_from_dex("egg rare")
        self.assertTrue(ok)
        self.assertIn("Incubating Rare Egg", msg)
        self.assertIsNone(self.engine.active_mon)
        self.assertEqual(self.engine.state.get("egg_tier"), "rare")
        self.assertEqual(self.engine.state.get("pending_eggs"), ["normal"])


if __name__ == "__main__":
    unittest.main()

