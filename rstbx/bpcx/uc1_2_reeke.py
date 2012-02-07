#!/usr/bin/env cctbx.python
#
# Biostruct-X Data Reduction Use Case 1.2:
#
# Given UB matrix, centring operation, generate a list of predictions as
# H K L x y phi. Also requires (clearly) a model for the detector positions
# and the crystal lattice type. This is aimed to help with identifying
# locations on the images.
#
# Requires:
#
# Determine maximum resolution limit.
# Generate full list of reflections to given resolution limit.
# Compute intersection angles for all reflections given UB matrix etc.
# Determine which of those will be recorded on the detector.

import sys
import math

from rstbx.cftbx.coordinate_frame_converter import coordinate_frame_converter
from rstbx.diffraction import rotation_angles, reflection_prediction
from cctbx.sgtbx import space_group, space_group_symbols
from cctbx.uctbx import unit_cell
from rstbx.bpcx import reeke

def generate_indices(unit_cell_constants, resolution_limit):
    '''Generate all possible reflection indices out to a given resolution
    limit, ignoring symmetry and centring.'''

    uc = unit_cell(unit_cell_constants)

    maxh, maxk, maxl = uc.max_miller_indices(resolution_limit)

    indices = []

    for h in range(-maxh, maxh + 1):
        for k in range(-maxk, maxk + 1):
            for l in range(-maxl, maxl + 1):

                if h == 0 and k == 0 and l == 0:
                    continue

                if uc.d((h, k, l)) < resolution_limit:
                    continue

                indices.append((h, k, l))

    return indices

def remove_absent_indices(indices, space_group_number):
    '''From the given list of indices, remove those reflections which should
    be systematic absences according to the given space group.'''

    sg = space_group(space_group_symbols(space_group_number).hall())

    present = []

    for hkl in indices:
        if not sg.is_sys_absent(hkl):
            present.append(hkl)

    return present

def parse_xds_xparm_scan_info(xparm_file):
    '''Read an XDS XPARM file, get the scan information.'''

    values = map(float, open(xparm_file).read().split())

    assert(len(values) == 42)

    img_start = values[0]
    osc_start = values[1]
    osc_range = values[2]

    return img_start, osc_start, osc_range

class python_reflection_prediction:
    def __init__(self, axis, s0, ub, detector_origin,
                 detector_fast, detector_slow,
                 f_min, f_max, s_min, s_max):
        self._axis = axis
        self._s0 = s0
        self._ub = ub
        self._detector_origin = detector_origin
        self._detector_fast = detector_fast
        self._detector_slow = detector_slow
        self._limits = f_min, f_max, s_min, s_max

        return

    def predict(self, indices, angles):

        detector_normal = self._detector_fast.cross(self._detector_slow)
        distance = self._detector_origin.dot(detector_normal)

        observed_reflection_positions = []

        for hkl, angle in zip(indices, angles):
            s = (self._ub * hkl).rotate(self._axis, angle)
            q = (s + self._s0).normalize()

            # check if diffracted ray parallel to detector face

            q_dot_n = q.dot(detector_normal)

            if q_dot_n == 0:
                continue

            r = (q * distance / q_dot_n) - self._detector_origin

            x = r.dot(self._detector_fast)
            y = r.dot(self._detector_slow)

            if x < self._limits[0] or y < self._limits[2]:
                continue
            if x > self._limits[1] or y > self._limits[3]:
                continue

            observed_reflection_positions.append((hkl, x, y, angle))

        return observed_reflection_positions

class cpp_reflection_prediction:
    def __init__(self, axis, s0, ub, detector_origin,
                 detector_fast, detector_slow,
                 f_min, f_max, s_min, s_max):
        self._rp = reflection_prediction(axis, s0, ub, detector_origin,
                                         detector_fast, detector_slow,
                                         f_min, f_max, s_min, s_max)

        return

    def predict(self, indices, angles):

        observed_reflection_positions = []

        for hkl, angle in zip(indices, angles):
            if self._rp(hkl, angle):
                x, y = self._rp.get_prediction()
                observed_reflection_positions.append((hkl, x, y, angle))

        return observed_reflection_positions

