import random
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from poketokenbar.utils.formatting import format_tokens


@dataclass
class ExcavatorTreasure:
    name: str
    kind: str  # "token", "item", "fossil", "barrier"
    key: str  # item key or description
    symbol: str
    coords: List[Tuple[int, int]]  # (row, col) 0-indexed
    uncovered: bool = False
    reward_val: int = 0


class ExcavatorEngine:
    """Engine for Underground Fossil Excavation minigame (Sinnoh Mining Wall)."""

    ROWS = 6
    COLS = 9
    MAX_INTEGRITY = 25

    def __init__(self):
        self.game_state: str = "idle"  # "idle", "digging", "collapsed", "cleared"
        self.entry_cost: int = 500_000
        self.integrity: int = self.MAX_INTEGRITY
        self.strata: List[List[int]] = [[0] * self.COLS for _ in range(self.ROWS)]
        self.treasures: List[ExcavatorTreasure] = []
        self.last_action_msg: str = ""
        self.recovered_rewards: List[Dict[str, Any]] = []

    def start_game(self, cost: int = 500_000) -> Tuple[bool, str]:
        if self.game_state == "digging":
            return False, "You already have an active excavation wall! Use 'pick <r> <c>' or 'hammer <r> <c>'."

        self.entry_cost = max(100_000, cost)
        self.integrity = self.MAX_INTEGRITY
        self.recovered_rewards = []
        self.last_action_msg = ""

        # Initialize dirt strata (mostly depth 2 and 3)
        self.strata = [
            [random.choices([1, 2, 3], weights=[20, 50, 30])[0] for _ in range(self.COLS)]
            for _ in range(self.ROWS)
        ]

        self.treasures = []
        occupied: Dict[Tuple[int, int], str] = {}

        # Candidate item templates: (name, kind, key, symbol, width, height, reward_val)
        fossils = [
            ("Helix Fossil", "fossil", "helix_fossil", "🐚", 2, 2, 10_000_000),
            ("Dome Fossil", "fossil", "dome_fossil", "🛡️", 2, 2, 10_000_000),
            ("Old Amber", "fossil", "old_amber", "🏺", 3, 2, 25_000_000),
        ]
        items = [
            ("Moon Stone", "item", "moon_stone", "🌙", 2, 1, 0),
            ("Sun Stone", "item", "sun_stone", "☀️", 2, 1, 0),
            ("Water Stone", "item", "water_stone", "💧", 2, 1, 0),
            ("Fire Stone", "item", "fire_stone", "🔥", 2, 1, 0),
            ("Thunder Stone", "item", "thunder_stone", "⚡", 2, 1, 0),
            ("Rare Candy", "item", "rare_candy", "🍬", 2, 1, 0),
            ("Heart Scale", "token", "heart_scale", "💖", 1, 2, 2_000_000),
            ("Token Cache", "token", "token_cache", "💰", 2, 2, 5_000_000),
            ("Sphere Cache", "token", "sphere_cache", "🔮", 1, 1, 1_000_000),
        ]
        barrier = ("Iron Bar", "barrier", "iron", "■", 1, 3, 0)

        # Place 1 fossil
        selected_fossil = random.choice(fossils)
        self._place_treasure(selected_fossil, occupied)

        # Place 2-3 items
        random.shuffle(items)
        for it in items[:3]:
            self._place_treasure(it, occupied)

        # Place 1 iron barrier
        self._place_treasure(barrier, occupied)

        self.game_state = "digging"
        return True, (
            f"Underground excavation started! Wall Integrity: {self.integrity}/{self.MAX_INTEGRITY}. "
            f"Use 'pick <row 1-6> <col 1-9>' (1 hit) or 'hammer <row> <col>' (3 hits) to excavate!"
        )

    def _place_treasure(self, tmpl: tuple, occupied: Dict[Tuple[int, int], str]) -> bool:
        name, kind, key, symbol, w, h, val = tmpl
        if random.random() < 0.5:
            w, h = h, w  # random rotation

        max_r = self.ROWS - h
        max_c = self.COLS - w
        if max_r < 0 or max_c < 0:
            return False

        attempts = 30
        while attempts > 0:
            attempts -= 1
            r0 = random.randint(0, max_r)
            c0 = random.randint(0, max_c)

            coords = [(r0 + dr, c0 + dc) for dr in range(h) for dc in range(w)]
            if any((r, c) in occupied for r, c in coords):
                continue

            for r, c in coords:
                occupied[(r, c)] = key

            self.treasures.append(
                ExcavatorTreasure(
                    name=name,
                    kind=kind,
                    key=key,
                    symbol=symbol,
                    coords=coords,
                    uncovered=False,
                    reward_val=val,
                )
            )
            return True
        return False

    def pick(self, row: int, col: int) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """Use pickaxe on (row, col) (1-indexed). Costs 1 integrity, digs 1 layer."""
        if self.game_state != "digging":
            return False, "No active excavation wall! Type 'dig' to start.", []

        if not (1 <= row <= self.ROWS and 1 <= col <= self.COLS):
            return False, f"Coordinates must be Row 1-{self.ROWS}, Col 1-{self.COLS}.", []

        r, c = row - 1, col - 1
        self.integrity -= 1

        # Check if tile is an iron barrier
        is_barrier = any((r, c) in t.coords for t in self.treasures if t.kind == "barrier")
        if not is_barrier and self.strata[r][c] > 0:
            self.strata[r][c] -= 1

        msg = f"⛏️ Pickaxe chipped [{row}, {col}] (Remaining Integrity: {self.integrity}/{self.MAX_INTEGRITY})"
        return self._evaluate_turn(msg)

    def hammer(self, row: int, col: int) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """Use sledgehammer on (row, col) (1-indexed). Costs 3 integrity, digs 2 layers center, 1 adjacent."""
        if self.game_state != "digging":
            return False, "No active excavation wall! Type 'dig' to start.", []

        if not (1 <= row <= self.ROWS and 1 <= col <= self.COLS):
            return False, f"Coordinates must be Row 1-{self.ROWS}, Col 1-{self.COLS}.", []

        r, c = row - 1, col - 1
        self.integrity -= 3

        # Blast center by 2
        is_barrier = any((r, c) in t.coords for t in self.treasures if t.kind == "barrier")
        if not is_barrier:
            self.strata[r][c] = max(0, self.strata[r][c] - 2)

        # Blast orthogonal neighbors by 1
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.ROWS and 0 <= nc < self.COLS:
                nb_barrier = any((nr, nc) in t.coords for t in self.treasures if t.kind == "barrier")
                if not nb_barrier:
                    self.strata[nr][nc] = max(0, self.strata[nr][nc] - 1)

        msg = f"🔨 Sledgehammer struck [{row}, {col}]! Area blasted! (Integrity: {self.integrity}/{self.MAX_INTEGRITY})"
        return self._evaluate_turn(msg)

    def _evaluate_turn(self, action_msg: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
        newly_uncovered = []
        for t in self.treasures:
            if not t.uncovered and t.kind != "barrier":
                if all(self.strata[r][c] == 0 for r, c in t.coords):
                    t.uncovered = True
                    newly_uncovered.append(t)

        messages = [action_msg]
        for t in newly_uncovered:
            messages.append(f"✨ UNBURIED: {t.symbol} {t.name}!")

        # Check clean sweep (all non-barrier treasures uncovered)
        non_barriers = [t for t in self.treasures if t.kind != "barrier"]
        if all(t.uncovered for t in non_barriers):
            self.game_state = "cleared"
            messages.append(f"🏆 CLEAN EXCAVATION! All relics safely uncovered! +5,000,000 Token Master Bonus!")
            rewards = self._collect_rewards(bonus_tokens=5_000_000)
            return True, "\n  ".join(messages), rewards

        # Check collapse
        if self.integrity <= 0:
            self.game_state = "collapsed"
            messages.append("💥 RUMBLE! The ceiling cracked and the wall collapsed!")
            rewards = self._collect_rewards()
            if rewards:
                recovered_str = ", ".join(f"{r['name']}" for r in rewards)
                messages.append(f"📦 Successfully extracted before cave-in: {recovered_str}")
            else:
                messages.append("❌ No treasures were fully uncovered before the collapse.")
            return True, "\n  ".join(messages), rewards

        return True, "\n  ".join(messages), []

    def _collect_rewards(self, bonus_tokens: int = 0) -> List[Dict[str, Any]]:
        rewards = []
        if bonus_tokens > 0:
            rewards.append({"kind": "token", "name": "Clean Excavation Bonus", "key": "clean_bonus", "val": bonus_tokens})

        for t in self.treasures:
            if t.uncovered and t.kind != "barrier":
                rewards.append({"kind": t.kind, "name": t.name, "key": t.key, "val": t.reward_val})

        self.recovered_rewards = rewards
        return rewards

    def get_tile_display(self, r: int, c: int) -> Tuple[str, str]:
        """Returns (symbol, color_code) for rendering."""
        depth = self.strata[r][c]
        if depth == 3:
            return "▓", "\033[90m"  # Dark gray solid rock
        elif depth == 2:
            return "▒", "\033[33m"  # Brown/amber crumbly dirt
        elif depth == 1:
            return "░", "\033[37m"  # Light gray loose soil
        else:
            # Depth 0: completely cleared! Show what's underneath
            for t in self.treasures:
                if (r, c) in t.coords:
                    if t.kind == "barrier":
                        return "■", "\033[31m"  # Red iron bar
                    elif t.uncovered:
                        return t.symbol, "\033[92m"  # Green / bright icon
                    else:
                        return t.symbol, "\033[36m"  # Cyan exposed part
            return " ", "\033[0m"
