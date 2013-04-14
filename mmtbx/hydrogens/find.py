from __future__ import division
from cctbx.array_family import flex
from mmtbx import find_peaks
from mmtbx import utils
import iotbx.phil
from scitbx import matrix
from libtbx import adopt_init_args
from mmtbx.refinement import print_statistics
import mmtbx.utils
from cctbx import maptbx
from cctbx import sgtbx
import cctbx

master_params_part1 = iotbx.phil.parse("""\
map_type = mFobs-DFmodel
  .type = str
  .help = Map type to be used to find hydrogens
map_cutoff = 2.0
  .type = float
  .help = Map cutoff
angular_step = 3.0
  .type = float
  .help = Step in degrees for 6D rigid body search for best fit
dod_and_od = False
  .type = bool
  .help = Build DOD/OD/O types of waters for neutron models
filter_dod = False
  .type = bool
  .help = Filter DOD/OD/O by correlation
min_od_dist = 0.8
  .type = float
  .help = Minimum O-D distance when building water from peaks
max_od_dist = 1.35
  .type = float
  .help = Maximum O-D distance when building water from peaks
min_dod_angle = 85.0
  .type = float
  .help = Minimum D-O-D angle when building water from peaks
max_dod_angle = 170.0
  .type = float
  .help = Maximum D-O-D angle when building water from peaks
h_bond_min_mac = 1.8
  .type = float
  .short_caption = H-bond minimum for DOD solvent-model
  .expert_level = 1
h_bond_max = 3.5
  .type = float
  .short_caption = Maximum H-bond length in DOD solvent model
  .expert_level = 1
""")

master_params_part2 = find_peaks.master_params.fetch(iotbx.phil.parse("""\
use_sigma_scaled_maps = True
resolution_factor = 1./4.
map_next_to_model
{
  min_model_peak_dist = 0.7
  max_model_peak_dist = 1.05
  min_peak_peak_dist = 1.0
  use_hydrogens = False
}
peak_search
{
  peak_search_level = 1
  min_cross_distance = 1.0
}
"""))

def all_master_params():
  return iotbx.phil.parse("""\
    include scope mmtbx.hydrogens.find.master_params_part1
    include scope mmtbx.hydrogens.find.master_params_part2
""", process_includes=True)

class h_peak(object):
  def __init__(self, site_frac,
                     height,
                     dist,
                     scatterer_o,
                     pdb_atom_o,
                     i_seq_o):
    self.site_frac = site_frac
    self.height = height
    self.dist = dist
    self.scatterer_o = scatterer_o
    self.pdb_atom_o = pdb_atom_o
    self.i_seq_o = i_seq_o

class water_and_peaks(object):
  def __init__(self, i_seq_o,
                     i_seq_h1,
                     i_seq_h2,
                     peaks_sites_frac):
    assert [i_seq_o,i_seq_h1,i_seq_h2,peaks_sites_frac].count(None) == 0
    adopt_init_args(self, locals())

def water_bond_angle(o,h1,h2):
  result = None
  a = h1[0]-o[0], h1[1]-o[1], h1[2]-o[2]
  b = h2[0]-o[0], h2[1]-o[1], h2[2]-o[2]
  a = matrix.col(a)
  b = matrix.col(b)
  return a.angle(b, deg=True)

def find_hydrogen_peaks(fmodel,
                        pdb_atoms,
                        params,
                        log):
  fp_manager = find_peaks.manager(fmodel     = fmodel,
                                  map_type   = params.map_type,
                                  map_cutoff = params.map_cutoff,
                                  params     = params,
                                  log        = log)
  result = fp_manager.peaks_mapped()
  fp_manager.show_mapped(pdb_atoms = pdb_atoms)
  return result

