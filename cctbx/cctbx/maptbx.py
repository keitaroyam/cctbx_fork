import cctbx.sgtbx

import libtbx.boost_python
ext = libtbx.boost_python.import_ext("cctbx_maptbx_ext")
from cctbx_maptbx_ext import *

from cctbx import crystal
from cctbx import sgtbx
from cctbx.array_family import flex
from scitbx.python_utils import dicts
from scitbx.python_utils.misc import adopt_init_args
from scitbx.boost_python_utils import injector
import sys

class statistics(ext.statistics):

  def __init__(self, map):
    ext.statistics.__init__(self, map)

class _statistics(injector, ext.statistics):

  def show_summary(self, f=None):
    if (f is None): f = sys.stdout
    print >> f, "max %.6g" % (self.max())
    print >> f, "min %.6g" % (self.min())
    print >> f, "mean %.6g" % (self.mean())
    print >> f, "sigma %.6g" % (self.sigma())

class symmetry_flags(ext.symmetry_flags):

  def __init__(self, use_space_group_symmetry,
                     use_normalizer_k2l=00000,
                     use_structure_seminvariants=00000):
    ext.symmetry_flags.__init__(self, use_space_group_symmetry,
                                      use_normalizer_k2l,
                                      use_structure_seminvariants)

class _symmetry_flags(injector, ext.symmetry_flags):

  def show_summary(self, f=None):
    if (f is None): f = sys.stdout
    print >> f, "use_space_group_symmetry:", self.use_space_group_symmetry()
    print >> f, "use_normalizer_k2l:", self.use_normalizer_k2l()
    print >> f, "use_structure_seminvariants:",
    print >> f, self.use_structure_seminvariants()

use_space_group_symmetry = symmetry_flags(use_space_group_symmetry=0001)

class peak_list(ext.peak_list):

  def __init__(self, data,
                     tags,
                     peak_search_level=1,
                     max_peaks=0,
                     peak_cutoff=None,
                     interpolate=0001):
    if (peak_cutoff is None):
      ext.peak_list.__init__(self,
        data, tags, peak_search_level, max_peaks, interpolate)
    else:
      ext.peak_list.__init__(self,
        data, tags, peak_search_level, peak_cutoff, max_peaks, interpolate)

def as_CObjectZYX(map_unit_cell, first, last, apply_sigma_scaling=0001):
  return ext.as_CObjectZYX(map_unit_cell, first, last, apply_sigma_scaling)

structure_factors = dicts.easy(
  to_map=structure_factors_to_map,
  from_map=structure_factors_from_map)

class crystal_gridding:

  def __init__(self, unit_cell,
                     d_min,
                     resolution_factor=1./3,
                     symmetry_flags=None,
                     space_group_info=None,
                     mandatory_factors=None,
                     max_prime=5,
                     assert_shannon_sampling=0001):
    adopt_init_args(self, locals(), hide=0001)
    if (symmetry_flags is not None): assert space_group_info is not None
    if (mandatory_factors is None): mandatory_factors = (1,1,1)
    assert len(mandatory_factors) == 3
    if (symmetry_flags is not None):
      self._n_real = determine_gridding(
        unit_cell, d_min, resolution_factor,
        symmetry_flags, space_group_info.type(),
        mandatory_factors, max_prime, assert_shannon_sampling)
    else:
      self._n_real = determine_gridding(
        unit_cell, d_min, resolution_factor,
        mandatory_factors, max_prime, assert_shannon_sampling)

  def _copy_constructor(self, other):
    self._unit_cell = other._unit_cell
    self._d_min = other._d_min
    self._resolution_factor = other._resolution_factor
    self._symmetry_flags = other._symmetry_flags
    self._space_group_info = other._space_group_info
    self._mandatory_factors = other._mandatory_factors
    self._max_prime = other._max_prime
    self._n_real = other._n_real

  def unit_cell(self):
    return self._unit_cell

  def d_min(self):
    return self._d_min

  def resolution_factor(self):
    return self._resolution_factor

  def symmetry_flags(self):
    return self._symmetry_flags

  def space_group_info(self):
    return self._space_group_info

  def mandatory_factors(self):
    return self._mandatory_factors

  def max_prime(self):
    return self._max_prime

  def n_real(self):
    return self._n_real

  def space_group(self):
    assert self.space_group_info() is not None
    return self.space_group_info().group()

  def crystal_symmetry(self):
    assert self.space_group_info() is not None
    return crystal.symmetry(
      unit_cell=self.unit_cell(),
      space_group_info=self.space_group_info())

  def n_grid_points(self):
    result = 1
    for n in self.n_real():
      result *= n
    return result

  def tags(self):
    return crystal_gridding_tags(self)

