/* Copyright (c) 2001-2002 The Regents of the University of California
   through E.O. Lawrence Berkeley National Laboratory, subject to
   approval by the U.S. Department of Energy.
   See files COPYRIGHT.txt and LICENSE.txt for further details.

   Revision history:
     2002 Aug: Created (R.W. Grosse-Kunstleve)
 */

#ifndef SCITBX_ARRAY_FAMILY_BOOST_PYTHON_REF_C_GRID_FLEX_CONVERSIONS_H
#define SCITBX_ARRAY_FAMILY_BOOST_PYTHON_REF_C_GRID_FLEX_CONVERSIONS_H

#include <scitbx/array_family/accessors/flex_grid.h>
#include <scitbx/array_family/versa.h>
#include <scitbx/array_family/boost_python/utils.h>
#include <boost/python/object.hpp>
#include <boost/python/extract.hpp>

namespace scitbx { namespace af { namespace boost_python {

  template <typename RefCGridType>
  struct ref_c_grid_from_flex
  {
    typedef typename RefCGridType::value_type element_type;
    typedef typename RefCGridType::accessor_type c_grid_type;
    typedef versa<element_type, flex_grid<> > flex_type;

    ref_c_grid_from_flex()
    {
      boost::python::converter::registry::push_back(
        &convertible,
        &construct,
        boost::python::type_id<RefCGridType>());
    }

    static void* convertible(PyObject* obj_ptr)
    {
      using namespace boost::python;
      using boost::python::borrowed; // works around gcc 2.96 bug
      object obj(borrowed(obj_ptr));
      extract<flex_type&> flex_proxy(obj);
      if (!flex_proxy.check()) return 0;
      flex_type& a = flex_proxy();
      try { c_grid_type(a.accessor()); }
      catch (...) { return 0; }
      return obj_ptr;
    }

    static void construct(
      PyObject* obj_ptr,
      boost::python::converter::rvalue_from_python_stage1_data* data)
    {
      using namespace boost::python;
      using boost::python::borrowed;
      object obj(borrowed(obj_ptr));
      flex_type& a = extract<flex_type&>(obj)();
      if (!a.check_shared_size()) raise_shared_size_mismatch();
      c_grid_type c_grid(a.accessor());
      void* storage = (
        (converter::rvalue_from_python_storage<RefCGridType>*)
          data)->storage.bytes;
      new (storage) RefCGridType(a.begin(), c_grid);
      data->convertible = storage;
    }
  };

  template <typename ElementType,
            typename CGridType>
  struct ref_c_grid_flex_conversions
  {
    ref_c_grid_flex_conversions()
    {
      ref_c_grid_from_flex<const_ref<ElementType, CGridType> >();
      ref_c_grid_from_flex<ref<ElementType, CGridType> >();
    }
  };

}}} // namespace scitbx::af::boost_python

#endif // SCITBX_ARRAY_FAMILY_BOOST_PYTHON_REF_C_GRID_FLEX_CONVERSIONS_H
