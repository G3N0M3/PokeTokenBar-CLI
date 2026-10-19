import datetime
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from poketokenbar.game.companion import CompanionEngine
from poketokenbar.game.combat.red_battle import RedBattleHandler
from poketokenbar.game.models import MonState, Rarity, PokemonBalance
from poketokenbar.game.storage import StorageManager
from poketokenbar.tracker.antigravity import parse_pb_file
from poketokenbar.tracker.custom import CustomUsageReader, parse_date_value
from poketokenbar.tui.matrix_tui import render_matrix_view, strip_ansi
from poketokenbar.tui_tabs.bank import _render_stock_terminal
from poketokenbar.tui_tabs.luxury import _render_wing_help_view
from poketokenbar.utils.formatting import format_tokens, parse_tokens


class TestAuditFixes(unittest.TestCase):
    def setUp(self):
        StorageManager.save_state(StorageManager.default_state())
        self.engine = CompanionEngine()

    def test_graduation_promotes_dict_pending_egg(self):
        """Graduating a final-stage Pokémon unwraps dict entries from pending_eggs."""
        grad_thresh = PokemonBalance.phase_threshold(Rarity.RARE, 3, 2)
        charizard = MonState(
            base_id=4,
            path_ids=[4, 5, 6],
            planned_path_ids=[4, 5, 6],
            stage_index=2,
            used_at_stage=grad_thresh - 100,
            rarity=Rarity.RARE,
            total_forms=3,
            happiness=100,
        )
        self.engine.set_active_mon(charizard)
        self.engine.state["dex"] = [
            {
                "species_id": 6,
                "base_id": 4,
                "status": "active",
                "happiness": 100,
                "mon_state": StorageManager.mon_to_dict(charizard),
            }
        ]
        self.engine.state["pending_eggs"] = [{"tier": "legendary", "progress": 250_000}]
        self.engine.state["install_baseline_set"] = True

        events = self.engine.process_usage(50_000)
        self.assertTrue(any("graduated" in e.lower() for e in events))
        self.assertIsNone(self.engine.active_mon)
        self.assertEqual(self.engine.state["egg_tier"], "legendary")
        self.assertEqual(self.engine.state["egg_usage"], 250_000)

    def test_reset_game_state_resets_minigame_engines(self):
        """reset_game_state re-initializes all in-memory minigame engines."""
        self.engine.poker.table_mode = "vip"
        self.engine.poker.game_state = "flop"
        self.engine.voltorb.game_state = "playing"

        self.engine.reset_game_state()
        self.assertEqual(self.engine.poker.table_mode, "standard")
        self.assertEqual(self.engine.poker.game_state, "idle")
        self.assertEqual(self.engine.voltorb.game_state, "idle")

    def test_exp_share_does_not_corrupt_evolved_dex_entry(self):
        """EXP Share / EXP Splitter does not overwrite evolved Dex entry back to pre-evolution."""
        pikachu = MonState(
            base_id=25,
            path_ids=[25, 26],
            planned_path_ids=[25, 26],
            stage_index=1,
            used_at_stage=0,
            rarity=Rarity.COMMON,
            total_forms=2,
            happiness=100,
            held_item="exp_share",
        )
        self.engine.set_active_mon(pikachu)
        thresh = PokemonBalance.phase_threshold(Rarity.COMMON, 3, 0)
        charmander = MonState(
            base_id=4,
            path_ids=[4, 5, 6],
            planned_path_ids=[4, 5, 6],
            stage_index=0,
            used_at_stage=thresh - 10,
            rarity=Rarity.COMMON,
            total_forms=3,
            happiness=100,
        )
        self.engine.state["dex"] = [
            {
                "species_id": 26,
                "base_id": 25,
                "status": "active",
                "happiness": 100,
                "held_item": "exp_share",
                "mon_state": StorageManager.mon_to_dict(pikachu),
            },
            {
                "species_id": 4,
                "base_id": 4,
                "status": "inactive",
                "happiness": 100,
                "mon_state": StorageManager.mon_to_dict(charmander),
            },
        ]
        self.engine.state["install_baseline_set"] = True
        self.engine.state["has_exp_splitter"] = True

        self.engine.process_usage(500_000)
        evolved_entry = next(d for d in self.engine.state["dex"] if d["species_id"] == 4)
        self.assertEqual(evolved_entry["status"], "evolved")
        new_entry = next(d for d in self.engine.state["dex"] if d["species_id"] == 5)
        self.assertEqual(new_entry["status"], "inactive")
        self.assertEqual(new_entry["mon_state"]["stage_index"], 1)

    def test_red_battle_arceus_recruitment_and_party_multipliers(self):
        """RedBattleHandler Arceus recruitment creates valid MonState and party members get held_item bonuses."""
        mon1 = MonState(
            base_id=6, path_ids=[4, 5, 6], planned_path_ids=[4, 5, 6],
            stage_index=2, used_at_stage=0, rarity=Rarity.RARE, total_forms=3
        )
        mon2 = MonState(
            base_id=9, path_ids=[7, 8, 9], planned_path_ids=[7, 8, 9],
            stage_index=2, used_at_stage=0, rarity=Rarity.RARE, total_forms=3,
            held_item="choice_band", is_mega=True
        )
        self.engine.set_active_mon(mon1)
        self.engine.state["dex"] = [
            {"species_id": 6, "base_id": 4, "status": "active", "happiness": 100, "mon_state": StorageManager.mon_to_dict(mon1)},
            {"species_id": 9, "base_id": 7, "status": "inactive", "happiness": 100, "held_item": "choice_band", "is_mega": True, "mon_state": StorageManager.mon_to_dict(mon2)},
        ]
        self.engine.state["red_battle_state"] = {
            "status": "ongoing",
            "arceus_phase": True,
            "baseline_global_tokens": 0,
            "red_spent_tokens": 0,
            "player_team": [6, 9, 3, 25, 143, 196],
            "player_active_index": 1,
            "player_hps": [100_000, 100_000, 100_000, 100_000, 100_000, 100_000],
            "player_max_hps": [100_000, 100_000, 100_000, 100_000, 100_000, 100_000],
            "red_team": [{"id": 493, "name": "Arceus", "hp": 1, "max_hp": 5_000_000, "type": "normal", "moves": ["Judgment"]}],
            "red_active_index": 0,
            "red_hps": [1],
            "red_max_hps": [5_000_000],
            "turn_log": [],
        }

        handler = RedBattleHandler(self.engine)
        ok, msg = handler.execute_turn(0)
        self.assertTrue(ok)
        self.assertIn("Arceus", msg)
        arceus_entries = [d for d in self.engine.state["dex"] if d.get("species_id") == 493]
        self.assertEqual(len(arceus_entries), 1)
        self.assertEqual(arceus_entries[0]["mon_state"]["base_id"], 493)

    def test_matrix_sequential_daemons_and_root_tweak_guard(self):
        """Matrix combat enforces sequential daemon order and blocks root tweaks before transcendence."""
        self.engine.state["matrix"]["unlocked"] = True
        matrix = self.engine.matrix

        # Cannot fight daemon_watchdog before daemon_gc
        ok_b, msg_b = matrix.start_combat("daemon_watchdog")
        self.assertFalse(ok_b)
        self.assertIn("Neutralize", msg_b)

        # Cannot apply root tweak before root transcendence
        matrix.hacked_nodes.append("root")
        ok_tw, msg_tw = matrix.apply_tweak("root", "global_yield", "2x")
        self.assertFalse(ok_tw)
        self.assertIn("locked", msg_tw)

    def test_voltorb_memo_guard_when_not_playing(self):
        """VoltorbFlipEngine.memo returns False cleanly when game is not active."""
        ok, msg = self.engine.voltorb.memo(1, 1, 0)
        self.assertFalse(ok)
        self.assertIn("No active Voltorb Flip game", msg)

    def test_luxury_wealth_includes_bank_stocks_and_cds(self):
        """Luxury availability checks total net worth across spendable, bank, stocks, and CDs."""
        self.engine.state["used_since_install"] = 10_000_000_000  # 10B spendable
        self.engine.state["bank_balance"] = 50_000_000_000        # 50B bank
        self.engine.state["term_deposits"] = [{"principal": 45_000_000_000}]  # 45B CD -> 105B total
        self.assertTrue(self.engine.is_luxury_available())

        # Interact with Baron's 24K Sovereign Watch decor
        self.engine.state["luxury"]["unlocked"] = True
        self.engine.state["luxury"]["decor"] = ["watch"]
        ok_w, msg_w = self.engine.interact_luxury_decor("watch")
        self.assertTrue(ok_w)
        self.assertIn("24K Sovereign Watch", msg_w)

    def test_poker_vip_unlock_on_100t_bet_and_watch_bonus(self):
        """Betting >= 100T on standard table unlocks VIP, and watch decor grants +15% VIP payout."""
        self.engine.state["used_since_install"] = 500_000_000_000_000
        self.assertFalse(self.engine.state["poker_vip_unlocked"])

        ok, _ = self.engine.play_poker_bet("100t")
        self.assertTrue(ok)
        self.assertTrue(self.engine.state["poker_vip_unlocked"])

    def test_token_formatting_and_decimal_parsing_precision(self):
        """format_tokens and parse_tokens preserve exact integer precision at Quintillion scale."""
        # 999.9Q should not round up to 1000.0Q due to float precision loss
        val = 999_940_000_000_000_000
        self.assertEqual(format_tokens(val), "999.9Q")

        # Exact Decimal parsing
        self.assertEqual(parse_tokens("1.23456789Q"), 1_234_567_890_000_000)
        self.assertEqual(parse_tokens("inf"), -1)
        self.assertEqual(parse_tokens("nan"), -1)

    def test_custom_provider_timezone_and_log_preservation(self):
        """CustomUsageReader returns timezone-aware datetimes and preserves Format A/B entries on log_entry."""
        dt = parse_date_value("2026-05-01T12:00:00", datetime.datetime.now().astimezone())
        self.assertIsNotNone(dt.tzinfo)

        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "tokens.json"
            p.write_text(json.dumps({"entries": [{"date": "2026-05-01", "tokens": 1000}]}), encoding="utf-8")
            ok, _ = CustomUsageReader.log_entry(2500, file_path=p)
            self.assertTrue(ok)
            saved = json.loads(p.read_text(encoding="utf-8"))
            self.assertEqual(len(saved), 2)

    def test_antigravity_pb_parser_no_double_count(self):
        """parse_pb_file does not double-count the first entry when sub_entries has 1 item."""
        from poketokenbar.tracker.base import UsageEntry
        fake_entry = UsageEntry(
            id="antigravity|conv|0",
            date=datetime.datetime.now().astimezone(),
            local_day="2026-05-01",
            model="antigravity/claude",
            input_tokens=100,
            output_tokens=200,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            pb_file = Path(tmpdir) / "conv.pb"
            # Wire type 2 (key=0x0a), length 4, payload b"test"
            pb_file.write_bytes(b"\x0a\x04test")
            with patch("poketokenbar.tracker.antigravity.parse_generation_metadata", return_value=fake_entry):
                entries = parse_pb_file(pb_file, pb_file.stat().st_mtime)
            self.assertEqual(len(entries), 1)

    def test_tui_72_column_regressions(self):
        """Verify 72-column compliance on stock terminal, wing help, and matrix tweaks view."""
        app = MagicMock()
        app.engine = self.engine
        self.engine.state["investments"]["aether"] = 65

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            _render_stock_terminal(app, avail=100_000_000, corp_key="aether")
            _render_wing_help_view(app, avail=100_000_000)
        for line in buf.getvalue().splitlines():
            clean = strip_ansi(line)
            self.assertLessEqual(len(clean), 72, f"Line exceeds 72 cols: '{clean}'")


if __name__ == "__main__":
    unittest.main()
