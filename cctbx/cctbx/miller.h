// $Id$
/* Copyright (c) 2001 The Regents of the University of California through
   E.O. Lawrence Berkeley National Laboratory, subject to approval by the
   U.S. Department of Energy. See files COPYRIGHT.txt and
   cctbx/LICENSE.txt for further details.

   Revision history:
     2001 Jul 02: Merged from CVS branch sgtbx_special_pos (rwgk)
     Apr 2001: SourceForge release (R.W. Grosse-Kunstleve)
 */

/*! \file
    Toolbox for Miller indices.
 */

#ifndef CCTBX_MILLER_H
#define CCTBX_MILLER_H

#include <iostream>
#include <cctbx/fixes/cmath>
#include <cctbx/fixes/cstdlib>
#include <boost/array.hpp>
#include <cctbx/basic/matrixlite.h>
#include <cctbx/coordinates.h>
#include <cctbx/constants.h>

namespace cctbx {
  //! %Miller index namespace.
  namespace Miller {

    //! Triple of 3 integers.
    typedef MatrixLite::itype::Vec3 Vec3;

    //! Enumeration for symbolic subscripting (e.g. MillerIndex[H]).
    enum {H, K, L};

    //! Miller index class.
    class Index : public Vec3 {
      public:
        //! @name Constructors.
        //@{
        Index() {
          for(std::size_t i=0;i<3;i++) elems[i] = 0;
        }
        explicit Index(const Vec3& v) {
          for(std::size_t i=0;i<3;i++) elems[i] = v[i];
        }
        explicit Index(const int* hkl) {
          for(std::size_t i=0;i<3;i++) elems[i] = hkl[i];
        }
        Index(const int h, const int k, const int l) {
          elems[0] = h; elems[1] = k; elems[2] = l;
        }
        //@}

        //! @name Convenience methods.
        //@{
        bool is000() const {
          return !(elems[0] || elems[1] || elems[2]);
        }
        Index operator-() const {
          return Index(-elems[0], -elems[1], -elems[2]);
        }
        Index FriedelMate() const {
          return operator-();
        }
        //@}

        //! @name Test for equality and inequality.
        //@{
        friend bool operator==(const Index& lhs, const Index& rhs) {
          for(std::size_t i=0;i<3;i++) if (lhs[i] != rhs[i]) return false;
          return true;
        }
        friend bool operator!=(const Index& lhs, const Index& rhs) {
          return !(lhs == rhs);
        }
        //@}

        //! @name Definition of sort order for human-readable listings.
        //@{
        /*! This comparison is computationally more expensive than
            the Miller::hashCompare below.
         */
        bool operator<(const Index& m2) const
        {
          const int P[3] = {2, 0, 1};
          std::size_t i;
          for(i=0;i<3;i++) {
            if (elems[P[i]] >= 0 && m2[P[i]] <  0) return true;
            if (elems[P[i]] <  0 && m2[P[i]] >= 0) return false;
          }
          for(i=0;i<3;i++) {
            if (std::abs(elems[P[i]]) < std::abs(m2[P[i]])) return true;
            if (std::abs(elems[P[i]]) > std::abs(m2[P[i]])) return false;
          }
          return false;
        }
        bool operator>(const Index& m2) const {
          return !(*this < m2);
        }
        //@}
    };

    //! Multiplication of Miller indices and fractional coordiantes.
    template <class FloatType>
    inline FloatType
    operator*(const Index& lhs, const fractional<FloatType>& rhs) {
      FloatType result = 0.;
      for(std::size_t i=0;i<3;i++) result += lhs[i] * rhs[i];
      return result;
    }

    /*! \brief Definition of fast comparison for use in,
        e.g., std::map<Miller::Index>.
     */
    class hashCompare {
      public:
        //! This fast comparison function is implemented as operator().
        bool operator()(const Index& m1,const Index& m2) const {
          for(std::size_t i=0;i<3;i++) {
            if (m1[i] < m2[i]) return true;
            if (m1[i] > m2[i]) return false;
          }
          return false;
        }
    };

    //! iostream output operator for class Miller::Index.
    inline std::ostream& operator<<(std::ostream& os, const Miller::Index& MIx)
    {
      os << "H=" << MIx[0] << " K=" << MIx[1] << " L=" << MIx[2];
      return os;
    }

    //! Determine max(abs(H[i])), i=1..3, for a vector of Miller indices.
    template <class MillerIndexVectorType>
    boost::array<int, 3>
    IndexRange(const MillerIndexVectorType& Indices)
    {
      boost::array<int, 3> result;
      result.assign(0);
      for(std::size_t i=0;i<Indices.size();i++) {
        for(std::size_t j=0;j<3;j++) {
          int m = Indices[i][j];
          if (m < 0) m *= -1;
          if (result[j] < m) result[j] = m;
        }
      }
      for(std::size_t j=0;j<3;j++) result[j]++;
      return result;
    }

    //! Type for vector of multiplicities for given Miller indices.
    template <class MultiplicityVectorType>
    struct multiplicity_vector
    {
      //! Compute the vector of multiplicites.
      /*! See also: cctbx::sgtbx::SpaceGroup::multiplicity()
       */
      template <class SpaceGroupType, class MillerIndexVectorType>
      static MultiplicityVectorType
      get(const SpaceGroupType& SgOps,
          bool FriedelFlag,
          const MillerIndexVectorType& MillerIndices)
      {
        MultiplicityVectorType result(MillerIndices.size());
        for(std::size_t i=0;i<MillerIndices.size();i++) {
          result[i] = SgOps.multiplicity(MillerIndices[i], FriedelFlag);
        }
        return result;
      }
    };

  } // namespace Miller
} // namespace cctbx

#endif // CCTBX_MILLER_H
