from cctbx import statistics
from cctbx import adptbx
from cctbx.development import random_structure
from cctbx.development import debug_utils
from scitbx.python_utils import dicts
import sys, os

def exercise(space_group_info, anomalous_flag,
             d_min=1.0, reflections_per_bin=200, n_bins=10, verbose=0):
  elements = ("N", "C", "C", "O") * 5
  structure_factors = random_structure.xray_structure(
    space_group_info,
    elements=elements,
    volume_per_atom=50.,
    min_distance=1.5,
    general_positions_only=True,
    anisotropic_flag=False,
    random_u_iso=False,
    u_iso=adptbx.b_as_u(10),
    random_occupancy=False
    ).structure_factors_direct(
        anomalous_flag=anomalous_flag, d_min=d_min)
  if (0 or verbose):
    structure_factors.xray_structure().show_summary()
  f_obs_array = abs(structure_factors.f_calc_array())
  f_obs_array.setup_binner(
    auto_binning=True,
    reflections_per_bin=reflections_per_bin,
    n_bins=n_bins)
  if (0 or verbose):
    f_obs_array.binner().show_summary()
  asu_contents = dicts.with_default_value(0)
  for elem in elements: asu_contents[elem] += 1
  wp = statistics.wilson_plot(f_obs_array, asu_contents)
  if (1 or verbose):
    print "wilson_k, wilson_b:", wp.wilson_k, wp.wilson_b
  assert 0.6 < wp.wilson_k < 1.4
  assert 9 < wp.wilson_b < 11
  assert wp.xy_plot_info().fit_cc == wp.fit_cc

def run_call_back(flags, space_group_info):
  for anomalous_flag in (False, True):
    exercise(space_group_info, anomalous_flag, verbose=flags.Verbose)

def run():
  debug_utils.parse_options_loop_space_groups(sys.argv[1:], run_call_back)

if (__name__ == "__main__"):
  run()
  t = os.times()
  print "u+s,u,s: %.2f %.2f %.2f" % (t[0] + t[1], t[0], t[1])
