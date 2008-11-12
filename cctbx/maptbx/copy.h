#ifndef CCTBX_MAPTBX_COPY_H
#define CCTBX_MAPTBX_COPY_H

#include <cctbx/maptbx/accessors/c_grid_padded_p1.h>
#include <scitbx/array_family/accessors/c_grid_padded.h>
#include <scitbx/array_family/accessors/c_grid.h>
#include <scitbx/array_family/versa.h>
#include <scitbx/array_family/loops.h>
#include <cctbx/error.h>
#include <cctbx/import_scitbx_af.h>
#include <cassert>

namespace cctbx { namespace maptbx {

  template <typename FloatType,
            typename IndexType>
  af::versa<FloatType, af::flex_grid<IndexType> >
  copy(af::const_ref<FloatType, af::flex_grid<IndexType> > const& map,
       af::flex_grid<IndexType> const& result_grid)
  {
    CCTBX_ASSERT(map.accessor().origin().all_eq(result_grid.origin()));
    CCTBX_ASSERT(map.accessor().focus().all_eq(result_grid.focus()));
    typedef af::flex_grid<IndexType> f_g;
    typedef af::versa<FloatType, f_g> result_type;
    f_g m0 = map.accessor().shift_origin();
    f_g r0 = result_grid.shift_origin();
    assert(m0.focus().all_eq(r0.focus()));
    if (!m0.is_padded() && !r0.is_padded()) {
      result_type result;
      result.as_base_array().assign(map.begin(), map.end());
      result.resize(result_grid);
      return result;
    }
    af::nested_loop<IndexType> loop(m0.focus());
    result_type result(result_grid);
    FloatType* r_begin = result.begin();
    for (IndexType const& pt = loop(); !loop.over(); loop.incr()) {
      r_begin[r0(pt)] = map[m0(pt)];
    }
    return result;
  }

  template <typename ElementType>
  void
  copy(
    af::const_ref<ElementType, af::c_grid_padded<3> > const& source,
    af::ref<ElementType, af::c_grid<3> > const& target)
  {
    CCTBX_ASSERT(target.accessor().all_eq(source.accessor().focus()));
    typename af::c_grid_padded<3>::index_type n = target.accessor();
    typename af::c_grid_padded<3>::index_type i;
    std::size_t j = 0;
    for(i[0]=0;i[0]<n[0];i[0]++)
    for(i[1]=0;i[1]<n[1];i[1]++)
    for(i[2]=0;i[2]<n[2];i[2]++, j++) {
      target[j] = source(i);
    }
  }

  /** @brief A copy of the parallelepiped between the opposite corners
      centre - extent/2 and centre + extent/2 (fractional coordinates).

  If those corners end up outside of the unit cell, i.e. one of their
  coordinates is not between 0 and 1, then this function will still
  correctly do the copy by seeking the grid points modulo the grid sizes.
  */
  template <typename FloatType>
  af::versa<FloatType, af::flex_grid<> >
  copy_across_unit_cell_boundaries(
    af::const_ref<FloatType, af::c_grid_padded<3> > const& map_unit_cell,
    scitbx::vec3<FloatType> const& centre,
    scitbx::vec3<FloatType> const& extent)
  {
    typedef af::c_grid_padded<3>::index_type input_index_t;
    typedef af::flex_grid_default_index_type output_index_t;
    typedef typename output_index_t::value_type output_index_value_t;
    typedef scitbx::math::float_int_conversions<
      FloatType, output_index_value_t> float_to_int_conversion;
    scitbx::vec3<FloatType> first_pt = centre - extent/2,
                            last_pt = centre + extent/2;
    // conversion unsigned to signed here:
    output_index_t grid_n(af::adapt(map_unit_cell.accessor().focus()));
    af::tiny<output_index_value_t, 3> first_, last_;
    for (int i=0; i<3; ++i) {
      first_[i] = float_to_int_conversion::nearest_integer(first_pt[i]*grid_n[i]);
      last_[i]  = float_to_int_conversion::nearest_integer(last_pt[i]*grid_n[i]);
    }
    output_index_t first(af::adapt(first_)), last(af::adapt(last_));
    // range with last included
    af::versa<FloatType, af::flex_grid<> > result((
      af::flex_grid<>(af::adapt(first), af::adapt(last), false)));
    input_index_t first_input, last_input;
    for (int i=0; i<3; ++i) {
      first_input[i] = scitbx::math::mod_positive(first[i], grid_n[i]);
      last_input[i] = scitbx::math::mod_positive(last[i], grid_n[i]) + 1;
    }
    FloatType* out_ptr = result.begin();
    input_index_t input;
    for (input[0] = first_input[0]; input[0] != last_input[0]; input[0]++) {
      if (input[0] >= grid_n[0]) input[0] -= grid_n[0];
      for (input[1] = first_input[1]; input[1] != last_input[1]; input[1]++) {
        if (input[1] >= grid_n[1]) input[1] -= grid_n[1];
        for (input[2] = first_input[2]; input[2] != last_input[2]; input[2]++) {
          if (input[2] >= grid_n[2]) input[2] -= grid_n[2];
          *out_ptr++ = map_unit_cell(input);
        }
      }
    }
    return result;
  }

