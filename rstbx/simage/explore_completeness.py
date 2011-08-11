import libtbx
import sys

class stats_manager(libtbx.slots_getstate_setstate):

  __slots__ = [
    "n_indices",
    "asu_iselection",
    "use_symmetry",
    "completeness_history",
    "min_count_history",
    "counts",
    "currently_zero",
    "new_0"]

  def __init__(O, n_reserve, n_indices, asu_iselection, use_symmetry):
    from cctbx.array_family import flex
    O.n_indices = n_indices
    O.asu_iselection = asu_iselection
    O.use_symmetry = use_symmetry
    O.completeness_history = flex.double()
    O.completeness_history.reserve(n_reserve)
    O.completeness_history.append(0)
    O.min_count_history = flex.size_t()
    O.min_count_history.reserve(n_reserve)
    O.min_count_history.append(0)
    O.counts = flex.size_t(O.n_indices, 0)
    O.currently_zero = O.n_indices
    O.new_0 = None

  def update(O, miller_index_i_seqs):
    from cctbx.array_family import flex
    if (O.use_symmetry):
      isel = O.asu_iselection.select(miller_index_i_seqs)
    else:
      isel = miller_index_i_seqs
    previously_zero = O.counts.increment_and_track_up_from_zero(
      iselection=isel)
    O.new_0 = O.currently_zero - previously_zero
    O.completeness_history.append(1-O.new_0/O.n_indices)
    O.min_count_history.append(flex.min(O.counts))
    assert O.new_0 >= 0
    if (O.new_0 == 0 and O.currently_zero != 0):
      print "Complete with %d images." % (len(O.completeness_history)-1)
      print
    O.currently_zero = O.new_0

  def report(O, plot):
    from cctbx.array_family import flex
    print "Histogram of counts per reflection:"
    flex.histogram(O.counts.as_double(), n_slots=8).show(
      prefix="  ", format_cutoffs="%7.0f")
    print
    print "Observations per reflection:"
    flex.show_count_stats(counts=O.counts, prefix="  ")
    print "  Median:", int(flex.median(O.counts.as_double())+0.5)
    print
    sys.stdout.flush()
    def dump_xy(name, array):
      f = open("%s.xy" % name, "w")
      for i,c in enumerate(array):
        print >> f, i, c
    dump_xy("completeness_history", O.completeness_history)
    dump_xy("min_count_history", O.min_count_history)
    if (plot):
      from libtbx import pyplot
      fig = pyplot.figure()
      ax1 = fig.add_subplot(111)
      _ = O.completeness_history
      nx = _.size()
      ax1.plot(range(nx), _, "r-")
      ax1.axis([0, nx, 0, 1])
      ax2 = ax1.twinx()
      _ = O.min_count_history
      ax2.plot(range(_.size()), _, "b-")
      ax2.axis([0, nx, 0, max(1, flex.max(_))])
      pyplot.show()

def kirian_delta_vs_ewald_proximity(
      unit_cell,
      miller_indices,
      crystal_rotation_matrix,
      ewald_radius,
      d_min,
      detector_distance,
      detector_size,
      detector_pixels):
  from scitbx import matrix
  from libtbx.math_utils import nearest_integer
  cr = matrix.sqr(crystal_rotation_matrix)
  a_matrix = cr * matrix.sqr(unit_cell.fractionalization_matrix()).transpose()
  a_inv = a_matrix.inverse()
  dsx, dsy = detector_size
  dpx, dpy = detector_pixels
  deltas = [[] for _ in xrange(len(miller_indices))]
  h_lookup = {}
  for i,h in enumerate(miller_indices):
    h_lookup[h] = i
  for pi in xrange(dpx):
    for pj in xrange(dpy):
      cx = ((pi + 0.5) / dpx - 0.5) * dsx
      cy = ((pj + 0.5) / dpy - 0.5) * dsy
      lo = matrix.col((cx, cy, -detector_distance))
      ko = lo.normalize() * ewald_radius
      ki = matrix.col((0,0,-ewald_radius))
      dk = ki - ko
      h_frac = a_inv * dk
      h = matrix.col([nearest_integer(_) for _ in h_frac])
      if (h.elems == (0,0,0)):
        continue
      g_hkl = a_matrix * h
      delta = (dk - g_hkl).length()
      i = h_lookup.get(h.elems)
      if (i is None):
        assert unit_cell.d(h) < d_min
      else:
        deltas[i].append(delta)
  def ewald_proximity(h):
    rv = matrix.col(unit_cell.reciprocal_space_vector(h))
    rvr = cr * rv
    rvre = matrix.col((rvr[0], rvr[1], rvr[2]+ewald_radius))
    rvre_len = rvre.length()
    return abs(1 - rvre_len / ewald_radius)
  def write_xy():
    fn_xy = "kirian_delta_vs_ewald_proximity.xy"
    print "Writing file:", fn_xy
    f = open(fn_xy, "w")
    print >> f, """\
@with g0
@ s0 symbol 1
@ s0 symbol size 0.1
@ s0 line type 0"""
    for h, ds in zip(miller_indices, deltas):
      if (len(ds) != 0):
        print >> f, min(ds), ewald_proximity(h)
    print >> f, "&"
    print
  write_xy()
  STOP()

