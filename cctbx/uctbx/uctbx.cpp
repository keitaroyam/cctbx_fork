/* Copyright (c) 2001-2002 The Regents of the University of California
   through E.O. Lawrence Berkeley National Laboratory, subject to
   approval by the U.S. Department of Energy.
   See files COPYRIGHT.txt and LICENSE.txt for further details.

   Revision history:
     2002 Sep: Refactored (R.W. Grosse-Kunstleve)
     2001 Jul: Merged from CVS branch sgtbx_special_pos (rwgk)
     2001 May: merged from CVS branch sgtbx_type (R.W. Grosse-Kunstleve)
     2001 Apr: SourceForge release (R.W. Grosse-Kunstleve)
 */

#include <cctbx/error.h>
#include <cctbx/uctbx.h>
#include <cctbx/sgtbx/rot_mx.h>

namespace cctbx { namespace uctbx {

  namespace {

    void throw_corrupt_unit_cell_parameters()
    {
      throw error("Corrupt unit cell parameters.");
    }

    void throw_corrupt_metrical_matrix()
    {
      throw error("Corrupt metrical matrix.");
    }

    double
    dot_g(uc_vec3 const& u, uc_sym_mat3 const& g, uc_vec3 const& v)
    {
      return u * (g * v);
    }

    uc_vec3
    cross_g(double sqrt_det_g, uc_sym_mat3 const& g,
            uc_vec3 const& r, uc_vec3 const& s)
    {
      return sqrt_det_g * (g * r).cross(g * s);
    }

    double acos_deg(double x) { return scitbx::rad_as_deg(std::acos(x)); }

    af::double6
    parameters_from_metrical_matrix(const double* metrical_matrix)
    {
      af::double6 params;
      for(std::size_t i=0;i<3;i++) {
        if (metrical_matrix[i] <= 0.) throw_corrupt_metrical_matrix();
        params[i] = std::sqrt(metrical_matrix[i]);
      }
      params[3] = acos_deg(metrical_matrix[5] / params[1] / params[2]);
      params[4] = acos_deg(metrical_matrix[4] / params[2] / params[0]);
      params[5] = acos_deg(metrical_matrix[3] / params[0] / params[1]);
      return params;
    }

    uc_sym_mat3
    construct_metrical_matrix(
      af::double6 const& params, uc_vec3 const& cos_ang)
    {
      return uc_sym_mat3(
       params[0] * params[0],
       params[1] * params[1],
       params[2] * params[2],
       params[0] * params[1] * cos_ang[2],
       params[0] * params[2] * cos_ang[1],
       params[1] * params[2] * cos_ang[0]);
    }

  } // namespace <anonymous>

  void unit_cell::init_volume()
  {
    /* V = a * b * c * sqrt(1 - cos(alpha)^2 - cos(beta)^2 - cos(gamma)^2
                              + 2 * cos(alpha) * cos(beta) * cos(gamma))
     */
    double d = 1.;
    for(std::size_t i=0;i<3;i++) d -= cos_ang_[i] * cos_ang_[i];
    d += 2. * cos_ang_[0] * cos_ang_[1] * cos_ang_[2];
    if (d < 0.) throw_corrupt_unit_cell_parameters();
        volume_ = params_[0] * params_[1] * params_[2] * std::sqrt(d);
    if (volume_ <= 0.) throw_corrupt_unit_cell_parameters();
  }

  void unit_cell::init_reciprocal()
  {
    // Transformation Lattice Constants -> Reciprocal Lattice Constants
    // after Kleber, W., 17. Aufl., Verlag Technik GmbH Berlin 1990, P.352
    for(std::size_t i=0;i<3;i++) r_params_[i] = params_[(i + 1) % 3]
                                              * params_[(i + 2) % 3]
                                              * sin_ang_[i] / volume_;
    for(std::size_t i=0;i<3;i++) r_cos_ang_[i] = (  cos_ang_[(i + 1) % 3]
                                                  * cos_ang_[(i + 2) % 3]
                                                  - cos_ang_[i])
                                               / (  sin_ang_[(i + 1) % 3]
                                                  * sin_ang_[(i + 2) % 3]);
    for(std::size_t i=0;i<3;i++) {
      double a_rad = std::acos(r_cos_ang_[i]);
      r_params_[i+3] = scitbx::rad_as_deg(a_rad);
      r_sin_ang_[i] = std::sin(a_rad);
      r_cos_ang_[i] = std::cos(a_rad);
    }
  }

