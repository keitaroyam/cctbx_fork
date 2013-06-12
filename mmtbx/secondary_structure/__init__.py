
from __future__ import division
from mmtbx.secondary_structure import base_pairing, proteins
import iotbx.pdb
import iotbx.pdb.secondary_structure
import iotbx.phil
from scitbx.array_family import flex
from libtbx.utils import null_out
from libtbx import easy_run
from libtbx import adopt_init_args
import libtbx.load_env
import cStringIO
from math import sqrt
import sys, os

ss_restraint_params_str = """
  verbose = False
    .type = bool
  substitute_n_for_h = None
    .type = bool
    .short_caption = Substitute N for H atoms
    .style = tribool
  restrain_helices = True
    .type = bool
  alpha_only = False
    .type = bool
    .short_caption = Use alpha helices only
  restrain_sheets = True
    .type = bool
  restrain_base_pairs = True
    .type = bool
  remove_outliers = None
    .type = bool
    .short_caption = Filter bond outliers
    .style = tribool
  distance_ideal_n_o = 2.9
    .type = float
    .short_caption = Ideal N-O distance
  distance_cut_n_o = 3.5
    .type = float
    .short_caption = N-O distance cutoff
  distance_ideal_h_o = 1.975
    .type = float
    .short_caption = Ideal H-O distance
  distance_cut_h_o = 2.5
    .type = float
    .short_caption = H-O distance cutoff
  sigma = 0.05
    .type = float
  slack = 0.0
    .type = float
  top_out = False
    .type = bool
"""

ss_tardy_params_str = """\
  group_helix_backbone = False
    .style = bool
"""

ss_group_params_str = """%s\n%s""" % (proteins.helix_group_params_str,
  proteins.sheet_group_params_str)
ss_tardy_params_str = "" # XXX: remove this later

sec_str_master_phil_str = """
input
  .style = box auto_align
{
%s
  find_automatically = None
    .type = bool
    .style = bold tribool
  helices_from_phi_psi = False
    .type = bool
    .short_caption = Use phi/psi angles to identify helices
    .expert_level = 2
  force_nucleic_acids = False
    .type = bool
    .short_caption = Force base pair detection
    .help = This will ignore the automatic chain type detection and run \
      the base pair detection using PROBE even if no nucleic acids are found. \
      Useful for tRNAs which have a large number of modified bases.
  use_ksdssp = True
    .type = bool
    .help = Use KSDSSP program to annotate secondary structure.  If False, a \
      built-in DSSP method will be used instead.
    .expert_level = 3
}
h_bond_restraints
  .short_caption = Hydrogen bonding restraints
  .style = box auto_align
{
%s
}
%s
nucleic_acids
  .caption = If sigma and slack are not defined for nucleic acids, the \
    overall default settings for protein hydrogen bonds will be used \
    instead.
  .style = box auto_align noauto
{
  sigma = None
    .type = float
    .short_caption = Sigma for nucleic acid H-bonds
    .help = Defaults to global setting
  slack = None
    .type = float
    .short_caption = Slack for nucleic acid H-bonds
    .help = Defaults to global setting
  use_db_values = True
    .type = bool
    .short_caption = Use distances from Rutgers BPS database
#  planar = False
#    .type = bool
#    .short_caption = Use planar restraints by default
#    .style = noauto
  %s
}
""" % (iotbx.pdb.secondary_structure.ss_input_params_str,
       ss_restraint_params_str, ss_group_params_str,
       base_pairing.dna_rna_params_str)

sec_str_master_phil = iotbx.phil.parse(sec_str_master_phil_str)
default_params = sec_str_master_phil.fetch().extract()

def sec_str_from_phil (phil_str) :
  ss_phil = iotbx.phil.parse(phil_str)
  return sec_str_master_phil.fetch(source=ss_phil).extract()

