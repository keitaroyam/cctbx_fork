from __future__ import division
from dxtbx.format.Format import Format
from dxtbx.format.FormatHDF5 import FormatHDF5

########################################################################
# Allow regularization of input parameters to correct for tiny O(10^-16)
# differences from rotation of coordinate frames - set debugging = True
########################################################################

debugging = False

if debugging:
  def rvec(a):
    from scitbx import matrix
    return matrix.col([round(_a) for _a in a.elems])
else:
  def rvec(a):
    return a

class FormatHDF5Nexus(FormatHDF5):

  @staticmethod
  def understand(image_file):
    try:
      tag = FormatHDF5.open_file(image_file, 'rb').read(8)
    except IOError, e:
      return False

    return tag == "\211HDF\r\n\032\n"

  def __init__(self, image_file):
    assert(self.understand(image_file))
    FormatHDF5.__init__(self, image_file)

  def _start(self):
    import h5py
    self._h5_handle = h5py.File(self.get_image_file(), 'r')

    # compute coordinate frame transformation to imgCIF frame, just for kicks
    entry = self._h5_handle['entry']
    sample = entry['sample']
    axis = tuple(sample['pose']['CBF_axis_omega'].attrs['vector'])

    # NeXus coordinate frame: Z is canonical
    from rstbx.cftbx.coordinate_frame_helpers import align_reference_frame
    self._R = align_reference_frame(axis, (1, 0, 0), (0, 0, -1), (0, 0, 1))

    return

  def _goniometer(self):
    ''' Get the rotation axis. '''
    entry = self._h5_handle['entry']
    sample = entry['sample']
    pose = sample['pose']
    axis = tuple(pose['CBF_axis_omega'].attrs['vector'])

    return self._goniometer_factory.known_axis(rvec(self._R * axis))

  def _detector(self):
    from scitbx import matrix

    # Get the detector geometry stuff
    entry = self._h5_handle['entry']
    instrument = entry['instrument']
    detector = instrument['detector']
    pose = detector['pose']
    translation = pose['translation']
    rotation = pose['rotation']

    # Get the translation
    offset = translation.attrs['offset']
    trans = translation[0]
    vector = matrix.col(translation.attrs['vector']).normalize()

    # Initialise detector frame
    fast = matrix.col((1.0, 0.0, 0.0))
    slow = matrix.col((0.0, 1.0, 0.0))
    orig = 1000 * matrix.col((offset[0] + trans * vector[0],
                              offset[1] + trans * vector[1],
                              offset[2] + trans * vector[2]))

    # Next comes a rotation about an axis
    vector = matrix.col(rotation.attrs['vector']).normalize()
    angle = rotation[0]
    m_rot = vector.axis_and_angle_as_r3_rotation_matrix(angle, deg=True)

    # Transform detector frame - also to imgCIF
    fast = self._R * (m_rot * fast).normalize()
    slow = self._R * (m_rot * slow).normalize()
    orig = self._R * m_rot * orig

    # Get the pixel and image size
    pixel_size = 1000 * detector['x_pixel_size'].value, \
                 1000 * detector['y_pixel_size'].value
    image_size = len(detector['x_pixel_offset']), \
                 len(detector['y_pixel_offset'])
    trusted_range = (-1, detector['saturation_value'][0])

    # Make the detector
    return self._detector_factory.make_detector(
      "", rvec(fast), rvec(slow), orig,
      pixel_size, image_size, trusted_range)

  def _beam(self):
    ''' Nexus defines beam along z axis, i.e. from source to sample (i.e. reversed
    w.r.t. imgCIF convention).'''

    from scitbx import matrix
    entry = self._h5_handle['entry']
    sample = entry['sample']
    beam = sample['beam']
    wavelength = beam['wavelength']
    return self._beam_factory.simple_directional(
      rvec(self._R * matrix.col((0,0,-1))),
      wavelength[0])

  def _scan(self):
    ''' Get the scan. '''
    import time
    entry = self._h5_handle['entry']
    sample = entry['sample']
    pose = sample['pose']
    angles = pose['CBF_axis_omega']
    oscillation = (angles[0], angles[1] - angles[0])
    image_range = (1, len(angles))
    instrument = entry['instrument']
    detector = instrument['detector']
    exposure_times = detector['count_time']

    # Create the epochs
    frame_time = detector['frame_time']
    start_time = entry['start_time']
    time_ssec = start_time.value.split('.')
    time_struct = time.strptime(time_ssec[0], "%Y-%m-%dT%H:%M:%S")
    start_time = time.mktime(time_struct) + float('0.%s' % time_ssec[1])
    epochs = {0 : start_time}
    for i, t in enumerate(frame_time[:-1]):
      epochs[i+1] = epochs[i] + t

    # Create the scan
    return self._scan_factory.make_scan(
      image_range,
      list(exposure_times),
      oscillation,
      list(epochs),
      deg=True)

  def get_num_images(self):
    entry = self._h5_handle['entry']
    data = entry['data']['data']
    return data.shape[0]

  def get_goniometer(self, index=None):
    return Format.get_goniometer(self)

  def get_detector(self, index=None):
    return Format.get_detector(self)

  def get_beam(self, index=None):
    return Format.get_beam(self)

  def get_scan(self, index=None):
    if index == None:
      return Format.get_scan(self)
    else:
      scan = Format.get_scan(self)
      return scan[index]

  def get_raw_data(self, index):
    from scitbx.array_family import flex
    entry = self._h5_handle['entry']
    data = entry['data']['data']
    return flex.int(data[index,:,:])

  def get_image_file(self, index=None):
    return Format.get_image_file(self)
