from cctbx import xray
from cctbx import miller
from cctbx import maptbx
from cctbx import crystal
from cctbx import sgtbx
from cctbx.array_family import flex
from scitbx.python_utils import dicts

def peak_cluster_reduction(crystal_symmetry, peak_list, min_peak_distance, max_reduced_peaks):
  special_position_settings = crystal.special_position_settings(
    crystal_symmetry=crystal_symmetry,
    min_distance_sym_equiv=min_peak_distance)
  gridding = peak_list.gridding()
  peaks = []
  for entry in peak_list.entries():
    site = [float(entry.index[i]) / gridding[i] for i in xrange(3)]
    peaks.append(dicts.easy(
      site=special_position_settings.site_symmetry(site).exact_site(),
      height=entry.value))
  reduced_peaks = []
  for peak in peaks:
    site_symmetry = special_position_settings.site_symmetry(peak.site)
    equiv_sites = sgtbx.sym_equiv_sites(site_symmetry)
    keep = 0001
    for reduced_peak in reduced_peaks:
      dist = sgtbx.min_sym_equiv_distance_info(
        equiv_sites, reduced_peak.site).dist()
      if (dist < min_peak_distance):
        keep = 00000
        break
    if (keep == 0001):
      reduced_peaks.append(peak)
      if (len(reduced_peaks) == max_reduced_peaks): break
  return reduced_peaks

def calculate_exp_i_two_phi_peaks(xray_structure, d_min, min_peak_distance, max_reduced_peaks):
  f_h_array = xray_structure.structure_factors(
    anomalous_flag=00000,
    d_min=d_min).f_calc_array()
  two_i_phi_h_array = miller.array(
    miller_set=f_h_array,
    data=flex.polar(1, flex.arg(f_h_array.data())*2))
  fft_map = miller.fft_map(
    coeff_array=two_i_phi_h_array,
    d_min=d_min,
    symmetry_flags=maptbx.use_space_group_symmetry)
  real_map = fft_map.real_map()
  real_map = maptbx.copy(real_map, flex.grid(real_map.focus()))
  stats = maptbx.statistics(real_map)
  if (stats.max() != 0):
    real_map /= abs(stats.max())
  grid_tags = maptbx.grid_tags(real_map.focus())
  grid_tags.build(fft_map.space_group_info().type(), fft_map.symmetry_flags())
  grid_tags.verify(real_map)
  peak_list = maptbx.peak_list(
    data=real_map,
    tags=grid_tags.tag_array(),
    max_peaks=10*max_reduced_peaks)
  reduced_peaks = peak_cluster_reduction(
    crystal_symmetry=xray_structure,
    peak_list=peak_list,
    min_peak_distance=min_peak_distance,
    max_reduced_peaks=max_reduced_peaks)
  return reduced_peaks
