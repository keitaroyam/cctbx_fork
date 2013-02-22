from __future__ import division
#!/usr/bin/env python
# detector_helpers.py
#   Copyright (C) 2011 Diamond Light Source, Graeme Winter
#
#   This code is distributed under the BSD license, a copy of which is
#   included in the root directory of this package.
#
# Helpers for the detector class...

import math
from scitbx import matrix

def read_xds_xparm(xds_xparm_file):
    '''Parse the XDS XPARM file, which contains a description of the detector
    and experimental geometry, to a dictionary.'''

    data = map(float, open(xds_xparm_file, 'r').read().split())

    assert(len(data) == 42)

    starting_frame = int(data[0])
    phi_start, phi_width = data[1:3]
    axis = data[3:6]

    wavelength = data[6]
    beam = data[7:10]

    nx, ny = map(int, data[10:12])
    px, py = data[12:14]

    distance = data[14]
    ox, oy = data[15:17]

    x, y = data[17:20], data[20:23]
    normal = data[23:26]

    spacegroup = int(data[26])
    cell = data[27:33]

    a, b, c = data[33:36], data[36:39], data[39:42]

    results = {
        'starting_frame':starting_frame,
        'phi_start':phi_start, 'phi_width':phi_width,
        'axis':axis, 'wavelength':wavelength, 'beam':beam,
        'nx':nx, 'ny':ny, 'px':px, 'py':py, 'distance':distance,
        'ox':ox, 'oy':oy, 'x':x, 'y':y, 'normal':normal,
        'spacegroup':spacegroup, 'cell':cell, 'a':a, 'b':b, 'c':c
        }

    return results

def compute_frame_rotation(original, final):
    '''Compute reference frame rotation to rotate from the original frame
    given by original = (x, y, z) to the to reference frame given by
    final = (_x, _y, _z). Returns M where M.x = _x etc.'''

    x, y, z = original
    _x, _y, _z = final

    O = matrix.sqr(x.elems + y.elems + z.elems).transpose()
    assert((O.determinant() - 1.0) < 1.0e-7)

    F = matrix.sqr(_x.elems + _y.elems + _z.elems).transpose()
    assert((F.determinant() - 1.0) < 1.0e-7)

    # #1 rotate about x ^ (1, 0, 0) - if they are not coincident,
    # rotate about _x ^ _y if they are colinear but in opposite
    # directions

    if _x.angle(x) % math.pi:
        _ra_x = _x.cross(x)
        _a_x = _x.angle(x)
    elif math.fabs(_x.angle(x) - math.pi) < 1.0e-7:
        _ra_x = _x.cross(_y)
        _a_x = math.pi
    else:
        _ra_x = _x
        _a_x = 0.0

    _m_x = _ra_x.axis_and_angle_as_r3_rotation_matrix(- _a_x)

    # then rotate z to _z by rotating about _x (which is now coincident
    # with x)

    _ra_z = _x
    _a_z = _z.angle(_m_x * z)
    _m_z = _ra_z.axis_and_angle_as_r3_rotation_matrix(- _a_z)

    _m = _m_z * _m_x

    assert(math.fabs(_m.determinant() - 1.0) < 1.0e-7)

    return _m

def find_undefined_value(cbf_handle):
    '''Given a cbf handle, get the value for the undefined pixel.'''

    cbf_handle.find_category('array_intensities')
    cbf_handle.find_column('undefined_value')
    return cbf_handle.get_doublevalue()

class detector_helper_sensors:
    '''A helper class which allows enumeration of detector sensor technologies
    which should help in identifying specific detectors when needed. These are
    currently limited to IMAGE_PLATE CCD PAD.'''

    SENSOR_CCD = 'SENSOR_CCD'
    SENSOR_PAD = 'SENSOR_PAD'
    SENSOR_IMAGE_PLATE = 'SENSOR_IMAGE_PLATE'
    SENSOR_UNKNOWN = 'SENSOR_UNKNOWN'

    @staticmethod
    def check_sensor(sensor_type):
        if sensor_type in [detector_helper_sensors.SENSOR_CCD,
                           detector_helper_sensors.SENSOR_PAD,
                           detector_helper_sensors.SENSOR_IMAGE_PLATE,
                           detector_helper_sensors.SENSOR_UNKNOWN]:
            return True
        return False

    @staticmethod
    def all():
        return [detector_helper_sensors.SENSOR_CCD,
                detector_helper_sensors.SENSOR_PAD,
                detector_helper_sensors.SENSOR_IMAGE_PLATE]
