import csv
import hashlib
import io
import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch
from v4.model import CHEMICALS, HALF_LIVES, rate, history, build_model
from v4.mesh_engine import MeshInput, STRUCTURES
from v4.sand import calculate_sand, csv_bytes, DEPTH, CONCENTRATION

ROOT = Path(__file__).resolve().parent.parent


class ModelTests(unittest.TestCase):
    def test_preserved_versions_and_v3_equivalence(self):
        snapshot=json.loads((ROOT/'v4/preserved_hashes.json').read_text(encoding='utf-8-sig'))
        for item in snapshot:
            self.assertEqual(hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest().upper(),item['hash'],item['path'])
        from v3 import mesh_engine as old
        from v3.leaching import calculate_leaching
        from v3.sand import calculate_sand as old_sand
        for name in ('mesh_engine.py','leaching.py'):
            self.assertEqual((ROOT/'v3'/name).read_bytes(),(ROOT/'v4'/name).read_bytes())
        for structure in STRUCTURES:
            m=build_model(MeshInput(10,1,2,20),structure,['Caprolactam'],7,{'Caprolactam':None},1500,10,1,14.4,37.6)
            g=old.calculate(old.MeshInput(10,1,2,20),structure)
            self.assertEqual(vars(g),vars(m['geometry']))
            leach=calculate_leaching(2,g.filament_length_m,g.total_surface_m2,7)
            self.assertEqual(leach.mass_kg,m['mass_kg'])
            self.assertEqual(leach.total_mg,m['chemicals'][0]['current']['cumulative_mg'])
            self.assertEqual(vars(old_sand(leach.total_mg,10,1500,10)),vars(m['chemicals'][0]['layers']['selected']))

    def test_coefficients_and_daily_decay_all_64_days(self):
        expected=[(.653,.771,.407),(.065,.873,.051),(.374,.879,.050),(.526,.900,.042),(.221,.939,.026)]
        for chemical,values in zip(CHEMICALS.values(),expected):
            self.assertEqual((chemical.ce,chemical.a,chemical.k),values)
            histories={h:history(chemical,2.3,h) for h in HALF_LIVES}
            for h,(decay,rows) in histories.items():
                self.assertEqual(decay,0 if h is None else math.log(2)/h)
                previous=0
                for row in rows:
                    day=row['day']
                    self.assertAlmostEqual(row['rate_percent'],values[0]*(1-values[1]*math.exp(-values[2]*day)))
                    self.assertGreaterEqual(row['cumulative_mg'],previous)
                    self.assertTrue(all(math.isfinite(v) for v in row.values()))
                    self.assertGreaterEqual(row['remaining_mg'],0)
                    self.assertLessEqual(row['remaining_mg'],row['cumulative_mg'])
                    direct=sum(r['increment_mg']*math.exp(-decay*(day-r['day'])) for r in rows[:day])
                    self.assertAlmostEqual(row['remaining_mg'],direct,places=8)
                    if h is None: self.assertEqual(row['remaining_mg'],row['cumulative_mg'])
                    previous=row['cumulative_mg']
                self.assertEqual(rows[0]['increment_mg'],rows[0]['cumulative_mg'])
                self.assertEqual(rows[0]['remaining_mg'],rows[0]['cumulative_mg'])
            for day in range(64):
                residual=[histories[h][1][day]['remaining_mg'] for h in (5.,9.5,14.,None)]
                self.assertEqual(residual,sorted(residual))
                self.assertEqual(len({histories[h][1][day]['cumulative_mg'] for h in HALF_LIVES}),1)

    def test_sand_units_scaling_and_invalid_inputs(self):
        r=calculate_sand(1000,10,1500,10)
        self.assertEqual((r.q_plan_mg_m2,r.volume_m3,r.mass_kg),(100,1,1500))
        self.assertAlmostEqual(r.concentration_mg_kg,2/3)
        self.assertEqual(calculate_sand(2000,10,1500,10).concentration_mg_kg,2*r.concentration_mg_kg)
        self.assertEqual(calculate_sand(1000,10,1500,20).concentration_mg_kg,r.concentration_mg_kg/2)
        self.assertEqual(calculate_sand(2000,20,1500,10).concentration_mg_kg,r.concentration_mg_kg)
        self.assertEqual(calculate_sand(0,10,1500,10).concentration_mg_kg,0)
        for i in range(4):
            for bad in (-1,float('nan'),float('inf'),-float('inf')):
                args=[1000,10,1500,10]; args[i]=bad
                with self.assertRaises(ValueError): calculate_sand(*args)
        for i in (1,2,3):
            args=[1000,10,1500,10]; args[i]=0
            with self.assertRaises(ValueError): calculate_sand(*args)
        for bad in (0,65,1.5,float('nan'),float('inf')):
            with self.assertRaises(ValueError): rate(CHEMICALS['Caprolactam'],bad)
        for bad in (0,-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError): history(CHEMICALS['Caprolactam'],bad,None)
        with self.assertRaises(ValueError): history(CHEMICALS['Caprolactam'],1,3)


