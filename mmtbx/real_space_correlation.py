from __future__ import division
from cctbx.array_family import flex
import mmtbx.utils
from iotbx import reflection_file_reader
from iotbx import reflection_file_utils
from cStringIO import StringIO
from cctbx import maptbx
import iotbx.phil
from libtbx.utils import Sorry, null_out
import os
from cctbx import miller
from libtbx import group_args
import sys
import iotbx.pdb

core_params_str = """\
atom_radius = None
  .type = float
  .help = Atomic radius for map CC calculation. Determined automatically if \
          if None is given
  .expert_level = 2
hydrogen_atom_radius = None
  .type = float
  .help = Atomic radius for map CC calculation for H or D.
  .expert_level = 2
resolution_factor = 1./4
  .type = float
use_hydrogens = None
  .type = bool
"""

master_params_str = """\
%s
scattering_table = *n_gaussian wk1995 it1992 neutron
  .type = choice
  .help = Scattering table for structure factors calculations
detail = atom residue *automatic
  .type = choice(multi=False)
  .help = Level of details to show CC for
map_1
  .help = First map to use in map CC calculation
{
 type = Fc
   .type = str
   .help = Electron density map type. Example xmFobs-yDFcalc (for \
           maximum-likelihood weighted map) or xFobs-yFcalc (for simple \
           unweighted map), x and y are any real numbers.
 fill_missing_reflections = False
   .type = bool
 isotropize = False
   .type = bool
}
map_2
  .help = Second map to use in map CC calculation
{
 type = 2mFo-DFc
   .type = str
   .help = Electron density map type. Example xmFobs-yDFcalc (for \
           maximum-likelihood weighted map) or xFobs-yFcalc (for simple \
           unweighted map), x and y are any real numbers.
 fill_missing_reflections = True
   .type = bool
 isotropize = True
   .type = bool
}
pdb_file_name = None
  .type = str
  .help = PDB file name.
reflection_file_name = None
  .type = str
  .help = File with experimental data (most of formats: CNS, SHELX, MTZ, etc).
data_labels = None
  .type = str
  .help = Labels for experimental data.
high_resolution = None
  .type=float
low_resolution = None
  .type=float
"""%core_params_str

def master_params():
  return iotbx.phil.parse(master_params_str, process_includes=False)

def pdb_to_xrs(pdb_file_name, scattering_table):
  pdb_inp = iotbx.pdb.input(file_name = pdb_file_name)
  xray_structure = pdb_inp.xray_structure_simple()
  pdb_hierarchy = pdb_inp.construct_hierarchy()
  pdb_hierarchy.atoms().reset_i_seq() # VERY important to do.
  mmtbx.utils.setup_scattering_dictionaries(
    scattering_table = scattering_table,
    xray_structure = xray_structure,
    d_min = None)
  return group_args(
    xray_structure = xray_structure,
    pdb_hierarchy  = pdb_hierarchy)

def extract_data_and_flags(params, crystal_symmetry=None):
  data_and_flags = None
  if(params.reflection_file_name is not None):
    reflection_file = reflection_file_reader.any_reflection_file(
      file_name = params.reflection_file_name)
    reflection_file_server = reflection_file_utils.reflection_file_server(
      crystal_symmetry = crystal_symmetry,
      force_symmetry   = True,
      reflection_files = [reflection_file])
    parameters = mmtbx.utils.data_and_flags_master_params().extract()
    parameters.force_anomalous_flag_to_be_equal_to = False
    if(params.data_labels is not None):
      parameters.labels = [params.data_labels]
    if(params.high_resolution is not None):
      parameters.high_resolution = params.high_resolution
    if(params.low_resolution is not None):
      parameters.low_resolution = params.low_resolution
    data_and_flags = mmtbx.utils.determine_data_and_flags(
      reflection_file_server = reflection_file_server,
      parameters             = parameters,
      data_description       = "X-ray data",
      extract_r_free_flags   = False, # XXX
      log                    = StringIO())
  return data_and_flags

