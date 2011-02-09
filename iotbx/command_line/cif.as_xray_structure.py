from cctbx import xray
from libtbx import easy_pickle
from libtbx.str_utils import show_string
import sys, os
op = os.path

def run(args):
  for f in args:
    try:
      xs = xray.structure.from_cif(file_path=f)
    except KeyboardInterrupt:
      raise
    except Exception, e:
      print "Error extracting xray structure from file: %s:" % (
        show_string(f))
      print " ", str(e)
      continue
    xs.show_summary()
    r, _ = op.splitext(op.basename(f))
    easy_pickle.dump(file_name=r+'_xray_structure.pickle', obj=xs)

if (__name__ == "__main__"):
  import sys
  run(args=sys.argv[1:])
