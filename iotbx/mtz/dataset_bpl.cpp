#include <cctbx/boost_python/flex_fwd.h>

#include <boost/python/class.hpp>
#include <boost/python/args.hpp>
#include <boost/python/return_arg.hpp>
#include <iotbx/mtz/batch.h>
#include <iotbx/mtz/column.h>
#include <scitbx/array_family/boost_python/shared_wrapper.h>

namespace iotbx { namespace mtz {
namespace {

  struct dataset_wrappers
  {
    typedef dataset w_t;

    static void
    wrap()
    {
      using namespace boost::python;
      class_<w_t>("dataset", no_init)
        .def(init<crystal const&, int>((
          arg("mtz_crystal"), arg("i_dataset"))))
        .def("mtz_crystal", &w_t::mtz_crystal)
        .def("i_dataset", &w_t::i_dataset)
        .def("mtz_object", &w_t::mtz_object)
        .def("id", &w_t::id)
        .def("set_id", &w_t::set_id, (arg("id")), return_self<>())
        .def("name", &w_t::name)
        .def("set_name", &w_t::set_name, (arg("new_name")), return_self<>())
        .def("wavelength", &w_t::wavelength)
        .def("set_wavelength", &w_t::set_wavelength, (arg("new_wavelength")),
          return_self<>())
        .def("n_batches", &w_t::n_batches)
        .def("batches", &w_t::batches)
        .def("add_batch", &w_t::add_batch)
        .def("n_columns", &w_t::n_columns)
        .def("columns", &w_t::columns)
        .def("add_column", &w_t::add_column, (
          arg("label"), arg("type")))
      ;
      {
        scitbx::af::boost_python::shared_wrapper<w_t>::wrap(
          "shared_dataset");
      }
    }
  };

  void
  wrap_all()
  {
    dataset_wrappers::wrap();
  }

} // namespace <anonymous>

namespace boost_python {

  void
  wrap_dataset() { wrap_all(); }

}}} // namespace iotbx::mtz::boost_python
