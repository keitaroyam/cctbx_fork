// $Id$
/* Copyright (c) 2001 The Regents of the University of California through
   E.O. Lawrence Berkeley National Laboratory, subject to approval by the
   U.S. Department of Energy. See files COPYRIGHT.txt and
   cctbx/LICENSE.txt for further details.

   Revision history:
     Jan 2002: Created (R.W. Grosse-Kunstleve)
 */

#ifndef CCTBX_ARRAY_FAMILY_SMALL_H
#define CCTBX_ARRAY_FAMILY_SMALL_H

#include <cctbx/array_family/small_plain.h>

namespace cctbx { namespace af {

  // Automatic allocation, fixed size, standard operators.
  template <typename ElementType, std::size_t N>
  class small : public small_plain<ElementType, N>
  {
    public:
      CCTBX_ARRAY_FAMILY_TYPEDEFS

      typedef small_plain<ElementType, N> base_class;

      small()
      {}

      explicit
      small(const size_type& sz)
        : base_class(sz)
      {}

      // non-std
      small(const size_type& sz, reserve_flag)
        : base_class(sz, reserve_flag())
      {}

      small(const size_type& sz, const ElementType& x)
        : base_class(sz, x)
      {}

#if !(defined(BOOST_MSVC) && BOOST_MSVC <= 1200) // VC++ 6.0
      // non-std
      template <typename InitFunctorType>
      small(const size_type& sz, InitFunctorType ftor)
        : base_class(sz, ftor)
      {}
#endif

      small(const ElementType* first, const ElementType* last)
        : base_class(first, last)
      {}

#if !(defined(BOOST_MSVC) && BOOST_MSVC <= 1200) // VC++ 6.0
      template <typename OtherElementType>
      small(const OtherElementType* first, const OtherElementType* last)
        : base_class(first, last)
      {}
#endif
  };

}} // namespace cctbx::af

#endif // CCTBX_ARRAY_FAMILY_SMALL_H
