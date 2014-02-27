from __future__ import division
from cctbx import xray
import scitbx.lbfgs
from libtbx import adopt_init_args
from scitbx.array_family import flex

class lbfgs(object):
  def __init__(self,
        fmodel,
        ncs_transformations_object=None,
        ncs_atom_selection = None,
        finite_grad_differences_test = False,
        max_iterations=100,
        sites = False,
        u_iso = False):
    """
    NCS constrained ADP and coordinates refinement
    """
    adopt_init_args(self, locals())
    assert [self.sites, self.u_iso].count(True) == 1
    self.fmodel.xray_structure.scatterers().flags_set_grads(state=False)
    self.x_target_functor = self.fmodel.target_functor()
    self.ncs_to_asu = ncs_transformations_object # XXX
    # xray structure of NCS chains for self.x
    ncs_fmodel_xrs = self.fmodel.xray_structure.select(ncs_atom_selection)
    if(self.sites):
      self.x = ncs_fmodel_xrs.sites_cart().as_double()
    if(self.u_iso):
      assert ncs_fmodel_xrs.scatterers().size() == \
        ncs_fmodel_xrs.use_u_iso().count(True)
      self.x = ncs_fmodel_xrs.extract_u_iso_or_u_equiv()
    if(self.sites):
      xray.set_scatterer_grad_flags(
        scatterers = self.fmodel.xray_structure.scatterers(),
        site       = True)
    if(self.u_iso):
      xray.set_scatterer_grad_flags(
        scatterers = self.fmodel.xray_structure.scatterers(),
        u_iso      = True)
    self.minimizer = scitbx.lbfgs.run(
      target_evaluator=self,
      termination_params=scitbx.lbfgs.termination_parameters(
        max_iterations=max_iterations),
      exception_handling_params=scitbx.lbfgs.exception_handling_parameters(
        ignore_line_search_failed_rounding_errors=True,
        ignore_line_search_failed_step_at_lower_bound=True,
        ignore_line_search_failed_maxfev=True))
    self.fmodel.xray_structure.tidy_us()
    self.fmodel.xray_structure.apply_symmetry_sites()
    self.fmodel.update_xray_structure(
      xray_structure = self.fmodel.xray_structure,
      update_f_calc  = True)

  def compute_functional_and_gradients(self, compute_gradients=True):
    self.update_fmodel()
    g = None
    tgx = self.x_target_functor(compute_gradients=compute_gradients)
    if(self.sites):
      if(compute_gradients):
        gx = flex.vec3_double(tgx.\
          gradients_wrt_atomic_parameters(site=True).packed())
        g = self.grads_asu_to_one_ncs(grad=gx).as_double()
    if(self.u_iso):
      if(compute_gradients):
        gx = tgx.gradients_wrt_atomic_parameters(u_iso=True)
        g = self.grads_asu_to_one_ncs(grad=gx).as_double()
    if(self.finite_grad_differences_test and compute_gradients):
      self.finite_difference_test(g)
    return tgx.target_work(), g

  def update_fmodel(self, x=None):
    if not x: x = self.x
    if(self.sites):
      x_asu = self.refinable_params_one_ncs_to_asu(x)
      self.fmodel.xray_structure.set_sites_cart(
        sites_cart = flex.vec3_double(x_asu))
    if(self.u_iso):
      x_asu = self.refinable_params_one_ncs_to_asu()
      self.fmodel.xray_structure.set_u_iso(values = x_asu)
    self.fmodel.update_xray_structure(
      xray_structure = self.fmodel.xray_structure,
      update_f_calc  = True)

  def refinable_params_one_ncs_to_asu(self, x=None):
    if(self.sites):
      assert x is not None
      rotations = self.ncs_to_asu.rotation_matrices
      translations =  self.ncs_to_asu.translation_vectors
      assert len(rotations)==len(translations)
      new_x = list(x)
      x = flex.vec3_double(x)
      for r,t in zip(rotations,translations):
        tmp_x = r.elems*x + t
        new_x += list(tmp_x.as_double())
      return flex.double(new_x)
    if(self.u_iso):
      return flex.double(list(self.x)*(self.ncs_to_asu.number_of_transforms+1))

  def grads_asu_to_one_ncs(self, grad):
    n = self.ncs_to_asu.number_of_transforms
    # gradients of the first NCS copy
    ncs_end = len(grad)//(n+1)
    assert ncs_end*(n+1)==len(grad)
    g_ave = grad[:ncs_end]
    for i in range(n):
      g = grad[ncs_end*(i+1):ncs_end*(i+2)]
      if(self.sites):
        rt = self.ncs_to_asu.rotation_matrices[i].transpose().elems
        g = rt*g
      g_ave += g
    g_ave = g_ave * (1./(n+1))
    if(self.sites): g_ave = flex.vec3_double(g_ave)
    assert type(grad)==type(g_ave)
    return g_ave

  def finite_difference_test(self, g):
    if(self.fmodel.r_work()>1.e-3):
      g = g.as_double()
      d = 1.e-3
      # find the index of the max gradient value
      i_g_max = flex.max_index(flex.abs(g))
      x_d = self.x
      # calc t(x+d)
      x_d[i_g_max] = self.x[i_g_max] + d
      self.update_fmodel(x = x_d)
      self.fmodel.update_xray_structure(update_f_calc=True)
      t1,_ = self.compute_functional_and_gradients(compute_gradients=False)
      # calc t(x-d)
      x_d[i_g_max] = self.x[i_g_max] - d
      self.update_fmodel(x = x_d)
      del x_d
      self.fmodel.update_xray_structure(update_f_calc=True)
      t2,_ = self.compute_functional_and_gradients(compute_gradients=False)
      # Return fmodel to the correct coordinates values
      self.update_fmodel(x = self.x)
      self.fmodel.update_xray_structure(update_f_calc=True)
      print g[i_g_max], (t1-t2)/(d*2), self.fmodel.r_work()