// $Id$
/* Copyright (c) 2001 The Regents of the University of California through
   E.O. Lawrence Berkeley National Laboratory, subject to approval by the
   U.S. Department of Energy. See files COPYRIGHT.txt and
   cctbx/LICENSE.txt for further details.

   Revision history:
     2002 Aug: Created (R.W. Grosse-Kunstleve)
 */

#include <boost/python/class_builder.hpp>
#include <cctbx/error.h>
#include <cctbx/miller.h>
#include <cctbx/hendrickson_lattman.h>
#include <cctbx/sftbx/xray_scatterer.h>
#include <cctbx/array_family/shared.h>
#include <cctbx/basic/meta.h>

namespace cctbx { namespace af {

  namespace picklers {

    inline char* o_advance(char *ptr)
    {
      while (*ptr != ',') ptr++;
      return ptr + 1;
    }

    template <typename ValueType>
    struct from_string {};

    char* to_string(char* start, bool const& value)
    {
      if (value == true) *start = '1';
      else               *start = '0';
      return start + 1;
    }

    template <>
    struct from_string<bool>
    {
      from_string(const char* start) : end(start)
      {
        if (*end++ == '1') value = true;
        else               value = false;
      }

      bool value;
      const char* end;
    };

    char* to_string(char* start, int const& value)
    {
      cctbx_assert(sprintf(start, "%d,", value) > 0);
      return o_advance(start);
    }

    template <>
    struct from_string<int>
    {
      from_string(const char* start)
      {
        value = static_cast<int>(strtol(start, &end, 10));
        cctbx_assert(*end++ == ',');
      }

      int value;
      char* end;
    };

    char* to_string(char* start, unsigned int const& value)
    {
      cctbx_assert(sprintf(start, "%u,", value) > 0);
      return o_advance(start);
    }

    template <>
    struct from_string<unsigned int>
    {
      from_string(const char* start)
      {
        value = static_cast<unsigned int>(strtoul(start, &end, 10));
        cctbx_assert(*end++ == ',');
      }

      unsigned int value;
      char* end;
    };

    char* to_string(char* start, long const& value)
    {
      cctbx_assert(sprintf(start, "%ld,", value) > 0);
      return o_advance(start);
    }

    template <>
    struct from_string<long>
    {
      from_string(const char* start)
      {
        value = strtol(start, &end, 10);
        cctbx_assert(*end++ == ',');
      }

      long value;
      char* end;
    };

    char* to_string(char* start, unsigned long const& value)
    {
      cctbx_assert(sprintf(start, "%lu,", value) > 0);
      return o_advance(start);
    }

    template <>
    struct from_string<unsigned long>
    {
      from_string(const char* start)
      {
        value = strtoul(start, &end, 10);
        cctbx_assert(*end++ == ',');
      }

      unsigned long value;
      char* end;
    };

    char* to_string(char* start, float const& value)
    {
      cctbx_assert(sprintf(start, "%.6g,", value) > 0);
      return o_advance(start);
    }

    template <>
    struct from_string<float>
    {
      from_string(const char* start)
      {
#if (defined(BOOST_MSVC) && BOOST_MSVC <= 1300) // VC++ 7.0
        value = strtod(start, &end);
#else
        value = strtof(start, &end);
#endif
        cctbx_assert(*end++ == ',');
      }

      float value;
      char* end;
    };

    char* to_string(char* start, double const& value)
    {
      cctbx_assert(sprintf(start, "%.12g,", value) > 0);
      return o_advance(start);
    }

    template <>
    struct from_string<double>
    {
      from_string(const char* start)
      {
        value = strtod(start, &end);
        cctbx_assert(*end++ == ',');
      }

      double value;
      char* end;
    };

    template <typename FloatType>
    char* to_string(char* start, std::complex<FloatType> const& value)
    {
      return to_string(to_string(start, value.real()), value.imag());
    }

    template <>
    struct from_string<std::complex<double> >
    {
      from_string(const char* start)
      {
        from_string<double> proxy_r(start);
        from_string<double> proxy_i(proxy_r.end);
        value = std::complex<double>(proxy_r.value, proxy_i.value);
        end = proxy_i.end;
      }

      std::complex<double> value;
      char* end;
    };

    char* to_string(char* start, miller::Index const& value)
    {
      return
        to_string(to_string(to_string(start, value[0]), value[1]), value[2]);
    }

