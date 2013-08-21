#ifndef CCTBX_MAPTBX_ASYMMETRIC_MAP_H
#define CCTBX_MAPTBX_ASYMMETRIC_MAP_H

#include <cctbx/sgtbx/space_group_type.h>
#include <scitbx/array_family/accessors/c_interval_grid.h>
#include <cctbx/sgtbx/direct_space_asu/proto/asymmetric_unit.h>

namespace cctbx { namespace maptbx
{

//! @todo code duplication: mmtbx/masks/atom_mask.cpp
inline void translate_into_cell(scitbx::int3 &num, const scitbx::int3 &den)
{
  for(register unsigned char i=0; i<3; ++i)
  {
    register int tn = num[i];
    register const int td = den[i];
    tn %= td;
    if( tn < 0 )
      tn += td;
    num[i] = tn;
  }
}

namespace asu = cctbx::sgtbx::asu;

///// UNDER CONSTRUCTION
//  purporse: convert full unit_cell map into asymmetric unit sized map
//            convert processed aysmmetric map into form suitable for FFT
// motivation: performance improvment of various map algorithms
// code duplication: see atom_mask.h
class asymmetric_map
{
public:
  typedef scitbx::af::c_interval_grid<3> asu_grid_t;
  typedef scitbx::af::c_grid_padded<3> unit_cell_grid_t;
  typedef scitbx::af::versa<double, asu_grid_t  > data_type;
  typedef scitbx::af::ref<double, asu_grid_t  >  data_ref_t;
  typedef scitbx::af::versa<double, unit_cell_grid_t> unit_cell_map_t;

  const data_type &data() const { return data_; }

  data_ref_t data_ref() { return data_.ref(); }

  scitbx::int3 box_begin() const
  {
    return scitbx::int3(data_.accessor().origin());
  }

  scitbx::int3 box_end() const
  {
    return scitbx::int3(data_.accessor().last());
  }

  const asu::asymmetric_unit<asu::direct,asu::optimized> &optimized_asu() const
  {
    return optimized_asu_;
  }

  asymmetric_map(const sgtbx::space_group_type &group,
    const unit_cell_map_t &cell_data) : asu_(group),
    optimized_asu_(asu_,cell_data.accessor().focus()),
    unit_cell_grid_(cell_data.accessor().focus())
  {
    scitbx::int3 grid(cell_data.accessor().focus());
    asu::rvector3_t box_min, box_max;
    asu_.box_corners(box_min, box_max);
    scitbx::mul(box_min, grid);
    scitbx::mul(box_max, grid);
    auto ibox_min = scitbx::floor(box_min);
    auto ibox_max = scitbx::ceil(box_max);
    ibox_max += scitbx::int3(1,1,1); // range: [box_min,box_max)
    // auto asu_size = ibox_max - ibox_min;
    data_.resize(asu_grid_t(ibox_min, ibox_max), 0.); //! @todo optimize
    for(int i=ibox_min[0]; i<ibox_max[0]; ++i)
    {
      for(int j=ibox_min[1]; j<ibox_max[1]; ++j)
      {
        for(int k=ibox_min[2]; k<ibox_max[2]; ++k)
        {
          scitbx::int3 pos(i,j,k);
          if( optimized_asu_.where_is(pos)!=0 )
          {
            scitbx::int3 pos_in_cell(pos);
            translate_into_cell(pos_in_cell, grid);
            data_(pos) = cell_data(pos_in_cell);
          }
        }
      }
    }
  }

  const unit_cell_grid_t &unit_cell_grid() const
  {
    return unit_cell_grid_; // optimized_asu_.grid();
  }

  // const cctbx::sgtbx::space_group &space_group() const
  // {
  //  return cctbx::sgtbx::space_group(); // asu_.space_group();
  // }

  // ! no symmetry expansion here; this should be good for FFT ?
  unit_cell_map_t unit_cell_map() const
  {
    scitbx::int3 grid(this->unit_cell_grid().focus());
    unit_cell_map_t result(this->unit_cell_grid(), 0.);
    auto ibox_min = data_.accessor().origin();
    auto ibox_max = data_.accessor().last();
    for(int i=ibox_min[0]; i<ibox_max[0]; ++i)
    {
      for(int j=ibox_min[1]; j<ibox_max[1]; ++j)
      {
        for(int k=ibox_min[2]; k<ibox_max[2]; ++k)
        {
          scitbx::int3 pos(i,j,k);
          if( optimized_asu_.where_is(pos)!=0 )
          {
            scitbx::int3 pos_in_cell(pos);
            translate_into_cell(pos_in_cell, grid);
            result(pos_in_cell) = data_(pos);
          }
        }
      }
    }
    return result;
  }

  // do I really need this one ?
  unit_cell_map_t symmetry_expanded_unit_cell_map() const;

private:
  data_type data_;
  asu::direct_space_asu asu_;
  asu::asymmetric_unit<asu::direct, asu::optimized> optimized_asu_;
  unit_cell_grid_t unit_cell_grid_;
};

}} // cctbx::maptbx
#endif
