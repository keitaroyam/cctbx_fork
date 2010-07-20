#include <boost/python/class.hpp>
#include <boost/python/implicit.hpp>

#include <smtbx/refinement/constraints/geometrical_hydrogens.h>

namespace smtbx { namespace refinement { namespace constraints {
namespace boost_python {

  struct terminal_tetrahedral_xhn_sites_wrapper
  {
    typedef terminal_tetrahedral_xhn_sites wt;

    static void wrap() {
      using namespace boost::python;
      class_<wt, bases<crystallographic_parameter>,
             std::auto_ptr<wt>,
             boost::noncopyable>("terminal_tetrahedral_xhn_sites", no_init)
        .def(init<site_parameter *,
                  site_parameter *,
                  independent_scalar_parameter *,
                  independent_scalar_parameter *,
                  cart_t const &,
                  af::small<wt::scatterer_type *, 3> const &>
             ((arg("pivot"), arg("pivot_neighbour"),
               arg("azimuth"), arg("length"),
               arg("e_zero_azimuth"),
               arg("hydrogen"))))
        ;
      implicitly_convertible<std::auto_ptr<wt>, std::auto_ptr<parameter> >();
    }
  };

  struct angle_starting_tetrahedral_wrapper
  {
    typedef angle_starting_tetrahedral wt;

    static void wrap() {
      using namespace boost::python;
      class_<wt, bases<crystallographic_parameter>,
             std::auto_ptr<wt>,
             boost::noncopyable>("angle_starting_tetrahedral", no_init)
        .def(init<bool>(arg("variable")))
        ;
      implicitly_convertible<std::auto_ptr<wt>, std::auto_ptr<parameter> >();
    }
  };

  struct secondary_ch2_sites_wrapper
  {
    typedef secondary_ch2_sites wt;

    static void wrap() {
      using namespace boost::python;
      class_<wt,
             bases<crystallographic_parameter>,
             std::auto_ptr<wt>,
             boost::noncopyable>("secondary_ch2_sites", no_init)
      .def(init<site_parameter *,
                site_parameter *,
                site_parameter *,
                independent_scalar_parameter *,
                angle_starting_tetrahedral *,
                wt::scatterer_type *,
                wt::scatterer_type *>
           ((arg("pivot"), arg("pivot_neighbour_0"), arg("pivot_neighbour_1"),
             arg("length"), arg("h_c_h_angle"),
             arg("hydrogen_0"), arg("hydrogen_1"))))
        ;
      implicitly_convertible<std::auto_ptr<wt>, std::auto_ptr<parameter> >();
    }
  };

  struct tertiary_ch_site_wrapper
  {
    typedef tertiary_ch_site wt;

    static void wrap() {
      using namespace boost::python;
      class_<wt, bases<crystallographic_parameter>,
             std::auto_ptr<wt>,
             boost::noncopyable>("tertiary_ch_site", no_init)
        .def(init<site_parameter *,
                  site_parameter *,
                  site_parameter *,
                  site_parameter *,
                  independent_scalar_parameter *,
                  wt::scatterer_type *>
             ((arg("pivot"), arg("pivot_neighbour_0"), arg("pivot_neighbour_1"),
               arg("pivot_neighbour_2"), arg("length"),
               arg("hydrogen"))))

        ;
      implicitly_convertible<std::auto_ptr<wt>, std::auto_ptr<parameter> >();
    }
  };

  struct secondary_planar_xh_site_wrapper
  {
    typedef secondary_planar_xh_site wt;

    static void wrap() {
      using namespace boost::python;
      class_<wt, bases<crystallographic_parameter>,
             std::auto_ptr<wt>,
             boost::noncopyable>("secondary_planar_xh_site", no_init)
        .def(init<site_parameter *,
                  site_parameter *,
                  site_parameter *,
                  independent_scalar_parameter *,
                  wt::scatterer_type *>
             ((arg("pivot"), arg("pivot_neighbour_0"), arg("pivot_neighbour_1"),
               arg("length"),
               arg("hydrogen"))))
        ;
      implicitly_convertible<std::auto_ptr<wt>, std::auto_ptr<parameter> >();
    }
  };

  struct terminal_planar_xh2_sites_wrapper
  {
    typedef terminal_planar_xh2_sites wt;

    static void wrap() {
      using namespace boost::python;
      class_<wt, bases<crystallographic_parameter>,
             std::auto_ptr<wt>,
             boost::noncopyable>("terminal_planar_xh2_sites", no_init)
        .def(init<site_parameter *,
                  site_parameter *,
                  site_parameter *,
                  independent_scalar_parameter *,
                  wt::scatterer_type *, wt::scatterer_type *>
             ((arg("pivot"), arg("pivot_neighbour_0"),
               arg("pivot_neighbour_substituent"), arg("length"),
               arg("hydrogen_0"), arg("hydrogen_1"))))
        ;
      implicitly_convertible<std::auto_ptr<wt>, std::auto_ptr<parameter> >();
    }
  };


  struct terminal_linear_ch_site_wrapper
  {
    typedef terminal_linear_ch_site wt;

    static void wrap() {
      using namespace boost::python;
      class_<wt, bases<crystallographic_parameter>,
             std::auto_ptr<wt>,
             boost::noncopyable>("terminal_linear_ch_site", no_init)
        .def(init<site_parameter *,
                  site_parameter *,
                  independent_scalar_parameter *,
                  wt::scatterer_type *>
             ((arg("pivot"), arg("pivot_neighbour"), arg("length"),
               arg("hydrogen"))))
        ;
      implicitly_convertible<std::auto_ptr<wt>, std::auto_ptr<parameter> >();
    }
  };

  void wrap_geometrical_hydrogens() {
    terminal_tetrahedral_xhn_sites_wrapper::wrap();
    angle_starting_tetrahedral_wrapper::wrap();
    secondary_ch2_sites_wrapper::wrap();
    tertiary_ch_site_wrapper::wrap();
    secondary_planar_xh_site_wrapper::wrap();
    terminal_planar_xh2_sites_wrapper::wrap();
    terminal_linear_ch_site_wrapper::wrap();
  }


}}}}
