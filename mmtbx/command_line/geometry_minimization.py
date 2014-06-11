# LIBTBX_SET_DISPATCHER_NAME phenix.geometry_minimization

from __future__ import division
import mmtbx.refinement.geometry_minimization
from mmtbx import monomer_library
import mmtbx.utils
from iotbx.pdb import combine_unique_pdb_files
import iotbx.phil
from cctbx.array_family import flex
from libtbx.utils import user_plus_sys_time, Sorry
from libtbx import runtime_utils
import os
import mmtbx.secondary_structure
import sys
from cStringIO import StringIO
from mmtbx.validation.ramalyze import ramalyze
from mmtbx.rotamer.rotamer_eval import RotamerEval

base_params_str = """\
silent = False
  .type = bool
write_geo_file = True
  .type = bool
file_name = None
  .type = path
  .short_caption = Model file
  .style = file_type:pdb bold input_file
restraints = None
  .type = path
  .multiple = True
  .short_caption = Restraints
  .style = file_type:cif bold input_file
restraints_directory = None
  .type = path
  .style = directory
output_file_name_prefix = None
  .type = str
  .input_size = 400
  .style = bold
directory = None
  .type = path
  .short_caption = Output directory
  .style = output_dir
include scope libtbx.phil.interface.tracking_params
fix_rotamer_outliers = True
  .type = bool
  .help = Remove outliers
reference_restraints {
  restrain_starting_coord_selection = None
    .type = str
    .help = Atom selection string: restraint selected to starting position
    .short_caption = Restrain selection
    .input_size = 400
  coordinate_sigma = 0.5
    .type = float
    .help = sigma value for coordinates restrained to starting positions
}
stop_for_unknowns = True
  .type = bool
  .short_caption = Stop for unknown residues
  .style = noauto
include scope mmtbx.monomer_library.pdb_interpretation.grand_master_phil_str
secondary_structure_restraints = False
  .type = bool
  .short_caption = Secondary structure restraints
secondary_structure
  .alias = refinement.secondary_structure
{
  include scope mmtbx.secondary_structure.sec_str_master_phil
}
use_c_beta_deviation_restraints=True
  .type = bool
"""

master_params_str = """
%s
selection = all
  .type = str
  .help = Atom selection string: selected atoms are subject to move
  .short_caption = Atom selection
  .input_size = 400
minimization
  .help = Geometry minimization parameters
  .short_caption = Minimization parameters
  .expert_level=1
{
  max_iterations = 500
    .type = int
    .help = Maximun number of minimization iterations
    .short_caption = Max. iterations
    .style = noauto
  macro_cycles = 5
    .type = int
    .help = Number of minimization macro-cycles
  alternate_nonbonded_off_on = False
    .type = bool
    .short_caption = Macro cycles
    .style = noauto
  rmsd_bonds_termination_cutoff = 0
    .type = float
    .help = stop after reaching specified cutoff value
  rmsd_angles_termination_cutoff = 0
    .type = float
    .help = stop after reaching specified cutoff value
  grmsd_termination_cutoff = 0
    .type = float
    .help = stop after reaching specified cutoff value
  move
    .help = Define what to include into refinement target
    .short_caption = Geometry terms
    .style = box auto_align columns:3 noauto
  {
  bond = True
    .type = bool
    .short_caption = Bond lengths
  nonbonded = True
    .type = bool
    .short_caption = Nonbonded distances
  angle = True
    .type = bool
    .short_caption = Bond angle
  dihedral = True
    .type = bool
    .short_caption = Dihedral angle
  chirality = True
    .type = bool
    .short_caption = Chirality
  planarity = True
    .type = bool
    .short_caption = Planarity
  }
}
  include scope mmtbx.geometry_restraints.external.external_energy_params_str
""" % base_params_str

def master_params():
  return iotbx.phil.parse(master_params_str, process_includes=True)

def broadcast(m, log):
  print >> log, "-"*79
  print >> log, m
  print >> log, "*"*len(m)

def format_usage_message(log):
  print >> log, "-"*79
  msg = """\
phenix.geometry_minimization: regularize model geometry

Usage examples:
  phenix.geometry_minimization model.pdb
  phenix.geometry_minimization model.pdb ligands.cif
"""
  print >> log, msg
  print >> log, "-"*79

