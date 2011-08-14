# LIBTBX_SET_DISPATCHER_NAME phenix.image_viewer
# LIBTBX_PRE_DISPATCHER_INCLUDE_SH PHENIX_GUI_ENVIRONMENT=1
# LIBTBX_PRE_DISPATCHER_INCLUDE_SH export PHENIX_GUI_ENVIRONMENT

from wxtbx.xray_viewer.frame import XrayFrame
import wx
import os
import sys

def run (args) :
  file_name = args[0]
  assert os.path.isfile(file_name)
  app = wx.App(0)
  frame = XrayFrame(None, -1, "X-ray image display", size=(800,720))
  if (os.path.basename(file_name) == "DISTL_pickle") :
    frame.load_distl_output(file_name)
  else :
    frame.load_image(file_name)
  frame.Show()
  app.MainLoop()

if (__name__ == "__main__") :
  run(sys.argv[1:])
