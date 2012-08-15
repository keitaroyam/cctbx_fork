from __future__ import division
# LIBTBX_SET_DISPATCHER_NAME phenix.map_box

import mmtbx.utils
from mmtbx.refinement import print_statistics
import iotbx.pdb
from scitbx.array_family import flex
import libtbx.phil
from libtbx.utils import Sorry
import os, sys
from iotbx import reflection_file_reader

master_phil = libtbx.phil.parse("""
  pdb_file = None
    .type = path
  map_coefficients_file = None
    .type = path
  label = None
    .type = str
  selection = all
    .type = str
  selection_radius = 3.0
    .type = float
  box_cushion = 3.0
    .type = float
  resolution_factor = 1./4
    .type = float
  output_format = *xplor *mtz *ccp4
    .type=choice(multi=True)
""")

def match_labels(target, label):
  label = label.lower()
  for s in target:
    s = s.lower()
    if(s.count(label)): return True
  return False

def select_within_no_sym(sites_cart, sites_cart_all, unit_cell, radius):
  small = 0.1
  if(radius < small): radius=small
  sites_frac = unit_cell.fractionalize(sites_cart)
  sites_frac_all = unit_cell.fractionalize(sites_cart_all)
  result = flex.bool(sites_frac_all.size(), False)
  for isfa, sfa in enumerate(sites_frac_all):
    for sfr in sites_frac:
      d = unit_cell.distance(sfa,sfr)
      if(d<radius):
        result[isfa]=True
  return result

def run (args, log=None):
  h = "phenix.map_box: extract box with model and map around selected atoms"
  if(log is None): log = sys.stdout
  print_statistics.make_header(h, out=log)
  default_message="""\

%s.

Usage:
  phenix.map_box model.pdb map_coefficients.mtz selection="chain A and resseq 1:10"

Parameters:"""%h
  if(len(args) == 0):
    print default_message
    master_phil.show(prefix="  ")
    return
  cmdline_phil = []
  got_pdb = False
  got_hkl = False
  for arg in args :
    if(os.path.isfile(arg)):
      if(iotbx.pdb.is_pdb_file(arg)):
        pdb_phil = libtbx.phil.parse("pdb_file=%s" % os.path.abspath(arg))
        cmdline_phil.append(pdb_phil)
        got_pdb = True
      else:
        reflection_file = reflection_file_reader.any_reflection_file(
          file_name=arg, ensure_read_access=False)
        if(reflection_file.file_type() is not None):
          reflection_phil = libtbx.phil.parse(
            "map_coefficients_file=%s" % os.path.abspath(arg))
          cmdline_phil.append(reflection_phil)
          got_hkl = True
    else:
      try: arg_phil = libtbx.phil.parse(arg)
      except Exception: raise Sorry("Bad parameter: %s"%arg)
      cmdline_phil.append(arg_phil)
  if(not got_pdb): raise Sorry("PDB file is needed.")
  if(not got_hkl): raise Sorry("File with map coefficients is needed.")
  #
  print_statistics.make_sub_header("parameters", out=log)
  working_phil = master_phil.fetch(sources=cmdline_phil)
  working_phil.show(out = log)
  params = working_phil.extract()
  if(params.label is None):
    raise Sorry("'label' has to be defined. Example: label=2mFo-DFc")
  if(params.selection is None):
    raise Sorry("'selection' has to be defined. Example: selection='chain A and resseq 1:10' ")
  #
  print_statistics.make_sub_header("pdb model", out=log)
  pdb_inp = iotbx.pdb.input(file_name=params.pdb_file)
  pdb_hierarchy = pdb_inp.construct_hierarchy()
  pdb_atoms = pdb_hierarchy.atoms()
  pdb_atoms.reset_i_seq()
  xray_structure = pdb_inp.xray_structure_simple()
  xray_structure.show_summary(f=log)
  #
  print_statistics.make_sub_header("map coefficients", out=log)
  miller_arrays = reflection_file.as_miller_arrays()
  print >> log, "Labels in input map coefficients file:"
  map_coeff = []
  label_taken = None
  for ma in miller_arrays:
    print >> log, "  ", ma.info().labels
    if(match_labels(target=ma.info().labels, label=params.label)):
      map_coeff.append(ma)
      label_taken = ma.info().labels
  if(len(map_coeff)==0):
    raise Sorry(
      "Could not match 'label=%s' against available labels."%params.label)
  elif(len(map_coeff)>1):
    raise Sorry("Multiple matches of 'label=%s' against available labels."%
      params.label)
  else:
    print >> log, "Label taken:", label_taken
    map_coeff = map_coeff[0]
    if(not isinstance(map_coeff.data(), flex.complex_double)):
      raise Sorry("Map coefficients must be a complex array.")
  #
  print_statistics.make_sub_header("atom selection", out=log)
  print >> log, "Selection string: selection='%s'"%params.selection
  selection = pdb_hierarchy.atom_selection_cache().selection(
    string = params.selection)
  print >> log, "  selects %d atoms from total %d atoms."%(selection.count(True),
    selection.size())
  #
  print_statistics.make_sub_header(
    "extracting box around selected atoms and writing output files", out=log)
  fft_map = map_coeff.fft_map(resolution_factor=params.resolution_factor)
  fft_map.apply_sigma_scaling()
  map_data = fft_map.real_map_unpadded()
  #
  sites_cart_all = xray_structure.sites_cart()
  sites_cart = sites_cart_all.select(selection)
  selection = select_within_no_sym(
    sites_cart     = sites_cart,
    sites_cart_all = sites_cart_all,
    unit_cell      = xray_structure.unit_cell(),
    radius         = params.selection_radius)
  #
  box = mmtbx.utils.extract_box_around_model_and_map(
    xray_structure   = xray_structure,
    pdb_hierarchy    = pdb_hierarchy,
    map_data         = map_data,
    box_cushion      = params.box_cushion,
    selection        = selection)
  output_prefix=os.path.basename(params.pdb_file)[:-4]
  file_name = "%s_box.pdb"%output_prefix
  box.write_pdb_file(file_name=file_name)
  if("ccp4" in params.output_format):
    file_name = "%s_box.ccp4"%output_prefix
    print >> log, "writing map to CCP4 formatted file:   %s"%file_name
    box.write_ccp4_map(file_name=file_name)
  if("xplor" in params.output_format):
    file_name = "%s_box.xplor"%output_prefix
    print >> log, "writing map to X-plor formatted file: %s"%file_name
    box.write_xplor_map(file_name=file_name)
  if("mtz" in params.output_format):
    file_name = "%s_box.mtz"%output_prefix
    print >> log, "writing map coefficients to MTZ file: %s"%file_name
    box.map_coefficients(d_min=map_coeff.d_min(),
      resolution_factor=params.resolution_factor, file_name=file_name)
  print >> log

if (__name__ == "__main__"):
  run(args=sys.argv[1:])