def compute_map_from_model(high_resolution, low_resolution, xray_structure,
                           grid_resolution_factor, crystal_gridding = None):
  f_calc = xray_structure.structure_factors(d_min = high_resolution).f_calc()
  f_calc = f_calc.resolution_filter(d_max = low_resolution)
  if(crystal_gridding is None):
    return f_calc.fft_map(
      resolution_factor = min(0.5,grid_resolution_factor),
      symmetry_flags    = None)
  return miller.fft_map(
    crystal_gridding     = crystal_gridding,
    fourier_coefficients = f_calc)

def extract_input_pdb(pdb_file, params):
  fn1, fn2 = None,None
  if(pdb_file is not None and iotbx.pdb.is_pdb_file(pdb_file.file_name)):
    fn1 = pdb_file.file_name
  if(params.pdb_file_name is not None and iotbx.pdb.is_pdb_file(params.pdb_file_name)):
    fn2 = params.pdb_file_name
  if([fn1, fn2].count(None)!=1):
    raise Sorry("PDB file must be provided.")
  result = None
  if(fn1 is not None): result = fn1
  else: result = fn2
  params.pdb_file_name = result

def extract_input_data(hkl_file, params):
  fn1, fn2 = None,None
  if(hkl_file is not None and os.path.isfile(hkl_file.file_name)):
    fn1 = hkl_file.file_name
  if(params.reflection_file_name is not None and
     os.path.isfile(params.reflection_file_name)):
    fn2 = params.reflection_file_name
  if([fn1, fn2].count(None)!=1):
    raise Sorry("Reflection file must be provided.")
  result = None
  if(fn1 is not None): result = fn1
  else: result = fn2
  params.reflection_file_name = result

def broadcast(m, log):
  print >> log, "-"*79
  print >> log, m
  print >> log, "*"*len(m)

def cmd_run(args, command_name, log=None):
  if(log is None): log = sys.stdout
  args = list(args)
  msg = """\

Compute map correlation coefficient given input PDB model and reflection data.

Examples:

  phenix.real_space_correlation m.pdb d.mtz
  phenix.real_space_correlation m.pdb d.mtz detail=atom
  phenix.real_space_correlation m.pdb d.mtz detail=residue
  phenix.real_space_correlation m.pdb d.mtz data_labels=FOBS
  phenix.real_space_correlation m.pdb d.mtz scattering_table=neutron
  phenix.real_space_correlation m.pdb d.mtz detail=atom use_hydrogens=true
  phenix.real_space_correlation m.pdb d.mtz map_1.type=Fc map_2.type="2mFo-DFc"
"""
  if(len(args) == 0) or (args == ["--help"]) or (args == ["--options"]):
    print >> log, msg
    broadcast(m="Default parameres:", log = log)
    master_params().show(out = log, prefix="  ")
    return
  else :
    from iotbx.file_reader import any_file
    pdb_file = None
    reflection_file = None
    phil_objects = []
    for arg in args :
      if(os.path.isfile(arg)) :
        inp = any_file(arg)
        if(  inp.file_type == "phil"): phil_objects.append(inp.file_object)
        elif(inp.file_type == "pdb"):  pdb_file = inp
        elif(inp.file_type == "hkl"):  reflection_file = inp
        else:
          raise Sorry(("Don't know how to deal with the file %s - unrecognized "+
            "format '%s'.  Please verify that the syntax is correct.") % (arg,
              str(inp.file_type)))
      else:
        try:
          phil_objects.append(iotbx.phil.parse(arg))
        except RuntimeError, e:
          raise Sorry("Unrecognized parameter or command-line argument '%s'." %
            arg)
    working_phil, unused = master_params().fetch(sources=phil_objects,
      track_unused_definitions=True)
    if(len(unused)>0):
      for u in unused:
        print str(u)
      raise Sorry("Unused parameters: see above.")
    params = working_phil.extract()
    # PDB file
    extract_input_pdb(pdb_file=pdb_file, params=params)
    broadcast(m="Input PDB file name: %s"%params.pdb_file_name, log=log)
    pdbo = pdb_to_xrs(pdb_file_name=params.pdb_file_name,
      scattering_table=params.scattering_table)
    pdbo.xray_structure.show_summary(f=log, prefix="  ")
    # data file
    extract_input_data(hkl_file=reflection_file, params=params)
    broadcast(
      m="Input reflection file name: %s"%params.reflection_file_name, log=log)
    data_and_flags = extract_data_and_flags(params = params)
    data_and_flags.f_obs.show_comprehensive_summary(f=log, prefix="  ")
    # create fmodel
    r_free_flags = data_and_flags.f_obs.array(
      data = flex.bool(data_and_flags.f_obs.size(), False))
    fmodel = mmtbx.utils.fmodel_simple(
      xray_structures     = [pdbo.xray_structure],
      scattering_table    = params.scattering_table,
      f_obs               = data_and_flags.f_obs,
      r_free_flags        = r_free_flags)
    broadcast(m="R-factors, reflection counts and scales", log=log)
    fmodel.show(log=log, show_header=False)
    # compute map coefficients
    e_map_obj = fmodel.electron_density_map()
    coeffs_1 = e_map_obj.map_coefficients(
      map_type     = params.map_1.type,
      fill_missing = params.map_1.fill_missing_reflections,
      isotropize   = params.map_1.isotropize)
    coeffs_2 = e_map_obj.map_coefficients(
      map_type     = params.map_2.type,
      fill_missing = params.map_2.fill_missing_reflections,
      isotropize   = params.map_2.isotropize)
    # compute cc
    results = simple(
      fmodel        = fmodel,
      pdb_hierarchy = pdbo.pdb_hierarchy,
      params        = params,
      show_results  = True,
      log           = log)

