// $Id$
/* Copyright (c) 2001 The Regents of the University of California through
   E.O. Lawrence Berkeley National Laboratory, subject to approval by the
   U.S. Department of Energy. See files COPYRIGHT.txt and
   cctbx/LICENSE.txt for further details.

   Revision history:
     Feb 2002: Created (R.W. Grosse-Kunstleve)
 */

#ifndef CCTBX_ARRAY_FAMILY_GRID_ACCESSOR_H
#define CCTBX_ARRAY_FAMILY_GRID_ACCESSOR_H

#include <cstddef>
#include <cctbx/array_family/tiny_helpers.h>

// forward declaration
namespace cctbx { namespace af {
  template <typename ElementType, std::size_t N>
  class tiny;
}}

namespace cctbx { namespace af {

  template <std::size_t N>
  struct c_index_1d {
    template <typename ExtendArrayType, typename IndexArrayType>
    std::size_t operator()(const ExtendArrayType& e, const IndexArrayType& i) {
      return c_index_1d<N-1>()(e, i) * e[N-1] + i[N-1];
    }
  };

  template<>
  struct c_index_1d<1> {
    template <typename ExtendArrayType, typename IndexArrayType>
    std::size_t operator()(const ExtendArrayType& e, const IndexArrayType& i) {
      return i[0];
    }
  };

  template <std::size_t N>
  struct fortran_index_1d {
    template <typename ExtendArrayType, typename IndexArrayType>
    std::size_t operator()(const ExtendArrayType& e, const IndexArrayType& i) {
      return fortran_index_1d<N-1>()(e, i) * e[e.size()-N] + i[e.size()-N];
    }
  };

  template<>
  struct fortran_index_1d<1> {
    template <typename ExtendArrayType, typename IndexArrayType>
    std::size_t operator()(const ExtendArrayType& e, const IndexArrayType& i) {
      return i[e.size()-1];
    }
  };

  template <std::size_t Nd,
            typename Index1dType = c_index_1d<Nd>,
            typename IndexType = tiny<int, Nd> >
  class grid_accessor : public IndexType
  {
    public:
      typedef IndexType index_type;
      typedef typename IndexType::value_type value_type;

      grid_accessor() {};
      grid_accessor(const IndexType& n) : IndexType(n) {}

      CCTBX_ARRAY_FAMILY_TINY_CONVENIENCE_CONSTRUCTORS(grid_accessor)

      static std::size_t nd() { return Nd; }

      void init_default() {
        for(std::size_t i=0;i<nd();i++) this->elems[i] = 0;
      }

      std::size_t size1d() const {
        // XXX return product(IndexType(*this));
        std::size_t result = 1;
        for(std::size_t i=0;i<nd();i++) result *= this->elems[i];
        return result;
      }

      std::size_t operator()(const IndexType& i) const {
        return Index1dType()(*this, i);
      }

      bool is_valid_index(const IndexType& i) const {
        for(std::size_t j=0;j<nd();j++) {
          if (i[j] < 0 || i[j] >= this->elems[j]) return false;
        }
        return true;
      }
  };

}} // namespace cctbx::af

#endif // CCTBX_ARRAY_FAMILY_GRID_ACCESSOR_H
