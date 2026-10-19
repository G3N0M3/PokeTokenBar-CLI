"""Pending confirmation handlers for reset, feed, buy, and syndicate initialization."""


def handle_pending_confirmation(app, cmd: str) -> bool:
    """Evaluates and executes any active staged confirmation states.
    
    Returns True if a staged confirmation was handled, False otherwise.
    """
    clean_cmd = str(cmd or "").strip().lower()

    if getattr(app, "pending_reset", False) is True:
        app.pending_reset = False
        if clean_cmd == "reset all":
            ok, msg = app.engine.reset_game_state()
            app.message = f"🧹 {msg}"
        else:
            app.message = "❌ Reset cancelled."
        return True

    if getattr(app, "pending_rocket_init", False) is True:
        app.pending_rocket_init = False
        if clean_cmd in ["confirm", "confirm rocket", "rocket init", "yes", "y"]:
            ok, msg = app.engine.initialize_rocket_process()
            app.message = f"🚀 {msg}"
        else:
            app.message = "❌ Team Rocket initialization cancelled."
        return True

    if getattr(app, "pending_sting_init", False) is True:
        app.pending_sting_init = False
        if clean_cmd in ["confirm", "confirm sting", "sting init", "yes", "y"]:
            ok, msg = app.engine.reset_velvet_sting()
            app.message = f"♠️ {msg}"
        else:
            app.message = "❌ Velvet Sting reset cancelled."
        return True

    if getattr(app, "pending_matrix_init", False) is True:
        app.pending_matrix_init = False
        if clean_cmd in ["confirm", "confirm matrix", "matrix init", "yes", "y"]:
            ok, msg = app.engine.reset_matrix_process()
            app.in_matrix = False
            app.matrix_subview = "dashboard"
            app.message = f"⚡ {msg}"
        else:
            app.message = "❌ Matrix re-initialization cancelled."
        return True

    if getattr(app, "pending_descend", False) is True:
        app.pending_descend = False
        if clean_cmd in ["confirm", "yes", "y", "ok", "descend"]:
            ok, msg = app.engine.descend_to_matrix()
            app.message = msg
            if ok:
                app.in_matrix = True
                app.matrix_subview = "dashboard"
        else:
            app.message = "❌ Descent cancelled. Subterranean reactor remains sealed."
        return True

    if isinstance(getattr(app, "pending_feed", None), dict):
        plan = app.pending_feed
        app.pending_feed = None
        if cmd in ["confirm", "yes", "y", "ok"]:
            ok, msg = app.engine.execute_feed_plan(plan)
            app.message = msg
        elif cmd.startswith("feed ") or cmd == "feed":
            app.handle_feed_command(cmd)
        else:
            app.message = "❌ Feeding cancelled."
            tab_max = 12 if app.engine.state.get("rocket_story_unlocked") else 11
            if cmd in [str(i) for i in range(1, tab_max + 1)]:
                app.expedition_picker_mode = False
                app.stock_terminal = None
                app.black_market_session = False
                if getattr(app, "shop_view", "normal") == "black_market":
                    app.shop_view = "normal"
                if getattr(app, "roster_subview", "roster") == "eggs":
                    app.roster_subview = "roster"
                app.luxury_subview = "main"
                app.penthouse_subview = "main"
                app.current_tab = int(cmd)
                app.message = ""
        return True

    if isinstance(getattr(app, "pending_buy", None), dict):
        plan = app.pending_buy
        app.pending_buy = None
        if cmd in ["confirm", "yes", "y", "ok", "buy"]:
            ok, msg = app.execute_pending_buy(plan)
            app.message = msg
        elif app.current_tab == 4 and (cmd.startswith("buy ") or cmd == "buy"):
            app.handle_shop_buy(cmd)
        elif app.current_tab == 10 and (cmd.startswith("buy ") or cmd == "buy" or cmd.startswith("invest ")):
            if cmd.startswith("invest "):
                app.handle_invest_command(cmd)
            else:
                app.handle_stock_terminal_buy(cmd)
        else:
            app.message = "❌ Purchase cancelled."
            tab_max = 12 if app.engine.state.get("rocket_story_unlocked") else 11
            if cmd in [str(i) for i in range(1, tab_max + 1)]:
                app.expedition_picker_mode = False
                app.stock_terminal = None
                app.black_market_session = False
                if getattr(app, "shop_view", "normal") == "black_market":
                    app.shop_view = "normal"
                if getattr(app, "roster_subview", "roster") == "eggs":
                    app.roster_subview = "roster"
                app.luxury_subview = "main"
                app.penthouse_subview = "main"
                app.current_tab = int(cmd)
                app.message = ""
        return True

    return False
