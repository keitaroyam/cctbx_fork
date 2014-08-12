#!/usr/bin/env python
#
# imageset.py
#
#  Copyright (C) 2013 Diamond Light Source
#
#  Author: James Parkhurst
#
#  This code is distributed under the BSD license, a copy of which is
#  included in the root directory of this package.
from __future__ import division


class ReaderBase(object):
  '''The imageset reader base class.'''

  def __init__(self):
    pass

  def __cmp__(self, other):
    pass

  def get_image_paths(self, indices=None):
    pass

  def get_image_size(self, panel=0):
    pass

  def get_format(self, index=None):
    pass

  def get_format_class(self, index=None):
    pass

  def get_path(self, index=None):
    pass

  def is_valid(self, indices=None):
    pass

  def read(self, index=None):
    pass

  def get_detectorbase(self, index=None):
    pass

  def get_detector(self, index=None):
    pass

  def get_goniometer(self, index=None):
    pass

  def get_beam(self, index=None):
    pass

  def get_scan(self, index=None):
    pass


class NullReader(ReaderBase):
  ''' A placeholder reader. '''

  def __init__(self, filenames):
    ReaderBase.__init__(self)
    self._filenames = filenames

  def __cmp__(self, other):
    ''' Compare with another reader. '''
    return isinstance(other, NullReader)

  def get_image_paths(self, indices=None):
    ''' Get the image paths. '''
    if indices == None:
      return list(self._filenames)
    return self._filenames(indices)

  def get_format(self, index=None):
    ''' Get the format. '''
    return None

  def get_format_class(self, index=None):
    ''' Get the format class. '''
    return None

  def get_path(self, index=None):
    ''' Get an image path. '''
    if index == None:
      return self._path[0]
    return self._filenames[index]

  def is_valid(self, indices=None):
    ''' Return whether the reader is valid. '''
    return True

  def read(self, index):
    raise RuntimeError('NullReader doesn\'t have image data')

  def get_detector(self, index=None):
    '''Get the detector instance.'''
    raise RuntimeError('NullReader doesn\'t have detector data')

  def get_beam(self, index=None):
    '''Get the beam instance.'''
    raise RuntimeError('NullReader doesn\'t have beam data')

  def get_goniometer(self, index=None):
    '''Get the goniometer instance.'''
    raise RuntimeError('NullReader doesn\'t have goniometer data')

  def get_scan(self, index=None):
    '''Get the scan instance.'''
    raise RuntimeError('NullReader doesn\'t have scan data')


class SingleFileReader(ReaderBase):
  '''The single file reader class.'''

  def __init__(self, format_instance = None):
    '''Initialise the reader class.'''
    ReaderBase.__init__(self)

    # Set the format instance
    self._format = format_instance

  def __cmp__(self, other):
    '''Compare the reader to another reader.'''
    return self._format == other._format

  def __getstate__(self):
    return self._format.__class__, self._format.get_image_file()

  def __setstate__(self, state):
    self._format = state[0](state[1])

  def get_image_paths(self, indices=None):
    '''Get the image paths within the file.'''

    # Get paths for each file
    filenames = [self._format.get_image_file(i)
                 for i in range(self._format.get_num_images())]

    # Return within the given range
    if indices == None:
      return filenames
    else:
      return [filenames[i] for i in indices]

  def get_format(self, index=None):
    '''Get the format instance'''
    return self._format

  def get_format_class(self, index=None):
    '''Get the format class'''
    return self._format.__class__

  def get_path(self, index=None):
    '''Get the image file for the given index.'''
    return self._format.get_image_file(index)

  def is_valid(self, indices=None):
    '''Ensure the reader is valid.'''
    return True

  def read(self, index=None):
    '''Get the image data.'''
    return self._format.get_raw_data(index)

  def get_detectorbase(self, index=None):
    '''Get the detector base instance.'''
    return self._format.get_detectorbase(index)

  def get_detector(self, index=None):
    '''Get the detector instance.'''
    return self._format.get_detector(index)

  def get_beam(self, index=None):
    '''Get the beam instance.'''
    return self._format.get_beam(index)

  def get_goniometer(self, index=None):
    '''Get the goniometer instance.'''
    return self._format.get_goniometer(index)

  def get_scan(self, index=None):
    '''Get the scan instance.'''
    return self._format.get_scan(index)


