#ifndef CCTBX_ADP_RESTRAINTS_ADP_SIMILARITY_H
#define CCTBX_ADP_RESTRAINTS_ADP_SIMILARITY_H

#include <cctbx/adp_restraints/adp_restraints.h>

namespace cctbx { namespace adp_restraints {

  struct adp_similarity_proxy : public adp_restraint_proxy<2> {
    adp_similarity_proxy() {}
    adp_similarity_proxy(
      af::tiny<unsigned, 2> const& i_seqs,
      double weight)
    : adp_restraint_proxy<2>(i_seqs, weight)
    {}
  };

  class adp_similarity : public adp_restraint_base<2> {
  public:
    //! Constructor.
    adp_similarity(
      af::tiny<scitbx::sym_mat3<double>, 2> const& u_cart,
      double weight)
    : adp_restraint_base<2>(af::tiny<bool, 2>(true, true), weight)
    {
      init_deltas(u_cart[0], u_cart[1]);
    }

    adp_similarity(
      af::tiny<double, 2> const& u_iso,
      double weight)
    : adp_restraint_base<2>(af::tiny<bool, 2>(false, false), weight)
    {
      init_deltas(u_iso[0], u_iso[1]);
    }

    adp_similarity(
      scitbx::sym_mat3<double> const& u_cart,
      double u_iso,
      double weight)
    : adp_restraint_base<2>(af::tiny<bool, 2>(true, false), weight)
    {
      init_deltas(u_cart, u_iso);
    }

    adp_similarity(
      double u_iso,
      scitbx::sym_mat3<double> const& u_cart,
      double weight)
    : adp_restraint_base<2>(af::tiny<bool, 2>(false, true), weight)
    {
      init_deltas(u_iso, u_cart);
    }

    //! Constructor.
    adp_similarity(
      adp_restraint_params<double> const &params,
      adp_similarity_proxy const& proxy)
    : adp_restraint_base<2>(params, proxy)
    {
      if (use_u_aniso[0] && use_u_aniso[1]) {
        CCTBX_ASSERT(proxy.i_seqs[0] < params.u_cart.size());
        CCTBX_ASSERT(proxy.i_seqs[1] < params.u_cart.size());
        init_deltas(params.u_cart[proxy.i_seqs[0]], params.u_cart[proxy.i_seqs[1]]);
      }
      else if (use_u_aniso[0] && !use_u_aniso[1]) {
        CCTBX_ASSERT(proxy.i_seqs[0] < params.u_cart.size());
        CCTBX_ASSERT(proxy.i_seqs[1] < params.u_iso.size());
        init_deltas(params.u_cart[proxy.i_seqs[0]], params.u_iso[proxy.i_seqs[1]]);
      }
      else if (!use_u_aniso[0] && use_u_aniso[1]) {
        CCTBX_ASSERT(proxy.i_seqs[0] < params.u_iso.size());
        CCTBX_ASSERT(proxy.i_seqs[1] < params.u_cart.size());
        init_deltas(params.u_iso[proxy.i_seqs[0]], params.u_cart[proxy.i_seqs[1]]);
      }
      else {
        CCTBX_ASSERT(proxy.i_seqs[0] < params.u_iso.size());
        CCTBX_ASSERT(proxy.i_seqs[1] < params.u_iso.size());
        init_deltas(params.u_iso[proxy.i_seqs[0]], params.u_iso[proxy.i_seqs[1]]);
      }
    }

    //! This returns gradients_u_cart and gradients_u_equiv combined
    af::tiny<scitbx::sym_mat3<double>, 2>
    gradients2() const {
      af::tiny<scitbx::sym_mat3<double>, 2> result;
      result[0] = gradients();
      result[1] = -result[0];
      return result;
    }