def simple(fmodel, pdb_hierarchy, params=None, log=None, show_results=False):
  if(params is None): params =master_params().extract()
  if(log is None): log = sys.stdout
  # compute map coefficients
  e_map_obj = fmodel.electron_density_map()
  coeffs_1 = e_map_obj.map_coefficients(
    map_type     = params.map_1.type,
    fill_missing = params.map_1.fill_missing_reflections,
    isotropize   = params.map_1.isotropize)
  coeffs_2 = e_map_obj.map_coefficients(
    map_type     = params.map_2.type,
    fill_missing = params.map_2.fill_missing_reflections,
    isotropize   = params.map_2.isotropize)
  # compute maps
  fft_map_1 = coeffs_1.fft_map(resolution_factor = params.resolution_factor)
  fft_map_1.apply_sigma_scaling()
  map_1 = fft_map_1.real_map_unpadded()
  fft_map_2 = miller.fft_map(
    crystal_gridding     = fft_map_1,
    fourier_coefficients = coeffs_2)
  fft_map_2.apply_sigma_scaling()
  map_2 = fft_map_2.real_map_unpadded()
  # compute cc
  broadcast(m="Map correlation and map values", log=log)
  overall_cc = flex.linear_correlation(x = map_1.as_1d(),
    y = map_2.as_1d()).coefficient()
  print >> log, "  Overall map cc(%s,%s): %6.4f"%(params.map_1.type,
    params.map_2.type, overall_cc)
  detail, atom_radius = params.detail, params.atom_radius
  detail, atom_radius = set_detail_level_and_radius(detail=detail,
    atom_radius=atom_radius, d_min=fmodel.f_obs().d_min())
  use_hydrogens = params.use_hydrogens
  if(use_hydrogens is None):
    if(params.scattering_table == "neutron" or fmodel.f_obs().d_min() <= 1.2):
      use_hydrogens = True
    else:
      use_hydrogens = False
  hydrogen_atom_radius = params.hydrogen_atom_radius
  if(hydrogen_atom_radius is None):
    if(params.scattering_table == "neutron"):
      hydrogen_atom_radius = atom_radius
    else:
      hydrogen_atom_radius = 1
  results = compute(
    pdb_hierarchy        = pdb_hierarchy,
    unit_cell            = fmodel.xray_structure.unit_cell(),
    fft_n_real           = map_1.focus(),
    fft_m_real           = map_1.all(),
    map_1                = map_1,
    map_2                = map_2,
    detail               = detail,
    atom_radius          = atom_radius,
    use_hydrogens        = use_hydrogens,
    hydrogen_atom_radius = hydrogen_atom_radius)
  if(show_results):
    show(log=log, results=results, params=params, detail=detail)
  return results

