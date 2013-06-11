from __future__ import division
import math
import random
from scitbx import matrix
from cctbx import sgtbx

class coordinate_frame_information:
    '''A bucket class to store coordinate frame information.'''

    def __init__(self, detector_origin, detector_fast, detector_slow,
                 detector_size_fast_slow, detector_pixel_size_fast_slow,
                 rotation_axis, sample_to_source, wavelength,
                 real_space_a = None, real_space_b = None,
                 real_space_c = None, space_group_number = None,
                 sigma_divergence = None,
                 mosaicity = None,
                 starting_angle = None, oscillation_range = None,
                 starting_frame = None):

        self._detector_origin = detector_origin
        self._detector_fast = detector_fast
        self._detector_slow = detector_slow
        self._detector_size_fast_slow = detector_size_fast_slow
        self._detector_pixel_size_fast_slow = detector_pixel_size_fast_slow
        self._rotation_axis = rotation_axis
        self._sample_to_source = sample_to_source
        self._wavelength = wavelength
        self._real_space_a = real_space_a
        self._real_space_b = real_space_b
        self._real_space_c = real_space_c
        self._space_group_number = space_group_number
        self._sigma_divergence = sigma_divergence
        self._mosaicity = mosaicity
        self._starting_angle = starting_angle
        self._oscillation_range = oscillation_range
        self._starting_frame = starting_frame

        self._R_to_CBF = None
        self._R_to_Rossmann = None
        self._R_to_Mosflm = None

        return

    def get_detector_origin(self):
        return self._detector_origin

    def get_detector_fast(self):
        return self._detector_fast

    def get_detector_slow(self):
        return self._detector_slow

    def get_rotation_axis(self):
        return self._rotation_axis

    def get_sample_to_source(self):
        return self._sample_to_source

    def get_wavelength(self):
        return self._wavelength

    def get_real_space_a(self):
        return self._real_space_a

    def get_real_space_b(self):
        return self._real_space_b

    def get_real_space_c(self):
        return self._real_space_c

    def get_space_group_number(self):
        return self._space_group_number

    def get(self, parameter_name):
        if not hasattr(self, '_%s' % parameter_name):
            raise RuntimeError, 'no parameter %s' % parameter_name
        return getattr(self, '_%s' % parameter_name)

    def R_to_CBF(self):

        if not self._R_to_CBF:
            self._R_to_CBF = align_reference_frame(
                self._rotation_axis, (1.0, 0.0, 0.0),
                self._sample_to_source, (0.0, 0.0, 1.0))

        return self._R_to_CBF

    def R_to_Rossmann(self):

        if not self._R_to_Rossmann:
            self._R_to_Rossmann = align_reference_frame(
                self._sample_to_source, (0.0, 0.0, - 1.0),
                self._rotation_axis, (0.0, 1.0, 0.0))

        return self._R_to_Rossmann

    def R_to_Mosflm(self):

        if not self._R_to_Mosflm:
            self._R_to_Mosflm = align_reference_frame(
                self._sample_to_source, (- 1.0, 0.0, 0.0),
                self._rotation_axis, (0.0, 0.0, 1.0))

        return self._R_to_Mosflm

def orthogonal_component(reference, changing):
    '''Return unit vector corresponding to component of changing orthogonal to
    reference.'''

    r = reference.normalize()
    c = changing.normalize()

    return (c - c.dot(r) * r).normalize()