    void
    linearise(
      uctbx::unit_cell const &unit_cell,
      cctbx::restraints::linearised_eqns_of_restraint<double> &linearised_eqns,
      cctbx::xray::parameter_map<cctbx::xray::scatterer<double> > const &parameter_map,
      af::tiny<unsigned, 2> const& i_seqs) const
    {
      linearise_2<adp_similarity>(
        unit_cell, linearised_eqns, parameter_map, i_seqs, use_u_aniso, weight, deltas_);
    }

    //! Support for adp_similarity_residual_sum.
    /*! Not available in Python.
     */
    void
    add_gradients(
      af::ref<scitbx::sym_mat3<double> > const& gradients_aniso_cart,
      af::ref<double> const& gradients_iso,
      af::tiny<unsigned, 2> const& i_seqs) const
    {
      //! () - ()
      if (use_u_aniso[0] && use_u_aniso[1]) {
        scitbx::sym_mat3<double> g0 = gradients();
        gradients_aniso_cart[i_seqs[0]] += g0;
        gradients_aniso_cart[i_seqs[1]] += -g0;
      }
      //! () - o
      else if (use_u_aniso[0] && !use_u_aniso[1]) {
        scitbx::sym_mat3<double> g0 = gradients();
        gradients_aniso_cart[i_seqs[0]] += g0;
        gradients_iso[i_seqs[1]] += -g0.trace();
      }
      //! o - ()
      else if (!use_u_aniso[0] && use_u_aniso[1]) {
        scitbx::sym_mat3<double> g0 = gradients();
        gradients_iso[i_seqs[0]] += g0.trace();
        gradients_aniso_cart[i_seqs[1]] += -g0;
      }
      //! o - o
      else if (!use_u_aniso[0] && !use_u_aniso[1]) {
        double g_iso = 2 * deltas_[0];
        gradients_iso[i_seqs[0]] += g_iso;
        gradients_iso[i_seqs[1]] += -g_iso;
      }
    }

    static double grad_u_iso(int) {
      return 1;
    }

    static const double* cart_grad_row(int i) {
      static const double grads_u_cart[6][6] = {
        { 1, 0, 0, 0, 0, 0},
        { 0, 1, 0, 0, 0, 0},
        { 0, 0, 1, 0, 0, 0},
        { 0, 0, 0, 1, 0, 0},
        { 0, 0, 0, 0, 1, 0},
        { 0, 0, 0, 0, 0, 1},
      };
      return &grads_u_cart[i][0];
    }

  protected:

    void init_deltas(scitbx::sym_mat3<double> const &u_cart1,
      scitbx::sym_mat3<double> const &u_cart2)
    {
      for (int i=0; i<6; i++)
        deltas_[i] = u_cart1[i] - u_cart2[i];
    }

    void init_deltas(double u_iso1, double u_iso2) {
      deltas_[0] = u_iso1 - u_iso2;
      for (int i=1; i<6; i++) deltas_[i] = 0;
    }

    void init_deltas(scitbx::sym_mat3<double> const &u_cart, double u_iso) {
      for (int i=0; i<6; i++)
        deltas_[i] = u_cart[i] - (i < 3 ? u_iso : 0);
    }

    void init_deltas(double u_iso, scitbx::sym_mat3<double> const &u_cart) {
      for (int i=0; i<6; i++)
        deltas_[i] = (i < 3 ? u_iso : 0 ) - u_cart[i];
    }

  };

struct adp_u_eq_similarity_proxy : public adp_restraint_proxy<2> {
    adp_u_eq_similarity_proxy() {}
    adp_u_eq_similarity_proxy(
      af::tiny<unsigned, 2> const& i_seqs,
      double weight)
    : adp_restraint_proxy<2>(i_seqs, weight)
    {}
  };

class adp_u_eq_similarity : public adp_restraint_base<2> {
  public:
    //! Constructor.
    adp_u_eq_similarity(
      af::tiny<scitbx::sym_mat3<double>, 2> const& u_cart,
      double weight)
    : adp_restraint_base<2>(af::tiny<bool, 2>(true, true), weight)
    {
      init_deltas(u_cart[0], u_cart[1]);
    }

