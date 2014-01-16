
# TODO more tests?

"""
Prototype for building alternate conformations into difference density.
The actual method is a variant of one that Pavel suggested, in combination
with the procedure in mmtbx.building.extend_sidechains: first, the
backbone atoms for a residue and its neighbors are refined into the
target map using minimization and/or annealing, then the sidechain is
replaced (using an idealized copy) and its placement optimized by a grid
search that also allows for backbone flexibility.
"""

from __future__ import division
from mmtbx.building import extend_sidechains
from mmtbx.building import disorder
from mmtbx import building
from libtbx import adopt_init_args, Auto, slots_getstate_setstate
from libtbx.str_utils import make_header, make_sub_header, format_value
from libtbx.utils import null_out
from libtbx import easy_mp
import time
import sys

class rebuild_residue (object) :
  """
  Callable wrapper class for rebuilding a single residue at a time.  This is
  not necessarily limited to modeling disorder, but it has been specifically
  designed to fit to a difference map in the presence of backbone and sidechain
  shifts.  Unlike some of the other tools, this method completely removes all
  sidechains within a sliding window before doing anything else.

  Only the target residue is returned; splitting of adjacent residues will be
  essential in most cases but is not handled here.
  """
  def __init__ (self,
      target_map,
      pdb_hierarchy,
      xray_structure,
      geometry_restraints_manager,
      rotamer_eval,
      d_min) :
    adopt_init_args(self, locals())
    from mmtbx.monomer_library import idealized_aa
    import mmtbx.monomer_library.server
    self.ideal_dict = idealized_aa.residue_dict()
    self.mon_lib_srv = mmtbx.monomer_library.server.server()

  def __call__ (self,
      atom_group,
      log,
      window_size=2,
      backbone_sample_angle=10,
      anneal=False,
      annealing_temperature=1000) :
    import iotbx.pdb.hierarchy
    from scitbx.array_family import flex
    assert (atom_group is not None)
    pdb_hierarchy = self.pdb_hierarchy.deep_copy()
    xray_structure = self.xray_structure.deep_copy_scatterers()
    geometry_restraints_manager = self.geometry_restraints_manager
    # FIXME this doesn't work - can't recover the atom_group afterwards!
    #hd_sel = xray_structure.hd_selection()
    #n_hydrogen = hd_sel.count(True)
    #if (n_hydrogen > 0) :
    #  non_hd_sel = ~hd_sel
    #  pdb_hierarchy = pdb_hierarchy.select(non_hd_sel)
    #  xray_structure = xray_structure.select(non_hd_sel)
    #  geometry_restraints_manager = geometry_restraints_manager.select(
    #    non_hd_sel)
    pdb_atoms = pdb_hierarchy.atoms()
    pdb_atoms.reset_i_seq()
    isel = building.extract_iselection([atom_group])
    atom_group = pdb_atoms[isel[0]].parent()
    atom_group_start = atom_group.detached_copy()
    needs_rebuild = not building.is_stub_residue(atom_group)
    residue_group = atom_group.parent()
    assert (len(residue_group.atom_groups()) == 1)
    sel_residues = building.get_window_around_residue(
      residue=atom_group,
      window_size=window_size)
    # get rid of sidechains for surrounding residues only
    adjacent_residues = []
    for other_rg in sel_residues :
      if (other_rg != residue_group) :
        adjacent_residues.append(other_rg)
    building.remove_sidechain_atoms(adjacent_residues)
    pdb_atoms = pdb_hierarchy.atoms()
    adjacent_trimmed_atom_names = pdb_atoms.extract_name()
    adjacent_trimmed_sel = pdb_atoms.extract_i_seq()
    xrs_adjacent_trimmed = xray_structure.select(adjacent_trimmed_sel)
    grm_adjacent_trimmed = geometry_restraints_manager.select(
      adjacent_trimmed_sel)
    pdb_atoms.reset_i_seq()
    # get rid of central sidechain and refine mainchain for entire window
    truncate = (not atom_group.resname in ["GLY","ALA"]) # XXX PRO?
    if (truncate) :
      building.remove_sidechain_atoms([ atom_group ])
    pdb_atoms = pdb_hierarchy.atoms()
    all_mc_sel = pdb_atoms.extract_i_seq()
    xrs_mc = xrs_adjacent_trimmed.select(all_mc_sel)
    pdb_atoms.reset_i_seq()
    window_mc_sel = building.extract_iselection(sel_residues)
    selection = flex.bool(pdb_atoms.size(), False).set_selected(window_mc_sel,
      True)
    restraints_manager = grm_adjacent_trimmed.select(all_mc_sel)
    box = building.box_build_refine_base(
      xray_structure=xrs_mc,
      pdb_hierarchy=pdb_hierarchy,
      selection=selection,
      processed_pdb_file=None,
      target_map=self.target_map,
      geometry_restraints_manager=restraints_manager.geometry,
      d_min=self.d_min,
      out=null_out(),
      debug=True)
    box.restrain_atoms(
      selection=box.others_in_box,
      reference_sigma=0.1)
    box.real_space_refine(selection=box.selection_in_box)
    sites_new = box.update_original_coordinates()
    pdb_atoms.set_xyz(sites_new)
    # extend and replace existing residue.  this is done in such a way that
    # the original atom ordering for the central residue is preserved, which
    # allows us to use the pre-existing geometry restraints instead of
    # re-calculating them every time this function is called.
    new_atom_group_base = extend_sidechains.extend_residue(
      residue=atom_group,
      ideal_dict=self.ideal_dict,
      hydrogens=False,
      mon_lib_srv=self.mon_lib_srv,
      match_conformation=True)
    new_atom_group = iotbx.pdb.hierarchy.atom_group(resname=atom_group.resname)
    for atom in atom_group_start.atoms() :
      for new_atom in new_atom_group_base.atoms() :
        if (new_atom.name == atom.name) :
          new_atom_group.append_atom(new_atom.detached_copy())
    assert len(new_atom_group.atoms()) == len(atom_group_start.atoms())
    rg = atom_group.parent()
    rg.remove_atom_group(atom_group)
    rg.append_atom_group(new_atom_group)
    pdb_atoms = pdb_hierarchy.atoms()
    pdb_atoms.reset_i_seq()
    new_names = pdb_atoms.extract_name()
    assert new_names.all_eq(adjacent_trimmed_atom_names)
    # get new box around this residue
    residue_sel = building.extract_iselection([ new_atom_group ])
    selection = flex.bool(pdb_atoms.size(), False).set_selected(residue_sel,
      True)
    xrs_adjacent_trimmed.set_sites_cart(pdb_atoms.extract_xyz())
    box = building.box_build_refine_base(
      xray_structure=xrs_adjacent_trimmed,
      pdb_hierarchy=pdb_hierarchy,
      selection=selection,
      processed_pdb_file=None,
      target_map=self.target_map,
      geometry_restraints_manager=grm_adjacent_trimmed.geometry,
      d_min=self.d_min,
      out=null_out(),
      debug=True)
    # place sidechain using mmtbx.refinement.real_space.fit_residue
    box.fit_residue_in_box(backbone_sample_angle=backbone_sample_angle)
    if (anneal) :
      box.anneal(start_temperature=annealing_temperature)
    #box.real_space_refine()
    sites_new = box.update_original_coordinates()
    pdb_hierarchy.atoms().set_xyz(sites_new)
    return building.atom_group_as_hierarchy(new_atom_group)

