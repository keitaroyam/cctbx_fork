#include <cctbx/boost_python/flex_fwd.h>
#include <boost/python.hpp>
#include <rstbx/apps/stills/simple_integration.h>

namespace rstbx { namespace integration { namespace ext {

  struct integration_wrappers
  {

    static void
    wrap()
    {
      using namespace boost::python;

      typedef return_value_policy<return_by_value> rbv;
      typedef default_call_policies dcp;

      class_<simple_integration>(
        "simple_integration", init<>())
         .enable_pickling()
        //Could not figure out how to expose member data from the C++ class into
        // a derived class in Python
        .def("set_pixel_size",&simple_integration::set_pixel_size)
        .def("set_detector_size",&simple_integration::set_detector_size)
        .def("set_frame",&simple_integration::set_frame)
        .def("set_nbr_cutoff_sq",&simple_integration::set_nbr_cutoff_sq)
        .def("get_bsmask",&simple_integration::get_bsmask)
        .def("safe_background",&simple_integration::safe_background,(
           arg_("predicted"),
           arg_("corrections"),
           arg_("OS_adapt"),
           arg_("sorted")
            ))
        .def("append_ISmask",&simple_integration::append_ISmask)
      ;
    }
  };

  void init_module()
  {
    using namespace boost::python;
    integration_wrappers::wrap();
  }

}}} // namespace rstbx::integration::ext

BOOST_PYTHON_MODULE(rstbx_integration_ext)
{
  rstbx::integration::ext::init_module();
}
