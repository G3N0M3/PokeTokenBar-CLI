"""Unit tests for the Quantum Singularity Matrix (QSM) Hack-Simulator & Cyberdeck."""

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
    MEMORY_NODES,
    SUBSTRATE_ENTITIES,
)
from poketokenbar.tui.matrix_tui import render_matrix_view, render_matrix_story_intro, strip_ansi
from poketokenbar.tui.matrix_router import MatrixRouter
from poketokenbar.tui.router import CommandRouter


class DummyTUI:
    """Mock TUI for testing Matrix views and command routing."""
    def __init__(self, engine):
        self.engine = engine
        self.in_matrix = True
        self.matrix_subview = "deck"
        self.message = ""
        self.current_tab = 10
        self.bank_subtab = "luxury"
        self.pending_descend = False


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
        can_descend, err = self.engine.can_descend_to_matrix()
        self.assertFalse(can_descend)
        self.assertIn("500.0Q tokens required", err)

        # 3. Succeeds if tokens >= 500Q
        self.engine.state["used_since_install"] = 600_000_000_000_000_000  # 600Q
        can_descend, err = self.engine.can_descend_to_matrix()
        self.assertTrue(can_descend)

        # 4. Atomic execution deduction
        ok, msg = self.engine.descend_to_matrix()
        self.assertTrue(ok)
        self.assertTrue(self.engine.matrix.is_unlocked)
        self.assertEqual(self.engine.available_tokens, 100_000_000_000_000_000)

        # 5. Subsequent descents are free
        ok2, msg2 = self.engine.descend_to_matrix()
        self.assertTrue(ok2)
        self.assertEqual(self.engine.available_tokens, 100_000_000_000_000_000)

    def test_descent_confirmation_flow(self):
        """Test two-step confirmation before debiting 500Q tokens."""
        self._setup_fully_completed_luxury_suite()
        self.engine.state["used_since_install"] = 600_000_000_000_000_000
        app = DummyTUI(self.engine)
        app.current_tab = 10
        app.bank_subtab = "luxury"
        app.in_matrix = False

        # 1. 'descend' prompts confirmation without debiting tokens yet
        CommandRouter.dispatch(app, "descend")
        self.assertTrue(app.pending_descend)
        self.assertFalse(app.in_matrix)
        self.assertIn("Are you sure you want to descend?", app.message)
        self.assertEqual(self.engine.available_tokens, 600_000_000_000_000_000)

        # 2. Cancel confirmation
        CommandRouter.dispatch(app, "cancel")
        self.assertFalse(app.pending_descend)
        self.assertFalse(app.in_matrix)
        self.assertIn("cancelled", app.message.lower())
        self.assertEqual(self.engine.available_tokens, 600_000_000_000_000_000)

        # 3. 'descend' again, then confirm
        CommandRouter.dispatch(app, "descend")
        self.assertTrue(app.pending_descend)
        CommandRouter.dispatch(app, "confirm")
        self.assertFalse(app.pending_descend)
        self.assertTrue(app.in_matrix)
        self.assertTrue(self.engine.matrix.is_unlocked)
        self.assertEqual(self.engine.available_tokens, 100_000_000_000_000_000)

        # 4. Once unlocked, ascend and then descend again bypasses confirmation
        MatrixRouter.dispatch(app, "ascend")
        self.assertFalse(app.in_matrix)
        CommandRouter.dispatch(app, "descend")
        self.assertFalse(app.pending_descend)
        self.assertTrue(app.in_matrix)
        self.assertEqual(self.engine.available_tokens, 100_000_000_000_000_000)

    def test_qram_allocation_scaling(self):
        """Test allocating Q-RAM blocks with sequential checks and multi-quadrillion costs."""
        self._setup_fully_completed_luxury_suite()
        self.engine.state["used_since_install"] = 25_000_000_000_000_000_000
        self.engine.state["spent_tokens"] = 0
        self.engine.descend_to_matrix()

        matrix = self.engine.matrix
        self.assertEqual(len(matrix.ram_blocks), 0)
        self.assertEqual(matrix.max_exaflops, 16.0)

        # Block 2 cannot be bought before Block 1
        ok, msg = matrix.allocate_ram(2)
        self.assertFalse(ok)
        self.assertIn("Prerequisite missing", msg)

        # Allocate Block 1 (500Q) -> 32.0 Exaflops
        ok, msg = matrix.allocate_ram(1)
        self.assertTrue(ok)
        self.assertIn(1, matrix.ram_blocks)
        self.assertEqual(matrix.max_exaflops, 32.0)

        # Allocate Block 2 (1,000Q) -> 64.0 Exaflops
        ok, msg = matrix.allocate_ram(2)
        self.assertTrue(ok)
        self.assertIn(2, matrix.ram_blocks)
        self.assertEqual(matrix.max_exaflops, 64.0)

    def test_network_scanning_and_node_structure(self):
        """Test scanning memory node network for upper simulation nodes."""
        self._setup_fully_completed_luxury_suite()
        self.engine.state["used_since_install"] = 10_000_000_000_000_000_000
        self.engine.descend_to_matrix()
        matrix = self.engine.matrix

        nodes = matrix.scan_network()
        self.assertIn("nursery", nodes)
        self.assertIn("expeditions", nodes)
        self.assertIn("bank", nodes)
        self.assertIn("roster", nodes)
        self.assertIn("combat", nodes)

        self.assertFalse(nodes["nursery"]["hacked"])
        self.assertEqual(nodes["nursery"]["offset"], "0x7FFF0010")

    def test_hex_breach_minigame_flow(self):
        """Test initiating breach puzzle, aligning buffer, and granting root clearance."""
        self._setup_fully_completed_luxury_suite()
        self.engine.state["used_since_install"] = 10_000_000_000_000_000_000
        self.engine.descend_to_matrix()
        matrix = self.engine.matrix

        # Cannot breach unknown node
        ok, msg = matrix.start_breach("unknown_node")
        self.assertFalse(ok)

        # Start breach for nursery
        ok, msg = matrix.start_breach("nursery")
        self.assertTrue(ok)
        self.assertIsNotNone(matrix.active_breach)
        breach = matrix.active_breach
        target_seq = list(breach["target"])

        # Abort test
        ok_a, msg_a = matrix.abort_breach()
        self.assertTrue(ok_a)
        self.assertIsNone(matrix.active_breach)

        # Start again and solve by feeding coordinates that match target sequence
        matrix.start_breach("nursery")
        breach = matrix.active_breach
        grid = breach["grid"]
        target_seq = list(breach["target"])

        for t_byte in target_seq:
            found = False
            for r in range(4):
                for c in range(4):
                    if grid[r][c] == t_byte:
                        matrix.breach_pick(r, c)
                        found = True
                        break
                if found:
                    break

        self.assertIn("nursery", matrix.hacked_nodes)
        self.assertIsNone(matrix.active_breach)

    def test_upper_system_tweaker_and_hooks(self):
        """Test tweaking upper systems and verifying hooks across game modules."""
        self._setup_fully_completed_luxury_suite()
        self.engine.state["used_since_install"] = 20_000_000_000_000_000_000
        self.engine.descend_to_matrix()
        matrix = self.engine.matrix

        # 1. Tweak fails before node is breached
        ok, msg = matrix.apply_tweak("nursery", "egg_speed", "5x")
        self.assertFalse(ok)
        self.assertIn("locked", msg)

        # Breach nursery node
        matrix.hacked_nodes.append("nursery")

        # 2. Apply egg_speed tweak (requires 8.0 Exaflops)
        ok, msg = matrix.apply_tweak("nursery", "egg_speed", "5x")
        self.assertTrue(ok)
        self.assertEqual(matrix.get_tweak_val("nursery", "egg_speed"), 5)
        self.assertTrue(matrix.is_tweak_active("nursery", "egg_speed"))
        self.assertGreater(matrix.trace_level, 0)

        # 3. Test hook in engine egg incubation
        # Active companion as egg
        self.engine.state["egg_tier"] = "common"
        self.engine.state["egg_usage"] = 0
        self.engine.set_active_mon(None)
        # Process usage: 1,000 raw tokens * 5x speed = 5,000 progress
        self.engine.process_usage(1_000, 1)
        self.assertEqual(self.engine.state["egg_usage"], 5000)

        # 4. Remove tweak
        ok_rm, msg_rm = matrix.remove_tweak("nursery", "egg_speed")
        self.assertTrue(ok_rm)
        self.assertFalse(matrix.is_tweak_active("nursery", "egg_speed"))

    def test_expeditions_and_combat_tweaks(self):
        """Test expeditions and combat overdrive hooks."""
        self._setup_fully_completed_luxury_suite()
        self.engine.state["used_since_install"] = 20_000_000_000_000_000_000
        self.engine.descend_to_matrix()
        matrix = self.engine.matrix

        matrix.hacked_nodes.extend(["expeditions", "combat"])
        matrix.allocate_ram(1)  # 32 Exaflops

        # Expeditions speed & yield
        matrix.apply_tweak("expeditions", "speed", "10x")
        self.assertTrue(matrix.is_time_warp_active())
        self.assertEqual(matrix.get_tweak_val("expeditions", "speed"), 10)

        matrix.apply_tweak("expeditions", "yield", "3x")
        self.assertEqual(matrix.get_tweak_val("expeditions", "yield"), 3)

        # Combat overdrive hook
        matrix.apply_tweak("combat", "overdrive", "2.0x")
        self.assertEqual(matrix.get_tweak_val("combat", "overdrive"), 2.0)

    def test_trace_heat_and_cyber_combat(self):
        """Test trace accumulation, ambush trigger, and tactical cyber-combat."""
        self._setup_fully_completed_luxury_suite()
        self.engine.state["used_since_install"] = 10_000_000_000_000_000_000
        self.engine.descend_to_matrix()
        matrix = self.engine.matrix

        # Add trace to 100% -> triggers host daemon
        matrix.add_trace(100)
        self.assertEqual(matrix.trace_level, 100)
        self.assertIsNotNone(matrix.active_threat)
        threat = matrix.active_threat

        # Test combat actions
        ok, msg = matrix.combat_firewall()
        self.assertTrue(ok)

        ok, msg = matrix.combat_fork()
        self.assertTrue(ok)
        self.assertEqual(matrix.deck_hardware["threads"], 2)

        # Exploit deals damage
        init_hp = threat["hp"]
        ok, msg = matrix.combat_exploit()
        self.assertTrue(ok)

        # Cool trace
        ok, msg = matrix.cool_trace(50)
        self.assertTrue(ok)
        self.assertLessEqual(matrix.trace_level, 60)

    def test_root_transcendence_climax(self):
        """Test 10,000Q Root Transcendence authorization."""
        self._setup_fully_completed_luxury_suite()
        self.engine.state["used_since_install"] = 50_000_000_000_000_000_000
        self.engine.descend_to_matrix()
        matrix = self.engine.matrix

        # Missing prerequisites
        ok, msg = matrix.execute_root_transcendence()
        self.assertFalse(ok)

        # Satisfy prerequisites: Block 5, 5 nodes, 3 daemons
        matrix.state["ram_blocks"] = [1, 2, 3, 4, 5]
        matrix.state["hacked_nodes"] = ["nursery", "expeditions", "bank", "roster", "combat"]
        matrix.state["defeated_daemons"] = ["daemon_gc", "daemon_watchdog", "daemon_hypervisor"]

        ok, msg = matrix.execute_root_transcendence()
        self.assertTrue(ok)
        self.assertTrue(matrix.is_root_transcended)

    def test_strict_72_column_width(self):
        """Ensure all screens rendered by Cyberdeck TUI strictly fit within 72 columns."""
        self._setup_fully_completed_luxury_suite()
        self.engine.state["used_since_install"] = 10_000_000_000_000_000_000
        self.engine.descend_to_matrix()
        matrix = self.engine.matrix

        app = DummyTUI(self.engine)

        views = ["deck", "nodes", "breach", "combat", "tweaks", "help"]
        matrix.start_breach("nursery")
        matrix.start_combat()

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

    def test_luxury_descend_hint_progression(self):
        """Verify that before first descent, hint displays Sovereign Throne clue,
        and after first descent it displays direct descend command."""
        self._setup_fully_completed_luxury_suite()
        app = DummyTUI(self.engine)
        app.current_tab = 10
        app.bank_subtab = "luxury"

        from poketokenbar.tui_tabs.luxury import _render_unlocked_luxury_view
        
        # 1. Before first descent
        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            _render_unlocked_luxury_view(app, self.engine.available_tokens)
        finally:
            sys.stdout = old_stdout
        out_before = buf.getvalue()
        self.assertIn("There's something under the Sovereign Throne... Type 'descend'", out_before)
        self.assertNotIn("Enter Sub-Level Quantum Singularity Matrix", out_before)

        # 2. After first descent (matrix unlocked)
        self.engine.state["used_since_install"] = 600_000_000_000_000_000
        self.engine.descend_to_matrix()
        self.assertTrue(self.engine.matrix.is_unlocked)

        buf2 = io.StringIO()
        try:
            sys.stdout = buf2
            _render_unlocked_luxury_view(app, self.engine.available_tokens)
        finally:
            sys.stdout = old_stdout
        out_after = buf2.getvalue()
        self.assertIn("'descend' (Enter Sub-Level Quantum Singularity Matrix)", out_after)
        self.assertNotIn("There's something under the Sovereign Throne", out_after)

    def test_throne_interaction_subterranean_clue(self):
        """Verify throne interaction yields subtle vibration clue before first descent."""
        self._setup_fully_completed_luxury_suite()
        ok, msg = self.engine.interact_luxury_decor("throne")
        self.assertTrue(ok)
        self.assertIn("subterranean vibration hums from beneath the dais", msg)

        # After descent
        self.engine.state["used_since_install"] = 600_000_000_000_000_000
        self.engine.descend_to_matrix()
        ok2, msg2 = self.engine.interact_luxury_decor("throne")
        self.assertTrue(ok2)
        self.assertNotIn("subterranean vibration", msg2)

    def test_matrix_story_intro_rendering_and_layout(self):
        """Verify streamlined 2-screen cinematic prologue renders and satisfies <= 72 columns."""
        app = DummyTUI(self.engine)
        old_stdout = sys.stdout
        old_stdin = sys.stdin
        buf = io.StringIO()
        try:
            sys.stdout = buf
            sys.stdin = io.StringIO("\n\n")
            render_matrix_story_intro(app)
        finally:
            sys.stdout = old_stdout
            sys.stdin = old_stdin

        out = buf.getvalue()
        # Verify Screen 1 and Screen 2 narrative elements
        self.assertIn("SUBTERRANEAN HYPERVISOR LIFT", out)
        self.assertIn("ADDR 0x7FFF0010: active_mon", out)
        self.assertIn("THE WORLD IS AN EXECUTION SANDBOX", out)
        self.assertIn("TOKENS ARE COGNITIVE ENERGY", out)
        self.assertIn("boot Substrate Cyberdeck Shell", out)

        # Verify Screen 3 (Directives infodump) is DELETED
        self.assertNotIn("SUB-LEVEL 0 DIRECTIVES", out)
        self.assertNotIn("ROOT TRANSCENDENCE PROTOCOL", out)

        # Verify strict <= 72 columns on every printed line
        for line in out.splitlines():
            clean = strip_ansi(line)
            self.assertLessEqual(len(clean), 72, f"Line exceeds 72 columns: '{clean}'")

    def test_matrix_story_intro_with_active_mon(self):
        """Verify story intro handles a real active MonState without attribute errors."""
        from poketokenbar.game.models import MonState, Rarity
        mon = MonState(
            base_id=1,
            path_ids=[1, 2, 3],
            planned_path_ids=[1, 2, 3],
            stage_index=0,
            used_at_stage=0,
            rarity=Rarity.COMMON,
            total_forms=3,
            is_shiny=True,
            happiness=120,
        )
        self.engine.set_active_mon(mon)
        app = DummyTUI(self.engine)
        old_stdout = sys.stdout
        old_stdin = sys.stdin
        buf = io.StringIO()
        try:
            sys.stdout = buf
            sys.stdin = io.StringIO("\n\n")
            render_matrix_story_intro(app)
        finally:
            sys.stdout = old_stdout
            sys.stdin = old_stdin

        out = buf.getvalue()
        self.assertIn("active_mon.current_id -> Integer: 1", out)
        self.assertIn("active_mon.happiness  -> Integer: 120", out)
        self.assertIn("Boolean: True", out)

    def test_matrix_story_router_replay(self):
        """Verify 'story' command re-triggers the prologue without crashing."""
        app = DummyTUI(self.engine)
        old_stdout = sys.stdout
        old_stdin = sys.stdin
        try:
            sys.stdout = io.StringIO()
            sys.stdin = io.StringIO("\n\n")
            MatrixRouter.dispatch(app, "story")
        finally:
            sys.stdout = old_stdout
            sys.stdin = old_stdin

        self.assertIn("prologue replayed", app.message)

    def test_matrix_story_viewed_persistence(self):
        """Verify story_viewed flag defaults to False and persists when set."""
        self.assertFalse(self.engine.matrix.state.get("story_viewed", False))
        self.engine.matrix.state["story_viewed"] = True
        self.engine.save()

        # Reload
        reloaded = CompanionEngine()
        self.assertTrue(reloaded.matrix.state.get("story_viewed", False))


if __name__ == "__main__":
    unittest.main()