def show(log, results, params, detail):
  print >> log
  print >> log, "Rho1 = %s, Rho2 = %s"%(params.map_1.type,
    params.map_2.type)
  print >> log
  if(detail == "atom"):
    print >> log, " <---id string--->  occ     ADP      CC   Rho1   Rho2"
  else:
    print >> log, " <id string>   occ     ADP      CC   Rho1   Rho2"
  fmt = "%s %4.2f %7.2f %7.4f %6.2f %6.2f"
  for r in results:
    print >> log, fmt%(r.id_str, r.occupancy, r.b, r.cc, r.map_value_1,
      r.map_value_2)

def compute(pdb_hierarchy,
            unit_cell,
            fft_n_real,
            fft_m_real,
            map_1,
            map_2,
            detail,
            atom_radius,
            use_hydrogens,
            hydrogen_atom_radius):
  assert detail in ["atom", "residue"]
  results = []
  for chain in pdb_hierarchy.chains():
    for residue_group in chain.residue_groups():
      for conformer in residue_group.conformers():
        for residue in conformer.residues():
          r_id_str = "%2s %1s %3s %4s"%(chain.id, conformer.altloc,
            residue.resname, residue.resseq)
          r_sites_cart = flex.vec3_double()
          r_b          = flex.double()
          r_occ        = flex.double()
          r_mv1        = flex.double()
          r_mv2        = flex.double()
          r_rad        = flex.double()
          for atom in residue.atoms():
            a_id_str = "%s %4s"%(r_id_str, atom.name)
            if(atom.element_is_hydrogen()): rad = hydrogen_atom_radius
            else: rad = atom_radius
            if(not (atom.element_is_hydrogen() and not use_hydrogens)):
              map_value_1 = map_1.eight_point_interpolation(
                unit_cell.fractionalize(atom.xyz))
              map_value_2 = map_2.eight_point_interpolation(
                unit_cell.fractionalize(atom.xyz))
              r_sites_cart.append(atom.xyz)
              r_b         .append(atom.b)
              r_occ       .append(atom.occ)
              r_mv1       .append(map_value_1)
              r_mv2       .append(map_value_2)
              r_rad       .append(rad)
              if(detail == "atom"):
                sel = maptbx.grid_indices_around_sites(
                  unit_cell  = unit_cell,
                  fft_n_real = fft_n_real,
                  fft_m_real = fft_m_real,
                  sites_cart = flex.vec3_double([atom.xyz]),
                  site_radii = flex.double([rad]))
                cc = flex.linear_correlation(x=map_1.select(sel),
                  y=map_2.select(sel)).coefficient()
                result = group_args(
                  chain_id    = chain.id,
                  atom        = atom,
                  id_str      = a_id_str,
                  cc          = cc,
                  map_value_1 = map_value_1,
                  map_value_2 = map_value_2,
                  b           = atom.b,
                  occupancy   = atom.occ,
                  n_atoms     = 1)
                results.append(result)
          if(detail == "residue"):
            sel = maptbx.grid_indices_around_sites(
              unit_cell  = unit_cell,
              fft_n_real = fft_n_real,
              fft_m_real = fft_m_real,
              sites_cart = r_sites_cart,
              site_radii = r_rad)
            cc = flex.linear_correlation(x=map_1.select(sel),
              y=map_2.select(sel)).coefficient()
            result = group_args(
              residue     = residue,
              chain_id    = chain.id,
              id_str      = r_id_str,
              cc          = cc,
              map_value_1 = flex.mean(r_mv1),
              map_value_2 = flex.mean(r_mv2),
              b           = flex.mean(r_b),
              occupancy   = flex.mean(r_occ),
              n_atoms     = r_sites_cart.size())
            results.append(result)
  return results

