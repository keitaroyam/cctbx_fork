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
#include <cctbx/array_family/shared.h>

namespace cctbx { namespace af {

  namespace {

    struct getstate_manager
    {
      getstate_manager(std::size_t a_size, std::size_t size_per_element)
      {
        str_capacity = a_size * size_per_element;
        str_obj = PyString_FromStringAndSize(
          0, static_cast<int>(str_capacity + 100));
        str_begin = PyString_AS_STRING(str_obj);
        str_end = str_begin;
        sprintf(str_end, "%lu", static_cast<unsigned long>(a_size));
        while (*str_end) str_end++;
        *str_end++ = ' ';
      };

      void advance()
      {
        while (*str_end) str_end++;
        *str_end++ = ' ';
        cctbx_assert(str_end - str_begin <= str_capacity);
      }

      PyObject* finalize()
      {
        str_capacity = str_end - str_begin;
        cctbx_assert(
          _PyString_Resize(&str_obj, static_cast<int>(str_capacity)) == 0);
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
        cctbx_assert(sscanf(str_ptr, "%lu", &a_capacity) == 1);
        while (*str_ptr != ' ') str_ptr++;
        str_ptr++;
      };

      void advance()
      {
        while (*str_ptr != ' ') str_ptr++;
        str_ptr++;
      }

      void finalize()
      {
        cctbx_assert(*str_ptr == 0);
      }

      char* str_ptr;
      std::size_t a_capacity;
    };

    struct bool_picklers
    {
      static
      boost::python::ref
      getstate(shared<bool> const& a)
      {
        getstate_manager mgr(a.size(), 1);
        for(std::size_t i=0;i<a.size();i++) {
          if (a[i]) *mgr.str_end++ = '1';
          else      *mgr.str_end++ = '0';
        }
        return boost::python::ref(mgr.finalize());
      }

      static
      void
      setstate(shared<bool>& a, boost::python::ref state)
      {
        setstate_manager mgr(a.size(), state.get());
        a.reserve(mgr.a_capacity);
        for(std::size_t i=0;i<mgr.a_capacity;i++) {
          if (*mgr.str_ptr++ == '1') a.push_back(true);
          else                       a.push_back(false);
        }
        mgr.finalize();
      }
    };

    template <typename ElementType>
    struct num_picklers
    {
      static
      boost::python::ref
      getstate(
        shared<ElementType> const& a,
        std::size_t size_per_element,
        const char* fmt)
      {
        getstate_manager mgr(a.size(), size_per_element);
        for(std::size_t i=0;i<a.size();i++) {
          sprintf(mgr.str_end, fmt, a[i]);
          mgr.advance();
        }
        return boost::python::ref(mgr.finalize());
      }

      static
      void
      setstate(
        shared<ElementType>& a,
        boost::python::ref state,
        const char* fmt)
      {
        setstate_manager mgr(a.size(), state.get());
        a.reserve(mgr.a_capacity);
        for(std::size_t i=0;i<mgr.a_capacity;i++) {
          ElementType val;
          cctbx_assert(sscanf(mgr.str_ptr, fmt, &val) == 1);
          mgr.advance();
          a.push_back(val);
        }
        mgr.finalize();
      }
    };

    template <typename ElementType>
    struct complex_picklers
    {
      static
      boost::python::ref
      getstate(
        shared<std::complex<ElementType> > const& a,
        std::size_t size_per_element,
        const char* fmt)
      {
        getstate_manager mgr(a.size(), 2 * size_per_element);
        for(std::size_t i=0;i<a.size();i++) {
          sprintf(mgr.str_end, fmt, a[i].real(), a[i].imag());
          mgr.advance();
        }
        return boost::python::ref(mgr.finalize());
      }

      static
      void
      setstate(
        shared<std::complex<ElementType> >& a,
        boost::python::ref state,
        const char* fmt)
      {
        setstate_manager mgr(a.size(), state.get());
        a.reserve(mgr.a_capacity);
        for(std::size_t i=0;i<mgr.a_capacity;i++) {
          ElementType val_real;
          ElementType val_imag;
          cctbx_assert(sscanf(mgr.str_ptr, fmt, &val_real, &val_imag) == 2);
          mgr.advance();
          a.push_back(std::complex<ElementType>(val_real, val_imag));
        }
        mgr.finalize();
      }
    };

    struct miller_index_picklers
    {
      static
      boost::python::ref
      getstate(shared<miller::Index> const& a)
      {
        getstate_manager mgr(a.size(), 3 * 6);
        for(std::size_t i=0;i<a.size();i++) {
          miller::Index const& h = a[i];
          sprintf(mgr.str_end, "%d,%d,%d", h[0], h[1], h[2]);
          mgr.advance();
        }
        return boost::python::ref(mgr.finalize());
      }

