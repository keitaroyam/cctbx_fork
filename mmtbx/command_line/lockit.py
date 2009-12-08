from __future__ import division
import mmtbx.monomer_library.pdb_interpretation
import iotbx.pdb.atom_name_interpretation
import iotbx.mtz
import iotbx.phil, libtbx.phil
from cctbx import maptbx
import cctbx.maptbx.real_space_refinement_simple
import cctbx.geometry_restraints
from cctbx.array_family import flex
import scitbx.rigid_body
import scitbx.graph.tardy_tree
import scitbx.lbfgs
from scitbx import matrix
from libtbx.str_utils import show_string
from libtbx.utils import Sorry
from libtbx import Auto, group_args
import libtbx
import sys, os
op = os.path

def real_space_rigid_body_gradients_simple(
      unit_cell,
      density_map,
      sites_cart_0,
      center_of_mass,
      q,
      unit_quaternion_delta=0.01,
      translation_delta=0.3):
  result = flex.double()
  q_delta = q.deep_copy()
  def get(i, delta):
    fs = []
    for signed_delta in [delta, -delta]:
      q_delta[i] = q[i] + signed_delta
      aja = matrix.rt(scitbx.rigid_body.joint_lib_six_dof_aja_simplified(
        center_of_mass=center_of_mass,
        q=q_delta))
      sites_cart_delta = aja * sites_cart_0
      rs_f = maptbx.real_space_target_simple(
        unit_cell=unit_cell,
        density_map=density_map,
        sites_cart=sites_cart_delta)
      fs.append(rs_f)
    result.append((fs[0]-fs[1])/(2*delta))
  for i in xrange(4): get(i=i, delta=unit_quaternion_delta)
  for i in xrange(3): get(i=i+4, delta=translation_delta)
  return result

class residue_refine_constrained(object):

  def __init__(O,
        pdb_hierarchy,
        residue,
        density_map,
        geometry_restraints_manager,
        real_space_target_weight,
        real_space_gradients_delta,
        lbfgs_termination_params):
    O.pdb_hierarchy = pdb_hierarchy
    O.residue = residue
    O.density_map = density_map
    O.geometry_restraints_manager = geometry_restraints_manager
    O.real_space_gradients_delta = real_space_gradients_delta
    O.real_space_target_weight = real_space_target_weight
    #
    O.unit_cell = geometry_restraints_manager.crystal_symmetry.unit_cell()
    O.sites_cart_all = pdb_hierarchy.atoms().extract_xyz()
    O.residue_i_seqs = residue.atoms().extract_i_seq()
    O.sites_cart_residue_0 = O.sites_cart_all.select(indices=O.residue_i_seqs)
    O.residue_center_of_mass = O.sites_cart_residue_0.mean()
    residue_tardy_tree = scitbx.graph.tardy_tree.construct(
      n_vertices=O.sites_cart_residue_0.size(),
      edge_list="all_in_one_rigid_body") \
        .build_tree() \
        .fix_near_singular_hinges(sites=None)
    O.residue_tardy_model = scitbx.rigid_body.tardy_model(
      labels=None,
      sites=O.sites_cart_residue_0,
      masses=flex.double(O.sites_cart_residue_0.size(), 1),
      tardy_tree=residue_tardy_tree,
      potential_obj=O)
    O.x = O.residue_tardy_model.pack_q()
    assert O.x.size() == 7 # other cases not implemented
    #
    O.number_of_function_evaluations = -1
    O.f_start, O.g_start = O.compute_functional_and_gradients()
    O.rs_f_start = O.rs_f
    O.minimizer = scitbx.lbfgs.run(
      target_evaluator=O,
      termination_params=lbfgs_termination_params)
    O.f_final, O.g_final = O.compute_functional_and_gradients()
    O.rs_f_final = O.rs_f
    del O.rs_f
    del O.x
    del O.residue_center_of_mass
    del O.sites_cart_residue_0
    del O.residue_i_seqs
    del O.sites_cart_all
    del O.unit_cell

  def compute_functional_and_gradients(O):
    if (O.number_of_function_evaluations == 0):
      O.number_of_function_evaluations += 1
      return O.f_start, O.g_start
    O.number_of_function_evaluations += 1
    O.residue_tardy_model.unpack_q(q_packed=O.x)
    O.sites_cart_residue = O.residue_tardy_model.sites_moved()
    rs_f = maptbx.real_space_target_simple(
      unit_cell=O.unit_cell,
      density_map=O.density_map,
      sites_cart=O.sites_cart_residue)
    rs_g = real_space_rigid_body_gradients_simple(
      unit_cell=O.unit_cell,
      density_map=O.density_map,
      sites_cart_0=O.sites_cart_residue_0,
      center_of_mass=O.residue_center_of_mass,
      q=O.x)
    O.rs_f = rs_f
    rs_f *= -O.real_space_target_weight
    rs_g *= -O.real_space_target_weight
    if (O.geometry_restraints_manager is None):
      f = rs_f
      g = rs_g
    else:
      O.sites_cart_all.set_selected(O.residue_i_seqs, O.sites_cart_residue)
      gr_e = O.geometry_restraints_manager.energies_sites(
        sites_cart=O.sites_cart_all, compute_gradients=True)
      O.__d_e_pot_d_sites = gr_e.gradients.select(indices=O.residue_i_seqs)
      f = rs_f + gr_e.target
      g = rs_g + O.residue_tardy_model.d_e_pot_d_q_packed()
    return f, g.as_double()

  def d_e_pot_d_sites(O, sites_moved):
    result = O.__d_e_pot_d_sites
    del O.__d_e_pot_d_sites
    return result

