from math import pi, cos, asin, sqrt
import pickle
from cctbx.array_family import flex
from cctbx import uctbx
from scitbx.test_utils import approx_equal

def exercise_functions():
  d_star_sq = 1.2345
  assert approx_equal(
    uctbx.d_star_sq_as_stol_sq(d_star_sq), d_star_sq / 4)
  assert approx_equal(
    uctbx.d_star_sq_as_two_stol(d_star_sq)**2, d_star_sq)
  assert approx_equal(
    uctbx.d_star_sq_as_stol(d_star_sq)**2, d_star_sq / 4)
  assert approx_equal(
    1/(uctbx.d_star_sq_as_d(d_star_sq)**2), d_star_sq)
  assert approx_equal(
    uctbx.d_star_sq_as_two_theta(d_star_sq, 1.5),
    2 * asin(1.5/2*sqrt(d_star_sq)))
  assert approx_equal(
    uctbx.d_star_sq_as_two_theta(d_star_sq, 1.5),
    uctbx.d_star_sq_as_two_theta(d_star_sq, 1.5, 0))
  assert approx_equal(
    uctbx.d_star_sq_as_two_theta(d_star_sq, 1.5)*180/pi,
    uctbx.d_star_sq_as_two_theta(d_star_sq, 1.5, 1))

def exercise_basic():
  d = (1,1,1,90,90,90)
  u = uctbx.unit_cell(d)
  assert u.parameters() == d
  assert approx_equal(u.parameters(), u.reciprocal_parameters())
  assert approx_equal(u.volume(), 1)
  assert approx_equal(u.longest_vector_sq(), 3)
  p = (2,3,4,80,100,110)
  for i in xrange(7):
    u = uctbx.unit_cell(p[:i])
    assert u.parameters() == p[:i] + d[i:]
    v = uctbx.unit_cell(p[:i], 0)
    assert v.parameters() == u.parameters()
    if (i):
      assert not approx_equal(u.parameters(), u.reciprocal_parameters())
      assert not u.is_similar_to(u.reciprocal())
      assert not u.is_similar_to(u.reciprocal(), 1.e-3)
      assert not u.is_similar_to(u.reciprocal(), 1.e-3, 1.e-3)
      assert u.is_similar_to(u.reciprocal(), 1000, 180)
    assert approx_equal(
      u.reciprocal_parameters(), u.reciprocal().parameters())
    assert approx_equal(
      u.parameters(), u.reciprocal().reciprocal_parameters())
    assert approx_equal(
      u.reciprocal_metrical_matrix(), u.reciprocal().metrical_matrix())
    assert approx_equal(
      u.metrical_matrix(), u.reciprocal().reciprocal_metrical_matrix())
    v = u.reciprocal().reciprocal()
    assert u.is_similar_to(v, 1.e-3, 1.e-3)
    assert approx_equal(u.volume(), 1/u.reciprocal().volume())
  u = uctbx.unit_cell(p)
  m = u.metrical_matrix()
  n = (2*2, 3*3, 4*4,
       2*3*cos(110*pi/180), 2*4*cos(100*pi/180), 3*4*cos(80*pi/180))
  assert approx_equal(m, n)
  v = uctbx.unit_cell(m, 1)
  assert approx_equal(u.parameters(), v.parameters())
  u = uctbx.unit_cell((2,3,4))
  assert approx_equal(u.volume(), 2*3*4)
  assert approx_equal(u.longest_vector_sq(), 2*2+3*3+4*4)
  u = uctbx.unit_cell(p)
  assert approx_equal(u.volume(), 22.04006625)

def exercise_frac_orth():
  u = uctbx.unit_cell(())
  assert approx_equal(
    u.fractionalization_matrix(), u.orthogonalization_matrix())
  u = uctbx.unit_cell((2,3,5))
  assert approx_equal(
    u.fractionalize((1,2,4)), (1/2., 2/3., 4/5.))
  assert approx_equal(
    u.orthogonalize((1/2., 2/3., 4/5.)), (1,2,4))
  assert approx_equal(
    u.length((1/2.,2/3.,4/5.))**2, 1**2 + 2**2 + 4**2)
  assert approx_equal(
    u.distance((7/2.,8/3.,9/5.), (3,2,1))**2, 1**2 + 2**2 + 4**2)
  assert approx_equal(
    u.mod_short_length((1/4.,2/3.,4/5.)),
    u.length((1/4.,-1/3.,-1/5.)))
  assert approx_equal(
    u.mod_short_distance((13/4.,8/3.,9/5.), (3,2,1)),
    u.length((1/4.,-1/3.,-1/5.)))
  c = flex.vec3_double(((7/2.,8/3.,9/5.), (13/4.,8/3.,9/5.)))
  assert approx_equal(
    u.min_mod_short_distance(c, (3,2,1)),
    u.mod_short_distance((13/4.,8/3.,9/5.), (3,2,1)))

