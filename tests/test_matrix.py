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
from poketokenbar.game.storage import StorageManager, get_state_file
from poketokenbar.game.matrix.models import (
    MATRIX_ENTRY_COST,
    ROOT_TRANSCENDENCE_COST,
    QRAM_BLOCKS,
    MEMORY_NODES,
    SUBSTRATE_ENTITIES,
    EXPLOIT_TOOLS,
    DECK_SUBSYSTEMS,
    VIVIENNE_POST_TUTORIAL_QUOTES,
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
        state_file = get_state_file()
        if state_file.exists():
            try:
                state_file.unlink()
            except Exception:
                pass
        self.engine = CompanionEngine()

    def tearDown(self):
        state_file = get_state_file()
        if state_file.exists():
            try:
                state_file.unlink()
            except Exception:
                pass

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

    def _unlock_matrix(self):
        """Helper to fully prime and descend to the Matrix."""
        self._setup_fully_completed_luxury_suite()
        self.engine.state["used_since_install"] = 10_000_000_000_000_000_000
        self.engine.descend_to_matrix()

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
        self.assertIn("500.0Q tokens", err)

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
        self.assertIn("Type 'confirm'", app.message)
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

    def test_node_view_clean_rendering_and_id_prompt(self):
        """Verify node view displays command target IDs in parentheses and omits long descriptions."""
        self._setup_fully_completed_luxury_suite()
        self.engine.state["used_since_install"] = 10_000_000_000_000_000_000
        self.engine.descend_to_matrix()
        app = DummyTUI(self.engine)
        app.matrix_subview = "nodes"

        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            render_matrix_view(app)
        finally:
            sys.stdout = old_stdout

        out = strip_ansi(buf.getvalue())
        # Verify target IDs are explicitly inside parentheses
        self.assertIn("(ID: nursery)", out)
        self.assertIn("(ID: expeditions)", out)
        self.assertIn("(ID: bank)", out)
        self.assertIn("(ID: roster)", out)
        self.assertIn("(ID: combat)", out)

        # Verify inline descriptions are removed from main node view
        self.assertNotIn("Bio-synthetic incubation pipelines", out)

        # Verify command instructions
        self.assertIn("hack <id>", out)
        self.assertIn("help <id>", out)

    def test_node_specific_help_command(self):
        """Verify 'help <id>' provides detailed subsystem overview and tweak explanations."""
        self._setup_fully_completed_luxury_suite()
        self.engine.state["used_since_install"] = 10_000_000_000_000_000_000
        self.engine.descend_to_matrix()
        app = DummyTUI(self.engine)

        # 1. Test routing with canonical ID
        MatrixRouter.dispatch(app, "help nursery")
        self.assertEqual(app.matrix_subview, "help")
        self.assertEqual(app.help_node_id, "nursery")

        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            render_matrix_view(app)
        finally:
            sys.stdout = old_stdout

        out = buf.getvalue()
        self.assertIn("NODE MANUAL: 0x10_NURSERY_BUS", out)
        self.assertIn("Bio-synthetic incubation", out)
        self.assertIn("AVAILABLE TWEAKS FOR UPPER GAME", out)
        self.assertIn("egg_speed", out)
        self.assertIn("shiny_rate", out)
        self.assertIn("tweak nursery egg_speed", out)

        # Verify strict <= 72 columns on every line in node help
        for line in out.splitlines():
            clean = strip_ansi(line)
            self.assertLessEqual(len(clean), 72, f"Line exceeds 72 columns: '{clean}'")

        # 2. Test routing with code hex alias '0x10'
        MatrixRouter.dispatch(app, "help 0x10")
        self.assertEqual(app.help_node_id, "nursery")

    def test_hacknet_pentest_flow(self):
        """Test Hacknet pen-testing flow: port scan, exploit deployment, tick cycles, spoofing, and cracking."""
        self._setup_fully_completed_luxury_suite()
        self.engine.state["used_since_install"] = 10_000_000_000_000_000_000
        self.engine.descend_to_matrix()
        matrix = self.engine.matrix

        # Cannot pen-test unknown node
        ok, msg = matrix.start_pentest("unknown_node")
        self.assertFalse(ok)

        # Start pen-test for nursery
        ok, msg = matrix.start_pentest("nursery")
        self.assertTrue(ok)
        self.assertIsNotNone(matrix.active_breach)
        breach = matrix.active_breach
        self.assertEqual(breach["node_id"], "nursery")
        self.assertEqual(breach["required_ports"], 2)
        self.assertIn("21", breach["ports"])
        self.assertIn("22", breach["ports"])
        self.assertIn("80", breach["ports"])

        # Abort test
        ok_a, msg_a = matrix.abort_pentest()
        self.assertTrue(ok_a)
        self.assertIsNone(matrix.active_breach)

        # Restart pen-test
        matrix.start_pentest("nursery")
        breach = matrix.active_breach

        # 1. Test deploying incompatible tool
        ok_bad, msg_bad = matrix.run_exploit(21, "bruteforce")
        self.assertFalse(ok_bad)
        self.assertIn("Incompatible exploit", msg_bad)

        # 2. Deploy valid tool (auto-detect tool when None is passed)
        ok_exp, msg_exp = matrix.run_exploit(21)
        self.assertTrue(ok_exp)
        self.assertEqual(len(breach["threads"]), 1)
        self.assertEqual(breach["ports"]["21"]["status"], "cracking")

        # 3. Test thread limit enforcement (base deck has 1 thread)
        ok_sat, msg_sat = matrix.run_exploit(80, "inject")
        self.assertFalse(ok_sat)
        self.assertIn("saturated", msg_sat)

        # 4. Advance execution cycle by 1 turn
        ok_t1, msg_t1 = matrix.tick_pentest(1)
        self.assertTrue(ok_t1)
        self.assertEqual(breach["ports"]["21"]["progress"], 1)
        self.assertEqual(breach["ports"]["21"]["status"], "cracking")

        # 5. Advance execution cycle by 2nd turn -> Port 21 compromised!
        ok_t2, msg_t2 = matrix.tick_pentest(1)
        self.assertTrue(ok_t2)
        self.assertEqual(breach["ports"]["21"]["status"], "compromised")
        self.assertEqual(len(breach["threads"]), 0)  # thread freed
        self.assertLess(breach["firewall"], 500)  # firewall damaged

        # 6. Cannot crack node yet (only 1 of 2 required ports compromised)
        ok_cr_early, msg_cr_early = matrix.crack_node()
        self.assertFalse(ok_cr_early)
        self.assertIn("Requires at least 2", msg_cr_early)

        # 7. Deploy 2nd exploit on Port 80 (inject, 2 turns)
        matrix.owned_tools.append("inject")
        ok_exp2, msg_exp2 = matrix.run_exploit(80, "inject")
        self.assertTrue(ok_exp2)

        # Test spoofing connection logs
        trace_before = matrix.trace_level
        ok_sp, msg_sp = matrix.spoof_trace()
        self.assertTrue(ok_sp)
        self.assertLessEqual(matrix.trace_level, trace_before)

        # Finish Port 80
        matrix.tick_pentest(2)
        self.assertEqual(breach["ports"]["80"]["status"], "compromised")

        # 8. Crack node!
        ok_cr, msg_cr = matrix.crack_node()
        self.assertTrue(ok_cr)
        self.assertIn("nursery", matrix.hacked_nodes)
        self.assertIsNone(matrix.active_breach)

    def test_pentest_router_dispatch(self):
        """Test router commands: hack, run, step, spoof, crack."""
        self._setup_fully_completed_luxury_suite()
        self.engine.state["used_since_install"] = 10_000_000_000_000_000_000
        self.engine.descend_to_matrix()
        app = DummyTUI(self.engine)

        MatrixRouter.dispatch(app, "hack nursery")
        self.assertEqual(app.matrix_subview, "breach")
        self.assertIsNotNone(self.engine.matrix.active_breach)

        MatrixRouter.dispatch(app, "run 21 overflow")
        self.assertIn("Deployed", app.message)

        MatrixRouter.dispatch(app, "step")
        self.assertIn("EXECUTION CYCLE ADVANCED", app.message)

        MatrixRouter.dispatch(app, "spoof")
        self.assertIn("CONNECTION MASKED", app.message)

        MatrixRouter.dispatch(app, "step")  # Port 21 finishes

        # Run port 80
        MatrixRouter.dispatch(app, "run 80")
        MatrixRouter.dispatch(app, "step")
        MatrixRouter.dispatch(app, "step")  # Port 80 finishes

        # Crack node
        MatrixRouter.dispatch(app, "crack")
        self.assertIn("ROOT PRIVILEGES GRANTED", app.message)
        self.assertEqual(app.matrix_subview, "tweaks")
        self.assertIn("nursery", self.engine.matrix.hacked_nodes)

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
        self.engine.state["install_baseline_set"] = True
        self.engine.state["egg_tier"] = "common"
        self.engine.state["egg_usage"] = 0
        self.engine.set_active_mon(None)
        # Process usage: 1,000 raw tokens * 1.7x XP multiplier (100% happiness + Lv 3 Springs) * 5x speed = 8,500 progress
        curr = self.engine.state.get("used_since_install", 0)
        self.engine.process_usage(curr + 1_000)
        self.assertEqual(self.engine.state["egg_usage"], 8500)

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
        matrix.allocate_ram(1)  # 32 Exaflops, 2 slots
        matrix.allocate_ram(2)  # 64 Exaflops, 3 slots

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
        self.assertIn("deflected by thread", msg)

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
        out_before = strip_ansi(buf.getvalue())
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
        out_after = strip_ansi(buf2.getvalue())
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
        # Verify Screen 1, Screen 2, and Screen 3 narrative elements
        self.assertIn("SUBTERRANEAN HYPERVISOR LIFT", out)
        self.assertIn("ADDR 0x7FFF0010: active_mon", out)
        self.assertIn("THE WORLD IS AN EXECUTION SANDBOX", out)
        self.assertIn("TOKENS ARE COGNITIVE ENERGY", out)
        self.assertIn("Madame Vivienne, Grand Concierge & Substrate Architect", out)
        self.assertIn("boot Cyberdeck Shell & Orientation", out)

        # Verify old text-heavy directives view is deleted
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

    def test_tutorial_progression_step_by_step(self):
        """Verify the full 7-step Madame Vivienne tutorial questline progresses correctly."""
        self._unlock_matrix()
        matrix = self.engine.matrix

        # Step 1: Initial state is Step 1 (Network Reconnaissance)
        self.assertEqual(matrix.tutorial_step, 1)
        self.assertFalse(matrix.tutorial_completed)
        q1 = matrix.get_current_tutorial_quest()
        self.assertEqual(q1["title"], "Network Reconnaissance")
        self.assertEqual(q1["speaker"], "Madame Vivienne")

        # Action 1: scan -> advances to Step 2
        matrix.scan_network()
        self.assertEqual(matrix.tutorial_step, 2)
        q2 = matrix.get_current_tutorial_quest()
        self.assertEqual(q2["title"], "Vulnerability Analysis")

        # Action 2: help nursery -> advances to Step 3
        app = DummyTUI(self.engine)
        MatrixRouter.dispatch(app, "help nursery")
        self.assertEqual(matrix.tutorial_step, 3)
        q3 = matrix.get_current_tutorial_quest()
        self.assertEqual(q3["title"], "Establish Remote Link")

        # Action 3: hack nursery -> advances to Step 4
        ok, _ = matrix.start_pentest("nursery")
        self.assertTrue(ok)
        self.assertEqual(matrix.tutorial_step, 4)
        q4 = matrix.get_current_tutorial_quest()
        self.assertEqual(q4["title"], "Exploit Deployment")

        # Action 4: run 21 overflow -> advances to Step 5
        ok_exp, _ = matrix.run_exploit(21, "overflow")
        self.assertTrue(ok_exp)
        self.assertEqual(matrix.tutorial_step, 5)
        q5 = matrix.get_current_tutorial_quest()
        self.assertEqual(q5["title"], "Execution & Countermeasures")

        # Action 5: step -> advances to Step 6
        ok_step, _ = matrix.tick_pentest(1)
        self.assertTrue(ok_step)
        self.assertEqual(matrix.tutorial_step, 6)
        q6 = matrix.get_current_tutorial_quest()
        self.assertEqual(q6["title"], "Root ICE Override")

        # Compromise remaining needed turns for Port 21 and crack Port 80
        matrix.tick_pentest(1)  # Port 21 compromised!
        matrix.owned_tools.append("inject")
        matrix.run_exploit(80, "inject")
        matrix.tick_pentest(2)  # Port 80 compromised!

        # Action 6: crack -> advances to Step 7
        ok_crack, _ = matrix.crack_node()
        self.assertTrue(ok_crack)
        self.assertIn("nursery", matrix.hacked_nodes)
        self.assertEqual(matrix.tutorial_step, 7)
        q7 = matrix.get_current_tutorial_quest()
        self.assertEqual(q7["title"], "Reality Overclock")

        # Action 7: tweak nursery egg_speed 2x -> completes tutorial!
        ok_twk, _ = matrix.apply_tweak("nursery", "egg_speed", "2x")
        self.assertTrue(ok_twk)
        self.assertTrue(matrix.tutorial_completed)
        self.assertEqual(matrix.tutorial_step, 8)
        comp = matrix.get_current_tutorial_quest()
        self.assertEqual(comp["title"], "Root Shell Master")

    def test_tutorial_skip_and_reset(self):
        """Verify tutorial can be cleanly skipped and reset via engine methods and router."""
        self._unlock_matrix()
        matrix = self.engine.matrix
        app = DummyTUI(self.engine)

        self.assertEqual(matrix.tutorial_step, 1)
        self.assertFalse(matrix.tutorial_completed)

        # Skip via router command 'quest skip'
        MatrixRouter.dispatch(app, "quest skip")
        self.assertTrue(matrix.tutorial_completed)
        self.assertEqual(matrix.tutorial_step, 8)
        self.assertIn("tutorial bypassed", app.message)

        # Reset via router command 'quest reset'
        MatrixRouter.dispatch(app, "quest reset")
        self.assertFalse(matrix.tutorial_completed)
        self.assertEqual(matrix.tutorial_step, 1)
        self.assertIn("re-synchronized", app.message)

    def test_tutorial_ui_rendering_and_column_width(self):
        """Verify Madame Vivienne guidance boxes and quest briefing screens obey <= 72 cols."""
        self._unlock_matrix()
        app = DummyTUI(self.engine)

        from poketokenbar.tui.matrix_tui import (
            _render_deck_view,
            _render_pentest_view,
            _render_quest_view,
        )

        # 1. Deck View with Tutorial Guidance Box
        buf_deck = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf_deck
            _render_deck_view(app, self.engine.matrix)
        finally:
            sys.stdout = old_stdout
        out_deck = buf_deck.getvalue()
        self.assertIn("COM-LINK // MADAME VIVIENNE", out_deck)
        self.assertIn("QUEST 1/7: RECON", out_deck)
        for line in out_deck.splitlines():
            clean = strip_ansi(line)
            self.assertLessEqual(len(clean), 72, f"Deck line exceeds 72 cols: '{clean}'")

        # 2. Pentest View with Vivienne Objective Reminder & Active Thread
        self.engine.matrix.tutorial_step = 4
        self.engine.matrix.start_pentest("nursery")
        ok_th, _ = self.engine.matrix.run_exploit(21, "overflow")
        self.assertTrue(ok_th)
        buf_pen = io.StringIO()
        try:
            sys.stdout = buf_pen
            _render_pentest_view(app, self.engine.matrix)
        finally:
            sys.stdout = old_stdout
        out_pen = buf_pen.getvalue()
        self.assertIn("[VIVIENNE]:", out_pen)
        self.assertIn("Thread 1: Port 21", out_pen)
        for line in out_pen.splitlines():
            clean = strip_ansi(line)
            self.assertLessEqual(len(clean), 72, f"Pentest line exceeds 72 cols: '{clean}'")

        # 3. Dedicated Quest Briefing View (_render_quest_view)
        buf_q = io.StringIO()
        try:
            sys.stdout = buf_q
            _render_quest_view(app, self.engine.matrix)
        finally:
            sys.stdout = old_stdout
        out_q = buf_q.getvalue()
        self.assertIn("COM-LINK BRIEFING // MADAME VIVIENNE", out_q)
        self.assertIn("OPERATION: ROOT OVERRIDE", out_q)
        for line in out_q.splitlines():
            clean = strip_ansi(line)
            self.assertLessEqual(len(clean), 72, f"Quest view line exceeds 72 cols: '{clean}'")

    def test_tutorial_router_commands(self):
        """Verify 'quest', 'tutorial', and 'comlink' commands switch subviews properly."""
        self._unlock_matrix()
        app = DummyTUI(self.engine)

        MatrixRouter.dispatch(app, "quest")
        self.assertEqual(app.matrix_subview, "quest")
        self.assertIn("COM-LINK briefing", app.message)

        MatrixRouter.dispatch(app, "deck")
        self.assertEqual(app.matrix_subview, "deck")

        MatrixRouter.dispatch(app, "tutorial")
        self.assertEqual(app.matrix_subview, "quest")

    def test_matrix_reinit_in_settings_and_router(self):
        """Verify matrix re-init process in settings tab, confirmation flow, and router."""
        from poketokenbar.tui_tabs.settings import render_settings_tab

        # Setup: unlock matrix and progress in it
        self._unlock_matrix()
        self.engine.matrix.allocate_ram(1)
        self.engine.matrix.state["tutorial_step"] = 5
        self.assertTrue(self.engine.matrix.is_unlocked)
        self.assertGreater(len(self.engine.matrix.ram_blocks), 0)

        # 1. Verify Settings Tab rendering (Page 3 contains item 15)
        app = DummyTUI(self.engine)
        app.current_tab = 11
        app.settings_page = 3
        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            render_settings_tab(app)
        finally:
            sys.stdout = old_stdout
        out = buf.getvalue()
        self.assertIn("[15] Singularity Matrix Sub-0:", out)
        self.assertIn("ACTIVE", out)
        self.assertIn("matrix init", out)

        # 2. Verify CommandRouter triggers confirmation when unlocked
        CommandRouter.dispatch(app, "matrix init")
        self.assertTrue(getattr(app, "pending_matrix_init", False))
        self.assertIn("CONFIRM", app.message)

        # 3. Confirm the re-initialization
        CommandRouter.dispatch(app, "confirm")
        self.assertFalse(getattr(app, "pending_matrix_init", False))
        self.assertFalse(self.engine.matrix.is_unlocked)
        self.assertEqual(len(self.engine.matrix.ram_blocks), 0)
        self.assertEqual(self.engine.matrix.state["tutorial_step"], 1)
        self.assertIn("fully re-initialized", app.message)

        # 4. Verify Option '15' triggers matrix init on Settings tab
        self._unlock_matrix()
        self.assertTrue(self.engine.matrix.is_unlocked)
        CommandRouter.dispatch(app, "15")
        self.assertTrue(getattr(app, "pending_matrix_init", False))
        CommandRouter.dispatch(app, "cancel")
        self.assertFalse(getattr(app, "pending_matrix_init", False))
        self.assertTrue(self.engine.matrix.is_unlocked)

        # 5. Verify matrix init directly inside MatrixRouter
        app.in_matrix = True
        MatrixRouter.dispatch(app, "matrix init")
        self.assertFalse(app.in_matrix)
        self.assertFalse(self.engine.matrix.is_unlocked)
        self.assertIn("Returned to Luxury Suite", app.message)

    def test_hardware_catalog_and_router_commands(self):
        """Verify 'ram', 'hardware', 'help hardware', and 'buy ram <1-5>' commands."""
        self._unlock_matrix()
        app = DummyTUI(self.engine)
        app.in_matrix = True

        # 1. 'hardware' or 'ram' switches to help view with hardware node
        MatrixRouter.dispatch(app, "hardware")
        self.assertEqual(app.matrix_subview, "help")
        self.assertEqual(app.help_node_id, "hardware")
        self.assertIn("Next Q-RAM: Block 1", app.message)

        # 2. 'help ram' switches to hardware specs
        MatrixRouter.dispatch(app, "help ram")
        self.assertEqual(app.matrix_subview, "help")
        self.assertEqual(app.help_node_id, "hardware")

        # 3. 'buy ram 1' allocates Q-RAM Block 1
        MatrixRouter.dispatch(app, "buy ram 1")
        self.assertIn(1, self.engine.matrix.ram_blocks)
        self.assertEqual(self.engine.matrix.max_exaflops, 32.0)
        self.assertEqual(self.engine.matrix.max_tweak_slots, 2)
        self.assertIn("DECK UPGRADED", app.message)

    def test_exploit_tool_purchasing_and_ownership(self):
        """Verify exploit software tool purchases and ownership gating."""
        self._unlock_matrix()
        matrix = self.engine.matrix
        app = DummyTUI(self.engine)

        # 1. 'overflow' is owned by default; other tools are not
        self.assertIn("overflow", matrix.owned_tools)
        self.assertNotIn("inject", matrix.owned_tools)
        self.assertNotIn("bruteforce", matrix.owned_tools)

        # 2. Deploying an uncompiled tool fails with compilation hint
        matrix.start_pentest("nursery")
        ok_unowned, msg_unowned = matrix.run_exploit(80, "inject")
        self.assertFalse(ok_unowned)
        self.assertIn("not compiled", msg_unowned)
        self.assertIn("buy tool inject", msg_unowned)

        # 3. Purchasing with insufficient tokens fails
        self.engine.state["used_since_install"] = 0
        self.engine.state["spent_tokens"] = 0
        ok_poor, msg_poor = matrix.buy_tool("inject")
        self.assertFalse(ok_poor)
        self.assertIn("Not enough spendable tokens", msg_poor)

        # 4. Purchasing with sufficient tokens succeeds
        self.engine.state["used_since_install"] = 10_000_000_000_000_000_000
        ok_buy, msg_buy = matrix.buy_tool("inject")
        self.assertTrue(ok_buy)
        self.assertIn("SOFTWARE COMPILED", msg_buy)
        self.assertIn("inject", matrix.owned_tools)

        # 5. Deploying the newly compiled tool now succeeds
        ok_exp, msg_exp = matrix.run_exploit(80, "inject")
        self.assertTrue(ok_exp)
        self.assertIn("Deployed Pickle_RCE.py", msg_exp)

        # 6. Buying an already compiled tool fails
        ok_again, msg_again = matrix.buy_tool("inject")
        self.assertFalse(ok_again)
        self.assertIn("already compiled", msg_again)

        # 7. Buying unknown tool fails
        ok_unk, msg_unk = matrix.buy_tool("magic_hack")
        self.assertFalse(ok_unk)
        self.assertIn("Unknown exploit software", msg_unk)

    def test_exploit_tool_overclocking_v2(self):
        """Verify upgrading software exploits to v2.0 Overclocked (-1 turn, -25% Exaflop cost)."""
        self._unlock_matrix()
        matrix = self.engine.matrix

        # 1. Upgrading an unowned tool fails
        ok_unowned, msg_unowned = matrix.upgrade_tool("rce")
        self.assertFalse(ok_unowned)
        self.assertIn("compile base", msg_unowned)

        # 2. Upgrading with insufficient tokens fails
        self.engine.state["used_since_install"] = 0
        self.engine.state["spent_tokens"] = 0
        ok_poor, msg_poor = matrix.upgrade_tool("overflow")
        self.assertFalse(ok_poor)
        self.assertIn("Not enough spendable tokens", msg_poor)

        # 3. Upgrading 'overflow' with sufficient tokens succeeds
        self.engine.state["used_since_install"] = 10_000_000_000_000_000_000
        ok_up, msg_up = matrix.upgrade_tool("overflow")
        self.assertTrue(ok_up)
        self.assertIn("SOFTWARE OVERCLOCKED", msg_up)
        self.assertIn("overflow", matrix.tool_upgrades)

        # 4. Deploying v2.0 'overflow' reflects -1 turn and -25% Exaflop cost
        matrix.start_pentest("nursery")
        ok_run, msg_run = matrix.run_exploit(21, "overflow")
        self.assertTrue(ok_run)
        self.assertIn("v2.0 Overclocked", msg_run)
        # Base overflow is 4.0 EF, 2 turns. v2.0 is 3.0 EF, 1 turn.
        self.assertIn("3.0 EF", msg_run)
        self.assertIn("1 turns total", msg_run)
        thread = matrix.active_breach["threads"][0]
        self.assertEqual(thread["max_progress"], 1)
        self.assertEqual(thread["cost_exaflops"], 3.0)
        self.assertTrue(thread["is_v2"])

        # 5. Upgrading an already upgraded tool fails
        ok_up2, msg_up2 = matrix.upgrade_tool("overflow")
        self.assertFalse(ok_up2)
        self.assertIn("already upgraded", msg_up2)

    def test_cyberdeck_subsystems_upgrades(self):
        """Verify upgrading Cyberdeck Subsystems (Shield, Stealth, Nanites, Clock)."""
        self._unlock_matrix()
        matrix = self.engine.matrix
        self.engine.state["used_since_install"] = 10_000_000_000_000_000_000

        # Initial subsystem levels
        self.assertEqual(matrix.get_subsystem_level("shield"), 0)
        self.assertEqual(matrix.get_subsystem_level("stealth"), 0)
        self.assertEqual(matrix.get_subsystem_level("nanites"), 0)
        self.assertEqual(matrix.get_subsystem_level("clock"), 0)
        self.assertEqual(matrix.deck_hardware["max_firewall"], 500)

        # 1. Upgrade Shield Subsystem Lv 1 (+500 Firewall -> 1,000 HP Total)
        ok_sh, msg_sh = matrix.upgrade_subsystem("shield")
        self.assertTrue(ok_sh)
        self.assertEqual(matrix.get_subsystem_level("shield"), 1)
        self.assertEqual(matrix.deck_hardware["max_firewall"], 1000)
        self.assertEqual(matrix.deck_hardware["firewall"], 1000)

        # 2. Upgrade Stealth Subsystem Lv 1 (-20% Spoof Trace & -10% Passive Trace)
        ok_st, msg_st = matrix.upgrade_subsystem("stealth")
        self.assertTrue(ok_st)
        self.assertEqual(matrix.get_subsystem_level("stealth"), 1)

        # 3. Upgrade Nanites Subsystem Lv 1 (+20% Integrity, +250 Shield on breach)
        ok_nan, msg_nan = matrix.upgrade_subsystem("nanites")
        self.assertTrue(ok_nan)
        self.assertEqual(matrix.get_subsystem_level("nanites"), 1)

        # 4. Upgrade Clock Subsystem Lv 1 (20% Double Tick Chance)
        ok_clk, msg_clk = matrix.upgrade_subsystem("clock")
        self.assertTrue(ok_clk)
        self.assertEqual(matrix.get_subsystem_level("clock"), 1)

        # 5. Upgrading to Max Level (Lv 5) and beyond
        for _ in range(4):
            matrix.upgrade_subsystem("clock")
        self.assertEqual(matrix.get_subsystem_level("clock"), 5)
        ok_max, msg_max = matrix.upgrade_subsystem("clock")
        self.assertFalse(ok_max)
        self.assertIn("already at Maximum Level", msg_max)

        # 6. Unknown subsystem
        ok_unk, msg_unk = matrix.upgrade_subsystem("quantum_laser")
        self.assertFalse(ok_unk)
        self.assertIn("Unknown subsystem", msg_unk)

    def test_vivienne_100_sentence_quote_pool(self):
        """Verify Madame Vivienne's post-tutorial broadcast pool contains exactly 100 unique sentences."""
        # 1. Exactly 100 quotes
        self.assertEqual(len(VIVIENNE_POST_TUTORIAL_QUOTES), 100)

        # 2. All 100 quotes are strictly unique
        self.assertEqual(len(set(VIVIENNE_POST_TUTORIAL_QUOTES)), 100)

        # 3. When tutorial is completed, get_current_tutorial_quest() draws from this pool
        self._unlock_matrix()
        matrix = self.engine.matrix
        matrix.tutorial_completed = True

        observed_quotes = set()
        for _ in range(50):
            quest = matrix.get_current_tutorial_quest()
            self.assertEqual(quest["title"], "Root Shell Master")
            self.assertEqual(quest["speaker"], "Madame Vivienne")
            self.assertIn(quest["summary"], VIVIENNE_POST_TUTORIAL_QUOTES)
            self.assertIn(quest["dialogue"][0], VIVIENNE_POST_TUTORIAL_QUOTES)
            observed_quotes.add(quest["summary"])

        # Over 50 random samples, we should observe multiple distinct quotes
        self.assertGreater(len(observed_quotes), 1)

        # 4. Verify all 100 quotes wrap cleanly within 64 width
        import textwrap
        for quote in VIVIENNE_POST_TUTORIAL_QUOTES:
            wrapped = textwrap.wrap(quote, width=64)
            for line in wrapped:
                self.assertLessEqual(len(line), 64)

    def test_router_subsystem_and_software_commands(self):
        """Verify command routing for software suite, purchases, and subsystem upgrades."""
        self._unlock_matrix()
        app = DummyTUI(self.engine)
        app.in_matrix = True
        self.engine.state["used_since_install"] = 10_000_000_000_000_000_000

        # 1. 'software' and 'tools' command
        MatrixRouter.dispatch(app, "software")
        self.assertEqual(app.matrix_subview, "help")
        self.assertEqual(app.help_node_id, "software")

        MatrixRouter.dispatch(app, "tools")
        self.assertEqual(app.matrix_subview, "help")
        self.assertEqual(app.help_node_id, "software")

        # 2. 'buy tool bruteforce'
        MatrixRouter.dispatch(app, "buy tool bruteforce")
        self.assertIn("bruteforce", self.engine.matrix.owned_tools)
        self.assertIn("SOFTWARE COMPILED", app.message)

        # 3. 'upgrade tool bruteforce'
        MatrixRouter.dispatch(app, "upgrade tool bruteforce")
        self.assertIn("bruteforce", self.engine.matrix.tool_upgrades)
        self.assertIn("SOFTWARE OVERCLOCKED", app.message)

        # 4. 'upgrade shield'
        init_fw = self.engine.matrix.deck_hardware["max_firewall"]
        MatrixRouter.dispatch(app, "upgrade shield")
        self.assertGreater(self.engine.matrix.deck_hardware["max_firewall"], init_fw)
        self.assertIn("SUBSYSTEM UPGRADED", app.message)

        # 5. 'upgrade stealth'
        MatrixRouter.dispatch(app, "upgrade stealth")
        self.assertEqual(self.engine.matrix.get_subsystem_level("stealth"), 1)

        # 6. Verify render_matrix_view produces output strictly <= 72 columns across all subviews
        subviews_to_test = ["deck", "nodes", "tweaks", "combat", "help", "quest"]
        for sv in subviews_to_test:
            app.matrix_subview = sv
            app.help_node_id = "software" if sv == "help" else None
            buf = io.StringIO()
            old_stdout = sys.stdout
            try:
                sys.stdout = buf
                render_matrix_view(app)
            finally:
                sys.stdout = old_stdout
            out = buf.getvalue()
            for line in out.splitlines():
                plain = strip_ansi(line)
                self.assertLessEqual(len(plain), 72, f"Line exceeds 72 cols in subview {sv}: {plain}")


if __name__ == "__main__":
    unittest.main()


