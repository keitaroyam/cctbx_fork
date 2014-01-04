
from __future__ import division
from libtbx.str_utils import make_sub_header
from libtbx.utils import Sorry
from libtbx import group_args
import libtbx.phil
from math import sqrt
import sys

#-----------------------------------------------------------------------
# MODEL UTILITIES

def multi_conformer_selection (pdb_hierarchy) :
  from scitbx.array_family import flex
  atoms = pdb_hierarchy.atoms()
  selection = flex.size_t()
  assert (not atoms.extract_i_seq().all_eq(0))
  for chain in pdb_hierarchy.only_model().chains( ):
    for residue_group in chain.residue_groups() :
      atom_groups = residue_group.atom_groups()
      if ((len(atom_groups) > 1) or (atom_groups[0].altloc.strip() != '')) :
        selection.extend(residue_group.atoms().extract_i_seq())
  return selection

def fragment_single_conformer_chain (residues, chain_break_distance=3.0) :
  """
  Split a protein chain into continuous peptide fragments (as lists of
  residue_group objects).
  """
  from scitbx.matrix import col
  k = 0
  current_fragment = []
  fragments = [ current_fragment ]
  while (k < len(residues)) :
    res = residues[k]
    resseq = res.resseq_as_int()
    next_res = prev_res = None
    if (k > 0) :
      prev_res = residues[k-1]
    if (k < len(residues) - 1) :
      next_res = residues[k+1]
    k += 1
    if (prev_res is not None) :
      prev_resseq = prev_res.resseq_as_int()
      c_atom = n_atom = None
      for atom in prev_res.atom_groups()[0].atoms() :
        if (atom.name.strip() == "C") :
          c_atom = col(atom.xyz)
          break
      for atom in res.atom_groups()[0].atoms() :
        if (atom.name.strip() == "N") :
          n_atom = col(atom.xyz)
          break
      if ((resseq > prev_resseq + 1) or
          (None in [n_atom, c_atom]) or
          (abs(n_atom-c_atom) > chain_break_distance)) :
        current_fragment = [ res ]
        fragments.append(current_fragment)
        continue
    current_fragment.append(res)
  return fragments

def get_selection_gap (sel1, sel2) :
  """
  Compute the gap or overlap between two selections (order-independent).
  Returns 0 if the selections are directly adjacent, or the number of
  residues overlapped (as a negative number) or missing between the
  selections (positive).
  """
  if (type(sel1).__name__ == 'bool') :
    sel1 = sel1.iselection()
  if (type(sel2).__name__ == 'bool') :
    sel2 = sel2.iselection()
  if (sel1[-1] == sel2[0] -1) or (sel2[-1] == sel1[0] - 1) :
    return 0
  elif (sel2[-1] >= sel1[0] >= sel2[0]) :
    return sel1[0] - sel2[-1] - 1
  elif (sel1[-1] >= sel2[0] >= sel1[0]) :
    return sel2[0] - sel1[-1] - 1
  else :
    return max(sel2[0] - sel1[-1] - 1, sel1[0] - sel2[-1] - 1)

def score_rotamers (hierarchy, selection) :
  """
  Count the number of rotamer outliers from a selection of residues in a
  PDB hierarchy.
  """
  from mmtbx.rotamer import rotamer_eval
  r = rotamer_eval.RotamerEval()
  n_outliers = 0
  sub_hierarchy = hierarchy.select(selection) # XXX probably inefficient
  for rg in sub_hierarchy.only_model().only_chain().residue_groups() :
    rotamer_flag = r.evaluate_residue(rg.only_atom_group())
    if (rotamer_flag == "OUTLIER") :
      n_outliers += 1
  return n_outliers

symmetric_atom_names = [
  ("OD1", "OD2"),
  ("OE1", "OE2"),
  ("OD1", "ND2"),
  ("OE1", "NE2"),
  ("CD1", "CD2"),
  ("CE1", "CE2"),
]
symmetric_atom_names_dict = dict(symmetric_atom_names +
    [ (n2,n1) for (n1,n2) in symmetric_atom_names ])