def align_reference_frame(primary_axis, primary_target,
                          secondary_axis, secondary_target):
    '''Compute a rotation matrix R: R x primary_axis = primary_target and
    R x secondary_axis places the secondary_axis in the plane perpendicular
    to the primary_target, as close as possible to the secondary_target.
    Require: primary_target orthogonal to secondary_target, primary axis
    not colinear with secondary axis.'''

    if type(primary_axis) == type(()) or type(primary_axis) == type([]):
        primary_axis = matrix.col(primary_axis).normalize()
    else:
        primary_axis = primary_axis.normalize()

    if type(primary_target) == type(()) or type(primary_target) == type([]):
        primary_target = matrix.col(primary_target).normalize()
    else:
        primary_target = primary_target.normalize()

    if type(secondary_axis) == type(()) or type(secondary_axis) == type([]):
        secondary_axis = matrix.col(secondary_axis).normalize()
    else:
        secondary_axis = secondary_axis.normalize()

    if type(secondary_target) == type(()) or \
           type(secondary_target) == type([]):
        secondary_target = matrix.col(secondary_target).normalize()
    else:
        secondary_target = secondary_target.normalize()

    # check properties of input axes

    assert(math.fabs(primary_axis.angle(secondary_axis) % math.pi) > 0.001)
    assert(primary_target.dot(secondary_target) < 0.001)

    if primary_target.angle(primary_axis) % math.pi:
        axis_p = primary_target.cross(primary_axis)
        angle_p = - primary_target.angle(primary_axis)
        Rprimary = axis_p.axis_and_angle_as_r3_rotation_matrix(angle_p)
    elif primary_target.angle(primary_axis) < 0:
        axis_p = primary_axis.ortho().normalize()
        angle_p = math.pi
        Rprimary = axis_p.axis_and_angle_as_r3_rotation_matrix(angle_p)
    else:
        Rprimary = matrix.identity(3)

    axis_r = secondary_target.cross(Rprimary * secondary_axis)
    axis_s = primary_target
    if (axis_r.angle(primary_target) > 0.5 * math.pi):
        angle_s = orthogonal_component(axis_s, secondary_target).angle(
            orthogonal_component(axis_s, Rprimary * secondary_axis))
    else:
        angle_s = - orthogonal_component(axis_s, secondary_target).angle(
            orthogonal_component(axis_s, Rprimary * secondary_axis))

    Rsecondary = axis_s.axis_and_angle_as_r3_rotation_matrix(angle_s)

    return Rsecondary * Rprimary

def is_xds_xparm(putative_xds_xparm_file):
    '''See if this file looks like an XDS XPARM file i.e. it consists of 42
    floating point values and nothing else.'''
    from iotbx.xds import xparm
    return xparm.reader.is_xparm_file(putative_xds_xparm_file)

def is_xds_integrate_hkl(putative_integrate_hkl_file):
    '''See if this looks like an XDS INTEGRATE.HKL file.'''

    first_record = open(putative_integrate_hkl_file).readline()

    if '!OUTPUT_FILE=INTEGRATE.HKL' in first_record:
        return True

    return False

def is_xds_ascii_hkl(putative_xds_ascii_hkl_file):
    '''See if this looks like an XDS INTEGRATE.HKL file.'''

    lines = open(putative_xds_ascii_hkl_file).readlines()
    if len(lines) < 2:
        return False

    if '!OUTPUT_FILE=XDS_ASCII.HKL' in lines[1]:
        return True

    return False

def is_recognized_file(filename):
    ''' Check if the file is recognized.'''
    if is_xds_xparm(filename):
        return True
    elif is_xds_integrate_hkl(filename):
        return True
    elif is_xds_ascii_hkl(filename):
        return True

    # Not recognices
    return False