def main(configuration_file, img_range, dmin = None):
    '''Perform the calculations needed for use case 1.1.'''

    d2r = math.pi / 180.0

    cfc = coordinate_frame_converter(configuration_file)

    img_start, osc_start, osc_range = parse_xds_xparm_scan_info(
        configuration_file)

    if dmin is None:
        dmin = cfc.derive_detector_highest_resolution()

    phi_start = ((img_range[0] - img_start) * osc_range + osc_start) * d2r
    phi_end = ((img_range[1] - img_start + 1) * osc_range + osc_start) * d2r

    # in principle this should come from the crystal model - should that
    # crystal model record the cell parameters or derive them from the
    # axis directions?

    A = cfc.get_c('real_space_a')
    B = cfc.get_c('real_space_b')
    C = cfc.get_c('real_space_c')

    cell = (A.length(), B.length(), C.length(), B.angle(C, deg = True),
            C.angle(A, deg = True), A.angle(B, deg = True))

    sg = cfc.get('space_group_number')

    # get the UB matrix and rotation axis according to the Rossmann
    # convention, which is used within the Labelit code. Also get the
    # source vector and wavelength

    u, b = cfc.get_u_b(convention = cfc.ROSSMANN)
    axis = cfc.get('rotation_axis', convention = cfc.ROSSMANN)
    ub = u * b
    wavelength = cfc.get('wavelength')
    s0 = (- 1.0 / wavelength) * cfc.get_c('sample_to_source')

    # generate indices per image based on the Reeke algorithm (see Mosflm)
    reeke_model = reeke.reeke_model(ub, axis, s0)
    sys.exit("The Reeke algorithm is not yet implemented")
    indices = []
    for img in range(img_range[0], img_range[1] + 1):
        img_phi_start = ((img - img_start) * osc_range + osc_start) * d2r
        img_phi_end = img_phi_start + osc_range * d2r
        indices.extend(reeke_model.loop_limits(img_phi_start, img_phi_end))

    indices = remove_absent_indices(indices, sg)

    # There may be some duplication in the list due to inclusive choice
    # of limits for each image. This needs to be checked.

    # work out which reflections should be observed (i.e. pass through the
    # Ewald sphere)

    ra = rotation_angles(dmin, ub, wavelength, axis)

    observed_indices = []
    observed_angles = []

    for hkl in indices:
        if ra(hkl):
            for angle in ra.get_intersection_angles():
                if angle >= phi_start and angle <= phi_end:
                    observed_indices.append(hkl)
                    observed_angles.append(angle)

    # convert all of these to full scattering vectors in a laboratory frame
    # (for which I will use the CBF coordinate frame) and calculate which
    # will intersect with the detector

    #u, b = cfc.get_u_b()
    #axis = cfc.get_c('rotation_axis')
    s0 = (- 1.0 / wavelength) * cfc.get_c('sample_to_source')
    ub = u * b

    # need some detector properties for this as well... this should be
    # abstracted to a detector model.

    detector_origin = cfc.get_c('detector_origin')
    detector_fast = cfc.get_c('detector_fast')
    detector_slow = cfc.get_c('detector_slow')
    sample_to_source = cfc.get_c('sample_to_source')
    pixel_size_fast, pixel_size_slow = cfc.get('detector_pixel_size_fast_slow')
    size_fast, size_slow = cfc.get('detector_size_fast_slow')

    dimension_fast = size_fast * pixel_size_fast
    dimension_slow = size_slow * pixel_size_slow

    detector_normal = detector_fast.cross(detector_slow)
    distance = detector_origin.dot(detector_normal)

    rp = cpp_reflection_prediction(axis, s0, ub, detector_origin,
                                   detector_fast, detector_slow,
                                   0, dimension_fast,
                                   0, dimension_slow)

    cpp_observed_reflection_positions = rp.predict(observed_indices,
                                                   observed_angles)

    r2d = 180.0 / math.pi

    for hkl, f, s, angle in cpp_observed_reflection_positions:
        print '%d %d %d' % hkl, '%.4f %4f %2f' % (
            f / pixel_size_fast, s / pixel_size_slow,
            (img_start - 1) + ((angle * r2d) - osc_start) / osc_range)

if __name__ == '__main__':

    # FIXME we should perhaps use Phil here to learn how to do this?!

    if len(sys.argv) < 4:
        msg = "Requires 3 arguments: path/to/xparm.xds start_image_no end_image_no"
        sys.exit(msg)
    else:
        if len(sys.argv) == 4:
            main(sys.argv[1], (int(sys.argv[2]), int(sys.argv[3])))
        else:
            main(sys.argv[1], (int(sys.argv[2]), int(sys.argv[3])),
                 float(sys.argv[4]))