build_params_str = """
  expected_occupancy = None
    .type = float(value_min=0.1,value_max=0.9)
  window_size = 2
    .type = int
  backbone_sample_angle = 10
    .type = int
  anneal = False
    .type = bool
  annealing_temperature = 1000
    .type = int
  rmsd_min = 0.5
    .type = float
  rescore = True
    .type = bool
  map_thresholds {
    two_fofc_min_sc_mean = 0.8
      .type = float
    two_fofc_min_mc = 1.0
      .type = float
    fofc_min_sc_mean = 2.5
      .type = float
    starting_fofc_min_sc_single = 3.0
      .type = float
  }
"""

class residue_trial (slots_getstate_setstate) :
  __slots__ = [ "new_hierarchy", "sc_n_atoms", "sc_two_fofc_mean",
                "sc_fofc_mean", "two_fofc_values", "fofc_values",
                "stats", "occupancy", "rotamer", ]
  def __init__ (self, residue, new_hierarchy, occupancy, rotamer_eval,
                      fmodel, two_fofc_map, fofc_map) :
    self.new_hierarchy = new_hierarchy
    self.occupancy = occupancy
    self.two_fofc_values = []
    self.fofc_values = []
    self.sc_n_atoms = 0
    self.sc_fofc_mean = self.sc_two_fofc_mean = None
    unit_cell = fmodel.xray_structure.unit_cell()
    sc_fofc_sum = sc_two_fofc_sum = 0
    for atom in new_hierarchy.atoms() :
      assert (not atom.element.strip() in ["H","D"])
      name = atom.name.strip()
      site_frac = unit_cell.fractionalize(site_cart=atom.xyz)
      two_fofc_value = two_fofc_map.eight_point_interpolation(site_frac)
      fofc_value = fofc_map.eight_point_interpolation(site_frac)
      self.two_fofc_values.append(two_fofc_value)
      self.fofc_values.append(fofc_value)
      if (not name in ["N","C","O","CA", "CB"]) :
        self.sc_n_atoms += 1
        sc_fofc_sum += fofc_value
        sc_two_fofc_sum += two_fofc_value
    if (self.sc_n_atoms > 0) :
      self.sc_fofc_mean = sc_fofc_sum / self.sc_n_atoms
      self.sc_two_fofc_mean = sc_two_fofc_sum / self.sc_n_atoms
    alt_conf = self.as_atom_group()
    self.stats = disorder.coord_stats_for_atom_groups(residue, alt_conf)
    self.rotamer = None
    if (not residue.resname in ["GLY","ALA","PRO"]) :
      self.rotamer = rotamer_eval.evaluate_residue(alt_conf)

  def as_atom_group (self) :
    return self.new_hierarchy.only_model().only_chain().only_residue_group().\
      only_atom_group()

  def rescore (self, params, log=None, prefix="") :
    if (log is None) : log = null_out()
    reject = (self.rotamer == "OUTLIER")
    bad_mc_two_fofc_msg = None
    for i_seq, atom in enumerate(self.new_hierarchy.atoms()) :
      name = atom.name.strip()
      if (name in ["N","C","O","CA", "CB"]) :
        if (self.two_fofc_values[i_seq] < params.two_fofc_min_mc) :
          bad_mc_two_fofc_msg = "poor backbone: 2Fo-Fc(%s)=%.2f" % (name,
                self.two_fofc_values[i_seq])
          reject = True
          break
    if (self.sc_fofc_mean is not None) :
      if (self.sc_fofc_mean < params.fofc_min_sc_mean) :
        reject = True
      elif (self.sc_two_fofc_mean < params.two_fofc_min_sc_mean) :
        reject = True
    flag = ""
    if (reject) :
      flag = " !!!"
    print >> log, prefix+\
      "occupancy=%.2f rotamer=%s 2Fo-Fc(mc)=%s  Fo-Fc(sc)=%s%s" % \
      (self.occupancy, self.rotamer,
       format_value("%5f", self.sc_two_fofc_mean),
       format_value("%5f", self.sc_fofc_mean),
       flag)
    if (bad_mc_two_fofc_msg is not None) :
      print >> log, prefix+"  %s" % bad_mc_two_fofc_msg
    return (not reject)

