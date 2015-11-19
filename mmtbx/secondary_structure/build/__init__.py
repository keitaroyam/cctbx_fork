from __future__ import division
from scitbx.math import superpose
import iotbx.pdb
from cctbx.array_family import flex
from mmtbx.monomer_library import idealized_aa
from libtbx.utils import Sorry, null_out
from iotbx.pdb.amino_acid_codes import one_letter_given_three_letter as one_three
from iotbx.pdb.amino_acid_codes import three_letter_given_one_letter as three_one
from mmtbx.rotamer.rotamer_eval import RotamerEval
from mmtbx import secondary_structure
from mmtbx.pdbtools import truncate_to_poly_gly

alpha_helix_str = """
ATOM      1  N   GLY A   1      -5.606  -2.251 -12.878  1.00  0.00           N
ATOM      2  CA  GLY A   1      -5.850  -1.194 -13.852  1.00  0.00           C
ATOM      3  C   GLY A   1      -5.186  -1.524 -15.184  1.00  0.00           C
ATOM      4  O   GLY A   1      -5.744  -1.260 -16.249  1.00  0.00           O
ATOM      6  N   GLY A   2      -3.991  -2.102 -15.115  1.00  0.00           N
ATOM      7  CA  GLY A   2      -3.262  -2.499 -16.313  1.00  0.00           C
ATOM      8  C   GLY A   2      -3.961  -3.660 -17.011  1.00  0.00           C
ATOM      9  O   GLY A   2      -4.016  -3.716 -18.240  1.00  0.00           O
"""

a310_helix_str = """\
ATOM      1  N   GLY A   1       8.836  -4.233 -14.408  1.00  0.00           N
ATOM      2  CA  GLY A   1      10.232  -4.071 -14.799  1.00  0.00           C
ATOM      3  C   GLY A   1      10.764  -5.331 -15.476  1.00  0.00           C
ATOM      4  O   GLY A   1      11.679  -5.262 -16.297  1.00  0.00           O
ATOM      6  N   GLY A   2      10.176  -6.478 -15.143  1.00  0.00           N
ATOM      7  CA  GLY A   2      10.582  -7.741 -15.750  1.00  0.00           C
ATOM      8  C   GLY A   2      10.381  -7.714 -17.262  1.00  0.00           C
ATOM      9  O   GLY A   2      11.080  -8.410 -17.999  1.00  0.00           O
"""

pi_helix_str = """\
ATOM      1  N   GLY A   1      -3.365  -3.446  -8.396  1.00  0.00           N
ATOM      2  CA  GLY A   1      -4.568  -4.249  -8.592  1.00  0.00           C
ATOM      3  C   GLY A   1      -5.809  -3.386  -8.805  1.00  0.00           C
ATOM      4  O   GLY A   1      -6.559  -3.591  -9.759  1.00  0.00           O
ATOM      6  N   GLY A   2      -6.025  -2.424  -7.914  1.00  0.00           N
ATOM      7  CA  GLY A   2      -7.221  -1.588  -7.976  1.00  0.00           C
ATOM      8  C   GLY A   2      -7.101  -0.486  -9.025  1.00  0.00           C
ATOM      9  O   GLY A   2      -8.089  -0.114  -9.659  1.00  0.00           O
"""

beta_pdb_str = """
ATOM      1  N   GLY A   1      27.961   0.504   1.988  1.00  0.00           N
ATOM      2  CA  GLY A   1      29.153   0.205   2.773  1.00  0.00           C
ATOM      3  C   GLY A   1      30.420   0.562   2.003  1.00  0.00           C
ATOM      4  O   GLY A   1      30.753  -0.077   1.005  1.00  0.00           O
ATOM      6  N   GLY A   2      31.123   1.587   2.474  1.00  0.00           N
ATOM      7  CA  GLY A   2      32.355   2.031   1.832  1.00  0.00           C
ATOM      8  C   GLY A   2      33.552   1.851   2.758  1.00  0.00           C
ATOM      9  O   GLY A   2      33.675   2.539   3.772  1.00  0.00           O
"""

helix_class_to_pdb_str = {'alpha':alpha_helix_str,
                          'pi':pi_helix_str,
                          '3_10': a310_helix_str}

