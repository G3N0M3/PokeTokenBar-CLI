import unittest
import datetime
from poketokenbar.tracker.antigravity import AntigravityProtoDecoder, parse_generation_metadata
from poketokenbar.game.models import Rarity, PokemonBalance, MonState, PokemonNature

class TestAntigravityTracker(unittest.TestCase):

    def test_varint_decoding(self):
        # Varint representation of 300 (0xAC 0x02)
        buf = bytes([0xAC, 0x02])
        val, next_idx = AntigravityProtoDecoder.decode_varint(buf, 0)
        self.assertEqual(val, 300)
        self.assertEqual(next_idx, 2)

    def test_pokemon_balance(self):
        # Common graduation = 50M
        self.assertEqual(Rarity.COMMON.graduation_total_for(), 50_000_000)
        # 3 forms: form 1 = 50M * (1 / (3*4/2)) = 50M * (1/6) = 8,333,333
        phase1 = PokemonBalance.phase_threshold(Rarity.COMMON, 3, 0)
        self.assertEqual(phase1, 8_333_333)

if __name__ == "__main__":
    unittest.main()