class UITests(unittest.TestCase):
    def test_live_panel_charts_csv_all_inputs(self):
        from streamlit.testing.v1 import AppTest
        import pyarrow as pa
        app=AppTest.from_file(str(ROOT/'v4/app.py'),default_timeout=30)
        captures=[]
        def capture(rows,conditions):
            data=csv_bytes(rows,conditions)
            captures.append(list(csv.DictReader(io.StringIO(data.decode('utf-8-sig')))))
            return data
        def verify():
            self.assertEqual(len(app.exception),0)
            names=app.multiselect(key='chemicals').value
            d=MeshInput(*[app.number_input(key=k).value for k in ('length','width','diameter','spacing')])
            halves={n: HALF_LIVES[app.selectbox(key='half_'+n).options.index(app.selectbox(key='half_'+n).value)] for n in names}
            m=build_model(d,app.selectbox(key='structure').value,names,app.slider(key='days').value,halves,
                          *[app.number_input(key=k).value for k in ('density','depth','surface','average','maximum')])
            latex='\n'.join(x.value for x in app.latex)
            for value in (m['mass_kg'],m['geometry'].total_surface_m2,m['geometry'].filament_length_m):
                self.assertIn(f'{value:.6f}',latex)
            summary=app.dataframe[0].value
            table=app.dataframe[1].value
            chart=app.get('vega_lite_chart')[2]
            graph=pa.ipc.open_stream(chart.proto.data.data).read_all().to_pandas()
            for item in m['chemicals']:
                name=item['chemical'].name
                row=summary.loc[summary['물질']==name].iloc[0]
                self.assertEqual(float(row['환경 잔존량 [mg]']),item['current']['remaining_mg'])
                for value in (item['current']['remaining_mg'],item['current']['rate_percent'],item['q_pa6']):
                    self.assertIn(f'{value:.6f}',latex)
                self.assertAlmostEqual(sum(r['contribution_mg'] for r in item['contributions']),item['current']['remaining_mg'],places=8)
                for layer in item['layers'].values():
                    self.assertIn(f'{layer.concentration_mg_kg:.6f}',latex)
                    self.assertIn(f'{layer.mass_kg:.6f}',latex)
                for r in item['table']:
                    actual=table.loc[(table['물질']==name)&(table[DEPTH]==r[DEPTH])].iloc[0]
                    exported=next(x for x in captures[-1] if x['물질']==name and float(x[DEPTH])==r[DEPTH])
                    self.assertEqual(float(actual[CONCENTRATION]),r[CONCENTRATION])
                    self.assertEqual(float(exported[CONCENTRATION]),r[CONCENTRATION])
                    points=graph.loc[(graph.series==name)&(graph.depth==r[DEPTH])]
                    if len(points): self.assertEqual(float(points.value.iloc[0]),r[CONCENTRATION])
            self.assertEqual(len(app.get('vega_lite_chart')),4)
            self.assertEqual(len(app.get('download_button')),1)
        with patch('v4.sand.csv_bytes',side_effect=capture):
            app.run(); verify()
            for key,value in [('length',8.2),('width',1.2),('diameter',1.5),('spacing',25.),
                               ('density',1600.),('depth',12.3),('surface',.1),('average',15.),('maximum',40.)]:
                app.number_input(key=key).set_value(value).run(); verify()
            app.selectbox(key='structure').select(STRUCTURES[1]).run(); verify()
            app.multiselect(key='chemicals').set_value(list(CHEMICALS)).run(); verify()
            app.slider(key='days').set_value(64).run(); verify()
            for name in CHEMICALS:
                widget=app.selectbox(key='half_'+name)
                widget.select(widget.options[1]).run(); verify()
            widget=app.selectbox(key='half_Caprolactam')
            widget.select(widget.options[0]).run(); verify()
            app.checkbox(key='log').check().run(); verify()
            app.number_input(key='density').set_value(0.).run()
            self.assertEqual(len(app.error),1)
            self.assertEqual(len(app.get('download_button')),0)


if __name__ == '__main__': unittest.main()