def coord_stats_with_flips (sites1, sites2, atoms) :
  """
  Calculate RMSD and maximum distance for a pair of coordinate arrays,
  taking into account the symmetric or pseudo-symmetric nature of many
  sidechains.
  """
  from scitbx.matrix import col
  assert (len(sites1) == len(sites2) == len(atoms) > 0)
  rmsd_no_flip = rmsd_flip = None
  mean_sq = max_deviation_no_flip = 0
  n_sites = 0
  for site1, site2, atom in zip(sites1, sites2, atoms) :
    if (atom.element.strip() == "H") : continue
    distance = abs(col(site1) - col(site2))
    mean_sq += distance**2
    if (distance > max_deviation_no_flip) :
      max_deviation_no_flip = distance
    n_sites += 1
  assert (n_sites > 0)
  rmsd_no_flip = sqrt(mean_sq/n_sites)
  # TODO add HIS?
  if (not atoms[0].parent().resname in ["ASP","GLU","ASN","GLN","PHE","TYR"]) :
    return group_args(rmsd=rmsd_no_flip, max_dev=max_deviation_no_flip)
  mean_sq = max_deviation_flip = 0
  for site1, site2, atom in zip(sites1, sites2, atoms) :
    if (atom.element.strip() == "H") : continue
    atom_name = atom.name.strip()
    labels = atom.fetch_labels()
    symmetric_name = symmetric_atom_names_dict.get(atom_name, None)
    if (symmetric_name is not None) :
      for site1_flip, site2_flip, atom_flip in zip(sites1, sites2, atoms) :
        labels_flip = atom_flip.fetch_labels()
        if ((labels_flip.resid() == labels.resid()) and
            (labels_flip.chain_id == labels.chain_id) and
            (atom_flip.name.strip() == symmetric_name)) :
          distance = abs(col(site1) - col(site2_flip))
          mean_sq += distance**2
          if (distance > max_deviation_flip) :
            max_deviation_flip = distance
          break
      else : # didn't find the symmetry atom,
        rmsd_flip = float(sys.maxint)
        max_deviation_flip = float(sys.maxint)
        break
    else :
      distance = abs(col(site1) - col(site2))
      mean_sq += distance**2
      if (distance > max_deviation_flip) :
        max_deviation_flip = distance
  rmsd_flip = sqrt(mean_sq/n_sites)
  return group_args(
    rmsd=min(rmsd_no_flip, rmsd_flip),
    max_dev=min(max_deviation_no_flip, max_deviation_flip))

def coord_stats_for_atom_groups (residue1, residue2) :
  from scitbx.array_family import flex
  sites1 = flex.vec3_double()
  sites2 = flex.vec3_double()
  atoms = []
  for atom1 in residue1.atoms() :
    if (atom1.element.strip() in ["H","D"]) : continue
    found = False
    for atom2 in residue2.atoms() :
      if (atom2.name == atom1.name) :
        assert (not found)
        found = True
        atoms.append(atom1)
        sites1.append(atom1.xyz)
        sites2.append(atom2.xyz)
  return coord_stats_with_flips(sites1, sites2, atoms)

#-----------------------------------------------------------------------
# MAP STUFF
def get_partial_omit_map (
      fmodel,
      selection,
      selection_delete=None,
      negate_surrounding=False,
      map_file_name=None,
      partial_occupancy=0.5,
      resolution_factor=1/4.) :
  """
  Generate an mFo-DFc map with a selection of atoms at reduced occupancy.
  Will write the map coefficients (along with 2mFo-DFc map) to an MTZ file
  if desired.
  """
  xrs = fmodel.xray_structure
  occ = xrs.scatterers().extract_occupancies()
  occ.set_selected(selection, partial_occupancy)
  xrs.set_occupancies(occ)
  xrs_tmp = xrs.deep_copy_scatterers()
  if (selection_delete is not None) :
    xrs_tmp = xrs_tmp.select(~selection_delete)
  fmodel.update_xray_structure(xrs_tmp, update_f_calc=True)
  fofc_coeffs = fmodel.map_coefficients(map_type="mFo-DFc",
    exclude_free_r_reflections=True)
  fofc_fft = fofc_coeffs.fft_map(resolution_factor=resolution_factor)
  fofc_map = fofc_fft.apply_sigma_scaling().real_map_unpadded()
  two_fofc_coeffs = fmodel.map_coefficients(map_type="2mFo-DFc",
    exclude_free_r_reflections=True)
  two_fofc_fft = two_fofc_coeffs.fft_map(resolution_factor=resolution_factor)
  two_fofc_map = two_fofc_fft.apply_sigma_scaling().real_map_unpadded()
  if (map_file_name is not None) :
    import iotbx.map_tools
    iotbx.map_tools.write_map_coeffs(two_fofc_coeffs, fofc_coeffs,
      map_file_name)
  if (negate_surrounding) :
    two_fofc_map = negate_surrounding_sites(
      map_data=two_fofc_map,
      xray_structure=xrs_tmp,
      iselection=selection)
    fofc_map = negate_surrounding_sites(
      map_data=fofc_map,
      xray_structure=xrs_tmp,
      iselection=selection)
  fmodel.update_xray_structure(xrs, update_f_calc=True)
  # XXX should the occupancies be reset now?
  return two_fofc_map, fofc_map

def negate_surrounding_sites (map_data, xray_structure, iselection,
      radius=1.5) :
  """
  Makes the target map negative around an atom selection.
  """
  import mmtbx.refinement.real_space
  negate_selection = mmtbx.refinement.real_space.selection_around_to_negate(
    xray_structure          = xray_structure,
    selection_within_radius = 5, # XXX make residue dependent !!!!
    iselection              = iselection)
  target_map = mmtbx.refinement.real_space.\
    negate_map_around_selected_atoms_except_selected_atoms(
      xray_structure          = xray_structure,
      map_data                = map_data,
      negate_selection        = negate_selection,
      atom_radius             = radius)
  return target_map

