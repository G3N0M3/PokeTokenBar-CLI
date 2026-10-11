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

        # 2. Subview Switches
        if cmd in ["1", "deck", "dashboard", "dash"]:
            app.matrix_subview = "deck"
            app.message = "Cyberdeck Dashboard online."
            return
        if cmd in ["2", "scan", "nodes", "network"]:
            app.matrix_subview = "nodes"
            app.message = "Memory Node Network mapped."
            return
        if cmd in ["3", "tweaks", "tweak"]:
            app.matrix_subview = "tweaks"
            app.message = "Upper System Tweaker active."
            return
        if cmd in ["4", "combat", "fight", "arena"]:
            app.matrix_subview = "combat"
            app.message = "Tactical Combat Matrix online."
            return
        if cmd in ["5", "help", "?", "manual"]:
            app.matrix_subview = "help"
            app.message = "Cyberdeck Command Manual displayed."
            return

        # 3. Breach Protocol Minigame: 'hack <node>' & 'pick <row> <col>'
        if cmd.startswith("hack ") or cmd.startswith("breach "):
            target = cmd.split(maxsplit=1)[1].strip()
            ok, msg = engine.start_breach(target)
            if ok:
                app.matrix_subview = "breach"
            app.message = msg
            return

        if cmd.startswith("pick "):
            parts = cmd.split()
            if len(parts) >= 3 and parts[1].isdigit() and parts[2].isdigit():
                r, c = int(parts[1]), int(parts[2])
                ok, msg = engine.breach_pick(r, c)
                app.message = msg
                if "ROOT ACCESS GRANTED" in msg:
                    app.matrix_subview = "tweaks"
                elif "BREACH FAILED" in msg:
                    app.matrix_subview = "nodes"
                return
            app.message = "Invalid pick syntax! Example: 'pick 1 2' (row 0-3, col 0-3)"
            return

        if cmd in ["abort", "cancel"]:
            if engine.active_breach:
                ok, msg = engine.abort_breach()
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

        # 7. Hardware Q-RAM Upgrades: 'buy ram <1-5>' or 'upgrade <1-5>'
        if cmd.startswith("buy ram ") or cmd.startswith("ram buy ") or cmd.startswith("upgrade "):
            val = cmd.replace("buy ram", "").replace("ram buy", "").replace("upgrade", "").strip()
            if val.isdigit():
                ok, msg = engine.allocate_ram(int(val))
                app.message = msg
                return
            app.message = "Invalid block index! Example: 'buy ram 1'"
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
