from libtbx import test_utils
import libtbx.load_env

def run():
  tst_list = (
  "$D/geometry/tests/tst_geometry.py",
  "$D/covariance/tests/tst_covariance.py",
  "$D/symmetry_search/tests/tst_goodness_of_symmetry.py",
  ["$D/symmetry_search/tests/tst_from_map.py", "P312"],
  "$D/regression/tst_adp_aniso_restraints.py",
  "$D/math/boost_python/tst_math.py",
  "$D/xray/boost_python/tst_targets_ls_with_scale.py",
  "$D/xray/boost_python/tst_f_model.py",
  "$D/array_family/boost_python/tst_flex.py",
  "$D/uctbx/boost_python/tst_uctbx.py",
  "$D/uctbx/boost_python/tst_crystal_orientation.py",
  "$D/sgtbx/boost_python/tst_sgtbx.py",
  "$D/sgtbx/boost_python/tst_N_fold_rot.py",
  "$D/crystal/tst_ext.py",
  "$D/crystal/tst_distance_based_connectivity.py",
  "$D/adptbx/boost_python/tst_adptbx.py",
  "$D/miller/boost_python/tst_miller.py",
  "$D/eltbx/boost_python/tst_chemical_elements.py",
  "$D/eltbx/boost_python/tst_xray_scattering.py",
  "$D/eltbx/boost_python/tst_henke.py",
  "$D/eltbx/boost_python/tst_icsd_radii.py",
  "$D/eltbx/boost_python/tst_covalent_radii.py",
  "$D/eltbx/boost_python/tst_neutron.py",
  "$D/eltbx/boost_python/tst_sasaki.py",
  "$D/eltbx/boost_python/tst_tiny_pse.py",
  "$D/eltbx/boost_python/tst_wavelengths.py",
  "$D/xray/boost_python/tst_xray.py",
  "$D/maptbx/boost_python/tst_maptbx.py",
  "$D/dmtbx/boost_python/tst_dmtbx.py",
  "$D/translation_search/boost_python/tst_translation_search.py",
  "$D/geometry_restraints/tst_ext.py",
  "$D/geometry_restraints/tst_proxy_registry.py",
  "$D/adp_restraints/tst_ext.py",
  "$D/regression/tst_math_module.py",
  ["$D/regression/tst_krivy_gruber.py", "--Quick"],
  "$D/regression/tst_sgtbx.py",
  "$D/regression/tst_itvb_2001_table_a1427_hall_symbols.py",
  "$D/regression/tst_space_group_type_tidy_cb_op_t.py",
  ["$D/regression/tst_sgtbx_denominators.py", "P31"],
  "$D/regression/tst_sgtbx_subgroups.py",
  "$D/regression/tst_sgtbx_lattice_symmetry.py",
  ["$D/regression/tst_adp_constraints.py", "P3"],
  "$D/regression/tst_adp_constraints_cartesian.py",
  "$D/regression/tst_sgtbx_site_constraints.py",
  "$D/regression/tst_reflection_statistics.py",
  "$D/regression/tst_sgtbx_harker.py",
  "$D/regression/tst_twin_target.py",
  "$D/sgtbx/symbol_confidence.py",
  "$D/sgtbx/bravais_types.py",
  "$D/regression/tst_miller_lookup_utils.py",
  ["$D/regression/tst_crystal.py", "I41/acd"],
  ["$D/regression/tst_direct_space_asu.py", "I41/acd"],
  "$D/regression/tst_pair_asu_table.py",
  "$D/regression/tst_crystal_asu_clusters.py",
  "$D/regression/tst_coordination_sequences.py",
  ["$D/regression/tst_crystal_close_packing.py", "R-3mr"],
  ["$D/regression/tst_xray.py", "I41/acd"],
  "$D/regression/tst_structure_factors_multithread.py",
  ["$D/regression/tst_miller.py", "P31"],
  ["$D/regression/tst_reciprocal_space_asu.py", "P312"],
  ["$D/regression/tst_triplet_generator.py", "P41"],
  ["$D/regression/tst_emma.py", "P31"],
  ["$D/regression/tst_expand_to_p1.py", "P31"],
  ["$D/regression/tst_change_basis.py", "P31"],
  ["$D/regression/tst_wilson_plot.py", "P31"],
  #"$D/regression/tst_xray_target_functors.py",
  ["$D/regression/tst_xray_derivatives.py", "P31"],
  ["$D/regression/tst_xray_fast_gradients.py", "P31"],
  ["$D/regression/tst_xray_minimization.py", "--F", "P31"],
  ["$D/regression/tst_xray_minimization.py", "--F_sq", "P31"],
  "$D/maptbx/tst_real_space_refinement.py",
  ["$D/regression/tst_maptbx_structure_factors.py", "P31"],
  ["$D/regression/tst_map_weights_for_symmetry_summation.py", "Pmmm"],
  "$D/maptbx/tst_real_space_refinement_simple.py",
  "$D/maptbx/tst_real_space_target_and_gradients.py",
  ["$D/regression/tst_miller_merge_equivalents.py", "P31"],
  ["$D/regression/tst_grouped_data.py", "P31"],
  ["$D/regression/tst_miller_fft_map.py", "P31"],
  ["$D/regression/tst_sampled_model_density.py", "P31"],
  ["$D/regression/tst_fast_nv1995.py", "F222"],
  "$D/regression/tst_geometry_restraints.py",
  "$D/regression/tst_geometry_restraints_lbfgs.py",
  "$D/regression/tst_geometry_restraints_2.py",
  ["$D/development/make_cns_input.py", "P31"],
  ["$D/development/tst_cns_epsilon.py", "P31"],
  ["$D/development/tst_cns_hl.py", "P31"],
  ["$D/development/run_shelx.py", "P31"],
   "$D/regression/tst_pointgroup_tools.py",
   "$D/sgtbx/sub_lattice_tools.py",
   "$D/sgtbx/rational_matrices_point_groups.py",
   "$D/sgtbx/cosets.py",
   "$D/sgtbx/reticular_pg_tools.py",
   "$D/sgtbx/reticular_twin_laws.py",
   "$D/regression/tst_find_best_cell.py",
   "$D/regression/tst_amplitude_normalisation.py",
   "$D/regression/tst_statistics_graphs.py",
   "$D/sgtbx/direct_space_asu/proto/tst_asu.py",
   "$D/masks/tests/tst_flood_fill.py",
  )

  build_dir = libtbx.env.under_build("cctbx")
  dist_dir = libtbx.env.dist_path("cctbx")

  test_utils.run_tests(build_dir, dist_dir, tst_list)

if (__name__ == "__main__"):
  run()
