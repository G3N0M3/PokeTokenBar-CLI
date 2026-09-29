import os
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import re

from poketokenbar.game.companion import CompanionEngine
from poketokenbar.game.models import MonState, Rarity, PokemonBalance
from poketokenbar.game.storage import StorageManager
from poketokenbar.tui.app import PokeTokenBarTUI as AppState
from poketokenbar.tui_tabs.companion import render as render_companion_tab
from poketokenbar.tui_tabs.roster import render_nursery, render as render_roster_tab
from poketokenbar.tui.router import CommandRouter

ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*[mK]')


class TestNurseryAndIncubation(unittest.TestCase):

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

    def test_active_companion_trains_mon_not_egg(self):
        """Active companion gains XP while reserve eggs do not passively incubate."""
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
        self.engine.state["pending_eggs"] = [{"tier": "rare", "progress": 0}]
        self.engine.state["install_baseline_set"] = True
        self.engine.state["used_since_install"] = 0

        # Spend 750,000 tokens
        self.engine.process_usage(750_000)

        # 1. Companion gained 750,000 XP
        self.assertEqual(self.engine.active_mon.used_at_stage, 750_000)

        # 2. Reserve egg was NOT incubated (no passive incubation)
        self.assertEqual(self.engine.state.get("pending_eggs")[0]["progress"], 0)
        self.assertIsNone(self.engine.state.get("egg_tier"))

    def test_egg_incubation_when_egg_is_active_companion(self):
        """When an egg is selected as companion, spending tokens incubates it to 1.5M hatch."""
        self.engine.set_active_mon(None)
        self.engine.state["egg_tier"] = "rare"
        self.engine.state["egg_usage"] = 0
        self.engine.state["pending_eggs"] = [{"tier": "common", "progress": 0}]
        self.engine.state["install_baseline_set"] = True
        self.engine.state["used_since_install"] = 0

        # Fixed threshold is 1.5M
        self.assertEqual(self.engine.get_egg_hatch_threshold("rare"), 1_500_000)

        # Spend 1,500,000 tokens
        self.engine.process_usage(1_500_000)

        # 1. Egg hatched and became active companion!
        self.assertIsNotNone(self.engine.active_mon)
        self.assertIsNone(self.engine.state.get("egg_tier"))

        # 2. Remaining egg stays in Nursery reserves
        self.assertEqual(len(self.engine.state.get("pending_eggs")), 1)
        self.assertEqual(self.engine.state.get("pending_eggs")[0]["tier"], "common")

    def test_fixed_1_5m_threshold_for_all_tiers(self):
        """All egg tiers have a fixed 1.5M threshold."""
        for tier in ["common", "normal", "starter", "uncommon", "rare", "fossil", "dragon", "legendary", "paradox"]:
            self.assertEqual(self.engine.get_egg_hatch_threshold(tier), 1_500_000)

    def test_select_nursery_egg_swaps_and_preserves_progress(self):
        """Selecting an egg in the nursery stashes current egg and preserves progress."""
        self.engine.set_active_mon(None)
        self.engine.state["egg_tier"] = "normal"
        self.engine.state["egg_usage"] = 600_000
        self.engine.state["pending_eggs"] = [{"tier": "rare", "progress": 100_000}]

        # Select Rare Egg (index 2)
        ok, msg = self.engine.select_nursery_egg("2")
        self.assertTrue(ok)
        self.assertEqual(self.engine.state.get("egg_tier"), "rare")
        self.assertEqual(self.engine.state.get("egg_usage"), 100_000)

        # Verify previous Normal egg is in reserves with its 600k progress preserved!
        reserves = self.engine.state.get("pending_eggs")
        self.assertEqual(len(reserves), 1)
        self.assertEqual(reserves[0], {"tier": "normal", "progress": 600_000})

        # Select back to Normal Egg
        ok2, msg2 = self.engine.select_nursery_egg("2")
        self.assertTrue(ok2)
        self.assertEqual(self.engine.state.get("egg_tier"), "normal")
        self.assertEqual(self.engine.state.get("egg_usage"), 600_000)

    def test_sell_egg_from_reserves_and_active(self):
        """Selling eggs from reserves or active gives proper token value."""
        self.engine.set_active_mon(None)
        self.engine.state["egg_tier"] = "normal"
        self.engine.state["egg_usage"] = 0
        self.engine.state["pending_eggs"] = ["uncommon", "rare"]
        self.engine.state["spent_tokens"] = 0

        # 1. Sell Uncommon Egg (index 2) -> 45M value
        ok, msg, cash = self.engine.sell_nursery_egg("2")
        self.assertTrue(ok)
        self.assertEqual(cash, 45_000_000)
        self.assertEqual(self.engine.state.get("spent_tokens"), -45_000_000)

        # 2. Sell Rare Egg by tier name -> 60M value
        ok2, msg2, cash2 = self.engine.sell_nursery_egg("rare")
        self.assertTrue(ok2)
        self.assertEqual(cash2, 60_000_000)
        self.assertEqual(self.engine.state.get("spent_tokens"), -105_000_000)

        # 3. Sell Active Normal Egg -> 30M value
        ok3, msg3, cash3 = self.engine.sell_nursery_egg("1")
        self.assertTrue(ok3)
        self.assertEqual(cash3, 30_000_000)
        self.assertEqual(self.engine.state.get("spent_tokens"), -135_000_000)
        self.assertIsNone(self.engine.state.get("egg_tier"))

    def test_nursery_and_companion_hud_72_column_compliance(self):
        """Nursery view and Companion Tab strictly obey <= 72 columns."""
        app = AppState()
        app.engine = self.engine
        mon = MonState(
            base_id=782,
            path_ids=[782, 783, 784],
            planned_path_ids=[782, 783, 784],
            stage_index=1,
            used_at_stage=15_000_000,
            rarity=Rarity.RARE,
            total_forms=3
        )
        self.engine.set_active_mon(mon)
        self.engine.state["egg_tier"] = "normal"
        self.engine.state["egg_usage"] = 750_000
        self.engine.state["pending_eggs"] = ["uncommon", "legendary"]

        # 1. Companion Tab check
        trap_comp = io.StringIO()
        with patch("sys.stdout", trap_comp):
            render_companion_tab(app, {"total_tokens": 100_000_000, "today_tokens": 5_000_000})
        comp_out = trap_comp.getvalue()
        for line in comp_out.splitlines():
            clean = ANSI_REGEX.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Companion line exceeds 72 cols: {clean}")

        # 2. Nursery View check
        trap_nursery = io.StringIO()
        with patch("sys.stdout", trap_nursery):
            render_nursery(app)
        nursery_out = trap_nursery.getvalue()
        for line in nursery_out.splitlines():
            clean = ANSI_REGEX.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Nursery line exceeds 72 cols: {clean}")

    def test_nursery_pagination_7_per_page(self):
        """Nursery displays exactly 7 eggs per page and navigates with n, p, page <N>."""
        app = AppState()
        app.engine = self.engine
        app.current_tab = 3
        app.roster_subview = "eggs"
        app.nursery_page = 1

        # Populate 15 eggs (1 active + 14 pending)
        self.engine.set_active_mon(None)
        self.engine.state["egg_tier"] = "normal"
        self.engine.state["egg_usage"] = 0
        self.engine.state["pending_eggs"] = [{"tier": "rare", "progress": i * 10_000} for i in range(14)]

        # Page 1: should render eggs [1] through [7]
        trap1 = io.StringIO()
        with patch("sys.stdout", trap1):
            render_nursery(app)
        out1 = trap1.getvalue()
        self.assertIn("[1] 🥚 Standard Egg", out1)
        self.assertIn("[7] 🥚 Rare Egg", out1)
        self.assertNotIn("[8] 🥚 Rare Egg", out1)
        self.assertIn("Page 1/3", out1)

        # Navigate to next page: 'n'
        CommandRouter.route(app, "n")
        self.assertEqual(app.nursery_page, 2)
        trap2 = io.StringIO()
        with patch("sys.stdout", trap2):
            render_nursery(app)
        out2 = trap2.getvalue()
        self.assertIn("[8] 🥚 Rare Egg", out2)
        self.assertIn("[14] 🥚 Rare Egg", out2)
        self.assertNotIn("[15] 🥚 Rare Egg", out2)
        self.assertIn("Page 2/3", out2)

        # Navigate with 'page 3'
        CommandRouter.route(app, "page 3")
        self.assertEqual(app.nursery_page, 3)
        trap3 = io.StringIO()
        with patch("sys.stdout", trap3):
            render_nursery(app)
        out3 = trap3.getvalue()
        self.assertIn("[15] 🥚 Rare Egg", out3)
        self.assertNotIn("[14] 🥚 Rare Egg", out3)

        # Navigate back with 'p'
        CommandRouter.route(app, "p")
        self.assertEqual(app.nursery_page, 2)

    def test_single_canonical_command_rule(self):
        """Verifies single canonical command rule: sel <#>, sell <#>, back."""
        app = AppState()
        app.engine = self.engine
        app.current_tab = 3
        app.roster_subview = "eggs"

        self.engine.set_active_mon(None)
        self.engine.state["egg_tier"] = "normal"
        self.engine.state["egg_usage"] = 0
        self.engine.state["pending_eggs"] = [{"tier": "rare", "progress": 200_000}]

        # 1. 'sel 2' works to select egg #2
        CommandRouter.route(app, "sel 2")
        self.assertEqual(self.engine.state["egg_tier"], "rare")

        # 2. 'sell 2' works to sell egg #2 (previous normal egg stashed to reserves)
        CommandRouter.route(app, "sell 2")
        self.assertIn("Sold 1x", app.message)

        # 3. 'sell egg 1' is rejected under the Single Canonical Command Policy
        CommandRouter.route(app, "sell egg 1")
        self.assertIn("Unknown command", app.message)

        # 4. 'back' returns to Caught Pokémon Roster
        CommandRouter.route(app, "back")
        self.assertEqual(app.roster_subview, "roster")
        self.assertIn("Returned to Caught Pokémon Roster", app.message)

    def test_parse_egg_entry_and_corrupted_state_healing(self):
        """Un-nests deeply corrupted nested dict entries back to clean strings and progress."""
        corrupted = {"tier": {"tier": {"tier": "normal", "progress": 0}, "progress": 0}, "progress": 500_000}
        tier, prog = self.engine.parse_egg_entry(corrupted)
        self.assertEqual(tier, "normal")
        self.assertEqual(prog, 500_000)

        # Healing in get_all_nursery_eggs
        self.engine.state["pending_eggs"] = [corrupted, {"tier": "uncommon", "progress": 0}]
        eggs = self.engine.get_all_nursery_eggs()
        self.assertEqual(eggs[0]["tier"], "normal")
        self.assertEqual(self.engine.state["pending_eggs"][0], {"tier": "normal", "progress": 500_000})

    def test_nursery_sorting_modes(self):
        """Verifies criteria-based sorting in nursery: tier, progress, value, default."""
        app = AppState()
        app.engine = self.engine
        app.current_tab = 3
        app.roster_subview = "eggs"

        self.engine.set_active_mon(None)
        self.engine.state["egg_tier"] = "common"
        self.engine.state["egg_usage"] = 300_000
        self.engine.state["pending_eggs"] = [
            {"tier": "rare", "progress": 100_000},
            {"tier": "legendary", "progress": 50_000},
            {"tier": "uncommon", "progress": 800_000},
        ]

        # 1. Default sort: Active first, then queue order
        ok, msg = self.engine.set_nursery_sort_criteria("default")
        self.assertTrue(ok)
        eggs_def = self.engine.get_all_nursery_eggs()
        self.assertEqual([e["tier"] for e in eggs_def], ["common", "rare", "legendary", "uncommon"])
        self.assertEqual([e["index"] for e in eggs_def], [1, 2, 3, 4])

        # 2. Sort by tier: Highest rarity (legendary -> rare -> uncommon -> common)
        CommandRouter.route(app, "sort tier")
        self.assertEqual(self.engine.state["nursery_sort_criteria"], "tier")
        eggs_tier = self.engine.get_all_nursery_eggs()
        self.assertEqual([e["tier"] for e in eggs_tier], ["legendary", "rare", "uncommon", "common"])

        # 3. Sort by progress: Highest progress first (800k -> 300k -> 100k -> 50k)
        CommandRouter.route(app, "sort progress")
        self.assertEqual(self.engine.state["nursery_sort_criteria"], "progress")
        eggs_prog = self.engine.get_all_nursery_eggs()
        self.assertEqual([e["tier"] for e in eggs_prog], ["uncommon", "common", "rare", "legendary"])
        self.assertEqual([e["progress"] for e in eggs_prog], [800_000, 300_000, 100_000, 50_000])

        # 4. Sort by value: Highest token value first
        CommandRouter.route(app, "sort value")
        self.assertEqual(self.engine.state["nursery_sort_criteria"], "value")
        eggs_val = self.engine.get_all_nursery_eggs()
        self.assertEqual([e["tier"] for e in eggs_val], ["legendary", "rare", "uncommon", "common"])

        # 5. Invalid sort criteria rejects gracefully
        CommandRouter.route(app, "sort invalid")
        self.assertIn("Invalid sort criteria", app.message)

    def test_nursery_selection_and_selling_under_custom_sort(self):
        """Selecting and selling eggs by display index works accurately under custom sort orders."""
        app = AppState()
        app.engine = self.engine
        app.current_tab = 3
        app.roster_subview = "eggs"

        self.engine.set_active_mon(None)
        self.engine.state["egg_tier"] = "common"
        self.engine.state["egg_usage"] = 200_000
        self.engine.state["pending_eggs"] = [
            {"tier": "uncommon", "progress": 900_000},
            {"tier": "legendary", "progress": 100_000},
        ]

        # Sort by progress: [1] Uncommon (900k), [2] Common (200k, active), [3] Legendary (100k)
        CommandRouter.route(app, "sort progress")
        self.assertEqual(app.nursery_page, 1)

        # Select egg #1 (Uncommon, 900k)
        CommandRouter.route(app, "sel 1")
        self.assertEqual(self.engine.state["egg_tier"], "uncommon")
        self.assertEqual(self.engine.state["egg_usage"], 900_000)

        # Common egg (200k) was stashed back to reserves
        pending = self.engine.state["pending_eggs"]
        self.assertTrue(any(p["tier"] == "common" and p["progress"] == 200_000 for p in pending))

        # Under progress sort, sell egg #3 (lowest progress)
        eggs = self.engine.get_all_nursery_eggs()
        target_egg = eggs[2]
        CommandRouter.route(app, "sell 3")
        self.assertIn("Sold 1x", app.message)
        self.assertNotIn(target_egg["tier"], [p["tier"] for p in self.engine.state["pending_eggs"]])

    def test_red_battle_first_win_grants_mysterious_fetal_egg(self):
        """Defeating Red on the first victory awards a Mysterious Fetal Form Egg to Nursery."""
        from poketokenbar.game.combat.red_battle import RedBattleHandler
        red = RedBattleHandler(self.engine)
        self.engine.state["red_wins"] = 0
        self.engine.state["dex"] = []
        self.engine.set_active_mon(None)

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

        # Verify egg obtained in nursery
        all_eggs = self.engine.get_all_nursery_eggs()
        self.assertTrue(any(e["tier"] == "mysterious fetal form" for e in all_eggs))

        # Check turn logs
        st_after = red._get_state()
        self.assertTrue(any("shining god-like being" in log for log in st_after.get("turn_log", [])))
        self.assertTrue(any("Mysterious Fetal Form Egg to your Nursery" in log for log in st_after.get("turn_log", [])))


if __name__ == "__main__":
    unittest.main()