def extract_hoh_peaks(peaks, pdb_hierarchy, pdb_atoms, xray_structure):
  scatterers = xray_structure.scatterers()
  assert scatterers.size() == pdb_atoms.size()
  assert peaks.sites.size() == peaks.heights.size()
  assert peaks.heights.size() == peaks.iseqs_of_closest_atoms.size()
  sentinel = pdb_atoms.reset_tmp(first_value=0, increment=0)
  for i_seq in peaks.iseqs_of_closest_atoms:
    pdb_atoms[i_seq].tmp = 1
  get_class = iotbx.pdb.common_residue_names_get_class
  o_i_seq_ag = {}
  result = []
  for model in pdb_hierarchy.models():
    for chain in model.chains():
      for rg in chain.residue_groups():
        for ag in rg.atom_groups():
          is_water = (get_class(name=ag.resname) == "common_water")
          for atom in ag.atoms():
            if (atom.tmp == 0): continue
            assert atom.element.strip() not in ['H','D']
            if (is_water):
              assert atom.element.strip() == 'O'
              o_i_seq_ag[atom.i_seq] = ag
              break
  del sentinel
  o_i_seq_i_peak = {}
  for i_seq in o_i_seq_ag:
    o_i_seq_i_peak[i_seq] = []
  for i_peak,i_seq in enumerate(peaks.iseqs_of_closest_atoms):
    if(o_i_seq_i_peak.get(i_seq) is not None):
      o_i_seq_i_peak[i_seq].append(i_peak)
  for i_seq,ag in o_i_seq_ag.items():
    ag_atoms = ag.atoms()
    assert ag_atoms.size() == 3
    o_atom = None
    h_atoms = []
    for atom in ag_atoms:
      el = atom.element.strip()
      if (el == 'O'):
        o_atom = atom
      else:
        assert el in ['H','D']
        h_atoms.append(atom)
    assert o_atom is not None
    assert len(h_atoms) == 2
    result.append(water_and_peaks(
      i_seq_o = o_atom.i_seq,
      i_seq_h1 = h_atoms[0].i_seq,
      i_seq_h2 = h_atoms[1].i_seq,
      peaks_sites_frac = [peaks.sites[i_peak]
        for i_peak in o_i_seq_i_peak[i_seq]]))
  return result

def fit_water(water_and_peaks, xray_structure, params, log):
  scatterers = xray_structure.scatterers()
  uc = xray_structure.unit_cell()
  site_frac_o  = scatterers[water_and_peaks.i_seq_o ].site
  site_frac_h1 = scatterers[water_and_peaks.i_seq_h1].site
  site_frac_h2 = scatterers[water_and_peaks.i_seq_h2].site
  peak_sites_frac = water_and_peaks.peaks_sites_frac
  if(len(peak_sites_frac) == 1):
    sc1 = scatterers[water_and_peaks.i_seq_h1]
    sc2 = scatterers[water_and_peaks.i_seq_h2]
    if(sc1.occupancy < sc2.occupancy and sc2.occupancy > 0.3):
      site_frac_h2 = sc2.site
    elif(sc1.occupancy > sc2.occupancy and sc1.occupancy > 0.3):
      site_frac_h2 = scatterers[water_and_peaks.i_seq_h1].site
    else:
      site_frac_h2 = peak_sites_frac[0]
    result = mmtbx.utils.fit_hoh(
      site_frac_o     = site_frac_o,
      site_frac_h1    = site_frac_h1,
      site_frac_h2    = site_frac_h2,
      site_frac_peak1 = peak_sites_frac[0],
      site_frac_peak2 = site_frac_h2,
      angular_shift   = params.angular_step,
      unit_cell       = uc)
    d_best = result.dist_best()
    o = uc.fractionalize(result.site_cart_o_fitted)
    h1 = uc.fractionalize(result.site_cart_h1_fitted)
    h2 = uc.fractionalize(result.site_cart_h2_fitted)
  else:
    peak_pairs = []
    for i, s1 in enumerate(peak_sites_frac):
      for j, s2 in enumerate(peak_sites_frac):
        if i < j:
          peak_pairs.append([s1,s2])
    d_best = 999.
    for pair in peak_pairs:
      result = mmtbx.utils.fit_hoh(
        site_frac_o     = site_frac_o,
        site_frac_h1    = site_frac_h1,
        site_frac_h2    = site_frac_h2,
        site_frac_peak1 = pair[0],
        site_frac_peak2 = pair[1],
        angular_shift   = params.angular_step,
        unit_cell       = uc)
      if(result.dist_best() < d_best):
        d_best = result.dist_best()
        o = uc.fractionalize(result.site_cart_o_fitted)
        h1 = uc.fractionalize(result.site_cart_h1_fitted)
        h2 = uc.fractionalize(result.site_cart_h2_fitted)
  if(d_best < 1.0):
    # do not move HOH located on special position
    skip = False
    sites = [scatterers[water_and_peaks.i_seq_o ].site,
             scatterers[water_and_peaks.i_seq_h1].site,
             scatterers[water_and_peaks.i_seq_h2].site]
    for site in sites:
      site_symmetry = sgtbx.site_symmetry(
        xray_structure.unit_cell(),
        xray_structure.space_group(),
        site,
        0.5,
        True)
      if(site_symmetry.n_matrices() != 1):
        skip = True
        break
    #
    if(not skip):
      scatterers[water_and_peaks.i_seq_o ].site = o
      scatterers[water_and_peaks.i_seq_h1].site = h1
      scatterers[water_and_peaks.i_seq_h2].site = h2
  print >> log, "%6.3f"%d_best

