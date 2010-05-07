/* The main purpose of this module is to provide access to the
   Boost.Python metaclass.
   See also:
     boost/libs/python/doc/tutorial/doc/quickstart.txt, keyword injector
     boost.python.injector (boost/python.py)
 */

#include <boost/python/module.hpp>
#include <boost/python/docstring_options.hpp>
#include <boost/python/def.hpp>
#include <boost/python/class.hpp>
#include <boost/python/args.hpp>
#include <boost/python/list.hpp>

#include <boost_adaptbx/type_id_eq.h>
#include <boost_adaptbx/python_streambuf.h>
#include <boost_adaptbx/libc_backtrace.hpp>

#include <boost/cstdint.hpp>
#include <sstream>
#include <stdexcept>

// for number_of_processors()
#if !defined(_MSC_VER)
#include <unistd.h>
#endif
#if defined(__APPLE_CC__)
#include <sys/sysctl.h>
#endif

#if defined(__linux) \
 || defined(__alpha__) \
 || defined(__host_mips) \
 || defined(__APPLE_CC__) \
 || defined(_MSC_VER)
#include <signal.h>
#define BOOST_ADAPTBX_META_EXT_HAVE_SIGNAL_H
#endif

#if defined(__linux)
#include <gnu/libc-version.h>
#define BOOST_ADAPTBX_META_EXT_HAVE_GNU_LIBC_VERSION_H
#endif

#include <boost_adaptbx/floating_point_exceptions.h>

namespace {

  long
  number_of_processors()
  {
#if defined(CTL_HW) && defined(HW_NCPU)
    int mib[2];
    mib[0] = CTL_HW;
    mib[1] = HW_NCPU;
    int ncpu;
    size_t len = sizeof(ncpu);
    sysctl(mib, 2, &ncpu, &len, 0, 0);
    return static_cast<long>(ncpu);
#elif defined(_SC_NPROCESSORS_ONLN)
    return sysconf(_SC_NPROCESSORS_ONLN);
#elif defined(_SC_NPROCESSORS_CONF)
    return sysconf(_SC_NPROCESSORS_CONF);
#else
    return 0L;
#endif
  }

  bool
  libtbx_introspection_show_stack()
  {
    using namespace boost::python;
    static bool active = false;
    if (active) return false;
    active = true;
    handle<> hdl(allow_null(PyImport_ImportModule("libtbx.introspection")));
    if (!hdl.get()) {
      PyErr_Clear();
      active = false;
      return false;
    }
#if PY_MAJOR_VERSION > 2 || (PY_MAJOR_VERSION == 2 && PY_MINOR_VERSION > 4)
    const
#endif
    char* attr_name = "show_stack_true_stderr";
    // test first, just to be maximally fault tolerant
    if (!PyObject_HasAttrString(hdl.get(), attr_name)) {
      active = false;
      return false;
    }
    hdl = handle<>(allow_null(PyObject_GetAttrString(hdl.get(), attr_name)));
    if (!hdl.get()) { // should never be true
      PyErr_Clear();
      active = false;
      return false;
    }
    hdl = handle<>(allow_null(PyObject_CallFunction(hdl.get(), 0)));
    if (!hdl.get()) {
      PyErr_Clear();
      active = false;
      return false;
    }
    active = false;
    return true;
  }

  bool
  boost_adaptbx_libc_backtrace(int n_frames_skip=0)
  {
    std::cout << std::flush;
    return boost_adaptbx::libc_backtrace::show_if_possible(
      std::cerr, n_frames_skip);
  }

  void
  show_call_stacks_and_exit(const char* what)
  {
    bool have_py_trace = libtbx_introspection_show_stack();
    bool have_libc_trace = boost_adaptbx_libc_backtrace(2);
    const char* hint = "sorry, call stacks not available";
    if (have_py_trace && have_libc_trace) {
      hint = "Python and libc call stacks above";
    }
    else if (have_py_trace) {
      hint = "Python call stack above";
    }
    else if (have_libc_trace) {
      hint = "libc call stack above";
    }
    fprintf(stderr, "%s (%s)\n", what, hint);
    fprintf(stderr,
"                This crash may be due to a problem in any imported\n"
"                Python module, including modules which are not part\n"
"                of the cctbx project. To disable the traps leading\n"
"                to this message, define these environment variables\n"
"                (e.g. assign the value 1):\n"
"                    BOOST_ADAPTBX_FPE_DEFAULT\n"
"                    BOOST_ADAPTBX_SIGNALS_DEFAULT\n"
"                This will NOT solve the problem, just mask it, but\n"
"                may allow you to proceed in case it is not critical.\n");
    fflush(stderr);
    exit(1);
  }

} // namespace anonymous

