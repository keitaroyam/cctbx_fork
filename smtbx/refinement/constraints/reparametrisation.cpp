#include <smtbx/refinement/constraints/reparametrisation.h>

namespace smtbx { namespace refinement { namespace constraints {

  // parameter

  parameter::~parameter() { delete[] arg; }

  bool parameter::is_variable() const { return variable; }

  void parameter::set_variable(bool f) { variable = f; }

  double *parameter::components() { return 0; }

 // independent_scalar_parameter

  std::size_t independent_scalar_parameter::size() const { return 1; }

  void independent_scalar_parameter
  ::linearise(uctbx::unit_cell const &unit_cell,
              sparse_matrix_type *jacobian_transpose)
  {}

  double *independent_scalar_parameter::components() { return &value; }

  // independent_small_vector_parameter

  template class independent_small_vector_parameter<3>;
  template class independent_small_vector_parameter<6>;

  // single_scatterer_parameter

  crystallographic_parameter::scatterer_sequence_type
  single_scatterer_parameter::scatterers() const {
    return scatterer_sequence_type(&scatterer, 1);
  }

  index_range
  single_scatterer_parameter
  ::component_indices_for(scatterer_type const *scatterer) const
  {
    return scatterer == this->scatterer ? index_range(index(), size())
                                        : index_range();
  }

  // site_parameter

  std::size_t site_parameter::size() const { return 3; }

  void site_parameter::store(uctbx::unit_cell const &unit_cell) const {
    scatterer->site = value;
  }

  // independent_site_parameter

  void independent_site_parameter::set_variable(bool f) {
    scatterer->flags.set_grad_site(f);
  }

  bool independent_site_parameter::is_variable() const {
    return scatterer->flags.grad_site();
  }

  void independent_site_parameter
  ::linearise(uctbx::unit_cell const &unit_cell,
              sparse_matrix_type *jacobian_transpose)
  {
    value = scatterer->site;
  }

  double *independent_site_parameter::components() {
    return value.begin();
  }

  // ADP

  std::size_t u_star_parameter::size() const { return 6; }

  void u_star_parameter::store(uctbx::unit_cell const &unit_cell) const {
    scatterer->u_star = value;
  }

  // independent ADP

  void independent_u_star_parameter::set_variable(bool f) {
    if (f) scatterer->flags.set_use_u_aniso(true);
    scatterer->flags.set_grad_u_aniso(f);
  }

  bool independent_u_star_parameter::is_variable() const {
    return scatterer->flags.use_u_aniso() && scatterer->flags.grad_u_aniso();
  }

  void independent_u_star_parameter
  ::linearise(uctbx::unit_cell const &unit_cell,
              sparse_matrix_type *jacobian_transpose)
  {
    value = adptbx::u_star_as_u_cart(unit_cell, scatterer->u_star);
  }

  double *independent_u_star_parameter::components() {
    return value.begin();
  }

  // Occupancy

  std::size_t occupancy_parameter::size() const { return 1; }

  void occupancy_parameter::store(uctbx::unit_cell const &unit_cell) const {
    scatterer->occupancy = value;
  }

  // independent Occupancy

  void independent_occupancy_parameter::set_variable(bool f) {
    scatterer->flags.set_grad_occupancy(f);
  }

  bool independent_occupancy_parameter::is_variable() const {
    return scatterer->flags.grad_occupancy();
  }

  void independent_occupancy_parameter
  ::linearise(uctbx::unit_cell const &unit_cell,
              sparse_matrix_type *jacobian_transpose)
  {
    value = scatterer->occupancy;
  }

  double *independent_occupancy_parameter::components() { return &value; }

  // u_iso

  std::size_t u_iso_parameter::size() const { return 1; }

  void u_iso_parameter::store(uctbx::unit_cell const &unit_cell) const {
    scatterer->u_iso = value;
  }

  // independent u_iso

  void independent_u_iso_parameter::set_variable(bool f) {
    if (f) scatterer->flags.set_use_u_iso(true);
    scatterer->flags.set_grad_u_iso(f);
  }

  bool independent_u_iso_parameter::is_variable() const {
    return scatterer->flags.grad_u_iso();
  }

  void independent_u_iso_parameter
  ::linearise(uctbx::unit_cell const &unit_cell,
              sparse_matrix_type *jacobian_transpose)
  {
    value = scatterer->u_iso;
  }

  double *independent_u_iso_parameter::components() { return &value; }

}}}