    adp_u_eq_similarity(
      af::tiny<double, 2> const& u_iso,
      double weight)
    : adp_restraint_base<2>(af::tiny<bool, 2>(false, false), weight)
    {
      init_deltas(u_iso[0], u_iso[1]);
    }

    adp_u_eq_similarity(
      scitbx::sym_mat3<double> const& u_cart,
      double u_iso,
      double weight)
    : adp_restraint_base<2>(af::tiny<bool, 2>(true, false), weight)
    {
      init_deltas(u_cart, u_iso);
    }

    adp_u_eq_similarity(
      double u_iso,
      scitbx::sym_mat3<double> const& u_cart,
      double weight)
    : adp_restraint_base<2>(af::tiny<bool, 2>(false, true), weight)
    {
      init_deltas(u_iso, u_cart);
    }

    //! Constructor.
    adp_u_eq_similarity(
      adp_restraint_params<double> const &params,
      adp_u_eq_similarity_proxy const& proxy)
    : adp_restraint_base<2>(params, proxy)
    {
      if (use_u_aniso[0] && use_u_aniso[1]) {
        CCTBX_ASSERT(proxy.i_seqs[0] < params.u_cart.size());
        CCTBX_ASSERT(proxy.i_seqs[1] < params.u_cart.size());
        init_deltas(params.u_cart[proxy.i_seqs[0]], params.u_cart[proxy.i_seqs[1]]);
      }
      else if (use_u_aniso[0] && !use_u_aniso[1]) {
        CCTBX_ASSERT(proxy.i_seqs[0] < params.u_cart.size());
        CCTBX_ASSERT(proxy.i_seqs[1] < params.u_iso.size());
        init_deltas(params.u_cart[proxy.i_seqs[0]], params.u_iso[proxy.i_seqs[1]]);
      }
      else if (!use_u_aniso[0] && use_u_aniso[1]) {
        CCTBX_ASSERT(proxy.i_seqs[0] < params.u_iso.size());
        CCTBX_ASSERT(proxy.i_seqs[1] < params.u_cart.size());
        init_deltas(params.u_iso[proxy.i_seqs[0]], params.u_cart[proxy.i_seqs[1]]);
      }
      else {
        CCTBX_ASSERT(proxy.i_seqs[0] < params.u_iso.size());
        CCTBX_ASSERT(proxy.i_seqs[1] < params.u_iso.size());
        init_deltas(params.u_iso[proxy.i_seqs[0]], params.u_iso[proxy.i_seqs[1]]);
      }
    }

    //! This returns gradients_u_cart and gradients_u_equiv combined
    af::tiny<scitbx::sym_mat3<double>, 2>
    gradients2() const {
      af::tiny<scitbx::sym_mat3<double>, 2> result;
      result[0] = gradients();
      result[1] = -result[0];
      return result;
    }

    void
    linearise(
      uctbx::unit_cell const &unit_cell,
      cctbx::restraints::linearised_eqns_of_restraint<double> &linearised_eqns,
      cctbx::xray::parameter_map<cctbx::xray::scatterer<double> > const &parameter_map,
      af::tiny<unsigned, 2> const& i_seqs) const
    {
      linearise_2<adp_u_eq_similarity>(
        unit_cell, linearised_eqns, parameter_map, i_seqs, use_u_aniso, weight, deltas_);
    }

