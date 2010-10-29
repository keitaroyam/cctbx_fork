from __future__ import division
from cctbx import uctbx, xray, sgtbx, crystal
from smtbx.refinement import constraints
from scitbx import sparse
from scitbx import matrix as mat
from cctbx.array_family import flex
from libtbx.test_utils import Exception_expected, approx_equal
import libtbx.utils
import smtbx.utils

class terminal_linear_ch_site_test_case(object):

  eps = 1.e-15
  bond_length = 0.9

  def __init__(self, with_special_position_pivot):
    self.with_special_position_pivot = with_special_position_pivot
    self.uc = uctbx.unit_cell((1, 2, 3))
    self.sg = sgtbx.space_group("P 6")
    self.c0 = xray.scatterer("C0", site=(1e-5, 0., 0.1))
    self.site_symm = sgtbx.site_symmetry(self.uc, self.sg, self.c0.site)
    self.c0.flags.set_grad_site(True)
    self.c1 = xray.scatterer("C1", site=(0.09, 0.11, 0.))
    self.c1.flags.set_grad_site(True)
    self.h = xray.scatterer("H")
    self.reparam = constraints.ext.reparametrisation(self.uc)
    if with_special_position_pivot:
      x0 = self.reparam.add(constraints.special_position_site_parameter,
                            self.site_symm, self.c0)
    else:
      x0 = self.reparam.add(constraints.independent_site_parameter, self.c0)
    x1 = self.reparam.add(constraints.independent_site_parameter, self.c1)
    l = self.reparam.add(constraints.independent_scalar_parameter,
                         self.bond_length, variable=False)
    x_h = self.reparam.add(constraints.terminal_linear_ch_site,
                           pivot=x0,
                           pivot_neighbour=x1,
                           length=l,
                           hydrogen=self.h)
    self.reparam.finalise()
    self.x0, self.x1, self.x_h, self.l = [ x.index for x in (x0, x1, x_h, l) ]
    if self.with_special_position_pivot:
      self.y0 = x0.independent_params.index

  def run(self):
    self.reparam.linearise()
    self.reparam.store()
    x_c0, x_c1, x_h = [ mat.col(sc.site)
                        for sc in (self.c0, self.c1, self.h) ]
    if self.with_special_position_pivot:
      assert approx_equal(x_c0, self.site_symm.exact_site(), self.eps)
    assert approx_equal(self.uc.angle(x_c1, x_c0, x_h), 180, self.eps)
    assert approx_equal(
      self.uc.distance(x_c0, x_h), self.bond_length, self.eps)

    if self.with_special_position_pivot:
      jt0 = sparse.matrix(1 + 3, # y0, x1
                          1 + 3 + 3 + 1 + 3) # y0, x0, x1, l, x_h
    else:
      jt0 = sparse.matrix(3 + 3, # x0, x1
                          3 + 3 + + 1 + 3) # x0, x1, l, x_h

    # Identity for independent parameters
    if self.with_special_position_pivot:
      jt0[self.y0, self.y0] = 1.
    for i in xrange(3): jt0[self.x0 + i, self.x0 + i] = 1.
    for i in xrange(3): jt0[self.x1 + i, self.x1 + i] = 1.

    # special position x0
    if self.with_special_position_pivot:
      jt0[self.y0, self.x0    ] = 0
      jt0[self.y0, self.x0 + 1] = 0
      jt0[self.y0, self.x0 + 2] = 1.

    # riding
    if self.with_special_position_pivot:
      jt0[self.y0, self.x_h + 2] = 1.
    else:
      for i in xrange(3): jt0[self.x0 + i, self.x_h + i] = 1.

    jt = self.reparam.jacobian_transpose
    assert sparse.approx_equal(self.eps)(jt, jt0)


class special_position_adp_test_case(object):

  eps = 1.e-15

  def __init__(self):
    cs = crystal.symmetry(uctbx.unit_cell((1, 1, 2, 90, 90, 120)), 'R3')
    sgi = sgtbx.space_group_info('R3(y+z, x+z, x+y+z)')
    op = sgi.change_of_basis_op_to_reference_setting()
    self.cs = cs.change_basis(op.inverse())
    self.sc = xray.scatterer('C',
                             site=(3/8,)*3,
                             u=(1/2, 1/4, 3/4, -3/2, -3/4, -1/4))
    self.sc.flags.set_grad_u_aniso(True)
    self.site_symm = sgtbx.site_symmetry(self.cs.unit_cell(),
                                         self.cs.space_group(),
                                         self.sc.site)
    self.reparam = constraints.ext.reparametrisation(self.cs.unit_cell())
    u = self.reparam.add(constraints.special_position_u_star_parameter,
                         self.site_symm, self.sc)
    self.reparam.finalise()
    self.u, self.v = u.index, u.independent_params.index

  def run(self):
    self.reparam.linearise()
    self.reparam.store()
    assert approx_equal(self.sc.u_star, (19/6, 19/6, 17/2,
                                         11/6, 9/2, 9/2), self.eps)
    jt0 = sparse.matrix(2, 8)
    jt0[0, 0] = 1
    jt0[1, 1] = 1
    jac_u_star_trans = self.site_symm.adp_constraints().gradient_sum_matrix()
    jac_u_star_trans.reshape(flex.grid(
      self.site_symm.adp_constraints().n_independent_params(), 6))
    (m,n) = jac_u_star_trans.focus()
    for i in xrange(m):
      for j in xrange(n):
        jt0[i, j + 2] = jac_u_star_trans[i, j]
    jt = self.reparam.jacobian_transpose
    assert sparse.approx_equal(self.eps)(jt, jt0)


