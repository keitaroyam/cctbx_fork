/* Copyright (c) 2001-2002 The Regents of the University of California
   through E.O. Lawrence Berkeley National Laboratory, subject to
   approval by the U.S. Department of Energy.
   See files COPYRIGHT.txt and LICENSE.txt for further details.

   Revision history:
     2002 Jul: Created from fragments of cctbx/miller.h (R.W. Grosse-Kunstleve)
 */

#ifndef CCTBX_MILLER_INDEX_SPAN_H
#define CCTBX_MILLER_INDEX_SPAN_H

#include <cctbx/miller.h>
#include <scitbx/array_family/ref.h>
#include <scitbx/array_family/tiny_types.h>

namespace cctbx { namespace miller {

  /*! \brief Determines min(indices[i]) and max(indices[i])+1, i=1..3,
       for an array of Miller indices.
   */
  class index_span : af::tiny<af::tiny<int, 2>, 3>
  {
    public:
      typedef af::tiny<int, 2> min_end;
      typedef af::tiny<min_end, 3> base_class;

      //! Default constructor. Some data members are not initialized!
      index_span() {}

      //! Determines the min and max elements in the array of indices.
      index_span(af::const_ref<index<> > const& indices);

      //! The min elements found in the array passed to the constructor.
      af::int3
      min() const;

      //! The max elements found in the array passed to the constructor.
      af::int3
      max() const;

      //! Maximum of abs(min()) and abs(max()) + 1.
      af::int3
      abs_range() const;

      /*! \brief Dimensions of 3-dimensional array for storing the indices
          found in the 1-dimensional array passed to the constructor.
       */
      /*! Formula used: (abs_range()-1) * 2 + 1
       */
      af::int3
      map_grid() const;

      //! Tests if min() <= h <= max().
      bool
      is_in_domain(index<> const& h) const;

      //! Computes a 1-dimensional index for h.
      /*! Useful for generating fast lookup maps.
          <p>
          Not available in Python.
       */
      std::size_t
      pack(index<> const& h) const
      {
        return ((h[0] - (*this)[0][0]) * range_((*this)[1])
              + (h[1] - (*this)[1][0])) * range_((*this)[2])
              + (h[2] - (*this)[2][0]);
      }

    private:
      static int
      range_(min_end const& span) { return span[1] - span[0]; }
  };

}} // namespace cctbx::miller

#endif // CCTBX_MILLER_INDEX_SPAN_H