def analyze_distances (self, params, pdb_hierarchy=None, log=sys.stderr) :
  atoms = None
  if params.verbose :
    assert pdb_hierarchy is not None
    atoms = pdb_hierarchy.atoms()
  remove_outliers = params.remove_outliers
  distance_max = params.h_o_distance_max
  distance_ideal = params.h_o_distance_ideal
  if params.substitute_n_for_h :
    distance_max = params.n_o_distance_max
    distance_ideal = params.n_o_distance_ideal
  atoms = pdb_hierarchy.atoms()
  hist =  flex.histogram(self.bond_lengths, 10)
  print >> log, "  Distribution of hydrogen bond lengths without filtering:"
  hist.show(f=log, prefix="    ", format_cutoffs="%.4f")
  print >> log, ""
  if not remove_outliers :
    return False
  for i, distance in enumerate(self.bond_lengths) :
    if distance > distance_max :
      self.flag_use_bond[i] = False
      if params.verbose :
        print >> log, "Excluding H-bond with length %.3fA" % distance
        i_seq, j_seq = self.bonds[i]
        print >> log, "  %s" % atoms[i_seq].fetch_labels().id_str()
        print >> log, "  %s" % atoms[j_seq].fetch_labels().id_str()
  print >> log, "  After filtering: %d bonds remaining." % \
    self.flag_use_bond.count(True)
  print >> log, "  Distribution of hydrogen bond lengths after applying cutoff:"
  hist = flex.histogram(self.bond_lengths.select(self.flag_use_bond), 10)
  hist.show(f=log, prefix="    ", format_cutoffs="%.4f")
  print >> log, ""
  return True

def hydrogen_bond_proxies_from_selections(
    pdb_hierarchy,
    params,
    use_hydrogens,
    as_python_objects=False,
    remove_outliers=False,
    master_selection=None,
    log=sys.stderr) :
  from mmtbx.geometry_restraints import hbond
  from scitbx.array_family import flex
  atoms = pdb_hierarchy.atoms()
  hbond_counts = flex.int(atoms.size(), 0)
  selection_cache = pdb_hierarchy.atom_selection_cache()
  if (master_selection is None) :
    master_selection = flex.bool(atoms.size(), True)
  elif (isinstance(master_selection, str)) :
    master_selection = selection_cache.seletion(master_selection)
  hbond_params = params.h_bond_restraints
  restrain_helices = params.h_bond_restraints.restrain_helices
  restrain_sheets = params.h_bond_restraints.restrain_sheets
  restrain_base_pairs = params.h_bond_restraints.restrain_base_pairs
  weight = 1.0
  distance_ideal = distance_cut = None
  if (use_hydrogens) :
    distance_ideal = hbond_params.distance_ideal_h_o
    distance_cut = hbond_params.distance_cut_h_o
  else :
    distance_ideal = hbond_params.distance_ideal_n_o
    distance_cut = hbond_params.distance_cut_n_o
  build_proxies = hbond.build_simple_hbond_proxies()
  if (as_python_objects) :
    build_proxies = hbond.build_distance_proxies()
  if (distance_cut is None) :
    distance_cut = -1
  if (restrain_helices) :
    for helix in params.helix :
      helix_class = helix.helix_type
      if helix_class != "alpha" and params.h_bond_restraints.alpha_only :
        print >> log, "  Skipping non-alpha helix (class %s):" % helix_class
        print >> log, "    %s" % helix.selection
        continue
      n_proxies = proteins.create_helix_hydrogen_bond_proxies(
        params=helix,
        pdb_hierarchy=pdb_hierarchy,
        selection_cache=selection_cache,
        build_proxies=build_proxies,
        weight=1.0,
        hbond_params=hbond_params,
        hbond_counts=hbond_counts,
        distance_ideal=distance_ideal,
        distance_cut=distance_cut,
        remove_outliers=remove_outliers,
        use_hydrogens=use_hydrogens,
        master_selection=master_selection,
        log=log)
      if (n_proxies == 0) :
        print >> log, "  No H-bonds generated for '%s'" % helix.selection
        continue
  if (restrain_sheets) :
    for k, sheet in enumerate(params.sheet) :
      n_proxies = proteins.create_sheet_hydrogen_bond_proxies(
        sheet_params=sheet,
        pdb_hierarchy=pdb_hierarchy,
        build_proxies=build_proxies,
        weight=1.0,
        hbond_params=hbond_params,
        hbond_counts=hbond_counts,
        distance_ideal=distance_ideal,
        distance_cut=distance_cut,
        remove_outliers=remove_outliers,
        use_hydrogens=use_hydrogens,
        master_selection=master_selection,
        log=log)
      if (n_proxies == 0) :
        print >> log, "  No H-bonds generated for sheet #%d" % k
        continue
  if (restrain_base_pairs) and (len(params.nucleic_acids.base_pair) > 0) :
    sigma = params.nucleic_acids.sigma
    if (sigma is None) :
      sigma = hbond_params.sigma
    slack = params.nucleic_acids.slack
    if (slack is None) :
      slack = hbond_params.slack
    base_pairing.identify_base_pairs(
      base_pairs=params.nucleic_acids.base_pair,
      pdb_hierarchy=pdb_hierarchy,
      use_hydrogens=use_hydrogens,
      distance_ideal=distance_ideal,
      use_db_values=(params.nucleic_acids.use_db_values and not use_hydrogens))
    n_proxies = base_pairing.create_hbond_proxies(
      build_proxies=build_proxies,
      base_pairs=params.nucleic_acids.base_pair,
      pdb_hierarchy=pdb_hierarchy,
      hbond_counts=hbond_counts,
      distance_ideal=distance_ideal,
      distance_cut=distance_cut,
      remove_outliers=remove_outliers,
      use_hydrogens=use_hydrogens,
      sigma=sigma,
      slack=slack,
      use_db_values=params.nucleic_acids.use_db_values,
      log=log)
    if (n_proxies == 0) :
      print >> log, "  No H-bonds generated for nucleic acids"
  return build_proxies