    template <>
    struct from_string<miller::Index>
    {
      from_string(const char* start)
      {
        end = start;
        for(std::size_t i=0;i<3;i++) {
          from_string<int> proxy(end);
          value[i] = proxy.value;
          end = proxy.end;
        }
      }

      af::int3 value;
      const char* end;
    };

    char* to_string(char* start, hendrickson_lattman<double> const& value)
    {
      return
        to_string(to_string(to_string(to_string(start,
          value[0]), value[1]), value[2]), value[3]);
    }

    template <>
    struct from_string<hendrickson_lattman<double> >
    {
      from_string(const char* start)
      {
        end = start;
        for(std::size_t i=0;i<4;i++) {
          from_string<double> proxy(end);
          value[i] = proxy.value;
          end = proxy.end;
        }
      }

      hendrickson_lattman<double> value;
      const char* end;
    };

    char* to_string(char* start, const char* value)
    {
      while (*value) *start++ = *value++;
      *start++ = '\0';
      *start++ = ',';
      return start;
    }

    char* to_string(char* start, std::string const& value)
    {
      return to_string(start, value.c_str());
    }

    template <>
    struct from_string<std::string>
    {
      from_string(const char* start)
      {
        value = std::string(start);
        while (*end) end++;
        cctbx_assert(*end++ == ',');
      }

      std::string value;
      char* end;
    };

    struct getstate_manager
    {
      getstate_manager(std::size_t a_size, std::size_t size_per_element)
      {
        str_capacity = a_size * size_per_element + 50;// extra space for a_size
        str_obj = PyString_FromStringAndSize(
          0, static_cast<int>(str_capacity + 100)); // extra space for safety
        str_begin = PyString_AS_STRING(str_obj);
        str_end = to_string(str_begin, a_size);
      };

      void advance(char* str_ptr)
      {
        str_end = str_ptr;
        cctbx_assert(str_end - str_begin <= str_capacity);
      }

      PyObject* finalize()
      {
        cctbx_assert(_PyString_Resize(&str_obj,
          static_cast<int>(str_end - str_begin)) == 0);
        return str_obj;
      }

      std::size_t str_capacity;
      PyObject* str_obj;
      char* str_begin;
      char* str_end;
    };

    struct setstate_manager
    {
      setstate_manager(std::size_t a_size, PyObject* state)
      {
        cctbx_assert(a_size == 0);
        str_ptr = PyString_AsString(state);
        cctbx_assert(str_ptr != 0);
        a_capacity = get_value(type_holder<std::size_t>());
      };

      template <typename ValueType>
      ValueType get_value(type_holder<ValueType>)
      {
        from_string<ValueType> proxy(str_ptr);
        str_ptr = proxy.end;
        return proxy.value;
      }

      void assert_end()
      {
        cctbx_assert(*str_ptr == 0);
      }

      const char* str_ptr;
      std::size_t a_capacity;
    };

    template <typename ElementType>
    struct array_fast
    {
      static
      boost::python::ref
      getstate(shared<ElementType> const& a, std::size_t size_per_element)
      {
        getstate_manager mgr(a.size(), size_per_element);
        for(std::size_t i=0;i<a.size();i++) {
          mgr.advance(to_string(mgr.str_end, a[i]));
        }
        return boost::python::ref(mgr.finalize());
      }

      static
      void
      setstate(shared<ElementType>& a, boost::python::ref state)
      {
        setstate_manager mgr(a.size(), state.get());
        a.reserve(mgr.a_capacity);
        for(std::size_t i=0;i<mgr.a_capacity;i++) {
          a.push_back(mgr.get_value(type_holder<ElementType>()));
        }
        mgr.assert_end();
      }
    };

    struct make_pickle_string
    {
      std::string buffer;

      make_pickle_string& operator<<(std::string const& val)
      {
        buffer += val + '\0' + ',';
        return *this;
      }

      make_pickle_string& operator<<(const char* val)
      {
        return *this << std::string(val);
      }

      make_pickle_string& operator<<(bool const& val)
      {
        if (val) buffer += "1";
        else     buffer += "0";
        return *this;
      }

      make_pickle_string& operator<<(int const& val)
      {
        char buf[64];
        sprintf(buf, "%d,", val);
        buffer += buf;
        return *this;
      }

