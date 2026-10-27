import csv
import hashlib
import io
import json
import math
from dataclasses import replace
from pathlib import Path
import unittest
from unittest.mock import patch
from v5.engine import *
from v5.reporting import report, export_csv, PW_LABEL, DEPTH, SAND

ROOT=Path(__file__).resolve().parent.parent


class EngineTests(unittest.TestCase):
    def test_r1_c0_presets_and_no_double_rib(self):
        allp=design_comparison(10,1.5); r=allp['R1']; c=allp['C0']
        self.assertEqual(r['length'],2511)
        self.assertAlmostEqual(r['mass'],20.06,delta=.005)
        self.assertAlmostEqual(r['surface'],23.67,delta=.005)
        self.assertAlmostEqual(c['mass'],19.60,delta=.005)
        self.assertAlmostEqual(c['surface'],33.58,delta=.005)
        self.assertEqual((c['cross'],c['long']),(9.,3.8))
        self.assertAlmostEqual(c['t_base']*1000,5.4)
        self.assertAlmostEqual(c['t_rib']*1000,6.4)
        self.assertAlmostEqual(c['waste'],32.7,delta=.05)
        self.assertEqual((c['nw'],c['nall'],c['nregular'],c['nrib']),(126,2000,1600,400))
        self.assertEqual(c['tf']+c['tr'],2000*1.5*1.6)
        self.assertEqual(set(allp),{'R1',*PRESETS})
        for p in allp.values(): self.assertGreater(p['mass'],0)
        self.assertEqual(physical(replace(Design(),length=.0125))['nall'],2) # round(2.5) half even
        self.assertEqual(physical(replace(Design(),length=.0175))['nall'],4)

    def test_92_days_mass_balance_and_decay(self):
        for name in CHEMICALS:
            cases={h:chemical_scenario(name,2.3,92,h,.5,.8,15,1500,2650,.5,[1,10,14.4,37.6]) for h in HALF_LIVES}
            for h,c in cases.items():
                increments=[]; previous=0
                for j,r in enumerate(c['records'],1):
                    self.assertTrue(all(math.isfinite(v) and v>=0 for v in r.values()))
                    self.assertGreaterEqual(r['cumulative_mg'],previous); previous=r['cumulative_mg']
                    self.assertLessEqual(r['pw_remaining'],r['pw_in']*(1+1e-12))
                    self.assertAlmostEqual(r['pw_in'],.4*r['cumulative_mg'],places=9)
                    increments.append(r['increment_mg'])
                    self.assertAlmostEqual(sum(increments),r['cumulative_mg'],places=8)
                    direct=sum(x['pw_increment']*math.exp(-c['decay']*(j-x['day'])) for x in c['records'][:j])
                    self.assertAlmostEqual(r['pw_remaining'],direct,places=8)
                    if h is None: self.assertEqual(r['pw_remaining'],r['pw_in'])
                self.assertEqual(c['records'][0]['increment_mg'],c['records'][0]['cumulative_mg'])
                for layer in c['layers']:
                    self.assertGreaterEqual(layer['peak'],layer['average'])
                    self.assertGreaterEqual(layer['peak'],layer['selected'])
            for j in range(92):
                residual=[cases[h]['records'][j]['pw_remaining'] for h in (5.,9.5,14.,None)]
                self.assertEqual(residual,sorted(residual))

    def test_volume_stats_ratios_zero_and_units(self):
        v=pore_volume(10,10,1500,2650,.5)
        self.assertAlmostEqual(v['porosity'],1-1500/2650)
        self.assertAlmostEqual(v['water'],216.9811320754717)
        self.assertEqual(pore_volume(10,10,1500,2650,1)['water'],2*v['water'])
        self.assertEqual(pore_volume(10,20,1500,2650,.5)['water'],2*v['water'])
        records=[{'pw_remaining':x} for x in (1000,2000,1000)]
        s=concentration_stats(records,100,3)
        self.assertEqual((s['selected'],s['peak'],s['peak_day']),(10,20,2))
        self.assertAlmostEqual(s['average'],40/3)
        self.assertIsNone(concentration_stats(records,0,3)['peak'])
        for burial,eta in [(0,1),(.5,0)]:
            c=chemical_scenario('Caprolactam',1,7,9.5,burial,eta,10,1500,2650,.5,[10])
            self.assertEqual(c['current']['pw_in'],0)
            self.assertEqual(c['layers'][0]['selected'],0)
        m=build_model(Design(),['Caprolactam'],7,{'Caprolactam':9.5},{'Caprolactam':1},.5,1500,2650,.5,10)
        self.assertEqual(m['physical']['buried'],m['physical']['surface']/2)
        c=m['chemicals'][0]
        self.assertEqual(c['ratios']['selected'],c['selected']['selected']/.13)
        self.assertEqual(c['ratios']['peak'],c['selected']['peak']/.13)
        self.assertEqual(c['ratios']['average'],c['selected']['average']/.13)
        self.assertAlmostEqual(c['selected']['selected']*c['selected']['water'],c['current']['pw_remaining'])

    def test_invalid_and_r2(self):
        for b,s in [(2650,2650),(3000,2650),(0,2650),(1500,0),(float('nan'),2650)]:
            with self.assertRaises(ValueError): pore_volume(10,10,b,s,.5)
        for bad in (-.1,1.1,float('nan'),float('inf')):
            with self.assertRaises(ValueError): fraction(bad)
        for kwargs in ({'length':0},{'dw':-1},{'spacing':3},{'n':100},{'path':.9},{'rib_period':1.2},{'h':float('nan')},{'recovery':0}):
            with self.assertRaises(ValueError): physical(replace(Design(),**kwargs))
        with self.assertRaises(ValueError): physical(Design(structure=MEASURED))
        d=Design(structure=MEASURED,measured_mass=20,measured_area=30,measured_thickness=6)
        args=(['Caprolactam'],7,{'Caprolactam':None},{'Caprolactam':1},.5,1500,2650,.5,10)
        self.assertEqual(build_model(d,*args)['chemicals'],[])
        self.assertEqual(build_model(replace(d,measured_pa6=True),*args)['physical']['mass'],20)

    def test_v4_equivalence_and_preservation(self):
        from v4.model import history as old_history, CHEMICALS as OLD, build_model as old_build
        from v4.mesh_engine import MeshInput as OldInput
        for name in CHEMICALS:
            self.assertEqual(vars(CHEMICALS[name]),vars(OLD[name]))
            for h in HALF_LIVES:
                _,old=old_history(OLD[name],3.2,h)
                _,new=history(CHEMICALS[name],3.2,h)
                self.assertEqual(old,new[:64])
        for structure in (SQUARE,ROTATED):
            d=Design(structure=structure,width=1,dw=2,spacing=20)
            old=old_build(OldInput(10,1,2,20),structure,['Caprolactam'],7,{'Caprolactam':9.5},1500,10,1,14.4,37.6)
            new=build_model(d,['Caprolactam'],7,{'Caprolactam':9.5},{'Caprolactam':1},.5,1500,2650,.5,10)
            self.assertAlmostEqual(old['mass_kg'],new['physical']['mass'],places=12)
            self.assertEqual(old['geometry'].total_surface_m2,new['physical']['surface'])
            self.assertAlmostEqual(old['chemicals'][0]['layers']['selected'].concentration_mg_kg,new['chemicals'][0]['selected']['sand'].concentration_mg_kg,places=10)
        for item in json.loads((ROOT/'v5/preserved_hashes.json').read_text(encoding='utf-8-sig')):
            self.assertEqual(hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest().upper(),item['hash'],item['path'])

    def test_csv_table_graph_consistency_and_no_tildes(self):
        names=list(CHEMICALS)
        m=build_model(Design(),names,92,{n:9.5 for n in names},{n:.8 for n in names},.5,1500,2650,.5,14.4)
        r=report(m); csvrows=list(csv.DictReader(io.StringIO(export_csv(r['export']).decode('utf-8-sig'))))
        self.assertTrue(m['extrapolated'])
        for row in r['layers']:
            matched=next(x for x in csvrows if x['표 구분']=='깊이 비교' and x['물질']==row['물질'] and float(x[DEPTH])==row[DEPTH])
            self.assertEqual(float(matched[PW_LABEL]),row[PW_LABEL])
            self.assertEqual(float(matched[SAND]),row[SAND])
        for c in m['chemicals']:
            for x in c['comparison']:
                self.assertAlmostEqual(x['selected']*x['water'],c['current']['pw_in'] if x['scenario']=='분해 미반영' else c['current']['pw_remaining'])
            if c['name']!='Caprolactam': self.assertIsNone(c['ratios'])
        for filename in ('app.py','panel.py','sources.py','reporting.py','sand.py'):
            self.assertNotIn('~',(ROOT/'v5'/filename).read_text(encoding='utf-8'))


