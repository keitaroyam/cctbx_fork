#include <boost/python/module.hpp>

namespace smtbx { namespace refinement {

namespace boost_python {
  void wrap_parameter_map();
  void wrap_minimization();
  void wrap_weighting_schemes();

  namespace {
    void init_module() {
      wrap_parameter_map();
      wrap_minimization();
      wrap_weighting_schemes();
    }
  }

}}} // end namespace smtbx::refinement::boost_python

BOOST_PYTHON_MODULE(smtbx_refinement_ext)
{
  smtbx::refinement::boost_python::init_module();
}