class c_oh_test_case(object):

  eps = 1.e-15
  bond_length = 0.9

  def __init__(self, staggered, verbose=False):
    self.staggered = staggered
    self.verbose = verbose
    self.cs = crystal.symmetry(uctbx.unit_cell((1, 1, 2, 90, 90, 80)),
                               "hall: P 2z")
    self.o = xray.scatterer('O', site=(0,0,0))
    self.o.flags.set_grad_site(True)
    self.c1 = xray.scatterer('C1', site=(1.5, 0, 0))
    self.c2 = xray.scatterer('C2', site=(2.5, 1, 0))
    self.h = xray.scatterer('H')
    self.reparam = constraints.ext.reparametrisation(self.cs.unit_cell())
    xo = self.reparam.add(constraints.independent_site_parameter, self.o)
    x1 = self.reparam.add(constraints.independent_site_parameter, self.c1)
    x2 = self.reparam.add(constraints.independent_site_parameter, self.c2)
    l = self.reparam.add(constraints.independent_scalar_parameter,
                         value=self.bond_length, variable=False)
    phi = self.reparam.add(constraints.independent_scalar_parameter,
                           value=0, variable=False)
    uc = self.cs.unit_cell()
    _ = mat.col
    if staggered:
      xh = self.reparam.add(
        constraints.staggered_terminal_tetrahedral_xh_site,
        pivot=xo,
        pivot_neighbour=x1,
        stagger_on=x2,
        length=l,
        hydrogen=(self.h,))
    else:
      xh = self.reparam.add(
        constraints.terminal_tetrahedral_xh_site,
        pivot=xo,
        pivot_neighbour=x1,
        azimuth=phi,
        length=l,
        e_zero_azimuth=uc.orthogonalize(_(self.c2.site) - _(self.c1.site)),
        hydrogen=(self.h,))
    self.reparam.finalise()
    self.xh, self.xo, self.x1, self.x2 = [ x.index for x in (xh, xo, x1, x2) ]
    self.l, self.phi = l.index, phi.index

  def run(self):
    self.reparam.linearise()
    self.reparam.store()
    uc = self.cs.unit_cell()
    _ = mat.col
    xh, xo, x1, x2 = [ uc.orthogonalize(sc.site)
                       for sc in (self.h, self.o, self.c1, self.c2) ]
    u_12 = _(x2) - _(x1)
    u_o1 = _(x1) - _(xo)
    u_oh = _(xh) - _(xo)
    assert approx_equal(u_12.cross(u_o1).dot(u_oh), 0, self.eps)
    assert approx_equal(u_12.cross(u_o1).angle(u_oh, deg=True), 90, self.eps)
    assert approx_equal(abs(u_oh), self.bond_length, self.eps)
    assert approx_equal(u_o1.angle(u_oh, deg=True), 109.47, 0.01)

    jt0 = sparse.matrix(3, 14)
    for i in xrange(3):
      jt0[self.xo + i, self.xo + i] = 1.
      jt0[self.xo + i, self.xh + i] = 1.
    jt = self.reparam.jacobian_transpose
    assert sparse.approx_equal(self.eps)(jt, jt0)

    if self.verbose:
      # finite difference derivatives to compare with
      # the crude riding approximation used for analytical ones
      def differentiate(sc):
        eta = 1.e-4
        jac = []
        for i in xrange(3):
          x0 = tuple(sc.site)
          x = list(x0)
          x[i] += eta
          sc.site = tuple(x)
          self.reparam.linearise()
          self.reparam.store()
          xp = _(self.h.site)
          x[i] -= 2*eta
          sc.site = tuple(x)
          self.reparam.linearise()
          self.reparam.store()
          xm = _(self.h.site)
          sc.site = tuple(x0)
          jac.extend( (xp - xm)/(2*eta) )
        return mat.sqr(jac)

      jac_o = differentiate(self.o)
      jac_1 = differentiate(self.c1)
      jac_2 = differentiate(self.c2)
      print "staggered: %s" % self.staggered
      print "J_o:"
      print jac_o.mathematica_form()
      print "J_1:"
      print jac_1.mathematica_form()
      print "J_2:"
      print jac_2.mathematica_form()

