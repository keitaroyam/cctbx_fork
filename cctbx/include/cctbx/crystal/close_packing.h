#ifndef CCTBX_CRYSTAL_CLOSE_PACKING_H
#define CCTBX_CRYSTAL_CLOSE_PACKING_H

#include <cctbx/crystal/direct_space_asu.h>

namespace cctbx { namespace crystal { namespace close_packing {

  namespace detail {

    inline
    scitbx::vec3<int> const&
    twelve_neighbor_offsets(std::size_t i)
    {
      typedef scitbx::vec3<int> v;
      static const v offsets[] = {
        v(1,0,0),v(1,1,0),v(0,1,0),v(-1,0,0),v(-1,-1,0),v(0,-1,0),
        v(0,0,1),v(-1,-1,1),v(0,-1,1),
        v(0,0,-1),v(-1,-1,-1),v(0,-1,-1)
      };
      return offsets[i];
    }

  } // namespace detail

  template <typename FloatType=double>
  class hexagonal_sampling
  {
    public:
      hexagonal_sampling() {}

      hexagonal_sampling(
        sgtbx::change_of_basis_op const& cb_op_original_to_sampling,
        direct_space_asu::float_asu<FloatType> const& float_asu,
        af::tiny<bool, 3> const& continuous_shift_flags,
        FloatType const& point_distance,
        FloatType const& buffer_thickness=-1,
        bool all_twelve_neighbors=false)
      :
        cb_op_original_to_sampling_(cb_op_original_to_sampling),
        float_asu_(float_asu),
        continuous_shift_flags_(continuous_shift_flags),
        point_distance_(point_distance),
        buffer_thickness_(buffer_thickness),
        all_twelve_neighbors_(all_twelve_neighbors),
        sampling_cell_(af::double6(
          point_distance, point_distance, point_distance*std::sqrt(8/3.),
          90, 90, 120)),
        box_lower_(0,0,0),
        box_upper_(0,0,0),
        loop_status_(0)
      {
        if (buffer_thickness_ < 0) {
          buffer_thickness_ = point_distance * (2/3. * (1/2. * std::sqrt(3.)));
        }
        float_asu_buffer_ = float_asu_.add_buffer(buffer_thickness_);
        sampling_box_determination();
        hex_to_frac_matrix_ = float_asu_.unit_cell().fractionalization_matrix()
                            * sampling_cell_.orthogonalization_matrix();
        cb_op_r_inv_ = cb_op_original_to_sampling_.c_inv().r()
          .as_floating_point(scitbx::type_holder<FloatType>());
        cb_op_t_inv_ = cb_op_original_to_sampling_.c_inv().t()
          .as_floating_point(scitbx::type_holder<FloatType>());
        incr();
      }

      sgtbx::change_of_basis_op const&
      cb_op_original_to_sampling() const {return cb_op_original_to_sampling_;}

      direct_space_asu::float_asu<FloatType> const&
      float_asu() const { return float_asu_; }

      af::tiny<bool, 3> const&
      continuous_shift_flags() const { return continuous_shift_flags_; }

      FloatType const&
      point_distance() const { return point_distance_; }

      FloatType const&
      buffer_thickness() const { return buffer_thickness_; }

      bool
      all_twelve_neighbors() const { return all_twelve_neighbors_; }

      scitbx::vec3<int> const&
      box_lower() const { return box_lower_; }

      scitbx::vec3<int> const&
      box_upper() const { return box_upper_; }

      /*! \brief True if the last site returned by next_site_frac()
          was the last one to be generated.
       */
      bool
      at_end() const { return loop_status_ < 0; }

      fractional<FloatType>
      next_site_frac()
      {
        CCTBX_ASSERT(!at_end());
        fractional<FloatType> result = get_site_frac_original();
        incr();
        return result;
      }

      af::shared<scitbx::vec3<FloatType> >
      all_sites_frac()
      {
        CCTBX_ASSERT(!at_end());
        af::shared<scitbx::vec3<FloatType> > result;
        while (!at_end()) {
          result.push_back(get_site_frac_original());
          incr();
        }
        return result;
      }

      //! Restarts the generator.
      void
      restart()
      {
        loop_status_ = 0;
        incr();
      }

      //! Counts the number of sites.
      std::size_t
      count_sites()
      {
        std::size_t result = 0;
        while (!at_end()) {
          incr();
          result++;
        }
        return result;
      }

