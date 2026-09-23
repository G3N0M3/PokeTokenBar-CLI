import random
import re
from typing import Dict, List, Optional, Tuple, Any
from poketokenbar.utils.formatting import format_tokens

TRIVIA_POKEMON_ROSTER: List[Dict[str, Any]] = [
    {"id": 1, "name": "Bulbasaur", "types": ["Grass", "Poison"], "cat": "Seed Pokémon", "ht": "0.7 m", "wt": "6.9 kg", "dex": "A strange seed was planted on its back at birth. The plant sprouts and grows with this Pokémon."},
    {"id": 4, "name": "Charmander", "types": ["Fire"], "cat": "Lizard Pokémon", "ht": "0.6 m", "wt": "8.5 kg", "dex": "The flame that burns at the tip of its tail is an indication of its emotions and life force."},
    {"id": 7, "name": "Squirtle", "types": ["Water"], "cat": "Tiny Turtle Pokémon", "ht": "0.5 m", "wt": "9.0 kg", "dex": "After birth, its back swells and hardens into a shell. Powerfully sprays foam from its mouth."},
    {"id": 6, "name": "Charizard", "types": ["Fire", "Flying"], "cat": "Flame Pokémon", "ht": "1.7 m", "wt": "90.5 kg", "dex": "Spits fire that is hot enough to melt boulders. Known to cause forest fires unintentionally."},
    {"id": 9, "name": "Blastoise", "types": ["Water"], "cat": "Shellfish Pokémon", "ht": "1.6 m", "wt": "85.5 kg", "dex": "A brutal Pokémon with pressurized water jets on its shell. They are used for high-speed tackles."},
    {"id": 25, "name": "Pikachu", "types": ["Electric"], "cat": "Mouse Pokémon", "ht": "0.4 m", "wt": "6.0 kg", "dex": "When several of these Pokémon gather, their electricity could build and cause lightning storms."},
    {"id": 26, "name": "Raichu", "types": ["Electric"], "cat": "Mouse Pokémon", "ht": "0.8 m", "wt": "30.0 kg", "dex": "Its long tail serves as a ground to protect itself from its own high voltage power."},
    {"id": 39, "name": "Jigglypuff", "types": ["Normal", "Fairy"], "cat": "Balloon Pokémon", "ht": "0.5 m", "wt": "5.5 kg", "dex": "When its huge eyes light up, it sings a mysteriously soothing melody that lulls its enemies to sleep."},
    {"id": 52, "name": "Meowth", "types": ["Normal"], "cat": "Scratch Cat Pokémon", "ht": "0.4 m", "wt": "4.2 kg", "dex": "Adores circular objects. It wanders the streets on a nightly basis to look for dropped coins."},
    {"id": 54, "name": "Psyduck", "types": ["Water"], "cat": "Duck Pokémon", "ht": "0.8 m", "wt": "19.6 kg", "dex": "While lulling its enemies with its vacant look, this wily Pokémon will use psychokinetic powers."},
    {"id": 59, "name": "Arcanine", "types": ["Fire"], "cat": "Legendary Pokémon", "ht": "1.9 m", "wt": "155.0 kg", "dex": "A Pokémon that has long been admired for its beauty. It runs gracefully as if on wings."},
    {"id": 65, "name": "Alakazam", "types": ["Psychic"], "cat": "Psi Pokémon", "ht": "1.5 m", "wt": "48.0 kg", "dex": "Its brain can outperform a super-computer. Its intelligence quotient is said to be 5,000."},
    {"id": 68, "name": "Machamp", "types": ["Fighting"], "cat": "Superpower Pokémon", "ht": "1.6 m", "wt": "130.0 kg", "dex": "Using its heavy-duty muscles, it throws powerful punches that can send the victim over the horizon."},
    {"id": 94, "name": "Gengar", "types": ["Ghost", "Poison"], "cat": "Shadow Pokémon", "ht": "1.5 m", "wt": "40.5 kg", "dex": "Under a full moon, this Pokémon likes to mimic the shadows of people and laugh at their fright."},
    {"id": 95, "name": "Onix", "types": ["Rock", "Ground"], "cat": "Rock Snake Pokémon", "ht": "8.8 m", "wt": "210.0 kg", "dex": "As it digs through the ground, it absorbs many hard objects. This is what makes its body so solid."},
    {"id": 104, "name": "Cubone", "types": ["Ground"], "cat": "Lonely Pokémon", "ht": "0.4 m", "wt": "6.5 kg", "dex": "Because it never removes its skull helmet, no one has ever seen this Pokémon's real face."},
    {"id": 129, "name": "Magikarp", "types": ["Water"], "cat": "Fish Pokémon", "ht": "0.9 m", "wt": "10.0 kg", "dex": "In the distant past, it was somewhat stronger than the horribly weak descendants that exist today."},
    {"id": 130, "name": "Gyarados", "types": ["Water", "Flying"], "cat": "Atrocious Pokémon", "ht": "6.5 m", "wt": "235.0 kg", "dex": "Rarely seen in the wild. Huge and vicious, it is capable of destroying entire cities in a rage."},
    {"id": 131, "name": "Lapras", "types": ["Water", "Ice"], "cat": "Transport Pokémon", "ht": "2.5 m", "wt": "220.0 kg", "dex": "A Pokémon that has been overhunted almost to extinction. It can ferry people across the water."},
    {"id": 132, "name": "Ditto", "types": ["Normal"], "cat": "Transform Pokémon", "ht": "0.3 m", "wt": "4.0 kg", "dex": "Capable of copying an enemy's genetic code to instantly transform itself into a duplicate of the enemy."},
    {"id": 133, "name": "Eevee", "types": ["Normal"], "cat": "Evolution Pokémon", "ht": "0.3 m", "wt": "6.5 kg", "dex": "Its genetic code is irregular. It may mutate if it is exposed to radiation from element stones."},
    {"id": 134, "name": "Vaporeon", "types": ["Water"], "cat": "Bubble Jet Pokémon", "ht": "1.0 m", "wt": "29.0 kg", "dex": "Lives close to water. Its long tail is ridged with a fin which is often mistaken for a mermaid's."},
    {"id": 135, "name": "Jolteon", "types": ["Electric"], "cat": "Lightning Pokémon", "ht": "0.8 m", "wt": "24.5 kg", "dex": "It accumulates negative ions in the atmosphere to blast out 10,000-volt lightning bolts."},
    {"id": 136, "name": "Flareon", "types": ["Fire"], "cat": "Flame Pokémon", "ht": "0.9 m", "wt": "25.0 kg", "dex": "When storing thermal energy in its body, its temperature could soar to over 1,600 degrees Fahrenheit."},
    {"id": 143, "name": "Snorlax", "types": ["Normal"], "cat": "Sleeping Pokémon", "ht": "2.1 m", "wt": "460.0 kg", "dex": "Very lazy. Just eats and sleeps. As its enormous body is not easily moved, it is difficult to wake."},
    {"id": 144, "name": "Articuno", "types": ["Ice", "Flying"], "cat": "Freeze Pokémon", "ht": "1.7 m", "wt": "55.4 kg", "dex": "A legendary bird Pokémon that is said to appear to doomed people who are lost in icy mountains."},
    {"id": 145, "name": "Zapdos", "types": ["Electric", "Flying"], "cat": "Electric Pokémon", "ht": "1.6 m", "wt": "52.6 kg", "dex": "A legendary bird Pokémon that is said to appear from clouds while dropping enormous lightning bolts."},
    {"id": 146, "name": "Moltres", "types": ["Fire", "Flying"], "cat": "Flame Pokémon", "ht": "2.0 m", "wt": "60.0 kg", "dex": "Known as the legendary bird of fire. Every flap of its wings creates a dazzling flash of flames."},
    {"id": 149, "name": "Dragonite", "types": ["Dragon", "Flying"], "cat": "Dragon Pokémon", "ht": "2.2 m", "wt": "210.0 kg", "dex": "An extremely rarely seen marine Pokémon. Its intelligence is said to match that of humans."},
    {"id": 150, "name": "Mewtwo", "types": ["Psychic"], "cat": "Genetic Pokémon", "ht": "2.0 m", "wt": "122.0 kg", "dex": "It was created by a scientist after years of horrific gene splicing and DNA engineering experiments."},
    {"id": 151, "name": "Mew", "types": ["Psychic"], "cat": "New Species Pokémon", "ht": "0.4 m", "wt": "4.0 kg", "dex": "So rare that it is still said to be a mirage by many experts. Only a few people have seen it worldwide."},
    {"id": 152, "name": "Chikorita", "types": ["Grass"], "cat": "Leaf Pokémon", "ht": "0.9 m", "wt": "6.4 kg", "dex": "A sweet aroma gently wafts from the leaf on its head. It is docile and loves to soak up the sun."},
    {"id": 155, "name": "Cyndaquil", "types": ["Fire"], "cat": "Fire Mouse Pokémon", "ht": "0.5 m", "wt": "7.9 kg", "dex": "It is timid, and always curls itself up into a ball. If attacked, it flares up its back for protection."},
    {"id": 158, "name": "Totodile", "types": ["Water"], "cat": "Big Jaw Pokémon", "ht": "0.6 m", "wt": "9.5 kg", "dex": "It has the habit of biting anything with its developed jaws. Even its Trainer needs to be careful."},
    {"id": 175, "name": "Togepi", "types": ["Fairy"], "cat": "Spike Ball Pokémon", "ht": "0.3 m", "wt": "1.5 kg", "dex": "The shell seems to be filled with joy. It is said that it will share good luck when treated kindly."},
    {"id": 196, "name": "Espeon", "types": ["Psychic"], "cat": "Sun Pokémon", "ht": "0.9 m", "wt": "26.5 kg", "dex": "It uses the fine hair that covers its body to sense air currents and predict its enemy's actions."},
    {"id": 197, "name": "Umbreon", "types": ["Dark"], "cat": "Moonlight Pokémon", "ht": "1.0 m", "wt": "27.0 kg", "dex": "When exposed to the moon's aura, the rings on its body glow faintly and it gains a mysterious power."},
    {"id": 212, "name": "Scizor", "types": ["Bug", "Steel"], "cat": "Pincer Pokémon", "ht": "1.8 m", "wt": "118.0 kg", "dex": "It swings its eye-patterned pincers up and down to intimidate its foe. They can crush any hard object."},
    {"id": 249, "name": "Lugia", "types": ["Psychic", "Flying"], "cat": "Diving Pokémon", "ht": "5.2 m", "wt": "216.0 kg", "dex": "It is said to be the guardian of the seas. It is rumored to be seen on the night of a storm."},
    {"id": 250, "name": "Ho-Oh", "types": ["Fire", "Flying"], "cat": "Rainbow Pokémon", "ht": "3.8 m", "wt": "199.0 kg", "dex": "Legends claim that this Pokémon flies the world's skies continuously on its magnificent seven-colored wings."},
]


