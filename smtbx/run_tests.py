from __future__ import division
from libtbx import test_utils
import libtbx.load_env

import smtbx.refinement.constraints.run_tests as constraint_tests

tst_list = (
    ["$D/absolute_structure/tests/tst_absolute_structure.py",
     "--fix_random_seeds"],
    "$D/ab_initio/tests/tst_ab_initio_ext.py",
    ["$D/ab_initio/tests/tst_charge_flipping.py", '--fix_seed', '--on=E',
     '"hall: P 1"', '"hall: P 3"', '"hall: -P 2ybc"' ],
    "$D/masks/tests/tst_masks.py",
    "$D/structure_factors/direct/tests/tst_standard_xray.py",
    #["$D/refinement/tests/tst_least_squares.py", "--fix_random_seeds"],
    ["$D/refinement/tests/tst_weighting_schemes.py",
     "--fix_random_seeds"],
    "$D/refinement/restraints/tests/tst_adp_restraints.py",
    "$D/refinement/restraints/tests/tst_manager.py",
    ["$D/refinement/restraints/tests/tst_restraints.py",
     '--verbose', '--scatterers=5', '--resolution=0.2'],
    "$D/tests/tst_utils.py",
    )

def run():
  constraint_tests.run()

  build_dir = libtbx.env.under_build("smtbx")
  dist_dir = libtbx.env.dist_path("smtbx")
  test_utils.run_tests(build_dir, dist_dir, tst_list)

if __name__ == '__main__':
  run()
