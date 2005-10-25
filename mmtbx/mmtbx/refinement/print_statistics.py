from cctbx.array_family import flex
from cctbx import geometry_restraints
from libtbx import adopt_init_args
import sys, os
from libtbx.test_utils import approx_equal
from cctbx import adptbx
from stdlib import math
from cctbx import xray
from mmtbx import bulk_solvent
from mmtbx import max_lik


def print_lbfgs_minimize_stat(minimized, text, out=None):
  if (out is None): out = sys.stdout
  print >> out
  line_len = len("| "+text+"|")
  fill_len = 80 - line_len-1
  print >> out, "| "+text+"-"*(fill_len)+"|"
  print >> out, "| target value start = %13.4f | number of iterations           = %4d  |"%\
        (minimized.first_target_value, minimized.minimizer.iter())
  print >> out, "| target value end   = %13.4f | number of function evaluations = %4d  |"%\
        (minimized.final_target_value, minimized.minimizer.nfun())
  try: print >> out, "| wx = %17.6f | wc = %17.6f | wu = %17.6f    |"%\
        (minimized.wx, minimized.wc, minimized.wu)
  except: pass
  print >> out, "|"+"-"*77+"|"
  out.flush()

def make_header(line, out=None):
  if (out is None): out = sys.stdout
  header_len = 80
  line_len = len(line)
  #assert line_len <= header_len
  fill_len = header_len - line_len
  fill_rl = fill_len/2
  fill_r = fill_rl
  fill_l = fill_rl
  if (fill_rl*2 != fill_len):
    fill_r +=1
  out_string = "\n"+"="*(fill_l-1)+" "+line+" "+"="*(fill_r-1)+"\n"
  if(len(out_string) > 80):
    out_string = "\n"+"="*(fill_l-1)+" "+line+" "+"="*(fill_r-2)+"\n"
  print >> out, out_string
  out.flush()

def make_sub_header(line_, out=None):
  if (out is None): out = sys.stdout
  header_len = 80
  line = "----------"+line_+"----------"
  line_len = len(line)
  #assert line_len <= header_len
  fill_len = header_len - line_len
  fill_rl = fill_len/2
  fill_r = fill_rl
  fill_l = fill_rl
  if (fill_rl*2 != fill_len):
    fill_r +=1
  out_string = "\n"+" "*(fill_l-1)+" "+line+" "+" "*(fill_r-1)+"\n"
  if(len(out_string) > 80):
    out_string = "\n"+" "*(fill_l-1)+" "+line+" "+" "*(fill_r-2)+"\n"
  print >> out, out_string
  out.flush()

def macro_cycle_header(macro_cycle, number_of_macro_cycles, out=None):
  if (out is None): out = sys.stdout
  header_len = 80
  macro_cycle = str(macro_cycle)
  number_of_macro_cycles = str(number_of_macro_cycles)
  macro_cycle_str = len(macro_cycle)
  number_of_macro_cycles_str = len(number_of_macro_cycles)
  line_len = len(" MACRO_CYCLE "+macro_cycle+" FROM "+number_of_macro_cycles)+1
  fill_len = header_len - line_len
  fill_rl = fill_len/2
  fill_r = fill_rl
  fill_l = fill_rl
  if (fill_rl*2 != fill_len): fill_r +=1
  str1 = "\n"+"*"*(fill_l-1)+" MACRO_CYCLE "+macro_cycle+" FROM "
  str2 = number_of_macro_cycles+" "+"*"*(fill_r)+"\n"
  out_string = str1+str2
  print >> out, out_string
  out.flush()

def show_histogram(data,
                   n_slots,
                   out=None,
                   prefix=""):
    if (out is None): out = sys.stdout
    print >> out, prefix
    histogram = flex.histogram(data    = data,
                               n_slots = n_slots)
    low_cutoff = histogram.data_min()
    for i,n in enumerate(histogram.slots()):
      high_cutoff = histogram.data_min() + histogram.slot_width() * (i+1)
      print >> out, "%7.3f - %7.3f: %d" % (low_cutoff, high_cutoff, n)
      low_cutoff = high_cutoff
    out.flush()
    return histogram

