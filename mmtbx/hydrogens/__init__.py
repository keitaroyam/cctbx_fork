from __future__ import division
from mmtbx.utils import rotatable_bonds
from scitbx.matrix import rotate_point_around_axis
from cctbx.array_family import flex
from cctbx import maptbx
import iotbx.pdb

hydrogens_master_params_str = """
refine = individual riding *Auto
  .type = choice
  .help = Choice for refinement: riding model or full (H is refined as \
          other atoms, useful at very high resolutions only)
  .short_caption = Hydrogen refinement model
  .expert_level=1
optimize_scattering_contribution = True
  .type = bool
contribute_to_f_calc = True
  .type = bool
  .help = Add H contribution to Xray (Fcalc) calculations
  .short_caption=Include hydrogens in Fcalc
  .expert_level=1
high_resolution_limit_to_include_scattering_from_h = 1.6
  .type = float
  .short_caption = High-resolution limit to include scattering from H
  .expert_level=2
real_space_optimize_x_h_orientation = True
  .type = bool
  .short_caption = Optimize X-H orientation in real-space
  .expert_level = 1
xh_bond_distance_deviation_limit = 0.0
  .type = float
  .help = Idealize XH bond distances if deviation from ideal is greater \
          than xh_bond_distance_deviation_limit
  .short_caption = X-H bond distance deviation limit
  .expert_level=2
"""

