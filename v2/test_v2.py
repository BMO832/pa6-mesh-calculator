import hashlib
import json
import math
from pathlib import Path
import unittest
from v2.leaching import calculate_leaching, release_rate
from v2 import mesh_engine as v2
import mesh_engine as v1

ROOT = Path(__file__).resolve().parent.parent


class V2Tests(unittest.TestCase):
    def test_v1_files_unchanged(self):
        for item in json.loads((ROOT / 'v2/v1_hashes.json').read_text(encoding='utf-8-sig')):
            self.assertEqual(hashlib.sha256((ROOT/item['Path']).read_bytes()).hexdigest().upper(), item['Hash'])

    def test_identical_engine_and_results(self):
        self.assertEqual((ROOT/'mesh_engine.py').read_bytes(), (ROOT/'v2/mesh_engine.py').read_bytes())
        for values in ((10, 1, 2, 20), (.3, .3, 2, 100), (2.3, .8, 2, 31)):
            for structure in v1.STRUCTURES:
                a = v1.calculate(v1.MeshInput(*values), structure)
                b = v2.calculate(v2.MeshInput(*values), structure)
                self.assertEqual(vars(a), vars(b))

    def test_mass_units_and_area_denominator(self):
        # d=2 mm, T=1000 m: volume=pi/1000 m³; mass=1.13*pi kg.
        p = calculate_leaching(2, 1000, 2*math.pi, 7)
        self.assertAlmostEqual(p.mass_kg, 1.13*math.pi)
        expected_rate = .653*(1-.771*math.exp(-2.849))
        self.assertAlmostEqual(p.rate_percent, expected_rate)
        self.assertAlmostEqual(p.total_mg, 1.13*math.pi*expected_rate*10000)
        self.assertAlmostEqual(p.per_area_mg_m2, 5650*expected_rate)
        double_length = calculate_leaching(2, 2000, 4*math.pi, 7)
        self.assertAlmostEqual(double_length.total_mg, 2*p.total_mg)
        self.assertAlmostEqual(double_length.per_area_mg_m2, p.per_area_mg_m2)

    def test_all_days_and_invalid_inputs(self):
        rates = [release_rate(t) for t in range(1,65)]
        self.assertTrue(all(0 < r < .653 for r in rates))
        self.assertTrue(all(a < b for a,b in zip(rates,rates[1:])))
        for t in range(1,65):
            self.assertTrue(math.isfinite(calculate_leaching(2,1011,6.352300345558562,t).total_mg))
        for t in (0,65,-1,math.inf,math.nan):
            with self.assertRaises(ValueError): release_rate(t)
        for value in (0,-1,math.inf,math.nan):
            for i in range(3):
                args = [2,1000,2*math.pi,7]
                args[i] = value
                with self.assertRaises(ValueError): calculate_leaching(*args)

    def test_ui_slider_preserves_geometry(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT/'v2/app.py'), default_timeout=20).run()
        app.button[0].click().run()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(len(app.metric),8)
        original = [m.value for m in app.metric[:4]]
        self.assertEqual(app.slider[0].value,7)
        for t in (1,64):
            app.slider[0].set_value(t).run()
            self.assertEqual(len(app.exception),0)
            self.assertEqual([m.value for m in app.metric[:4]],original)
        app.selectbox[0].select_index(1)
        app.button[0].click().run()
        self.assertEqual(app.metric[3].value,'3.1416 m²')
        app.number_input[3].set_value(1)
        app.button[0].click().run()
        self.assertEqual(len(app.error),1)
        self.assertEqual(len(app.metric),0)


if __name__ == '__main__': unittest.main()