def exercise_change_basis():
  u = uctbx.unit_cell(())
  assert approx_equal(
    u.parameters(),
    u.change_basis((1,0,0, 0,1,0, 0,0,1)).parameters())
  assert approx_equal(
    u.parameters(),
    u.change_basis((2,0,0, 0,2,0, 0,0,2), 2).parameters())
  u = uctbx.unit_cell((2,3,5))
  assert approx_equal(
    u.change_basis((0,1,0, 0,0,1, 1,0,0)).parameters(),
    (5,2,3,90,90,90))

def exercise_miller_index_methods():
  u = uctbx.unit_cell((2,3,5))
  assert u.max_miller_indices(0.5) == (4,6,10)
  assert u.max_miller_indices(0.5, 1.e-3) == (4,6,10)
  assert approx_equal(
    u.d_star_sq((1,0,0)), 1/4.)
  assert approx_equal(
    u.d_star_sq((0,1,0)), 1/9.)
  assert approx_equal(
    u.d_star_sq((0,0,1)), 1/25.)
  u = uctbx.unit_cell((2,3,5,80,100,110))
  h = (1,2,3)
  d_star_sq_123 = 1.39498933203
  assert approx_equal(
    u.d_star_sq(h), d_star_sq_123)
  assert approx_equal(
    u.stol_sq(h), d_star_sq_123 / 4)
  assert approx_equal(
    u.two_stol(h)**2, d_star_sq_123)
  assert approx_equal(
    u.stol(h)**2, d_star_sq_123 / 4)
  assert approx_equal(
    1/(u.d(h)**2), d_star_sq_123)
  assert approx_equal(
    u.two_theta(h, 1.5), 2 * asin(1.5/2*sqrt(d_star_sq_123)))
  assert approx_equal(
    u.two_theta(h, 1.5),
    u.two_theta(h, 1.5, 0))
  assert approx_equal(
    u.two_theta(h, 1.5)*180/pi,
    u.two_theta(h, 1.5, 1))
  miller_indices = flex.miller_index(((1,2,3), (-3,4,-5), (2,-3,4)))
  for d_spacing_measure in (u.d_star_sq,
                            u.stol_sq,
                            u.two_stol,
                            u.stol,
                            u.d):
    values = d_spacing_measure(miller_indices)
    for i,v in values.items():
      assert approx_equal(
        v, d_spacing_measure(miller_indices[i]))
  values = u.two_theta(miller_indices, 1.5)
  for i,v in values.items():
    assert approx_equal(
      v, u.two_theta(miller_indices[i], 1.5))
  for deg in (0,1):
    values = u.two_theta(miller_indices, 1.5, deg)
    for i,v in values.items():
      assert approx_equal(
        v, u.two_theta(miller_indices[i], 1.5, deg))
  assert u.max_d_star_sq(miller_indices) == u.d_star_sq((-3,4,-5))
  assert u.min_max_d_star_sq(miller_indices) == (
    u.d_star_sq((1,2,3)), u.d_star_sq((-3,4,-5)))

def exercise_pickle():
  u = uctbx.unit_cell((2,3,5,80,100,110))
  p = pickle.dumps(u)
  v = pickle.loads(p)
  assert u.parameters() == v.parameters()

def exercise_exceptions():
  import sys
  if ("--skip" in sys.argv[1:]):
    print "SKIPPING: exercise_exceptions"
    return
  try:
    u = uctbx.unit_cell((0,0,0,0,0,0))
  except RuntimeError, e:
    assert str(e) == "cctbx Error: Corrupt unit cell parameters."
  else:
    raise AssertionError, 'exception expected'
  try:
    u = uctbx.unit_cell((0,0,0,0,0,0), 1)
  except RuntimeError, e:
    assert str(e) == "cctbx Error: Corrupt metrical matrix."
  else:
    raise AssertionError, 'exception expected'

def run():
  exercise_functions()
  exercise_basic()
  exercise_frac_orth()
  exercise_change_basis()
  exercise_miller_index_methods()
  exercise_pickle()
  exercise_exceptions()
  print "OK"

if (__name__ == "__main__"):
  run()