model_idealization_master_phil_str = """
model_idealization
{
  enabled = False
    .type = bool
    .help = Enable secondary structure idealization
  file_name_before_regularization = None
    .type = path
  restrain_torsion_angles = False
    .type = bool
    .help = Restrain torsion angles
  sigma_on_reference_non_ss = 1
    .type = float
    .help = Weight on original model coordinates restraints where no ss \
      present. Keeps loops close to initial model. \
      (bigger number gives lighter restraints)
  sigma_on_reference_helix = 1
    .type = float
    .help = Weight on original model coordinates restraints where helix \
      present. Bends helices a bit according to initial model. \
      (bigger number gives lighter restraints)
  sigma_on_reference_sheet = 0.5
    .type = float
    .help = Weight on original model coordinates restraints where sheet \
      present. Bends helices a bit according to initial model. \
      (bigger number gives lighter restraints)
  sigma_on_torsion_ss = 5
    .type = float
    .help = Weight on torsion angles restraints where ss present. \
      Keeps helices torsion angles close to ideal. \
      (bigger number gives lighter restraints)
  sigma_on_torsion_nonss = 5
    .type = float
  sigma_on_ramachandran = 1
    .type = float
  sigma_on_cbeta = 2.5
    .type = float
  n_macro=3
    .type = int
  n_iter=300
    .type = int
}
"""

master_phil = iotbx.phil.parse(model_idealization_master_phil_str)

def print_hbond_proxies(geometry, hierarchy, pymol=False):
  """ Print hydrogen bonds in geometry restraints manager for debugging
  purposes"""
  assert 0, "need to rewrite due to reorganization of GRM"
  atoms = hierarchy.atoms()
  if pymol:
    dashes = open('dashes.pml', 'w')
  hbondlen=flex.double()
  for hb in geometry.generic_restraints_manager.hbonds_as_simple_bonds():
    hbondlen.append(atoms[hb[0]].distance(atoms[hb[1]]))
    print (atoms[hb[0]].id_str(), "<====>",atoms[hb[1]].id_str(),
        atoms[hb[0]].distance(atoms[hb[1]]), hb[0], hb[1])
    if pymol:
      s1 = atoms[hb[0]].id_str()
      s2 = atoms[hb[1]].id_str()
      #print "pdbstr1:", s1
      #print "pdbstr1:",s2
      ps = "dist chain \"%s\" and resi %s and name %s, chain \"%s\" and resi %s and name %s\n" % (s1[14:15],
         s1[16:19], s1[5:7], s2[14:15], s2[16:19], s2[5:7])
      dashes.write(ps)
  print "min, max, mean, sd hbond lenghts", hbondlen.min_max_mean().as_tuple(),\
    hbondlen.standard_deviation_of_the_sample()
  if pymol:
    dashes.close()

def get_r_t_matrices_from_structure(pdb_str):
  """ Return rotation and translation matrices for the ideal structure.

  The function determines r and t matrices from alingment of 1st and 2nd
  residues of the structure passed in pdb_str.
  """
  pdb_hierarchy = iotbx.pdb.input(source_info=None, lines=pdb_str).\
    construct_hierarchy()
  conformer = pdb_hierarchy.models()[0].chains()[0].conformers()[0]
  residues = conformer.residues()
  fixed_sites = flex.vec3_double()
  moving_sites = flex.vec3_double()
  main_chain_atoms = ["N","CA","C","O"]
  if len(residues)>=2:
    for (r, arr) in [(residues[0], fixed_sites), (residues[1], moving_sites)]:
      for a in r.atoms():
        if a.name.strip() in main_chain_atoms:
          arr.append(a.xyz)
  else:
    raise Sorry('pdb_str should contain at least 2 residues')
  lsq_fit_obj = superpose.least_squares_fit(reference_sites = moving_sites,
                                            other_sites = fixed_sites)
  return lsq_fit_obj.r, lsq_fit_obj.t


