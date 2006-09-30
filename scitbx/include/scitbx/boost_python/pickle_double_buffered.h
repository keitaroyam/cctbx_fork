#ifndef SCITBX_BOOST_PYTHON_PICKLE_DOUBLE_BUFFERED_H
#define SCITBX_BOOST_PYTHON_PICKLE_DOUBLE_BUFFERED_H

#include <stdio.h>
#include <complex>
#include <scitbx/error.h>
#include <scitbx/type_holder.h>
#include <scitbx/boost_python/pickle_single_buffered.h>

namespace scitbx { namespace boost_python { namespace pickle_double_buffered {

  namespace base_256 = serialization::base_256;

  struct to_string
  {
    std::string buffer;

    to_string& operator<<(bool const& val)
    {
      if (val) buffer += "1";
      else     buffer += "0";
      return *this;
    }

    to_string& operator<<(int const& val)
    {
      char buf[64];
      buffer.append(buf, base_256::to_string(buf, val));
      return *this;
    }

    to_string& operator<<(unsigned int const& val)
    {
      char buf[64];
      buffer.append(buf, base_256::to_string(buf, val));
      return *this;
    }

    to_string& operator<<(long const& val)
    {
      char buf[64];
      buffer.append(buf, base_256::to_string(buf, val));
      return *this;
    }

    to_string& operator<<(unsigned long const& val)
    {
      char buf[64];
      buffer.append(buf, base_256::to_string(buf, val));
      return *this;
    }

    to_string& operator<<(float const& val)
    {
      char buf[64];
      buffer.append(buf, base_256::to_string(buf, val));
      return *this;
    }

    to_string& operator<<(double const& val)
    {
      char buf[64];
      buffer.append(buf, base_256::to_string(buf, val));
      return *this;
    }

    template <typename FloatType>
    to_string& operator<<(std::complex<FloatType> const& val)
    {
      return *this << val.real() << val.imag();
    }

    to_string& operator<<(std::string const& val)
    {
      *this << val.size();
      buffer += val;
      return *this;
    }

    to_string& operator<<(const char* val)
    {
      *this << std::string(val);
      return *this;
    }

  };

  struct from_string
  {
    const char* str_ptr;

    from_string(PyObject* str_obj)
    : str_ptr(PyString_AsString(str_obj))
    {
      SCITBX_ASSERT(str_ptr != 0);
    }

    void assert_end() const
    {
      SCITBX_ASSERT(*str_ptr == 0);
    }

    template <typename ValueType>
    ValueType get_value(type_holder<ValueType>)
    {
      pickle_single_buffered::from_string<ValueType> proxy(str_ptr);
      str_ptr = proxy.end;
      return proxy.value;
    }

    from_string& operator>>(std::string& val)
    {
      val = get_value(type_holder<std::string>());
      return *this;
    }

    from_string& operator>>(bool& val)
    {
      val = get_value(type_holder<bool>());
      return *this;
    }

    from_string& operator>>(int& val)
    {
      val = get_value(type_holder<int>());
      return *this;
    }

    from_string& operator>>(unsigned int& val)
    {
      val = get_value(type_holder<unsigned int>());
      return *this;
    }

    from_string& operator>>(long& val)
    {
      val = get_value(type_holder<long>());
      return *this;
    }

    from_string& operator>>(unsigned long& val)
    {
      val = get_value(type_holder<unsigned long>());
      return *this;
    }

    from_string& operator>>(float& val)
    {
      val = get_value(type_holder<float>());
      return *this;
    }

    from_string& operator>>(double& val)
    {
      val = get_value(type_holder<double>());
      return *this;
    }

    template <typename FloatType>
    from_string& operator>>(std::complex<FloatType>& val)
    {
      val = get_value(type_holder<std::complex<FloatType> >());
      return *this;
    }

  };

}}} // namespace scitbx::boost_python::pickle_double_buffered

#endif // SCITBX_BOOST_PYTHON_PICKLE_DOUBLE_BUFFERED_H