def run(fmodel, model, log, params = None):
  print_statistics.make_header("Fit water hydrogens into residual map",
    out = log)
  if(params is None):
    params = all_master_params().extract()
  print_statistics.make_sub_header("find peak-candidates", out = log)
  peaks = find_hydrogen_peaks(
    fmodel = fmodel,
    pdb_atoms = model.pdb_atoms,
    params = params,
    log = log)
  waters_and_peaks = extract_hoh_peaks(
    peaks = peaks,
    pdb_hierarchy = model.pdb_hierarchy(),
    pdb_atoms = model.pdb_atoms,
    xray_structure = model.xray_structure)
  print_statistics.make_sub_header("6D rigid body fit of HOH", out = log)
  print >> log, "Fit quality:"
  for water_and_peaks in waters_and_peaks:
    fit_water(water_and_peaks = water_and_peaks,
              xray_structure  = model.xray_structure,
              params          = params,
              log             = log)
  # adjust ADP for H
  # TODO mrt: probably H bfactors should be equal to those
  # of the bonded atom
  u_isos = model.xray_structure.extract_u_iso_or_u_equiv()
  u_iso_mean = flex.mean(u_isos)
  sel_big = u_isos > u_iso_mean*2
  hd_sel = model.xray_structure.hd_selection()
  sel_big.set_selected(~hd_sel, False)
  model.xray_structure.set_u_iso(value = u_iso_mean, selection = sel_big)

def build_dod_and_od(model, fmodels, log=None, params=None):
  fmodels.update_xray_structure(xray_structure = model.xray_structure,
    update_f_calc  = True,
    update_f_mask  = True)
  fmodels.show_short()
  hbparams = params.hydrogens.build
  if hbparams is None:
    hbparams = all_master_params().extract()
  if log is None:
    log = fmodels.log
  if fmodels.fmodel_n is not None:
    fmodel = fmodels.fmodel_neutron()
  else:
    fmodel = fmodels.fmodel_xray()
  title = "xray"
  if fmodel.xray_structure.guess_scattering_type_neutron():
    title="neutron"
  print_statistics.make_header("Build water hydrogens into "+title+" difference"
    " map", out=log)
  model = build_water_hydrogens_from_map(model, fmodel, params=hbparams, log=log)
  #
  if hbparams.filter_dod:
    bmax=params.ordered_solvent.b_iso_max
    water_map_correlations(model, fmodels, log)
    model = remove_zero_occupancy(model,0.01,bmax)
    model.reprocess_pdb_hierarchy_inefficient()
  fmodels.update_xray_structure(xray_structure = model.xray_structure,
    update_f_calc  = True,
    update_f_mask  = True)
  fmodels.show_short()
  compare_hierarchy(model.pdb_hierarchy(), model.xray_structure.scatterers(),
      model.xray_structure.unit_cell())
  sol_sel = model.solvent_selection()
  hd_sel = sol_sel & model.xray_structure.hd_selection()
  print>>log, "Final number of water hydrogens: ", hd_sel.count(True)
  return model, fmodels

def remove_zero_occupancy(model, min_occupancy=0.05, max_b_iso=80.):
  atoms = model.xray_structure.scatterers()
  occ = atoms.extract_occupancies()
  # print "dir(atoms): ", dir(atoms)
  umax = cctbx.adptbx.b_as_u(max_b_iso)
  uiso = atoms.extract_u_iso_or_u_equiv(model.xray_structure.unit_cell())
  sol_sel = model.solvent_selection()
  hd_sel = model.xray_structure.hd_selection()
  sel = sol_sel & hd_sel & ((occ < min_occupancy) | (uiso>umax))
  sel = ~sel
  return model.select( selection = sel)

