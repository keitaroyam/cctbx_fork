# LIBTBX_SET_DISPATCHER_NAME phenix.data_viewer
# LIBTBX_PRE_DISPATCHER_INCLUDE_SH PHENIX_GUI_ENVIRONMENT=1
# LIBTBX_PRE_DISPATCHER_INCLUDE_SH export PHENIX_GUI_ENVIRONMENT

from crys3d.hklview import master_phil
from crys3d.hklview.frames import *
import os
import sys

def run (args) :
  ma = None
  hkl_file = None
  user_phil = []
  if (len(args) == 0) :
    from cctbx import miller, crystal
    from cctbx.array_family import flex
    xs = crystal.symmetry((3,3,5,90,90,120), "P6")
    mi = flex.miller_index([
      (0,0,1),(0,0,2),(0,0,3),
      (0,1,0),(0,2,0),(0,3,0),
      (1,1,0),(1,2,0),(1,3,0)])
    d = flex.double([1.0, 2.0, 3.0, 5.0, 10.0, 15.0, 6.0, 9.0, 12.0])
    s = miller.set(xs, mi, anomalous_flag=False)
    ma = s.array(data=d).set_info("test")
  else :
    for arg in args :
      if os.path.isfile(arg) :
        hkl_file = arg
      else :
        try :
          arg_phil = libtbx.phil.parse(arg)
        except RuntimeError :
          print "unrecognizeable argument '%s'" % arg
        else :
          user_phil.append(arg_phil)
  working_phil = master_phil.fetch(sources=user_phil)
  settings = working_phil.extract()
  a = wx.App(0)
  a.hklview_settings = settings
  f = HKLViewFrame(None, -1, "Reflection data viewer", size=(1024,768))
  f.Show()
  if (ma is not None) :
    f.set_miller_array(ma)
  elif (hkl_file is not None) :
    f.load_reflections_file(hkl_file)
  else :
    f.OnLoadFile(None)
  a.MainLoop()

if (__name__ == "__main__") :
  run(sys.argv[1:])