def show_4_histograms(h_1, h_2, h_3, h_4, n_slots, out):
  format = "|%5.3f-%5.3f: %4d|%5.3f-%5.3f: %4d|%6.2f-%6.2f: %4d|%6.2f-%6.2f: %4d  |"
  lc_1 = h_1.data_min()
  lc_2 = h_2.data_min()
  lc_3 = h_3.data_min()
  lc_4 = h_4.data_min()
  s_1 = enumerate(h_1.slots())
  s_2 = enumerate(h_2.slots())
  s_3 = enumerate(h_3.slots())
  s_4 = enumerate(h_4.slots())
  for (i_1,n_1),(i_2,n_2),(i_3,n_3),(i_4,n_4) in zip(s_1,s_2,s_3,s_4):
    hc_1 = h_1.data_min() + h_1.slot_width() * (i_1+1)
    hc_2 = h_2.data_min() + h_2.slot_width() * (i_2+1)
    hc_3 = h_3.data_min() + h_3.slot_width() * (i_3+1)
    hc_4 = h_4.data_min() + h_4.slot_width() * (i_4+1)
    outs = (lc_1,hc_1,n_1,lc_2,hc_2,n_2,lc_3,hc_3,n_3,lc_4,hc_4,n_4)
    print >> out, format % outs
    lc_1 = hc_1
    lc_2 = hc_2
    lc_3 = hc_3
    lc_4 = hc_4
  out.flush()


def write_pdb_header(out,
                     xray_structure,
                     monitor):
   remark = "REMARK "
   print >> out, "CRYST1%9.3f%9.3f%9.3f%7.2f%7.2f%7.2f" % \
       xray_structure.unit_cell().parameters(), str(xray_structure.space_group_info())
   monitor.print_items(f = out, remark = remark)
   out.flush()


