/// Tools implementing the Gauss-Newton method for non-linear least-squares.

#ifndef SCITBX_GAUSS_NEWTON_H
#define SCITBX_GAUSS_NEWTON_H

#include <scitbx/array_family/shared.h>
#include <scitbx/array_family/owning_ref.h>
#include <scitbx/matrix/cholesky.h>
#include <scitbx/matrix/matrix_vector_operations.h>

namespace scitbx { namespace lstbx {

#define SCITBX_LSTBX_DECLARE_ARRAY_TYPE(FloatType)                            \
    typedef FloatType scalar_t;                                               \
    typedef af::ref_owning_versa<scalar_t,                                    \
                                 matrix::packed_u_accessor>                   \
            symmetric_matrix_owning_ref_t;                                    \
    typedef af::ref<scalar_t,                                                 \
                    matrix::packed_u_accessor>                                \
            symmetric_matrix_ref_t;                                           \
    typedef af::versa<scalar_t,                                               \
                      matrix::packed_u_accessor>                              \
            symmetric_matrix_t;                                               \
    typedef af::ref_owning_versa<FloatType, af::mat_grid> matrix_owning_ref_t;\
    typedef af::ref<FloatType, af::mat_grid> matrix_ref_t;                    \
    typedef af::ref_owning_shared<scalar_t> vector_owning_ref_t;              \
    typedef af::shared<scalar_t> vector_t;                                    \
    typedef af::ref<scalar_t> vector_ref_t;


  /// Normal equations for linear and non-linear least-squares
  /** The least-squares target reads

      \f$ L(x) = \| A x - b \|^2 + \sum \|r(x)\|^2\f$

      where the norm is diagonal-weighted

      \f$ \| y \|^2 = \sum_i w_i y_i^2 \f$

      and \f$r(x)\f$ is a vector of residuals.
  */
  template <typename FloatType>
  class normal_equations
  {
  public:
    SCITBX_LSTBX_DECLARE_ARRAY_TYPE(FloatType);

    /// Construct a least-squares problem with the given number of unknowns.
    normal_equations(int n_parameters)
      : n_params(n_parameters),
        normal_matrix_(n_params),
        right_hand_side_(n_params),
        r_sq(0)
    {}

    /// Initialise the least-squares problem with the given normal matrix a
    /// and right hand side b
    normal_equations(symmetric_matrix_t const &a,
                     vector_t const &b)
      : n_params(a.accessor().n),
        normal_matrix_(a),
        right_hand_side_(b),
        r_sq(0)
    {
      SCITBX_ASSERT(a.accessor().n == b.size());
    }

    /// Add the equation \f$ A_{i.}^T x = b_i \f$
    void add_equation(scalar_t b_i,
                      af::const_ref<scalar_t> const &a_row,
                      scalar_t w)
    {
      double *p = normal_matrix_.begin();
      for (int i=0; i<n_params; ++i)  {
        right_hand_side_[i] += w * a_row[i] * b_i;
        for (int j=i; j<n_params; ++j) *p++ += w * a_row[i] * a_row[j];
      }
    }

    /// Add the linearisation of the equation \f$r_i(x) = 0\f$
    void add_equation(scalar_t r, af::const_ref<scalar_t> const &grad_r) {
      r_sq += r*r;
      scalar_t *p = normal_matrix_.begin();
      for (int i=0; i<n_params; ++i) {
        right_hand_side_[i] -= r*grad_r[i];
        for (int j=i; j<n_params; ++j) *p++ += grad_r[i]*grad_r[j];
      }
    }

    /// Reset the state to construction time, i.e. no equations accumulated
    void reset() {
      std::fill(normal_matrix_.begin(), normal_matrix_.end(), scalar_t(0));
      std::fill(right_hand_side_.begin(), right_hand_side_.end(), scalar_t(0));
      r_sq = 0;
    }

    symmetric_matrix_t normal_matrix() {
      return normal_matrix_.array();
    }

    vector_t right_hand_side() {
      return right_hand_side_.array();
    }

  private:
    int n_params;
    scalar_t r_sq;
    symmetric_matrix_owning_ref_t normal_matrix_;
    vector_owning_ref_t right_hand_side_;
  };


  /// Normal equations for least-squares fit with an overall scale.
  /** The least-squares target reads

      \f$ L(K, x) = \sum w ( K y_c(x) - y_o )^2 \f$

      where the both of \f$ y_c(x) \f$ and \f$ y_o \f$ are vectors,
      respectively the model to fit to the data.

      One takes advantage of the separability of the problem:

        - step 1: \f$ K^*(x) = \argmin_K L(K, x) \f$

        - step 2: Build the Newton equations for the problem
                  \f$ \min_x L(K^*(x), x) \f$

          in the Gauss approximation of small residuals.
  */
  template <typename FloatType>
  class normal_equations_separating_scale_factor
  {
  public:
    SCITBX_LSTBX_DECLARE_ARRAY_TYPE(FloatType);

