/*
 * scan.cc
 *
 *  Copyright (C) 2013 Diamond Light Source
 *
 *  Author: James Parkhurst
 *
 *  This code is distributed under the BSD license, a copy of which is
 *  included in the root directory of this package.
 */
#include <boost/python.hpp>
#include <boost/python/def.hpp>
#include <boost/python/make_constructor.hpp>
#include <string>
#include <sstream>
#include <scitbx/constants.h>
#include <dxtbx/model/scan.h>

namespace dxtbx { namespace model { namespace boost_python {

  using namespace boost::python;
  using scitbx::deg_as_rad;
  using scitbx::rad_as_deg;

  static
  vec2<double> rad_as_deg(vec2<double> angles) {
    angles[0] = rad_as_deg(angles[0]);
    angles[1] = rad_as_deg(angles[1]);
    return angles;
  }

  std::string scan_to_string(const ScanData &scan) {
    std::stringstream ss;
    ss << scan;
    return ss.str();
  }

  struct ScanPickleSuite : boost::python::pickle_suite {
    static
    boost::python::tuple getinitargs(const ScanData &obj) {
      return boost::python::make_tuple(
        obj.get_image_range(),
        rad_as_deg(obj.get_oscillation()),
        obj.get_exposure_time(),
        obj.get_epochs());
    }
  };

  static ScanData* make_scan(vec2 <int> image_range, vec2 <double> oscillation,
      double exposure_time, bool deg) {
    ScanData *scan = NULL;
    if (deg) {
      scan = new ScanData(image_range, 
        vec2 <double> (
          deg_as_rad(oscillation[0]), 
          deg_as_rad(oscillation[1])), 
        exposure_time);
    } else {
      scan = new ScanData(image_range, oscillation, exposure_time);
    }
    return scan;
  }

  static ScanData* make_scan_w_epoch(vec2 <int> image_range, 
      vec2 <double> oscillation, double exposure_time, 
      const flex_double &epochs, bool deg) {
    ScanData *scan = NULL;
    if (deg) {
      scan = new ScanData(image_range, 
        vec2 <double> (
          deg_as_rad(oscillation[0]), 
          deg_as_rad(oscillation[1])), 
        exposure_time, epochs);
    } else {
      scan = new ScanData(image_range, oscillation, exposure_time, epochs);
    }
    return scan;
  }
  
 
  static
  vec2<double> get_oscillation_range(const ScanData &scan, bool deg) {
    vec2<double> range = scan.get_oscillation_range();
    return deg ? rad_as_deg(range) : range;
  }

  static  
  vec2<double> get_oscillation(const ScanData &scan, bool deg) {
    vec2<double> oscillation = scan.get_oscillation();
    return deg ? rad_as_deg(oscillation) : oscillation;
  }

  static
  void set_oscillation(ScanData &scan, vec2<double> oscillation,
      bool deg) {
    if (deg) {
      oscillation = rad_as_deg(oscillation);
    }
    scan.set_oscillation(oscillation);
  }

   static  
  vec2<double> get_image_oscillation(const ScanData &scan, int image, 
      bool deg) {
    vec2<double> oscillation = scan.get_image_oscillation(image);
    return deg ? rad_as_deg(oscillation) : oscillation;
  }

  
  static 
  bool is_angle_valid(const ScanData &scan, double angle, bool deg) {
    return scan.is_angle_valid(deg ? deg_as_rad(angle) : angle);
  }

  static 
  double get_angle_from_image_index(const ScanData &scan, double index, 
      bool deg) {
    double angle = scan.get_angle_from_image_index(index);
    return deg ? rad_as_deg(angle) : angle;
  }

  static 
  double get_angle_from_array_index(const ScanData &scan, double index, 
      bool deg) {
    double angle = scan.get_angle_from_array_index(index);
    return deg ? rad_as_deg(angle) : angle;
  }

