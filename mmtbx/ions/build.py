"""
Deals with modifying a structure to include unbuilt and misidentified ions.
"""

from __future__ import division
from libtbx.str_utils import make_sub_header
from libtbx.utils import null_out
from libtbx import Auto
import sys

ion_building_params_str = """
debug = False
  .type = bool
  .short_caption = Debugging mode (verbose)
elements = Auto
  .type = strings
  .help = If Auto, the program will search for MG, CL, CA, and ZN ions, but \
    with stricter rules for accepting a candidate element.  You may \
    alternately specify a list of element symbols to search for.  (Not all \
    elements are supported.)
ion_chain_id = X
  .type = str
  .input_size = 80
  .short_caption = Ion chain ID
initial_occupancy = 1.0
  .type = float
  .input_size = 80
  .help = Occupancy for newly placed ions - if less than 1.0, the occupancy \
    may be refined automatically in future runs of phenix.refine.
initial_b_iso = Auto
  .type = float
  .input_size = 80
  .short_caption = Initial B-iso
refine_ion_occupancies = True
  .type = bool
  .help = Toggles refinement of occupancies for newly placed ions.  This \
    will only happen if the occupancy refinement strategy is selected.
refine_ion_adp = *Auto isotropic anisotropic none
  .type = choice
  .short_caption = Refine ion B-factor
  .help = B-factor refinement type for newly placed ions.  At medium-to-high \
    resolution, anisotropic refinement may be preferrable for the heavier \
    elements.
refine_anomalous = True
  .type = bool
  .short_caption = Model anomalous scattering
  .help = If True and the wavelength is specified, any newly placed ions will \
    have anomalous scattering factors refined.  This is \
    unlikely to affect R-factors but should flatten the anomalous LLG map.
max_distance_between_like_charges = 3.5
  .type = float
"""

