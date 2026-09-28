"""Pending confirmation handlers for reset, feed, buy, and syndicate initialization."""


def handle_pending_confirmation(app, cmd: str) -> bool:
    """Evaluates and executes any active staged confirmation states.
    
    Returns True if a staged confirmation was handled, False otherwise.
    """
    if getattr(app, "pending_reset", False) is True:
        app.pending_reset = False
        if cmd == "reset all":
            ok, msg = app.engine.reset_game_state()
            app.message = f"🧹 {msg}"
        else:
            app.message = "❌ Reset cancelled."
        return True

    if getattr(app, "pending_rocket_init", False) is True:
        app.pending_rocket_init = False
        if cmd in ["confirm", "confirm rocket", "rocket init", "yes", "y"]:
            ok, msg = app.engine.initialize_rocket_process()
            app.message = f"🚀 {msg}"
        else:
            app.message = "❌ Team Rocket initialization cancelled."
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
                app.current_tab = int(cmd)
                app.message = ""
        return True

    return False
