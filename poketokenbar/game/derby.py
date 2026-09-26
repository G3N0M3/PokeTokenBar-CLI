import random
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from poketokenbar.utils.formatting import format_tokens


@dataclass
class DerbyRacer:
    lane: int
    name: str
    icon: str
    odds: float
    style: str
    position: int = 0
    stumbled: bool = False
    special_event: str = ""


class DerbyEngine:
    """Engine for Pokémon Stadium Derby 4-lane hurdle race betting."""

    TRACK_LENGTH = 36
    HURDLES = [12, 24]

    RACER_TEMPLATES = [
        (1, "Ponyta", "🐴", 2.0, "Steady 3-5 pace with rare hurdle stumbles."),
        (2, "Dodrio", "🐦", 3.5, "Fast 3-6 pace, but heads argue occasionally."),
        (3, "Jolteon", "⚡", 5.0, "High volatility with huge Agility bursts."),
        (4, "Slowpoke", "🐢", 20.0, "Mostly naps (0-2 pace), but 5% Teleport leap!"),
    ]

    def __init__(self):
        self.game_state: str = "idle"  # "idle", "bet_placed", "finished"
        self.bet_lane: int = 1
        self.bet_amount: int = 0
        self.racers: List[DerbyRacer] = []
        self.winner: Optional[DerbyRacer] = None
        self.winners: List[DerbyRacer] = []
        self.is_dead_heat: bool = False
        self.last_result: str = ""
        self.last_winnings: int = 0
        self.race_frames: List[Dict[str, Any]] = []
        self._reset_racers()

    def _reset_racers(self):
        self.racers = [
            DerbyRacer(
                lane=lane,
                name=name,
                icon=icon,
                odds=odds,
                style=style,
                position=0,
                stumbled=False,
                special_event="",
            )
            for lane, name, icon, odds, style in self.RACER_TEMPLATES
        ]
        self.winner = None
        self.winners = []
        self.is_dead_heat = False

    def place_bet(self, lane: int, amount: int) -> Tuple[bool, str]:
        if not (1 <= lane <= 4):
            return False, "Invalid lane! Choose a racer on Lane 1 to 4 (e.g. 'bet 1 500k')."

        if amount <= 0:
            return False, "Bet amount must be greater than 0!"

        self._reset_racers()
        self.race_frames = []
        self.bet_lane = lane
        self.bet_amount = amount
        self.game_state = "bet_placed"

        chosen = self.racers[lane - 1]
        return True, (
            f"🏇 Bet of {format_tokens(amount)} placed on Lane {lane}: {chosen.icon} {chosen.name} ({chosen.odds:.1f}x)!\n"
            f"  ➔ Type 'race' to drop the starting flag!"
        )

    def simulate_race(self) -> List[Dict[str, Any]]:
        """Simulates race turns and returns a list of frame states for rendering."""
        self._reset_racers()
        frames: List[Dict[str, Any]] = []

        # Record initial frame
        frames.append({
            "positions": {r.lane: r.position for r in self.racers},
            "events": ["🚩 GONG! The race has begun! Racers burst from the gates!"],
        })

        race_over = False
        turn = 0
        max_turns = 30

        while not race_over and turn < max_turns:
            turn += 1
            turn_events = []

            for r in self.racers:
                if r.position >= self.TRACK_LENGTH:
                    continue

                prev_pos = r.position
                step = 0
                event = ""

                if r.lane == 1:  # Ponyta
                    step = random.randint(3, 5)
                    if r.position in self.HURDLES and random.random() < 0.15:
                        step = max(1, step - 1)
                        event = f"{r.icon} Ponyta nicked a hurdle!"

                elif r.lane == 2:  # Dodrio
                    if random.random() < 0.15:
                        step = 0
                        event = f"{r.icon} Dodrio's heads started arguing! Paused!"
                    else:
                        step = random.randint(3, 6)
                        if r.position in self.HURDLES and random.random() < 0.20:
                            step = max(1, step - 2)
                            event = f"{r.icon} Dodrio stumbled over a hurdle!"

                elif r.lane == 3:  # Jolteon
                    if random.random() < 0.16:
                        step = random.randint(7, 9)
                        event = f"{r.icon} Jolteon used AGILITY! Rocket surge!"
                    else:
                        step = random.randint(2, 4)

                elif r.lane == 4:  # Slowpoke
                    if random.random() < 0.05:
                        step = random.randint(18, 22)
                        event = f"{r.icon} 🌀 SLOWPOKE USED TELEPORT! Quantum leap forward!"
                    elif random.random() < 0.50:
                        step = 0
                        event = f"{r.icon} Slowpoke is happily gazing at a cloud..."
                    else:
                        step = random.randint(1, 2)

                r.position = min(self.TRACK_LENGTH, prev_pos + step)
                if event:
                    turn_events.append(event)

            # Check if any racer reached the finish line
            finishers = [r for r in self.racers if r.position >= self.TRACK_LENGTH]
            if finishers:
                race_over = True
                max_pos = max(r.position for r in finishers)
                top_finishers = [r for r in finishers if r.position == max_pos]
                self.winners = top_finishers
                self.winner = top_finishers[0]
                self.is_dead_heat = len(top_finishers) > 1

                if self.is_dead_heat:
                    names_str = " & ".join(f"{w.icon} {w.name}" for w in top_finishers)
                    turn_events.append(f"📸 DEAD HEAT! {names_str} tie at the finish line!")

            # Record turn frame
            frames.append({
                "positions": {r.lane: r.position for r in self.racers},
                "events": turn_events if turn_events else ["💨 Racers thunder down the homestretch!"],
            })

        self.race_frames = frames
        return frames

    def resolve_race(self) -> Tuple[bool, str, int]:
        if self.game_state != "bet_placed":
            return False, "No active bet placed! Type 'bet <lane 1-4> <amount>'.", 0

        if not self.race_frames or not self.winners:
            self.simulate_race()
        self.game_state = "finished"

        winning_lanes = [w.lane for w in self.winners]
        won_bet = self.bet_lane in winning_lanes

        if self.is_dead_heat:
            winners_str = " & ".join(f"Lane {w.lane} [{w.icon} {w.name}]" for w in self.winners)
            if won_bet:
                chosen = next(w for w in self.winners if w.lane == self.bet_lane)
                self.last_winnings = int(self.bet_amount * chosen.odds)
                self.last_result = (
                    f"🏆 DEAD HEAT! {winners_str} tied for 1st Place!\n"
                    f"  Your pick [{chosen.icon} {chosen.name}] won! Payout: {chosen.odds:.1f}x! You won {format_tokens(self.last_winnings)} tokens!"
                )
                return True, self.last_result, self.last_winnings
            else:
                self.last_winnings = 0
                self.last_result = (
                    f"💀 DEAD HEAT! {winners_str} tied for 1st Place!\n"
                    f"  Your racer on Lane {self.bet_lane} lost. Surrendered {format_tokens(self.bet_amount)} tokens."
                )
                return True, self.last_result, 0
        else:
            winner = self.winner or self.racers[0]
            if won_bet:
                self.last_winnings = int(self.bet_amount * winner.odds)
                self.last_result = (
                    f"🏆 WINNER! Lane {winner.lane} [{winner.icon} {winner.name}] takes 1st Place!\n"
                    f"  Payout: {winner.odds:.1f}x! You won {format_tokens(self.last_winnings)} tokens!"
                )
                return True, self.last_result, self.last_winnings
            else:
                self.last_winnings = 0
                self.last_result = (
                    f"💀 Lane {winner.lane} [{winner.icon} {winner.name}] crossed the finish line first!\n"
                    f"  Your racer on Lane {self.bet_lane} lost. Surrendered {format_tokens(self.bet_amount)} tokens."
                )
                return True, self.last_result, 0
