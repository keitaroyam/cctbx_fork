#include <cctbx/boost_python/flex_fwd.h>

#include <boost/python/module.hpp>
#include <boost/python/class.hpp>
#include <boost/python/def.hpp>
#include <boost/python/dict.hpp>
#include <boost/python/list.hpp>
#include <scitbx/array_family/flex_types.h>
#include <scitbx/array_family/shared.h>
#include <scitbx/constants.h>
#include <scitbx/math/mean_and_variance.h>

#include <vector>
#include <map>

using namespace boost::python;

namespace xfel {

struct mark2_iteration {
  typedef scitbx::af::shared<double> farray;
  typedef scitbx::af::shared<int> iarray;
  farray values;
  farray tox;
  farray toy;
  farray spotcx;
  farray spotcy;
  farray spotfx;
  farray spotfy;
  iarray master_tiles;
  double functional;
  farray gradients_,curvatures_;

  farray model_calcx, model_calcy;
  double calc_minus_To_x, calc_minus_To_y;
  double rotated_o_x, rotated_o_y;
  double partial_partial_theta_x, partial_partial_theta_y;
  double partial_sq_theta_x, partial_sq_theta_y;

  farray sine,cosine;

  mark2_iteration(){}
  mark2_iteration(farray values, farray tox, farray toy, farray spotcx, farray spotcy,
                  farray spotfx, farray spotfy,
                  iarray master_tiles):
    values(values),tox(tox),toy(toy),spotcx(spotcx),spotcy(spotcy),
    master_tiles(master_tiles),
    model_calcx(spotcx.size(),scitbx::af::init_functor_null<double>()),
    model_calcy(spotcx.size(),scitbx::af::init_functor_null<double>()),
    functional(0.),
    gradients_(3*64),
    curvatures_(3*64)
  {
    SCITBX_ASSERT(tox.size()==64);
    SCITBX_ASSERT(toy.size()==64);
    SCITBX_ASSERT(values.size()==3*64);
    for (int tidx=0; tidx < 64; ++tidx){
      cosine.push_back(std::cos(values[128+tidx]*scitbx::constants::pi_180));
      sine.push_back(std::sin(values[128+tidx]*scitbx::constants::pi_180));
    }

    for (int ridx=0; ridx < spotcx.size(); ++ridx){
      int itile = master_tiles[ridx];
      calc_minus_To_x = spotcx[ridx] - tox[itile];
      calc_minus_To_y = spotcy[ridx] - toy[itile];

      rotated_o_x = calc_minus_To_x * cosine[itile] - calc_minus_To_y * sine[itile];
      rotated_o_y = calc_minus_To_x * sine[itile] +   calc_minus_To_y * cosine[itile];

      model_calcx[ridx] = rotated_o_x + (tox[itile] + values[2*itile]);
      model_calcy[ridx] = rotated_o_y + (toy[itile] + values[2*itile+1]);

      partial_partial_theta_x = -calc_minus_To_x * sine[itile] - calc_minus_To_y * cosine[itile];
      partial_partial_theta_y =  calc_minus_To_x * cosine[itile] - calc_minus_To_y * sine[itile];

      partial_sq_theta_x = -calc_minus_To_x * cosine[itile] + calc_minus_To_y * sine[itile];
      partial_sq_theta_y = -calc_minus_To_x * sine[itile] - calc_minus_To_y * cosine[itile];

      double delx = model_calcx[ridx] - spotfx[ridx];
      double dely = model_calcy[ridx] - spotfy[ridx];
      double delrsq(delx*delx + dely*dely);
      functional += delrsq; // sum of square differences

      gradients_[2*itile]  += 2. *  delx;
      gradients_[2*itile+1]+= 2. *  dely;

      gradients_[128+itile] += scitbx::constants::pi_180 * 2.* (
        delx * partial_partial_theta_x +
        dely * partial_partial_theta_y
      );

      curvatures_[2*itile] += 2.;
      curvatures_[2*itile+1] += 2.;

      curvatures_[128+itile] += scitbx::constants::pi_180 * scitbx::constants::pi_180 * 2. * (
        ( partial_partial_theta_x*partial_partial_theta_x +
          partial_partial_theta_y*partial_partial_theta_y ) +
        ( delx*partial_sq_theta_x + dely*partial_sq_theta_y )
      );
    }
  }

  double f(){ return functional; }
  farray gradients(){ return gradients_; }
  farray curvatures(){ return curvatures_; }
};

namespace boost_python { namespace {

  void
  metrology_init_module() {
    using namespace boost::python;

    typedef return_value_policy<return_by_value> rbv;
    typedef default_call_policies dcp;

    class_<mark2_iteration>("mark2_iteration",no_init)
      .def(init< >())
      .def(init<mark2_iteration::farray, mark2_iteration::farray, mark2_iteration::farray,
                mark2_iteration::farray, mark2_iteration::farray,
                mark2_iteration::farray, mark2_iteration::farray,
                mark2_iteration::iarray >(
        (arg_("values"),arg("tox"),arg_("toy"),arg_("spotcx"),arg_("spotcy"),
         arg_("spotfx"),arg_("spotfy"),
         arg_("master_tiles"))))
      .def("f",&mark2_iteration::f)
      .def("gradients",&mark2_iteration::gradients)
      .def("curvatures",&mark2_iteration::curvatures)
      .add_property("model_calcx", make_getter(&mark2_iteration::model_calcx, rbv()))
      .add_property("model_calcy", make_getter(&mark2_iteration::model_calcy, rbv()))
    ;

}
}}} // namespace xfel::boost_python::<anonymous>

BOOST_PYTHON_MODULE(xfel_metrology_ext)
{
  xfel::boost_python::metrology_init_module();

}
