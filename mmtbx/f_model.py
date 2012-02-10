from __future__ import division

import mmtbx.f_model_info
import libtbx.load_env
from cctbx.array_family import flex
import math, sys, os
from cctbx import miller
from cctbx import adptbx
from libtbx import adopt_init_args
from mmtbx import bulk_solvent
from mmtbx import masks
from cctbx import xray
from mmtbx import max_lik
from mmtbx.max_lik import maxlik
from mmtbx.scaling.sigmaa_estimation import sigmaa_estimator
import mmtbx.bulk_solvent.bulk_solvent_and_scaling as bss
from cctbx import miller
from iotbx.cns.miller_array import crystal_symmetry_as_cns_comments
import cctbx.xray.structure_factors
from cctbx.array_family import flex
from stdlib import math
from cctbx import xray
from cctbx import adptbx
import boost.python
import mmtbx
from libtbx.math_utils import iround
from libtbx.utils import user_plus_sys_time, date_and_time, Sorry
from libtbx.str_utils import format_value, show_string
import libtbx.path
from cStringIO import StringIO
import iotbx.phil
from mmtbx.scaling import outlier_rejection
from mmtbx.scaling import absolute_scaling
from cctbx import sgtbx
from mmtbx import map_tools
from copy import deepcopy
from libtbx import group_args
import mmtbx.scaling.ta_alpha_beta_calc
import mmtbx.refinement.targets
from libtbx import Auto

ext = boost.python.import_ext("mmtbx_f_model_ext")

time_bulk_solvent_and_scale         = 0.0
time_mask                           = 0.0
time_f_calc                         = 0.0
time_alpha_beta                     = 0.0
time_target                         = 0.0
time_gradients_wrt_atomic_parameters = 0.0
time_fmodel_core_data               = 0.0
time_r_factors                      = 0.0
time_phase_errors                   = 0.0
time_foms                           = 0.0
time_show                           = 0.0

def show_times(out = None):
  if(out is None): out = sys.stdout
  total = time_mask                           +\
          time_f_calc                         +\
          time_alpha_beta                     +\
          time_target                         +\
          time_gradients_wrt_atomic_parameters +\
          time_fmodel_core_data               +\
          time_r_factors                      +\
          time_phase_errors                   +\
          time_foms
  print >> out, "  Micro-tasks:"
  print >> out, "    mask                            = %-7.2f" % (time_mask)
  print >> out, "    f_calc                          = %-7.2f" % time_f_calc
  print >> out, "    alpha_beta                      = %-7.2f" % time_alpha_beta
  print >> out, "    target                          = %-7.2f" % time_target
  print >> out, "    gradients_wrt_atomic_parameters = %-7.2f" % \
    time_gradients_wrt_atomic_parameters
  print >> out, "    fmodel                         = %-7.2f" % time_fmodel_core_data
  print >> out, "    r_factors                      = %-7.2f" % time_r_factors
  print >> out, "    phase_errors                   = %-7.2f" % time_phase_errors
  print >> out, "    foms                           = %-7.2f" % time_foms
  print >> out, "    TOTAL for micro-tasks          = %-7.2f" % total
  return total

class active_arrays(object):

  def __init__(self,
               core,
               f_obs,
               r_free_flags,
               hl_coeffs=None,
               core_twin=None,
               twin_fraction=None):
    adopt_init_args(self, locals())
    self.work_sel = ~self.r_free_flags.data()
    self.free_sel = self.r_free_flags.data()
    if(self.free_sel.all_ne(True)): self.free_sel = ~self.free_sel
    self.d_spacings = self.f_obs.d_spacings().data()
    self.d_spacings_work = self.d_spacings.select(self.work_sel)
    self.d_spacings_free = self.d_spacings.select(self.free_sel)
    self._update_derived_arrays()

  def _update_derived_arrays(self):
    if(self.core_twin is None):
      self.f_model = self.core.f_model
    else:
      self.f_model = self.f_obs.array(data =
        mmtbx.utils.apply_twin_fraction(
          amplitude_data_part_one = flex.abs(self.core.f_model.data()),
          amplitude_data_part_two = flex.abs(self.core_twin.f_model.data()),
          twin_fraction           = self.twin_fraction))
    self.f_model_work = self.f_model.select(self.work_sel)
    self.f_model_free = self.f_model.select(self.free_sel)
    self.fb_cart_work = self.core.data.f_aniso.select(self.work_sel) #XXX no-twin
    self.f_obs_work = self.f_obs.select(self.work_sel)
    self.f_obs_free = self.f_obs.select(self.free_sel)

  def update_core(self, core=None, core_twin=None, twin_fraction=None):
    if(core is not None): self.core = core
    if(core_twin is not None): self.core_twin = core_twin
    if(twin_fraction is not None): self.twin_fraction = twin_fraction
    if([core, core_twin].count(None)<2): self._update_derived_arrays()

class core(object):
  def __init__(self,
               f_calc  = None,
               f_mask  = None,
               k_sols  = [0.],
               b_sol   = 0.,
               f_part1 = None,
               f_part2 = None,
               u_star  = [0,0,0,0,0,0],
               fmodel  = None,
               ss      = None):
    if(fmodel is not None):
      self.f_calc  = fmodel.f_calc()
      self.f_mask  = fmodel.shell_f_masks()
      self.k_sols  = fmodel.k_sols()
      self.b_sol   = fmodel.b_sol()
      self.f_part1 = fmodel.f_part1()
      self.f_part2 = fmodel.f_part2()
      self.u_star  = fmodel.u_star()
    else: adopt_init_args(self, locals())
    if (self.u_star is None): self.u_star = [0,0,0,0,0,0] # XXX
    if not ((type(self.k_sols) is list) or (self.k_sols is None)):
      assert (type(self.k_sols) is float) or \
        (type(self.k_sols) is int), type(self.k_sols)
      self.k_sols = [self.k_sols]
    assert len(self.k_sols) >= 1
    typfm = type(self.f_mask)
    if( not((typfm is list) or (typfm is None)) ):
      self.f_mask = [self.f_mask]
    assert len(self.k_sols) == len(self.f_mask), \
        "VALS: %d %d"%(len(self.k_sols),len(self.f_mask))
    self.ss = ss
    if(self.ss is None):
      self.ss = 1./flex.pow2(self.f_calc.d_spacings().data()) / 4.
    fmdata = []
    for fm in self.f_mask:
      fmdata.append(fm.data())
    if(self.f_part1 is None):
      self.f_part1 = self.f_calc.customized_copy(data =
        flex.complex_double(self.f_calc.data().size(), 0))
    if(self.f_part2 is None):
      self.f_part2 = self.f_calc.customized_copy(data =
        flex.complex_double(self.f_calc.data().size(), 0))
    self.data = ext.core(
      f_calc        = self.f_calc.data(),
      shell_f_masks = fmdata,
      k_sols        = self.k_sols,
      b_sol         = self.b_sol,
      f_part1       = self.f_part1.data(),
      f_part2       = self.f_part2.data(),
      u_star        = self.u_star,
      hkl           = self.f_calc.indices(),
      uc            = self.f_calc.unit_cell(),
      ss            = self.ss)
    self.uc = self.data.uc
    self.hkl = self.data.hkl
    self.f_model = miller.array(miller_set=self.f_calc, data=self.data.f_model)

  def update(self,
             f_calc  = None,
             f_mask  = None,
             k_sols  = None,
             b_sol   = None,
             f_part1 = None,
             f_part2 = None,
             u_star  = None):
    if(f_calc  is not None): self.f_calc  = f_calc
    if(f_mask  is not None): self.f_mask  = f_mask
    if(k_sols  is not None): self.k_sols  = k_sols
    if(b_sol   is not None): self.b_sol   = b_sol
    if(f_part1 is not None): self.f_part1 = f_part1
    if(f_part2 is not None): self.f_part2 = f_part2
    if(u_star  is not None): self.u_star  = u_star
    if([f_calc,f_mask,k_sols,b_sol,f_part1,f_part2,u_star].count(None)!=7):
      self.__init__(
        f_calc  = self.f_calc,
        f_mask  = self.f_mask,
        k_sols  = self.k_sols,
        b_sol   = self.b_sol,
        f_part1 = self.f_part1,
        f_part2 = self.f_part2,
        u_star  = self.u_star,
        ss      = self.ss)
    return self

  def __getstate__(self):
    return {"args": (
      self.f_calc,
      self.f_mask,
      self.k_sols,
      self.b_sol,
      self.f_part1,
      self.f_part2,
      self.u_star,
      self.fmodel)}

  def __setstate__(self, state):
    assert len(state) == 1
    self.__init__(*state["args"])

class manager_mixin(object):

  def target_w(self):
    global time_target
    timer = user_plus_sys_time()
    result = self.target_functor()(compute_gradients=False).target_work()
    time_target += timer.elapsed()
    return result

  def target_t(self):
    global time_target
    timer = user_plus_sys_time()
    result = self.target_functor()(compute_gradients=False).target_test()
    time_target += timer.elapsed()
    return result

  def one_time_gradients_wrt_atomic_parameters(self, **keyword_args):
    return self.target_functor()(compute_gradients=True) \
      .gradients_wrt_atomic_parameters(**keyword_args)

sf_and_grads_accuracy_master_params = iotbx.phil.parse("""\
  algorithm = *fft direct
    .type = choice
  cos_sin_table = False
    .type = bool
  grid_resolution_factor=1/3.
    .type = float
  quality_factor = None
    .type = float
  u_base = None
    .type = float
  b_base = None
    .type = float
  wing_cutoff = None
    .type = float
  exp_table_one_over_step_size = None
    .type = float
""")

alpha_beta_master_params = iotbx.phil.parse("""\
  include scope mmtbx.max_lik.maxlik.alpha_beta_params
  sigmaa_estimator
    .expert_level=2
  {
    include scope mmtbx.scaling.sigmaa_estimation.sigmaa_estimator_params
  }
""", process_includes=True)

def _scale_helper(num, den, selection=None, num_num=False):
  if (selection is not None):
    num = num.select(selection)
    den = den.select(selection)
  if (den.size() == 0):
    raise RuntimeError("No data for scale calculation.")
  denom = flex.sum(den*den)
  if (denom == 0):
    raise RuntimeError("Zero denominator in scale calculation.")
  if (num_num): return flex.sum(num*num) / denom
  return flex.sum(num*den) / denom