class MultiFileState(object):
  '''A class to keep track of multi file reader state.'''

  def __init__(self, format_class):
    '''Initialise with format class.'''
    self._format_class = format_class
    self._current_format_instance = None

  def format_class(self):
    '''Get the format class.'''
    return self._format_class

  def load_file(self, filename):
    '''Load the file with the given filename.'''

    # Check the current format is the one we need
    if (self.get_format() == None or
        filename != self.get_format().get_image_file()):

      # Read the format instance
      format_instance = self._format_class(filename)

      # Check the format instance is valid
      if not self._is_format_valid(format_instance):
        RuntimeError("Format is invalid.")

      # Set the current format instance
      self._current_format_instance = format_instance

  def get_format(self):
    '''Get the current format instance.'''
    return self._current_format_instance

  def _is_format_valid(self, format_instance):
    '''Check if the format object is valid.'''
    return format_instance.understand(format_instance.get_image_file())

  def __getstate__(self):
    ''' Save the current image and format class for pickling. '''
    if self._current_format_instance is not None:
      current_filename = self._current_format_instance.get_image_file()
    else:
      current_filename = None
    return { 'format_class' : self._format_class,
             'current_filename' : current_filename }

  def __setstate__(self, state):
    ''' Set the format class and load the image. '''
    self._format_class = state['format_class']
    self._current_format_instance = None
    if state['current_filename'] is not None:
      self.load_file(state['current_filename'])


class NullFormatChecker(object):
  def __call__(self, fmt):
    return True


class MultiFileReader(ReaderBase):
  '''A multi file reader class implementing the ReaderBase interface.'''

  def __init__(self, format_class, filenames, formatchecker=None):
    '''Initialise the reader with the format and list of filenames.'''
    ReaderBase.__init__(self)

    import os

    # Ensure we have enough images and format has been specified
    assert(format_class != None)
    assert(len(filenames) > 0)

    # Save the image indices
    self._filenames = filenames

    # Handle the state of the MultiFileReader class
    self._state = MultiFileState(format_class)

    # A function object to check formats are valid
    if formatchecker != None:
      self._is_format_valid = formatchecker
    else:
      self._is_format_valid = NullFormatChecker()

  def __cmp__(self, other):
    '''Compare the reader by format class and filename list.'''
    return (self.get_format_class() == other.get_format_class() and
            self.get_image_paths() == other.get_image_paths())

  def get_image_paths(self, indices=None):
    '''Get the list of image paths.'''
    if indices == None:
      return list(self._filenames)
    else:
      return [self._filenames[i] for i in indices]

  def get_format_class(self):
    '''Get the format class.'''
    return self._state.format_class()

  def get_image_size(self, panel=0):
    '''Get the image size.'''
    return self.get_format().get_detector()[panel].get_image_size()

  def get_path(self, index=None):
    '''Get the path the given index.'''
    if index == None:
      return self.get_format().get_image_file()
    else:
      return self._filenames[index]

  def get_detectorbase(self, index=None):
    '''Get the detector base instance at given index.'''
    return self.get_format(index).get_detectorbase()

  def get_detector(self, index=None):
    '''Get the detector instance at given index.'''
    return self.get_format(index).get_detector()

  def get_beam(self, index=None):
    '''Get the beam instance at given index.'''
    return self.get_format(index).get_beam()

  def get_goniometer(self, index=None):
    '''Get the goniometer instance at given index.'''
    return self.get_format(index).get_goniometer()

  def get_scan(self, index=None):
    '''Get the scan instance at given index.'''
    return self.get_format(index).get_scan()

  def read(self, index=None):
    '''Read the image frame at the given index.'''

    # Get the format instance and the number of panels
    format_instance = self.get_format(index)
    npanels = len(format_instance.get_detector())

    # Return a flex array for single panels and a tuple of flex arrays
    # for multiple panels
    assert(npanels > 0)
    if npanels == 1:
      return format_instance.get_raw_data()
    else:
      return tuple([format_instance.get_raw_data(i) for i in range(npanels)])

  def get_format(self, index=None):
    '''Get the format at the given index.'''
    return self._update_state(index).get_format()

  def _update_state(self, index=None):
    '''Update the state and load file at given index.'''
    if index is not None:
      self._state.load_file(self.get_path(index))
    elif self._state.get_format() == None:
      self._state.load_file(self.get_path(0))

    return self._state

  def is_valid(self, indices=None):
    '''Ensure imageset is valid.'''
    import os

    # If no indices, get indices of all filenames
    if indices == None:
      indices = range(len(self._filenames))

    # Loop through all the images
    for index in indices:

      # Read and try to cache the format, if this fails, the
      # format is invalid, so return false.
      try:
        format_instance = self.get_format(index)
      except IndexError, RuntimeError:
        return False

      # Check the format experimental models
      if not self._is_format_valid(format_instance):
        return False

    # All images valid
    return True


