#include <boost/python/def.hpp>
#include <boost/python/class.hpp>
#include <boost/python/args.hpp>
#include <boost/python/return_value_policy.hpp>
#include <boost/python/return_by_value.hpp>
#include <cctbx/adp_restraints/adp_restraints.h>
#include <cctbx/adp_restraints/isotropic_adp.h>
#include <cctbx/adp_restraints/fixed_u_eq_adp.h>
#include <cctbx/adp_restraints/adp_similarity.h>
#include <scitbx/boost_python/container_conversions.h>


namespace cctbx { namespace adp_restraints {

namespace {

  template <typename FloatType>
  struct adp_restraint_params_wrapper {
    static void wrap() {
      using namespace boost::python;
      typedef adp_restraint_params<FloatType> w_t;
      class_<w_t>("adp_restraint_params", no_init)
        .def(init<
              af::shared<scitbx::vec3<FloatType> > const &,
              af::shared<scitbx::sym_mat3<FloatType> > const &,
              af::shared<FloatType> const &,
              af::shared<bool> const &>(
             (arg("sites_cart"),
              arg("u_cart"),
              arg("u_iso"),
              arg("use_u_aniso"))))
        .def(init<
              af::shared<scitbx::sym_mat3<FloatType> > const &,
              af::shared<FloatType> const &,
              af::shared<bool> const &>(
             (arg("u_cart"),
              arg("u_iso"),
              arg("use_u_aniso"))))
        .def(init<
              af::shared<scitbx::vec3<FloatType> > const &,
              af::shared<scitbx::sym_mat3<FloatType> > const &>(
             (arg("sites_cart"),
              arg("u_cart"))))
        .def(init<
              af::shared<scitbx::sym_mat3<FloatType> > const &>(
             (arg("u_cart"))))
        .def(init<
              af::shared<FloatType> const &>(
             (arg("u_iso"))))
        ;
    }
  };

  struct functions_wrapper {
    template <typename ProxyType, typename RestraintType>
    static void wrap(std::string name) {
      using namespace boost::python;
      def((name+"_residual_sum").c_str(),
        adp_restraint_residual_sum<ProxyType,RestraintType>,
        (arg("params"),
         arg("proxies"),
         arg("gradients_aniso_cart"),
         arg("gradients_iso")));
      def((name+"_residuals").c_str(),
        adp_restraint_residuals<ProxyType,RestraintType>,
        (arg("params"),
         arg("proxies")));
      def((name+"_deltas_rms").c_str(),
        adp_restraint_deltas_rms<ProxyType,RestraintType>,
        (arg("params"),
         arg("proxies")));
    }

    template <typename ProxyType, typename RestraintType>
    static void wrap_aniso(std::string name) {
      using namespace boost::python;
      def((name+"_residual_sum").c_str(),
        adp_restraint_residual_sum_aniso<ProxyType,RestraintType>,
        (arg("params"),
         arg("proxies"),
         arg("gradients_aniso_cart")));
      def((name+"_residuals").c_str(),
        adp_restraint_residuals<ProxyType,RestraintType>,
        (arg("params"),
         arg("proxies")));
      def((name+"_deltas_rms").c_str(),
        adp_restraint_deltas_rms<ProxyType,RestraintType>,
        (arg("params"),
         arg("proxies")));
    }
  };

  template <int n_adp>
  struct adp_restraint_base_wrapper  {
    static void wrap_proxy() {
      typedef adp_restraint_proxy<n_adp> w_t;
      using namespace boost::python;
      typedef return_value_policy<return_by_value> rbv;
      std::ostringstream sname("adp_restraint_proxy");
      if (n_adp > 1) sname << n_adp;
      std::string name = sname.str();
      class_<w_t>
            (name.c_str(), no_init)
        .def(init<
           af::tiny<unsigned, n_adp> const &,
           double>(
          (arg("i_seqs"),
           arg("weight"))))
        .add_property("i_seqs", make_getter(&w_t::i_seqs, rbv()))
        .add_property("weight", &w_t::weight)
      ;
    }
    static void wrap_restraint() {
      typedef adp_restraint_base<n_adp> w_t;
      using namespace boost::python;
      typedef return_value_policy<return_by_value> rbv;
      std::ostringstream sname("adp_restraint_base");
      if (n_adp > 1) sname << n_adp;
      std::string name = sname.str();

      class_<w_t>
            (name.c_str(), no_init)
        .def(init<af::tiny<bool, n_adp> const &, double>(
          (arg("use_u_aniso"),
           arg("weight"))))
        .def(init<
            adp_restraint_params<double> const &,
            adp_restraint_proxy<n_adp> const &>(
          (arg("params"),
           arg("proxy"))))
        .add_property("use_u_aniso", make_getter(&w_t::use_u_aniso, rbv()))
        .add_property("weight", make_getter(&w_t::weight, rbv()))
        .def("deltas", &w_t::deltas)
        .def("rms_deltas", &w_t::rms_deltas)
        .def("residual", &w_t::residual)
        .def("gradients", &w_t::gradients)
      ;
    }
    static void wrap() {
      wrap_proxy();
      wrap_restraint();
      functions_wrapper::wrap_aniso<
        isotropic_adp_proxy, isotropic_adp>("isotropic_adp");
      functions_wrapper::wrap<
        fixed_u_eq_adp_proxy, fixed_u_eq_adp>("fixed_u_eq_adp");
      functions_wrapper::wrap<
        adp_similarity_proxy, adp_similarity>("adp_similarity");
      functions_wrapper::wrap<
        adp_u_eq_similarity_proxy, adp_u_eq_similarity>("adp_u_eq_similarity");
      functions_wrapper::wrap<
        adp_volume_similarity_proxy, adp_volume_similarity>("adp_volume_similarity");
    }
  };

}

namespace boost_python {

  void wrap_adp_restraint_base() {
    adp_restraint_params_wrapper<double>::wrap();

    adp_restraint_base_wrapper<1>::wrap();
    adp_restraint_base_wrapper<2>::wrap();

    using namespace scitbx::boost_python::container_conversions;
    tuple_mapping_fixed_size<scitbx::af::tiny<bool, 1> >();
    tuple_mapping_fixed_size<scitbx::af::tiny<unsigned, 1> >();
    tuple_mapping_fixed_size<scitbx::af::tiny<double, 1> >();
    tuple_mapping_fixed_size<scitbx::af::tiny<scitbx::sym_mat3<double>, 1> >();
    tuple_mapping_fixed_size<scitbx::af::tiny<bool, 2> >();
    tuple_mapping_fixed_size<scitbx::af::tiny<scitbx::sym_mat3<double>, 2> >();
  }

}}}