def find_alternate_residue (residue,
    pdb_hierarchy,
    fmodel,
    restraints_manager,
    params,
    verbose=False,
    log=None) :
  if (log is None) :
    log = null_out()
  if (verbose) :
    print >> log, "  building %s" % residue.id_str()
  from scitbx.array_family import flex
  selection = flex.size_t()
  window = building.get_window_around_residue(residue,
    window_size=params.window_size)
  for pdb_object in window :
    selection.extend(pdb_object.atoms().extract_i_seq())
  assert (len(selection) > 0) and (not selection.all_eq(0))
  occupancies = []
  if (params.expected_occupancy is not None) :
    assert (0.1 <= params.expected_occupancy <= 0.9)
    occupancies = [ params.expected_occupancy ]
  else :
    occupancies = [ 0.2, 0.3, 0.4, 0.5 ]
  trials = []
  sites_start_1d = pdb_hierarchy.atoms().extract_xyz().as_double()
  from mmtbx.rotamer import rotamer_eval
  rotamer_manager = rotamer_eval.RotamerEval()
  for occupancy in occupancies :
    two_fofc_map, fofc_map = disorder.get_partial_omit_map(
      fmodel=fmodel.deep_copy(),
      selection=selection,
      selection_delete=None,#nearby_water_selection,
      negate_surrounding=True,
      partial_occupancy=1.0 - occupancy)
    rebuild = rebuild_residue(
      target_map=fofc_map,
      pdb_hierarchy=pdb_hierarchy,
      xray_structure=fmodel.xray_structure,
      geometry_restraints_manager=restraints_manager,
      rotamer_eval=rotamer_manager,
      d_min=fmodel.f_obs().d_min())
    new_hierarchy = rebuild(atom_group=residue,
      window_size=params.window_size,
      backbone_sample_angle=params.backbone_sample_angle,
      anneal=params.anneal,
      annealing_temperature=params.annealing_temperature,
      log=log)
    trial = residue_trial(
      residue=residue,
      new_hierarchy=new_hierarchy,
      occupancy=occupancy,
      rotamer_eval=rotamer_manager,
      fmodel=fmodel,
      two_fofc_map=two_fofc_map,
      fofc_map=fofc_map)
    trials.append(trial)
  sites_end_1d = pdb_hierarchy.atoms().extract_xyz().as_double()
  assert sites_start_1d.all_eq(sites_end_1d)
  return trials

