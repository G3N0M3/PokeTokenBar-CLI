import sys
from poketokenbar.utils.formatting import format_tokens

HEADER = "\033[95m\033[1m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def render_quests_tab(app):
    qdata = app.engine.state.get("daily_quests", {})
    quests = qdata.get("quests", [])
    badges = app.engine.state.get("gym_badges", [])
    achievements = app.engine.state.get("achievements", [])

    sys.stdout.write(f"\n  {BOLD}{HEADER}🏆 Quests, Badges & Achievements{RESET}\n\n")

    # 1. Daily Quests
    sys.stdout.write(f"  {BOLD}🎯 Quests (Type 'claim <id>'):{RESET}\n")
    if not quests:
        sys.stdout.write("   No daily quests active today. Spend tokens to refresh!\n")
    else:
        for q in quests:
            q_id = q["id"]
            txt = q["text"]
            prog = q["progress"]
            target = q["target"]
            claimed = q["claimed"]
            if claimed:
                status = f"{BOLD}{GREEN}[CLAIMED]{RESET}"
            elif prog >= target:
                status = f"{BOLD}{YELLOW}[READY - TYPE 'claim {q_id}']{RESET}"
            else:
                status = f"({format_tokens(prog)} / {format_tokens(target)})"
            sys.stdout.write(f"   [{q_id}] {txt:<38} {status}\n")

    # 2. Gym Badges Collected
    sys.stdout.write(f"\n  {BOLD}🏅 Gym Badges Collected ({len(badges)}):{RESET}\n")
    if not badges:
        sys.stdout.write("   No badges earned yet. Defeat Gym Bosses to earn badges!\n")
    else:
        for i in range(0, len(badges), 3):
            chunk = badges[i:i+3]
            sys.stdout.write("   " + "   ".join([f"{BOLD}{YELLOW}{b}{RESET}" for b in chunk]) + "\n")

    # 3. Achievements Unlocked
    sys.stdout.write(f"\n  {BOLD}🎖️ Achievements ({len(achievements)} Unlocked):{RESET}\n")
    all_achievements = [
        ("shiny_hunter", "🌟 Shiny Hunter", "Hatch a rare Shiny Pokémon"),
        ("token_tycoon", "💎 Token Tycoon", "Burn 100M+ lifetime tokens"),
        ("dex_collector", "📖 Dex Collector", "Register 5+ species in Pokédex"),
        ("gym_champion", "🏆 Gym Champion", "Defeat your first Gym Boss Raid"),
        ("streak_master", "⚡ Streak Master", "Maintain a 3+ day coding streak")
    ]
    unlocked_set = set(achievements)
    for code, title, desc in all_achievements:
        if code in unlocked_set:
            badge = f"{BOLD}{GREEN}[UNLOCKED]{RESET}"
            sys.stdout.write(f"   • {BOLD}{title:<18}{RESET} - {desc:<36} {badge}\n")
        else:
            badge = f"{BOLD}{YELLOW}[LOCKED]{RESET}"
            sys.stdout.write(f"   • {title:<18} - {desc:<36} {badge}\n")
    sys.stdout.write("\n")