class residue_refine_restrained(object):

  def __init__(O,
        pdb_hierarchy,
        residue,
        density_map,
        geometry_restraints_manager,
        real_space_target_weight,
        real_space_gradients_delta,
        lbfgs_termination_params):
    O.pdb_hierarchy = pdb_hierarchy
    O.residue = residue
    O.density_map = density_map
    O.geometry_restraints_manager = geometry_restraints_manager
    O.real_space_gradients_delta = real_space_gradients_delta
    O.real_space_target_weight = real_space_target_weight
    #
    O.unit_cell = geometry_restraints_manager.crystal_symmetry.unit_cell()
    O.sites_cart_all = pdb_hierarchy.atoms().extract_xyz()
    O.residue_i_seqs = residue.atoms().extract_i_seq()
    O.x = O.sites_cart_all.select(indices=O.residue_i_seqs).as_double()
    #
    O.real_space_target = None
    O.number_of_function_evaluations = -1
    O.f_start, O.g_start = O.compute_functional_and_gradients()
    O.rs_f_start = O.rs_f
    O.minimizer = scitbx.lbfgs.run(
      target_evaluator=O,
      termination_params=lbfgs_termination_params)
    O.f_final, O.g_final = O.compute_functional_and_gradients()
    O.rs_f_final = O.rs_f
    del O.rs_f
    del O.x
    del O.residue_i_seqs
    del O.sites_cart_all
    del O.unit_cell

  def compute_functional_and_gradients(O):
    if (O.number_of_function_evaluations == 0):
      O.number_of_function_evaluations += 1
      return O.f_start, O.g_start
    O.number_of_function_evaluations += 1
    O.sites_cart_residue = flex.vec3_double(O.x)
    rs_f = maptbx.real_space_target_simple(
      unit_cell=O.unit_cell,
      density_map=O.density_map,
      sites_cart=O.sites_cart_residue)
    O.real_space_target = rs_f
    rs_g = maptbx.real_space_gradients_simple(
      unit_cell=O.unit_cell,
      density_map=O.density_map,
      sites_cart=O.sites_cart_residue,
      delta=O.real_space_gradients_delta)
    O.rs_f = rs_f
    rs_f *= -O.real_space_target_weight
    rs_g *= -O.real_space_target_weight
    if (O.geometry_restraints_manager is None):
      f = rs_f
      g = rs_g
    else:
      O.sites_cart_all.set_selected(O.residue_i_seqs, O.sites_cart_residue)
      gr_e = O.geometry_restraints_manager.energies_sites(
        sites_cart=O.sites_cart_all, compute_gradients=True)
      f = rs_f + gr_e.target
      g = rs_g + gr_e.gradients.select(indices=O.residue_i_seqs)
    return f, g.as_double()