# TODO code duplicate in model.add_hydrogens.insert_atoms
def insert_atom_into_model(xs, atom, atom_name, site_frac, occupancy, uiso, element):
  i_seq = atom.i_seq
  cart = xs.unit_cell().orthogonalize
  xyz = cart(site_frac)
  h = atom.detached_copy()
  h.name = atom_name
  h.xyz = xyz
  h.sigxyz = (0,0,0)
  h.occ = occupancy
  h.sigocc = 0
  h.b = cctbx.adptbx.u_as_b(uiso)
  h.sigb = 0
  h.uij = (-1,-1,-1,-1,-1,-1)
  if (iotbx.pdb.hierarchy.atom.has_siguij()):
    h.siguij = (-1,-1,-1,-1,-1,-1)
  h.element = "%2s" % element.strip()
  ag = atom.parent() # atom group
  rg = ag.parent()
  na =  ag.atoms().size()
  assert na==2 or na==1
  j_seq = i_seq+1
  if na==2:
    j_seq = j_seq +1
  h.set_serial("") # 0) # j_seq+1)
  # h.i_seq = j_seq
  ag.append_atom(atom=h)
  appat = ag.atoms()[-1]
  scatterer = cctbx.xray.scatterer(
    label           = h.name,
    scattering_type = h.element.strip(),
    site            = site_frac,
    u               = uiso,
    occupancy       = h.occ)
  xs.add_scatterer(
    scatterer = scatterer,
    insert_at_index = j_seq)

def distances_to_peaks(xray_structure, sites_frac, peak_heights,
    distance_cutoff, use_selection=None):
  asu_mappings = xray_structure.asu_mappings(buffer_thickness =
    distance_cutoff)
  asu_mappings.process_sites_frac(sites_frac, min_distance_sym_equiv =
    xray_structure.min_distance_sym_equiv())
  pair_generator = cctbx.crystal.neighbors_fast_pair_generator(asu_mappings =
    asu_mappings, distance_cutoff = distance_cutoff)
  n_xray = xray_structure.scatterers().size()
  result = {}
  for pair in pair_generator:
    if(pair.i_seq < n_xray):
      if (pair.j_seq < n_xray): continue
      # i_seq = molecule
      # j_seq = site
      rt_mx_i = asu_mappings.get_rt_mx_i(pair)
      rt_mx_j = asu_mappings.get_rt_mx_j(pair)
      rt_mx_ji = rt_mx_i.inverse().multiply(rt_mx_j)
      i_seq_new_site_frac = pair.j_seq - n_xray
      new_site_frac = rt_mx_ji * sites_frac[i_seq_new_site_frac]
      jn = pair.i_seq
    else:
      if(pair.j_seq >= n_xray): continue
      # i_seq = site
      # j_seq = molecule
      rt_mx_i = asu_mappings.get_rt_mx_i(pair)
      rt_mx_j = asu_mappings.get_rt_mx_j(pair)
      rt_mx_ij = rt_mx_j.inverse().multiply(rt_mx_i)
      i_seq_new_site_frac = pair.i_seq - n_xray
      new_site_frac = rt_mx_ij * sites_frac[i_seq_new_site_frac]
      jn = pair.j_seq
    if use_selection is not None:
      height = peak_heights[i_seq_new_site_frac]
      if(use_selection[jn]):
        if result.has_key(jn):
          result[jn].extend( [(height, new_site_frac)] )
        else:
          result[jn] = [(height, new_site_frac)]
  return result

def choose_h_for_water(unit_cell, o_site, xyz_h, h1_site=None, min_dod_angle=80,
    max_dod_angle=170):
  hh1_site = h1_site
  if hh1_site is None:
    mx = max(xyz_h)
    xyz_h.remove(mx)
    hh1_site = mx[1]
  h_max = -1.e300
  h2_site = None
  d1 = unit_cell.distance(o_site, hh1_site)
  assert d1 > 0.5 and d1 < 1.5, "D-O distance is out of range: %f"%d1
  for h,s in xyz_h:
    d = unit_cell.distance(o_site, s)
    if d<0.5:
      continue
    a = unit_cell.angle(s, o_site, hh1_site)
    if a>min_dod_angle and a<max_dod_angle :
      if h>h_max:
        h_max = h
        h2_site = s
  result = []
  if h1_site is None:
    result = [hh1_site]
  if not h2_site is None :
    result.extend( [h2_site] )
  return result