      make_pickle_string& operator<<(unsigned int const& val)
      {
        char buf[64];
        sprintf(buf, "%u,", val);
        buffer += buf;
        return *this;
      }

      make_pickle_string& operator<<(long const& val)
      {
        char buf[64];
        sprintf(buf, "%ld,", val);
        buffer += buf;
        return *this;
      }

      make_pickle_string& operator<<(unsigned long const& val)
      {
        char buf[64];
        sprintf(buf, "%lu,", val);
        buffer += buf;
        return *this;
      }

      make_pickle_string& operator<<(float const& val)
      {
        char buf[64];
        sprintf(buf, "%.6g,", val);
        buffer += buf;
        return *this;
      }

      make_pickle_string& operator<<(double const& val)
      {
        char buf[64];
        sprintf(buf, "%.12g,", val);
        buffer += buf;
        return *this;
      }

      template <typename FloatType>
      make_pickle_string& operator<<(std::complex<FloatType> const& val)
      {
        return *this << val.real() << val.imag();
      }

      template <typename ElementType, typename AccessorType>
      make_pickle_string& operator<<(
        af::const_ref<ElementType, AccessorType> const& vals)
      {
        for(std::size_t i=0;i<vals.size();i++) {
          *this << vals[i];
        }
        return *this;
      }
    };

    struct read_from_pickle_string
    {
      const char* str_ptr;

      read_from_pickle_string(PyObject* str_obj)
      : str_ptr(PyString_AsString(str_obj))
      {
        cctbx_assert(str_ptr != 0);
      }

      void assert_end() const
      {
        cctbx_assert(*str_ptr == 0);
      }

      read_from_pickle_string& advance()
      {
        while (*str_ptr != ',') str_ptr++;
        str_ptr++;
        return *this;
      }

      template <typename ValueType>
      ValueType get_value(type_holder<ValueType>)
      {
        from_string<ValueType> proxy(str_ptr);
        str_ptr = proxy.end;
        return proxy.value;
      }

      read_from_pickle_string& operator>>(std::string& val)
      {
        val = std::string(str_ptr);
        while (*str_ptr) str_ptr++;
        return advance();
      }

      read_from_pickle_string& operator>>(bool& val)
      {
        val = get_value(type_holder<bool>());
        return *this;
      }

      read_from_pickle_string& operator>>(int& val)
      {
        val = get_value(type_holder<int>());
        return *this;
      }

      read_from_pickle_string& operator>>(unsigned int& val)
      {
        val = get_value(type_holder<unsigned int>());
        return *this;
      }

      read_from_pickle_string& operator>>(long& val)
      {
        val = get_value(type_holder<long>());
        return *this;
      }

      read_from_pickle_string& operator>>(unsigned long& val)
      {
        val = get_value(type_holder<unsigned long>());
        return *this;
      }

      read_from_pickle_string& operator>>(float& val)
      {
        val = get_value(type_holder<float>());
        return *this;
      }

      read_from_pickle_string& operator>>(double& val)
      {
        val = get_value(type_holder<double>());
        return *this;
      }

      template <typename FloatType>
      read_from_pickle_string& operator>>(std::complex<FloatType>& val)
      {
        val = get_value(type_holder<std::complex<FloatType> >());
        return *this;
      }

      template <typename ElementType, typename AccessorType>
      read_from_pickle_string& operator>>(
        af::ref<ElementType, AccessorType> vals)
      {
        for(std::size_t i=0;i<vals.size();i++) {
          *this >> vals[i];
        }
        return *this;
      }
    };

    template <typename FloatType, typename CAASF_Type>
    struct xray_scatterer_
    {
      typedef sftbx::XrayScatterer<FloatType, CAASF_Type> xs_type;

      static
      boost::python::ref
      getstate(shared<xs_type> const& a)
      {
        make_pickle_string result;
        result << a.size();
        for(std::size_t i=0;i<a.size();i++) {
          xs_type const& site = a[i];
          result << site.Label()
                 << site.CAASF().Label()
                 << site.fpfdp()
                 << site.Coordinates().const_ref()
                 << site.Occ()
                 << site.isAnisotropic();
          if (site.isAnisotropic()) result << site.Uaniso().const_ref();
          else                      result << site.Uiso();
        }
        return boost::python::make_ref(result.buffer);
      }

