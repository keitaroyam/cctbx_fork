#include <cctbx/boost_python/flex_fwd.h>

#include <cctbx/xray/sampling_base.h>
#include <boost/python/class.hpp>
#include <boost/python/def.hpp>
#include <boost/python/overloads.hpp>
#include <boost/python/return_value_policy.hpp>
#include <boost/python/copy_const_reference.hpp>
#include <boost/python/return_internal_reference.hpp>

namespace cctbx { namespace xray { namespace boost_python {

namespace {

  struct sampling_base_wrappers
  {
    typedef sampling_base<> w_t;

    static void
    wrap()
    {
      using namespace boost::python;
      typedef return_value_policy<copy_const_reference> ccr;
      typedef return_internal_reference<> rir;
      class_<w_t>("sampling_base", no_init)
        .def("unit_cell", &w_t::unit_cell, rir())
        .def("u_extra", &w_t::u_extra)
        .def("wing_cutoff", &w_t::wing_cutoff)
        .def("exp_table_one_over_step_size",
          &w_t::exp_table_one_over_step_size)
        .def("tolerance_positive_definite",
          &w_t::tolerance_positive_definite)
        .def("n_scatterers_passed", &w_t::n_scatterers_passed)
        .def("n_contributing_scatterers", &w_t::n_contributing_scatterers)
        .def("n_anomalous_scatterers", &w_t::n_anomalous_scatterers)
        .def("anomalous_flag", &w_t::anomalous_flag)
        .def("exp_table_size", &w_t::exp_table_size)
        .def("max_shell_radii", &w_t::max_shell_radii, ccr())
        .def("max_shell_radii_frac", &w_t::max_shell_radii_frac)
      ;
    }
  };

  BOOST_PYTHON_FUNCTION_OVERLOADS(
    calc_u_extra_overloads, calc_u_extra, 2, 4)

  void
  apply_u_extra_double(
    uctbx::unit_cell const& unit_cell,
    double const& u_extra,
    af::const_ref<miller::index<> > const& miller_indices,
    af::ref<std::complex<double> > const& structure_factors,
    double const& multiplier=1)
  {
    apply_u_extra(unit_cell, u_extra, miller_indices, structure_factors,
                      multiplier);
  }

  BOOST_PYTHON_FUNCTION_OVERLOADS(
    apply_u_extra_double_overloads, apply_u_extra_double, 4, 5)

  void
  apply_u_extra_array_double(
    uctbx::unit_cell const& unit_cell,
    double const& u_extra,
    af::const_ref<miller::index<> > const& miller_indices,
    af::ref<std::complex<double> > const& structure_factors,
    af::const_ref<double> const& multipliers)
  {
    apply_u_extra(unit_cell, u_extra, miller_indices, structure_factors,
                      multipliers);
  }

} // namespace <anoymous>

  void wrap_sampling_base()
  {
    using namespace boost::python;

    def("calc_u_extra", calc_u_extra, calc_u_extra_overloads());
    def("apply_u_extra",apply_u_extra_double,apply_u_extra_double_overloads());
    def("apply_u_extra", apply_u_extra_array_double);

    sampling_base_wrappers::wrap();
  }

}}} // namespace cctbx::xray::boost_python