    /// Construct a least-squares problem with the given number of parameters
    /** That is the length of the vector \f$ x \f$ */
    normal_equations_separating_scale_factor(int n_parameters)
      : yo_dot_yc(0), yc_sq(0), sum_w(0),
        n_params(n_parameters),
        a(n_parameters),
        yo_dot_grad_yc(n_parameters),
        yc_dot_grad_yc(n_parameters)
    {}

    /** \brief Add the linearisation of the equation
         \f$y_{c,i} \propto y_{o,i}\f$ with weight w.
     */
    void add_equation(scalar_t yc, af::const_ref<scalar_t> const &grad_yc,
                      scalar_t yo, scalar_t w)
      {
        SCITBX_ASSERT(grad_yc.size() == n_params);
        add_equation(yc, grad_yc.begin(), yo, w);
      }

    /// Overload for when efficiency is paramount.
    void add_equation(scalar_t yc, scalar_t const *grad_yc,
                      scalar_t yo, scalar_t w)
    {
      sum_w += w;
      yo_dot_yc += w * yo * yc;
      yc_sq += w * yc * yc;
      double *pa = a.begin();
      for (int i=0; i<n_params; ++i) for (int j=i; j<n_params; ++j) {
        *pa++ += w * grad_yc[i] * grad_yc[j];
      }
      for (int i=0; i<n_params; ++i) {
        yo_dot_grad_yc[i] += w * yo * grad_yc[i];
        yc_dot_grad_yc[i] += w * yc * grad_yc[i];
      }
    }

    /// The separately optimised value of the scale factor, \f$ K^*(x) \f$
    scalar_t optimised_scale_factor() {
      return yo_dot_yc/yc_sq;
    }

    /// The normal equation for the optimised overall scale factor.
    normal_equations<scalar_t> equations() {
      scalar_t inv_k = 1/optimised_scale_factor();
      scalar_t inv_yc_norm = 1/std::sqrt(yc_sq);
      vector_ref_t alpha = yc_dot_grad_yc.ref();
      vector_owning_ref_t b = yo_dot_grad_yc;
      for (int i=0; i<n_params; ++i) {
        scalar_t yo_dot_grad_yc_i = yo_dot_grad_yc[i];
        scalar_t yc_dot_grad_yc_i = yc_dot_grad_yc[i];
        b[i] = inv_k*yo_dot_grad_yc_i - yc_dot_grad_yc_i;
        alpha[i] = (2*yc_dot_grad_yc_i - inv_k*yo_dot_grad_yc_i)*inv_yc_norm;
      }
      double *pa = a.begin();
      for (int i=0; i<n_params; ++i) for (int j=i; j<n_params; ++j) {
        *pa++ -= alpha[i]*alpha[j];
      }
      return normal_equations<scalar_t>(a.array(), b.array());
    }

    /// Ready this for another computation of the normal equations
    void reset() {
      yo_dot_yc = 0; yc_sq = 0; sum_w = 0;
      std::fill(a.begin(), a.end(), scalar_t(0));
      std::fill(yo_dot_grad_yc.begin(), yo_dot_grad_yc.end(), scalar_t(0));
      std::fill(yc_dot_grad_yc.begin(), yc_dot_grad_yc.end(), scalar_t(0));
    }

  private:
    scalar_t yo_dot_yc, yc_sq, sum_w;
    int n_params;
    symmetric_matrix_owning_ref_t a; // normal matrix stored
                                     // as packed upper diagonal
    vector_owning_ref_t yo_dot_grad_yc;
    vector_owning_ref_t yc_dot_grad_yc;
  };



  /// Normal equations for least-squares with a separable linear part
  /** The least-squares target reads

   \f$ L(a, x) = \sum w ( y_o - Y_c(x) a )

   Thus the model \f$ y_c \f$ fitted to the data \f$ y_o \f$ is the linear
   combination of some \f$ y_{c,1}, \cdots, y_{c,p} \f$ with coefficients
   \f$ a_1, \cdots, a_p \f$.

   The separability of the problem is exploited by

   - first computing \f$ a^* = \argmin_a L(a, x) \f$,

   - and then building the Newton equations for \f$ L(a^*(x), x) \f$
     in the Gauss approximation of small residuals.
   */
  template <typename FloatType>
  class normal_equations_separating_linear_part
  {
  public:
    SCITBX_LSTBX_DECLARE_ARRAY_TYPE(FloatType);

