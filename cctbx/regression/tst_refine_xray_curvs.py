from __future__ import division
from cctbx import xray
from cctbx.development import random_structure
from cctbx.development import debug_utils
from cctbx.array_family import flex
import scitbx.lbfgs
from scitbx import matrix
from libtbx.test_utils import approx_equal
import random
import sys

if (1):
  random.seed(0)
  flex.set_random_seed(0)

class ls_refinement(object):

  def __init__(O,
        f_obs,
        xray_structure,
        use_lbfgs_raw,
        diagco,
        lbfgs_impl_switch,
        lbfgs_termination_params=None,
        lbfgs_exception_handling_params=None,
        reference_structure=None):
    O.f_obs = f_obs
    O.weights = flex.double(f_obs.data().size(), 1)
    O.xray_structure = xray_structure
    O.reference_structure = reference_structure
    O.pack_parameters()
    O.number_of_function_evaluations = -1
    O.number_of_lbfgs_iterations = -1
    O.f_start, O.g_start = O.compute_functional_and_gradients()
    O.callback_after_step(minimizer=None)
    if (use_lbfgs_raw):
      O.run_lbfgs_raw(diagco=diagco, lbfgs_impl_switch=lbfgs_impl_switch)
      O.callback_after_step(minimizer=None)
    else:
      O.minimizer = scitbx.lbfgs.run(
        target_evaluator=O,
        termination_params=lbfgs_termination_params,
        exception_handling_params=lbfgs_exception_handling_params)
    O.f_final, O.g_final = O.compute_functional_and_gradients()

  def pack_parameters(O):
    O.x = flex.double()
    sstab = O.xray_structure.site_symmetry_table()
    for i_sc,sc in enumerate(O.xray_structure.scatterers()):
      assert sc.flags.use_u_iso()
      assert not sc.flags.use_u_aniso()
      site_symmetry = sstab.get(i_sc)
      if (site_symmetry.is_point_group_1()):
        p = sc.site
      else:
        p = site_symmetry.site_constraints().independent_params(
          all_params=sc.site)
      O.x.extend(flex.double(p))
      O.x.append(sc.u_iso)

  def unpack_parameters(O):
    ix = 0
    sstab = O.xray_structure.site_symmetry_table()
    for i_sc,sc in enumerate(O.xray_structure.scatterers()):
      site_symmetry = sstab.get(i_sc)
      if (site_symmetry.is_point_group_1()):
        sc.site = tuple(O.x[ix:ix+3])
        ix += 3
      else:
        constr = site_symmetry.site_constraints()
        np = constr.n_independent_params()
        constr.all_params(independent_params=tuple(O.x[ix:ix+np]))
        ix += np
      sc.u_iso = O.x[ix]
      ix += 1
    assert ix == O.x.size()

  def compute_functional_and_gradients(O):
    O.number_of_function_evaluations += 1
    O.unpack_parameters()
    f_calc = O.f_obs.structure_factors_from_scatterers(
      xray_structure=O.xray_structure,
      algorithm="direct",
      cos_sin_table=False).f_calc()
    ls = xray.targets_ls_with_scale(
      apply_scale_to_f_calc=True,
      compute_scale_using_all_data=False,
      f_obs=O.f_obs.data(),
      weights=O.weights,
      r_free_flags=None,
      f_calc=f_calc.data(),
      compute_derivatives=2,
      scale_factor=1)
    gact = O.xray_structure.grads_and_curvs_target_simple(
      miller_indices=O.f_obs.indices(),
      da_db=ls.gradients_work(),
      daa_dbb_dab=ls.curvatures_work())
    g_all = gact.grads
    c_all = gact.curvs
    assert g_all.size() == c_all.size()
    #
    c_active_site = flex.double()
    c_active_u_iso = flex.double()
    i_all = 0
    sstab = O.xray_structure.site_symmetry_table()
    for i_sc,sc in enumerate(O.xray_structure.scatterers()):
      assert sc.flags.use_u_iso()
      assert not sc.flags.use_u_aniso()
      site_symmetry = sstab.get(i_sc)
      if (site_symmetry.is_point_group_1()):
        np = 3
      else:
        np = site_symmetry.site_constraints().n_independent_params()
      c_active_site.extend(g_all[i_all:i_all+np])
      c_active_u_iso.append(g_all[i_all+np])
      np += 4 # u_iso, occ, fp, fdp
      i_all += np
    assert i_all == g_all.size()
    #
    class curv_filter(object):
      def __init__(O, curvs, lim_eps=1e-6):
        c_abs_max = flex.max(flex.abs(curvs))
        O.c_lim = c_abs_max * lim_eps
        if (O.c_lim == 0):
          O.c_lim = 1
          O.c_rms = 1
        else:
          O.c_rms = flex.mean_sq(curvs)**0.5
      def apply(O, some_curvs):
        result = flex.double()
        for c in some_curvs:
          if (c < O.c_lim): c = O.c_rms
          result.append(c)
        return result
    cf_site = curv_filter(curvs=c_active_site)
    cf_u_iso = curv_filter(curvs=c_active_u_iso)
    #
    g_active = flex.double()
    c_active = flex.double()
    i_all = 0
    for i_sc,sc in enumerate(O.xray_structure.scatterers()):
      assert sc.flags.use_u_iso()
      assert not sc.flags.use_u_aniso()
      site_symmetry = sstab.get(i_sc)
      if (site_symmetry.is_point_group_1()):
        np = 3
      else:
        np = site_symmetry.site_constraints().n_independent_params()
      g_active.extend(g_all[i_all:i_all+np+1])
      c_active.extend(cf_site.apply(c_all[i_all:i_all+np]))
      c_active.extend(cf_u_iso.apply(c_all[i_all+np:i_all+np+1]))
      np += 4 # u_iso, occ, fp, fdp
      i_all += np
    assert i_all == g_all.size()
    assert g_active.size() == O.x.size()
    assert c_active.size() == O.x.size()
    #
    O.f_last = ls.target_work()
    O.g_last = g_active
    O.c_last = c_active
    return O.f_last, O.g_last

  def callback_after_step(O, minimizer):
    O.number_of_lbfgs_iterations += 1
    if (O.number_of_lbfgs_iterations % 10 == 0):
      s = "step  fun    f        |g|      curv min    max      mean"
      if (O.reference_structure is not None):
        s += "    cRMSD aRMSD uRMSD"
      print s
    c = O.c_last.min_max_mean()
    s = "%4d %4d %9.2e %9.2e %9.2e %9.2e %9.2e" % (
      O.number_of_lbfgs_iterations,
      O.number_of_function_evaluations,
      O.f_last, O.g_last.norm(), c.min, c.max, c.mean)
    if (O.reference_structure is not None):
      xs = O.xray_structure
      rs = O.reference_structure
      xf = xs.sites_frac()
      rf = rs.sites_frac()
      # TODO: use scattering power as weights, move to method of xray.structure
      ave_csh = matrix.col((xf-rf).mean())
      ave_csh_perp = matrix.col(xs.space_group_info()
        .subtract_continuous_allowed_origin_shifts(translation_frac=ave_csh))
      caosh_corr = ave_csh - ave_csh_perp
      omx = xs.unit_cell().orthogonalization_matrix()
      r = (omx * (rf - xf)).rms_length()
      s += " %5.3f" % r
      r = (omx * (rf - xf + caosh_corr)).rms_length()
      s += " %5.3f" % r
      s += " %5.3f" % (flex.mean_sq(
          xs.scatterers().extract_u_iso()
        - rs.scatterers().extract_u_iso())**0.5)
    print s
    sys.stdout.flush()

  def run_lbfgs_raw(O, diagco, lbfgs_impl_switch):
    assert diagco in [0,1]
    n = O.x.size()
    m = 5
    iprint = [1, 0]
    eps = 1.0e-5
    xtol = 1.0e-16
    size_w = n*(2*m+1)+2*m
    w = flex.double(size_w)
    diag = None
    diag0 = None
    iflag = 0
    while True:
      if (iflag in [0,1]):
        f, g = O.compute_functional_and_gradients()
        if (iflag == 0):
          if (diagco == 0):
            diag = flex.double(n, -1e20)
          else:
            assert O.c_last.all_gt(0)
            diag0 = 1 / O.c_last
            diag = diag0.deep_copy()
      else:
        assert iflag == 2
        diag.clear()
        diag.extend(diag0)
      iflag = [scitbx.lbfgs.raw_reference,
               scitbx.lbfgs.raw][lbfgs_impl_switch](
        n=n, m=m, x=O.x, f=f, g=g, diagco=diagco, diag=diag,
        iprint=iprint, eps=eps, xtol=xtol, w=w, iflag=iflag)
      if (iflag <= 0): break