class ImageSet(object):
  ''' A class exposing the external image set interface. '''

  def __init__(self, reader, indices=None, models=None):
    ''' Initialise the ImageSet object.

    Params:
        reader The reader object
        array_range The image range (first, last)

    '''
    # If no reader is set then throw an exception
    if not reader:
      raise ValueError("ImageSet needs a reader!")

    # Set the reader
    self._reader = reader

    # Set the array range or get the range from the reader
    if indices:
      self._indices = indices
    else:
      self._indices = range(len(self.reader().get_image_paths()))

    # Cache the models
    if models is None:
      self._models = dict()
    else:
      self._models = models

  def __getitem__(self, item):
    ''' Get an item from the image set stream.

    If the item is an index, read and return the image at the given index.
    Otherwise, if the item is a slice, then create a new ImageSet object
    with the given number of array indices from the slice.

    Params:
        item The index or slice

    Returns:
        An image or new ImageSet object

    '''
    if isinstance(item, slice):
      indices = self._indices[item]
      return ImageSet(self.reader(), indices, self._models)
    else:
      return self.reader().read(self._indices[item])

  def __len__(self):
    ''' Return the number of images in this image set. '''
    return len(self._indices)

  def __str__(self):
    ''' Return the array indices of the image set as a string. '''
    return str(self.paths())

  def __iter__(self):
    ''' Iterate over the array indices and read each image in turn. '''
    for f in self._indices:
      yield self.reader().read(f)

  def __cmp__(self, other):
    ''' Compare this image set to another. '''
    return self.reader() == other.reader()

  def indices(self):
    ''' Return the indices in the image set. '''
    return list(self._indices)

  def paths(self):
    ''' Return a list of filenames referenced by this set. '''
    filenames = self.reader().get_image_paths()
    return [filenames[i] for i in self._indices]

  def is_valid(self):
    ''' Validate all the images in the image set. Can take a long time. '''
    return self.reader().is_valid(self._indices)

  def get_image_models(self, index=None, no_read=False):
    ''' Get the models for the image.'''
    path = self.get_path(index)
    if path not in self._models:
      models = {}
      if not no_read:
        image_index = self._image_index(index)
        try:
          models['detector'] = self.reader().get_detector(image_index)
        except Exception:
          models['detector'] = None
        try:
          models['goniometer'] = self.reader().get_goniometer(image_index)
        except Exception:
          models['goniometer'] = None
        try:
          models['beam'] = self.reader().get_beam(image_index)
        except Exception:
          models['beam'] = None
        try:
          models['scan'] = self.reader().get_scan(image_index)
        except Exception:
          models['scan'] = None
      else:
        models['detector'] = None
        models['beam'] = None
        models['goniometer'] = None
        models['scan'] = None
      self._models[path] = models
    return self._models[path]

  def get_image_size(self, panel=0, index=None):
    ''' Get the image size. '''
    return self.get_detector()[panel].get_image_size()

  def get_detector(self, index=None):
    ''' Get the detector. '''
    return self.get_image_models(index)['detector']

  def set_detector(self, detector, index=None):
    ''' Set the detector model.'''
    self.get_image_models(index)['detector'] = detector

  def get_beam(self, index=None):
    ''' Get the beam. '''
    return self.get_image_models(index)['beam']

  def set_beam(self, beam, index=None):
    ''' Set the beam model.'''
    self.get_image_models(index)['beam'] = beam

  def get_goniometer(self, index=None):
    ''' Get the goniometer model. '''
    return self.get_image_models(index)['goniometer']

  def set_goniometer(self, goniometer, index=None):
    ''' Set the goniometer model. '''
    self.get_image_models(index)['goniometer'] = goniometer

  def get_scan(self, index=None):
    ''' Get the scan model. '''
    return self.get_image_models(index)['scan']

  def set_scan(self, scan, index=None):
    ''' Set the scan model. '''
    self.get_image_models(index)['scan'] = scan

  def get_detectorbase(self, index):
    ''' Get the detector base instance for the given index. '''
    return self.reader().get_detectorbase(self._image_index(index))

  def reader(self):
    ''' Return the image set reader. '''
    return self._reader

  def get_path(self, index):
    ''' Get the path for the index '''
    return self.reader().get_path(self._image_index(index))

  def _image_index(self, index=None):
    ''' Convert image set index to image index.'''
    if index == None:
      return self._indices[0]
    elif index < 0 or index >= len(self._indices):
      raise IndexError('Index out of range')
    return self._indices[index]

  def complete_set(self):
    ''' Return the set of all images (i.e. not just the subset). '''
    return ImageSet(self.reader(), models=self._models)


