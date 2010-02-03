from libtbx import test_utils
import libtbx.load_env

def run():
  tst_list = (
    "$D/masks/tests/tst_masks.py",
    "$D/ab_initio/tests/tst_ab_initio_ext.py",
    "$D/ab_initio/tests/tst_charge_flipping.py",
    "$D/structure_factors/direct/tests/tst_standard_xray.py",
    "$D/refinement/tests/tst_minimization.py",
    #"$D/refinement/tests/tst_least_squares.py",
    "$D/refinement/constraints/tests/tst_constraints.py",
    "$D/refinement/restraints/tests/tst_adp_restraints.py",
    "$D/refinement/restraints/tests/tst_manager.py",
    #"$D/refinement/tests/tst_minimization_at_random.py",
    )
  build_dir = libtbx.env.under_build("smtbx")
  dist_dir = libtbx.env.dist_path("smtbx")
  test_utils.run_tests(build_dir, dist_dir, tst_list)

if __name__ == '__main__':
  run()