def len_peaks(set_of_peaks):
  r = 0
  for peaks in set_of_peaks.values():
    r += len(peaks)
  return r

def print_scats(xray_structure, fn):
  import cctbx
  ftmp = file(fn, "w")
  print>>ftmp, " scats "
  itmp=0
  for scat in xray_structure.scatterers():
    itmp=itmp+1
    print>>ftmp, itmp, ' ', scat.label.strip(), \
      ' ', scat.scattering_type.strip(), ' ', \
      xray_structure.unit_cell().orthogonalize(scat.site), \
      ' ', scat.occupancy, ' ', cctbx.adptbx.u_as_b(scat.u_iso)
  ftmp.close()

def print_atom(out,atom):
  print>>out, '     ', atom.format_atom_record()
  print>>out, "        atom.xyz:  ", atom.xyz
  print>>out, "        atom.occ:  ", atom.occ
  print>>out, "        atom.b:    ", atom.b
  print>>out, '        atom.segid: "%s"' % atom.segid
  print>>out, "        atom.i_seq: ", atom.i_seq
  print>>out, "        atom.name: ", atom.name
  print>>out, "        atom.element: ", atom.element.strip()

def print_scat(out, s):
  print>>out, "scatterer  label : ", s.label.strip()
  print>>out, "            site : ", s.site
  print>>out, "         element : ", s.scattering_type.strip()
  print>>out, "            biso : ", cctbx.adptbx.u_as_b(s.u_iso)
  print>>out, "             occ : ", s.occupancy

def atom_scat(atom,scat):
  import StringIO
  s=StringIO.StringIO()
  print_atom(s,atom)
  print_scat(s,scat)
  # print>>s, "dir(s):\n",dir(scat)
  return s.getvalue()

def compare_hierarchy(hierarchy, scatterers, cell):
  from libtbx.test_utils import approx_equal
  # Primary "view" of hierarchy:
  #   model, chain, residue_group, atom_group, atom"""
  n = hierarchy.atoms_size()
  n2 = scatterers.size()
  assert n == n2, " size mismatch %d != %d"%(n,n2)
  match = flex.bool()
  match.resize(n, False)
  assert match.size() == n
  if n>0:
    assert match[0] == False
    assert match[n-1] == False
  for model in hierarchy.models():
    # print 'model: "%s"' % model.id
    for chain in model.chains():
      # print 'chain: "%s"' % chain.id
      for residue_group in chain.residue_groups():
        #print '  residue_group: resseq="%s" icode="%s"' % (
        #  residue_group.resseq, residue_group.icode)
        for atom_group in residue_group.atom_groups():
          #print '    atom_group: altloc="%s" resname="%s"' % (
          #  atom_group.altloc, atom_group.resname)
          for atom in atom_group.atoms():
            # print_atom(atom)
            assert atom.i_seq < n
            assert match[atom.i_seq] == False
            s = scatterers[atom.i_seq]
            # assert (atom.serial_as_int() == atom.i_seq + 1), atom_scat(atom,s)
            match[atom.i_seq] = True
            assert atom.element.strip().upper() == \
                s.scattering_type.strip().upper(), atom_scat(atom,s)
            assert len(atom.name.strip())>0, atom_scat(atom,s)
            # assert len(s.label.strip())>0, atom_scat(atom,s)
            # assert approx_equal(atom.occ, s.occupancy, 0.01), atom_scat(atom,s)
            assert approx_equal(cell.orthogonalize(s.site), atom.xyz, 0.001), \
                atom_scat(atom,s)
            #assert approx_equal(atom.b, cctbx.adptbx.u_as_b(s.u_iso), 2.01), \
            #    atom_scat(atom,s)
  #
  assert match.all_eq(True)
  if n>0:
    assert match[0] == True
    assert match[n-1] == True