def import_xds_integrate_hkl(integrate_hkl_file):
    '''Read an XDS INTEGRATE.HKL file, transform the parameters contained therein
    into the standard coordinate frame, record this as a dictionary.'''

    assert(is_xds_integrate_hkl(integrate_hkl_file))

    header = []

    for record in open(integrate_hkl_file):
        if not record.startswith('!'):
            break

        header.append(record)

    # now need to dig out the values I want, convert and return

    for record in header:
        if record.startswith('!ROTATION_AXIS='):
            axis = map(float, record.split()[-3:])
            continue
        if record.startswith('!INCIDENT_BEAM_DIRECTION='):
            beam = map(float, record.split()[-3:])
            continue
        if record.startswith('!DIRECTION_OF_DETECTOR_X-AXIS='):
            x = map(float, record.split()[-3:])
            continue
        if record.startswith('!DIRECTION_OF_DETECTOR_Y-AXIS='):
            y = map(float, record.split()[-3:])
            continue
        if record.startswith('!UNIT_CELL_A-AXIS='):
            a = map(float, record.split()[-3:])
            continue
        if record.startswith('!UNIT_CELL_B-AXIS='):
            b = map(float, record.split()[-3:])
            continue
        if record.startswith('!UNIT_CELL_C-AXIS='):
            c = map(float, record.split()[-3:])
            continue
        if record.startswith('!X-RAY_WAVELENGTH='):
            wavelength = float(record.split()[-1])
            continue
        if record.startswith('!DETECTOR_DISTANCE='):
            distance = float(record.split()[-1])
            continue
        if record.startswith('!SPACE_GROUP_NUMBER='):
            space_group_number = int(record.split()[-1])
            continue
        if record.startswith('!BEAM_DIVERGENCE_E.S.D.'):
            sigma_divergence = float(record.split()[-1])
            continue
        if record.startswith('!REFLECTING_RANGE_E.S.D.'):
            mosaicity = float(record.split()[-1])
            continue
        if record.startswith('!NX='):
            nx = int(record.split()[1])
            ny = int(record.split()[3])
            px = float(record.split()[5])
            py = float(record.split()[7])
            continue
        if record.startswith('!ORGX='):
            ox = float(record.split()[1])
            oy = float(record.split()[3])
            continue
        if record.startswith('!STARTING_FRAME'):
            starting_frame = int(record.split()[-1])
            continue
        if record.startswith('!STARTING_ANGLE'):
            starting_angle = float(record.split()[-1])
            continue
        if record.startswith('!OSCILLATION_RANGE'):
            oscillation_range = float(record.split()[-1])
            continue

    # XDS defines the beam vector as s0 rather than from sample -> source.
    # Keep in mind that any inversion of a vector needs to be made with great
    # care!

    B = - matrix.col(beam).normalize()
    A = matrix.col(axis).normalize()

    X = matrix.col(x).normalize()
    Y = matrix.col(y).normalize()
    N = X.cross(Y)

    _X = matrix.col([1, 0, 0])
    _Y = matrix.col([0, 1, 0])
    _Z = matrix.col([0, 0, 1])

    R = align_reference_frame(A, _X, B, _Z)

    detector_origin = R * (distance * N - ox * px * X - oy * py * Y)
    detector_fast = R * X
    detector_slow = R * Y
    rotation_axis = R * A
    sample_to_source = R * B
    real_space_a = R * matrix.col(a)
    real_space_b = R * matrix.col(b)
    real_space_c = R * matrix.col(c)

    return coordinate_frame_information(
        detector_origin, detector_fast, detector_slow, (nx, ny), (px, py),
        rotation_axis, sample_to_source, wavelength,
        real_space_a, real_space_b, real_space_c, space_group_number,
        sigma_divergence, mosaicity,
        starting_angle, oscillation_range, starting_frame)

