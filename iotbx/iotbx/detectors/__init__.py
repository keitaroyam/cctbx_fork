from scitbx.array_family import flex

import boost.python
ext = boost.python.import_ext("iotbx_detectors_ext")
from iotbx_detectors_ext import *

import exceptions
from iotbx.detectors.adsc import ADSCImage
from iotbx.detectors.mar import MARImage
from iotbx.detectors.marIP import MARIPImage
from iotbx.detectors.raxis import RAXISImage
from iotbx.detectors.raxis_nonsquare import NonSquareRAXISImage
from iotbx.detectors.macscience import DIPImage
from iotbx.detectors.saturn import SaturnImage

class ImageException(exceptions.Exception):
  def __init__(self,string):
    self.message = string
  def __str__(self): return self.message

all_image_types = [SaturnImage,DIPImage,ADSCImage,
                  MARImage,MARIPImage,RAXISImage,
                  NonSquareRAXISImage]

def ImageFactory(filename):
  for itype in all_image_types:
    try:
      I = itype(filename)
      I.readHeader()
      if itype==RAXISImage:
        assert I.head['sizeFast']==I.head['sizeSlow']
      return I
    except:
      pass
  raise ImageException(filename+" not recognized as any known detector image type")