class MemImageSet(ImageSet):
  ''' A class exposing the external image set interface, but instead of a file list, uses
  an already instantiated list of Format objects. Derives from ImageSet for clarity and for
  the dials importer, but overrides all of ImageSet's methods '''

  def __init__(self, images, indices=None):
    ''' Initialise the MemImageSet object.

    Params:
        images: list of Format objects
        indices: list of indices into the images list

    '''
    # If no list of images is set then throw an exception
    if images is None:
      raise ValueError("MemImageSet needs a list of images!")

    # Save the images
    self._images = images

    # Set the array range or get the range from the list of images
    if indices is not None:
      self._indices = indices
    else:
      self._indices = range(len(images))

  def __getitem__(self, item):
    ''' Get an item from the image set.

    If the item is an index, read and return the image at the given index.
    Otherwise, if the item is a slice, then create a new MemImageSet object
    with the given number of array indices from the slice.

    Params:
        item The index or slice

    Returns:
        An image or new ImageSet object

    '''
    if isinstance(item, slice):
      indices = self._indices[item]
      return MemImageSet(self._images, indices)
    else:
      img = self._images[self._indices[item]]
      return tuple([img.get_raw_data(i) for i in xrange(len(self.get_detector()))])

  def __len__(self):
    ''' Return the number of images in this image set. '''
    return len(self._indices)

  def __str__(self):
    ''' Return the array indices of the image set as a string. '''
    return str(self._indices)

  def __iter__(self):
    ''' Iterate over the array indices and read each image in turn. '''
    for j in self._indices:
      img = self._images[j]
      yield tuple([img.get_raw_data(i) for i in xrange(len(self.get_detector()))])

  def __cmp__(self, other):
    ''' Compare this image set to another. '''
    return self._images == other._images

  def indices(self):
    ''' Return the indices in the image set. '''
    return list(self._indices)

  def paths(self):
    ''' Return a list of filenames referenced by this set. '''
    raise NotImplementedError("No path list for an in-memory image set")

  def is_valid(self):
    ''' Validate all the images in the image set. Can take a long time. '''
    #return self.reader().is_valid(self._indices)
    return True

  def get_detector(self, index=None):
    ''' Get the detector. '''
    if index is None:
      index = self._indices[0]
    return self._images[index].get_detector()

  def set_detector(self, detector):
    ''' Set the detector model.'''
    for img in self._images:
      img._detector = detector

  def get_beam(self, index=None):
    ''' Get the beam. '''
    if index is None:
      index = self._indices[0]
    return self._images[index].get_beam()

  def set_beam(self, beam):
    ''' Set the beam model.'''
    for img in self._images:
      img._beam = beam

  def get_goniometer(self, index=None):
    if index is None:
      index = self._indices[0]
    return self._images[index].get_goniometer()

  def get_scan(self, index=None):
    if index is None:
      index = self._indices[0]
    return self._images[index].get_scan()

  def get_image_size(self, index=0):
    ''' Get the image size. '''
    if index is None:
      index = self._indices[0]
    return self._images[index].get_image_size()

  def get_detectorbase(self, index=None):
    ''' Get the detector base instance for the given index. '''
    if index is None:
      index = self._indices[0]
    return self._images[index].get_detector_base()

  def reader(self):
    ''' Return the image set reader. '''
    raise NotImplementedError("MemImageSet has no reader")

  def _image_index(self, index=None):
    ''' Convert image set index to image index.'''
    if index == None:
      return None
    elif index < 0 or index >= len(self._indices):
      raise IndexError('Index out of range')
    return self._indices[index]


