#ifndef SMTBX_REFINEMENT_CONSTRAINTS_GEOMETRICAL_HYDROGENS_H
#define SMTBX_REFINEMENT_CONSTRAINTS_GEOMETRICAL_HYDROGENS_H

#include <smtbx/refinement/constraints/reparametrisation.h>
#include <scitbx/constants.h>
#include <scitbx/math/orthonormal_basis.h>
#include <boost/optional.hpp>
#include <cmath>


namespace smtbx { namespace refinement { namespace constraints {

namespace constants {
  using namespace scitbx::constants;
  static double const cos_tetrahedral_angle = -1./3.;
  static double const tetrahedral_angle = std::acos(cos_tetrahedral_angle);
  static double const sin_tetrahedral_angle
    = std::sqrt(1. - cos_tetrahedral_angle*cos_tetrahedral_angle);
  static double const half_sqrt_3 = std::sqrt(3.)/2;
}


/// Model of Y-XHn with tetrahedral angles
/**
  X is referred to as the "pivot" and Y as the "pivot neighbour".

  All angles Hi-X-Hj and Hi-X-Y are tetrahedral.
  All distances X-Hi are equal. That unique distance may be a variable
  parameter if stretching is allowed.
  A free rotation around the bond Y-X is allowed, characterized by an
  azimuthal angle.

  The Hydrogen sites ride on the pivot site.
*/
class terminal_tetrahedral_xhn_sites : public crystallographic_parameter
{
public:
  /// Construct sites depending on the given parameter groups
  /** e_zero_azimuth is the vector defining azimuth = 0. It shall be such that
      it can never become nearly colinear to the bond between the pivot
      and its neighbour.
   */
  terminal_tetrahedral_xhn_sites(site_parameter *pivot,
                                 site_parameter *pivot_neighbour,
                                 independent_scalar_parameter *azimuth,
                                 independent_scalar_parameter *length,
                                 cart_t const &e_zero_azimuth,
                                 af::small<scatterer_pointer, 3> const &hydrogen)
    : crystallographic_parameter(4),
      e_zero_azimuth(e_zero_azimuth),
      hydrogen(hydrogen),
      x_h(hydrogen.size())
  {
    set_arguments(pivot, pivot_neighbour, azimuth, length);
  }

  virtual std::size_t size() const;

  virtual void linearise(uctbx::unit_cell const &unit_cell,
                         sparse_matrix_type *jacobian_transpose);

  virtual void store(uctbx::unit_cell const &unit_cell) const;

private:
  af::small<scatterer_pointer, 3> hydrogen;
  cart_t e_zero_azimuth;
  af::small<cart_t, 3> x_h;
};


/// A parameter representing an angle in radians starting as tetrahedral
class angle_starting_tetrahedral : public independent_scalar_parameter
{
public:
  angle_starting_tetrahedral(bool variable=true)
    : independent_scalar_parameter(constants::tetrahedral_angle, variable)
  {}
};


/// Model of X-CH2-Y
/**
  C is referred to as the "pivot" and X and Y as pivot's neighbour 1 and 2.

  All angles Hi-C-X and Hi-C-Y are equal.
  The angle H-C-H is refinable (flapping).
*/
class secondary_ch2_sites : public crystallographic_parameter
{
public:
  secondary_ch2_sites(site_parameter *pivot,
                      site_parameter *pivot_neighbour_0,
                      site_parameter *pivot_neighbour_1,
                      independent_scalar_parameter *length,
                      angle_starting_tetrahedral *h_c_h,
                      scatterer_pointer &hydrogen_0,
                      scatterer_pointer &hydrogen_1)
    : crystallographic_parameter(5),
      h(hydrogen_0, hydrogen_1)
  {
    set_arguments(pivot, pivot_neighbour_0, pivot_neighbour_1, length, h_c_h);
  }

  virtual std::size_t size() const;

  virtual void linearise(uctbx::unit_cell const &unit_cell,
                         sparse_matrix_type *jacobian_transpose);

  virtual void store(uctbx::unit_cell const &unit_cell) const;

private:
  af::tiny<scatterer_pointer, 2> h;
  af::tiny<cart_t, 2> x_h;
};


/// Model of tertiary CH
/** All angles Hi-C-X are equal.
 */
class tertiary_ch_site : public crystallographic_parameter
{
public:
  tertiary_ch_site(site_parameter *pivot,
                   site_parameter *pivot_neighbour_0,
                   site_parameter *pivot_neighbour_1,
                   site_parameter *pivot_neighbour_2,
                   independent_scalar_parameter *length,
                   scatterer_pointer &hydrogen)
    : crystallographic_parameter(5), h(hydrogen)
  {
    set_arguments(pivot,
                  pivot_neighbour_0, pivot_neighbour_1, pivot_neighbour_2,
                  length);
  }

  virtual std::size_t size() const;

  virtual void linearise(uctbx::unit_cell const &unit_cell,
                         sparse_matrix_type *jacobian_transpose);

  virtual void store(uctbx::unit_cell const &unit_cell) const;

private:
  scatterer_pointer h;
  cart_t x_h;
};


/// Model of aromatic C-H or amide N-H
/** Denoting C or N as X and the two neighbours of X as Y and Z,
    Z-X-Y is bisected by X-H.
*/
class secondary_planar_xh : public crystallographic_parameter
{
public:
  secondary_planar_xh(site_parameter *pivot,
                      site_parameter *pivot_neighbour_0,
                      site_parameter *pivot_neighbour_1,
                      independent_scalar_parameter *length,
                      scatterer_pointer &hydrogen)
    : crystallographic_parameter(4), h(hydrogen)
  {
    set_arguments(pivot, pivot_neighbour_0, pivot_neighbour_1, length);
  }

  virtual std::size_t size() const;

  virtual void linearise(uctbx::unit_cell const &unit_cell,
                         sparse_matrix_type *jacobian_transpose);

  virtual void store(uctbx::unit_cell const &unit_cell) const;

private:
  scatterer_pointer h;
  cart_t x_h;
};


/// Model of terminal Z-Y=XH2 (ethylenic CH2 or amide NH2)
/**
    X is referred to as the "pivot" whereas Y is the pivot's neighbour
    and Z is the pivot's neighbour's substituent.

    The two hydrogen atoms are in the plane ZYX,
    and XY bissects the 120-degree angle H1-X-H2.
*/
class terminal_planar_xh2_sites : public crystallographic_parameter
{
public:
  terminal_planar_xh2_sites(site_parameter *pivot,
                            site_parameter *pivot_neighbour,
                            site_parameter *pivot_neighbour_substituent,
                            independent_scalar_parameter *length,
                            scatterer_pointer &hydrogen_0,
                            scatterer_pointer &hydrogen_1)
    : crystallographic_parameter(4), h(hydrogen_0, hydrogen_1)
  {
    set_arguments(pivot, pivot_neighbour, pivot_neighbour_substituent, length);
  }

  virtual std::size_t size() const;

  virtual void linearise(uctbx::unit_cell const &unit_cell,
                         sparse_matrix_type *jacobian_transpose);

  virtual void store(uctbx::unit_cell const &unit_cell) const;

private:
  af::tiny<cart_t, 2> x_h;
  af::tiny<scatterer_pointer, 2> h;
};


}}}

#endif // GUARD
