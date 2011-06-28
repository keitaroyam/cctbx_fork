from cctbx.array_family import flex
import iotbx.phil
from mmtbx.refinement import minimization
import mmtbx.refinement.group
from mmtbx.tls import tools
from mmtbx.refinement import print_statistics
import scitbx.lbfgs
from libtbx.test_utils import approx_equal
from libtbx import adopt_init_args
from libtbx.utils import user_plus_sys_time
from mmtbx import utils
from cctbx import adptbx

time_adp_refinement_py = 0.0

def show_times(out = None):
  if(out is None): out = sys.stdout
  total = time_adp_refinement_py
  if(total > 0.01):
     print >> out, "ADP refinement:"
     print >> out, "  time spent in adp_refinement.py          = %-7.2f" % time_adp_refinement_py
  return total

group_adp_master_params = iotbx.phil.parse("""\
  number_of_macro_cycles   = 3
    .type = int
  max_number_of_iterations = 25
    .type = int
  convergence_test         = False
    .type = bool
  run_finite_differences_test = False
    .type = bool
""")

tls_master_params = iotbx.phil.parse("""\
  one_residue_one_group       = None
    .type = bool
    .style = tribool
  refine_T                    = True
    .type = bool
  refine_L                    = True
    .type = bool
  refine_S                    = True
    .type = bool
  number_of_macro_cycles      = 2
    .type = int
  max_number_of_iterations    = 25
    .type = int
  start_tls_value             = None
    .type = float
  run_finite_differences_test = False
    .type = bool
  eps                         = 1.e-6
    .type = float
""")

individual_adp_master_params = iotbx.phil.parse("""\
  iso {
    max_number_of_iterations = 25
      .type = int
    automatic_randomization_if_all_equal = True
      .type = bool
    scaling {
      scale_max       = 3.0
        .type = float
      scale_min       = 10.0
        .type = float
    }
  }
""")

adp_restraints_master_params = iotbx.phil.parse("""\
  iso {
    use_u_local_only = False
      .type = bool
    sphere_radius = 5.0
      .type = float
    distance_power = 1.69
      .type = float
    average_power = 1.03
      .type = float
    wilson_b_weight_auto = False
      .type = bool
    wilson_b_weight = None
      .type = float
    plain_pairs_radius = 5.0
      .type = float
    refine_ap_and_dp = False
      .type = bool
  }
""")

