from __future__ import division
#-*- Mode: Python; c-basic-offset: 2; indent-tabs-mode: nil; tab-width: 8 -*-
#
# LIBTBX_SET_DISPATCHER_NAME cxi.print_pickle
#

"""
Simple utility for printing the contents of a cctbx.xfel pickle file
"""

from libtbx import easy_pickle
import sys, os
from xfel.detector_formats import detector_format_version as detector_format_function
from xfel.detector_formats import reverse_timestamp
from cctbx import sgtbx # import dependency
from cctbx.array_family import flex

args = sys.argv[1:]
if "--break" in args:
  args.remove("--break")
  dobreak = True
else:
  dobreak = False

if "--plots" in args:
  args.remove("--plots")
  doplots = True
else:
  doplots = False


for path in args:
  if not os.path.isfile(path):
    print "Not a file:", path
    continue

  data = easy_pickle.load(path)
  if not isinstance(data, dict):
    print "Not a dictionary pickle"
    continue

  print "Printing contents of", path

  if data.has_key('TIMESTAMP'):
    # this is how FormatPYunspecified guesses the address
    if not "DETECTOR_ADDRESS" in data:
      # legacy format; try to guess the address
      LCLS_detector_address = 'CxiDs1-0|Cspad-0'
      if "DISTANCE" in data and data["DISTANCE"] > 1000:
        # downstream CS-PAD detector station of CXI instrument
        LCLS_detector_address = 'CxiDsd-0|Cspad-0'
    else:
      LCLS_detector_address = data["DETECTOR_ADDRESS"]

    detector_format_version = detector_format_function(
      LCLS_detector_address, reverse_timestamp(data['TIMESTAMP'])[0])
    print "Detector format version:", detector_format_version
    image_pickle = True
  else:
    print "Not an image pickle"
    image_pickle = False

  for key in data:
    if key == 'ACTIVE_AREAS':
      print int(len(data[key])/4), "active areas, first one: ", list(data[key][0:4])
    elif key == 'observations':
      print key, data[key], "Showing unit cell/spacegroup:"
      obs = data[key][0]
      uc = obs.unit_cell()
      uc.show_parameters()
      obs.space_group().info().show_summary()
      d = uc.d(obs.indices())
      print "Number of observations:", len(obs.indices())
      print "Max resolution: %f"%flex.min(d)
      print "Mean I/sigma:", flex.mean(obs.data())/flex.mean(obs.sigmas())
      print "I/sigma > 1 count:", (obs.data()/obs.sigmas() > 1).count(True)
      print "I <= 0:", len(obs.data().select(obs.data() <= 0))

    elif key == 'mapped_predictions':
      print key, data[key][0][0], "(only first shown of %d)"%len(data[key][0])
    elif key == 'correction_vectors' and data[key] is not None and data[key][0] is not None:
      if data[key][0] is None:
        print key, "None"
      else:
        print key, data[key][0][0], "(only first shown)"
    elif key == "DATA":
      print key,"len=%d max=%f min=%f dimensions=%s"%(data[key].size(),flex.max(data[key]),flex.min(data[key]),str(data[key].focus()))
    elif key == "WAVELENGTH":
      print "WAVELENGTH", data[key], ", converted to eV:", 12398.4187/data[key]
    elif key == "applied_absorption_correction":
      print key, data[key]
      if doplots:
        c = data[key][0]
        hist = flex.histogram(c, n_slots=30)
        from matplotlib import pyplot as plt
        plt.scatter(hist.slot_centers(), hist.slots())
        plt.show()

        obs = data['observations'][0]
        preds = data['mapped_predictions'][0]
        p1 = preds.select(c == 1.0)
        p2 = preds.select((c != 1.0) & (c <= 1.5))
        plt.scatter(preds.parts()[1], preds.parts()[0], c='g')
        plt.scatter(p1.parts()[1], p1.parts()[0], c='b')
        plt.scatter(p2.parts()[1], p2.parts()[0], c='r')
        plt.show()

    else:
      print key, data[key]

  if image_pickle:
    import dxtbx
    image = dxtbx.load(path)
    tile_manager = image.detectorbase.get_tile_manager(image.detectorbase.horizons_phil_cache)
    tiling = tile_manager.effective_tiling_as_flex_int(reapply_peripheral_margin = True)
    print int(len(tiling)/4), "translated active areas, first one: ", list(tiling[0:4])

  if dobreak:
    print "Entering break. The pickle is loaded in the variable 'data'"
    try:
      from IPython import embed
    except ImportError:
      import pdb; pdb.set_trace()
    else:
      embed()