extern "C" {

  void
  boost_adaptbx_segmentation_fault_backtrace(int)
  {
    show_call_stacks_and_exit("Segmentation fault");
  }

  void
  boost_adaptbx_bus_error_backtrace(int)
  {
    show_call_stacks_and_exit("Bus error");
  }

  void
  boost_adaptbx_floating_point_error_backtrace(int)
  {
    show_call_stacks_and_exit("Floating-point error");
  }

} // extern "C"

namespace {

  template <typename T>
  std::string
  to_str(T const & value)
  {
    std::ostringstream o;
    o << value;
    return o.str();
  }

  inline
  std::string
  to_str(bool value)
  {
    return std::string(value ? "true" : "false");
  }

  std::string
  platform_info()
  {
    std::string result;
    std::string nl = "\n";
    result += "__FILE__ = " __FILE__ "\n";
#if defined(__DATE__)
    result += "__DATE__ = " __DATE__ "\n";
#endif
#if defined(__TIME__)
    result += "__TIME__ = " __TIME__ "\n";
#endif
#if defined(__TIMESTAMP__)
    result += "__TIMESTAMP__ = " __TIMESTAMP__ "\n";
#endif
#if defined(__alpha__)
    result += "__alpha__\n";
#endif
#if defined(__host_mips)
    result += "__host_mips\n";
#endif
#if defined(__i386__)
    result += "__i386__\n";
#endif
#if defined(__x86_64__)
    result += "__x86_64__\n";
#endif
#if defined(__linux)
    result += "__linux\n";
#endif
#if defined(__osf__)
    result += "__osf__\n";
#endif
#if defined(__hpux)
    result += "__hpux\n";
#endif
#if defined(__sgi)
    result += "__sgi\n";
#endif
#if defined(_WIN32)
    result += "_WIN32\n";
#endif
#if defined(_WIN64)
    result += "_WIN64\n";
#endif
#if defined(__APPLE_CC__)
    result += "__APPLE_CC__ = " + to_str(__APPLE_CC__) + nl;
#endif
#if defined(_COMPILER_VERSION)
    result += "_COMPILER_VERSION = " + to_str(_COMPILER_VERSION) + nl;
#endif
#if defined(__DECCXX_VER)
    result += "__DECCXX_VER = " + to_str(__DECCXX_VER) + nl;
#endif
#if defined(__HP_aCC)
    result += "__HP_aCC = " + to_str(__HP_aCC) + nl;
#endif
#if defined(__EDG__)
    result += "__EDG__\n";
#endif
#if defined(__EDG_VERSION__)
    result += "__EDG_VERSION__ = " + to_str(__EDG_VERSION__) + nl;
#endif
#if defined(__EDG_ABI_COMPATIBILITY_VERSION)
    result += "__EDG_ABI_COMPATIBILITY_VERSION = "
            + to_str(__EDG_ABI_COMPATIBILITY_VERSION) + nl;
#endif
#if defined(__EDG_IMPLICIT_USING_STD)
    result += "__EDG_IMPLICIT_USING_STD\n";
#endif
#if defined(__EDG_RUNTIME_USES_NAMESPACES)
    result += "__EDG_RUNTIME_USES_NAMESPACES\n";
#endif
#if defined(__GNUC__)
    result += "__GNUC__ = " + to_str(__GNUC__) + nl;
#endif
#if defined(__GNUC_MINOR__)
    result += "__GNUC_MINOR__ = " + to_str(__GNUC_MINOR__) + nl;
#endif
#if defined(__GNUC_PATCHLEVEL__)
    result += "__GNUC_PATCHLEVEL__ = " + to_str(__GNUC_PATCHLEVEL__) + nl;
#endif
#if defined(BOOST_PYTHON_HAVE_CXXABI_CXA_DEMANGLE_IS_BROKEN)
    result += "boost::python::cxxabi_cxa_demangle_is_broken(): "
            + to_str(boost::python::cxxabi_cxa_demangle_is_broken()) + nl;
#endif
#if defined(__GXX_WEAK__)
    result += "__GXX_WEAK__ = " + to_str(__GXX_WEAK__) + nl;
#endif
#if defined(__IEEE_FLOAT)
    result += "__IEEE_FLOAT = " + to_str(__IEEE_FLOAT) + nl;
#endif
#if defined(__INTEL_COMPILER)
    result += "__INTEL_COMPILER = " + to_str(__INTEL_COMPILER) + nl;
#endif
#if defined(__INTEL_COMPILER_BUILD_DATE)
    result += "__INTEL_COMPILER_BUILD_DATE = "
            + to_str(__INTEL_COMPILER_BUILD_DATE) + nl;
#endif
#if defined(__ICC)
    result += "__ICC = " + to_str(__ICC) + nl;
#endif
#if defined(__LP64__)
    result += "__LP64__ = " + to_str(__LP64__) + nl;
#endif
#if defined(_M_IX86)
    result += "_M_IX86 = " + to_str(_M_IX86) + nl;
#endif
#if defined(_MSC_EXTENSIONS)
    result += "_MSC_EXTENSIONS = " + to_str(_MSC_EXTENSIONS) + nl;
#endif
#if defined(_MSC_VER)
    result += "_MSC_VER = " + to_str(_MSC_VER) + nl;
#endif
#if defined(__VERSION__)
    result += "__VERSION__ = " __VERSION__ "\n";
#endif
#if defined(FE_INEXACT)
    result += "FE_INEXACT = " + to_str(int(FE_INEXACT)) + nl;
#endif
#if defined(FE_DIVBYZERO)
    result += "FE_DIVBYZERO = " + to_str(int(FE_DIVBYZERO)) + nl;
#endif
#if defined(FE_UNDERFLOW)
    result += "FE_UNDERFLOW = " + to_str(int(FE_UNDERFLOW)) + nl;
#endif
#if defined(FE_OVERFLOW)
    result += "FE_OVERFLOW = " + to_str(int(FE_OVERFLOW)) + nl;
#endif
#if defined(FE_INVALID)
    result += "FE_INVALID = " + to_str(int(FE_INVALID)) + nl;
#endif
#if defined(FE_ALL_EXCEPT)
    result += "FE_ALL_EXCEPT = " + to_str(int(FE_ALL_EXCEPT)) + nl;
#endif
#if defined(__SSE2__)
    result += "__SSE2__ = " + to_str(__SSE2__) + nl;
#endif
#if defined(PY_VERSION)
    result += "PY_VERSION = " PY_VERSION "\n";
#endif
#if defined(PYTHON_API_VERSION)
    result += "PYTHON_API_VERSION = " + to_str(PYTHON_API_VERSION) + nl;
#endif
#undef P
#define P(T) result += "sizeof(" #T ") = " + to_str(sizeof(T)) + nl;
    P(bool)
    P(short)
    P(int)
    P(long)
    P(std::size_t)
    P(void*)
#if !defined(_MSC_VER) || _MSC_VER > 1200
    P(long long)
#endif
    P(float)
    P(double)
    P(long double)
    P(boost::int32_t)
    P(boost::uint32_t)
#if defined(HAVE_WCHAR_H)
    P(wchar_t)
#endif
#if defined(Py_USING_UNICODE)
    result += "Py_USING_UNICODE\n";
#endif
#if defined(PY_UNICODE_TYPE)
    P(PY_UNICODE_TYPE)
#endif
#undef P
#if defined(_OPENMP)
    result += "_OPENMP = " + to_str(_OPENMP) + nl;
#endif
#if defined(BOOST_ADAPTBX_META_EXT_HAVE_GNU_LIBC_VERSION_H)
    result += "gnu libc version: ";
    result += gnu_get_libc_version() + nl;
#endif
#if defined(BOOST_ADAPTBX_TYPE_ID_SIZE_T_EQ_UNSIGNED_SHORT)
    result += "BOOST_ADAPTBX_TYPE_ID_SIZE_T_EQ_UNSIGNED_SHORT\n";
#endif
#if defined(BOOST_ADAPTBX_TYPE_ID_SIZE_T_EQ_UNSIGNED)
    result += "BOOST_ADAPTBX_TYPE_ID_SIZE_T_EQ_UNSIGNED\n";
#endif
#if defined(BOOST_ADAPTBX_TYPE_ID_SIZE_T_EQ_UNSIGNED_LONG)
    result += "BOOST_ADAPTBX_TYPE_ID_SIZE_T_EQ_UNSIGNED_LONG\n";
#endif
#if defined(BOOST_ADAPTBX_TYPE_ID_SIZE_T_EQ_UNSIGNED_LONG_LONG)
    result += "BOOST_ADAPTBX_TYPE_ID_SIZE_T_EQ_UNSIGNED_LONG_LONG\n";
#endif
    return result;
  }

#if defined(Py_USING_UNICODE)
  boost::python::list
  str_or_unicode_as_char_list(
    boost::python::object const& O)
  {
    PyObject* obj = O.ptr();
    boost::python::ssize_t n;
    const char* c;
    if (PyString_Check(obj)) {
      n = PyString_GET_SIZE(obj);
      c = PyString_AS_STRING(obj);
    }
    else if (PyUnicode_Check(obj)) {
      n = PyUnicode_GET_DATA_SIZE(obj);
      c = PyUnicode_AS_DATA(obj);
    }
    else {
      throw std::invalid_argument("str or unicode object expected.");
    }
    boost::python::list result;
    for(boost::python::ssize_t i=0;i<n;i++) {
      result.append(std::string(c+i, 1u));
    }
    return result;
  }
#endif

