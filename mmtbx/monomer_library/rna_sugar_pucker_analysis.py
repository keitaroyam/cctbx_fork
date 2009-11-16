from cctbx import geometry_restraints
import scitbx.math
from scitbx import matrix
import libtbx.phil
from libtbx.math_utils import normalize_angle

master_phil = libtbx.phil.parse("""\
  bond_min_distance = 1.2
    .type = float
  bond_max_distance = 1.8
    .type = float
  epsilon_range_not_2p_min = 155
    .type = float
  epsilon_range_not_2p_max = 310
    .type = float
  delta_range_2p_min = 115
    .type = float
  delta_range_2p_max = 180
    .type = float
  p_distance_c1p_outbound_line_2p_max = 2.9
    .type = float
  o3p_distance_c1p_outbound_line_2p_max = 1.6
    .type = float
  bond_detection_distance_tolerance = 0.5
    .type = float
""")

class evaluate(object):

  __slots__ = [
    "epsilon",
    "delta",
    "p_distance_c1p_outbound_line",
    "o3p_distance_c1p_outbound_line",
    "is_2p_epsilon",
    "is_2p_delta",
    "is_2p_p_distance_c1p_outbound_line",
    "is_2p_o3p_distance_c1p_outbound_line",
    "is_2p"]

  def assign(O, **keyword_args):
    for slot in evaluate.__slots__:
      setattr(O, slot, keyword_args.get(slot, None))

  def __init__(O,
        params,
        residue_1_deoxy_ribo_atom_dict,
        residue_1_c1p_outbound_atom,
        residue_2_p_atom):
    def v(key): return matrix.col(residue_1_deoxy_ribo_atom_dict[key].xyz)
    c1p = v("C1'")
    o3p = v("O3'")
    c3p = v("C3'")
    c4p = v("C4'")
    c5p = v("C5'")
    bonded_sites = [
      (o3p, c3p),
      (c3p, c4p),
      (c5p, c4p)]
    distances = [abs(s2-s1) for s1,s2 in bonded_sites]
    p = None
    if (residue_2_p_atom is not None):
      p_trial = matrix.col(residue_2_p_atom.xyz)
      d = abs(p_trial-o3p)
      if (d <= params.bond_max_distance):
        p = p_trial
        distances.append(d)
    if (residue_1_c1p_outbound_atom is None):
      c1p_outbound = None
    else:
      c1p_outbound = matrix.col(residue_1_c1p_outbound_atom.xyz)
      distances.append(abs(c1p-c1p_outbound))
    if (   min(distances) < params.bond_min_distance
        or max(distances) > params.bond_max_distance):
      O.assign()
      return
    #
    def dihe(sites): return normalize_angle(geometry_restraints.dihedral(
      sites=sites, angle_ideal=0, weight=1).angle_model, deg=True)
    if (p is None):
      epsilon = None
    else:
      epsilon = dihe([p, o3p, c3p, c4p])
    delta = dihe([c5p, c4p, c3p, o3p])
    if (c1p_outbound is None):
      p_distance_c1p_outbound_line = None
      o3p_distance_c1p_outbound_line = None
    else:
      if (p is None):
        p_distance_c1p_outbound_line = None
      else:
        p_distance_c1p_outbound_line = scitbx.math.line_given_points(
          points=(c1p, c1p_outbound)).distance_sq(point=p)**0.5
      o3p_distance_c1p_outbound_line = scitbx.math.line_given_points(
        points=(c1p, c1p_outbound)).distance_sq(point=o3p)**0.5
    n_decisions = 0
    if (   epsilon is None
        or params.epsilon_range_not_2p_min is None
        or params.epsilon_range_not_2p_max is None):
      is_2p_epsilon = None
    else:
      is_2p_epsilon = (   epsilon < params.epsilon_range_not_2p_min
                       or epsilon > params.epsilon_range_not_2p_max)
      n_decisions += 1
    if (   params.delta_range_2p_min is None
        or params.delta_range_2p_max is None):
      is_2p_delta = None
    else:
      is_2p_delta = (    delta >= params.delta_range_2p_min
                     and delta <= params.delta_range_2p_max)
      n_decisions += 1
    if (   p_distance_c1p_outbound_line is None
        or params.p_distance_c1p_outbound_line_2p_max is None):
      is_2p_p_distance_c1p_outbound_line = None
    else:
      is_2p_p_distance_c1p_outbound_line = (
          p_distance_c1p_outbound_line
        < params.p_distance_c1p_outbound_line_2p_max)
      n_decisions += 1
    if (   o3p_distance_c1p_outbound_line is None
        or params.o3p_distance_c1p_outbound_line_2p_max is None):
      is_2p_o3p_distance_c1p_outbound_line = None
    else:
      is_2p_o3p_distance_c1p_outbound_line = (
          o3p_distance_c1p_outbound_line
        < params.o3p_distance_c1p_outbound_line_2p_max)
      n_decisions += 1
    if (n_decisions == 0):
      is_2p = None
    else:
      perp_distance = is_2p_p_distance_c1p_outbound_line
      if (perp_distance is None):
        perp_distance = is_2p_o3p_distance_c1p_outbound_line
      is_2p = (is_2p_epsilon or is_2p_delta or perp_distance)
    O.assign(
      epsilon=epsilon,
      delta=delta,
      p_distance_c1p_outbound_line=p_distance_c1p_outbound_line,
      o3p_distance_c1p_outbound_line=o3p_distance_c1p_outbound_line,
      is_2p_epsilon=is_2p_epsilon,
      is_2p_delta=is_2p_delta,
      is_2p_p_distance_c1p_outbound_line=is_2p_p_distance_c1p_outbound_line,
      is_2p_o3p_distance_c1p_outbound_line=is_2p_o3p_distance_c1p_outbound_line,
      is_2p=is_2p)
