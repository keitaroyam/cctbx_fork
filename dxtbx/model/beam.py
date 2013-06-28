from __future__ import division
#!/usr/bin/env python
# beam.py
#   Copyright (C) 2011 Diamond Light Source, Graeme Winter
#
#   This code is distributed under the BSD license, a copy of which is
#   included in the root directory of this package.
#
# A model for the beam for the "updated experimental model" project documented
# in internal ticket #1555. This is not designed to be used outside of the
# XSweep classes.

import math
import pycbf
from dxtbx_model_ext import Beam

class beam_factory:
    '''A factory class for beam objects, which encapsulate standard beam
    models. In cases where a full cbf desctiption is available this
    will be used, otherwise simplified descriptions can be applied.'''

    def __init__(self):
        pass

    @staticmethod
    def make_beam(sample_to_source=None, wavelength=None,
                  s0=None, unit_s0=None,
                  divergence=None, sigma_divergence=None):

        if divergence == None or sigma_divergence == None:
            divergence = 0.0
            sigma_divergence = 0.0

        if sample_to_source:
            assert(wavelength)
            return Beam(
                tuple(map(float, sample_to_source)),
                float(wavelength),
                float(divergence),
                float(sigma_divergence))
        elif unit_s0:
            assert(wavelength)
            return Beam(
                tuple(map(lambda x: - x, map(float, unit_s0))),
                float(wavelength),
                float(divergence),
                float(sigma_divergence))
        else:
            assert(s0)
            return Beam(tuple(map(float, s0)))

    @staticmethod
    def make_polarized_beam(sample_to_source=None, wavelength=None,
                            s0=None, unit_s0=None,
                            polarization=None, polarization_fraction=None,
                            divergence=None, sigma_divergence=None):
        assert(polarization)
        assert(polarization_fraction)

        if divergence == None or sigma_divergence == None:
            divergence = 0.0
            sigma_divergence = 0.0

        if sample_to_source:
            assert(wavelength)
            return Beam(
                tuple(map(float, sample_to_source)),
                float(wavelength),
                float(divergence),
                float(sigma_divergence),
                tuple(map(float, polarization)),
                float(polarization_fraction))
        elif unit_s0:
            assert(wavelength)
            return Beam(
                tuple(map(lambda x: - x, map(float, unit_s0))),
                float(wavelength),
                float(divergence),
                float(sigma_divergence),
                tuple(map(float, polarization)),
                float(polarization_fraction))
        else:
            assert(s0)
            return Beam(
                tuple(map(float, s0)),
                float(divergence),
                float(sigma_divergence),
                tuple(map(float, polarization)),
                float(polarization_fraction))

    @staticmethod
    def simple(wavelength):
        '''Construct a beam object on the principle that the beam is aligned
        with the +z axis, as is quite normal. Also assume the beam has
        polarization fraction 0.999 and is polarized in the x-z plane.'''

        return beam_factory.make_beam(
            sample_to_source=(0.0, 0.0, 1.0),
            wavelength=wavelength)

    @staticmethod
    def simple_directional(direction, wavelength):
        '''Construct a beam with direction and wavelength.'''

        return beam_factory.make_beam(
            sample_to_source=direction,
            wavelength=wavelength)

    @staticmethod
    def complex(beam_direction, polarization_fraction,
                polarization_plane_normal, wavelength):
        '''Full access to the constructor for cases where we do know everything
        that we need...'''

        return beam_factory.make_polarized_beam(
            sample_to_source=beam_direction,
            wavelength=wavelength,
            polarization=polarization_plane_normal,
            polarization_fraction=polarization_fraction)

    @staticmethod
    def imgCIF(cif_file):
        '''Initialize a detector model from an imgCIF file. N.B. the
        definition of the polarization plane is not completely helpful
        in this - it is the angle between the polarization plane and the
        +Y laboratory frame vector.'''

        d2r = math.pi / 180.0

        cbf_handle = pycbf.cbf_handle_struct()
        cbf_handle.read_file(cif_file, pycbf.MSG_DIGEST)

        cbf_handle.find_category('axis')

        # find record with equipment = source
        cbf_handle.find_column('equipment')
        cbf_handle.find_row('source')

        # then get the vector and offset from this
        direction = []

        for j in range(3):
            cbf_handle.find_column('vector[%d]' % (j + 1))
            direction.append(cbf_handle.get_doublevalue())

        # and the wavelength
        wavelength = cbf_handle.get_wavelength()

        # and information about the polarization - FIXME this should probably
        # be a rotation about the beam not about the Z axis.

        try:
            polar_fraction, polar_angle = cbf_handle.get_polarization()
        except: # intentional
            polar_fraction = 0.999
            polar_angle = 0.0

        polar_plane_normal = (
            math.sin(polar_angle * d2r), math.cos(polar_angle * d2r), 0.0)

        return beam_factory.make_polarized_beam(
                sample_to_source=direction,
                wavelength=wavelength,
                polarization=polar_plane_normal,
                polarization_fraction=polar_fraction)

    @staticmethod
    def imgCIF_H(cbf_handle):
        '''Initialize a detector model from an imgCIF file. N.B. the
        definition of the polarization plane is not completely helpful
        in this - it is the angle between the polarization plane and the
        +Y laboratory frame vector. This example works from a cbf_handle,
        which is already configured.'''

        d2r = math.pi / 180.0

        cbf_handle.find_category('axis')

        # find record with equipment = source
        cbf_handle.find_column('equipment')
        cbf_handle.find_row('source')

        # then get the vector and offset from this
        direction = []

        for j in range(3):
            cbf_handle.find_column('vector[%d]' % (j + 1))
            direction.append(cbf_handle.get_doublevalue())

        # and the wavelength
        wavelength = cbf_handle.get_wavelength()

        # and information about the polarization - FIXME this should probably
        # be a rotation about the beam not about the Z axis.

        try:
            polar_fraction, polar_angle = cbf_handle.get_polarization()
        except: # intentional
            polar_fraction = 0.999
            polar_angle = 0.0

        polar_plane_normal = (
            math.sin(polar_angle * d2r), math.cos(polar_angle * d2r), 0.0)

        return beam_factory.make_polarized_beam(
            sample_to_source=direction,
            wavelength=wavelength,
            polarization=polar_plane_normal,
            polarization_fraction=polar_fraction)