def process_input_files(inputs, params, log):
  pdb_file_names = []
  pdb_file_names = list(inputs.pdb_file_names)
  if (params.file_name is not None) :
    pdb_file_names.append(params.file_name)
  cs = inputs.crystal_symmetry
  is_non_crystallographic_unit_cell = False
  if(cs is None):
    is_non_crystallographic_unit_cell = True
    import iotbx.pdb
    pdb_combined = combine_unique_pdb_files(file_names = pdb_file_names)
    cs = iotbx.pdb.input(source_info = None, lines = flex.std_string(
      pdb_combined.raw_records)).xray_structure_simple().\
        cubic_unit_cell_around_centered_scatterers(
        buffer_size = 10).crystal_symmetry()
  cif_objects = list(inputs.cif_objects)
  if (len(params.restraints) > 0) :
    import iotbx.cif
    for file_name in params.restraints :
      cif_object = iotbx.cif.reader(file_path=file_name, strict=False).model()
      cif_objects.append((file_name, cif_object))
  if (params.restraints_directory is not None) :
    restraint_files = os.listdir(params.restraints_directory)
    for file_name in restraint_files :
      if (file_name.endswith(".cif")) :
        full_path = os.path.join(params.restraints_directory, file_name)
        cif_object = iotbx.cif.reader(file_path=full_path,
          strict=False).model()
        cif_objects.append((full_path, cif_object))
  processed_pdb_files_srv = mmtbx.utils.process_pdb_file_srv(
    crystal_symmetry          = cs,
    pdb_interpretation_params = params.pdb_interpretation,
    stop_for_unknowns         = params.stop_for_unknowns,
    log                       = log,
    cif_objects               = cif_objects,
    use_neutron_distances     = params.pdb_interpretation.use_neutron_distances)
  processed_pdb_file, junk = processed_pdb_files_srv.\
    process_pdb_files(pdb_file_names = pdb_file_names) # XXX remove junk
  processed_pdb_file.is_non_crystallographic_unit_cell = \
    is_non_crystallographic_unit_cell # XXX bad hack
  return processed_pdb_file

def get_geometry_restraints_manager(processed_pdb_file, xray_structure, params,
    log=sys.stdout):
  has_hd = None
  if(xray_structure is not None):
    sctr_keys = xray_structure.scattering_type_registry().type_count_dict().keys()
    has_hd = "H" in sctr_keys or "D" in sctr_keys
  hbond_params = None
  if(params.secondary_structure_restraints):
    sec_str = mmtbx.secondary_structure.process_structure(
      params             = params.secondary_structure,
      processed_pdb_file = processed_pdb_file,
      tmp_dir            = os.getcwd(),
      log                = log,
      assume_hydrogens_all_missing=(not has_hd))
    sec_str.initialize(log=log)
    build_proxies = sec_str.create_hbond_proxies(
      log          = log,
      hbond_params = None)
    hbond_params = build_proxies.proxies
  geometry = processed_pdb_file.geometry_restraints_manager(
    show_energies                = False,
    show_nonbonded_clashscore    = False,
    params_edits                 = params.geometry_restraints.edits,
    plain_pairs_radius           = 5,
    hydrogen_bond_proxies        = hbond_params,
    assume_hydrogens_all_missing = not has_hd)
  restraints_manager = mmtbx.restraints.manager(
    geometry      = geometry,
    normalization = True)
  if(xray_structure is not None):
    restraints_manager.crystal_symmetry = xray_structure.crystal_symmetry()
  return restraints_manager

def run_minimization(
      selection,
      restraints_manager,
      pdb_hierarchy,
      params,
      cdl,
      correct_hydrogens,
      fix_rotamer_outliers,
      log):
  o = mmtbx.refinement.geometry_minimization.run2(
    restraints_manager             = restraints_manager,
    pdb_hierarchy                  = pdb_hierarchy,
    max_number_of_iterations       = params.max_iterations,
    number_of_macro_cycles         = params.macro_cycles,
    selection                      = selection,
    bond                           = params.move.bond,
    nonbonded                      = params.move.nonbonded,
    angle                          = params.move.angle,
    dihedral                       = params.move.dihedral,
    chirality                      = params.move.chirality,
    planarity                      = params.move.planarity,
    generic_restraints             = False,
    rmsd_bonds_termination_cutoff  = params.rmsd_bonds_termination_cutoff,
    rmsd_angles_termination_cutoff = params.rmsd_angles_termination_cutoff,
    alternate_nonbonded_off_on     = params.alternate_nonbonded_off_on,
    cdl                            = cdl,
    correct_hydrogens              = correct_hydrogens,
    fix_rotamer_outliers           = fix_rotamer_outliers,
    log                            = log)