class refinement_monitor(object):
  def __init__(self, params,
                     model_ref = None,
                     out=None):
    adopt_init_args(self, locals())
    if (self.out is None): self.out = sys.stdout
    self.model_ini = None
    self.steps = []
    self.wilson_b = None
    self.bond_start = None
    self.angle_start= None
    self.bond_final = None
    self.angle_final= None
    self.r_works         = []
    self.r_frees         = []
    self.targets_w       = []
    self.targets_t       = []
    self.gs_wrt_xyz_norm = []
    self.k_sols          = []
    self.b_sols          = []
    self.b_anisos        = []
    self.wxcs            = []
    self.wxus            = []
    self.wxc_scales      = []
    self.wxu_scales      = []
    self.angles_xc       = []
    self.angles_xu       = []
    self.alphas          = []
    self.betas           = []
    self.foms            = []
    self.phers           = []
    self.as_ave          = []
    self.as_max          = []
    self.bs_ave          = []
    self.bs_max          = []
    self.cs_ave          = []
    self.cs_max          = []
    self.ds_ave          = []
    self.ds_max          = []
    self.ps_ave          = []
    self.ps_max          = []
    self.rs_ave          = []
    self.rs_min          = []
    self.targets_c       = []
    self.gs_c_norm       = []
    self.wcs             = []
    self.bs_iso_max_a    = []
    self.bs_iso_min_a    = []
    self.bs_iso_ave_a    = []
    self.bs_iso_max_p    = []
    self.bs_iso_min_p    = []
    self.bs_iso_ave_p    = []
    self.bs_iso_max_s    = []
    self.bs_iso_min_s    = []
    self.bs_iso_ave_s    = []
    self.tus             = []
    self.wus             = []
    self.ds_ic_min       = []
    self.ds_ic_max       = []
    self.ds_ic_ave       = []
    self.ds_rc_min       = []
    self.ds_rc_max       = []
    self.ds_rc_ave       = []
    self.dopts_ic        = []
    self.dopts_rc        = []
    self.n_zeros         = []
    self.n_zeros_p       = []
    self.k1s_w           = []
    self.k1s_t           = []
    self.k3s_w           = []
    self.k3s_t           = []
    self.scale_ml        = []
    self.n_solv          = []

  def collect(self, model,
                    fmodel,
                    target_weights,
                    step,
                    wilson_b = None):
    mxrs = model.xray_structure
    fxrs = fmodel.xray_structure
    # XXX assert xrs from target_weights ?
    if(self.model_ini is None): self.model_ini = model.deep_copy()
    assert mxrs.scatterers().size() == fxrs.scatterers().size()
    atom_atom_distances = flex.sqrt(mxrs.difference_vectors_cart(fxrs).dot())
    assert approx_equal(flex.mean_default(atom_atom_distances,0), 0)
    if(wilson_b is not None): self.wilson_b = wilson_b
    self.steps.append(step)
    ###
    self.r_works         .append(fmodel.r_work()                  )
    self.r_frees         .append(fmodel.r_free()                  )
    self.targets_w       .append(fmodel.target_w()                )
    self.targets_t       .append(fmodel.target_t()                )
    self.gs_wrt_xyz_norm .append(fmodel.gradient_wrt_xyz().norm() )
    self.k_sols          .append(fmodel.k_sol_b_sol()[0]          )
    self.b_sols          .append(fmodel.k_sol_b_sol()[1]          )
    self.b_anisos        .append(fmodel.u_aniso                   )
    self.wxcs            .append(target_weights.wx_xyz()          )
    self.wxus            .append(target_weights.wx_adp()          )
    self.wxc_scales      .append(target_weights.holder.wxc_scale  )
    self.wxu_scales      .append(target_weights.holder.wxu_scale  )
    angle_xc = target_weights.holder.angle_xc
    angle_xu = target_weights.holder.angle_xu
    if(angle_xc is not None): angle_xc = angle_xc * 180 / math.pi
    else:                     angle_xc = 0.0
    if(angle_xu is not None): angle_xu = angle_xu * 180 / math.pi
    else:                     angle_xu = 0.0
    self.angles_xc       .append(angle_xc)
    self.angles_xu       .append(angle_xu)
    alpha, beta = fmodel.alpha_beta()
    self.alphas          .append(flex.mean_default(alpha.data(),0)          )
    self.betas           .append(flex.mean_default(beta.data(),0)           )
    self.foms            .append(flex.mean_default(fmodel.figures_of_merit(),0))
    self.phers           .append(flex.mean_default(fmodel.phase_errors(),0) )
    geom = model.geometry_statistics()
    self.as_ave          .append(geom.a_mean                      )
    self.as_max          .append(geom.a_max                       )
    self.bs_ave          .append(geom.b_mean                      )
    self.bs_max          .append(geom.b_max                       )
    self.cs_ave          .append(geom.c_mean                      )
    self.cs_max          .append(geom.c_max                       )
    self.ds_ave          .append(geom.d_mean                      )
    self.ds_max          .append(geom.d_max                       )
    self.ps_ave          .append(geom.p_mean                      )
    self.ps_max          .append(geom.p_max                       )
    self.rs_ave          .append(geom.r_mean                      )
    self.rs_min          .append(geom.r_min                       )
    self.targets_c       .append(geom.target                      )
    grads = geom.gradients
    if(grads is not None): norm = grads.norm()
    else:                  norm = 0.0
    self.gs_c_norm       .append(norm                             )
    self.wcs             .append(target_weights.wc()              )
    b_isos = model.xray_structure.extract_u_iso_or_u_equiv() * math.pi**2*8
    self.bs_iso_max_a    .append(flex.max_default( b_isos, 0)     )
    self.bs_iso_min_a    .append(flex.min_default( b_isos, 0)     )
    self.bs_iso_ave_a    .append(flex.mean_default(b_isos, 0)     )
    s_sel = model.solvent_selection
    if(s_sel.count(True) > 0):
       b_isos_s = b_isos.select(s_sel)
       b_isos_p = b_isos.select(~s_sel)
       self.bs_iso_max_p .append(flex.max_default( b_isos_p, 0)   )
       self.bs_iso_min_p .append(flex.min_default( b_isos_p, 0)   )
       self.bs_iso_ave_p .append(flex.mean_default(b_isos_p, 0)   )
       self.bs_iso_max_s .append(flex.max_default( b_isos_s, 0)   )
       self.bs_iso_min_s .append(flex.min_default( b_isos_s, 0)   )
       self.bs_iso_ave_s .append(flex.mean_default(b_isos_s, 0)   )
    adp = model.adp_statistics(iso_restraints = self.params.adp_restraints.iso,
                               wilson_b       = self.wilson_b)
    self.tus             .append(adp.target_adp_iso               )
    self.wus             .append(target_weights.wu()              )
    rem = relative_errors(
              model                  = model,
              model_ini              = self.model_ini,
              model_ref              = self.model_ref,
              compute_optimal_errors = self.params.main.compute_optimal_errors)
    self.ds_ic_min       .append(rem.d_ic_min                     )
    self.ds_ic_max       .append(rem.d_ic_max                     )
    self.ds_ic_ave       .append(rem.d_ic_ave                     )
    if(self.model_ref is not None):
       self.ds_rc_min    .append(rem.d_rc_min                     )
       self.ds_rc_max    .append(rem.d_rc_max                     )
       self.ds_rc_ave    .append(rem.d_rc_ave                     )
    if(self.params.main.compute_optimal_errors):
       self.dopts_ic     .append(rem.dopt_ic                      )
       self.dopts_rc     .append(rem.dopt_rc                      )
    if(fmodel.target_name.count("lsm") == 1):
       n_zero = fmodel.f_star_w_star_obj().number_of_f_star_zero()
       percent = n_zero*100./fmodel.f_obs.data().size()
       self.n_zeros      .append(n_zero                           )
       self.n_zeros_p    .append(percent                          )
    self.k1s_w           .append(fmodel.scale_k1_w()              )
    self.k1s_t           .append(fmodel.scale_k1_t()              )
    self.k3s_w           .append(fmodel.scale_k3_w()              )
    self.k3s_t           .append(fmodel.scale_k3_t()              )
    if(fmodel.alpha_beta_params.method == "calc"):
       if(fmodel.alpha_beta_params.fix_scale_for_calc_option == None):
          scale_ml = fmodel.scale_ml()
       else:
          scale_ml =fmodel.alpha_beta_params.fix_scale_for_calc_option
    if(fmodel.alpha_beta_params.method == "est"):
       scale_ml = 1.0
    self.scale_ml        .append(scale_ml                         )
    self.n_solv          .append(model.number_of_ordered_solvent_molecules())
    if([self.bond_start,self.angle_start].count(None) == 2):
       self.bond_start  = self.bs_ave[0]
       self.angle_start = self.as_ave[0]
    try:
      self.bond_final  = self.bs_ave[len(self.bs_ave)-1]
      self.angle_final = self.as_ave[len(self.as_ave)-1]
    except:
      self.bond_final  = self.bs_ave[0]
      self.angle_final = self.as_ave[0]
    ###
    xrs                      = model.xray_structure
    self.natoms              = xrs.scatterers().size()
    self.volume              = xrs.unit_cell().volume()
    self.sg                  = xrs.space_group().type().number()
    self.nsym                = xrs.space_group().n_smx()
    self.target_name         = fmodel.target_name
    self.number_of_restraints= geom.number_of_restraints

  def show(self, out=None, remark=""):
    if(out is None): out = self.out
    separator = "-"*72
    print >> out, remark + "*"*72
    print >> out, remark + "Refinement target            :  %s"   % self.target_name
    print >> out, remark + "Number of atoms              : %7d"   % self.natoms
    print >> out, remark + "Number of geometry restraints: %7d"   % self.number_of_restraints
    print >> out, remark + "Unit cell volume             : %15.3f"% self.volume
    print >> out, remark + "Space group number           : %4d"   % self.sg
    print >> out, remark + "Number of symmetries         : %4d"   % self.nsym
    print >> out, remark + "Wilson B-factor              : %10.3f"% self.wilson_b
    print >> out, remark + "Isotropic ADP: distance_power: %5.2f" % self.params.adp_restraints.iso.distance_power
    print >> out, remark + "Isotropic ADP: average_power : %5.2f" % self.params.adp_restraints.iso.average_power
    #
    #
    print >> out, remark + "****************** REFINEMENT STATISTICS STEP BY STEP ******************"
    print >> out, remark + "leading digit, like 1_, means number of macro-cycle                     "
    print >> out, remark + "0    : statistics at the very beginning when nothing is done yet        "
    print >> out, remark + "1_bss: bulk solvent correction and/or (anisotropic) scaling             "
    print >> out, remark + "1_xyz: refinement of coordinates                                        "
    print >> out, remark + "1_adp: refinement of ADPs (Atomic Displacement Parameters)              "
    print >> out, remark + "1_sar: simulated annealing refinement of x,y,z                          "
    print >> out, remark + "1_wat: ordered solvent update (add / remove)                            "
    print >> out, remark + separator
    #
    #
    a,b,c,d,e,f,g,h,i,j = [None,]*10
    print >> out, remark + \
      " R-factors, x-ray target values and norm of gradient of x-ray target"
    print >> out, remark + \
      " stage     r-work r-free  xray_target_w  xray_target_t         |grad|"
    format = remark + "%9s  %6.4f %6.4f %14.6e %14.6e %14.6e"
    for a,b,c,d,e,f in zip(self.steps,
                           self.r_works,
                           self.r_frees,
                           self.targets_w,
                           self.targets_t,
                           self.gs_wrt_xyz_norm):
        print >> out, format % (a,b,c,d,e,f)
    print >> out, remark + separator
    #
    #
    a,b,c,d,e,f,g,h,i,j = [None,]*10
    print >> out, remark + " Weights for target T = Exray * wxc * wxc_scale + Echem * wc and"
    print >> out, remark + " angles between gradient vectors, eg. (d_Exray/d_sites, d_Echem/d_sites)"
    print >> out, remark + \
       " stage              wxc          wxu  wxc_sc  wxu_sc /_gxc,gc /_gxu,gu"
    format = remark + "%9s  %12.4e %12.4e%8.3f%8.3f%9.3f%9.3f"
    for a,b,c,d,e,f,g in zip(self.steps,
                             self.wxcs,
                             self.wxus,
                             self.wxc_scales,
                             self.wxu_scales,
                             self.angles_xc,
                             self.angles_xu):
        print >> out, format % (a,b,c,d,e,f,g)
    print >> out, remark + separator
    #
    #
    a,b,c,d,e,f,g,h,i,j = [None,]*10
    print >> out, remark + \
     " stage     k_sol   b_sol     b11     b22     b33     b12     b13     b23"
    format = remark + "%9s  %5.3f %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
    for a,b,c,d in zip(self.steps, self.k_sols, self.b_sols, self.b_anisos):
        print >> out, format % (a,b,c,d[0],d[1],d[2],d[3],d[4],d[5])
    print >> out, remark + separator
    #
    #
    a,b,c,d,e,f,g,h,i,j = [None,]*10
    print >> out, remark + " stage     <pher>    fom   alpha         beta"
    format = remark + "%9s %7.3f %6.4f %7.4f %12.3f"
    for a,b,c,d,e in zip(self.steps,
                         self.phers,
                         self.foms,
                         self.alphas,
                         self.betas):
        print >> out, format % (a,b,c,d,e)
    print >> out, remark + separator
    #
    #
    a,b,c,d,e,f,g,h,i,j = [None,]*10
    print >> out, remark + \
    " stage       angl   bond   chir   dihe   plan   repu  geom_target     wc"
    format = remark + "%9s %7.3f%7.3f%7.3f%7.3f%7.3f%7.3f %12.4e%7.2f"
    for a,b,c,d,e,f,g,h,i in zip(self.steps,
                                 self.as_ave,
                                 self.bs_ave,
                                 self.cs_ave,
                                 self.ds_ave,
                                 self.ps_ave,
                                 self.rs_ave,
                                 self.targets_c,
                                 self.wcs):
        print >> out, format % (a,b,c,d,e,f,g,h,i)
    print >> out, remark + separator
    #
    #
    a,b,c,d,e,f,g,h,i,j = [None,]*10
    print >> out, remark + "                      Maximal deviations:"
    print >> out, remark + \
            " stage       angl   bond   chir   dihe   plan   repu       |grad|"
    format = remark + "%9s %7.3f%7.3f%7.3f%7.3f%7.3f%7.3f %12.4e"
    for a,b,c,d,e,f,g,h in zip(self.steps,
                               self.as_max,
                               self.bs_max,
                               self.cs_max,
                               self.ds_max,
                               self.ps_max,
                               self.rs_min,
                               self.gs_c_norm):
        print >> out, format % (a,b,c,d,e,f,g,h)
    print >> out, remark + separator
    #
    #
    a,b,c,d,e,f,g,h,i,j = [None,]*10
    if(len(self.bs_iso_max_s) == 0):
       print >> out, remark + " stage      b_max   b_min   b_ave"
    else:
       print >> out, remark + "           |-----overall-----|---macromolecule----|------solvent-------|"
       print >> out, remark + "  stage    b_max  b_min  b_ave  b_max  b_min  b_ave  b_max  b_min  b_ave"
    if(len(self.bs_iso_max_s) > 0):
       format = remark + "%9s %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f"
       for a,b,c,d,e,f,g,h,i,j in zip(self.steps,
                                      self.bs_iso_max_a,
                                      self.bs_iso_min_a,
                                      self.bs_iso_ave_a,
                                      self.bs_iso_max_p,
                                      self.bs_iso_min_p,
                                      self.bs_iso_ave_p,
                                      self.bs_iso_max_s,
                                      self.bs_iso_min_s,
                                      self.bs_iso_ave_s):
           print >> out, format % (a,b,c,d,e,f,g,h,i,j)
    if(len(self.bs_iso_max_s) == 0):
       format = remark + "%9s %7.2f %7.2f %7.2f"
       for a,b,c,d in zip(self.steps,
                                      self.bs_iso_max_a,
                                      self.bs_iso_min_a,
                                      self.bs_iso_ave_a):
           print >> out, format % (a,b,c,d)
    print >> out, remark + separator
    #
    #
    a,b,c,d,e,f,g,h,i,j = [None,]*10
    if(len(self.ds_rc_min) > 0 and len(self.dopts_ic) == 0):
       if(self.model_ref is not None):
          print >> out, remark + "Stage        Deviation of refined model from"
          print >> out, remark + "                     start model        reference model"
          print >> out, remark + "                  max    min   mean    max    min   mean"
          format = remark + "%11s   %8.3f %8.3f %8.3f %8.3f %8.3f %8.3f"
    if(len(self.ds_rc_min) == 0 and len(self.dopts_ic) == 0):
       print >> out, remark + " stage        Deviation of refined"
       print >> out, remark + "              model from start model"
       print >> out, remark + "               max      min     mean"
       format = remark + "%9s %8.3f %8.3f %8.3f"
    if(len(self.ds_rc_min) > 0 and len(self.dopts_ic) > 0 and len(self.dopts_rc) > 0):
       if(self.model_ref is not None):
          print >> out, remark + "Stage                      Deviation of refined model from"
          print >> out, remark + "                 Start model                         Reference model"
          print >> out, remark + "                   max      min     mean      opt      max      min     mean      opt"
          format = remark + "%11s   %8.3f %8.3f %8.3f %8.3f %8.3f %8.3f %8.3f %8.3f"
    if(len(self.ds_rc_min) == 0 and len(self.dopts_ic) > 0):
          print >> out, remark + "Stage                Deviation of refined"
          print >> out, remark + "                     model from start model"
          print >> out, remark + "                  max      min     mean    opt"
          format = remark + "%11s %8.3f %8.3f %8.3f %8.3f"
    if(len(self.ds_rc_min) == 0 and len(self.dopts_ic) == 0):
       for a,b,c,d in zip(self.steps,
                          self.ds_ic_max,
                          self.ds_ic_min,
                          self.ds_ic_ave):
           print >> out, format % (a,b,c,d)
    if(len(self.ds_rc_min) > 0 and len(self.dopts_ic) == 0):
       for a,b,c,d,e,f,g in zip(self.steps,
                                self.ds_ic_max,
                                self.ds_ic_min,
                                self.ds_ic_ave,
                                self.ds_rc_max,
                                self.ds_rc_min,
                                self.ds_rc_ave):
           print >> out, format % (a,b,c,d,e,f,g)
    if(len(self.ds_rc_min) == 0 and len(self.dopts_ic) > 0):
       for a,b,c,d,e in zip(self.steps,
                                self.ds_ic_max,
                                self.ds_ic_min,
                                self.ds_ic_ave,
                                self.dopts_ic):
           print >> out, format % (a,b,c,d,e)
    if(len(self.ds_rc_min) > 0 and len(self.dopts_ic) > 0 and len(self.dopts_rc) > 0):
       for a,b,c,d,e,f,g,h,i in zip(self.steps,
                                    self.ds_ic_max,
                                    self.ds_ic_min,
                                    self.ds_ic_ave,
                                    self.dopts_ic,
                                    self.ds_rc_max,
                                    self.ds_rc_min,
                                    self.ds_rc_ave,
                                    self.dopts_rc):
           print >> out, format % (a,b,c,d,e,f,g,h,i)
    print >> out, remark + separator
    #
    #
    a,b,c,d,e,f,g,h,i,j = [None,]*10
    if(len(self.n_zeros) > 0):
       print >> out, remark + "Fobs* statistics"
       print >> out, remark + "Stage        number_of_f_star_zero %_from_total"
       format = remark + "%11s                 %6d %5.2f"
       for a,b,c in zip(self.steps, self.n_zeros, self.n_zeros_p):
         print >> out, format % (a, b ,c)
    #
    #
    a,b,c,d,e,f,g,h,i,j = [None,]*10
    print >> out, remark + \
                      " stage         k1_w     k1_t     k3_w     k3_t scale_ml"
    format = remark + "%9s  %8.4f %8.4f %8.4f %8.4f %8.4f"
    for a,b,c,d,e,f in zip(self.steps,
                           self.k1s_w,
                           self.k1s_t,
                           self.k3s_w,
                           self.k3s_t,
                           self.scale_ml):
        print >> out, format % (a,b,c,d,e,f)
    print >> out, remark + separator
    #
    #
    a,b,c,d,e,f,g,h,i,j = [None,]*10
    proceed = False
    n_solv_0 = self.n_solv[0]
    for n in self.n_solv:
        if(n != n_solv_0):
           proceed = True
           break
    if(proceed):
       print >> out, remark + " stage  number of ordered solvent"
       format = remark + "%11s  %15d"
       for a,b in zip(self.steps, self.n_solv):
           print >> out, format % (a,b)
       print >> out, remark + separator
    #
    #
    a,b,c,d,e,f,g,h,i,j = [None,]*10
    print >> out, remark + " stage      adp_target      wu"
    format = remark + "%9s %12.4e %7.3f"
    for a,b,c in zip(self.steps,self.tus,self.wus):
        print >> out, format % (a,b,c)
    print >> out, remark + separator
    out.flush()

