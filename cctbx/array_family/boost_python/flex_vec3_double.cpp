/* Copyright (c) 2001-2002 The Regents of the University of California
   through E.O. Lawrence Berkeley National Laboratory, subject to
   approval by the U.S. Department of Energy.
   See files COPYRIGHT.txt and LICENSE.txt for further details.

   Revision history:
     2002 Sep: Created (R.W. Grosse-Kunstleve)
 */

#include <cctbx/boost_python/flex_fwd.h>

#include <scitbx/array_family/boost_python/flex_wrapper.h>
#include <scitbx/boost_python/pickle_single_buffered.h>
#include <cctbx/math/utils.h>
#include <cctbx/error.h>

namespace scitbx { namespace boost_python { namespace pickle_single_buffered {

  inline
  char* to_string(char* start, vec3<double> const& value)
  {
    return
      to_string(to_string(to_string(start, value[0]), value[1]), value[2]);
  }

  template <>
  struct from_string<vec3<double> >
  {
    from_string(const char* start)
    {
      end = start;
      for(std::size_t i=0;i<3;i++) {
        from_string<double> proxy(end);
        value[i] = proxy.value;
        end = proxy.end;
      }
    }

    vec3<double> value;
    const char* end;
  };

}}} // namespace scitbx::boost_python::pickle_single_buffered

#include <scitbx/array_family/boost_python/flex_pickle_single_buffered.h>

namespace scitbx { namespace af { namespace boost_python {

  namespace {

    flex_double
    as_double(flex<vec3<double> >::type const& a)
    {
      CCTBX_ASSERT(a.accessor().is_trivial_1d());
      flex_double result(a.size()*3, init_functor_null<double>());
      double* r = result.begin();
      const_ref<vec3<double> > a_ref = a.const_ref().as_1d();
      for(std::size_t i=0;i<a_ref.size();i++) {
        for(std::size_t j=0;j<3;j++) {
          *r++ = a_ref[i][j];
        }
      }
      return result;
    }

    flex<vec3<double> >::type
    from_double(flex<vec3<double> >::type& vec, flex_double const& dbl)
    {
      CCTBX_ASSERT(vec.size() == 0);
      CCTBX_ASSERT(dbl.size() % 3 == 0);
      std::size_t vec_size = dbl.size() / 3;
      shared<vec3<double> > v = vec.as_base_array();
      v.reserve(vec_size);
      const double* d = dbl.begin();
      for(std::size_t i=0;i<vec_size;i++) {
        v.push_back(vec3<double>(d));
        d += 3;
      }
      vec.resize(flex_grid<>(vec_size));
      return vec;
    }

    vec3<double>
    vec3_min(flex<vec3<double> >::type const& a)
    {
      CCTBX_ASSERT(!a.accessor().is_padded());
      vec3<double> result(0,0,0);
      af::const_ref<vec3<double>, af::flex_grid<> > a_ref = a.const_ref();
      if (a_ref.size() > 0) {
        result = a_ref[0];
        for(std::size_t i=0;i<a_ref.size();i++) {
          for(std::size_t j=0;j<3;j++) {
            cctbx::math::update_min(result[j], a_ref[i][j]);
          }
        }
      }
      return result;
    }

    vec3<double>
    vec3_max(flex<vec3<double> >::type const& a)
    {
      CCTBX_ASSERT(!a.accessor().is_padded());
      vec3<double> result(0,0,0);
      af::const_ref<vec3<double>, af::flex_grid<> > a_ref = a.const_ref();
      if (a_ref.size() > 0) {
        result = a_ref[0];
        for(std::size_t i=0;i<a_ref.size();i++) {
          for(std::size_t j=0;j<3;j++) {
            cctbx::math::update_max(result[j], a_ref[i][j]);
          }
        }
      }
      return result;
    }

    af::shared<vec3<double> >
    mul_a_mat3(
      af::const_ref<vec3<double> > const& a,
      mat3<double> const& m)
    {
      af::shared<vec3<double> > result;
      for(std::size_t i=0;i<a.size();i++) {
        result.push_back(a[i] * m);
      }
      return result;
    }

    af::shared<vec3<double> >
    rmul_a_mat3(
      af::const_ref<vec3<double> > const& a,
      mat3<double> const& m)
    {
      mat3<double> m_transposed = m.transpose();
      af::shared<vec3<double> > result;
      for(std::size_t i=0;i<a.size();i++) {
        result.push_back(a[i] * m_transposed);
      }
      return result;
    }

  } // namespace <anonymous>

  void wrap_flex_vec3_double()
  {
    flex_wrapper<vec3<double> >::plain("vec3_double")
      .def_pickle(flex_pickle_single_buffered<vec3<double>,
        3*pickle_size_per_element<double>::value>())
      .def("as_double", as_double)
      .def("from_double", from_double)
      .def("min", vec3_min)
      .def("max", vec3_max)
      .def("__add__", flex_wrapper<vec3<double> >::add_a_s)
      .def("__iadd__", flex_wrapper<vec3<double> >::iadd_a_s)
      .def("__mul__", mul_a_mat3)
      .def("__rmul__", rmul_a_mat3)
    ;
  }

}}} // namespace scitbx::af::boost_python
