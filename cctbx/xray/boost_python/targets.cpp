/* Copyright (c) 2001-2002 The Regents of the University of California
   through E.O. Lawrence Berkeley National Laboratory, subject to
   approval by the U.S. Department of Energy.
   See files COPYRIGHT.txt and LICENSE.txt for further details.

   Revision history:
     2002 Oct: Created (rwgk)
 */

#include <cctbx/boost_python/flex_fwd.h>

#include <cctbx/xray/targets.h>
#include <boost/python/class.hpp>

namespace cctbx { namespace xray { namespace targets { namespace boost_python {

namespace {

  struct least_squares_residual_wrappers
  {
    typedef least_squares_residual<> w_t;

    static void
    wrap()
    {
      using namespace boost::python;
      class_<w_t>("targets_least_squares_residual", no_init)
        .def(init<af::const_ref<double> const&,
                  af::const_ref<double> const&,
                  af::const_ref<std::complex<double> > const&,
                  optional<bool, double> >())
        .def(init<af::const_ref<double> const&,
                  af::const_ref<std::complex<double> > const&,
                  optional<bool, double> >())
        .def("scale_factor", &w_t::scale_factor)
        .def("target", &w_t::target)
        .def("derivatives", &w_t::derivatives)
      ;
    }
  };

  struct intensity_correlation_wrappers
  {
    typedef intensity_correlation<> w_t;

    static void
    wrap()
    {
      using namespace boost::python;
      class_<w_t>("targets_intensity_correlation", no_init)
        .def(init<af::const_ref<double> const&,
                  af::const_ref<int> const&,
                  af::const_ref<std::complex<double> > const&,
                  optional<bool> >())
        .def(init<af::const_ref<double> const&,
                  af::const_ref<std::complex<double> > const&,
                  optional<bool> >())
        .def("correlation", &w_t::correlation)
        .def("target", &w_t::target)
        .def("derivatives", &w_t::derivatives)
      ;
    }
  };

  struct maximum_likelihood_criterion_wrappers
  {
    typedef maximum_likelihood_criterion<> w_t;

    static void
    wrap()
    {
      using namespace boost::python;
      class_<w_t>("targets_maximum_likelihood_criterion",
             init<af::const_ref<double> const&,
                  af::const_ref<std::complex<double> > const&,
                  af::const_ref<double> const&,
                  af::const_ref<double> const&,
                  double const&,
                  af::const_ref<int> const&,
                  af::const_ref<int> const&,
                  bool const& >())
        .def("target", &w_t::target)
        .def("derivatives", &w_t::derivatives)
      ;
    }
  };

  struct maximum_likelihood_criterion_hl_wrappers
  {
    typedef maximum_likelihood_criterion_hl<> w_t;

    static void
    wrap()
    {
      using namespace boost::python;
      class_<w_t>("targets_maximum_likelihood_criterion_hl",
             init<af::const_ref<double> const&,
                  af::const_ref<std::complex<double> > const&,
                  af::const_ref<double> const&,
                  af::const_ref<double> const&,
                  af::const_ref<int> const&,
                  af::const_ref<int> const&,
                  bool const&,
                  af::const_ref<cctbx::hendrickson_lattman<double> > const&,
                  double const& >())
        .def("target", &w_t::target)
        .def("derivatives", &w_t::derivatives)
      ;
    }
  };

} // namespace <anoymous>

}} // namespace targets::boost_python

namespace boost_python {

  void wrap_targets()
  {
    targets::boost_python::least_squares_residual_wrappers::wrap();
    targets::boost_python::intensity_correlation_wrappers::wrap();
    targets::boost_python::maximum_likelihood_criterion_wrappers::wrap();
    targets::boost_python::maximum_likelihood_criterion_hl_wrappers::wrap();
  }

}}} // namespace cctbx::xray::boost_python
