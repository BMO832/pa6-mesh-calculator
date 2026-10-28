import math
import unittest
from dataclasses import replace
from aquaculture.model import Design, evaluate, ROTATED, band_coverage


class GeometryTests(unittest.TestCase):
    def test_original_reference_and_no_fixed_burial(self):
        r = evaluate(Design())
        self.assertEqual(r['전체 제작 실 길이 (m)'], 2510)
        self.assertAlmostEqual(r['부착 가능 표면적 (m²)'], math.pi * .002 * 2510)
        self.assertAlmostEqual(r['빈 그물 가림률 (%)'], 19)
        self.assertAlmostEqual(r['수면 투영 차광면적 (m²)'], 4.75)

    def test_contact_and_growth_are_distinct(self):
        r = evaluate(Design(inaccessible_pct=25, cultivation_pct=50, light_usable_pct=40, biofilm_mm=.5))
        total = math.pi * .002 * 2510
        self.assertAlmostEqual(r['부착 가능 표면적 (m²)'], total * .75)
        self.assertAlmostEqual(r['광 이용 가능 표면적 가정 (m²)'], total * .75 * .5 * .4)
        self.assertGreater(r['생물막 포함 가림률 (%)'], r['빈 그물 가림률 (%)'])
        self.assertAlmostEqual(r['전개 구간 실 표면적 (m²)'], total)

    def test_retrieval_zero_and_partial_deployment(self):
        empty = evaluate(Design(deployment_pct=0))
        self.assertEqual(empty['수면 투영 차광면적 (m²)'], 0)
        self.assertEqual(empty['부착 가능 표면적 (m²)'], 0)
        self.assertEqual(empty['전체 제작 실 길이 (m)'], 2510)
        half = evaluate(Design(deployment_pct=50))
        self.assertAlmostEqual(half['수면 전체 기준 가림률 (%)'], 9.5)

    def test_finite_boundary_clipping(self):
        self.assertAlmostEqual(band_coverage(.025, .02, .002, 2), .003)
        # One boundary filament only, half its diameter lies in a tiny rectangle.
        r = evaluate(Design(length_m=.005, width_m=.005))
        self.assertAlmostEqual(r['빈 그물 가림률 (%)'], 36)

    def test_rotated_and_closed_pores(self):
        r = evaluate(Design(structure=ROTATED))
        self.assertAlmostEqual(r['빈 그물 가림률 (%)'], 19)
        self.assertGreater(r['부착 가능 표면적 (m²)'], 0)
        closed = evaluate(Design(biofilm_mm=9))
        self.assertAlmostEqual(closed['기하학적 개구율 (%)'], 0)

    def test_invalid_inputs(self):
        for d in [Design(diameter_mm=20), Design(spacing_mm=0), Design(length_m=float('nan')),
                  Design(deployment_pct=101), Design(biofilm_mm=-1), Design(structure='unknown')]:
            with self.assertRaises(ValueError):
                evaluate(d)


if __name__ == '__main__':
    unittest.main()
