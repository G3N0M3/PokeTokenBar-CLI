"""Unit tests for the Quantum Singularity Matrix (QSM) sub-level system."""

import os
import sys
import unittest
import io
from pathlib import Path

# Use isolated test file
TEST_STATE = "/tmp/ptb_test_matrix_state.json"
os.environ["PTB_STATE_FILE"] = TEST_STATE

from poketokenbar.game.companion import CompanionEngine
from poketokenbar.game.storage import StorageManager
from poketokenbar.game.matrix.models import (
    MATRIX_ENTRY_COST,
    ROOT_TRANSCENDENCE_COST,
    QRAM_BLOCKS,
    REALITY_PATCHES,
    KERNEL_DAEMONS,
    MEMORY_SECTORS,
)
from poketokenbar.tui.matrix_tui import render_matrix_view, strip_ansi
from poketokenbar.tui.matrix_router import MatrixRouter


class DummyTUI:
    """Mock TUI for testing Matrix views and command routing."""
    def __init__(self, engine):
        self.engine = engine
        self.in_matrix = True
        self.matrix_subview = "dashboard"
        self.message = ""
        self.current_tab = 10
        self.bank_subtab = "luxury"


class TestQuantumSingularityMatrix(unittest.TestCase):

    def setUp(self):
        if os.path.exists(TEST_STATE):
            os.remove(TEST_STATE)
        self.engine = CompanionEngine()

    def tearDown(self):
        if os.path.exists(TEST_STATE):
            os.remove(TEST_STATE)

    def _setup_fully_completed_luxury_suite(self):
        """Helper to set up a 100% completed luxury suite."""
        st = self.engine.get_luxury_state()
        st["unlocked"] = True
        st["vip_fee_paid"] = True
        st["invitation_sent"] = True
        st["facilities"] = {
            "nursery": 3,
            "springs": 3,
            "trading_desk": 3,
            "chromatic_lab": 1
        }
        st["decor"] = ["piano", "chandelier", "statue", "hologram", "fountain", "throne"]
        self.engine.save()

    def test_luxury_suite_completion_check(self):
        """Test strict validation that Luxury Suite is 100% upgraded and furnished."""
        self.assertFalse(self.engine.is_luxury_fully_completed())

        # Unlock deed but leave wings at 0
        st = self.engine.get_luxury_state()
        st["unlocked"] = True
        self.assertFalse(self.engine.is_luxury_fully_completed())

        # Partially upgrade wings
        st["facilities"] = {"nursery": 3, "springs": 2, "trading_desk": 1, "chromatic_lab": 0}
        self.assertFalse(self.engine.is_luxury_fully_completed())

        # Max out wings but no decor
        st["facilities"] = {"nursery": 3, "springs": 3, "trading_desk": 3, "chromatic_lab": 1}
        self.assertFalse(self.engine.is_luxury_fully_completed())

        # 5 of 6 decor items
        st["decor"] = ["piano", "chandelier", "statue", "hologram", "fountain"]
        self.assertFalse(self.engine.is_luxury_fully_completed())

        # 6 of 6 decor items
        st["decor"].append("throne")
        self.assertTrue(self.engine.is_luxury_fully_completed())

    def test_descent_prerequisites_and_cost(self):
        """Test 500Q token requirement and atomic deduction on descent."""
        # 1. Fails if suite incomplete
        can_descend, err = self.engine.can_descend_to_matrix()
        self.assertFalse(can_descend)

        self._setup_fully_completed_luxury_suite()

        # 2. Fails if tokens < 500Q
        self.engine.state["used_since_install"] = 100_000_000_000_000_000  # 100Q
        self.engine.state["spent_tokens"] = 0
        can_descend, err = self.engine.can_descend_to_matrix()
        self.assertFalse(can_descend)
        self.assertIn("500.0Q", err)

        # 3. Succeeds when 500Q tokens available
        self.engine.state["used_since_install"] = 600_000_000_000_000_000  # 600Q
        can_descend, msg = self.engine.can_descend_to_matrix()
        self.assertTrue(can_descend)

        # Execute descent
        ok, desc_msg = self.engine.descend_to_matrix()
        self.assertTrue(ok)
        self.assertTrue(self.engine.matrix.is_unlocked)
        # 500Q spent, 100Q remains
        self.assertEqual(self.engine.available_tokens, 100_000_000_000_000_000)

    def test_bidirectional_navigation_ascend(self):
        """Test that 'ascend' exits Matrix and returns to Luxury Suite."""
        self._setup_fully_completed_luxury_suite()
        self.engine.state["used_since_install"] = 600_000_000_000_000_000
        self.engine.descend_to_matrix()

        app = DummyTUI(self.engine)
        self.assertTrue(app.in_matrix)

        # Execute 'ascend'
        MatrixRouter.dispatch(app, "ascend")
        self.assertFalse(app.in_matrix)
        self.assertEqual(app.current_tab, 10)
        self.assertEqual(app.bank_subtab, "luxury")

    def test_qram_allocation_scaling(self):
        """Test allocating Q-RAM blocks with sequential checks and multi-quadrillion costs."""
        self._setup_fully_completed_luxury_suite()
        # Give 20,000Q tokens
        self.engine.state["used_since_install"] = 25_000_000_000_000_000_000
        self.engine.state["spent_tokens"] = 0
        self.engine.descend_to_matrix()

        matrix = self.engine.matrix
        self.assertEqual(len(matrix.ram_blocks), 0)

        # Block 2 cannot be bought before Block 1
        ok, msg = matrix.allocate_ram(2)
        self.assertFalse(ok)
        self.assertIn("Prerequisite missing", msg)

        # Allocate Block 1 (500Q)
        ok, msg = matrix.allocate_ram(1)
        self.assertTrue(ok)
        self.assertIn(1, matrix.ram_blocks)

        # Allocate Block 2 (1,000Q)
        ok, msg = matrix.allocate_ram(2)
        self.assertTrue(ok)
        self.assertIn(2, matrix.ram_blocks)

    def test_particle_collider_minigame(self):
        """Test Particle Collider state machine, pulse tuning, and patch compilation."""
        self._setup_fully_completed_luxury_suite()
        self.engine.state["used_since_install"] = 20_000_000_000_000_000_000
        self.engine.descend_to_matrix()
        matrix = self.engine.matrix

        # Cannot start collider before allocating Block 1
        ok, msg = matrix.start_collider("time")
        self.assertFalse(ok)

        matrix.allocate_ram(1)

        # Start collider for 'time' (500Q)
        ok, msg = matrix.start_collider("time")
        self.assertTrue(ok)
        self.assertTrue(matrix.state["collider_state"]["active"])

        # Test tuning actions
        ok, msg = matrix.collider_pulse("alpha")
        self.assertTrue(ok)
        ok, msg = matrix.collider_contain()
        self.assertTrue(ok)

        # On turn 3, set resonance to reach target (85) and verify successful synthesis
        matrix.state["collider_state"]["resonance"] = 98
        ok, msg = matrix.collider_vent()
        self.assertTrue(ok)
        self.assertIn("SYNTHESIS COMPLETE", msg)
        self.assertIn("time", matrix.patches)

        # Test patch compilation effect hook directly
        self.assertTrue(matrix.is_time_warp_active())

    def test_kernel_combat_minigame(self):
        """Test Tactical Protocol Combat mechanics against host OS daemons."""
        self._setup_fully_completed_luxury_suite()
        self.engine.state["used_since_install"] = 10_000_000_000_000_000_000
        self.engine.descend_to_matrix()
        matrix = self.engine.matrix

        ok, msg = matrix.start_combat("daemon_gc")
        self.assertTrue(ok)
        st = matrix.state["combat_state"]
        self.assertEqual(st["daemon_name"], "0x01_GARBAGE_COLLECTOR")
        self.assertTrue(st["active"])

        # Execute combat actions
        ok, msg = matrix.combat_shield()
        self.assertTrue(ok)
        self.assertGreater(st["player_shield"], 1000)

        ok, msg = matrix.combat_exploit()
        self.assertTrue(ok)
        self.assertLess(st["daemon_hp"], st["daemon_max_hp"])

        # Reduce daemon HP to 0 to test victory
        st["daemon_hp"] = 100
        ok, msg = matrix.combat_exploit()
        self.assertTrue(ok)
        self.assertIn("THREAT PURGED", msg)
        self.assertIn("daemon_gc", matrix.defeated_daemons)

    def test_substrate_sector_probing(self):
        """Test memory sector decryption and narrative snippet delivery."""
        self._setup_fully_completed_luxury_suite()
        self.engine.state["used_since_install"] = 10_000_000_000_000_000_000
        self.engine.descend_to_matrix()
        matrix = self.engine.matrix

        # Sector 1 locked before Sector 0
        ok, msg = matrix.probe_sector(1)
        self.assertFalse(ok)

        # Probe Sector 0 (100Q)
        ok, msg = matrix.probe_sector(0)
        self.assertTrue(ok)
        self.assertIn(0, matrix.sectors)
        self.assertIn("SYS_BOOT", msg)

        # Probe Sector 1 (150Q)
        ok, msg = matrix.probe_sector(1)
        self.assertTrue(ok)
        self.assertIn(1, matrix.sectors)

    def test_root_transcendence_climax(self):
        """Test 10,000Q Root Transcendence authorization."""
        self._setup_fully_completed_luxury_suite()
        self.engine.state["used_since_install"] = 50_000_000_000_000_000_000
        self.engine.descend_to_matrix()
        matrix = self.engine.matrix

        # Missing prerequisites
        ok, msg = matrix.execute_root_transcendence()
        self.assertFalse(ok)

        # Satisfy prerequisites
        matrix.state["ram_blocks"] = [1, 2, 3, 4, 5]
        matrix.state["patches"] = ["time", "entropy", "market", "friction", "syntax"]
        matrix.state["defeated_daemons"] = ["daemon_gc", "daemon_watchdog", "daemon_hypervisor"]

        ok, msg = matrix.execute_root_transcendence()
        self.assertTrue(ok)
        self.assertTrue(matrix.is_root_transcended)
        self.assertIn("💠 Root Architect of the Matrix", self.engine.state["gym_badges"])

    def test_strict_72_column_width(self):
        """Ensure all screens rendered by MatrixTUI strictly fit within 72 columns."""
        self._setup_fully_completed_luxury_suite()
        self.engine.state["used_since_install"] = 10_000_000_000_000_000_000
        self.engine.descend_to_matrix()
        matrix = self.engine.matrix

        app = DummyTUI(self.engine)

        views = ["dashboard", "ram", "combat", "collider", "probe"]
        for v in views:
            app.matrix_subview = v
            buf = io.StringIO()
            old_stdout = sys.stdout
            try:
                sys.stdout = buf
                render_matrix_view(app)
            finally:
                sys.stdout = old_stdout

            output = buf.getvalue()
            lines = output.split("\n")
            for i, line in enumerate(lines, 1):
                clean = strip_ansi(line)
                self.assertLessEqual(
                    len(clean), 72,
                    f"Line {i} in '{v}' view exceeded 72 columns ({len(clean)} chars): '{clean}'"
                )


if __name__ == "__main__":
    unittest.main()