def side_chain_placement(ag_to_place, current_reference_ag, rotamer_manager):
  """
  Works with poly_gly truncated hierarchy.
  Also used in fix_rama_outliers.
  """
  resname = current_reference_ag.resname.upper()
  c = one_three.get(resname, None)
  if c is None:
    msg = "Only standard protein residues are currently supported.\n"
    msg += "The residue %s (chain %s, resid %s) chain is not standard." % (
        resname,
        current_reference_ag.parent().parent().id,
        current_reference_ag.parent().resid())
    raise Sorry(msg)
  ag_to_place.resname = three_one[c]
  if c == 'G':
    return

  # align residue from ideal_res_dict to just placed ALA (ag_to_place)
  # or from pdb_hierarchy_template
  fixed_sites = flex.vec3_double()
  moving_sites = flex.vec3_double()
  reper_atoms = ["C","CA", "N"]
  for (ag, arr) in [(ag_to_place, fixed_sites),
                    (current_reference_ag, moving_sites)]:
    for a in ag.atoms():
      if a.name.strip() in reper_atoms:
        arr.append(a.xyz)
  lsq_fit_obj = superpose.least_squares_fit(reference_sites = fixed_sites,
                                            other_sites = moving_sites)
  ideal_correct_ag = current_reference_ag.detached_copy()
  ideal_correct_ag.atoms().set_xyz(
      lsq_fit_obj.r.elems*ideal_correct_ag.atoms().extract_xyz()+\
      lsq_fit_obj.t.elems)
  ideal_correct_ag.atoms().set_xyz(
      rotamer_manager.nearest_rotamer_sites_cart(ideal_correct_ag))
  ag_to_place.pre_allocate_atoms(number_of_additional_atoms=\
                                              len(ideal_correct_ag.atoms())-5)
  for a in ideal_correct_ag.atoms():
    if a.name.strip() not in ["N","CA","C","O"]:
      at = a.detached_copy()
      at.uij_erase()
      ag_to_place.append_atom(atom=at)


def secondary_structure_from_sequence(pdb_str,
      sequence=None,
      pdb_hierarchy_template=None,
      rotamer_manager=None):
  """ Return pdb.hierarchy with secondary structure according to sequence or
  reference hierarcy. If reference hierarchy provided, the resulting hierarchy
  will be rigid body aligned to it. Residue numbers will start from 1.

  pdb_str - "ideal" structure at least 2 residues long.
  sequence - string with sequence (one-letter codes)
  pdb_hierarchy_template - reference hierarchy.
  """
  if rotamer_manager is None:
    rotamer_manager = RotamerEval()
  pht = pdb_hierarchy_template
  assert [sequence, pht].count(None) == 1
  if pht is not None:
    lk = len(pht.altloc_indices().keys())
    if lk ==0:
      raise Sorry(
          "Hierarchy template in secondary_structure_from_sequence is empty")
    else:
      assert len(pht.altloc_indices().keys()) == 1, \
          "Alternative conformations are not supported"
  number_of_residues = len(sequence) if sequence!=None else \
    len(pht.models()[0].chains()[0].conformers()[0].residues())
  if number_of_residues<1:
    raise Sorry('sequence should contain at least one residue.')
  ideal_res_dict = idealized_aa.residue_dict()
  real_res_list = None
  if pht:
    real_res_list = pht.models()[0].chains()[0].residue_groups()
  pdb_hierarchy = iotbx.pdb.input(source_info=None, lines=pdb_str).\
      construct_hierarchy()
  truncate_to_poly_gly(pdb_hierarchy)
  chain = pdb_hierarchy.models()[0].chains()[0]
  current_gly_ag = chain.residue_groups()[0].atom_groups()[0]
  new_chain = iotbx.pdb.hierarchy.chain(id="A")
  new_chain.pre_allocate_residue_groups(number_of_additional_residue_groups=\
                                                            number_of_residues)
  r, t = get_r_t_matrices_from_structure(pdb_str)
  for j in range(number_of_residues):
    # put ALA
    rg = iotbx.pdb.hierarchy.residue_group(icode="")
    rg.resseq = j+1
    new_chain.append_residue_group(residue_group=rg)
    ag_to_place = current_gly_ag.detached_copy()
    rg.append_atom_group(atom_group=ag_to_place)
    current_gly_ag.atoms().set_xyz(
                          r.elems*current_gly_ag.atoms().extract_xyz()+t.elems)
    current_reference_ag = real_res_list[j].atom_groups()[0] if pht else \
        ideal_res_dict[three_one[sequence[j]].lower()].models()[0].chains()[0].\
        residue_groups()[0].atom_groups()[0]
    side_chain_placement(ag_to_place, current_reference_ag, rotamer_manager)
  new_pdb_h = iotbx.pdb.hierarchy.new_hierarchy_from_chain(new_chain)
  # align to real
  if pht != None:
    fixed_sites = pht.atoms().extract_xyz()
    moving_sites = new_pdb_h.atoms().extract_xyz()
    assert len(fixed_sites) == len(moving_sites)
    lsq_fit_obj = superpose.least_squares_fit(reference_sites = fixed_sites,
                                              other_sites = moving_sites)
    new_pdb_h.atoms().set_xyz(
        lsq_fit_obj.r.elems*new_pdb_h.atoms().extract_xyz()+lsq_fit_obj.t.elems)
  return new_pdb_h

