#ifndef RSTBX_DETECTOR_MODEL_SENSOR_H
#define RSTBX_DETECTOR_MODEL_SENSOR_H
#include <scitbx/vec2.h>
#include <scitbx/vec3.h>
#include <scitbx/mat3.h>

namespace rstbx { namespace detector_model {

class sensor {

 public:

  sensor(const scitbx::vec3<double>& origin,
         const scitbx::vec3<double>& dir1,
         const scitbx::vec3<double>& dir2,
         const scitbx::vec2<double>& lim1,
         const scitbx::vec2<double>& lim2);

  //getters
  double get_distance() const {return distance;}
  scitbx::vec3<double> get_origin() const {return origin;}
  scitbx::vec3<double> get_normal() const {return normal;}
  scitbx::vec3<double> get_dir1() const {return dir1;}
  scitbx::vec3<double> get_dir2() const {return dir2;}
  scitbx::vec2<double> get_lim1() const {return lim1;}
  scitbx::vec2<double> get_lim2() const {return lim2;}
  scitbx::mat3<double> get_D() const {return D;}
  scitbx::mat3<double> get_d() const;

  //setters
  //Not yet implemented. Each must call update()

 private:

  //members
  scitbx::vec3<double> origin;
  scitbx::vec3<double> dir1;
  scitbx::vec3<double> dir2;
  scitbx::vec2<double> lim1;
  scitbx::vec2<double> lim2;

  scitbx::vec3<double> normal;
  scitbx::mat3<double> D;
  double distance;

  //Update the D() matrix, according to Lure I-II Contribution 8
  //(D. Thomas) amongst other things. Call this from any set method.
  void update();

};

}} //namespace rstbx::detector_model
#endif //RSTBX_DETECTOR_MODEL_SENSOR_H
