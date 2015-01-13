#!/usr/bin/env python
# FormatRAXISIVSPring8.py
#
#  Copyright (C) (2015) STFC Rutherford Appleton Laboratory, UK.
#
#  Author: David Waterman.
#
#  This code is distributed under the BSD license, a copy of which is
#  included in the root directory of this package.
#

from __future__ import division
import struct

from dxtbx.format.Format import Format

class FormatRAXISIVSPring8(Format):
  '''Format class for R-AXIS4 images. Currently the only example we have is
  from SPring-8, which requires a reverse axis goniometer. It is not clear how
  to distinguish this detector from others that produce 'R-AXIS4' images that we
  may come across in future. This will be a problem if other detectors do not
  also require reverse axis.
  '''

  @staticmethod
  def understand(image_file):
    try:
      tag = Format.open_file(image_file, 'rb').read(7)
    except IOError,e:
      return False

    return tag == "R-AXIS4"

  def __init__(self, image_file):
    assert(self.understand(image_file))

    Format.__init__(self, image_file)

    return

  def _start(self):
    self._header_bytes = Format.open_file(self._image_file).read(1024)

    if self._header_bytes[812:822].strip() in ['SGI', 'IRIS']:
      self._f = '>f'
      self._i = '>i'
    else:
      self._f = '<f'
      self._i = '<i'

    from iotbx.detectors.raxis import RAXISImage
    self.detectorbase = RAXISImage(self._image_file)
    self.detectorbase.readHeader()

  def _goniometer(self):

    return self._goniometer_factory.single_axis_reverse()

  def _detector(self):
    '''Return a model for the detector as defined in the image header,
    with the additional knowledge about how things are arranged i.e. that
    the principle rotation axis vector points from the sample downwards.'''

    i = self._i
    f = self._f
    header = self._header_bytes

    det_h = struct.unpack(i, header[832:836])[0]
    det_v = struct.unpack(i, header[836:840])[0]
    det_f = struct.unpack(i, header[840:844])[0]

    assert(det_h == 0)
    assert(det_v == 0)
    assert(det_f == 0)

    nx = struct.unpack(i, header[768:772])[0]
    ny = struct.unpack(i, header[772:776])[0]

    dx = struct.unpack(f, header[776:780])[0]
    dy = struct.unpack(f, header[780:784])[0]

    distance = struct.unpack(f, header[344:348])[0]
    two_theta = struct.unpack(f, header[556:560])[0]

    beam_x = struct.unpack(f, header[540:544])[0]
    beam_y = struct.unpack(f, header[544:548])[0]

    beam = (beam_x * dx, beam_y * dy)

    return self._detector_factory.two_theta(
        'IMAGE_PLATE', distance, beam, '+y', '-x', '+x', two_theta,
        (dx, dy), (nx, ny), (0, 1000000), [])

  def _beam(self):
    '''Return a simple model for the beam.'''

    wavelength = struct.unpack(self._f, self._header_bytes[292:296])[0]

    return self._beam_factory.simple(wavelength)

  def _scan(self):
    '''Return the scan information for this image.'''
    import calendar
    i = self._i
    f = self._f
    header = self._header_bytes

    format = self._scan_factory.format('RAXIS')
    exposure_time = struct.unpack(f, header[536:540])[0]

    y, m, d = map(int, header[256:268].strip().split('-'))

    epoch = calendar.timegm(datetime.datetime(y, m, d, 0, 0, 0).timetuple())

    s = struct.unpack(i, header[980:984])[0]

    osc_start = struct.unpack(f, header[920 + s * 4:924 + s * 4])[0]
    osc_end = struct.unpack(f, header[940 + s * 4:944 + s * 4])[0]

    osc_range = osc_end - osc_start

    return self._scan_factory.single(
        self._image_file, format, exposure_time,
        osc_start, osc_range, epoch)
