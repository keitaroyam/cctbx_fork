from __future__ import division
from cctbx.array_family import flex
from scitbx import sparse
from cctbx import uctbx, xray, crystal
from smtbx.refinement import constraints
from math import pi
import math
from scitbx.matrix import col
from scitbx import matrix as mat
from libtbx.test_utils import approx_equal

def exercise_rigid_site_proxy(n=5):
  uc = uctbx.unit_cell((1, 2, 3))
  reparam = constraints.ext.reparametrisation(uc)
  independents = [ ]
  for name in ('C#', 'C##'):
    sc = xray.scatterer(name, site=tuple(flex.random_double(3)))
    sc.flags.set_grad_site(True)
    p = reparam.add(constraints.independent_site_parameter, sc)
    independents.append(p)
  pivot, pivot_neighbour = independents
  rigid_group_scatterers = [ ]
  for i in xrange(n):
    sc = xray.scatterer('C%i' %i,
                        site=tuple(flex.random_double(3)))
    sc.flags.set_grad_site(True)
    rigid_group_scatterers.append(sc)
  phi = reparam.add(constraints.independent_scalar_parameter,
                    value=0.1, variable=True)
  rigid_group = reparam.add(constraints.rigid_pivoted_rotable_group,
                            pivot, pivot_neighbour,
                            azimuth=phi,
                            scatterers=rigid_group_scatterers)
  proxies = [ ]
  for i in xrange(n):
    proxies.append(reparam.add(constraints.rigid_site_proxy,
                               parent=rigid_group,
                               index=i))
  reparam.finalise()

  assert str(reparam) == """\
digraph dependencies {
7 -> 0;
7 -> 3;
7 -> 6;
22 -> 7;
25 -> 7;
28 -> 7;
31 -> 7;
34 -> 7;
0 [label="independent_site_parameter (C#) #0"];
3 [label="independent_site_parameter (C##) #3"];
6 [label="independent_scalar_parameter #6"];
7 [label="rigid_pivoted_rotable_group (C0, C1, C2, C3, C4) #7"];
22 [label="rigid_site_proxy #22"];
25 [label="rigid_site_proxy #25"];
28 [label="rigid_site_proxy #28"];
31 [label="rigid_site_proxy #31"];
34 [label="rigid_site_proxy #34"]
}"""

  reparam.linearise()
  jt = reparam.jacobian_transpose

  q = 2*3 + 1 # pivot, its neighbour, azimuthal angle
  jt0 = sparse.matrix(q, q + 2*3*n) # + rigid_group + constrained site proxies
  assert jt.n_rows == jt0.n_rows
  assert jt.n_cols == jt0.n_cols
  for i,j in zip(xrange(q, q+3*n), xrange(q+3*n, jt0.n_cols)):
    assert jt.col(i) == jt.col(j)

def exercise_rigid_pivoted_rotable():
  uc = uctbx.unit_cell((1, 1, 1))
  xs = xray.structure(
    crystal_symmetry=crystal.symmetry(
      unit_cell=uc,
      space_group_symbol='hall: P 2x 2y'),
    scatterers=flex.xray_scatterer(( #triangle
      xray.scatterer('C0', site=(0,0,0)),
      xray.scatterer('C1', site=(0,2,0)),
      xray.scatterer('C2', site=(1,1,0)),
      )))
  r = constraints.ext.reparametrisation(xs.unit_cell())
  sc = xs.scatterers()
  pivot = r.add(constraints.independent_site_parameter, sc[0])
  pivot_neighbour = r.add(constraints.independent_site_parameter, sc[1])
  azimuth = r.add(constraints.independent_scalar_parameter,
                  value=pi/2, variable=True)
  rg = r.add(constraints.rigid_pivoted_rotable_group,
                pivot=pivot,
                pivot_neighbour=pivot_neighbour,
                azimuth = azimuth,
                scatterers=(sc[1], sc[2]))
  site_proxy = r.add(constraints.rigid_site_proxy, rg, 1)
  r.finalise()
  r.linearise()
  r.store()
  #check that proxy an the final results are the same...
  assert approx_equal(
    uc.distance(col(site_proxy.value), col(sc[2].site)), 0, eps=1e-15)
  #rotation happens around the center of gravity
  assert approx_equal(
    uc.distance(col((.5,1,.5)), col(sc[2].site)), 0, eps=1e-15)