def build_water_hydrogens_from_map(model, fmodel, params=None, log=None):
  self = model
  xs = self.xray_structure
  unit_cell = xs.unit_cell()
  scatterers = xs.scatterers()
  hier = model.pdb_hierarchy()
  compare_hierarchy(hier, scatterers, unit_cell)
  if log is None:
    log = model.log
  if params is None:
    params = all_master_params().extract()
  max_od_dist = params.max_od_dist
  min_od_dist = params.min_od_dist
  assert min_od_dist >0.5
  assert max_od_dist >min_od_dist and max_od_dist<1.5
  keep_max = params.map_next_to_model.max_model_peak_dist
  keep_min = params.map_next_to_model.min_model_peak_dist
  params.map_next_to_model.max_model_peak_dist = max_od_dist * 1.8
  params.map_next_to_model.min_model_peak_dist = min_od_dist
  params.peak_search.min_cross_distance = params.min_od_dist # 0.5
  params.map_next_to_model.use_hydrogens = True
  params.map_next_to_model.min_peak_peak_dist = min_od_dist #0.8
  max_dod_angle = params.max_dod_angle
  min_dod_angle = params.min_dod_angle
  assert max_dod_angle<180 and min_dod_angle>30 and max_dod_angle>min_dod_angle
  peaks = find_hydrogen_peaks(
    fmodel = fmodel,
    pdb_atoms = model.pdb_atoms,
    params = params,
    log = log)
  if peaks is None:
    return model
  params.map_next_to_model.use_hydrogens = False
  hs = peaks.heights
  params.map_next_to_model.max_model_peak_dist = keep_max
  params.map_next_to_model.min_model_peak_dist = keep_min
  sol_O = model.solvent_selection().set_selected(
    model.xray_structure.hd_selection(), False)
  print >>log, "Number of solvent molecules: ", sol_O.count(True)
  sol_sel = model.solvent_selection()
  hd_sel = sol_sel & model.xray_structure.hd_selection()
  print>>log, "Number of water hydrogens: ", hd_sel.count(True)
  pks = distances_to_peaks(xs, peaks.sites, hs, max_od_dist, use_selection=sol_O)
  pkss = distances_to_peaks(xs, peaks.sites, hs, max_od_dist*1.7, use_selection=sol_O)
  print>>log, "Peaks to consider: ", len(pks.keys()), " : ", len(pkss.keys())
  water_rgs = self.extract_water_residue_groups()
  water_rgs.reverse()
  element='D'
  next_to_i_seqs = []
  for rg in water_rgs:
    if (rg.atom_groups_size() != 1):
      raise RuntimeError(
        "Not implemented: cannot handle water with alt. conf.")
    ag = rg.only_atom_group()
    atoms = ag.atoms()
    h1=0
    h1_atom=None
    h1_site=None
    h1_i_seq=None
    if atoms.size()==2:
      o_atom = None
      h_atom = None
      for atom in atoms:
        if (atom.element.strip() == "O"): o_atom = atom
        else:                             h_atom = atom
      assert [o_atom, h_atom].count(None) == 0
      h1_i_seq = h_atom.i_seq
      h1_site=scatterers[h1_i_seq].site
      h1_atom=h_atom
      if h_atom.name.strip().endswith('1'):
        h1=1
      elif h_atom.name.strip().endswith('2'):
        h1=2
    elif atoms.size()==1:
      o_atom = atoms[0]
      h1_site = None
    elif atoms.size()==3:
      continue
    else:
      assert False
    o_i = o_atom.i_seq
    if pks.has_key(o_i) :
      o_site = scatterers[o_i].site
      o_u = scatterers[o_i].u_iso_or_equiv(unit_cell)
      h_sites = pks[o_i]
      hh = choose_h_for_water(unit_cell, o_site, h_sites, h1_site=h1_site,
          min_dod_angle=min_dod_angle, max_dod_angle=max_dod_angle)
      nats = atoms.size() + len(hh)
      if nats==2:
        if len(hh)==0:
          h_swap = h1_site
        else:
          h_swap = hh[0]
        assert pkss.has_key(o_i)
        h_sitess = pkss[o_i]
        hhs = choose_h_for_water(unit_cell, h_swap, h_sitess, h1_site=o_site,
            min_dod_angle=min_dod_angle, max_dod_angle=max_dod_angle)
        if len(hhs)>0:
          assert len(hhs)==1
          scatterers[o_i].site = h_swap
          o_atom.xyz = unit_cell.orthogonalize(h_swap)
          if h1_site is not None:
            scatterers[h1_i_seq].site = o_site
            h1_atom.xyz = unit_cell.orthogonalize(o_site)
          else:
            hhs.append(o_site)
            assert len(hhs)==2
          hh = hhs
          assert (atoms.size() + len(hh)) == 3
      for i,site_frac in enumerate(hh):
        assert (h1>0 and i<1) or (h1==0 and i<2)
        if h1==1: j=2
        elif h1==2: j=1
        else: j=i+1
        name = element+str(j)
        i_seq = o_atom.i_seq
        # this breaks atom sequence: o_atom.i_seq
        insert_atom_into_model(xs, atom=o_atom, atom_name=name, site_frac=site_frac,
          occupancy=1, uiso=o_u, element=element)
        next_to_i_seqs.append(i_seq)
  if( model.refinement_flags is not None and len(next_to_i_seqs)!=0):
    # TODO: adp_group=True according to params.dod_and_od_group_adp
    model.refinement_flags.add(
      next_to_i_seqs=next_to_i_seqs, # [i_seq], # ,
      sites_individual = True,
      s_occupancies    = False,
      adp_individual_iso=True)
  print >> log, "Number of H added:", len(next_to_i_seqs)
  model.reprocess_pdb_hierarchy_inefficient()
  compare_hierarchy(model.pdb_hierarchy(), model.xray_structure.scatterers(), unit_cell)
  sol_sel = model.solvent_selection()
  hd_sel = sol_sel & model.xray_structure.hd_selection()
  assert hd_sel.count(True) >= len(next_to_i_seqs)
  return model