def rotatable(pdb_hierarchy, mon_lib_srv, restraints_manager, log):
  """
  General tool to identify rotatable H, such as C-O-H, C-H3, in any molecule.
  """
  result = []
  def analyze_group_aa_specific(g, atoms):
    result = []
    for gi in g:
      assert len(gi[0])==2 # because this is axis
      assert len(gi[1])>0  # because these are atoms rotating about this axis
      # condition 1: axis does not contain H or D
      a1, a2 = atoms[gi[0][0]], atoms[gi[0][1]]
      e1 = a1.element.strip().upper()
      e2 = a2.element.strip().upper()
      condition_1 = [e1,e2].count("H")==0 and [e1,e2].count("D")==0
      # condition 2: all atoms to rotate are H or D
      condition_2 = True
      rot_atoms = []
      for gi1i in gi[1]:
        if(not atoms[gi1i].element.strip().upper() in ["H","D"]):
          condition_2 = False
          break
      rot_atoms = []
      axis = None
      if(condition_1 and condition_2):
        axis = [a1.i_seq, a2.i_seq]
        for gi1i in gi[1]:
          rot_atoms.append(atoms[gi1i].i_seq)
        result.append([axis, rot_atoms])
    if(len(result)>0 is not None): return result
    else: return None
  def analyze_group_general(g, atoms, bps, psel):
    result = []
    for gi in g:
      condition_1, condition_2, condition_3 = None,None,None
      assert len(gi[0])==2 # because this is axis
      assert len(gi[1])>0  # because these are atoms rotating about this axis
      # condition 1: axis does not contain H or D
      a1, a2 = atoms[gi[0][0]], atoms[gi[0][1]]
      e1 = a1.element.strip().upper()
      e2 = a2.element.strip().upper()
      condition_1 = [e1,e2].count("H")==0 and [e1,e2].count("D")==0
      s1 = set(gi[1])
      if(condition_1):
        # condition 2: all atoms to rotate are H or D
        condition_2 = True
        for gi1i in gi[1]:
          if(not atoms[gi1i].element.strip().upper() in ["H","D"]):
            condition_2 = False
            break
        if(condition_2):
          # condition 3: one of axis atoms is terminal (bonded to another axis
          #              atom and hydrogens
          condition_3 = False
          for gia in gi[0]:
            bonds_involved_into = []
            for bp in bps:
              if(gia in bp.i_seqs):
                for i_seq in bp.i_seqs:
                  if(atoms[i_seq].element.strip().upper() in ["H","D"]):
                    bonds_involved_into.append(i_seq)
            s2 = set(bonds_involved_into)
            s = list(s1 & s2)
            if(len(s)>0): condition_3 = True
          #
          if(condition_1 and condition_2 and condition_3):
            axis = [a1.i_seq, a2.i_seq]
            rot_atoms = []
            in_plane = False
            for i in bonds_involved_into:
              if(atoms[i].i_seq in psel): in_plane = True
              rot_atoms.append(atoms[i].i_seq)
            if(not in_plane): result.append([axis, rot_atoms])
    if(len(result)>0 is not None): return result
    else: return None
  if(restraints_manager is not None):
    psel = flex.size_t()
    for p in restraints_manager.geometry.planarity_proxies:
      psel.extend(p.i_seqs)
  # very handy for debugging: do not remove
  #NAMES = pdb_hierarchy.atoms().extract_name()
  #
  get_class = iotbx.pdb.common_residue_names_get_class
  import scitbx.graph.tardy_tree
  for model in pdb_hierarchy.models():
    for chain in model.chains():
      residue_groups = chain.residue_groups()
      n_residues = len(residue_groups)
      for i_rg, residue_group in enumerate(residue_groups):
        first_or_last = i_rg == 0 or i_rg+1 == n_residues
        conformers = residue_group.conformers()
        for conformer in residue_group.conformers():
          for residue in conformer.residues():
            if(residue.resname.strip().upper() == "PRO"): continue
            atoms = residue.atoms()
            if(get_class(name=residue.resname)=="common_water" and
               len(atoms)==1):
                 continue
            if(get_class(name=residue.resname)=="common_amino_acid" and
               not first_or_last):
              fr = rotatable_bonds.axes_and_atoms_aa_specific(
                residue=residue, mon_lib_srv=mon_lib_srv,
                remove_clusters_with_all_h=False, log=log)
              if(fr is not None):
                r = analyze_group_aa_specific(g=fr, atoms=atoms)
                if(r is not None):
                  for r_ in r: result.append(r_)
            elif(restraints_manager is not None):
              elements = atoms.extract_element()
              names = atoms.extract_name()
              # create tardy_model
              iselection = atoms.extract_i_seq()
              sites_cart = atoms.extract_xyz()
              masses     = [1]*sites_cart.size()
              labels     = range(sites_cart.size())
              grm_i = restraints_manager.select(iselection)
              bps = grm_i.geometry.pair_proxies(
                sites_cart = sites_cart).bond_proxies.simple
              edge_list = []
              for bp in bps: edge_list.append(bp.i_seqs)
              fixed_vertex_lists = []
              tmp_r = []
              # try all possible edges (bonds) as potential fixed vertices and
              # accept only non-redundant
              for bp in bps:
                tardy_tree = scitbx.graph.tardy_tree.construct(
                  sites              = sites_cart,
                  edge_list          = edge_list,
                  fixed_vertex_lists = [bp.i_seqs])
                tardy_model = scitbx.rigid_body.tardy_model(
                  labels        = labels,
                  sites         = sites_cart,
                  masses        = masses,
                  tardy_tree    = tardy_tree,
                  potential_obj = None)
                fr = rotatable_bonds.axes_and_atoms_aa_specific(
                  residue=residue, mon_lib_srv=mon_lib_srv,
                  remove_clusters_with_all_h=False, log=None,
                  tardy_model = tardy_model)
                if(fr is not None):
                  r = analyze_group_general(g=fr, atoms=atoms,bps=bps,psel=psel)
                  if(r is not None and len(r)>0):
                    for r_ in r:
                      if(not r_ in tmp_r):
                        if(not r_ in tmp_r): tmp_r.append(r_)
              for r in tmp_r:
                result.append(r)
  # very handy for debugging: do not remove
  #for r_ in result:
  #  print "  analyze_group:", r_, \
  #    [NAMES[i] for i in r_[0]], [NAMES[i] for i in r_[1]], residue.resname
  return result