class SweepFileList(object):
  '''Class implementing a file list interface for sweep templates.'''

  def __init__(self, template, array_range):
    '''Initialise the class with the template and array range.'''

    #assert(array_range[0] >= 0)
    assert(array_range[0] <= array_range[1])
    self._template = template
    self._array_range = array_range

  def __getitem__(self, index):
    '''Get the filename at that array index.'''
    return self.get_filename(self._array_range[0] + index)

  def __iter__(self):
    '''Iterate through the filenames.'''
    for i in range(len(self)):
      yield self.__getitem__(i)

  def __str__(self):
    '''Get the string representation of the file list.'''
    return str([filename for filename in self])

  def __len__(self):
    '''Get the length of the file list.'''
    return self._array_range[1] - self._array_range[0]

  def __eq__(self, other):
    '''Compare filelist by template and array range.'''
    return (self.template() == other.template() and
            self.array_range() == other.array_range())

  def template(self):
    '''Get the template.'''
    return self._template

  def array_range(self):
    '''Get the array range.'''
    return self._array_range

  def indices(self):
    '''Get the image indices.'''
    return range(*self._array_range)

  def get_filename(self, index):
    '''Get the filename at the given index.'''
    if not self.is_index_in_range(index):
      raise IndexError('Image file index out of range')

    return self._template % (index + 1)

  def is_index_in_range(self, index):
    '''Ensure that the index is within the array range.'''
    return self._array_range[0] <= index < self._array_range[1]


