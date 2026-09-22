import sys
import time
import argparse
import datetime

from poketokenbar.tracker.manager import UsageManager
from poketokenbar.game.companion import CompanionEngine
from poketokenbar.game.models import ItemKind, Rarity
from poketokenbar.sprite_renderer import SpriteRenderer
from poketokenbar.utils.formatting import format_tokens, format_progress_bar
from poketokenbar.tui import PokeTokenBarTUI

def cmd_status(tracker: UsageManager, engine: CompanionEngine):
    summary = tracker.get_summary()
    events = engine.process_usage(summary.get("raw_total_tokens", summary["total_tokens"]), summary.get("active_days"))

    # Print any evolution, hatch, or graduation milestone events
    alerts = engine.state.get("unread_alerts", [])
    all_events = list(events)
    for a in alerts:
        if a not in all_events:
            all_events.append(a)

    for ev in all_events:
        if "Evolution!" in ev or "Egg Hatched!" in ev or "Graduation!" in ev:
            print(f"{ev}")
            if ev in engine.state.get("unread_alerts", []):
                engine.state["unread_alerts"].remove(ev)
                engine.save()

    active = engine.active_mon
    today_tok = format_tokens(summary["today_tokens"])

    if active is None:
        egg_usage = engine.state.get("egg_usage", 0)
        pct = (egg_usage / 5_000_000) * 100
        print(f"🥚 Egg Incubating ({pct:.1f}%) | Today: {today_tok} tokens")
    else:
        name = engine.api.get_species_name(active.current_id)
        shiny = "✨" if active.is_shiny else ""
        stage = f"Form {active.stage_index+1}/{active.total_forms}"
        hap = active.happiness if active else engine.state.get("happiness", 100)
        streak = engine.state.get("streak_days", 1)
        held = ""
        if active.held_item:
            from poketokenbar.game.models import ItemKind
            try:
                kind = ItemKind(active.held_item)
                held = f" | {kind.emoji} {kind.name_en}"
            except ValueError:
                held = f" | {active.held_item}"
        print(f"🐾 {shiny}{name} (#{active.current_id}) [{stage}] | 💖 {hap}% | 🔥 {streak}d{held} | Today: {today_tok} tokens | Burn: {format_tokens(summary['burn_rate_tpm'])} tpm")