def get_rotamer_iterator(mon_lib_srv, residue, atom_selection_bool):
  atoms = residue.atoms()
  if (atom_selection_bool is not None):
    if (atom_selection_bool.select(
          indices=residue.atoms().extract_i_seq()).all_eq(False)):
      return None
  rotamer_iterator = mon_lib_srv.rotamer_iterator(
    comp_id=residue.resname,
    atom_names=residue.atoms().extract_name(),
    sites_cart=residue.atoms().extract_xyz())
  if (rotamer_iterator.problem_message is not None):
    return None
  if (rotamer_iterator.rotamer_info is None):
    return None
  return rotamer_iterator

def rotamer_score_and_choose_best(
      mon_lib_srv,
      density_map,
      pdb_hierarchy,
      geometry_restraints_manager,
      atom_selection_bool,
      real_space_target_weight,
      real_space_gradients_delta,
      lbfgs_termination_params):
  n_other_residues = 0
  n_amino_acids_ignored = 0
  n_amino_acids_scored = 0
  get_class = iotbx.pdb.common_residue_names_get_class
  def refine_constrained():
    refined = residue_refine_constrained(
      pdb_hierarchy=pdb_hierarchy,
      residue=residue,
      density_map=density_map,
      geometry_restraints_manager=geometry_restraints_manager,
      real_space_target_weight=real_space_target_weight,
      real_space_gradients_delta=real_space_gradients_delta,
      lbfgs_termination_params=lbfgs_termination_params)
    print residue.id_str(), "constr. refined(%s): %.6g -> %.6g" % (
      rotamer_id, refined.rs_f_start, refined.rs_f_final)
    return refined
  def refine_restrained():
    refined = residue_refine_restrained(
      pdb_hierarchy=pdb_hierarchy,
      residue=residue,
      density_map=density_map,
      geometry_restraints_manager=geometry_restraints_manager,
      real_space_target_weight=real_space_target_weight,
      real_space_gradients_delta=real_space_gradients_delta,
      lbfgs_termination_params=lbfgs_termination_params)
    print residue.id_str(), "restr. refined(%s): %.6g -> %.6g" % (
      rotamer_id, refined.rs_f_start, refined.rs_f_final)
    return refined
  def refine():
    residue.atoms().set_xyz(new_xyz=refine_constrained().sites_cart_residue)
    return refine_restrained()
  for model in pdb_hierarchy.models():
    for chain in model.chains():
      for residue in chain.only_conformer().residues():
        if (get_class(residue.resname) != "common_amino_acid"):
          n_other_residues += 1
        else:
          rotamer_iterator = get_rotamer_iterator(
            mon_lib_srv=mon_lib_srv,
            residue=residue,
            atom_selection_bool=atom_selection_bool)
          if (rotamer_iterator is None):
            n_amino_acids_ignored += 1
          else:
            rotamer_id = "as_given"
            best = group_args(rotamer_id=rotamer_id, refined=refine())
            n_amino_acids_scored += 1
            for rotamer,rotamer_sites_cart in rotamer_iterator:
              residue.atoms().set_xyz(new_xyz=rotamer_sites_cart)
              trial = group_args(rotamer_id=rotamer.id, refined=refine())
              if (trial.refined.rs_f_final > best.refined.rs_f_final):
                best = trial
            print residue.id_str(), "best rotamer:", best.rotamer_id
            residue.atoms().set_xyz(new_xyz=best.refined.sites_cart_residue)
            print
  print "number of amino acid residues scored:", n_amino_acids_scored
  print "number of amino acid residues ignored:", n_amino_acids_ignored
  print "number of other residues:", n_other_residues
  print
  sys.stdout.flush()

def get_master_phil():
  return iotbx.phil.parse(
    input_string="""\
atom_selection = None
  .type = str

map_coeff_labels {
  f = 2FOFCWT,PH2FOFCWT
    .type = str
  phases = None
    .type = str
  weights = None
    .type = str
}
map_resolution_factor = 1/3
  .type = float

real_space_target_weight = 1
  .type = float
real_space_gradients_delta_resolution_factor = 1/3
  .type = float

coordinate_refinement {
  run = False
    .type = bool
  atom_selection = Auto
    .type = str
  lbfgs_max_iterations = 500
    .type = int
}

rotamer_score_and_choose_best {
  run = False
    .type = bool
  atom_selection = Auto
    .type = str
  lbfgs_max_iterations = 50
    .type = int
}

include scope mmtbx.monomer_library.pdb_interpretation.grand_master_phil_str
""", process_includes=True)

