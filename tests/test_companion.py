import os
import io
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from poketokenbar.game.companion import CompanionEngine
from poketokenbar.game.models import ItemKind, Rarity, MonState, PokemonBalance
from poketokenbar.game.storage import StorageManager

class TestCompanionEngine(unittest.TestCase):

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

    def test_item_prices(self):
        self.assertEqual(ItemKind.BERRY_ORAN.price, 1_000_000)
        self.assertEqual(ItemKind.SHINY_STONE.price, 50_000_000)

    def test_hatch(self):
        mon, events = self.engine.hatch_egg(0)
        self.assertIsNotNone(mon)
        self.assertTrue(len(events) > 0)
        self.assertIn("Hatched", events[0])

    def test_select_active_mon(self):
        mon, events = self.engine.hatch_egg(0)
        ok, msg = self.engine.select_active_from_dex("1")
        self.assertTrue(ok)
        self.assertIn("Switched active companion", msg)

    def test_duplicate_egg_restriction(self):
        # Hatch initial mon to clear baseline
        self.engine.hatch_egg(0)
        # Give enough tokens to buy eggs
        self.engine.state["used_since_install"] = 500_000_000
        ok1, msg1 = self.engine.buy_egg(None)
        self.assertTrue(ok1)
        # Second buy while holding egg should fail
        ok2, msg2 = self.engine.buy_egg(None)
        self.assertFalse(ok2)
        # After clearing egg (e.g. hatching), buying should succeed
        self.engine.state["egg_tier"] = None
        ok3, msg3 = self.engine.buy_egg(Rarity.UNCOMMON)
        self.assertTrue(ok3)

    def test_strict_no_duplicate_pokemon_hatching(self):
        # Register the 8 original legendaries in the dex (including Ho-Oh #250)
        original_8_legs = [144, 150, 249, 250, 384, 483, 484, 643]
        self.engine.state["dex"] = [
            {"id": f"sp_{sp}", "species_id": sp, "base_id": sp, "status": "inactive"}
            for sp in original_8_legs
        ]
        self.engine.set_active_mon(None)

        # Hatch 10 legendary eggs in a row - NONE should ever be any of the original 8!
        hatched_ids = set()
        for _ in range(10):
            mon, events = self.engine.hatch_egg(0, force_tier="legendary")
            self.assertNotIn(mon.base_id, original_8_legs)
            self.assertNotIn(mon.base_id, hatched_ids)
            hatched_ids.add(mon.base_id)
            self.assertEqual(mon.rarity, Rarity.LEGENDARY)
            self.engine.set_active_mon(None)

    def test_legendary_egg_never_hatches_mew(self):
        # Mew (#151) must NEVER hatch from legendary eggs, even on an empty Pokédex
        self.engine.state["dex"] = []
        self.engine.set_active_mon(None)
        hatched_ids = set()
        for _ in range(15):
            mon, events = self.engine.hatch_egg(0, force_tier="legendary")
            self.assertNotEqual(mon.base_id, 151)
            hatched_ids.add(mon.base_id)
            self.engine.set_active_mon(None)
        self.assertNotIn(151, hatched_ids)

    def test_shadow_fetal_hatches_celebi_not_mew(self):
        # Shadow fetal egg must hatch Celebi (#251), never Mew (#151)
        self.engine.state["dex"] = []
        self.engine.set_active_mon(None)
        mon, events = self.engine.hatch_egg(0, force_tier="shadow_fetal")
        self.assertEqual(mon.base_id, 251)
        self.assertNotEqual(mon.base_id, 151)

    def test_mysterious_fetal_form_legacy_unowned_hatches_mew(self):
        # Legacy mysterious fetal form eggs can hatch Mew if unowned
        self.engine.state["dex"] = []
        self.engine.set_active_mon(None)
        mon, events = self.engine.hatch_egg(0, force_tier="mysterious fetal form")
        self.assertEqual(mon.base_id, 151)

    def test_mysterious_fetal_form_legacy_already_owned_never_duplicates_mew(self):
        # Legacy mysterious fetal form eggs must fall back to another legendary if Mew is already owned
        self.engine.state["dex"] = [
            {"id": "sp_151", "species_id": 151, "base_id": 151, "chain_order": [151], "status": "active"}
        ]
        self.engine.set_active_mon(None)
        mon, events = self.engine.hatch_egg(0, force_tier="mysterious fetal form")
        self.assertNotEqual(mon.base_id, 151)
        self.assertEqual(mon.rarity, Rarity.LEGENDARY)

    def test_red_battle_first_win_recruits_mew_directly_without_egg(self):
        from poketokenbar.game.red_battle import RedBattleHandler
        red = RedBattleHandler(self.engine)
        self.engine.state["red_wins"] = 0
        self.engine.state["dex"] = []
        self.engine.set_active_mon(None)

        # Simulate win turn on Red battle
        st = {
            "player_team": [25],
            "player_active_index": 0,
            "player_hps": [1000],
            "player_max_hps": [1000],
            "red_team": [{"name": "Pikachu", "type": "electric", "max_hp": 1000}],
            "red_active_index": 0,
            "red_hps": [1],
            "red_max_hps": [1000],
            "turn_log": [],
            "status": "active"
        }
        red._save_state(st)
        ok, msg = red.execute_turn(0)
        self.assertTrue(ok)

        # No egg should be assigned
        self.assertIsNone(self.engine.state.get("egg_tier"))

        # Mew must be directly recruited into dex/roster
        dex_sp_ids = {d.get("species_id") for d in self.engine.state.get("dex", [])}
        self.assertIn(151, dex_sp_ids)

        # Check turn log message
        st_after = red._get_state()
        self.assertTrue(any("Mew was touched by your bond" in log for log in st_after.get("turn_log", [])))

    def test_red_battle_win_when_mew_already_owned_does_not_duplicate(self):
        from poketokenbar.game.red_battle import RedBattleHandler
        red = RedBattleHandler(self.engine)
        self.engine.state["red_wins"] = 0
        self.engine.state["dex"] = [
            {"id": "sp_151", "species_id": 151, "base_id": 151, "chain_order": [151], "status": "inactive"}
        ]
        self.engine.set_active_mon(None)

        st = {
            "player_team": [151],
            "player_active_index": 0,
            "player_hps": [1000],
            "player_max_hps": [1000],
            "red_team": [{"name": "Pikachu", "type": "electric", "max_hp": 1000}],
            "red_active_index": 0,
            "red_hps": [1],
            "red_max_hps": [1000],
            "turn_log": [],
            "status": "active"
        }
        red._save_state(st)
        ok, msg = red.execute_turn(0)
        self.assertTrue(ok)

        # No egg should be awarded
        self.assertIsNone(self.engine.state.get("egg_tier"))

        # Mew should only appear once in dex
        mew_entries = [d for d in self.engine.state.get("dex", []) if d.get("species_id") == 151 or d.get("base_id") == 151]
        self.assertEqual(len(mew_entries), 1)

    def test_egg_hatch_sets_milestone_and_alert(self):
        self.engine.state["egg_tier"] = "common"
        self.engine.state["egg_usage"] = 0
        self.engine.set_active_mon(None)

        mon, events = self.engine.hatch_egg(0)
        self.assertIsNotNone(mon)

        # Check that last_evolution and last_milestone are recorded
        last_milestone = self.engine.state.get("last_milestone")
        self.assertIsNotNone(last_milestone)
        self.assertIn("Egg Hatched!", last_milestone)
        self.assertEqual(self.engine.state.get("last_evolution"), last_milestone)

        # Check that milestone alert is triggered in events
        self.assertTrue(any("Egg Hatched!" in e for e in events))

    def test_companion_tab_renders_egg_hatch_milestone(self):
        from poketokenbar.tui_tabs import companion as companion_tab
        import io
        import sys
        from poketokenbar.game.models import MonState, Rarity

        self.engine.state["last_milestone"] = "Egg Hatched! You got a Bulbasaur (#1)!"
        mon = MonState(
            base_id=1,
            path_ids=[1, 2, 3],
            planned_path_ids=[1, 2, 3],
            stage_index=0,
            used_at_stage=0,
            rarity=Rarity.COMMON,
            total_forms=3
        )
        self.engine.set_active_mon(mon)

        class DummyApp:
            def __init__(self, engine):
                self.engine = engine
                self.tab_index = 0
                self.page = 1

        app = DummyApp(self.engine)
        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            companion_tab.render(app, {
                "total_tokens": 1000,
                "today_tokens": 500,
                "antigravity_today": 250,
                "week_tokens": 2000,
                "month_tokens": 5000,
                "burn_rate_tpm": 10,
            })
        finally:
            sys.stdout = old_stdout

        rendered = buf.getvalue()
        self.assertIn("Milestone:", rendered)
        self.assertIn("Egg Hatched! You got a Bulbasaur (#1)!", rendered)
        self.assertIn("🐣", rendered)

        # Verify all rendered lines strictly respect <= 72 visible columns
        import re
        for line in rendered.split("\n"):
            visible_line = re.sub(r'\033\[[0-9;]*m', '', line)
            self.assertLessEqual(len(visible_line), 72, f"Line exceeds 72 cols: {visible_line}")

    def test_companion_tab_renders_egg_incubation_progress_shortened(self):
        from poketokenbar.tui_tabs import companion as companion_tab
        import io
        import sys
        import re

        self.engine.set_active_mon(None)
        self.engine.state["egg_tier"] = "legendary"
        self.engine.state["egg_usage"] = 197_600

        class DummyApp:
            def __init__(self, engine):
                self.engine = engine
                self.tab_index = 0
                self.page = 1

        app = DummyApp(self.engine)
        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            companion_tab.render(app, {
                "total_tokens": 1000,
                "today_tokens": 500,
                "antigravity_today": 250,
                "week_tokens": 2000,
                "month_tokens": 5000,
                "burn_rate_tpm": 10,
            })
        finally:
            sys.stdout = old_stdout

        rendered = buf.getvalue()
        self.assertIn("Incubation:", rendered)
        self.assertNotIn("Incubation Progress:", rendered)
        self.assertIn("197.6K / 1.5M tokens", rendered)

        # Verify all lines strictly <= 72 visible columns
        for line in rendered.split("\n"):
            visible_line = re.sub(r'\033\[[0-9;]*m', '', line)
            self.assertLessEqual(len(visible_line), 72, f"Egg incubation line exceeds 72 cols: {visible_line}")

    def test_new_game_features(self):
        mon, events = self.engine.hatch_egg(0)
        
        # Test Oran Berry feeding
        self.engine.state["inventory"]["berry_oran"] = 1
        ok, msg = self.engine.use_item(ItemKind.BERRY_ORAN)
        self.assertTrue(ok)
        self.assertIn("Fed 1 Oran Berry", msg)

        # Test Trainer Card generation
        card_str = self.engine.generate_trainer_card()
        self.assertIn("TRAINER PROFILE CARD", card_str)

        # Test Expedition dispatching by index and species ID
        ok, msg = self.engine.dispatch_expedition("1", "viridian")
        self.assertTrue(ok)
        self.assertIn("Dispatched", msg)

    def test_streak_calculation(self):
        today_str = "2026-08-20"
        active_days = ["2026-08-19", "2026-08-20"]
        streak = self.engine._calculate_streak_from_active_days(active_days, today_str)
        self.assertEqual(streak, 2)

    def test_day_rollover_zero_delta(self):
        import datetime
        self.engine.state["last_active_date"] = "2026-08-19"
        self.engine.state["used_since_install"] = 100_000
        self.engine.state["install_baseline_set"] = True

        today_str = datetime.date.today().strftime("%Y-%m-%d")
        active_days = ["2026-08-19", today_str]
        # Call process_usage with 0 delta
        self.engine.process_usage(100_000, active_days)
        self.assertEqual(self.engine.state["last_active_date"], today_str)

    def test_expedition_roster_restriction(self):
        # Register an evolved species entry (e.g. Dratini #147 with status evolved)
        self.engine.state["dex"] = [
            {"id": "sp_147", "species_id": 147, "base_id": 147, "chain_order": [147, 148, 149], "status": "evolved"},
            {"id": "sp_149", "species_id": 149, "base_id": 147, "chain_order": [147, 148, 149], "status": "inactive"}
        ]
        # Attempt to dispatch evolved Dratini (#147)
        ok, msg = self.engine.dispatch_expedition("#147", "viridian")
        self.assertFalse(ok)
        self.assertIn("not found in Roster", msg)

        # Attempt to dispatch active roster Dragonite (#149)
        ok2, msg2 = self.engine.dispatch_expedition("#149", "viridian")
        self.assertTrue(ok2)
        self.assertIn("Dispatched", msg2)

    def test_expedition_dispatch_unevolved_companion_with_higher_form_discovered(self):
        # User has Quilava (#156) and Typhlosion (#157) in dex
        self.engine.state["dex"] = [
            {"id": "sp_155", "species_id": 155, "base_id": 155, "chain_order": [155, 156, 157], "status": "evolved"},
            {"id": "sp_156", "species_id": 156, "base_id": 155, "chain_order": [155, 156, 157], "status": "inactive"},
            {"id": "sp_157", "species_id": 157, "base_id": 155, "chain_order": [155, 156, 157], "status": "inactive"}
        ]
        # In roster: row 1 is Quilava (156), row 2 is Typhlosion (157)
        # 1. Dispatch row 1 -> must dispatch Quilava (#156)
        ok1, msg1 = self.engine.dispatch_expedition("1", "viridian")
        self.assertTrue(ok1)
        self.assertIn("Quilava", msg1)
        self.assertEqual(self.engine.state["expeditions"][0]["sp_id"], 156)

        # Clear expeditions
        self.engine.state["expeditions"] = []

        # 2. Dispatch by name "quilava" -> must dispatch Quilava (#156)
        ok2, msg2 = self.engine.dispatch_expedition("quilava", "viridian")
        self.assertTrue(ok2)
        self.assertIn("Quilava", msg2)
        self.assertEqual(self.engine.state["expeditions"][0]["sp_id"], 156)

        # Clear expeditions
        self.engine.state["expeditions"] = []

        # 3. Dispatch by species ID "156" -> must dispatch Quilava (#156)
        ok3, msg3 = self.engine.dispatch_expedition("156", "viridian")
        self.assertTrue(ok3)
        self.assertIn("Quilava", msg3)
        self.assertEqual(self.engine.state["expeditions"][0]["sp_id"], 156)

    def test_multi_target_expedition_dispatch(self):
        # Setup 4 companions in dex / roster
        self.engine.state["dex"] = [
            {"id": "sp_1", "species_id": 1, "base_id": 1, "chain_order": [1, 2, 3], "status": "inactive", "happiness": 100},
            {"id": "sp_4", "species_id": 4, "base_id": 4, "chain_order": [4, 5, 6], "status": "inactive", "happiness": 100},
            {"id": "sp_7", "species_id": 7, "base_id": 7, "chain_order": [7, 8, 9], "status": "inactive", "happiness": 100},
            {"id": "sp_25", "species_id": 25, "base_id": 25, "chain_order": [25, 26], "status": "inactive", "happiness": 0}  # Exhausted
        ]
        self.engine.state["expeditions"] = []

        # 1. Comma-separated dispatch (1 and 2 to Viridian)
        ok, msg = self.engine.dispatch_expedition("1, 2", "viridian")
        self.assertTrue(ok)
        self.assertIn("Dispatched 2 Pokémon", msg)
        self.assertEqual(len(self.engine.state["expeditions"]), 2)
        exp_sps = {e["sp_id"] for e in self.engine.state["expeditions"]}
        self.assertIn(1, exp_sps)
        self.assertIn(4, exp_sps)

        # 2. Reset and test range dispatch ("1-3" to Evolution Mine)
        self.engine.state["expeditions"] = []
        ok, msg = self.engine.dispatch_expedition("1-3", "mine")
        self.assertTrue(ok)
        self.assertIn("Dispatched 3 Pokémon", msg)
        self.assertEqual(len(self.engine.state["expeditions"]), 3)

        # 3. Test 'all' dispatch: should dispatch eligible (sp_1, sp_4, sp_7) and skip exhausted (sp_25)
        self.engine.state["expeditions"] = []
        ok, msg = self.engine.dispatch_expedition("all", "silver")
        self.assertTrue(ok)
        self.assertIn("Dispatched 3 Pokémon", msg)
        self.assertIn("skipped", msg.lower())
        self.assertEqual(len(self.engine.state["expeditions"]), 3)

        # 4. Test TUI _parse_send_args helper
        from poketokenbar.tui import PokeTokenBarTUI
        self.assertEqual(PokeTokenBarTUI._parse_send_args("1 viridian"), ("1", "viridian"))
        self.assertEqual(PokeTokenBarTUI._parse_send_args("1,2,3 viridian"), ("1,2,3", "viridian"))
        self.assertEqual(PokeTokenBarTUI._parse_send_args("1 2 3 viridian"), ("1 2 3", "viridian"))
        self.assertEqual(PokeTokenBarTUI._parse_send_args("1-5 mine"), ("1-5", "mine"))
        self.assertEqual(PokeTokenBarTUI._parse_send_args("all mt silver"), ("all", "mt silver"))
        self.assertEqual(PokeTokenBarTUI._parse_send_args("1 2 3"), ("1 2 3", "viridian"))
        self.assertEqual(PokeTokenBarTUI._parse_send_args("1-5"), ("1-5", "viridian"))
        self.assertEqual(PokeTokenBarTUI._parse_send_args("1, 2, 3"), ("1, 2, 3", "viridian"))
        self.assertEqual(PokeTokenBarTUI._parse_send_args("1 ine"), ("1", "ine"))

    def test_expedition_progress_advancement(self):
        self.engine.state["dex"] = [
            {"id": "sp_149", "species_id": 149, "base_id": 147, "chain_order": [147, 148, 149], "status": "inactive"}
        ]
        self.engine.dispatch_expedition("#149", "viridian")
        old_used = self.engine.state.get("used_since_install", 0)
        self.engine.process_usage(old_used + 1_000_000)
        expeditions = self.engine.state.get("expeditions", [])
        self.assertEqual(len(expeditions), 1)

    def test_active_pokemon_xp_and_evolution(self):
        mon, events = self.engine.hatch_egg(0)
        self.assertIsNotNone(self.engine.active_mon)
        self.engine.state["install_baseline_set"] = True
        
        initial_stage = self.engine.active_mon.stage_index
        initial_xp = self.engine.active_mon.used_at_stage
        
        # Burn 10,000,000 tokens
        old_used = self.engine.state.get("used_since_install", 0)
        events = self.engine.process_usage(old_used + 10_000_000)
        
        active = self.engine.active_mon
        if active:
            # XP should have increased
            self.assertGreater(active.used_at_stage, initial_xp)

    def test_auto_halt_evolution_when_next_stage_owned(self):
        # Register Typhlosion (#157) in dex
        self.engine.state["dex"] = [
            {"id": "sp_157", "species_id": 157, "base_id": 155, "chain_order": [155, 156, 157], "status": "inactive"}
        ]
        # Active companion is Quilava (#156, stage 1)
        mon = MonState(
            base_id=155,
            path_ids=[155, 156, 157],
            planned_path_ids=[155, 156, 157],
            stage_index=1,
            used_at_stage=0,
            rarity=Rarity.RARE,
            total_forms=3
        )
        self.engine.set_active_mon(mon)

        target_xp = PokemonBalance.phase_threshold(mon.rarity, mon.total_forms, mon.stage_index, self.engine.current_difficulty)

        # Burn enough XP to normally trigger evolution
        mon.used_at_stage = target_xp + 5_000_000
        events = self.engine._check_growth(mon)

        # Evolution should be halted: stage_index is still 1 (Quilava), XP capped at target_xp
        self.assertEqual(self.engine.active_mon.stage_index, 1)
        self.assertEqual(self.engine.active_mon.current_id, 156)
        self.assertEqual(self.engine.active_mon.used_at_stage, target_xp)
        self.assertEqual(len(events), 0)

    def test_prevent_stone_evolution_if_owned(self):
        from poketokenbar.game.models import ItemKind
        # Register Vaporeon (#134) in dex
        self.engine.state["dex"] = [
            {"id": "sp_134", "species_id": 134, "base_id": 133, "status": "inactive"}
        ]
        # Active companion is Eevee (#133)
        mon = MonState(
            base_id=133,
            path_ids=[133],
            planned_path_ids=[133],
            stage_index=0,
            used_at_stage=0,
            rarity=Rarity.UNCOMMON,
            total_forms=2
        )
        self.engine.set_active_mon(mon)
        self.engine.state["inventory"] = {"water_stone": 1}

        # Attempt to use Water Stone
        ok, msg = self.engine.use_item(ItemKind.WATER_STONE)
        self.assertFalse(ok)
        self.assertIn("already exists in your Pokédex", msg)
        self.assertEqual(self.engine.state["inventory"].get("water_stone"), 1)

    def test_dynamic_evolution_cosmoem_day_night(self):
        import datetime
        from poketokenbar.game.models import MonState, Rarity, PokemonBalance
        day_time = datetime.datetime(2026, 9, 16, 12, 0, 0)
        night_time = datetime.datetime(2026, 9, 16, 22, 0, 0)

        # Active companion is Cosmoem (#790, stage 1)
        mon = MonState(
            base_id=789,
            path_ids=[789, 790, 791],
            planned_path_ids=[789, 790, 791],
            stage_index=1,
            used_at_stage=0,
            rarity=Rarity.LEGENDARY,
            total_forms=3
        )
        self.engine.set_active_mon(mon)

        # Test dynamic evolution ID resolution
        self.assertEqual(self.engine.get_next_evolution_id(mon, now=day_time), 791)
        self.assertEqual(mon.path_ids[2], 791)

        self.assertEqual(self.engine.get_next_evolution_id(mon, now=night_time), 792)
        self.assertEqual(mon.path_ids[2], 792)

        # Natural evolution at night -> Lunala (#792)
        target_xp = PokemonBalance.phase_threshold(mon.rarity, mon.total_forms, mon.stage_index, self.engine.current_difficulty)
        mon.used_at_stage = target_xp
        events = self.engine._check_growth(mon, now=night_time)
        self.assertEqual(mon.stage_index, 2)
        self.assertEqual(mon.current_id, 792)
        self.assertTrue(any("Lunala" in ev for ev in events))

    def test_dynamic_evolution_pokedex_duplicate_branching(self):
        import datetime
        from poketokenbar.game.models import MonState, Rarity, PokemonBalance
        day_time = datetime.datetime(2026, 9, 16, 12, 0, 0)
        night_time = datetime.datetime(2026, 9, 16, 22, 0, 0)

        # Register Solgaleo (#791) in Pokédex
        self.engine.state["dex"] = [
            {"id": "sp_791", "species_id": 791, "base_id": 789, "status": "inactive"}
        ]

        # Active companion is Cosmoem (#790, stage 1)
        mon = MonState(
            base_id=789,
            path_ids=[789, 790, 791],
            planned_path_ids=[789, 790, 791],
            stage_index=1,
            used_at_stage=0,
            rarity=Rarity.LEGENDARY,
            total_forms=3
        )
        self.engine.set_active_mon(mon)

        target_xp = PokemonBalance.phase_threshold(mon.rarity, mon.total_forms, mon.stage_index, self.engine.current_difficulty)
        mon.used_at_stage = target_xp + 100_000

        # During the Day, next form is Solgaleo (791), which is already owned -> evolution halts
        events_day = self.engine._check_growth(mon, now=day_time)
        self.assertEqual(self.engine.active_mon.stage_index, 1)
        self.assertEqual(self.engine.active_mon.current_id, 790)
        self.assertEqual(self.engine.active_mon.used_at_stage, target_xp)
        self.assertEqual(len(events_day), 0)

        # During the Night, next form resolves to Lunala (792), which is unowned -> evolves into Lunala!
        events_night = self.engine._check_growth(mon, now=night_time)
        self.assertEqual(self.engine.active_mon.stage_index, 2)
        self.assertEqual(self.engine.active_mon.current_id, 792)
        self.assertTrue(any("Lunala" in ev for ev in events_night))

    def test_cosmoem_sun_moon_stone_overrides(self):
        from poketokenbar.game.models import ItemKind, MonState, Rarity
        # Cosmoem can use Sun Stone to become Solgaleo
        mon_sol = MonState(
            base_id=789,
            path_ids=[789, 790, 791],
            planned_path_ids=[789, 790, 791],
            stage_index=1,
            used_at_stage=0,
            rarity=Rarity.LEGENDARY,
            total_forms=3
        )
        self.engine.set_active_mon(mon_sol)
        self.engine.state["inventory"] = {"sun_stone": 1, "moon_stone": 1}

        ok_sun, msg_sun = self.engine.use_item(ItemKind.SUN_STONE)
        self.assertTrue(ok_sun)
        self.assertEqual(self.engine.active_mon.current_id, 791)
        self.assertIn("Solgaleo", msg_sun)

        # Fresh Cosmoem can use Moon Stone to become Lunala
        mon_luna = MonState(
            base_id=789,
            path_ids=[789, 790, 791],
            planned_path_ids=[789, 790, 791],
            stage_index=1,
            used_at_stage=0,
            rarity=Rarity.LEGENDARY,
            total_forms=3
        )
        self.engine.set_active_mon(mon_luna)
        ok_moon, msg_moon = self.engine.use_item(ItemKind.MOON_STONE)
        self.assertTrue(ok_moon)
        self.assertEqual(self.engine.active_mon.current_id, 792)
        self.assertIn("Lunala", msg_moon)

    def test_eevee_day_night_evolution(self):
        import datetime
        from poketokenbar.game.models import MonState, Rarity, PokemonBalance
        day_time = datetime.datetime(2026, 9, 16, 10, 0, 0)
        night_time = datetime.datetime(2026, 9, 16, 20, 0, 0)

        # Day evolution: Eevee -> Espeon (#196)
        eevee_day = MonState(
            base_id=133,
            path_ids=[133, 196],
            planned_path_ids=[133, 196],
            stage_index=0,
            used_at_stage=0,
            rarity=Rarity.UNCOMMON,
            total_forms=2
        )
        self.assertEqual(self.engine.get_next_evolution_id(eevee_day, now=day_time), 196)
        target_xp = PokemonBalance.phase_threshold(eevee_day.rarity, eevee_day.total_forms, eevee_day.stage_index, self.engine.current_difficulty)
        eevee_day.used_at_stage = target_xp
        self.engine.set_active_mon(eevee_day)
        events_day = self.engine._check_growth(eevee_day, now=day_time)
        self.assertEqual(self.engine.active_mon.current_id, 196)
        self.assertTrue(any("Espeon" in ev for ev in events_day))

        # Night evolution: Eevee -> Umbreon (#197)
        eevee_night = MonState(
            base_id=133,
            path_ids=[133, 196],
            planned_path_ids=[133, 196],
            stage_index=0,
            used_at_stage=0,
            rarity=Rarity.UNCOMMON,
            total_forms=2
        )
        self.assertEqual(self.engine.get_next_evolution_id(eevee_night, now=night_time), 197)
        eevee_night.used_at_stage = target_xp
        self.engine.set_active_mon(eevee_night)
        events_night = self.engine._check_growth(eevee_night, now=night_time)
        self.assertEqual(self.engine.active_mon.current_id, 197)
        self.assertTrue(any("Umbreon" in ev for ev in events_night))

    def test_companion_tab_72_col_compliance_with_dynamic_evo(self):
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.companion import render as render_companion_tab
        from poketokenbar.game.models import MonState, Rarity

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        app = MagicMock()
        app.engine = self.engine

        # Active companion: Cosmoem (#790)
        cosmoem = MonState(
            base_id=789,
            path_ids=[789, 790, 791],
            planned_path_ids=[789, 790, 791],
            stage_index=1,
            used_at_stage=100_000,
            rarity=Rarity.LEGENDARY,
            total_forms=3
        )
        self.engine.set_active_mon(cosmoem)

        summary = {
            "today_tokens": 150_000,
            "antigravity_today": 120_000,
            "week_tokens": 800_000,
            "month_tokens": 2_500_000,
            "total_tokens": 10_000_000,
            "burn_rate_tpm": 2500,
        }

        for time_mock in ["day", "night"]:
            with patch.object(self.engine, "get_current_time_of_day", return_value=time_mock):
                trap = io.StringIO()
                with patch("sys.stdout", trap):
                    render_companion_tab(app, summary)
                output = trap.getvalue()
                expected_tag = "☀️" if time_mock == "day" else "🌙"
                self.assertIn(expected_tag, output)
                for line in output.split("\n"):
                    clean = ansi_regex.sub("", line)
                    self.assertLessEqual(len(clean), 72, f"Companion tab line exceeds 72 cols: '{clean}' (len={len(clean)})")

    def test_billing_cycle_start_calculation(self):
        import datetime
        from poketokenbar.tracker.manager import get_billing_cycle_start

        # Day 1 cycle: Sept 16, 2026 -> Sept 1, 2026
        dt1 = datetime.datetime(2026, 9, 16, 12, 0, 0)
        s1 = get_billing_cycle_start(dt1, 1)
        self.assertEqual(s1.year, 2026)
        self.assertEqual(s1.month, 9)
        self.assertEqual(s1.day, 1)

        # Day 15 cycle: Sept 16, 2026 (day >= 15) -> Sept 15, 2026
        s2 = get_billing_cycle_start(dt1, 15)
        self.assertEqual(s2.month, 9)
        self.assertEqual(s2.day, 15)

        # Day 15 cycle: Sept 10, 2026 (day < 15) -> August 15, 2026
        dt2 = datetime.datetime(2026, 9, 10, 12, 0, 0)
        s3 = get_billing_cycle_start(dt2, 15)
        self.assertEqual(s3.month, 8)
        self.assertEqual(s3.day, 15)

        # Year rollover: Jan 5, 2027 (day < 20) -> Dec 20, 2026
        dt3 = datetime.datetime(2027, 1, 5, 12, 0, 0)
        s4 = get_billing_cycle_start(dt3, 20)
        self.assertEqual(s4.year, 2026)
        self.assertEqual(s4.month, 12)
        self.assertEqual(s4.day, 20)

    def test_usage_manager_billing_cycle_and_baseline(self):
        import datetime
        from poketokenbar.tracker.base import UsageEntry
        from poketokenbar.tracker.manager import UsageManager

        tracker = UsageManager()
        tz = datetime.timezone.utc
        e1 = UsageEntry(
            id="test|1",
            date=datetime.datetime(2026, 8, 20, 10, 0, 0, tzinfo=tz),
            local_day="2026-08-20",
            model="claude-3-5-sonnet",
            input_tokens=500_000,
            output_tokens=500_000
        )
        e2 = UsageEntry(
            id="test|2",
            date=datetime.datetime(2026, 9, 10, 10, 0, 0, tzinfo=tz),
            local_day="2026-09-10",
            model="claude-3-5-sonnet",
            input_tokens=1_000_000,
            output_tokens=1_000_000
        )
        e3 = UsageEntry(
            id="test|3",
            date=datetime.datetime(2026, 9, 16, 10, 0, 0, tzinfo=tz),
            local_day="2026-09-16",
            model="claude-3-5-sonnet",
            input_tokens=1_500_000,
            output_tokens=1_500_000
        )
        entries = [e1, e2, e3]

        # Case A: Billing cycle day = 15 (as of Sept 16)
        # Cycle start is Sept 15. Only e3 (Sept 16) is in current billing cycle (3,000,000 tokens)
        summary_d15 = tracker._compute_summary(entries, billing_cycle_day=15, baseline_total=0)
        self.assertEqual(summary_d15["month_tokens"], 3_000_000)
        self.assertEqual(summary_d15["raw_total_tokens"], 6_000_000)
        self.assertEqual(summary_d15["total_tokens"], 6_000_000)

        # Case B: Re-baseline total tokens by 5,000,000
        # Displayed total should be 6,000,000 - 5,000,000 = 1,000,000
        summary_base = tracker._compute_summary(entries, billing_cycle_day=15, baseline_total=5_000_000)
        self.assertEqual(summary_base["total_tokens"], 1_000_000)
        self.assertEqual(summary_base["raw_total_tokens"], 6_000_000)
        self.assertEqual(summary_base["baseline_total_tokens"], 5_000_000)

    def test_engine_billing_cycle_and_baseline_methods(self):
        # Set billing cycle day
        ok_valid, msg = self.engine.set_billing_cycle_day(15)
        self.assertTrue(ok_valid)
        self.assertEqual(self.engine.get_billing_cycle_day(), 15)

        ok_invalid, _ = self.engine.set_billing_cycle_day(35)
        self.assertFalse(ok_invalid)

        # Initialize total tokens baseline
        ok_init, msg_init = self.engine.initialize_total_tokens(10_000_000)
        self.assertTrue(ok_init)
        self.assertEqual(self.engine.state["baseline_total_tokens"], 10_000_000)

        # Ensure companion growth and process_usage remain unaffected
        mon = self.engine.active_mon
        if not mon:
            mon, _ = self.engine.hatch_egg(0)
        old_used = self.engine.state.get("used_since_install", 0)
        # Passing raw cumulative tokens to process_usage continues normal game progression
        self.engine.process_usage(old_used + 500_000)
        self.assertEqual(self.engine.state["used_since_install"], old_used + 500_000)

        # Clear baseline
        ok_clear, _ = self.engine.clear_total_tokens_baseline()
        self.assertTrue(ok_clear)
        self.assertEqual(self.engine.state["baseline_total_tokens"], 0)

    def test_tokens_init_clears_all_metrics_to_zero(self):
        from poketokenbar.tracker.manager import UsageManager
        from poketokenbar.tracker.base import UsageEntry
        import datetime

        now = datetime.datetime.now().astimezone()
        today_str = now.strftime("%Y-%m-%d")
        past = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Create past entries within today, week, and month
        entries = [
            UsageEntry(
                id="test|1",
                date=past,
                local_day=today_str,
                model="test",
                input_tokens=100_000,
                output_tokens=50_000
            )
        ]

        mgr = UsageManager()
        try:
            # Before init: metrics show 150K
            s_before = mgr._compute_summary(entries)
            self.assertEqual(s_before["today_tokens"], 150_000)
            self.assertEqual(s_before["week_tokens"], 150_000)
            self.assertEqual(s_before["month_tokens"], 150_000)
            self.assertEqual(s_before["total_tokens"], 150_000)

            # Run tokens init
            ok_init, msg_init = self.engine.initialize_total_tokens(150_000)
            self.assertTrue(ok_init)
            self.assertIn("tokens_init_ts", self.engine.state)

            # After init: past entries are ignored, all 4 metrics reset to 0
            s_after = mgr._compute_summary(entries)
            self.assertEqual(s_after["today_tokens"], 0)
            self.assertEqual(s_after["week_tokens"], 0)
            self.assertEqual(s_after["month_tokens"], 0)
            self.assertEqual(s_after["total_tokens"], 0)

            # New entry generated after init
            init_dt = datetime.datetime.fromisoformat(self.engine.state["tokens_init_ts"])
            future_entry = UsageEntry(
                id="test|2",
                date=init_dt + datetime.timedelta(seconds=1),
                local_day=today_str,
                model="test",
                input_tokens=20_000,
                output_tokens=5_000
            )
            s_future = mgr._compute_summary(entries + [future_entry])
            self.assertEqual(s_future["today_tokens"], 25_000)
            self.assertEqual(s_future["week_tokens"], 25_000)
            self.assertEqual(s_future["month_tokens"], 25_000)
            self.assertEqual(s_future["total_tokens"], 25_000)
        finally:
            mgr.stop()

    def test_settings_tab_72_col_compliance_with_billing_and_baseline(self):
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.settings import render_settings_tab

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        app = MagicMock()
        app.engine = self.engine
        self.engine.state["billing_cycle_day"] = 15
        self.engine.state["baseline_total_tokens"] = 5_000_000

        # Page 1
        app.settings_page = 1
        trap1 = io.StringIO()
        with patch("sys.stdout", trap1):
            render_settings_tab(app)
        out1 = trap1.getvalue()
        self.assertIn("System Date & Hour:", out1)
        self.assertRegex(out1, r'\d{4}-\d{2}-\d{2} \d{2}')
        self.assertTrue("(Day)" in out1 or "(Night)" in out1)
        self.assertNotIn("☀️", out1)
        self.assertIn("Day 15 of each month", out1)
        self.assertIn("Initialized", out1)
        for line in out1.split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Settings tab page 1 line exceeds 72 cols: '{clean}' (len={len(clean)})")

        # Page 2
        app.settings_page = 2
        trap2 = io.StringIO()
        with patch("sys.stdout", trap2):
            render_settings_tab(app)
        out2 = trap2.getvalue()
        self.assertIn("System Date & Hour:", out2)
        self.assertRegex(out2, r'\d{4}-\d{2}-\d{2} \d{2}')
        self.assertIn("Reset Game Progress:", out2)
        for line in out2.split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Settings tab page 2 line exceeds 72 cols: '{clean}' (len={len(clean)})")

    def test_quests_tab_72_col_compliance_and_achievements_formatting(self):
        """Verify Quests tab and compact Achievements lines satisfy 72 cols with tight spacing."""
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.quests import render_quests_tab

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        app = MagicMock()
        app.engine = self.engine

        # Test with mix of locked and unlocked achievements
        self.engine.state["achievements"] = ["shiny_hunter", "token_tycoon"]
        self.engine.state["gym_badges"] = ["Boulder", "Cascade", "Thunder", "Rainbow"]
        self.engine.state["daily_quests"] = {
            "quests": [
                {"id": "1", "text": "Burn 10,000,000 tokens", "progress": 5_000_000, "target": 10_000_000, "claimed": False},
                {"id": "2", "text": "Complete 2 Expeditions", "progress": 2, "target": 2, "claimed": True}
            ]
        }

        trap = io.StringIO()
        with patch("sys.stdout", trap):
            render_quests_tab(app)
        output = trap.getvalue()
        clean_output = ansi_regex.sub("", output)

        self.assertIn("🌟 Shiny Hunter - Hatch a Shiny Pokémon [UNLOCKED]", clean_output)
        self.assertIn("💎 Token Tycoon - Burn 100M+ tokens [UNLOCKED]", clean_output)
        self.assertIn("⚡ Streak Master - Maintain 3+ day streak [LOCKED]", clean_output)

        for line in output.split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Quests tab line exceeds 72 cols: '{clean}' (len={len(clean)})")
            # Verify no excessive 4+ space gaps in achievement lines
            if "•" in clean:
                self.assertNotIn("    ", clean, f"Achievement line contains excessive spacing: '{clean}'")

    def test_expedition_missing_keys_defensive(self):
        # Expeditions with missing reward/target/progress should not raise KeyError
        self.engine.state["expeditions"] = [
            {"sp_id": 3, "area": "cerulean"}
        ]
        events = []
        self.engine._update_expeditions(500_000, events)
        exp = self.engine.state["expeditions"][0]
        self.assertEqual(exp.get("reward"), "berry_oran")
        self.assertGreater(exp.get("progress", 0), 0)
        self.assertEqual(exp.get("target"), 5_000_000)

    def test_dispatch_expedition_invalid_destination(self):
        mon, events = self.engine.hatch_egg(0)
        # Dispatch with mistyped destination 'ine'
        ok, msg = self.engine.dispatch_expedition("1", "ine")
        self.assertFalse(ok)
        self.assertIn("not one of the available options", msg)
        self.assertIn("ine", msg)
        # Active companion should NOT be cleared on failed dispatch
        self.assertIsNotNone(self.engine.active_mon)
        # Valid destination 'mine' should succeed
        ok_valid, msg_valid = self.engine.dispatch_expedition("1", "mine")
        self.assertTrue(ok_valid)
        self.assertIn("Evolution Mine", msg_valid)

    def test_roster_and_pokedex_rendering_defensive(self):
        from unittest.mock import MagicMock
        from poketokenbar.tui_tabs.roster import render as render_roster
        from poketokenbar.tui_tabs.pokedex import render as render_pokedex
        
        # Add a mon to dex
        self.engine.hatch_egg(0)
        # Set a malformed expedition entry missing keys
        self.engine.state["expeditions"] = [{"sp_id": 16}]
        
        app = MagicMock()
        app.engine = self.engine
        app.roster_page = 1
        app.pokedex_page = 1
        
        # Rendering shouldn't raise any KeyError
        try:
            render_roster(app)
            render_pokedex(app)
        except Exception as e:
            self.fail(f"Rendering raised unexpected exception: {e}")

    def test_red_battle_assembly_with_expeditions(self):
        from poketokenbar.game.red_battle import RedBattleHandler
        self.engine.state["dex"] = [
            {"species_id": pid, "base_id": pid, "status": "graduated"}
            for pid in [3, 6, 9, 25, 143, 149]
        ]
        self.engine.state["expeditions"] = [{"sp_id": 149}]
        handler = RedBattleHandler(self.engine)
        ok, msg = handler.assemble_team([3, 6, 9, 25, 143, 149])
        self.assertFalse(ok)
        self.assertIn("expedition", msg)

    def test_red_battle_hp_reduction_does_not_mutate_max_hp(self):
        from poketokenbar.game.red_battle import RedBattleHandler
        self.engine.state["dex"] = [
            {"species_id": pid, "base_id": pid, "status": "graduated"}
            for pid in [3, 6, 9, 25, 143, 149]
        ]
        handler = RedBattleHandler(self.engine)
        ok, msg = handler.assemble_team([3, 6, 9, 25, 143, 149])
        self.assertTrue(ok)
        st = handler._get_state()
        
        # Verify that player_hps and player_max_hps are distinct list instances
        self.assertIsNot(st["player_hps"], st["player_max_hps"])
        initial_hp = st["player_hps"][0]
        initial_max_hp = st["player_max_hps"][0]
        self.assertEqual(initial_hp, initial_max_hp)

        # Force Red's turn: execute turn 0 (Strike) where Red retaliates
        ok, msg = handler.execute_turn(0)
        self.assertTrue(ok)
        
        st_after = handler._get_state()
        # Verify Red deals damage to player and reduces current HP
        self.assertLess(st_after["player_hps"][0], initial_hp)
        # Verify that player_max_hps has NOT shrunk with current HP!
        self.assertEqual(st_after["player_max_hps"][0], initial_max_hp)

    def test_red_battle_companions_cannot_be_active_or_sent_on_expeditions(self):
        from poketokenbar.game.red_battle import RedBattleHandler
        from poketokenbar.game.models import MonState, Rarity
        # Register a roster: 6 for Red, and 1 extra (#1)
        self.engine.state["dex"] = [
            {"species_id": pid, "base_id": pid, "status": "graduated"}
            for pid in [1, 3, 6, 9, 25, 143, 149]
        ]
        # Set #25 as active companion before assembly
        mon25 = MonState(
            base_id=25,
            path_ids=[25],
            planned_path_ids=[25],
            stage_index=0,
            used_at_stage=0,
            rarity=Rarity.COMMON,
            total_forms=1
        )
        self.engine.set_active_mon(mon25)
        self.assertIsNotNone(self.engine.active_mon)

        handler = RedBattleHandler(self.engine)
        ok, msg = handler.assemble_team([3, 6, 9, 25, 143, 149])
        self.assertTrue(ok)

        # 1. Active companion must be disengaged because #25 was drafted into Red battle
        self.assertIsNone(self.engine.active_mon)

        # 2. Cannot select any of the 6 Pokémon currently in Red battle as active companion
        ok_sel, msg_sel = self.engine.select_active_from_dex("25")
        self.assertFalse(ok_sel)
        self.assertIn("battle with Red", msg_sel)

        # But Pokémon #1 (not in battle with Red) can still be selected
        ok_sel_1, msg_sel_1 = self.engine.select_active_from_dex("1")
        self.assertTrue(ok_sel_1)
        self.assertEqual(self.engine.active_mon.base_id, 1)

        # 3. Cannot dispatch Pokémon in Red battle on single expedition
        ok_exp, msg_exp = self.engine.dispatch_expedition("25", "viridian")
        self.assertFalse(ok_exp)
        self.assertIn("battle with Red", msg_exp)

        # 4. Batch expedition skips Pokémon in Red battle
        ok_batch, msg_batch = self.engine.dispatch_expedition("all", "viridian")
        # #1 is dispatched, #25, #3, etc. are skipped because they are in Red battle
        self.assertIn("in Red battle", msg_batch)

        # 5. When battle ends (e.g. running away), Pokémon are freed
        ok_run, msg_run = handler.run_away()
        self.assertTrue(ok_run)
        self.assertEqual(self.engine.get_red_battle_active_pokemon_ids(), set())

        # Now #25 can be selected as active companion
        ok_sel_again, msg_sel_again = self.engine.select_active_from_dex("25")
        self.assertTrue(ok_sel_again)
        self.assertEqual(self.engine.active_mon.base_id, 25)

    def test_render_battles_tab_shows_both_original_tui_and_hall_of_fame(self):
        import io
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.battles import render_battles_tab

        # Setup state as won Red battle
        self.engine.state["gym_badges"] = ["🏆 Champion Badge"]
        self.engine.state["red_wins"] = 1
        self.engine.state["red_hof"] = [[3, 6, 9, 25, 143, 149]]
        self.engine.state["red_battle_state"] = {"status": "win", "player_team": [3, 6, 9, 25, 143, 149]}
        self.engine.state["trainer_battles"] = {"wins": 15, "losses": 3}
        self.engine.state["battle_logs"] = ["Won against Youngster Joey"]

        app = MagicMock()
        app.engine = self.engine

        stdout_trap = io.StringIO()
        with patch("sys.stdout", stdout_trap):
            render_battles_tab(app)

        output = stdout_trap.getvalue()
        # Verifies that the original Battles TUI is rendered
        self.assertIn("Gym Boss Raids & Trainer Auto-Battles", output)
        self.assertIn("Mini-Trainer Auto-Battle Record", output)
        self.assertIn("Won against Youngster Joey", output)
        # AND verifies that the Hall of Fame section is also rendered
        self.assertIn("HALL OF FAME", output)
        self.assertIn("Total Wins: 1", output)
        self.assertIn("restart", output)
        self.assertIn("challenge him again!", output)

    def test_held_item_persistence_and_display(self):
        import io
        from unittest.mock import MagicMock
        from poketokenbar.tui_tabs.companion import render as render_companion

        mon = MonState(
            base_id=4,
            path_ids=[4, 5, 6],
            planned_path_ids=[4, 5, 6],
            stage_index=0,
            used_at_stage=1000,
            rarity=Rarity.COMMON,
            total_forms=3,
            happiness=100
        )
        self.engine.set_active_mon(mon)
        self.engine._register_to_dex(mon, status="active")
        self.engine.state["inventory"]["everstone"] = 1
        ok, msg = self.engine.use_item(ItemKind.EVERSTONE)
        self.assertTrue(ok)
        self.assertEqual(self.engine.active_mon.held_item, "everstone")

        # Verify StorageManager serialization preserves held_item
        mon_dict = StorageManager.mon_to_dict(self.engine.active_mon)
        self.assertEqual(mon_dict.get("held_item"), "everstone")
        loaded_mon = StorageManager.dict_to_mon(mon_dict)
        self.assertEqual(loaded_mon.held_item, "everstone")

        # Verify Trainer Card displays held item
        card = self.engine.generate_trainer_card()
        self.assertIn("Everstone", card)

        # Verify Companion TUI tab displays held item
        app = MagicMock()
        app.engine = self.engine
        app.active_mon = self.engine.active_mon
        app.current_difficulty = self.engine.current_difficulty
        app.tracker = MagicMock()
        app.tracker.get_daily_burn_profile.return_value = {}
        
        summary = {
            "today_tokens": 100_000,
            "antigravity_today": 100_000,
            "week_tokens": 500_000,
            "month_tokens": 1_000_000,
            "total_tokens": 5_000_000,
            "burn_rate_tpm": 10_000,
            "active_days": []
        }
        stdout_trap = io.StringIO()
        with unittest.mock.patch("sys.stdout", stdout_trap):
            render_companion(app, summary)
        output = stdout_trap.getvalue()
        self.assertIn("Everstone", output)
        self.assertIn("EVERSTONE", output)

        # Test unequip
        ok_unequip, msg_unequip = self.engine.unequip_item()
        self.assertTrue(ok_unequip)
        self.assertIsNone(self.engine.active_mon.held_item)
        self.assertEqual(self.engine.state["inventory"]["everstone"], 1)

    def test_term_deposits_system(self):
        self.engine.state["used_since_install"] = 100_000_000
        initial_tokens = self.engine.available_tokens

        # Open 3-day CD with 10M
        ok, msg = self.engine.open_cd("10m", 3)
        self.assertTrue(ok)
        self.assertEqual(self.engine.available_tokens, initial_tokens - 10_000_000)
        cds = self.engine.state.get("term_deposits", [])
        self.assertEqual(len(cds), 1)
        self.assertEqual(cds[0]["principal"], 10_000_000)
        self.assertEqual(cds[0]["term_days"], 3)
        self.assertFalse(cds[0]["matured"])

        # Premature claim should fail
        ok_claim, msg_claim = self.engine.claim_cd("1")
        self.assertFalse(ok_claim)
        self.assertIn("not matured", msg_claim)

        # Early break forfeits interest and incurs 10% penalty
        ok_break, msg_break = self.engine.break_cd("1")
        self.assertTrue(ok_break)
        self.assertEqual(len(self.engine.state.get("term_deposits", [])), 0)
        self.assertEqual(self.engine.available_tokens, initial_tokens - 1_000_000)

        # Open a 7-day CD and let it mature through day rollovers
        ok, msg = self.engine.open_cd("10m", 7)
        self.assertTrue(ok)
        self.engine.state["last_active_date"] = "2026-08-01"
        self.engine.state["install_baseline_set"] = True
        
        # Advance 7 days
        self.engine.process_usage(100_000_000, ["2026-08-01", "2026-08-08"])
        cds = self.engine.state.get("term_deposits", [])
        self.assertEqual(len(cds), 1)
        self.assertTrue(cds[0]["matured"])
        self.assertGreater(cds[0]["current_value"], 10_000_000)

        # Claim matured CD
        cur_val = cds[0]["current_value"]
        before_claim = self.engine.available_tokens
        ok_claim, msg_claim = self.engine.claim_cd("all")
        self.assertTrue(ok_claim)
        self.assertEqual(len(self.engine.state.get("term_deposits", [])), 0)
        self.assertEqual(self.engine.available_tokens, before_claim + cur_val)

    def test_corporate_investments_and_perks(self):
        self.engine.state["used_since_install"] = 200_000_000

        self.assertFalse(self.engine.has_perk("silph"))
        self.assertFalse(self.engine.has_perk("devon"))

        # Buy 2 shares of Silph and 1 share of Devon using stock codes (case-insensitive)
        ok_silph, msg_silph = self.engine.invest_corporate("SILPH", "2")
        self.assertTrue(ok_silph)
        ok_devon, msg_devon = self.engine.invest_corporate("DEVON", "1")
        self.assertTrue(ok_devon)
        # Also verify ticker alias DEVN works
        ok_devn_alias, _ = self.engine.invest_corporate("DEVN", "1")
        self.assertTrue(ok_devn_alias)

        self.assertTrue(self.engine.has_perk("silph"))
        self.assertTrue(self.engine.has_perk("devon"))
        self.assertFalse(self.engine.has_perk("macro"))

        from poketokenbar.game.models import CORPORATIONS
        self.assertNotIn("Red", CORPORATIONS["macro"].perk_desc)
        self.assertNotIn("Red", CORPORATIONS["macro"].catalyst_desc)
        self.assertIn("Boss raids", CORPORATIONS["macro"].perk_desc)

        # Test Devon perk: dynamic tiered discount on Shop Rare Candy
        # With 2 shares owned (Retail tier: 1-4 shares), discount is 5%
        self.assertEqual(self.engine.get_corp_rank("devon")[1], "Retail")
        rc_base = ItemKind.RARE_CANDY.price_for(self.engine.current_difficulty)
        expected_cost_bronze = int(rc_base * 0.95)
        tokens_before_rc = self.engine.available_tokens
        ok_buy, msg_buy = self.engine.buy_item(ItemKind.RARE_CANDY, 1)
        self.assertTrue(ok_buy)
        self.assertEqual(tokens_before_rc - self.engine.available_tokens, expected_cost_bronze)

        # Reach Preferred tier (5+ shares) for 10% discount
        ok_silver, _ = self.engine.invest_corporate("DEVON", "3")
        self.assertTrue(ok_silver)
        self.assertEqual(self.engine.get_corp_rank("devon")[1], "Preferred")
        expected_cost_silver = int(rc_base * 0.90)
        tokens_before_rc2 = self.engine.available_tokens
        ok_buy2, _ = self.engine.buy_item(ItemKind.RARE_CANDY, 1)
        self.assertTrue(ok_buy2)
        self.assertEqual(tokens_before_rc2 - self.engine.available_tokens, expected_cost_silver)

        # Test Day rollover dividend payout with streak bonus
        self.engine.state["streak_days"] = 5
        self.engine.state["last_active_date"] = "2026-08-01"
        self.engine.state["install_baseline_set"] = True
        avail_before_div = self.engine.available_tokens
        self.engine.process_usage(200_000_000, ["2026-08-01", "2026-08-02"])
        self.assertGreater(self.engine.available_tokens, avail_before_div)

        # Divest 1 share of Silph using stock code (10% liquidation spread)
        silph_price = self.engine.get_or_init_stock_market()["prices"]["silph"]
        expected_payout = int(silph_price * 0.90)
        avail_before_divest = self.engine.available_tokens
        ok_divest, msg_divest = self.engine.divest_corporate("SILPH", "1")
        self.assertTrue(ok_divest)
        self.assertEqual(self.engine.available_tokens, avail_before_divest + expected_payout)
        self.assertEqual(self.engine.state["investments"]["silph"], 1)

    def test_black_market_and_held_items(self):
        from poketokenbar.game.black_market import BLACK_MARKET_POOL_100, unpack_trove, unpack_mystery_crate, get_fake_item_fraud_message
        self.assertEqual(len(BLACK_MARKET_POOL_100), 100)

        self.engine.state["used_since_install"] = 500_000_000
        bm = self.engine.get_or_init_black_market(force_open=True)
        self.assertTrue(bm["is_open"])
        self.assertEqual(len(bm["deals"]), 7)

        # Test purchasing first deal
        deal = bm["deals"][0]
        initial_stock = deal["stock"]
        ok, msg = self.engine.buy_black_market_deal(str(deal["id"]), 1)
        self.assertTrue(ok)
        self.assertEqual(deal["stock"], initial_stock - 1)

        # Test sealed troves and mystery crates unpack logic
        trove_res, reveal_names = unpack_trove({"type": "trove_stone", "qty": 3}, 1)
        self.assertEqual(sum(trove_res.values()), 3)
        self.assertEqual(len(reveal_names), 3)
        for it_key in trove_res:
            self.assertTrue(it_key.endswith("_stone"))

        crate_items, crate_tokens, crate_egg, crate_msg = unpack_mystery_crate("rocket_black_box")
        self.assertTrue(len(crate_msg) > 0)

        # Test counterfeit items fraud message and usage
        self.engine.state["inventory"]["fake_rare_candy"] = 2
        ok_fake, msg_fake = self.engine.use_item("fake_rare_candy", 1)
        self.assertTrue(ok_fake)
        self.assertIn("SCAM REVEALED", msg_fake)
        self.assertIn("rock candy", msg_fake.lower())
        self.assertEqual(self.engine.state["inventory"].get("fake_rare_candy"), 1)

        # Test selling counterfeit item (should yield 1 token each)
        avail_before_sell = self.engine.available_tokens
        ok_sell, msg_sell = self.engine.sell_item("fake_rare_candy", 1)
        self.assertTrue(ok_sell)
        self.assertIn("+1 Token", msg_sell)
        self.assertEqual(self.engine.available_tokens, avail_before_sell + 1)
        self.assertNotIn("fake_rare_candy", self.engine.state["inventory"])

        # Test equipping new held items
        mon, _ = self.engine.hatch_egg(0)
        self.engine.state["inventory"]["choice_band"] = 1
        ok_band, msg_band = self.engine.use_item(ItemKind.CHOICE_BAND)
        self.assertTrue(ok_band)
        self.assertEqual(self.engine.active_mon.held_item, "choice_band")

        # Test Choice Band damage boost in boss battle
        self.engine.state["active_boss"] = {
            "id": "boss_1",
            "name": "Brock & Geodude",
            "sp_id": 74,
            "badge": "🪨 Boulder Badge",
            "current_hp": 100_000,
            "hp": 100_000,
            "reward": "rare_candy"
        }
        self.engine._update_boss_battle(10_000)
        # Normal base damage = 10,000; with Choice Band (+50%) = 15,000 -> 85,000 HP remaining
        self.assertEqual(self.engine.state["active_boss"]["current_hp"], 85_000)

        # Test Choice Specs SpAtk boost against Boss
        self.engine.state["inventory"]["choice_specs"] = 1
        ok_specs, msg_specs = self.engine.use_item(ItemKind.CHOICE_SPECS)
        self.assertTrue(ok_specs)
        self.assertEqual(self.engine.active_mon.held_item, "choice_specs")
        self.engine._update_boss_battle(10_000)
        self.assertEqual(self.engine.state["active_boss"]["current_hp"], 70_000)

    def test_72_column_layout_compliance(self):
        import io
        import re
        from unittest.mock import MagicMock
        from poketokenbar.tui_tabs.bank import render_bank_tab
        from poketokenbar.tui_tabs.shop import render_shop_tab

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')

        app = MagicMock()
        app.engine = self.engine
        app.engine.state["used_since_install"] = 200_000_000
        app.engine.open_cd("10m", 3)
        app.engine.invest_corporate("SILPH", "2")
        app.engine.invest_corporate("MAUV", "1")

        # Test Bank Checking
        app.bank_subtab = "checking"
        trap = io.StringIO()
        with unittest.mock.patch("sys.stdout", trap):
            render_bank_tab(app)
        checking_output = trap.getvalue()
        self.assertNotIn("c' for Term Deposits", checking_output)
        for line in checking_output.split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Bank Checking line exceeds 72 cols: '{clean}' (len={len(clean)})")

        # Test Bank CD
        app.bank_subtab = "cd"
        trap = io.StringIO()
        with unittest.mock.patch("sys.stdout", trap):
            render_bank_tab(app)
        cd_output = trap.getvalue()
        self.assertNotIn("b' for Checking", cd_output)
        for line in cd_output.split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Bank CD line exceeds 72 cols: '{clean}' (len={len(clean)})")

        # Test Bank Stocks (Page 1)
        app.bank_subtab = "stocks"
        app.stock_page = 1
        trap = io.StringIO()
        with unittest.mock.patch("sys.stdout", trap):
            render_bank_tab(app)
        stocks_p1_output = trap.getvalue()
        self.assertNotIn("b' for Checking", stocks_p1_output)
        self.assertIn("Page 1/2", stocks_p1_output)
        for line in stocks_p1_output.split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Bank Stocks P1 line exceeds 72 cols: '{clean}' (len={len(clean)})")

        # Test Bank Stocks (Page 2)
        app.stock_page = 2
        trap = io.StringIO()
        with unittest.mock.patch("sys.stdout", trap):
            render_bank_tab(app)
        stocks_p2_output = trap.getvalue()
        self.assertIn("Page 2/2", stocks_p2_output)
        for line in stocks_p2_output.split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Bank Stocks P2 line exceeds 72 cols: '{clean}' (len={len(clean)})")

        # Test Shop Normal
        app.shop_view = "normal"
        app.shop_page = 1
        trap = io.StringIO()
        with unittest.mock.patch("sys.stdout", trap):
            render_shop_tab(app)
        for line in trap.getvalue().split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Shop Normal line exceeds 72 cols: '{clean}' (len={len(clean)})")

        # Test Shop Black Market across all 100 contraband pool items
        from poketokenbar.game.black_market import BLACK_MARKET_POOL_100
        import copy
        app.shop_view = "black_market"
        for i in range(0, len(BLACK_MARKET_POOL_100), 7):
            chunk = BLACK_MARKET_POOL_100[i:i+7]
            bm_test_deals = []
            for didx, item in enumerate(chunk, 1):
                d = copy.deepcopy(item)
                d["id"] = didx
                bm_test_deals.append(d)
            app.engine.state["black_market"]["deals"] = bm_test_deals
            trap = io.StringIO()
            with unittest.mock.patch("sys.stdout", trap):
                render_shop_tab(app)
            for line in trap.getvalue().split("\n"):
                clean = ansi_regex.sub("", line)
                self.assertLessEqual(len(clean), 72, f"Shop Black Market line exceeds 72 cols: '{clean}' (len={len(clean)})")

    def test_stock_market_initialization_and_details(self):
        sm = self.engine.get_or_init_stock_market()
        self.assertIn("prices", sm)
        self.assertIn("price_history", sm)
        self.assertIn("cost_basis", sm)
        self.assertIn("latest_news", sm)
        self.assertIn("daily_catalysts", sm)
        self.assertIn("market_headline", sm)

        for corp in ["silph", "devon", "aether", "mauville", "macro"]:
            self.assertIn(corp, sm["prices"])
            self.assertGreaterEqual(sm["prices"][corp], 1_000_000)
            self.assertEqual(len(sm["price_history"][corp]), 1)

        details = self.engine.get_stock_details("SILPH")
        self.assertIsNotNone(details)
        self.assertEqual(details["key"], "silph")
        self.assertEqual(details["current_price"], 10_000_000)
        self.assertEqual(details["owned"], 0)
        self.assertEqual(details["cost_basis"], 0)

        # Test ticker and alias resolution
        self.assertEqual(self.engine._resolve_corp_key("slph"), "silph")
        self.assertEqual(self.engine._resolve_corp_key("devn"), "devon")
        self.assertEqual(self.engine._resolve_corp_key("athr"), "aether")

    def test_stock_cost_basis_and_pnl_analytics(self):
        self.engine.state["used_since_install"] = 500_000_000
        self.engine.state["spent_tokens"] = 0

        # Buy 2 shares of Devon at 10M each -> 20M cost basis
        ok, msg = self.engine.invest_corporate("DEVON", "2")
        self.assertTrue(ok)
        details = self.engine.get_stock_details("DEVON")
        self.assertEqual(details["owned"], 2)
        self.assertEqual(details["cost_basis"], 20_000_000)
        self.assertEqual(details["avg_cost"], 10_000_000)

        # Manually alter Devon price to simulate market shift to 14M
        sm = self.engine.get_or_init_stock_market()
        sm["prices"]["devon"] = 14_000_000
        details = self.engine.get_stock_details("DEVON")
        self.assertEqual(details["market_val"], 28_000_000)
        self.assertEqual(details["liq_val"], int(28_000_000 * 0.90)) # 25.2M
        # Unrealized P&L = liq_val - cost_basis = 25.2M - 20M = 5.2M
        self.assertEqual(details["unrealized_pnl"], 5_200_000)

        # Buy 1 more share at 14M -> total cost basis 34M, 3 shares -> avg cost 11.33M
        ok, msg = self.engine.invest_corporate("DEVON", "1")
        self.assertTrue(ok)
        details = self.engine.get_stock_details("DEVON")
        self.assertEqual(details["owned"], 3)
        self.assertEqual(details["cost_basis"], 34_000_000)
        self.assertEqual(details["avg_cost"], 34_000_000 // 3)

        # Sell 1 share at 14M: gross 14M, payout = 12.6M (10% spread)
        # Cost of sold = 1 * (34M // 3) = 11,333,333
        # Realized P&L = 12,600,000 - 11,333,333 = +1,266,667
        avail_before = self.engine.available_tokens
        ok, msg = self.engine.divest_corporate("DEVON", "1")
        self.assertTrue(ok)
        self.assertEqual(self.engine.available_tokens, avail_before + 12_600_000)
        self.assertIn("P&L: +1.2M", msg)

        # Sell remaining 2 shares -> cost_basis resets to 0
        ok, msg = self.engine.divest_corporate("DEVON", "all")
        self.assertTrue(ok)
        details = self.engine.get_stock_details("DEVON")
        self.assertEqual(details["owned"], 0)
        self.assertEqual(details["cost_basis"], 0)
        self.assertEqual(details["avg_cost"], 0)

    def test_player_action_catalysts_and_burn_rollover(self):
        self.engine.state["used_since_install"] = 500_000_000
        self.engine.state["spent_tokens"] = 0
        sm = self.engine.get_or_init_stock_market()

        # Simulate actions to record catalysts
        self.engine._record_catalyst("expeditions_completed", 2) # Silph boost
        self.engine._record_catalyst("shop_tokens_spent", 15_000_000) # Devon boost
        self.engine._record_catalyst("casino_net_pnl", -5_000_000) # Mauville house win boost
        self.engine._record_catalyst("bosses_defeated", 1) # Macro Cosmos boost

        # Set burned today tokens > 500k for heavy burn momentum
        self.engine.state["tokens_burned_today"] = 2_000_000
        silph_price_before = sm["prices"]["silph"]

        events = []
        self.engine._rollover_stock_market(days_to_apply=1, diff=1, current_streak=5, events=events)

        # Catalysts should be reset
        cats = sm["daily_catalysts"]
        self.assertEqual(cats["expeditions_completed"], 0)
        self.assertEqual(cats["shop_tokens_spent"], 0)
        self.assertEqual(cats["casino_net_pnl"], 0)
        self.assertEqual(cats["bosses_defeated"], 0)

        # Price history should have 2 entries now
        self.assertEqual(len(sm["price_history"]["silph"]), 2)
        # All prices should respect price floor
        for corp, price in sm["prices"].items():
            self.assertGreaterEqual(price, 1_000_000)

        # Market headline and latest news should be populated
        self.assertTrue(len(sm["market_headline"]) > 0)
        for corp, news in sm["latest_news"].items():
            self.assertTrue(len(news) > 0)

    def test_stock_trade_terminal_and_72_col_compliance(self):
        import io
        import re
        from unittest.mock import MagicMock
        from poketokenbar.tui_tabs.bank import render_bank_tab

        ansi_regex = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        app = MagicMock()
        app.engine = self.engine
        app.bank_subtab = "stocks"

        for corp_key in ["silph", "devon", "aether", "mauville", "macro", "viridian"]:
            app.stock_terminal = corp_key
            trap = io.StringIO()
            with unittest.mock.patch("sys.stdout", trap):
                render_bank_tab(app)
            out = trap.getvalue()
            self.assertIn("Position:", out)
            self.assertIn("Shareholder Rank & Perk Progression:", out)
            for line in out.split("\n"):
                clean = ansi_regex.sub("", line)
                self.assertLessEqual(len(clean), 72, f"Trade Terminal '{corp_key}' line exceeds 72 cols: '{clean}' (len={len(clean)})")

    def test_shareholder_tier_rank_thresholds(self):
        from poketokenbar.game.models import get_shareholder_rank, SHAREHOLDER_TIERS
        # Boundary tests
        self.assertEqual(get_shareholder_rank(0), (0, "None"))
        self.assertEqual(get_shareholder_rank(1), (1, "Retail"))
        self.assertEqual(get_shareholder_rank(4), (1, "Retail"))
        self.assertEqual(get_shareholder_rank(5), (2, "Preferred"))
        self.assertEqual(get_shareholder_rank(14), (2, "Preferred"))
        self.assertEqual(get_shareholder_rank(15), (3, "Strategic"))
        self.assertEqual(get_shareholder_rank(29), (3, "Strategic"))
        self.assertEqual(get_shareholder_rank(30), (4, "Majority"))
        self.assertEqual(get_shareholder_rank(100), (4, "Majority"))
        self.assertEqual(len(SHAREHOLDER_TIERS), 5)

    def test_shareholder_perk_multipliers(self):
        self.engine.state["investments"] = {
            "silph": 0, "devon": 0, "aether": 0, "mauville": 0, "macro": 0, "viridian": 0
        }
        # Rank 0 (None)
        self.assertEqual(self.engine.get_silph_multipliers(), (1.0, 1.0))
        self.assertEqual(self.engine.get_devon_multiplier(), 1.0)
        self.assertEqual(self.engine.get_devon_discount_pct(), 0)
        self.assertEqual(self.engine.get_aether_perks(), (1.0, 0))
        self.assertEqual(self.engine.get_mauville_multiplier(), 1.0)
        self.assertEqual(self.engine.get_macro_multiplier(), 1.0)
        self.assertEqual(self.engine.get_viridian_dividend_bonus(), 0.0)

        # Rank 1 (Retail: 1-4 shares)
        self.engine.state["investments"]["silph"] = 2
        self.engine.state["investments"]["devon"] = 4
        self.engine.state["investments"]["aether"] = 1
        self.engine.state["investments"]["mauville"] = 3
        self.engine.state["investments"]["macro"] = 2
        self.engine.state["investments"]["viridian"] = 4
        self.assertEqual(self.engine.get_silph_multipliers(), (1.10, 1.10))
        self.assertEqual(self.engine.get_devon_multiplier(), 0.95)
        self.assertEqual(self.engine.get_devon_discount_pct(), 5)
        self.assertEqual(self.engine.get_aether_perks(), (1.5, 3))
        self.assertEqual(self.engine.get_mauville_multiplier(), 1.05)
        self.assertEqual(self.engine.get_macro_multiplier(), 1.10)
        self.assertEqual(self.engine.get_viridian_dividend_bonus(), 0.005)

        # Rank 2 (Preferred: 5-14 shares)
        self.engine.state["investments"] = {k: 5 for k in self.engine.state["investments"]}
        self.assertEqual(self.engine.get_silph_multipliers(), (1.15, 1.15))
        self.assertEqual(self.engine.get_devon_multiplier(), 0.90)
        self.assertEqual(self.engine.get_devon_discount_pct(), 10)
        self.assertEqual(self.engine.get_aether_perks(), (2.0, 5))
        self.assertEqual(self.engine.get_mauville_multiplier(), 1.10)
        self.assertEqual(self.engine.get_macro_multiplier(), 1.20)
        self.assertEqual(self.engine.get_viridian_dividend_bonus(), 0.010)

        # Rank 3 (Strategic: 15-29 shares)
        self.engine.state["investments"] = {k: 20 for k in self.engine.state["investments"]}
        self.assertEqual(self.engine.get_silph_multipliers(), (1.20, 1.20))
        self.assertEqual(self.engine.get_devon_multiplier(), 0.85)
        self.assertEqual(self.engine.get_devon_discount_pct(), 15)
        self.assertEqual(self.engine.get_aether_perks(), (2.5, 8))
        self.assertEqual(self.engine.get_mauville_multiplier(), 1.15)
        self.assertEqual(self.engine.get_macro_multiplier(), 1.30)
        self.assertEqual(self.engine.get_viridian_dividend_bonus(), 0.015)

        # Rank 4 (Majority: 30+ shares)
        self.engine.state["investments"] = {k: 35 for k in self.engine.state["investments"]}
        self.assertEqual(self.engine.get_silph_multipliers(), (1.25, 1.25))
        self.assertEqual(self.engine.get_devon_multiplier(), 0.80)
        self.assertEqual(self.engine.get_devon_discount_pct(), 20)
        self.assertEqual(self.engine.get_aether_perks(), (3.0, 12))
        self.assertEqual(self.engine.get_mauville_multiplier(), 1.20)
        self.assertEqual(self.engine.get_macro_multiplier(), 1.40)
        self.assertEqual(self.engine.get_viridian_dividend_bonus(), 0.020)

    def test_stock_trade_terminal_progression_and_72_col_compliance(self):
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.bank import _render_stock_terminal

        ansi_regex = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        app = MagicMock()
        app.engine = self.engine

        # Test each corporation across all 5 ranks (0, 2, 7, 20, 35 shares)
        for corp_key in ["silph", "devon", "aether", "mauville", "macro", "viridian"]:
            for share_count in [0, 2, 7, 20, 35]:
                self.engine.state["investments"][corp_key] = share_count
                trap = io.StringIO()
                with patch("sys.stdout", trap):
                    _render_stock_terminal(app, avail=100_000_000, corp_key=corp_key)
                out = trap.getvalue()
                self.assertIn("Shareholder Rank & Perk Progression:", out)
                self.assertIn("Rank Tiers:", out)
                if share_count > 0:
                    self.assertIn("◄ ACTIVE", out)
                else:
                    self.assertIn("Current Status: None (0 shares)", ansi_regex.sub("", out))
                for line in out.split("\n"):
                    clean = ansi_regex.sub("", line)
                    self.assertLessEqual(len(clean), 72, f"Terminal [{corp_key}, {share_count} sh] exceeds 72 cols: '{clean}' (len={len(clean)})")

    def test_stock_tui_interactive_commands(self):
        import io
        from unittest.mock import patch, MagicMock
        from poketokenbar.tui import PokeTokenBarTUI

        with patch("poketokenbar.tui.UsageManager") as mock_mgr:
            instance = MagicMock()
            instance.get_summary.return_value = {
                "total_tokens": 500_000_000,
                "today_tokens": 0,
                "week_tokens": 0,
                "month_tokens": 0,
                "antigravity_today": 0,
                "gemini_today": 0,
                "claude_today": 0,
                "burn_rate_tpm": 0,
                "active_days": []
            }
            mock_mgr.return_value = instance

            tui = PokeTokenBarTUI()
            tui.engine = self.engine
            tui.engine.state["used_since_install"] = 500_000_000
            tui.engine.state["spent_tokens"] = 0

            # Navigate to Bank -> Stocks -> Open Silph via 'stock 1' -> Buy 1 -> Sell 1 -> Back -> Open Devon via 'stock DEVON' -> Buy 1 -> Back -> Quit
            commands = "\n".join(["10", "s", "stock 1", "buy 1", "sell 1", "back", "stock DEVON", "buy 1", "back", "q"]) + "\n"
            with patch("sys.stdin", io.StringIO(commands)), patch("sys.stdout"):
                tui.run()

            self.assertEqual(tui.engine.state["investments"]["devon"], 1)
            self.assertEqual(tui.engine.state["investments"]["silph"], 0)
            self.assertIsNone(tui.stock_terminal)

            # Test that typing '1'..'5' in stock menu switches tabs instead of opening terminal
            tui_nav = PokeTokenBarTUI()
            tui_nav.engine = self.engine
            commands_nav = "\n".join(["10", "s", "2", "q"]) + "\n"
            with patch("sys.stdin", io.StringIO(commands_nav)), patch("sys.stdout"):
                tui_nav.run()
            self.assertEqual(tui_nav.current_tab, 2)
            self.assertIsNone(tui_nav.stock_terminal)

    def test_expedition_multi_selection_and_interactive_picker(self):
        """Verify interactive multi-select picker and staged expedition dispatching."""
        from poketokenbar.tui import PokeTokenBarTUI
        from poketokenbar.tui_tabs.expeditions import render_expedition_picker
        import io
        from unittest.mock import patch, MagicMock

        # Setup 4 companions in dex
        for sp in [4, 7, 1, 25]:
            mon = MonState(
                base_id=sp,
                path_ids=[sp],
                planned_path_ids=[sp],
                stage_index=0,
                used_at_stage=1000,
                rarity=Rarity.COMMON,
                total_forms=1,
                happiness=100
            )
            self.engine._register_to_dex(mon, status="inactive")

        with patch("poketokenbar.tui.UsageManager") as mock_mgr:
            instance = MagicMock()
            instance.get_summary.return_value = {
                "total_tokens": 100_000_000,
                "today_tokens": 0, "week_tokens": 0, "month_tokens": 0,
                "antigravity_today": 0, "gemini_today": 0, "claude_today": 0,
                "burn_rate_tpm": 0, "active_days": []
            }
            mock_mgr.return_value = instance

            tui = PokeTokenBarTUI()
            tui.engine = self.engine

            # 1. Test _parse_indices_string
            self.assertEqual(tui._parse_indices_string("1,2,3"), [1, 2, 3])
            self.assertEqual(tui._parse_indices_string("1 2 4"), [1, 2, 4])
            self.assertEqual(tui._parse_indices_string("1-3"), [1, 2, 3])
            self.assertEqual(tui._parse_indices_string("#25"), [4])
            self.assertEqual(tui._parse_indices_string("all"), [1, 2, 3, 4])

            # 2. Test _toggle_selection_indices
            tui._toggle_selection_indices([1, 2])
            self.assertEqual(tui.selected_expedition_targets, {1, 2})
            # Toggling 1 removes it
            tui._toggle_selection_indices([1])
            self.assertEqual(tui.selected_expedition_targets, {2})
            # Toggling 1 re-adds it
            tui._toggle_selection_indices([1])
            self.assertEqual(tui.selected_expedition_targets, {1, 2})

            # 3. Test render_expedition_picker
            out = io.StringIO()
            with patch("sys.stdout", out):
                render_expedition_picker(tui)
            rendered = out.getvalue()
            self.assertIn("Expedition Dispatcher", rendered)
            self.assertIn("Charmander", rendered)

            # 4. Test staged expedition dispatch via TUI loop ('send mine')
            # 2 companions are selected: #1 Charmander, #2 Squirtle
            commands = "\n".join(["send mine", "q"]) + "\n"
            with patch("sys.stdin", io.StringIO(commands)), patch("sys.stdout"):
                tui.run()

            exps = self.engine.state.get("expeditions", [])
            self.assertEqual(len(exps), 2)
            self.assertEqual(exps[0]["area"], "Evolution Mine")
            self.assertEqual(exps[1]["area"], "Evolution Mine")
            # Selection should be cleared after dispatch
            self.assertEqual(len(tui.selected_expedition_targets), 0)

            # 5. Test Interactive Picker Mode via 'pick'
            # Dispatch Bulbasaur (#3 in roster) and Pikachu (#4 in roster) to Viridian via picker
            tui2 = PokeTokenBarTUI()
            tui2.engine = self.engine
            commands2 = "\n".join(["5", "pick", "3 4", "viridian", "q"]) + "\n"
            with patch("sys.stdin", io.StringIO(commands2)), patch("sys.stdout"):
                tui2.run()

            exps = self.engine.state.get("expeditions", [])
            self.assertEqual(len(exps), 4)
            self.assertEqual(exps[2]["area"], "Viridian Forest")
            self.assertEqual(exps[3]["area"], "Viridian Forest")

            # 6. Test 'back' in picker mode exits picker mode back to Tab 5, then 'q' exits game
            tui3 = PokeTokenBarTUI()
            tui3.engine = self.engine
            commands3 = "\n".join(["5", "pick", "back", "q"]) + "\n"
            with patch("sys.stdin", io.StringIO(commands3)), patch("sys.stdout"):
                tui3.run()
            self.assertFalse(tui3.expedition_picker_mode)
            self.assertEqual(tui3.current_tab, 5)

            # 7. Test 'q' in picker mode directly terminates app (universal exit)
            tui4 = PokeTokenBarTUI()
            tui4.engine = self.engine
            commands4 = "\n".join(["5", "pick", "q"]) + "\n"
            with patch("sys.stdin", io.StringIO(commands4)), patch("sys.stdout"):
                tui4.run()

    def test_black_market_5pct_daily_chance_and_poster_grunt_bribe(self):
        """Verify 5% daily chance, daily bribe randomized in [1M..5M], and Game Corner poster bribe access."""
        from poketokenbar.tui import PokeTokenBarTUI
        from poketokenbar.tui_tabs.game_corner import render_grunt_bribe_tab
        from unittest.mock import patch, MagicMock
        import io
        import re

        # 1. Verify bribe amount is valid
        bribe = self.engine.get_daily_grunt_bribe()
        self.assertIn(bribe, [1_000_000, 2_000_000, 3_000_000, 4_000_000, 5_000_000])

        # 2. Test bribe failure when not enough tokens
        self.engine.state["used_since_install"] = 0
        self.engine.state["spent_tokens"] = 0
        ok, msg = self.engine.bribe_grunt_for_black_market()
        self.assertFalse(ok)
        self.assertIn("don't have enough tokens", msg)

        # 3. Test bribe success when player has enough tokens
        self.engine.state["used_since_install"] = 20_000_000
        prev_spent = self.engine.state["spent_tokens"]
        ok, msg = self.engine.bribe_grunt_for_black_market()
        self.assertTrue(ok)
        self.assertEqual(self.engine.state["spent_tokens"], prev_spent + bribe)
        self.assertTrue(self.engine.state["black_market"]["is_open"])

        # 4. Verify 72-column formatting of grunt bribe view
        app = PokeTokenBarTUI()
        app.engine = self.engine
        app.minigame_state = "grunt_bribe"
        trap = io.StringIO()
        with patch("sys.stdout", trap):
            render_grunt_bribe_tab(app)
        ansi_regex = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
        for line in trap.getvalue().split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Grunt bribe line exceeds 72 cols: '{clean}'")

        # 5. Test TUI flow: Tab 9 -> Slots ('play 3') -> 'poster' -> 'back' -> 'poster' -> 'bribe'
        self.engine.state["used_since_install"] = 50_000_000
        self.engine.state["spent_tokens"] = 0
        self.engine.state["black_market"]["is_open"] = False

        with patch("poketokenbar.tui.UsageManager") as mock_mgr:
            instance = MagicMock()
            instance.get_summary.return_value = {
                "total_tokens": 50_000_000, "today_tokens": 0, "week_tokens": 0,
                "month_tokens": 0, "antigravity_today": 0, "gemini_today": 0,
                "claude_today": 0, "burn_rate_tpm": 0, "active_days": []
            }
            mock_mgr.return_value = instance

            tui = PokeTokenBarTUI()
            tui.engine = self.engine
            commands = "\n".join(["9", "play 3", "poster", "back", "poster", "bribe", "back", "q"]) + "\n"
            with patch("sys.stdin", io.StringIO(commands)), patch("sys.stdout"):
                tui.run()

            # Should have successfully unlocked and opened black market session, but natural_open remains False
            self.assertTrue(self.engine.state["black_market"]["is_open"])
            self.assertFalse(self.engine.state["black_market"].get("natural_open", False))

            # 6. Test Mart Tab 4 door is bolted when natural_open is False and no session
            tui5 = PokeTokenBarTUI()
            tui5.engine = self.engine
            commands5 = "\n".join(["4", "black", "q"]) + "\n"
            trap5 = io.StringIO()
            with patch("sys.stdin", io.StringIO(commands5)), patch("sys.stdout", trap5):
                tui5.run()
            self.assertIn("The back alley door is bolted shut from the inside.", trap5.getvalue())
            self.assertEqual(getattr(tui5, "shop_view", "normal"), "normal")

            # 7. When natural_open is True, Tab 4 alley door opens
            self.engine.state["black_market"]["natural_open"] = True
            tui6 = PokeTokenBarTUI()
            tui6.engine = self.engine
            commands6 = "\n".join(["4", "black", "q"]) + "\n"
            with patch("sys.stdin", io.StringIO(commands6)), patch("sys.stdout"):
                tui6.run()
            self.assertEqual(tui6.shop_view, "black_market")

            # 8. When permanent_black_market is True, 'poster' in Slots enters Black Market directly without bribe
            self.engine.state["permanent_black_market"] = True
            self.engine.state["spent_tokens"] = 1000
            tui7 = PokeTokenBarTUI()
            tui7.engine = self.engine
            commands7 = "\n".join(["9", "play 3", "poster", "q"]) + "\n"
            trap7 = io.StringIO()
            with patch("sys.stdin", io.StringIO(commands7)), patch("sys.stdout", trap7):
                tui7.run()
            # Directly transitions to Tab 4 Black Market with 0 bribe deducted
            self.assertEqual(tui7.current_tab, 4)
            self.assertEqual(tui7.shop_view, "black_market")
            self.assertEqual(self.engine.state["spent_tokens"], 1000)
            self.assertIn("Syndicate Black Pass recognized", trap7.getvalue())

            # 9. Test slot alias and entering with pass
            tui8 = PokeTokenBarTUI()
            tui8.engine = self.engine
            commands8 = "\n".join(["9", "slot", "poster", "q"]) + "\n"
            trap8 = io.StringIO()
            with patch("sys.stdin", io.StringIO(commands8)), patch("sys.stdout", trap8):
                tui8.run()
            self.assertEqual(tui8.current_tab, 4)
            self.assertEqual(tui8.shop_view, "black_market")

            # 10. Verify render_grunt_bribe_tab does not display "Bribe Demanded" when pass is owned
            from poketokenbar.tui_tabs.game_corner import render_grunt_bribe_tab
            app_mock = MagicMock()
            app_mock.engine = self.engine
            trap_bribe = io.StringIO()
            with patch("sys.stdout", trap_bribe):
                render_grunt_bribe_tab(app_mock)
            bribe_out = trap_bribe.getvalue()
            self.assertNotIn("Bribe Demanded", bribe_out)
            self.assertIn("Access Clearance", bribe_out)
            self.assertIn("WAIVED", bribe_out)

    def test_viridian_stock_market_and_perk(self):
        from poketokenbar.game.models import CORPORATIONS
        self.assertIn("viridian", CORPORATIONS)
        corp = CORPORATIONS["viridian"]
        self.assertEqual(corp.ticker, "VRDN")
        self.assertEqual(corp.share_price, 25_000_000)

        # Check alias resolution
        self.assertEqual(self.engine._resolve_corp_key("vrdn"), "viridian")
        self.assertEqual(self.engine._resolve_corp_key("virg"), "viridian")
        self.assertEqual(self.engine._resolve_corp_key("VRDN"), "viridian")

        # Invest in VRDN
        self.engine.state["used_since_install"] = 100_000_000
        self.engine.state["spent_tokens"] = 0
        ok, msg = self.engine.invest_corporate("VRDN", "2")
        self.assertTrue(ok)
        self.assertEqual(self.engine.state["investments"]["viridian"], 2)

    def test_rocket_story_unlock_prerequisites_500m_holding(self):
        # Case A: Red badge present, but 0 VRDN shares
        self.engine.state["gym_badges"] = ["👑 Master of Masters"]
        self.engine.state["investments"]["viridian"] = 0
        unlocked, _ = self.engine.check_rocket_story_unlock()
        self.assertFalse(unlocked)
        self.assertFalse(self.engine.state.get("rocket_story_unlocked", False))

        # Case B: No Red badge, but 20 VRDN shares (500M holding value)
        self.engine.state["gym_badges"] = []
        self.engine.state["investments"]["viridian"] = 20
        unlocked, _ = self.engine.check_rocket_story_unlock()
        self.assertFalse(unlocked)
        self.assertFalse(self.engine.state.get("rocket_story_unlocked", False))

        # Case C: Red badge present, but 19 shares (475M holding value < 500M)
        self.engine.state["gym_badges"] = ["👑 Master of Masters"]
        self.engine.state["investments"]["viridian"] = 19
        unlocked, _ = self.engine.check_rocket_story_unlock()
        self.assertFalse(unlocked)
        self.assertFalse(self.engine.state.get("rocket_story_unlocked", False))

        # Case D: Red badge present AND 20 shares (500M holding value) -> UNLOCK!
        self.engine.state["investments"]["viridian"] = 20
        unlocked, alert_msg = self.engine.check_rocket_story_unlock()
        self.assertTrue(unlocked)
        self.assertTrue(self.engine.state["rocket_story_unlocked"])
        self.assertFalse(self.engine.state["rocket_story_viewed"])
        self.assertIn("Commander Petrel", alert_msg)

    def test_tab_12_hidden_until_unlocked(self):
        from poketokenbar.tui import PokeTokenBarTUI
        import io
        from unittest.mock import patch

        tui = PokeTokenBarTUI()
        tui.engine = self.engine

        # 1. Before unlock: Tab 12 is NOT rendered
        self.engine.state["rocket_story_unlocked"] = False
        trap = io.StringIO()
        with patch("sys.stdout", trap):
            tui.render_tabs()
        output = trap.getvalue()
        self.assertNotIn("Rocket HQ", output)
        self.assertNotIn("[12]", output)

        # 2. After unlock before alliance accepted: Tab 12 is rendered as [12] Secure Comm
        self.engine.state["rocket_story_unlocked"] = True
        self.engine.state["rocket_alliance_accepted"] = False
        trap2 = io.StringIO()
        with patch("sys.stdout", trap2):
            tui.render_tabs()
        output2 = trap2.getvalue()
        self.assertIn("[12] Secure Comm", output2)

        # 3. After alliance accepted: Tab 12 is rendered as [12] Rocket HQ
        self.engine.state["rocket_alliance_accepted"] = True
        trap3 = io.StringIO()
        with patch("sys.stdout", trap3):
            tui.render_tabs()
        output3 = trap3.getvalue()
        self.assertIn("[12] Rocket HQ", output3)

    def test_rocket_interactive_transmission_and_dormant_channel(self):
        import io
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.rocket import render_rocket_transmission, handle_rocket_command

        app = MagicMock()
        app.engine = self.engine

        # Scenario A: Accept immediately (choice 1)
        self.engine.state["rocket_story_viewed"] = False
        self.engine.state["rocket_alliance_accepted"] = False
        with patch("sys.stdout", io.StringIO()), patch("sys.stdin.readline", side_effect=["1\n"]):
            render_rocket_transmission(app)
        self.assertTrue(self.engine.state["rocket_story_viewed"])
        self.assertTrue(self.engine.state["rocket_alliance_accepted"])

        # Scenario B: Demand proof (choice 2) then accept (choice 1)
        self.engine.state["rocket_story_viewed"] = False
        self.engine.state["rocket_alliance_accepted"] = False
        with patch("sys.stdout", io.StringIO()), patch("sys.stdin.readline", side_effect=["2\n", "1\n"]):
            render_rocket_transmission(app)
        self.assertTrue(self.engine.state["rocket_story_viewed"])
        self.assertTrue(self.engine.state["rocket_alliance_accepted"])

        # Scenario C: Decline (choice 3), then refuse again (choice 2) -> sets dormant fallback
        self.engine.state["rocket_story_viewed"] = False
        self.engine.state["rocket_alliance_accepted"] = False
        with patch("sys.stdout", io.StringIO()), patch("sys.stdin.readline", side_effect=["3\n", "2\n", "\n"]):
            render_rocket_transmission(app)
        self.assertTrue(self.engine.state["rocket_story_viewed"])
        self.assertFalse(self.engine.state["rocket_alliance_accepted"])

        # Dormant channel rejects command '1' (reserved for tab switching)
        handle_rocket_command(app, "1")
        self.assertFalse(self.engine.state["rocket_alliance_accepted"])

        # Dormant channel accepts command 'accept'
        handle_rocket_command(app, "accept")
        self.assertTrue(self.engine.state["rocket_alliance_accepted"])

    def test_rocket_operations_and_boss_progression(self):
        self.engine.state["used_since_install"] = 500_000_000
        self.engine.state["spent_tokens"] = 0
        self.engine.state["rocket_alliance_accepted"] = True

        ops = self.engine.get_rocket_operations()
        self.assertEqual(len(ops), 10)
        self.assertEqual(ops[0]["status"], "available")
        self.assertEqual(ops[1]["status"], "locked")

        # Op 1: Start and test objective check
        ok_start, _ = self.engine.start_rocket_operation("1")
        self.assertTrue(ok_start)
        self.engine.state["rocket_ops"]["op_1"]["expeditions_done"] = 2
        events = []
        self.engine._update_rocket_operations(5_000_000, events)
        ok_claim, msg_claim = self.engine.claim_rocket_operation("1")
        self.assertTrue(ok_claim)
        self.assertEqual(self.engine.state["rocket_reputation"], 1)

        # Op 2: Requires 2 battle wins
        self.engine.state["rocket_ops"]["op_2"]["battle_wins"] = 2
        ok_start2, _ = self.engine.start_rocket_operation("2")
        self.assertTrue(ok_start2)
        self.engine._update_rocket_operations(10_000_000, events)
        ok_claim2, _ = self.engine.claim_rocket_operation("2")
        self.assertTrue(ok_claim2)
        self.assertEqual(self.engine.state["rocket_reputation"], 2)
        self.assertEqual(self.engine.state["rocket_rank"], "Operative")

        # Op 3: Boss 1 (Prototype Chimera-001)
        ok_start3, _ = self.engine.start_rocket_operation("3")
        self.assertTrue(ok_start3)
        # Cannot claim while boss is alive
        ok_premature, _ = self.engine.claim_rocket_operation("3")
        self.assertFalse(ok_premature)
        # Attack boss
        ok_atk, msg_atk = self.engine.attack_rocket_boss(burst=False)
        self.assertTrue(ok_atk)
        # Burst attack with tokens
        ok_burst, msg_burst = self.engine.attack_rocket_boss(burst=True)
        self.assertTrue(ok_burst)
        # Defeat boss
        self.engine.state["rocket_battle_state"] = {"status": "win", "op_code": "3"}
        self.engine.state["rocket_ops"]["op_3"]["boss_hp_remaining"] = 0
        ok_claim3, msg_claim3 = self.engine.claim_rocket_operation("3")
        self.assertTrue(ok_claim3)

        # Test Dossiers 1-3 unlocked
        dossier = self.engine.get_rocket_dossier()
        self.assertEqual(len(dossier), 10)
        self.assertTrue(dossier[0]["unlocked"])
        self.assertTrue(dossier[1]["unlocked"])
        self.assertTrue(dossier[2]["unlocked"])

        # Test Final Op 10 Climax Unlocks
        self.engine.state["rocket_ops"]["op_10"]["status"] = "available"
        self.engine.start_rocket_operation("10")
        self.engine.state["rocket_battle_state"] = {"status": "win", "op_code": "10"}
        self.engine.state["rocket_ops"]["op_10"]["boss_hp_remaining"] = 0
        ok_final, msg_final = self.engine.claim_rocket_operation("10")
        self.assertTrue(ok_final)

        # Verify Endgame Rewards
        self.assertIn("👑 Seeker of Truth", self.engine.state.get("gym_badges", []))
        self.assertTrue(self.engine.state.get("permanent_black_market", False))

        # Check recruited companions in dex roster
        dex_sp_ids = [d.get("species_id") for d in self.engine.state.get("dex", [])]
        self.assertIn(2001, dex_sp_ids)  # Armored Mewtwo
        self.assertIn(2002, dex_sp_ids)  # Porygon-Zero
        for aug_id in [2003, 2004, 2005, 2006, 2007, 2008]:
            self.assertIn(aug_id, dex_sp_ids)

        # Verify species names
        self.assertEqual(self.engine.api.get_species_name(2001), "Armored Mewtwo")
        self.assertEqual(self.engine.api.get_species_name(2002), "Porygon-Zero")
        self.assertEqual(self.engine.api.get_species_name(2003), "Augmented Venusaur")

    def test_rocket_armory_rank_clearance(self):
        self.engine.state["used_since_install"] = 500_000_000
        self.engine.state["spent_tokens"] = 0

        # At Informant rank:
        self.engine.state["rocket_rank"] = "Informant"
        ok_pass, _ = self.engine.buy_rocket_armory_item("pass")
        self.assertTrue(ok_pass)

        # Operative items require Operative rank
        ok_spray_denied, msg_spray = self.engine.buy_rocket_armory_item("spray")
        self.assertFalse(ok_spray_denied)
        self.assertIn("Clearance Denied", msg_spray)

        ok_chrono_denied, msg_chrono = self.engine.buy_rocket_armory_item("chrono")
        self.assertFalse(ok_chrono_denied)
        self.assertIn("Clearance Denied", msg_chrono)

        # Upgrade to Operative
        self.engine.state["rocket_rank"] = "Operative"
        ok_spray, _ = self.engine.buy_rocket_armory_item("spray")
        self.assertTrue(ok_spray)

        # Special Agent items require Special Agent rank
        ok_splitter_denied, msg_split = self.engine.buy_rocket_armory_item("splitter")
        self.assertFalse(ok_splitter_denied)
        self.assertIn("Clearance Denied", msg_split)

        # Upgrade to Special Agent
        self.engine.state["rocket_rank"] = "Special Agent"
        ok_splitter, _ = self.engine.buy_rocket_armory_item("splitter")
        self.assertTrue(ok_splitter)

        # Executive items require Executive rank
        ok_cat_denied, msg_cat = self.engine.buy_rocket_armory_item("catalyst")
        self.assertFalse(ok_cat_denied)
        self.assertIn("Clearance Denied", msg_cat)

        # Upgrade to Executive
        self.engine.state["rocket_rank"] = "Executive"
        ok_cat, _ = self.engine.buy_rocket_armory_item("catalyst")
        self.assertTrue(ok_cat)

        # Commander items require Commander rank
        ok_auth_denied, msg_auth = self.engine.buy_rocket_armory_item("authority")
        self.assertFalse(ok_auth_denied)
        self.assertIn("Clearance Denied", msg_auth)

        # Upgrade to Commander
        self.engine.state["rocket_rank"] = "Commander"
        ok_auth, _ = self.engine.buy_rocket_armory_item("authority")
        self.assertTrue(ok_auth)

    def test_syndicate_black_pass_and_grunt_toll_waiver(self):
        """Verify Syndicate Black Pass waives Grunt bribe and unlocks 24/7 Black Market."""
        self.engine.state["used_since_install"] = 50_000_000
        self.engine.state["spent_tokens"] = 0
        self.engine.state["rocket_rank"] = "Informant"

        # Buy pass
        ok, msg = self.engine.buy_rocket_armory_item("pass")
        self.assertTrue(ok)
        self.assertTrue(self.engine.state.get("permanent_black_market"))

        # Cannot buy duplicate pass
        ok_dup, msg_dup = self.engine.buy_rocket_armory_item("pass")
        self.assertFalse(ok_dup)
        self.assertIn("already possess", msg_dup)

        # Black market is open
        bm = self.engine.get_or_init_black_market()
        self.assertTrue(bm.get("natural_open"))
        self.assertTrue(bm.get("is_open"))

        # Grunt bribe is completely waived (0 tokens deducted)
        prev_spent = self.engine.state.get("spent_tokens", 0)
        ok_bribe, msg_bribe = self.engine.bribe_grunt_for_black_market()
        self.assertTrue(ok_bribe)
        self.assertIn("Syndicate Black Pass recognized", msg_bribe)
        self.assertEqual(self.engine.state.get("spent_tokens"), prev_spent)

    def test_syndicate_morale_mist_squad_happiness(self):
        """Verify Syndicate Morale Mist restores 100% happiness across entire squad."""
        self.engine.state["used_since_install"] = 100_000_000
        self.engine.state["spent_tokens"] = 0
        self.engine.state["rocket_rank"] = "Operative"

        # Setup active mon with 25 happiness
        active_mon = MonState(
            base_id=25, path_ids=[25, 26], planned_path_ids=[25, 26], stage_index=0,
            used_at_stage=0, rarity=Rarity.COMMON, total_forms=2, happiness=25
        )
        self.engine.set_active_mon(active_mon)
        self.assertEqual(self.engine.state.get("happiness"), 25)

        # Setup reserve roster mons with low happiness
        sub1 = MonState(base_id=1, path_ids=[1, 2, 3], planned_path_ids=[1, 2, 3], stage_index=0, used_at_stage=0, rarity=Rarity.COMMON, total_forms=3, happiness=10)
        sub2 = MonState(base_id=4, path_ids=[4, 5, 6], planned_path_ids=[4, 5, 6], stage_index=0, used_at_stage=0, rarity=Rarity.COMMON, total_forms=3, happiness=50)
        self.engine.state["dex"] = [
            {"species_id": 1, "status": "inactive", "happiness": 10, "mon_state": StorageManager.mon_to_dict(sub1)},
            {"species_id": 4, "status": "inactive", "happiness": 50, "mon_state": StorageManager.mon_to_dict(sub2)},
            {"species_id": 100, "status": "evolved", "happiness": 0}  # Evolved form shouldn't prevent or break anything
        ]

        # Buy Morale Mist
        ok, msg = self.engine.buy_rocket_armory_item("spray")
        self.assertTrue(ok)
        self.assertIn("Syndicate Morale Mist", msg)
        self.assertEqual(self.engine.active_mon.happiness, 100)
        self.assertEqual(self.engine.state.get("happiness"), 100)
        for d in self.engine.state["dex"]:
            if d.get("status") != "evolved":
                self.assertEqual(d.get("happiness"), 100)
                self.assertEqual(d["mon_state"]["happiness"], 100)

    def test_chrono_accelerator_cd_fast_forward(self):
        """Verify Chrono Accelerator advances active Bank CDs by +1 day and triggers maturity."""
        self.engine.state["used_since_install"] = 200_000_000
        self.engine.state["spent_tokens"] = 0
        self.engine.state["rocket_rank"] = "Operative"

        # Open a 3-day CD for 10M tokens
        ok_open, _ = self.engine.open_cd("10m", 3)
        self.assertTrue(ok_open)
        cds = self.engine.state.get("term_deposits", [])
        self.assertEqual(len(cds), 1)
        cd = cds[0]
        self.assertEqual(cd["days_elapsed"], 0)
        self.assertFalse(cd["matured"])

        # First acceleration
        ok_ch1, msg_ch1 = self.engine.buy_rocket_armory_item("chrono")
        self.assertTrue(ok_ch1)
        self.assertEqual(self.engine.state["term_deposits"][0]["days_elapsed"], 1)
        self.assertFalse(self.engine.state["term_deposits"][0]["matured"])

        # Second acceleration
        ok_ch2, _ = self.engine.buy_rocket_armory_item("chrono")
        self.assertTrue(ok_ch2)
        self.assertEqual(self.engine.state["term_deposits"][0]["days_elapsed"], 2)
        self.assertFalse(self.engine.state["term_deposits"][0]["matured"])

        # Third acceleration -> Matures!
        ok_ch3, msg_ch3 = self.engine.buy_rocket_armory_item("chrono")
        self.assertTrue(ok_ch3)
        self.assertEqual(self.engine.state["term_deposits"][0]["days_elapsed"], 3)
        self.assertTrue(self.engine.state["term_deposits"][0]["matured"])
        self.assertIn("1 matured", msg_ch3)

        # Claim the matured CD
        ok_claim, msg_claim = self.engine.claim_cd(str(cd["id"]))
        self.assertTrue(ok_claim)
        self.assertIn("Claimed CD", msg_claim)

    def test_corrupted_exp_splitter_passive_xp_mirror(self):
        """Verify Corrupted EXP Splitter mirrors 25% of coding XP to inactive roster mons without unseating active mon."""
        self.engine.state["used_since_install"] = 100_000_000
        self.engine.state["spent_tokens"] = 0
        self.engine.state["rocket_rank"] = "Special Agent"
        self.engine.state["install_baseline_set"] = True

        # Buy Corrupted Splitter
        ok_split, _ = self.engine.buy_rocket_armory_item("splitter")
        self.assertTrue(ok_split)
        self.assertTrue(self.engine.state.get("has_exp_splitter"))

        # Setup active Charmander (ID: 4)
        char_mon = MonState(
            base_id=4, path_ids=[4, 5, 6], planned_path_ids=[4, 5, 6], stage_index=0,
            used_at_stage=0, rarity=Rarity.COMMON, total_forms=3, happiness=100
        )
        self.engine.set_active_mon(char_mon)

        # Setup reserve Squirtle (ID: 7) in dex
        sq_mon = MonState(
            base_id=7, path_ids=[7, 8, 9], planned_path_ids=[7, 8, 9], stage_index=0,
            used_at_stage=0, rarity=Rarity.COMMON, total_forms=3, happiness=100
        )
        self.engine.state["dex"] = [
            {"species_id": 7, "base_id": 7, "status": "inactive", "happiness": 100, "mon_state": StorageManager.mon_to_dict(sq_mon)}
        ]
        self.engine.save()

        # Generate coding token usage
        curr_used = self.engine.state.get("used_since_install", 0)
        self.engine.process_usage(curr_used + 100_000)

        # Squirtle in dex should have received 25% of effective XP
        sq_entry = self.engine.state["dex"][0]
        sq_saved = sq_entry["mon_state"]
        self.assertGreater(sq_saved["used_at_stage"], 0)
        # Active companion remains Charmander!
        self.assertEqual(self.engine.active_mon.base_id, 4)

    def test_dark_gene_catalyst_evolution(self):
        """Verify Dark Gene Catalyst triggers immediate evolution of active companion."""
        self.engine.state["used_since_install"] = 100_000_000
        self.engine.state["spent_tokens"] = 0
        self.engine.state["rocket_rank"] = "Executive"

        # Buy catalyst
        ok_buy, msg_buy = self.engine.buy_rocket_armory_item("catalyst")
        self.assertTrue(ok_buy)
        self.assertEqual(self.engine.state["inventory"].get("dark_gene_catalyst"), 1)

        # Active Wartortle (ID: 8)
        wartortle = MonState(
            base_id=7, path_ids=[7, 8, 9], planned_path_ids=[7, 8, 9], stage_index=1,
            used_at_stage=0, rarity=Rarity.COMMON, total_forms=3, happiness=100
        )
        self.engine.set_active_mon(wartortle)
        self.assertEqual(self.engine.active_mon.current_id, 8)

        # Use Dark Gene Catalyst
        ok_use, msg_use = self.engine.use_item("dark_gene_catalyst")
        self.assertTrue(ok_use)
        self.assertIn("Dark Gene Catalyst", msg_use)
        self.assertEqual(self.engine.active_mon.current_id, 9)
        self.assertEqual(self.engine.active_mon.stage_index, 2)
        self.assertEqual(self.engine.state["inventory"].get("dark_gene_catalyst", 0), 0)

    def test_team_rocket_authority_delivery_and_recruitment(self):
        """Verify Team Rocket Authority costs 100 tokens, delivers non-duplicate species, and supports keep/dismiss."""
        self.engine.state["used_since_install"] = 1_000
        self.engine.state["spent_tokens"] = 0
        self.engine.state["rocket_rank"] = "Commander"

        # Populate roster with specific IDs
        pika = MonState(base_id=25, path_ids=[25, 26], planned_path_ids=[25, 26], stage_index=0, used_at_stage=0, rarity=Rarity.COMMON, total_forms=2)
        self.engine.set_active_mon(pika)

        # Requisition authority (free clearance perk)
        ok_auth, msg_auth = self.engine.buy_rocket_armory_item("authority")
        self.assertTrue(ok_auth)
        self.assertEqual(self.engine.state["spent_tokens"], 0)
        self.assertIn("Team Rocket Authority", msg_auth)
        pending_id = self.engine.state.get("pending_authority_delivery")
        self.assertIsNotNone(pending_id)
        self.assertNotEqual(pending_id, 25)
        self.assertIn(pending_id, range(1, 152))

        # Cannot buy again same day / while delivery pending
        ok_rep, msg_rep = self.engine.buy_rocket_armory_item("authority")
        self.assertFalse(ok_rep)
        self.assertIn("already waiting", msg_rep)

        # Test dismiss
        ok_dis, msg_dis = self.engine.handle_authority_delivery("dismiss")
        self.assertTrue(ok_dis)
        self.assertIn("dismissed back into the wild", msg_dis)
        self.assertIsNone(self.engine.state.get("pending_authority_delivery"))

        # Cannot buy again today due to daily limit
        ok_daily, msg_daily = self.engine.buy_rocket_armory_item("authority")
        self.assertFalse(ok_daily)
        self.assertIn("already dispatched today", msg_daily)

        # Reset daily limit and buy again for 'keep' test
        self.engine.state["last_authority_date"] = "2020-01-01"
        ok_auth2, _ = self.engine.buy_rocket_armory_item("authority")
        self.assertTrue(ok_auth2)
        new_pending_id = self.engine.state.get("pending_authority_delivery")
        self.assertIsNotNone(new_pending_id)

        # Test keep
        ok_keep, msg_keep = self.engine.handle_authority_delivery("keep")
        self.assertTrue(ok_keep)
        self.assertIn("Registered", msg_keep)
        self.assertIsNone(self.engine.state.get("pending_authority_delivery"))

        # Verify new Pokémon is in Dex roster as inactive with 100 happiness
        roster = [d for d in self.engine.state["dex"] if d.get("species_id") == new_pending_id or d.get("base_id") == new_pending_id]
        self.assertTrue(len(roster) > 0)
        self.assertEqual(roster[0]["status"], "inactive")

    def test_72_column_layout_compliance_tab_12(self):
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.rocket import render_rocket_tab, render_rocket_transmission

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        app = MagicMock()
        app.engine = self.engine
        self.engine.state["rocket_story_unlocked"] = True
        self.engine.state["rocket_alliance_accepted"] = True

        # Test all subviews: ops, intel, read_intel, armory
        for subview in ["ops", "intel", "read_intel", "armory"]:
            app.rocket_subview = subview
            app.rocket_reading_file = 1
            trap = io.StringIO()
            with patch("sys.stdout", trap):
                render_rocket_tab(app)
            for line in trap.getvalue().split("\n"):
                clean = ansi_regex.sub("", line)
                self.assertLessEqual(len(clean), 72, f"Rocket Tab [{subview}] exceeds 72 cols: '{clean}' (len={len(clean)})")

        # Test dormant secure comm channel
        self.engine.state["rocket_alliance_accepted"] = False
        trap_comm = io.StringIO()
        with patch("sys.stdout", trap_comm):
            render_rocket_tab(app)
        comm_val = trap_comm.getvalue()
        self.assertIn("Type 'accept' to initiate the Rocket Alliance.", ansi_regex.sub("", comm_val))
        self.assertNotIn("or '1'", ansi_regex.sub("", comm_val))
        for line in comm_val.split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Secure Comm line exceeds 72 cols: '{clean}' (len={len(clean)})")

        # Test active boss chamber HUD in ops view
        self.engine.state["rocket_alliance_accepted"] = True
        app.rocket_subview = "ops"
        self.engine.state["rocket_ops"]["op_3"]["status"] = "active"
        self.engine.state["rocket_ops"]["op_3"]["boss_hp_remaining"] = 12_500
        trap_boss = io.StringIO()
        with patch("sys.stdout", trap_boss):
            render_rocket_tab(app)
        for line in trap_boss.getvalue().split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Boss chamber line exceeds 72 cols: '{clean}' (len={len(clean)})")

        # Test transmission screens with all choices
        for seq in [["1\n"], ["2\n", "1\n"], ["3\n", "1\n"], ["3\n", "2\n", "\n"]]:
            trap_modal = io.StringIO()
            with patch("sys.stdout", trap_modal), patch("sys.stdin.readline", side_effect=seq):
                render_rocket_transmission(app)
            for line in trap_modal.getvalue().split("\n"):
                clean = ansi_regex.sub("", line)
                self.assertLessEqual(len(clean), 72, f"Transmission line exceeds 72 cols: '{clean}' (len={len(clean)})")

    def test_rocket_single_active_quest_display(self):
        """Verify Rocket Operations menu displays ONLY the single active/available operation."""
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.rocket import render_rocket_tab, handle_rocket_command

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        app = MagicMock()
        app.engine = self.engine
        app.rocket_subview = "ops"
        self.engine.state["rocket_story_unlocked"] = True
        self.engine.state["rocket_alliance_accepted"] = True

        # 1. Op 1 is available initially
        trap = io.StringIO()
        with patch("sys.stdout", trap):
            render_rocket_tab(app)
        out = ansi_regex.sub("", trap.getvalue())

        # Op 1 should appear without [ NUM] index and with 'start operation' badge
        self.assertIn("Operation Genesis", out)
        self.assertIn("[AVAILABLE - 'start operation']", out)
        self.assertNotIn("[ 1]", out)
        self.assertNotIn("[1]", out)
        # Notice and switch view hints should be removed
        self.assertNotIn("Complete 10 operations to dismantle Oak's secret facilities", out)
        self.assertNotIn("Switch view:", out)
        # Op 2 through 10 should NOT be printed
        self.assertNotIn("Operation Chimera", out)
        self.assertNotIn("Silph Sub-Vault", out)
        self.assertNotIn("The Oak Citadel", out)

        # 2. 'start 1' is rejected; only 'start operation' is accepted
        handle_rocket_command(app, "start 1")
        self.assertEqual(self.engine.state["rocket_ops"]["op_1"]["status"], "available")
        self.assertIn("start operation", app.message)

        handle_rocket_command(app, "start operation")
        self.assertEqual(self.engine.state["rocket_ops"]["op_1"]["status"], "active")

        # Re-render with Op 1 active
        trap2 = io.StringIO()
        with patch("sys.stdout", trap2):
            render_rocket_tab(app)
        out2 = ansi_regex.sub("", trap2.getvalue())
        self.assertIn("[ACTIVE]", out2)
        self.assertNotIn("[ 1]", out2)
        self.assertNotIn("Operation Chimera", out2)
        self.assertNotIn("Switch view:", out2)

        # 3. Fulfill Op 1 objective and test parameterless 'claim' command
        self.engine.state["rocket_ops"]["op_1"]["expeditions_done"] = 2
        events = []
        self.engine._update_rocket_operations(5_000_000, events)
        handle_rocket_command(app, "claim")
        self.assertTrue(self.engine.state["rocket_ops"]["op_1"]["claimed"])
        self.assertEqual(self.engine.state["rocket_ops"]["op_2"]["status"], "available")

        # Re-render: now Op 2 is the ONLY quest shown, without [ NUM] index
        trap3 = io.StringIO()
        with patch("sys.stdout", trap3):
            render_rocket_tab(app)
        out3 = ansi_regex.sub("", trap3.getvalue())
        self.assertIn("Operation Chimera", out3)
        self.assertNotIn("[ 2]", out3)
        self.assertNotIn("Operation Genesis", out3)
        self.assertNotIn("Silph Sub-Vault", out3)
        self.assertNotIn("Switch view:", out3)

        # 4. When all 10 are claimed, verify completion message
        for i in range(1, 11):
            self.engine.state["rocket_ops"][f"op_{i}"]["claimed"] = True
        trap4 = io.StringIO()
        with patch("sys.stdout", trap4):
            render_rocket_tab(app)
        out4 = ansi_regex.sub("", trap4.getvalue())
        self.assertIn("ALL 10 COVERT OPERATIONS COMPLETED!", out4)
        self.assertNotIn("Switch view:", out4)

        # 5. Verify Intel and Armory also have no menu changing hints
        app.rocket_subview = "intel"
        trap_intel = io.StringIO()
        with patch("sys.stdout", trap_intel):
            render_rocket_tab(app)
        self.assertNotIn("return to Operations menu", ansi_regex.sub("", trap_intel.getvalue()))

        app.rocket_subview = "armory"
        trap_armory = io.StringIO()
        with patch("sys.stdout", trap_armory):
            render_rocket_tab(app)
        self.assertNotIn("Switch view:", ansi_regex.sub("", trap_armory.getvalue()))

        for line in trap3.getvalue().split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Ops line exceeds 72 cols: '{clean}'")

    def test_rocket_intel_paging_and_armory_locked_display(self):
        """Verify Intel hides locked archives, uses 5-item paging, and Armory masks locked items."""
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.rocket import render_rocket_tab, handle_rocket_command

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        app = MagicMock()
        app.engine = self.engine
        app.intel_page = 1
        self.engine.state["rocket_story_unlocked"] = True
        self.engine.state["rocket_alliance_accepted"] = True

        # 1. Test Intel: only intel_001 unlocked initially
        self.engine.state["rocket_intel_unlocked"] = ["intel_001"]
        app.rocket_subview = "intel"
        trap1 = io.StringIO()
        with patch("sys.stdout", trap1):
            render_rocket_tab(app)
        out1 = ansi_regex.sub("", trap1.getvalue())

        self.assertIn("Dossier #001", out1)
        # Locked archives must be hidden
        self.assertNotIn("Dossier #002", out1)
        self.assertNotIn("Dossier #003", out1)
        self.assertNotIn("[LOCKED", out1)
        # Single page, so no page navigation hint needed
        self.assertNotIn("Page 1/", out1)

        # Attempting to read an un-retrieved dossier should be rejected
        handle_rocket_command(app, "read 2")
        self.assertIn("not been retrieved yet", app.message)
        self.assertNotEqual(getattr(app, "rocket_subview", ""), "read_intel")

        # 2. Test Intel: 7 dossiers unlocked -> 2 pages (5 per page)
        self.engine.state["rocket_intel_unlocked"] = [f"intel_{i:03d}" for i in range(1, 8)]
        trap_p1 = io.StringIO()
        with patch("sys.stdout", trap_p1):
            render_rocket_tab(app)
        out_p1 = ansi_regex.sub("", trap_p1.getvalue())

        # Page 1 contains dossiers 1..5, but not 6 or 7
        self.assertIn("Dossier #001", out_p1)
        self.assertIn("Dossier #005", out_p1)
        self.assertNotIn("Dossier #006", out_p1)
        self.assertNotIn("Dossier #007", out_p1)
        self.assertIn("Page 1/2", out_p1)

        # Page navigation with 'n'
        handle_rocket_command(app, "n")
        self.assertEqual(app.intel_page, 2)
        trap_p2 = io.StringIO()
        with patch("sys.stdout", trap_p2):
            render_rocket_tab(app)
        out_p2 = ansi_regex.sub("", trap_p2.getvalue())

        # Page 2 contains dossiers 6 and 7, but not 1..5
        self.assertIn("Dossier #006", out_p2)
        self.assertIn("Dossier #007", out_p2)
        self.assertNotIn("Dossier #001", out_p2)
        self.assertNotIn("Dossier #005", out_p2)
        self.assertIn("Page 2/2", out_p2)

        # Successfully read an unlocked dossier
        handle_rocket_command(app, "read 7")
        self.assertEqual(app.rocket_subview, "read_intel")
        self.assertEqual(app.rocket_reading_file, 7)

        # 3. Test Armory: Informant rank sees higher rank items masked with ??? and higher rank notice
        app.rocket_subview = "armory"
        self.engine.state["rocket_rank"] = "Informant"
        trap_arm = io.StringIO()
        with patch("sys.stdout", trap_arm):
            render_rocket_tab(app)
        out_arm = ansi_regex.sub("", trap_arm.getvalue())

        # Informant item is clear
        self.assertIn("Syndicate Black Pass", out_arm)
        self.assertIn("[CLEARANCE GRANTED]", out_arm)
        # Operative and higher items are masked with ???
        self.assertIn("??? ???", out_arm)
        self.assertIn("[LOCKED - OPERATIVE REQUIRED]", out_arm)
        self.assertIn("[LOCKED - COMMANDER REQUIRED]", out_arm)
        self.assertIn("Requires rank 'Operative' (Promoted via Covert Operations).", out_arm)
        self.assertIn("Requires rank 'Commander' (Promoted via Covert Operations).", out_arm)
        self.assertNotIn("Syndicate Morale Mist", out_arm)
        self.assertNotIn("Team Rocket Authority", out_arm)
        # Verify codes and buy/claim command hints are removed
        self.assertNotIn("('pass')", out_arm)
        self.assertNotIn("('???')", out_arm)
        self.assertNotIn("claim <code>", out_arm)
        self.assertNotIn("buy <code>", out_arm)
        self.assertIn("Clearance perks activate automatically upon rank promotion.", out_arm)

        # Verify 72-col compliance across Intel and Armory
        for t in [trap_p1, trap_p2, trap_arm]:
            for line in t.getvalue().split("\n"):
                clean = ansi_regex.sub("", line)
                self.assertLessEqual(len(clean), 72, f"Line exceeds 72 cols: '{clean}'")

    def test_graduated_companion_no_repeated_graduation_or_alerts(self):
        """Verify that once a companion graduates, feeding berries or gaining tokens does not re-trigger graduation."""
        # 1. Setup Venusaur (ID: 3) in dex as graduated
        venusaur_state = MonState(
            base_id=1,
            path_ids=[1, 2, 3],
            planned_path_ids=[1, 2, 3],
            stage_index=2,
            used_at_stage=125_000_000,
            rarity=Rarity.RARE,
            total_forms=3,
            is_shiny=True,
            happiness=50,
            is_graduated=True
        )
        self.engine.state["collected_finals"] = ["1_3"]
        self.engine.state["dex"] = [{
            "id": "sp_3",
            "species_id": 3,
            "base_id": 1,
            "chain_order": [1, 2, 3],
            "rarity": "rare",
            "status": "graduated",
            "mon_state": StorageManager.mon_to_dict(venusaur_state)
        }]
        self.engine.state["inventory"] = {"berry_oran": 5}
        self.engine.state["unread_alerts"] = []

        # 2. Select Venusaur from dex as active companion
        ok_sel, msg_sel = self.engine.select_active_from_dex("3")
        self.assertTrue(ok_sel)
        self.assertIsNotNone(self.engine.active_mon)
        self.assertEqual(self.engine.active_mon.current_id, 3)
        self.assertTrue(self.engine.active_mon.is_graduated)

        # 3. Feed an Oran Berry
        ok_feed, msg_feed = self.engine.use_item("berry_oran", 1)
        self.assertTrue(ok_feed)
        self.assertEqual(self.engine.active_mon.happiness, 75)

        # 4. Simulate token growth / process_usage
        initial_tokens = self.engine.state.get("used_since_install", 0)
        events = self.engine.process_usage(initial_tokens + 5_000_000)

        # 5. Assertions: Venusaur remains active and NO graduation event or alert is fired!
        self.assertIsNotNone(self.engine.active_mon)
        self.assertEqual(self.engine.active_mon.current_id, 3)
        self.assertNotIn("🎓 Graduation!", " ".join(events))
        alerts = self.engine.state.get("unread_alerts", [])
        self.assertFalse(any("Graduation!" in a for a in alerts))

        # 6. Switch away to egg, verify status in dex returns to 'graduated', not 'inactive'
        self.engine.state["egg_tier"] = "common"
        self.engine.select_active_from_dex("egg")
        self.assertIsNone(self.engine.active_mon)
        dex_v = [d for d in self.engine.state["dex"] if d.get("species_id") == 3][0]
        self.assertEqual(dex_v["status"], "graduated")

    def test_stock_market_pattern_cycles_and_forward_hints(self):
        """Verify stock market pattern cycles, forward-looking hints, and anti-infinite price bounds."""
        from poketokenbar.game.stock_market import (
            StockMarketEngine, BASE_PRICES, PATTERN_HINTS
        )

        sm = self.engine.get_or_init_stock_market()
        self.assertIn("market_state", sm)

        # 1. Verify all corporations have pattern state and hints <= 52 characters
        for c_key in BASE_PRICES:
            self.assertIn(c_key, sm["market_state"])
            st = sm["market_state"][c_key]
            self.assertIn("pattern", st)
            self.assertIn("phase", st)
            self.assertIn("next_bias", st)
            self.assertIn("next_hint", st)
            self.assertLessEqual(len(st["next_hint"]), 52, f"Hint for {c_key} exceeds 52 chars: {st['next_hint']}")
            self.assertEqual(sm["latest_news"][c_key], st["next_hint"])

        # 2. Verify all pattern hints in the dictionary are <= 52 characters
        for c_key, pat_map in PATTERN_HINTS.items():
            for pat_name, phase_list in pat_map.items():
                for bias, hint_text in phase_list:
                    self.assertLessEqual(len(hint_text), 52, f"Hint '{hint_text}' for {c_key} exceeds 52 cols")

        # 3. Step the market forward 30 days and verify price bounds
        events = []
        for day in range(30):
            self.engine._rollover_stock_market(days_to_apply=1, diff=1, current_streak=day + 1, events=events)

        for c_key, base in BASE_PRICES.items():
            price = sm["prices"][c_key]
            floor = StockMarketEngine.get_floor_price(c_key)
            cap = StockMarketEngine.get_hard_cap(c_key)
            self.assertGreaterEqual(price, floor, f"{c_key} fell below floor: {price} < {floor}")
            self.assertLessEqual(price, cap, f"{c_key} exceeded hard cap: {price} > {cap}")

    def test_72_column_layout_compliance_tab_10_bank_and_terminal(self):
        """Verify that Bank Tab 10 and Stock Terminal views strictly respect <= 72 columns."""
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.bank import render_bank_tab, _render_stock_terminal

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        app = MagicMock()
        app.engine = self.engine
        app.bank_subtab = "stocks"
        app.stock_terminal = None
        app.stock_page = 1

        # Render Main Board page 1 and page 2
        for p in [1, 2]:
            app.stock_page = p
            trap = io.StringIO()
            with patch("sys.stdout", trap):
                render_bank_tab(app)
            for line in trap.getvalue().split("\n"):
                clean = ansi_regex.sub("", line)
                self.assertLessEqual(len(clean), 72, f"Bank Tab [stocks page {p}] exceeds 72 cols: '{clean}' (len={len(clean)})")

        # Render Stock Terminal for each corporation
        for c_key in ["silph", "devon", "aether", "mauville", "macro", "viridian"]:
            trap_term = io.StringIO()
            with patch("sys.stdout", trap_term):
                _render_stock_terminal(app, avail=50_000_000, corp_key=c_key)
            for line in trap_term.getvalue().split("\n"):
                clean = ansi_regex.sub("", line)
                self.assertLessEqual(len(clean), 72, f"Stock Terminal [{c_key}] exceeds 72 cols: '{clean}' (len={len(clean)})")

    def test_spear_pillar_expedition_happiness_retention(self):
        """Verify Spear Pillar expedition dispatch and pass usage retain proper happiness (90% without insurance, 100% with insurance)."""
        # 1. Setup Charizard in dex with 100% happiness
        charizard_state = MonState(
            base_id=4,
            path_ids=[4, 5, 6],
            planned_path_ids=[4, 5, 6],
            stage_index=2,
            used_at_stage=100_000_000,
            rarity=Rarity.RARE,
            total_forms=3,
            happiness=100,
            is_graduated=True
        )
        self.engine.state["dex"] = [{
            "id": "sp_6",
            "species_id": 6,
            "base_id": 4,
            "chain_order": [4, 5, 6],
            "rarity": "rare",
            "status": "inactive",
            "happiness": 100,
            "mon_state": StorageManager.mon_to_dict(charizard_state)
        }]
        self.engine.state["inventory"] = {
            "map_fragment": 3,
            "expedition_pass": 1
        }
        self.engine.state["expeditions"] = []

        # 2. Dispatch Charizard to Spear Pillar
        ok_disp, msg_disp = self.engine.dispatch_expedition("#6", "spear")
        self.assertTrue(ok_disp, f"Dispatch failed: {msg_disp}")
        self.assertEqual(len(self.engine.state["expeditions"]), 1)
        self.assertEqual(self.engine.state["expeditions"][0]["sp_id"], 6)

        # 3. Assert happiness was NOT deducted prematurely upon dispatch
        entry = [d for d in self.engine.state["dex"] if d.get("species_id") == 6][0]
        self.assertEqual(entry.get("happiness"), 100)
        self.assertEqual(entry.get("mon_state", {}).get("happiness"), 100)

        # 4. Use Expedition Pass to instantly complete the expedition
        ok_pass, msg_pass = self.engine.use_expedition_pass("1")
        self.assertTrue(ok_pass, f"Use pass failed: {msg_pass}")
        self.assertEqual(len(self.engine.state["expeditions"]), 0)

        # 5. Assert happiness is 90% (standard -10 fatigue on completion, NOT 0%!)
        entry = [d for d in self.engine.state["dex"] if d.get("species_id") == 6][0]
        self.assertEqual(entry.get("happiness"), 90)
        self.assertEqual(entry.get("mon_state", {}).get("happiness"), 90)

        # 6. Now test with expedition insurance: happiness stays protected at 100%
        charizard_state.happiness = 100
        entry["happiness"] = 100
        entry["mon_state"] = StorageManager.mon_to_dict(charizard_state)
        self.engine.state["inventory"]["map_fragment"] = 3
        self.engine.state["inventory"]["expedition_pass"] = 1
        self.engine.state["expedition_insurance"] = 1

        ok_disp2, msg_disp2 = self.engine.dispatch_expedition("#6", "spear")
        self.assertTrue(ok_disp2, f"Dispatch 2 failed: {msg_disp2}")
        ok_pass2, msg_pass2 = self.engine.use_expedition_pass("1")
        self.assertTrue(ok_pass2, f"Use pass 2 failed: {msg_pass2}")
        entry = [d for d in self.engine.state["dex"] if d.get("species_id") == 6][0]
        self.assertEqual(entry.get("happiness"), 100)
        self.assertEqual(entry.get("mon_state", {}).get("happiness"), 100)
        self.assertEqual(self.engine.state.get("expedition_insurance"), 0)

    def test_mega_stone_bag_exclusion_and_single_ownership_enforcement(self):
        """Verify Mega Stones do not appear in the Bag, only in Tab 8, and strictly enforce 1 stone limit."""
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.shop import render_shop_tab
        from poketokenbar.tui_tabs.mega_evo import render_mega_evo_tab
        from poketokenbar.game.models import MEGA_STONES

        # 1. Setup inventory with a regular item and multiple mega stones
        self.engine.state["inventory"] = {
            "rare_candy": 5,
            "mega_stone_6_X": 1,
            "mega_stone_6_Y": 1,
            "mega_stone_3": 1
        }
        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        app = MagicMock()
        app.engine = self.engine
        app.shop_view = "normal"
        app.shop_page = 1
        app.mega_page = 1

        # 2. Render Shop/Bag Tab (Tab 4): Mega Stones must NOT appear in Bag output!
        trap_bag = io.StringIO()
        with patch("sys.stdout", trap_bag):
            render_shop_tab(app)
        bag_output = ansi_regex.sub("", trap_bag.getvalue())
        self.assertIn("Rare Candy", bag_output)
        self.assertNotIn("Charizardite", bag_output)
        self.assertNotIn("Venusaurite", bag_output)

        # 3. Render Mega Evolution Tab (Tab 8): Mega Stones MUST appear!
        trap_mega = io.StringIO()
        with patch("sys.stdout", trap_mega):
            render_mega_evo_tab(app)
        mega_output = ansi_regex.sub("", trap_mega.getvalue())
        self.assertIn("Venusaurite", mega_output)
        self.assertIn("Charizardite X", mega_output)
        self.assertIn("Charizardite Y", mega_output)
        # Ensure 72-col compliance in Tab 8
        for line in trap_mega.getvalue().split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Tab 8 line exceeds 72 cols: '{clean}'")

        # 4. Enforce max 1 stone: Clamping on initialization
        self.engine.state["inventory"]["mega_stone_6_X"] = 5
        self.engine.__init__()
        self.assertEqual(self.engine.state["inventory"]["mega_stone_6_X"], 1)

        # 5. Prevent selling Mega Stones
        ok_sell, msg_sell = self.engine.sell_item("mega_stone_6_X", 1)
        self.assertFalse(ok_sell)
        self.assertIn("cannot be sold", msg_sell)

        # 6. Prevent duplicate purchases in Shop (buy_item)
        for sid in MEGA_STONES.keys():
            self.engine.state["inventory"][f"mega_stone_{sid}"] = 1
        self.engine.state["spent_tokens"] = 0
        self.engine.state["used_since_install"] = 100_000_000
        ok_buy, msg_buy = self.engine.buy_item(ItemKind.MEGA_STONE, 1)
        self.assertFalse(ok_buy)
        self.assertIn("already own all available Mega Stones", msg_buy)

        # 7. Prevent duplicate purchases in Black Market
        bm = self.engine.get_or_init_black_market(force_open=True)
        deals = [{"id": i, "name": f"Deal {i}", "type": "item", "item_key": "rare_candy", "price": 10_000_000, "stock": 1, "qty": 1} for i in range(1, 8)]
        deals[0] = {"id": 1, "name": "🔮 Charizardite X", "type": "mega_stone", "stone_id": "6_X", "price": 10_000_000, "stock": 1}
        bm["deals"] = deals
        self.engine.state["black_market"] = bm
        self.engine.save()
        ok_bm, msg_bm = self.engine.buy_black_market_deal("1", 1)
        self.assertFalse(ok_bm)
        self.assertIn("already own", msg_bm)

    def test_fixed_numeric_bag_catalog_and_np_paging(self):
        """Verify fixed numeric indexing for all items in Bag, 'n'/'p' navigation hints, and 72-col compliance."""
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.shop import render_shop_tab, handle_bag_use, handle_bag_sell, BAG_CATALOG_MAP
        from poketokenbar.tui_tabs.mega_evo import render_mega_evo_tab
        from poketokenbar.game.models import ItemKind, MonState, Rarity

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')

        # Verify BAG_CATALOG_MAP maps fixed numeric keys
        self.assertEqual(BAG_CATALOG_MAP["41"], "water_stone")
        self.assertEqual(BAG_CATALOG_MAP["18"], "choice_specs")
        self.assertEqual(BAG_CATALOG_MAP["24"], "revitalizing_tonic")
        self.assertEqual(BAG_CATALOG_MAP["31"], "metal_coat")
        self.assertEqual(BAG_CATALOG_MAP["51"], "fake_rare_candy")

        # 1. Setup inventory with diverse items
        self.engine.state["inventory"] = {
            "rare_candy": 5,
            "choice_specs": 1,
            "revitalizing_tonic": 2,
            "metal_coat": 1,
            "water_stone": 2,
            "fake_rare_candy": 1,
        }
        self.engine.state["page_size_bag"] = 3
        app = MagicMock()
        app.engine = self.engine
        app.shop_view = "normal"
        app.shop_page = 1
        app.message = ""

        # 2. Render Bag page 1: Check numeric indices and 'n', 'p' navigation hint
        trap_bag = io.StringIO()
        with patch("sys.stdout", trap_bag):
            render_shop_tab(app)
        bag_output = ansi_regex.sub("", trap_bag.getvalue())

        self.assertIn("[1] 🍬 Rare Candy: 5 owned", bag_output)
        self.assertIn("Type 'n', 'p', or 'page <N>' to navigate bag!", bag_output)
        self.assertNotIn("Type 'next', 'prev'", bag_output)

        for line in trap_bag.getvalue().split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Bag line exceeds 72 cols: '{clean}'")

        # 3. Render Bag page 2: Check evolution stone numeric index [41]
        app.shop_page = 2
        trap_bag2 = io.StringIO()
        with patch("sys.stdout", trap_bag2):
            render_shop_tab(app)
        bag_output2 = ansi_regex.sub("", trap_bag2.getvalue())

        self.assertIn("[41] 💎 Water Stone: 2 owned", bag_output2)
        self.assertNotIn("[water_stone]", bag_output2)

        for line in trap_bag2.getvalue().split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Bag line exceeds 72 cols: '{clean}'")

        # 4. Use item with numeric ID '41' to evolve active Eevee into Vaporeon
        eevee = MonState(
            base_id=133,
            path_ids=[133],
            planned_path_ids=[133],
            stage_index=0,
            used_at_stage=0,
            rarity=Rarity.UNCOMMON,
            total_forms=1,
            happiness=100
        )
        self.engine.set_active_mon(eevee)

        handle_bag_use(app, "use 41")
        self.assertIn("Vaporeon", app.message)
        self.assertEqual(self.engine.active_mon.current_id, 134)
        self.assertEqual(self.engine.state["inventory"].get("water_stone", 0), 1)

        # 5. Sell item with numeric ID '41' and confirm 'y'
        trap_sell = io.StringIO()
        with patch("sys.stdout", trap_sell), patch("sys.stdin.readline", return_value="y\n"):
            handle_bag_sell(app, "sell 41 1")
        self.assertIn("Successfully sold 1x Water Stone", app.message)
        self.assertEqual(self.engine.state["inventory"].get("water_stone", 0), 0)

        for line in trap_sell.getvalue().split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Sell prompt line exceeds 72 cols: '{clean}'")

        # 6. Backwards compatibility: verify string name 'water_stone' works for use and sell
        self.engine.state["inventory"]["water_stone"] = 2
        eevee2 = MonState(
            base_id=133,
            path_ids=[133],
            planned_path_ids=[133],
            stage_index=0,
            used_at_stage=0,
            rarity=Rarity.UNCOMMON,
            total_forms=1,
            happiness=100
        )
        self.engine.state["dex"] = []
        self.engine.set_active_mon(eevee2)
        handle_bag_use(app, "use water_stone")
        self.assertIn("Vaporeon", app.message)
        self.assertEqual(self.engine.state["inventory"]["water_stone"], 1)

        with patch("sys.stdout", io.StringIO()), patch("sys.stdin.readline", return_value="y\n"):
            handle_bag_sell(app, "sell water_stone 1")
        self.assertIn("Successfully sold 1x Water Stone", app.message)
        self.assertEqual(self.engine.state["inventory"].get("water_stone", 0), 0)

        # 7. Tab 8 Mega Evolution: verify 'n', 'p' paging hint
        self.engine.state["inventory"]["mega_stone_6_X"] = 1
        self.engine.state["inventory"]["mega_stone_6_Y"] = 1
        self.engine.state["page_size_mega"] = 1
        app.mega_page = 1
        trap_mega = io.StringIO()
        with patch("sys.stdout", trap_mega):
            render_mega_evo_tab(app)
        mega_output = ansi_regex.sub("", trap_mega.getvalue())
        self.assertIn("Type 'n', 'p', or 'page <N>' to navigate!", mega_output)
        self.assertNotIn("Type 'next', 'prev'", mega_output)

        for line in trap_mega.getvalue().split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Mega Evo line exceeds 72 cols: '{clean}'")

    def test_bag_help_command(self):
        """Verify the 'help <id>' command on Tab 4 shop and bag tab."""
        import io
        import re
        from unittest.mock import MagicMock
        from poketokenbar.tui_tabs.shop import handle_bag_help, render_shop_tab
        from poketokenbar.game.models import MonState, Rarity

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')

        app = MagicMock()
        app.engine = self.engine
        app.shop_view = "normal"
        app.shop_page = 1
        app.message = ""

        # 1. Clear inventory and active mon
        self.engine.state["inventory"] = {}
        pikachu = MonState(
            base_id=25,
            path_ids=[25],
            planned_path_ids=[25],
            stage_index=0,
            used_at_stage=0,
            rarity=Rarity.COMMON,
            total_forms=1,
            happiness=100
        )
        self.engine.set_active_mon(pikachu)

        # 2. Test missing argument -> Usage message
        handle_bag_help(app, "help")
        self.assertIn("Usage: help <id>", app.message)

        # 3. Test unowned items and absent indices -> Rejected with clear 'You do not have' message
        # Crucial test: Give player Amulet Coin (index 12, contains '50% tokens' in desc).
        # 'help 5' must NEVER match Amulet Coin! It must state user does not have item [5].
        self.engine.state["inventory"]["amulet_coin"] = 1
        handle_bag_help(app, "help 5")
        self.assertEqual(app.message, "You do not have Master Ball in your Bag!")
        self.assertNotIn("Amulet Coin", app.message)

        # Brackets support
        handle_bag_help(app, "help [5]")
        self.assertEqual(app.message, "You do not have Master Ball in your Bag!")

        handle_bag_help(app, "help 16")  # Life Orb (unowned)
        self.assertEqual(app.message, "You do not have Life Orb in your Bag!")

        handle_bag_help(app, "help 14")  # Soothe Bell (unowned)
        self.assertEqual(app.message, "You do not have Soothe Bell in your Bag!")

        handle_bag_help(app, "help life_orb")
        self.assertEqual(app.message, "You do not have Life Orb in your Bag!")

        handle_bag_help(app, "help 999")
        self.assertEqual(app.message, "You do not have item [999] in your Bag!")

        # 4. Give player 1x Life Orb
        self.engine.state["inventory"]["life_orb"] = 1
        handle_bag_help(app, "help 16")
        self.assertIn("Life Orb", app.message)
        self.assertIn("[Held Item]", app.message)
        self.assertIn("(Owned: 1)", app.message)
        self.assertIn("Channels +10% bonus token power", app.message)
        self.assertIn("use 16", app.message)

        # 5. Verify layout compliance (<= 72 columns)
        for line in app.message.split("\n"):
            rendered_len = 4 + len(line.lstrip()) if not line.startswith("  ") else 2 + len(line)
            self.assertLessEqual(rendered_len, 72, f"Help message line exceeds 72 cols: '{line}' ({rendered_len})")

        # 6. Test item name variants (with underscores and spaces)
        handle_bag_help(app, "help life_orb")
        self.assertIn("Life Orb", app.message)
        handle_bag_help(app, "help life orb")
        self.assertIn("Life Orb", app.message)

        # 7. Test equipped held item (count 0 in Bag, but held by active companion)
        self.engine.state["inventory"]["life_orb"] = 0
        pikachu.held_item = "life_orb"
        self.engine.set_active_mon(pikachu)
        handle_bag_help(app, "help 16")
        self.assertIn("Life Orb", app.message)
        self.assertIn("Held by", app.message)
        self.assertIn("unequip", app.message)

        # 8. Test consumable (Rare Candy)
        self.engine.state["inventory"]["rare_candy"] = 3
        handle_bag_help(app, "help 1")
        self.assertIn("Rare Candy", app.message)
        self.assertIn("[Consumable]", app.message)
        self.assertIn("(Owned: 3)", app.message)

        # 9. Test Evolution Stone (Water Stone)
        self.engine.state["inventory"]["water_stone"] = 2
        handle_bag_help(app, "help 41")
        self.assertIn("Water Stone", app.message)
        self.assertIn("[Evolution Stone]", app.message)

        # 10. Test Contraband Fake item (fake_rare_candy)
        self.engine.state["inventory"]["fake_rare_candy"] = 1
        handle_bag_help(app, "help 51")
        self.assertIn("Rare Candy", app.message)
        self.assertIn("[Contraband / Fake]", app.message)

        # 11. Test Tab 4 prompt rendering contains 'help <id>'
        trap = io.StringIO()
        with unittest.mock.patch("sys.stdout", trap):
            render_shop_tab(app)
        shop_output = ansi_regex.sub("", trap.getvalue())
        self.assertIn("help <id>", shop_output)
        for line in trap.getvalue().split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Shop tab line exceeds 72 cols: '{clean}'")

    def test_term_deposit_paging_and_bracket_indexing(self):
        """Verify Active Term Deposits list uses [NUM] indexing format, supports paging, and adheres to 72 cols."""
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.bank import _render_cd_view

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')

        # 1. Setup 8 term deposits in state
        self.engine.state["used_since_install"] = 500_000_000
        self.engine.state["term_deposits"] = []
        for i in range(1, 9):
            self.engine.state["term_deposits"].append({
                "id": i,
                "principal": 10_000_000,
                "term_days": 7,
                "rate": 0.12,
                "days_elapsed": i % 8,
                "current_value": 10_000_000 + i * 1_000_000,
                "matured": (i == 7)
            })
        self.engine.state["page_size_cd"] = 5

        app = MagicMock()
        app.engine = self.engine
        app.cd_page = 1

        # 2. Render Page 1 (items 1..5)
        trap1 = io.StringIO()
        with patch("sys.stdout", trap1):
            _render_cd_view(app, self.engine.available_tokens)
        out1 = ansi_regex.sub("", trap1.getvalue())

        # Check [NUM] indexing format and NOT #NUM
        self.assertIn("[1] 10.0M", out1)
        self.assertIn("[5] 10.0M", out1)
        self.assertNotIn("#1", out1)
        self.assertNotIn("#5", out1)
        self.assertNotIn("[6] 10.0M", out1)
        # In default 'days' sort mode, matured CD is sorted to position 1 on page 1
        self.assertIn("[MATURED! Claimable]", out1)
        # Check paging hint
        self.assertIn("Page 1/2 - Type 'n', 'p', or 'page <N>' to navigate deposits!", out1)

        # Check 72-col compliance
        for line in trap1.getvalue().split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"CD line exceeds 72 cols: '{clean}'")

        # 3. Render Page 2 (items 6..8)
        app.cd_page = 2
        trap2 = io.StringIO()
        with patch("sys.stdout", trap2):
            _render_cd_view(app, self.engine.available_tokens)
        out2 = ansi_regex.sub("", trap2.getvalue())

        self.assertIn("[6] 10.0M", out2)
        self.assertIn("[7] 10.0M", out2)
        self.assertIn("[8] 10.0M", out2)
        self.assertNotIn("[1] 10.0M", out2)
        self.assertIn("[LOCKED]", out2)
        self.assertIn("Page 2/2", out2)

        for line in trap2.getvalue().split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"CD line exceeds 72 cols: '{clean}'")

        # 4. Verify claim and break work with dynamic 1-based display index e.g. '[1]' and '[7]'
        ok_claim, msg_claim = self.engine.claim_cd("[1]")
        self.assertTrue(ok_claim)
        self.assertIn("Claimed CD [1]", msg_claim)

        ok_break, msg_break = self.engine.break_cd("[7]")
        self.assertTrue(ok_break)
        self.assertIn("Early withdrawal of CD [7]", msg_break)

    def test_term_deposits_dynamic_slot_recycling_and_positional_fallback(self):
        """Verify CDs recycle lowest available IDs and support dynamic display indexing."""
        self.engine.state["used_since_install"] = 1_000_000_000
        self.engine.state["term_deposits"] = []

        # Open 3 CDs -> Should have IDs 1, 2, 3
        self.assertTrue(self.engine.open_cd("10m", 3)[0])
        self.assertTrue(self.engine.open_cd("10m", 7)[0])
        self.assertTrue(self.engine.open_cd("10m", 14)[0])
        ids = [c["id"] for c in self.engine.state["term_deposits"]]
        self.assertEqual(ids, [1, 2, 3])

        # Break CD [2] -> CDs 1 and 3 remain
        ok, msg = self.engine.break_cd("[2]")
        self.assertTrue(ok)
        self.assertIn("Early withdrawal of CD [2]", msg)
        ids = [c["id"] for c in self.engine.state["term_deposits"]]
        self.assertEqual(ids, [1, 3])

        # Open a new CD -> Should recycle ID 2 (lowest available) instead of incrementing to 4
        ok, msg = self.engine.open_cd("10m", 3)
        self.assertTrue(ok)
        self.assertIn("CD [2]", msg)

        # Test dynamic index resolution with sparse IDs [10, 20]:
        self.engine.state["term_deposits"] = [
            {"id": 10, "principal": 10_000_000, "term_days": 3, "days_elapsed": 3, "current_value": 12_000_000, "matured": True},
            {"id": 20, "principal": 10_000_000, "term_days": 7, "days_elapsed": 1, "current_value": 10_000_000, "matured": False}
        ]
        # Position 1 is CD [10] (matured). Using "[1]" matches display index 1!
        ok_pos_claim, msg_pos_claim = self.engine.claim_cd("[1]")
        self.assertTrue(ok_pos_claim)
        self.assertIn("Claimed CD [1]", msg_pos_claim)
        self.assertEqual(len(self.engine.state["term_deposits"]), 1)
        self.assertEqual(self.engine.state["term_deposits"][0]["id"], 20)

        # Position 1 is now CD [20]. Early break position 1!
        ok_pos_break, msg_pos_break = self.engine.break_cd("[1]")
        self.assertTrue(ok_pos_break)
        self.assertIn("Early withdrawal of CD [1]", msg_pos_break)
        self.assertEqual(len(self.engine.state["term_deposits"]), 0)

    def test_rocket_operations_and_rank_alignments(self):
        """Verify operations thematic alignment with armory items and rank promotions."""
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.rocket import render_rocket_tab

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        ops = self.engine.get_rocket_operations()
        ops_dict = {op["id"]: op for op in ops}

        # 1. Op 2 (Operative rank approval) aligns with Morale Mist & Chrono Accelerator
        op2 = ops_dict["op_2"]
        self.assertEqual(op2["reward_rank"], "Operative")
        self.assertIn("Operation Chimera", op2["name"])
        self.assertIn("Morale Mist", op2["briefing"])
        self.assertIn("Chrono", op2["briefing"])

        # 2. Op 4 (Operative tier) connects to Bank CDs and Chrono disruptors
        op4 = ops_dict["op_4"]
        self.assertEqual(op4["reward_rank"], "Operative")
        self.assertIn("Bank CD", op4["briefing"])

        # 3. Op 5 (Special Agent rank approval) aligns with Corrupted EXP Splitter
        op5 = ops_dict["op_5"]
        self.assertEqual(op5["reward_rank"], "Special Agent")
        self.assertIn("Corrupted EXP Splitter", op5["briefing"])
        self.assertIn("telemetry", op5["briefing"])

        # 4. Op 7 (Special Agent tier) connects to Morale Mist / 100% Happiness
        op7 = ops_dict["op_7"]
        self.assertEqual(op7["reward_rank"], "Special Agent")
        self.assertIn("Morale Mist", op7["briefing"])

        # 5. Op 8 (Executive rank approval) aligns with Dark Gene Catalyst & evolution
        op8 = ops_dict["op_8"]
        self.assertEqual(op8["reward_rank"], "Executive")
        self.assertIn("Dark Gene Catalyst", op8["briefing"])
        self.assertIn("evolved Pokémon", op8["target_desc"])

        # 6. Op 10 (Commander rank approval) aligns with Team Rocket Authority
        op10 = ops_dict["op_10"]
        self.assertEqual(op10["reward_rank"], "Commander")
        self.assertIn("Commander Authority", op10["briefing"])

        # 7. Test op_8 objective check with evolved pokemon vs shares
        self.engine.state["rocket_ops"]["op_8"] = {"status": "active", "progress": 25_000_000, "claimed": False, "objective_done": False}
        self.engine.state["investments"] = {"viridian": 0}
        self.engine.state["dex"] = []
        if self.engine.active_mon:
            self.engine.active_mon.stage_index = 0
        ok_8_fail, msg_8_fail = self.engine.check_operation_objective("op_8")
        self.assertFalse(ok_8_fail)
        self.assertIn("Requires 2+ evolved Pokémon", msg_8_fail)

        # Satisfy with 2 evolved pokemon
        self.engine.state["dex"] = [
            {"id": "sp_2", "species_id": 2, "status": "inactive", "mon_state": {"stage_index": 1}},
            {"id": "sp_5", "species_id": 5, "status": "inactive", "mon_state": {"stage_index": 1}},
        ]
        ok_8_pass, msg_8_pass = self.engine.check_operation_objective("op_8")
        self.assertTrue(ok_8_pass)

        # Or satisfy with VRDN shares
        self.engine.state["dex"] = []
        self.engine.state["rocket_ops"]["op_8"]["objective_done"] = False
        self.engine.state["investments"] = {"viridian": 10}
        ok_8_shares, _ = self.engine.check_operation_objective("op_8")
        self.assertTrue(ok_8_shares)

        # 8. Test Dossiers #002, #005, #008, #010
        dossiers = {d["id"]: d for d in self.engine.get_rocket_dossier()}
        self.assertIn("Chrono", dossiers[2]["title"])
        self.assertIn("Telemetry", dossiers[5]["title"])
        self.assertIn("Mutagen Protocol", dossiers[8]["title"])
        self.assertIn("Supreme Authority", dossiers[10]["title"])

        # 9. Verify layout compliance (<= 72 columns) when reading each dossier
        app = MagicMock()
        app.engine = self.engine
        app.rocket_subview = "read_intel"
        self.engine.state["rocket_alliance_accepted"] = True
        self.engine.state["rocket_intel_unlocked"] = ["intel_001", "intel_002", "intel_005", "intel_008", "intel_010"]

        for d_id in [2, 5, 8, 10]:
            app.rocket_reading_file = d_id
            trap = io.StringIO()
            with patch("sys.stdout", trap):
                render_rocket_tab(app)
            for line in trap.getvalue().split("\n"):
                clean = ansi_regex.sub("", line)
                self.assertLessEqual(len(clean), 72, f"Dossier #{d_id} line exceeds 72 cols: '{clean}' (len={len(clean)})")

        # 10. Verify layout compliance for operations rendering
        app.rocket_subview = "ops"
        for op_key in ["op_2", "op_4", "op_5", "op_7", "op_8", "op_10"]:
            for k in self.engine.state["rocket_ops"]:
                self.engine.state["rocket_ops"][k]["status"] = "locked"
            self.engine.state["rocket_ops"][op_key]["status"] = "active"
            trap_op = io.StringIO()
            with patch("sys.stdout", trap_op):
                render_rocket_tab(app)
            for line in trap_op.getvalue().split("\n"):
                clean = ansi_regex.sub("", line)
                self.assertLessEqual(len(clean), 72, f"Op {op_key} line exceeds 72 cols: '{clean}' (len={len(clean)})")

    def test_rocket_operation_dialogues_and_immersion(self):
        """Verify immersive operation dialogues for all 10 operations and 72-col compliance."""
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.rocket import render_operation_dialogue, handle_rocket_command

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        app = MagicMock()
        app.engine = self.engine
        app.rocket_subview = "ops"

        # 1. Verify dialogues exist and are complete for all 10 operations
        for i in range(1, 11):
            d_info = self.engine.get_operation_dialogue(str(i))
            self.assertIsNotNone(d_info, f"Dialogue for Operation {i} should exist.")
            self.assertIn("title", d_info)
            self.assertIn("location", d_info)
            self.assertEqual(d_info["speaker"], "Commander Petrel")
            self.assertGreater(len(d_info["dialogue"]), 0)
            self.assertGreater(len(d_info["tactical_orders"]), 0)

        # 2. Verify render_operation_dialogue strictly obeys <= 72 columns for all 10 ops
        for i in range(1, 11):
            trap = io.StringIO()
            with patch("sys.stdout", trap), patch("sys.stdin.readline", return_value="\n"):
                render_operation_dialogue(app, str(i))
            out = trap.getvalue()
            self.assertIn("TACTICAL COMM-LINK", out)
            self.assertIn("Commander Petrel", out)
            for line in out.split("\n"):
                clean = ansi_regex.sub("", line)
                self.assertLessEqual(len(clean), 72, f"Op {i} dialogue line exceeds 72 cols: '{clean}' (len={len(clean)})")

        # 3. Test 'briefing' command replays dialogue
        self.engine.state["rocket_alliance_accepted"] = True
        self.engine.state["rocket_ops"]["op_1"]["status"] = "available"
        self.engine.state["rocket_ops"]["op_1"]["claimed"] = False
        trap_b = io.StringIO()
        with patch("sys.stdout", trap_b), patch("sys.stdin.readline", return_value="\n"):
            handle_rocket_command(app, "briefing")
        self.assertIn("Replayed Operation 1 tactical briefing", app.message)
        self.assertIn("TACTICAL MISSION DIRECTIVES", trap_b.getvalue())

        # 4. Test 'start operation' renders dialogue and activates operation
        trap_start = io.StringIO()
        with patch("sys.stdout", trap_start), patch("sys.stdin.readline", return_value="\n"):
            handle_rocket_command(app, "start operation")
        self.assertEqual(self.engine.state["rocket_ops"]["op_1"]["status"], "active")
        self.assertIn("Operation 1 activated", app.message)
        self.assertIn("TACTICAL COMM-LINK", trap_start.getvalue())

        # 5. Test claim command in Tab 12 routes to Rocket operations instead of daily quests
        from poketokenbar.tui import PokeTokenBarTUI
        tui = PokeTokenBarTUI()
        tui.engine = self.engine
        tui.tracker.get_summary = MagicMock(return_value={"total_tokens": 0, "active_days": []})
        tui.current_tab = 12
        self.engine.state["unread_alerts"] = []
        self.engine.state["rocket_story_unlocked"] = True
        self.engine.state["rocket_story_viewed"] = True
        self.engine.state["rocket_alliance_accepted"] = True
        self.engine.state["rocket_ops"]["op_1"]["status"] = "active"
        self.engine.state["rocket_ops"]["op_1"]["progress"] = 5_000_000
        self.engine.state["rocket_ops"]["op_1"]["objective_done"] = True
        self.engine.state["rocket_ops"]["op_1"]["claimed"] = False
        self.engine.state["rocket_ops"]["op_1"]["briefing_viewed"] = True
        self.engine.state["expedition_logs"] = [{"id": 1}, {"id": 2}]
        trap_out = io.StringIO()
        with patch("sys.stdin", io.StringIO("claim\nq\n")), patch("sys.stdout", trap_out):
            tui.run()
        self.assertTrue(self.engine.state["rocket_ops"]["op_1"]["claimed"])
        self.assertIn("Operation 1 Completed", trap_out.getvalue())

    def test_rocket_operation_requirements_tracing_and_auto_briefing(self):
        """Verify explicit multi-requirement tracing, hints order, and auto-briefing."""
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.rocket import render_rocket_tab, handle_rocket_command
        from poketokenbar.tui import PokeTokenBarTUI

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        app = MagicMock()
        app.engine = self.engine
        app.rocket_subview = "ops"
        self.engine.state["rocket_story_unlocked"] = True
        self.engine.state["rocket_alliance_accepted"] = True

        # 1. Test get_operation_requirements returns individual tracked tasks
        # Test Op 1 initial
        self.engine.state["rocket_ops"]["op_1"] = {
            "status": "available",
            "progress": 0,
            "claimed": False,
            "objective_done": False,
            "boss_hp_remaining": 0,
            "briefing_viewed": True,
            "expeditions_done": 0,
            "battle_wins": 0,
            "black_market_trades": 0
        }
        self.engine.state["expeditions"] = []
        self.engine.state["expedition_logs"] = [
            {"id": 1}, {"id": 2}, {"id": 3}
        ]
        reqs1 = self.engine.get_operation_requirements("1")
        self.assertEqual(len(reqs1), 2)
        self.assertEqual(reqs1[0]["name"], "Coding Tokens")
        self.assertEqual(reqs1[0]["target"], 5_000_000)
        self.assertFalse(reqs1[0]["is_met"])
        self.assertEqual(reqs1[1]["name"], "Scout Expeditions")
        self.assertEqual(reqs1[1]["target"], 2)
        self.assertEqual(reqs1[1]["current"], 0)
        self.assertFalse(reqs1[1]["is_met"])

        # Trace Op 1 progress when 1 expedition is logged
        self.engine.state["rocket_ops"]["op_1"]["expeditions_done"] = 1
        reqs1_step = self.engine.get_operation_requirements("1")
        self.assertEqual(reqs1_step[1]["current"], 1)
        self.assertFalse(reqs1_step[1]["is_met"])

        # Trace Op 1 progress when 2 expeditions are logged
        self.engine.state["rocket_ops"]["op_1"]["expeditions_done"] = 2
        reqs1_done = self.engine.get_operation_requirements("1")
        self.assertEqual(reqs1_done[1]["current"], 2)
        self.assertTrue(reqs1_done[1]["is_met"])

        # Test Op 2 requirements (Tokens + Trainer Battle Wins)
        self.engine.state["trainer_battles"] = {"wins": 50}
        self.engine.state["rocket_ops"]["op_2"]["battle_wins"] = 1
        reqs2 = self.engine.get_operation_requirements("2")
        self.assertEqual(len(reqs2), 2)
        self.assertEqual(reqs2[1]["name"], "Battle Arena Wins")
        self.assertEqual(reqs2[1]["current"], 1)
        self.assertFalse(reqs2[1]["is_met"])

        # Test Op 4 requirements (Tokens + Bank CD)
        self.engine.state["term_deposits"] = [{"id": 101}]
        reqs4 = self.engine.get_operation_requirements("4")
        self.assertEqual(len(reqs4), 2)
        self.assertEqual(reqs4[1]["name"], "Active Bank CD")
        self.assertTrue(reqs4[1]["is_met"])

        # Test Op 5 requirements (Active Expeditions + Black Market Trade)
        self.engine.state["expeditions"] = [{"id": 1}, {"id": 2}]
        self.engine.state["rocket_ops"]["op_5"]["black_market_trades"] = 1
        reqs5 = self.engine.get_operation_requirements("5")
        self.assertEqual(len(reqs5), 2)
        self.assertEqual(reqs5[0]["name"], "Active Expeditions")
        self.assertTrue(reqs5[0]["is_met"])
        self.assertEqual(reqs5[1]["name"], "Black Market Trade")
        self.assertTrue(reqs5[1]["is_met"])

        # Test Op 7 requirements (Tokens + Happiness)
        self.engine.state["happiness"] = 100
        reqs7 = self.engine.get_operation_requirements("7")
        self.assertEqual(len(reqs7), 2)
        self.assertEqual(reqs7[1]["name"], "Companion Happiness")
        self.assertTrue(reqs7[1]["is_met"])

        # 2. Test command hints order: briefing first, start operation second
        self.engine.state["rocket_ops"]["op_1"]["status"] = "available"
        self.engine.state["rocket_ops"]["op_1"]["briefing_viewed"] = True
        trap_render = io.StringIO()
        with patch("sys.stdout", trap_render):
            render_rocket_tab(app)
        raw_out = ansi_regex.sub("", trap_render.getvalue())
        self.assertIn("Requirements:", raw_out)
        self.assertIn("• Coding Tokens", raw_out)
        self.assertIn("• Scout Expeditions", raw_out)
        # Verify briefing hint appears before start operation hint
        pos_briefing = raw_out.find("Type 'briefing'")
        pos_start = raw_out.find("Type 'start operation'")
        self.assertNotEqual(pos_briefing, -1)
        self.assertNotEqual(pos_start, -1)
        self.assertLess(pos_briefing, pos_start, "'briefing' command hint must appear before 'start operation'")

        # 3. Test 72-column layout compliance with traced requirements
        for line in raw_out.split("\n"):
            self.assertLessEqual(len(line), 72, f"Line exceeds 72 cols: '{line}' (len={len(line)})")

        # 4. Test automatic briefing display in TUI loop
        tui = PokeTokenBarTUI()
        tui.engine = self.engine
        tui.tracker.get_summary = MagicMock(return_value={"total_tokens": 0, "active_days": []})
        tui.current_tab = 12
        tui.rocket_subview = "ops"
        self.engine.state["unread_alerts"] = []
        self.engine.state["rocket_story_viewed"] = True
        self.engine.state["rocket_alliance_accepted"] = True
        self.engine.state["rocket_ops"]["op_1"]["status"] = "available"
        self.engine.state["rocket_ops"]["op_1"]["briefing_viewed"] = False

        trap_auto = io.StringIO()
        with patch("sys.stdin", io.StringIO("q\n")), patch("sys.stdout", trap_auto):
            tui.run()
        # Briefing should have been triggered automatically
        self.assertTrue(self.engine.state["rocket_ops"]["op_1"]["briefing_viewed"])
        self.assertIn("TACTICAL COMM-LINK", trap_auto.getvalue())

    def test_bank_repossession_liquidates_cds_and_stocks(self):
        """Verify that bank repossession at day 7 liquidates CDs and stocks before touching inventory."""
        import datetime
        from unittest.mock import patch

        _orig_dt = datetime.datetime

        # 1. Setup loan nearing repossession (day 6 -> day 7)
        self.engine.state["install_baseline_set"] = True
        self.engine.state["bank_loan"] = 50_000_000
        self.engine.state["loan_days_active"] = 6
        self.engine.state["bank_balance"] = 0
        total_used = 100_000_000
        self.engine.state["used_since_install"] = total_used
        self.engine.state["spent_tokens"] = total_used + 1000

        # 1 matured CD worth 20M
        self.engine.state["term_deposits"] = [{
            "id": 1,
            "principal": 20_000_000,
            "term_days": 7,
            "rate": 0.12,
            "days_elapsed": 7,
            "current_value": 20_000_000,
            "matured": True
        }]

        # 4 shares of Silph Co (base 10M, 90% forced sale value = 9M each)
        self.engine.state["investments"] = {"silph": 4, "devon": 0, "aether": 0, "mauville": 0, "macro": 0, "viridian": 0}
        self.engine.get_or_init_stock_market()
        self.engine.state["stock_market"]["prices"]["silph"] = 10_000_000
        self.engine.state["stock_market"]["cost_basis"]["silph"] = 40_000_000

        # Bag items that should be spared if CD + stocks cover the debt
        self.engine.state["inventory"] = {"rare_candy": 10}

        # Set last active date to yesterday to trigger 1-day rollover
        yesterday_str = "2026-09-01"
        today_str = "2026-09-02"
        self.engine.state["last_active_date"] = yesterday_str

        mock_dt = _orig_dt.strptime(today_str, "%Y-%m-%d")
        with patch.object(self.engine, "_rollover_stock_market"):
            with patch("poketokenbar.game.companion.datetime.datetime") as mock_datetime:
                mock_datetime.now.return_value = mock_dt
                mock_datetime.strptime.side_effect = lambda *args, **kwargs: _orig_dt.strptime(*args, **kwargs)
                events = self.engine.process_usage(total_used + 1000, active_days=[yesterday_str, today_str])

        # CD liquidation: 20M seized -> CD removed
        self.assertEqual(len(self.engine.state["term_deposits"]), 0)
        self.assertTrue(any("Liquidated 1 CD(s) for 20.0M tokens" in e for e in events))

        # Stock liquidation: shares sold to satisfy debt
        self.assertEqual(self.engine.state["investments"]["silph"], 0)
        self.assertTrue(any("Liquidated" in e and "SILPH" in e for e in events))

        # Loan completely cleared
        self.assertEqual(self.engine.state["bank_loan"], 0)
        self.assertEqual(self.engine.state["loan_days_active"], 0)
        self.assertTrue(any("All companions suffered a 50 happiness penalty" in e for e in events))

    def test_bank_checking_tab_renders_repossession_protocol_72_cols(self):
        """Verify checking subtab renders updated Repossession Protocol within 72 columns."""
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.bank import render_bank_tab

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        self.engine.state["bank_loan"] = 20_000_000
        self.engine.state["loan_days_active"] = 5

        app = MagicMock()
        app.engine = self.engine
        app.bank_subtab = "checking"

        trap = io.StringIO()
        with patch("sys.stdout", trap):
            render_bank_tab(app)

        output = trap.getvalue()
        self.assertIn("Loan Deadline:", output)
        self.assertIn("D-2", output)
        self.assertIn("Repossession Protocol:", output)
        self.assertIn("Liquidation of Term Deposits (CDs)", output)
        self.assertIn("Liquidation of Corporate Stock Shares", output)

        for line in output.split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Bank Checking line exceeds 72 cols: '{clean}'")

    def test_bank_loan_repossession_deadline_d_day_formatting(self):
        """Verify loan repossession deadline is formatted as D-<NumOfDays> across countdown days."""
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.bank import render_bank_tab

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        self.engine.state["bank_loan"] = 10_000_000

        app = MagicMock()
        app.engine = self.engine
        app.bank_subtab = "checking"

        # Days active -> Expected D-day countdown
        cases = [
            (0, "D-7"),
            (1, "D-6"),
            (2, "D-5"),
            (5, "D-2"),
            (6, "D-1"),
            (7, "D-0"),
        ]

        for days_active, expected_d_day in cases:
            self.engine.state["loan_days_active"] = days_active
            trap = io.StringIO()
            with patch("sys.stdout", trap):
                render_bank_tab(app)
            output = trap.getvalue()
            clean_output = ansi_regex.sub("", output)
            self.assertIn(f"Loan Deadline:  {expected_d_day} until repossession", clean_output)
            if days_active == 6:
                self.assertIn("FINAL DAY BEFORE REPOSSESSION (D-1)", output)
            for line in output.split("\n"):
                clean = ansi_regex.sub("", line)
                self.assertLessEqual(len(clean), 72, f"Line exceeds 72 cols: '{clean}'")

    def test_rocket_operation_token_tracking_with_process_usage(self):
        """Verify Rocket Operations track raw coding tokens regardless of companion happiness, auto-activate from available, and save state."""
        self.engine.state["install_baseline_set"] = True
        self.engine.state["rocket_story_unlocked"] = True
        self.engine.state["rocket_alliance_accepted"] = True
        self.engine.state["rocket_ops"]["op_1"]["status"] = "available"
        self.engine.state["rocket_ops"]["op_1"]["progress"] = 0
        self.engine.state["rocket_ops"]["op_1"]["claimed"] = False

        mon, _ = self.engine.hatch_egg(0)
        self.engine.set_active_mon(mon)
        mon.happiness = 0
        self.engine.state["happiness"] = 0

        initial_used = self.engine.state.get("used_since_install", 0)
        burn_tokens = 500_000
        new_total = initial_used + burn_tokens

        # Process usage with delta = 500,000
        events = self.engine.process_usage(new_total)

        # Op 1 should have auto-activated and gained exactly 500,000 tokens
        op1 = self.engine.state["rocket_ops"]["op_1"]
        self.assertEqual(op1["status"], "active")
        self.assertEqual(op1["progress"], 500_000)

        # start_rocket_operation should return True when already active
        ok_start, msg_start = self.engine.start_rocket_operation("1")
        self.assertTrue(ok_start)
        self.assertIn("already active", msg_start)

        # Burn remainder to reach target (5,000,000)
        events = self.engine.process_usage(new_total + 4_500_000)
        self.assertEqual(self.engine.state["rocket_ops"]["op_1"]["progress"], 5_000_000)
        self.assertTrue(any("Rocket Operation Ready!" in e for e in events))

    def test_rocket_boss_tactical_combat_handler(self):
        """Verify RocketBattleHandler initialization, multi-stage boss gauntlet, stance shifts, and victory condition."""
        from poketokenbar.game.rocket_battle import RocketBattleHandler, get_effectiveness, generate_player_moves

        # 1. Type effectiveness including glitch
        self.assertEqual(get_effectiveness("glitch", "psychic"), 2.0)
        self.assertEqual(get_effectiveness("glitch", "ghost"), 2.0)
        self.assertEqual(get_effectiveness("fighting", "glitch"), 0.0)
        self.assertEqual(get_effectiveness("water", "fire"), 2.0)

        # 2. Setup engine state for Op 3
        self.engine.state["install_baseline_set"] = True
        self.engine.state["rocket_story_unlocked"] = True
        self.engine.state["rocket_alliance_accepted"] = True
        self.engine.state["rocket_ops"]["op_3"]["status"] = "active"
        self.engine.state["rocket_ops"]["op_3"]["claimed"] = False
        self.engine.state["rocket_ops"]["op_3"]["objective_done"] = False

        handler = RocketBattleHandler(self.engine)
        squad = handler.auto_assemble_squad()
        self.assertEqual(len(squad), 6)

        # 3. Start boss battle
        ok, msg = handler.start_boss_battle("3")
        self.assertTrue(ok)
        self.assertIn("Prototype Chimera-001", msg)

        st = handler._get_state()
        self.assertEqual(st["status"], "in_combat")
        self.assertEqual(len(st["boss_team"]), 1)
        self.assertEqual(st["boss_team"][0]["name"], "Prototype Chimera-001")
        self.assertEqual(st["boss_hps"][0], 150_000)

        # 4. Player moves generation
        moves = generate_player_moves("fire")
        self.assertEqual(len(moves), 4)
        self.assertIn("Fire Strike", moves[0]["name"])

        # 5. Execute Turn
        ok, msg = handler.execute_turn(0)
        self.assertTrue(ok)
        st = handler._get_state()
        self.assertGreater(st["turn_count"], 0)
        self.assertLess(st["boss_hps"][0], st["boss_max_hps"][0])

        # 6. Test Chimera stance shift on even turns
        st["turn_count"] = 3
        handler._save_state(st)
        ok, msg = handler.execute_turn(0)
        self.assertTrue(ok)
        st = handler._get_state()
        chimera = st["boss_team"][0]
        self.assertIn(chimera["type"], ["fire", "ice", "electric", "dragon"])

        # 7. Defeat Chimera -> Victory!
        st["boss_hps"][0] = 10
        handler._save_state(st)
        ok, msg = handler.execute_turn(0)
        self.assertTrue(ok)
        st = handler._get_state()
        self.assertEqual(st["status"], "win")
        self.assertTrue(self.engine.state["rocket_ops"]["op_3"]["objective_done"])
        self.assertEqual(self.engine.state["rocket_ops"]["op_3"]["boss_hp_remaining"], 0)

        # 10. Test swap_pokemon
        handler.start_boss_battle("3")
        ok, msg = handler.swap_pokemon(1)
        self.assertTrue(ok)
        self.assertEqual(handler._get_state()["player_active_index"], 1)

        # 11. Test run_away
        ok, msg = handler.run_away()
        self.assertTrue(ok)
        self.assertEqual(handler._get_state(), {})

    def test_72_column_layout_compliance_tab_12_combat(self):
        """Verify Rocket Tab [12] combat screen strictly adheres to <= 72 columns."""
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.rocket import render_rocket_tab, handle_rocket_command
        from poketokenbar.game.rocket_battle import RocketBattleHandler

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        app = MagicMock()
        app.engine = self.engine
        app.rocket_subview = "ops"
        self.engine.state["rocket_story_unlocked"] = True
        self.engine.state["rocket_alliance_accepted"] = True
        self.engine.state["rocket_ops"]["op_3"]["status"] = "active"
        self.engine.state["rocket_ops"]["op_3"]["claimed"] = False
        self.engine.state["rocket_ops"]["op_3"]["objective_done"] = False

        handler = RocketBattleHandler(self.engine)
        handler.start_boss_battle("3")

        # 1. In combat screen
        trap = io.StringIO()
        with patch("sys.stdout", trap):
            render_rocket_tab(app)
        combat_output = trap.getvalue()
        self.assertIn("TACTICAL COMBAT", combat_output)
        self.assertIn("Prototype Chimera-001", combat_output)
        self.assertNotIn("[O] Operations", combat_output)
        self.assertNotIn("[I] Intel Dossier", combat_output)
        self.assertNotIn("[A] Covert Armory", combat_output)
        for line in combat_output.split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Combat screen line exceeds 72 cols: '{clean}' (len={len(clean)})")

        # 2. Test command handling while in combat
        handle_rocket_command(app, "fight 1")
        self.assertIsNotNone(app.message)

        # 3. Test Victory screen layout
        st = handler._get_state()
        st["status"] = "win"
        self.engine.state["rocket_ops"]["op_3"]["objective_done"] = True
        handler._save_state(st)
        trap_win = io.StringIO()
        with patch("sys.stdout", trap_win):
            render_rocket_tab(app)
        for line in trap_win.getvalue().split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Victory screen line exceeds 72 cols: '{clean}' (len={len(clean)})")

        # 4. Test Blackout / Loss screen layout
        st["status"] = "loss"
        handler._save_state(st)
        trap_loss = io.StringIO()
        with patch("sys.stdout", trap_loss):
            render_rocket_tab(app)
        for line in trap_loss.getvalue().split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Loss screen line exceeds 72 cols: '{clean}' (len={len(clean)})")

        # Clean up combat state
        handler.run_away()

    def test_initialize_rocket_process(self):
        """Verify initialize_rocket_process unlocks Tab 12, initializes Op 1, and resets progress cleanly."""
        self.engine.state["rocket_story_unlocked"] = False
        self.engine.state["rocket_story_viewed"] = False
        self.engine.state["rocket_alliance_accepted"] = False
        self.engine.state["rocket_reputation"] = 0

        ok, msg = self.engine.initialize_rocket_process()
        self.assertTrue(ok)
        self.assertIn("initialized", msg.lower())

        self.assertTrue(self.engine.state["rocket_story_unlocked"])
        self.assertFalse(self.engine.state["rocket_story_viewed"])
        self.assertFalse(self.engine.state["rocket_alliance_accepted"])
        self.assertEqual(self.engine.state["rocket_transmission_state"], "intro")
        self.assertEqual(self.engine.state["rocket_rank"], "Informant")
        self.assertEqual(self.engine.state["rocket_reputation"], 0)
        self.assertEqual(self.engine.state["rocket_ops"]["op_1"]["status"], "available")
        self.assertEqual(self.engine.state["rocket_ops"]["op_2"]["status"], "locked")
        self.assertEqual(self.engine.state["rocket_intel_unlocked"], ["intel_001"])
        self.assertTrue(self.engine.state["permanent_black_market"])
        self.assertFalse(self.engine.state["has_exp_splitter"])
        self.assertEqual(self.engine.state["rocket_battle_state"], {})
        self.assertTrue(any("Team Rocket frequency initialized" in a for a in self.engine.state["unread_alerts"]))

        # Re-initialize when in-progress
        self.engine.state["rocket_ops"]["op_1"]["claimed"] = True
        self.engine.state["rocket_ops"]["op_2"]["status"] = "active"
        self.engine.state["rocket_reputation"] = 1
        self.engine.state["rocket_rank"] = "Operative"

        ok2, msg2 = self.engine.initialize_rocket_process()
        self.assertTrue(ok2)
        self.assertEqual(self.engine.state["rocket_ops"]["op_1"]["status"], "available")
        self.assertFalse(self.engine.state["rocket_ops"]["op_1"]["claimed"])
        self.assertEqual(self.engine.state["rocket_ops"]["op_2"]["status"], "locked")
        self.assertEqual(self.engine.state["rocket_reputation"], 0)
        self.assertEqual(self.engine.state["rocket_rank"], "Informant")

        # Preserves purchased permanent equipment across campaign resets
        self.engine.state["permanent_black_market"] = True
        self.engine.state["has_exp_splitter"] = True
        ok3, _ = self.engine.initialize_rocket_process()
        self.assertTrue(ok3)
        self.assertTrue(self.engine.state["permanent_black_market"])
        self.assertTrue(self.engine.state["has_exp_splitter"])

    def test_rocket_armory_buy_from_any_subview_and_fuzzy_code(self):
        """Verify armory tech codes resolve and buy/claim commands notify that perks are auto-granted."""
        from poketokenbar.tui_tabs.rocket import (
            handle_rocket_command, _resolve_armory_tech_code
        )
        self.assertEqual(_resolve_armory_tech_code("pass"), "pass")
        self.assertEqual(_resolve_armory_tech_code("black pass"), "pass")
        self.assertEqual(
            _resolve_armory_tech_code("syndicate black pass"), "pass"
        )
        self.assertEqual(_resolve_armory_tech_code("mist"), "spray")
        self.assertEqual(
            _resolve_armory_tech_code("chrono accelerator"), "chrono"
        )

        app = MagicMock()
        app.engine = self.engine
        app.rocket_subview = "ops"
        self.engine.state["rocket_alliance_accepted"] = True
        self.engine.state["rocket_rank"] = "Informant"

        # Attempting 'buy black pass' informs that perks are automatic
        handle_rocket_command(app, "buy black pass")
        self.assertIn("Covert Armory perks are automatically granted", app.message)
        self.assertIn("No purchase required", app.message)

        # Attempting 'claim pass' informs that perks are automatic
        handle_rocket_command(app, "claim pass")
        self.assertIn("Covert Armory perks are automatically granted", app.message)
        self.assertIn("No claim or purchase required", app.message)

    def test_render_settings_tab_and_rocket_init_option(self):
        """Verify Option 8 displays correctly in Settings tab and complies with 72-column limit."""
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.settings import render_settings_tab

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        app = MagicMock()
        app.engine = self.engine

        # Case 1: Uninitialized (Option 11 is on Page 2)
        app.settings_page = 2
        self.engine.state["rocket_story_unlocked"] = False
        trap = io.StringIO()
        with patch("sys.stdout", trap):
            render_settings_tab(app)
        output = trap.getvalue()
        self.assertIn("[11] Team Rocket Process:", output)
        self.assertIn("UNINITIALIZED", output)
        self.assertIn("rocket init", output)
        for line in output.split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Settings (uninitialized) exceeds 72 cols: '{clean}' (len={len(clean)})")

        # Case 2: Active
        app.settings_page = 2
        self.engine.state["rocket_story_unlocked"] = True
        self.engine.state["rocket_rank"] = "Informant"
        self.engine.state["rocket_reputation"] = 3
        trap2 = io.StringIO()
        with patch("sys.stdout", trap2):
            render_settings_tab(app)
        output2 = trap2.getvalue()
        self.assertIn("[11] Team Rocket Process:", output2)
        self.assertIn("ACTIVE", output2)
        self.assertNotIn("Rep:", output2)
        self.assertNotIn("Informant", output2)
        for line in output2.split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Settings (active) exceeds 72 cols: '{clean}' (len={len(clean)})")

    def test_cli_settings_init_rocket(self):
        """Verify CLI settings --init-rocket executes initialization."""
        from unittest.mock import MagicMock
        from poketokenbar.cli import cmd_settings

        self.engine.state["rocket_story_unlocked"] = False
        args = MagicMock()
        args.init_rocket = True
        args.auto_track = None
        args.interval = None

        cmd_settings(self.engine, args)
        self.assertTrue(self.engine.state["rocket_story_unlocked"])
        self.assertEqual(self.engine.state["rocket_ops"]["op_1"]["status"], "available")

    def test_settings_tab_paging_navigation_and_clamping(self):
        """Verify settings tab renders correct items per page and clamps page bounds."""
        import io
        from poketokenbar.tui_tabs.settings import render_settings_tab

        app = MagicMock()
        app.engine = self.engine
        self.engine.state["page_size_settings"] = 6

        # Page 1: Items 1-6
        app.settings_page = 1
        trap1 = io.StringIO()
        with patch("sys.stdout", trap1):
            render_settings_tab(app)
        out1 = trap1.getvalue()
        self.assertIn("Page 1/2", out1)
        self.assertIn("[1] Token Tracking Baseline:", out1)
        self.assertIn("[6] Roster Page Size:", out1)
        self.assertNotIn("[7] Bag Page Size:", out1)
        self.assertNotIn("[12] Reset Game Progress:", out1)

        # Page 2: Items 7-12
        app.settings_page = 2
        trap2 = io.StringIO()
        with patch("sys.stdout", trap2):
            render_settings_tab(app)
        out2 = trap2.getvalue()
        self.assertIn("Page 2/2", out2)
        self.assertNotIn("[1] Token Tracking Baseline:", out2)
        self.assertNotIn("[6] Roster Page Size:", out2)
        self.assertIn("[7] Bag Page Size:", out2)
        self.assertIn("[11] Team Rocket Process:", out2)
        self.assertIn("[12] Reset Game Progress:", out2)

        # Out-of-bounds upper clamping (page 99 -> 2)
        app.settings_page = 99
        trap3 = io.StringIO()
        with patch("sys.stdout", trap3):
            render_settings_tab(app)
        self.assertEqual(app.settings_page, 2)

        # Out-of-bounds lower clamping (page -5 -> 1)
        app.settings_page = -5
        trap4 = io.StringIO()
        with patch("sys.stdout", trap4):
            render_settings_tab(app)
        self.assertEqual(app.settings_page, 1)

    def test_settings_tab_custom_page_sizes(self):
        """Verify settings tab adapts dynamically to custom page_size_settings values."""
        import io
        from poketokenbar.tui_tabs.settings import render_settings_tab

        app = MagicMock()
        app.engine = self.engine

        # 4 items per page = 3 pages total
        self.engine.state["page_size_settings"] = 4
        app.settings_page = 3
        trap = io.StringIO()
        with patch("sys.stdout", trap):
            render_settings_tab(app)
        out = trap.getvalue()
        self.assertIn("Page 3/3", out)
        self.assertIn("[9] Mega Evo Page Size:", out)
        self.assertIn("[12] Reset Game Progress:", out)
        self.assertNotIn("[1] Token Tracking Baseline:", out)

        # 12 items per page = 1 page total (no page tag)
        self.engine.state["page_size_settings"] = 12
        app.settings_page = 1
        trap_all = io.StringIO()
        with patch("sys.stdout", trap_all):
            render_settings_tab(app)
        out_all = trap_all.getvalue()
        self.assertNotIn("Page 1/1", out_all)
        self.assertIn("[1] Token Tracking Baseline:", out_all)
        self.assertIn("[12] Reset Game Progress:", out_all)

    def test_tui_settings_page_and_pagesize_commands(self):
        """Verify TUI event loop handling for n/p/page and pagesize settings commands on tab 11."""
        from poketokenbar.tui import PokeTokenBarTUI

        app = PokeTokenBarTUI()
        app.current_tab = 11
        app.settings_page = 1
        app.engine = self.engine

        # Mock readline for "n"
        with patch("sys.stdin.readline", side_effect=["n", "q"]):
            with patch("sys.stdout"):
                app.run()
        self.assertEqual(app.settings_page, 2)

        # Mock readline for "p"
        with patch("sys.stdin.readline", side_effect=["p", "q"]):
            with patch("sys.stdout"):
                app.run()
        self.assertEqual(app.settings_page, 1)

        # Mock readline for "page 2"
        with patch("sys.stdin.readline", side_effect=["page 2", "q"]):
            with patch("sys.stdout"):
                app.run()
        self.assertEqual(app.settings_page, 2)

        # Mock readline for "pagesize settings 5"
        trap = io.StringIO()
        with patch("sys.stdin.readline", side_effect=["pagesize settings 5", "q"]):
            with patch("sys.stdout", trap):
                app.run()
        self.assertEqual(self.engine.state["page_size_settings"], 5)
        self.assertIn("Settings page size set to 5", trap.getvalue())

        # Mock readline for "pagesize settings 0" (invalid)
        trap_err = io.StringIO()
        with patch("sys.stdin.readline", side_effect=["pagesize settings 0", "q"]):
            with patch("sys.stdout", trap_err):
                app.run()
        self.assertIn("must be at least 1", trap_err.getvalue())

        # Mock readline for "pagesize cd 7"
        trap_cd = io.StringIO()
        with patch("sys.stdin.readline", side_effect=["pagesize cd 7", "q"]):
            with patch("sys.stdout", trap_cd):
                app.run()
        self.assertEqual(self.engine.state["page_size_cd"], 7)
        self.assertIn("Term Deposits page size set to 7", trap_cd.getvalue())

    def test_prototype_chimera_custom_sprite_resolution(self):
        """Test that Prototype Chimera-001 (species 2012) resolves to its individual custom sprite."""
        from poketokenbar.sprite_renderer import SpriteRenderer
        import re

        sprite_path = self.engine.api.download_sprite(2012)
        self.assertIsNotNone(sprite_path)
        self.assertTrue(sprite_path.exists())
        self.assertTrue(sprite_path.name.endswith("2012.png"))

        # Verify ANSI render works cleanly
        ansi = SpriteRenderer.render_png_to_ansi(sprite_path, 24)
        self.assertIn("▀", ansi)
        ansi_clean = re.compile(r'\x1b\[[0-9;]*[mK]')
        for line in ansi.split("\n"):
            clean_line = ansi_clean.sub("", line)
            self.assertLessEqual(len(clean_line), 24)

        # Verify is_back=True fallback resolves to front sprite if back not present
        back_sprite = self.engine.api.download_sprite(2012, is_back=True)
        self.assertIsNotNone(back_sprite)
        self.assertTrue(back_sprite.exists())

    def test_companion_tab_metrics_date_display(self):
        """Verify date information is rendered for Monthly Tokens and Total Tokens in Tab 1, obeying 72 columns."""
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.companion import render as render_companion_tab
        from poketokenbar.game.models import MonState, Rarity

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        app = MagicMock()
        app.engine = self.engine

        pikachu = MonState(
            base_id=25,
            path_ids=[25, 26],
            planned_path_ids=[25, 26],
            stage_index=0,
            used_at_stage=1000,
            rarity=Rarity.COMMON,
            total_forms=2
        )
        self.engine.set_active_mon(pikachu)

        # Case 1: Standard cycle Day 1, lifetime total tokens
        self.engine.state["billing_cycle_day"] = 1
        self.engine.state["baseline_total_tokens"] = 0
        self.engine.state.pop("baseline_date", None)
        summary1 = {
            "today_tokens": 50_000,
            "antigravity_today": 40_000,
            "week_tokens": 200_000,
            "month_tokens": 1_200_000,
            "total_tokens": 5_000_000,
            "burn_rate_tpm": 1500,
            "billing_cycle_start": "2026-09-01",
            "billing_cycle_day": 1,
            "earliest_date": "2026-08-10",
        }

        trap1 = io.StringIO()
        with patch("sys.stdout", trap1):
            render_companion_tab(app, summary1)
        out1 = trap1.getvalue()
        self.assertIn("Monthly Tokens: 1.2M  (since 2026-09-01)", out1)
        self.assertIn("Total Tokens:   5.0M  (since 2026-08-10)", out1)
        for line in out1.split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Companion Tab 1 exceeds 72 cols: '{clean}' (len={len(clean)})")

        # Case 2: Custom cycle Day 15, re-baselined total tokens
        self.engine.state["billing_cycle_day"] = 15
        self.engine.initialize_total_tokens(5_000_000, date_str="2026-09-17")
        self.assertEqual(self.engine.state["baseline_date"], "2026-09-17")
        summary2 = {
            "today_tokens": 50_000,
            "antigravity_today": 40_000,
            "week_tokens": 200_000,
            "month_tokens": 1_200_000,
            "total_tokens": 300_000,
            "baseline_total_tokens": 5_000_000,
            "baseline_date": "2026-09-17",
            "burn_rate_tpm": 1500,
            "billing_cycle_start": "2026-08-15",
            "billing_cycle_day": 15,
        }

        trap2 = io.StringIO()
        with patch("sys.stdout", trap2):
            render_companion_tab(app, summary2)
        out2 = trap2.getvalue()
        self.assertIn("Monthly Tokens: 1.2M  (since 2026-08-15 | Cycle: Day 15)", out2)
        self.assertIn("Total Tokens:   300.0K  (since 2026-09-17)", out2)
        self.assertNotIn("re-baselined", out2)
        for line in out2.split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Companion Tab 1 exceeds 72 cols: '{clean}' (len={len(clean)})")

        # Case 3: Clear baseline removes baseline_date
        self.engine.clear_total_tokens_baseline()
        self.assertNotIn("baseline_date", self.engine.state)
        self.assertEqual(self.engine.state["baseline_total_tokens"], 0)

    def test_rocket_op1_tracks_expeditions_only_after_operation_starts(self):
        """Verify that Operation 1 only tracks scout expeditions completed after starting the operation."""
        # 1. Initialize rocket process
        self.engine.initialize_rocket_process()
        op1 = self.engine.state["rocket_ops"]["op_1"]
        self.assertEqual(op1["status"], "available")
        self.assertEqual(op1["expeditions_done"], 0)
        self.assertFalse(op1["objective_done"])

        # 2. Existing historical logs from past sessions must NOT auto-satisfy the quest
        self.engine.state["expedition_logs"] = [
            "[10:00:00] Pikachu: Berry | +50K 🪙 | +50K XP",
            "[11:00:00] Charmander: Nugget | +100K 🪙 | +100K XP",
            "[12:00:00] Squirtle: Herb | +75K 🪙 | +75K XP",
        ]
        ok_obj, msg_obj = self.engine.check_operation_objective("op_1")
        self.assertFalse(ok_obj)
        self.assertIn("Need 2 scout expeditions (Completed: 0/2)", msg_obj)
        self.assertFalse(self.engine.state["rocket_ops"]["op_1"]["objective_done"])

        reqs = self.engine.get_operation_requirements("1")
        self.assertEqual(reqs[1]["name"], "Scout Expeditions")
        self.assertEqual(reqs[1]["current"], 0)
        self.assertFalse(reqs[1]["is_met"])

        # 3. Expeditions finished while merely 'available' must NOT increment expeditions_done
        self.engine.state["expeditions"] = [{
            "area": "viridian",
            "target": 100,
            "progress": 90,
            "sp_id": 25,
            "reward": "berry",
        }]
        events = []
        self.engine._update_expeditions(100, events)
        self.assertEqual(self.engine.state["rocket_ops"]["op_1"]["expeditions_done"], 0)

        # 4. Activate operation via start_rocket_operation
        ok_start, _ = self.engine.start_rocket_operation("1")
        self.assertTrue(ok_start)
        self.assertEqual(self.engine.state["rocket_ops"]["op_1"]["status"], "active")
        self.assertEqual(self.engine.state["rocket_ops"]["op_1"]["expeditions_done"], 0)

        # 5. Complete 1st expedition after operation start
        self.engine.state["expeditions"] = [{
            "area": "viridian",
            "target": 100,
            "progress": 90,
            "sp_id": 25,
            "reward": "berry",
        }]
        events = []
        self.engine._update_expeditions(100, events)
        self.assertEqual(self.engine.state["rocket_ops"]["op_1"]["expeditions_done"], 1)
        ok_obj1, _ = self.engine.check_operation_objective("op_1")
        self.assertFalse(ok_obj1)
        reqs1 = self.engine.get_operation_requirements("1")
        self.assertEqual(reqs1[1]["current"], 1)
        self.assertFalse(reqs1[1]["is_met"])

        # 6. Complete 2nd expedition after operation start
        self.engine.state["expeditions"] = [{
            "area": "viridian",
            "target": 100,
            "progress": 90,
            "sp_id": 25,
            "reward": "berry",
        }]
        events = []
        self.engine._update_expeditions(100, events)
        self.assertEqual(self.engine.state["rocket_ops"]["op_1"]["expeditions_done"], 2)
        ok_obj2, _ = self.engine.check_operation_objective("op_1")
        self.assertTrue(ok_obj2)
        self.assertTrue(self.engine.state["rocket_ops"]["op_1"]["objective_done"])
        reqs2 = self.engine.get_operation_requirements("1")
        self.assertEqual(reqs2[1]["current"], 2)
        self.assertTrue(reqs2[1]["is_met"])

    def test_rocket_boss_operations_initialization_and_anti_premature_completion(self):
        """Verify boss operations initialize with full HP, resist false-positive completion, and require combat victory."""
        from poketokenbar.game.rocket_battle import RocketBattleHandler

        # 1. Verify fresh initialization allocates proper boss HP
        self.engine.initialize_rocket_process()
        ops = self.engine.state["rocket_ops"]
        self.assertEqual(ops["op_3"]["boss_hp_remaining"], 150_000)
        self.assertFalse(ops["op_3"]["objective_done"])
        self.assertEqual(ops["op_6"]["boss_hp_remaining"], 200_000)
        self.assertEqual(ops["op_9"]["boss_hp_remaining"], 300_000)
        self.assertEqual(ops["op_10"]["boss_hp_remaining"], 350_000)

        # 2. Simulate claiming Op 1 & Op 2 to sequentially unlock Op 3
        self.engine.state["rocket_ops"]["op_1"]["claimed"] = True
        self.engine.state["rocket_ops"]["op_1"]["status"] = "completed"
        self.engine.state["rocket_ops"]["op_2"]["status"] = "active"
        self.engine.state["rocket_ops"]["op_2"]["progress"] = 10_000_000
        self.engine.state["rocket_ops"]["op_2"]["battle_wins"] = 2
        ok_claim2, _ = self.engine.claim_rocket_operation("2")
        self.assertTrue(ok_claim2)

        # Op 3 must now be available with full 150,000 HP and objective_done False
        op3_st = self.engine.state["rocket_ops"]["op_3"]
        self.assertEqual(op3_st["status"], "available")
        self.assertEqual(op3_st["boss_hp_remaining"], 150_000)
        self.assertFalse(op3_st["objective_done"])

        # 3. Check objective before combat -> Must NOT be marked done
        ok_obj, msg_obj = self.engine.check_operation_objective("op_3")
        self.assertFalse(ok_obj)
        self.assertIn("150,000", msg_obj)
        self.assertFalse(op3_st["objective_done"])

        # 4. Start Op 3
        ok_start, _ = self.engine.start_rocket_operation("3")
        self.assertTrue(ok_start)
        self.assertEqual(op3_st["status"], "active")
        self.assertEqual(op3_st["boss_hp_remaining"], 150_000)
        self.assertFalse(op3_st["objective_done"])

        # 5. Test self-healing against corrupted/zeroed state without combat win
        op3_st["boss_hp_remaining"] = 0
        op3_st["objective_done"] = True
        self.engine.state["rocket_battle_state"] = {} # No win recorded!

        # check_operation_objective must catch the unearned zero HP, heal HP to 150k, and reject objective_done
        ok_healed, msg_healed = self.engine.check_operation_objective("op_3")
        self.assertFalse(ok_healed)
        self.assertEqual(op3_st["boss_hp_remaining"], 150_000)
        self.assertFalse(op3_st["objective_done"])

        # Claiming while un-neutralized must fail
        ok_claim, msg_claim = self.engine.claim_rocket_operation("3")
        self.assertFalse(ok_claim)
        self.assertIn("objective not fulfilled", msg_claim)

        # 6. Engage and complete combat via RocketBattleHandler
        handler = RocketBattleHandler(self.engine)
        ok_engage, _ = handler.start_boss_battle("3")
        self.assertTrue(ok_engage)

        b_st = handler._get_state()
        b_st["boss_hps"][0] = 1
        handler._save_state(b_st)
        handler.execute_turn(0) # defeat Prototype Chimera-001 -> VICTORY

        b_st = handler._get_state()
        self.assertEqual(b_st["status"], "win")
        self.assertEqual(op3_st["boss_hp_remaining"], 0)
        self.assertTrue(op3_st["objective_done"])

        # 7. check_operation_objective must now verify victory
        ok_won, msg_won = self.engine.check_operation_objective("op_3")
        self.assertTrue(ok_won)
        self.assertIn("neutralized", msg_won)

        # 8. Claim Op 3 rewards
        spent_before = self.engine.state.get("spent_tokens", 0)
        ok_claim_final, msg_claim_final = self.engine.claim_rocket_operation("3")
        self.assertTrue(ok_claim_final)
        self.assertTrue(op3_st["claimed"])
        self.assertEqual(self.engine.state.get("spent_tokens", 0), spent_before - 40_000_000)
        self.assertIn("intel_003", self.engine.state.get("rocket_intel_unlocked", []))
        self.assertEqual(self.engine.state["rocket_ops"]["op_4"]["status"], "available")

    def test_rocket_armory_free_clearance_and_auto_granted_perks(self):
        """Verify armory items cost 0 tokens, require no token balance, and auto-grant perks upon rank promotion."""
        from poketokenbar.tui_tabs.rocket import handle_rocket_command
        from unittest.mock import MagicMock

        # 1. Zero tokens balance
        self.engine.state["used_since_install"] = 0
        self.engine.state["spent_tokens"] = 0
        self.assertEqual(self.engine.available_tokens, 0)

        # 2. Informant Rank: Black Pass auto-granted on joining/alliance
        self.engine.initialize_rocket_process()
        self.assertTrue(self.engine.state.get("permanent_black_market"))
        self.assertFalse(self.engine.state.get("has_exp_splitter"))

        # Requisitioning pass while already active
        ok_p, msg_p = self.engine.buy_rocket_armory_item("pass")
        self.assertFalse(ok_p)
        self.assertIn("already possess", msg_p)

        # 3. Operative Rank: Free requisition of Morale Mist with 0 tokens balance
        self.engine.state["rocket_rank"] = "Operative"
        spent_before = self.engine.state.get("spent_tokens", 0)
        ok_spray, msg_spray = self.engine.buy_rocket_armory_item("spray")
        self.assertTrue(ok_spray)
        self.assertIn("Clearance Authorized", msg_spray)
        self.assertEqual(self.engine.state.get("spent_tokens", 0), spent_before)

        # 4. Rank promotion to Special Agent auto-grants Corrupted EXP Splitter
        self.engine.state["rocket_ops"] = {f"op_{i}": {"claimed": True} for i in range(1, 6)}
        self.engine.state["rocket_ops"]["op_6"] = {"status": "available", "claimed": False, "objective_done": False, "boss_hp_remaining": 200_000, "progress": 0}
        self.engine.state["rocket_ops"]["op_5"]["claimed"] = False
        self.engine.state["rocket_ops"]["op_5"]["status"] = "active"
        self.engine.state["rocket_ops"]["op_5"]["expeditions_done"] = 2
        self.engine.state["rocket_ops"]["op_5"]["black_market_trades"] = 1
        self.engine.state["expeditions"] = [{"area": "pallet", "target": 100, "progress": 10}, {"area": "viridian", "target": 100, "progress": 10}]
        self.engine.state["has_exp_splitter"] = False

        ok_claim5, msg_claim5 = self.engine.claim_rocket_operation("5")
        self.assertTrue(ok_claim5)
        self.assertEqual(self.engine.state["rocket_rank"], "Special Agent")
        self.assertTrue(self.engine.state["has_exp_splitter"])
        self.assertIn("Auto-activated Corrupted EXP Splitter", msg_claim5)

        # 5. TUI command routing: deprecated commands notify that perks are auto-granted
        app = MagicMock()
        app.engine = self.engine
        app.rocket_subview = "armory"
        self.engine.state["rocket_alliance_accepted"] = True
        self.engine.state["rocket_rank"] = "Executive"

        # 'claim spray' from armory
        handle_rocket_command(app, "claim spray")
        self.assertIn("Covert Armory perks are automatically granted", app.message)

        # 'requisition chrono'
        handle_rocket_command(app, "requisition chrono")
        self.assertIn("Covert Armory perks are automatically granted", app.message)

        # direct 'catalyst'
        handle_rocket_command(app, "catalyst")
        self.assertIn("Covert Armory perks are automatically granted", app.message)

    def test_mint_removal_and_expedition_rewards(self):
        from poketokenbar.tui_tabs.shop import BAG_CATALOG, handle_shop_buy
        from poketokenbar.game.black_market import BLACK_MARKET_POOL_100
        from poketokenbar.game.gacha import GACHA_LOOT_TABLE

        # 1. ItemKind has no MINT
        self.assertFalse(hasattr(ItemKind, "MINT"))

        # 2. Game Corner Gacha loot table has no mint
        for tier, name, weight, r_type, val in GACHA_LOOT_TABLE:
            self.assertNotEqual(val, "mint")

        # 3. Black market pool has exactly 100 items and no mint
        self.assertEqual(len(BLACK_MARKET_POOL_100), 100)
        for d in BLACK_MARKET_POOL_100:
            self.assertNotEqual(d.get("key"), "mint")
            if d.get("contents"):
                self.assertNotIn("mint", d["contents"])

        # 4. Bag catalog indexing: sequential 1..64 with no gaps and no mint
        self.assertEqual(len(BAG_CATALOG), 64)
        for i, (cid, key, _) in enumerate(BAG_CATALOG, start=1):
            self.assertEqual(cid, str(i))
            self.assertNotEqual(key, "mint")

        # 5. Shop buying re-indexed 1..11
        app = MagicMock()
        app.engine = self.engine
        app.shop_view = "normal"
        self.engine.state["used_since_install"] = 1_000_000_000
        self.engine.state["spent_tokens"] = 0
        self.engine.state["egg_tier"] = None

        # Buy [1] -> Rare Candy
        rc_before = self.engine.state["inventory"].get("rare_candy", 0)
        handle_shop_buy(app, "buy 1 1")
        self.assertEqual(self.engine.state["inventory"].get("rare_candy", 0), rc_before + 1)

        # Buy [4] -> Oran Berry
        oran_before = self.engine.state["inventory"].get("berry_oran", 0)
        handle_shop_buy(app, "buy 4 2")
        self.assertEqual(self.engine.state["inventory"].get("berry_oran", 0), oran_before + 2)

        # 6. Expedition rewards: Viridian -> rare_candy, Cerulean -> berry_oran
        mon, _ = self.engine.hatch_egg(0)
        mon2, _ = self.engine.hatch_egg(0)
        self.engine.state["expedition_slots"] = 5
        ok_v, _ = self.engine.dispatch_expedition("1", "viridian")
        self.assertTrue(ok_v)
        viridian_exp = [e for e in self.engine.state["expeditions"] if "Viridian" in e.get("area", "")][0]
        self.assertEqual(viridian_exp["reward"], "rare_candy")

        ok_c, _ = self.engine.dispatch_expedition("2", "cerulean")
        self.assertTrue(ok_c)
        cerulean_exp = [e for e in self.engine.state["expeditions"] if "Cerulean" in e.get("area", "")][0]
        self.assertEqual(cerulean_exp["reward"], "berry_oran")

        # Process expedition completion for Viridian (gives rare_candy)
        rc_count = self.engine.state["inventory"].get("rare_candy", 0)
        viridian_exp["progress"] = viridian_exp["target"]
        self.engine._update_expeditions(1, [])
        self.assertEqual(self.engine.state["inventory"].get("rare_candy", 0), rc_count + 1)

        # Process expedition completion for Cerulean (gives berry_oran)
        oran_count = self.engine.state["inventory"].get("berry_oran", 0)
        cerulean_exp["progress"] = cerulean_exp["target"]
        self.engine._update_expeditions(1, [])
        self.assertEqual(self.engine.state["inventory"].get("berry_oran", 0), oran_count + 1)

        # 7. Legacy state migration in __init__
        raw_state = StorageManager.default_state()
        raw_state["inventory"]["mint"] = 5
        raw_state["inventory"]["items"] = {"mint": 5}
        raw_state["expeditions"] = [{"sp_id": 1, "area": "Viridian Forest", "reward": "mint", "progress": 0, "target": 5_000_000}]
        raw_state["active_boss"] = {"id": "boss_2", "reward": "mint"}
        raw_state["daily_quests"] = {"quests": [{"id": "q1", "reward": "mint"}]}
        StorageManager.save_state(raw_state)

        migrated_engine = CompanionEngine()
        self.assertNotIn("mint", migrated_engine.state["inventory"])
        self.assertNotIn("mint", migrated_engine.state["inventory"].get("items", {}))
        self.assertEqual(migrated_engine.state["expeditions"][0]["reward"], "rare_candy")
        self.assertEqual(migrated_engine.state["active_boss"]["reward"], "rare_candy")
        self.assertEqual(migrated_engine.state["daily_quests"]["quests"][0]["reward"], "rare_candy")

    def test_rocket_boss_chimera_hp_sync_and_compact_tui(self):
        """Verify Chimera-001 HP synchronization, HP% left banner rendering, compact combat TUI, and sprite flipping."""
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.rocket import render_rocket_tab
        from poketokenbar.game.rocket_battle import RocketBattleHandler, ROCKET_BOSS_TEAMS
        from poketokenbar.sprite_renderer import SpriteRenderer

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')

        # 1. Op 3 boss team definition matches 150k HP Chimera-001
        self.assertEqual(len(ROCKET_BOSS_TEAMS["3"]["team"]), 1)
        chimera_def = ROCKET_BOSS_TEAMS["3"]["team"][0]
        self.assertEqual(chimera_def["name"], "Prototype Chimera-001")
        self.assertEqual(chimera_def["max_hp"], 150_000)
        self.assertEqual(chimera_def["id"], 2012)

        # 2. Operations Menu: HP% left calculation verification
        app = MagicMock()
        app.engine = self.engine
        app.rocket_subview = "ops"
        self.engine.state["rocket_story_unlocked"] = True
        self.engine.state["rocket_alliance_accepted"] = True
        self.engine.state["rocket_ops"]["op_3"]["status"] = "active"
        self.engine.state["rocket_ops"]["op_3"]["claimed"] = False
        self.engine.state["rocket_ops"]["op_3"]["objective_done"] = False
        self.engine.state["rocket_ops"]["op_3"]["boss_hp_remaining"] = 60_000
        self.engine.state["rocket_battle_state"] = {}

        trap_banner = io.StringIO()
        with patch("sys.stdout", trap_banner):
            render_rocket_tab(app)
        banner_out = ansi_regex.sub("", trap_banner.getvalue())

        # Must display 40.0% left and NOT the inverted 60.0% (40% left)
        self.assertIn("HP: 60,000/150,000 | [█████░░░░░░░] 40.0% left", banner_out)
        self.assertNotIn("60.0% (40% left)", banner_out)

        # 3. Combat TUI: submenu removal & vertical compactness
        handler = RocketBattleHandler(self.engine)
        handler.start_boss_battle("3")

        trap_combat = io.StringIO()
        with patch("sys.stdout", trap_combat):
            render_rocket_tab(app)
        combat_out = ansi_regex.sub("", trap_combat.getvalue())

        # Submenu and HQ header must be omitted in combat
        self.assertNotIn("TEAM ROCKET COVERT HEADQUARTERS", combat_out)
        self.assertNotIn("[O] Operations", combat_out)
        self.assertNotIn("[I] Intel Dossier", combat_out)
        self.assertNotIn("[A] Covert Armory", combat_out)
        self.assertIn("TACTICAL COMBAT // Silph Sub-Vault 4: Prototype Chimera-001", combat_out)
        self.assertIn("Prototype Chimera-001", combat_out)

        # Verify <= 72 columns compliance on all lines
        for line in combat_out.split("\n"):
            self.assertLessEqual(len(line), 72, f"Combat line exceeds 72 cols: '{line}'")

        # 4. Sprite horizontal flipping
        ansi_normal = SpriteRenderer.render_png_to_ansi(None, 24, flip_h=False)
        ansi_flipped = SpriteRenderer.render_png_to_ansi(None, 24, flip_h=True)
        self.assertIsNotNone(ansi_normal)
        self.assertIsNotNone(ansi_flipped)

    def test_cd_criteria_sorting_modes(self):
        """Verify get_sorted_cds and set_cd_sort_criteria across 'days', 'amount', and 'term' modes."""
        self.engine.state["term_deposits"] = [
            {"id": 1, "principal": 5_000_000, "term_days": 3, "days_elapsed": 1, "current_value": 5_400_000, "matured": False},   # 2d left
            {"id": 2, "principal": 50_000_000, "term_days": 14, "days_elapsed": 14, "current_value": 75_000_000, "matured": True}, # Matured (0d left)
            {"id": 3, "principal": 25_000_000, "term_days": 7, "days_elapsed": 2, "current_value": 28_000_000, "matured": False},  # 5d left
            {"id": 4, "principal": 10_000_000, "term_days": 14, "days_elapsed": 10, "current_value": 15_000_000, "matured": False}, # 4d left
        ]

        # 1. Default mode: 'days' -> Matured first (id 2), then 2d left (id 1), then 4d left (id 4), then 5d left (id 3)
        self.assertEqual(self.engine.state.get("cd_sort_criteria"), "days")
        sorted_days = self.engine.get_sorted_cds()
        self.assertEqual([c["id"] for c in sorted_days], [2, 1, 4, 3])

        # 2. 'amount' mode -> Highest value first: 75M (id 2), 28M (id 3), 15M (id 4), 5.4M (id 1)
        ok_amt, msg_amt = self.engine.set_cd_sort_criteria("amount")
        self.assertTrue(ok_amt)
        self.assertIn("Deposit Value", msg_amt)
        sorted_amt = self.engine.get_sorted_cds()
        self.assertEqual([c["id"] for c in sorted_amt], [2, 3, 4, 1])

        # 3. 'term' mode -> Longest duration first: 14d matured (id 2), 14d locked (id 4), 7d (id 3), 3d (id 1)
        ok_term, msg_term = self.engine.set_cd_sort_criteria("term")
        self.assertTrue(ok_term)
        self.assertIn("Term Duration", msg_term)
        sorted_term = self.engine.get_sorted_cds()
        self.assertEqual([c["id"] for c in sorted_term], [2, 4, 3, 1])

        # 4. Invalid mode rejection
        ok_bad, msg_bad = self.engine.set_cd_sort_criteria("invalid_mode")
        self.assertFalse(ok_bad)
        self.assertIn("Invalid sort criteria", msg_bad)

        # 5. Shorthand synonyms: 'days_left' -> 'days', 'val' -> 'amount', 'duration' -> 'term'
        self.assertTrue(self.engine.set_cd_sort_criteria("days_left")[0])
        self.assertEqual(self.engine.state["cd_sort_criteria"], "days")
        self.assertTrue(self.engine.set_cd_sort_criteria("val")[0])
        self.assertEqual(self.engine.state["cd_sort_criteria"], "amount")
        self.assertTrue(self.engine.set_cd_sort_criteria("duration")[0])
        self.assertEqual(self.engine.state["cd_sort_criteria"], "term")

    def test_cd_tui_sort_and_indexing_interaction(self):
        """Verify TUI rendering with sequential [1..N] indexing, interactive sort commands, and 72-col safety."""
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui import PokeTokenBarTUI
        from poketokenbar.tui_tabs.bank import _render_cd_view

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')

        self.engine.state["used_since_install"] = 500_000_000
        self.engine.state["spent_tokens"] = 0
        self.engine.state["cd_sort_criteria"] = "amount"
        self.engine.state["term_deposits"] = [
            {"id": 10, "principal": 5_000_000, "term_days": 3, "days_elapsed": 1, "current_value": 5_400_000, "matured": False},
            {"id": 20, "principal": 50_000_000, "term_days": 14, "days_elapsed": 14, "current_value": 75_000_000, "matured": True},
            {"id": 30, "principal": 25_000_000, "term_days": 7, "days_elapsed": 2, "current_value": 28_000_000, "matured": False},
        ]

        app = MagicMock()
        app.engine = self.engine
        app.cd_page = 1

        # Render under 'amount' sort: [1] should be 75M (id 20), [2] should be 28M (id 30), [3] should be 5.4M (id 10)
        trap = io.StringIO()
        with patch("sys.stdout", trap):
            _render_cd_view(app, self.engine.available_tokens)
        out = ansi_regex.sub("", trap.getvalue())

        self.assertIn("Sort: Amount", out)
        self.assertIn("[1] 50.0M", out)
        self.assertIn("[2] 25.0M", out)
        self.assertIn("[3] 5.0M", out)
        self.assertIn("sort <days|amount|term>", out)

        for line in trap.getvalue().split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"CD view line exceeds 72 cols: '{clean}'")

        # Test breaking item [1] on screen (which is 50M deposit, id 20)
        ok_brk, msg_brk = self.engine.break_cd("1")
        self.assertTrue(ok_brk)
        self.assertIn("Early withdrawal of CD [1]", msg_brk)
        remaining_ids = [c["id"] for c in self.engine.state["term_deposits"]]
        self.assertEqual(remaining_ids, [10, 30])

        # Test TUI interactive commands for sorting and claiming
        tui = PokeTokenBarTUI()
        tui.engine = self.engine
        tui.current_tab = 10
        tui.bank_subtab = "cd"
        self.engine.state["term_deposits"] = [
            {"id": 1, "principal": 10_000_000, "term_days": 3, "days_elapsed": 3, "current_value": 12_000_000, "matured": True},
            {"id": 2, "principal": 20_000_000, "term_days": 7, "days_elapsed": 1, "current_value": 20_000_000, "matured": False},
        ]

        # Use in-tab 'sort days' command
        commands = "\n".join(["sort days", "claim 1", "q"]) + "\n"
        with patch("sys.stdin", io.StringIO(commands)), patch("sys.stdout"), patch("poketokenbar.tui.UsageManager"):
            tui.run()
        self.assertEqual(self.engine.state["cd_sort_criteria"], "days")
        self.assertEqual(len(self.engine.state["term_deposits"]), 1)
        self.assertEqual(self.engine.state["term_deposits"][0]["id"], 2)

    def test_companion_tab_header_line_reformatting(self):
        """Verify rebalanced companion header: L2 has Rarity, Form, Held; L3 has Happiness, Streak."""
        import re
        import io
        from poketokenbar.tui_tabs.companion import render as render_companion_tab
        from poketokenbar.game.models import MonState, Rarity, ItemKind

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        app = MagicMock()
        app.engine = self.engine

        active_mon = MonState(
            base_id=6,
            path_ids=[4, 5, 6],
            planned_path_ids=[4, 5, 6],
            stage_index=2,
            used_at_stage=500_000,
            rarity=Rarity.RARE,
            total_forms=3,
            held_item=ItemKind.LUCKY_EGG.value,
            happiness=100,
        )
        self.engine.set_active_mon(active_mon)
        self.engine.state["streak_days"] = 7
        self.engine.state["last_milestone"] = "🎉 Graduated to Charizard!"

        summary = {
            "today_tokens": 100_000,
            "antigravity_today": 80_000,
            "week_tokens": 500_000,
            "month_tokens": 1_000_000,
            "total_tokens": 2_000_000,
            "burn_rate_tpm": 1200,
        }

        trap = io.StringIO()
        with patch("sys.stdout", trap):
            render_companion_tab(app, summary)
        out = trap.getvalue()
        clean_lines = [ansi_regex.sub("", line) for line in out.split("\n")]

        # Line 1: Active Companion
        self.assertTrue(any("Active Companion: Charizard (#6)" in l for l in clean_lines))
        # Line 2: Rarity, Form, Held
        l2 = next(l for l in clean_lines if "Rarity:" in l)
        self.assertIn("Rarity: RARE", l2)
        self.assertIn("Form: 3/3", l2)
        self.assertIn("Held: 🍀 Lucky Egg", l2)
        # Line 3: Happiness, Streak
        l3 = next(l for l in clean_lines if "Happiness:" in l)
        self.assertIn("Happiness: 💖 100% (+20% XP)", l3)
        self.assertIn("Streak: 🔥 7d", l3)
        self.assertNotIn("Held:", l3)
        # Line 4: Milestone
        l4 = next(l for l in clean_lines if "Milestone:" in l)
        self.assertIn("Milestone: 🎉 Graduated to Charizard!", l4)

        for line in clean_lines:
            self.assertLessEqual(len(line), 72, f"Line exceeds 72 cols: '{line}'")

