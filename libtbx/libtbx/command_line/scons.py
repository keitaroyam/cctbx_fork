import sys, os

dist_root = os.environ["LIBTBX_DIST_ROOT"]
engine = os.path.normpath(os.path.join(dist_root, "scons/engine"))
if (not os.path.isdir(engine)):
  engine = os.path.normpath(os.path.join(dist_root, "scons/src/engine"))
sys.path.insert(0, engine)
try: import SCons
except: del sys.path[0]

def show_times():
  t = os.times()
  usr_plus_sys = t[0] + t[1]
  try: ticks = sys.gettickeraccumulation()
  except: ticks = None
  s = "usr+sys time: %.2f" % usr_plus_sys
  if (ticks is not None):
    s += ", ticks: %d" % ticks
    if (ticks != 0):
      s += ", micro-seconds/tick: %.3f" % (usr_plus_sys*1.e6/ticks)
  print s

import atexit
atexit.register(show_times)

from SCons import Script
Script.main()
