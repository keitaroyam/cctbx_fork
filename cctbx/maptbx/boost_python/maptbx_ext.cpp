#include <cctbx/boost_python/flex_fwd.h>

#include <cctbx/maptbx/copy.h>
#include <cctbx/maptbx/eight_point_interpolation.h>
#include <scitbx/boost_python/utils.h>
#include <boost/python/module.hpp>
#include <boost/python/def.hpp>
#include <boost/python/overloads.hpp>
#include <boost/python/args.hpp>

namespace cctbx { namespace maptbx { namespace boost_python {

  void wrap_grid_tags();
  void wrap_gridding();
  void wrap_misc();
  void wrap_peak_list();
  void wrap_pymol_interface();
  void wrap_statistics();
  void wrap_structure_factors();

namespace {

  BOOST_PYTHON_FUNCTION_OVERLOADS(
    non_crystallographic_eight_point_interpolation_overloads,
    non_crystallographic_eight_point_interpolation, 3, 5)

  void init_module()
  {
    using namespace boost::python;

    wrap_grid_tags();
    wrap_gridding();
    wrap_misc();
    wrap_peak_list();
    wrap_pymol_interface();
    wrap_statistics();
    wrap_structure_factors();

    def("copy",
      (af::versa<float, af::flex_grid<> >(*)
        (af::const_ref<float, af::flex_grid<> > const& map,
         af::flex_grid<> const& result_grid))
           maptbx::copy);
    def("copy",
      (af::versa<double, af::flex_grid<> >(*)
        (af::const_ref<double, af::flex_grid<> > const& map,
         af::flex_grid<> const& result_grid))
           maptbx::copy);

    def("eight_point_interpolation",
      (double(*)
        (af::const_ref<double, af::c_grid_padded<3> > const&,
         fractional<double> const&)) eight_point_interpolation);
    def("closest_grid_point",
      (af::c_grid_padded<3>::index_type(*)
        (af::const_ref<double, af::c_grid_padded<3> > const&,
         fractional<double> const&)) closest_grid_point);
    def("non_crystallographic_eight_point_interpolation",
      (double(*)
        (af::const_ref<double, af::flex_grid<> > const&,
         scitbx::mat3<double> const&,
         scitbx::vec3<double> const&,
         bool,
         double const&))
           non_crystallographic_eight_point_interpolation,
         non_crystallographic_eight_point_interpolation_overloads((
           arg_("map"),
           arg_("gridding_matrix"),
           arg_("site_cart"),
           arg_("allow_out_of_bounds")=false,
           arg_("out_of_bounds_substitute_value")=0)));
  }

} // namespace <anonymous>
}}} // namespace cctbx::maptbx::boost_python

BOOST_PYTHON_MODULE(cctbx_maptbx_ext)
{
  cctbx::maptbx::boost_python::init_module();
}
