from libtbx import test_utils
import libtbx.load_env

def run():
  tst_list = (
  "$D/cctbx/regression/tst_adp_aniso_restraints.py",
  "$D/math/boost_python/tst_math.py",
  "$D/xray/boost_python/tst_f_model.py",
  "$D/array_family/boost_python/tst_flex.py",
  "$D/uctbx/boost_python/tst_uctbx.py",
  "$D/sgtbx/boost_python/tst_sgtbx.py",
  "$D/sgtbx/boost_python/tst_N_fold_rot.py",
  "$D/include/cctbx/crystal/tst_ext.py",
  "$D/adptbx/boost_python/tst_adptbx.py",
  "$D/miller/boost_python/tst_miller.py",
  "$D/eltbx/boost_python/tst_chemical_elements.py",
  "$D/eltbx/boost_python/tst_xray_scattering.py",
  "$D/eltbx/boost_python/tst_henke.py",
  "$D/eltbx/boost_python/tst_icsd_radii.py",
  "$D/eltbx/boost_python/tst_neutron.py",
  "$D/eltbx/boost_python/tst_sasaki.py",
  "$D/eltbx/boost_python/tst_tiny_pse.py",
  "$D/eltbx/boost_python/tst_wavelengths.py",
  "$D/xray/boost_python/tst_xray.py",
  "$D/maptbx/boost_python/tst_maptbx.py",
  "$D/dmtbx/boost_python/tst_dmtbx.py",
  "$D/translation_search/boost_python/tst_translation_search.py",
  "$D/include/cctbx/geometry_restraints/tst_ext.py",
  "$D/include/cctbx/adp_restraints/tst_ext.py",
  ["$D/cctbx/regression/tst_krivy_gruber.py", "--Quick"],
  "$D/cctbx/regression/tst_sgtbx.py",
  "$D/cctbx/regression/tst_itvb_2001_table_a1427_hall_symbols.py",
  "$D/cctbx/regression/tst_space_group_type_tidy_cb_op_t.py",
  ["$D/cctbx/regression/tst_sgtbx_denominators.py", "P31"],
  "$D/cctbx/regression/tst_sgtbx_subgroups.py",
  "$D/cctbx/regression/tst_sgtbx_lattice_symmetry.py",
  ["$D/cctbx/regression/tst_adp_constraints.py", "P3"],
  "$D/cctbx/regression/tst_sgtbx_site_constraints.py",
  "$D/cctbx/regression/tst_reflection_statistics.py",
  "$D/cctbx/regression/tst_sgtbx_harker.py",
  "$D/cctbx/regression/tst_twin_target.py",
  "$D/cctbx/sgtbx/symbol_confidence.py",
  "$D/cctbx/sgtbx/bravais_types.py",
  "$D/cctbx/regression/tst_miller_lookup_utils.py",
  ["$D/cctbx/regression/tst_crystal.py", "I41/acd"],
  ["$D/cctbx/regression/tst_direct_space_asu.py", "I41/acd"],
  "$D/cctbx/regression/tst_pair_asu_table.py",
  "$D/cctbx/regression/tst_crystal_asu_clusters.py",
  "$D/cctbx/regression/tst_coordination_sequences.py",
  ["$D/cctbx/regression/tst_crystal_close_packing.py", "R-3mr"],
  ["$D/cctbx/regression/tst_xray.py", "I41/acd"],
  ["$D/cctbx/regression/tst_miller.py", "P31"],
  ["$D/cctbx/regression/tst_reciprocal_space_asu.py", "P312"],
  ["$D/cctbx/regression/tst_triplet_generator.py", "P41"],
  ["$D/cctbx/regression/tst_emma.py", "P31"],
  ["$D/cctbx/regression/tst_find_centre_of_inversion.py", "P31"],
  ["$D/cctbx/regression/tst_expand_to_p1.py", "P31"],
  ["$D/cctbx/regression/tst_change_basis.py", "P31"],
  ["$D/cctbx/regression/tst_wilson_plot.py", "P31"],
  "$D/cctbx/regression/tst_xray_target_functors.py",
  ["$D/cctbx/regression/tst_xray_derivatives.py", "P31"],
  ["$D/cctbx/regression/tst_xray_fast_gradients.py", "P31"],
  ["$D/cctbx/regression/tst_xray_minimization.py", "P31"],
  "$D/cctbx/maptbx/tst_real_space_refinement.py",
  ["$D/cctbx/regression/tst_maptbx_structure_factors.py", "P31"],
  ["$D/cctbx/regression/tst_miller_merge_equivalents.py", "P31"],
  ["$D/cctbx/regression/tst_miller_fft_map.py", "P31"],
  ["$D/cctbx/regression/tst_sampled_model_density.py", "P31"],
  ["$D/cctbx/regression/tst_fast_nv1995.py", "F222"],
  "$D/cctbx/regression/tst_geometry_restraints.py",
  "$D/cctbx/regression/tst_geometry_restraints_lbfgs.py",
  "$D/cctbx/regression/tst_geometry_restraints_2.py",
  ["$D/cctbx/development/make_cns_input.py", "P31"],
  ["$D/cctbx/development/tst_cns_epsilon.py", "P31"],
  ["$D/cctbx/development/tst_cns_hl.py", "P31"],
  ["$D/cctbx/development/run_shelx.py", "P31"],
   "$D/cctbx/regression/tst_pointgroup_tools.py",
   "$D/cctbx/sgtbx/sub_lattice_tools.py",
   "$D/cctbx/sgtbx/cosets.py",
   "$D/cctbx/regression/tst_find_best_cell.py",
  )

  build_dir = libtbx.env.under_build("cctbx")
  dist_dir = libtbx.env.dist_path("cctbx")

  from libtbx.option_parser import option_parser
  command_line = (option_parser(
    usage="run_tests [-j n]",
    description="Run tests in parallel")
    .option("-j", "--threads",
      action="store",
      type="int",
      default=1,
      help="number of threads",)
  ).process()
  n_threads = command_line.options.threads
  test_utils.run_tests(build_dir, dist_dir, tst_list, threads=n_threads)

if (__name__ == "__main__"):
  run()