class TestOranBerryFeeding(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.temp_state = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.temp_state.close()
        os.environ["PTB_STATE_FILE"] = self.temp_state.name
        self.engine = CompanionEngine()

    def tearDown(self):
        if os.path.exists(self.temp_state.name):
            os.remove(self.temp_state.name)
        bak = self.temp_state.name.replace(".json", ".json.bak")
        if os.path.exists(bak):
            os.remove(bak)

    def test_feed_active_companion_custom_qty(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        self.assertIsNotNone(active)
        active.happiness = 50
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 5}

        ok, msg = self.engine.feed_pokemon("active", 1)
        self.assertTrue(ok)
        self.assertIn("Fed 1 Oran Berry", msg)
        self.assertEqual(self.engine.active_mon.happiness, 75)
        self.assertEqual(self.engine.state["inventory"].get("berry_oran"), 4)

    def test_feed_zero_happiness_defaults_to_4_berries(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 0
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 10}

        ok, msg = self.engine.feed_pokemon("0")
        self.assertTrue(ok)
        self.assertIn("Fed 4 Oran Berries", msg)
        self.assertIn("100%", msg)
        self.assertEqual(self.engine.active_mon.happiness, 100)
        self.assertEqual(self.engine.state["inventory"].get("berry_oran"), 6)

    def test_feed_zero_multiple_exhausted_companions(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 0
        self.engine.set_active_mon(active)

        # Add second companion to roster
        self.engine.state["dex"].append({
            "id": "sp_25",
            "species_id": 25,
            "base_id": 25,
            "chain_order": [25, 26],
            "rarity": "uncommon",
            "status": "inactive",
            "mon_state": {"base_id": 25, "current_id": 25, "happiness": 0, "stage_index": 0, "total_forms": 2},
            "happiness": 0
        })
        self.engine.state["inventory"] = {"berry_oran": 10}

        ok, msg = self.engine.feed_pokemon("exhausted")
        self.assertTrue(ok)
        self.assertIn("Fed 8 Oran Berries", msg)
        self.assertEqual(self.engine.active_mon.happiness, 100)
        self.assertEqual(self.engine.state["dex"][-1]["mon_state"]["happiness"], 100)
        self.assertEqual(self.engine.state["inventory"].get("berry_oran"), 2)

    def test_feed_zero_partial_inventory(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 0
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 3}

        ok, msg = self.engine.feed_pokemon("0")
        self.assertTrue(ok)
        self.assertIn("Fed 3 Oran Berries", msg)
        self.assertEqual(self.engine.active_mon.happiness, 75)
        self.assertNotIn("berry_oran", self.engine.state["inventory"])

    def test_feed_saves_excess_berries_at_max_happiness(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 75
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 5}

        # Requesting 4 berries, but only 1 needed to reach 100%
        ok, msg = self.engine.feed_pokemon("active", 4)
        self.assertTrue(ok)
        self.assertIn("Fed 1 Oran Berry", msg)
        self.assertIn("saved 3 berries", msg)
        self.assertEqual(self.engine.active_mon.happiness, 100)
        self.assertEqual(self.engine.state["inventory"].get("berry_oran"), 4)

    def test_feed_all_option_is_removed(self):
        self.engine.hatch_egg(0)
        self.engine.state["inventory"] = {"berry_oran": 10}

        # 'all' option is rejected with explanatory error
        ok, msg = self.engine.feed_pokemon("all")
        self.assertFalse(ok)
        self.assertIn("The 'all' option has been removed", msg)

    def test_feed_by_species_id_and_rejection_of_names(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 50
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 5}

        # Feed by species #id (e.g. #25)
        ok, msg = self.engine.feed_pokemon(f"#{active.current_id}", 1)
        self.assertTrue(ok)
        self.assertEqual(self.engine.active_mon.happiness, 75)

        # Species name is rejected
        name = self.engine.api.get_species_name(active.current_id)
        ok, msg = self.engine.feed_pokemon(name, 1)
        self.assertFalse(ok)
        self.assertIn("not found in your Roster", msg)

    def test_feed_by_happiness_threshold_function(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 25
        self.engine.set_active_mon(active)

        # Mon 2: 50% happiness
        self.engine.state["dex"].append({
            "id": "sp_25",
            "species_id": 25,
            "base_id": 25,
            "chain_order": [25, 26],
            "rarity": "uncommon",
            "status": "inactive",
            "mon_state": {"base_id": 25, "current_id": 25, "happiness": 50, "stage_index": 0, "total_forms": 2},
            "happiness": 50
        })
        # Mon 3: 75% happiness (should NOT be fed when threshold is <= 50%)
        self.engine.state["dex"].append({
            "id": "sp_133",
            "species_id": 133,
            "base_id": 133,
            "chain_order": [133],
            "rarity": "rare",
            "status": "inactive",
            "mon_state": {"base_id": 133, "current_id": 133, "happiness": 75, "stage_index": 0, "total_forms": 1},
            "happiness": 75
        })
        self.engine.state["inventory"] = {"berry_oran": 10}

        # Feed 1 berry to all companions with happiness <= 50%
        ok, msg = self.engine.feed_by_happiness_threshold(max_happiness=50, qty=1)
        self.assertTrue(ok)
        self.assertIn("Fed 2 Oran Berries", msg)
        self.assertEqual(self.engine.active_mon.happiness, 50)  # 25 + 25 = 50
        self.assertEqual(self.engine.state["dex"][1]["mon_state"]["happiness"], 75)  # 50 + 25 = 75
        self.assertEqual(self.engine.state["dex"][2]["mon_state"]["happiness"], 75)  # unchanged!
        self.assertEqual(self.engine.state["inventory"]["berry_oran"], 8)

    def test_feed_by_happiness_threshold_confirm_flag(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 40
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 15}

        # confirm=True returns prompt string without mutating inventory
        ok, prompt_str = self.engine.feed_by_happiness_threshold(max_happiness=50, qty=2, confirm=True)
        self.assertTrue(ok)
        self.assertIn("Req:", prompt_str)
        self.assertIn("Bag: 15", prompt_str)
        self.assertLessEqual(len(prompt_str), 72)
        self.assertEqual(self.engine.active_mon.happiness, 40)
        self.assertEqual(self.engine.state["inventory"]["berry_oran"], 15)

    def test_feed_string_threshold_variations(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 30
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 10}

        # Test '<=50%' target string
        plan1 = self.engine.get_feed_plan("<=50%", qty=1)
        self.assertTrue(plan1["ok"])
        self.assertEqual(plan1["plan_type"], "threshold")
        self.assertEqual(plan1["threshold"], 50)

        # Test '50%' target string
        plan2 = self.engine.get_feed_plan("50%", qty=1)
        self.assertTrue(plan2["ok"])
        self.assertEqual(plan2["threshold"], 50)

        # Test '<=50' target string
        plan3 = self.engine.get_feed_plan("<=50", qty=1)
        self.assertTrue(plan3["ok"])
        self.assertEqual(plan3["threshold"], 50)

    def test_feed_plan_stating_required_and_available(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 0
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 15}

        plan = self.engine.get_feed_plan("0")
        self.assertTrue(plan["ok"])
        self.assertEqual(plan["total_berries"], 4)
        self.assertEqual(plan["available_berries"], 15)
        self.assertIn("Req: 4", plan["prompt"])
        self.assertIn("Bag: 15", plan["prompt"])
        self.assertLessEqual(len(plan["prompt"]), 72)
        # Verify state was not mutated by planning
        self.assertEqual(self.engine.active_mon.happiness, 0)
        self.assertEqual(self.engine.state["inventory"]["berry_oran"], 15)

    def test_feed_pokemon_confirm_flag(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 0
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 10}

        # With confirm=True, returns prompt without mutating state
        ok, prompt_str = self.engine.feed_pokemon("0", confirm=True)
        self.assertTrue(ok)
        self.assertIn("Req: 4", prompt_str)
        self.assertIn("Bag: 10", prompt_str)
        self.assertEqual(self.engine.active_mon.happiness, 0)
        self.assertEqual(self.engine.state["inventory"]["berry_oran"], 10)

    def test_feed_tui_confirmation_flow(self):
        from poketokenbar.tui import PokeTokenBarTUI
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 0
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 10}

        app = PokeTokenBarTUI()
        app.engine = self.engine

        # Calling 'feed 0' creates pending_feed and shows prompt with req and in bag
        app.handle_feed_command("feed 0")
        self.assertIsNotNone(app.pending_feed)
        self.assertIn("Req: 4", app.message)
        self.assertIn("Bag: 10", app.message)
        # Berries not consumed yet
        self.assertEqual(self.engine.active_mon.happiness, 0)
        self.assertEqual(self.engine.state["inventory"]["berry_oran"], 10)

        # Confirming executes the plan
        ok, msg = app.engine.execute_feed_plan(app.pending_feed)
        app.pending_feed = None
        self.assertTrue(ok)
        self.assertIn("Fed 4 Oran Berries", msg)
        self.assertEqual(self.engine.active_mon.happiness, 100)
        self.assertEqual(self.engine.state["inventory"]["berry_oran"], 6)

    def test_feed_tui_bypass_confirm_flags(self):
        from poketokenbar.tui import PokeTokenBarTUI
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 0
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 10}

        app = PokeTokenBarTUI()
        app.engine = self.engine

        # With -y flag, executes immediately without pending_feed
        app.handle_feed_command("feed 0 -y")
        self.assertIsNone(app.pending_feed)
        self.assertIn("Fed 4 Oran Berries", app.message)
        self.assertEqual(self.engine.active_mon.happiness, 100)
        self.assertEqual(self.engine.state["inventory"]["berry_oran"], 6)

    def test_feed_confirmation_prompts_under_72_cols(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 0
        self.engine.set_active_mon(active)

        for i in range(1, 15):
            self.engine.state["dex"].append({
                "id": f"sp_{i}",
                "species_id": i,
                "base_id": i,
                "chain_order": [i],
                "rarity": "common",
                "status": "inactive",
                "mon_state": {"base_id": i, "current_id": i, "happiness": 0, "stage_index": 0, "total_forms": 1},
                "happiness": 0
            })
        self.engine.state["inventory"] = {"berry_oran": 100}

        # Check exhausted prompt
        plan = self.engine.get_feed_plan("0")
        self.assertTrue(plan["ok"])
        self.assertLessEqual(len(plan["prompt"]), 72)
        self.assertIn("Req:", plan["prompt"])
        self.assertIn("Bag:", plan["prompt"])

        # Check threshold prompt
        plan_thresh = self.engine.get_feed_plan("<=50%")
        self.assertTrue(plan_thresh["ok"])
        self.assertLessEqual(len(plan_thresh["prompt"]), 72)
        self.assertIn("Req:", plan_thresh["prompt"])
        self.assertIn("Bag:", plan_thresh["prompt"])

        # Check single target prompt
        plan_single = self.engine.get_feed_plan(f"#{active.current_id}", 4)
        self.assertTrue(plan_single["ok"])
        self.assertLessEqual(len(plan_single["prompt"]), 72)
        self.assertIn("Req:", plan_single["prompt"])
        self.assertIn("Bag:", plan_single["prompt"])

class TestBankDailyInterest(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.temp_state = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.temp_state.close()
        os.environ["PTB_STATE_FILE"] = self.temp_state.name
        self.engine = CompanionEngine()

    def tearDown(self):
        if os.path.exists(self.temp_state.name):
            os.remove(self.temp_state.name)
        bak = self.temp_state.name.replace(".json", ".json.bak")
        if os.path.exists(bak):
            os.remove(bak)

    def test_bank_checking_view_displays_daily_interest(self):
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.bank import render_bank_tab

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        self.engine.state["bank_balance"] = 10_000_000
        self.engine.state["bank_loan"] = 5_000_000

        app = MagicMock()
        app.engine = self.engine
        app.bank_subtab = "checking"

        trap = io.StringIO()
        with patch("sys.stdout", trap):
            render_bank_tab(app)

        output = trap.getvalue()
        clean_lines = [ansi_regex.sub("", l) for l in output.split("\n")]

        # Check daily deposit interest (+500.0K/day interest)
        self.assertIn("+500.0K/day interest", output)
        self.assertIn("+5% daily interest (+500.0K tokens/day)", output)

        # Check daily loan interest (+500.0K/day interest)
        self.assertIn("+500.0K/day interest", output)
        self.assertIn("+10% daily interest (+500.0K debt/day", output)

        # 72-col compliance check
        for line in clean_lines:
            self.assertLessEqual(len(line), 72, f"Line exceeds 72 cols: '{line}'")

    def test_bank_checking_view_zero_balances(self):
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.bank import render_bank_tab

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        self.engine.state["bank_balance"] = 0
        self.engine.state["bank_loan"] = 0

        app = MagicMock()
        app.engine = self.engine
        app.bank_subtab = "checking"

        trap = io.StringIO()
        with patch("sys.stdout", trap):
            render_bank_tab(app)

        output = trap.getvalue()
        clean_lines = [ansi_regex.sub("", l) for l in output.split("\n")]

        self.assertIn("+0/day interest", output)
        self.assertIn("No active debt", output)
        self.assertIn("+5% daily interest (+0 tokens/day)", output)
        self.assertIn("+10% daily interest (+0 debt/day", output)

        for line in clean_lines:
            self.assertLessEqual(len(line), 72, f"Line exceeds 72 cols: '{line}'")

    def test_bank_transactions_feedback_daily_interest(self):
        self.engine.state["used_since_install"] = 50_000_000
        self.engine.state["spent_tokens"] = 0

        # Deposit 10M -> balance 10M -> daily interest +500K/day
        ok, msg = self.engine.handle_bank_transaction("deposit", "10m")
        self.assertTrue(ok)
        self.assertIn("Deposited 10.0M tokens", msg)
        self.assertIn("+500.0K/day interest", msg)

        # Withdraw 2M -> balance 8M -> daily interest +400K/day
        ok, msg = self.engine.handle_bank_transaction("withdraw", "2m")
        self.assertTrue(ok)
        self.assertIn("Withdrew 2.0M tokens", msg)
        self.assertIn("+400.0K/day interest", msg)

        # Loan 5M -> debt 5M -> daily debt interest +500K/day
        ok, msg = self.engine.handle_bank_transaction("loan", "5m")
        self.assertTrue(ok)
        self.assertIn("Took loan of 5.0M tokens", msg)
        self.assertIn("+500.0K/day interest", msg)

        # Payoff 3M -> debt 2M -> daily debt interest +200K/day
        ok, msg = self.engine.handle_bank_transaction("payoff", "3m")
        self.assertTrue(ok)
        self.assertIn("Paid off 3.0M tokens", msg)
        self.assertIn("+200.0K/day interest", msg)

        # Payoff remaining 2M -> debt 0 -> debt fully cleared
        ok, msg = self.engine.handle_bank_transaction("payoff", "2m")
        self.assertTrue(ok)
        self.assertIn("debt fully cleared", msg)

class TestLargeQuantityPurchaseConfirmation(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.temp_state = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.temp_state.close()
        os.environ["PTB_STATE_FILE"] = self.temp_state.name
        self.engine = CompanionEngine()
        self.engine.state["used_since_install"] = 100_000_000
        self.engine.state["spent_tokens"] = 0

    def tearDown(self):
        if os.path.exists(self.temp_state.name):
            os.remove(self.temp_state.name)
        bak = self.temp_state.name.replace(".json", ".json.bak")
        if os.path.exists(bak):
            os.remove(bak)

    def test_shop_buy_small_qty_executes_immediately(self):
        from poketokenbar.tui import PokeTokenBarTUI
        app = PokeTokenBarTUI()
        app.engine = self.engine

        # Buy 5 Oran Berries (<= 5)
        app.handle_shop_buy("buy 4 5")
        self.assertIsNone(app.pending_buy)
        self.assertIn("Successfully purchased 5x Oran Berry", app.message)
        self.assertEqual(self.engine.state["inventory"].get("berry_oran"), 5)

    def test_shop_buy_large_qty_prompts_confirmation(self):
        from poketokenbar.tui import PokeTokenBarTUI
        app = PokeTokenBarTUI()
        app.engine = self.engine

        # Buy 10 Oran Berries (> 5)
        app.handle_shop_buy("buy 4 10")
        self.assertIsNotNone(app.pending_buy)
        self.assertIn("Buy 10x Oran Berry", app.message)
        self.assertIn("Type 'confirm'", app.message)
        self.assertNotIn("berry_oran", self.engine.state.get("inventory", {}))

        # Confirm purchase
        ok, msg = app.execute_pending_buy(app.pending_buy)
        app.pending_buy = None
        self.assertTrue(ok)
        self.assertIn("Successfully purchased 10x Oran Berry", msg)
        self.assertEqual(self.engine.state["inventory"].get("berry_oran"), 10)

    def test_shop_buy_large_qty_bypass_flag(self):
        from poketokenbar.tui import PokeTokenBarTUI
        app = PokeTokenBarTUI()
        app.engine = self.engine

        # Buy 10 Oran Berries with -y bypass
        app.handle_shop_buy("buy 4 10 -y")
        self.assertIsNone(app.pending_buy)
        self.assertIn("Successfully purchased 10x Oran Berry", app.message)
        self.assertEqual(self.engine.state["inventory"].get("berry_oran"), 10)

    def test_stock_large_shares_prompts_confirmation(self):
        from poketokenbar.tui import PokeTokenBarTUI
        app = PokeTokenBarTUI()
        app.engine = self.engine

        # Buy 10 shares of SILPH (> 5)
        app.handle_invest_command("invest SILPH 10")
        self.assertIsNotNone(app.pending_buy)
        self.assertIn("Buy 10 shares of SILPH", app.message)
        self.assertIn("Type 'confirm'", app.message)
        self.assertEqual(self.engine.state.get("investments", {}).get("silph", 0), 0)

        # Confirm stock purchase
        ok, msg = app.execute_pending_buy(app.pending_buy)
        app.pending_buy = None
        self.assertTrue(ok)
        self.assertIn("Invested in 10 shares", msg)
        self.assertEqual(self.engine.state["investments"]["silph"], 10)

    def test_stock_terminal_large_shares_prompts_confirmation(self):
        from poketokenbar.tui import PokeTokenBarTUI
        app = PokeTokenBarTUI()
        app.engine = self.engine
        app.stock_terminal = "silph"

        app.handle_stock_terminal_buy("buy 10")
        self.assertIsNotNone(app.pending_buy)
        self.assertIn("Buy 10 shares of SILPH", app.message)
        self.assertEqual(self.engine.state.get("investments", {}).get("silph", 0), 0)

        # Confirm purchase
        ok, msg = app.execute_pending_buy(app.pending_buy)
        app.pending_buy = None
        self.assertTrue(ok)
        self.assertEqual(self.engine.state["investments"]["silph"], 10)

    def test_buy_item_confirm_flag_programmatic(self):
        # Programmatic CompanionEngine.buy_item with confirm=True
        ok, prompt = self.engine.buy_item(ItemKind.BERRY_ORAN, 10, confirm=True)
        self.assertTrue(ok)
        self.assertIn("Buy 10x Oran Berry", prompt)
        self.assertLessEqual(len(prompt), 72)
        self.assertNotIn("berry_oran", self.engine.state.get("inventory", {}))

    def test_large_buy_prompts_72_column_compliance(self):
        from poketokenbar.tui import PokeTokenBarTUI
        app = PokeTokenBarTUI()
        app.engine = self.engine

        # Test shop item prompts
        for item_id in ["1", "4", "5", "6", "7", "8", "9", "10", "11"]:
            app.handle_shop_buy(f"buy {item_id} 10")
            if app.pending_buy:
                self.assertLessEqual(len(app.pending_buy["prompt"]), 72, f"Item {item_id} prompt exceeds 72 cols: {app.pending_buy['prompt']}")

        # Test stock prompts
        for ticker in ["SILPH", "DEVON", "AETHER", "MAUV", "MACRO", "VIRIDIAN"]:
            app.handle_invest_command(f"invest {ticker} 10")
            if app.pending_buy:
                self.assertLessEqual(len(app.pending_buy["prompt"]), 72, f"Stock {ticker} prompt exceeds 72 cols: {app.pending_buy['prompt']}")

if __name__ == "__main__":
    unittest.main()



