import iotbx.pdb
from cctbx import crystal
from cctbx.crystal.direct_space_asu import non_crystallographic_asu_mappings
from cctbx import sgtbx
from cctbx import uctbx
from cctbx.array_family import flex
from cctbx.development import debug_utils
from scitbx import matrix
from scitbx.python_utils.math_utils import ifloor, iceil
from scitbx.python_utils.misc import adopt_init_args
from libtbx.test_utils import approx_equal
from libtbx.itertbx import count
import math
import sys

def hexagonal_sampling_cell(point_distance):
  return uctbx.unit_cell((
    point_distance, point_distance, point_distance*math.sqrt(8/3.),
    90, 90, 120))

class hexagonal_box:

  def __init__(self, hex_cell, vertices_cart):
    assert len(vertices_cart) > 0
    vertices_hex = hex_cell.fractionalization_matrix() * vertices_cart
    self.min = vertices_hex.min()
    self.max = vertices_hex.max()
    self.pivot = vertices_hex[flex.min_index(vertices_hex.dot())]

def hex_indices_as_site(point, layer=0):
  if (layer % 2 == 0):
    if (point[2] % 2 == 0):
      return [point[0],point[1],point[2]*.5]
    else:
      return [point[0]+1/3.,point[1]+2/3.,point[2]*.5]
  else:
    if (point[2] % 2 == 0):
      return [-point[0],-point[1],point[2]*.5]
    else:
      return [-point[0]-1/3.,-point[1]-2/3.,point[2]*.5]

def hcp_fill_box(cb_op_original_to_sampling, float_asu, continuous_shift_flags,
                 point_distance,
                 buffer_thickness=-1, all_twelve_neighbors=00000,
                 exercise_cpp=0001):
  if (exercise_cpp):
    cpp = crystal.close_packing_hexagonal_sampling(
      cb_op_original_to_sampling=cb_op_original_to_sampling,
      float_asu=float_asu,
      continuous_shift_flags=continuous_shift_flags,
      point_distance=point_distance,
      buffer_thickness=buffer_thickness,
      all_twelve_neighbors=all_twelve_neighbors)
  assert point_distance > 0
  if (buffer_thickness < 0):
    buffer_thickness = point_distance * (2/3. * (.5 * math.sqrt(3)))
  if (exercise_cpp):
    assert cpp.cb_op_original_to_sampling().c()==cb_op_original_to_sampling.c()
    assert cpp.float_asu().unit_cell().is_similar_to(float_asu.unit_cell())
    assert cpp.continuous_shift_flags() == continuous_shift_flags
    assert approx_equal(cpp.point_distance(), point_distance)
    assert approx_equal(cpp.buffer_thickness(), buffer_thickness)
    assert cpp.all_twelve_neighbors() == all_twelve_neighbors
  float_asu_buffer = float_asu.add_buffer(thickness=buffer_thickness)
  hex_cell = hexagonal_sampling_cell(point_distance=point_distance)
  hex_box = hexagonal_box(
    hex_cell=hex_cell,
    vertices_cart=float_asu.volume_vertices(cartesian=0001))
  hex_box_buffer = hexagonal_box(
    hex_cell=hex_cell,
    vertices_cart=float_asu_buffer.volume_vertices(cartesian=0001))
  box_lower = []
  box_upper = []
  for i in xrange(3):
    if (continuous_shift_flags[i]):
      box_lower.append(0)
      box_upper.append(0)
    else:
      n = iceil(abs(hex_box.max[i]-hex_box.pivot[i]))
      box_lower.append(min(-2,ifloor(hex_box_buffer.min[i]-hex_box.pivot[i])))
      box_upper.append(n+max(2,iceil(hex_box_buffer.max[i]-hex_box.max[i])))
  if (exercise_cpp):
    assert list(cpp.box_lower()) == box_lower
    assert list(cpp.box_upper()) == box_upper
  hex_to_frac_matrix = (
      matrix.sqr(float_asu.unit_cell().fractionalization_matrix())
    * matrix.sqr(hex_cell.orthogonalization_matrix()))
  sites_frac = flex.vec3_double()
  for point in flex.nested_loop(begin=box_lower,
                                end=box_upper,
                                open_range=00000):
    site_hex = matrix.col(hex_box.pivot) \
             + matrix.col(hex_indices_as_site(point))
    site_frac = hex_to_frac_matrix * site_hex
    if (float_asu_buffer.is_inside(site_frac)):
      sites_frac.append(site_frac)
    elif (all_twelve_neighbors):
      for offset in [(1,0,0),(1,1,0),(0,1,0),(-1,0,0),(-1,-1,0),(0,-1,0),
                     (0,0,1),(-1,-1,1),(0,-1,1),
                     (0,0,-1),(-1,-1,-1),(0,-1,-1)]:
        offset_hex = hex_indices_as_site(offset, layer=point[2])
        offset_frac = hex_to_frac_matrix * matrix.col(offset_hex)
        other_site_frac = site_frac + offset_frac
        if (float_asu.is_inside(other_site_frac)):
          sites_frac.append(site_frac)
          break
  assert sites_frac.size() > 0
  rt = cb_op_original_to_sampling.c_inv().as_double_array()
  sites_frac = rt[:9] * sites_frac
  sites_frac += rt[9:]
  if (exercise_cpp):
    assert not cpp.at_end()
    cpp_sites_frac = cpp.all_sites_frac()
    assert cpp.at_end()
    assert cpp_sites_frac.size() == sites_frac.size()
    assert approx_equal(cpp_sites_frac, sites_frac)
    cpp.restart()
    assert not cpp.at_end()
    assert approx_equal(cpp.next_site_frac(), sites_frac[0])
    assert cpp.count_sites() == sites_frac.size()-1
    assert cpp.at_end()
    cpp.restart()
    n = 0
    for site in cpp: n += 1
    assert n == sites_frac.size()
  return sites_frac

