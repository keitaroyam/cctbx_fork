#include <cctbx/boost_python/flex_fwd.h>

#include <cctbx/maptbx/fft.h>
#include <cctbx/maptbx/average_densities.h>
#include <cctbx/maptbx/standard_deviations_around_sites.hpp>
#include <cctbx/maptbx/real_space_gradients_simple.h>
#include <cctbx/maptbx/real_space_target_and_gradients.h>
#include <scitbx/boost_python/utils.h>
#include <boost/python/module.hpp>
#include <boost/python/class.hpp>
#include <boost/python/def.hpp>
#include <boost/python/args.hpp>
#include <cctbx/maptbx/histogram.h>
#include <cctbx/maptbx/sphericity.h>
#include <cctbx/maptbx/mask.h>
#include <cctbx/maptbx/utils.h>
#include <cctbx/maptbx/connectivity.h>

namespace cctbx { namespace maptbx { namespace boost_python {

  void wrap_grid_indices_around_sites();
  void wrap_grid_tags();
  void wrap_gridding();
  void wrap_misc();
  void wrap_peak_list();
  void wrap_pymol_interface();
  void wrap_statistics();
  void wrap_structure_factors();
  void wrap_coordinate_transformers();
  void wrap_mappers();
  void wrap_basic_map();
  void wrap_real_space_refinement();

namespace {

