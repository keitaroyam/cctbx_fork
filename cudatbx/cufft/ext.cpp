
#include <boost/python/module.hpp>
#include <boost/python/def.hpp>

#include <cuda.h>
#include <cuda_runtime.h>

namespace gputbx { namespace cufft {
  void clean_up () {
    cudaThreadExit();
  }

  void wrap_cufft_single_precision();
  void wrap_cufft_double_precision();
  void wrap_util () {
    using namespace boost::python;
    def("clean_up", clean_up);
  }

namespace {
  void init_module() {
    wrap_cufft_single_precision();
    wrap_cufft_double_precision();
    wrap_util();
  }
}
}}

BOOST_PYTHON_MODULE(gputbx_cufft_ext)
{
  gputbx::cufft::init_module();
}