def hexagonal_close_packing_sampling(crystal_symmetry,
                                     symmetry_flags,
                                     point_distance,
                                     buffer_thickness,
                                     all_twelve_neighbors):
  cb_op_original_to_sampling = crystal_symmetry \
    .change_of_basis_op_to_reference_setting()
  point_group_type = crystal_symmetry.space_group().point_group_type()
  add_cb_op = {"2": "z,x,y",
               "m": "y,z,x"}.get(point_group_type, None)
  if (add_cb_op is not None):
    cb_op_original_to_sampling = sgtbx.change_of_basis_op(add_cb_op) \
                               * cb_op_original_to_sampling
  work_symmetry = crystal_symmetry.change_basis(cb_op_original_to_sampling)
  search_symmetry = sgtbx.search_symmetry(
    flags=symmetry_flags,
    space_group_type=work_symmetry.space_group_info().type(),
    seminvariant=work_symmetry.space_group_info().structure_seminvariant())
  expanded_symmetry = crystal.symmetry(
    unit_cell=work_symmetry.unit_cell(),
    space_group=search_symmetry.projected_group())
  rational_asu = expanded_symmetry.space_group_info().direct_space_asu()
  rational_asu.add_planes(
    normal_directions=search_symmetry.continuous_shifts(),
    both_directions=0001)
  sites_frac = hcp_fill_box(
    cb_op_original_to_sampling=cb_op_original_to_sampling,
    float_asu=rational_asu.define_metric(
      unit_cell=expanded_symmetry.unit_cell()).as_float_asu(),
    continuous_shift_flags=search_symmetry.continuous_shift_flags(),
    point_distance=point_distance,
    buffer_thickness=buffer_thickness,
    all_twelve_neighbors=all_twelve_neighbors)
  return crystal_symmetry.unit_cell().orthogonalization_matrix() * sites_frac