def extract_map_coeffs(params, miller_arrays):
  def find(labels):
    for miller_array in miller_arrays:
      if (",".join(miller_array.info().labels) == labels):
        return miller_array
    matching_array = None
    for miller_array in miller_arrays:
      if (",".join(miller_array.info().labels).lower() == labels.lower()):
        if (matching_array is not None):
          return None
        matching_array = miller_array
    return matching_array
  def raise_sorry(msg_intro, name):
    msg = [
      msg_intro,
      "  %s = %s" % params.__phil_path_and_value__(object_name=name),
      "  List of available labels:"]
    for miller_array in miller_arrays:
      msg.append("    %s" % ",".join(miller_array.info().labels))
    raise Sorry("\n".join(msg))
  if (params.f is None):
    raise_sorry(msg_intro="Missing assignment:", name="f")
  f = find(labels=params.f)
  if (f is None):
    raise_sorry(msg_intro="Cannot find map coefficients:", name="f")
  if (not f.is_complex_array()):
    if (params.phases is None):
      raise_sorry(msg_intro="Missing assignment:", name="phases")
    phases = find(labels=params.phases)
    if (phases is None):
      raise_sorry(
        msg_intro="Cannot find map coefficient phases:", name="phases")
    cf, cp = f.common_sets(other=phases)
    if (cf.indices().size() != f.indices().size()):
      raise Sorry(
        "Number of missing map coefficient phases: %d" % (
          f.indices().size() - cf.indices().size()))
    f = cf.phase_transfer(phase_source=cp, deg=True)
  if (params.weights is not None):
    weights = find(labels=params.weights)
    if (weights is None):
      raise_sorry(
        msg_intro="Cannot find map coefficient weights:",
        name="weights")
    cf, cw = f.common_sets(other=weights)
    if (cf.indices().size() != f.indices().size()):
      raise Sorry(
        "Number of missing map coefficient weights: %d" % (
          f.indices().size() - cf.indices().size()))
    f = cf.customized_copy(data=cw.data()*cf.data())
  return f

