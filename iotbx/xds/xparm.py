#!/usr/bin/env libtbx.python
#
# iotbx.xds.xparm.py
#
#   Copyright (C) 2013 Diamond Light Source, James Parkhurst & Richard Gildea
#
#   Class to read all the data from a (G)XPARM.XDS file
#
from __future__ import division
import sys
from libtbx import adopt_init_args

class reader(object):
  """A class to read the XPARM.XDS/GXPARM.XDS file used in XDS"""

  def __init__(self):
    pass

  @staticmethod
  def find_version(filename):
    """Check the version if the given file is a (G)XPARM.XDS file.

    If the file contains exactly 11 lines and 42 tokens, it is the old style
    version 1 file. If the file starts with XPARM.XDS it is the new style
    version 2 file.

    Params:
      filename The (G)XPARM.XDS filename

    Returns:
      The version or None if the file is not recognised

    """

    # Check file contains 11 lines and 42 tokens
    with open(filename, 'r') as file_handle:
      tokens = []
      old_style = True
      for count, line in enumerate(file_handle):
        line_tokens = line.split()
        if count == 0:
          if len(line_tokens) == 1 and line_tokens[0] == 'XPARM.XDS':
              old_style=False
        if old_style:
          if count+1 > 11:
            return None
        else:
          if count+1 > 14:
            return None
        tokens.extend(line_tokens)

      if old_style:
        if count+1 != 11 or len(tokens) != 42:
          return None

    # Is a (G)XPARM.XDS file
    if old_style:
      return 1
    else:
      return 2

  @staticmethod
  def is_xparm_file(filename, check_filename = True):
    """Check if the given file is a (G)XPARM.XDS file.

    Ensure it is named correctly and contains exactly 11 lines and 42
    tokens, otherwise return False.

    Params:
      filename The (G)XPARM.XDS filename

    Returns:
      True/False the file is a (G)XPARM.XDS file

    """
    return reader.find_version(filename) != None

  def read_file(self, filename, check_filename = True):
    """Read the XPARM.XDS/GXPARAM.XDS file.

    See http://xds.mpimf-heidelberg.mpg.de/html_doc/xds_files.html for more
    information about the file format.

    Param:
      filename The path to the file

    """

    # Check version and read file
    version = reader.find_version(filename)
    if version != None:
      tokens = [l.split() for l in open(filename, 'r').readlines()]
    else:
      raise IOError("{0} is not a (G)XPARM.XDS file".format(filename))

    # Parse the tokens
    if version == 1:
      self.parse_version_1_tokens(tokens)
    else:
      self.parse_version_2_tokens(tokens)

  def parse_version_1_tokens(self, tokens):
    """Parse the version 1 tokens

    Param:
      tokens The list of tokens

    """
    # Scan and goniometer stuff
    self.starting_frame    = int(tokens[0][0])
    self.starting_angle    = float(tokens[0][1])
    self.oscillation_range = float(tokens[0][2])
    self.rotation_axis     = tuple(map(float, tokens[0][3:6]))

    # Beam stuff
    self.wavelength        = float(tokens[1][0])
    self.beam_vector       = tuple(map(float, tokens[1][1:4]))

    # Detector stuff
    self.num_segments      = None
    self.detector_size     = tuple(map(int, tokens[2][0:2]))
    self.pixel_size        = tuple(map(float, tokens[2][2:4]))
    self.detector_distance = float(tokens[3][0])
    self.detector_origin   = tuple(map(float, tokens[3][1:3]))
    self.detector_x_axis   = tuple(map(float, tokens[4]))
    self.detector_y_axis   = tuple(map(float, tokens[5]))
    self.detector_normal   = tuple(map(float, tokens[6]))

    # Crystal stuff
    self.space_group       = int(tokens[7][0])
    self.unit_cell         = tuple(map(float, tokens[7][1:7]))
    self.unit_cell_a_axis  = tuple(map(float, tokens[8]))
    self.unit_cell_b_axis  = tuple(map(float, tokens[9]))
    self.unit_cell_c_axis  = tuple(map(float, tokens[10]))

  def parse_version_2_tokens(self, tokens):
    """Parse the version 2 tokens

    Param:
      tokens The list of tokens

    """
    # Scan and goniometer stuff
    self.starting_frame    = int(tokens[1][0])
    self.starting_angle    = float(tokens[1][1])
    self.oscillation_range = float(tokens[1][2])
    self.rotation_axis     = tuple(map(float, tokens[1][3:6]))

    # Beam stuff
    self.wavelength        = float(tokens[2][0])
    self.beam_vector       = tuple(map(float, tokens[2][1:4]))

    # Crystal stuff
    self.space_group       = int(tokens[3][0])
    self.unit_cell         = tuple(map(float, tokens[3][1:7]))
    self.unit_cell_a_axis  = tuple(map(float, tokens[4]))
    self.unit_cell_b_axis  = tuple(map(float, tokens[5]))
    self.unit_cell_c_axis  = tuple(map(float, tokens[6]))

    # Detector stuff
    self.num_segments      = int(tokens[7][0])
    self.detector_size     = tuple(map(int, tokens[7][1:3]))
    self.pixel_size        = tuple(map(float, tokens[7][3:5]))
    self.detector_origin   = tuple(map(float, tokens[8][0:2]))
    self.detector_distance = float(tokens[8][2])
    self.detector_x_axis   = tuple(map(float, tokens[9]))
    self.detector_y_axis   = tuple(map(float, tokens[10]))
    self.detector_normal   = tuple(map(float, tokens[11]))

    # Loop through all the segments
    self.segments = []
    self.orientation = []
    for i in range(self.num_segments):
        self.segments.append(tuple(map(int, tokens[12+i*2])))
        self.orientation.append(tuple(map(float, tokens[12+i*2+1])))


