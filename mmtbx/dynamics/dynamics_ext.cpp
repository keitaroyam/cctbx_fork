#include <cctbx/boost_python/flex_fwd.h>

#include <boost/python/module.hpp>
#include <boost/python/class.hpp>
#include <boost/python/def.hpp>
#include <boost/python/args.hpp>
#include <mmtbx/dynamics/dynamics.h>

namespace mmtbx { namespace dynamics {
namespace {

  void init_module()
  {
    using namespace boost::python;

    def("kinetic_energy", kinetic_energy<double>, (
      arg("velocities"), arg("masses")));

    class_<center_of_mass_info>("center_of_mass_info",
                  init<vec3<double>,
                       af::shared<vec3<double> >,
                       af::shared<vec3<double> >,
                       af::shared<double> const&>())

      .def("ekcm", &center_of_mass_info::ekcm)
      .def("acm",  &center_of_mass_info::acm)
      .def("vcm",  &center_of_mass_info::vcm)
    ;

    def("vxyz_at_t_plus_dt_over_2",vxyz_at_t_plus_dt_over_2) ;
    def("stop_center_of_mass_motion",stop_center_of_mass_motion) ;
  }

} // namespace <anonymous>
}} // namespace mmtbx::dynamics

BOOST_PYTHON_MODULE(mmtbx_dynamics_ext)
{
  mmtbx::dynamics::init_module();
}
