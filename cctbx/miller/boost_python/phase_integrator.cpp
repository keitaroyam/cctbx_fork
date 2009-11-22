#include <cctbx/boost_python/flex_fwd.h>

#include <cctbx/miller/phase_integrator.h>
#include <boost/python/class.hpp>
#include <boost/python/args.hpp>

namespace cctbx { namespace miller { namespace boost_python {

namespace {

  struct phase_integrator_wrappers
  {
    typedef phase_integrator<> w_t;

    static void
    wrap()
    {
      using namespace boost::python;
      class_<w_t>("phase_integrator", no_init)
        .def(init<optional<unsigned> >(arg("n_steps")=360/5))
        .def("n_steps", &w_t::n_steps)
        .def("__call__",
          (std::complex<double>(w_t::*)(
            sgtbx::phase_info const&,
            hendrickson_lattman<> const&) const) &w_t::operator(), (
          arg("phase_info"), arg("hendrickson_lattman")))
        .def("__call__",
          (af::shared<std::complex<double> >(w_t::*)(
            sgtbx::space_group const&,
            af::const_ref<miller::index<> > const&,
            af::const_ref<hendrickson_lattman<> > const&) const)
              &w_t::operator(), (
          arg("space_group"),
          arg("miller_indices"),
          arg("hendrickson_lattman_coefficients")))
      ;
    }
  };




  struct phase_entropy_wrappers
  {
    typedef phase_entropy<> w_t;

    static void
    wrap()
    {
      using namespace boost::python;
      class_<w_t>("phase_entropy", no_init)
        .def(init<optional<unsigned> >(arg("n_steps")=360/5))
        .def("n_steps", &w_t::n_steps)
        .def("relative_entropy", &w_t::relative_entropy)
      ;
    }
  };





} // namespace <anoymous>

  void wrap_phase_integrator()
  {
    phase_integrator_wrappers::wrap();
    phase_entropy_wrappers::wrap();
  }

}}} // namespace cctbx::miller::boost_python
