from __future__ import division
from scitbx.array_family import flex
import random
from mmtbx import map_tools
from cctbx import miller
from cctbx import maptbx
from libtbx.test_utils import approx_equal

def get_map(map_coeffs, crystal_gridding):
  fft_map = miller.fft_map(
    crystal_gridding     = crystal_gridding,
    fourier_coefficients = map_coeffs)
  fft_map.apply_sigma_scaling()
  return fft_map.real_map_unpadded()

def compute_map_and_combine(
      map_coeffs,
      crystal_gridding,
      map_data):
  m = get_map(map_coeffs=map_coeffs, crystal_gridding=crystal_gridding)
  if(map_data is None): map_data = m
  else:
    for i in [0,0.1,0.2,0.3,0.4,0.5]:
      maptbx.intersection(
        map_data_1 = m,
        map_data_2 = map_data,
        threshold  = i)
    map_data = (m+map_data)/2
  return map_data

def randomize_struture_factors(map_coeffs, number_of_kicks, phases_only=False):
  map_coeff_data = None
  for kick in xrange(number_of_kicks):
    rc, ar, pr = random.choice([(0.1, 0.10, 10),
                                (0.2, 0.09, 9),
                                (0.3, 0.08, 8),
                                (0.4, 0.07, 7),
                                (0.5, 0.06, 6),
                                (0.6, 0.05, 5),
                                (0.7, 0.04, 4),
                                (0.8, 0.03, 3),
                                (0.9, 0.02, 2),
                                (1.0, 0.01, 1),
                               ])
    if(phases_only): ar = 0
    sel = flex.random_bool(map_coeffs.size(), rc)
    mc = map_coeffs.randomize_amplitude_and_phase(
      amplitude_error=ar, phase_error_deg=pr, selection=sel)
    if(map_coeff_data is None): map_coeff_data = mc.data()
    else:                       map_coeff_data = map_coeff_data + mc.data()
  map_coeff_data/number_of_kicks
  return miller.set(
    crystal_symmetry = map_coeffs.crystal_symmetry(),
    indices          = map_coeffs.indices(),
    anomalous_flag   = False).array(data = map_coeff_data)

def kick_map_coeffs(
      map_coeffs,
      crystal_gridding,
      number_of_kicks = 10,
      macro_cycles    = 10,
      missing         = None,
      kick_completeness = 0.95,
      phases_only       = False):
  map_data = None
  if(macro_cycles==0):
    map_data = compute_map_and_combine(
      map_coeffs       = map_coeffs,
      crystal_gridding = crystal_gridding,
      map_data         = map_data)
  for it in xrange(macro_cycles):
    print "  %d"%it
    if(number_of_kicks>0):
      mc = randomize_struture_factors(map_coeffs=map_coeffs,
        number_of_kicks=number_of_kicks, phases_only=phases_only)
    else:
      mc = map_coeffs.deep_copy()
    if(missing is not None):
      mc = mc.complete_with(other=missing, scale=True)
    if(kick_completeness):
      mc = mc.select(flex.random_bool(mc.size(), kick_completeness))
    map_data = compute_map_and_combine(
      map_coeffs       = mc,
      crystal_gridding = crystal_gridding,
      map_data         = map_data)
  return map_data

