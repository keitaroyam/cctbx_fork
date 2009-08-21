import mmtbx.monomer_library.server
import iotbx.pdb.atom_name_interpretation
import iotbx.pdb.amino_acid_codes
import cctbx.geometry_restraints
import scitbx.rigid_body
import scitbx.graph.tardy_tree
from scitbx.array_family import flex
from scitbx import matrix
import libtbx.phil
from libtbx.str_utils import show_string
import libtbx.load_env
import math
import string
import sys, os
op = os.path

rotamer_info_master_phil_str = """\
tor_ids = None
  .type = strings
tor_atom_ids = None
  .type = strings
  .multiple = True
tree_generation_without_bond = None
  .type = strings
  .multiple = True
constrain_dihedrals_with_sigma_less_than_or_equal_to = 10
  .type=float
rotamer
  .multiple = True
{
 id = None
   .type = str
 frequency = None
   .type = float
 frequency_annotation = None
   .type = str
 angles = None
   .type = floats(allow_none_elements=True)
}
"""

protein_pdb_files = libtbx.env.find_in_repositories(
  relative_path="phenix_regression/protein_pdb_files",
  optional=False)

reference_pdb_file_names = """\
ala_chain_all_h_1ozo_v3.ent
arg_chain_all_h_1o8t_v3.ent
asn_chain_all_h_1o8t_v3.ent
asp_chain_all_h_1jjx_v3.ent
cys_chain_all_h_1rfa_v3.ent
gln_chain_all_h_1o8t_v3.ent
glu_chain_all_h_1bm4_v3.ent
gly_chain_all_h_1ozo_v3.ent
his_chain_all_h_1g7e_v3.ent
ile_chain_all_h_1ozo_v3.ent
leu_chain_all_h_1ozo_v3.ent
lys_chain_all_h_1o8t_v3.ent
met_chain_all_h_1ozo_v3.ent
mse_chain_all_h_1ozo_v3.ent
phe_chain_all_h_1hdj_v3.ent
pro_chain_all_h_1a03_v3.ent
ser_chain_all_h_1o8t_v3.ent
thr_chain_all_h_1o8t_v3.ent
trp_chain_all_h_1cx1_v3.ent
tyr_chain_all_h_1cx1_v3.ent
val_chain_all_h_1ozo_v3.ent
""".splitlines()
def __init_reference_pdb_file_name_lookup():
  result = {}
  for file_name in reference_pdb_file_names:
    result[file_name[:3].upper()] = file_name
  return result
reference_pdb_file_name_lookup = __init_reference_pdb_file_name_lookup()

def report_tors(comp, residue_sites, matched_mon_lib_atom_names, targets):
  lookup = {}
  for j,atom_id in enumerate(matched_mon_lib_atom_names):
    lookup[atom_id] = j
  for tor in comp.tor_list:
    atom_ids = tor.atom_ids()
    js = [lookup.get(ai) for ai in atom_ids]
    if (js.count(None) != 0):
      angle_model = None
    else:
      d_sites = [residue_sites[j] for j in js]
      d = cctbx.geometry_restraints.dihedral(
        sites=d_sites, angle_ideal=0, weight=1)
      angle_model = d.angle_model
    target = targets.get(tor.id)
    if (angle_model is not None and target is not None):
      if (cctbx.geometry_restraints.angle_delta_deg(
            angle_1=angle_model,
            angle_2=target) > 1.e-5):
        annotation = "MISMATCH"
      else:
        annotation = "OK_target"
    else:
      annotation = "no_target"
    print tor.id, atom_ids, angle_model, annotation

