/* Copyright (c) 2001-2002 The Regents of the University of California
   through E.O. Lawrence Berkeley National Laboratory, subject to
   approval by the U.S. Department of Energy.
   See files COPYRIGHT.txt and LICENSE.txt for further details.

   Revision history:
     2003 Jun: Created based on triplet.h (R.W. Grosse-Kunstleve)
 */

/* References:
     C.M. Weeks, P.D. Adams, J. Berendzen, A.T. Brunger, E.J. Dodson,
     R.W. Grosse-Kunstleve, T.R. Schneider, G.M. Sheldrick,
     T.C. Terwilliger, M. Turkenburg, I. Uson
     Automatic solution of heavy-atom substructures.
     Methods in Enzymology, in press.

     Sheldrick, G.M. (1982).
     Crystallographic algorithms for mini- and maxi-computers.
     In: Computational Crystallography, Ed. D. Sayre,
     Oxford University Press, 506-514.
 */

#ifndef CCTBX_DMTBX_TRIPLET_GENERATOR_H
#define CCTBX_DMTBX_TRIPLET_GENERATOR_H

#include <cctbx/dmtbx/triplet_phase_relation.h>
#include <cctbx/miller/sym_equiv.h>

namespace cctbx { namespace dmtbx {

  namespace detail {

    struct expanded_index
    {
      expanded_index(
        std::size_t ih_,
        miller::sym_equiv_index sym_equiv_index_)
      :
        ih(ih_),
        h(sym_equiv_index_.h()),
        friedel_flag(sym_equiv_index_.friedel_flag()),
        ht(sym_equiv_index_.ht())
      {}

      bool
      operator<(expanded_index const& other) const
      {
        for(std::size_t i=0;i<3;i++) {
          if (h[i] < other.h[i]) return true;
          if (h[i] > other.h[i]) return false;
        }
        return false;
      }

      std::size_t ih;
      miller::index<> h;
      bool friedel_flag;
      int ht;
    };

  } // namespace detail

  template <typename FloatType = double>
  class triplet_generator
  {
    protected:
      typedef weighted_triplet_phase_relation wtpr_t;
      typedef af::shared<af::shared<wtpr_t> > array_of_wtprs_t;
      typedef af::const_ref<wtpr_t> cr_wtprs_t;

    public:
      triplet_generator() {}

      triplet_generator(
        sgtbx::space_group const& space_group,
        af::const_ref<miller::index<> > const& miller_indices,
        bool sigma_2_only=false,
        bool discard_weights=false)
      :
        t_den_(space_group.t_den()),
        sigma_2_only_(sigma_2_only),
        discard_weights_(discard_weights),
        array_of_wtprs_((af::reserve(miller_indices.size())))
      {
        std::vector<detail::expanded_index> expanded_indices;
        setup_expanded_indices(space_group, miller_indices, expanded_indices);
        for(std::size_t ih=0;ih<miller_indices.size();ih++) {
          array_of_wtprs_.push_back(find_triplets(
            ih,
            miller_indices[ih],
            expanded_indices));
        }
      }

      int
      t_den() const { return t_den_; }

      bool
      sigma_2_only() const { return sigma_2_only_; }

      bool
      discard_weights() const { return discard_weights_; }

      af::shared<std::size_t>
      n_relations() const
      {
        af::shared<std::size_t> result((af::reserve(array_of_wtprs_.size())));
        std::size_t n_miller_indices = array_of_wtprs_.size();
        for(std::size_t ih=0;ih<n_miller_indices;ih++) {
          cr_wtprs_t tprs = array_of_wtprs_[ih].const_ref();
          std::size_t n = 0;
          for(const wtpr_t* tpr=tprs.begin();tpr!=tprs.end();tpr++) {
            n += tpr->weight();
          }
          result.push_back(n);
        }
        return result;
      }

      af::shared<weighted_triplet_phase_relation>
      relations_for(std::size_t ih)
      {
        std::size_t n_miller_indices = array_of_wtprs_.size();
        CCTBX_ASSERT(ih < n_miller_indices);
        return array_of_wtprs_[ih];
      }