def get_helix(helix_class, rotamer_manager, sequence=None, pdb_hierarchy_template=None):
  if helix_class not in helix_class_to_pdb_str.keys():
    raise Sorry("Unsupported helix type.")
  return secondary_structure_from_sequence(
    pdb_str=helix_class_to_pdb_str[helix_class],
    sequence=sequence,
    rotamer_manager=rotamer_manager,
    pdb_hierarchy_template=pdb_hierarchy_template)

def calculate_rmsd_smart(h1, h2):
  assert h1.atoms().size() == h2.atoms().size()
  rmsd = 0
  for atom in h1.atoms():
    for c in h2.chains():
      if c.id != atom.parent().parent().parent().id:
        continue
      for rg in c.residue_groups():
        if (rg.resseq, rg.icode) != (atom.parent().parent().resseq, atom.parent().parent().icode):
          continue
        for ag in rg.atom_groups():
          if (ag.resname, ag.altloc) != (atom.parent().resname, atom.parent().altloc):
            continue
          a = ag.get_atom(atom.name.strip())
          if a is not None:
            rmsd += a.distance(atom)**2
  return rmsd ** 0.5

def set_xyz_smart(dest_h, source_h):
  """
  Even more careful setting of coordinates than set_xyz_carefully below
  """
  assert dest_h.atoms().size() >= source_h.atoms().size()
  for atom in source_h.atoms():
    for c in dest_h.chains():
      if c.id != atom.parent().parent().parent().id:
        continue
      for rg in c.residue_groups():
        if (rg.resseq, rg.icode) != (atom.parent().parent().resseq, atom.parent().parent().icode):
          continue
        for ag in rg.atom_groups():
          if (ag.resname, ag.altloc) != (atom.parent().resname, atom.parent().altloc):
            continue
          # print "atom name", atom.name
          a = ag.get_atom(atom.name.strip())
          if a is not None:
            # print "actually setting coordinates:", a.xyz, "->", atom.xyz
            a.set_xyz(atom.xyz)

def set_xyz_carefully(dest_h, source_h):
  assert dest_h.atoms().size() >= source_h.atoms().size()
  for d_ag, s_ag in zip(dest_h.atom_groups(), source_h.atom_groups()):
    for s_atom in s_ag.atoms():
      d_atom = d_ag.get_atom(s_atom.name.strip())
      if d_atom is not None:
        d_atom.set_xyz(s_atom.xyz)

def get_empty_ramachandran_proxies():
  import boost.python
  ext = boost.python.import_ext("mmtbx_ramachandran_restraints_ext")
  proxies = ext.shared_phi_psi_proxy()
  return proxies

def process_params(params):
  min_sigma = 1e-5
  if params is None:
    params = master_phil.fetch().extract()
    params.model_idealization.enabled = True
  if hasattr(params, "model_idealization"):
    p_pars = params.model_idealization
  else:
    assert hasattr(params, "enabled") and hasattr(params, "sigma_on_cbeta"), \
        "Something wrong with parameters passed to model_idealization"
    p_pars = params
  assert isinstance(p_pars.enabled, bool)
  assert isinstance(p_pars.restrain_torsion_angles, bool)
  for par in ["sigma_on_reference_non_ss",
      "sigma_on_reference_helix", "sigma_on_reference_sheet",
      "sigma_on_torsion_ss", "sigma_on_torsion_nonss", "sigma_on_ramachandran",
      "sigma_on_cbeta"]:
    assert (isinstance(getattr(p_pars, par), float) and \
      getattr(p_pars, par) > min_sigma), "" + \
      "Bad %s parameter" % par
  for par in ["n_macro", "n_iter"]:
    assert (isinstance(getattr(p_pars, par), int) and \
      getattr(p_pars, par) >= 0), ""+ \
      "Bad %s parameter" % par
  return p_pars