class ImageSweep(ImageSet):
  ''' A class exposing the external sweep interface. '''

  def __init__(self, reader, indices=None,
               beam=None, goniometer=None,
               detector=None, scan=None):
    ''' Create the sweep.

    If the models are given here. They are used, otherwise the models
    are read from the files themselves, with the beam, detector and
    goniometer taken from the first image and the scan read from the
    whole range of images. The scan must be consistent with the indices
    given if both are specified.

    Params:
        reader The reader class
        indices The list of image indices
        beam The beam model
        goniometer The goniometer model
        detector The detector model
        scan The scan model

    '''
    ImageSet.__init__(self, reader, indices)
    # FIXME_HACK
    if scan is not None and self._indices != [0]:
      assert(scan.get_num_images() == (self._indices[-1] - self._indices[0] + 1))
    self._beam = beam
    self._goniometer = goniometer
    self._detector = detector
    self._scan = scan

  def __getitem__(self, item):
    ''' Get an item from the sweep stream.

    If the item is an index, read and return the image at the given index.
    Otherwise, if the item is a slice, then create a new Sweep object
    with the given number of array indices from the slice.

    Params:
        item The index or slice

    Returns:
        An image or new Sweep object

    '''
    if isinstance(item, slice):
      if item.step != None:
        raise IndexError('Sweeps must be sequential')
      if self._scan is None:
        scan = None
      else:
        scan = self._scan[item]
      return ImageSweep(self.reader(), self._indices[item],
        self._beam, self._goniometer, self._detector, scan)
    else:
      return self.reader().read(self._indices[item])

  def get_template(self):
    ''' Get the template. '''
    from dxtbx.sweep_filenames import template_format_to_string
    return template_format_to_string(self.reader()._filenames.template())

  def get_array_range(self):
    ''' Get the array range. '''
    return self.get_scan().get_array_range()

  def get_image_size(self, panel=0, index=None):
    ''' Get the image size. '''
    return self.get_detector()[panel].get_image_size()

  def get_beam(self, index=None):
    ''' Get the beam. '''
    if self._beam == None:
      self._beam = self.reader().get_beam()
    return self._beam

  def get_detector(self, index=None):
    ''' Get the detector. '''
    if self._detector == None:
      self._detector = self.reader().get_detector()
    return self._detector

  def get_goniometer(self, index=None):
    ''' Get goniometer, '''
    if self._goniometer == None:
      self._goniometer = self.reader().get_goniometer()
    return self._goniometer

  def get_scan(self, index=None):
    ''' Get the scan.'''
    if self._scan == None:
      self._scan = sum(
        (self.reader().get_scan(i) for i in self._indices[1:]),
        self.reader().get_scan(self._indices[0]))
    if index is not None:
      if index < 0 or index >= self._scan.get_num_images():
        raise IndexError('index out of range')
      return self._scan[index]
    return self._scan

  def set_beam(self, beam):
    ''' Set the beam. '''
    self._beam = beam

  def set_goniometer(self, goniometer):
    ''' Set the goniometer model '''
    self._goniometer = goniometer

  def set_detector(self, detector):
    ''' Set the detector model. '''
    self._detector = detector

  def set_scan(self, scan):
    ''' Set the scan model. '''
    # FIXME_HACK
    if self._indices != [0]:
      assert(scan.get_num_images() == (self._indices[-1] - self._indices[0] + 1))
    self._scan = scan

  def complete_set(self):
    ''' Return the set of all images (i.e. not just the subset). '''
    return ImageSweep(self.reader(), beam=self._beam, detector=self._detector,
                      goniometer=self._goniometer, scan=self._scan)

  def to_array(self, item=None, panel=0):
    ''' Read all the files in the sweep and convert them into an array
    of the appropriate dimensions.

    The required array is allocated first, this has he useful property
    that if you've been lazy and just got a sweep and extracted the
    array without consideration for the amount of memory available on
    your machine, you'll get an exception straight away.

    TODO:
        Currently uses numpy for fast copying of arrays, try to do
        this using flex arrays.

    Params:
        item The index item (frame 0, frame n), (z0, z1, y0, y1, x0, x1)

    Returns:
        The sweep image data as an array.

    '''
    if item is None:
      return self._to_array_all(panel)
    else:
      return self._to_array_w_range(item, panel)

  def _to_array_all(self, panel=0):
    ''' Get the array from all the sweep elements. '''

    from scitbx.array_family import flex

    # Get the image dimensions
    size_z = len(self)
    size_y = self.reader().get_image_size(panel)[1]
    size_x = self.reader().get_image_size(panel)[0]

    # Check sizes are valid
    if size_z <= 0 or size_y <= 0 or size_x <= 0:
      raise RuntimeError("Invalid dimensions")

    # Allocate the array
    array = flex.int(flex.grid(size_z, size_y, size_x))

    # Loop through all the images and set the image data
    for k, image in enumerate(self):
      if not isinstance(image, tuple):
        image = (image,)
      im = image[panel]
      im.reshape(flex.grid(1, *im.all()))
      array[k:k+1,:,:] = im

    # Return the array
    return array

  def _to_array_w_range(self, item, panel=0):
    ''' Get the array from the user specified range. '''
    from scitbx.array_family import flex

    # Get the range from the given index item
    z0, z1, y0, y1, x0, x1 = self._get_data_range(item, panel)

    # Get the image dimensions
    size_z = z1 - z0
    size_y = y1 - y0
    size_x = x1 - x0

    # Check sizes are valid
    if size_z <= 0 or size_y <= 0 or size_x <= 0:
      raise RuntimeError("Invalid dimensions")

    # Allocate the array
    array = flex.int(flex.grid(size_z, size_y, size_x))

    # Loop through all the images and set the image data
    for k, index in enumerate(self.indices()[z0:z1]):
      image = self.reader().read(index)
      if not isinstance(image, tuple):
        image = (image,)
      im = image[panel]
      im.reshape(flex.grid(1, *im.all()))
      array[k:k+1,:,:] = im[0:1, y0:y1, x0:x1]

    # Return the array
    return array

  def _get_data_range(self, item, panel=0):
    ''' Get the range from the user specified index item. '''

    # Ensure item is a tuple
    if isinstance(item, tuple):

      # Just the range of images given
      if len(item) == 2:
        z0, z1 = item
        y0, y1 = (0, self.reader().get_image_size(panel)[1])
        x0, x1 = (0, self.reader().get_image_size(panel)[0])
        return self._truncate_range((z0, z1, y0, y1, x0, x1))

      # The range in each direction given
      elif len(item) == 6:
        return self._truncate_range(item, panel)

    # Raise index error
    raise IndexError("bad index")

  def _truncate_range(self, data_range, panel=0):
    ''' Truncate the range to the size of available data. '''

    # Get items from range
    z0, z1, y0, y1, x0, x1 = data_range

    # Get the number of frames and image size
    size_z = len(self)
    size_x, size_y = self.reader().get_image_size(panel)

    # Ensure range is valid
    if z0 < 0: z0 = 0
    if y0 < 0: y0 = 0
    if x0 < 0: x0 = 0
    if z1 > size_z: z1 = size_z
    if y1 > size_y: y1 = size_y
    if x1 > size_x: x1 = size_x

    # Return truncated range
    return (z0, z1, y0, y1, x0, x1)


class FilenameAnalyser(object):
  '''Group images by filename into image sets.'''

  def __init__(self):
    '''Initialise the class.'''
    pass

  def __call__(self, filenames):
    '''Group the filenames by imageset.

    Params:
        filenames The list of filenames

    Returns:
        A list of (template, [indices], is_sweep)

    '''
    from sweep_filenames import group_files_by_imageset

    # Analyse filenames to figure out how many imagesets we have
    filelist_per_imageset = group_files_by_imageset(filenames)

    # Label each group as either an imageset or a sweep.
    file_groups = []
    for template, indices in filelist_per_imageset.iteritems():

      # Check if this imageset is a sweep
      is_sweep = self._is_imageset_a_sweep(template, indices)

      # Append the items to the group list
      file_groups.append((template, indices, is_sweep))

    # Return the groups of files
    return file_groups

  def _is_imageset_a_sweep(self, template, indices):
    ''' Return True/False if the imageset is a sweep or not.

    Where more than 1 image that follow sequential numbers are given
    the images are catagorised as belonging to a sweep, otherwise they
    belong to an image set.

    '''
    if len(indices) <= 1:
      return False
    else:
      indices = sorted(indices)
      if self._indices_sequential_ge_zero(indices):
        return True
      else:
        return False

  def _indices_sequential_ge_zero(self, indices):
    ''' Determine if indices are sequential.'''
    prev = indices[0]
    if prev < 0:
      return False
    for curr in indices[1:]:
      if curr != prev + 1:
        return False
      prev = curr

    return True


