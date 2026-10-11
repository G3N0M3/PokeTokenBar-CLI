"""Command router for the independent Quantum Singularity Matrix (QSM) TUI."""

from typing import Optional


class MatrixRouter:
    """Dispatches user inputs when the player is inside the Quantum Singularity Matrix."""

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
        if cmd in ["1", "dash", "dashboard"]:
            app.matrix_subview = "dashboard"
            app.message = "Matrix Dashboard active."
            return
        if cmd in ["2", "ram"]:
            app.matrix_subview = "ram"
            app.message = "Q-RAM Memory Matrix active."
            return
        if cmd in ["3", "combat"]:
            app.matrix_subview = "combat"
            app.message = "Kernel Protocol Combat active."
            return
        if cmd in ["4", "collider"]:
            app.matrix_subview = "collider"
            app.message = "Singularity Particle Collider active."
            return
        if cmd in ["5", "probe"]:
            app.matrix_subview = "probe"
            app.message = "Substrate Sector Diagnostics active."
            return

        # 3. RAM Allocation: 'buy ram <1-5>' or 'buy <1-5>'
        if cmd.startswith("buy ram ") or cmd.startswith("ram buy "):
            val = cmd.replace("buy ram", "").replace("ram buy", "").strip()
            if val.isdigit():
                ok, msg = engine.allocate_ram(int(val))
                app.message = msg
                return
            app.message = "Invalid block index! Example: 'buy ram 1'"
            return

        if getattr(app, "matrix_subview", "dashboard") == "ram" and cmd.startswith("buy "):
            val = cmd.replace("buy", "").strip()
            if val.isdigit():
                ok, msg = engine.allocate_ram(int(val))
                app.message = msg
                return

        # 4. Particle Collider Commands
        if cmd.startswith("synthesize ") or cmd.startswith("synth "):
            target = cmd.split(maxsplit=1)[1].strip()
            ok, msg = engine.start_collider(target)
            if ok:
                app.matrix_subview = "collider"
            app.message = msg
            return

        if cmd.startswith("pulse"):
            parts = cmd.split()
            freq = parts[1] if len(parts) > 1 else "alpha"
            ok, msg = engine.collider_pulse(freq)
            app.message = msg
            return

        if cmd == "contain":
            ok, msg = engine.collider_contain()
            app.message = msg
            return

        if cmd == "vent":
            ok, msg = engine.collider_vent()
            app.message = msg
            return

        if cmd == "abort" and getattr(app, "matrix_subview", "") == "collider":
            st = engine.state.get("collider_state")
            if st and st.get("active"):
                st["active"] = False
                app.engine.save()
                app.message = "Particle Collider chamber aborted. Target energy dissipated."
                return

        # 5. Kernel Combat Commands
        if cmd in ["fight", "breach"] or (cmd.startswith("combat ") and not cmd == "combat"):
            daemon_id = None
            if cmd.startswith("combat "):
                daemon_id = cmd.replace("combat", "").strip()
            ok, msg = engine.start_combat(daemon_id)
            if ok:
                app.matrix_subview = "combat"
            app.message = msg
            return

        if cmd == "exploit":
            ok, msg = engine.combat_exploit()
            app.message = msg
            return

        if cmd == "shield":
            ok, msg = engine.combat_shield()
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

        if cmd == "retreat" and getattr(app, "matrix_subview", "") == "combat":
            st = engine.state.get("combat_state")
            if st and st.get("active"):
                st["active"] = False
                app.engine.save()
                app.message = "Withdrew execution threads from combat arena."
                return

        # 6. Sector Probing
        if cmd.startswith("probe "):
            val = cmd.replace("probe", "").strip()
            if val.isdigit():
                ok, msg = engine.probe_sector(int(val))
                app.message = msg
                app.matrix_subview = "probe"
                return
            app.message = "Invalid sector index! Example: 'probe 0'"
            return

        # 7. Climax: Root Transcendence
        if cmd in ["execute root", "transcend", "root"]:
            ok, msg = engine.execute_root_transcendence()
            app.message = msg
            return

        app.message = f"Unknown command '{cmd}'. Available: dash, ram, combat, collider, probe, ascend"
