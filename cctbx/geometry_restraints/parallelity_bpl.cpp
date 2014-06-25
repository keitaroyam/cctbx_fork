#include <cctbx/boost_python/flex_fwd.h>

#include <boost/python/def.hpp>
#include <boost/python/class.hpp>
#include <boost/python/args.hpp>
#include <boost/python/return_value_policy.hpp>
#include <boost/python/copy_const_reference.hpp>
#include <boost/python/return_internal_reference.hpp>
#include <boost/python/return_by_value.hpp>
#include <scitbx/array_family/boost_python/shared_wrapper.h>
#include <cctbx/geometry_restraints/parallelity.h>
#include <cctbx/geometry_restraints/proxy_select.h>

namespace cctbx { namespace geometry_restraints {
namespace {

  struct parallelity_proxy_wrappers
  {
    typedef parallelity_proxy w_t;

    static void
    wrap()
    {
      using namespace boost::python;
      typedef return_value_policy<return_by_value> rbv;
      class_<w_t>("parallelity_proxy", no_init)
        .def(init<
          af::shared<std::size_t> const&,
          af::shared<std::size_t> const&,
          double >((
            arg("i_seqs"), arg("j_seqs"), arg("weight"))))
        .def("scale_weight", &w_t::scale_weight, (arg("factor")))
        .def("sort_ij_seqs", &w_t::sort_ij_seqs)
        .add_property("i_seqs", make_getter(&w_t::i_seqs, rbv()))
        .add_property("j_seqs", make_getter(&w_t::j_seqs, rbv()))
        .add_property("weight", make_getter(&w_t::weight, rbv()))
        .add_property("sym_ops", make_getter(&w_t::sym_ops, rbv()))
      ;
      {
        scitbx::af::boost_python::shared_wrapper<w_t>::wrap(
          "shared_parallelity_proxy")
          .def("proxy_select",
            (af::shared<w_t>(*)(
              af::const_ref<w_t> const&,
              std::size_t,
              af::const_ref<std::size_t> const&))
                shared_parallelity_proxy_select, (
            arg("n_seq"), arg("iselection")))
          .def("proxy_remove",
            (af::shared<w_t>(*)(
              af::const_ref<w_t> const&,
              af::const_ref<bool> const&))
                shared_proxy_remove, (
            arg("selection")))
        ;
      }
    }
  };

  struct parallelity_wrappers
  {
    typedef parallelity w_t;

    static void
    wrap()
    {
      using namespace boost::python;
      typedef return_value_policy<copy_const_reference> ccr;
      typedef return_internal_reference<> rir;
      typedef return_value_policy<return_by_value> rbv;
      class_<w_t>("parallelity", no_init)
        .def(init<
          af::shared<scitbx::vec3<double> > const&,
          af::shared<scitbx::vec3<double> > const&,
          double >(
            (arg("i_sites"), arg("j_sites"), arg("weight"))))
        .def(init<af::const_ref<scitbx::vec3<double> > const&,
                  parallelity_proxy const&>(
          (arg("sites_cart"), arg("proxy"))))
        .def(init<uctbx::unit_cell const&,
                  af::const_ref<scitbx::vec3<double> > const&,
                  parallelity_proxy const&>(
          (arg("unit_cell"), arg("sites_cart"), arg("proxy"))))
        .add_property("i_sites", make_getter(&w_t::i_sites, rbv()))
        .add_property("j_sites", make_getter(&w_t::j_sites, rbv()))
        .add_property("weight", make_getter(&w_t::weight, rbv()))
        .def("delta", &w_t::delta, rbv())
        //.def("rms_deltas", &w_t::rms_deltas)
        .def("residual", &w_t::residual)
        .def("gradients", &w_t::gradients)
      ;
    }
  };


  void
  wrap_all()
  {
    using namespace boost::python;
    parallelity_proxy_wrappers::wrap();
    parallelity_wrappers::wrap();
    def("parallelity_deltas_rms",
      (af::shared<double>(*)(
        af::const_ref<scitbx::vec3<double> > const&,
        af::const_ref<parallelity_proxy> const&))
      parallelity_deltas_rms,
      (arg("sites_cart"), arg("proxies")));
    def("parallelity_residuals",
      (af::shared<double>(*)(
        af::const_ref<scitbx::vec3<double> > const&,
        af::const_ref<parallelity_proxy> const&))
      parallelity_residuals,
      (arg("sites_cart"), arg("proxies")));
    def("parallelity_residual_sum",
      (double(*)(
        af::const_ref<scitbx::vec3<double> > const&,
        af::const_ref<parallelity_proxy> const&,
        af::ref<scitbx::vec3<double> > const&))
      parallelity_residual_sum,
      (arg("sites_cart"), arg("proxies"), arg("gradient_array")));
    def("parallelity_deltas_rms",
      (af::shared<double>(*)(
        uctbx::unit_cell const&,
        af::const_ref<scitbx::vec3<double> > const&,
        af::const_ref<parallelity_proxy> const&))
      parallelity_deltas_rms,
      (arg("unit_cell"), arg("sites_cart"), arg("proxies")));
    def("parallelity_residuals",
      (af::shared<double>(*)(
        uctbx::unit_cell const&,
        af::const_ref<scitbx::vec3<double> > const&,
        af::const_ref<parallelity_proxy> const&))
      parallelity_residuals,
      (arg("unit_cell"), arg("sites_cart"), arg("proxies")));
    def("parallelity_residual_sum",
      (double(*)(
        uctbx::unit_cell const&,
        af::const_ref<scitbx::vec3<double> > const&,
        af::const_ref<parallelity_proxy> const&,
        af::ref<scitbx::vec3<double> > const&))
      parallelity_residual_sum,
      (arg("unit_cell"), arg("sites_cart"), arg("proxies"), arg("gradient_array")));
  }

} // namespace <anonymous>

namespace boost_python {

  void
  wrap_parallelity() { wrap_all(); }

}}} // namespace cctbx::geometry_restraints::boost_python
