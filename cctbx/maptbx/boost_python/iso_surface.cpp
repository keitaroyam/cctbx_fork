#include <scitbx/array_family/boost_python/flex_fwd.h>

#include <boost/python/class.hpp>

#include <cctbx/maptbx/iso_surface.h>

namespace cctbx { namespace maptbx { namespace boost_python {

  template <class CoordinatesType, class ValueType>
  struct iso_surface_wrapper
  {
    typedef iso_surface<CoordinatesType, ValueType> wt;

    static void wrap(const char *name) {
      using namespace boost::python;

      class_<wt>(name, no_init)
        .def(init<typename wt::map_const_ref_type,
                  ValueType, scitbx::vec3<CoordinatesType> const&>
                  ((arg("map"), arg("iso_level"), arg("grid_size"))))
        .add_property("vertices", &wt::vertices)
        .add_property("triangles", &wt::triangles)
        .add_property("normals", &wt::normals)
      ;
    }

  };

  void wrap_iso_surface() {
    iso_surface_wrapper<double, double>::wrap("iso_surface");

  }

}}}