def _get_distances (bonds, sites_cart) :
  distances = flex.double(bonds.size(), -1)
  for k, (i_seq, j_seq) in enumerate(bonds) :
    (x1, y1, z1) = sites_cart[i_seq]
    (x2, y2, z2) = sites_cart[j_seq]
    dist = sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
    distances[k] = dist
  return distances

def get_pdb_hierarchy (file_names) :
  pdb_combined = iotbx.pdb.combine_unique_pdb_files(file_names=file_names)
  pdb_structure = iotbx.pdb.input(source_info=None,
    lines=flex.std_string(pdb_combined.raw_records))
  return pdb_structure.construct_hierarchy()

class manager (object) :
  def __init__ (self,
                pdb_hierarchy,
                sec_str_from_pdb_file=None,
                params=None,
                assume_hydrogens_all_missing=None,
                tmp_dir=None,
                verbose=-1) :
    adopt_init_args(self, locals())
    atoms = pdb_hierarchy.atoms()
    i_seqs = atoms.extract_i_seq()
    if (i_seqs.all_eq(0)) :
      atoms.reset_i_seq()
      i_seqs = atoms.extract_i_seq()
    self.n_atoms = atoms.size()
    self._was_initialized = False
    if self.params is None :
      self.params = sec_str_master_phil.fetch().extract()
    if self.tmp_dir is None :
      self.tmp_dir = os.getcwd()
    if self.assume_hydrogens_all_missing is None :
      elements = atoms.extract_element().strip()
      self.assume_hydrogens_all_missing = not ("H" in elements or
        "D" in elements)
    self.selection_cache = pdb_hierarchy.atom_selection_cache()
    self.pdb_atoms = atoms

  def as_phil_str (self, master_phil=sec_str_master_phil) :
    return master_phil.format(python_object=self.params)

  def initialize (self, log=sys.stderr) :
    if not self._was_initialized :
      self.find_automatically(log=log)
      self.show_summary(out=log)
      self._was_initialized = True

  def find_automatically (self, log=sys.stderr) :
    params = self.params
    find_automatically = params.input.find_automatically
    atom_labels = list(self.pdb_hierarchy.atoms_with_labels())
    segids = flex.std_string([ a.segid for a in atom_labels ])
    use_segid = not segids.all_eq('    ')
    # XXX: check for presence of protein first?
    if len(params.helix) == 0 and len(params.sheet) == 0 :
      if(self.verbose>0):
        print >> log, "No existing secondary structure definitions found."
      if (self.sec_str_from_pdb_file is None) and (find_automatically!=False) :
        if(self.verbose>0):
          print >> log, "No HELIX or SHEET records found in PDB file."
        find_automatically = True
    if find_automatically :
      if (use_segid) :
        self.sec_str_from_pdb_file = self.find_sec_str_with_segids(log=log)
      else :
        self.sec_str_from_pdb_file = self.find_sec_str(log=log)
    if (self.sec_str_from_pdb_file is not None) :
      if isinstance(self.sec_str_from_pdb_file, list) :
        if(self.verbose>0):
          print >> log, "  Interpreting HELIX and SHEET records for individual chains"
        ss_params = []
        for annotation, segid in self.sec_str_from_pdb_file :
          ss_phil = annotation.as_restraint_groups(log=log,
            prefix_scope="",
            add_segid=segid)
          ss_params.append(ss_phil)
        ss_params_str = "\n".join(ss_params)
      else :
        if(self.verbose>0):
          print >> log, "  Interpreting HELIX and SHEET records from PDB file"
        ss_params_str = self.sec_str_from_pdb_file.as_restraint_groups(log=log,
          prefix_scope="")
      self.apply_phil_str(ss_params_str, log=log)
    if (find_automatically) and (self.params.input.helices_from_phi_psi) :
      restraint_groups = self.find_approximate_helices(log=log)
      if (restraint_groups is not None) :
        self.params.helix = restraint_groups.helix
    # Step 2: nucleic acids
    if ((find_nucleic_acids(self.pdb_hierarchy) or
         params.input.force_nucleic_acids) and
        (params.h_bond_restraints.restrain_base_pairs)) :
      find_automatically = params.input.find_automatically
      if (len(params.nucleic_acids.base_pair) == 0) :
        if (find_automatically != False) :
          find_automatically = True
      if find_automatically :
        if (use_segid) :
          base_pairs = self.find_base_pairs_with_segids(log=log,
            force=params.input.force_nucleic_acids)
        else :
          base_pairs = self.find_base_pairs(log=log)
        if base_pairs is not None :
          bp_phil = iotbx.phil.parse(base_pairs)
          bp_params = sec_str_master_phil.fetch(source=bp_phil).extract()
          self.params.nucleic_acids.base_pair = \
            bp_params.nucleic_acids.base_pair

  def find_sec_str (self, log=sys.stderr) :
    if (self.params.input.use_ksdssp) :
      pdb_str = self.pdb_hierarchy.as_pdb_string()
      (records, stderr) = run_ksdssp_direct(pdb_str)
      return iotbx.pdb.secondary_structure.process_records(
        records=records,
        allow_none=True)
    else : # TODO make this the default
      from mmtbx.secondary_structure import dssp
      print >> log, "  running mmtbx.dssp..."
      return dssp.dssp(
        pdb_hierarchy=self.pdb_hierarchy,
        pdb_atoms=self.pdb_atoms,
        out=null_out()).get_annotation()

  def find_sec_str_with_segids (self, log=sys.stderr) :
    annotations = []
    for chain in self.pdb_hierarchy.models()[0].chains() :
      if not chain.conformers()[0].is_protein() :
        continue
      segid = chain.atoms()[0].segid
      detached_hierarchy = iotbx.pdb.hierarchy.new_hierarchy_from_chain(chain)
      pdb_str = detached_hierarchy.as_pdb_string()
      (records, stderr) = run_ksdssp_direct(pdb_str)
      sec_str_from_pdb_file = iotbx.pdb.secondary_structure.process_records(
        records=records,
        allow_none=True)
      if sec_str_from_pdb_file is not None :
        annotations.append((sec_str_from_pdb_file, segid))
    return annotations

  def find_approximate_helices (self, log=sys.stderr) :
    print >> log, "  Looking for approximately helical regions. . ."
    print >> log, "    warning: experimental, results not guaranteed to work!"
    find_helices = proteins.find_helices_simple(self.pdb_hierarchy)
    find_helices.show(out=log)
    restraint_groups = find_helices.as_restraint_groups()
    return restraint_groups

  def find_base_pairs (self, log=sys.stderr) :
    base_pairs = base_pairing.get_phil_base_pairs(
      pdb_hierarchy=self.pdb_hierarchy,
      prefix=None,
      log=log)
    return base_pairs

  def find_base_pairs_with_segids (self, log=sys.stderr, force=False) :
    annotations = []
    for chain in self.pdb_hierarchy.models()[0].chains() :
      if not force and not chain.conformers()[0].is_na() :
        continue
      segid = chain.atoms()[0].segid
      detached_hierarchy = iotbx.pdb.hierarchy.new_hierarchy_from_chain(chain)
      pdb_str = detached_hierarchy.as_pdb_string()
      base_pairs = base_pairing.get_phil_base_pairs(
        pdb_hierarchy=detached_hierarchy,
        prefix=None,
        log=log,
        add_segid=segid)
      if (base_pairs is not None) :
        annotations.append(base_pairs)
    return "\n".join(annotations)

  def apply_phil_str (self, phil_string, log=sys.stderr, verbose=False) :
    ss_phil = sec_str_master_phil.fetch(source=iotbx.phil.parse(phil_string))
    if verbose :
      ss_phil.show(out=log, prefix="    ")
    new_ss_params = ss_phil.extract()
    self.params.helix = new_ss_params.helix
    self.params.sheet = new_ss_params.sheet

  def apply_params (self, params) :
    self.params.helix = params.helix
    self.params.sheet = params.sheet

  def create_hbond_proxies (self,
                            log=sys.stdout,
                            hbond_params=None,
                            as_python_objects=False,
                            master_selection=None) :
    params = self.params
    remove_outliers = self.params.h_bond_restraints.remove_outliers
    # choice of atoms to restraint is a three-way option: default is to guess
    # based on whether hydrogens are present in the model, but this can be
    # misleading in some cases.
    if (self.params.h_bond_restraints.substitute_n_for_h is None) :
      use_hydrogens = (not self.assume_hydrogens_all_missing)
    elif (self.params.h_bond_restraints.substitute_n_for_h) :
      use_hydrogens = False
    else :
      use_hydrogens = True
    build_proxies = hydrogen_bond_proxies_from_selections(
      pdb_hierarchy=self.pdb_hierarchy,
      params=params,
      use_hydrogens=use_hydrogens,
      as_python_objects=as_python_objects,
      remove_outliers=remove_outliers,
      master_selection=master_selection,
      log=log)
    if isinstance(build_proxies.proxies, list) :
      n_proxies = len(build_proxies.proxies)
    else :
      n_proxies = build_proxies.proxies.size()
    print >> log, ""
    if (n_proxies == 0) :
      print >> log, "  No hydrogen bonds defined."
    else :
      print >> log, "  %d hydrogen bonds defined." % n_proxies
    return build_proxies

  def get_simple_bonds (self, selection_phil=None) :
    if (selection_phil is not None) :
      if isinstance(selection_phil, str) :
        selection_phil = iotbx.phil.parse(selection_phil)
      params = sec_str_master_phil.fetch(source=selection_phil).extract()
    else :
      params = self.params
    from mmtbx.geometry_restraints import hbond
    build_proxies = hydrogen_bond_proxies_from_selections(
      pdb_hierarchy=self.pdb_hierarchy,
      params=params,
      use_hydrogens=(not self.assume_hydrogens_all_missing),
      as_python_objects=True,
      remove_outliers=self.params.h_bond_restraints.remove_outliers,
      master_selection=None,
      log=cStringIO.StringIO())
    bonds = hbond.get_simple_bonds(build_proxies.proxies)
    return bonds

  def calculate_structure_content (self) :
    isel = self.selection_cache.iselection
    calpha = isel("name N and (altloc ' ' or altloc 'A')")
    alpha_sele = self.alpha_selection(limit="name N", main_conf_only=True)
    n_alpha = alpha_sele.count(True)
    beta_sele = self.beta_selection(limit="name N", main_conf_only=True)
    n_beta = beta_sele.count(True)
    if calpha.size() == 0 :
      return (0.0, 0.0)
    return (n_alpha / calpha.size(), n_beta / calpha.size())

  def show_summary (self, out=sys.stdout) :
    (frac_alpha, frac_beta) = self.calculate_structure_content()
    n_helices = len(self.params.helix)
    n_sheets  = len(self.params.sheet)
    print >> out, "Secondary structure from input PDB file:"
    print >> out, "  %d helices and %d sheets defined" % (n_helices,n_sheets)
    print >> out, "  %.1f%% alpha, %.1f%% beta" %(frac_alpha*100,frac_beta*100)

  def helix_selections (self, limit=None, main_conf_only=False,
      alpha_only=False) :
    sele = self.selection_cache.selection
    all_selections = []
    for helix in self.params.helix :
      if (helix.selection is not None) :
        if (alpha_only) and (helix.helix_type != "alpha") :
          continue
        clauses = [ "(%s)" % helix.selection ]
        if (limit is not None) :
          assert isinstance(limit, str)
          clauses.append("(%s)" % limit)
        if main_conf_only :
          clauses.append("(altloc ' ' or altloc 'A')")
        helix_sel = sele(" and ".join(clauses))
        all_selections.append(helix_sel)
    return all_selections

  def get_helix_types (self) :
    return [ helix.helix_type for helix in self.params.helix ]

  def helix_selection (self, **kwds) :
    whole_selection = flex.bool(self.n_atoms)
    for helix in self.helix_selections(**kwds) :
      whole_selection |= helix
    return whole_selection

  # FIXME backwards compatibility
  def alpha_selection (self, **kwds) :
    return self.helix_selection(**kwds)

  def alpha_selections (self, **kwds) :
    return self.helix_selections(**kwds)

  def beta_selections (self, limit=None, main_conf_only=False) :
    sele = self.selection_cache.selection
    all_selections = []
    for sheet in self.params.sheet :
      sheet_selection = flex.bool(self.n_atoms)
      clauses = []
      if (limit is not None) :
        assert isinstance(limit, str)
        clauses.append("(%s)" % limit)
      if main_conf_only :
        clauses.append("(altloc ' ' or altloc 'A')")
      main_clause = [ "(%s)" % sheet.first_strand ]
      strand_sel = sele(" and ".join(main_clause+clauses))
      sheet_selection |= strand_sel
      for strand in sheet.strand :
        main_clause = [ "(%s)" % strand.selection ]
        strand_sel = sele(" and ".join(main_clause+clauses))
        sheet_selection |= strand_sel
      all_selections.append(sheet_selection)
    return all_selections

  def beta_selection (self, **kwds) :
    whole_selection = flex.bool(self.n_atoms)
    for sheet in self.beta_selections(**kwds) :
      whole_selection |= sheet
    return whole_selection

  def base_pair_selections (self, limit=None, main_conf_only=False) :
    sele = self.selection_cache.selection
    all_selections = []
    for bp in self.params.nucleic_acids.base_pair :
      if (bp.base1 is not None) and (bp.base2 is not None) :
        clauses = [ "((%s) or (%s))" % (bp.base1, bp.base2) ]
        if (limit is not None) :
          clauses.append("(%s)" % limit)
        if main_conf_only :
          clauses.append("(altloc ' ' or altloc 'A')")
        bp_sele = sele(" and ".join(clauses))
        all_selections.append(bp_sele)
    return all_selections

  def base_pair_selection (self, **kwds) :
    whole_selection = flex.bool(self.n_atoms)
    for sheet in self.base_pair_selections(**kwds) :
      whole_selection |= sheet
    return whole_selection

  def selections_as_ints (self) :
    sec_str = flex.int(self.n_atoms, 0)
    all_alpha = flex.int(self.n_atoms, 1)
    all_beta = flex.int(self.n_atoms, 2)
    helices = self.alpha_selection()
    sheets = self.beta_selection()
    sec_str.set_selected(helices, all_alpha.select(helices))
    sec_str.set_selected(sheets, all_beta.select(sheets))
    return sec_str

