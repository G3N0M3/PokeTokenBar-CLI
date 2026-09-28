import unittest
import datetime
from poketokenbar.tracker.antigravity import AntigravityProtoDecoder, parse_generation_metadata
from poketokenbar.game.models import Rarity, PokemonBalance

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

    def test_pb_file_parsing(self):
        from poketokenbar.tracker.antigravity import AntigravityUsageReader
        reader = AntigravityUsageReader()
        entries = reader.get_entries()
        self.assertIsInstance(entries, list)

    def test_parse_generation_metadata_explicit_dt(self):
        # Construct a simple proto blob with total tokens = 500 (field 4 -> field 1 = 500)
        blob = bytes([0x22, 0x03, 0x08, 0xF4, 0x03])
        dt = datetime.datetime(2026, 9, 15, 12, 0, 0, tzinfo=datetime.timezone.utc)
        entry = parse_generation_metadata(blob, "conv_test", 1, explicit_dt=dt)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.date, dt)
        self.assertEqual(entry.local_day, "2026-09-15")
        self.assertEqual(entry.total_tokens, 500)

if __name__ == "__main__":
    unittest.main()
