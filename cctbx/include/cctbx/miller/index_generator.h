/* Copyright (c) 2001-2002 The Regents of the University of California
   through E.O. Lawrence Berkeley National Laboratory, subject to
   approval by the U.S. Department of Energy.
   See files COPYRIGHT.txt and LICENSE.txt for further details.

   Revision history:
     2002 Jul: Created from fragments of cctbx/sgtbx/miller_asu.h (rwgk)
 */

#ifndef CCTBX_MILLER_INDEX_GENERATOR_H
#define CCTBX_MILLER_INDEX_GENERATOR_H

#include <cctbx/sgtbx/reciprocal_space_asu.h>
#include <scitbx/array_family/loops.h>

namespace cctbx { namespace miller {

  /*! \brief Efficient, easy-to-use algorithm for building
      an asymmetric unit of Miller indices up to a given
      high-resolution limit or up to a given maximum Miller
      index.
   */
  /*! Example (Python syntax):<pre>
        # Given a resolution limit.
        unit_cell = uctbx.unit_cell((10, 10, 10, 90, 90, 90))
        sg_type = sgtbx.space_group_type("P 41")
        mig = sgtbx.miller_index_generator(unit_cell, sg_type, 1, 3.0)
        for h in mig: print h
        #
        # Given a maximum Miller index.
        sg_type = sgtbx.space_group_type("P 31")
        mig = sgtbx.miller_index_generator(sg_type, 1, (3,4,5))
        for h in mig: print h
      </pre>
      This class is implemented as an iterator. Therefore
      the generation of Miller indices does not consume any
      significant amounts of memory. The key to efficiency
      is cctbx::sgtbx::reciprocal_space::reference_asu .
   */
  class index_generator
  {
    public:
      //! Default constructor.
      /*! Default-constructed instances will throw exceptions if
          some of the member functions are used.
       */
      index_generator() {}

      //! Initialization with resolution limit.
      /*! Miller indices up to and including resolution_d_min will
          be generated.
       */
      index_generator(uctbx::unit_cell const& unit_cell,
                      sgtbx::space_group_type const& sg_type,
                      bool anomalous_flag,
                      double resolution_d_min);

      //! Initialization with maximum Miller index.
      /*! Miller indices in the range from -max_index to +max_index
          will be generated.
       */
      index_generator(sgtbx::space_group_type const& sg_type,
                      bool anomalous_flag,
                      index<> const& max_index);

      //! Unit cell in use.
      uctbx::unit_cell const&
      unit_cell() const { return unit_cell_; }

      //! Space group in use.
      sgtbx::space_group_type const&
      space_group_type() const { return sg_type_; }

      //! Anomalous flag in use.
      bool
      anomalous_flag() const { return anomalous_flag_; }

      //! Access to the reciprocal space asymmetric unit.
      /*! The Miller indices that are generated by this class (member
          function next()) are inside this asymmetric unit.
       */
      sgtbx::reciprocal_space::asu const&
      asu() const { return asu_; }

      //! Iterator over Miller indices.
      /*! Each call to this member function will return the next
          Miller index in the sequence. The indices are inside
          sgtbx::reciprocal_space::asu(). Systematically absent
          reflections are automatically filtered out.
          <p>
          The Miller index (0,0,0) indicates the end of the iteration.
       */
      index<>
      next();

      //! Returns all Miller indices in an array.
      /*! The next() method is called in a loop until the list
          of Miller indices is exhausted.
       */
      af::shared<index<> >
      to_array();

    private:
      uctbx::unit_cell unit_cell_;
      sgtbx::space_group_type sg_type_;
      bool anomalous_flag_;

      sgtbx::reciprocal_space::asu asu_;
      double d_star_sq_max_;
      af::nested_loop<index<> > loop_;
      bool next_is_minus_previous_;
      sgtbx::phase_info phase_info_;
      index<> previous_;

      void
      initialize_loop(index<> const& reference_h_max);

      bool
      set_phase_info(index<> const& h);

      index<>
      next_under_friedel_symmetry();
  };

}} // namespace cctbx::miller

#endif // CCTBX_MILLER_INDEX_GENERATOR_H
