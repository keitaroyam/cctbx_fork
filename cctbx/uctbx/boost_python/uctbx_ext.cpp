#include <cctbx/boost_python/flex_fwd.h>

#include <cctbx/uctbx.h>
#include <boost/python/tuple.hpp>
#include <boost/python/module.hpp>
#include <boost/python/def.hpp>
#include <boost/python/class.hpp>
#include <boost/python/args.hpp>
#include <boost/python/overloads.hpp>
#include <boost/python/return_value_policy.hpp>
#include <boost/python/copy_const_reference.hpp>

namespace cctbx { namespace uctbx { namespace boost_python {

  void wrap_fast_minimum_reduction();

namespace {

  BOOST_PYTHON_FUNCTION_OVERLOADS(
    d_star_sq_as_two_theta_overloads, d_star_sq_as_two_theta, 2, 3)

  struct unit_cell_wrappers : boost::python::pickle_suite
  {
    typedef unit_cell w_t;
    typedef cartesian<> cart_t;
    typedef fractional<> frac_t;
    typedef miller::index<> mix_t;
    typedef af::const_ref<mix_t> cr_mix_t;
    typedef af::shared<double> sh_dbl_t;

    BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(
      is_degenerate_overloads, is_degenerate, 0, 2)

    BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(
      is_similar_to_overloads, is_similar_to, 1, 3)

    BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(
      similarity_transformations_overloads, similarity_transformations, 1, 4)

    BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(
      change_basis_overloads, change_basis, 1, 2)

    BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(
      max_miller_indices_overloads, max_miller_indices, 1, 2)

    BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(
      two_theta_overloads, two_theta, 2, 3)

    static boost::python::tuple
    getinitargs(w_t const& ucell)
    {
      return boost::python::make_tuple(ucell.parameters());
    }

