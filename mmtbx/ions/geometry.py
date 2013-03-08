"""
Methods for examining bond angles around an ion and categorizing
the coordination geometry.
"""
from __future__ import division
from math import sqrt

def _bond_angles(vectors):
  """
  Returns a list of angles (In degrees) between all two-element combinations
  in vectors.
  """

  return [(v1, v2, v1.angle(v2, deg = True))
          for index, v1 in enumerate(vectors)
          for v2 in vectors[index + 1:]]

# Tetrahedrons have 4 vertices, with angles between all pairs of vertices
# uniformly about 104.5 degrees.
def _is_tetrahedral(vectors, dev_cutoff = 16):
  if len(vectors) > 4 or len(vectors) < 3:
    return

  angles = _bond_angles(vectors)
  deviation = sqrt(sum(abs(i[2] - 104.5) ** 2 for i in angles) / len(vectors))

  if deviation <= dev_cutoff:
    return deviation, 4 - len(vectors)

# Square planar geometry has 4 vertices, all on the same equatorial plane.
# The expected angles are 90 degrees between neighboring vertices and 180
# degrees between vertices across from one another.
def _is_square_planar(vectors, dev_cutoff = 20):
  if len(vectors) > 4 or len(vectors) < 3:
    return

  angles = _bond_angles(vectors)
  deviation = sqrt(sum(abs(i[2] - 90) ** 2 for i in angles) / len(vectors))

  if deviation <= dev_cutoff:
    return deviation, 4 - len(vectors)

# Octahedrons have 6 vertices (Their name comes from their 8 faces).
# The expected angles are all either 90 degrees (Next to each other),
# or 180 degrees (Across from each other).
def _is_octahedral(vectors, dev_cutoff = 15):
  if len(vectors) > 6 or len(vectors) < 5:
    return

  angles = _bond_angles(vectors)

  # Grab the two axial vectors
  deviants = []
  opposites = 0

  for v1, v2, angle in angles:
    from_90 = abs(90 - angle)
    from_180 = abs(180 - angle)

    if from_180 < from_90:
      opposites += 1
      deviants += from_180,
    else:
      deviants += from_90,

  deviation = sqrt(sum(abs(i) ** 2 for i in deviants) / len(deviants))

  if opposites > 3 or opposites < 2:
    return

  if deviation <= dev_cutoff:
    return deviation, 6 - len(vectors)

# Trigonal bipyramids have 5 vertices. Three vertices form a plane in the middle
# and the angles between all 3 are 120 degrees. The two other vertices reside
# axial to the plane, at 90 degrees from all the equatorial vertices.
def _is_trigonal_bipyramid(vectors, dev_cutoff = 15):
  if len(vectors) > 5 or len(vectors) < 4:
    return

  angles = _bond_angles(vectors)

  # Grab the two axial vectors
  ax1, ax2, axial_angle = max(angles, key = lambda x: abs(x[-1]))

  if axial_angle < 150:
    # Missing one of the two axial vectors, just quit
    return

  base_to_axials = []
  equatorial_angles = []

  for v1, v2, angle in angles:
    # Python has no boolean xor!
    # Grab the angles between the two endpoints of the bipyramid and the base
    if v1 in [ax1, ax2] != v2 in [ax1, ax2]:
      base_to_axials += angle,
    elif v1 not in [ax1, ax2] and v2 not in [ax1, ax2]:
      equatorial_angles += angle,

  deviants =  [axial_angle - 180]
  deviants += [i - 90 for i in base_to_axials]
  deviants += [i - 120 for i in equatorial_angles]
  deviation = sqrt(sum(abs(i) ** 2 for i in deviants) / len(deviants))

  if deviation <= dev_cutoff:
    return deviation, 5 - len(vectors)

SUPPORTED_GEOMETRIES = {
  "tetrahedral": _is_tetrahedral,
  "square planar": _is_square_planar,
  "octahedral": _is_octahedral,
  "trigonal bipyramid": _is_trigonal_bipyramid,
  }

def find_coordination_geometry(nearby_atoms, cutoff = 2.5):
  """
  Returns a list of tuples of potential geometries for the vectors given by
  nearby_atoms, along with the average deviation from those geometries.
  """

  # Filter out overlapping atoms, we just want an idea of the coordinating
  # geometry, even if it is two different atoms are occupying the same spot.
  nearby_atoms = [atom for index, atom in enumerate(nearby_atoms)
                  if not [other for other in nearby_atoms[index + 1:]
                          if atom.distance_from(other) < 0.5]]

  geometries = []
  vectors = []
  for contact in nearby_atoms :
    if (contact.distance() <= cutoff) :
      vectors.append(contact.vector)

  for name, func in SUPPORTED_GEOMETRIES.items():
    val = func(vectors)

    if val is not None:
      deviation, missing = val
      geometries += (name, deviation, missing),

  return geometries