  void
  enable_signals_backtrace_if_possible()
  {
#if defined(BOOST_ADAPTBX_META_EXT_HAVE_SIGNAL_H)
#if defined(SIGSEGV)
    signal(SIGSEGV, boost_adaptbx_segmentation_fault_backtrace);
#endif
#if defined(SIGBUS)
    signal(SIGBUS, boost_adaptbx_bus_error_backtrace);
#endif
#if defined(SIGFPE)
    signal(SIGFPE, boost_adaptbx_floating_point_error_backtrace);
#endif
#endif
  }

  char
  dereference_char_pointer(const char* pointer) { return *pointer; }

  double
  divide_doubles(double const& x, double const& y) { return x / y; }

  double
  multiply_doubles(double const& x, double const& y) { return x * y; }

  int
  add_ints(int i, int j) { return i + j; }

  long
  add_longs(long i, long j) { return i + j; }

  struct python_streambuf_wrapper
  {
    typedef boost_adaptbx::python::streambuf wt;

    static void
    wrap()
    {
      using namespace boost::python;
      class_<wt, boost::noncopyable>("streambuf", no_init)
        .def(init<object&, std::size_t>((
          arg("python_file_obj"),
          arg("buffer_size")=0)))
        .def_readwrite(
          "default_buffer_size", wt::default_buffer_size,
          "The default size of the buffer sitting "
          "between a Python file object and a C++ stream.")
      ;
    }
  };