    static void
    wrap()
    {
      using namespace boost::python;
      typedef return_value_policy<copy_const_reference> ccr;
      class_<w_t>("unit_cell", no_init)
        .def(init<scitbx::mat3<double> const&>((
          arg_("orthogonalization_matrix"))))
        .def(init<scitbx::sym_mat3<double> const&>((
          arg_("metrical_matrix"))))
        .def(init<af::small<double, 6> const&>((
          arg_("parameters"))))
        .def("parameters", &w_t::parameters, ccr())
        .def("reciprocal_parameters", &w_t::reciprocal_parameters, ccr())
        .def("metrical_matrix", &w_t::metrical_matrix, ccr())
        .def("reciprocal_metrical_matrix",
          &w_t::reciprocal_metrical_matrix, ccr())
        .def("volume", &w_t::volume)
        .def("reciprocal", &w_t::reciprocal)
        .def("longest_vector_sq", &w_t::longest_vector_sq)
        .def("shortest_vector_sq", &w_t::shortest_vector_sq)
        .def("is_degenerate",
          &w_t::is_degenerate,
          is_degenerate_overloads((
            arg_("min_min_length_over_max_length")=1.e-10,
            arg_("min_volume_over_min_length")=1.e-5)))
        .def("is_similar_to",
          &w_t::is_similar_to,
          is_similar_to_overloads((
            arg_("other"),
            arg_("relative_length_tolerance")=0.01,
            arg_("absolute_angle_tolerance")=1.)))
        .def("similarity_transformations",
          &w_t::similarity_transformations,
          similarity_transformations_overloads((
            arg_("other"),
            arg_("relative_length_tolerance")=0.02,
            arg_("absolute_angle_tolerance")=2,
            arg_("unimodular_generator_range")=1)))
        .def("fractionalization_matrix", &w_t::fractionalization_matrix, ccr())
        .def("orthogonalization_matrix", &w_t::orthogonalization_matrix, ccr())
        .def("fractionalize",
          (frac_t(w_t::*)(cart_t const&) const)
          &w_t::fractionalize)
        .def("orthogonalize",
          (cart_t(w_t::*)(frac_t const& xf) const)
          &w_t::orthogonalize)
        .def("length",
          (double(w_t::*)(frac_t const& xf) const)
          &w_t::length)
        .def("distance",
          (double(w_t::*)(frac_t const& xf, frac_t const& yf) const)
          &w_t::distance)
        .def("mod_short_length",
          (double(w_t::*)(frac_t const& xf) const)
          &w_t::mod_short_length)
        .def("mod_short_distance",
          (double(w_t::*)(frac_t const& xf, frac_t const& yf) const)
          &w_t::mod_short_distance)
        .def("min_mod_short_distance",
          (double(w_t::*)
            (af::const_ref<scitbx::vec3<double> > const& xf,
             frac_t const& yf) const)
          &w_t::min_mod_short_distance)
        .def("change_basis",
          (w_t(w_t::*)(uc_mat3 const&, double) const) 0,
          change_basis_overloads())
        .def("max_miller_indices",
          (mix_t(w_t::*)(double, double) const) 0,
          max_miller_indices_overloads())
        .def("d_star_sq",
          (double(w_t::*)(mix_t const&) const)
          &w_t::d_star_sq)
        .def("d_star_sq",
          (sh_dbl_t(w_t::*)(cr_mix_t const&) const)
          &w_t::d_star_sq)
        .def("max_d_star_sq",
          (double(w_t::*)(cr_mix_t const& h) const)
          &w_t::max_d_star_sq)
        .def("min_max_d_star_sq",
          (af::double2(w_t::*)(cr_mix_t const& h) const)
          &w_t::min_max_d_star_sq)
        .def("stol_sq",
          (double(w_t::*)(mix_t  const& h) const)
          &w_t::stol_sq)
        .def("stol_sq",
          (sh_dbl_t(w_t::*)(cr_mix_t const& h) const)
          &w_t::stol_sq)
        .def("two_stol",
          (double(w_t::*)(mix_t const& h) const)
          &w_t::two_stol)
        .def("two_stol",
          (sh_dbl_t(w_t::*)(cr_mix_t const& h) const)
          &w_t::two_stol)
        .def("stol",
          (double(w_t::*)(mix_t const& h) const)
          &w_t::stol)
        .def("stol",
          (sh_dbl_t(w_t::*)(cr_mix_t const& h) const)
          &w_t::stol)
        .def("d",
          (double(w_t::*)(mix_t const& h) const)
          &w_t::d)
        .def("d",
          (sh_dbl_t(w_t::*)(cr_mix_t const& h) const)
          &w_t::d)
        .def("two_theta",
          (double(w_t::*)(mix_t const&, double, bool) const) 0,
          two_theta_overloads())
        .def("two_theta",
          (sh_dbl_t(w_t::*)(cr_mix_t const&, double, bool) const) 0,
          two_theta_overloads())
        .def("compare_orthorhombic", &w_t::compare_orthorhombic,
          (arg_("other")))
        .def("compare_monoclinic", &w_t::compare_monoclinic,
          (arg_("other"), arg_("unique_axis"), arg_("angular_tolerance")))
        .def_pickle(unit_cell_wrappers())
      ;
    }
  };

  void init_module()
  {
    using namespace boost::python;

    def("d_star_sq_as_stol_sq", d_star_sq_as_stol_sq);
    def("d_star_sq_as_two_stol", d_star_sq_as_two_stol);
    def("d_star_sq_as_stol", d_star_sq_as_stol);
    def("d_star_sq_as_two_theta", d_star_sq_as_two_theta,
      d_star_sq_as_two_theta_overloads());
    def("d_star_sq_as_d", d_star_sq_as_d);

    unit_cell_wrappers::wrap();
    wrap_fast_minimum_reduction();
  }

} // namespace <anonymous>
}}} // namespace cctbx::uctbx::boost_python

BOOST_PYTHON_MODULE(cctbx_uctbx_ext)
{
  cctbx::uctbx::boost_python::init_module();
}
