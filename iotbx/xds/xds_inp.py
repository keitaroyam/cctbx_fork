#!/usr/bin/env libtbx.python
#
# iotbx.xds.xds_inp.py
#
#   James Parkhurst, Richard Gildea, Diamond Light Source, 2014
#
#   Class to read all the data from a XDS.INP file
#
from __future__ import division

class reader:
  """A class to read the XDS.INP file used in XDS"""

  def __init__(self):
    pass

  @staticmethod
  def is_xds_inp_file(filename):
    """Check if the given file is an XDS.INP file.

    Params:
      filename The XDS.INP filename

    Returns:
      True/False the file is a XDS.INP file

    """
    import os
    return os.path.basename(filename) == 'XDS.INP'

  def read_file(self, filename, check_filename = True):
    """Read the XDS.INP file.

    See http://xds.mpimf-heidelberg.mpg.de/html_doc/xds_files.html for more
    information about the file format.

    Param:
      filename The path to the file

    """

    # defaults
    self.unit_cell_constants = None
    self.minimum_valid_pixel_value = 0
    self.corrections = None
    self.trusted_region = None
    self.maximum_number_of_processor = 32
    self.fraction_of_polarization = 0.5
    self.polarization_plane_normal = None
    self.starting_angle = 0.0
    #STARTING_FRAME=first data image (as specified by DATA_RANGE=)
    self.starting_frame = None
    self.include_resolution_range = [20.0, 0.0]
    self.unit_cell_constants = None
    self.space_group_number = 1
    self.max_fac_rmeas = 2.0
    self.data_range = None

    # Check and read file
    if reader.is_xds_inp_file(filename):
      lines = open(filename, 'r').readlines()
    else:
      raise IOError("{0} is not a XDS.INP file".format(filename))

    # Parse the tokens
    self.parse_lines(lines)

  def parse_lines(self, lines):
    """Parse the lines

    Param:
      tokens The list of lines

    """
    import re
    parameters = []
    self.untrusted_rectangle = []
    for record in lines:
      comment_char = record.find("!")
      if comment_char > -1:
        record = record[0:comment_char]
      record = record.strip()
      tok = [c for c in re.split(r' |\t', record) if c != '']
      tokens = []
      for t in tok:
        i = t.find('=')
        if i > -1:
          tokens.append(t[:i+1])
          if (i+1) < len(t):
            tokens.append(t[i+1:])
        else:
          tokens.append(t)
      while len(tokens):
        if len(tokens) == 1:
          assert tokens[0].find('=') > -1
          parameters.append(tokens)
          break
        for i_tok, t in enumerate(tokens):
          if i_tok == 0:
            assert t.find('=') > -1
          elif i_tok > 0 and t.find('=') > -1:
            parameters.append((tokens[0:i_tok]))
            tokens = tokens[i_tok:]
            break
          elif (i_tok+1) == len(tokens):
            parameters.append(tokens)
            tokens = []
            break

    for parameter in parameters:
      name = parameter[0]
      if name == 'DETECTOR=':
        self.detector = " ".join(parameter[1:])
      elif name == 'MINIMUM_VALID_PIXEL_VALUE=':
        self.minimum_valid_pixel_value = float(parameter[1])
      elif name == 'OVERLOAD=':
        self.overload = int(parameter[1])
      elif name == 'CORRECTIONS=':
        if len(parameter) == 1:
          self.corrections = None
        else:
          self.corrections = parameter[1]
      elif name == 'DIRECTION_OF_DETECTOR_X-AXIS=':
        self.direction_of_detector_x_axis = map(float, parameter[-3:])
      elif name == 'DIRECTION_OF_DETECTOR_Y-AXIS=':
        self.direction_of_detector_y_axis = map(float, parameter[-3:])
      elif name == 'TRUSTED_REGION=':
        self.trusted_region = map(float, parameter[-2:])
      elif name == 'SENSOR_THICKNESS=':
        self.sensor_thickness = float(parameter[1])
      elif name == 'UNTRUSTED_RECTANGLE=':
        self.untrusted_rectangle.append(map(int, parameter[-4:]))
      elif name == 'MAXIMUM_NUMBER_OF_PROCESSORS=':
        self.maximum_number_of_processor = int(parameter[1])
      elif name == 'NX=':
        self.nx = int(parameter[1])
      elif name == 'NY=':
        self.ny = int(parameter[1])
      elif name == 'QX=':
        self.px = float(parameter[1])
      elif name == 'QY=':
        self.py = float(parameter[1])
      elif name == 'ORGX=':
        self.orgx = float(parameter[1])
      elif name == 'ORGY=':
        self.orgy = float(parameter[1])
      elif name == 'ROTATION_AXIS=':
        self.rotation_axis = map(float, parameter[-3:])
      elif name == 'DETECTOR_DISTANCE=':
        self.detector_distance = float(parameter[1])
      elif name == 'X-RAY_WAVELENGTH=':
        self.xray_wavelength = float(parameter[1])
      elif name == 'INCIDENT_BEAM_DIRECTION=':
        self.incident_beam_direction = map(float, parameter[-3:])
      elif name == 'FRACTION_OF_POLARIZATION=':
        self.fraction_of_polarization = float(parameter[-1])
      elif name == 'POLARIZATION_PLANE_NORMAL=':
        self.polarization_plane_normal = map(float, parameter[-3:])
      elif name == 'FRIEDEL\'S_LAW=':
        self.friedels_law = bool(parameter[-1])
      elif name == 'NAME_TEMPLATE_OF_DATA_FRAMES=':
        self.name_template_of_data_frames = parameter[1:]
      elif name == 'STARTING_ANGLE=':
        self.starting_angle = float(parameter[1])
      elif name == 'STARTING_FRAME=':
        self.starting_frame = float(parameter[1])
      elif name == 'INCLUDE_RESOLUTION_RANGE=':
        self.include_resolution_range = map(float, parameter[-2:])
      elif name == 'UNIT_CELL_CONSTANTS=':
        self.unit_cell_constants = map(float, parameter[-6:])
      elif name == 'SPACE_GROUP_NUMBER=':
        self.space_group_number = int(parameter[-1])
      elif name == 'MAX_FAC_Rmeas=':
        self.max_fac_rmeas = float(parameter[-1])
      elif name == 'DATA_RANGE=':
        self.data_range = map(int, parameter[-2:])