      static
      void
      setstate(shared<miller::Index>& a, boost::python::ref state)
      {
        setstate_manager mgr(a.size(), state.get());
        a.reserve(mgr.a_capacity);
        for(std::size_t i=0;i<mgr.a_capacity;i++) {
          int h[3];
          cctbx_assert(sscanf(mgr.str_ptr, "%d,%d,%d", h+0, h+1, h+2) == 3);
          mgr.advance();
          a.push_back(miller::Index(h));
        }
        mgr.finalize();
      }
    };

    template <typename FloatType>
    struct hendrickson_lattman_picklers
    {
      typedef hendrickson_lattman<FloatType> hl_type;

      static
      boost::python::ref
      getstate(
        shared<hl_type> const& a,
        std::size_t size_per_element,
        const char* fmt)
      {
        getstate_manager mgr(a.size(), 4 * size_per_element);
        for(std::size_t i=0;i<a.size();i++) {
          af::tiny<FloatType, 4> const& c = a[i].array();
          sprintf(mgr.str_end, fmt, c[0], c[1], c[2], c[3]);
          mgr.advance();
        }
        return boost::python::ref(mgr.finalize());
      }

      static
      void
      setstate(
        shared<hl_type>& a,
        boost::python::ref state,
        const char* fmt)
      {
        setstate_manager mgr(a.size(), state.get());
        a.reserve(mgr.a_capacity);
        for(std::size_t i=0;i<mgr.a_capacity;i++) {
          FloatType c[4];
          cctbx_assert(sscanf(mgr.str_ptr, fmt, c+0, c+1, c+2, c+3) == 4);
          mgr.advance();
          a.push_back(hl_type(c));
        }
        mgr.finalize();
      }
    };

  } // namespace <anonymous>

  boost::python::ref shared_bool_getstate(shared<bool> const& a)
  {
    return bool_picklers::getstate(a);
  }

  void shared_bool_setstate(shared<bool>& a, boost::python::ref state)
  {
    bool_picklers::setstate(a, state);
  }

  boost::python::ref shared_int_getstate(shared<int> const& a)
  {
    return num_picklers<int>::getstate(a, 12, "%d");
  }

  void shared_int_setstate(shared<int>& a, boost::python::ref state)
  {
    num_picklers<int>::setstate(a, state, "%d");
  }

  boost::python::ref shared_long_getstate(shared<long> const& a)
  {
    return num_picklers<long>::getstate(a, 21, "%ld");
  }

  void shared_long_setstate(shared<long>& a, boost::python::ref state)
  {
    num_picklers<long>::setstate(a, state, "%ld");
  }

  boost::python::ref shared_float_getstate(shared<float> const& a)
  {
    return num_picklers<float>::getstate(a, 12, "%.6g");
  }

  void shared_float_setstate(shared<float>& a, boost::python::ref state)
  {
    num_picklers<float>::setstate(a, state, "%g");
  }

  boost::python::ref shared_double_getstate(shared<double> const& a)
  {
    return num_picklers<double>::getstate(a, 18, "%.12g");
  }

  void shared_double_setstate(shared<double>& a, boost::python::ref state)
  {
    num_picklers<double>::setstate(a, state, "%lg");
  }

  boost::python::ref shared_complex_double_getstate(
    shared<std::complex<double> > const& a)
  {
    return complex_picklers<double>::getstate(a, 18, "%.12g,%.12g");
  }

  void shared_complex_double_setstate(
    shared<std::complex<double> >& a,
    boost::python::ref state)
  {
    complex_picklers<double>::setstate(a, state, "%lg,%lg");
  }

  boost::python::ref shared_miller_index_getstate(
    shared<miller::Index> const& a)
  {
    return miller_index_picklers::getstate(a);
  }

  void shared_miller_index_setstate(
    shared<miller::Index>& a,
    boost::python::ref state)
  {
    miller_index_picklers::setstate(a, state);
  }

  boost::python::ref shared_hendrickson_lattman_double_getstate(
    shared<hendrickson_lattman<double> > const& a)
  {
    return hendrickson_lattman_picklers<double>::getstate(
      a, 18, "%.12g,%.12g,%.12g,%.12g");
  }

  void shared_hendrickson_lattman_double_setstate(
    shared<hendrickson_lattman<double> >& a,
    boost::python::ref state)
  {
    hendrickson_lattman_picklers<double>::setstate(
      a, state, "%lg,%lg,%lg,%lg");
  }

}} // namespace cctbx::af
