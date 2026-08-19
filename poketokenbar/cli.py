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
    events = engine.process_usage(summary["total_tokens"])

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
        print(f"🐾 {shiny}{name} (#{active.current_id}) [{stage}] | Today: {today_tok} tokens | Burn: {format_tokens(summary['burn_rate_tpm'])} tpm")

def cmd_watch(tracker: UsageManager, engine: CompanionEngine, interval: float = 3.0):
    """Continuous live token monitoring mode."""
    print("📡 PokeTokenBar Live Monitor active. Press Ctrl+C to stop.")
    try:
        while True:
            summary = tracker.get_summary()
            events = engine.process_usage(summary["total_tokens"])
            
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
                    ansi = SpriteRenderer.render_png_to_ansi(sprite_path, max_cols=20)
                    print("\n" + ansi + "\n")
            else:
                print(" Companion: 🥚 Incubating Egg...")

            print(f" Today's Tokens:   {format_tokens(summary['today_tokens'])} (Antigravity: {format_tokens(summary['antigravity_today'])})")
            print(f" Total Tokens:     {format_tokens(summary['total_tokens'])}")
            print(f" Active Burn Rate: {format_tokens(summary['burn_rate_tpm'])} tokens/min")

            if events:
                print("\n Recent Events:")
                for ev in events:
                    print(f"  ➔ {ev}")

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitor stopped.")

def cmd_settings(engine: CompanionEngine, args):
    if args.auto_track is not None:
        val = (args.auto_track.lower() in ["on", "true", "1", "yes"])
        engine.update_settings(auto_tracking_enabled=val)
        print(f"Automatic tracking set to: {'ON' if val else 'OFF'}")
    if args.interval is not None:
        ok, msg = engine.update_settings(refresh_interval=args.interval)
        print(msg)

    s = engine.get_settings()
    print("\n⚙️ Current PokeTokenBar Settings:")
    print(f"  • Automatic Tracking: {'ON' if s['auto_tracking_enabled'] else 'OFF'}")
    print(f"  • Refresh Interval:   {s['refresh_interval']} seconds\n")

def main():
    parser = argparse.ArgumentParser(prog="ptb", description="PokeTokenBar CLI - AI Token Pokémon Companion for Linux CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="Print compact 1-line status banner (useful for prompt/tmux)")
    watch_parser = subparsers.add_parser("watch", help="Continuous live token tracking monitor")
    watch_parser.add_argument("--interval", "-i", type=float, default=3.0, help="Refresh interval in seconds")
    
    subparsers.add_parser("dex", help="View Pokédex catch history")
    subparsers.add_parser("shop", help="View Shop & available spendable tokens")
    subparsers.add_parser("card", help="Print shareable ASCII Trainer Profile Card")

    settings_parser = subparsers.add_parser("settings", help="View or update tracking settings")
    settings_parser.add_argument("--auto-track", choices=["on", "off"], help="Toggle automatic tracking system ON or OFF")
    settings_parser.add_argument("--interval", "-i", type=float, help="Configure update interval in seconds")

    args = parser.parse_args()
    tracker = UsageManager()
    engine = CompanionEngine()

    if args.command == "status":
        cmd_status(tracker, engine)
    elif args.command == "watch":
        cmd_watch(tracker, engine, args.interval)
    elif args.command == "card":
        print(engine.generate_trainer_card())
    elif args.command == "dex":
        tui = PokeTokenBarTUI()
        tui.render_pokedex_tab()
    elif args.command == "shop":
        tui = PokeTokenBarTUI()
        tui.render_shop_tab()
    elif args.command == "settings":
        cmd_settings(engine, args)
    else:
        # Default: Launch full interactive TUI
        tui = PokeTokenBarTUI()
        tui.run()

if __name__ == "__main__":
    main()
