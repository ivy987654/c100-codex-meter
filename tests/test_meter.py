import json
import tempfile
import unittest
from pathlib import Path
import c100_codex_meter as meter

class MeterTests(unittest.TestCase):
    def test_percent_clamping(self):
        for used,remaining in [(-5,100),(0,100),(60,40),(100,0),(150,0)]:
            self.assertEqual(meter.remaining_from_usage(used),remaining)

    def test_all_percentages_have_exact_light_count(self):
        for remaining in range(101):
            with self.subTest(remaining=remaining):
                colors=meter.colors_for_remaining(remaining,(0,200,255),180)
                self.assertEqual(len(colors),100)
                self.assertEqual(sum(c[2]>0 for c in colors),remaining)

    def test_single_step_removes_one_light(self):
        previous=set(range(100))
        for remaining in range(99,-1,-1):
            now={i for i,c in enumerate(meter.colors_for_remaining(remaining,(0,200,255),180)) if c[2]}
            self.assertTrue(now<previous)
            self.assertEqual(len(previous-now),1)
            previous=now

    def test_mapping_is_bijective(self):
        self.assertEqual({meter.physical_to_driver_index(i) for i in range(100)},set(range(100)))
        self.assertEqual(meter.physical_to_driver_index(0),90)
        self.assertEqual(meter.physical_to_driver_index(99),9)

    def test_reads_only_five_hour_fixture(self):
        original=meter.SESSION_ROOT
        with tempfile.TemporaryDirectory() as directory:
            try:
                meter.SESSION_ROOT=Path(directory)
                events=[{'rate_limits':{'primary':{'window_minutes':60,'used_percent':20}}}, {'payload':{'rate_limits':{'primary':{'window_minutes':300,'used_percent':60,'resets_at':123456}}}}]
                (Path(directory)/'example.jsonl').write_text('\n'.join(map(json.dumps,events)))
                used,reset,_=meter.latest_five_hour_usage()
                self.assertEqual((used,reset),(60,123456))
            finally:meter.SESSION_ROOT=original

    def test_empty_fixture(self):
        original=meter.SESSION_ROOT
        with tempfile.TemporaryDirectory() as directory:
            try:
                meter.SESSION_ROOT=Path(directory)
                self.assertIsNone(meter.latest_five_hour_usage())
            finally:meter.SESSION_ROOT=original

if __name__=='__main__':unittest.main()