def check_distances(sites_cart, point_distance):
  asu_mappings = non_crystallographic_asu_mappings(sites_cart=sites_cart)
  distance_cutoff = point_distance * math.sqrt(2) * 0.99
  simple_pair_generator = crystal.neighbors_simple_pair_generator(
    asu_mappings=asu_mappings,
    distance_cutoff=distance_cutoff,
    full_matrix=0001)
  pair_generator = crystal.neighbors_fast_pair_generator(
    asu_mappings=asu_mappings,
    distance_cutoff=distance_cutoff,
    full_matrix=0001)
  assert simple_pair_generator.count_pairs() == pair_generator.count_pairs()
  pair_generator.restart()
  neighbors = {}
  for pair in pair_generator:
    assert approx_equal(pair.dist_sq, point_distance**2)
    neighbors[pair.i_seq] = neighbors.get(pair.i_seq, 0) + 1
  n_dict = {}
  for n in neighbors.values():
    n_dict[n] = n_dict.get(n, 0) + 1
  print n_dict
  if (len(neighbors) > 0):
    assert max(neighbors.values()) <= 12

def dump_pdb(file_name, crystal_symmetry, sites_cart):
  f = open(file_name, "w")
  print >> f, iotbx.pdb.format_cryst1_record(
    crystal_symmetry=crystal_symmetry)
  for serial,site in zip(count(1), sites_cart):
    print >> f, iotbx.pdb.format_atom_record(serial=serial, site=site)
  print >> f, "END"
  f.close()

def check_with_grid_tags(inp_symmetry, symmetry_flags,
                         sites_cart, point_distance,
                         strictly_inside, flag_write_pdb):
  cb_op_inp_ref = inp_symmetry.change_of_basis_op_to_reference_setting()
  print "cb_op_inp_ref.c():", cb_op_inp_ref.c()
  ref_symmetry = inp_symmetry.change_basis(cb_op_inp_ref)
  search_symmetry = sgtbx.search_symmetry(
    flags=symmetry_flags,
    space_group_type=ref_symmetry.space_group_info().type(),
    seminvariant=ref_symmetry.space_group_info().structure_seminvariant())
  assert search_symmetry.continuous_shifts_are_principal()
  continuous_shift_flags = search_symmetry.continuous_shift_flags()
  if (flag_write_pdb):
    tag_sites_frac = flex.vec3_double()
  else:
    tag_sites_frac = None
  if (strictly_inside):
    inp_tags = inp_symmetry.gridding(
      step=point_distance*.7,
      symmetry_flags=symmetry_flags).tags()
    if (tag_sites_frac is not None):
      for point in flex.nested_loop(inp_tags.n_real()):
        if (inp_tags.tags().tag_array()[point] < 0):
          point_frac_inp=[float(n)/d for n,d in zip(point, inp_tags.n_real())]
          tag_sites_frac.append(point_frac_inp)
    if (inp_tags.tags().n_independent() < sites_cart.size()):
      print "FAIL:", inp_symmetry.space_group_info(), \
                     inp_tags.tags().n_independent(), sites_cart.size()
      raise AssertionError
  else:
    inp_tags = inp_symmetry.gridding(
      step=point_distance/2.,
      symmetry_flags=symmetry_flags).tags()
    sites_frac_inp = inp_symmetry.unit_cell().fractionalization_matrix() \
                   * sites_cart
    rt = cb_op_inp_ref.c().as_double_array()
    sites_frac_ref = rt[:9] * sites_frac_inp
    sites_frac_ref += rt[9:]
    max_distance = 2 * ((.5 * math.sqrt(3) * point_distance) * 2/3.)
    print "max_distance:", max_distance
    for point in flex.nested_loop(inp_tags.n_real()):
      if (inp_tags.tags().tag_array()[point] < 0):
        point_frac_inp = [float(n)/d for n,d in zip(point, inp_tags.n_real())]
        if (tag_sites_frac is not None):
          tag_sites_frac.append(point_frac_inp)
        point_frac_ref = cb_op_inp_ref.c() * point_frac_inp
        equiv_points = sgtbx.sym_equiv_sites(
          unit_cell=ref_symmetry.unit_cell(),
          space_group=search_symmetry.group(),
          original_site=point_frac_ref,
          minimum_distance=2.e-6,
          tolerance=1.e-6)
        min_dist = sgtbx.min_sym_equiv_distance_info(
          reference_sites=equiv_points,
          others=sites_frac_ref,
          principal_continuous_allowed_origin_shift_flags
            =continuous_shift_flags).dist()
        if (min_dist > max_distance):
          print "FAIL:", inp_symmetry.space_group_info(), \
                         point_frac_ref, min_dist
          raise AssertionError
    if (inp_tags.tags().n_independent()+10 < sites_cart.size()):
      print "FAIL:", inp_symmetry.space_group_info(), \
                     inp_tags.tags().n_independent(), sites_cart.size()
      raise AssertionError
  if (tag_sites_frac is not None):
    dump_pdb(
      file_name="tag_sites.pdb",
      crystal_symmetry=inp_symmetry,
      sites_cart=inp_symmetry.unit_cell().orthogonalization_matrix()
                *tag_sites_frac)

