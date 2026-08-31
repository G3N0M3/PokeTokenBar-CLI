import sys
from poketokenbar.utils.formatting import format_tokens, format_progress_bar

HEADER = "\033[95m\033[1m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def render_battles_tab(app):
    boss = app.engine.state.get("active_boss")
    battles = app.engine.state.get("trainer_battles", {"wins": 0, "losses": 0})
    logs = app.engine.state.get("battle_logs", [])

    sys.stdout.write(f"\n  {BOLD}{HEADER}⚔️ Gym Boss Raids & Trainer Auto-Battles{RESET}\n\n")

    # 1. Active Gym Boss Raid
    sys.stdout.write(f"  {BOLD}⚔️ Active Gym Boss Raid:{RESET}\n")
    if boss:
        b_name = boss["name"]
        b_sp_id = boss["sp_id"]
        hp_cur = boss["current_hp"]
        hp_tot = boss["total_hp"]
        badge = boss["badge"]
        bar = format_progress_bar(hp_cur, hp_tot)
        sys.stdout.write(f"   Boss: {BOLD}{RED}{b_name} (#{b_sp_id}){RESET} - Reward: {badge}\n")
        sys.stdout.write(f"   Boss HP: {bar} ({format_tokens(hp_cur)} / {format_tokens(hp_tot)})\n")
        active = app.engine.active_mon
        if active and active.is_mega:
            sys.stdout.write(f"   ➔ {GREEN}✨ MEGA BONUS: 2x Damage & 1.5x Token Rewards!{RESET} Spend tokens to attack!\n\n")
        else:
            sys.stdout.write("   ➔ Attack the boss by spending tokens in Antigravity CLI!\n\n")
    else:
        badges = app.engine.state.get("gym_badges", [])
        if "🏆 Champion Badge" in badges:
            sys.stdout.write(f"   {BOLD}{RED}A chilling wind blows from the peak of Mt. Silver...{RESET}\n")
            sys.stdout.write(f"   {BOLD}{RED}Someone is waiting for you in Tab [12].{RESET}\n\n")
        else:
            sys.stdout.write("   No active Boss Raid. Reach daily token milestones to summon Gym Bosses!\n\n")

    # 2. Mini-Trainer Auto-Battle Record
    sys.stdout.write(f"  {BOLD}⚔️ Mini-Trainer Auto-Battle Record:{RESET}\n")
    sys.stdout.write(f"   Wins: {BOLD}{GREEN}{battles.get('wins', 0)}{RESET}  |  Losses: {BOLD}{RED}{battles.get('losses', 0)}{RESET} (Triggers auto-battles every 2.0M tokens!)\n\n")

    # 3. Recent Auto-Battle Logs (Last 5 Fights)
    sys.stdout.write(f"  {BOLD}📜 Recent Auto-Battle Logs (Last 5 Fights):{RESET}\n")
    if not logs:
        sys.stdout.write("   No recent auto-battles recorded yet. Keep coding to trigger fights!\n\n")
    else:
        for log in logs:
            sys.stdout.write(f"   {log}\n")
        sys.stdout.write("\n")
