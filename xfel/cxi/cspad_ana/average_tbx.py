from __future__ import division
# -*- Mode: Python; c-basic-offset: 2; indent-tabs-mode: nil; tab-width: 8 -*-
#
# $Id$

import math
import multiprocessing
import numpy

from libtbx import easy_pickle
from scitbx.array_family import flex
import scitbx.math
from xfel.cxi.cspad_ana import common_mode
from xfel.cxi.cspad_ana import cspad_tbx


class average_mixin(common_mode.common_mode_correction):

  sum_img = None
  sumsq_img = None
  sum_distance = None
  sum_wavelength = None

  def __init__(self,
               address,
               avg_dirname=None,
               avg_basename=None,
               stddev_dirname=None,
               stddev_basename=None,
               background_path=None,
               flags=None,
               hot_threshold=None,
               gain_threshold=None,
               noise_threshold=7,
               elastic_threshold=9,
               symnoise_threshold=4,
               n=None,
               **kwds):
    """
    @param address         Address string XXX Que?!
    @param avg_dirname     Directory portion of output average image
                           XXX mean, mu?
    @param avg_basename    Filename prefix of output average image XXX
                           mean, mu?
    @param flags inactive:  Eliminate the inactive pixels
                 noelastic: Eliminate elastic scattering
                 nohot:     Eliminate the hot pixels
                 nonoise:   Eliminate noisy pixels
                 symnoise:  Symmetrically eliminate noisy pixels
    @param n     The number of shots to process, or as many as
                 possible if undefined XXX Sort of redundant with
                 pyana
    @param stddev_dirname  Directory portion of output standard
                           deviation image XXX sigma?
    @param stddev_basename Filename prefix of output standard
                           deviation image XXX sigma?
    """

    super(average_mixin, self).__init__(
      address=address,
      **kwds
    )
    self.roi = None
    self.avg_basename = cspad_tbx.getOptString(avg_basename)
    self.avg_dirname = cspad_tbx.getOptString(avg_dirname)
    self.flags = cspad_tbx.getOptStrings(flags, default = [])
    self.nmemb_max = cspad_tbx.getOptInteger(n)
    self.stddev_basename = cspad_tbx.getOptString(stddev_basename)
    self.stddev_dirname = cspad_tbx.getOptString(stddev_dirname)
    self.background_path = cspad_tbx.getOptString(background_path)
    self.hot_threshold = cspad_tbx.getOptFloat(hot_threshold)
    self.gain_threshold = cspad_tbx.getOptFloat(gain_threshold)
    self.noise_threshold = cspad_tbx.getOptFloat(noise_threshold)
    self.elastic_threshold = cspad_tbx.getOptFloat(elastic_threshold)
    self.symnoise_threshold = cspad_tbx.getOptFloat(symnoise_threshold)

    if self.dark_img is not None and self.hot_threshold is not None:
      self.hot_threshold *= flex.median(self.dark_img.as_1d())
      self.logger.info("HOT THRESHOLD: %.2f" %self.hot_threshold)
      self.logger.info("Number of pixels above hot threshold: %i" %(
        self.dark_img > self.hot_threshold).count(True))

    if background_path is not None:
      background_dict = easy_pickle.load(background_path)
      self.background_img = background_dict['DATA']

    # Initialise all totals to zero.  self._tot_peers is a bit field
    # where a bit is set if the partial sum from the corresponding
    # worker process is pending.  XXX Hardcoding the detector size is
    # not nice.
    self._tot_lock = multiprocessing.Lock()

    self._tot_distance = multiprocessing.Value('d', 0, lock=False)
    self._tot_nfail = multiprocessing.Value('L', 0, lock=False)
    self._tot_nmemb = multiprocessing.Value('L', 0, lock=False)
    self._tot_peers = multiprocessing.Value('L', 0, lock=False)
    self._tot_wavelength = multiprocessing.Value('d', 0, lock=False)

    if address == 'Camp-0|pnCCD-0' or address == 'Camp-0|pnCCD-1':
      self._tot_sum = multiprocessing.Array('d', 1024 * 1024, lock=False)
      self._tot_ssq = multiprocessing.Array('d', 1024 * 1024, lock=False)
    elif address == 'CxiDs1-0|Cspad-0':
      self._tot_sum = multiprocessing.Array('d', 1765 * 1765, lock=False)
      self._tot_ssq = multiprocessing.Array('d', 1765 * 1765, lock=False)
    elif address == 'CxiDsd-0|Cspad-0':
      self._tot_sum = multiprocessing.Array('d', 1765 * 1765, lock=False)
      self._tot_ssq = multiprocessing.Array('d', 1765 * 1765, lock=False)
    elif address == 'CxiSc1-0|Cspad2x2-0':
      self._tot_sum = multiprocessing.Array('d', 370 * 391, lock=False)
      self._tot_ssq = multiprocessing.Array('d', 370 * 391, lock=False)
    else:
      raise RuntimeError("Unsupported detector address")


  def event(self, evt, env):
    """The event() function is called for every L1Accept transition.
    Once self.nmemb_max shots are accumulated, this function turns
    into a nop.

    @param evt Event data object, a configure object
    @param env Environment object
    """

    super(average_mixin, self).event(evt, env)
    if (evt.get("skip_event")):
      return

    if (self.nmemb_max is not None and self.nmemb >= self.nmemb_max):
      return

    if ("skew" in self.flags):
      # Take out inactive pixels
      if self.roi is not None:
        pixels = self.cspad_img[self.roi[2]:self.roi[3], self.roi[0]:self.roi[1]]
        dark_mask = self.dark_mask[self.roi[2]:self.roi[3], self.roi[0]:self.roi[1]]
        pixels = pixels.as_1d().select(dark_mask.as_1d())
      else:
        pixels = self.cspad_img.as_1d().select(self.dark_mask.as_1d()).as_double()
      stats = scitbx.math.basic_statistics(pixels.as_double())
      #stats.show()
      self.logger.info("skew: %.3f" %stats.skew)
      self.logger.info("kurtosis: %.3f" %stats.kurtosis)
      if 0:
        from matplotlib import pyplot
        hist_min, hist_max = flex.min(flex_cspad_img.as_double()), flex.max(flex_cspad_img.as_double())
        print hist_min, hist_max
        n_slots = 100
        n, bins, patches = pyplot.hist(flex_cspad_img.as_1d().as_numpy_array(), bins=n_slots, range=(hist_min, hist_max))
        pyplot.show()

      # XXX This skew threshold probably needs fine-tuning
      skew_threshold = 0.35
      if stats.skew < skew_threshold:
        self.nfail += 1
        self.logger.warning("event(): skew < %f, shot skipped" % skew_threshold)
        evt.put(True, "skip_event")
        return
      #self.cspad_img *= stats.skew

    if ("inactive" in self.flags):
      self.cspad_img.set_selected(self.dark_stddev <= 0, 0)

    if ("noelastic" in self.flags):
      ELASTIC_THRESHOLD = self.elastic_threshold
      self.cspad_img.set_selected(self.cspad_img > ELASTIC_THRESHOLD, 0)

    if self.hot_threshold is not None:
      HOT_THRESHOLD = self.hot_threshold
      self.cspad_img.set_selected(self.dark_img > HOT_THRESHOLD, 0)

    if self.gain_map is not None and self.gain_threshold is not None:
      # XXX comparing each pixel to a moving average would probably be better
      # since the gain should vary approximately smoothly over different areas
      # of the detector
      GAIN_THRESHOLD = self.gain_threshold
      #self.logger.debug(
        #"rejecting: %i" %(self.gain_map > GAIN_THRESHOLD).count(True))
      self.cspad_img.set_selected(self.gain_map > GAIN_THRESHOLD, 0)

    if ("nonoise" in self.flags):
      NOISE_THRESHOLD = self.noise_threshold
      self.cspad_img.set_selected(self.cspad_img < NOISE_THRESHOLD, 0)

    if ("sigma_scaling" in self.flags):
      self.do_sigma_scaling()

    if ("symnoise" in self.flags):
      SYMNOISE_THRESHOLD = self.symnoise_threshold
      self.cspad_img.set_selected((-SYMNOISE_THRESHOLD < self.cspad_img) &
                                  ( self.cspad_img  < SYMNOISE_THRESHOLD), 0)

    if ("output" in self.flags):
      import pickle,os
      if (not os.path.isdir(self.pickle_dirname)):
        os.makedirs(self.pickle_dirname)
      flexdata = flex.int(self.cspad_img.astype(numpy.int32))
      d = cspad_tbx.dpack(
        data = flexdata,
        timestamp = cspad_tbx.evt_timestamp(evt)
      )
      G = open(os.path.join(".",self.pickle_dirname)+"/"+self.pickle_basename,
               "ab")
      pickle.dump(d,G,pickle.HIGHEST_PROTOCOL)
      G.close()

    if self.photon_threshold is not None and self.two_photon_threshold is not None:
      self.do_photon_counting()

    if self.background_path is not None:
      self.cspad_img -= self.background_img

    if (self.nmemb == 0):
      # If this is a worker process, set its corresponding bit in the
      # bit field since it will contribute a partial sum.
      if (env.subprocess() >= 0):
        self._tot_lock.acquire()
        self._tot_peers.value |= (1 << env.subprocess())
        self._tot_lock.release()
      self.sum_distance = self.distance
      self.sum_img = self.cspad_img.deep_copy()
      self.sumsq_img = flex.pow2(self.cspad_img)
      self.sum_wavelength = self.wavelength
    else:
      self.sum_distance += self.distance
      self.sum_img += self.cspad_img
      self.sumsq_img += flex.pow2(self.cspad_img)
      self.sum_wavelength += self.wavelength
    self.nmemb += 1

    if 0:
      stats = scitbx.math.basic_statistics(flex_cspad_img.as_double().as_1d())
      self.logger.info("average pixel value: %.3f" %stats.mean)
      self.logger.info("stddev pixel value: %.3f" %stats.biased_standard_deviation)


  def endjob(self, env):
    """
    @param env Environment object
    """
    super(average_mixin, self).endjob(env)

    # This entire function is protected by self._tot_lock to guard
    # against race conditions.
    self._tot_lock.acquire()

    # Add the partial sums to the grand total and clear the bit field
    # for the worker process.
    if (self.nmemb > 0):
      self._tot_distance.value += self.sum_distance
      self._tot_nfail.value += self.nfail
      self._tot_nmemb.value += self.nmemb
      self._tot_wavelength.value += self.sum_wavelength

      # XXX @rwgk: is this really the way to do it?  Need something
      # like the numpy bridge for Python arrays.  Also, _tot_sum ->
      # _tot_img_sum, _tot_ssq -> _tot_img_ssq
      for i in xrange(len(self._tot_sum)):
        self._tot_sum[i] += self.sum_img.as_1d()[i]
        self._tot_ssq[i] += self.sumsq_img.as_1d()[i]

      if (env.subprocess() >= 0):
        self._tot_peers.value &= ~(1 << env.subprocess())

    # XXX Ugly hack: self.nfail and self.nmemb are reset to zero here.
    # Thus, all worker processes except the last one to finish will
    # appear to have processed zero images.  The proper fix will
    # probably require making self.sum_img and self.sumsq_img
    # "private".
    self.avg_distance = 0
    self.avg_img = flex.double(self._tot_sum)
    self.avg_wavelength = 0
    self.nfail = 0
    self.nmemb = 0
    self.stddev_img = flex.double(self._tot_ssq)

    # If all worker processes have contributed their partial sums,
    # finalise the average and standard deviation.
    if (self._tot_peers.value == 0):
      self.nfail = self._tot_nfail.value
      self.nmemb = self._tot_nmemb.value

      if (self.nmemb != 0):
        # Accumulating floating-point numbers introduces errors, which
        # may cause negative variances.  Since a two-pass approach is
        # unacceptable, the standard deviation is clamped at zero.
        self.avg_img = flex.double(self._tot_sum) / self.nmemb
        self.stddev_img = flex.double(self._tot_ssq) \
            - flex.double(self._tot_sum) * self.avg_img
        self.avg_distance = self._tot_distance.value / self.nmemb
        self.avg_wavelength = self._tot_wavelength.value / self.nmemb

        self.stddev_img.set_selected(self.stddev_img < 0, 0)
        if (self.nmemb == 1):
          self.stddev_img = flex.sqrt(self.stddev_img)
        else:
          self.stddev_img = flex.sqrt(self.stddev_img / (self.nmemb - 1))

    # Resize the images to their proper dimensions.  XXX Hardcoded
    # detector size... again!
    if len(self._tot_sum) == 1024 * 1024:
      self.avg_img.resize(flex.grid(1024, 1024))
      self.stddev_img.resize(flex.grid(1024, 1024))
    elif len(self._tot_sum) == 1765 * 1765:
      self.avg_img.resize(flex.grid(1765, 1765))
      self.stddev_img.resize(flex.grid(1765, 1765))
    elif len(self._tot_sum) == 370 * 391:
      self.avg_img.resize(flex.grid(370, 391))
      self.stddev_img.resize(flex.grid(370, 391))
    else:
      raise RuntimeError("Unsupported detector size")
    self._tot_lock.release()
