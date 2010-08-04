import boost.python
boost.python.import_ext("spotfinder_distltbx_ext")
from spotfinder_distltbx_ext import *
import spotfinder_distltbx_ext as ext
boost.python.import_ext("spotfinder_hough_ext")
from spotfinder_hough_ext import *
from libtbx import adopt_init_args
from libtbx.utils import Sorry

class Distl(w_Distl):

  def __init__(self,options,image,pd,report_overloads=False,params=None):
    w_Distl.__init__(self,options,report_overloads)
    adopt_init_args(self, locals())

    try:    saturation = image.saturation
    except: saturation = 65535
    self.setspotimg(image.pixel_size, image.distance, image.wavelength,
                    float(pd['xbeam']),float(pd['ybeam']),image.rawdata,
                    saturation)
    #Fixes a longstanding gremlin:  my corrected xy must be propagated
    # to zepu's code; or else ice rings are treated incorrectly.

    #Setup tiling, if any.
    self.set_tiling(image.vendortype)

    self.deprecation_warnings()
    if params!=None:
        if params.distl.minimum_spot_area != None:
          self.set_minimum_spot_area(params.distl.minimum_spot_area)
        if params.distl.minimum_signal_height != None:
          self.set_minimum_signal_height(params.distl.minimum_signal_height)
        if params.distl.minimum_spot_height != None:
          self.set_minimum_spot_height(params.distl.minimum_spot_height)
        if params.distl.spot_area_maximum_factor != None:
          self.set_spot_area_maximum_factor(params.distl.spot_area_maximum_factor)
    self.parameter_guarantees()

    self.get_underload()
    try:
      self.pxlclassify()
    except Exception, e:
      if str(e).find("cannot distinguish signal")>0: print e
      else: raise e
    self.search_icerings()
    self.search_maximas()
    self.search_spots()
    self.search_overloadpatches()
    self.finish_analysis()

  def deprecation_warnings(self):
    """Eventually migrate away from dataset_preferences.py mechanism, toward
    100% use of phil for specifying parameters.  For now, simply guard against
    specifying a given parameter by both mechanisms."""

    template = "%s on the command line and %s parameter (%s) of dataset_preferences.py file specify the same thing."

    # spotarealowcut <==> -s2 <==> minimum_spot_area
    if self.params.distl.minimum_spot_area != None:
      if self.options.find("-s2") >= 0:
        raise Sorry( (template%("minimum_spot_area (%d)","-s2",self.options)%(
        self.params.distl.minimum_spot_area,)) )

    if self.params.distl.minimum_signal_height != None:
      template1 = template%("minimum_signal_height (%.2f)","-bg%1d",self.options)

      # bgupperint <==> -bg0 <==> minimum_signal_height
      if self.options.find("-bg0") >= 0:
        raise Sorry( (template1%(self.params.distl.minimum_signal_height,0)) )

      # bgupperint <==> -bg1 <==> minimum_signal_height
      if self.options.find("-bg1") >= 0:
        raise Sorry( (template1%(self.params.distl.minimum_signal_height,1)) )

      # bgupperint <==> -bg2 <==> minimum_signal_height
      if self.options.find("-bg2") >= 0:
        raise Sorry( (template1%(self.params.distl.minimum_signal_height,2)) )

    # difflowerint <==> -d1 <==> minimum_spot_height
    if self.params.distl.minimum_spot_height != None:
      if self.options.find("-d1") >= 0:
        raise Sorry( (template%("minimum_spot_height (%.2f)","-d1",self.options)%(
        self.params.distl.minimum_spot_height,)) )

    # apotareamaxfactor <==> -s7 <==> spot_area_maximum_factor
    if self.params.distl.spot_area_maximum_factor != None:
      if self.options.find("-s7") >= 0:
        raise Sorry( (template%("spot_area_maximum_factor (%.2f)","-s7",self.options)%(
        self.params.distl.spot_area_maximum_factor,)) )

class _SpotFilterAgent(boost.python.injector, SpotFilterAgent):
  def __getinitargs__(self):
    return (self.pixel_size, self.xbeam, self.ybeam, self.distance,
            self.wavelength, self.icerings)
