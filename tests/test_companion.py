import os
import tempfile
import unittest
from pathlib import Path
from poketokenbar.game.companion import CompanionEngine
from poketokenbar.game.models import ItemKind, Rarity, MonState, PokemonBalance
from poketokenbar.game.storage import StorageManager

class TestCompanionEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._temp_dir = tempfile.TemporaryDirectory()
        cls._temp_state_file = Path(cls._temp_dir.name) / "test_state.json"
        os.environ["PTB_STATE_FILE"] = str(cls._temp_state_file)

    @classmethod
    def tearDownClass(cls):
        cls._temp_dir.cleanup()
        os.environ.pop("PTB_STATE_FILE", None)

    def setUp(self):
        StorageManager.save_state(StorageManager.default_state())
        self.engine = CompanionEngine()

    def test_item_prices(self):
        self.assertEqual(ItemKind.MINT.price, 1_000_000)
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

    def test_expedition_missing_keys_defensive(self):
        # Expeditions with missing reward/target/progress should not raise KeyError
        self.engine.state["expeditions"] = [
            {"sp_id": 3, "area": "cerulean"}
        ]
        events = []
        self.engine._update_expeditions(500_000, events)
        exp = self.engine.state["expeditions"][0]
        self.assertEqual(exp.get("reward"), "rare_candy")
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

        # Test Devon perk: 10% discount on Shop Rare Candy
        rc_base = ItemKind.RARE_CANDY.price_for(self.engine.current_difficulty)
        expected_cost = int(rc_base * 0.90)
        tokens_before_rc = self.engine.available_tokens
        ok_buy, msg_buy = self.engine.buy_item(ItemKind.RARE_CANDY, 1)
        self.assertTrue(ok_buy)
        self.assertEqual(tokens_before_rc - self.engine.available_tokens, expected_cost)

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

        for corp_key in ["silph", "devon", "aether", "mauville", "macro"]:
            app.stock_terminal = corp_key
            trap = io.StringIO()
            with unittest.mock.patch("sys.stdout", trap):
                render_bank_tab(app)
            out = trap.getvalue()
            self.assertIn("TRADE TERMINAL", out)
            self.assertIn("Your Position & Analytics", out)
            for line in out.split("\n"):
                clean = ansi_regex.sub("", line)
                self.assertLessEqual(len(clean), 72, f"Trade Terminal '{corp_key}' line exceeds 72 cols: '{clean}' (len={len(clean)})")

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
        self.engine.state["expedition_logs"] = ["log 1", "log 2"]
        events = []
        self.engine._update_rocket_operations(5_000_000, events)
        ok_claim, msg_claim = self.engine.claim_rocket_operation("1")
        self.assertTrue(ok_claim)
        self.assertEqual(self.engine.state["rocket_reputation"], 1)

        # Op 2: Requires 2 battle wins
        self.engine.state["trainer_battles"] = {"wins": 2, "losses": 0}
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
        ok_elixir, _ = self.engine.buy_rocket_armory_item("elixir")
        self.assertTrue(ok_elixir)

        # Overclock chip requires Operative
        ok_chip_denied, msg_chip = self.engine.buy_rocket_armory_item("chip")
        self.assertFalse(ok_chip_denied)
        self.assertIn("Clearance Denied", msg_chip)

        # Upgrade to Operative
        self.engine.state["rocket_rank"] = "Operative"
        self.engine.state["expeditions"] = [{"area_id": "viridian", "target_tokens": 10_000_000, "progress_tokens": 0}]
        ok_chip, _ = self.engine.buy_rocket_armory_item("chip")
        self.assertTrue(ok_chip)

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
        for line in trap_comm.getvalue().split("\n"):
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
        self.assertEqual(BAG_CATALOG_MAP["43"], "water_stone")
        self.assertEqual(BAG_CATALOG_MAP["20"], "choice_specs")
        self.assertEqual(BAG_CATALOG_MAP["26"], "revitalizing_tonic")
        self.assertEqual(BAG_CATALOG_MAP["33"], "metal_coat")
        self.assertEqual(BAG_CATALOG_MAP["53"], "fake_rare_candy")

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

        # 3. Render Bag page 2: Check evolution stone numeric index [43]
        app.shop_page = 2
        trap_bag2 = io.StringIO()
        with patch("sys.stdout", trap_bag2):
            render_shop_tab(app)
        bag_output2 = ansi_regex.sub("", trap_bag2.getvalue())

        self.assertIn("[43] 💎 Water Stone: 2 owned", bag_output2)
        self.assertNotIn("[water_stone]", bag_output2)

        for line in trap_bag2.getvalue().split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Bag line exceeds 72 cols: '{clean}'")

        # 4. Use item with numeric ID '43' to evolve active Eevee into Vaporeon
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

        handle_bag_use(app, "use 43")
        self.assertIn("Vaporeon", app.message)
        self.assertEqual(self.engine.active_mon.current_id, 134)
        self.assertEqual(self.engine.state["inventory"].get("water_stone", 0), 1)

        # 5. Sell item with numeric ID '43' and confirm 'y'
        trap_sell = io.StringIO()
        with patch("sys.stdout", trap_sell), patch("sys.stdin.readline", return_value="y\n"):
            handle_bag_sell(app, "sell 43 1")
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

if __name__ == "__main__":
    unittest.main()