class writer(object):

  def __init__(self,
               starting_frame,
               starting_angle,
               oscillation_range,
               rotation_axis,
               wavelength,
               beam_vector,
               space_group,
               unit_cell,
               unit_cell_a_axis,
               unit_cell_b_axis,
               unit_cell_c_axis,
               num_segments,
               detector_size,
               pixel_size,
               detector_origin,
               detector_distance,
               detector_x_axis,
               detector_y_axis,
               detector_normal,
               segments=None,
               orientation=None):
    adopt_init_args(self, locals())
    if [num_segments, segments, orientation].count(None) == 3:
      self.num_segments = 1
      self.segments = []
      self.orientation = []
      for i in range(self.num_segments):
        self.segments.append(
          (i+1, 1, self.detector_size[0], 1, self.detector_size[1]))
        self.orientation.append((0, 0, 0, 1, 0, 0, 0, 1, 0))

  def show(self, out=None):
    """
    http://xds.mpimf-heidelberg.mpg.de/html_doc/xds_files.html#XPARM.XDS
    """
    if out is None:
      out = sys.stdout
    print >> out, "XPARM.XDS"
    print >> out, "%6i %13.4f %9.4f" %(
      self.starting_frame, self.starting_angle, self.oscillation_range),
    print >> out, "%9.6f %9.6f %9.6f" %(self.rotation_axis)
    print >> out, " %14.6f" %self.wavelength,
    print >> out, "%14.6f %14.6f %14.6f" %(self.beam_vector)
    print >> out, "   %3i" %(self.space_group),
    print >> out, "%11.4f %11.4f %11.4f %7.3f %7.3f %7.3f" %self.unit_cell
    print >> out, " %14.6f  %14.6f  %14.6f" %self.unit_cell_a_axis
    print >> out, " %14.6f  %14.6f  %14.6f" %self.unit_cell_b_axis
    print >> out, " %14.6f  %14.6f  %14.6f" %self.unit_cell_c_axis
    print >> out, " %8i %9i %9i %11.6f %11.6f" %(
      self.num_segments, self.detector_size[0], self.detector_size[1],
      self.pixel_size[0], self.pixel_size[1])
    print >> out, " %14.6f %14.6f" %self.detector_origin,
    print >> out, " %14.6f" %self.detector_distance
    print >> out, " %14.6f %14.6f %14.6f" %self.detector_x_axis
    print >> out, " %14.6f %14.6f %14.6f" %self.detector_y_axis
    print >> out, " %14.6f %14.6f %14.6f" %self.detector_normal
    for i in range(self.num_segments):
      print >> out, " %9i %9i %9i %9i %9i" %tuple(self.segments[i])
      print >> out, "".join([" %7.2f"*3] + [" %8.5f"]*6) %tuple(self.orientation[i])

  def write_file(self, filename):
    with open(filename, 'wb') as f:
      self.show(out=f)
