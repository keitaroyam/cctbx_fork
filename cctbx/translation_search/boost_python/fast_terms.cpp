#include <cctbx/boost_python/flex_fwd.h>

#include <cctbx/translation_search/fast_terms.h>
#include <boost/python/class.hpp>
#include <boost/python/return_internal_reference.hpp>

namespace cctbx { namespace translation_search { namespace boost_python {

namespace {

  struct fast_terms_wrappers
  {
    typedef fast_terms<> w_t;

    static void
    wrap()
    {
      using namespace boost::python;
      typedef return_internal_reference<> rir;
      class_<w_t>("fast_terms", no_init)
        .def(init<af::int3 const&,
                  bool,
                  af::const_ref<miller::index<> > const&,
                  af::const_ref<std::complex<double> > >())
        .def("summation", &w_t::summation, rir())
        .def("fft", &w_t::fft, rir())
        .def("accu_real_copy", &w_t::accu_real_copy)
      ;
    }
  };

} // namespace <anoymous>

  void wrap_fast_terms()
  {
    fast_terms_wrappers::wrap();
  }

}}} // namespace cctbx::translation_search::boost_python