  struct python_ostream_wrapper
  {
    typedef boost_adaptbx::python::ostream wt;

    static void
    wrap()
    {
      using namespace boost::python;
      class_<std::ostream, boost::noncopyable>("std_ostream", no_init);
      class_<wt, boost::noncopyable, bases<std::ostream> >("ostream", no_init)
        .def(init<object&, std::size_t>((
          arg("python_file_obj"),
          arg("buffer_size")=0)))
      ;
    }
  };

} // namespace anonymous

namespace boost_python_meta_ext { struct holder {}; }

BOOST_PYTHON_MODULE(boost_python_meta_ext)
{
  using namespace boost::python;
  def("number_of_processors", number_of_processors);
  def("boost_adaptbx_libc_backtrace", boost_adaptbx_libc_backtrace);
  def("libtbx_introspection_show_stack", libtbx_introspection_show_stack);
  def("platform_info", platform_info);
#if defined(Py_USING_UNICODE)
  def("str_or_unicode_as_char_list", str_or_unicode_as_char_list);
#endif
  def("enable_signals_backtrace_if_possible",
       enable_signals_backtrace_if_possible);
  def("trap_exceptions",
      boost_adaptbx::floating_point::trap_exceptions,
      (arg("division_by_zero"), arg("invalid"), arg("overflow")));
  def("is_division_by_zero_trapped",
      boost_adaptbx::floating_point::is_division_by_zero_trapped);
  def("is_invalid_trapped",
      boost_adaptbx::floating_point::is_invalid_trapped);
  def("is_overflow_trapped",
      boost_adaptbx::floating_point::is_overflow_trapped);
  def("dereference_char_pointer", dereference_char_pointer);
  def("divide_doubles", divide_doubles);
  def("multiply_doubles", multiply_doubles);
  def("add_ints", add_ints);
  def("add_longs", add_longs);
  class_<boost_python_meta_ext::holder>("holder").enable_pickling();
  python_streambuf_wrapper::wrap();
  python_ostream_wrapper::wrap();
  class_<docstring_options, boost::noncopyable>("docstring_options", no_init)
    .def(init<bool, bool>((
      arg("show_user_defined"),
      arg("show_signatures"))))
  ;
}
