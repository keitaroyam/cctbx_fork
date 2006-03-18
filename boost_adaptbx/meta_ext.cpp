/* The main purpose of this module is to provide access to the
   Boost.Python metaclass via meta_ext.empty.__class__.
   See also:
     boost/libs/python/doc/tutorial/doc/quickstart.txt, keyword injector
     boost.python.injector (boost/python.py)
 */

#include <boost/python/module.hpp>
#include <boost/python/def.hpp>
#include <boost/python/class.hpp>
#include <boost/cstdint.hpp>

namespace {

  inline
  std::string
  to_str(bool value)
  {
    return std::string(value ? "true" : "false");
  }

  inline
  std::string
  to_str(int value)
  {
    char buf[256];
    sprintf(buf, "%d", value);
    return std::string(buf);
  }

  inline
  std::string
  to_str(unsigned int value)
  {
    char buf[256];
    sprintf(buf, "%u", value);
    return std::string(buf);
  }

  inline
  std::string
  to_str(long value)
  {
    char buf[256];
    sprintf(buf, "%ld", value);
    return std::string(buf);
  }

  inline
  std::string
  to_str(unsigned long value)
  {
    char buf[256];
    sprintf(buf, "%lu", value);
    return std::string(buf);
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
#if defined(PY_VERSION)
    result += "PY_VERSION = " PY_VERSION "\n";
#endif
#if defined(PYTHON_API_VERSION)
    result += "PYTHON_API_VERSION = " + to_str(PYTHON_API_VERSION) + nl;
#endif
#undef P
#define P(T) result += "sizeof(" #T ") = " + to_str(sizeof(T)) + nl;
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
#if defined(PY_UNICODE_TYPE)
    P(PY_UNICODE_TYPE)
#endif
#undef P
    return result;
  }

} // namespace anonymous

namespace { struct empty {}; }

BOOST_PYTHON_MODULE(boost_python_meta_ext)
{
  using namespace boost::python;
  def("platform_info", platform_info);
  class_<empty>("empty", no_init);
}