    normal_equations_separating_linear_part(int n_parameters, int n_bases)
      : n(n_parameters), p(n_bases),
        linear_part(p),
        grad_yc_trans_grad_yc(n*(n+1)/2 * p*p),
        yo_trans_grad_yc(af::mat_grid(n,p)),
        yc_trans_grad_yc(n*p*p),
        a(n), b(n),
        has_solved_separable_linear_part(false)
    {}

    void add_equation(af::const_ref<scalar_t> const &yc,
                      af::const_ref<scalar_t, af::mat_grid> const &grad_yc,
                      scalar_t yo, scalar_t w)
    {
      sum_w += w;
      linear_part.add_equation(yo, yc, w);

      double *q = grad_yc_trans_grad_yc.begin();
      for (int i=0; i<n; ++i) for (int j=i; j<n; ++j) {
        for (int k=0; k<p; ++k) for (int l=0; l<p; ++l) {
          *q++ += w * grad_yc(i,k) * grad_yc(j,l);
        }
      }

      double *yo_tr_grad_yc = yo_trans_grad_yc.begin();
      double *yc_tr_grad_yc = yc_trans_grad_yc.begin();
      for (int i=0; i<n; ++i) {
        for (int k=0; k<p; ++k) {
          *yo_tr_grad_yc++ += w * yo * grad_yc(i,k);
          for (int l=0; l<p; ++l) {
            *yc_tr_grad_yc++ += w * yc(k) * grad_yc(i,l);
          }
        }
      }
    }

    vector_t optimal_linear_coefficients() {
      if(!has_solved_separable_linear_part) optimise_separable_linear_part();
      return a_star.array();
    }

    normal_equations<scalar_t> equations() {
      using namespace scitbx::matrix;
      if(!has_solved_separable_linear_part) optimise_separable_linear_part();

      int sym_p = p*(p+1)/2;
      scalar_t *a_star_ = a_star.begin();
      scalar_t *alpha0 = yo_trans_grad_yc.begin();

      scalar_t *alpha = alpha0;
      scalar_t *yc_tr_grad_yc = yc_trans_grad_yc.begin();
      for (int i=0; i<n; ++i, yc_tr_grad_yc += p*p, alpha += p)
      {
        scalar_t *beta = alpha;
        matrix_vector(p, p, yc_tr_grad_yc, a_star_, beta, -1., 1.);
        b[i] = dot(p, a_star_, beta);
        matrix_transposed_vector(p, p, yc_tr_grad_yc, a_star_, alpha, -1., 1.);
        forward_substitution_given_transpose(p, lin_u.begin(), alpha);
      }

      scalar_t *a_ = a.begin();
      alpha = alpha0;
      scalar_t *grad_yc_tr_grad_yc = grad_yc_trans_grad_yc.begin();
      for (int i=0; i<n; ++i) for (int j=i; j<n; ++j) {
        scalar_t a_ij = quadratic_form(p, grad_yc_tr_grad_yc, a_star_)
                        -dot(p, &alpha[i*p], &alpha[j*p]);
        *a_++ = a_ij;
        grad_yc_tr_grad_yc += p*p;
      }

      return normal_equations<scalar_t>(a.array(), b.array());
    }

  private:
    void optimise_separable_linear_part() {
      using namespace scitbx::matrix;
      symmetric_matrix_owning_ref_t lin_a = linear_part.normal_matrix();
      vector_owning_ref_t lin_b = linear_part.right_hand_side();
      cholesky::u_transpose_u_decomposition_in_place<scalar_t> chol(lin_a);
      SCITBX_ASSERT(!chol.failure);
      lin_u = lin_a.array();
      cholesky::solve_in_place::using_u_transpose_u(lin_u, lin_b);
      a_star = lin_b.array();
      has_solved_separable_linear_part = true;
    }

    int n;
    int p;

    normal_equations<scalar_t> linear_part;

    scalar_t sum_w;
    af::ref_owning_shared<scalar_t> grad_yc_trans_grad_yc;
    matrix_owning_ref_t yo_trans_grad_yc;
    af::ref_owning_shared<scalar_t> yc_trans_grad_yc;

    vector_owning_ref_t b;
    symmetric_matrix_owning_ref_t a;

    bool has_solved_separable_linear_part;
    symmetric_matrix_owning_ref_t lin_u;
    vector_owning_ref_t a_star;
  };



}}

#endif // GUARD
