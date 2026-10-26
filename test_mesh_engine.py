import math
import unittest

from mesh_engine import MeshInput, SQUARE, ROTATED, calculate, clip_line, segments, square_counts


class GeometryTests(unittest.TestCase):
    def test_invalid_inputs(self):
        for value in (0, -1, math.inf, math.nan):
            for index in range(4):
                values = [10, 1, 2, 20]
                values[index] = value
                with self.subTest(index=index, value=value), self.assertRaises(ValueError):
                    MeshInput(*values)
        for spacing in (1, 2):
            with self.assertRaises(ValueError):
                MeshInput(10, 1, 2, spacing)

    def test_units_and_square_independent_value(self):
        data = MeshInput(10, 1, 2, 20)
        self.assertEqual(data.diameter_m, .002)
        self.assertEqual(data.spacing_m, .02)
        self.assertEqual(square_counts(data), (51, 501))
        result = calculate(data, SQUARE)
        self.assertEqual(result.planar_area_m2, 10)
        self.assertEqual(result.filament_length_m, 1011)
        self.assertAlmostEqual(result.total_surface_m2, 6.352300345558562)
        self.assertAlmostEqual(result.exposed_surface_m2, 3.176150172779281)

    def test_square_boundary_and_remainder(self):
        self.assertEqual(square_counts(MeshInput(.3, .3, 2, 100)), (4, 4))
        self.assertEqual(square_counts(MeshInput(.29, .29, 2, 100)), (3, 3))

    def test_clipping_diagonal(self):
        a = math.sqrt(.5)
        p, q = clip_line((-a, a), 0, 2, 1)
        self.assertAlmostEqual(math.dist(p, q), math.sqrt(2))
        self.assertEqual(set((p, q)), {(0, 0), (1, 1)})

    def test_clipping_parallel_boundary_outside_corner(self):
        self.assertEqual(clip_line((1, 0), 0, 2, 1), ((0, 0), (0, 1)))
        self.assertIsNone(clip_line((1, 0), 3, 2, 1))
        a = math.sqrt(.5)
        self.assertIsNone(clip_line((a, a), 0, 2, 1))

    def test_rotated_analytical_unit_square(self):
        # s=.5 m: +45° has lengths sqrt(2), sqrt(2)-1 (twice).
        # -45° has lengths 1, 2*sqrt(2)-2; origin touch has length 0.
        result = calculate(MeshInput(1, 1, 2, 500), ROTATED)
        self.assertAlmostEqual(result.filament_length_m, 5 * math.sqrt(2) - 3)

    def test_rotated_sparse_origin_anchor(self):
        result = calculate(MeshInput(2, 1, 2, 3000), ROTATED)
        self.assertAlmostEqual(result.filament_length_m, math.sqrt(2))

    def test_all_segments_inside_and_on_grid(self):
        data = MeshInput(2.3, .8, 2, 31)
        for p, q in segments(data, ROTATED):
            for x, y in (p, q):
                self.assertTrue(0 <= x <= data.length_m)
                self.assertTrue(0 <= y <= data.width_m)
                self.assertTrue(min(x, y, data.length_m-x, data.width_m-y) < 1e-12)
            x, y = p
            sign = -1 if (q[0]-x)*(q[1]-y) > 0 else 1
            k = (sign*x+y) / math.sqrt(2) / data.spacing_m
            self.assertAlmostEqual(k, round(k), places=10)

    def test_scale_invariance(self):
        for structure in (SQUARE, ROTATED):
            base = calculate(MeshInput(2, 1, 2, 30), structure)
            scaled = calculate(MeshInput(20, 10, 20, 300), structure)
            self.assertAlmostEqual(scaled.filament_length_m, base.filament_length_m * 10)
            self.assertAlmostEqual(scaled.total_surface_m2, base.total_surface_m2 * 100)

    def test_preview_does_not_change_calculation(self):
        data = MeshInput(2, 1, 2, 10)
        before = calculate(data, ROTATED)
        self.assertLessEqual(len(list(segments(data, ROTATED, 20))), 22)
        self.assertEqual(calculate(data, ROTATED), before)

    def test_resource_limit(self):
        with self.assertRaises(ValueError):
            calculate(MeshInput(100, 100, .01, .1), ROTATED)

    def test_unknown_structure(self):
        with self.assertRaises(ValueError):
            calculate(MeshInput(1, 1, 2, 20), "invalid")


if __name__ == "__main__":
    unittest.main()
