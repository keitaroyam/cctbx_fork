from __future__ import division
# -*- Mode: Python; c-basic-offset: 2; indent-tabs-mode: nil; tab-width: 8 -*-
#
# LIBTBX_SET_DISPATCHER_NAME cctbx.image_viewer
# LIBTBX_PRE_DISPATCHER_INCLUDE_SH export PHENIX_GUI_ENVIRONMENT=1
# LIBTBX_PRE_DISPATCHER_INCLUDE_SH export BOOST_ADAPTBX_FPE_DEFAULT=1
#
# $Id$

import os
import sys
import wx

from rstbx.slip_viewer.frame import XrayFrame
from libtbx import phil
from spotfinder import phil_str
from spotfinder.command_line.signal_strength import additional_spotfinder_phil_defs

master_str="""
anti_aliasing = False
  .type = bool
  .help = "Enable anti-aliasing"
effective_metrology = None
  .type = path
  .help = "Read effective metrology from PATH"
beam_center = True
  .type = bool
  .help = "Mark beam center"
show_integration_results = False
  .type = bool
  .help = "Show integration results"
show_spotfinder_results = False
  .type = bool
  .help = "Show spotfinder results"
show_effective_tiling = False
  .type = bool
  .help = "Show the effective tiling of the detector"
"""

def run(argv=None):
  if (argv is None):
    argv = sys.argv

  # XXX Could/should handle effective metrology the same way, except
  # it does not have a single scope.
  work_phil = phil.process_command_line(
    args=argv[1:],
    master_string=master_str + phil_str + additional_spotfinder_phil_defs)
  work_params = work_phil.work.extract()

  app = wx.App(0)
  wx.SystemOptions.SetOptionInt("osx.openfiledialog.always-show-types", 1)
  frame = XrayFrame(None, -1, "X-ray image display", size=(800,720))

  # Update initial settings with values from the command line.  Needs
  # to be done before image is loaded (but after the frame is
  # instantiated).
  frame.params = work_params
  frame.pyslip.tiles.user_requests_antialiasing = work_params.anti_aliasing

  frame.settings_frame.panel.center_ctrl.SetValue(
    work_params.beam_center)
  frame.settings_frame.panel.integ_ctrl.SetValue(
    work_params.show_integration_results)
  frame.settings_frame.panel.spots_ctrl.SetValue(
    work_params.show_spotfinder_results)
  frame.settings.show_effective_tiling = work_params.show_effective_tiling
  frame.settings_frame.panel.collect_values()

  if (work_params.effective_metrology is not None):
    from xfel.cftbx.detector.metrology2phil import master_phil
    from xfel.cftbx.detector.metrology import metrology_as_transformation_matrices

    stream = open(work_params.effective_metrology)
    metrology_phil = master_phil.fetch(sources=[phil.parse(stream.read())])
    stream.close()
    frame.metrology_matrices = metrology_as_transformation_matrices(
      metrology_phil.extract())

  paths = work_phil.remaining_args
  if (len(paths) == 1 and os.path.basename(paths[0]) == "DISTL_pickle"):
    assert os.path.isfile(paths[0])
    frame.load_distl_output(paths[0])
  elif (len(paths) > 0):
    for path in paths:
      assert os.path.isfile(path)
      frame.add_file_name_or_data(path)
    frame.load_image(paths[0])

  frame.Show()
  app.MainLoop()

  return 0


if (__name__ == "__main__"):
  sys.exit(run())