def set_detail_level_and_radius(detail, atom_radius, d_min):
  assert detail in ["atom","residue","automatic"]
  if(detail == "automatic"):
    if(d_min < 2.0): detail = "atom"
    else:            detail = "residue"
  if(atom_radius is None):
    if(d_min < 1.0):                    atom_radius = 1.0
    elif(d_min >= 1.0 and d_min<2.0):   atom_radius = 1.5
    elif(d_min >= 2.0 and d_min < 4.0): atom_radius = 2.0
    else:                               atom_radius = 2.5
  return detail, atom_radius

def map_statistics_for_atom_selection (
    atom_selection,
    fmodel=None,
    resolution_factor=0.25,
    map1=None,
    map2=None,
    xray_structure=None,
    map1_type="2mFo-DFc",
    map2_type="Fmodel",
    atom_radius=1.5,
    exclude_hydrogens=False) :
  """
  Simple-but-flexible function to give the model-to-map CC and mean density
  values (sigma-scaled, unless pre-calculated maps are provided) for any
  arbitrary atom selection.
  """
  assert (atom_selection is not None) and (len(atom_selection) > 0)
  if (fmodel is not None) :
    assert (map1 is None) and (map2 is None) and (xray_structure is None)
    map1_coeffs = fmodel.electron_density_map().map_coefficients(map1_type)
    map1 = map1_coeffs.fft_map(
      resolution_factor=resolution_factor).apply_sigma_scaling().real_map()
    map2_coeffs = fmodel.electron_density_map().map_coefficients(map2_type)
    map2 = map2_coeffs.fft_map(
      resolution_factor=resolution_factor).apply_sigma_scaling().real_map()
    xray_structure = fmodel.xray_structure
  else :
    assert (not None in [map1, map2, xray_structure])
    assert isinstance(map1, flex.double) and isinstance(map2, flex.double)
  if (exclude_hydrogens) :
    hd_selection = xray_structure.hd_selection()
    if (type(atom_selection).__name__ == "size_t") :
      atom_selection_new = flex.size_t()
      for i_seq in atom_selection :
        if (not hd_selection[i_seq]) :
          atom_selection_new.append(i_seq)
      atom_selection = atom_selection_new
      assert (len(atom_selection) > 0)
    else :
      assert (type(atom_selection).__name__ == "bool")
      atom_selection &= ~hd_selection
  sites = xray_structure.sites_cart().select(atom_selection)
  sites_frac = xray_structure.sites_fract().select(atom_selection)
  scatterers = xray_structure.scatterers().select(atom_selection)
  atom_radii = flex.double(sites.size(), atom_radius)
  for i_seq, sc in enumerate(scatterers):
    if (sc.element_symbol().strip().lower() in ["h","d"]):
      atom_radii[i_seq] = 1.0
  sel = maptbx.grid_indices_around_sites(
    unit_cell  = xray_structure.unit_cell(),
    fft_n_real = map1.focus(),
    fft_m_real = map1.all(),
    sites_cart = sites,
    site_radii = atom_radii)
  map1_sel = map1.select(sel)
  map2_sel = map2.select(sel)
  values_1 = flex.double()
  values_2 = flex.double()
  for site_frac in sites_frac:
    values_1.append(map1.eight_point_interpolation(site_frac))
    values_2.append(map2.eight_point_interpolation(site_frac))
  cc = flex.linear_correlation(x=map1_sel, y=map2_sel).coefficient()
  return group_args(
    cc=cc,
    map1_mean=flex.mean(values_1),
    map2_mean=flex.mean(values_2))