def select_one_water(water_residue_group, n_atoms):
  rg = water_residue_group
  if (rg.atom_groups_size() != 1):
    raise RuntimeError(
      "Not implemented: cannot handle water with alt. conf.")
  ag = rg.only_atom_group()
  atoms = ag.atoms()
  ws = []
  for atom in atoms:
    i = atom.i_seq
    ws.append(i)
  result = flex.bool()
  for j in xrange(0,n_atoms):
    if j in ws:
      result.append(True)
    else:
      result.append(False)
  nw = result.count(True)
  assert nw>0 and nw <= 3
  return result

def get_pdb_oxygen(water_residue_group):
  rg = water_residue_group
  if (rg.atom_groups_size() != 1):
    raise RuntimeError(
      "Not implemented: cannot handle water with alt. conf.")
  ag = rg.only_atom_group()
  atoms = ag.atoms()
  for atom in atoms:
    if atom.element.strip() == 'O':
      return atom
  assert False

def one_water_correlation(model, fmodels, water):
  import mmtbx.solvent.ordered_solvent as ordered_solvent
  from mmtbx import real_space_correlation
  params = ordered_solvent.master_params().extract()
  par = params.secondary_map_and_map_cc_filter
  rcparams = real_space_correlation.master_params().extract()
  rcparams.detail = "residue"
  if fmodels.fmodel_n is not None:
    fmodel = fmodels.fmodel_neutron()
  else:
    fmodel = fmodels.fmodel_xray()
  title = "xray"
  if fmodel.xray_structure.guess_scattering_type_neutron():
    title="neutron"
  scatterers = model.xray_structure.scatterers()
  assert scatterers is fmodel.xray_structure.scatterers()
  results = real_space_correlation.map_statistics_for_atom_selection(
    atom_selection = water,
    fmodel = fmodel,
    map1_type="Fo",
    map2_type="Fmodel"
  )
  return results.cc

def scatterers_info(scatterers, selection):
  r = str()
  for s,u in zip(scatterers,selection):
    if u:
      r += s.element_symbol().strip()
      r += " : "
      r += ("%4.2f %6.3f"%(s.occupancy,s.u_iso))
      r += " = "
      r += s.label
      r += ";   "
  return r

