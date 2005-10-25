def run():
  # complete exact model
  from cctbx.development import random_structure
  from cctbx import sgtbx

  space_group_info = sgtbx.space_group_info(
    symbol="P212121")
  n_sites = 500
  d_min = 2.0
  structure = random_structure.xray_structure(
    space_group_info = space_group_info,
    elements         = ["N"]*(n_sites),
    volume_per_atom  = 50,
    anisotropic_flag = False,
    random_u_iso     = True)

  f_obs = abs(structure.structure_factors(
    d_min          = d_min,
    anomalous_flag = False).f_calc())

  # partial model with errors
  from cctbx import xray

  fraction_missing = 0.1
  max_shift = 0.2
  n_keep = int(round(structure.scatterers().size()
                     * (1-fraction_missing)))
  partial_structure = xray.structure(
    special_position_settings=structure)
  partial_structure.add_scatterers(
    structure.scatterers()[:n_keep])
  partial_structure.replace_scatterers(
    partial_structure.random_shift_sites(
      max_shift_cart=max_shift).scatterers())

  f_calc = partial_structure.structure_factors(
    d_min          = d_min,
    anomalous_flag = False).f_calc()

  # R-free flags
  from cctbx.array_family import flex
  n_reflections = f_calc.data().size()
  partitioning = flex.random_permutation(size=n_reflections) % 10

  r_free_flags = f_obs.array(data=(partitioning == 0))

  import mmtbx.f_model

  f_model_manager = mmtbx.f_model.manager(
    xray_structure = partial_structure,
    f_obs = f_obs,
    r_free_flags = r_free_flags)
  f_model_manager.show()

  print f_model_manager.r_work()
  print f_model_manager.r_free()

  f_model_manager.r_factors_in_resolution_bins(
    reflections_per_bin = 100,
    max_number_of_bins  = 10)

  f_model_manager.update(
    k_sol = 1.2,
    b_sol = 30.0)

  f_model = f_model_manager.f_model()
  f_bulk = f_model_manager.f_bulk()

  f_model_manager.show_fom_phase_error_alpha_beta_in_bins(
    reflections_per_bin = 100,
    max_number_of_bins  = 10)

  fft_map = f_model_manager.electron_density_map(
    map_type = "2m*Fobs-D*Fmodel")

  import iotbx.xplor.map

  fft_map = f_model_manager.electron_density_map(
    map_type = "k*Fobs-n*Fmodel",
    k        = 2,
    n        = 1)
  fft_map.as_xplor_map(
    file_name="2fo-fm.xplor",
    title_lines=["2*Fobs - Fmodel"],
    gridding_first=(0,0,0),
    gridding_last=fft_map.n_real())

  figures_of_merit = f_model_manager.figures_of_merit()
  phase_errors = f_model_manager.phase_errors()

if (__name__ == "__main__"):
  run()
  print "OK"