def substitute_ss(real_h,
                    xray_structure,
                    ss_annotation,
                    params = None,
                    cif_objects=None,
                    log=null_out(),
                    rotamer_manager=None,
                    verbose=False):
  """
  Substitute secondary structure elements in real_h hierarchy with ideal
  ones _in_place_.
  Returns reference torsion proxies - the only thing that cannot be restored
  with little effort outside the procedure.
  real_h - hierarcy to substitute secondary structure elements.
  xray_structure - xray_structure - needed to get crystal symmetry (to
      construct processed_pdb_file and xray_structure is needed to call
      get_geometry_restraints_manager for no obvious reason).
  ss_annotation - iotbx.pdb.annotation object.
  """
  if rotamer_manager is None:
    rotamer_manager = RotamerEval()
  for model in real_h.models():
    for chain in model.chains():
      if len(chain.conformers()) > 1:
        raise Sorry("Alternative conformations are not supported.")

  processed_params = process_params(params)
  if not processed_params.enabled:
    return None

  expected_n_hbonds = 0
  ann = ss_annotation
  phil_str = ann.as_restraint_groups()
  for h in ann.helices:
    expected_n_hbonds += h.get_n_maximum_hbonds()
  edited_h = real_h.deep_copy()
  n_atoms_in_real_h = real_h.atoms().size()
  selection_cache = real_h.atom_selection_cache()
  # check the annotation for correctness (atoms are actually in hierarchy)
  error_msg = "The following secondary structure annotations result in \n"
  error_msg +="empty atom selections. They don't match the structre: \n"
  error_flg = False

  # Checking for SS selections
  for h in ann.helices:
    selstring = h.as_atom_selections()
    isel = selection_cache.iselection(selstring[0])
    if len(isel) == 0:
      error_flg = True
      error_msg += "  %s\n" % h
  for sh in ann.sheets:
    for st in sh.strands:
      selstring = st.as_atom_selections()
      isel = selection_cache.iselection(selstring)
      if len(isel) == 0:
        error_flg = True
        error_msg += "  %s\n" % sh.as_pdb_str(strand_id=st.strand_id)
  if error_flg:
    raise Sorry(error_msg)

  # Actually idelizing SS elements
  log.write("Replacing ss-elements with ideal ones:\n")
  for h in ann.helices:
    log.write("  %s\n" % h.as_pdb_str())
    selstring = h.as_atom_selections()
    isel = selection_cache.iselection(selstring[0])
    all_bsel = flex.bool(n_atoms_in_real_h, False)
    all_bsel.set_selected(isel, True)
    sel_h = real_h.select(all_bsel, copy_atoms=True)
    ideal_h = get_helix(helix_class=h.helix_class,
                        pdb_hierarchy_template=sel_h,
                        rotamer_manager=rotamer_manager)
    # edited_h.select(all_bsel).atoms().set_xyz(ideal_h.atoms().extract_xyz())
    set_xyz_carefully(dest_h=edited_h.select(all_bsel), source_h=ideal_h)
  for sh in ann.sheets:
    s = "  %s\n" % sh.as_pdb_str()
    ss = s.replace("\n", "\n  ")
    log.write(ss[:-2])
    for st in sh.strands:
      selstring = st.as_atom_selections()
      isel = selection_cache.iselection(selstring)
      all_bsel = flex.bool(n_atoms_in_real_h, False)
      all_bsel.set_selected(isel, True)
      sel_h = real_h.select(all_bsel, copy_atoms=True)
      ideal_h = secondary_structure_from_sequence(
          pdb_str=beta_pdb_str,
          sequence=None,
          pdb_hierarchy_template=sel_h,
          rotamer_manager=rotamer_manager,
          )
      set_xyz_carefully(edited_h.select(all_bsel), ideal_h)
      # edited_h.select(all_bsel).atoms().set_xyz(ideal_h.atoms().extract_xyz())

  pre_result_h = edited_h
  pre_result_h.reset_i_seq_if_necessary()
  n_atoms = real_h.atoms().size()
  bsel = flex.bool(n_atoms, False)
  helix_selection = flex.bool(n_atoms, False)
  sheet_selection = flex.bool(n_atoms, False)
  other_selection = flex.bool(n_atoms, False)
  ss_for_tors_selection = flex.bool(n_atoms, False)
  nonss_for_tors_selection = flex.bool(n_atoms, False)
  selection_cache = real_h.atom_selection_cache()
  # set all CA atoms to True for other_selection
  #isel = selection_cache.iselection("name ca")
  isel = selection_cache.iselection("name ca or name n or name o or name c")
  other_selection.set_selected(isel, True)
  n_main_chain_atoms = other_selection.count(True)
  isel = selection_cache.iselection("name ca or name n or name o or name c")
  nonss_for_tors_selection.set_selected(isel, True)
  main_chain_selection_prefix = "(name ca or name n or name o or name c) %s"

  # Here we are just preparing selections
  for h in ann.helices:
    ss_sels = h.as_atom_selections()[0]
    selstring = main_chain_selection_prefix % ss_sels
    isel = selection_cache.iselection(selstring)
    helix_selection.set_selected(isel, True)
    other_selection.set_selected(isel, False)
    isel = selection_cache.iselection(selstring)
    ss_for_tors_selection.set_selected(isel, True)
    nonss_for_tors_selection.set_selected(isel, False)

  for sheet in ann.sheets:
    for ss_sels in sheet.as_atom_selections():
      selstring = main_chain_selection_prefix % ss_sels
      isel = selection_cache.iselection(selstring)
      sheet_selection.set_selected(isel, True)
      other_selection.set_selected(isel, False)
      isel = selection_cache.iselection(selstring)
      ss_for_tors_selection.set_selected(isel, True)
      nonss_for_tors_selection.set_selected(isel, False)
  isel = selection_cache.iselection(
      "not name ca and not name n and not name o and not name c")
  other_selection.set_selected(isel, False)
  helix_sheet_intersection = helix_selection & sheet_selection
  if helix_sheet_intersection.count(True) > 0:
    sheet_selection = sheet_selection & ~helix_sheet_intersection
  assert ((helix_selection | sheet_selection) & other_selection).count(True)==0

  from mmtbx.monomer_library.pdb_interpretation import grand_master_phil_str
  params_line = grand_master_phil_str
  params_line += "secondary_structure {%s}" % secondary_structure.sec_str_master_phil_str
  params = iotbx.phil.parse(input_string=params_line, process_includes=True)
  custom_pars = params.fetch(source = iotbx.phil.parse("\n".join([
      "pdb_interpretation.secondary_structure {protein.remove_outliers = False\n%s}" \
          % phil_str,
      "pdb_interpretation.peptide_link.ramachandran_restraints = True",
      "c_beta_restraints = True",
      "pdb_interpretation.secondary_structure.enabled=True"]))).extract()

  import mmtbx.utils
  processed_pdb_files_srv = mmtbx.utils.\
      process_pdb_file_srv(
          crystal_symmetry= xray_structure.crystal_symmetry(),
          pdb_interpretation_params = custom_pars.pdb_interpretation,
          log=null_out(),
          cif_objects=cif_objects)
  if verbose:
    print >> log, "Processing file..."
  processed_pdb_file, junk = processed_pdb_files_srv.\
      process_pdb_files(raw_records=flex.split_lines(real_h.as_pdb_string()))
  has_hd = None
  if(xray_structure is not None):
    sctr_keys = xray_structure.scattering_type_registry().type_count_dict().keys()
    has_hd = "H" in sctr_keys or "D" in sctr_keys
  if verbose:
    print >> log, "Getting geometry_restraints_manager..."
  geometry = processed_pdb_file.geometry_restraints_manager(
    show_energies                = False,
    params_edits                 = custom_pars.geometry_restraints.edits,
    plain_pairs_radius           = 5,
    assume_hydrogens_all_missing = not has_hd)
  restraints_manager = mmtbx.restraints.manager(
    geometry      = geometry,
    normalization = True)
  if(xray_structure is not None):
    restraints_manager.crystal_symmetry = xray_structure.crystal_symmetry()
  grm = restraints_manager

  real_h.reset_i_seq_if_necessary()
  if verbose:
    print >> log, "Adding reference coordinate restraints..."
  from mmtbx.geometry_restraints import reference
  grm.geometry.append_reference_coordinate_restraints_in_place(
      reference.add_coordinate_restraints(
          sites_cart = real_h.atoms().extract_xyz().select(helix_selection),
          selection  = helix_selection,
          sigma      = processed_params.sigma_on_reference_helix))
  grm.geometry.append_reference_coordinate_restraints_in_place(
      reference.add_coordinate_restraints(
          sites_cart = real_h.atoms().extract_xyz().select(sheet_selection),
          selection  = sheet_selection,
          sigma      = processed_params.sigma_on_reference_sheet))
  grm.geometry.append_reference_coordinate_restraints_in_place(
      reference.add_coordinate_restraints(
          sites_cart = real_h.atoms().extract_xyz().select(other_selection),
          selection  = other_selection,
          sigma      = processed_params.sigma_on_reference_non_ss))
  if verbose:
    print >> log, "Adding chi torsion restraints..."
  grm.geometry.add_chi_torsion_restraints_in_place(
          pdb_hierarchy   = pre_result_h,
          sites_cart      = pre_result_h.atoms().extract_xyz().\
                                 select(ss_for_tors_selection),
          selection = ss_for_tors_selection,
          chi_angles_only = False,
          sigma           = processed_params.sigma_on_torsion_ss)
  grm.geometry.add_chi_torsion_restraints_in_place(
          pdb_hierarchy   = pre_result_h,
          sites_cart      = real_h.atoms().extract_xyz().\
                                select(nonss_for_tors_selection),
          selection = nonss_for_tors_selection,
          chi_angles_only = False,
          sigma           = processed_params.sigma_on_torsion_nonss)

  real_h.atoms().set_xyz(pre_result_h.atoms().extract_xyz())
  if processed_params.file_name_before_regularization is not None:
    print >> log, "Outputting model before regularization %s" % processed_params.file_name_before_regularization
    real_h.write_pdb_file(
        file_name=processed_params.file_name_before_regularization)

  #testing number of restraints
  assert grm.geometry.get_n_den_proxies() == 0
  assert grm.geometry.get_n_reference_coordinate_proxies() == n_main_chain_atoms
  # f = open("before.geo", "w")
  # grm.geometry.show_sorted(
  #     site_labels=[atom.id_str() for atom in real_h.atoms()],
  #     f=f)
  # f.close()
  refinement_log = null_out()
  log.write(
      "Refining geometry of substituted secondary structure elements...")
  if verbose:
    refinement_log = log
  from mmtbx.refinement.geometry_minimization import run2
  obj = run2(
      restraints_manager       = grm,
      pdb_hierarchy            = real_h,
      correct_special_position_tolerance = 1.0,
      max_number_of_iterations = processed_params.n_iter,
      number_of_macro_cycles   = processed_params.n_macro,
      bond                     = True,
      nonbonded                = True,
      angle                    = True,
      dihedral                 = True,
      chirality                = True,
      planarity                = True,
      fix_rotamer_outliers     = False,
      log                      = refinement_log)
  log.write(" Done\n")

  #print_hbond_proxies(grm.geometry,real_h)
  return grm.geometry.get_chi_torsion_proxies()


def beta():
  pdb_hierarchy = secondary_structure_from_sequence(beta_pdb_str,
      "ACEDGFIHKMLNQPSRTWVY")
  pdb_hierarchy.write_pdb_file(file_name = "o_beta_seq.pdb")

def alpha_310():
  pdb_hierarchy = secondary_structure_from_sequence(alpha310_pdb_str,
      "ACEDGFIHKMLNQPSRTWVY")
  pdb_hierarchy.write_pdb_file(file_name = "o_helix310_seq.pdb")

def alpha_pi():
  pdb_hierarchy = secondary_structure_from_sequence(alpha_pi_pdb_str,
      "ACEDGFIHKMLNQPSRTWVY")
  pdb_hierarchy.write_pdb_file(file_name = "o_helix_pi_seq.pdb")

def alpha():
  pdb_hierarchy = secondary_structure_from_sequence(alpha_pdb_str,
      "ACEDGFIHKMLNQPSRTWVY")
  pdb_hierarchy.write_pdb_file(file_name = "o_helix_seq.pdb")