def find_and_build_ions (
      manager,
      fmodels,
      model,
      wavelength,
      params,
      nproc=1,
      out=None,
      run_ordered_solvent=False,
      occupancy_strategy_enabled=False,
      group_anomalous_strategy_enabled=False) :
  import mmtbx.refinement.minimization
  from mmtbx.refinement.anomalous_scatterer_groups import \
    get_single_atom_selection_string
  from mmtbx.refinement import anomalous_scatterer_groups
  import mmtbx.ions
  from cctbx.eltbx import sasaki
  from cctbx import crystal
  from cctbx import adptbx
  from cctbx import xray
  from scitbx.array_family import flex
  import scitbx.lbfgs
  assert (1.0 >= params.initial_occupancy >= 0)
  fmodel = fmodels.fmodel_xray()
  anomalous_flag = fmodel.f_obs().anomalous_flag()
  if (out is None) : out = sys.stdout
  model.xray_structure = fmodel.xray_structure
  model.xray_structure.tidy_us()
  pdb_hierarchy = model.pdb_hierarchy(sync_with_xray_structure=True)
  pdb_atoms = pdb_hierarchy.atoms()
  pdb_atoms.reset_i_seq()
  # FIXME why does B for anisotropic waters end up negative?
  u_iso = model.xray_structure.extract_u_iso_or_u_equiv()
  for i_seq, atom in enumerate(pdb_atoms) :
    labels = atom.fetch_labels()
    if (labels.resname == "HOH") and (atom.b < 0) :
      assert (u_iso[i_seq] >= 0)
      atom.b = adptbx.u_as_b(u_iso[i_seq])
  if (manager is None) :
    manager = mmtbx.ions.create_manager(
      pdb_hierarchy=pdb_hierarchy,
      geometry_restraints_manager=model.restraints_manager.geometry,
      fmodel=fmodel,
      wavelength=wavelength,
      params=params,
      nproc=nproc,
      verbose=params.debug,
      log=out)
  else :
    grm = model.restraints_manager.geometry
    connectivity = grm.shell_sym_tables[0].full_simple_connectivity()
    manager.update_structure(
      pdb_hierarchy=pdb_hierarchy,
      xray_structure=fmodel.xray_structure,
      connectivity=connectivity,
      log=out)
    manager.update_maps()
  model.update_anomalous_groups(out=out)
  make_sub_header("Analyzing water molecules", out=out)
  manager.show_current_scattering_statistics(out=out)
  elements = params.elements
  anomalous_groups = []
  # XXX somehow comma-separation of phil strings fields doesn't work
  if (isinstance(elements, list)) and (len(elements) == 1) :
    elements = elements[0].split(",")
  water_ion_candidates = manager.analyze_waters(
    out=out,
    candidates=elements)
  modified_iselection = flex.size_t()
  default_b_iso = manager.get_initial_b_iso()
  # Build in the identified ions
  for_building = []
  for i_seq, final_choices, two_fofc in water_ion_candidates :
    if (len(final_choices) == 1) :
      for_building.append((i_seq, final_choices[0]))
  skipped = []
  if (len(for_building) > 0) :
    make_sub_header("Adding %d ions to model" % len(for_building), out)
    for k, (i_seq, final_choice) in enumerate(for_building) :
      atom = manager.pdb_atoms[i_seq]
      skip = False
      for other_i_seq, other_ion in for_building[:k] :
        if (other_i_seq in skipped) : continue
        if (((other_ion.charge > 0) and (final_choice.charge > 0)) or
            ((other_ion.charge < 0) and (final_choice.charge < 0))) :
          other_atom = manager.pdb_atoms[other_i_seq]
          dxyz = atom.distance(other_atom)
          if (dxyz < params.max_distance_between_like_charges) :
            print >> out, \
              "  %s (%s%+d) is only %.3fA from %s (%s%+d), skipping for now" %\
              (atom.id_str(), final_choice.element, final_choice.charge, dxyz,
               other_atom.id_str(), other_ion.element, other_ion.charge)
            skipped.append(i_seq)
            skip = True
            break
      if (skip) : continue
      print >> out, "  %s becomes %s%+d" % \
          (atom.id_str(), final_choice.element, final_choice.charge)
      refine_adp = params.refine_ion_adp
      if (refine_adp == "Auto") :
        if (fmodel.f_obs().d_min() <= 1.5) :
          refine_adp = "anisotropic"
        elif (fmodel.f_obs().d_min() < 2.5) :
          atomic_number = sasaki.table(final_choice.element).atomic_number()
          if (atomic_number >= 19) :
            refine_adp = "anisotropic"
      # Modify the atom object - this is clumsy but they will be grouped into
      # a single chain at the end of refinement
      initial_b_iso = params.initial_b_iso
      if (initial_b_iso is Auto) :
        initial_b_iso = manager.guess_b_iso_real(i_seq)
      modified_atom = model.convert_atom(
        i_seq=i_seq,
        scattering_type=final_choice.scattering_type(),
        atom_name=final_choice.element,
        element=final_choice.element,
        charge=final_choice.charge,
        residue_name=final_choice.element,
        initial_occupancy=params.initial_occupancy,
        initial_b_iso=initial_b_iso,
        chain_id=params.ion_chain_id,
        segid="ION",
        refine_adp=refine_adp,
        refine_occupancies=False) #params.refine_ion_occupancies)
      if (params.refine_anomalous) and (anomalous_flag) :
        scatterer = model.xray_structure.scatterers()[i_seq]
        if (wavelength is not None) :
          fp_fdp_info = sasaki.table(final_choice.element).at_angstrom(
            wavelength)
          scatterer.fp = fp_fdp_info.fp()
          scatterer.fdp = fp_fdp_info.fdp()
          print >> out, "    setting f'=%g, f''=%g" % (scatterer.fp,
            scatterer.fdp)
        group = xray.anomalous_scatterer_group(
          iselection=flex.size_t([i_seq]),
          f_prime=scatterer.fp,
          f_double_prime=scatterer.fdp,
          refine=["f_prime","f_double_prime"],
          selection_string=get_single_atom_selection_string(modified_atom),
          update_from_selection=True)
        anomalous_groups.append(group)
      modified_iselection.append(i_seq)
  if (len(modified_iselection) > 0) :
    scatterers = model.xray_structure.scatterers()
    # FIXME not sure this is actually working as desired...
    site_symmetry_table = model.xray_structure.site_symmetry_table()
    for i_seq in site_symmetry_table.special_position_indices() :
      scatterers[i_seq].site = crystal.correct_special_position(
        crystal_symmetry=model.xray_structure,
        special_op=site_symmetry_table.get(i_seq).special_op(),
        site_frac=scatterers[i_seq].site,
        site_label=scatterers[i_seq].label,
        tolerance=1.0)
    model.xray_structure.replace_scatterers(scatterers=scatterers)
    def show_r_factors () :
       return "r_work=%6.4f r_free=%6.4f" % (fmodel.r_work(), fmodel.r_free())
    fmodel.update_xray_structure(
      xray_structure=model.xray_structure,
      update_f_calc=True,
      update_f_mask=True)
    n_anom = len(anomalous_groups)
    refine_anomalous = anomalous_flag and params.refine_anomalous and n_anom>0
    refine_occupancies = ((params.refine_ion_occupancies or refine_anomalous)
      and ((not occupancy_strategy_enabled) or
           (model.refinement_flags.s_occupancies is None) or
           (len(model.refinement_flags.s_occupancies) == 0)))
    if (refine_anomalous) :
      if ((model.anomalous_scatterer_groups is not None) and
          (group_anomalous_strategy_enabled)) :
        model.anomalous_scatterer_groups.extend(anomalous_groups)
        refine_anomalous = False
    if (refine_occupancies) or (refine_anomalous) :
      print >> out, ""
      print >> out, "  occupancy refinement (new ions only): start %s" % \
        show_r_factors()
      fmodel.xray_structure.scatterers().flags_set_grads(state = False)
      fmodel.xray_structure.scatterers().flags_set_grad_occupancy(
        iselection = modified_iselection)
      lbfgs_termination_params = scitbx.lbfgs.termination_parameters(
        max_iterations = 25)
      minimized = mmtbx.refinement.minimization.lbfgs(
        restraints_manager       = None,
        fmodels                  = fmodels,
        model                    = model,
        is_neutron_scat_table    = False,
        lbfgs_termination_params = lbfgs_termination_params)
      fmodel.xray_structure.adjust_occupancy(
        occ_max   = 1.0,
        occ_min   = 0,
        selection = modified_iselection)
      zero_occ = []
      for i_seq in modified_iselection :
        occ = fmodel.xray_structure.scatterers()[i_seq].occupancy
        if (occ == 0) :
          zero_occ.append(i_seq)
      fmodel.update_xray_structure(
        update_f_calc=True,
        update_f_mask=True)
      print >> out, "                                        final %s" % \
        show_r_factors()
      if (len(zero_occ) > 0) :
        print >> out, "  WARNING: occupancy dropped to zero for %d atoms:"
        atoms = model.pdb_hierarchy().atoms()
        for i_seq in zero_occ :
          print >> out, "    %s" % atoms[i_seq].id_str(suppress_segid=True)
      print >> out, ""
    if (refine_anomalous) :
      assert fmodel.f_obs().anomalous_flag()
      print >> out, "  anomalous refinement (new ions only): start %s" % \
        show_r_factors()
      fmodel.update(target_name="ls")
      anomalous_scatterer_groups.minimizer(
        fmodel=fmodel,
        groups=anomalous_groups)
      fmodel.update(target_name="ml")
      print >> out, "                                        final %s" % \
        show_r_factors()
      print >> out, ""
  return manager

