
#include <scitbx/graphics_utils/colors.h>

#include <boost/python/module.hpp>
#include <boost/python/def.hpp>
#include <boost/python/class.hpp>
#include <boost/python/args.hpp>

namespace scitbx { namespace graphics_utils {
namespace {

  void init_module ()
  {
    using namespace boost::python;
    def("make_rainbow_gradient", make_rainbow_gradient, (
      arg("nbins")));
    def("color_rainbow", color_rainbow, (
      arg("selection"),
      arg("color_all")=false));
    def("color_by_property", color_by_property, (
      arg("properties"),
      arg("selection"),
      arg("color_all")=true,
      arg("use_rb_color_gradient")=false));
    def("scale_selected_colors", scale_selected_colors, (
      arg("input_colors"),
      arg("selection"),
      arg("scale")=0.5));
  }
}
}}

BOOST_PYTHON_MODULE(scitbx_graphics_utils_ext)
{
  scitbx::graphics_utils::init_module();
}
