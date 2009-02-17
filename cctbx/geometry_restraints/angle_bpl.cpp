#include <cctbx/boost_python/flex_fwd.h>

#include <boost/python/def.hpp>
#include <boost/python/class.hpp>
#include <boost/python/args.hpp>
#include <boost/python/overloads.hpp>
#include <boost/python/return_value_policy.hpp>
#include <boost/python/copy_const_reference.hpp>
#include <boost/python/return_internal_reference.hpp>
#include <boost/python/return_by_value.hpp>
#include <scitbx/array_family/boost_python/shared_wrapper.h>
#include <scitbx/boost_python/is_polymorphic_workaround.h>
#include <cctbx/geometry_restraints/angle.h>
#include <cctbx/geometry_restraints/proxy_select.h>

SCITBX_BOOST_IS_POLYMORPHIC_WORKAROUND(cctbx::geometry_restraints::angle)

namespace cctbx { namespace geometry_restraints {
namespace {

  struct angle_params_wrappers
  {
    typedef angle_params w_t;

    static void
    wrap()
    {
      using namespace boost::python;
      class_<w_t>("angle_params", no_init)
        .def(init<double, double>((
          arg_("angle_ideal"), arg_("weight"))))
        .def_readwrite("angle_ideal", &w_t::angle_ideal)
        .def_readwrite("weight", &w_t::weight)
      ;
    }
  };

  struct angle_proxy_wrappers
  {
    typedef angle_proxy w_t;

    static void
    wrap()
    {
      using namespace boost::python;
      typedef return_value_policy<return_by_value> rbv;
      class_<w_t>("angle_proxy", no_init)
        .def(init<af::tiny<unsigned, 3> const&, double, double>(
          (arg_("i_seqs"), arg_("angle_ideal"), arg_("weight"))))
        .def("sort_i_seqs", &w_t::sort_i_seqs)
        .add_property("i_seqs", make_getter(&w_t::i_seqs, rbv()))
        .def_readonly("angle_ideal", &w_t::angle_ideal)
        .def_readonly("weight", &w_t::weight)
      ;
      {
        scitbx::af::boost_python::shared_wrapper<w_t>::wrap(
          "shared_angle_proxy")
          .def("proxy_select",
            (af::shared<w_t>(*)(
              af::const_ref<w_t> const&,
              std::size_t,
              af::const_ref<std::size_t> const&))
                shared_proxy_select, (
            arg_("n_seq"), arg_("iselection")))
          .def("proxy_remove",
            (af::shared<w_t>(*)(
              af::const_ref<w_t> const&,
              af::const_ref<bool> const&))
                shared_proxy_remove, (
            arg_("selection")))
        ;
      }
    }
  };

  struct angle_sym_proxy_wrappers
  {
    typedef angle_sym_proxy w_t;

    static void
    wrap()
    {
      using namespace boost::python;
      typedef return_value_policy<return_by_value> rbv;
      class_<w_t>("angle_sym_proxy", no_init)
        .def(init<
          af::tiny<unsigned, 3> const&,
          sgtbx::rt_mx const&,
          sgtbx::rt_mx const&,
          double,
          double>((
            arg_("i_seqs"),
            arg_("rt_mx_ji"),
            arg_("rt_mx_ki"),
            arg_("angle_ideal"),
            arg_("weight"))))
        .def("sort_i_seqs", &w_t::sort_i_seqs)
        .add_property("i_seqs", make_getter(&w_t::i_seqs, rbv()))
        .def_readonly("angle_ideal", &w_t::angle_ideal)
        .def_readonly("weight", &w_t::weight)
        .def_readonly("rt_mx_ji", &w_t::rt_mx_ji)
        .def_readonly("rt_mx_ki", &w_t::rt_mx_ki)
      ;
      {
        scitbx::af::boost_python::shared_wrapper<w_t>::wrap(
          "shared_angle_sym_proxy")
        ;
      }
    }
  };

  struct angle_wrappers
  {
    typedef angle w_t;

    BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(
      gradients_overloads, gradients, 0, 1)

    static void
    wrap()
    {
      using namespace boost::python;
      typedef return_value_policy<return_by_value> rbv;
      class_<w_t>("angle", no_init)
        .def(init<af::tiny<scitbx::vec3<double>, 3> const&, double, double>(
          (arg_("sites"), arg_("angle_ideal"), arg_("weight"))))
        .def(init<af::const_ref<scitbx::vec3<double> > const&,
                  angle_proxy const&>(
          (arg_("sites_cart"), arg_("proxy"))))
        .def(init<uctbx::unit_cell const&,
                  af::const_ref<scitbx::vec3<double> > const&,
                  angle_sym_proxy const&>(
          (arg_("unit_cell"), arg_("sites_cart"), arg_("proxy"))))
        .add_property("sites", make_getter(&w_t::sites, rbv()))
        .def_readonly("angle_ideal", &w_t::angle_ideal)
        .def_readonly("weight", &w_t::weight)
        .def_readonly("have_angle_model", &w_t::have_angle_model)
        .def_readonly("angle_model", &w_t::angle_model)
        .def_readonly("delta", &w_t::delta)
        .def("residual", &w_t::residual)
        .def("gradients", &w_t::gradients, gradients_overloads(
          (arg_("epsilon"))))
      ;
    }
  };

  void
  wrap_all()
  {
    using namespace boost::python;
    angle_params_wrappers::wrap();
    angle_proxy_wrappers::wrap();
    angle_sym_proxy_wrappers::wrap();
    angle_wrappers::wrap();
    def("angle_deltas",
      (af::shared<double>(*)(
        af::const_ref<scitbx::vec3<double> > const&,
        af::const_ref<angle_proxy> const&))
      angle_deltas,
      (arg_("sites_cart"), arg_("proxies")));
    def("angle_residuals",
      (af::shared<double>(*)(
        af::const_ref<scitbx::vec3<double> > const&,
        af::const_ref<angle_proxy> const&))
      angle_residuals,
      (arg_("sites_cart"), arg_("proxies")));
    def("angle_residual_sum",
      (double(*)(
        af::const_ref<scitbx::vec3<double> > const&,
        af::const_ref<angle_proxy> const&,
        af::ref<scitbx::vec3<double> > const&))
      angle_residual_sum,
      (arg_("sites_cart"), arg_("proxies"), arg_("gradient_array")));
    def("angle_deltas",
      (af::shared<double>(*)(
        uctbx::unit_cell const&,
        af::const_ref<scitbx::vec3<double> > const&,
        af::const_ref<angle_sym_proxy> const&))
      angle_deltas,
      (arg_("unit_cell"), arg_("sites_cart"), arg_("proxies")));
    def("angle_residuals",
      (af::shared<double>(*)(
        uctbx::unit_cell const&,
        af::const_ref<scitbx::vec3<double> > const&,
        af::const_ref<angle_sym_proxy> const&))
      angle_residuals,
      (arg_("unit_cell"), arg_("sites_cart"), arg_("proxies")));
    def("angle_residual_sum",
      (double(*)(
        uctbx::unit_cell const&,
        af::const_ref<scitbx::vec3<double> > const&,
        af::const_ref<angle_sym_proxy> const&,
        af::ref<scitbx::vec3<double> > const&))
      angle_residual_sum,
      (arg_("unit_cell"), arg_("sites_cart"), arg_("proxies"), arg_("gradient_array")));
  }

} // namespace <anonymous>

namespace boost_python {

  void
  wrap_angle() { wrap_all(); }

}}} // namespace cctbx::geometry_restraints::boost_python