def clean_up_ions (fmodel, model, params, log=None, verbose=True) :
  if (log is None) :
    log = null_out()
  ion_selection = model.pdb_hierarchy().atom_selection_cache().selection(
    "segid ION")
  ion_iselection = ion_selection.iselection()
  if (len(ion_iselection) == 0) :
    print >> log, "  No ions (segid=ION) found."
    return model
  n_sites_start = model.xray_structure.scatterers().size()
  new_model = model.select(~ion_selection)
  ion_model = model.select(ion_selection)
  ion_pdb_hierarchy = ion_model.pdb_hierarchy(sync_with_xray_structure=True)
  ion_atoms = ion_pdb_hierarchy.atoms()
  nonbonded_types = ion_model.restraints_manager.geometry.nonbonded_types
  nonbonded_charges = ion_model.restraints_manager.geometry.nonbonded_charges
  new_model.append_single_atoms(
    new_xray_structure=ion_model.xray_structure,
    atom_names=[ atom.name for atom in ion_atoms ],
    residue_names=[ atom.fetch_labels().resname for atom in ion_atoms ],
    nonbonded_types=nonbonded_types,
    nonbonded_charges=nonbonded_charges,
    chain_id=params.ion_chain_id,
    segids=[ "ION" for atom in ion_atoms ],
    refine_occupancies=params.refine_ion_occupancies,
    reset_labels=True)
  n_sites_end = new_model.xray_structure.scatterers().size()
  new_hierarchy = new_model.pdb_hierarchy()
  n_sites_pdb = new_hierarchy.atoms().size()
  assert (n_sites_start == n_sites_end == n_sites_pdb)
  new_selection = new_hierarchy.atom_selection_cache().selection("segid ION")
  ion_atoms = new_hierarchy.atoms().select(new_selection)
  if (verbose) :
    print >> log, "  Final list of ions:"
    for atom in ion_atoms :
      print >> log, "    %s" % atom.id_str()
    print >> log, ""
  fmodel.update_xray_structure(new_model.xray_structure)
  return new_model