  static 
  double get_image_index_from_angle(const ScanData &scan, double angle, 
      bool deg) {
    return scan.get_image_index_from_angle(deg ? deg_as_rad(angle) : angle);
  }

  static 
  double get_array_index_from_angle(const ScanData &scan, double angle,
      bool deg) {
    return scan.get_array_index_from_angle(
      deg ? deg_as_rad(angle) : angle);
  }

  static 
  flex_double get_image_indices_with_angle(const ScanData &scan, double angle, 
      bool deg) {
    return scan.get_image_indices_with_angle(deg ? deg_as_rad(angle) : angle);
  }
  
  static 
  flex_double get_array_indices_with_angle(const ScanData &scan, 
      double angle, bool deg) {
    return scan.get_array_indices_with_angle(
      deg ? deg_as_rad(angle) : angle);
  }  
  
  void export_scan()
  {
    // Export ScanBase
    class_ <ScanBase> ("ScanBase");

    // Export Scan : ScanBase
    class_ <ScanData, bases <ScanBase> > ("ScanData")
      .def("__init__",
          make_constructor(
          &make_scan, 
          default_call_policies(), (
          arg("image_range"),
          arg("oscillation"),
          arg("exposure_time"),
          arg("deg") = true)))
      .def("__init__",
          make_constructor(
          &make_scan_w_epoch, 
          default_call_policies(), (
          arg("image_range"),
          arg("oscillation"),
          arg("exposure_time"),
          arg("epochs"),          
          arg("deg") = true)))
      .def("get_image_range",  
        &ScanData::get_image_range)
      .def("set_image_range",
        &ScanData::set_image_range)
      .def("get_array_range",  
        &ScanData::get_array_range)
      .def("get_oscillation",  
        &get_oscillation, (
          arg("deg") = true))
      .def("set_oscillation",
        &set_oscillation, (
          arg("deg") = true))
      .def("get_exposure_time",
        &ScanData::get_exposure_time)
      .def("set_exposure_time",
        &ScanData::set_exposure_time)
      .def("get_epochs",
        &ScanData::get_epochs)
      .def("set_epochs",
        &ScanData::set_epochs)
      .def("get_num_images",
        &ScanData::get_num_images)
      .def("get_image_oscillation",
        &get_image_oscillation, (
          arg("index"),
          arg("deg") = true))
      .def("get_image_epoch",
        &ScanData::get_image_epoch, (
          arg("index")))
      .def("get_oscillation_range",
        &get_oscillation_range, (
          arg("deg") = true))          
      .def("is_angle_valid",
        &is_angle_valid, (
          arg("angle"),
          arg("deg") = true))
      .def("is_image_index_valid",
        &ScanData::is_image_index_valid, (
          arg("index")))
      .def("is_array_index_valid",
        &ScanData::is_array_index_valid, (
          arg("index")))
      .def("get_angle_from_image_index",
        &get_angle_from_image_index, (
          arg("index"),
          arg("deg") = true))
      .def("get_angle_from_array_index",
        &get_angle_from_array_index, (
          arg("index"),
          arg("deg") = true))          
      .def("get_image_index_from_angle",
        &get_image_index_from_angle, (
          arg("angle"),
          arg("deg") = true))
      .def("get_array_index_from_angle",
        &get_array_index_from_angle, (
          arg("angle"),
          arg("deg") = true))
      .def("get_image_indices_with_angle",
        &get_image_indices_with_angle, (
          arg("angle"),
          arg("deg") = true))
      .def("get_array_indices_with_angle",
        &get_array_indices_with_angle, (
          arg("angle"),
          arg("deg") = true))
      .def("__eq__", &ScanData::operator==)
      .def("__nq__", &ScanData::operator!=)
      .def("__len__", &ScanData::get_num_images)
      .def("__str__", &scan_to_string)
      .def_pickle(ScanPickleSuite());
  }

}}} // namespace = dxtbx::model::boost_python
