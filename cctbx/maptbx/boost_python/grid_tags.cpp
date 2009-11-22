#include <cctbx/boost_python/flex_fwd.h>

#include <cctbx/maptbx/grid_tags.h>
#include <boost/python/class.hpp>
#include <boost/python/args.hpp>
#include <boost/python/return_value_policy.hpp>
#include <boost/python/copy_const_reference.hpp>
#include <boost/python/return_internal_reference.hpp>

namespace cctbx { namespace maptbx {
namespace {

  struct grid_tags_wrappers
  {
    typedef grid_tags<> w_t;

    static void
    wrap()
    {
      using namespace boost::python;
      typedef return_value_policy<copy_const_reference> ccr;
      typedef return_internal_reference<> rir;
      class_<w_t>("grid_tags", no_init)
        .def(init<af::int3 const&>((arg("dim"))))
        .def("is_valid", &w_t::is_valid)
        .def("tag_array", &w_t::tag_array)
        .def("build", &w_t::build,
          (arg("space_group_type"), arg("symmetry_flags")))
        .def("space_group_type", &w_t::space_group_type, rir())
        .def("symmetry_flags", &w_t::symmetry_flags, ccr())
        .def("grid_ss_continuous", &w_t::grid_ss_continuous, ccr())
        .def("n_grid_misses", &w_t::n_grid_misses)
        .def("n_independent", &w_t::n_independent)
        .def("n_dependent", &w_t::n_dependent)
        .def("dependent_correlation",
          (scitbx::math::linear_correlation<>(w_t::*)(
            af::const_ref<float, af::c_grid_padded<3> > const&,
            double) const)
              &w_t::dependent_correlation, (
                arg("data"),
                arg("epsilon")=1e-15))
        .def("dependent_correlation",
          (scitbx::math::linear_correlation<>(w_t::*)(
            af::const_ref<double, af::c_grid_padded<3> > const&,
            double) const)
              &w_t::dependent_correlation, (
                arg("data"),
                arg("epsilon")=1e-15))
        .def("verify",
          (bool(w_t::*)(
            af::const_ref<float, af::c_grid_padded<3> > const&,
            double) const)
              &w_t::verify, (
                arg("data"), arg("min_correlation")=0.99))
        .def("verify",
          (bool(w_t::*)(
            af::const_ref<double, af::c_grid_padded<3> > const&,
            double) const)
              &w_t::verify, (
                arg("data"), arg("min_correlation")=0.99))
        .def("sum_sym_equiv_points",
          (void(w_t::*)(af::ref<float, c_grid_padded_p1<3> > const&) const)
            &w_t::sum_sym_equiv_points,
              (arg("data")))
        .def("sum_sym_equiv_points",
          (void(w_t::*)(af::ref<double, c_grid_padded_p1<3> > const&) const)
            &w_t::sum_sym_equiv_points,
              (arg("data")))
        .def("apply_symmetry_to_mask",
          (std::size_t(w_t::*)(af::ref<int, af::c_grid<3> > const&) const)
            &w_t::apply_symmetry_to_mask,
              (arg("data")))
      ;
    }
  };

} // namespace <anoymous>

namespace boost_python {

  void wrap_grid_tags()
  {
    grid_tags_wrappers::wrap();
  }

}}} // namespace cctbx::maptbx::boost_python