    protected:
      sgtbx::change_of_basis_op cb_op_original_to_sampling_;
      direct_space_asu::float_asu<FloatType> float_asu_;
      af::tiny<bool, 3> continuous_shift_flags_;
      FloatType point_distance_;
      FloatType buffer_thickness_;
      bool all_twelve_neighbors_;
      uctbx::unit_cell sampling_cell_;
      direct_space_asu::float_asu<FloatType> float_asu_buffer_;
      scitbx::vec3<FloatType> box_pivot_;
      scitbx::vec3<int> box_lower_;
      scitbx::vec3<int> box_upper_;
      scitbx::mat3<FloatType> hex_to_frac_matrix_;
      scitbx::mat3<FloatType> cb_op_r_inv_;
      scitbx::vec3<FloatType> cb_op_t_inv_;
      // loop state
      int loop_status_;
      scitbx::vec3<int> point_;
      fractional<FloatType> site_frac_sampling_;
      std::size_t i12_;

      void
      sampling_box_determination()
      {
        typedef scitbx::vec3<FloatType> v;
        typedef cartesian<FloatType> c;
        typedef scitbx::math::float_int_conversions<FloatType, int> fic;
        af::shared<v> asu_vertices_cart = float_asu_.volume_vertices(true);
        CCTBX_ASSERT(asu_vertices_cart.size() > 0);
        v box_max = sampling_cell_.fractionalize(c(asu_vertices_cart[0]));
        FloatType pivot_dist_sq = box_max.length_sq();
        box_pivot_ = box_max;
        for(std::size_t i=1;i<asu_vertices_cart.size();i++) {
          v vertex_hex = sampling_cell_.fractionalize(c(asu_vertices_cart[i]));
          box_max.each_update_max(vertex_hex);
          FloatType dist_sq = vertex_hex.length_sq();
          if (pivot_dist_sq > dist_sq) {
            pivot_dist_sq = dist_sq;
            box_pivot_ = vertex_hex;
          }
        }
        asu_vertices_cart = float_asu_buffer_.volume_vertices(true);
        CCTBX_ASSERT(asu_vertices_cart.size() > 0);
        v box_buffer_min = sampling_cell_.fractionalize(
                             c(asu_vertices_cart[0]));
        v box_buffer_max = box_buffer_min;
        for(std::size_t i=1;i<asu_vertices_cart.size();i++) {
          v vertex_hex = sampling_cell_.fractionalize(c(asu_vertices_cart[i]));
          box_buffer_min.each_update_min(vertex_hex);
          box_buffer_max.each_update_max(vertex_hex);
        }
        for(std::size_t i=0;i<3;i++) {
          if (!continuous_shift_flags_[i]) {
            box_lower_[i] = std::min(-2,
              fic::ifloor(box_buffer_min[i]-box_pivot_[i]));
            int n = fic::iceil(scitbx::fn::absolute(box_max[i]-box_pivot_[i]));
            box_upper_[i] = n+std::max(2,
              fic::iceil(box_buffer_max[i]-box_max[i]));
          }
        }
      }

      static
      scitbx::vec3<FloatType>
      indices_as_site(scitbx::vec3<int> const& point, int layer=0)
      {
        typedef scitbx::vec3<FloatType> v;
        if (layer % 2 == 0) {
          if (point[2] % 2 == 0) {
            return v(point[0],point[1],point[2]*.5);
          }
          return v(point[0]+1/3.,point[1]+2/3.,point[2]*.5);
        }
        else {
          if (point[2] % 2 == 0) {
            return v(-point[0],-point[1],point[2]*.5);
          }
          return v(-point[0]-1/3.,-point[1]-2/3.,point[2]*.5);
        }
      }

      void
      incr()
      {
        if (loop_status_ == 1) goto continue_after_return_1;
        if (loop_status_ == 2) goto continue_after_return_2;
        for(point_[0]=box_lower_[0];point_[0]<=box_upper_[0];point_[0]++)
        for(point_[1]=box_lower_[1];point_[1]<=box_upper_[1];point_[1]++)
        for(point_[2]=box_lower_[2];point_[2]<=box_upper_[2];point_[2]++) {
          site_frac_sampling_ = hex_to_frac_matrix_
                              * (box_pivot_ + indices_as_site(point_));
          if (float_asu_buffer_.is_inside(site_frac_sampling_)) {
            loop_status_ = 1;
            return;
            continue_after_return_1:;
          }
          else if (all_twelve_neighbors_) {
            for(i12_=0;i12_<12;i12_++) {
              if (float_asu_.is_inside(site_frac_sampling_
                    + hex_to_frac_matrix_ * indices_as_site(
                        detail::twelve_neighbor_offsets(i12_),
                        point_[2]))) {
                loop_status_ = 2;
                return;
                continue_after_return_2:;
                break;
              }
            }
          }
        }
        loop_status_ = -1;
      }

      fractional<FloatType>
      get_site_frac_original() const
      {
        return cb_op_r_inv_ * site_frac_sampling_ + cb_op_t_inv_;
      }
  };

}}} // namespace cctbx::crystal::close_packing

#endif // CCTBX_CRYSTAL_CLOSE_PACKING_H