class ImageSetFactory(object):
  ''' Factory to create imagesets and sweeps. '''

  @staticmethod
  def new(filenames, check_headers=False, ignore_unknown=False):
    ''' Create an imageset or sweep

    Params:
        filenames A list of filenames
        check_headers Check the headers to ensure all images are valid
        ignore_unknown Ignore unknown formats

    Returns:
        A list of imagesets

    '''
    # Ensure we have enough images
    if isinstance(filenames, list):
      assert(len(filenames) > 0)
    elif isinstance(filenames, str):
      filenames = [filenames]
    else:
      raise RuntimeError, 'unknown argument passed to ImageSetFactory'

    # Analyse the filenames and group the images into imagesets.
    analyse_files = FilenameAnalyser()
    filelist_per_imageset = analyse_files(filenames)

    # For each file list denoting an image set, create the imageset
    # and return as a list of imagesets. N.B sweeps and image sets are
    # returned in the same list.
    imagesetlist = []
    for filelist in filelist_per_imageset:
      try:
        imagesetlist.append(ImageSetFactory._create_imageset_or_sweep(
            filelist, check_headers))
      except Exception, e:
        if not ignore_unknown:
          raise e

    # Return the imageset list
    return imagesetlist

  @staticmethod
  def from_template(template, image_range=None, check_headers=False,
                    check_format=True):
    '''Create a new sweep from a template.

    Params:
        template The template argument
        image_range The image range
        check_headers Check the headers to ensure all images are valid

    Returns:
        A list of sweeps

    '''
    import os
    from dxtbx.format.Registry import Registry
    from dxtbx.sweep_filenames import template_image_range

    if not check_format: assert not check_headers

    # Check the template is valid
    if template.count('#') < 1:
      raise ValueError("Invalid template")

    # Get the template format
    pfx = template.split('#')[0]
    sfx = template.split('#')[-1]
    template_format = '%s%%0%dd%s' % (pfx, template.count('#'), sfx)

    # Get the template image range
    if image_range is None:
      image_range = template_image_range(template)

    # Set the image range
    array_range = (image_range[0] - 1, image_range[1])

    # Create the sweep file list
    filenames = SweepFileList(template_format, array_range)

    # Get the format class
    if check_format:
      format_class = Registry.find(filenames[0])
      from format.FormatMultiImage import FormatMultiImage
      if issubclass(format_class, FormatMultiImage):
        assert len(filenames) == 1
        format_instance = format_class(filenames[0])
        reader = SingleFileReader(format_instance)
      else:
        reader = MultiFileReader(format_class, filenames)
    else:
      reader = NullReader(filenames)

    # Create the sweep object
    sweep = ImageSweep(reader)

    # Check the sweep is valid
    if check_headers and not sweep.is_valid():
      raise RuntimeError('Invalid sweep of images')

    # Return the sweep
    return [sweep]

  @staticmethod
  def _create_imageset_or_sweep(filelist, check_headers):
    '''Create either an imageset of sweep.'''
    if filelist[2] == True:
      return ImageSetFactory._create_sweep(filelist, check_headers)
    else:
      return ImageSetFactory._create_imageset(filelist, check_headers)

  @staticmethod
  def _create_imageset(filelist, check_headers):
    '''Create an image set'''
    from dxtbx.format.Registry import Registry

    # Extract info from filelist
    template, indices, is_sweep = filelist

    # Get the template format
    count = template.count('#')
    if count > 0:
      pfx = template.split('#')[0]
      sfx = template.split('#')[-1]
      template_format = '%s%%0%dd%s' % (pfx, template.count('#'), sfx)
      filenames = [template_format % index for index in indices]
    else:
      filenames = [template]

    # Sort the filenames
    filenames = sorted(filenames)

    # Get the format object
    format_class = Registry.find(filenames[0])

    # Create the image set object
    from format.FormatMultiImage import FormatMultiImage
    if issubclass(format_class, FormatMultiImage):
      assert len(filenames) == 1
      format_instance = format_class(filenames[0])
      image_set = ImageSet(SingleFileReader(format_instance))
    else:
      image_set = ImageSet(MultiFileReader(format_class, filenames))

    # Check the image set is valid
    if check_headers and not image_set.is_valid():
      raise RuntimeError('Invalid ImageSet')

    # Return the image set
    return image_set

  @staticmethod
  def _create_sweep(filelist, check_headers):
    '''Create a sweep'''
    import os
    from dxtbx.format.Registry import Registry

    # Extract info from filelist
    template, indices, is_sweep = filelist

    # Get the template format
    count = template.count('#')
    if count > 0:
      pfx = template.split('#')[0]
      sfx = template.split('#')[-1]
      template_format = '%s%%0%dd%s' % (pfx, template.count('#'), sfx)
      filenames = [template_format % index for index in indices]
    else:
      filenames = [template]

    # Sort the filenames
    filenames = sorted(filenames)

    # Get the format object
    format_class = Registry.find(filenames[0])

    # Get the first image and our understanding
    first_image = filenames[0]

    # Get the directory and first filename and set the template format
    directory, first_image_name = os.path.split(first_image)
    first_image_number = indices[0]

    # Get the template format
    pfx = template.split('#')[0]
    sfx = template.split('#')[-1]
    template_format = '%s%%0%dd%s' % (pfx, template.count('#'), sfx)

    # Set the image range
    array_range = (min(indices) - 1, max(indices))

    # Create the sweep file list
    filenames = SweepFileList(template_format, array_range)

    # Create the sweep object
    sweep = ImageSweep(MultiFileReader(format_class, filenames))

    # Check the sweep is valid
    if check_headers and not sweep.is_valid():
      raise RuntimeError('Invalid sweep of images')

    # Return the sweep
    return sweep


  @staticmethod
  def make_imageset(filenames, format_class=None, check_format=True):
    '''Create an image set'''
    from dxtbx.format.Registry import Registry
    from format.FormatMultiImage import FormatMultiImage

    # Get the format object
    if format_class == None and check_format:
      format_class = Registry.find(filenames[0])
    if format_class is None:
      reader = NullReader(filenames)
    else:
      if issubclass(format_class, FormatMultiImage):
        assert len(filenames) == 1
        format_instance = format_class(filenames[0])
        reader = SingleFileReader(format_instance)
      else:
        reader = MultiFileReader(format_class, filenames)

    # Return the imageset
    return ImageSet(reader)

  @staticmethod
  def make_sweep(template, indices, format_class=None, beam=None,
                 detector=None, goniometer=None, scan=None,
                 check_format=True):
    '''Create a sweep'''
    import os
    from dxtbx.format.Registry import Registry
    from format.FormatMultiImage import FormatMultiImage

    indices = sorted(indices)

    # Get the template format
    count = template.count('#')
    if count > 0:
      pfx = template.split('#')[0]
      sfx = template.split('#')[-1]
      template_format = '%s%%0%dd%s' % (pfx, template.count('#'), sfx)
      filenames = [template_format % index for index in indices]
    else:
      template_format = None
      filenames = [template]

    # Sort the filenames
    filenames = sorted(filenames)

    # Get the first image and our understanding
    first_image = filenames[0]

    # Get the directory and first filename and set the template format
    directory, first_image_name = os.path.split(first_image)
    first_image_number = indices[0]

    # Set the image range
    array_range = (min(indices) - 1, max(indices))
    if scan is not None:
      assert(array_range == scan.get_array_range())

    # Get the format object and reader
    if format_class is None and check_format:
      format_class = Registry.find(filenames[0])

    # Create the reader
    if format_class is None:
      if template_format is not None:
        filenames = SweepFileList(template_format, array_range)
      reader = NullReader(filenames)
    else:
      if issubclass(format_class, FormatMultiImage):
        assert len(filenames) == 1
        format_instance = format_class(filenames[0])
        reader = SingleFileReader(format_instance)
      else:
        assert(template_format is not None)
        filenames = SweepFileList(template_format, array_range)
        reader = MultiFileReader(format_class, filenames)

    # Create the sweep object
    sweep = ImageSweep(
      reader,
      beam=beam,
      detector=detector,
      goniometer=goniometer,
      scan=scan)

    # Return the sweep
    return sweep