def water_map_correlations(model, fmodels, log=None):
  print_statistics.make_header("Water real space correlations", out=log)
  fmodels.update_xray_structure(xray_structure = model.xray_structure,
    update_f_calc=True, update_f_mask=True)
  fmodels.show_short()
  scatterers = model.xray_structure.scatterers()
  waters = model.solvent_selection()
  water_rgs = model.extract_water_residue_groups()
  n_atoms = len(scatterers)
  for rg in water_rgs:
    o_atom = get_pdb_oxygen(rg)
    o_scat = scatterers[o_atom.i_seq]
    water = select_one_water(rg, n_atoms)
    if water.count(True) < 2:
      continue
    for s,u in zip(scatterers,water):
      if u:
        e = s.element_symbol().strip()
        if e=='D':
          if s.occupancy <= 0.02 or s.occupancy >=0.98:
            keep_occ = s.occupancy
            neutron_cc = one_water_correlation(model, fmodels, water)
            if s.occupancy <= 0.02:
              s.occupancy = 1.0
              s.u_iso = o_scat.u_iso
            else:
              s.occupancy = 0.0
            fmodels.update_xray_structure(xray_structure = model.xray_structure,
              update_f_calc=True, update_f_mask=True)
            ncc = one_water_correlation(model, fmodels, water)
            if ncc < neutron_cc:
              s.occupancy = keep_occ
              fmodels.update_xray_structure(xray_structure = model.xray_structure,
                update_f_calc=True, update_f_mask=True)
            else:
              neutron_cc = ncc
  return True

def run_flip_hd(fmodel, model, log, params = None):
  if(params is None):
    params = all_master_params().extract()
  params.map_next_to_model.min_model_peak_dist = 0 # XXX
  print_statistics.make_sub_header("find peak-candidates", out = log)
  xray_structure_dc = fmodel.xray_structure.deep_copy_scatterers()
  xh_connectivity_table = model.xh_connectivity_table()
  scatterers = fmodel.xray_structure.scatterers()
  scattering_types = scatterers.extract_scattering_types()
  fmodel_dc = fmodel.deep_copy()
  ed_values = flex.double()
  for h_in_residue in model.refinement_flags.group_h:
    xray_structure_dc_dc = xray_structure_dc.deep_copy_scatterers()
    xray_structure_dc_dc.set_occupancies(value = 0, selection = h_in_residue)
    fmodel_dc.update_xray_structure(
      xray_structure = xray_structure_dc_dc,
      update_f_calc  = True,
      update_f_mask  = True)
    fft_map = fmodel_dc.electron_density_map(
      map_type          = "mFo-DFc",
      resolution_factor = 1/4.,
      symmetry_flags    = maptbx.use_space_group_symmetry)
    fft_map.apply_sigma_scaling()
    fft_map_data = fft_map.real_map_unpadded()
    for i_seq_h in h_in_residue:
      ed_val = maptbx.eight_point_interpolation(fft_map_data,
          scatterers[i_seq_h].site)
      ed_values.append(ed_val)
      assert fmodel_dc.xray_structure.scatterers()[i_seq_h].occupancy == 0
      if 1:#((ed_val < 0 and scattering_types[i_seq_h]=='D') or
         #(ed_val > 0 and scattering_types[i_seq_h]=='H')):
        #print >> log, "%3d %6.2f %s" % (i_seq_h, ed_val, scattering_types[i_seq_h]), \
        #  model.pdb_atoms[i_seq_h].quote()
        pass
  #
  #hd_selection = model.xray_structure.hd_selection()
  scattering_types = model.xray_structure.scatterers().extract_scattering_types()
  hd_selection = flex.bool()
  for sct in scattering_types:
    if(sct.strip() in ['H','D']): hd_selection.append(True)
    else: hd_selection.append(False)

  total = int(flex.sum(model.xray_structure.scatterers().
    extract_occupancies().select(hd_selection)))
  ed_values_abs = flex.abs(ed_values)
  for sigma in (1,2,3):
    ns = (ed_values_abs > sigma).count(True)
    print "sigma = %6.2f n_visible = %5d out of total %-5d" % (sigma, ns, total),ed_values.size()
  #

      #if(abs(ed_val) < 1.0):
      #  print >> log, "*** %3d %6.2f %s" % (i_seq_h, ed_val, scattering_types[i_seq_h]), \
      #  model.pdb_atoms[i_seq_h].quote()
      #  for map_cutoff in [3, -3]:
      #    params.map_cutoff = map_cutoff
      #    peaks = find_hydrogen_peaks(
      #      fmodel               = fmodel,
      #      pdb_atoms = model.pdb_atoms,
      #      params               = params,
      #      log                  = log)