def simulate(work_params, i_calc, asu_iselection):
  from rstbx.simage import image_simple
  from cctbx.array_family import flex
  if (not work_params.use_symmetry):
    n_indices = i_calc.indices().size()
  else:
    n_indices = flex.max(asu_iselection)+1
  n_shots = work_params.number_of_shots
  mc_target = work_params.min_count_target
  stats = stats_manager(
    n_reserve=max(n_shots, 1000000),
    n_indices=n_indices,
    asu_iselection=asu_iselection,
    use_symmetry=work_params.use_symmetry)
  def update_stats(miller_index_i_seqs):
    stats.update(miller_index_i_seqs)
    if (n_shots is not None and stats.min_count_history.size()-1 < n_shots):
      return False
    if (mc_target is not None and stats.min_count_history[-1] < mc_target):
      return False
    if (stats.new_0 != 0 and n_shots is None and mc_target is None):
      return False
    return True
  def get_miller_index_i_seqs(i_img, parallel=True):
    mt = flex.mersenne_twister(seed=work_params.noise.random_seed+i_img)
    crystal_rotation = mt.random_double_r3_rotation_matrix_arvo_1992()
    if (work_params.kirian_delta_vs_ewald_proximity):
      kirian_delta_vs_ewald_proximity(
        unit_cell=i_calc.unit_cell(),
        miller_indices=i_calc.indices(),
        crystal_rotation_matrix=crystal_rotation,
        ewald_radius=1/work_params.wavelength,
        d_min=work_params.d_min,
        detector_distance=work_params.detector.distance,
        detector_size=work_params.detector.size,
        detector_pixels=work_params.detector.pixels)
    img = image_simple(
        store_miller_index_i_seqs=True,
        store_signals=True).compute(
      unit_cell=i_calc.unit_cell(),
      miller_indices=i_calc.indices(),
      spot_intensity_factors=None,
      crystal_rotation_matrix=crystal_rotation,
      ewald_radius=1/work_params.wavelength,
      ewald_proximity=work_params.ewald_proximity,
      signal_max=1,
      detector_distance=work_params.detector.distance,
      detector_size=work_params.detector.size,
      detector_pixels=work_params.detector.pixels,
      point_spread=work_params.point_spread,
      gaussian_falloff_scale=work_params.gaussian_falloff_scale)
    result = img.miller_index_i_seqs
    if (work_params.usable_partiality_threshold is not None):
      result = result.select(
        img.signals > work_params.usable_partiality_threshold)
    if (parallel):
      return result.copy_to_byte_str()
    return result
  i_img = 0
  stop = False
  if (not work_params.multiprocessing):
    while (not stop):
      miller_index_i_seqs = get_miller_index_i_seqs(i_img, parallel=False)
      i_img += 1
      stop = update_stats(miller_index_i_seqs)
  else:
    from libtbx import easy_mp
    pool = easy_mp.Pool(fixed_func=get_miller_index_i_seqs)
    try:
      print "multiprocessing pool size:", pool.processes
      print
      sys.stdout.flush()
      while (not stop):
        next_i_img = i_img + pool.processes
        args = range(i_img, next_i_img)
        mp_results = pool.map_fixed_func(iterable=args)
        i_img = next_i_img
        for miller_index_i_seqs in mp_results:
          assert miller_index_i_seqs is not None
          miller_index_i_seqs = flex.size_t_from_byte_str(
            byte_str=miller_index_i_seqs)
          stop = update_stats(miller_index_i_seqs)
          if (stop):
            break
    finally:
      pool.close()
      pool.join()
  return stats

def run(args):
  from libtbx.utils import show_times_at_exit
  show_times_at_exit()
  from rstbx.simage import create
  work_params = create.process_args(
    args=args,
    extra_phil_str="""\
use_symmetry = False
  .type = bool
number_of_shots = None
  .type = int
min_count_target = None
  .type = int
usable_partiality_threshold = 0.1
  .type = float
kirian_delta_vs_ewald_proximity = False
  .type = bool
multiprocessing = False
  .type = bool
plot = False
  .type = bool
""")
  i_calc, asu_iselection = create.build_i_calc(work_params)
  i_calc.show_comprehensive_summary()
  print
  sys.stdout.flush()
  stats = simulate(work_params, i_calc, asu_iselection)
  stats.report(plot=work_params.plot)