def kick_fmodel(
      fmodel,
      map_type,
      crystal_gridding,
      number_of_kicks = 10,
      macro_cycles    = 10,
      missing         = None,
      kick_completeness = 0.95):
  f_model = fmodel.f_model_no_scales()
  zero = fmodel.f_calc().customized_copy(data =
    flex.complex_double(fmodel.f_calc().data().size(), 0))
  fmodel_dc  = mmtbx.f_model.manager(
    f_obs         = fmodel.f_obs(),
    r_free_flags  = fmodel.r_free_flags(),
    k_isotropic   = fmodel.k_isotropic(),
    k_anisotropic = fmodel.k_anisotropic(),
    f_calc        = fmodel.f_model_no_scales(),
    f_part1       = fmodel.f_part1(),
    f_part2       = fmodel.f_part2(),
    f_mask        = zero)
  r1 = fmodel.r_work()
  r2 = fmodel_dc.r_work()
  assert approx_equal(r1, r2, 1.e-4), [r1, r2]
  def get_mc(fm):
   return fm.electron_density_map(
     update_f_part1=False).map_coefficients(
       map_type     = map_type,
       isotropize   = True,
       fill_missing = False)
  def recreate_r_free_flags(fmodel):
    rc = random.choice([0.05, 0.9])
    r_free_flags = flex.random_bool(fmodel.f_obs().indices().size(), rc)
    fmodel._r_free_flags._data = r_free_flags
    return fmodel
  map_data = None
  for it in xrange(macro_cycles):
    print "  %d"%it
    f_model_kick = randomize_struture_factors(map_coeffs=f_model,
      number_of_kicks=number_of_kicks)
    fmodel_dc = recreate_r_free_flags(fmodel = fmodel_dc)
    fmodel_dc.update(f_calc = f_model_kick)
    mc = get_mc(fm=fmodel_dc)
    if(missing is not None):
      mc = mc.complete_with(missing, scale=True)
    if(kick_completeness):
      mc = mc.select(flex.random_bool(mc.size(), kick_completeness))
    map_data = compute_map_and_combine(
      map_coeffs       = mc,
      crystal_gridding = crystal_gridding,
      map_data         = map_data)
  return map_data

class run(object):
  """
  Note 1: Assume Fmodel has correct scaling already (all f_parts etc).
  Note 2: More macro_cycles can substantially clean map in extremely bad cases.
  """

  def __init__(
      self,
      fmodel,
      map_type           = "2mFo-DFc",
      mask_data          = None,
      crystal_gridding   = None,
      number_of_kicks    = 10,
      macro_cycles       = 10,
      kick_completeness  = 0.95):
    fmodel = self.convert_to_non_anomalous(fmodel=fmodel)
    self.mc_orig = map_tools.electron_density_map(
      fmodel=fmodel).map_coefficients(
        map_type     = "2mFo-DFc",
        isotropize   = True,
        fill_missing = False)
    # Kick map coefficients
    md_kick = kick_map_coeffs(
      map_coeffs        = self.mc_orig,
      crystal_gridding  = crystal_gridding,
      number_of_kicks   = number_of_kicks,
      macro_cycles      = macro_cycles,
      missing           = None,
      kick_completeness = kick_completeness)
    self.mc_kick = self.map_coeffs_from_map(map_data=md_kick)
    # Kick fmodel
    md_fm = kick_fmodel(
      fmodel            = fmodel,
      map_type          = map_type,
      crystal_gridding  = crystal_gridding,
      number_of_kicks   = number_of_kicks,
      macro_cycles      = macro_cycles,
      missing           = None,
      kick_completeness = kick_completeness)
    self.mc_fm = self.map_coeffs_from_map(map_data=md_fm)
    # Kick OMIT map
    com1 = mmtbx.maps.composite_omit_map.run(
      map_type             = "mFo-DFc",
      crystal_gridding     = crystal_gridding,
      n_debias_cycles      = 2,
      fmodel               = fmodel.deep_copy(), # XXX
      full_resolution_map  = True,
      box_size_as_fraction = 0.03)
    md_com1 = kick_map_coeffs(
      map_coeffs        = com1.map_coefficients,
      crystal_gridding  = crystal_gridding,
      number_of_kicks   = number_of_kicks,
      macro_cycles      = macro_cycles,
      phases_only       = True,
      missing           = None,
      kick_completeness = kick_completeness)
    self.mc_com1 = self.map_coeffs_from_map(map_data=md_com1)
    # Kick OMIT map 2
    com2 = mmtbx.maps.composite_omit_map.run(
      map_type             = "2mFo-DFc",
      crystal_gridding     = crystal_gridding,
      n_debias_cycles      = 2,
      fmodel               = fmodel.deep_copy(), # XXX
      full_resolution_map  = True,
      box_size_as_fraction = 0.03)
    md_com2 = kick_map_coeffs(
      map_coeffs        = com2.map_coefficients,
      crystal_gridding  = crystal_gridding,
      number_of_kicks   = number_of_kicks,
      macro_cycles      = macro_cycles,
      phases_only       = True,
      missing           = None,
      kick_completeness = kick_completeness)
    self.mc_com2 = self.map_coeffs_from_map(map_data=md_com2)
    # combine maps
    def intersect(m1,m2, use_average):
      for i in [0,0.1,0.2,0.3,0.4,0.5]:
        maptbx.intersection(
          map_data_1 = m1,
          map_data_2 = m2,
          threshold  = i)
      if(use_average): return (m1+m2)/2
      else:            return m1
    m = (md_kick + md_fm)/2
    m = intersect(m, md_kick, use_average=True)
    m = intersect(m, md_fm,   use_average=True)
    m = intersect(m, md_com1, use_average=False)
    m = intersect(m, md_com2, use_average=False)
    # final: experimental (m2)
    m2 = m.deep_copy()
    maptbx.reset(
      data=m2,
      substitute_value=0.0,
      less_than_threshold=0.5,
      greater_than_threshold=-9999,
      use_and=True)
    for i in xrange(3): # may not be needed given that unsharp mask is used below
      maptbx.map_box_average(
        map_data   = m2,
        cutoff     = 0.6,
        index_span = 1)
    maptbx.sharpen(map_data=m2, index_span=1, n_averages=2)
    # final, real final (m)
    self.mc_result  = self.map_coeffs_from_map(map_data=m)
    self.mc_result2 = self.map_coeffs_from_map(map_data=m2)

  def write_mc(self, file_name="mc.mtz"):
    mtz_dataset = self.mc_orig.as_mtz_dataset(column_root_label="mc_orig")
    mtz_dataset.add_miller_array(
      miller_array=self.mc_kick,
      column_root_label="mc_kick")
    mtz_dataset.add_miller_array(
      miller_array=self.mc_fm,
      column_root_label="mc_fm")
    mtz_dataset.add_miller_array(
      miller_array=self.mc_com1,
      column_root_label="mc_com1")
    mtz_dataset.add_miller_array(
      miller_array=self.mc_com2,
      column_root_label="mc_com2")
    mtz_dataset.add_miller_array(
      miller_array=self.mc_result,
      column_root_label="mc_result")

    mtz_dataset.add_miller_array(
      miller_array=self.mc_result2,
      column_root_label="mc_result2")

    mtz_object = mtz_dataset.mtz_object()
    mtz_object.write(file_name = file_name)

  def map_coeffs_from_map(self, map_data):
    return self.mc_orig.structure_factors_from_map(
      map            = map_data,
      use_scale      = True,
      anomalous_flag = False,
      use_sg         = False)

  def convert_to_non_anomalous(self, fmodel):
    if(fmodel.f_obs().anomalous_flag()):
      f_obs        = fmodel.f_obs().average_bijvoet_mates()
      r_free_flags = fmodel.r_free_flags().average_bijvoet_mates()
      fmodel = mmtbx.f_model.manager(
        f_obs = f_obs,
        r_free_flags = r_free_flags,
        xray_structure = fmodel.xray_structure)
      fmodel.update_all_scales(update_f_part1_for="refinement")
    return fmodel


