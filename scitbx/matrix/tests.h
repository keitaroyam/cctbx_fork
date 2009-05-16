#ifndef SCITBX_MATRIX_TESTS_H
#define SCITBX_MATRIX_TESTS_H

#include <scitbx/array_family/accessors/mat_grid.h>
#include <scitbx/array_family/versa_matrix.h>
#include <scitbx/array_family/ref_algebra.h>
#include <scitbx/matrix/norms.h>
#include <limits>
#include <cmath>

namespace scitbx { namespace matrix {

/// A measure of whether the columns and/or the rows of u
/// form an orthonormal system.
/** Reference: DLQT02.F and DQRT02.F in LAPACK tests (c.f. very end of those
    files) */
template <typename T>
T normality_ratio(af::const_ref<T, af::mat_grid> const &u,
                  T eps=std::numeric_limits<T>::epsilon())
{
  typedef af::versa<T, af::mat_grid> matrix_t;
  typedef af::const_ref<T, af::mat_grid> matrix_const_ref_t;
  typedef af::ref<T, af::mat_grid> matrix_ref_t;

  int m=u.n_rows(), n = u.n_columns();
  matrix_t ut_= af::matrix_transpose(u);
  matrix_const_ref_t ut = ut_.const_ref();
  if (m <= n) { // only the rows can be tested
    matrix_t delta = af::matrix_multiply(u, ut);
    matrix_ref_t delta_ = delta.ref();
    for (int i=0; i<m; ++i) delta_(i,i) -= 1;
    return (norm_1(delta.const_ref())/n)/eps;
  }
  else { // only the columns can be tested
    matrix_t delta = af::matrix_multiply(ut, u);
    matrix_ref_t delta_ = delta.ref();
    for (int i=0; i<n; ++i) delta_(i,i) -= 1;
    return (norm_1(delta.const_ref())/m)/eps;
  }
}


/// A measure the relative difference between a and b
template <typename T>
T equality_ratio(af::const_ref<T, af::mat_grid> const &a,
                 af::const_ref<T, af::mat_grid> const &b,
                 T eps=std::numeric_limits<T>::epsilon())
{
  SCITBX_ASSERT(a.n_rows() == b.n_rows());
  SCITBX_ASSERT(a.n_columns() == b.n_columns());
  typedef af::c_grid<2> dim;
  int m=a.n_rows(), n=a.n_columns();
  af::versa<T, dim> delta(dim(m, n));
  for (int i=0; i<m; ++i) for (int j=0; j<n; ++j) delta(i,j) = a(i,j) - b(i,j);
  return ((norm_1(delta.const_ref())
           /std::max(a.n_rows(), a.n_columns()))
           /norm_1(a))/eps;
}


}} // scitbx::matrix

#endif // GUARD