  template <typename FloatType>
  af::versa<FloatType, af::flex_grid<> >
  copy(
    af::const_ref<FloatType, c_grid_padded_p1<3> > const& map_unit_cell,
    af::int3 const& first,
    af::int3 const& last)
  {
    CCTBX_ASSERT(first.all_le(last));
    af::flex_grid_default_index_type first_(af::adapt(first));
    af::flex_grid_default_index_type last_(af::adapt(last));
    af::versa<FloatType, af::flex_grid<> > result(
      af::flex_grid<>(first_, last_, false));
    FloatType* out_ptr = result.begin();
    typename c_grid_padded_p1<3>::index_type out_pt;
    for (out_pt[0] = first[0]; out_pt[0] <= last[0]; out_pt[0]++) {
    for (out_pt[1] = first[1]; out_pt[1] <= last[1]; out_pt[1]++) {
    for (out_pt[2] = first[2]; out_pt[2] <= last[2]; out_pt[2]++) {
      *out_ptr++ = static_cast<FloatType>(map_unit_cell(out_pt));
    }}}
    return result;
  }

  template <
    typename ElementType,
    typename IndexType>
  void
  unpad_in_place(
    ElementType* map_begin,
    IndexType const& all,
    IndexType const& focus)
  {
    CCTBX_ASSERT(focus[0] == all[0]);
    CCTBX_ASSERT(focus[1] == all[1]);
    CCTBX_ASSERT(focus[2] <= all[2]);
    typedef typename IndexType::value_type i_v_t;
    const i_v_t n0 = focus[0];
    const i_v_t n1 = focus[1];
    const i_v_t n2 = focus[2];
    const i_v_t d2 = all[2] - n2;
    if (d2 == 0) return;
    ElementType* target = map_begin + n2;
    const ElementType* source = target + d2;
    for(i_v_t i01=1;i01<n0*n1;i01++) {
      for(i_v_t i2=0;i2<n2;i2++) *target++ = *source++;
      source += d2;
    }
  }

  template <typename ElementType>
  void
  unpad_in_place(
    af::versa<ElementType, af::flex_grid<> >& map)
  {
    CCTBX_ASSERT(map.accessor().nd() == 3);
    CCTBX_ASSERT(map.accessor().is_0_based());
    unpad_in_place(map.begin(), map.accessor().all(), map.accessor().focus());
    map = af::versa<ElementType, af::flex_grid<> >(
      map, af::flex_grid<>(map.accessor().focus()));
  }

}} // namespace cctbx::maptbx

#endif // CCTBX_MAPTBX_COPY_H
