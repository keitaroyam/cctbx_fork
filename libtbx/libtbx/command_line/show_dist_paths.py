import libtbx.load_env
import sys
if (len(sys.argv) == 1):
  for path in libtbx.env.dist_paths():
    print path
else:
  for arg in sys.argv[1:]:
    print libtbx.env.dist_path(arg, None)