class find_all_alternates (object) :
  """
  Wrapper for parallelizing calls to find_alternate_residue.
  """
  def __init__ (self,
      residues,
      pdb_hierarchy,
      fmodel,
      restraints_manager,
      params,
      nproc=Auto,
      verbose=False,
      log=sys.stdout) :
    adopt_init_args(self, locals())
    nproc = easy_mp.get_processes(nproc)
    print >> log, ""
    if (nproc == 1) :
      print >> log, "  running all residues serially"
      self.results = []
      for i_res in range(len(residues)) :
        self.results.append(self.__call__(i_res, log=log))
    else :
      print >> log, "  will use %d processes" % nproc
      self.results = easy_mp.pool_map(
        fixed_func=self,
        iterable=range(len(residues)),
        processes=nproc)

  def __call__ (self, i_res, log=None) :
    return find_alternate_residue(
      residue=self.residues[i_res],
      pdb_hierarchy=self.pdb_hierarchy,
      fmodel=self.fmodel,
      restraints_manager=self.restraints_manager,
      params=self.params,
      verbose=self.verbose,
      log=log)

def pick_best_alternate (
    trials,
    params,
    rotamer,
    log=None) :
  if (log is None) :
    log = null_out()
  if (params.rescore) :
    filtered = []
    for trial in trials :
      accept = trial.rescore(params=params.map_thresholds,
        log=log,
        prefix="    ")
      if (accept) : filtered.append(trial)
    trials = filtered
  if (len(trials) == 0) :
    return None
  elif (len(trials) == 1) :
    return trials[0]
  else :
    rmsd_max = 0
    best_trial = None
    for trial in trials :
      if (trial.stats.rmsd > rmsd_max) :
        rmsd_max = trial.stats.rmsd
        best_trial = trial
    return best_trial

