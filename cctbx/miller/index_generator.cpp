/* Copyright (c) 2001-2002 The Regents of the University of California
   through E.O. Lawrence Berkeley National Laboratory, subject to
   approval by the U.S. Department of Energy.
   See files COPYRIGHT.txt and LICENSE.txt for further details.

   Revision history:
     2002 Oct: Refactored parts of miller/miller_lib.cpp (rwgk)
 */

#include <cctbx/miller/index_generator.h>
#include <scitbx/array_family/tiny_algebra.h>

namespace cctbx { namespace miller {

  void
  index_generator::initialize_loop(index<> const& reference_h_max)
  {
    af::int3 cut = asu_.reference()->cut_parameters();
    index<> reference_h_begin;
    index<> reference_h_end;
    for(std::size_t i=0;i<3;i++) {
      reference_h_begin[i] = reference_h_max[i] * cut[i];
      reference_h_end[i] = reference_h_max[i] + 1;
    }
    loop_ = af::nested_loop<index<> >(reference_h_begin, reference_h_end);
    next_is_minus_previous_ = false;
  }

  index_generator::index_generator(uctbx::unit_cell const& unit_cell,
                                   sgtbx::space_group_type const& sg_type,
                                   bool anomalous_flag,
                                   double resolution_d_min)
    : unit_cell_(unit_cell),
      sg_type_(sg_type),
      anomalous_flag_(anomalous_flag),
      asu_(sg_type)
  {
    if (resolution_d_min <= 0.) {
      throw error("Resolution limit must be greater than zero.");
    }
    d_star_sq_max_ = 1. / (resolution_d_min * resolution_d_min);
    uctbx::unit_cell
      reference_unit_cell = sg_type_.cb_op().apply(unit_cell_);
    initialize_loop(reference_unit_cell.max_miller_indices(resolution_d_min));
  }

  index_generator::index_generator(sgtbx::space_group_type const& sg_type,
                                   bool anomalous_flag,
                                   index<> const& max_index)
    : sg_type_(sg_type),
      anomalous_flag_(anomalous_flag),
      asu_(sg_type),
      d_star_sq_max_(-1.)
  {
    initialize_loop(index<>(af::absolute(max_index.as_tiny())));
  }

  bool
  index_generator::set_phase_info(index<> const& h)
  {
    phase_info_ = sgtbx::phase_info(sg_type_.group(), h, false);
    return phase_info_.is_sys_absent();
  }

  index<>
  index_generator::next_under_friedel_symmetry()
  {
    int r_den = asu_.cb_op().c().r().den();
    for (; loop_.over() == 0;) {
      index<> reference_h = loop_();
      loop_.incr();
      if (asu_.reference()->is_inside(reference_h)) {
        if (asu_.is_reference()) {
          if (d_star_sq_max_ < 0.) {
            if (!reference_h.is_zero() && !set_phase_info(reference_h)) {
              return reference_h;
            }
          }
          else {
            double d_star_sq = unit_cell_.d_star_sq(reference_h);
            if (d_star_sq != 0 && d_star_sq <= d_star_sq_max_
                && !set_phase_info(reference_h)) {
              return reference_h;
            }
          }
        }
        else {
          sgtbx::tr_vec hr(reference_h * asu_.cb_op().c().r(), r_den);
          hr = hr.cancel();
          if (hr.den() == 1) {
            index<> h(hr.num());
            if (d_star_sq_max_ < 0.) {
              if (!h.is_zero() && !set_phase_info(h)) {
                return h;
              }
            }
            else {
              double d_star_sq = unit_cell_.d_star_sq(h);
              if (d_star_sq != 0 && d_star_sq <= d_star_sq_max_
                  && !set_phase_info(h)) {
                return h;
              }
            }
          }
        }
      }
    }
    return index<>(0,0,0);
  }

  index<>
  index_generator::next()
  {
    if (!anomalous_flag_) return next_under_friedel_symmetry();
    if (next_is_minus_previous_) {
      next_is_minus_previous_ = false;
      return -previous_;
    }
    previous_ = next_under_friedel_symmetry();
    if (previous_.is_zero()) return previous_;
    next_is_minus_previous_ = !phase_info_.is_centric();
    if (next_is_minus_previous_ && 143 <= sg_type_.number()
                                       && sg_type_.number() <= 167) {
      // For trigonal space groups it has to be checked if a symmetrically
      // equivalent index of the Friedel opposite is in the ASU.
      sgtbx::space_group const& sg = sg_type_.group();
      CCTBX_ASSERT(!sg.is_centric());
      index<> minus_h = -previous_;
      for(std::size_t i=0;i<sg.n_smx();i++) {
        index<> minus_h_eq = minus_h * sg.smx(i).r();
        if (asu_.is_inside(minus_h_eq)) {
          next_is_minus_previous_ = false;
          break;
        }
      }
    }
    return previous_;
  }

  af::shared<index<> >
  index_generator::to_array()
  {
    af::shared<index<> > result;
    for (;;) {
      index<> h = next();
      if (h.is_zero()) break;
      result.push_back(h);
    }
    return result;
  }

}} // namespace cctbx::miller
