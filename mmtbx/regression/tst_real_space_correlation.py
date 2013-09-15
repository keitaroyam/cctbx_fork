
from __future__ import division
import libtbx.load_env
from libtbx.test_utils import approx_equal
from libtbx.utils import null_out
from libtbx import group_args
import os

def exercise_1():
  pdb_file = libtbx.env.find_in_repositories(
    relative_path="phenix_regression/pdb/1yjp_h.pdb",
    test=os.path.isfile)
  mtz_file = libtbx.env.find_in_repositories(
    relative_path="phenix_regression/reflection_files/1yjp.mtz",
    test=os.path.isfile)
  if (None in [pdb_file, mtz_file]) :
    print "phenix_regression not found, skipping test"
    return False
  from mmtbx import real_space_correlation
  import mmtbx.utils
  from iotbx import file_reader
  from scitbx.array_family import flex
  pdb_in = file_reader.any_file(pdb_file)
  hierarchy = pdb_in.file_object.construct_hierarchy()
  hierarchy.atoms().reset_i_seq()
  xrs = pdb_in.file_object.xray_structure_simple()
  mtz_in = file_reader.any_file(mtz_file)
  f_obs = mtz_in.file_server.miller_arrays[0]
  r_free = mtz_in.file_server.miller_arrays[1]
  r_free = r_free.customized_copy(data=(r_free.data()==1))
  fmodel = mmtbx.utils.fmodel_simple(
    f_obs=f_obs,
    update_f_part1_for=None,
    r_free_flags=r_free,
    xray_structures=[xrs],
    scattering_table="n_gaussian")
  map_stats = real_space_correlation.map_statistics_for_fragment(
    fragment=hierarchy,
    fmodel=fmodel)
  assert approx_equal(map_stats.cc, 0.965, eps=0.003)
  edm = fmodel.electron_density_map(update_f_part1=False)
  map1_coeffs = edm.map_coefficients("2mFo-DFc")
  map1 = map1_coeffs.fft_map(
    resolution_factor=0.25).apply_sigma_scaling().real_map()
  map2_coeffs = edm.map_coefficients("Fmodel")
  map2 = map2_coeffs.fft_map(
    resolution_factor=0.25).apply_sigma_scaling().real_map()
  xray_structure = fmodel.xray_structure
  map_stats2 = real_space_correlation.map_statistics_for_atom_selection(
    atom_selection=flex.bool(xrs.sites_cart().size(), True),
    map1=map1,
    map2=map2,
    xray_structure=xrs)
  assert approx_equal(map_stats2.cc, map_stats.cc, 0.01)
  # XXX other code outside cctbx depends on the current API - do not simply
  # change the test if this breaks!
  results = real_space_correlation.simple(
    fmodel=fmodel,
    pdb_hierarchy=hierarchy,
    log=null_out())
  assert isinstance(results, list)
  assert isinstance(results[0], group_args)
  assert (results[0].n_atoms == 1)
  assert (results[0].id_str == " A   GLY    1    N  ")
  return True

if (__name__ == "__main__") :
  if (exercise_1()) :
    print "OK"