      af::shared<FloatType>
      sum_of_amplitude_products(
        af::const_ref<miller::index<> > const& miller_indices,
        af::const_ref<FloatType> const& amplitudes) const
      {
        CCTBX_ASSERT(miller_indices.size() == array_of_wtprs_.size());
        CCTBX_ASSERT(miller_indices.size() == amplitudes.size());
        af::shared<FloatType> result((af::reserve(amplitudes.size())));
        std::size_t n_miller_indices = array_of_wtprs_.size();
        for(std::size_t ih=0;ih<n_miller_indices;ih++) {
          cr_wtprs_t tprs = array_of_wtprs_[ih].const_ref();
          FloatType sum = 0;
          for(const wtpr_t* tpr=tprs.begin();tpr!=tprs.end();tpr++) {
            sum += amplitudes[tpr->ik()]
                 * amplitudes[tpr->ihmk()]
                 * tpr->weight();
          }
          result.push_back(sum);
        }
        return result;
      }

      af::shared<FloatType>
      apply_tangent_formula(
        af::const_ref<FloatType> const& amplitudes,
        af::const_ref<FloatType> const& phases,
        af::const_ref<bool> const& selection_fixed,
        af::const_ref<std::size_t> const& extrapolation_order,
        bool reuse_results=false,
        FloatType const& sum_epsilon=1.e-10) const
      {
        CCTBX_ASSERT(amplitudes.size() == array_of_wtprs_.size());
        CCTBX_ASSERT(phases.size() == amplitudes.size());
        CCTBX_ASSERT(   selection_fixed.size() == 0
                     || selection_fixed.size() == amplitudes.size());
        CCTBX_ASSERT(   extrapolation_order.size() == 0
                     || extrapolation_order.size() == amplitudes.size());
        af::shared<FloatType> result(phases.begin(), phases.end());
        const FloatType* phase_source = (
          reuse_results ? result.begin() : phases.begin());
        std::vector<bool> fixed_or_extrapolated;
        if (selection_fixed.size() == 0) {
          fixed_or_extrapolated.resize(amplitudes.size(), false);
        }
        else {
          fixed_or_extrapolated.assign(
            selection_fixed.begin(), selection_fixed.end());
        }
        std::size_t ih;
        for(std::size_t ip=0;ip<phases.size();ip++) {
          if (extrapolation_order.size() == 0) {
            ih = ip;
          }
          else {
            ih = extrapolation_order[ip];
            CCTBX_ASSERT(ih < amplitudes.size());
          }
          if (selection_fixed.size() != 0 && selection_fixed[ih]) continue;
          CCTBX_ASSERT(!fixed_or_extrapolated[ih]);
          cr_wtprs_t tprs = array_of_wtprs_[ih].const_ref();
          FloatType sum_sin(0);
          FloatType sum_cos(0);
          for(const wtpr_t* tpr=tprs.begin();tpr!=tprs.end();tpr++) {
            CCTBX_ASSERT(tpr->ik() < amplitudes.size());
            CCTBX_ASSERT(tpr->ihmk() < amplitudes.size());
            if (reuse_results) {
              if (!fixed_or_extrapolated[tpr->ik()]) continue;
              if (!fixed_or_extrapolated[tpr->ihmk()]) continue;
            }
            FloatType a_k_a_hmk = amplitudes[tpr->ik()]
                                * amplitudes[tpr->ihmk()]
                                * tpr->weight();
            FloatType phi_k_phi_hmk = tpr->phi_k_phi_hmk(phase_source, t_den_);
            sum_sin += a_k_a_hmk * std::sin(phi_k_phi_hmk);
            sum_cos += a_k_a_hmk * std::cos(phi_k_phi_hmk);
          }
          if (   scitbx::fn::absolute(sum_sin) >= sum_epsilon
              || scitbx::fn::absolute(sum_cos) >= sum_epsilon) {
            result[ih] = std::atan2(sum_sin, sum_cos);
            fixed_or_extrapolated[ih] = true;
          }
        }
        return result;
      }

