/* Copyright (c) 2001-2002 The Regents of the University of California
   through E.O. Lawrence Berkeley National Laboratory, subject to
   approval by the U.S. Department of Energy.
   See files COPYRIGHT.txt and LICENSE.txt for further details.

   Revision history:
     2002 Sep: Created (rwgk)
 */

#include <scitbx/boost_python/utils.h>
#include <scitbx/boost_python/iterator_wrappers.h>
#include <cctbx/eltbx/icsd_radii.h>
#include <boost/python/module.hpp>
#include <boost/python/scope.hpp>
#include <boost/python/class.hpp>

namespace cctbx { namespace eltbx { namespace icsd_radii {
namespace boost_python {

namespace {

  struct table_wrappers
  {
    typedef table w_t;

    static void
    wrap()
    {
      using namespace boost::python;
      class_<w_t>("table", no_init)
        .def(init<std::string const&, optional<bool> >())
        .def("label", &w_t::label)
        .def("radius", &w_t::radius)
      ;
    }
  };

  void init_module()
  {
    using namespace boost::python;

    scope().attr("__version__") = scitbx::boost_python::cvs_revision(
      "$Revision$");

    table_wrappers::wrap();
    scitbx::boost_python::iterator_wrappers<
      table, table_iterator>::wrap("table_iterator");
  }

} // namespace <anonymous>
}}}} // namespace cctbx::eltbx::icsd_radii::boost_python

BOOST_PYTHON_MODULE(icsd_radii_ext)
{
  cctbx::eltbx::icsd_radii::boost_python::init_module();
}
