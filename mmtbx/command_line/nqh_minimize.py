
from __future__ import division
import sys
from mmtbx.validation.molprobity import nqh_minimize

if __name__ == "__main__":
  nqh_minimize.run(sys.argv[1:])