  void init_module()
  {
    using namespace boost::python;

    wrap_grid_indices_around_sites();
    wrap_grid_tags();
    wrap_gridding();
    wrap_misc();
    wrap_peak_list();
    wrap_pymol_interface();
    wrap_statistics();
    wrap_structure_factors();
    wrap_coordinate_transformers();
    wrap_mappers();
    wrap_basic_map();
    wrap_real_space_refinement();

    {
      typedef target_and_gradients w_t;
      class_<w_t>("target_and_gradients", no_init)
        .def(init<uctbx::unit_cell const&,
                  af::const_ref<double, af::c_grid_padded<3> > const&,
                  af::const_ref<double, af::c_grid_padded<3> > const&,
                  double const&,
                  af::const_ref<scitbx::vec3<double> > const& >((
                                    arg("unit_cell"),
                                    arg("map_target"),
                                    arg("map_current"),
                                    arg("step"),
                                    arg("sites_frac"))))
        .def("target", &w_t::target)
        .def("gradients", &w_t::gradients)
      ;
    }
    {
      typedef grid_points_in_sphere_around_atom_and_distances w_t;

      class_<w_t>("grid_points_in_sphere_around_atom_and_distances", no_init)
        .def(init<cctbx::uctbx::unit_cell const&,
                  af::const_ref<double, af::c_grid<3> > const&,
                  double const&,
                  double const&,
                  scitbx::vec3<double> const& >(
                    (arg("unit_cell"),
                     arg("data"),
                     arg("radius"),
                     arg("shell"),
                     arg("site_frac"))))
        .def("data_at_grid_points", &w_t::data_at_grid_points)
        .def("data_at_grid_points_averaged", &w_t::data_at_grid_points_averaged)
        .def("distances", &w_t::distances)
      ;
    }
    //
    {
      typedef non_linear_map_modification_to_match_average_cumulative_histogram w_t;

      class_<w_t>("non_linear_map_modification_to_match_average_cumulative_histogram", no_init)
        .def(init<af::const_ref<double, af::c_grid<3> > const&,
                  af::const_ref<double, af::c_grid<3> > const& >(
                    (arg("map_1"),
                     arg("map_2"))))
        .def("map_1", &w_t::map_1)
        .def("map_2", &w_t::map_2)
        .def("histogram_1", &w_t::histogram_1)
        .def("histogram_2", &w_t::histogram_2)
        .def("histogram_12", &w_t::histogram_12)
        .def("histogram_values", &w_t::histogram_values)
      ;
    }
    //
    {
      typedef histogram w_t;

      class_<w_t>("histogram", no_init)
        .def(init<af::const_ref<double, af::c_grid<3> > const&,
                  int const& >(
                    (arg("map"),
                     arg("n_bins"))))
        .def("values",    &w_t::values)
        .def("c_values",  &w_t::c_values)
        .def("v_values",  &w_t::v_values)
        .def("bin_width", &w_t::bin_width)
        .def("arguments", &w_t::arguments)
      ;
    }

    {
      typedef volume_scale w_t;

      class_<w_t>("volume_scale", no_init)
        .def(init<af::const_ref<double, af::c_grid<3> > const&,
                  int const& >(
                    (arg("map"),
                     arg("n_bins"))))
        .def("map_data", &w_t::map_data)
        .def("v_values", &w_t::v_values)
      ;
    }

    {
      typedef connectivity w_t;

      class_<w_t>("connectivity", no_init)
        .def(init<af::const_ref<double, af::c_grid<3> > const&,
                  double const& >(
                    (arg("map_data"),
                     arg("threshold"))))
        .def("result",    &w_t::result)
        .def("regions",   &w_t::regions)
      ;
    }

    {
      typedef one_gaussian_peak_approximation w_t;

      class_<w_t>("one_gaussian_peak_approximation", no_init)
        .def(init<af::const_ref<double> const&,
                  af::const_ref<double> const&,
                  bool const&,
                  bool const& >(
                    (arg("data_at_grid_points"),
                     arg("distances"),
                     arg("use_weights"),
                     arg("optimize_cutoff_radius"))))
        .def("a_real_space", &w_t::a_real_space)
        .def("b_real_space", &w_t::b_real_space)
        .def("a_reciprocal_space", &w_t::a_reciprocal_space)
        .def("b_reciprocal_space", &w_t::b_reciprocal_space)
        .def("gof", &w_t::gof)
        .def("cutoff_radius", &w_t::cutoff_radius)
        .def("weight_power", &w_t::weight_power)
        .def("first_zero_radius", &w_t::first_zero_radius)
      ;
    }

    def("copy",
      (af::versa<float, af::flex_grid<> >(*)
        (af::const_ref<float, af::flex_grid<> > const&,
         af::flex_grid<> const&)) maptbx::copy, (
      arg("map"),
      arg("result_grid")));
    def("copy",
      (af::versa<double, af::flex_grid<> >(*)
        (af::const_ref<double, af::flex_grid<> > const&,
         af::flex_grid<> const&)) maptbx::copy, (
      arg("map"),
      arg("result_grid")));
    def("copy",
      (af::versa<float, af::flex_grid<> >(*)
        (af::const_ref<float, c_grid_padded_p1<3> > const&,
         af::int3 const&,
         af::int3 const&)) maptbx::copy, (
      arg("map_unit_cell"),
      arg("first"),
      arg("last")));
    def("copy",
      (af::versa<double, af::flex_grid<> >(*)
        (af::const_ref<double, c_grid_padded_p1<3> > const&,
         af::int3 const&,
         af::int3 const&)) maptbx::copy, (
      arg("map_unit_cell"),
      arg("first"),
      arg("last")));
    def("unpad_in_place",
      (void(*)(af::versa<float, af::flex_grid<> >&))
        maptbx::unpad_in_place, (arg("map")));
    def("unpad_in_place",
      (void(*)(af::versa<double, af::flex_grid<> >&))
        maptbx::unpad_in_place, (arg("map")));

    def("fft_to_real_map_unpadded",
      (af::versa<double, af::c_grid<3> >(*)(
        sgtbx::space_group const&,
        af::tiny<int, 3> const&,
        af::const_ref<miller::index<> > const&,
        af::const_ref<std::complex<double> > const&))
          maptbx::fft_to_real_map_unpadded, (
            arg("space_group"),
            arg("n_real"),
            arg("miller_indices"),
            arg("data")));

    def("direct_summation_at_point",
      (std::complex<double>(*)(
        af::const_ref<miller::index<> > const&,
        af::const_ref<std::complex<double> > const&,
        scitbx::vec3<double>))
          maptbx::direct_summation_at_point, (
            arg("miller_indices"),
            arg("data"),
            arg("site_frac")));

    def("cc_weighted_maps",cc_weighted_maps);

    def("kuwahara_filter",
      (void(*)
        (af::ref<double, af::c_grid<3> >,
         int const&)) kuwahara_filter, (
      arg("map_data"),
      arg("index_span")));

    def("median_filter",
      (void(*)
        (af::ref<double, af::c_grid<3> >,
         int const&)) median_filter, (
      arg("map_data"),
      arg("index_span")));

    def("remove_single_node_peaks",
      (void(*)
        (af::ref<double, af::c_grid<3> >,
         af::ref<double, af::c_grid_padded<3> >,
         double const&,
         int const&)) remove_single_node_peaks, (
      arg("map_data"),
      arg("mask_data"),
      arg("cutoff"),
      arg("index_span")));

    def("map_box_average",
      (void(*)
        (af::ref<double, af::c_grid<3> >,
         double const&,
         int const&)) map_box_average, (
      arg("map_data"),
      arg("cutoff"),
      arg("index_span")));

    def("sharpen",
      (void(*)
        (af::ref<double, af::c_grid<3> >,
         int const&,
         int const&)) sharpen, (
      arg("map_data"),
      arg("index_span"),
      arg("n_averages")));

    def("map_box_average",
      (void(*)
        (af::ref<double, af::c_grid<3> >,
         cctbx::uctbx::unit_cell const&,
         double const&)) map_box_average, (
      arg("map_data"),
      arg("unit_cell"),
      arg("radius")));

    def("hoppe_gassman_modification",
      (void(*)
        (af::ref<double, af::c_grid<3> >,
         double,
         int)) hoppe_gassman_modification, (
      arg("data"),
      arg("mean_scale"),
      arg("n_iterations")));

    def("hoppe_gassman_modification2",
      (void(*)
        (af::ref<double, af::c_grid<3> >,
         double,
         int)) hoppe_gassman_modification2, (
      arg("data"),
      arg("mean_scale"),
      arg("n_iterations")));

    def("sphericity_tensor",
      (scitbx::sym_mat3<double>(*)
        (af::const_ref<double, af::c_grid<3> > const&,
          uctbx::unit_cell const&,
         double const&,
         cctbx::fractional<> const&)) sphericity_tensor, (
      arg("map_data"),
      arg("unit_cell"),
      arg("radius"),
      arg("site_frac")));

    def("sphericity",
      (af::shared<double>(*)
        (af::const_ref<double, af::c_grid<3> > const&,
          uctbx::unit_cell const&,
         double const&,
         af::const_ref<scitbx::vec3<double> > const&)) sphericity, (
      arg("map_data"),
      arg("unit_cell"),
      arg("radius"),
      arg("sites_frac")));

    def("average_densities",
      (af::shared<double>(*)
        (uctbx::unit_cell const&,
         af::const_ref<double, af::c_grid<3> > const&,
         af::const_ref<scitbx::vec3<double> > const&,
         float)) average_densities, (
      arg("unit_cell"),
      arg("data"),
      arg("sites_frac"),
      arg("radius")));

    def("mask",
      (af::versa<double, af::c_grid<3> >(*)
        (af::const_ref<scitbx::vec3<double> > const&,
          uctbx::unit_cell const&,
          af::tiny<int, 3> const&,
          af::const_ref<double> const&)) mask, (
      arg("sites_frac"),
      arg("unit_cell"),
      arg("n_real"),
      arg("radii")));

    def("convert_to_non_negative",
      (void(*)
        (af::ref<double, af::c_grid<3> >,
         double)) convert_to_non_negative, (
      arg("data"),
      arg("substitute_value")));

    def("flexible_boundary_mask",
      (void(*)
        (af::ref<double, af::c_grid<3> >,
         af::ref<double, af::c_grid<3> >)) flexible_boundary_mask, (
      arg("data"),
      arg("mask")));

    def("reset",
      (void(*)
        (af::ref<double, af::c_grid<3> >,
         double,
         double,
         double,
         bool)) reset, (
      arg("data"),
      arg("substitute_value"),
      arg("less_than_threshold"),
      arg("greater_than_threshold"),
      arg("use_and")));

    def("intersection",
      (void(*)
        (af::ref<double, af::c_grid<3> >,
         af::ref<double, af::c_grid<3> >,
         af::ref<double> const&,
         bool)) intersection, (
      arg("map_data_1"),
      arg("map_data_2"),
      arg("thresholds"),
      arg("average")));

    def("cut_by",
      (void(*)
        (af::ref<double, af::c_grid<3> >,
         af::ref<double, af::c_grid<3> >,
         double)) cut_by, (
      arg("kick"),
      arg("fem"),
      arg("cut_by_threshold")));

    def("rotate_translate_map",
      (af::versa<double, af::c_grid<3> >(*)
        (uctbx::unit_cell const&,
         af::const_ref<double, af::c_grid<3> > const&,
         scitbx::mat3<double> const&,
         scitbx::vec3<double> const&,
         af::tiny<int, 3> const&,
         af::tiny<int, 3> const&)) rotate_translate_map, (
      arg("unit_cell"),
      arg("map_data"),
      arg("rotation_matrix"),
      arg("translation_vector"),
      arg("start"),
      arg("end")));

    def("rotate_translate_map",
      (af::versa<double, af::c_grid<3> >(*)
        (uctbx::unit_cell const&,
         af::const_ref<double, af::c_grid<3> > const&,
         scitbx::mat3<double> const&,
         scitbx::vec3<double> const& )) rotate_translate_map, (
      arg("unit_cell"),
      arg("map_data"),
      arg("rotation_matrix"),
      arg("translation_vector")));

    def("superpose_maps",
      (af::versa<double, af::c_grid<3> >(*)
        (uctbx::unit_cell const&,
         uctbx::unit_cell const&,
         af::const_ref<double, af::c_grid<3> > const&,
         af::tiny<int, 3> const&,
         scitbx::mat3<double> const&,
         scitbx::vec3<double> const& )) superpose_maps, (
      arg("unit_cell_1"),
      arg("unit_cell_2"),
      arg("map_data_1"),
      arg("n_real_2"),
      arg("rotation_matrix"),
      arg("translation_vector")));

    def("combine_and_maximize_maps",
      (af::versa<double, af::c_grid<3> >(*)
        (af::const_ref<double, af::c_grid<3> > const&,
         af::const_ref<double, af::c_grid<3> > const&,
         af::tiny<int, 3> const& )) combine_and_maximize_maps, (
      arg("map_data_1"),
      arg("map_data_2"),
      arg("n_real")));

    def("denmod_simple",
      (af::versa<double, af::c_grid<3> >(*)
        (af::const_ref<double, af::c_grid<3> > const&,
         af::tiny<int, 3> const&,
         double,double)) denmod_simple, (
      arg("map_data"),
      arg("n_real"),
      arg("cutoffp"),
      arg("cutoffm")));

    def("truncate_between_min_max",
      (void(*)
        (af::ref<double, af::c_grid<3> >,
         double const&,
         double const&)) truncate_between_min_max, (
      arg("map_data"),
      arg("min"),
      arg("max")));

    def("truncate",
      (void(*)
        (af::ref<double, af::c_grid<3> >,
         double const&,
         double const&,
         double const&,
         double const&)) truncate, (
      arg("map_data"),
      arg("standard_deviation"),
      arg("by_sigma_less_than"),
      arg("scale_by"),
      arg("set_value")));

    def("fem_averaging_loop",
      (af::shared<std::complex<double> >(*)
        (af::const_ref<std::complex<double> > const&,
         af::const_ref<double> const&,
         af::const_ref<double> const&,
         double const&,
         int const&,
         int const&)) fem_averaging_loop, (
      arg("map_coefficients"),
      arg("r_factors"),
      arg("sigma_over_f_obs"),
      arg("random_scale"),
      arg("random_seed"),
      arg("n_cycles")));

    def("conditional_solvent_region_filter",
      (af::versa<double, af::c_grid<3> >(*)
        (af::const_ref<double, af::c_grid_padded<3> > const&,
         af::const_ref<double, af::c_grid<3> > const&,
         double const&)) conditional_solvent_region_filter, (
      arg("bulk_solvent_mask"),
      arg("map_data"),
      arg("threshold")));

    def("map_sum_at_sites_frac",
      (double(*)
        (af::const_ref<double, af::c_grid<3> > const&,
         af::const_ref<scitbx::vec3<double> > const&)) map_sum_at_sites_frac, (
      arg("map_data"),
      arg("sites_frac")));

    def("set_box_copy",
      (af::versa<double, af::c_grid<3> >(*)
        (double const&,
         af::ref<double, af::c_grid<3> >,
         af::tiny<int, 3> const&,
         af::tiny<int, 3> const&)) set_box_copy, (
      arg("value"),
      arg("map_data_to"),
      arg("start"),
      arg("end")));

    def("set_box",
      (void(*)
        (double const&,
         af::ref<double, af::c_grid<3> >,
         af::tiny<int, 3> const&,
         af::tiny<int, 3> const&)) set_box, (
      arg("value"),
      arg("map_data_to"),
      arg("start"),
      arg("end")));

    def("set_box",
      (void(*)
        (af::const_ref<double, af::c_grid<3> > const&,
         af::ref<double, af::c_grid<3> >,
         af::tiny<int, 3> const&,
         af::tiny<int, 3> const&)) set_box, (
      arg("map_data_from"),
      arg("map_data_to"),
      arg("start"),
      arg("end")));

    def("copy_box",
      (void(*)
        (af::const_ref<double, af::c_grid<3> > const&,
         af::ref<double, af::c_grid<3> >,
         af::tiny<int, 3> const&,
         af::tiny<int, 3> const&)) copy_box, (
      arg("map_data_from"),
      arg("map_data_to"),
      arg("start"),
      arg("end")));

    def("eight_point_interpolation",
      (double(*)
        (af::const_ref<double, af::c_grid_padded<3> > const&,
         scitbx::vec3<double> const&)) eight_point_interpolation);
    def("closest_grid_point",
      (af::c_grid_padded<3>::index_type(*)
        (af::flex_grid<> const&,
         fractional<double> const&)) closest_grid_point);
    def("tricubic_interpolation",
      (double(*)
        (af::const_ref<double, af::c_grid_padded<3> > const&,
         scitbx::vec3<double> const&)) tricubic_interpolation);
    def("non_crystallographic_eight_point_interpolation",
      (double(*)
        (af::const_ref<double, af::flex_grid<> > const&,
         scitbx::mat3<double> const&,
         scitbx::vec3<double> const&,
         bool,
         double const&))
           non_crystallographic_eight_point_interpolation, (
             arg("map"),
             arg("gridding_matrix"),
             arg("site_cart"),
             arg("allow_out_of_bounds")=false,
             arg("out_of_bounds_substitute_value")=0));
    def("asu_eight_point_interpolation",
      (double(*)
        (af::const_ref<double, af::flex_grid<> > const&,
         crystal::direct_space_asu::asu_mappings<double> &,
         fractional<double> const&)) asu_eight_point_interpolation);
    def("real_space_target_simple",
      (double(*)
        (uctbx::unit_cell const&,
         af::const_ref<double, af::c_grid_padded<3> > const&,
         af::const_ref<scitbx::vec3<double> > const&,
         af::const_ref<bool> const&))
           real_space_target_simple, (
             arg("unit_cell"),
             arg("density_map"),
             arg("sites_cart"),
             arg("selection")));
    def("real_space_target_simple",
      (double(*)
        (af::const_ref<double, af::c_grid<3> > const&,
         af::const_ref<scitbx::vec3<double> > const&))
           real_space_target_simple, (
             arg("density_map"),
             arg("sites_frac")));
    def("real_space_target_simple_per_site",
      (af::shared<double>(*)
        (uctbx::unit_cell const&,
         af::const_ref<double, af::c_grid_padded<3> > const&,
         af::const_ref<scitbx::vec3<double> > const&))
           real_space_target_simple_per_site, (
             arg("unit_cell"),
             arg("density_map"),
             arg("sites_cart")));
    def("real_space_gradients_simple",
      (af::shared<scitbx::vec3<double> >(*)
        (uctbx::unit_cell const&,
         af::const_ref<double, af::c_grid_padded<3> > const&,
         af::const_ref<scitbx::vec3<double> > const&,
         double,
         af::const_ref<bool> const&)) real_space_gradients_simple, (
           arg("unit_cell"),
           arg("density_map"),
           arg("sites_cart"),
           arg("delta"),
           arg("selection")));

    def("standard_deviations_around_sites",
      standard_deviations_around_sites, (
        arg("unit_cell"),
        arg("density_map"),
        arg("sites_cart"),
        arg("site_radii")));
  }

} // namespace <anonymous>
}}} // namespace cctbx::maptbx::boost_python

BOOST_PYTHON_MODULE(cctbx_maptbx_ext)
{
  cctbx::maptbx::boost_python::init_module();
}
