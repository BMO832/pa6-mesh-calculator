import csv
import hashlib
import io
import json
import math
from pathlib import Path
import unittest
from v3.sand import *
from v3.leaching import calculate_leaching
from v3.mesh_engine import MeshInput, calculate, SQUARE, STRUCTURES

ROOT = Path(__file__).resolve().parent.parent


class SandTests(unittest.TestCase):
    def test_reference_and_units(self):
        result = calculate_sand(1000, 10, 1500, 10)
        self.assertEqual(result.q_plan_mg_m2, 100)
        self.assertEqual(result.volume_m3, 1)
        self.assertEqual(result.mass_kg, 1500)
        self.assertAlmostEqual(result.concentration_mg_kg, .6666666666666666)
        # 1000 mg = 1 g: input is already mg; do not multiply it again.
        self.assertAlmostEqual(result.concentration_mg_kg * result.mass_kg, 1000)

    def test_scaling(self):
        c = calculate_sand(1000,10,1500,10).concentration_mg_kg
        self.assertEqual(calculate_sand(2000,10,1500,10).concentration_mg_kg, 2*c)
        self.assertEqual(calculate_sand(1000,10,1500,20).concentration_mg_kg, c/2)
        self.assertEqual(calculate_sand(2000,20,1500,10).concentration_mg_kg, c)
        self.assertEqual(calculate_sand(0,10,1500,10).concentration_mg_kg, 0)

    def test_invalid(self):
        for index in range(4):
            for bad in (-1, float('nan'), float('inf'), -float('inf')):
                args = [1000,10,1500,10]
                args[index] = bad
                with self.subTest(index=index,bad=bad), self.assertRaises(ValueError):
                    calculate_sand(*args)
        for index in (1,2,3):
            args = [1000,10,1500,10]; args[index]=0
            with self.assertRaises(ValueError): calculate_sand(*args)

    def test_rows_curve_csv_and_zero_log(self):
        table, curve = scenario_rows(1000,10,1500,14.4,.1)
        self.assertEqual(len([r for r in table if r[DEPTH]==14.4]),1)
        self.assertEqual(len(curve),132)
        self.assertTrue(all(r[DEPTH]>0 for r in curve))
        self.assertIn(.1,[r[DEPTH] for r in curve])
        graph = {r[DEPTH]:r for r in curve}
        exported = list(csv.DictReader(io.StringIO(csv_bytes(table,{'期間':7}).decode('utf-8-sig'))))
        for row, downloaded in zip(table,exported):
            if row[DEPTH] in graph:
                self.assertEqual(row[CONCENTRATION],graph[row[DEPTH]][CONCENTRATION])
            self.assertEqual(row[CONCENTRATION],calculate_sand(1000,10,1500,row[DEPTH]).concentration_mg_kg)
            self.assertEqual(row[CONCENTRATION],float(downloaded[CONCENTRATION]))
            self.assertEqual(downloaded['모델 설명'],MODEL)
        self.assertEqual(chart_spec(curve,True)['encoding']['y']['scale']['type'],'log')
        _, zero = scenario_rows(0,10,1500,10,1)
        self.assertEqual(chart_spec(zero,True)['encoding']['y']['scale']['type'],'linear')

    def test_old_versions_preserved_and_results_identical(self):
        saved = json.loads((ROOT/'v3/preserved_hashes.json').read_text(encoding='utf-8-sig'))
        for item in saved:
            self.assertEqual(hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest().upper(),item['hash'])
        for path in ('mesh_engine.py','leaching.py'):
            self.assertEqual((ROOT/'v2'/path).read_bytes(),(ROOT/'v3'/path).read_bytes())
        from v2 import mesh_engine as old
        from v2.leaching import calculate_leaching as old_leaching
        for structure in STRUCTURES:
            a = calculate(MeshInput(10,1,2,20),structure)
            b = old.calculate(old.MeshInput(10,1,2,20),structure)
            self.assertEqual(vars(a),vars(b))
            self.assertEqual(vars(calculate_leaching(2,a.filament_length_m,a.total_surface_m2,7)),
                             vars(old_leaching(2,b.filament_length_m,b.total_surface_m2,7)))

    def test_default_ui_and_download_data(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT/'v3/app.py'),default_timeout=25).run()
        app.button[0].click().run()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(app.metric[3].value,'3.1762 m²')
        self.assertEqual(app.metric[6].value,'22,390.2287 mg')
        data = app.dataframe[0].value
        geom = calculate(MeshInput(10,1,2,20),SQUARE)
        mass = calculate_leaching(2,geom.filament_length_m,geom.total_surface_m2,7).total_mg
        table,curve = scenario_rows(mass,10,1500,10,1)
        for i,row in enumerate(table):
            self.assertEqual(float(data.iloc[i][CONCENTRATION]),row[CONCENTRATION])
        self.assertEqual(len(app.get('download_button')),1)
        self.assertEqual(len(app.get('vega_lite_chart')),2)
        import pyarrow as pa
        chart_data = pa.ipc.open_stream(app.get('vega_lite_chart')[1].proto.data.data).read_all().to_pandas()
        self.assertEqual(float(chart_data.loc[chart_data.depth_cm==10,'concentration'].iloc[0]),
                         float(data.loc[data[DEPTH]==10,CONCENTRATION].iloc[0]))
        app.checkbox[0].check().run()
        self.assertEqual(len(app.exception),0)
        app.number_input[5].set_value(.1).run()
        self.assertEqual(len(app.exception),0)
        app.slider[0].set_value(64).run()
        self.assertEqual(len(app.exception),0)
        app.number_input[4].set_value(0).run()
        self.assertEqual(len(app.error),1)
        self.assertEqual(len(app.get('download_button')),0)


if __name__ == '__main__': unittest.main()
