import sys

HEADER = "\033[95m\033[1m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def render_settings_tab(app):
    sys.stdout.write(f"\n  {BOLD}{CYAN}⚙️ Tracking & Application Settings{RESET}\n\n")
    
    current_size = app.engine.state.get("sprite_size", 30)
    sys.stdout.write(f"  [1] Sprite Resolution:         {BOLD}{current_size} columns{RESET}\n")
    sys.stdout.write(f"      ➔ Type '{BOLD}size <number>{RESET}' to adjust\n\n")

    pokedex_size = app.engine.state.get("page_size_pokedex", 15)
    roster_size = app.engine.state.get("page_size_roster", 14)
    expedition_size = app.engine.state.get("page_size_expedition", 10)

    sys.stdout.write(f"  [2] Pokédex Page Size:         {BOLD}{pokedex_size} items{RESET}\n")
    sys.stdout.write(f"      ➔ Type '{BOLD}pagesize dex <number>{RESET}' to adjust\n\n")

    sys.stdout.write(f"  [3] Roster Page Size:          {BOLD}{roster_size} items{RESET}\n")
    sys.stdout.write(f"      ➔ Type '{BOLD}pagesize roster <number>{RESET}' to adjust\n\n")

    sys.stdout.write(f"  [4] Expeditions Page Size:     {BOLD}{expedition_size} items{RESET}\n")
    sys.stdout.write(f"      ➔ Type '{BOLD}pagesize exp <number>{RESET}' to adjust\n\n")

    bag_size = app.engine.state.get("page_size_bag", 10)
    sys.stdout.write(f"  [5] Bag Page Size:             {BOLD}{bag_size} items{RESET}\n")
    sys.stdout.write(f"      ➔ Type '{BOLD}pagesize bag <number>{RESET}' to adjust\n\n")

    mega_size = app.engine.state.get("page_size_mega", 14)
    sys.stdout.write(f"  [6] Mega Evo Page Size:        {BOLD}{mega_size} items{RESET}\n")
    sys.stdout.write(f"      ➔ Type '{BOLD}pagesize mega <number>{RESET}' to adjust\n\n")

    sys.stdout.write(f"  [7] Reset Game Progress:       {BOLD}{RED}[DANGER]{RESET}\n")
    sys.stdout.write(f"      ➔ Type '{BOLD}reset{RESET}' to clear all progress & restart\n\n")
