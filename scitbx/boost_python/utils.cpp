#if defined(_SGI_COMPILER_VERSION) && _SGI_COMPILER_VERSION == 741
# include <complex>
#endif
#include <scitbx/boost_python/utils.h>

namespace scitbx { namespace boost_python {

  boost::python::object
  cvs_revision(const std::string& revision)
  {
    using namespace boost::python;
    return object(borrowed(object(
      revision.substr(11, revision.size()-11-2)).ptr()));
  }

  boost::python::handle<>
  import_module(const char* module_name)
  {
    using namespace boost::python;
    return handle<>(PyImport_ImportModule(const_cast<char*>(module_name)));
  }

  void raise_index_error()
  {
    PyErr_SetString(PyExc_IndexError, "Index out of range.");
    boost::python::throw_error_already_set();
  }

  boost::python::object
  range(long start, long len, long step)
  {
    return boost::python::object(boost::python::handle<>(
      PyRange_New(start, len, step, 1)));
  }

  boost::python::object
  range(long len)
  {
    return range(0, len);
  }

}} // namespace scitbx::boost_python