def run(args):
  show_times = libtbx.utils.show_times(time_start="now")
  master_phil = get_master_phil()
  import iotbx.utils
  input_objects = iotbx.utils.process_command_line_inputs(
    args=args,
    master_phil=master_phil,
    input_types=("mtz", "pdb", "cif"))
  work_phil = master_phil.fetch(sources=input_objects["phil"])
  work_phil.show()
  print
  work_params = work_phil.extract()
  #
  assert len(input_objects["mtz"]) == 1
  map_coeffs = extract_map_coeffs(
    miller_arrays=input_objects["mtz"][0].file_content.as_miller_arrays(),
    params=work_params.map_coeff_labels)
  #
  mon_lib_srv = mmtbx.monomer_library.server.server()
  ener_lib = mmtbx.monomer_library.server.ener_lib()
  for file_obj in input_objects["cif"]:
    print "Processing CIF file: %s" % show_string(file_obj.file_name)
    for srv in [mon_lib_srv, ener_lib]:
      srv.process_cif_object(
        cif_object=file_obj.file_content,
        file_name=file_obj.file_name)
  #
  assert len(input_objects["pdb"]) == 1 # TODO not implemented
  file_obj = input_objects["pdb"][0]
  input_pdb_file_name = file_obj.file_name
  processed_pdb_file = mmtbx.monomer_library.pdb_interpretation.process(
    mon_lib_srv=mon_lib_srv,
    ener_lib=ener_lib,
    params=work_params.pdb_interpretation,
    file_name=file_obj.file_name,
    pdb_inp=file_obj.file_content,
    strict_conflict_handling=True,
    substitute_non_crystallographic_unit_cell_if_necessary=True,
    log=sys.stdout)
  #
  grm = processed_pdb_file.geometry_restraints_manager(
    params_edits=work_params.geometry_restraints.edits,
    params_remove=work_params.geometry_restraints.remove)
  print
  sys.stdout.flush()
  #
  d_min = map_coeffs.d_min()
  fft_map = map_coeffs.fft_map(
    d_min=d_min,
    resolution_factor=work_params.map_resolution_factor)
  fft_map.apply_sigma_scaling()
  density_map = fft_map.real_map()
  real_space_gradients_delta = \
    d_min * work_params.real_space_gradients_delta_resolution_factor
  print "real_space_gradients_delta: %.6g" % real_space_gradients_delta
  print
  sys.stdout.flush()
  #
  common_atom_selection_bool_cache = []
  def atom_selection_bool(scope_extract, attr):
    result = processed_pdb_file.all_chain_proxies \
      .phil_atom_selection(
        cache=None,
        scope_extract=scope_extract,
        attr="atom_selection",
        allow_none=True,
        allow_auto=True)
    if (result is None or result is not Auto):
      return result
    if (len(common_atom_selection_bool_cache) == 0):
      common_atom_selection_bool_cache.append(
        processed_pdb_file.all_chain_proxies
          .phil_atom_selection(
            cache=None,
            scope_extract=work_params,
            attr="atom_selection",
            allow_none=True))
    return common_atom_selection_bool_cache[0]
  #
  if (work_params.rotamer_score_and_choose_best.run):
    rotamer_score_and_choose_best(
      mon_lib_srv=mon_lib_srv,
      density_map=density_map,
      pdb_hierarchy=processed_pdb_file.all_chain_proxies.pdb_hierarchy,
      geometry_restraints_manager=grm,
      atom_selection_bool=atom_selection_bool(
        scope_extract=work_params.rotamer_score_and_choose_best,
        attr="atom_selection"),
      real_space_target_weight=work_params.real_space_target_weight,
      real_space_gradients_delta=real_space_gradients_delta,
      lbfgs_termination_params=scitbx.lbfgs.termination_parameters(
        max_iterations=work_params
          .rotamer_score_and_choose_best.lbfgs_max_iterations))
  #
  if (work_params.coordinate_refinement.run != 0):
    pdb_atoms = processed_pdb_file.all_chain_proxies.pdb_atoms
    sites_cart = pdb_atoms.extract_xyz()
    print "Before coordinate refinement:"
    grm.energies_sites(sites_cart=sites_cart).show()
    print
    sys.stdout.flush()
    atom_selection_bool = atom_selection_bool(
      scope_extract=work_params.coordinate_refinement,
      attr="atom_selection")
    if (atom_selection_bool is None):
      iselection_refine = None
    else:
      iselection_refine = atom_selection_bool.iselection()
    refined = maptbx.real_space_refinement_simple.lbfgs(
      sites_cart=sites_cart,
      density_map=density_map,
      iselection_refine=iselection_refine,
      geometry_restraints_manager=grm,
      real_space_target_weight=work_params.real_space_target_weight,
      real_space_gradients_delta=real_space_gradients_delta,
      lbfgs_termination_params=scitbx.lbfgs.termination_parameters(
        max_iterations=work_params.coordinate_refinement
          .lbfgs_max_iterations))
    print "After coordinate refinement:"
    grm.energies_sites(sites_cart=refined.sites_cart).show()
    pdb_atoms.set_xyz(new_xyz=refined.sites_cart)
    print
    print "number_of_function_evaluations:", \
      refined.number_of_function_evaluations
    print "real+geo target start: %.6g" % refined.f_start
    print "real+geo target final: %.6g" % refined.f_final
    print
  #
  file_name = op.basename(input_pdb_file_name)
  if (   file_name.endswith(".pdb")
      or file_name.endswith(".ent")):
    file_name = file_name[:-4]
  file_name += "_lockit.pdb"
  pdb_hierarchy = processed_pdb_file.all_chain_proxies.pdb_hierarchy
  print "Writing file: %s" % show_string(file_name)
  sys.stdout.flush()
  pdb_hierarchy.write_pdb_file(
    file_name=file_name,
    crystal_symmetry=grm.crystal_symmetry)
  print
  #
  show_times()
  sys.stdout.flush()

if (__name__ == "__main__"):
  run(args=sys.argv[1:])
