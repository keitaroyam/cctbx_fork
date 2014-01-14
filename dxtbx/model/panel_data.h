/*
* panel_data.h
*
*  Copyright (C) 2013 Diamond Light Source
*
*  Author: James Parkhurst
*
*  This code is distributed under the BSD license, a copy of which is
*  included in the root directory of this package.
*/
#ifndef DXTBX_MODEL_PANEL_DATA_H
#define DXTBX_MODEL_PANEL_DATA_H

#include <string>
#include <scitbx/array_family/tiny_types.h>
#include <dxtbx/model/model_helpers.h>
#include <dxtbx/model/virtual_panel.h>
#include <dxtbx/error.h>

namespace dxtbx { namespace model {

  using scitbx::af::int4;

  /**
   * A panel class.
   */
  class PanelData : public VirtualPanel {
  public:

    /** Construct the panel with the simple px->mm strategy */
    PanelData()
      : pixel_size_(0.0, 0.0),
        image_size_(0, 0),
        trusted_range_(0.0, 0.0) {}

    /** Construct with data */
    PanelData(std::string type,
          std::string name,
          vec3 <double> fast_axis,
          vec3 <double> slow_axis,
          vec3 <double> origin,
          vec2 <double> pixel_size,
          vec2 <std::size_t> image_size,
          vec2 <double> trusted_range)
      : pixel_size_(pixel_size),
        image_size_(image_size),
        trusted_range_(trusted_range) {
      set_type(type);
      set_name(name);
      set_local_frame(fast_axis, slow_axis, origin);
    }

    virtual ~PanelData() {}

    /** Get the pixel size */
    vec2 <double> get_pixel_size() const {
      return pixel_size_;
    }

    /** Set the pixel size */
    void set_pixel_size(vec2 <double> pixel_size) {
      pixel_size_ = pixel_size;
    }

    /** Get the image size */
    vec2 <std::size_t> get_image_size() const {
      return image_size_;
    }

    /** Set the image size */
    void set_image_size(vec2 <std::size_t> image_size) {
      image_size_ = image_size;
    }

    /** Get the trusted range */
    vec2 <double> get_trusted_range() const {
      return trusted_range_;
    }

    /** Set the trusted range */
    void set_trusted_range(vec2 <double> trusted_range) {
      trusted_range_ = trusted_range;
    }

    /** Get the mask array */
    scitbx::af::shared<int4> get_mask() const {
      scitbx::af::shared<int4> result((scitbx::af::reserve(mask_.size())));
      std::copy(mask_.begin(), mask_.end(), std::back_inserter(result));
      return result;
    }

    /** Set the mask */
    void set_mask(const scitbx::af::const_ref<int4> &mask) {
      mask_.clear();
      std::copy(mask.begin(), mask.end(), std::back_inserter(mask_));
    }

    /** Add an element to the mask */
    void add_mask(int f0, int s0, int f1, int s1) {
      mask_.push_back(int4(f0, f1, s0, s1));
    }

    /** @returns True/False this is the same as the other */
    bool operator==(const PanelData &rhs) const {
      return VirtualPanel::operator==(rhs)
          && image_size_ == rhs.image_size_
          && pixel_size_.const_ref().all_approx_equal(rhs.pixel_size_.const_ref(), 1e-6)
          && trusted_range_.const_ref().all_approx_equal(rhs.trusted_range_.const_ref(), 1e-6);
    }

    /** @returns True/False this is not the same as the other */
    bool operator!=(const PanelData &rhs) const {
      return !(*this == rhs);
    }

    /** @returns True/False the panels are similar */
    bool is_similar_to(const PanelData &rhs) const {
      return image_size_.const_ref().all_eq(
              rhs.image_size_.const_ref())
          && pixel_size_.const_ref().all_approx_equal(
              rhs.pixel_size_.const_ref(), 1e-7);
//          && trusted_range_.const_ref().all_approx_equal(
//              rhs.trusted_range_.const_ref(), 1e-7);
    }

  protected:
    vec2 <double> pixel_size_;
    vec2 <std::size_t> image_size_;
    vec2 <double> trusted_range_;
    scitbx::af::shared<int4> mask_;
  };

}} // namespace dxtbx::model

#endif // DXTBX_MODEL_PANEL_H