  void unit_cell::init_orth_and_frac_matrices()
  {
    // Crystallographic Basis: D = {a,b,c}
    // Cartesian Basis:        C = {i,j,k}
    //
    // PDB convention:
    //   i || a
    //   j is in (a,b) plane
    //   k = i x j

    double s1rca2 = std::sqrt(1. - r_cos_ang_[0] * r_cos_ang_[0]);
    if (s1rca2 == 0.) throw_corrupt_unit_cell_parameters();

    // fractional to cartesian
    orth_[0] =  params_[0];
    orth_[1] =  cos_ang_[2] * params_[1];
    orth_[2] =  cos_ang_[1] * params_[2];
    orth_[3] =  0.;
    orth_[4] =  sin_ang_[2] * params_[1];
    orth_[5] = -sin_ang_[1] * r_cos_ang_[0] * params_[2];
    orth_[6] =  0.;
    orth_[7] =  0.;
    orth_[8] =  sin_ang_[1] * params_[2] * s1rca2;

    // cartesian to fractional
    frac_[0] =  1. / params_[0];
    frac_[1] = -cos_ang_[2] / (sin_ang_[2] * params_[0]);
    frac_[2] = -(  cos_ang_[2] * sin_ang_[1] * r_cos_ang_[0]
                 + cos_ang_[1] * sin_ang_[2])
             / (sin_ang_[1] * s1rca2 * sin_ang_[2] * params_[0]);
    frac_[3] =  0.;
    frac_[4] =  1. / (sin_ang_[2] * params_[1]);
    frac_[5] =  r_cos_ang_[0] / (s1rca2 * sin_ang_[2] * params_[1]);
    frac_[6] =  0.;
    frac_[7] =  0.;
    frac_[8] =  1. / (sin_ang_[1] * s1rca2 * params_[2]);
  }

  void unit_cell::init_metrical_matrices()
  {
    metr_mx_ = construct_metrical_matrix(params_, cos_ang_);
    r_metr_mx_ = construct_metrical_matrix(r_params_, r_cos_ang_);
  }

  void unit_cell::initialize()
  {
    std::size_t i;
    for(i=0;i<6;i++) {
      if (params_[i] <= 0.) throw_corrupt_unit_cell_parameters();
    }
    for(i=3;i<6;i++) {
      double a_deg = params_[i];
      if (a_deg >= 180.) throw_corrupt_unit_cell_parameters();
      double a_rad = scitbx::deg_as_rad(a_deg);
      cos_ang_[i-3] = std::cos(a_rad);
      sin_ang_[i-3] = std::sin(a_rad);
      if (sin_ang_[i-3] == 0.) throw_corrupt_unit_cell_parameters();
    }
    init_volume();
    init_reciprocal();
    init_metrical_matrices();
    init_orth_and_frac_matrices();
    longest_vector_sq_ = -1.;
  }

  unit_cell::unit_cell(af::small<double, 6> const& parameters,
                       bool is_metrical_matrix)
  : params_(1,1,1,90,90,90)
  {
    if (!is_metrical_matrix) {
      std::copy(parameters.begin(), parameters.end(), params_.begin());
    }
    else {
      if (parameters.size() != 6) throw_corrupt_metrical_matrix();
      params_ = parameters_from_metrical_matrix(parameters.begin());
    }
    initialize();
  }

  unit_cell::unit_cell(af::double6 const& parameters)
  : params_(parameters)
  {
    initialize();
  }