    //! Support for adp_similarity_residual_sum.
    /*! Not available in Python.
     */
    void
    add_gradients(
      af::ref<scitbx::sym_mat3<double> > const& gradients_aniso_cart,
      af::ref<double> const& gradients_iso,
      af::tiny<unsigned, 2> const& i_seqs) const
    {
      //! () - ()
      if (use_u_aniso[0] && use_u_aniso[1]) {
        scitbx::sym_mat3<double> g0 = gradients();
        gradients_aniso_cart[i_seqs[0]] += g0;
        gradients_aniso_cart[i_seqs[1]] += -g0;
      }
      //! () - o
      else if (use_u_aniso[0] && !use_u_aniso[1]) {
        scitbx::sym_mat3<double> g0 = gradients();
        gradients_aniso_cart[i_seqs[0]] += g0;
        gradients_iso[i_seqs[1]] += -g0.trace();
      }
      //! o - ()
      else if (!use_u_aniso[0] && use_u_aniso[1]) {
        scitbx::sym_mat3<double> g0 = gradients();
        gradients_iso[i_seqs[0]] += g0.trace();
        gradients_aniso_cart[i_seqs[1]] += -g0;
      }
      //! o - o
      else if (!use_u_aniso[0] && !use_u_aniso[1]) {
        double g_iso = 2 * deltas_[0];
        gradients_iso[i_seqs[0]] += g_iso;
        gradients_iso[i_seqs[1]] += -g_iso;
      }
    }

    static double grad_u_iso(int) { return 1; }

    static const double* cart_grad_row(int i) {
      static const double grads_u_cart[6][6] = {
        {1./3, 1./3, 1./3, 0, 0, 0},
        {1./3, 1./3, 1./3, 0, 0, 0},
        {1./3, 1./3, 1./3, 0, 0, 0},
        {   0,    0,    0, 0, 0, 0},
        {   0,    0,    0, 0, 0, 0},
        {   0,    0,    0, 0, 0, 0}
      };
      return &grads_u_cart[i][0];
    }

  protected:

    void init_deltas(scitbx::sym_mat3<double> const &u_cart1,
      scitbx::sym_mat3<double> const &u_cart2)
    {
      double u_eq_minus_u_eq  = (u_cart1.trace()-u_cart2.trace())/3;
      for (int i=0; i<6; i++)
        deltas_[i] = (i < 3 ? u_eq_minus_u_eq : 0);
    }

    void init_deltas(double u_iso1, double u_iso2) {
      deltas_[0] = u_iso1 - u_iso2;
      for (int i=1; i<6; i++) deltas_[i] = 0;
    }

    void init_deltas(scitbx::sym_mat3<double> const &u_cart, double u_iso) {
      double u_eq_minus_u_iso = (u_cart.trace()/3-u_iso);
      for (int i=0; i<6; i++)
        deltas_[i] = (i < 3 ? u_eq_minus_u_iso : 0);
    }

    void init_deltas(double u_iso, scitbx::sym_mat3<double> const &u_cart) {
      double u_iso_minus_u_eq = (u_iso-u_cart.trace()/3);
      for (int i=0; i<6; i++)
        deltas_[i] = (i < 3 ? u_iso_minus_u_eq : 0);
    }

  };

struct adp_volume_similarity_proxy : public adp_restraint_proxy<2> {
    adp_volume_similarity_proxy() {}
    adp_volume_similarity_proxy(
      af::tiny<unsigned, 2> const& i_seqs,
      double weight)
    : adp_restraint_proxy<2>(i_seqs, weight)
    {}
  };

class adp_volume_similarity : public adp_restraint_base<2> {
  public:
    //! Constructor.
    adp_volume_similarity(
      af::tiny<scitbx::sym_mat3<double>, 2> const& u_cart,
      double weight)
    : adp_restraint_base<2>(af::tiny<bool, 2>(true, true), weight)
    {
      init();
      init_deltas(u_cart[0], u_cart[1]);
    }

    adp_volume_similarity(
      af::tiny<double, 2> const& u_iso,
      double weight)
    : adp_restraint_base<2>(af::tiny<bool, 2>(false, false), weight)
    {
      init_deltas(u_iso[0], u_iso[1]);
    }

    adp_volume_similarity(
      scitbx::sym_mat3<double> const& u_cart,
      double u_iso,
      double weight)
    : adp_restraint_base<2>(af::tiny<bool, 2>(true, false), weight)
    {
      init();
      init_deltas(u_cart, u_iso);
    }