def process_results (
    pdb_hierarchy,
    fmodel,
    residues_in,
    building_trials,
    params,
    verbose=False,
    log=sys.stdout) :
  assert (len(residues_in) == len(building_trials))
  from mmtbx.rotamer import rotamer_eval
  n_alternates = 0
  unit_cell = fmodel.xray_structure.unit_cell()
  two_fofc_map = fofc_map = None
  if (params.rescore) :
    two_fofc_map, fofc_map = building.get_difference_maps(fmodel)
  print >> log, ""
  print >> log, "Scoring and assembling disordered residues..."
  rot_eval = rotamer_eval.RotamerEval()
  for main_conf, trials in zip(residues_in, building_trials) :
    if (len(trials) == 0) :
      continue
    print >> log, "  %s:" % main_conf.id_str()
    main_rotamer = alt_rotamer = None
    if (not main_conf.resname in ["GLY","PRO","ALA"]) :
      main_rotamer = rot_eval.evaluate_residue(main_conf)
      assert (main_rotamer != "OUTLIER")
    best_trial = pick_best_alternate(
      trials=trials,
      params=params,
      rotamer=main_rotamer,
      log=log)
    if (best_trial is None) :
      continue
    new_conf = best_trial.as_atom_group()
    changed_rotamer = (best_trial.rotamer == main_rotamer)
    skip = False
    flag = ""
    stats = best_trial.stats
    if (stats.rmsd < params.rmsd_min) and (not changed_rotamer) :
      skip = True
    print >> log, "    selected conformer (occ=%.2f):" % best_trial.occupancy
    if (params.rescore) : # FIXME this is very crude...
      fofc_max = 0
      for atom in new_conf.atoms() :
        name = atom.name.strip()
        site_frac = unit_cell.fractionalize(site_cart=atom.xyz)
        fofc_value = fofc_map.eight_point_interpolation(site_frac)
        if ((not name in ["N","C","O","CA", "CB"]) or
            ((name == "O") and (new_conf.resname in ["GLY", "ALA"]))) :
          if (fofc_value > fofc_max) :
            fofc_max = fofc_value
      if (fofc_max < params.map_thresholds.starting_fofc_min_sc_single) :
        skip = True
      if (not skip) : flag = " ***"
      print >> log, "      RMSD=%5.3f  max. change=%.2f  max(Fo-Fc)=%.1f%s" \
        % (stats.rmsd, stats.max_dev, fofc_max, flag)
    else :
      if (not skip) : flag = " ***"
      print >> log, "      RMSD=%5.3f  max. change=%.2f%s" % \
        (stats.rmsd, stats.max_dev, flag)
    if (changed_rotamer) :
      print >> log, "      starting rotamer=%s  new rotamer=%s" % \
        (main_rotamer, best_trial.rotamer)
    if (skip) : continue
    residue_group = main_conf.parent()
    main_conf.altloc = 'A'
    new_occ = 0.5
    if (params.expected_occupancy is not None) :
      new_occ = params.expected_occupancy
    for atom in main_conf.atoms() :
      atom.occ = 1.0 - new_occ
      atom.segid = "OLD1"
    alt_conf = new_conf.detached_copy()
    alt_conf.altloc = 'B'
    for atom in alt_conf.atoms() :
      atom.segid = "NEW1"
      atom.occ = new_occ
    residue_group.append_atom_group(alt_conf)
    n_alternates += 1
  if (n_alternates > 0) :
    spread_alternates(pdb_hierarchy, params, log=log)
  return n_alternates