def map_statistics_for_fragment (fragment, **kwds) :
  """
  Shortcut to map_statistics_for_atom_selection using a PDB hierarchy object
  to define the atom selection.
  """
  atoms = fragment.atoms()
  i_seqs = atoms.extract_i_seq()
  assert (not i_seqs.all_eq(0))
  return map_statistics_for_atom_selection(i_seqs, **kwds)

def find_suspicious_residues (
    fmodel,
    pdb_hierarchy,
    hetatms_only=True,
    skip_single_atoms=True,
    skip_alt_confs=True,
    min_acceptable_cc=0.8,
    min_acceptable_2fofc=1.0,
    max_frac_atoms_below_min=0.5,
    ignore_resnames=(),
    log=None) :
  if (log is None) : log = null_out()
  xray_structure = fmodel.xray_structure
  assert (len(pdb_hierarchy.atoms()) == xray_structure.scatterers().size())
  map_coeffs1 = fmodel.electron_density_map().map_coefficients(
    map_type="2mFo-DFc",
    fill_missing=False)
  map1 = map_coeffs1.fft_map(
    resolution_factor=0.25).apply_sigma_scaling().real_map_unpadded()
  map_coeffs2 = fmodel.electron_density_map().map_coefficients(
    map_type="Fc",
    fill_missing=False)
  map2 = map_coeffs2.fft_map(
    resolution_factor=0.25).apply_sigma_scaling().real_map_unpadded()
  unit_cell = xray_structure.unit_cell()
  hd_selection = xray_structure.hd_selection()
  outliers = []
  for chain in pdb_hierarchy.models()[0].chains() :
    for residue_group in chain.residue_groups() :
      atom_groups = residue_group.atom_groups()
      if (len(atom_groups) > 1) and (skip_alt_confs) :
        continue
      for atom_group in residue_group.atom_groups() :
        if (atom_group.resname in ignore_resnames) :
          continue
        atoms = atom_group.atoms()
        assert (len(atoms) > 0)
        if (len(atoms) == 1) and (skip_single_atoms) :
          continue
        if (hetatms_only) :
          if (not atoms[0].hetero) :
            continue
        map_stats = map_statistics_for_fragment(
          fragment=atom_group,
          map1=map1,
          map2=map2,
          xray_structure=fmodel.xray_structure,
          exclude_hydrogens=True)
        n_below_min = n_heavy = sum = 0
        for atom in atoms :
          if (hd_selection[atom.i_seq]) :
            continue
          n_heavy += 1
          site = atom.xyz
          site_frac = unit_cell.fractionalize(site)
          map_value = map1.tricubic_interpolation(site_frac)
          if (map_value < min_acceptable_2fofc) :
            n_below_min += 1
          sum += map_value
        map_mean = sum / n_heavy
        frac_below_min = n_below_min / n_heavy
        if ((map_stats.cc < min_acceptable_cc) or
            (frac_below_min > max_frac_atoms_below_min) or
            (map_mean < min_acceptable_2fofc)) :
          residue_info = "%1s%3s%2s%5s" % (atom_group.altloc,
            atom_group.resname, chain.id, residue_group.resid())
          xyz_mean = atoms.extract_xyz().mean()
          outliers.append((residue_info, xyz_mean))
          print >> log, "Suspicious residue: %s" % residue_info
          print >> log, "  Overall CC to 2mFo-DFc map = %.2f" % map_stats.cc
          print >> log, "  Fraction of atoms where 2mFo-DFc < %.2f = %.2f" % \
            (min_acceptable_2fofc, frac_below_min)
          print >> log, "  Mean 2mFo-DFc value = %.2f" % map_mean
  return outliers