def import_xds_ascii_hkl(xds_ascii_hkl_file):
    '''Read an XDS INTEGRATE.HKL file, transform the parameters contained therein
    into the standard coordinate frame, record this as a dictionary.'''

    assert(is_xds_ascii_hkl(xds_ascii_hkl_file))

    header = []

    for record in open(xds_ascii_hkl_file):
        if not record.startswith('!'):
            break

        header.append(record)

    # now need to dig out the values I want, convert and return

    for record in header:
        if record.startswith('!ROTATION_AXIS='):
            axis = map(float, record.split()[-3:])
            continue
        if record.startswith('!INCIDENT_BEAM_DIRECTION='):
            beam = map(float, record.split()[-3:])
            continue
        if record.startswith('!DIRECTION_OF_DETECTOR_X-AXIS='):
            x = map(float, record.split()[-3:])
            continue
        if record.startswith('!DIRECTION_OF_DETECTOR_Y-AXIS='):
            y = map(float, record.split()[-3:])
            continue
        if record.startswith('!UNIT_CELL_A-AXIS='):
            a = map(float, record.split()[-3:])
            continue
        if record.startswith('!UNIT_CELL_B-AXIS='):
            b = map(float, record.split()[-3:])
            continue
        if record.startswith('!UNIT_CELL_C-AXIS='):
            c = map(float, record.split()[-3:])
            continue
        if record.startswith('!X-RAY_WAVELENGTH='):
            wavelength = float(record.split()[-1])
            continue
        if record.startswith('!DETECTOR_DISTANCE='):
            distance = float(record.split()[-1])
            continue
        if record.startswith('!SPACE_GROUP_NUMBER='):
            space_group_number = int(record.split()[-1])
            continue
        if record.startswith('!BEAM_DIVERGENCE_E.S.D.'):
            sigma_divergence = float(record.split()[-1])
            continue
        if record.startswith('!REFLECTING_RANGE_E.S.D.'):
            mosaicity = float(record.split()[-1])
            continue
        if record.startswith('!NX='):
            nx = int(record.split()[1])
            ny = int(record.split()[3])
            px = float(record.split()[5])
            py = float(record.split()[7])
            continue
        if record.startswith('!ORGX='):
            ox = float(record.split()[1])
            oy = float(record.split()[3])
            continue
        if record.startswith('!STARTING_FRAME'):
            starting_frame = int(record.split()[-1])
            continue
        if record.startswith('!STARTING_ANGLE'):
            starting_angle = float(record.split()[-1])
            continue
        if record.startswith('!OSCILLATION_RANGE'):
            oscillation_range = float(record.split()[-1])
            continue

    # XDS defines the beam vector as s0 rather than from sample -> source.
    # Keep in mind that any inversion of a vector needs to be made with great
    # care!

    B = - matrix.col(beam).normalize()
    A = matrix.col(axis).normalize()

    X = matrix.col(x).normalize()
    Y = matrix.col(y).normalize()
    N = X.cross(Y)

    _X = matrix.col([1, 0, 0])
    _Y = matrix.col([0, 1, 0])
    _Z = matrix.col([0, 0, 1])

    R = align_reference_frame(A, _X, B, _Z)

    detector_origin = R * (distance * N - ox * px * X - oy * py * Y)
    detector_fast = R * X
    detector_slow = R * Y
    rotation_axis = R * A
    sample_to_source = R * B
    real_space_a = R * matrix.col(a)
    real_space_b = R * matrix.col(b)
    real_space_c = R * matrix.col(c)

    return coordinate_frame_information(
        detector_origin, detector_fast, detector_slow, (nx, ny), (px, py),
        rotation_axis, sample_to_source, wavelength,
        real_space_a, real_space_b, real_space_c, space_group_number,
        sigma_divergence, mosaicity,
        starting_angle, oscillation_range, starting_frame)

