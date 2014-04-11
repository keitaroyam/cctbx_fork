from __future__ import division
from cctbx.array_family import flex
import scitbx.math.euler_angles
from scitbx import matrix
from libtbx.utils import format_cpu_times, getenv_bool
from libtbx import adopt_init_args, slots_getstate_setstate
import sys, time
from libtbx import str_utils
from libtbx.str_utils import prefix_each_line_suffix, format_value
from libtbx import introspection
from stdlib import math
from cctbx import xray
import cctbx.xray.structure_factors.global_counters
from libtbx import easy_pickle
from itertools import count

enable_show_process_info = getenv_bool(
  "MMTBX_PRINT_STATISTICS_ENABLE_SHOW_PROCESS_INFO")

time_collect_and_process = 0.0

def show_times(out = None):
  if(out is None): out = sys.stdout
  total = time_collect_and_process
  if(total > 0.01):
     print >> out, "Collect and process                      = %-7.2f" % time_collect_and_process
  return total

def show_process_info(out):
  print >> out, "\\/"*39
  introspection.virtual_memory_info().show_if_available(out=out, show_max=True)
  xray.structure_factors.global_counters.show(out=out)
  print >> out, format_cpu_times()
  print >> out, "/\\"*39
  out.flush()

def make_header(line, out=None):
  if (out is None): out = sys.stdout
  if (enable_show_process_info):
    show_process_info(out=out)
  str_utils.make_header(line, out=out, header_len=80)

def make_sub_header(text, out=None):
  if (out is None): out = sys.stdout
  str_utils.make_sub_header(text, out=out, header_len=80)

def macro_cycle_header(macro_cycle, number_of_macro_cycles, out=None):
  if (out is None): out = sys.stdout
  #show_process_info(out=out)
  header_len = 80
  macro_cycle = str(macro_cycle)
  number_of_macro_cycles = str(number_of_macro_cycles)
  macro_cycle_str = len(macro_cycle)
  number_of_macro_cycles_str = len(number_of_macro_cycles)
  line_len = len(" REFINEMENT MACRO_CYCLE "+macro_cycle+" OF "+\
             number_of_macro_cycles)+1
  fill_len = header_len - line_len
  fill_rl = fill_len//2
  fill_r = fill_rl
  fill_l = fill_rl
  if (fill_rl*2 != fill_len): fill_r +=1
  str1 = "\n"+"*"*(fill_l-1)+" REFINEMENT MACRO_CYCLE "+macro_cycle+" OF "
  str2 = number_of_macro_cycles+" "+"*"*(fill_r)+"\n"
  out_string = str1+str2
  print >> out, out_string
  out.flush()

def show_rigid_body_rotations_and_translations(
      out,
      prefix,
      frame,
      euler_angle_convention,
      rotations,
      translations):
  assert euler_angle_convention in ["xyz", "zyz"]
  euler_angles_as_matrix = getattr(
    scitbx.math.euler_angles, euler_angle_convention+"_matrix")
  print >> out, prefix_each_line_suffix(
    prefix=prefix+frame, lines_as_one_string=
"                            rotation (deg)                 translation (A)   "
"\n"
"                         %s              total           xyz          total "
      % euler_angle_convention, suffix=frame)
  for i,r,t in zip(count(1), rotations, translations):
    r = list(r)
    r.reverse()
    r_total = abs(scitbx.math.r3_rotation_axis_and_angle_from_matrix(
      r=euler_angles_as_matrix(*r)).angle(deg=True))
    t_total = abs(matrix.col(t))
    print >> out, (prefix + frame +
      " group %4d: %8.3f %8.3f %8.3f %7.2f  %6.2f %6.2f %6.2f %6.2f "
        % tuple([i] + r + [r_total] + list(t) + [t_total])
      + frame).rstrip()
  out.flush()