def run_minimization_amber (
      sites_cart,
      selection,
      restraints_manager,
      pdb_hierarchy,
      params,
      log,
      prmtop,
      ambcrd):
  import amber_adaptbx.amber_geometry_minimization
  o = amber_adaptbx.amber_geometry_minimization.run(
    sites_cart                     = sites_cart,
    restraints_manager             = restraints_manager,
    pdb_hierarchy = pdb_hierarchy,
    max_number_of_iterations       = params.max_iterations,
    number_of_macro_cycles         = params.macro_cycles,
    selection                      = selection,
    bond                           = params.move.bond,
    nonbonded                      = params.move.nonbonded,
    angle                          = params.move.angle,
    dihedral                       = params.move.dihedral,
    chirality                      = params.move.chirality,
    planarity                      = params.move.planarity,
    generic_restraints             = False,
    grmsd_termination_cutoff       = params.grmsd_termination_cutoff,
    alternate_nonbonded_off_on     = params.alternate_nonbonded_off_on,
    log                            = log,
    prmtop                         = prmtop,
    ambcrd                         = ambcrd)

class run(object):
  _pdb_suffix = "minimized"
  def __init__(self, args, log, use_directory_prefix=True):
    self.log                = log
    self.params             = None
    self.inputs             = None
    self.args               = args
    self.processed_pdb_file = None
    self.xray_structure     = None
    self.pdb_hierarchy      = None
    self.selection          = None
    self.restrain_selection = None
    self.grm                = None
    self.time_strings       = []
    self.total_time         = 0
    self.output_file_name   = None
    self.pdb_file_names     = []
    self.use_directory_prefix = use_directory_prefix
    self.sites_cart_start  = None
    self.__execute()

  def __execute(self):
    #
    self.caller(self.initialize,           "Initialization, inputs")
    self.caller(self.process_inputs,       "Processing inputs")
    self.caller(self.atom_selection,       "Atom selection")
    self.caller(self.get_restraints,       "Geometry Restraints")
    self.caller(self.addcbetar,            "Add C-beta deviation restraints")
    self.caller(self.reference_restraints, "Add reference restraints")
    self.caller(self.minimization,         "Minimization")
    self.caller(self.write_pdb_file,       "Write PDB file")
    self.caller(self.write_geo_file,       "Write GEO file")
    #
    self.show_times()

  def master_params(self):
    return master_params()

  def caller(self, func, prefix):
    timer = user_plus_sys_time()
    func(prefix = prefix)
    t = timer.elapsed()
    self.total_time += t
    self.time_strings.append("  %s: %s"%(prefix, str("%8.3f"%t).strip()))

  def show_times(self):
    broadcast(m="Detailed timing", log = self.log)
    max_len = 0
    for ts in self.time_strings:
      lts = len(ts)
      if(lts > max_len): max_len = lts
    fmt = "  %-"+str(lts)+"s"
    for ts in self.time_strings:
      sts = ts.split()
      l = " ".join(sts[:len(sts)-1])
      print >> self.log, fmt%l, sts[len(sts)-1]
    print >> self.log, "  Sum of individual times: %s"%\
      str("%8.3f"%self.total_time).strip()

  def format_usage_message (self) :
    format_usage_message(log=self.log)

  def initialize(self, prefix):
    if (self.log is None) : self.log = sys.stdout
    if(len(self.args)==0):
      self.format_usage_message()
    parsed = self.master_params()
    self.inputs = mmtbx.utils.process_command_line_args(args = self.args,
      master_params = parsed)
    self.params = self.inputs.params.extract()
    if(self.params.silent): self.log = StringIO()
    broadcast(m=prefix, log = self.log)
    self.inputs.params.show(prefix="  ", out=self.log)
    if(len(self.args)==0): sys.exit(0)

  def process_inputs(self, prefix):
    broadcast(m=prefix, log = self.log)
    self.pdb_file_names = list(self.inputs.pdb_file_names)
    if(self.params.file_name is not None):
      self.pdb_file_names.append(self.params.file_name)
    self.processed_pdb_file = process_input_files(inputs=self.inputs,
      params=self.params, log=self.log)
    self.output_crystal_symmetry = \
      not self.processed_pdb_file.is_non_crystallographic_unit_cell
    self.xray_structure = self.processed_pdb_file.xray_structure()
    self.sites_cart_start = self.xray_structure.sites_cart().deep_copy()
    self.pdb_hierarchy = self.processed_pdb_file.all_chain_proxies.pdb_hierarchy

  def atom_selection(self, prefix):
    broadcast(m=prefix, log = self.log)
    self.selection = mmtbx.utils.atom_selection(
      all_chain_proxies = self.processed_pdb_file.all_chain_proxies,
      string = self.params.selection)
    print >> self.log, "  selected %s atoms out of total %s"%(
      str(self.selection.count(True)),str(self.selection.size()))
    self.generate_reference_restraints_selection()

  def generate_reference_restraints_selection(self):
    if(self.params.reference_restraints.\
       restrain_starting_coord_selection is not None):
      self.restrain_selection = mmtbx.utils.atom_selection(
        all_chain_proxies = self.processed_pdb_file.all_chain_proxies,
        string =
          self.params.reference_restraints.restrain_starting_coord_selection)
      self.exclude_outliers_from_reference_restraints_selection()

  def exclude_outliers_from_reference_restraints_selection(self):
    if(self.restrain_selection is not None):
      # ramachandran plot outliers
      rama_outlier_selection = ramalyze(pdb_hierarchy=self.pdb_hierarchy,
        outliers_only=False).outlier_selection()
      rama_outlier_selection = flex.bool(self.restrain_selection.size(),
        rama_outlier_selection)
      # rotamer outliers
      rota_outlier_selection = flex.size_t()
      rotamer_manager = RotamerEval() # slow!
      for model in self.pdb_hierarchy.models():
        for chain in model.chains():
          for residue_group in chain.residue_groups():
            conformers = residue_group.conformers()
            if(len(conformers)>1): continue
            for conformer in residue_group.conformers():
              residue = conformer.only_residue()
              if(rotamer_manager.evaluate_residue(residue)=="OUTLIER"):
                rota_outlier_selection.extend(residue.atoms().extract_i_seq())
      rota_outlier_selection = flex.bool(self.restrain_selection.size(),
        rota_outlier_selection)
      outlier_selection = rama_outlier_selection | rota_outlier_selection
      self.restrain_selection = self.restrain_selection & (~outlier_selection)

  def addcbetar(self, prefix):
    if(self.params.use_c_beta_deviation_restraints):
      broadcast(m=prefix, log = self.log)
      mmtbx.torsion_restraints.utils.add_c_beta_restraints(
        geometry      = self.grm.geometry,
        pdb_hierarchy = self.pdb_hierarchy,
        log           = self.log)

  def get_restraints(self, prefix):
    broadcast(m=prefix, log = self.log)
    self.grm = get_geometry_restraints_manager(
      processed_pdb_file = self.processed_pdb_file,
      xray_structure     = self.xray_structure,
      params             = self.params,
      log                = self.log)

  def reference_restraints(self, prefix):
    if(self.restrain_selection is not None):
      broadcast(m=prefix, log = self.log)
      restrain_sites_cart = self.xray_structure.sites_cart().deep_copy().\
        select(self.restrain_selection)
      self.grm.geometry.generic_restraints_manager.reference_manager.\
        add_coordinate_restraints(
          sites_cart = restrain_sites_cart,
          selection  = self.restrain_selection,
          #top_out_potential=True,
          sigma      = self.params.reference_restraints.coordinate_sigma)
      # sanity check
      assert self.grm.geometry.generic_restraints_manager.flags.reference is True
      assert self.grm.geometry.generic_restraints_manager.reference_manager.\
        reference_coordinate_proxies is not None
      assert len(self.grm.geometry.generic_restraints_manager.reference_manager.
        reference_coordinate_proxies) == len(restrain_sites_cart)

  def minimization(self, prefix): # XXX USE alternate_nonbonded_off_on etc
    broadcast(m=prefix, log = self.log)
    use_amber = False
    if hasattr(self.params, "amber"):
      use_amber = self.params.amber.use_amber
    if(use_amber):
      run_minimization_amber(
        sites_cart = sites_cart,
        selection = self.selection,
        restraints_manager = self.grm,
        params = self.params.minimization,
        pdb_hierarchy = self.pdb_hierarchy,
        log = self.log,
        prmtop = self.params.amber.topology_file_name,
        ambcrd = self.params.amber.coordinate_file_name)
    else:
      run_minimization(
        selection = self.selection,
        restraints_manager = self.grm, params = self.params.minimization,
        pdb_hierarchy = self.pdb_hierarchy,
        cdl=self.params.pdb_interpretation.cdl,
        correct_hydrogens=self.params.pdb_interpretation.correct_hydrogens,
        fix_rotamer_outliers = self.params.fix_rotamer_outliers,
        log = self.log)
    self.xray_structure.set_sites_cart(
      sites_cart = self.pdb_hierarchy.atoms().extract_xyz())

  def write_pdb_file(self, prefix):
    broadcast(m=prefix, log = self.log)
    self.pdb_hierarchy.adopt_xray_structure(self.xray_structure)
    ofn = self.params.output_file_name_prefix
    directory = self.params.directory
    suffix = "_" + self._pdb_suffix  + ".pdb"
    if(ofn is None):
      pfn = os.path.basename(self.pdb_file_names[0])
      ind = max(0,pfn.rfind("."))
      ofn = pfn+suffix if ind==0 else pfn[:ind]+suffix
    else: ofn = self.params.output_file_name_prefix+".pdb"
    if (self.use_directory_prefix) and (directory is not None) :
      ofn = os.path.join(directory, ofn)
    print >> self.log, "  output file name:", ofn
    print >> self.log, self.min_max_mean_shift()
    if (self.output_crystal_symmetry) :
      self.pdb_hierarchy.write_pdb_file(file_name = ofn, crystal_symmetry =
        self.xray_structure.crystal_symmetry())
    else :
      self.pdb_hierarchy.write_pdb_file(file_name = ofn)
    self.output_file_name = os.path.abspath(ofn)

  def min_max_mean_shift(self):
    return "min,max,mean shift from start: %6.3f %6.3f %6.3f"%flex.sqrt((
      self.sites_cart_start - self.xray_structure.sites_cart()).dot()
      ).min_max_mean().as_tuple()

  def write_geo_file(self, prefix):
    if(self.params.write_geo_file and self.grm is not None):
      broadcast(m=prefix, log = self.log)
      ofn = os.path.basename(self.output_file_name).replace(".pdb",".geo")
      directory = self.params.directory
      if (self.use_directory_prefix) and (directory is not None) :
        ofn = os.path.join(directory, ofn)
      f=file(ofn,"wb")
      print >> self.log, "  output file name:", ofn
      print >> f, "# Geometry restraints after refinement"
      print >> f
      xray_structure = self.xray_structure
      sites_cart = xray_structure.sites_cart()
      site_labels = xray_structure.scatterers().extract_labels()
      self.grm.geometry.show_sorted(
        sites_cart=sites_cart,
        site_labels=site_labels,
        f=f)
      f.close()

class launcher (runtime_utils.target_with_save_result) :
  def run (self) :
    os.mkdir(self.output_dir)
    os.chdir(self.output_dir)
    return run(args=self.args, log=sys.stdout,
      use_directory_prefix=False).output_file_name

def validate_params (params) :
  if (params.file_name is None) :
    raise Sorry("Please specify a model file to minimize.")
  if (params.restraints_directory is not None) :
    if (not os.path.isdir(params.restraints_directory)) :
      raise Sorry("The path '%s' does not exist or is not a directory." %
        params.restraints_directory)
  return True

def finish_job (result) :
  output_files = []
  if (result is not None) :
    output_files.append((result, "Minimized model"))
  return output_files, []

if(__name__ == "__main__"):
  timer = user_plus_sys_time()
  log = sys.stdout
  o = run(sys.argv[1:], log=log)
  tt = timer.elapsed()
  print >> o.log, "Overall runtime: %-8.3f" % tt
  assert abs(tt-o.total_time) < 0.1 # guard against unaccounted times
