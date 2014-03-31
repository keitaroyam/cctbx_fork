from __future__ import division
# LIBTBX_SET_DISPATCHER_NAME cxi.image2pickle

# Convert images of any extant format to pickle files suitable for processing with
# cxi.index.  Note, oscillation values are not preserved.

import dxtbx, sys, os
from xfel.cxi.cspad_ana.cspad_tbx import dpack
from libtbx import easy_pickle
from libtbx.utils import Usage

def run(argv=None):
  if argv is None:
    argv = sys.argv[1:]

  if len(argv) == 0:
    raise Usage("cxi.image2pickle image1 image2...\nConverts images of any extant format to pickle files suitable for processing with cxi.index. Note, oscillation values are not preserved.")

  for imgpath in argv:
    destpath = os.path.join(os.path.dirname(imgpath), os.path.splitext(os.path.basename(imgpath))[0] + ".pickle")

    img = dxtbx.load(imgpath)
    detector = img.get_detector()[0]
    beam = img.get_beam()
    beam_center = detector.get_beam_centre(beam.get_s0())

    data = dpack(data=img.get_raw_data(),
                 distance=detector.get_distance(),
                 pixel_size=detector.get_pixel_size()[0],
                 wavelength=beam.get_wavelength(),
                 beam_center_x=beam_center[0],
                 beam_center_y=beam_center[1],
                 ccd_image_saturation=detector.get_trusted_range()[1],
                 saturated_value=detector.get_trusted_range()[1]
                 )

    easy_pickle.dump(destpath, data)


if (__name__ == "__main__") :
  run(sys.argv[1:])