# these are the steps we actually want to display in the GUI
show_actions = {
   "bss" : "bss",
   "sol" : "sol",
   "ion" : "ion",
   "rbr" : "rbr",
   "realsrl" : "rsrl",
   "realsrg" : "rsrg",
   "den" : "den",
   "tardy" : "SA",
   "sacart" : "SA",
   "xyzrec" : "xyz",
   "adp" : "adp",
   "occ" : "occ",
   "fp_fdp" : "anom",
}

class refinement_monitor(object):
  __arrays__ = [
    "steps",
    "r_works",
    "r_frees",
    "geom",
    "bs_iso_max_a",
    "bs_iso_min_a",
    "bs_iso_ave_a",
    "n_solv",
    "shifts",
  ]

  def __init__(
        self,
        params,
        out=None,
        neutron_refinement = None,
        call_back_handler=None,
        is_neutron_monitor=False):
    adopt_init_args(self, locals())
    if (self.out is None): self.out = sys.stdout
    self.wilson_b = None
    self.bond_start = None
    self.angle_start= None
    self.bond_final = None
    self.angle_final= None
    self.rigid_body_shift_accumulator = None
    self.sites_cart_start = None
    for name in self.__arrays__ :
      setattr(self, name, [])

  def dump_statistics (self, file_name) :
    stats = {}
    for name in self.__arrays__ :
      stats[name] = getattr(self, name)
    easy_pickle.dump(file_name, stats)

  def collect(self, model,
                    fmodel,
                    step,
                    wilson_b = None,
                    rigid_body_shift_accumulator = None):
    global time_collect_and_process
    t1 = time.time()
    if(self.sites_cart_start is None):
      self.sites_cart_start = model.xray_structure.sites_cart()
    sites_cart_curr = model.xray_structure.sites_cart()
    if(sites_cart_curr.size()==self.sites_cart_start.size()):
      self.shifts.append(
        flex.mean(flex.sqrt((self.sites_cart_start-sites_cart_curr).dot())))
    else: self.shifts.append("n/a")
    if(wilson_b is not None): self.wilson_b = wilson_b
    self.steps.append(step)
    self.r_works.append(fmodel.r_work())
    self.r_frees.append(fmodel.r_free())
    geom = model.geometry_statistics(ignore_hd = not self.neutron_refinement)
    if(geom is not None): self.geom.append(geom)
    hd_sel = None
    if(not self.neutron_refinement and not self.is_neutron_monitor):
      hd_sel = model.xray_structure.hd_selection()
    b_isos = model.xray_structure.extract_u_iso_or_u_equiv() * math.pi**2*8
    if(hd_sel is not None): b_isos = b_isos.select(~hd_sel)
    self.bs_iso_max_a.append(flex.max_default( b_isos, 0))
    self.bs_iso_min_a.append(flex.min_default( b_isos, 0))
    self.bs_iso_ave_a.append(flex.mean_default(b_isos, 0))
    self.n_solv.append(model.number_of_ordered_solvent_molecules())
    if([self.bond_start,self.angle_start].count(None) == 2):
      if(len(self.geom)>0):
        self.bond_start  = self.geom[0].b[2]
        self.angle_start = self.geom[0].a[2]
    if(len(self.geom)>0):
      self.bond_final  = self.geom[len(self.geom)-1].b[2]
      self.angle_final = self.geom[len(self.geom)-1].a[2]
    elif(len(self.geom)==1):
      self.bond_final  = self.geom[0].b[2]
      self.angle_final = self.geom[0].a[2]
    if(rigid_body_shift_accumulator is not None):
      self.rigid_body_shift_accumulator = rigid_body_shift_accumulator
    t2 = time.time()
    time_collect_and_process += (t2 - t1)
    self.call_back(model, fmodel)

  def call_back (self, model, fmodel, method="monitor_collect") :
    if self.call_back_handler is not None and callable(self.call_back_handler) :
      self.call_back_handler(self, model, fmodel, method)

  def show(self, out=None, remark=""):
    global time_collect_and_process
    t1 = time.time()
    max_step_len = max([len(s) for s in self.steps])
    if(out is None): out = self.out
    separator = "-"*72
    if(self.rigid_body_shift_accumulator is not None):
      print >> out, remark + "Information about total rigid body shift of selected groups:"
      show_rigid_body_rotations_and_translations(
        out=out,
        prefix=remark,
        frame=" ",
        euler_angle_convention
          =self.rigid_body_shift_accumulator.euler_angle_convention,
        rotations=self.rigid_body_shift_accumulator.rotations,
        translations=self.rigid_body_shift_accumulator.translations)
    #
    print >> out, remark + "****************** REFINEMENT STATISTICS STEP BY STEP ******************"
    print >> out, remark + "leading digit, like 1_, means number of macro-cycle                     "
    print >> out, remark + "0    : statistics at the very beginning when nothing is done yet        "
    if(self.params.main.bulk_solvent_and_scale):
       print >> out, remark + "1_bss: bulk solvent correction and/or (anisotropic) scaling             "
    if("individual_sites" in self.params.refine.strategy):
       print >> out, remark + "1_xyz: refinement of coordinates                                        "
    if("individual_adp" in self.params.refine.strategy):
       print >> out, remark + "1_adp: refinement of ADPs (Atomic Displacement Parameters)              "
    if(self.params.main.simulated_annealing):
       print >> out, remark + "1_sar: simulated annealing refinement of x,y,z                          "
    if(self.params.main.ordered_solvent):
       print >> out, remark + "1_wat: ordered solvent update (add / remove)                            "
    if("rigid_body" in self.params.refine.strategy):
       print >> out, remark + "1_rbr: rigid body refinement                                            "
    if("group_adp" in self.params.refine.strategy):
       print >> out, remark + "1_gbr: group B-factor refinement                                        "
    if("occupancies" in self.params.refine.strategy):
       print >> out, remark + "1_occ: refinement of occupancies                                        "
    print >> out, remark + separator
    #
    print >> out, remark + \
      " stage       r-work r-free bonds angles b_min b_max b_ave n_water shift"
    format = remark + "%s%ds"%("%",max_step_len)+\
      " %6.4f %6.4f %5.3f %5.2f %5.1f %5.1f %5.1f %3d %s"
    for a,b,c,d,e,f,g,h,i in zip(self.steps,
                                 self.r_works,
                                 self.r_frees,
                                 self.geom,
                                 self.bs_iso_min_a,
                                 self.bs_iso_max_a,
                                 self.bs_iso_ave_a,
                                 self.n_solv,
                                 self.shifts):
      if(type(1.)==type(i)): i = "     "+str("%5.3f"%i)
      else: i = "%9s"%i
      print >> out, format % (a,b,c,d.b[2],d.a[2],e,f,g,h,i)
    print >> out, remark + separator
    out.flush()
    #
    t2 = time.time()
    time_collect_and_process += (t2 - t1)

  def format_stats_for_phenix_gui (self) :
    steps = []
    r_works = []
    r_frees = []
    as_ave = []
    bs_ave = []
    for i_step, label in enumerate(self.steps) :
      label = label.replace(":", "")
      fields = label.split("_")
      if (len(fields) < 2) :
        steps.append(label)
      else :
        cycle = fields[0]
        action = "_".join(fields[1:])
        action_label = show_actions.get(action, None)
        if (action_label is None) : continue
        steps.append(cycle + "_" + action_label)
      r_works.append(self.r_works[i_step])
      r_frees.append(self.r_frees[i_step])
      if (self.geom is not None) and (len(self.geom) != 0) :
        as_ave.append(self.geom[i_step].a[2])
        bs_ave.append(self.geom[i_step].b[2])
      else :
        as_ave.append(None)
        bs_ave.append(None)
    return stats_table(
      steps=steps,
      r_works=r_works,
      r_frees=r_frees,
      as_ave=as_ave,
      bs_ave=bs_ave,
      neutron_flag=self.is_neutron_monitor)

  def show_current_r_factors_summary (self, out, prefix="") :
    if (len(self.steps) == 0) :
      return
    last_step = self.steps[-1].replace(":", "")
    fields = last_step.split("_")
    action_label = None
    if (len(fields) >= 2) :
      cycle = fields[0]
      action = "_".join(fields[1:])
      action_label = show_actions.get(action, None)
      if (action_label is None) :
        return
      action_label = cycle + "_" + action_label
    if (action_label is None) :
      if (len(self.steps) == 1) :
        action_label = "start"
      else :
        action_label = "end"
    print >> out, "%s%-6s  r_work=%s  r_free=%s" % (prefix,
      action_label,
      format_value("%.4f", self.r_works[-1]),
      format_value("%.4f", self.r_frees[-1]))