class crystal_gridding_tags(crystal_gridding):

  def __init__(self, gridding):
    crystal_gridding._copy_constructor(self, gridding)
    assert gridding.symmetry_flags() is not None
    self._tags = grid_tags(self.n_real())
    self._tags.build(
      self.space_group_info().type(),
      self.symmetry_flags())
    assert self._tags.n_grid_misses() == 0

  def tags(self):
    return self._tags

  def peak_search(self, parameters, map, verify_symmetry=0001):
    if (verify_symmetry):
      assert self._tags.verify(map)
    if (map.accessor().is_padded()):
      map = copy(map, flex.grid(map.focus()))
    grid_peaks = peak_list(
      data=map,
      tags=self._tags.tag_array(),
      peak_search_level=parameters.peak_search_level(),
      max_peaks=parameters.max_peaks(),
      peak_cutoff=parameters.peak_cutoff(),
      interpolate=parameters.interpolate())
    if (parameters.min_distance_sym_equiv() is None):
      return grid_peaks
    return peak_cluster_analysis(
      peak_list=grid_peaks,
      special_position_settings=crystal.special_position_settings(
        crystal_symmetry=self.crystal_symmetry(),
        min_distance_sym_equiv=parameters.min_distance_sym_equiv()),
      general_positions_only=parameters.general_positions_only(),
      min_cross_distance=parameters.min_cross_distance(),
      max_clusters=parameters.max_clusters())

class peak_search_parameters:

  def __init__(self, peak_search_level=1,
                     max_peaks=0,
                     peak_cutoff=None,
                     interpolate=0001,
                     min_distance_sym_equiv=None,
                     general_positions_only=00000,
                     min_cross_distance=None,
                     max_clusters=None):
    adopt_init_args(self, locals(), hide=0001)

  def _copy_constructor(self, other):
    self._peak_search_level = other._peak_search_level
    self._max_peaks = other._max_peaks
    self._peak_cutoff = other._peak_cutoff
    self._interpolate = other._interpolate
    self._min_distance_sym_equiv = other._min_distance_sym_equiv
    self._general_positions_only = other._general_positions_only
    self._min_cross_distance = other._min_cross_distance
    self._max_clusters = other._max_clusters

  def peak_search_level(self):
    return self._peak_search_level

  def max_peaks(self):
    return self._max_peaks

  def peak_cutoff(self):
    return self._peak_cutoff

  def interpolate(self):
    return self._interpolate

  def min_distance_sym_equiv(self):
    return self._min_distance_sym_equiv

  def general_positions_only(self):
    return self._general_positions_only

  def min_cross_distance(self):
    return self._min_cross_distance

  def max_clusters(self):
    return self._max_clusters

class cluster_site_info:

  def __init__(self, peak_list_index, grid_index, grid_height, site, height):
    adopt_init_args(self, locals())

class peak_cluster_analysis:

  def __init__(self, peak_list,
                     special_position_settings,
                     general_positions_only=00000,
                     min_cross_distance=None,
                     max_clusters=None):
    adopt_init_args(self, locals(), hide=0001)
    if (min_cross_distance is None):
      min_cross_distance = special_position_settings.min_distance_sym_equiv()
    self._gridding = peak_list.gridding()
    self._peak_list_indices = flex.size_t()
    self._peak_list_index = 0
    self._sites = flex.vec3_double()
    self._heights = flex.double()
    self._fixed_site_indices = flex.size_t()

  def peak_list(self):
    return self._peak_list

  def special_position_settings(self):
    return self._special_position_settings

  def general_positions_only(self):
    return self._general_positions_only

  def min_cross_distance(self):
    return self._min_cross_distance

  def max_clusters(self):
    return self._max_clusters

  def peak_list_indices(self):
    return self._peak_list_indices

  def fixed_site_indices(self):
    return self._fixed_site_indices

  def sites(self):
    return self._sites

  def heights(self):
    return self._heights

  def max_grid_height(self):
    if (self._peak_list.size() == 0):
      return None
    return self._peak_list.heights()[0]

  def append_fixed_site(self, site, height=0):
    self._fixed_site_indices.append(self._sites.size())
    self._sites.append(site)
    self._heights.append(height)
    self._peak_list_indices.append(self._peak_list.size())

  def next(self):
    while 1:
      peak_list_index = self._peak_list_index
      if (peak_list_index >= self._peak_list.size()): return None
      grid_index = self._peak_list.grid_indices(peak_list_index)
      grid_height = self._peak_list.grid_heights()[peak_list_index]
      site = self._peak_list.sites()[peak_list_index]
      height = self._peak_list.heights()[peak_list_index]
      self._peak_list_index += 1
      site_symmetry = self._special_position_settings.site_symmetry(site)
      if (    self._general_positions_only
          and not site_symmetry.is_point_group_1()):
        continue
      site = site_symmetry.exact_site()
      equiv_sites = sgtbx.sym_equiv_sites(site_symmetry)
      keep = 0001
      for s in self._sites:
        dist = sgtbx.min_sym_equiv_distance_info(equiv_sites, s).dist()
        if (dist < self._min_cross_distance):
          keep = 00000
          break
      if (keep == 0001):
        self._peak_list_indices.append(peak_list_index)
        self._sites.append(site)
        self._heights.append(height)
        return cluster_site_info(
          peak_list_index=peak_list_index,
          grid_index=grid_index,
          grid_height=grid_height,
          site=site,
          height=height)

  def all(self, max_clusters=None):
    if (max_clusters is None):
      max_clusters = self._max_clusters
    assert max_clusters is not None
    while 1:
      if (self._sites.size() >= max_clusters): break
      if (self.next() is None): break
    return self

  def discard_last(self):
    assert self._peak_list_indices.size() > 0
    self._peak_list_indices.pop_back()
    self._sites.pop_back()
    self._heights.pop_back()
