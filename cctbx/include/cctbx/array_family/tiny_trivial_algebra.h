// $Id$
/* Copyright (c) 2001 The Regents of the University of California through
   E.O. Lawrence Berkeley National Laboratory, subject to approval by the
   U.S. Department of Energy. See files COPYRIGHT.txt and
   cctbx/LICENSE.txt for further details.

   Revision history:
     Mar 2002: modified copy of parts of matrixlite.h (rwgk)
     2001 Oct 16: Moved tensor transformations from adptbx (rwgk)
     2001 Jul 02: Merged from CVS branch sgtbx_special_pos (rwgk)
     2001 May 31: merged from CVS branch sgtbx_type (R.W. Grosse-Kunstleve)
     2001 May 07 added: identidy, isDiagonal, transpose
     Apr 2001: SourceForge release (R.W. Grosse-Kunstleve)
 */

#ifndef CCTBX_ARRAY_FAMILAY_TINY_TRIVIAL_ALGEBRA_H
#define CCTBX_ARRAY_FAMILAY_TINY_TRIVIAL_ALGEBRA_H

#include <cctbx/array_family/tiny.h>
#include <cctbx/array_family/misc_functions.h>

namespace cctbx { namespace af {

  template<typename AnyType, std::size_t N>
  inline
  bool
  operator==(tiny<AnyType,N> const& x, tiny<AnyType,N> const& y) {
      for (std::size_t i = 0; i < x.size(); i++)
          if (x[i] != y[i]) return false;
      return true;
  }

  template<typename AnyType, std::size_t N>
  inline
  bool
  operator==(tiny<AnyType,N> const& x, AnyType const& value) {
      for (std::size_t i = 0; i < x.size(); i++)
          if (x[i] != value) return false;
      return true;
  }

  template<typename AnyType, std::size_t N>
  inline
  bool
  operator!=(tiny<AnyType,N> const& x, tiny<AnyType,N> const& y) {
      for (std::size_t i = 0; i < x.size(); i++)
          if (x[i] != y[i]) return true;
      return false;
  }

  template<typename AnyType, std::size_t N>
  inline
  bool
  operator!=(tiny<AnyType,N> const& x, AnyType const& value) {
      for (std::size_t i = 0; i < x.size(); i++)
          if (x[i] != value) return true;
      return false;
  }

  template<typename NumType, std::size_t N>
  inline
  tiny<NumType,N>
  operator+(tiny<NumType,N> const& lhs,
            tiny<NumType,N> const& rhs) {
      tiny<NumType,N> result;
      for (std::size_t i = 0; i < lhs.size(); i++) {
          result[i] = lhs[i] + rhs[i];
      }
      return result;
  }

  template<typename NumType, std::size_t N>
  inline
  tiny<NumType,N>&
  operator+=(tiny<NumType,N>& lhs,
            tiny<NumType,N> const& rhs) {
      for (std::size_t i = 0; i < lhs.size(); i++) {
          lhs[i] += rhs[i];
      }
      return lhs;
  }

  template<typename NumType, std::size_t N>
  inline
  tiny<NumType,N>
  operator-(tiny<NumType,N> const& lhs,
            tiny<NumType,N> const& rhs) {
      tiny<NumType,N> result;
      for (std::size_t i = 0; i < lhs.size(); i++) {
          result[i] = lhs[i] - rhs[i];
      }
      return result;
  }

  template<typename NumType, std::size_t N>
  inline
  tiny<NumType,N>
  operator-(tiny<NumType,N> const& rhs) {
      tiny<NumType,N> result;
      for (std::size_t i = 0; i < rhs.size(); i++) {
          result[i] = -rhs[i];
      }
      return result;
  }

  template<typename NumType, std::size_t N>
  inline
  tiny<NumType,N>
  operator*(tiny<NumType,N> const& lhs,
            tiny<NumType,N> const& rhs) {
      tiny<NumType,N> result;
      for (std::size_t i = 0; i < lhs.size(); i++) {
          result[i] = lhs[i] * rhs[i];
      }
      return result;
  }

  template<typename NumType, std::size_t N>
  inline
  tiny<NumType,N>
  operator*(NumType const& lhs,
            tiny<NumType,N> const& rhs) {
      tiny<NumType,N> result;
      for (std::size_t i = 0; i < rhs.size(); i++) result[i] = lhs * rhs[i];
      return result;
  }

  template<typename NumType, std::size_t N>
  inline
  tiny<NumType,N>
  operator*(tiny<NumType,N> const& lhs,
            NumType const& rhs) {
      tiny<NumType,N> result;
      for (std::size_t i = 0; i < lhs.size(); i++) result[i] = lhs[i] * rhs;
      return result;
  }

  template<typename NumType, std::size_t N>
  inline
  tiny<NumType,N>&
  operator*=(tiny<NumType,N>& lhs,
             NumType const& rhs) {
      for (std::size_t i = 0; i < lhs.size(); i++) lhs[i] *= rhs;
      return lhs;
  }

  template<typename NumType, std::size_t N>
  inline
  tiny<NumType,N>
  operator/(tiny<NumType,N> const& lhs,
            NumType const& rhs) {
      tiny<NumType,N> result;
      for (std::size_t i = 0; i < lhs.size(); i++) result[i] = lhs[i] / rhs;
      return result;
  }

  template<typename NumType, std::size_t N>
  inline
  bool
  operator>=(tiny<NumType,N> const& lhs,
             NumType const& rhs) {
      for (std::size_t i = 0; i < lhs.size(); i++) {
          if (!(lhs[i] >= rhs)) return false;
      }
      return true;
  }

  template <typename NumType, std::size_t N>
  inline
  tiny<NumType, N>
  abs(tiny<NumType, N> const& a)
  {
    tiny<NumType, N> result;
    for (std::size_t i = 0; i < N; i++) {
      if (a[i] < 0) result[i] = -a[i];
      else          result[i] =  a[i];
    }
    return result;
  }

  template<typename ElementType, std::size_t N>
  inline
  tiny<ElementType, N>
  fabs(tiny<ElementType, N> const& a)
  {
    tiny<ElementType, N> result;
    for (std::size_t i = 0; i < N; i++) {
      result[i] = std::fabs(a[i]);
    }
    return result;
  }

  template <typename FloatType, std::size_t N>
  inline
  tiny<bool, N>
  approx_equal_scaled(tiny<FloatType, N> const& a,
                      tiny<FloatType, N> const& b,
                      FloatType scaled_tolerance) {
    tiny<bool, N> result;
    for (std::size_t i = 0; i < N; i++) {
      result[i] = approx_equal_scaled(a[i], b[i], scaled_tolerance);
    }
    return result;
  }

}} // namespace cctbx::af

#endif // CCTBX_ARRAY_FAMILAY_TINY_TRIVIAL_ALGEBRA_H