def run_call_back(flags, space_group_info):
  crystal_symmetry = crystal.symmetry(
    unit_cell=space_group_info.any_compatible_unit_cell(volume=1000),
    space_group_info=space_group_info)
  print crystal_symmetry.unit_cell()
  symmetry_flags=sgtbx.search_symmetry_flags(
      use_space_group_symmetry=0001,
      use_space_group_ltr=0,
      use_seminvariant=0001,
      use_normalizer_k2l=00000,
      use_normalizer_l2n=00000)
  point_distance = 2
  buffer_thickness = -1
  all_twelve_neighbors = 00000
  if (flags.strictly_inside):
    buffer_thickness = 0
  if (flags.all_twelve_neighbors):
    all_twelve_neighbors = 0001
  print "buffer_thickness:", buffer_thickness
  print "all_twelve_neighbors:", all_twelve_neighbors
  sites_cart = hexagonal_close_packing_sampling(
    crystal_symmetry=crystal_symmetry,
    symmetry_flags=symmetry_flags,
    point_distance=point_distance,
    buffer_thickness=buffer_thickness,
    all_twelve_neighbors=all_twelve_neighbors)
  if (1):
    check_distances(sites_cart, point_distance)
  if (1):
    check_with_grid_tags(
      inp_symmetry=crystal_symmetry,
      symmetry_flags=symmetry_flags,
      sites_cart=sites_cart,
      point_distance=point_distance,
      strictly_inside=flags.strictly_inside,
      flag_write_pdb=flags.write_pdb)
  if (flags.write_pdb):
    dump_pdb("hex_sites.pdb", crystal_symmetry, sites_cart)

def exercise_all_twelve_neighbors():
  sites_cart = hexagonal_close_packing_sampling(
    crystal_symmetry=crystal.symmetry(
      unit_cell=(14.4225, 14.4225, 14.4225, 90, 90, 90),
      space_group_symbol="F m -3 m"),
    symmetry_flags=sgtbx.search_symmetry_flags(
      use_space_group_symmetry=0001,
      use_space_group_ltr=0,
      use_seminvariant=0001,
      use_normalizer_k2l=00000,
      use_normalizer_l2n=00000),
    point_distance=2,
    buffer_thickness=-1,
    all_twelve_neighbors=0001)
  assert len(sites_cart) == 37

def run():
  debug_utils.parse_options_loop_space_groups(sys.argv[1:], run_call_back, (
    "strictly_inside",
    "all_twelve_neighbors",
    "write_pdb"))
  exercise_all_twelve_neighbors()
  print "OK"

if (__name__ == "__main__"):
  run()