def process_structure (params, processed_pdb_file, tmp_dir, log,
    assume_hydrogens_all_missing=None) :
  acp = processed_pdb_file.all_chain_proxies
  try :
    sec_str_from_pdb_file = acp.extract_secondary_structure()
  except Exception :
    sec_str_from_pdb_file = None
  pdb_hierarchy = acp.pdb_hierarchy
  structure_manager = manager(
    pdb_hierarchy=pdb_hierarchy,
    sec_str_from_pdb_file=sec_str_from_pdb_file,
    params=params,
    assume_hydrogens_all_missing=assume_hydrogens_all_missing,
    tmp_dir=tmp_dir)
  return structure_manager

def find_nucleic_acids (pdb_hierarchy) :
  for model in pdb_hierarchy.models() :
    for chain in model.chains() :
      for conformer in chain.conformers() :
        if conformer.is_na() :
          return True
  return False

def get_ksdssp_exe_path():
  if (not libtbx.env.has_module(name="ksdssp")):
    raise RuntimeError("ksdssp module is not configured")
  exe_path = libtbx.env.under_build("ksdssp/exe/ksdssp")
  if (os.name == "nt"):
    exe_path += ".exe"
  if (not os.path.isfile(exe_path)):
    raise RuntimeError("ksdssp executable is not available")
  return exe_path

