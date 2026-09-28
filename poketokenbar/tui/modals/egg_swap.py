"""Egg swap decision dialog when a new egg is found while holding one."""

import sys
import time
from poketokenbar.utils.formatting import format_tokens

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def check_and_render_egg_swap(app) -> bool:
    """Checks for pending eggs and handles incubator assignment or swap decision.
    
    Returns True if an egg prompt or auto-assignment was processed (and loop should continue).
    """
    pending_eggs = app.engine.state.get("pending_eggs", [])
    if not pending_eggs:
        return False

    new_egg = pending_eggs[0]
    curr_egg = app.engine.state.get("egg_tier")
    if curr_egg is None:
        # User has an open slot, auto-assign the egg
        app.engine.state["egg_tier"] = new_egg
        app.engine.state["egg_usage"] = 0
        app.engine.state["pending_eggs"] = pending_eggs[1:]
        app.engine.save()
        sys.stdout.write(f"\n  {GREEN}You found a {new_egg.capitalize()} Egg! It is now incubating.{RESET}\n")
        return True

    app.clear_screen()
    sys.stdout.write(f"\n  {BOLD}{YELLOW}🥚 EGG DECISION!{RESET}\n\n")
    sys.stdout.write(f"  You found a {BOLD}{new_egg.capitalize()}{RESET} Egg, but you can only carry one egg at a time!\n")
    sys.stdout.write(f"  You are currently holding a {BOLD}{curr_egg.capitalize()}{RESET} Egg.\n\n")
    sys.stdout.write(f"  Do you want to SWAP your {curr_egg.capitalize()} Egg for the {new_egg.capitalize()} Egg? (y/n)> ")
    sys.stdout.flush()
    cmd = sys.stdin.readline().strip().lower()

    egg_payouts = {
        "common": 500_000,
        "uncommon": 1_000_000,
        "rare": 2_500_000,
        "epic": 5_000_000,
        "legendary": 10_000_000,
        "mysterious fetal form": 50_000_000,
        "normal": 500_000,
    }

    if cmd in ["y", "yes"]:
        payout = egg_payouts.get(curr_egg.lower(), 500_000)
        app.engine.state["spent_tokens"] = app.engine.state.get("spent_tokens", 0) - payout
        app.engine.state["egg_tier"] = new_egg
        app.engine.state["egg_usage"] = 0
        app.engine.state["pending_eggs"] = pending_eggs[1:]
        app.engine.save()
        sys.stdout.write(f"\n  {GREEN}Swapped! You are now holding a {new_egg.capitalize()} Egg!{RESET}\n")
        sys.stdout.write(f"  {YELLOW}The discarded {curr_egg.capitalize()} Egg was sold for {format_tokens(payout)} tokens!{RESET}\n")
        time.sleep(2)
    elif cmd in ["n", "no"]:
        payout = egg_payouts.get(new_egg.lower(), 500_000)
        app.engine.state["spent_tokens"] = app.engine.state.get("spent_tokens", 0) - payout
        app.engine.state["pending_eggs"] = pending_eggs[1:]
        app.engine.save()
        sys.stdout.write(f"\n  {YELLOW}Discarded the {new_egg.capitalize()} Egg and sold it for {format_tokens(payout)} tokens!{RESET}\n")
        time.sleep(2)
    else:
        sys.stdout.write(f"\n  {RED}Invalid choice. Please type 'y' or 'n'.{RESET}\n")
        time.sleep(1)

    return True
