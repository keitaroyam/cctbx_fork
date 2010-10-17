#ifndef CCTBX_RESTRAINTS_H
#define CCTBX_RESTRAINTS_H

#include <cctbx/import_scitbx_af.h>
#include <cctbx/xray/parameter_map.h>
#include <cctbx/xray/scatterer.h>

#include <scitbx/sparse/matrix.h>


namespace cctbx { namespace restraints {

  /// The linearised equations of restraints.
  /*
      Take advantage of the fact that the restraints part of the design matrix
      is sparse by constructing the design matrix for restraints only, along
      with the associated vectors of weights and deltas.

      The normal equations can then be obtained separately, and the normal
      equations derived from the observations can updated with the contribution
      from the restraints.
   */

  // Used by smtbx/refinement/restraints

  template <typename FloatType>
  class linearised_eqns_of_restraint
  {
  public:
    typedef FloatType scalar_t;

    std::size_t n_columns, n_rows;
    scitbx::sparse::matrix<scalar_t> design_matrix;
    scitbx::af::shared<scalar_t> weights;
    scitbx::af::shared<scalar_t> deltas;

  private:
    std::size_t row_i;

  public:
    linearised_eqns_of_restraint(std::size_t n_rows_, std::size_t n_columns_)
      : n_rows(n_rows_),
        n_columns(n_columns_),
        design_matrix(n_rows_, n_columns_),
        weights(n_rows_), deltas(n_rows_),
        row_i(0)
    {}

    std::size_t next_row() {
      CCTBX_ASSERT(!finalised())(row_i)(n_rows);
      return row_i++;
    }

    bool finalised() { return row_i >= n_rows; }

    std::size_t n_restraints() { return row_i; }

    std::size_t n_crystallographic_params() { return n_columns; }

  };

  template <typename FloatType, typename proxy_t, typename restraint_t>
  void linearise_restraints(
    uctbx::unit_cell const &unit_cell,
    af::const_ref<scitbx::vec3<FloatType> > const &sites_cart,
    cctbx::xray::parameter_map<cctbx::xray::scatterer<FloatType> > const &parameter_map,
    af::const_ref<proxy_t> const &proxies,
    linearised_eqns_of_restraint<FloatType> &linearised_eqns)
  {
    for(std::size_t i=0;i<proxies.size();i++) {
      proxy_t const& proxy = proxies[i];
      restraint_t restraint(unit_cell, sites_cart, proxy);
      restraint.linearise(
        unit_cell, linearised_eqns, parameter_map, proxy);
    }
  }

  template <typename FloatType, typename proxy_t, typename restraint_t>
  void linearise_restraints(
    af::const_ref<scitbx::sym_mat3<FloatType> > const &u_cart,
    af::const_ref<FloatType> const &u_iso,
    af::const_ref<bool> const &use_u_aniso,
    cctbx::xray::parameter_map<cctbx::xray::scatterer<FloatType> > const &parameter_map,
    af::const_ref<proxy_t> const &proxies,
    linearised_eqns_of_restraint<FloatType> &linearised_eqns)
  {
    for(std::size_t i=0;i<proxies.size();i++) {
      proxy_t const& proxy = proxies[i];
      restraint_t restraint(u_cart, u_iso, use_u_aniso, proxy);
      restraint.linearise(
        linearised_eqns, parameter_map, proxy.i_seqs);
    }
  }

  template <typename FloatType, typename proxy_t, typename restraint_t>
  void linearise_restraints(
    af::const_ref<scitbx::vec3<double> > const &sites_cart,
    af::const_ref<scitbx::sym_mat3<FloatType> > const &u_cart,
    cctbx::xray::parameter_map<cctbx::xray::scatterer<FloatType> > const &parameter_map,
    af::const_ref<proxy_t> const &proxies,
    linearised_eqns_of_restraint<FloatType> &linearised_eqns)
  {
    for(std::size_t i=0;i<proxies.size();i++) {
      proxy_t const& proxy = proxies[i];
      restraint_t restraint(sites_cart, u_cart, proxy);
      restraint.linearise(
        linearised_eqns, parameter_map, proxy.i_seqs);
    }
  }

  template <typename FloatType, typename proxy_t, typename restraint_t>
  void linearise_restraints(
    af::const_ref<scitbx::sym_mat3<FloatType> > const &u_cart,
    cctbx::xray::parameter_map<cctbx::xray::scatterer<FloatType> > const &parameter_map,
    af::const_ref<proxy_t> const &proxies,
    linearised_eqns_of_restraint<FloatType> &linearised_eqns)
  {
    for(std::size_t i=0;i<proxies.size();i++) {
      proxy_t const& proxy = proxies[i];
      restraint_t restraint(u_cart, proxy);
      restraint.linearise(
        linearised_eqns, parameter_map, proxy.i_seq);
    }
  }

}} // cctbx::restraints

#endif // GUARD