filter_params_str = """
  discard_outliers = *rama *rota *cbeta *geo *map
    .type = choice(multi=True)
  min_model_map_cc = 0.85
    .type = float
  use_difference_map = True
    .type = bool
  sampling_radius = 2.5
    .type = float
"""

def is_validation_outlier (validation, params) :
  filters = params.discard_outliers
  outlier = False
  if (validation.is_rotamer_outlier()) and ("rota" in filters) :
    outlier = True
  if (validation.is_ramachandran_outlier()) and ("rama" in filters) :
    outlier = True
  if (validation.is_cbeta_outlier()) and ("cbeta" in filters) :
    outlier = True
  if (validation.is_geometry_outlier()) and ("geo" in filters) :
    outlier = True
  if (validation.is_clash_outlier()) and ("clash" in filters) :
    outlier = True
  if ((validation.is_map_outlier(cc_min=params.min_model_map_cc)) and
      ("map" in filters)) :
    outlier = True
  return outlier

def filter_before_build (
    pdb_hierarchy,
    fmodel,
    geometry_restraints_manager,
    selection=None,
    params=None,
    verbose=True,
    log=sys.stdout) :
  """
  Pick residues suitable for building alternate conformations - by default,
  this means no MolProbity/geometry outliers, good fit to map, no missing
  atoms, and no pre-existing alternates, but with significant difference
  density nearby.
  """
  from mmtbx.validation import molprobity
  from mmtbx.rotamer import rotamer_eval
  import mmtbx.monomer_library.server
  from mmtbx import building
  from iotbx.pdb import common_residue_names_get_class
  from scitbx.array_family import flex
  if (selection is None) :
    selection = flex.bool(fmodel.xray_structure.scatterers().size(), True)
  pdb_hierarchy.atoms().reset_i_seq()
  full_validation = molprobity.molprobity(
    pdb_hierarchy=pdb_hierarchy,
    fmodel=fmodel,
    geometry_restraints_manager=geometry_restraints_manager,
    outliers_only=False)
  if (verbose) :
    full_validation.show(out=log)
  multi_criterion = full_validation.as_multi_criterion_view()
  if (params is None) :
    params = libtbx.phil.parse(filter_params_str).extract()
  mon_lib_srv = mmtbx.monomer_library.server.server()
  two_fofc_map, fofc_map = building.get_difference_maps(fmodel=fmodel)
  residues = []
  filters = params.discard_outliers
  make_sub_header("Identifying candidates for building", out=log)
  for chain in pdb_hierarchy.only_model().chains() :
    if (not chain.is_protein()) :
      continue
    for residue_group in chain.residue_groups() :
      atom_groups = residue_group.atom_groups()
      id_str = residue_group.id_str()
      i_seqs = residue_group.atoms().extract_i_seq()
      residue_sel = selection.select(i_seqs)
      if (not residue_sel.all_eq(True)) :
        continue
      if (len(atom_groups) > 1) :
        print >> log, "  %s is already multi-conformer" % id_str
        continue
      atom_group = atom_groups[0]
      res_class = common_residue_names_get_class(atom_group.resname)
      if (res_class != "common_amino_acid") :
        print >> log, "  %s: non-standard residue" % id_str
        continue
      missing_atoms = rotamer_eval.eval_residue_completeness(
        residue=atom_group,
        mon_lib_srv=mon_lib_srv,
        ignore_hydrogens=True)
      if (len(missing_atoms) > 0) :
        print >> log, "  %s: missing %d atoms" % (id_str, len(missing_atoms))
        continue
      validation = multi_criterion.get_residue_group_data(residue_group)
      is_outlier = is_validation_outlier(validation, params)
      if (is_outlier) :
        print >> log, "  %s" % str(validation)
        continue
      if (params.use_difference_map) :
        i_seqs_no_hd = building.get_non_hydrogen_atom_indices(residue_group)
        map_stats = building.local_density_quality(
          fofc_map=fofc_map,
          two_fofc_map=two_fofc_map,
          atom_selection=i_seqs_no_hd,
          xray_structure=fmodel.xray_structure,
          radius=params.sampling_radius)
        if ((map_stats.number_of_atoms_in_difference_holes() == 0) and
            (map_stats.fraction_of_nearby_grid_points_above_cutoff()==0)) :
          if (verbose) :
            print >> log, "  no difference density for %s" % id_str
          continue
      residues.append(residue_group.only_atom_group())
  if (len(residues) == 0) :
    raise Sorry("No residues passed the filtering criteria.")
  if (verbose) :
    print >> log, ""
    print >> log, "Alternate conformations will be tried for these residues:"
    for residue in residues :
      print >> log, "  %s" % residue.id_str()
  return residues