class manager(object):
  def __init__(
            self,
            fmodels,
            model,
            all_params,
            group_adp_selections   = None,
            group_adp_selections_h = None,
            group_adp_params       = group_adp_master_params.extract(),
            tls_selections         = None,
            tls_params             = tls_master_params.extract(),
            individual_adp_params  = individual_adp_master_params.extract(),
            adp_restraints_params  = adp_restraints_master_params.extract(),
            refine_adp_individual  = None,
            refine_adp_group       = None,
            refine_tls             = None,
            tan_b_iso_max          = None,
            restraints_manager     = None,
            target_weights         = None,
            macro_cycle            = None,
            log                    = None,
            h_params               = None):
    global time_adp_refinement_py
    scatterers = fmodels.fmodel_xray().xray_structure.scatterers()
    timer = user_plus_sys_time()
    if(log is None): log = sys.stdout
    tan_u_iso = False
    param = 0
    if(tan_b_iso_max > 0.0):
       tan_u_iso = True
       param = int(tan_b_iso_max)
    if(macro_cycle == 1):
       offset = True
    else:
       offset = False

    if(refine_tls):
       print_statistics.make_sub_header(text = "TLS refinement",
                                        out  = log)
       tls_sel_st = flex.size_t()
       for ts in tls_selections:
         tls_sel_st.extend(ts)
       tls_sel_bool = flex.bool(scatterers.size(), flex.size_t(tls_sel_st))
       ### totally ad hoc fix
       tmp_site_t = flex.size_t()
       for gs in group_adp_selections:
         for gs_ in gs:
           tmp_site_t.append(gs_)
       ###
       if(macro_cycle == 1 or tmp_site_t.size() != scatterers.size()):
          gbr_selections = []
          for s in tls_selections:
            gbr_selections.append(s)
       else:
          gbr_selections = []
          for gs in group_adp_selections:
            gbr_selection = flex.size_t()
            for gs_ in gs:
              if(tls_sel_bool[gs_]):
                gbr_selection.append(gs_)
            if(gbr_selection.size() > 0):
              gbr_selections.append(gbr_selection)
       gbr_selections_one_arr = flex.size_t()
       for gbs in gbr_selections:
         gbr_selections_one_arr.extend(gbs)
       scatterers = fmodels.fmodel_xray().xray_structure.scatterers()
       for gbr_selection in gbr_selections_one_arr:
         scatterers[gbr_selection].flags.set_use_u_iso(True)
       group_b_manager = mmtbx.refinement.group.manager(
          fmodel                   = fmodels.fmodel_xray(),
          selections               = gbr_selections,
          convergence_test         = group_adp_params.convergence_test,
          max_number_of_iterations = 50,
          number_of_macro_cycles   = 1,
          refine_adp               = True,
          log                      = log)
       scatterers = fmodels.fmodel_xray().xray_structure.scatterers()
       for tls_selection_ in tls_selections:
         for tls_selection__ in tls_selection_:
           scatterers[tls_selection__].flags.set_use_u_aniso(True)
       model.show_groups(tls = True, out = log)
       current_target_name = fmodels.fmodel_xray().target_name
       fmodels.fmodel_xray().update(target_name = "ls_wunit_k1")
       tools.split_u(fmodels.fmodel_xray().xray_structure, tls_selections, offset)
       self.tls_refinement_manager = tools.tls_refinement(
          fmodel                      = fmodels.fmodel_xray(),
          model                       = model,
          selections                  = tls_selections,
          selections_1d               = tls_sel_st,
          refine_T                    = tls_params.refine_T,
          refine_L                    = tls_params.refine_L,
          refine_S                    = tls_params.refine_S,
          number_of_macro_cycles      = tls_params.number_of_macro_cycles,
          max_number_of_iterations    = tls_params.max_number_of_iterations,
          start_tls_value             = tls_params.start_tls_value,
          run_finite_differences_test = tls_params.run_finite_differences_test,
          eps                         = tls_params.eps,
          out                         = log,
          macro_cycle = macro_cycle)
       fmodels.fmodel_xray().update(target_name = current_target_name)
       fmodels.update_xray_structure(
            xray_structure = self.tls_refinement_manager.fmodel.xray_structure,
            update_f_calc  = True)
       model.xray_structure = fmodels.fmodel_xray().xray_structure

    if(refine_adp_individual):
       refine_adp(model, fmodels, target_weights, individual_adp_params, adp_restraints_params, h_params, log,
       all_params = all_params)

    if(refine_adp_group):
       print_statistics.make_sub_header(text= "group isotropic ADP refinement",
                                        out = log)
       group_b_manager = mmtbx.refinement.group.manager(
          fmodel                   = fmodels.fmodel_xray(),
          selections               = group_adp_selections,
          convergence_test         = group_adp_params.convergence_test,
          max_number_of_iterations = group_adp_params.max_number_of_iterations,
          number_of_macro_cycles   = group_adp_params.number_of_macro_cycles,
          run_finite_differences_test = group_adp_params.run_finite_differences_test,
          refine_adp               = True,
          log                      = log)
    time_adp_refinement_py += timer.elapsed()