class TriviaEngine:
    """Engine for 'Who's That Pokémon?' silhouette trivia game."""

    def __init__(self):
        self.game_state: str = "idle"  # "idle", "guessing", "won", "lost", "given_up"
        self.current_target: Optional[Dict[str, Any]] = None
        self.current_bet: int = 0
        self.hints_used: int = 0
        self.current_multiplier: float = 5.0
        self.guesses_left: int = 3
        self.streak: int = 0
        self.last_result: str = ""
        self.last_winnings: int = 0

    def start_game(self, bet: int) -> Tuple[bool, str]:
        if self.game_state == "guessing":
            return False, "You already have a quiz round active! Type 'guess <name>', 'hint', or 'giveup'."

        # Avoid picking exact same target consecutively if possible
        pool = [p for p in TRIVIA_POKEMON_ROSTER if not self.current_target or p["id"] != self.current_target["id"]]
        self.current_target = random.choice(pool)

        self.current_bet = max(100_000, bet)
        self.hints_used = 0
        self.current_multiplier = 5.0
        self.guesses_left = 3
        self.last_winnings = 0
        self.last_result = ""
        self.game_state = "guessing"

        types_str = " / ".join(self.current_target["types"])
        return True, (
            f"❓ WHO'S THAT POKÉMON?! Bet {format_tokens(self.current_bet)} tokens!\n"
            f"  Type: {types_str} | Base Multiplier: {self.current_multiplier:.1f}x\n"
            f"  ➔ Type 'guess <name>' to answer, or 'hint' for a clue!"
        )

    def guess(self, name_str: str) -> Tuple[bool, str, int]:
        if self.game_state != "guessing" or not self.current_target:
            return False, "No active trivia round! Type 'bet <amount>' to start.", 0

        clean_guess = re.sub(r"[^a-z0-9]", "", name_str.lower().strip())
        target_name = self.current_target["name"]
        clean_target = re.sub(r"[^a-z0-9]", "", target_name.lower().strip())

        if clean_guess == clean_target:
            # Correct answer!
            self.game_state = "won"
            self.streak += 1
            mult = self.current_multiplier
            if self.streak >= 3:
                mult += 0.5 * (self.streak - 2)

            self.last_winnings = int(self.current_bet * mult)
            streak_str = f" 🔥 Streak: {self.streak}!" if self.streak >= 2 else ""
            self.last_result = (
                f"🎉 IT'S {target_name.upper()}! CORRECT!{streak_str}\n"
                f"  Payout: {mult:.1f}x! You won {format_tokens(self.last_winnings)} tokens!"
            )
            return True, self.last_result, self.last_winnings

        # Incorrect answer
        self.guesses_left -= 1
        if self.guesses_left <= 0:
            self.game_state = "lost"
            self.streak = 0
            self.last_winnings = 0
            self.last_result = (
                f"❌ Out of guesses! It was {target_name.upper()}!\n"
                f"  You lost {format_tokens(self.current_bet)} tokens. Streak reset."
            )
            return True, self.last_result, 0

        return False, f"❌ Not {name_str.strip().title()}! {self.guesses_left} guesses remaining.", 0

    def request_hint(self) -> Tuple[bool, str]:
        if self.game_state != "guessing" or not self.current_target:
            return False, "No active round to get a hint for."

        if self.hints_used >= 3:
            return False, "All hints have already been revealed!"

        self.hints_used += 1
        target = self.current_target

        if self.hints_used == 1:
            self.current_multiplier = 3.5
            return True, f"💡 Hint 1: {target['cat']} (Height: {target['ht']}, Weight: {target['wt']}) [Multiplier: 3.5x]"
        elif self.hints_used == 2:
            self.current_multiplier = 2.0
            first_l = target["name"][0]
            length = len(target["name"])
            return True, f"💡 Hint 2: Name starts with '{first_l}' ({length} letters total) [Multiplier: 2.0x]"
        else:
            self.current_multiplier = 1.2
            # Redact name in dex
            dex_redacted = re.sub(re.escape(target["name"]), "______", target["dex"], flags=re.IGNORECASE)
            return True, f"💡 Hint 3: Pokédex: \"{dex_redacted}\" [Multiplier: 1.2x]"

    def give_up(self) -> Tuple[bool, str]:
        if self.game_state != "guessing" or not self.current_target:
            return False, "No active round to give up on."

        target_name = self.current_target["name"]
        self.game_state = "given_up"
        self.streak = 0
        self.last_winnings = 0
        self.last_result = f"🏳️ Gave up! It was {target_name.upper()}! Lost {format_tokens(self.current_bet)} tokens."
        return True, self.last_result
