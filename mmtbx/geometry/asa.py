from __future__ import division

import mmtbx.geometry.primitive # import dependency
import mmtbx.geometry.shared_types # import dependency

import boost.python
ext = boost.python.import_ext( "mmtbx_geometry_asa_ext" )
from mmtbx_geometry_asa_ext import *

from mmtbx.geometry import altloc

# Indexing with altloc support
def create_description(index, atom, radius_for, probe):

  return altloc.Description(
    data = sphere(
      centre = atom.xyz,
      radius = radius_for[ atom.element.strip().capitalize() ] + probe,
      index = index,
      ),
    coordinates = atom.xyz,
    altid = altloc.altid_for( atom = atom ),
    )


def create_and_populate_indexer(factory, descriptions):

  indexer = altloc.Indexer( factory = factory )
  inserter = altloc.Inserter( indexer = indexer )

  for d in descriptions:
    d.accept( processor = inserter )

  return indexer


def get_linear_indexer_for(descriptions):

  return create_and_populate_indexer(
    factory = indexing.linear_spheres,
    descriptions = descriptions,
    )


def get_hash_indexer_for(descriptions):

  voxelizer = get_voxelizer_for( descriptions = descriptions )
  return create_and_populate_indexer(
    factory = lambda: indexing.hash_spheres( voxelizer = voxelizer, margin = 1 ),
    descriptions = descriptions,
    )


def get_optimal_indexer_for(descriptions):

  return get_linear_indexer_for( descriptions = descriptions )


def get_voxelizer_for(descriptions, step = 7):

  lows = [ d.data.low for d in descriptions ]
  ( low_xs, low_ys, low_zs ) = zip( *lows )
  low = ( min( low_xs ), min( low_ys ), min( low_zs ) )

  return mmtbx.geometry.shared_types.voxelizer(
    base = low,
    step = ( step, step, step ),
    )


# Visitors
class CompositeCheckerBuilder(object):
  """
  Finds neighbours for a sphere
  """

  def __init__(self, indexer, description):

    self.indexer = indexer
    self.checker = accessibility.pythagorean_checker()
    description.accept( processor = self )


  def process_regular(self, data, coordinates):

    self.append_neighbours(
      indexer = self.indexer.regular,
      sphere = data,
      centre = coordinates,
      )

    for indexer in self.indexer.altlocs.values():
      self.append_neighbours( indexer = indexer, sphere = data, centre = coordinates )


  def process_altloc(self, data, coordinates, identifier):

    self.append_neighbours(
      indexer = self.indexer.regular,
      sphere = data,
      centre = coordinates,
      )
    self.append_neighbours(
      indexer = self.indexer.altlocs[ identifier ],
      sphere = data,
      centre = coordinates,
      )


  def append_neighbours(self, indexer, sphere, centre):

    self.checker.add(
      neighbours = accessibility.filter(
        range = indexer.close_to( centre = centre ),
        predicate = accessibility.overlap_equality_predicate( object = sphere )
        )
      )


class SeparateCheckerBuilder(object):
  """
  Finds neighbours for a sphere
  """

  def __init__(self, indexer, description):

    self.indexer = indexer
    self.regular = accessibility.pythagorean_checker()
    self.altlocs = {}
    description.accept( processor = self )


  def process_regular(self, data, coordinates):

    self.append_neighbours(
      indexer = self.indexer.regular,
      sphere = data,
      centre = coordinates,
      checker = self.regular,
      )

    for ( identifier, indexer ) in self.indexer.altlocs.items():
      checker = accessibility.pythagorean_checker()
      self.append_neighbours(
        indexer = indexer,
        sphere = data,
        centre = coordinates,
        checker = checker,
        )

      if checker.neighbours():
        self.altlocs[ identifier ] = checker


  def process_altloc(self, data, coordinates, identifier):

    self.append_neighbours(
      indexer = self.indexer.regular,
      sphere = data,
      centre = coordinates,
      checker = self.regular,
      )
    self.altlocs[ identifier ] = accessibility.pythagorean_checker()
    self.append_neighbours(
      indexer = self.indexer.altlocs[ identifier ],
      sphere = data,
      centre = coordinates,
      checker = self.altlocs[ identifier ],
      )


  @staticmethod
  def append_neighbours(indexer, sphere, centre, checker):

    checker.add(
      neighbours = accessibility.filter(
        range = indexer.close_to( centre = centre ),
        predicate = accessibility.overlap_equality_predicate( object = sphere )
        )
      )


# Results
class AccessibleSurfaceResult(object):
  """
  Result of the calculation
  """

  def __init__(self, count, radius_sq):

    self.count = count
    self.radius_sq = radius_sq


  @property
  def surface(self):

    return self.count * self.radius_sq


class AccessibleSurfaceAreas(object):
  """
  Result of a series of calculations
  """

  def __init__(self, values, unit):

    self.values = values
    self.unit = unit


  @property
  def points(self):

    return [ v.count for v in self.values ]


  @property
  def areas(self):

    from scitbx.array_family import flex
    return self.unit * flex.double( v.surface for v in self.values )


# Ways for calculating ASA
def simple_surface_calculation(indexer, sampling, description):
  """
  Calculates ASA by not worrying about altlocs
  """

  builder = CompositeCheckerBuilder( indexer = indexer, description = description )
  overlapped = accessibility.filter(
    range = accessibility.transform(
      range = sampling.points,
      transformation = accessibility.transformation(
        centre = description.data.centre,
        radius = description.data.radius,
        ),
      ),
    predicate = builder.checker,
    )

  return AccessibleSurfaceResult(
    count = len( overlapped ),
    radius_sq = description.data.radius_sq,
    )


def altloc_averaged_calculation(indexer, sampling, description):
  """
  For atoms with altloc identifier, use empty altloc + atom with same altloc.
  For atoms with empty altloc, run a calculation for each know altloc and
  average the results.
  """

  builder = SeparateCheckerBuilder( indexer = indexer, description = description )

  overlapped = accessibility.filter(
    range = accessibility.transform(
      range = sampling.points,
      transformation = accessibility.transformation(
        centre = description.data.centre,
        radius = description.data.radius,
        ),
      ),
    predicate = builder.regular,
    )

  accessible_for = {}

  for ( identifier, checker ) in builder.altlocs.items():
    accessible_for[ identifier ] = [
      p for p in overlapped if checker( point = p )
      ]

  if not accessible_for:
    count = len( overlapped )

  else:
    count = sum( [ len( l ) for l in accessible_for.values() ] ) / len( accessible_for )

  return AccessibleSurfaceResult(
    count = count,
    radius_sq = description.data.radius_sq,
    )


# Module-level function
def calculate(
  atoms,
  calculation = simple_surface_calculation,
  indexer_selector = get_optimal_indexer_for,
  probe = 1.4,
  precision = 960,
  ):

  from cctbx.eltbx import van_der_waals_radii
  radius_for = van_der_waals_radii.vdw.table

  descriptions = [
    create_description( index = i, atom = a, radius_for = radius_for, probe = probe )
    for ( i, a ) in enumerate( atoms )
    ]

  indexer = indexer_selector( descriptions = descriptions )

  from mmtbx.geometry import sphere_surface_sampling
  sampling = sphere_surface_sampling.golden_spiral( count = precision )

  values = [
    calculation( indexer = indexer, sampling = sampling, description = d )
    for d in descriptions
    ]

  return AccessibleSurfaceAreas(
    values = values,
    unit = sampling.unit_area,
    )

