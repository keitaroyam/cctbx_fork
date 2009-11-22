#include <scitbx/array_family/boost_python/flex_fwd.h>

#include <boost/python/class.hpp>
#include <boost/python/args.hpp>
#include <boost/python/return_value_policy.hpp>
#include <boost/python/return_by_value.hpp>
#include <boost/python/copy_const_reference.hpp>
#include <boost/python/module.hpp>
#include <boost/python/def.hpp>
#include <boost/python/overloads.hpp>


#include <mmtbx/scaling/outlier.h>

namespace mmtbx { namespace scaling { namespace outlier {

namespace{


  struct likelihood_ratio_outlier_test_wrapper
  {
    typedef likelihood_ratio_outlier_test<double> w_t;

    static void
    wrap()
    {
      using namespace boost::python;

      class_<w_t>("likelihood_ratio_outlier_test", no_init)
        .def(init<
             scitbx::af::const_ref< double >  const&,
             scitbx::af::const_ref< double >  const&,
             scitbx::af::const_ref< double >  const&,
             scitbx::af::const_ref< double >  const&,
             scitbx::af::const_ref< bool >  const&,
             scitbx::af::const_ref< double >  const&,
             scitbx::af::const_ref< double >  const&>
             ((arg("f_obs"),
               arg("sigma_obs"),
               arg("f_calc"),
               arg("epsilon"),
               arg("centric"),
               arg("alpha"),
               arg("beta")
               )))
        .def("log_likelihood", &w_t::log_likelihood)
        .def("posterior_mode_log_likelihood", &w_t::posterior_mode_log_likelihood)
        .def("posterior_mode", &w_t::posterior_mode)
        .def("posterior_mode_snd_der", &w_t::posterior_mode_snd_der)
        .def("flag_potential_outliers", &w_t::flag_potential_outliers)
        .def("f_obs_fst_der", &w_t::f_obs_fst_der)
        .def("f_obs_snd_der", &w_t::f_obs_snd_der)
        .def("mean_fobs", &w_t::mean_fobs)
        .def("std_fobs", &w_t::std_fobs)
        .def("standardized_likelihood", &w_t::standardized_likelihood)
        ;
    }

  };


  struct sigmaa_estimator_wrapper
  {
    typedef sigmaa_estimator<double> w_t;

    static void
    wrap()
    {
      using namespace boost::python;

      class_<w_t>("sigmaa_estimator", no_init)
        .def(init<
             scitbx::af::const_ref< double >  const&,
             scitbx::af::const_ref< double >  const&,
             scitbx::af::const_ref< bool >    const&,
             scitbx::af::const_ref< double >  const&,
             double                           const&>
             ((arg("e_obs"),
               arg("e_calc"),
               arg("centric"),
               arg("d_star_cubed"),
               arg("width")
               )))
        .def("sum_weights", &w_t::sum_weights,
             ( arg("d_star_cubed")
               )
             )
        .def("target", &w_t::target,
             (( arg("d_star_cubed"),
                arg("sigmaa")
                ))
             )
        .def("dtarget", &w_t::dtarget,
             (( arg("d_star_cubed"),
                arg("sigmaa")
                ))
             )
        .def("target_and_gradient", &w_t::target_and_gradient,
             (( arg("d_star_cubed"),
                arg("sigmaa")
                ))
             )
        ;
    }

  };








}} // namespace <anonymous>

namespace boost_python{

  void wrap_outlier()
  {
    mmtbx::scaling::outlier::likelihood_ratio_outlier_test_wrapper::wrap();
    mmtbx::scaling::outlier::sigmaa_estimator_wrapper::wrap();
  }



}

}}