    adp_volume_similarity(
      double u_iso,
      scitbx::sym_mat3<double> const& u_cart,
      double weight)
    : adp_restraint_base<2>(af::tiny<bool, 2>(false, true), weight)
    {
      init();
      init_deltas(u_iso, u_cart);
    }

    //! Constructor.
    adp_volume_similarity(
      adp_restraint_params<double> const &params,
      adp_volume_similarity_proxy const& proxy)
    : adp_restraint_base<2>(params, proxy)
    {
      init();
      if (use_u_aniso[0] && use_u_aniso[1]) {
        CCTBX_ASSERT(proxy.i_seqs[0] < params.u_cart.size());
        CCTBX_ASSERT(proxy.i_seqs[1] < params.u_cart.size());
        init_deltas(params.u_cart[proxy.i_seqs[0]], params.u_cart[proxy.i_seqs[1]]);
      }
      else if (use_u_aniso[0] && !use_u_aniso[1]) {
        CCTBX_ASSERT(proxy.i_seqs[0] < params.u_cart.size());
        CCTBX_ASSERT(proxy.i_seqs[1] < params.u_iso.size());
        init_deltas(params.u_cart[proxy.i_seqs[0]], params.u_iso[proxy.i_seqs[1]]);
      }
      else if (!use_u_aniso[0] && use_u_aniso[1]) {
        CCTBX_ASSERT(proxy.i_seqs[0] < params.u_iso.size());
        CCTBX_ASSERT(proxy.i_seqs[1] < params.u_cart.size());
        init_deltas(params.u_iso[proxy.i_seqs[0]], params.u_cart[proxy.i_seqs[1]]);
      }
      else {
        CCTBX_ASSERT(proxy.i_seqs[0] < params.u_iso.size());
        CCTBX_ASSERT(proxy.i_seqs[1] < params.u_iso.size());
        init_deltas(params.u_iso[proxy.i_seqs[0]], params.u_iso[proxy.i_seqs[1]]);
      }
    }

    //! This returns gradients_u_cart and gradients_u_equiv combined
    af::tiny<scitbx::sym_mat3<double>, 2>
    gradients2() const {
      af::tiny<scitbx::sym_mat3<double>, 2> result;
      result[0] = gradients();
      result[1] = -result[0];
      return result;
    }

    void
    linearise(
      uctbx::unit_cell const &unit_cell,
      cctbx::restraints::linearised_eqns_of_restraint<double> &linearised_eqns,
      cctbx::xray::parameter_map<cctbx::xray::scatterer<double> > const &parameter_map,
      af::tiny<unsigned, 2> const& i_seqs) const
    {
      linearise_2<adp_volume_similarity>(*this,
        unit_cell, linearised_eqns, parameter_map, i_seqs, use_u_aniso, weight, deltas_);
    }

    void
    add_gradients(
      af::ref<scitbx::sym_mat3<double> > const& gradients_aniso_cart,
      af::ref<double> const& gradients_iso,
      af::tiny<unsigned, 2> const& i_seqs) const
    {
      //! () - ()
      if (use_u_aniso[0] && use_u_aniso[1]) {
        scitbx::sym_mat3<double> g0 = gradients();
        gradients_aniso_cart[i_seqs[0]] += g0;
        gradients_aniso_cart[i_seqs[1]] += -g0;
      }
      //! () - o
      else if (use_u_aniso[0] && !use_u_aniso[1]) {
        scitbx::sym_mat3<double> g0 = gradients();
        gradients_aniso_cart[i_seqs[0]] += g0;
        gradients_iso[i_seqs[1]] += -g0.trace();
      }
      //! o - ()
      else if (!use_u_aniso[0] && use_u_aniso[1]) {
        scitbx::sym_mat3<double> g0 = gradients();
        gradients_iso[i_seqs[0]] += g0.trace();
        gradients_aniso_cart[i_seqs[1]] += -g0;
      }
      //! o - o
      else if (!use_u_aniso[0] && !use_u_aniso[1]) {
        double g_iso = 2 * deltas_[0];
        gradients_iso[i_seqs[0]] += g_iso;
        gradients_iso[i_seqs[1]] += -g_iso;
      }
    }

