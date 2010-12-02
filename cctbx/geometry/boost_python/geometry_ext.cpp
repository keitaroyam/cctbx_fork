#include <boost/python/module.hpp>
#include <boost/python/class.hpp>
#include <cctbx/geometry/geometry.h>

namespace cctbx { namespace geometry { namespace boost_python {

  static void wrap_distance() {
    using namespace boost::python;
    typedef distance<double> wt;

    class_<wt>("distance", no_init)
      .def(init<af::tiny<scitbx::vec3<double>, 2> const &>())
      .def("d_distance_d_sites", &wt::d_distance_d_sites, (
            arg("epsilon")=1.e-100))
      .def("d_distance_d_metrical_matrix", &wt::d_distance_d_metrical_matrix,
           (arg("unit_cell")))
      .def("d_distance_d_cell_params", &wt::d_distance_d_cell_params,
           (arg("unit_cell")))
      .def("variance",
       (double(wt::*)(
        af::const_ref<double, af::packed_u_accessor> const &,
        cctbx::uctbx::unit_cell const &,
        sgtbx::rt_mx const &) const)
          &wt::variance,
         (arg("covariance_matrix"),
          arg("unit_cell"),
          arg("rt_mx_ji")))
      .def("variance",
       (double(wt::*)(
        af::const_ref<double, af::packed_u_accessor> const &,
        af::const_ref<double, af::packed_u_accessor> const &,
        cctbx::uctbx::unit_cell const &,
        sgtbx::rt_mx const &) const)
          &wt::variance,
         (arg("covariance_matrix"),
          arg("cell_covariance_matrix"),
          arg("unit_cell"),
          arg("rt_mx_ji")))
      .def_readonly("distance_model", &wt::distance_model)
    ;
  }

  static void wrap_angle() {
    using namespace boost::python;
    typedef angle<double> wt;

    class_<wt>("angle", no_init)
      .def(init<af::tiny<scitbx::vec3<double>, 3> const &>())
      .def("d_angle_d_sites", &wt::d_angle_d_sites, (
            arg("epsilon")=1.e-100))
      .def("d_angle_d_metrical_matrix", &wt::d_angle_d_metrical_matrix,
           (arg("unit_cell"), arg("epsilon")=1.e-100))
      .def("d_angle_d_cell_params", &wt::d_angle_d_cell_params,
           (arg("unit_cell")))
      .def("variance",
       (double(wt::*)(
        af::const_ref<double, af::packed_u_accessor> const &,
        cctbx::uctbx::unit_cell const &,
        optional_container<af::shared<sgtbx::rt_mx> > const &) const)
          &wt::variance,
         (arg("covariance_matrix"),
          arg("unit_cell"),
          arg("sym_ops")))
      .def("variance",
       (double(wt::*)(
        af::const_ref<double, af::packed_u_accessor> const &,
        af::const_ref<double, af::packed_u_accessor> const &,
        cctbx::uctbx::unit_cell const &,
        optional_container<af::shared<sgtbx::rt_mx> > const &) const)
          &wt::variance,
         (arg("covariance_matrix"),
          arg("cell_covariance_matrix"),
          arg("unit_cell"),
          arg("sym_ops")))
      .def_readonly("angle_model", &wt::angle_model)
    ;
  }

  void init_module()
  {
    wrap_distance();
    wrap_angle();
  }

}}} // namespace cctbx::geometry::boost_python

BOOST_PYTHON_MODULE(cctbx_geometry_ext)
{
  cctbx::geometry::boost_python::init_module();
}
