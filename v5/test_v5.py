import math, unittest
from dataclasses import replace
from v5.engine import Design, PRESETS, geometry, exposures, porosity, pore_volume, solid_loading, PNEC

class V5Tests(unittest.TestCase):
    def test_reference_geometry(self):
        r=geometry(Design(kind='R1')); c=geometry(Design())
        self.assertEqual(r['total_length'],2511)
        self.assertAlmostEqual(r['mass'],20.0567,delta=.02)
        self.assertAlmostEqual(r['area'],23.6656,delta=.02)
        self.assertAlmostEqual(c['mass'],19.59866,places=4)
        self.assertAlmostEqual(c['area'],33.58048,places=4)
        self.assertAlmostEqual(c['waste'],32.66443,places=4)
        self.assertEqual((c['gap_cross'],c['gap_long']),(9.0,3.8))
        self.assertAlmostEqual(c['thickness_base']*1000,5.4)
        self.assertAlmostEqual(c['thickness_rib']*1000,6.4)
        self.assertEqual(c['details']['n_all'],c['details']['n_regular']+c['details']['n_rib'])
        self.assertEqual((r['gap_cross'],r['gap_long']),(9,9))
    def test_burial(self):
        x=self.x(buried=.5)
        y=self.x(buried=0)
        z=self.x(eta=0)
        self.assertAlmostEqual(x['current']['allocated_mg'],x['current']['total_mg']*.5)
        self.assertEqual(y['current']['remaining_mg'],0)
        self.assertEqual(z['current']['allocated_mg'],0)
    def test_pore(self):
        self.assertAlmostEqual(porosity(1500,2650),1-1500/2650)
        self.assertAlmostEqual(pore_volume(15,10,1500,2650,.5),15*.1*(1-1500/2650)*.5*1000)
        self.assertEqual(self.x(saturation=0)['current']['concentration'],None)
        with self.assertRaises(ValueError): porosity(2650,2650)
        with self.assertRaises(ValueError): porosity(2800,2650)
        self.assertAlmostEqual(pore_volume(15,10,1500,2650,1),2*pore_volume(15,10,1500,2650,.5))
    def x(self,**changes):
        args=dict(mass_kg=19.6,chemical_name='Caprolactam',days=92,buried=.5,eta=1,
                  half=9.5,plan=15,depth=10,bulk=1500,particle=2650,saturation=.5)
        args.update(changes)
        return exposures(**args)
    def test_daily_and_reference(self):
        x=self.x();y=self.x(half=None)
        self.assertEqual(len(x['rows']),92)
        self.assertEqual(x['rows'][-1]['day'],92)
        self.assertGreaterEqual(x['peak'],x['average'])
        self.assertEqual(y['current']['allocated_mg'],y['current']['remaining_mg'])
        self.assertAlmostEqual(sum(r['increment_mg'] for r in x['rows']),x['current']['total_mg'])
        for r in x['rows']:
            self.assertGreaterEqual(r['remaining_mg'],0)
            self.assertLessEqual(r['remaining_mg'],r['allocated_mg']+1e-8)
        self.assertAlmostEqual(x['pnec_ratios']['current']*PNEC,x['current']['concentration'])
        self.assertAlmostEqual(solid_loading(1500,15,10,1500),1500/2250)
    def test_sat_conditions_and_extremes(self):
        a,b,c=(self.x(saturation=s)['current']['concentration'] for s in (.25,.5,1.))
        self.assertAlmostEqual(a,2*b)
        self.assertAlmostEqual(b,2*c)
        self.assertEqual(self.x(days=1)['peak_day'],1)
        for days in (0,93):
            with self.assertRaises(ValueError): self.x(days=days)

if __name__=='__main__': unittest.main()