def exercise_symmetry_equivalent():
  xs = xray.structure(
    crystal_symmetry=crystal.symmetry(
      unit_cell=(1, 2, 3),
      space_group_symbol='hall: P 2x'),
    scatterers=flex.xray_scatterer((
      xray.scatterer("C", site=(0.1, 0.2, 0.3)),
    )))
  xs.scatterers()[0].flags.set_grad_site(True)
  connectivity_table = smtbx.utils.connectivity_table(xs)
  reparametrisation = constraints.reparametrisation(
    xs, [], connectivity_table)
  site_0 = reparametrisation.add(constraints.independent_site_parameter,
                                 scatterer=xs.scatterers()[0])
  g = sgtbx.rt_mx('x,-y,-z')
  symm_eq = reparametrisation.add(
    constraints.symmetry_equivalent_site_parameter,
    site=site_0, motion=g)
  reparametrisation.finalise()

  assert approx_equal(symm_eq.original.scatterers[0].site, (0.1, 0.2, 0.3),
                      eps=1e-15)
  assert str(symm_eq.motion) == 'x,-y,-z'
  assert symm_eq.is_variable
  reparametrisation.linearise()
  assert approx_equal(symm_eq.value, g*site_0.value, eps=1e-15)

  reparametrisation.store()
  assert approx_equal(symm_eq.value, (0.1, -0.2, -0.3), eps=1e-15)
  assert approx_equal(site_0.value, (0.1, 0.2, 0.3), eps=1e-15)

def exercise_u_iso_proportional_to_pivot_u_eq():
  xs = xray.structure(
    crystal_symmetry=crystal.symmetry(
      unit_cell=(),
      space_group_symbol='hall: P 2x 2y'),
    scatterers=flex.xray_scatterer((
      xray.scatterer('C0', u=(1, 1, 1, 0, 0, 0)),
      xray.scatterer('C1'),
      xray.scatterer('C2', site=(0.1, 0.2, 0.3), u=(1, 2, 3, 0, 0, 0)),
      xray.scatterer('C3'),
      )))
  r = constraints.ext.reparametrisation(xs.unit_cell())
  sc = xs.scatterers()
  sc[0].flags.set_grad_u_aniso(True)
  sc[2].flags.set_grad_u_aniso(True)

  u_0 = r.add(constraints.special_position_u_star_parameter,
              site_symmetry=xs.site_symmetry_table().get(0),
              scatterer=sc[0])
  u_iso_1 = r.add(constraints.u_iso_proportional_to_pivot_u_eq,
                pivot_u=u_0,
                multiplier=3,
                scatterer=sc[1])
  u_2 = r.add(constraints.independent_u_star_parameter, sc[2])
  u_iso_3 = r.add(constraints.u_iso_proportional_to_pivot_u_eq,
                pivot_u=u_2,
                multiplier=2,
                scatterer=sc[3])
  r.finalise()
  m = 3 + 6
  n = m + 6 + 1 + 1
  r.linearise()
  assert approx_equal(u_iso_1.value, 3, eps=1e-15)
  assert approx_equal(u_iso_3.value, 4, eps=1e-15)
  jt0 = sparse.matrix(m, n)
  for i in xrange(m): jt0[i, i] = 1
  p, q = u_0.argument(0).index, u_0.index
  jt0[p, q] = jt0[p+1, q+1] = jt0[p+2, q+2] = 1
  q = u_iso_1.index
  jt0[p, q] = jt0[p+1, q] = jt0[p+2, q] = 1
  p, q = u_2.index, u_iso_3.index
  jt0[p, q] = jt0[p+1, q] = jt0[p+2, q] = 2/3
  assert sparse.approx_equal(tolerance=1e-15)(r.jacobian_transpose, jt0)


def exercise(verbose):
  exercise_u_iso_proportional_to_pivot_u_eq()
  terminal_linear_ch_site_test_case(with_special_position_pivot=False).run()
  terminal_linear_ch_site_test_case(with_special_position_pivot=True).run()
  special_position_adp_test_case().run()
  c_oh_test_case(staggered=False, verbose=verbose).run()
  c_oh_test_case(staggered=True, verbose=verbose).run()
  exercise_symmetry_equivalent()

def run():
  libtbx.utils.show_times_at_exit()
  import sys
  exercise('--verbose' in sys.argv)

if __name__ == '__main__':
  run()
