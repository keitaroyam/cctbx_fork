// $Id$
/* Copyright (c) 2001 The Regents of the University of California through
   E.O. Lawrence Berkeley National Laboratory, subject to approval by the
   U.S. Department of Energy. See files COPYRIGHT.txt and
   cctbx/LICENSE.txt for further details.

   Revision history:
     Created 2001 Jul 03 (R.W. Grosse-Kunstleve)
 */

#ifndef CCTBX_COORDINATES_H
#define CCTBX_COORDINATES_H

#include <boost/array.hpp>
#include <cctbx/basic/matrixlite.h>

namespace cctbx {

  //! Class for cartesian (orthogonal, real) coordinates.
  /*! The template parameter T should be a floating point type
      (e.g. float or double).
      <p>
      See also: class fractional
   */
  template <class T>
  class cartesian : public boost::array<T, 3> {
    public:
      //! The elements of the coordinate vector are initialized with 0.
      cartesian() {
        for(std::size_t i=0;i<3;i++) elems[i] = 0;
      }
      //! The elements of the coordinate vector are copied from v.
      template <class U>
      cartesian(const boost::array<U, 3> v) {
        for(std::size_t i=0;i<3;i++) elems[i] = v[i];
      }
      //! The elements of the coordinate vector are copied from xyz.
      template <class U>
      cartesian(const U* xyz) {
        for(std::size_t i=0;i<3;i++) elems[i] = xyz[i];
      }
      //! The elements of the coordinate vector are initialized with x,y,z.
      cartesian(const T& x, const T& y, const T& z) {
        elems[0] = x; elems[1] = y; elems[2] = z;
      }
      //! Length squared (scalar product) of the coordinate vector.
      inline T Length2() const {
        return (*this) * (*this);
      }
  };

  //! Class for fractional coordinates.
  /*! The template parameter T should be a floating point type
      (e.g. float or double).
      <p>
      See also: class cartesian
   */
  template <class T>
  class fractional : public boost::array<T, 3> {
    public:
      //! The elements of the coordinate vector are initialized with 0.
      fractional() {
        for(std::size_t i=0;i<3;i++) elems[i] = 0;
      }
      //! The elements of the coordinate vector are copied from v.
      template <class U>
      fractional(const boost::array<U, 3> v) {
        for(std::size_t i=0;i<3;i++) elems[i] = v[i];
      }
      //! The elements of the coordinate vector are copied from xyz.
      template <class U>
      fractional(const U* xyz) {
        for(std::size_t i=0;i<3;i++) elems[i] = xyz[i];
      }
      //! The elements of the coordinate vector are initialized with x,y,z.
      fractional(const T& x, const T& y, const T& z) {
        elems[0] = x; elems[1] = y; elems[2] = z;
      }
      /*! \brief Apply modulus operation such that 0.0 <= x < 1.0
          for all elements of the coordinate vector.
       */
      fractional modPositive() const {
        fractional result;
        for(std::size_t i=0;i<3;i++) {
          result[i] = std::fmod(elems[i], 1.);
          while (result[i] <  0.) result[i] += 1.;
          while (result[i] >= 1.) result[i] -= 1.;
        }
        return result;
      }
      /*! \brief Apply modulus operation such that -0.5 < x <= 0.5
          for all elements of the coordinate vector.
       */
      fractional modShort() const {
        fractional result;
        for(std::size_t i=0;i<3;i++) {
          result[i] = std::fmod(elems[i], 1.);
          if      (result[i] <= -.5) result[i] += 1.;
          else if (result[i] >   .5) result[i] -= 1.;
        }
        return result;
      }
  };

} // namespace cctbx

#endif // CCTBX_COORDINATES_H