class manager(manager_mixin):

  def __init__(self,
         f_obs                        = None,
         r_free_flags                 = None,
         f_mask                       = None,
         f_part1                      = None,
         f_calc                       = None,
         abcd                         = None,
         b_cart                       = [0.,0.,0.,0.,0.,0.],
         k_sol                        = None, # TODO rename to k_sols
         b_sol                        = 0.0,
         sf_and_grads_accuracy_params = None,
         target_name                  = "ml",
         alpha_beta_params            = None,
         xray_structure               = None,
         mask_params                  = None,
         use_f_model_scaled           = False,
         mask_manager                 = None,
         twin_law                     = None,
         twin_fraction                = 0,
         max_number_of_bins           = 30,
         _target_memory               = None):
    if( k_sol is None ):
      k_sol = [0.]
    if( type(k_sol) is not list ):
      k_sol = [k_sol]
    if(twin_law is not None): target_name = "twin_lsq_f"
    self.active_arrays = None
    self.twin_law = twin_law
    self.twin_law_str = twin_law
    self.twin_fraction = twin_fraction
    self.twin_set = self._set_twin_set(miller_array = f_obs)
    if(f_part1 is None): # XXX ???
      f_part1 = f_obs.array(
        data = flex.complex_double(f_obs.data().size(),0+0j))
    if(r_free_flags is None):
      r_free_flags = f_obs.array(
        data = flex.bool(f_obs.data().size(),False))
    if abcd is not None and not abcd.indices().all_eq(f_obs.indices()):
        abcd = abcd.complete_array(
          new_data_value=(0,0,0,0), d_min=f_obs.d_min()).common_set(f_obs)
    self.passive_arrays = group_args(f_obs = f_obs, r_free_flags = r_free_flags,
      hl_coeffs = abcd, f_part1 = f_part1)
    if(sf_and_grads_accuracy_params is None):
      sf_and_grads_accuracy_params = sf_and_grads_accuracy_master_params.extract()
    if(alpha_beta_params is None):
      alpha_beta_params = alpha_beta_master_params.extract()
    self.twin = False
    assert f_obs is not None
    assert f_obs.is_real_array()
    assert f_obs.is_unique_set_under_symmetry()
    assert r_free_flags.is_unique_set_under_symmetry()
    if(twin_law is None):
      # twin mate of mapped-to-asu does not have to obey this!
      assert f_obs.is_in_asu()
      assert r_free_flags.is_in_asu()
    self.sfg_params = sf_and_grads_accuracy_params
    self.alpha_beta_params = alpha_beta_params
    self.xray_structure    = xray_structure
    self.use_f_model_scaled= use_f_model_scaled
    self.max_number_of_bins = max_number_of_bins
    if(mask_params is not None):
       self.mask_params = mask_params
    else:
       self.mask_params = mmtbx.masks.mask_master_params.extract()
    self.mask_manager = mask_manager
    if(self.mask_manager is None):
      self.mask_manager = masks.manager(
        miller_array      = f_obs,
        miller_array_twin = self.twin_set,
        mask_params       = self.mask_params)
    if(r_free_flags is not None):
      assert r_free_flags.indices().all_eq(f_obs.indices())
    self.uc = f_obs.unit_cell()
    if(self.xray_structure is None):
      assert [f_calc, f_mask].count(None) == 0
      if not type(f_mask) is list:
        f_mask = [f_mask]
      assert f_calc.is_complex_array()
      assert f_calc.data().size() <= f_obs.data().size()
      for fm in f_mask:
        assert fm.is_complex_array()
        assert fm.data().size() <= f_obs.data().size()
        assert fm.data().size() == f_calc.data().size()
      f_calc_twin = None
      f_mask_twin = None
    else:
      if(f_calc is None): f_calc = self.compute_f_calc(miller_array=f_obs)
      f_calc_twin = None
      if(self.twin_set is not None):
        f_calc_twin = self.compute_f_calc(miller_array = self.twin_set)
      if(f_mask is None):
        f_mask = self.mask_manager.shell_f_masks(
          xray_structure = self.xray_structure,
          force_update       = True)
        if( len(k_sol) != len(f_mask) ):
          assert len(k_sol) == 1
          assert len(f_mask) > 1
          k_sol.extend( [k_sol[0]]*(len(f_mask)-1) )
          assert len(k_sol) == len(f_mask)
      f_mask_twin = self.mask_manager.shell_f_masks_twin()
    self.update_core(
      f_calc      = f_calc,
      f_mask      = f_mask,
      f_calc_twin = f_calc_twin,
      f_mask_twin = f_mask_twin,
      b_cart      = b_cart,
      k_sols      = k_sol,
      b_sol       = b_sol,
      f_part1     = f_part1.common_set(f_calc))
    assert len(b_cart) == 6
    self.set_target_name(target_name=target_name)
    self._target_memory = _target_memory
    self._structure_factor_gradients_w = None
    self._wilson_b = None

  def __getstate__(self):
    self._structure_factor_gradients_w = None
    return (self.__dict__,)

  def __setstate__(self, state):
    assert len(state) == 1
    self.__dict__.update(state[0])

  def _get_structure_factor_gradients_w(self):
    if (self._structure_factor_gradients_w is None):
      self._structure_factor_gradients_w \
        = cctbx.xray.structure_factors.gradients(
         miller_set                   = self.f_obs_work(),
         cos_sin_table                = self.sfg_params.cos_sin_table,
         grid_resolution_factor       = self.sfg_params.grid_resolution_factor,
         quality_factor               = self.sfg_params.quality_factor,
         u_base                       = self.sfg_params.u_base,
         b_base                       = self.sfg_params.b_base,
         wing_cutoff                  = self.sfg_params.wing_cutoff,
         exp_table_one_over_step_size =
                                  self.sfg_params.exp_table_one_over_step_size)
    return self._structure_factor_gradients_w

  structure_factor_gradients_w = property(_get_structure_factor_gradients_w)

  def _set_twin_set(self, miller_array):
    result = None
    if(self.twin_law is not None):
      twin_law_xyz = sgtbx.rt_mx(symbol=self.twin_law, r_den=12, t_den=144)
      twin_law_matrix = twin_law_xyz.as_double_array()[0:9]
      twin_mi = mmtbx.utils.create_twin_mate(
        miller_indices  = miller_array.indices(),
        twin_law_matrix = twin_law_matrix)
      result = miller_array.customized_copy(
        indices = twin_mi,
        crystal_symmetry = miller_array.crystal_symmetry())
    return result

  def compute_f_calc(self, miller_array = None):
    if(miller_array is None): miller_array = self.f_obs()
    p = self.sfg_params
    if(miller_array.indices().size()==0):
      raise RuntimeError("Empty miller_array.")
    return miller_array.structure_factors_from_scatterers(
      xray_structure               = self.xray_structure,
      algorithm                    = p.algorithm,
      cos_sin_table                = p.cos_sin_table,
      grid_resolution_factor       = p.grid_resolution_factor,
      quality_factor               = p.quality_factor,
      u_base                       = p.u_base,
      b_base                       = p.b_base,
      wing_cutoff                  = p.wing_cutoff,
      exp_table_one_over_step_size = p.exp_table_one_over_step_size).f_calc()

  def update_twin_fraction(self): # XXX
    if(self.twin_set is None): return
    tfb = self.twin_fraction
    r_work = self.r_work()
    if(len(self.k_sols())>1):
      raise RuntimeError("Not implemented")
    ks_best = self.k_sols()[0] # XXX one shell assumed
    bs_best = self.b_sol()
    if(ks_best == 0.0):
      for ks in [max(0,self.k_sol(0)),0.3,0.5]: # one shell assumed
        for bs in [max(0,self.b_sol()),50.,80.]:
          twin_fraction = 0.0
          tf_best = tfb
          while twin_fraction <= 1.0:
            r_work_= abs(bulk_solvent.r_factor(
              self.f_obs_work().data(),
              self.active_arrays.core.data.f_model.select(self.active_arrays.work_sel),
              self.active_arrays.core_twin.data.f_model.select(self.active_arrays.work_sel),
              twin_fraction))
            if(r_work_ < r_work):
              r_work = r_work_
              tf_best = twin_fraction
            twin_fraction += 0.01
          self.update(twin_fraction = tf_best, k_sols=[ks], b_sol=bs)
          r_work_= abs(bulk_solvent.r_factor(
            self.f_obs_work().data(),
            self.active_arrays.core.data.f_model.select(self.active_arrays.work_sel),
            self.active_arrays.core_twin.data.f_model.select(self.active_arrays.work_sel),
            self.twin_fraction))
          if(r_work_ < r_work):
            r_work = r_work_
            ks_best = ks
            bs_best = bs
            tfb = tf_best
      if(ks_best == 0.0): bs_best = 0.0
      if(bs_best == 0.0): ks_best = 0.0
      self.update(k_sols = [ks_best], b_sol = bs_best, twin_fraction = tfb) # XXX one shell assumed
    r_work = self.r_work()
    twin_fraction = 0.0
    tf_best = self.twin_fraction
    while twin_fraction <= 1.0:
      r_work_= abs(bulk_solvent.r_factor(
        self.f_obs_work().data(),
        self.active_arrays.core.data.f_model.select(self.active_arrays.work_sel),
        self.active_arrays.core_twin.data.f_model.select(self.active_arrays.work_sel),
        twin_fraction))
      if(r_work_ < r_work):
        r_work = r_work_
        tf_best = twin_fraction
      twin_fraction += 0.001
    self.update(twin_fraction = tf_best)

  def core_data_work(self): # XXX WHICH one : twin? non-twin?
    return core(fmodel = self.select(self.active_arrays.work_sel))

  def outlier_selection(self, show = False, log = None):
    if(log is None): log = sys.stdout
    n_free = self.r_free_flags().data().count(True)
    result = outlier_rejection.outlier_manager(
      miller_obs   = self.passive_arrays.f_obs,
      r_free_flags = self.passive_arrays.r_free_flags,
      out          = "silent")
    s1 = result.basic_wilson_outliers().data()
    s2 = result.extreme_wilson_outliers().data()
    s3 = result.beamstop_shadow_outliers().data()
    if(n_free > 0):
      f_masks = self.mask_manager.shell_f_masks()
      if(f_masks is None): f_masks = self.shell_f_masks()
      for fm in f_masks:
        assert fm.data().size() == self.passive_arrays.f_obs.data().size()
      f_part1 = self.passive_arrays.f_part1
      #if(self.k_part()==0):
      #  f_mask = self.mask_manager.f_mask()
      #  if(f_mask is None): f_mask = self.f_mask()
      #  assert f_mask.data().size() == self.passive_arrays.f_obs.data().size()
      #  f_part_base = passive_arrays.f_part_base
      #else:
      #  nuo = self.compute_f_part()
      #  f_mask = nuo.f_mask_new
      #  f_part_base = passive_arrays.f_part_base
      if(self.xray_structure is not None):
        core_ = core(
          f_calc  = self.compute_f_calc(miller_array = f_masks[0]), #TODO why f_mask
          f_mask  = f_masks,
          k_sols  = self.k_sols(),
          b_sol   = self.b_sol(),
          f_part1 = f_part1, #XXX f_part2 ?
          u_star  = self.u_star())
        f_model = core_.f_model
      else:
        f_model = self.f_model()
      s4 = result.model_based_outliers(f_model = f_model).data()
      result = s1 & s2 & s3 & s4
    else: result = s1 & s2 & s3
    if(show):
      print >> log
      print >> log, "basic_wilson_outliers    =", s1.count(False)
      print >> log, "extreme_wilson_outliers  =", s2.count(False)
      print >> log, "beamstop_shadow_outliers =", s3.count(False)
      if(n_free > 0):
        print >> log, "model_based_outliers     =", s4.count(False)
      print >> log, "total                    =", result.count(False)
    return result

  def remove_outliers(self, show = False, log = None):
    if(log is None): log = sys.stdout
    if(show):
      print >> log, "Distribution of F-obs values:"
      show_histogram(data = self.passive_arrays.f_obs.data(), n_slots = 10, log = log)
    o_sel = self.outlier_selection(show = show, log = log)
    if(o_sel.count(False) > 0):
      assert self.twin_set is None #XXX twinning is not supported yet
      assert self.active_arrays.core_twin is None
      new_f_obs = self.passive_arrays.f_obs.select(o_sel)
      new_r_free_flags = self.passive_arrays.r_free_flags.select(o_sel)
      new_hl_coeffs = self.passive_arrays.hl_coeffs
      if(new_hl_coeffs is not None):
        new_hl_coeffs = self.passive_arrays.hl_coeffs.select(o_sel)
      #
      f_part1 = self.passive_arrays.f_part1.common_set(new_f_obs)
      f_masks = []
      for fm in self.mask_manager.shell_f_masks():
        f_masks.append( fm.common_set(new_f_obs) )
      #if(self.k_part()==0):
      #  f_mask = self.mask_manager.f_mask().common_set(new_f_obs)
      #  f_part_base = new_f_obs.array(
      #    data = flex.complex_double(new_f_obs.data().size(),0+0j)) # XXX
      #else:
      #  nuo = self.compute_f_part()
      #  f_mask = nuo.f_mask_new.common_set(new_f_obs)
      #  f_part_base = nuo.f_part.common_set(new_f_obs)
      core_ = core(
        f_calc  = self.compute_f_calc(miller_array = new_f_obs),
        f_mask  = f_masks,
        k_sols  = self.k_sols(),
        b_sol   = self.b_sol(),
        f_part1 = f_part1, #XXX f_part2
        u_star  = self.u_star())
      self.active_arrays = active_arrays(
        core          = core_,
        core_twin     = None, #XXX twinning is not supported yet
        f_obs         = new_f_obs,
        r_free_flags  = new_r_free_flags,
        hl_coeffs     = new_hl_coeffs,
        twin_fraction = self.twin_fraction)
      if(show):
        print >> log, "\nDistribution of active F-obs values after outliers rejection:"
        show_histogram(data=self.active_arrays.f_obs.data(),n_slots=10,log=log)
    return self

  def wilson_b(self, force_update = False):
    if(self.xray_structure is not None and (self._wilson_b is None or
       force_update)):
      result = absolute_scaling.ml_iso_absolute_scaling(
        miller_array = self.f_obs(),
        n_residues   = self.xray_structure.scatterers().size()/8).b_wilson
      self._wilson_b = result
    else: result = self._wilson_b
    return result


  def deep_copy(self):
    return self.select()

  def select(self, selection=None):
    sel_passive = flex.bool(self.passive_arrays.f_obs.data().size(), True)
    if(selection is None):
      sel_active = flex.bool(self.f_obs().data().size(), True)
    else:
      sel_active = selection
    if(self.hl_coeffs() is not None):
      new_hl_coeffs = self.passive_arrays.hl_coeffs.select(selection=sel_passive)
    else:
      new_hl_coeffs = None
    if(self.mask_manager is not None):
      new_mask_manager = self.mask_manager.select(selection = sel_passive) # XXX
    else:
      new_mask_manager = None
    xrs = self.xray_structure
    if(xrs is not None): xrs = self.xray_structure.deep_copy_scatterers()
    fmsks=[]
    for fm in self.shell_f_masks():
      fmsks.append(fm.select(selection=sel_active))
    result = manager(
      f_obs                        = self.passive_arrays.f_obs.select(selection=sel_passive),
      r_free_flags                 = self.passive_arrays.r_free_flags.select(selection=sel_passive),
      b_cart                       = tuple(self.b_cart()),
      k_sol                        = self.k_sols(),
      b_sol                        = self.b_sol(),
      f_part1                      = self.passive_arrays.f_part1.select(selection=sel_passive),
      sf_and_grads_accuracy_params = deepcopy(self.sfg_params),
      target_name                  = self.target_name,
      abcd                         = new_hl_coeffs,
      alpha_beta_params            = deepcopy(self.alpha_beta_params),
      xray_structure               = xrs,
      f_calc                       = self.f_calc().select(selection=sel_active),
      f_mask                       = fmsks,
      mask_params                  = deepcopy(self.mask_params),
      mask_manager                 = new_mask_manager,
      twin_law                     = self.twin_law,
      twin_fraction                = self.twin_fraction,
      max_number_of_bins           = self.max_number_of_bins,
      _target_memory               = self._target_memory)
    result.twin = self.twin
    result.twin_law_str = self.twin_law_str
    return result

  def resolution_filter(self,
        d_max=0,
        d_min=0):
    if(d_min is None): d_min = 0
    if(d_max is None): d_max = 0
    return self.select(
      selection=self.f_obs().resolution_filter_selection(d_max=d_max,d_min=d_min))

  def apply_back_b_iso(self):
    if(self.xray_structure is None): return
    b_min = min(self.b_sol(),
      self.xray_structure.min_u_cart_eigenvalue()*adptbx.u_as_b(1.))
    if(b_min < 0):
      self.xray_structure.tidy_us()
    b_iso = self.b_iso()
    b_test = b_min+b_iso
    if(b_test < 0.0): b_adj = b_iso + abs(b_test) + 0.001
    else: b_adj = b_iso
    if(abs(b_adj) <= 300.0):
      b_cart = self.b_cart()
      b_cart_new = [b_cart[0]-b_adj,b_cart[1]-b_adj,b_cart[2]-b_adj,
                    b_cart[3],      b_cart[4],      b_cart[5]]
      self.update(b_cart = b_cart_new)
      self.update(b_sol = self.b_sol() + b_adj)
      self.xray_structure.shift_us(b_shift = b_adj)
      b_min = min(self.b_sol(),
        self.xray_structure.min_u_cart_eigenvalue()*adptbx.u_as_b(1.))
      assert b_min >= 0.0
      self.xray_structure.tidy_us()
      self.update_xray_structure(
        xray_structure = self.xray_structure,
        update_f_calc  = True,
        update_f_mask  = False)

  def update_xray_structure(self,
                            xray_structure      = None,
                            update_f_calc       = False,
                            update_f_mask       = False,
                            force_update_f_mask = False):
    if(xray_structure is not None):
      self.xray_structure = xray_structure
    if(self.active_arrays.core is None or
       (self.twin_set is not None)):
      force_update_f_mask = True
    f_calc = None
    f_calc_twin = None
    if(update_f_calc):
      f_calc = self.compute_f_calc()
      if(self.twin_law is not None):
        f_calc_twin = self.compute_f_calc(miller_array = self.twin_set)
    f_masks = None
    f_mask_twin = None
    if(update_f_mask):
      mngmsks = self.mask_manager.shell_f_masks(
        xray_structure = self.xray_structure,
        force_update   = force_update_f_mask)
      curfmsks = self.shell_f_masks()
      if(mngmsks is not None):
        f_masks = mngmsks[:] # copy
      if(mngmsks is not None and curfmsks is not None):
        assert len(curfmsks) == len(mngmsks)
        for i in range(len(curfmsks)):
          if( mngmsks[i].data().size() != curfmsks[i].data().size() ):
            f_masks[i] = mngmsks[i].common_set(curfmsks[i])
      f_mask_twin = self.mask_manager.shell_f_masks_twin()
    if([f_calc, f_masks, f_calc_twin, f_mask_twin].count(None) == 4):
      set_core_flag = False
    else: set_core_flag = True
    if(f_calc is None and self.active_arrays.core is not None):
      f_calc = self.f_calc()
    if(f_masks is None and self.active_arrays.core is not None):
      f_masks = self.shell_f_masks()
    if(set_core_flag):
      self.update_core(
        f_calc      = f_calc,
        f_mask      = f_masks,
        f_calc_twin = f_calc_twin,
        f_mask_twin = f_mask_twin)

  def update_core(self, f_calc      = None,
                        f_mask      = None,
                        f_calc_twin = None,
                        f_mask_twin = None,
                        b_cart      = None,
                        u_star      = None,
                        k_sols      = None,
                        b_sol       = None,
                        f_part1     = None,
                        f_part2     = None):
    if(b_cart is not None and list(b_cart).count(None) != 6):# XXX
      u_star = adptbx.u_cart_as_u_star(
        self.f_obs().unit_cell(),adptbx.b_as_u(b_cart))
    if(self.twin_set is not None):
      f_part1_twin = self.twin_set.array(
        data = flex.complex_double(self.twin_set.data().size(),0+0j)) # XXX
    core_ = None
    core_twin_ = None
    if(self.active_arrays is None):
      core_ = core(
        f_calc  = f_calc,
        f_mask  = f_mask,
        k_sols  = k_sols,
        b_sol   = b_sol,
        f_part1 = f_part1,
        f_part2 = f_part2,
        u_star  = u_star)
      if(self.twin_set is not None):
        core_twin_ = core(
          f_calc      = self.compute_f_calc(miller_array = self.twin_set),
          f_mask      = self.mask_manager.shell_f_masks_twin(),
          u_star      = u_star,
          k_sols      = k_sols,
          b_sol       = b_sol,
          f_part1     = f_part1_twin, # XXX
          f_part2     = f_part2)# XXX TWIN ?
      f_obs = self.passive_arrays.f_obs
      r_free_flags = self.passive_arrays.r_free_flags
      hl_coeffs = self.passive_arrays.hl_coeffs
      if(f_obs.data().size() != core_.data.f_model.size()):
        f_obs = f_obs.common_set(core_.f_model)
        r_free_flags = r_free_flags.common_set(core_.f_model)
        if(hl_coeffs is not None):
          hl_coeffs = hl_coeffs.common_set(core_.f_model)
      self.active_arrays = active_arrays(
        core          = core_,
        core_twin     = core_twin_,
        f_obs         = f_obs,
        r_free_flags  = r_free_flags,
        hl_coeffs     = hl_coeffs,
        twin_fraction = self.twin_fraction)
    else:
      core_ = self.active_arrays.core.update(
        f_calc      = f_calc,
        f_mask      = f_mask,
        k_sols      = k_sols,
        b_sol       = b_sol,
        u_star      = u_star,
        f_part1     = f_part1,
        f_part2     = f_part2)
      if(self.twin_set is not None):
        core_twin_ = self.active_arrays.core_twin.update(
          f_calc  = f_calc_twin,
          f_mask  = f_mask_twin,
          u_star  = u_star,
          k_sols  = k_sols,
          b_sol   = b_sol,
          f_part1 = f_part1_twin, # XXX
          f_part2 = f_part2)#, # XXX TWIN ?
      self.active_arrays.update_core(core = core_, core_twin = core_twin_,
        twin_fraction = self.twin_fraction)

  def show_mask_optimization_statistics(self, prefix="", out=None):
    if(out is None): return
    line_len = len("|-"+"|"+prefix)
    fill_len = 80-line_len-1
    print >> out, "|-"+prefix+"-"*(fill_len)+"|"
    print >> out, \
      "| Solvent (probe) radius= %4.2f Shrink truncation radius= %4.2f%s|"%(
      self.mask_params.solvent_radius,
      self.mask_params.shrink_truncation_radius," "*17)
    print >> out, \
      "| all data:                         500 lowest resolution reflections:        |"
    rwl = self.r_work_low()
    fmtl = "| r_work= %s r_free= %s     r_work= %s (resolution: %s-%s A)"%(
      format_value(format="%6.4f", value=self.r_work()).strip(),
      format_value(format="%6.4f", value=self.r_free()).strip(),
      format_value(format="%6.4f", value=rwl.r_work).strip(),
      format_value(format="%6.2f", value=rwl.d_min).strip(),
      format_value(format="%7.2f", value=rwl.d_max).strip())
    pad = " "*(78-len(fmtl))
    print >> out, fmtl + pad + "|"
    print >> out, "|"+"-"*77+"|"
    print >> out

  def optimize_mask(self, params = None, thorough=False, out = None,
      nproc=1):
    if( len(self.k_sols()) != 1 ):
      return False
    if (nproc is None) : nproc = 1
    if(self.k_sols().count(0)>0): return False
    rw_ = self.r_work()
    rf_ = self.r_free()
    r_solv_   = self.mask_params.solvent_radius
    r_shrink_ = self.mask_params.shrink_truncation_radius
    k_sols    = self.k_sols()
    b_sol     = self.b_sol()
    b_cart    = self.b_cart()
    self.show_mask_optimization_statistics(prefix="Mask optimization: start",
      out = out)
    hydrogens_present = False
    if(self.xray_structure is not None):
      if(self.xray_structure.hd_selection().count(True) > 0):
        hydrogens_present = True
    def r_solv_shrink(a,b,r_solv_range):
      r_shrinks = []
      for r_solv in r_solv_range:
        r_shrinks.append(a*r_solv - b)
      return r_shrinks, r_solv_range
    if(thorough):
      trial_range = [0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0,1.1,1.2,1.3,1.4]
      r_shrinks = []
      r_solvs = []
      for tr1 in trial_range:
        for tr2 in trial_range:
          r_shrinks.append(tr1)
          r_solvs.append(tr2)
      r_solv = trial_range[:]
      r_shrink = trial_range[:]
    else:
      r_shrinks, r_solvs = r_solv_shrink(a=1.2821, b=0.554,
        r_solv_range=[0.8,0.9,1.0,1.1,1.2,1.3,1.4])
    trial_params = zip(r_solvs, r_shrinks)
    parallel = False
    mask_results = []
    if (nproc is Auto) or (nproc > 1) :
      parallel = True
      from libtbx import easy_mp
      stdout_and_results = easy_mp.pool_map(
        processes=nproc,
        fixed_func=self.try_mask_params,
        args=trial_params,
        func_wrapper="buffer_stdout_stderr") # XXX safer for phenix GUI
      mask_results = [ r for so, r in stdout_and_results ]
    else :
      for r_solv, r_shrink in trial_params :
        result = self.try_mask_params((r_solv, r_shrink))
        result.show(out=out)
        mask_results.append(result)
    for result in mask_results :
      if (parallel) :
        result.show(out=out)
      if(result.r_work < rw_):
        rw_       = result.r_work
        rf_       = result.r_free
        r_solv_   = result.r_solv
        r_shrink_ = result.r_shrink
    if(out is not None): print >> out
    self.mask_params.solvent_radius = r_solv_
    self.mask_params.shrink_truncation_radius = r_shrink_
    self.mask_manager.mask_params = self.mask_params
    self.update_xray_structure(
      xray_structure      = self.xray_structure,
      update_f_calc       = False,
      update_f_mask       = True,
      force_update_f_mask = True)
    self.show_mask_optimization_statistics(prefix="Mask optimization: final",
      out = out)
    return True

  # XXX parallel routine
  def try_mask_params (self, args) :
    r_solv, r_shrink = args
    self.mask_params.solvent_radius = r_solv
    self.mask_params.shrink_truncation_radius = r_shrink
    self.mask_manager.mask_params = self.mask_params
    self.update_xray_structure(
      xray_structure      = self.xray_structure,
      update_f_calc       = False,
      update_f_mask       = True,
      force_update_f_mask = True)
    k_sols    = self.k_sols()
    b_sol     = self.b_sol()
    b_cart    = self.b_cart()
    self.update(k_sols = k_sols, b_sol = b_sol, b_cart = b_cart)
    return mask_result(
      r_solv=r_solv,
      r_shrink=r_shrink,
      r_work=self.r_work(),
      r_free=self.r_free(),
      r_work_low=self.r_work_low().r_work)

  def check_f_mask_all_zero(self):
    # TODO: mrt is this the required logic?
    result = False
    ksols = self.k_sols()[:] # copy
    fmsks = self.shell_f_masks()
    results = [False]*len(ksols)
    for i in range(len(ksols)):
      if(flex.abs(fmsks[i].data()).all_eq(0)):
        ksols[i] = 0
        results[i] = True
    if results.count(True)!=0:
      bsol = self.b_sol()
      if( results.count(False)==0 ):
        bsol = 0
        result = True
      self.update(k_sols = ksols, b_sol = bsol)
    return result

  def compute_f_part1(self, params, log = None):
    phenix_masks = None
    if(not libtbx.env.has_module(name="solve_resolve")):
      raise Sorry("solve_resolve not installed or not configured.")
    else:
      import solve_resolve.masks as phenix_masks
    if(log is None): log = sys.stdout
    return phenix_masks.nu(fmodel = self, params = params)

  def update_f_hydrogens(self, log=None):
    if(self.xray_structure is None): return None
    def f_k_exp_scaled(k,b,ss,f):
      return f.customized_copy(data = k*flex.exp(-b*ss)*f.data())
    hds = self.xray_structure.hd_selection()
    if(hds.count(True)==0): return None
    xrsh = self.xray_structure.select(selection = hds)
    xrsh.set_occupancies(value=1)
    fh = self.f_obs().structure_factors_from_scatterers(
      xray_structure = xrsh).f_calc()
    b_min = int(flex.min(xrsh.extract_u_iso_or_u_equiv()*adptbx.u_as_b(1)))
    ss = self.active_arrays.core.ss
    kbest = 0
    bbest = 0
    self.update_core(f_part2 =
      fh.customized_copy(data=flex.complex_double(fh.data().size(),0)))
    rws = self.r_work()
    b_range = [0]+range(-b_min,b_min+50,1)
    k_range = [i/10. for i in xrange(11)]
    for b in b_range:
      for k in k_range:
        fh_kb = f_k_exp_scaled(k = k, b = b, ss = ss, f = fh.deep_copy())
        self.update_core(f_part2 = fh_kb)
        rw = self.r_work()
        if(rw < rws):
          rws = rw
          kbest=k
          bbest=b
    fh_kb = f_k_exp_scaled(k = kbest, b = bbest, ss = ss, f = fh)
    self.update_core(f_part2 = fh_kb)
    return kbest, bbest

  def update_f_part1(self, params=None, log=None):
    raise RuntimeError("Not implemented")
    #def show(r_work,r_free,k_part,b_part,k_sol,b_sol,prefix,log):
    #  fmt = "%s %6.4f %6.4f %5.2f %6.2f %5.2f %6.2f"
    #  print >> log, fmt % (prefix,r_work,r_free,k_part,b_part,k_sol,b_sol)
    #show(r_work=self.r_work(), r_free=self.r_free(), k_part=self.k_part(),
    #     b_part=self.b_part(), k_sol=self.k_sol(), b_sol=self.b_sol(),
    #     prefix="Start:", log=log)
    #self.update_core(k_part = 0, b_part = 0)
    #self.update_xray_structure(update_f_mask=True)
    #show(r_work=self.r_work(), r_free=self.r_free(), k_part=self.k_part(),
    #     b_part=self.b_part(), k_sol=self.k_sol(), b_sol=self.b_sol(),
    #     prefix="  ", log=log)
    #self.update_solvent_and_scale(optimize_mask=False)
    #show(r_work=self.r_work(), r_free=self.r_free(), k_part=self.k_part(),
    #     b_part=self.b_part(), k_sol=self.k_sol(), b_sol=self.b_sol(),
    #     prefix="  ", log=log)
    #nuo = self.compute_f_part(params = params, log = log)
    #self.passive_arrays.f_part_base = nuo.f_part
    ## This is how it should be in theory, but in practice is not the case...
    ##self.update_core(f_mask      = nuo.f_mask_new.common_set(self.f_obs()),
    ##                 f_part_base = nuo.f_part.common_set(self.f_obs()))
    #self.update_core(f_mask      = nuo.f_mask.common_set(self.f_obs()),
    #                 f_part_base = nuo.f_part.common_set(self.f_obs()))
    #show(r_work=self.r_work(), r_free=self.r_free(), k_part=self.k_part(),
    #     b_part=self.b_part(), k_sol=self.k_sol(), b_sol=self.b_sol(),
    #     prefix="  ", log=log)
    #self.update_solvent_and_scale(optimize_mask=False)
    #show(r_work=self.r_work(), r_free=self.r_free(), k_part=self.k_part(),
    #     b_part=self.b_part(), k_sol=self.k_sol(), b_sol=self.b_sol(),
    #     prefix="  ", log=log)
    #rws = self.r_work()
    #kbest=self.k_part()
    #bbest=self.b_part()
    #b_part_range = range(0,100,5)
    #for b_part in b_part_range:
    #  kpr = [i/10. for i in xrange(22)] + [i/1. for i in range(2,21)]
    #  for k_part in kpr:
    #    self.update_core(k_part = k_part, b_part = b_part)
    #    rw = self.r_work()
    #    if(rw < rws):
    #      rws = rw
    #      kbest=k_part
    #      bbest=b_part
    #      show(r_work=rws, r_free=self.r_free(), k_part=kbest,
    #           b_part=bbest, k_sol=self.k_sol(), b_sol=self.b_sol(),
    #           prefix="   ", log=log)
    #self.update_core(k_part = kbest, b_part = bbest)
    #show(r_work=self.r_work(), r_free=self.r_free(), k_part=self.k_part(),
    #     b_part=self.b_part(), k_sol=self.k_sol(), b_sol=self.b_sol(),
    #     prefix="Final:", log=log)
    #self.update_solvent_and_scale(optimize_mask=False)
    #show(r_work=self.r_work(), r_free=self.r_free(), k_part=self.k_part(),
    #     b_part=self.b_part(), k_sol=self.k_sol(), b_sol=self.b_sol(),
    #     prefix="Final:", log=log)
    #print >> log

  def update_solvent_and_scale(self, params = None, out = None, verbose=None,
        optimize_mask = True, optimize_mask_thorough=False, nproc=1):
    global time_bulk_solvent_and_scale
    timer = user_plus_sys_time()
    self.update_core()
    if(self.twin_set is not None): self.update_twin_fraction()
    if(params is None): params = bss.master_params.extract()
    if(verbose is not None): params.verbose=verbose
    save_params_bulk_solvent = params.bulk_solvent
    if(self.check_f_mask_all_zero()): params.bulk_solvent = False
    is_mask_optimized = False
    self.update_core()
    if(self.check_f_mask_all_zero()): params.bulk_solvent = False
    if(optimize_mask):
      is_mask_optimized = self.optimize_mask(params = params, out = out,
        thorough = optimize_mask_thorough, nproc=nproc)
    if(self.check_f_mask_all_zero()): params.bulk_solvent = False
    bss.bulk_solvent_and_scales(fmodel = self, params = params, log = out,
      nproc=nproc)
    self.update_core()
    if(not is_mask_optimized and optimize_mask):
      self.optimize_mask(params = params, out = out,
        thorough = optimize_mask_thorough, nproc=nproc)
    self.update_core()
    if(self.check_f_mask_all_zero()):
      params.bulk_solvent = save_params_bulk_solvent
    time_bulk_solvent_and_scale += timer.elapsed()

  def complete_set_core(self, d_min=None, d_max=None):
    if(d_min is None): d_min = self.f_model().d_min()
    complete_set = self.f_model().complete_set(d_min = d_min, d_max = d_max)
    f_calc = self.compute_f_calc(miller_array = complete_set)
    fmasks = masks.manager(
      miller_array   = f_calc,
      mask_params    = self.mask_params,
      xray_structure = self.xray_structure).shell_f_masks()
    lone_set = f_calc.lone_set(other = self.f_model())
    f_part1_lone = lone_set.array(data = lone_set.data()*0)
    f_part1 = self.f_part1().concatenate(other = f_part1_lone)
    f_part2_lone = lone_set.array(data = lone_set.data()*0)
    f_part2 = self.f_part2().concatenate(other = f_part2_lone)
    return core(
      f_calc  = f_calc,
      f_mask  = fmasks,
      k_sols  = self.k_sols(),
      b_sol   = self.b_sol(),
      f_part1 = f_part1,
      f_part2 = f_part2,
      u_star  = self.u_star())

  def _get_target_name(self): return self._target_name
  target_name = property(_get_target_name)

  def target_attributes(self):
    if (self.target_name is None): return None
    result = mmtbx.refinement.targets.target_names.get(self.target_name)
    if (result is None):
      raise RuntimeError(
        "Unknown target name: %s" % show_string(self.target_name))
    return result

  def target_functor(self):
    return mmtbx.refinement.targets.target_functor(manager=self)

  def set_target_name(self, target_name):
    if (target_name == "ls"): target_name = "ls_wunit_k1"
    self._target_name = target_name

  def determine_n_bins(self,
        free_reflections_per_bin,
        max_n_bins=None,
        min_n_bins=1,
        min_refl_per_bin=100):
    assert free_reflections_per_bin > 0
    n_refl = self.active_arrays.free_sel.size()
    n_free = self.active_arrays.free_sel.count(True)
    n_refl_per_bin = free_reflections_per_bin
    if (n_free != 0):
      n_refl_per_bin *= n_refl / n_free
    n_refl_per_bin = min(n_refl, iround(n_refl_per_bin))
    result = max(1, iround(n_refl / max(1, n_refl_per_bin)))
    if (min_n_bins is not None):
      result = max(result, min(min_n_bins, iround(n_refl / min_refl_per_bin)))
    if (max_n_bins is not None):
      result = min(max_n_bins, result)
    return result

  def update(self, f_calc                       = None,
                   f_obs                        = None,
                   f_mask                       = None,
                   r_free_flags                 = None,
                   f_part1                      = None,
                   b_cart                       = None,
                   k_sols                       = None,
                   b_sol                        = None,
                   sf_and_grads_accuracy_params = None,
                   target_name                  = None,
                   abcd                         = None,
                   alpha_beta_params            = None,
                   twin_fraction                = None,
                   xray_structure               = None,
                   mask_params                  = None):
    self.update_core(f_calc = f_calc, f_mask = f_mask, b_cart = b_cart,
      k_sols = k_sols, b_sol = b_sol, f_part1 = f_part1)
    if(mask_params is not None):
       self.mask_params = mask_params
    if(f_obs is not None):
      #BAD IDEA ? self.passive_arrays.f_obs = f_obs
      self.active_arrays.f_obs = f_obs
      self.update_core()
    if(r_free_flags is not None):
      self.passive_arrays.r_free_flags = r_free_flags
    if(sf_and_grads_accuracy_params is not None):
      self.sfg_params = sf_and_grads_accuracy_params
      self.update_xray_structure(update_f_calc  = True)
    if(target_name is not None):
      self.set_target_name(target_name=target_name)
    if abcd is not None:
      if not abcd.indices().all_eq(self.passive_arrays.f_obs.indices()):
        abcd = abcd.complete_array(
          new_data_value=(0,0,0,0), d_min=self.passive_arrays.f_obs.d_min())\
             .common_set(self.passive_arrays.f_obs)
      self.abcd = abcd
      self.passive_arrays.hl_coeffs = abcd
      self.active_arrays.hl_coeffs = abcd.common_set(self.f_obs())
    if(twin_fraction is not None):
      self.twin_fraction = twin_fraction
      self.update_core()
    if(alpha_beta_params is not None):
      self.alpha_beta_params = alpha_beta_params
    if(xray_structure is not None):
       self.update_xray_structure(xray_structure = xray_structure,
                                  update_f_mask  = True,
                                  update_f_calc  = True)
    return self

  def hl_coeffs(self):
    if(self.active_arrays is None):
      return self.passive_arrays.hl_coeffs
    else:
      return self.active_arrays.hl_coeffs

  def f_obs(self):
    if(self.active_arrays is None):
      return self.passive_arrays.f_obs
    else:
      return self.active_arrays.f_obs

  def r_free_flags(self):
    if(self.active_arrays is None):
      return self.passive_arrays.r_free_flags
    else:
      return self.active_arrays.r_free_flags

  def f_bulk(self):
    return miller.array(miller_set = self.f_obs(),
      data = self.active_arrays.core.data.f_bulk)

  def f_bulk_w(self):
    if(self.r_free_flags().data().count(True) > 0):
      return self.f_bulk().select(self.active_arrays.work_sel)
    else:
      return self.f_bulk()

  def f_bulk_t(self):
    if(self.r_free_flags().data().count(True) > 0):
      return self.f_bulk().select(self.active_arrays.free_sel)
    else:
      return self.f_bulk()

  def fb_cart(self):
    return self.active_arrays.core.data.f_aniso

  def fb_cart_work(self):
    return self.active_arrays.fb_cart_work

  def fb_cart_t(self):
    return self.fb_cart().select(self.active_arrays.free_sel)

  def f_obs_work(self):
    return self.active_arrays.f_obs_work

  def f_obs_free(self):
    return self.active_arrays.f_obs_free

  def f_model(self):
    return self.active_arrays.f_model

  def f_model_work(self):
    return self.active_arrays.f_model_work

  def f_mask(self):
    return self.f_calc().customized_copy(
      data = self.active_arrays.core.data.f_mask())

  def f_model_free(self):
    return self.active_arrays.f_model_free

  def f_model_scaled_with_k1(self):
    return miller.array(
      miller_set = self.f_obs(),
      data       = self.scale_k1()*self.f_model().data())

  def f_model_scaled_with_k1_debug(self, debug):
    if(debug):
      return self.f_calc().customized_copy(
        data = self.scale_k1()*self.f_model().data())
    else:
      return miller.array(
        miller_set = self.f_obs(),
        data       = self.scale_k1()*self.f_model().data())

  def f_model_scaled_with_k1_composite_work_free(self):
    ma_w = self.f_model_scaled_with_k1_w()
    ma_f = self.f_model_scaled_with_k1_t()
    if(ma_w.indices().size() == ma_f.indices().size()): return ma_w
    return ma_w.concatenate(ma_f)

  def f_model_scaled_with_k1_t(self):
    return miller.array(
      miller_set = self.f_obs_free(),
      data       = self.scale_k1_t()*self.f_model_free().data())

  def f_model_scaled_with_k1_w(self):
    return miller.array(
      miller_set = self.f_obs_work(),
      data       = self.scale_k1_w()*self.f_model_work().data())

  def f_star_w_star_obj(self):
    alpha, beta = self.alpha_beta()
    obj = max_lik.f_star_w_star_mu_nu(
      f_obs          = self.f_obs().data(),
      f_model        = flex.abs(self.f_model().data()),
      alpha          = alpha.data(),
      beta           = beta.data(),
      space_group    = self.f_obs().space_group(),
      miller_indices = self.f_obs().indices())
    return obj

  def f_star_w_star(self):
    obj = self.f_star_w_star_obj()
    f_star = miller.array(miller_set = self.f_obs(), data = obj.f_star())
    w_star = miller.array(miller_set = self.f_obs(), data = obj.w_star())
    return f_star, w_star

  def b_cart(self):
    uc = self.f_obs().unit_cell()
    b_cart = adptbx.u_as_b(
      adptbx.u_star_as_u_cart(uc, self.active_arrays.core.data.u_star))
    return b_cart

  def u_star(self):
    return self.active_arrays.core.data.u_star

  def b_iso(self):
    b_cart = self.b_cart()
    return (b_cart[0]+b_cart[1]+b_cart[2])/3.0

  def shell_f_masks(self):
    return self.active_arrays.core.f_mask

  def f_part1(self):
    return self.active_arrays.core.f_part1

  def f_part2(self):
    return self.active_arrays.core.f_part2

  def f_calc(self):
    return self.active_arrays.core.f_calc

  def f_calc_w(self):
    if(self.r_free_flags().data().count(True) > 0):
      return self.f_calc().select(~self.r_free_flags().data())
    else:
      return self.f_calc()

  def f_calc_t(self):
    if(self.r_free_flags().data().count(True) > 0):
      return self.f_calc().select(self.r_free_flags().data())
    else:
      return self.f_calc()

  def k_sol(self, i):
    return self.active_arrays.core.data.k_sol(i)

  def k_sols(self):
    return list(self.active_arrays.core.data.k_sols())

  def b_sol(self):
    return self.active_arrays.core.data.b_sol

  def f_obs_vs_f_model(self, log=None):
    if(log is None): log = sys.stdout
    for fo, fm, d in zip(self.f_obs().data(),
                         abs(self.f_model_scaled_with_k1()),
                         self.f_obs().d_spacings().data()):
      print >> log, "Fobe   Fmodel   resolution (A)"
      print >> log, "%12.3f %12.3f %6.3f"%(fo, fm, d)

  #TA alpha beta parameters
  set_sigmaa         = None
  eobs_norm_factor   = None
  ecalc_norm_factor  = None
  def eobs_and_ecalc_miller_array_normalizers(self, fix_norm_factors = True, res_scale = None):
    p = self.alpha_beta_params.sigmaa_estimator
    fmodel = self.f_model()
    eobs_norm_factor, ecalc_norm_factor = mmtbx.scaling.ta_alpha_beta_calc.ta_alpha_beta_calc(
             miller_obs = self.f_obs(),
             miller_calc = fmodel,
             r_free_flags = self.r_free_flags(),
             ta_d = self.set_sigmaa,
             kernel_width_free_reflections=p.kernel_width_free_reflections,
             kernel_on_chebyshev_nodes=p.kernel_on_chebyshev_nodes,
             n_sampling_points=p.number_of_sampling_points,
             n_chebyshev_terms=p.number_of_chebyshev_terms,
             use_sampling_sum_weights=p.use_sampling_sum_weights).eobs_and_ecalc_miller_array_normalizers()
    if fix_norm_factors:
      self.eobs_norm_factor  = eobs_norm_factor
      self.ecalc_norm_factor = ecalc_norm_factor
    return eobs_norm_factor, ecalc_norm_factor

  def alpha_beta_from_fixed_norm_factors(self):
    assert self.eobs_norm_factor is not None
    assert self.ecalc_norm_factor is not None
    alpha = self.set_sigmaa * flex.sqrt(
        self.eobs_norm_factor /
        self.ecalc_norm_factor )
    beta  = (1.0 - self.set_sigmaa*self.set_sigmaa) * self.eobs_norm_factor
    alpha = self.f_obs().array(data=alpha)
    beta  = self.f_obs().array(data=beta)
    return alpha, beta

  def alpha_beta(self, f_obs = None, f_model = None):
    global time_alpha_beta
    timer = user_plus_sys_time()
    if(f_obs is None): f_obs = self.f_obs()
    if(f_model is None): f_model = self.f_model()
    alpha, beta = None, None
    ab_params = self.alpha_beta_params
    #Eobs and Ecalc normalization factors are fixed for TA
    if self.set_sigmaa != None:
      return self.alpha_beta_from_fixed_norm_factors()
    if(self.alpha_beta_params is not None):
       assert self.alpha_beta_params.method in ("est", "calc")
       assert self.alpha_beta_params.estimation_algorithm in [
         "analytical", "iterative"]
       if (self.alpha_beta_params.method == "est"):
         if (self.alpha_beta_params.estimation_algorithm == "analytical"):
           alpha, beta = maxlik.alpha_beta_est_manager(
             f_obs           = f_obs,
             f_calc          = f_model,
             free_reflections_per_bin
               = self.alpha_beta_params.free_reflections_per_bin,
             flags           = self.r_free_flags().data(),
             interpolation   = self.alpha_beta_params.interpolation) \
               .alpha_beta()
         else:
           p = self.alpha_beta_params.sigmaa_estimator
           alpha, beta = sigmaa_estimator(
             miller_obs  = f_obs,
             miller_calc = f_model,
             r_free_flags=self.r_free_flags(),
             kernel_width_free_reflections=p.kernel_width_free_reflections,
             kernel_on_chebyshev_nodes=p.kernel_on_chebyshev_nodes,
             n_sampling_points=p.number_of_sampling_points,
             n_chebyshev_terms=p.number_of_chebyshev_terms,
             use_sampling_sum_weights=p.use_sampling_sum_weights).alpha_beta()
       else:
         n_atoms_missed = ab_params.number_of_macromolecule_atoms_absent + \
                          ab_params.number_of_waters_absent
         alpha, beta = maxlik.alpha_beta_calc(
           f                = f_obs,
           n_atoms_absent   = n_atoms_missed,
           n_atoms_included = ab_params.n_atoms_included,
           bf_atoms_absent  = ab_params.bf_atoms_absent,
           final_error      = ab_params.final_error,
           absent_atom_type = ab_params.absent_atom_type).alpha_beta()
    else:
       alpha, beta = maxlik.alpha_beta_est_manager(
         f_obs                    = f_obs,
         f_calc                   = f_model,
         free_reflections_per_bin = 140,
         flags                    = self.r_free_flags().data(),
         interpolation            = False).alpha_beta()
    time_alpha_beta += timer.elapsed()
    return alpha, beta

  def alpha_beta_w(self, only_if_required_by_target=False):
    if(only_if_required_by_target):
      if(self.target_name not in ["ml", "mlhl"]): return None, None
    alpha, beta = self.alpha_beta()
    if(self.r_free_flags().data().count(True) > 0):
      return alpha.select(self.active_arrays.work_sel), \
             beta.select(self.active_arrays.work_sel)
    else:
      return alpha, beta

  def alpha_beta_t(self):
    alpha, beta = self.alpha_beta()
    if(self.r_free_flags().data().count(True) > 0):
      return alpha.select(self.active_arrays.free_sel), \
             beta.select(self.active_arrays.free_sel)
    else:
      return alpha, beta

  def sigmaa(self, f_obs = None, f_model = None):
    p = self.alpha_beta_params.sigmaa_estimator
    sigmaa_obj = sigmaa_estimator(
      miller_obs                    = self.f_obs(),
      miller_calc                   = self.f_model(),
      r_free_flags                  = self.r_free_flags(),
      kernel_width_free_reflections = p.kernel_width_free_reflections,
      kernel_on_chebyshev_nodes     = p.kernel_on_chebyshev_nodes,
      n_sampling_points             = p.number_of_sampling_points,
      n_chebyshev_terms             = p.number_of_chebyshev_terms,
      use_sampling_sum_weights      = p.use_sampling_sum_weights)
    return sigmaa_obj

  def model_error_ml(self):
    #XXX needs clean solution / one more unfinished project
    if (self.alpha_beta_params is None):
      free_reflections_per_bin = 140
      estimation_algorithm = "analytical"
    else:
      free_reflections_per_bin=self.alpha_beta_params.free_reflections_per_bin
      estimation_algorithm = self.alpha_beta_params.estimation_algorithm
    assert estimation_algorithm in ["analytical", "iterative"]
    est_exceptions = []
    if(estimation_algorithm == "analytical"):
      alpha, beta = maxlik.alpha_beta_est_manager(
        f_obs           = self.f_obs(),
        f_calc          = self.f_model_scaled_with_k1(),
        free_reflections_per_bin = free_reflections_per_bin,
        flags           = self.r_free_flags().data(),
        interpolation   = True).alpha_beta()
    else:
      p = self.alpha_beta_params.sigmaa_estimator
      alpha, beta = sigmaa_estimator(
        miller_obs=self.f_obs(),
        miller_calc=self.f_model_scaled_with_k1(),
        r_free_flags=self.r_free_flags(),
        kernel_width_free_reflections=p.kernel_width_free_reflections,
        kernel_on_chebyshev_nodes=p.kernel_on_chebyshev_nodes,
        n_sampling_points=p.number_of_sampling_points,
        n_chebyshev_terms=p.number_of_chebyshev_terms,
        use_sampling_sum_weights=p.use_sampling_sum_weights).alpha_beta()
    sel = alpha.data() > 0
    alpha_data = alpha.data().select(sel)
    sj = self.active_arrays.core.ss.select(sel)
    sel = alpha_data > 1.
    alpha_data = alpha_data.set_selected(sel, 1.)
    aj = -math.pi**3 * sj
    bj = flex.log(alpha_data)
    den = flex.sum(aj*aj)
    if(den != 0):
      omega = math.sqrt( flex.sum(aj*bj) / den )
    else: omega = None
    return omega

  def _r_factor(self,
                type="work",
                d_min=None,
                d_max=None,
                d_spacings=None,
                selection=None):
    global time_r_factors
    if(type == "work"):
      f_obs = self.f_obs_work().data()
      f_model = self.f_model_scaled_with_k1_w().data()
    elif(type == "free"):
      f_obs = self.f_obs_free().data()
      f_model = self.f_model_scaled_with_k1_t().data()
    elif(type == "all"):
      f_obs = self.f_obs().data()
      f_model = self.f_model_scaled_with_k1().data()
    else: raise RuntimeError
    if(selection is not None): assert [d_min, d_max].count(None) == 2
    if([d_min, d_max].count(None) < 2):
      assert selection is None and d_spacings is not None
    timer = user_plus_sys_time()
    if([d_min, d_max].count(None) == 0):
      keep = flex.bool(d_spacings.size(), True)
      if (d_max): keep &= d_spacings <= d_max
      if (d_min): keep &= d_spacings >= d_min
      f_obs   = f_obs.select(keep)
      f_model = f_model.select(keep)
    if(selection is not None):
      f_obs   = f_obs.select(selection)
      f_model = f_model.select(selection)
    result = abs(bulk_solvent.r_factor(f_obs, f_model, 1.0))
    time_r_factors += timer.elapsed()
    if(result >= 1.e+9): result = None
    return result

  def r_work(self, d_min = None, d_max = None, selection = None):
    return self._r_factor(
      type       = "work",
      d_min      = d_min,
      d_max      = d_max,
      d_spacings = self.active_arrays.d_spacings_work,
      selection  = selection)

  def r_free(self, d_min = None, d_max = None, selection = None):
    return self._r_factor(
      type       = "free",
      d_min      = d_min,
      d_max      = d_max,
      d_spacings = self.active_arrays.d_spacings_free,
      selection  = selection)

  def r_all(self):
    return self._r_factor(type="all")

  #XXX Fix k1 option for TA
  set_scale_switch = 0
  def scale_k1(self, selection = None):
    if self.set_scale_switch is not None:
      if (self.set_scale_switch == 0):
        return _scale_helper(
        num=self.f_obs().data(),
        den=flex.abs(self.f_model().data()),
        selection=selection)
      if (self.set_scale_switch > 0):
        return self.set_scale_switch
    else:
      return _scale_helper(
        num=self.f_obs().data(),
        den=flex.abs(self.f_model().data()),
        selection=selection)

  def scale_k1_w(self, selection = None):
    if self.set_scale_switch is not None:
      if (self.set_scale_switch == 0):
        return _scale_helper(
          num=self.f_obs_work().data(),
          den=flex.abs(self.f_model_work().data()),
          selection=selection)
      if (self.set_scale_switch > 0):
        return self.set_scale_switch

  def scale_k1_t(self, selection = None):
    if self.set_scale_switch is not None:
      if (self.set_scale_switch == 0):
        return _scale_helper(
          num=self.f_obs_free().data(),
          den=flex.abs(self.f_model_free().data()),
          selection=selection)
      if (self.set_scale_switch > 0):
        return self.set_scale_switch

  def scale_k2(self, selection = None):
    return _scale_helper(
      num=flex.abs(self.active_arrays.f_model.data()),
      den=self.f_obs().data(),
      selection=selection)

  def scale_k2_w(self, selection = None):
    return _scale_helper(
      num=flex.abs(self.f_model_work().data()),
      den=self.f_obs_work().data(),
      selection=selection)

  def scale_k2_t(self, selection = None):
    return _scale_helper(
      num=flex.abs(self.f_model_free().data()),
      den=self.f_obs_free().data(),
      selection=selection)

  def scale_k3_w(self, selection = None):
    mul_eps_sqrt = flex.sqrt(
        self.f_obs_work().multiplicities().data().as_double()
      / self.f_obs_work().epsilons().data().as_double())
    result = _scale_helper(
      num=self.f_obs_work().data() * mul_eps_sqrt,
      den=flex.abs(self.f_model_work().data()) * mul_eps_sqrt,
      selection=selection,
      num_num=True)
    if (result is None): return None
    return result**0.5

  def scale_k3_t(self, selection = None):
    mul_eps_sqrt = flex.sqrt(
        self.f_obs_free().multiplicities().data().as_double()
      / self.f_obs_free().epsilons().data().as_double())
    result = _scale_helper(
      num=self.f_obs_free().data() * mul_eps_sqrt,
      den=flex.abs(self.f_model_free().data()) * mul_eps_sqrt,
      selection=selection,
      num_num=True)
    if (result is None): return None
    return result**0.5

  def r_work_low(self, size=500, reverse=False):
    sel = self.f_obs_work().sort_permutation(reverse=reverse)
    fo = self.f_obs_work().select(sel)
    fm = self.f_model_scaled_with_k1_w().select(sel)
    ds = fo.d_spacings().data()[:size]
    d_min = flex.max(ds)
    d_max = flex.min(ds)
    fo = fo.data()[:size]
    fm = fm.data()[:size]
    return group_args(
      r_work = abs(bulk_solvent.r_factor(fo, fm, 1)),
      d_min  = d_min,
      d_max  = d_max)

  def r_overall_low_high(self, d = 6.0):
    r_work = self.r_work()
    d_max, d_min = self.f_obs_work().d_max_min()
    if(d_max < d): d = d_max
    if(d_min > d): d = d_min
    n_low = self.f_obs_work().resolution_filter(d_min = d, d_max = 999.9).data().size()
    if(n_low > 0):
       r_work_l = self.r_work(d_min = d, d_max = 999.9)
    else:
       r_work_l = None
    n_high = self.f_obs_work().resolution_filter(d_min = 0.0, d_max = d).data().size()
    if(n_high > 0):
       r_work_h = self.r_work(d_min = 0.0, d_max = d)
    else:
       r_work_h = None
    if(r_work_l is not None):
       r_work_l = r_work_l
    else:
       r_work_l = 0.0
    if(r_work_h is not None):
       r_work_h = r_work_h
    else:
       r_work_h = 0.0
    return r_work, r_work_l, r_work_h, n_low, n_high

  def fill_missing_f_obs(self, fill_mode, update_scaling = True):
    if(flex.max(abs(self.f_part1()).data()) != 0): return None # do not fill if Fpart is used.
    import mmtbx.missing_reflections_handler
    return mmtbx.missing_reflections_handler.fill_missing_f_obs(
      fmodel=self, fill_mode=fill_mode, update_scaling=update_scaling)

  def scale_ml_wrapper(self):
    if (self.alpha_beta_params is None): return 1.0
    if (self.alpha_beta_params.method != "calc"): return 1.0
    if (self.alpha_beta_params.fix_scale_for_calc_option is None):
      return self.scale_ml()
    return self.alpha_beta_params.fix_scale_for_calc_option

  def figures_of_merit(self):
    alpha, beta = self.alpha_beta()
    global time_foms
    timer = user_plus_sys_time()
    result = max_lik.fom_and_phase_error(
      f_obs          = self.f_obs().data(),
      f_model        = flex.abs(self.active_arrays.f_model.data()),
      alpha          = alpha.data(),
      beta           = beta.data(),
      space_group    = self.f_obs().space_group(),
      miller_indices = self.f_obs().indices()).fom()
    time_foms += timer.elapsed()
    return result

  def figures_of_merit_work(self):
    fom = self.figures_of_merit()
    if(self.r_free_flags().data().count(True) > 0):
      return fom.select(self.active_arrays.work_sel)
    else:
      return fom

  def phase_errors(self):
    alpha, beta = self.alpha_beta()
    global time_phase_errors
    timer = user_plus_sys_time()
    result = max_lik.fom_and_phase_error(
      f_obs          = self.f_obs().data(),
      f_model        = flex.abs(self.active_arrays.f_model.data()),
      alpha          = alpha.data(),
      beta           = beta.data(),
      space_group    = self.f_obs().space_group(),
      miller_indices = self.f_obs().indices()).phase_error()
    time_phase_errors += timer.elapsed()
    return result

  def phase_errors_test(self):
    pher = self.phase_errors()
    if(self.r_free_flags().data().count(True) > 0):
      return pher.select(self.r_free_flags().data())
    else:
      return pher

  def phase_errors_work(self):
    pher = self.phase_errors()
    if(self.r_free_flags().data().count(True) > 0):
      return pher.select(self.active_arrays.work_sel)
    else:
      return pher

  def filter_by_fom(self, fom_threshold = 0.2):
    fom = self.figures_of_merit()
    sel = fom > fom_threshold
    dsel = self.f_obs().d_spacings().data() < 5.
    sel = sel.set_selected(~dsel,True)
    self = self.select(sel)
    return self

  def filter_by_delta_fofc(self):
    deltas = flex.double()
    for fc, fo in zip(self.f_model_scaled_with_k1().data(), self.f_obs().data()):
      deltas.append(abs(fo - abs(fc)))
    sel = flex.sort_permutation(deltas, reverse=True)
    self = self.select(sel)
    sel = flex.size_t(range(100, deltas.size()))
    self = self.select(sel)
    return self

  def map_calculation_helper(self,
                             free_reflections_per_bin = 100,
                             interpolation = True):
    class result(object):
      def __init__(self, fmodel, free_reflections_per_bin, interpolation):
        self.f_obs = fmodel.f_obs()
        self.f_model = fmodel.f_model_scaled_with_k1()
        b_cart = fmodel.b_cart()
        trace = (b_cart[0]+b_cart[1]+b_cart[2])/3.
        if(abs(trace)>20): # XXX BAD!!! fix asap by refining Biso applied to Fobs XXX
          fb_cart = 1./fmodel.fb_cart()
          self.f_obs = self.f_obs.array(data = self.f_obs.data()*fb_cart)
          self.f_model = self.f_model.array(data = self.f_model.data()*fb_cart)
        self.alpha, self.beta = maxlik.alpha_beta_est_manager(
          f_obs                    = self.f_obs,
          f_calc                   = self.f_model,
          free_reflections_per_bin = free_reflections_per_bin,
          flags                    = fmodel.r_free_flags().data(),
          interpolation            = interpolation).alpha_beta()
        self.fom = max_lik.fom_and_phase_error(
          f_obs          = self.f_obs.data(),
          f_model        = flex.abs(self.f_model.data()),
          alpha          = self.alpha.data(),
          beta           = self.beta.data(),
          space_group    = fmodel.r_free_flags().space_group(),
          miller_indices = fmodel.r_free_flags().indices()).fom()
        self.isotropize_helper = fmodel.isotropize_helper()
    return result(
      fmodel                   = self,
      free_reflections_per_bin = free_reflections_per_bin,
      interpolation            = interpolation)

  def isotropize_helper(self):
    if(self.xray_structure is None): return None
    def subtract_min_eigenvalue(x):
      from scitbx import linalg
      import scitbx.linalg.eigensystem
      es = linalg.eigensystem.real_symmetric(x)
      from scitbx import matrix
      vals = matrix.col((es.values()))
      min_v = min(vals.elems)
      vals = matrix.col([e-min_v for e in vals])
      vecs = matrix.sqr((es.vectors()))
      vecs_inv = vecs.inverse()
      m = vecs_inv * matrix.sym(sym_mat3=vals.elems+(0,0,0)) * vecs_inv.transpose()
      m = m.as_sym_mat3()
      return m
      tmp = [i for i in m.elems]
      return flex.sym_mat3_double([tmp])[0]
    b_cart = self.b_cart()
    trace = (b_cart[0]+b_cart[1]+b_cart[2])/3.
    b_cart_new = [b_cart[0]-trace,b_cart[1]-trace,b_cart[2]-trace,
                      b_cart[3],      b_cart[4],      b_cart[5]]
    ##
    #print "b_cart_new", list(b_cart_new)
    #b_cart_new = subtract_min_eigenvalue(b_cart_new)
    #print "b_cart_new", list(b_cart_new)
    ##
    u_star = adptbx.u_cart_as_u_star(
        self.f_obs().unit_cell(),adptbx.b_as_u(b_cart_new))
    fmasks = self.shell_f_masks()
    core_ = core(
      f_calc  = self.f_calc(),
      f_mask  = fmasks,
      k_sols  = [0.]*len(fmasks),
      b_sol   = 0.,
      f_part1 = self.f_part1(),
      u_star  = u_star,
      fmodel  = None,
      ss      = None)
    fb = miller.set(crystal_symmetry=self.f_obs().crystal_symmetry(),
      indices = self.f_obs().indices(),
      anomalous_flag=False).array(data= core_.data.f_aniso)
    fb = fb.average_bijvoet_mates()
    ss = 1./flex.pow2(fb.d_spacings().data()) / 4.
    if(abs(trace)>20): # XXX BAD!!! fix asap by refining Biso applied to Fobs XXX
      scale = fb.data()
    else:
      scale = 1./fb.data()
    scale = miller.set(crystal_symmetry=self.f_obs().crystal_symmetry(),
      indices = self.f_obs().deep_copy().average_bijvoet_mates().indices(),
      anomalous_flag=False).array(data=scale)
    return group_args(
      iso_scale = scale,
      ss = ss,
      sites_frac = self.xray_structure.sites_frac(),
      b_isos = self.xray_structure.extract_u_iso_or_u_equiv()*adptbx.u_as_b(1.))

  def f_model_phases_as_hl_coefficients(self, map_calculation_helper):
    if(map_calculation_helper is not None):
      mch = map_calculation_helper
    else:
      mch = self.map_calculation_helper()
    f_model_phases = mch.f_model.phases().data()
    sin_f_model_phases = flex.sin(f_model_phases)
    cos_f_model_phases = flex.cos(f_model_phases)
    t = maxlik.fo_fc_alpha_over_eps_beta(
      f_obs   = mch.f_obs,
      f_model = mch.f_model,
      alpha   = mch.alpha,
      beta    = mch.beta)
    hl_a_model = t * cos_f_model_phases
    hl_b_model = t * sin_f_model_phases
    return flex.hendrickson_lattman(a = hl_a_model, b = hl_b_model)

  def f_model_phases_as_hl_coeffs_array (self) :
    hl_coeffs = miller.set(crystal_symmetry=self.f_obs().crystal_symmetry(),
        indices = self.f_obs().indices(),
        anomalous_flag=False).array(
          data=self.f_model_phases_as_hl_coefficients(
            map_calculation_helper=None))
    return hl_coeffs

  def combined_hl_coefficients(self, map_calculation_helper):
    result = None
    if(self.hl_coeffs() is not None):
      result = self.hl_coeffs().data() + self.f_model_phases_as_hl_coefficients(
        map_calculation_helper)
    return result

  def combine_phases(self, n_steps = 360, map_calculation_helper=None):
    result = None
    if(self.hl_coeffs() is not None):
      integrator = miller.phase_integrator(n_steps = n_steps)
      phase_source = integrator(
        space_group= self.f_obs().space_group(),
        miller_indices = self.f_obs().indices(),
        hendrickson_lattman_coefficients =
          self.combined_hl_coefficients(map_calculation_helper))
      class tmp:
        def __init__(self, phase_source):
          self.phase_source = phase_source
        def phases(self):
          return flex.arg(self.phase_source)
        def fom(self):
          return flex.abs(self.phase_source)
        def f_obs_phase_and_fom_source(self):
          return self.phase_source
      result = tmp(phase_source = phase_source)
    return result

  def electron_density_map(self,
                           fill_missing_f_obs = False,
                           fill_mode = None,
                           update_scaling = True):
    return map_tools.electron_density_map(
      fmodel                 = self,
      fill_missing_f_obs     = fill_missing_f_obs,
      update_scaling         = update_scaling,
      fill_mode              = fill_mode)

  def info(self, free_reflections_per_bin = None, max_number_of_bins = None):
    if(free_reflections_per_bin is None):
      free_reflections_per_bin= self.alpha_beta_params.free_reflections_per_bin
    if(max_number_of_bins is None):
      max_number_of_bins = self.max_number_of_bins
    return mmtbx.f_model_info.info(
      fmodel                   = self,
      free_reflections_per_bin = free_reflections_per_bin,
      max_number_of_bins       = max_number_of_bins)

  def fft_vs_direct(self, reflections_per_bin = 250,
                          n_bins              = 0,
                          out                 = None):
    if(out is None): out = sys.stdout
    f_obs_w = self.f_obs_work()
    f_obs_w.setup_binner(reflections_per_bin = reflections_per_bin,
                         n_bins              = n_bins)
    fmodel_dc = self.deep_copy()
    fft_p = sf_and_grads_accuracy_master_params.extract()
    fft_p.algorithm = "fft"
    dir_p = sf_and_grads_accuracy_master_params.extract()
    dir_p.algorithm = "direct"
    if(self.sfg_params.algorithm == "fft"):
       fmodel_dc.update(sf_and_grads_accuracy_params = dir_p)
    elif(self.sfg_params.algorithm == "direct"):
       fmodel_dc.update(sf_and_grads_accuracy_params = fft_p)
    print >> out, "|"+"-"*77+"|"
    print >> out, "| Bin     Resolution   Compl.  No.       Scale_k1             R-work          |"
    print >> out, "|number     range              Refl.      direct       fft direct fft-direct,%|"
    deltas = flex.double()
    for i_bin in f_obs_w.binner().range_used():
        sel         = f_obs_w.binner().selection(i_bin)
        r_work_1    = self.r_work(selection = sel)
        scale_k1_1  = self.scale_k1_w(selection = sel)
        r_work_2    = fmodel_dc.r_work(selection = sel)
        scale_k1_2  = fmodel_dc.scale_k1_w(selection = sel)
        f_obs_sel   = f_obs_w.select(sel)
        d_max,d_min = f_obs_sel.d_max_min()
        compl       = f_obs_sel.completeness(d_max = d_max)
        n_ref       = sel.count(True)
        delta       = abs(r_work_1-r_work_2)*100.
        deltas.append(delta)
        d_range     = f_obs_w.binner().bin_legend(
                   i_bin = i_bin, show_bin_number = False, show_counts = False)
        format = "|%3d: %-17s %4.2f %6d %14.3f %6.4f %6.4f   %9.4f  |"
        if(self.sfg_params.algorithm == "fft"):
           print >> out, format % (i_bin,d_range,compl,n_ref,
                                            scale_k1_2,r_work_1,r_work_2,delta)
        else:
           print >> out, format % (i_bin,d_range,compl,n_ref,
                                            scale_k1_1,r_work_2,r_work_1,delta)
    print >> out, "|"+"-"*77+"|"
    out.flush()

  def explain_members(self, out=None, prefix="", suffix=""):
    if (out is None): out = sys.stdout
    def zero_if_almost_zero(v, eps=1.e-6):
      if (abs(v) < eps): return 0
      return v
    for line in [
          "Fmodel   = scale_k1 * fb_cart * (Fcalc + Fbulk)",
          "Fcalc    = structure factors calculated from atomic model",
          "Fbulk    = k_sol * exp(-b_sol*s**2/4) * Fmask",
          "scale_k1 = SUM(Fobs * Fmodel) / SUM(Fmodel**2)",
          "fb_cart  = exp(-h^t * A^-1 * B_cart * A^-t * h)",
          "A        = orthogonalization matrix",
          "k_sol    = %s" % " ".join(["%5.2f"%i for i in self.k_sols()]).strip(),
          "b_sol    = %.6g" % zero_if_almost_zero(self.b_sol()),
          "scale_k1 = %.6g" % self.scale_k1(),
          "B_cart = (B11, B22, B33, B12, B13, B23)",
          "       = (%s)" % ", ".join(
            ["%.6g" % zero_if_almost_zero(v) for v in self.b_cart()])]:
      print >> out, prefix + line + suffix

  def export(self, out=None, format="mtz"):
    assert format in ["mtz", "cns"]
    file_name = None
    if (out is None):
      out = sys.stdout
    elif (hasattr(out, "name")):
      file_name = libtbx.path.canonical_path(file_name=out.name)
    if (format == "cns"):
      print >> out, "{ %s }" % date_and_time()
      if (file_name is not None):
        print >> out, "{ file name: %s }" % os.path.basename(file_name)
        print >> out, "{ directory: %s }" % os.path.dirname(file_name)
      self.explain_members(out=out, prefix="{ ", suffix=" }")
      crystal_symmetry_as_cns_comments(
        crystal_symmetry=self.f_obs(), out=out)
      print >> out, "NREFlections=%d" % self.f_obs().indices().size()
      print >> out, "ANOMalous=%s" % {0: "FALSE"}.get(
        int(self.f_obs().anomalous_flag()), "TRUE")
      have_sigmas = self.f_obs().sigmas() is not None
      for n_t in [("FOBS", "REAL"),
                  ("SIGFOBS", "REAL"),
                  ("R_FREE_FLAGS", "INTEGER"),
                  ("FMODEL", "COMPLEX"),
                  ("FCALC", "COMPLEX"),
                  ("FMASK", "COMPLEX"),
                  ("FBULK", "COMPLEX"),
                  ("FB_CART", "REAL"),
                  ("FOM", "REAL"),
                  ("ALPHA", "REAL"),
                  ("BETA", "REAL")]:
        if (not have_sigmas and n_t[0] == "SIGFOBS"): continue
        print >> out, "DECLare NAME=%s DOMAin=RECIprocal TYPE=%s END" % n_t
      f_model            = self.f_model_scaled_with_k1()
      f_model_amplitudes = f_model.amplitudes().data()
      f_model_phases     = f_model.phases(deg=True).data()
      f_calc_amplitudes  = self.f_calc().amplitudes().data()
      f_calc_phases      = self.f_calc().phases(deg=True).data()
      f_bulk_amplitudes  = self.f_bulk().amplitudes().data()
      f_bulk_phases      = self.f_bulk().phases(deg=True).data()
      alpha, beta        = [item.data() for item in self.alpha_beta()]
      arrays = [
        self.f_obs().indices(), self.f_obs().data(), self.f_obs().sigmas(),
        self.r_free_flags().data(),
        f_model_amplitudes, f_model_phases,
        f_calc_amplitudes, f_calc_phases]
      f_masks = self.shell_f_masks()
      n_masks = len(f_masks)
      masks_format = ""
      for ifm,fm in enumerate(f_masks):
        f_mask_amplitudes = fm.amplitudes().data()
        f_mask_phases = fm.phases(deg=True).data()
        arrays.extend( [f_mask_amplitudes, f_mask_phases] )
        if( n_masks==1 ):
          mask_format = " FMASK="
        else:
          mask_format = " FMASK%d="%(ifm+1)
        masks_format += (mask_format+" %.6g %.6g")
      arrays.extend([
        f_bulk_amplitudes, f_bulk_phases,
        self.fb_cart(),
        self.figures_of_merit(),
        alpha, beta])
      if (not have_sigmas):
        del arrays[2]
        i_r_free_flags = 2
      else:
        i_r_free_flags = 3
      im1 = i_r_free_flags+5
      im2 = im1 + (n_masks*2)
      for values in zip(*arrays):
        print >> out, "INDE %d %d %d" % values[0]
        print >> out, " FOBS= %.6g" % values[1],
        if (have_sigmas):
          print >> out, " SIGFOBS= %.6g" % values[2],
        print >> out, \
          " R_FREE_FLAGS= %d FMODEL= %.6g %.6g\n" \
          " FCALC= %.6g %.6g" % values[i_r_free_flags:im1],
        print >>out, masks_format % values[im1:im2],
        print >>out, " FBULK= %.6g %.6g\n" \
          " FB_CART= %.6g FOM= %.6g ALPHA= %.6g BETA= %.6g" % values[im2:]
      if (file_name is not None):
        out.close()
    else:
      assert file_name is not None
      mtz_dataset = self.f_obs().as_mtz_dataset(column_root_label="FOBS")
      mtz_dataset.add_miller_array(
        miller_array=self.r_free_flags(), column_root_label="R_FREE_FLAGS")
      mtz_dataset.add_miller_array(
        miller_array=self.f_model_scaled_with_k1(), column_root_label="FMODEL")
      mtz_dataset.add_miller_array(
        miller_array=self.f_calc(), column_root_label="FCALC")
      for ifm,fm in enumerate(self.shell_f_masks()):
        if( len(self.shell_f_masks())==1 ):
          label = "FMASK"
        else:
          label= "FMASK%d"%(ifm+1)
        mtz_dataset.add_miller_array(
          miller_array=fm, column_root_label=label)
      mtz_dataset.add_miller_array(
        miller_array=self.f_bulk(), column_root_label="FBULK")
      mtz_dataset.add_miller_array(
        miller_array=self.f_obs().array(data=self.fb_cart()),
        column_root_label="FB_CART", column_types="W")
      mtz_dataset.add_miller_array(
        miller_array=self.f_obs().array(data=self.figures_of_merit()),
        column_root_label="FOM", column_types="W")
      alpha, beta = self.alpha_beta()
      mtz_dataset.add_miller_array(
        miller_array=alpha, column_root_label="ALPHA", column_types="W")
      mtz_dataset.add_miller_array(
        miller_array=beta, column_root_label="BETA", column_types="W")
      if(self.hl_coeffs() is not None):
        mtz_dataset.add_miller_array(
          miller_array=self.hl_coeffs(), column_root_label="HL")
      hl_model = miller.set(crystal_symmetry=self.f_obs().crystal_symmetry(),
        indices = self.f_obs().indices(),
        anomalous_flag=False).array(
          data=self.f_model_phases_as_hl_coefficients(
            map_calculation_helper=None))
      mtz_dataset.add_miller_array(
        miller_array = hl_model,
        column_root_label="HLmodel")
      hl_comb = miller.set(crystal_symmetry=self.f_obs().crystal_symmetry(),
        indices = self.f_obs().indices(),
        anomalous_flag=False).array(
          data=self.combined_hl_coefficients(map_calculation_helper=None))
      mtz_dataset.add_miller_array(
        miller_array = hl_model,
        column_root_label="HLcomb")
      mtz_dataset.add_miller_array(
        miller_array = self.f_obs().d_spacings(),
        column_root_label="RESOLUTION", column_types="R")
      mtz_history_buffer = flex.std_string()
      ha = mtz_history_buffer.append
      ha(date_and_time())
      ha("file name: %s" % os.path.basename(file_name))
      ha("directory: %s" % os.path.dirname(file_name))
      s = StringIO()
      self.explain_members(out=s)
      for line in s.getvalue().splitlines():
        ha(line)
      mtz_object = mtz_dataset.mtz_object()
      mtz_object.add_history(lines=mtz_history_buffer)
      out.close()
      mtz_object.write(file_name=file_name)

  def adopt_external_b_iso_adjustments(self, overall_b_iso_shift):
    b_cart = self.b_cart()
    self.update_core(b_cart=[
      b_cart[0]+overall_b_iso_shift,
      b_cart[1]+overall_b_iso_shift,
      b_cart[2]+overall_b_iso_shift,
      b_cart[3],
      b_cart[4],
      b_cart[5]])

  def estimate_f000 (self, debug=False) :
    assert (self.xray_structure is not None)
    miller_set = miller.set(
      crystal_symmetry=self.xray_structure,
      indices=self.f_obs().indices().deep_copy(),
      anomalous_flag=False)
    indices = miller_set.indices()
    indices.insert(0, (0,0,0))
    f_calc = miller_set.structure_factors_from_scatterers(
      xray_structure=self.xray_structure,
      algorithm=self.sfg_params.algorithm).f_calc()
    f_calc_000 = f_calc.data()[0].real
    if (debug) :
      print "Fcalc(0,0,0) = %.2f" % f_calc_000
    f_obs = self.f_obs().deep_copy()
    r_free_flags = self.r_free_flags().deep_copy()
    f_obs.indices().insert(0, (0,0,0))
    f_obs.data().insert(0, f_calc_000)
    if (f_obs.sigmas() is not None) :
      f_obs.sigmas().insert(0, 1.)
    r_free_flags.indices().insert(0, (0,0,0))
    r_free_flags.data().insert(0, False)
    f_model_tmp = manager(
      xray_structure=self.xray_structure,
      f_obs=f_obs,
      r_free_flags=r_free_flags,
      k_sol=self.k_sols(),
      b_sol=0, # XXX very important
      b_cart=self.b_cart())
    f000 = f_model_tmp.f_model().data()[0].real
    del f_model_tmp
    if (debug) :
      print "Fmodel(0,0,0) = %.2f" % f000
    return f000