#    mc_1 = oo.map_coefficients
#    self.complete_set = mc_1
#    self.partial_set = mc_1
#
#    #self.complete_set = map_tools.electron_density_map(
#    #  fmodel=fmodel).map_coefficients(
#    #    map_type            = self.map_type,
#    #    isotropize          = True,
#    #    fill_missing        = True,
#    #    fill_missing_method = fill_mode)
#    #self.partial_set = map_tools.electron_density_map(
#    #  fmodel=fmodel).map_coefficients(
#    #    map_type     = self.map_type,
#    #    isotropize   = True,
#    #    fill_missing = False)
#    self.missing = self.complete_set.lone_set(self.partial_set)
#    # initialize result map
#    map_data = None
#    # utility function
#    def compute_map_and_combine(map_coeffs, crystal_gridding, map_data):
#      fft_map = miller.fft_map(
#        crystal_gridding     = crystal_gridding,
#        fourier_coefficients = map_coeffs)
#      fft_map.apply_sigma_scaling()
#      m = fft_map.real_map_unpadded()
#      if(mask_data is not None):
#        maptbx.remove_single_node_peaks(
#          map_data   = m,
#          mask_data  = mask_data,
#          cutoff     = 1,
#          index_span = 2)
#      if(map_data is None): map_data = m
#      else:
#        for i in [0,0.1,0.2,0.3,0.4,0.5]:
#          maptbx.intersection(
#            map_data_1 = m,
#            map_data_2 = map_data,
#            threshold  = i)
#        map_data = (m+map_data)/2
#      return map_data
#    # shake Fmap
#    if(shake_f_map):
#      print "shake map coefficients cycles:"
#      for it in xrange(macro_cycles):
#        print "  %d"%it
#        if(0): # may need do this if filling mode is f_model
#          sel = flex.random_bool(self.missing.data().size(), 0.5)
#          missing = self.missing.select(sel)
#          missing = missing.randomize_amplitude_and_phase(
#            amplitude_error=0.1,
#            phase_error_deg=60)
#        else: missing = self.missing
#        mc = self.call_run_kick_loop(map_coeffs=self.partial_set)
#        mc = mc.complete_with(other=missing, scale=True)
#        if(shake_completeness):
#          mc = mc.select(flex.random_bool(mc.size(), 0.95))
#        map_data = compute_map_and_combine(
#          map_coeffs       = mc,
#          crystal_gridding = crystal_gridding,
#          map_data         = map_data)
#    # shake Fmodel
#    if(shake_f_model):
#      print "shake f_model cycles:"
#      f_model = fmodel.f_model_no_scales()
#      zero = fmodel.f_calc().customized_copy(data = fmodel.f_calc().data()*0)
#      fmodel_dc  = mmtbx.f_model.manager(
#        f_obs         = fmodel.f_obs(),
#        r_free_flags  = fmodel.r_free_flags(),
#        k_isotropic   = fmodel.k_isotropic(),
#        k_anisotropic = fmodel.k_anisotropic(),
#        f_calc        = fmodel.f_model_no_scales(),
#        f_part1       = fmodel.f_part1(),
#        f_part2       = fmodel.f_part2(),
#        f_mask        = zero)
#      r1 = fmodel.r_work()
#      r2 = fmodel_dc.r_work()
#      assert approx_equal(r1, r2, 1.e-4), [r1, r2]
#      def get_mc(fm):
#       return fm.electron_density_map(
#         update_f_part1=False).map_coefficients(
#           map_type     = self.map_type,
#           isotropize   = True,
#           fill_missing = False)
#      for it in xrange(macro_cycles):
#        print "  %d"%it
#        f_model_kick = self.call_run_kick_loop(map_coeffs=f_model)
#        fmodel_dc = self.recreate_r_free_flags(fmodel = fmodel_dc)
#        fmodel_dc.update(f_calc = f_model_kick)
#        mc = get_mc(fm=fmodel_dc)
#        if(0): # may need do this if filling mode is f_model
#          sel = flex.random_bool(self.missing.data().size(), 0.5)
#          missing = self.missing.select(sel)
#          missing = missing.randomize_amplitude_and_phase(
#            amplitude_error=0.1,
#            phase_error_deg=60)
#        else: missing = self.missing
#        mc = mc.complete_with(missing, scale=True)
#        if(shake_completeness):
#          mc = mc.select(flex.random_bool(mc.size(), 0.95))
#        map_data = compute_map_and_combine(
#          map_coeffs       = mc,
#          crystal_gridding = crystal_gridding,
#          map_data         = map_data)
#    # XXX see what it does to waters
#    if(mask_data is not None):
#      maptbx.remove_single_node_peaks(
#        map_data   = map_data,
#        mask_data  = mask_data,
#        cutoff     = 1,
#        index_span = 2)
#    #
#    for i in xrange(3):
#      maptbx.map_box_average(
#        map_data   = map_data,
#        cutoff     = 0.5,
#        index_span = 1)
#    # set to zero negative map values
#    maptbx.reset(
#      data=map_data,
#      substitute_value=0.0,
#      less_than_threshold=0.0,
#      greater_than_threshold=-9999,
#      use_and=True)
#    #
#    sd = map_data.sample_standard_deviation()
#    map_data = map_data/sd
#    self.map_data = map_data
#    self.map_coefficients = self.complete_set.structure_factors_from_map(
#      map            = self.map_data,
#      use_scale      = True,
#      anomalous_flag = False,
#      use_sg         = False)
#
#
#