class stats_table (slots_getstate_setstate) :
  __slots__ = [
    "steps",
    "r_works",
    "r_frees",
    "as_ave",
    "bs_ave",
    "neutron_flag",
  ]
  def __init__ (self, **kwds) :
    for attr in self.__slots__ :
      setattr(self, attr, kwds.get(attr))

# we need something simpler for the Phenix GUI...
class coordinate_shifts (object) :
  def __init__ (self, hierarchy_start, hierarchy_end) :
    from scitbx.array_family import flex
    self.hierarchy_shifted = hierarchy_end.deep_copy()
    atoms_shifted = self.hierarchy_shifted.atoms()
    coords_start = {}
    for atom in hierarchy_start.atoms() :
      id_str = atom.fetch_labels().id_str()
      coords_start[id_str] = atom.xyz
    def get_distance (xyz1, xyz2) :
      x1,y1,z1 = xyz1
      x2,y2,z2 = xyz2
      return math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
    for i_seq, atom in enumerate(atoms_shifted) :
      id_str = atom.fetch_labels().id_str()
      if (id_str in coords_start) :
        atom.b = get_distance(coords_start[id_str], atom.xyz)
      else :
        atom.b = -1.0

  def get_shifts (self) :
    return self.hierarchy_shifted.atoms().extract_b()

  def min_max_mean (self) :
    shifts = self.hierarchy_shifted.atoms().extract_b()
    shifts = shifts.select(shifts >= 0)
    return shifts.min_max_mean()

  def save_pdb_file (self, file_name) :
    f = open(file_name, "w")
    f.write(self.hierarchy_shifted.as_pdb_string())
    f.close()