def count_rotatable(selections):
  result = 0
  for s in selections:
    result += len(s[1])
  return result


def fit_rotatable(
      pdb_hierarchy,
      xray_structure,
      map_data,
      rotatable_h_selection):
  unit_cell = xray_structure.unit_cell()
  sites_cart = xray_structure.sites_cart()
  scatterers = xray_structure.scatterers()
  for sel_ in rotatable_h_selection:
    ed_val = -1
    angle = 0.
    angular_step = 1
    axis = sel_[0]
    points_i_seqs = sel_[1]
    sites_frac_best = flex.vec3_double(len(points_i_seqs))
    while angle <= 360:
      sites_frac_tmp  = flex.vec3_double(len(points_i_seqs))
      ed_val_ = 0
      for i_seq, point_i_seq in enumerate(points_i_seqs):
        site_cart_new = rotate_point_around_axis(
          axis_point_1 = sites_cart[axis[0]],
          axis_point_2 = sites_cart[axis[1]],
          point        = sites_cart[point_i_seq],
          angle        = angle,
          deg          = True)
        site_frac_new = unit_cell.fractionalize(site_cart_new)
        ed_val_ += abs(maptbx.eight_point_interpolation(map_data,site_frac_new))
        sites_frac_tmp[i_seq] = site_frac_new
      if(ed_val_ > ed_val):
        ed_val = ed_val_
        sites_frac_best = sites_frac_tmp.deep_copy()
      angle += angular_step
    for i_seq, point_i_seq in enumerate(points_i_seqs):
      scatterers[point_i_seq].site = sites_frac_best[i_seq]
  pdb_hierarchy.adopt_xray_structure(xray_structure)

def run_fit_rotatable(
      fmodel,
      ref_model,
      angular_step,
      log = None,
      use_h_omit_map = False,
      map_type="2mFo-DFc"):
  pdb_hierarchy = ref_model.pdb_hierarchy(sync_with_xray_structure=True)
  xrs = fmodel.xray_structure
  rotatable_h_selection = rotatable(
    pdb_hierarchy      = pdb_hierarchy,
    mon_lib_srv        = ref_model.processed_pdb_files_srv.mon_lib_srv,
    restraints_manager = ref_model.restraints_manager,
    log                = log)
  rotatable_h_selection_1d = []
  for s in rotatable_h_selection:
    rotatable_h_selection_1d.extend(s[1])
  rotatable_h_selection_1d = flex.size_t(rotatable_h_selection_1d)
  rotatable_h_selection_1d_bool = flex.bool(xrs.scatterers().size(),
    rotatable_h_selection_1d)
  if(log is not None):
    print >> log, "Real-space grid search fit H (or D) atoms:"
    print >> log, "  start:  r_work=%6.4f r_free=%6.4f"%(fmodel.r_work(),
      fmodel.r_free())
  if(use_h_omit_map):
    xrs_omit = fmodel.xray_structure.select(~rotatable_h_selection_1d_bool)
    fmodel.update_xray_structure(xray_structure = xrs_omit, update_f_calc= True)
    if(log is not None):
      print >> log, "  H omit: r_work=%6.4f r_free=%6.4f"%(fmodel.r_work(),
        fmodel.r_free())
  fft_map = fmodel.electron_density_map().fft_map(
    resolution_factor = 1./4.,
    map_type          = map_type,
    symmetry_flags    = maptbx.use_space_group_symmetry)
  fft_map.apply_sigma_scaling()
  map_data = fft_map.real_map_unpadded()
  fit_rotatable(
    pdb_hierarchy  = pdb_hierarchy,
    xray_structure = xrs,
    rotatable_h_selection=rotatable_h_selection,
    map_data       = map_data)
  fmodel.update_xray_structure(xray_structure = xrs, update_f_calc=True)
  ref_model.xray_structure = xrs
  if(log is not None):
    print >> log, "  final:  r_work=%6.4f r_free=%6.4f"%(fmodel.r_work(),
      fmodel.r_free())
