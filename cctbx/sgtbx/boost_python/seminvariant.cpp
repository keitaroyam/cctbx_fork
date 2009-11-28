#include <boost/python/class.hpp>
#include <boost/python/args.hpp>
#include <boost/python/return_value_policy.hpp>
#include <boost/python/copy_const_reference.hpp>
#include <boost/python/return_by_value.hpp>
#include <cctbx/sgtbx/seminvariant.h>

namespace cctbx { namespace sgtbx { namespace boost_python {

namespace {

  struct ss_vec_mod_wrappers
  {
    typedef ss_vec_mod w_t;

    static void
    wrap()
    {
      using namespace boost::python;
      typedef return_value_policy<return_by_value> rbv;
      class_<w_t>("ss_vec_mod", no_init)
        .add_property("v", make_getter(&w_t::v, rbv()))
        .def_readonly("m", &w_t::m)
      ;
    }
  };

  struct structure_seminvariants_wrappers
  {
    typedef structure_seminvariants w_t;

    static void
    wrap()
    {
      using namespace boost::python;
      typedef return_value_policy<copy_const_reference> ccr;
      class_<w_t>("structure_seminvariants", no_init)
        .def(init<space_group const&>((arg("space_group"))))
        .def("vectors_and_moduli", &w_t::vectors_and_moduli, ccr())
        .def("size", &w_t::size)
        .def("is_ss", &w_t::is_ss, (arg("miller_index")))
        .def("apply_mod", &w_t::apply_mod, (arg("miller_index")))
        .def("select", &w_t::select, (arg("discrete")))
        .def("continuous_shifts_are_principal",
          &w_t::continuous_shifts_are_principal)
        .def("principal_continuous_shift_flags",
          &w_t::principal_continuous_shift_flags, (
            arg("assert_principal")=true))
        .def("subtract_principal_continuous_shifts",
          &w_t::subtract_principal_continuous_shifts, (
            arg("translation"),
            arg("assert_principal")=true))
        .def("gridding", &w_t::gridding)
        .def("refine_gridding",
          (sg_vec3(w_t::*)(sg_vec3 const&) const)
          &w_t::refine_gridding, (arg("grid")))
        .def("grid_adapted_moduli",
          (af::small<ss_vec_mod, 3>(w_t::*)(sg_vec3 const&) const)
          &w_t::grid_adapted_moduli, (arg("dim")))
      ;
    }
  };

} // namespace <anoymous>

  void wrap_seminvariant()
  {
    ss_vec_mod_wrappers::wrap();
    structure_seminvariants_wrappers::wrap();
  }

}}} // namespace cctbx::sgtbx::boost_python