class trajectory_output (object) :
  """
  Callback object for saving the intermediate results of refinement as a stack
  of PDB and MTZ files.  Equivalent to the interactivity with Coot in the
  Phenix GUI, but intended for command-line use and demonstrative purposes.
  """
  def __init__ (self, file_base="refine", filled_maps=True, log=sys.stdout,
      verbose=True) :
    adopt_init_args(self, locals())
    self._i_trajectory = 0

  def __call__ (self, monitor, model, fmodel, method="monitor_collect") :
    import iotbx.map_tools
    self._i_trajectory += 1
    file_base = "%s_traj_%d" % (self.file_base, self._i_trajectory)
    pdb_hierarchy = model.pdb_hierarchy(sync_with_xray_structure=True)
    two_fofc_map_coeffs = fmodel.map_coefficients(map_type="2mFo-DFc",
      fill_missing=self.filled_maps)
    fofc_map_coeffs = fmodel.map_coefficients(map_type="mFo-DFc")
    iotbx.map_tools.write_map_coeffs(
      fwt_coeffs=two_fofc_map_coeffs,
      delfwt_coeffs=fofc_map_coeffs,
      file_name=file_base+".mtz")
    f = open(file_base + ".pdb", "w")
    f.write(pdb_hierarchy.as_pdb_string(
      crystal_symmetry=model.xray_structure))
    f.close()
    print >> self.log, "wrote model to %s.pdb" % file_base
    print >> self.log, "wrote map coefficients to %s.mtz" % file_base

class annealing_callback (object) :
  def __init__ (self, model, monitor) :
    self.model = model
    self.monitor = monitor

  def __call__ (self, fmodel) :
    self.monitor.call_back(model=self.model,
      fmodel=fmodel,
      method="anneal")
