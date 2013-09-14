#include <boost/python/class.hpp>
#include <boost/python/implicit.hpp>

#include <smtbx/refinement/constraints/affine.h>

namespace smtbx { namespace refinement { namespace constraints {
  namespace boost_python {

  struct affine_scalar_parameter_wrapper {
    typedef affine_scalar_parameter wt;

    static void wrap() {
      using namespace boost::python;
      class_<wt,
             bases<scalar_parameter>,
             std::auto_ptr<wt> >("affine_scalar_parameter", no_init)
        .def(init<scalar_parameter *, double, double>
             ((arg("dependee"), arg("a"), arg("b"))))
        .def(init<scalar_parameter *, double,
                  scalar_parameter *, double,
                  double>
             ((arg("dependee_0"), arg("a_0"),
               arg("dependee_1"), arg("a_1"),
               arg("b"))))
        .def(init<af::const_ref<scalar_parameter *> const &,
                  af::const_ref<double> const &, double>
             ((arg("dependees"), arg("a"), arg("b"))))
        .add_property("affine_form", &wt::affine_form)
        ;
      implicitly_convertible<std::auto_ptr<wt>, std::auto_ptr<parameter> >();
    }
  };

  void wrap_affine_scalar_parameter_wrapper() {
    affine_scalar_parameter_wrapper::wrap();
  }

}}}}
