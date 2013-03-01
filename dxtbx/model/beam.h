/*
 * beam.h
 *
 *  Copyright (C) 2013 Diamond Light Source
 *
 *  Author: James Parkhurst
 *
 *  This code is distributed under the BSD license, a copy of which is
 *  included in the root directory of this package.
 */
#ifndef DXTBX_MODEL_BEAM_H
#define DXTBX_MODEL_BEAM_H

#include <cmath>
#include <scitbx/vec3.h>

namespace dxtbx { namespace model {

  using scitbx::vec3;

  /** Base class for beam objects */
  class BeamBase {};

  /** A class to represent a simple beam. */
  class Beam : public BeamBase {
  public:
    /** Default constructor: initialise all to zero */
    Beam()
      : wavelength_(0.0),
        direction_(0.0, 0.0, 0.0) {}

    /**
     * Initialise all the beam parameters.
     * @param direction The beam direction vector.
     */
    Beam(vec3 <double> s0)
      : wavelength_(1.0 / s0.length()),
        direction_(s0.normalize()) {}

    /**
     * Initialise all the beam parameters. Normalize the direction vector
     * and give it the length of 1.0 / wavelength
     * @param wavelength The wavelength of the beam
     * @param direction The beam direction vector.
     */
    Beam(vec3 <double> direction, double wavelength)
      : wavelength_(wavelength),
        direction_(direction.normalize()) {}

    /** Virtual destructor */
    virtual ~Beam() {}

    /** Get the direction */
    vec3 <double> get_direction() const {
      return direction_;
    }

    /** Get the wavelength */
    double get_wavelength() const {
      return wavelength_;
    }

    /** Set the direction. */
    void set_direction(vec3 <double> direction) {
      direction_ = direction.normalize();
    }

    /** Set the wavelength */
    void set_wavelength(double wavelength) {
      wavelength_ = wavelength;
    }

    /** Get the wave vector in units of inverse angstroms */
    vec3 <double> get_s0() const {
      return direction_ * 1.0 / wavelength_;
    }

    /** Check wavlength and direction are (almost) same */
    bool operator==(const Beam &beam) {
      double eps = 1.0e-6;
      double d_direction =  std::abs(direction_.angle(beam.direction_));
      double d_wavelength = std::abs(wavelength_ - beam.wavelength_);
      return (d_direction <= eps && d_wavelength <= eps);
    }

    /** Check wavelength and direction are not (almost) equal. */
    bool operator!=(const Beam &beam) {
      return !(*this == beam);
    }

  private:
    double wavelength_;
    vec3 <double> direction_;
  };

}} // namespace dxtbx::model

#endif // DXTBX_MODEL_BEAM_H