class relative_errors(object):
  def __init__(self, model, model_ini, model_ref, compute_optimal_errors):
    #XXX fix this later
    if(model.xray_structure.scatterers().size() !=
                                 model_ini.xray_structure.scatterers().size()):
       xray_structure   = model.xray_structure_macromolecule()
       xray_structure_0 = model_ini.xray_structure_macromolecule()
    else:
       xray_structure   = model.xray_structure
       xray_structure_0 = model_ini.xray_structure
    array_of_distances_between_each_atom_ini_curr = \
                              flex.sqrt(xray_structure.difference_vectors_cart(
                                                       xray_structure_0).dot())
    self.d_ic_min = \
             flex.min_default( array_of_distances_between_each_atom_ini_curr,0)
    self.d_ic_max = \
             flex.max_default( array_of_distances_between_each_atom_ini_curr,0)
    self.d_ic_ave = \
             flex.mean_default(array_of_distances_between_each_atom_ini_curr,0)
    if(model_ref is not None):
       #XXX fix this later
       if(model.xray_structure.scatterers().size() !=
                                 model_ref.xray_structure.scatterers().size()):
          xray_structure   = model.xray_structure_macromolecule()
          xray_structure_ref = model_ref.xray_structure_macromolecule()
       else:
          xray_structure   = model.xray_structure
          xray_structure_ref = model_ref.xray_structure
       array_of_distances_between_each_atom_ini_ref = \
                             flex.sqrt(xray_structure.difference_vectors_cart(
                                                    xray_structure_ref).dot())
       self.d_rc_min = \
             flex.min_default( array_of_distances_between_each_atom_ini_ref,0)
       self.d_rc_max = \
             flex.max_default( array_of_distances_between_each_atom_ini_ref,0)
       self.d_rc_ave = \
             flex.mean_default(array_of_distances_between_each_atom_ini_ref,0)
    if(compute_optimal_errors != False):
       assert model.xray_structure.scatterers().size() == \
                                   model_ini.xray_structure.scatterers().size()
       xrs = model.xray_structure
       xrs_ini = model_ini.xray_structure
       self.dopt_ic = max_lik.sasha_error_calculator(
                                  r1f  = xrs_ini.sites_frac(),
                                  r1c  = xrs_ini.sites_cart(),
                                  r2f  = xrs.sites_frac(),
                                  r2c  = xrs.sites_cart(),
                                  lab1 = xrs_ini.scatterers().extract_labels(),
                                  lab2 = xrs.scatterers().extract_labels(),
                                  uc   = xrs_ini.unit_cell(),
                                  sg   = xrs_ini.space_group(),
                                  rad  = 3.0).doptimal()
       if(model_ref is not None):
          xrs = model.xray_structure
          xrs_ref = model_ref.xray_structure
          assert xrs.scatterers().size() == xrs_ref.scatterers().size()
          self.dopt_rc = max_lik.sasha_error_calculator(
                                  r1f  = xrs_ref.sites_frac(),
                                  r1c  = xrs_ref.sites_cart(),
                                  r2f  = xrs.sites_frac(),
                                  r2c  = xrs.sites_cart(),
                                  lab1 = xrs_ref.scatterers().extract_labels(),
                                  lab2 = xrs.scatterers().extract_labels(),
                                  uc   = xrs_ref.unit_cell(),
                                  sg   = xrs_ref.space_group(),
                                  rad  = 3.0).doptimal()