def generate_rotamers(comp, rotamer_info, bonds_to_omit, strip_hydrogens):
  resname = comp.chem_comp.id
  comp_atom_names = set([atom.atom_id for atom in comp.atom_list])
  pdb_inp = iotbx.pdb.input(
    file_name=op.join(
      protein_pdb_files, reference_pdb_file_name_lookup[resname]))
  pdb_atoms = pdb_inp.atoms()
  pdb_atoms.reset_i_seq()
  matched_atom_names = iotbx.pdb.atom_name_interpretation.interpreters[
    resname].match_atom_names(atom_names=pdb_atoms.extract_name())
  names = matched_atom_names.unexpected
  if (len(names) != 0):
    raise RuntimeError("%: unexpected atoms: %s" % (
      resname, " ".join(sorted(names))))
  names = matched_atom_names.missing_atom_names(ignore_hydrogen=True)
  if (len(names) != 0):
    raise RuntimeError("%: missing atoms: %s" % (
      resname, " ".join(sorted(names))))
  pdb_hierarchy = pdb_inp.construct_hierarchy()
  ag = pdb_hierarchy.only_atom_group()
  if (strip_hydrogens):
    for atom in ag.atoms():
      if (atom.element == " H"):
        ag.remove_atom(atom=atom)
    pdb_residue = pdb_hierarchy.only_residue()
  else:
    pdb_residue = pdb_hierarchy.only_residue()
    remove_name = {"ASP": " HD2", "GLU": " HE2"}.get(pdb_residue.resname)
    if (remove_name is not None):
      for atom in ag.atoms():
        if (atom.name == remove_name):
          ag.remove_atom(atom=atom)
      pdb_residue = pdb_hierarchy.only_residue()
  pdb_atoms = pdb_residue.atoms()
  matched_mon_lib_atom_names = flex.select(
    sequence=matched_atom_names.mon_lib_names(),
    permutation=pdb_atoms.extract_i_seq())
  for p,m in zip(pdb_atoms, matched_mon_lib_atom_names):
    print 'atom name mapping: pdb="%s" -> %s' % (p.name, m)
  if (strip_hydrogens):
    assert len(matched_mon_lib_atom_names) == comp.chem_comp.number_atoms_nh
  comp_atom_name_set = set([atom.atom_id for atom in comp.atom_list])
  for name in matched_mon_lib_atom_names:
    if (name not in comp_atom_name_set):
      raise RuntimeError(
        "Missing comp atom: %s %s" % (pdb_residue.resname, name))
  #
  pdb_atoms.reset_i_seq()
  pdb_atoms.set_occ(new_occ=flex.double(pdb_atoms.size(), 1))
  pdb_atoms.set_b(new_b=flex.double(pdb_atoms.size(), 0))
  rg = pdb_hierarchy.only_residue_group()
  rg.resseq = 1
  rg.icode = " "
  assert pdb_hierarchy.only_atom_group().altloc == ""
  #
  # XXX severe duplication of source code
  tree_root_atom_names = set(["CA", "C", "O"])
  if (("N", "CA") not in bonds_to_omit):
    tree_root_atom_names.add("N")
  fixed_vertices = []
  atom_indices = {}
  for i,matched_atom_name in enumerate(matched_mon_lib_atom_names):
    atom_id = matched_atom_name
    assert atom_id not in atom_indices
    atom_indices[atom_id] = i
    if (atom_id in tree_root_atom_names):
      fixed_vertices.append(i)
  assert len(atom_indices) == len(matched_mon_lib_atom_names)
  assert len(fixed_vertices) == len(tree_root_atom_names)
  edge_list = []
  for bond in comp.bond_list:
    bond_atom_ids = bond.atom_ids()
    if (bond_atom_ids not in bonds_to_omit):
      ai = [atom_indices.get(atom_id) for atom_id in bond_atom_ids]
      if (ai.count(None) == 0):
        edge_list.append(tuple(sorted(ai)))
  external_clusters = []
  if (rotamer_info is not None):
    for tor in comp.tor_list:
      if (   tor.value_angle_esd
          <= rotamer_info.constrain_dihedrals_with_sigma_less_than_or_equal_to):
        ai = [atom_indices.get(atom_id) for atom_id in tor.atom_ids()]
        if (ai.count(None) == 0):
          external_clusters.append(sorted(ai))
    for plane in comp.get_planes():
      ai = []
      for atom_id in plane.plane_atoms:
        i = atom_indices.get(atom_id)
        if (i is not None):
          ai.append(i)
      external_clusters.append(sorted(ai))
  tardy_tree = scitbx.graph.tardy_tree.construct(
    n_vertices=pdb_atoms.size(),
    edge_list=edge_list,
    external_clusters=external_clusters,
    fixed_vertex_lists=[fixed_vertices]).build_tree()
  assert len(tardy_tree.cluster_manager.loop_edges) == 0
  tardy_model = scitbx.rigid_body.tardy_model(
    labels=pdb_atoms.extract_name(),
    sites=pdb_atoms.extract_xyz(),
    masses=flex.double(pdb_atoms.size(), 1),
    tardy_tree=tardy_tree,
    potential_obj=None)
  joint_dofs = tardy_model.degrees_of_freedom_each_joint()
  for ib in xrange(len(joint_dofs)):
    c = tardy_tree.cluster_manager.clusters[ib]
    print "cluster:", joint_dofs[ib], [pdb_atoms[i].name for i in c]
  assert joint_dofs[0] == 0
  assert joint_dofs[1:].all_eq(1)
  #
  if (rotamer_info is None):
    return None
  #
  comp_tor_by_id = {}
  for tor in comp.tor_list:
    assert tor.id not in comp_tor_by_id
    comp_tor_by_id[tor.id] = tor
  rotmer_info_tor_ids = set(rotamer_info.tor_ids)
  rotamer_tor_by_id = {}
  for tor_atom_ids in rotamer_info.tor_atom_ids:
    assert len(tor_atom_ids) == 5
    tor_id = tor_atom_ids[0]
    assert tor_id in rotmer_info_tor_ids
    assert tor_id not in comp_tor_by_id
    assert tor_id not in rotamer_tor_by_id
    rotamer_tor_by_id[tor_id] = tuple(tor_atom_ids[1:])
  rotamer_tor_atom_ids_by_tor_id = {}
  for tor_id in rotamer_info.tor_ids:
    comp_tor = comp_tor_by_id.get(tor_id)
    if (comp_tor is not None):
      rotamer_tor_atom_ids_by_tor_id[tor_id] = comp_tor.atom_ids()
    else:
      atom_ids = rotamer_tor_by_id.get(tor_id)
      if (atom_ids is None):
        raise RuntimeError(
          "rotamer_info.tor_id %s is unknown." % show_string(tor_id))
      rotamer_tor_atom_ids_by_tor_id[tor_id] = atom_ids
  #
  tor_id_by_rotatable_bond_atom_names = {}
  for tor_id,atom_ids in rotamer_tor_atom_ids_by_tor_id.items():
    atom_names = tuple(sorted(atom_ids[1:3]))
    assert atom_names not in tor_id_by_rotatable_bond_atom_names
    tor_id_by_rotatable_bond_atom_names[atom_names] = tor_id
  #
  tor_id_i_q_packed_matches = {}
  number_of_trees = 0
  for i_body,he in enumerate(tardy_tree.cluster_manager.hinge_edges):
    if (he[0] == -1):
      number_of_trees += 1
      continue
    hinge_atom_names = [tardy_model.labels[i].strip() for i in he]
    atom_names = tuple(sorted(hinge_atom_names))
    tor_id = tor_id_by_rotatable_bond_atom_names.get(atom_names)
    if (tor_id is None):
      raise RuntimeError(
        "rotatable bond atoms %s - %s (as defined by tardy_tree):"
        " no match in rotamer_info.tor_ids" % tuple(hinge_atom_names))
    tor_id_i_q_packed_matches[tor_id] = i_body - 1
  assert number_of_trees == 1
  #
  unused_rotamer_info_tor_ids = []
  for tor_id in rotamer_info.tor_ids:
    if (tor_id not in tor_id_i_q_packed_matches):
      unused_rotamer_info_tor_ids.append(tor_id)
  if (len(unused_rotamer_info_tor_ids) != 0):
    print "Info: unused rotamer_info.tor_ids:", \
      " ".join(unused_rotamer_info_tor_ids)
    assert strip_hydrogens
  #
  tors_start = {}
  for tor_id in tor_id_i_q_packed_matches.keys():
    tor_atom_ids = rotamer_tor_atom_ids_by_tor_id[tor_id]
    ai = [atom_indices.get(atom_id) for atom_id in tor_atom_ids]
    assert ai.count(None) == 0
    d_sites = [tardy_model.sites[i] for i in ai]
    d = cctbx.geometry_restraints.dihedral(
      sites=d_sites, angle_ideal=0, weight=1)
    assert tor_id not in tors_start
    tors_start[tor_id] = d.angle_model
  #
  if (strip_hydrogens):
    rotamers_sub_dir = "rotamers_no_h"
  else:
    rotamers_sub_dir = "rotamers_with_h"
  rotamers_sep_sub_dir = rotamers_sub_dir + "_sep"
  if (not os.path.isdir(rotamers_sub_dir)):
    os.mkdir(rotamers_sub_dir)
  if (not os.path.isdir(rotamers_sep_sub_dir)):
    os.mkdir(rotamers_sep_sub_dir)
  remark_strings = []
  atom_strings = []
  atom_serial_first_value = 1
  for i_rotamer,rotamer in enumerate(rotamer_info.rotamer):
    q_packed_work = flex.double(tardy_model.q_packed_size, 0)
    for tor_id,angle in zip(rotamer_info.tor_ids, rotamer.angles):
      i_q_packed = tor_id_i_q_packed_matches.get(tor_id)
      if (i_q_packed is not None and angle is not None):
        q_packed_work[i_q_packed] = math.radians(angle - tors_start[tor_id])
    tardy_model.unpack_q(q_packed=q_packed_work)
    rotamer_sites = tardy_model.sites_moved()
    rotamer_sites += matrix.col((4,4,4)) * i_rotamer
    pdb_atoms.set_xyz(new_xyz=rotamer_sites)
    report_tors(
      comp=comp,
      residue_sites=rotamer_sites,
      matched_mon_lib_atom_names=matched_mon_lib_atom_names,
      targets=dict(zip(rotamer_info.tor_ids, rotamer.angles)))
    #
    file_name = "%s/%s_%s.pdb" % (
      rotamers_sep_sub_dir, pdb_residue.resname, rotamer.id)
    print "Writing file:", file_name
    f = open(file_name, "w")
    print >> f, "REMARK %s %s" % (pdb_residue.resname, rotamer.id)
    pdb_atoms.reset_serial(first_value=1)
    f.write(pdb_hierarchy.as_pdb_string(append_end=True))
    del f
    #
    pdb_atoms.reset_serial(first_value=atom_serial_first_value)
    atom_serial_first_value += pdb_atoms.size()
    chain_id = (string.uppercase + string.lowercase)[i_rotamer]
    pdb_hierarchy.only_chain().id = chain_id
    remark_strings.append(
      "REMARK %s %s = chain %s" % (pdb_residue.resname, rotamer.id, chain_id))
    atom_strings.append(pdb_hierarchy.as_pdb_string(append_end=False))
  file_name = "%s/%s.pdb" % (rotamers_sub_dir, pdb_residue.resname)
  print "Writing file:", file_name
  f = open(file_name, "w")
  for s in remark_strings:
    print >> f, s
  for s in atom_strings:
    f.write(s)
  print >> f, "END"
  del f

