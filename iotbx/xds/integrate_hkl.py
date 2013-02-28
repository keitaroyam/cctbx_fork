#!/usr/bin/env libtbx.python
#
# iotbx.xds.integrate_hkl.py
#
#   James Parkhurst, Diamond Light Source, 2012/OCT/16
#
#   Class to read all the data from an INTEGRATE.HKL file
#
class reader:
    """A class to read the INTEGRATE.HKL file used in XDS"""

    def __init__(self):
        """Initialise the file contents."""
        self._header = {}
        self.hkl = []
        self.iobs = []
        self.sigma = []
        self.xyzcal = []
        self.rlp = []
        self.peak = []
        self.corr = []
        self.maxc = []
        self.xyzobs = []
        self.alfbet0 = []
        self.alfbet1 = []
        self.psi = []

    @staticmethod
    def is_integrate_hkl_file(filename):
        '''Check that the file is identified as an INTEGRATE.HKL

        Params:
            filename The path to the file

        Returns:
            True/False Is the file an INTEGRATE.HKL file

        '''
        return open(filename, 'r').read(26) == '!OUTPUT_FILE=INTEGRATE.HKL'

    def read_file(self, filename):
        """Read the INTEGRATE.HKL file.

        See http://xds.mpimf-heidelberg.mpg.de/html_doc/xds_files.html for more
        information about the file format.

        Params:
            filename The path to the file

        """

        # Check the file is an INTEGRATE.HKL file
        if not reader.is_integrate_hkl_file(filename):
            raise IOError("{0} is not an INTEGRATE.HKL file".format(filename))

        # Read the lines from the file
        lines = open(filename, 'r').readlines()

        # Loop through the lines in the file. First off, parse the header
        # lines until we reach !END_OF_HEADER. Then parse the data lines
        # until we read !END_OF_DATA
        in_header = True
        for l in lines:
            if in_header:
                if l.strip().startswith('!END_OF_HEADER'):
                    in_header = False
                    continue
                else:
                    if not l.strip().startswith('!'):
                        continue
                    self._parse_header_line(l.strip()[1:])
            else:
                if l.strip().startswith('!END_OF_DATA'):
                    break
                else:
                    self._parse_data_line(l)

        # Set the header parameters
        self._set_header_parameters()

    def _parse_str(self, s):
        """Parse a string to either an int, float or string

        Params:
            s The input string

        Returns:
            The parsed value

        """
        try:
            return int(s)
        except ValueError:
            try:
                return float(s)
            except ValueError:
                return str(s)

    def _parse_value(self, value):
        """Parse the value or array of values contained in the string

        Params:
            value The value to parse

        Returns:
            The parsed value

        """
        values = value.split()
        if len(values) == 1:
            return self._parse_str(values[0])
        else:
            return tuple([self._parse_str(s) for s in values])

    def _set_header_parameters(self):
        """Get the parameters from the header dict

        """
        self.space_group       = self._header['SPACE_GROUP_NUMBER']
        self.unit_cell         = self._header['UNIT_CELL_CONSTANTS']
        self.detector_size     = (self._header['NX'], self._header['NY'])
        self.pixel_size        = (self._header['QX'], self._header['QY'])
        self.starting_frame    = self._header['STARTING_FRAME']
        self.starting_angle    = self._header['STARTING_ANGLE']
        self.oscillation_range = self._header['OSCILLATION_RANGE']
        self.rotation_axis     = self._header['ROTATION_AXIS']
        self.wavelength        = self._header['X-RAY_WAVELENGTH']
        self.beam_vector       = self._header['INCIDENT_BEAM_DIRECTION']
        self.detector_x_axis   = self._header['DIRECTION_OF_DETECTOR_X-AXIS']
        self.detector_y_axis   = self._header['DIRECTION_OF_DETECTOR_Y-AXIS']
        self.detector_origin   = (self._header['ORGX'], self._header['ORGY'])
        self.detector_distance = self._header['DETECTOR_DISTANCE']
        self.unit_cell_a_axis  = self._header['UNIT_CELL_A-AXIS']
        self.unit_cell_b_axis  = self._header['UNIT_CELL_B-AXIS']
        self.unit_cell_c_axis  = self._header['UNIT_CELL_C-AXIS']
        self.sigma_divergence  = self._header['BEAM_DIVERGENCE_E.S.D.']
        self.sigma_mosaicity   = self._header['REFLECTING_RANGE_E.S.D.']
        self.template          = self._header['NAME_TEMPLATE_OF_DATA_FRAMES']
        self.detector_type     = self._header['DETECTOR']
        self.minpk             = self._header['MINPK']
        self.cut               = self._header['CUT']
        self.variance_model    = self._header['VARIANCE_MODEL']
        del(self._header)

    def _parse_header_line(self, line):
        """Parse a line that has been identified as a header line

        Params:
          line The line to parse

        """
        name_value = line.split('=')
        if (len(name_value) < 2):
            return

        name = name_value[0]
        if (len(name_value) > 2):
            for i in range(1, len(name_value)-1):
                value_name = name_value[i].split()
                value = ''.join(value_name[:-1])
                self._header[name] = self._parse_value(value)
                name = value_name[-1]

        value = name_value[-1]
        self._header[name] = self._parse_value(value)

    def _parse_data_line(self, line):
        """Parse a data line from the Integrate.hkl file

        Params:
            line The line to parse

        """
        # Split the tokens
        tokens = line.split()
        tokens = map(int, tokens[0:3]) + map(float, tokens[3:])

        # Get the reflection information and append to the lists
        self.hkl.append(tuple(tokens[0:3]))
        self.iobs.append(tokens[3])
        self.sigma.append(tokens[4])
        self.xyzcal.append(tuple(tokens[5:8]))
        self.rlp.append(tokens[8])
        self.peak.append(tokens[9])
        self.corr.append(tokens[10])
        self.maxc.append(tokens[11])
        self.xyzobs.append(tuple(tokens[12:15]))
        self.alfbet0.append(tuple(tokens[15:17]))
        self.alfbet1.append(tuple(tokens[17:19]))
        self.psi.append(tokens[19])