def cmd_watch(tracker: UsageManager, engine: CompanionEngine, interval: float = 3.0):
    """Continuous live token monitoring mode."""
    print("📡 PokeTokenBar Live Monitor active. Press Ctrl+C to stop.")
    persistent_events = []
    try:
        while True:
            summary = tracker.get_summary()
            events = engine.process_usage(summary["total_tokens"], summary.get("active_days"))
            for ev in events:
                if ev not in persistent_events:
                    persistent_events.append(ev)
            persistent_events = persistent_events[-5:]
            
            sys.stdout.write("\033[H\033[2J")
            sys.stdout.flush()

            print(f"==========================================================")
            print(f" ⚡ POKETOKENBAR LIVE MONITOR — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"==========================================================")
            
            active = engine.active_mon

            if active:
                sp_id = active.current_id
                name = engine.api.get_species_name(sp_id)
                shiny = "✨ Shiny " if active.is_shiny else ""
                print(f" Companion: {shiny}{name} (#{sp_id}) [{active.rarity.value.upper()}]")

                sprite_path = engine.api.download_sprite(sp_id, is_shiny=active.is_shiny)
                if sprite_path:
                    sprite_size = engine.state.get("sprite_size", 30)
                    ansi = SpriteRenderer.render_png_to_ansi(sprite_path, max_cols=sprite_size, center_width=58)
                    print("\n" + ansi + "\n")
            else:
                print(" Companion: 🥚 Incubating Egg...")

            print(f" Today's Tokens:   {format_tokens(summary['today_tokens'])} (Antigravity: {format_tokens(summary['antigravity_today'])})")
            print(f" Total Tokens:     {format_tokens(summary['total_tokens'])}")
            print(f" Active Burn Rate: {format_tokens(summary['burn_rate_tpm'])} tokens/min")

            if persistent_events:
                print("\n Recent Events:")
                for ev in persistent_events:
                    print(f"  ➔ {ev}")

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitor stopped.")

def cmd_settings(engine: CompanionEngine, args, tracker: Optional[UsageManager] = None):
    if tracker is None:
        tracker = UsageManager()
    if getattr(args, "init_rocket", False):
        ok, msg = engine.initialize_rocket_process()
        print(f"🚀 {msg}")
    if getattr(args, "billing_day", None) is not None:
        ok, msg = engine.set_billing_cycle_day(args.billing_day)
        print(f"📅 {msg}")
    if getattr(args, "init_tokens", False):
        summary = tracker.get_summary(force=True)
        raw_total = summary.get("raw_total_tokens", summary.get("total_tokens", 0))
        ok, msg = engine.initialize_total_tokens(raw_total)
        print(f"📊 {msg}")
    if getattr(args, "clear_tokens_baseline", False):
        ok, msg = engine.clear_total_tokens_baseline()
        print(f"📊 {msg}")
    if getattr(args, "auto_track", None) is not None:
        val = (args.auto_track.lower() in ["on", "true", "1", "yes"])
        engine.update_settings(auto_tracking_enabled=val)
        print(f"Automatic tracking set to: {'ON' if val else 'OFF'}")
    if getattr(args, "interval", None) is not None:
        ok, msg = engine.update_settings(refresh_interval=args.interval)
        print(msg)

    is_unlocked = engine.state.get("rocket_story_unlocked", False)
    rocket_str = "ACTIVE" if is_unlocked else "UNINITIALIZED"
    b_day = engine.get_billing_cycle_day()
    base_tok = engine.state.get("baseline_total_tokens", 0)
    base_str = f"Active baseline ({format_tokens(base_tok)})" if base_tok > 0 else "Unset (showing lifetime total)"

    date_hour_str = datetime.datetime.now().strftime("%Y-%m-%d %H")

    print("\n⚙️ Current PokeTokenBar Settings:")
    print(f"  • System Date & Hour:   {date_hour_str}")
    print(f"  • Monthly Billing Day:  Day {b_day} of each month")
    print(f"  • Total Tokens Status:  {base_str}")
    print(f"  • Team Rocket:          {rocket_str}\n")

def main():
    parser = argparse.ArgumentParser(prog="ptb", description="PokeTokenBar CLI - AI Token Pokémon Companion for Linux CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="Print compact 1-line status banner (useful for prompt/tmux)")
    watch_parser = subparsers.add_parser("watch", help="Continuous live token tracking monitor")
    watch_parser.add_argument("--interval", "-i", type=float, default=3.0, help="Refresh interval in seconds")
    
    subparsers.add_parser("dex", help="View Pokédex catch history")
    subparsers.add_parser("shop", help="View Shop & available spendable tokens")
    subparsers.add_parser("card", help="Print shareable ASCII Trainer Profile Card")
    feed_parser = subparsers.add_parser("feed", help="Feed Oran Berries 🫐 to companions (e.g. 'ptb feed #25 4', 'ptb feed <=70%% 2', or 'ptb feed =70')")
    feed_parser.add_argument("target", nargs="?", default=None, help="Target Pokémon (#[id], 0 for exhausted, <=[pct], <[pct], or [pct])")
    feed_parser.add_argument("qty", nargs="?", type=int, default=None, help="Number of Oran Berries to feed (default 4 for exhausted, 1 otherwise)")
    feed_parser.add_argument("-m", "--max-happiness", type=int, default=None, help="Feed companions with happiness at or below this percentage")
    feed_parser.add_argument("-y", "--yes", action="store_true", help="Bypass confirmation prompt")

    settings_parser = subparsers.add_parser("settings", help="View or update tracking settings")
    settings_parser.add_argument("--auto-track", choices=["on", "off"], help="Toggle automatic tracking system ON or OFF")
    settings_parser.add_argument("--interval", "-i", type=float, help="Configure update interval in seconds")
    settings_parser.add_argument("--init-rocket", action="store_true", help="Initialize or reset the Team Rocket campaign and operations")
    settings_parser.add_argument("--billing-day", type=int, help="Configure monthly billing cycle start day (1-31)")
    settings_parser.add_argument("--init-tokens", action="store_true", help="Initialize/re-baseline displayed Total Tokens metric so it starts from 0")
    settings_parser.add_argument("--clear-tokens-baseline", action="store_true", help="Clear Total Tokens baseline to show lifetime total tokens")

    args = parser.parse_args()
    tracker = UsageManager()
    engine = CompanionEngine()

    if args.command == "status":
        cmd_status(tracker, engine)
    elif args.command == "watch":
        cmd_watch(tracker, engine, args.interval)
    elif args.command == "card":
        print(engine.generate_trainer_card())
    elif args.command == "feed":
        if getattr(args, "max_happiness", None) is not None:
            plan = engine.get_feed_threshold_plan(max_happiness=args.max_happiness, qty=args.qty)
        else:
            plan = engine.get_feed_plan(target=args.target, qty=args.qty)
        if not plan.get("ok"):
            print(f"❌ {plan.get('error', 'Could not feed Pokémon.')}")
        else:
            if getattr(args, "yes", False):
                ok, msg = engine.execute_feed_plan(plan)
                print(msg)
            else:
                prompt_text = plan.get("prompt", "")
                print(prompt_text)
                try:
                    resp = input("Proceed? [y/N]: ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    print("\nFeeding cancelled.")
                    return
                if resp in ["y", "yes", "confirm"]:
                    ok, msg = engine.execute_feed_plan(plan)
                    print(msg)
                else:
                    print("Feeding cancelled.")
    elif args.command == "dex":
        tui = PokeTokenBarTUI()
        tui.render_pokedex_tab()
    elif args.command == "shop":
        tui = PokeTokenBarTUI()
        tui.render_shop_tab()
    elif args.command == "settings":
        cmd_settings(engine, args, tracker=tracker)
    else:
        # Default: Launch full interactive TUI
        tui = PokeTokenBarTUI()
        tui.run()

if __name__ == "__main__":
    main()