    protected:
      void
      setup_expanded_indices(
        sgtbx::space_group const& space_group,
        af::const_ref<miller::index<> > const& miller_indices,
        std::vector<detail::expanded_index>& expanded_indices)
      {
        for(std::size_t ih=0;ih<miller_indices.size();ih++) {
          miller::index<> h = miller_indices[ih];
          miller::sym_equiv_indices sym_eq_h(space_group, h);
          int mult = sym_eq_h.multiplicity(false);
          for(std::size_t ih_eq=0;ih_eq<mult;ih_eq++) {
            miller::sym_equiv_index h_seq = sym_eq_h(ih_eq);
            CCTBX_ASSERT(h_seq.t_den() == t_den_);
            expanded_indices.push_back(detail::expanded_index(ih, h_seq));
          }
        }
        std::sort(expanded_indices.begin(), expanded_indices.end());
      }

      struct expanded_indices_scanner
      {
        expanded_indices_scanner(
          std::vector<detail::expanded_index> const& expanded_indices)
        :
          i_low(0),
          i_high(expanded_indices.size() - 1),
          e_low(&expanded_indices[i_low]),
          e_high(&expanded_indices[i_high])
        {}

        bool
        incr_low()
        {
          if (i_low == i_high) return false;
          i_low++;
          e_low++;
          return true;
        }

        bool
        decr_high()
        {
          if (i_low == i_high) return false;
          i_high--;
          e_high--;
          return true;
        }

        bool
        advance()
        {
          if (!incr_low()) return false;
          if (!decr_high()) return false;
          return true;
        }

        bool
        find_next(miller::index<> const& h)
        {
          for(std::size_t i=0;i<3;) {
            int s = e_low->h[i] + e_high->h[i];
            if (h[i] > s) {
              if (!incr_low()) return false;
              i = 0;
            }
            else if (h[i] < s) {
              if (!decr_high()) return false;
              i = 0;
            }
            else {
              i++;
            }
          }
          return true;
        }

        bool
        current_is_sigma_2(std::size_t ih) const
        {
          return e_low->ih != ih
              && e_high->ih != ih
              && e_low->ih != e_high->ih;
        }

        triplet_phase_relation
        get_tpr(int t_den) const
        {
          return triplet_phase_relation(
            e_low->ih,
            e_low->friedel_flag,
            e_low->ht,
            e_high->ih,
            e_high->friedel_flag,
            e_high->ht,
            t_den);
        }

        std::size_t
        get_weight() const
        {
          if (i_low == i_high) return 1;
          return 2;
        }

        std::size_t i_low;
        std::size_t i_high;
        const detail::expanded_index* e_low;
        const detail::expanded_index* e_high;
      };

      af::shared<weighted_triplet_phase_relation>
      find_triplets(
        std::size_t ih,
        miller::index<> const& h,
        std::vector<detail::expanded_index> const& expanded_indices)
      {
        typedef std::map<triplet_phase_relation, std::size_t> tpr_map_t;
        tpr_map_t tpr_map;
        tpr_map_t::const_iterator m;
        if (expanded_indices.size() != 0) {
          expanded_indices_scanner scanner(expanded_indices);
          while (scanner.find_next(h)) {
            if (!sigma_2_only_ || scanner.current_is_sigma_2(ih)) {
              tpr_map[scanner.get_tpr(t_den_)] += scanner.get_weight();
            }
            if (!scanner.advance()) break;
          }
        }
        af::shared<wtpr_t> wtpr_array((af::reserve(tpr_map.size())));
        if (!discard_weights_) {
          for(m=tpr_map.begin();m!=tpr_map.end();m++) {
            wtpr_array.push_back(wtpr_t(m->first, m->second));
          }
        }
        else {
          const triplet_phase_relation* prev_tpr = 0;
          for(m=tpr_map.begin();m!=tpr_map.end();m++) {
            if (prev_tpr != 0 && m->first.is_similar_to(*prev_tpr)) continue;
            prev_tpr = &m->first;
            wtpr_array.push_back(wtpr_t(m->first, 1));
          }
        }
        return wtpr_array;
      }

      int t_den_;
      bool sigma_2_only_;
      bool discard_weights_;
      array_of_wtprs_t array_of_wtprs_;
  };

}} // namespace cctbx::dmtbx

#endif // CCTBX_DMTBX_TRIPLET_GENERATOR_H