def spread_alternates (pdb_hierarchy, params, log) :
  print >> log, ""
  print >> log, "Splitting adjacent residues..."
  def split_residue (residue_group) :
    print >> log, "  %s" % residue_group.id_str()
    new_occ = 0.5
    if (params.expected_occupancy is not None) :
      new_occ = params.expected_occupancy
    main_conf = residue_group.only_atom_group()
    main_conf.altloc = 'A'
    for atom in main_conf.atoms() :
      atom.occ = 1.0 - new_occ
      atom.segid = "OLD2"
    alt_conf = main_conf.detached_copy()
    alt_conf.altloc = 'B'
    for atom in alt_conf.atoms() :
      atom.occ = new_occ
      atom.segid = 'NEW2'
    residue_group.append_atom_group(alt_conf)
  for chain in pdb_hierarchy.only_model().chains() :
    residue_groups = chain.residue_groups()
    for i_res, residue_group in enumerate(residue_groups) :
      atom_groups = residue_group.atom_groups()
      if (len(atom_groups) > 1) :
        segid = atom_groups[-1].atoms()[0].segid
        if (segid != 'NEW1') :
          continue
        if (i_res > 0) :
          prev_group = residue_groups[i_res - 1]
          if (len(prev_group.atom_groups()) == 1) :
            split_residue(prev_group)
        if (i_res < len(residue_groups) - 1) :
          next_group = residue_groups[i_res + 1]
          if (len(next_group.atom_groups()) == 1) :
            split_residue(next_group)

def real_space_refine (
    pdb_hierarchy,
    fmodel,
    cif_objects,
    out) :
  from scitbx.array_family import flex
  make_sub_header("Real-space refinement", out=out)
  fmodel.info().show_targets(out=out, text="Rebuilt model")
  processed_pdb_file = building.reprocess_pdb(
    pdb_hierarchy=pdb_hierarchy,
    cif_objects=cif_objects,
    crystal_symmetry=fmodel.xray_structure,
    out=null_out())
  # get the 2mFo-DFc map without alternates!
  two_fofc_map = fmodel.two_fofc_map(exclude_free_r_reflections=True)
  pdb_hierarchy = processed_pdb_file.all_chain_proxies.pdb_hierarchy
  pdb_atoms = pdb_hierarchy.atoms()
  xray_structure = processed_pdb_file.xray_structure()
  geometry_restraints_manager = processed_pdb_file.geometry_restraints_manager(
    show_energies=False)
  fmodel.update_xray_structure(xray_structure)
  sele_cache = pdb_hierarchy.atom_selection_cache()
  # this will include both the newly built residues and the original atoms,
  # including residues split to allow for backbone flexibility.
  sele_split = sele_cache.selection(
    "segid NEW1 or segid NEW2 or segid OLD1 or segid OLD2")
  assert (len(sele_split) > 0)
  k = 0
  while (k < len(sele_split)) :
    if (sele_split[k]) :
      current_fragment = flex.size_t()
      while (sele_split[k]) :
        current_fragment.append(k)
        k += 1
      print >> out, "  refining %d atoms..." % len(current_fragment)
      frag_selection = flex.bool(sele_split.size(), current_fragment)
      box = building.box_build_refine_base(
        pdb_hierarchy=pdb_hierarchy,
        xray_structure=xray_structure,
        processed_pdb_file=processed_pdb_file,
        target_map=two_fofc_map,
        selection=frag_selection,
        d_min=fmodel.f_obs().d_min(),
        out=out)
      box.restrain_atoms("segid OLD1 or segid OLD2", 0.02)
      box.restrain_atoms("segid NEW1", 0.05)
      # first fix the geometry of adjacent residues
      box.real_space_refine("segid NEW2")
      # now the entire B conformer
      box.real_space_refine("segid NEW1 or segid NEW2")
      sites_new = box.update_original_coordinates()
      xray_structure.set_sites_cart(sites_new)
      pdb_atoms.set_xyz(sites_new)
    else :
      k += 1
  fmodel.update_xray_structure(xray_structure)
  fmodel.info().show_targets(out=out, text="After real-space refinement")
  return pdb_hierarchy