class refine_adp(object):

  def __init__(self, model, fmodels, target_weights, individual_adp_params,
               adp_restraints_params, h_params, log, all_params):
    adopt_init_args(self, locals())
    # define similarity width for r-free
    d_min = fmodels.fmodel_xray().f_obs().d_min()
    if  (d_min<=1.5):               r_free_range_width = 0.
    elif(d_min>1.5 and d_min<=2.0): r_free_range_width = 0.5
    elif(d_min>2.0 and d_min<=2.5): r_free_range_width = 1.0
    elif(d_min>2.5 and d_min<=3.0): r_free_range_width = 1.5
    elif(d_min>3.0):                r_free_range_width = 2.0
    # r-free-r-work gap value
    if  (d_min<=1.5):               r_free_r_work_gap = 4.0
    elif(d_min>1.5 and d_min<=2.0): r_free_r_work_gap = 5.0
    elif(d_min>2.0 and d_min<=2.5): r_free_r_work_gap = 6.0
    elif(d_min>2.5 and d_min<=3.0): r_free_r_work_gap = 6.0
    elif(d_min>3.0):                r_free_r_work_gap = 7.0
    #
    print_statistics.make_sub_header(text="Individual ADP refinement", out = log)
    assert fmodels.fmodel_xray().xray_structure is model.xray_structure
    #
    fmodels.create_target_functors()
    assert approx_equal(self.fmodels.fmodel_xray().target_w(),
      self.fmodels.target_functor_result_xray(
        compute_gradients=False).target_work())
    rw     = flex.double()
    rf     = flex.double()
    rfrw   = flex.double()
    deltab = flex.double()
    w      = flex.double()
    if(self.target_weights is not None):
      fmth ="    R-FACTORS      <Bi-Bj>  <B>   WEIGHT       TARGETS"
      print >> self.log, fmth
      print >> self.log, " work  free  delta                           data restr"
    else:
      print >> self.log, "Unresrained refinement..."
    save_scatterers = self.fmodels.fmodel_xray().xray_structure.\
        deep_copy_scatterers().scatterers()
    if(self.target_weights is not None):
      default_weight = self.target_weights.adp_weights_result.wx*\
          self.target_weights.adp_weights_result.wx_scale
      if(self.target_weights.twp.optimize_adp_weight):
        wx_scale = [0.,0.0625,0.125,0.25,0.5,0.75,1.,1.125,1.25,1.5,1.75,2.,2.5,
          3.,3.5,4.,4.5,5.]
        trial_weights = list( flex.double(wx_scale)*self.target_weights.xyz_weights_result.wx )
        wx_scale = 1
      else:
        trial_weights = [self.target_weights.adp_weights_result.wx]
        wx_scale = self.target_weights.adp_weights_result.wx_scale
    else:
      default_weight = 1
      trial_weights = [1]
      wx_scale = 1
    self.show(weight=default_weight)
    #
    for weight in trial_weights:
      if(self.target_weights is not None):
        self.fmodels.fmodel_xray().xray_structure.replace_scatterers(
          save_scatterers.deep_copy())
        self.fmodels.update_xray_structure(
          xray_structure = self.fmodels.fmodel_xray().xray_structure,
          update_f_calc  = True)
        self.target_weights.adp_weights_result.wx = weight
        self.target_weights.adp_weights_result.wx_scale = wx_scale
      minimized = self.minimize()
      wt = weight*wx_scale
      rw_,rf_,rfrw_,deltab_,w_ = self.show(weight=wt)
      if(rw_ is not None):
        rw     .append(rw_  )
        rf     .append(rf_  )
        rfrw   .append(rfrw_)
        deltab .append(deltab_)
        w      .append(w_   )
    #
    if(len(trial_weights)>1):
      # sort by r-free
      sel = flex.sort_permutation(rf)
      rw,rf,rfrw,deltab,w=self.select(
        rw=rw,rf=rf,rfrw=rfrw,deltab=deltab,w=w,sel=sel)
      # select equally good results
      sel = (rf <= rf[0]+r_free_range_width)
      rw,rf,rfrw,deltab,w= self.select(
        rw=rw,rf=rf,rfrw=rfrw,deltab=deltab,w=w,sel=sel)
      # filter by rfree-rwork
      rw,rf,rfrw,deltab,w = self.score(rw=rw,rf=rf,rfrw=rfrw,deltab=deltab,w=w,
        score_target=rfrw,score_target_value=r_free_r_work_gap,
        secondary_target=deltab)
      # filter by <Bi-Bj>
      rw,rf,rfrw,deltab,w = self.score(rw=rw,rf=rf,rfrw=rfrw,deltab=deltab,w=w,
        score_target=deltab,score_target_value=10)
      # select the result with lowest rfree
      sel = flex.sort_permutation(rf)
      rw,rf,rfrw,deltab,w= self.select(
        rw=rw,rf=rf,rfrw=rfrw,deltab=deltab,w=w,sel=sel)
      #
      w_best = w[0]
      print >> self.log, "Best weight: %8.3f"%w_best
      #
      self.target_weights.adp_weights_result.wx = w_best
      self.target_weights.adp_weights_result.wx_scale = 1
      self.fmodels.fmodel_xray().xray_structure.replace_scatterers(
        save_scatterers.deep_copy())
      self.fmodels.update_xray_structure(
        xray_structure = self.fmodels.fmodel_xray().xray_structure,
        update_f_calc  = True)
      print >> self.log, "Accepted refinement result:"
      minimized = self.minimize()
      self.show(weight=w_best)
    #
    assert approx_equal(self.fmodels.fmodel_xray().target_w(),
       self.fmodels.target_functor_result_xray(
         compute_gradients=False).target_work())
    self.model.xray_structure = self.fmodels.fmodel_xray().xray_structure
    #

  def show(self, weight = None, prefix = "", show_neutron=True):
    deltab = self.model.rms_b_iso_or_b_equiv_bonded()
    r_work = self.fmodels.fmodel_xray().r_work()*100.
    r_free = self.fmodels.fmodel_xray().r_free()*100.
    mean_b = flex.mean(
      self.model.xray_structure.extract_u_iso_or_u_equiv())*adptbx.u_as_b(1)
    if(deltab is None):
      print >> self.log, "  r_work=%5.2f r_free=%5.2f"%(r_work, r_free)
      return [None,]*5
    if(len(prefix.strip())>0): prefix += " "
    format = prefix+"%5.2f %5.2f %6.2f %6.3f  %6.3f %6.3f   %6.3f"
    print >> self.log, format%(r_work,r_free,r_free-r_work,deltab,mean_b,weight,
      self.fmodels.fmodel_xray().target_w())
    if(show_neutron and self.fmodels.fmodel_neutron() is not None):
      print >> self.log
      print >> self.log, "Neutron data: r_work=%5.2f r_free=%5.2f"%(
        self.fmodels.fmodel_neutron().r_work()*100.,
        self.fmodels.fmodel_neutron().r_free()*100.)
    return r_work,r_free,r_free-r_work,deltab,weight

  def score(self, rw, rf, rfrw, deltab, w, score_target, score_target_value,
            secondary_target=None):
    sel  = score_target < score_target_value
    sel &= score_target > 0
    if(sel.count(True)>0):
      rw,rf,rfrw,deltab,w = self.select(
        rw=rw,rf=rf,rfrw=rfrw,deltab=deltab,w=w, sel=sel)
    else:
      if(secondary_target is None):
        sel = flex.sort_permutation(score_target)
      else:
        sel = flex.sort_permutation(secondary_target)
      rw,rf,rfrw,deltab,w = self.select(
        rw=rw,rf=rf,rfrw=rfrw,deltab=deltab,w=w, sel=sel)
      #
      rw     = flex.double([rw    [0]])
      rf     = flex.double([rf    [0]])
      rfrw   = flex.double([rfrw  [0]])
      deltab = flex.double([deltab[0]])
      w      = flex.double([w     [0]])
    return rw, rf, rfrw, deltab, w

  def select(self, rw, rf, rfrw, deltab, w, sel):
    rw     = rw    .select(sel)
    rf     = rf    .select(sel)
    rfrw   = rfrw  .select(sel)
    deltab = deltab.select(sel)
    w      = w     .select(sel)
    return rw, rf, rfrw, deltab, w

  def minimize(self):
    utils.assert_xray_structures_equal(
      x1 = self.fmodels.fmodel_xray().xray_structure,
      x2 = self.model.xray_structure)
    self.model.set_refine_individual_adp()
    lbfgs_termination_params = scitbx.lbfgs.termination_parameters(
      max_iterations = self.individual_adp_params.iso.max_number_of_iterations)
    is_neutron_scat_table = False
    if(self.all_params.main.scattering_table == "neutron"):
      is_neutron_scat_table = True
    minimized = minimization.lbfgs(
      restraints_manager       = self.model.restraints_manager,
      fmodels                  = self.fmodels,
      model                    = self.model,
      refine_adp               = True,
      is_neutron_scat_table    = is_neutron_scat_table,
      lbfgs_termination_params = lbfgs_termination_params,
      iso_restraints           = self.adp_restraints_params.iso,
      verbose                  = 0,
      target_weights           = self.target_weights,
      h_params                 = self.h_params)
    self.model.xray_structure = self.fmodels.fmodel_xray().xray_structure
    assert minimized.xray_structure is self.model.xray_structure
    utils.assert_xray_structures_equal(
      x1 = minimized.xray_structure,
      x2 = self.model.xray_structure)
    return minimized