def kb_range(x_max, x_min, step):
  x_range = []
  x = x_min
  while x <= x_max + 0.0001:
    x_range.append(x)
    x += step
  return x_range

def n_as_s(format, value):
  if (value is None):
    return format_value(format=format, value=value)
  if (isinstance(value, (int, float))):
    return (format % value).strip()
  return [(format % v).strip() for v in value]

def show_histogram(data, n_slots, log):
  hm = flex.histogram(data = data, n_slots = n_slots)
  lc_1 = hm.data_min()
  s_1 = enumerate(hm.slots())
  for (i_1,n_1) in s_1:
    hc_1 = hm.data_min() + hm.slot_width() * (i_1+1)
    print >> log, "%10.3f - %-10.3f : %d" % (lc_1, hc_1, n_1)
    lc_1 = hc_1

class mask_result (object) :
  def __init__ (self, r_solv, r_shrink, r_work, r_free, r_work_low) :
    adopt_init_args(self, locals())

  def show (self, out) :
    if (out is None) : return
    print >> out, "r_solv=%s r_shrink=%s r_work=%s r_free=%s r_work_low=%s"%(
          format_value("%6.2f", self.r_solv),
          format_value("%6.2f", self.r_shrink),
          format_value("%6.4f", self.r_work),
          format_value("%6.4f", self.r_free),
          format_value("%6.4f", self.r_work_low))

# XXX backwards compatibility 2011-02-08
class info (mmtbx.f_model_info.info) :
  pass

class resolution_bin (mmtbx.f_model_info.resolution_bin) :
  pass