class UITests(unittest.TestCase):
    def test_live_ui_presets_panel_download_and_boundaries(self):
        from streamlit.testing.v1 import AppTest
        import pyarrow as pa
        captured=[]
        def capture(m):
            captured.append(m); return report(m)
        app=AppTest.from_file(str(ROOT/'v5/app.py'),default_timeout=30)
        def verify():
            self.assertEqual(len(app.exception),0)
            self.assertEqual(len(app.error),0)
            m=captured[-1]; latex='\n'.join(x.value for x in app.latex)
            self.assertIn(f"{m['physical']['mass']:.6f}",latex)
            self.assertIn(f"{m['physical']['buried']:.6f}",latex)
            self.assertIn(f"{m['volume']['porosity']:.6f}",latex)
            self.assertIn(f"{m['volume']['water']:.6f}",latex)
            for c in m['chemicals']:
                for v in (c['current']['pw_remaining'],c['current']['pw_in'],c['current']['cumulative_mg']):
                    self.assertIn(f'{v:.6f}',latex)
                if c['selected']['selected'] is not None:
                    for key in ('selected','peak','average'): self.assertIn(f"{c['selected'][key]:.6f}",latex)
            if m['chemicals']:
                self.assertEqual(len(app.get('download_button')),1)
                summary=app.dataframe[2].value
                self.assertEqual(float(summary.iloc[0]['총 누적 용출량 [mg]']),m['chemicals'][0]['current']['cumulative_mg'])
                if m['volume']['water']>0:
                    chart=app.get('vega_lite_chart')[2]
                    points=pa.ipc.open_stream(chart.proto.data.data).read_all().to_pandas()
                    for c in m['chemicals']:
                        point=points.loc[(points.series==c['name'])&(points.x==m['days'])].iloc[0]
                        self.assertEqual(float(point.y),c['selected']['selected'])
        with patch('v5.reporting.report',side_effect=capture):
            app.run(); verify()
            for key,value in [('length',8.),('width',1.65),('dw',2.8),('spacing',13.),('df',1.),('n',22.),('h',.8),
                              ('rib_period',4),('path',1.7),('crimp',1.1),('rho',1140.),('recovery',70.),('core',.2),
                              ('burial',30.),('eta_Caprolactam',60.),('density',1600.),('particle',2700.),('sat',25.),
                              ('depth',12.3),('surface',.5),('average',15.),('maximum',40.)]:
                app.number_input(key=key).set_value(value).run(); verify()
            app.slider(key='days').set_value(65).run(); verify()
            self.assertTrue(any('외삽' in x.value for x in app.warning))
            app.slider(key='days').set_value(92).run(); verify()
            app.multiselect(key='chemicals').set_value(list(CHEMICALS)).run(); verify()
            for name in CHEMICALS:
                x=app.selectbox(key='half_'+name); x.select(x.options[1]).run(); verify()
                app.number_input(key='eta_'+name).set_value(80.).run(); verify()
            for name in ('A1','A2','A3','A4','C0'):
                app.selectbox(key='preset').select(name).run(); verify()
                self.assertEqual(app.number_input(key='spacing').value,PRESETS[name][0])
            app.selectbox(key='preset').select('R1').run(); verify()
            app.selectbox(key='structure').select(ROTATED).run(); verify()
            app.selectbox(key='width_preset').select('1.525').run(); verify()
            self.assertEqual(app.number_input(key='width').value,1.525)
            app.selectbox(key='sat_preset').select('100%').run(); verify()
            self.assertEqual(app.number_input(key='sat').value,100.)
            app.number_input(key='sat').set_value(0.).run(); verify()
            self.assertTrue(any('공극수 없음' in x.value for x in app.warning))
            self.assertIsNone(captured[-1]['chemicals'][0]['selected']['peak'])
            app.number_input(key='sat').set_value(50.).run()
            app.number_input(key='burial').set_value(0.).run(); verify()
            app.checkbox(key='log').check().run(); verify()
            self.assertEqual(captured[-1]['chemicals'][0]['selected']['selected'],0)
            app.number_input(key='density').set_value(3000.).run()
            self.assertEqual(len(app.error),1)
            self.assertEqual(len(app.get('download_button')),0)
            app.number_input(key='density').set_value(1500.).run()
            app.selectbox(key='preset').select('R2').run()
            self.assertEqual(len(app.error),1)
            for k,v in [('measured_mass',20.),('measured_area',30.),('measured_thickness',6.)]: app.number_input(key=k).set_value(v)
            app.run(); verify()
            self.assertEqual(len(app.get('download_button')),0)
            app.checkbox(key='measured_pa6').check().run(); verify()


if __name__=='__main__': unittest.main()