  unit_cell::unit_cell(uc_sym_mat3 const& metrical_matrix)
  : params_(parameters_from_metrical_matrix(metrical_matrix.begin()))
  {
    try {
      initialize();
    }
    catch (error const&) {
      throw_corrupt_metrical_matrix();
    }
  }

  // used by reciprocal()
  unit_cell::unit_cell(
    af::double6 const& params,
    af::double3 const& sin_ang,
    af::double3 const& cos_ang,
    double volume,
    uc_sym_mat3 const& metr_mx,
    af::double6 const& r_params,
    af::double3 const& r_sin_ang,
    af::double3 const& r_cos_ang,
    uc_sym_mat3 const& r_metr_mx)
  :
    params_(params),
    sin_ang_(sin_ang),
    cos_ang_(cos_ang),
    volume_(volume),
    metr_mx_(metr_mx),
    r_params_(r_params),
    r_sin_ang_(r_sin_ang),
    r_cos_ang_(r_cos_ang),
    r_metr_mx_(r_metr_mx),
    longest_vector_sq_(-1.)
  {
    init_orth_and_frac_matrices();
  }

  unit_cell
  unit_cell::reciprocal() const
  {
    return unit_cell(
      r_params_,
      r_sin_ang_,
      r_cos_ang_,
      1. / volume_,
      r_metr_mx_,
      params_,
      sin_ang_,
      cos_ang_,
      metr_mx_);
  }

  double
  unit_cell::longest_vector_sq() const
  {
    if (longest_vector_sq_ < 0.) {
      longest_vector_sq_ = 0.;
      int corner[3];
      for (corner[0] = 0; corner[0] <= 1; corner[0]++)
      for (corner[1] = 0; corner[1] <= 1; corner[1]++)
      for (corner[2] = 0; corner[2] <= 1; corner[2]++) {
        fractional<> xf;
        for(std::size_t i=0;i<3;i++) xf[i] = corner[i];
        math::update_max(longest_vector_sq_, length_sq(xf));
      }
    }
    return longest_vector_sq_;
  }

  bool
  unit_cell::is_similar_to(unit_cell const& other,
                           double relative_length_tolerance,
                           double absolute_angle_tolerance) const
  {
    using scitbx::fn::absolute;
    const double* l1 = params_.begin();
    const double* l2 = other.params_.begin();
    for(std::size_t i=0;i<3;i++) {
      if (absolute(std::min(l1[i], l2[i]) / std::max(l1[i], l2[i]) - 1)
          > relative_length_tolerance) {
        return false;
      }
    }
    const double* a1 = l1 + 3;
    const double* a2 = l2 + 3;
    for(std::size_t i=0;i<3;i++) {
      if (absolute(a1[i] - a2[i]) > absolute_angle_tolerance) {
        return false;
      }
    }
    return true;
  }

  unit_cell
  unit_cell::change_basis(uc_mat3 const& r, double r_den) const
  {
    uc_mat3 r_ = r;
    if (r_den != 0) {
      r_ /= r_den;
    }
    return unit_cell(metr_mx_.tensor_transpose_transform(r_));
  }

  unit_cell
  unit_cell::change_basis(sgtbx::rot_mx const& c_inv_r) const
  {
    return change_basis(c_inv_r.as_double(), 1.);
  }

  miller::index<>
  unit_cell::max_miller_indices(double d_min, double tolerance) const
  {
    miller::index<> max_h;
    for(std::size_t i=0;i<3;i++) {
      uc_vec3 u(0,0,0);
      uc_vec3 v(0,0,0);
      u[(i + 1) % 3] = 1.;
      v[(i + 2) % 3] = 1.;
      // length of uxv is not used => sqrt(det(metr_mx)) is simply set to 1
      uc_vec3 uxv = cross_g(1., r_metr_mx_, u, v);
      double uxv2 = dot_g(uxv, r_metr_mx_, uxv);
      max_h[i] = (int)(uxv[i] / std::sqrt(uxv2) / d_min + tolerance);
    }
    return max_h;
  }

}} // namespace cctbx::uctbx
