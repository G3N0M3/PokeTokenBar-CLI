"""Command router for the Quantum Singularity Matrix (QSM) Cyberdeck."""

from typing import Optional


class MatrixRouter:
    """Dispatches user inputs when the player is inside the Sub-Level 0 Cyberdeck."""

    @staticmethod
    def dispatch(app, cmd: str) -> None:
        cmd = cmd.strip().lower()
        if not cmd:
            return

        engine = app.engine.matrix

        # 1. Canonical Exit Command
        if cmd == "ascend":
            app.in_matrix = False
            app.current_tab = 10
            app.bank_subtab = "luxury"
            app.message = "Elevator ascended. Returned to Resort Area Executive Luxury Suite."
            return

        if cmd in ["matrix init", "init matrix", "matrix reset", "reset matrix"]:
            ok, msg = app.engine.reset_matrix_process()
            app.in_matrix = False
            app.current_tab = 10
            app.bank_subtab = "luxury"
            app.message = f"⚡ {msg} Returned to Luxury Suite."
            return

        # 2. Subview Switches
        if cmd in ["1", "deck", "dashboard", "dash"]:
            app.matrix_subview = "deck"
            app.help_node_id = None
            app.message = "Cyberdeck Dashboard online."
            return
        if cmd in ["2", "scan", "nodes", "network"]:
            app.matrix_subview = "nodes"
            app.help_node_id = None
            app.message = "Memory Node Network mapped."
            return
        if cmd in ["3", "tweaks", "tweak"]:
            app.matrix_subview = "tweaks"
            app.help_node_id = None
            app.message = "Upper System Tweaker active."
            return
        if cmd in ["4", "combat", "fight", "arena"]:
            app.matrix_subview = "combat"
            app.help_node_id = None
            app.message = "Tactical Combat Matrix online."
            return
        if cmd in ["5", "help", "?", "manual"]:
            app.matrix_subview = "help"
            app.help_node_id = None
            app.message = "Cyberdeck Command Manual displayed."
            return

        # 2b. Madame Vivienne COM-LINK Tutorial Quests
        if cmd in ["quest", "tutorial", "comlink"]:
            app.matrix_subview = "quest"
            app.help_node_id = None
            app.message = "COM-LINK briefing frequency synchronized."
            return

        if cmd.startswith("quest ") or cmd.startswith("tutorial "):
            parts = cmd.split(maxsplit=1)
            subcmd = parts[1].strip().lower() if len(parts) > 1 else ""
            if subcmd in ["skip", "bypass"]:
                ok, msg = engine.skip_tutorial()
                app.message = msg
                app.matrix_subview = "deck"
                return
            elif subcmd in ["reset", "restart"]:
                ok, msg = engine.reset_tutorial()
                app.message = msg
                app.matrix_subview = "quest"
                return
            app.message = "Usage: 'quest', 'quest skip', or 'quest reset'."
            return

        if cmd in ["software", "tools", "exploits", "tool"]:
            app.matrix_subview = "help"
            app.help_node_id = "software"
            app.message = "Showing Exploit Software Suite & compiled tools."
            return

        if cmd.startswith("help ") or cmd.startswith("? "):
            target = cmd.split(maxsplit=1)[1].strip()
            if target.lower() in ["hardware", "ram", "qram", "upgrade", "upgrades"]:
                app.matrix_subview = "help"
                app.help_node_id = "hardware"
                app.message = "Showing Cyberdeck Hardware & Q-RAM specifications."
                return
            if target.lower() in ["software", "tools", "exploits", "tool"]:
                app.matrix_subview = "help"
                app.help_node_id = "software"
                app.message = "Showing Exploit Software Suite & specifications."
                return
            from poketokenbar.game.matrix.models import MEMORY_NODES
            resolved = engine.resolve_node_id(target)
            if resolved:
                app.matrix_subview = "help"
                app.help_node_id = resolved
                engine.advance_tutorial("help_node")
                app.message = f"Showing manual for node '{resolved}'."
                return
            valid_nodes = ", ".join([k for k in MEMORY_NODES.keys() if k != "root"])
            app.message = f"Unknown node '{target}'! Available: {valid_nodes}, 'help hardware', or 'help software'"
            return

        # 3. Hacknet Pen-Testing: 'hack <node>', 'run <port> [tool]', 'step', 'spoof', 'crack', 'abort'
        if cmd.startswith("hack ") or cmd.startswith("breach ") or cmd.startswith("pentest "):
            target = cmd.split(maxsplit=1)[1].strip()
            ok, msg = engine.start_pentest(target)
            if ok:
                app.matrix_subview = "breach"
            app.message = msg
            return

        if cmd.startswith("run ") or (engine.active_breach and cmd.startswith("exploit ") and " " in cmd):
            parts = cmd.split()
            if len(parts) >= 2 and parts[1].isdigit():
                port = int(parts[1])
                tool = parts[2] if len(parts) >= 3 else None
                ok, msg = engine.run_exploit(port, tool)
                app.message = msg
                return
            app.message = "Usage: 'run <port> [tool]' (e.g. 'run 21 overflow' or 'run 21')"
            return

        if cmd in ["step", "wait", "tick"]:
            if engine.active_breach:
                ok, msg = engine.tick_pentest(1)
                app.message = msg
                if "INTRUSION DETECTED" in msg:
                    app.matrix_subview = "combat"
                return
            app.message = "No active pen-testing session to advance cycles."
            return

        if cmd in ["spoof", "mask"]:
            if engine.active_breach:
                ok, msg = engine.spoof_trace()
                app.message = msg
                return
            app.message = "No active pen-testing session to spoof."
            return

        if cmd in ["crack", "crack node", "seize root"] or (cmd == "root" and engine.active_breach):
            ok, msg = engine.crack_node()
            app.message = msg
            if ok:
                app.matrix_subview = "tweaks"
            return

        if cmd.startswith("pick "):
            parts = cmd.split()
            if len(parts) >= 3 and parts[1].isdigit() and parts[2].isdigit():
                r, c = int(parts[1]), int(parts[2])
                ok, msg = engine.breach_pick(r, c)
                app.message = msg
                return
            app.message = "Breach format upgraded to Pen-Testing. Use 'run <port> [tool]' to deploy."
            return

        if cmd in ["abort", "cancel", "disconnect"]:
            if engine.active_breach:
                ok, msg = engine.abort_pentest()
                app.matrix_subview = "nodes"
                app.message = msg
                return
            elif engine.active_threat:
                ok, msg = engine.combat_flee()
                app.matrix_subview = "deck"
                app.message = msg
                return

        # 4. Reality Tweaker: 'tweak <node> <param> <val>' & 'untweak <node> <param>'
        if cmd.startswith("tweak "):
            parts = cmd.split()
            if len(parts) == 4:
                node_id, param, val = parts[1], parts[2], parts[3]
                ok, msg = engine.apply_tweak(node_id, param, val)
                app.message = msg
                return
            elif len(parts) == 2:
                app.matrix_subview = "tweaks"
                app.message = f"Showing tweak parameters for node '{parts[1]}'."
                return
            app.message = "Usage: 'tweak <node> <param> <val>' (e.g. 'tweak nursery egg_speed 5x')"
            return

        if cmd.startswith("untweak "):
            parts = cmd.split()
            if len(parts) >= 3:
                node_id, param = parts[1], parts[2]
                ok, msg = engine.remove_tweak(node_id, param)
                app.message = msg
                return
            app.message = "Usage: 'untweak <node> <param>' (e.g. 'untweak nursery egg_speed')"
            return

        # 5. Trace Cooling & Telemetry Scrubbing
        if cmd in ["tracekill", "cool", "scrub", "trace cool"]:
            ok, msg = engine.cool_trace()
            app.message = msg
            return

        if cmd == "trace":
            app.message = f"Trace Heat: {engine.trace_level}% [{engine._trace_status_label(engine.trace_level)}]"
            return

        # 6. Tactical Cyber-Combat Commands
        if cmd.startswith("combat ") and not cmd in ["combat"]:
            target_id = cmd.replace("combat", "").strip()
            ok, msg = engine.start_combat(target_id)
            if ok:
                app.matrix_subview = "combat"
            app.message = msg
            return

        if cmd == "exploit":
            ok, msg = engine.combat_exploit()
            app.message = msg
            return

        if cmd in ["firewall", "shield"]:
            ok, msg = engine.combat_firewall()
            app.message = msg
            return

        if cmd == "fork":
            ok, msg = engine.combat_fork()
            app.message = msg
            return

        if cmd == "overflow":
            ok, msg = engine.combat_overflow()
            app.message = msg
            return

        if cmd == "repair":
            ok, msg = engine.combat_repair()
            app.message = msg
            return

        if cmd in ["flee", "retreat", "run"]:
            ok, msg = engine.combat_flee()
            app.matrix_subview = "deck"
            app.message = msg
            return

        # 7. Hardware, Software, and Subsystem Upgrades
        if cmd.startswith("buy tool ") or cmd.startswith("buy exploit ") or cmd.startswith("buy software "):
            for prefix in ["buy tool ", "buy exploit ", "buy software "]:
                if cmd.startswith(prefix):
                    tool_target = cmd[len(prefix):].strip()
                    ok, msg = engine.buy_tool(tool_target)
                    app.message = msg
                    return

        if cmd.startswith("upgrade tool ") or cmd.startswith("upgrade exploit ") or cmd.startswith("upgrade software "):
            for prefix in ["upgrade tool ", "upgrade exploit ", "upgrade software "]:
                if cmd.startswith(prefix):
                    tool_target = cmd[len(prefix):].strip()
                    ok, msg = engine.upgrade_tool(tool_target)
                    app.message = msg
                    return

        if cmd.startswith("buy ram ") or cmd.startswith("ram buy "):
            val = cmd.replace("buy ram", "").replace("ram buy", "").strip()
            if val.isdigit():
                ok, msg = engine.allocate_ram(int(val))
                app.message = msg
                return
            app.message = "Invalid block index! Example: 'buy ram 1'"
            return

        if cmd.startswith("upgrade ") or cmd.startswith("buy upgrade "):
            val = cmd.replace("buy upgrade", "").replace("upgrade", "").strip().lower()
            if val.isdigit():
                ok, msg = engine.allocate_ram(int(val))
                app.message = msg
                return
            from poketokenbar.game.matrix.models import DECK_SUBSYSTEMS, EXPLOIT_TOOLS
            if val in DECK_SUBSYSTEMS:
                ok, msg = engine.upgrade_subsystem(val)
                app.message = msg
                return
            if val in EXPLOIT_TOOLS:
                ok, msg = engine.upgrade_tool(val)
                app.message = msg
                return
            app.message = f"Unknown upgrade '{val}'! Available: shield, stealth, nanites, clock, or 'upgrade tool <name>'"
            return

        if cmd in ["ram", "hardware", "qram", "upgrades", "buy ram", "ram buy"]:
            from poketokenbar.game.matrix.models import QRAM_BLOCKS
            from poketokenbar.utils.formatting import format_tokens
            app.matrix_subview = "help"
            app.help_node_id = "hardware"
            next_b = next((b for b in range(1, 6) if b not in engine.ram_blocks), None)
            if next_b:
                b_info = QRAM_BLOCKS[next_b]
                app.message = f"Next Q-RAM: Block {next_b} ({format_tokens(b_info['cost'])} tokens). Type 'buy ram {next_b}'."
            else:
                app.message = "All 5 Q-RAM hardware blocks are fully allocated!"
            return

        # 8. Climax: Root Transcendence
        if cmd in ["execute root", "transcend", "root"]:
            ok, msg = engine.execute_root_transcendence()
            app.message = msg
            return

        # 9. Story Narration Replay
        if cmd in ["story", "lore", "intro", "prologue"]:
            from poketokenbar.tui.matrix_tui import render_matrix_story_intro
            render_matrix_story_intro(app)
            app.message = "Substrate initialization prologue replayed."
            return

        app.message = f"Unknown command '{cmd}'. Available: scan, hack, tweak, combat, tracekill, help, ascend"