def import_xds_xparm(xparm_file):
    '''Read an XDS XPARM file, transform the parameters contained therein
    into the standard coordinate frame, record this as a dictionary.'''
    from iotbx.xds import xparm

    handle = xparm.reader()
    handle.read_file(xparm_file)

    # first determine the rotation R from the XDS coordinate frame used in
    # the processing to the central (i.e. imgCIF) coordinate frame. N.B.
    # if the scan was e.g. a PHI scan the resulting frame could well come out
    # a little odd...

    axis = handle.rotation_axis
    beam = handle.beam_vector
    x, y = handle.detector_x_axis, handle.detector_y_axis

    # XDS defines the beam vector as s0 rather than from sample -> source.

    B = - matrix.col(beam).normalize()
    A = matrix.col(axis).normalize()

    X = matrix.col(x).normalize()
    Y = matrix.col(y).normalize()
    N = X.cross(Y)

    _X = matrix.col([1, 0, 0])
    _Y = matrix.col([0, 1, 0])
    _Z = matrix.col([0, 0, 1])

    R = align_reference_frame(A, _X, B, _Z)

    # now transform contents of the XPARM file to the form which we want to
    # return...

    nx, ny = handle.detector_size
    px, py = handle.pixel_size

    distance = handle.detector_distance
    ox, oy = handle.detector_origin

    a = handle.unit_cell_a_axis
    b = handle.unit_cell_b_axis
    c = handle.unit_cell_c_axis

    detector_origin = R * (distance * N - ox * px * X - oy * py * Y)
    detector_fast = R * X
    detector_slow = R * Y
    rotation_axis = R * A
    sample_to_source = R * B
    wavelength = handle.wavelength
    real_space_a = R * matrix.col(a)
    real_space_b = R * matrix.col(b)
    real_space_c = R * matrix.col(c)
    space_group_number = handle.space_group
    starting_angle = handle.starting_angle
    oscillation_range = handle.oscillation_range
    starting_frame = handle.starting_frame

    return coordinate_frame_information(
        detector_origin, detector_fast, detector_slow, (nx, ny), (px, py),
        rotation_axis, sample_to_source, wavelength,
        real_space_a, real_space_b, real_space_c, space_group_number,
        None, None, starting_angle, oscillation_range, starting_frame)

def test_align_reference_frame():

    _i = (1, 0, 0)
    _j = (0, 1, 0)
    _k = (0, 0, 1)

    primary_axis = _i
    primary_target = _i
    secondary_axis = _k
    secondary_target = _k

    m = align_reference_frame(primary_axis, primary_target,
                              secondary_axis, secondary_target)

    i = matrix.identity(3)

    for j in range(9):
        assert(math.fabs(m.elems[j] - i.elems[j]) < 0.001)

    primary_axis = _j
    primary_target = _i
    secondary_axis = _k
    secondary_target = _k

    m = align_reference_frame(primary_axis, primary_target,
                              secondary_axis, secondary_target)

    for j in range(3):
        assert(math.fabs((m * primary_axis).elems[j] -
                         matrix.col(primary_target).elems[j]) < 0.001)

def test_align_reference_frame_dw():

    s = math.sqrt(0.5)

    pa = [s, s, 0]
    pt = [1, 0, 0]
    sa = [- s, s, 0]
    st = [0, 1, 0]

    R = align_reference_frame(pa,pt,sa,st)

    print R * pa
    print pt
    print R * sa
    print st

def random_orthogonal_vectors():
    v1 = matrix.col((random.random(), random.random(),
                     random.random())).normalize()
    v2 = v1.ortho().normalize()

    return v1, v2

def test_align_reference_frame_brute():

    for j in range(10000):
        m = random_orthogonal_vectors()
        t = random_orthogonal_vectors()

        assert(math.fabs(m[0].dot(m[1])) < 0.001)
        assert(math.fabs(t[0].dot(t[1])) < 0.001)

        R = align_reference_frame(m[0], t[0],
                                  m[1], t[1])

        r = (R * m[0], R * m[1])

        assert(math.fabs(r[0].dot(t[0])) > 0.999)
        assert(math.fabs(r[1].dot(t[1])) > 0.999)

    return

def find_closest_matrix(moving, target):
    '''Work through lattice permutations to try to align moving with target,
    with the metric of trace(inverse(moving) * target).'''

    trace = 0.0
    reindex = matrix.identity(3)

    for op in sgtbx.space_group_info('P422').type().group().all_ops():
        moved = matrix.sqr(op.r().as_double()) * moving
        if (moved.inverse() * target).trace() > trace:
            trace = (moved.inverse() * target).trace()
            reindex = matrix.sqr(op.r().as_double())

    return reindex

def work():
    import sys
    import_xds_integrate_hkl(sys.argv[1])
    print 'OK'

if __name__ == '__main__':
    work()