      static
      void
      setstate(shared<xs_type>& a, boost::python::ref state)
      {
        cctbx_assert(a.size() == 0);
        read_from_pickle_string inp(state.get());
        std::size_t a_capacity;
        inp >> a_capacity;
        a.reserve(a_capacity);
        std::string lbl, sf_lbl;
        std::complex<FloatType> fpfdp;
        fractional<FloatType> coor;
        FloatType occ;
        bool is_aniso;
        for(std::size_t i=0;i<a_capacity;i++) {
          inp >> lbl >> sf_lbl >> fpfdp >> coor.ref() >> occ >> is_aniso;
          if (is_aniso) {
            af::tiny<FloatType, 6> u_aniso;
            inp >> u_aniso.ref();
            a.push_back(
              xs_type(lbl, CAASF_Type(sf_lbl), fpfdp, coor, occ, u_aniso));
          }
          else {
            FloatType u_iso;
            inp >> u_iso;
            a.push_back(
              xs_type(lbl, CAASF_Type(sf_lbl), fpfdp, coor, occ, u_iso));
          }
        }
        inp.assert_end();
      }
    };

  } // picklers

  boost::python::ref shared_bool_getstate(shared<bool> const& a)
  {
    return picklers::array_fast<bool>::getstate(a, 1);
  }

  void shared_bool_setstate(shared<bool>& a, boost::python::ref state)
  {
    picklers::array_fast<bool>::setstate(a, state);
  }

  boost::python::ref shared_int_getstate(shared<int> const& a)
  {
    return picklers::array_fast<int>::getstate(a, 12);
  }

  void shared_int_setstate(shared<int>& a, boost::python::ref state)
  {
    picklers::array_fast<int>::setstate(a, state);
  }

  boost::python::ref shared_long_getstate(shared<long> const& a)
  {
    return picklers::array_fast<long>::getstate(a, 21);
  }

  void shared_long_setstate(shared<long>& a, boost::python::ref state)
  {
    picklers::array_fast<long>::setstate(a, state);
  }

  boost::python::ref shared_float_getstate(shared<float> const& a)
  {
    return picklers::array_fast<float>::getstate(a, 13);
  }

  void shared_float_setstate(shared<float>& a, boost::python::ref state)
  {
    picklers::array_fast<float>::setstate(a, state);
  }

  boost::python::ref shared_double_getstate(shared<double> const& a)
  {
    return picklers::array_fast<double>::getstate(a, 19);
  }

  void shared_double_setstate(shared<double>& a, boost::python::ref state)
  {
    picklers::array_fast<double>::setstate(a, state);
  }

  boost::python::ref shared_complex_double_getstate(
    shared<std::complex<double> > const& a)
  {
    return picklers::array_fast<std::complex<double> >::getstate(a, 2*19);
  }

  void shared_complex_double_setstate(
    shared<std::complex<double> >& a,
    boost::python::ref state)
  {
    picklers::array_fast<std::complex<double> >::setstate(a, state);
  }

  boost::python::ref shared_miller_index_getstate(
    shared<miller::Index> const& a)
  {
    return picklers::array_fast<miller::Index>::getstate(a, 3*12);
  }

  void shared_miller_index_setstate(
    shared<miller::Index>& a,
    boost::python::ref state)
  {
    picklers::array_fast<miller::Index>::setstate(a, state);
  }

  boost::python::ref shared_hendrickson_lattman_double_getstate(
    shared<hendrickson_lattman<double> > const& a)
  {
    return
      picklers::array_fast<hendrickson_lattman<double> >::getstate(a, 4*19);
  }

  void shared_hendrickson_lattman_double_setstate(
    shared<hendrickson_lattman<double> >& a,
    boost::python::ref state)
  {
    picklers::array_fast<hendrickson_lattman<double> >::setstate(a, state);
  }

  boost::python::ref shared_xray_scatterer_double_wk1995_getstate(
    shared<sftbx::XrayScatterer<double, eltbx::CAASF_WK1995> > const& a)
  {
    return picklers::xray_scatterer_<double, eltbx::CAASF_WK1995>::getstate(a);
  }

  void shared_xray_scatterer_double_wk1995_setstate(
    shared<sftbx::XrayScatterer<double, eltbx::CAASF_WK1995> >& a,
    boost::python::ref state)
  {
    picklers::xray_scatterer_<double, eltbx::CAASF_WK1995>::setstate(a, state);
  }

}} // namespace cctbx::af