def run_ksdssp (file_name, log=sys.stderr) :
  if not os.path.isfile(file_name) :
    raise RuntimeError("File %s not found.")
  exe_path = get_ksdssp_exe_path()
  print >> log, "  Running KSDSSP to generate HELIX and SHEET records"
  ksdssp_out = easy_run.fully_buffered(command="%s %s" % (exe_path, file_name))
#  if len(ksdssp_out.stderr_lines) > 0 :
#    print >> log, "\n".join(ksdssp_out.stderr_lines)
  return ksdssp_out.stdout_lines

def run_ksdssp_direct(pdb_str) :
  exe_path = get_ksdssp_exe_path()
  ksdssp_out = easy_run.fully_buffered(command=exe_path, stdin_lines=pdb_str)
  return ( ksdssp_out.stdout_lines, ksdssp_out.stderr_lines )

def manager_from_pdb_file (pdb_file) :
  from iotbx import file_reader
  assert os.path.isfile(pdb_file)
  pdb_in = file_reader.any_file(pdb_file, force_type="pdb")
  pdb_hierarchy = pdb_in.file_object.construct_hierarchy()
  pdb_hierarchy.atoms().reset_i_seq()
  ss_manager  = manager(pdb_hierarchy=pdb_hierarchy)
  return ss_manager

def calculate_structure_content (pdb_file) :
  ss_manager = manager_from_pdb_file(pdb_file)
  ss_manager.find_automatically()
  return ss_manager.calculate_structure_content()