    double grad_u_iso(int i) const {
      if (!use_u_aniso[i]) {
        return scitbx::constants::four_pi*scitbx::fn::pow2(
          i==0 ? radii_[0] : radii_[3]);
      }
      CCTBX_NOT_IMPLEMENTED();
      return 0;
    }
    // i - which i_seq, j - which row
    const double* cart_grad_row(int i_seq, int i) const {
      static const double coeff = 4*scitbx::constants::pi/3;
      if (use_u_aniso[i_seq]) {
        if (i>2) {
          for (int i=0; i < 3; i++)
            grad_u_cart_row_[i] = 0;
        }
        else {
          if (i_seq==0)  {
            grad_u_cart_row_[0] = coeff*radii_[1]*radii_[2];
            grad_u_cart_row_[1] = coeff*radii_[0]*radii_[2];
            grad_u_cart_row_[2] = coeff*radii_[0]*radii_[1];
          }
          else {
            grad_u_cart_row_[0] = coeff*radii_[4]*radii_[5];
            grad_u_cart_row_[1] = coeff*radii_[3]*radii_[5];
            grad_u_cart_row_[2] = coeff*radii_[3]*radii_[4];
          }
        }
        return &grad_u_cart_row_[0];
      }
      CCTBX_NOT_IMPLEMENTED();
      return 0;
    }

  protected:
    // note that two rows cannot be accessed at the same time!
    mutable double grad_u_cart_row_[6];
    double radii_[6];

    static double r3diff_to_vol(double r3diff) {
      return 4*scitbx::constants::pi*r3diff/3;
    }

    void init_deltas(scitbx::sym_mat3<double> const &u_cart1,
      scitbx::sym_mat3<double> const &u_cart2)
    {
      double delta_vol = r3diff_to_vol(
        u_cart1[0]*u_cart1[1]*u_cart1[2] -
        u_cart2[0]*u_cart2[1]*u_cart2[2]);
      for (int i=0; i<3; i++) {
        deltas_[i] = delta_vol;
        radii_[i] = u_cart1[i];
        deltas_[i+3] = 0;
        radii_[i+3] = u_cart2[i];
      }
    }

    void init_deltas(double u_iso1, double u_iso2) {
      deltas_[0] = r3diff_to_vol(
        scitbx::fn::pow3(u_iso1) -
        scitbx::fn::pow3(u_iso2));
      radii_[0] = u_iso1;
      radii_[3] = u_iso2;
      for (int i=1; i<6; i++) deltas_[i] = 0;
    }

    void init_deltas(scitbx::sym_mat3<double> const &u_cart, double u_iso) {
      double delta_vol = r3diff_to_vol(
        u_cart[0]*u_cart[1]*u_cart[2] -
        scitbx::fn::pow3(u_iso));
      radii_[3] = u_iso;
      for (int i=0; i<3; i++) {
        deltas_[i] = delta_vol;
        deltas_[i+3] = 0;
        radii_[i] = u_cart[i];
      }
    }

    void init_deltas(double u_iso, scitbx::sym_mat3<double> const &u_cart) {
      double delta_vol = r3diff_to_vol(
        scitbx::fn::pow3(u_iso) -
        u_cart[0]*u_cart[1]*u_cart[2]);
      radii_[0] = u_iso;
      for (int i=0; i<3; i++) {
        deltas_[i] = delta_vol;
        deltas_[i+3] = 0;
        radii_[i+3] = u_cart[i];
      }
    }

    void init() {
      for (int i=0; i < 6; i++)
        grad_u_cart_row_[i] = radii_[i] = 0;
    }

  };

}} // cctbx::adp_restraints

#endif