class rigid_rotable(object):
  def __init__(self):
    self.size_value = 9
    self.rx = pi
    self.ry = pi/2
    self.rz = pi/3
    self.sites = ((0,0,0), (1,0,0), (0,1,0), (0,0,1))
    self.uc = uctbx.unit_cell((1, 1, 1))
    self.xs = xray.structure(
      crystal_symmetry=crystal.symmetry(
        unit_cell=self.uc,
        space_group_symbol='hall: P 2x 2y'),
      scatterers=flex.xray_scatterer(( #triangle
        xray.scatterer('C0'),
        xray.scatterer('C1'),
        xray.scatterer('C2'),
        xray.scatterer('C3'),
        )))
    self.center = col((0,0,0))
    for s in self.sites[1:]:
      self.center = self.center + col(s)
    self.center = self.center / (len(self.sites)-1)
    self.reset_sites()
  def reset_sites(self):
    sc = self.xs.scatterers()
    for i, s in enumerate(self.sites):
      sc[i].site = s
  def exercise_expansion(self):
    self.reset_sites()
    r = constraints.ext.reparametrisation(self.uc)
    sc = self.xs.scatterers()
    pivot = r.add(constraints.independent_site_parameter, sc[0])
    size = r.add(constraints.independent_scalar_parameter,
                    value=self.size_value, variable=True)
    r_x = r.add(constraints.independent_scalar_parameter,
                    value=0, variable=False)
    r_y = r.add(constraints.independent_scalar_parameter,
                    value=0, variable=False)
    r_z = r.add(constraints.independent_scalar_parameter,
                    value=0, variable=False)
    rg = r.add(constraints.rigid_rotable_expandable_group,
                  pivot=pivot,
                  size = size,
                  alpha = r_x,
                  beta = r_y,
                  gamma = r_z,
                  scatterers=(sc[1], sc[2], sc[3]))
    r.finalise()
    r.linearise()
    r.store()
    for i in xrange(1,4):
      calc_site = (col(self.sites[i])-self.center)*self.size_value + self.center
      assert approx_equal(
        self.uc.distance(
          calc_site, col(sc[i].site)), 0, eps=1e-14)
  def exercise_rotation(self):
    self.reset_sites()
    r = constraints.ext.reparametrisation(self.uc)
    sc = self.xs.scatterers()
    pivot = r.add(constraints.independent_site_parameter, sc[0])
    size = r.add(constraints.independent_scalar_parameter,
                    value=1, variable=False)
    r_x = r.add(constraints.independent_scalar_parameter,
                    value=pi, variable=True)
    r_y = r.add(constraints.independent_scalar_parameter,
                    value=pi/2, variable=True)
    r_z = r.add(constraints.independent_scalar_parameter,
                    value=pi/3, variable=True)
    rg = r.add(constraints.rigid_rotable_expandable_group,
                  pivot=pivot,
                  size = size,
                  alpha = r_x,
                  beta = r_y,
                  gamma = r_z,
                  scatterers=(sc[1], sc[2], sc[3]))
    r.finalise()
    r.linearise()
    r.store()
    rx_m = mat.sqr((1, 0, 0,
                0, math.cos(self.rx), -math.sin(self.rx),
                0, math.sin(self.rx), math.cos(self.rx)))
    ry_m = mat.sqr((math.cos(self.ry), 0, math.sin(self.ry),
                    0, 1, 0,
                    -math.sin(self.ry), 0, math.cos(self.ry)))
    rz_m = mat.sqr((math.cos(self.rz), -math.sin(self.rz), 0,
                    math.sin(self.rz), math.cos(self.rz), 0,
                    0, 0, 1))
    R = rx_m*ry_m*rz_m #comulative rotation matrix
    for i in xrange(1,4):
      calc_site = col(mat.row(col(self.sites[i])-self.center)*R) + self.center
      assert approx_equal(
        self.uc.distance(
          calc_site, col(sc[i].site)), 0, eps=1e-14)
  def excercise(self):
    self.exercise_expansion()
    self.exercise_rotation()


def run():
  exercise_rigid_site_proxy()
  exercise_rigid_pivoted_rotable()
  rigid_rotable().excercise()
  print 'OK'

if __name__ == '__main__':
  run()