master_phil_str = """
building {
  %s
  #delete_hydrogens = False
  #  .type = bool
}
prefilter {
  include scope mmtbx.building.disorder.filter_params_str
}""" % build_params_str

def build_cycle (pdb_hierarchy,
    fmodel,
    geometry_restraints_manager,
    params,
    selection=None,
    cif_objects=(),
    nproc=Auto,
    out=sys.stdout,
    verbose=False,
    i_cycle=0) :
  from mmtbx import restraints
  from scitbx.array_family import flex
  t_start = time.time()
  hd_sel = fmodel.xray_structure.hd_selection()
  n_hydrogen = hd_sel.count(True)
  if (n_hydrogen > 0) and (True) : #params.building.delete_hydrogens) :
    print >> out, "WARNING: %d hydrogen atoms will be removed!" % n_hydrogen
    non_hd_sel = ~hd_sel
    pdb_hierarchy = pdb_hierarchy.select(non_hd_sel)
    xray_structure = fmodel.xray_structure.select(non_hd_sel)
    fmodel.update_xray_structure(xray_structure)
    geometry_restraints_manager = geometry_restraints_manager.select(non_hd_sel)
  pdb_atoms = pdb_hierarchy.atoms()
  segids = pdb_atoms.extract_segid().strip()
  if (not segids.all_eq("")) :
    print >> out, "WARNING: resetting segids to blank"
    for i_seq, atom in enumerate(pdb_atoms) :
      atom.segid = ""
      sc = fmodel.xray_structure.scatterers()[i_seq]
      sc.label = atom.id_str()
  if isinstance(selection, str) :
    sele_cache = pdb_hierarchy.atom_selection_cache()
    selection = sele_cache.selection(selection)
  make_header("Build cycle %d" % i_cycle, out=out)
  candidate_residues = disorder.filter_before_build(
    pdb_hierarchy=pdb_hierarchy,
    fmodel=fmodel,
    geometry_restraints_manager=geometry_restraints_manager,
    selection=selection,
    params=params.prefilter,
    verbose=verbose,
    log=out)
  restraints_manager = restraints.manager(
    geometry=geometry_restraints_manager,
    normalization=True)
  make_sub_header("Finding alternate conformations", out=out)
  fmodel.info().show_rfactors_targets_scales_overall(out=out)
  building_trials = find_all_alternates(
    residues=candidate_residues,
    pdb_hierarchy=pdb_hierarchy,
    restraints_manager=restraints_manager,
    fmodel=fmodel,
    params=params.building,
    nproc=params.nproc,
    verbose=verbose,
    log=out).results
  n_alternates = process_results(
    pdb_hierarchy=pdb_hierarchy,
    fmodel=fmodel,
    residues_in=candidate_residues,
    building_trials=building_trials,
    params=params.building,
    verbose=verbose,
    log=out)
  if (n_alternates == 0) :
    print >> out, "No alternates built this round."
  else :
    pdb_hierarchy = real_space_refine(
      pdb_hierarchy=pdb_hierarchy,
      fmodel=fmodel,
      cif_objects=cif_objects,
      out=out)
  t_end = time.time()
  print >> out, "Build time: %.1fs" % (t_end - t_start)
  pdb_atoms = pdb_hierarchy.atoms()
  pdb_atoms.reset_serial()
  pdb_atoms.reset_i_seq()
  pdb_atoms.reset_tmp()
  for atom in pdb_atoms :
    segid = atom.segid.strip()
    if (segid.startswith("OLD")) :
      segid = ""
    elif (segid.startswith("NEW")) :
      segid = "NEW"
  return pdb_hierarchy
