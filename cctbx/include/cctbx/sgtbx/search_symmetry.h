#ifndef CCTBX_SGTBX_SEARCH_SYMMETRY_H
#define CCTBX_SGTBX_SEARCH_SYMMETRY_H

#include <cctbx/sgtbx/seminvariant.h>
#include <cctbx/sgtbx/space_group_type.h>

namespace cctbx { namespace sgtbx {

  class search_symmetry_flags
  {
    public:
      search_symmetry_flags() {}

      explicit
      search_symmetry_flags(
        bool use_space_group_symmetry,
        int use_space_group_ltr=0,
        bool use_seminvariant=false,
        bool use_normalizer_k2l=false,
        bool use_normalizer_l2n=false)
      :
        use_space_group_symmetry_(use_space_group_symmetry),
        use_space_group_ltr_(use_space_group_ltr),
        use_seminvariant_(use_seminvariant),
        use_normalizer_k2l_(use_normalizer_k2l),
        use_normalizer_l2n_(use_normalizer_l2n)
      {}

      bool
      use_space_group_symmetry() const { return use_space_group_symmetry_; }

      int
      use_space_group_ltr() const { return use_space_group_ltr_; }

      bool
      use_seminvariant() const { return use_seminvariant_; }

      bool
      use_normalizer_k2l() const { return use_normalizer_k2l_; }

      bool
      use_normalizer_l2n() const { return use_normalizer_l2n_; }

      bool
      operator==(search_symmetry_flags const& rhs) const
      {
        return
             use_space_group_symmetry_ == rhs.use_space_group_symmetry_
          && use_space_group_ltr_ == rhs.use_space_group_ltr_
          && use_seminvariant_ == rhs.use_seminvariant_
          && use_normalizer_k2l_ == rhs.use_normalizer_k2l_
          && use_normalizer_l2n_ == rhs.use_normalizer_l2n_;
      }

      bool
      operator!=(search_symmetry_flags const& rhs) const
      {
        return !((*this) == rhs);
      }

    protected:
      bool use_space_group_symmetry_;
      int use_space_group_ltr_;
      bool use_seminvariant_;
      bool use_normalizer_k2l_;
      bool use_normalizer_l2n_;
  };

  class search_symmetry
  {
    public:
      search_symmetry() {}

      search_symmetry(
        search_symmetry_flags const& flags,
        space_group_type const& group_type)
      :
        flags_(flags)
      {
        init(group_type);
      }

      search_symmetry(
        search_symmetry_flags const& flags,
        space_group_type const& group_type,
        structure_seminvariant const& seminvariant)
      :
        flags_(flags)
      {
        init(group_type, &seminvariant);
      }

      search_symmetry_flags const&
      flags() const { return flags_; }

      space_group const&
      group() const { return group_; }

      af::small<scitbx::vec3<int>, 3> const&
      continuous_shifts() const { return continuous_shifts_; }

      bool
      continuous_shifts_are_principal() const
      {
        typedef scitbx::vec3<int> v;
        for(std::size_t i=0;i<continuous_shifts_.size();i++) {
          v const& s = continuous_shifts_[i];
          if (   s != v(1,0,0)
              && s != v(0,1,0)
              && s != v(0,0,1)) {
            return false;
          }
        }
        return true;
      }

      af::tiny<bool, 3>
      continuous_shift_flags() const
      {
        af::tiny<bool, 3> result(false,false,false);
        typedef scitbx::vec3<int> v;
        for(std::size_t i=0;i<continuous_shifts_.size();i++) {
          v const& s = continuous_shifts_[i];
          for(std::size_t j=0;j<3;j++) {
            if (s[j]) result[j] = true;
          }
        }
        return result;
      }

      //! Projection of symmetry operations along continuous shifts.
      space_group
      projected_group() const
      {
        CCTBX_ASSERT(continuous_shifts_are_principal());
        space_group result;
        for(std::size_t i_smx=1;i_smx<group_.order_z();i_smx++) {
          rt_mx s = group_(i_smx);
          for(std::size_t i_sh=0;i_sh<continuous_shifts_.size();i_sh++) {
            std::size_t i=0;
            for(;i<3;i++) {
              if (continuous_shifts_[i_sh][i] != 0) break;
            }
            for(std::size_t j=0;j<3;j++) {
              if (j != i) s.r().num()(i,j) = 0;
            }
            s.t().num()[i] = 0;
          }
          result.expand_smx(s);
        }
        return result;
      }

    protected:
      search_symmetry_flags flags_;
      space_group group_;
      af::small<scitbx::vec3<int>, 3> continuous_shifts_;

      void
      init(
        space_group_type const& group_type,
        const structure_seminvariant* seminvariant=0)
      {
        if (flags_.use_space_group_symmetry()) {
          group_ = group_type.group();
        }
        else if (   flags_.use_space_group_ltr() > 0
                 || (   flags_.use_space_group_ltr() == 0
                     && flags_.use_seminvariant())) {
          for(std::size_t i=1;i<group_type.group().n_ltr();i++) {
            group_.expand_ltr(group_type.group().ltr(i));
          }
        }
        if (flags_.use_seminvariant()) {
          CCTBX_ASSERT(seminvariant != 0);
          af::small<ss_vec_mod, 3> const&
            ss = seminvariant->vectors_and_moduli();
          for(std::size_t i_ss=0;i_ss<ss.size();i_ss++) {
            if (ss[i_ss].m == 0) {
              continuous_shifts_.push_back(ss[i_ss].v);
            }
            else {
              group_.expand_ltr(tr_vec(ss[i_ss].v, ss[i_ss].m)
                .new_denominator(group_.t_den()));
            }
          }
        }
        if (flags_.use_normalizer_k2l() || flags_.use_normalizer_l2n()) {
          group_.expand_smx(
            group_type.addl_generators_of_euclidean_normalizer(
              flags_.use_normalizer_k2l(),
              flags_.use_normalizer_l2n()).const_ref());
        }
      }
  };

}} // namespace cctbx::sgtbx

#endif // CCTBX_SGTBX_SEARCH_SYMMETRY_H
