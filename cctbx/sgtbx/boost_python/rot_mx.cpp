#include <boost/python/class.hpp>
#include <boost/python/args.hpp>
#include <boost/python/return_value_policy.hpp>
#include <boost/python/copy_const_reference.hpp>
#include <cctbx/sgtbx/rot_mx_info.h>
#include <cctbx/sgtbx/rot_mx_hash.h>

namespace cctbx { namespace sgtbx { namespace boost_python {

namespace {

  struct rot_mx_wrappers
  {
    typedef rot_mx w_t;

    static
    scitbx::vec3<double>
    rmul_vec3_double(
      w_t const& rhs,
      scitbx::vec3<double> const& lhs)
    {
      return lhs * rhs;
    }

    static std::size_t py_hash(w_t const &self) {
      return boost::hash<w_t>()(self);
    }

    static void
    wrap()
    {
      using namespace boost::python;
      typedef return_value_policy<copy_const_reference> ccr;
      class_<w_t>("rot_mx", no_init)
        .def(init<optional<int, int> >((
          arg("denominator")=1,
          arg("diagonal")=1)))
        .def(init<sg_mat3 const&, optional<int> >((
          arg("m")=1,
          arg("denominator")=1)))
        .def("num", (sg_mat3 const&(w_t::*)() const) &w_t::num, ccr())
        .def("den", (int const&(w_t::*)() const) &w_t::den, ccr())
        .def("__eq__", &w_t::operator==)
        .def("__ne__", &w_t::operator!=)
        .def("__hash__", py_hash)
        .def("is_valid", &w_t::is_valid)
        .def("is_unit_mx", &w_t::is_unit_mx)
        .def("minus_unit_mx", &w_t::minus_unit_mx)
        .def("new_denominator", &w_t::new_denominator, (arg("new_den")))
        .def("scale", &w_t::scale, (arg("factor")))
        .def("determinant", &w_t::determinant)
        .def("transpose", &w_t::transpose)
        .def("inverse", &w_t::inverse)
        .def("cancel", &w_t::cancel)
        .def("inverse_cancel", &w_t::inverse_cancel)
        .def("multiply",
          (rot_mx (w_t::*)(rot_mx const&) const) &w_t::multiply, (
            arg("rhs")))
        .def("multiply",
          (tr_vec (w_t::*)(tr_vec const&) const) &w_t::multiply, (
            arg("rhs")))
        .def("divide", &w_t::divide, (arg("rhs")))
        .def("type", &w_t::type)
        .def("order", &w_t::order, (arg("type")=0))
        .def("accumulate", &w_t::accumulate, (arg("type")=0))
        .def("info", &w_t::info)
        .def("as_double", &w_t::as_double)
        .def("as_xyz", &w_t::as_xyz, (
           arg("decimal")=false,
           arg("symbol_letters")="xyz",
           arg("separator")=","))
        .def("as_hkl", &w_t::as_hkl, (
           arg("decimal")=false,
           arg("letters_hkl")="hkl",
           arg("separator")=","))
        .def("__mul__",
          (scitbx::vec3<double>(*)(
            rot_mx const&, scitbx::vec3<double> const&)) operator*)
        .def("__rmul__", rmul_vec3_double)
      ;
    }
  };

  struct rot_mx_info_wrappers
  {
    typedef rot_mx_info w_t;

    static void
    wrap()
    {
      using namespace boost::python;
      typedef return_value_policy<copy_const_reference> ccr;
      class_<w_t>("rot_mx_info", no_init)
        .def(init<rot_mx const&>())
        .def("type", &w_t::type)
        .def("ev", &w_t::ev, ccr())
        .def("sense", &w_t::sense)
      ;
    }
  };

} // namespace <anoymous>

  void wrap_rot_mx()
  {
    rot_mx_wrappers::wrap();
    rot_mx_info_wrappers::wrap();
  }

}}} // namespace cctbx::sgtbx::boost_python