def run_call_back(flags, space_group_info, params):
  structure_shake = random_structure.xray_structure(
    space_group_info,
    elements=("N", "C", "O", "S", "Yb"),
    volume_per_atom=200,
    min_distance=2.0,
    random_u_iso=True)
  structure_ideal = structure_shake.deep_copy_scatterers()
  print "Ideal structure:"
  structure_ideal.show_summary().show_scatterers()
  print
  f_obs = abs(structure_ideal.structure_factors(
    anomalous_flag=False,
    d_min=1,
    algorithm="direct",
    cos_sin_table=False).f_calc())
  structure_shake.shake_sites_in_place(rms_difference=0.2)
  structure_shake.shake_adp()
  print "Modified structure:"
  structure_shake.show_summary().show_scatterers()
  print
  print "rms difference:", \
    structure_ideal.rms_difference(other=structure_shake)
  print
  ls_refinement(
    f_obs=f_obs,
    xray_structure=structure_shake,
    use_lbfgs_raw=params.use_lbfgs_raw,
    diagco=params.diagco,
    lbfgs_impl_switch=params.lbfgs_impl_switch,
    reference_structure=structure_ideal)

def run(args):
  from libtbx import group_args
  params = group_args(
    use_lbfgs_raw=True,
    diagco=0,
    lbfgs_impl_switch=1)
  debug_utils.parse_options_loop_space_groups(
    argv=args, call_back=run_call_back, params=params)

if (__name__ == "__main__"):
  run(args=sys.argv[1:])
