from libtbx import test_utils
import libtbx.env

def run():
  tst_list = (
  "$B/examples/getting_started",
  "$D/cctbx/examples/getting_started.py",
  "$D/cctbx/examples/analyze_adp.py",
  ["$D/cctbx/examples/all_axes.py", "P31"],
  ["$D/cctbx/examples/tst_phase_o_phrenia.py", "P2"],
  "$D/cctbx/examples/map_skewness.py",
  )

  build_dir = libtbx.env.under_build("cctbx")
  dist_dir = libtbx.env.dist_path("cctbx")

  test_utils.run_tests(build_dir, dist_dir, tst_list)

if (__name__ == "__main__"):
  run()