def process_rotamer_info(rotamer_info_master_phil, comp):
  assert len(comp.rotamer_info) < 2
  if (len(comp.rotamer_info) == 0):
    print "No rotamer_info."
    rotamer_info = None
  else:
    rotamer_info_phil = rotamer_info_master_phil.fetch(
      source=libtbx.phil.parse(
        input_string=comp.rotamer_info[0].phil_str))
    rotamer_info_phil.show()
    rotamer_info = rotamer_info_phil.extract()
    n_missing_frequencies = 0
    for rotamer in rotamer_info.rotamer:
      assert rotamer.id is not None
      assert len(rotamer.id.strip()) == len(rotamer.id)
      assert len(rotamer.id.split()) == 1
      if (rotamer.frequency is None):
        if (rotamer.frequency_annotation != "for more uniform sampling"):
          n_missing_frequencies += 1
      else:
        assert rotamer.frequency > 0
        assert rotamer.frequency < 1
      assert rotamer.angles is not None
      assert len(rotamer.angles) == len(rotamer_info.tor_ids)
      for angle in rotamer.angles:
        assert angle is None or -180 < angle <= 180
    if (n_missing_frequencies != 0):
      print "Warning: number of missing frequencies:", n_missing_frequencies
  return rotamer_info

def process(mon_lib_srv, rotamer_info_master_phil, resname):
  print "resname:", resname
  comp = mon_lib_srv.get_comp_comp_id_direct(comp_id=resname)
  rotamer_info = process_rotamer_info(
    rotamer_info_master_phil=rotamer_info_master_phil,
    comp=comp)
  bonds_to_omit = {}
  if (rotamer_info is not None):
    for bond in rotamer_info.tree_generation_without_bond:
      assert len(bond) == 2
      bond = tuple(bond)
      if (bond in bonds_to_omit):
        raise RuntimeError(
          "Duplicate tree_generation_without_bond definition: %s" % str(bond))
      bonds_to_omit[bond] = False
  tree_root_atom_names = set(["N", "CA", "C", "O"])
  fixed_vertices = []
  atom_indices = {}
  for i,atom in enumerate(comp.atom_list):
    atom_id = atom.atom_id
    assert atom_id not in atom_indices
    atom_indices[atom_id] = i
    if (atom_id in tree_root_atom_names):
      fixed_vertices.append(i)
  assert len(fixed_vertices) == len(tree_root_atom_names)
  edge_list = []
  for bond in comp.bond_list:
    bond_atom_ids = bond.atom_ids()
    if (bond_atom_ids in bonds_to_omit):
      bonds_to_omit[bond_atom_ids] = True
    else:
      edge_list.append(tuple(sorted([atom_indices[atom_id]
        for atom_id in bond_atom_ids])))
  for bond_atom_ids,was_used in bonds_to_omit.items():
    if (not was_used):
      raise RuntimeError(
        "tree_generation_without_bond does not match any bonds: %s"
          % str(bond_atom_ids))
  tor_dict = {}
  for tor in comp.tor_list:
    atom_names = tuple(sorted([tor.atom_id_2, tor.atom_id_3]))
    tor_dict.setdefault(atom_names, []).append(tor)
    print tor.id, ", ".join([
      tor.atom_id_1, tor.atom_id_2, tor.atom_id_3, tor.atom_id_4]), \
      tor.value_angle_esd
  for atom_ids,tors in tor_dict.items():
    if (len(tors) != 1):
      print "Info: redundant tors:", ", ".join([tor.id for tor in tors])
  tardy_tree = scitbx.graph.tardy_tree.construct(
    n_vertices=len(comp.atom_list),
    edge_list=edge_list,
    fixed_vertex_lists=[fixed_vertices]).build_tree()
  assert len(tardy_tree.cluster_manager.loop_edges) == 0
  tor_hinge_matches = set()
  number_of_trees = 0
  for ib,he in enumerate(tardy_tree.cluster_manager.hinge_edges):
    if (he[0] == -1):
      number_of_trees += 1
      continue
    hinge_atom_names = [comp.atom_list[i].atom_id for i in he]
    atom_names = tuple(sorted(hinge_atom_names))
    tors = tor_dict.get(atom_names)
    if (tors is None):
      s = "Warning: no tor"
    else:
      for tor in tors:
        tor_hinge_matches.add(tor.id)
      s = ", ".join([tor.id for tor in tors])
      if (len(tors) != 1):
        s = "Info: multiple tors: " + s
    print "hinge edge:", ", ".join(hinge_atom_names), s
  assert number_of_trees == 1
  #
  non_const_tor_ids = set()
  for tor in comp.tor_list:
    if (tor.value_angle_esd == 0):
      assert tor.id.startswith("CONST_")
    else:
      non_const_tor_ids.add(tor.id)
  tors_not_hinge = non_const_tor_ids.difference(tor_hinge_matches)
  if (len(tors_not_hinge) != 0):
    print "tors_not_hinge:", ", ".join(sorted(tors_not_hinge))
  for strip_hydrogens in [True, False]:
    generate_rotamers(
      comp=comp,
      rotamer_info=rotamer_info,
      bonds_to_omit=bonds_to_omit,
      strip_hydrogens=strip_hydrogens)
  print

def run(args):
  assert len(args) == 0
  mon_lib_srv = mmtbx.monomer_library.server.server()
  rotamer_info_master_phil = libtbx.phil.parse(
    input_string=rotamer_info_master_phil_str)
  amino_acid_resnames = sorted(
    iotbx.pdb.amino_acid_codes.one_letter_given_three_letter.keys())
  for resname in amino_acid_resnames:
    process(
      mon_lib_srv=mon_lib_srv,
      rotamer_info_master_phil=rotamer_info_master_phil,
      resname=resname)
  print "OK"

if (__name__ == "__main__"):
  run(args=sys.argv[1:])
