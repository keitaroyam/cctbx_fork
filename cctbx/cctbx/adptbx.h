// $Id$
/* Copyright (c) 2001 The Regents of the University of California through
   E.O. Lawrence Berkeley National Laboratory, subject to approval by the
   U.S. Department of Energy. See files COPYRIGHT.txt and
   cctbx/LICENSE.txt for further details.

   Revision history:
     2001 Oct 11: Created (R.W. Grosse-Kunstleve)
 */

/*! \file
    Toolbox for the handling of atomic displacement parameters (adp).
 */

#ifndef CCTBX_ADPTBX_H
#define CCTBX_ADPTBX_H

#include <complex>
#include <cctbx/uctbx.h>

//! ADP Toolbox namespace.
namespace adptbx {

  using namespace cctbx;

  static const error
    not_positive_definite("anisotropic adp tensor is not positive definite.");

  const double   TwoPiSquared = 2. * constants::pi * constants::pi;
  const double EightPiSquared = 8. * constants::pi * constants::pi;

  //! Convert isotropic adp U -> B.
  inline double
  U_as_B(double Uiso) {
    return Uiso * EightPiSquared;
  }
  //! Convert isotropic adp B -> U.
  inline double
  B_as_U(double Biso) {
    return Biso / EightPiSquared;
  }
  //! Convert anisotropic adp U -> B.
  template <class FloatType>
  boost::array<FloatType, 6>
  U_as_B(const boost::array<FloatType, 6>& Uaniso) {
    return EightPiSquared * Uaniso;
  }
  //! Convert anisotropic adp B -> U.
  template <class FloatType>
  boost::array<FloatType, 6>
  B_as_U(const boost::array<FloatType, 6>& Baniso) {
    return (1. / EightPiSquared) * Baniso;
  }

  //! Convert anisotropic adp Uuvrs -> Ustar.
  /*! The transformation matrix used is:<pre>
              (a*  0  0)
          C = ( 0 b*  0)
              ( 0  0 c*)</pre>
      The formula for the transformation is Ustar = C Uuvrs Ct,
      where Ct is the transposed of C. In this particular case
      the expression simplifies to:<pre>
          Ustar11 = a*^2  Uuvrs11
          Ustar22 = b*^2  Uuvrs22
          Ustar33 = c*^2  Uuvrs33
          Ustar12 = a* b* Uuvrs12
          Ustar13 = a* c* Uuvrs13
          Ustar23 = b* c* Uuvrs23</pre>
   */
  template <class FloatType>
  boost::array<FloatType, 6>
  Uuvrs_as_Ustar(const uctbx::UnitCell& uc,
                 const boost::array<FloatType, 6>& Uuvrs) {
    const uctbx::Vec3& R_Len = uc.getLen(true);
    boost::array<FloatType, 6> Ustar;
    Ustar[0] = Uuvrs[0] * (R_Len[0] * R_Len[0]);
    Ustar[1] = Uuvrs[1] * (R_Len[1] * R_Len[1]);
    Ustar[2] = Uuvrs[2] * (R_Len[2] * R_Len[2]);
    Ustar[3] = Uuvrs[3] * (R_Len[0] * R_Len[1]);
    Ustar[4] = Uuvrs[4] * (R_Len[0] * R_Len[2]);
    Ustar[5] = Uuvrs[5] * (R_Len[1] * R_Len[2]);
    return Ustar;
  }
  //! Convert anisotropic adp Ustar -> Uuvrs.
  /*! Inverse of Uuvrs_as_Ustar().
   */
  template <class FloatType>
  boost::array<FloatType, 6>
  Ustar_as_Uuvrs(const uctbx::UnitCell& uc,
                 const boost::array<FloatType, 6>& Ustar) {
    const uctbx::Vec3& R_Len = uc.getLen(true);
    boost::array<FloatType, 6> Uuvrs;
    Uuvrs[0] = Ustar[0] / (R_Len[0] * R_Len[0]);
    Uuvrs[1] = Ustar[1] / (R_Len[1] * R_Len[1]);
    Uuvrs[2] = Ustar[2] / (R_Len[2] * R_Len[2]);
    Uuvrs[3] = Ustar[3] / (R_Len[0] * R_Len[1]);
    Uuvrs[4] = Ustar[4] / (R_Len[0] * R_Len[2]);
    Uuvrs[5] = Ustar[5] / (R_Len[1] * R_Len[2]);
    return Uuvrs;
  }

  //! Convert anisotropic adp Ucart -> Ustar.
  /*! The transformation matrix C used is the orthogonalization
      matrix for the given UnitCell.
      The formula for the transformation is Ustar = C Ucart Ct,
      where Ct is the transposed of C.
   */
  template <class FloatType>
  inline boost::array<FloatType, 6>
  Ucart_as_Ustar(const uctbx::UnitCell& uc,
                 const boost::array<FloatType, 6>& Ucart) {
    return MatrixLite::CondensedTensorTransformation(
      uc.getFractionalizationMatrix(), Ucart);
  }
  //! Convert anisotropic adp Ustar -> Ucart.
  /*! Inverse of Ucart_as_Ustar(). I.e., the transformation matrix
      C used is the fractionalization matrix for the given
      UnitCell.
      The formula for the transformation is Ucart = C Ustar Ct,
      where Ct is the transposed of C.
   */
  template <class FloatType>
  inline boost::array<FloatType, 6>
  Ustar_as_Ucart(const uctbx::UnitCell& uc,
                 const boost::array<FloatType, 6>& Ustar) {
    return MatrixLite::CondensedTensorTransformation(
      uc.getOrthogonalizationMatrix(), Ustar);
  }

  //! Convert anisotropic adp Ucart -> Uuvrs.
  /*! This is implemented without a significant loss of efficiency
      as Ustar_as_Uuvrs(uc, Ucart_as_Ustar(uc, Ucart)).
   */
  template <class FloatType>
  inline boost::array<FloatType, 6>
  Ucart_as_Uuvrs(const uctbx::UnitCell& uc,
                 const boost::array<FloatType, 6>& Ucart) {
    return Ustar_as_Uuvrs(uc, Ucart_as_Ustar(uc, Ucart));
  }
  //! Convert anisotropic adp Uuvrs -> Ucart.
  /*! This is implemented without a significant loss of efficiency
      as Ustar_as_Ucart(uc, Uuvrs_as_Ustar(uc, Uuvrs)).
   */
  template <class FloatType>
  inline boost::array<FloatType, 6>
  Uuvrs_as_Ucart(const uctbx::UnitCell& uc,
                 const boost::array<FloatType, 6>& Uuvrs) {
    return Ustar_as_Ucart(uc, Uuvrs_as_Ustar(uc, Uuvrs));
  }

  //! Convert anisotropic adp Ustar -> beta.
  /*! The elements of Ustar are multiplied by 2pi^2.
   */
  template <class FloatType>
  inline boost::array<FloatType, 6>
  Ustar_as_beta(const boost::array<FloatType, 6>& Ustar) {
    return TwoPiSquared * Ustar;
  }
  //! Convert anisotropic adp beta -> Ustar.
  /*! The elements of beta are divided by 2pi^2.
   */
  template <class FloatType>
  inline boost::array<FloatType, 6>
  beta_as_Ustar(const boost::array<FloatType, 6>& beta) {
    return beta / TwoPiSquared;
  }

  //! Convert anisotropic adp Ucart -> beta.
  /*! This is implemented as Ustar_as_beta(Ucart_as_Ustar(uc, Ucart)).
   */
  template <class FloatType>
  inline boost::array<FloatType, 6>
  Ucart_as_beta(const uctbx::UnitCell& uc,
                const boost::array<FloatType, 6>& Ucart) {
    return Ustar_as_beta(Ucart_as_Ustar(uc, Ucart));
  }
  //! Convert anisotropic adp beta -> Ucart.
  /*! This is implemented as Ustar_as_Ucart(uc, beta_as_Ustar(beta)).
   */
  template <class FloatType>
  inline boost::array<FloatType, 6>
  beta_as_Ucart(const uctbx::UnitCell& uc,
                const boost::array<FloatType, 6>& beta) {
    return Ustar_as_Ucart(uc, beta_as_Ustar(beta));
  }

  //! Convert anisotropic adp Uuvrs -> beta.
  /*! This is implemented as Ustar_as_beta(Uuvrs_as_Ustar(uc, Uuvrs)).
   */
  template <class FloatType>
  inline boost::array<FloatType, 6>
  Uuvrs_as_beta(const uctbx::UnitCell& uc,
                const boost::array<FloatType, 6>& Uuvrs) {
    return Ustar_as_beta(Uuvrs_as_Ustar(uc, Uuvrs));
  }
  //! Convert anisotropic adp beta -> Uuvrs.
  /*! This is implemented as Ustar_as_Uuvrs(uc, beta_as_Ustar(beta)).
   */
  template <class FloatType>
  inline boost::array<FloatType, 6>
  beta_as_Uuvrs(const uctbx::UnitCell& uc,
                const boost::array<FloatType, 6>& beta) {
    return Ustar_as_Uuvrs(uc, beta_as_Ustar(beta));
  }

  //! Convert Ucart -> Uiso.
  /*! Uiso is defined as the mean of the diagonal elements of Ucart:<pre>
          Uiso = 1/3 (Ucart11 + Ucart22 + Ucart33)</pre>
   */
  template <class FloatType>
  inline FloatType
  Ucart_as_Uiso(const boost::array<FloatType, 6>& Ucart)
  {
    return (Ucart[0] + Ucart[1] + Ucart[2]) / 3.;
  }
  //! Convert Uiso -> Ucart.
  /*! The diagonal elements of Ucart are set to the value of Uiso.
      The off-diagonal components Ucart are set to zero.
   */
  template <class FloatType>
  boost::array<FloatType, 6>
  Uiso_as_Ucart(const FloatType& Uiso)
  {
    boost::array<FloatType, 6> result;
    result.assign(0.);
    for(std::size_t i=0;i<3;i++) result[i] = Uiso;
    return result;
  }

  //! Convert Uuvrs -> Uiso.
  /*! This is implemented as Ucart_as_Uiso(Uuvrs_as_Ucart(uc, Uuvrs)).
   */
  template <class FloatType>
  inline FloatType
  Uuvrs_as_Uiso(const uctbx::UnitCell& uc,
                const boost::array<FloatType, 6>& Uuvrs)
  {
    return Ucart_as_Uiso(Uuvrs_as_Ucart(uc, Uuvrs));
  }
  //! Convert Uiso -> Uuvrs.
  /*! This is implemented as Ucart_as_Uuvrs(uc, Uiso_as_Ucart(Uiso)).
   */
  template <class FloatType>
  inline boost::array<FloatType, 6>
  Uiso_as_Uuvrs(const uctbx::UnitCell& uc,
                const FloatType& Uiso)
  {
    return Ucart_as_Uuvrs(uc, Uiso_as_Ucart(Uiso));
  }

  //! Isotropic Debye-Waller factor given (sin(theta)/lambda)^2 and Biso.
  inline double
  DebyeWallerFactorBiso(double stol2,
                        double Biso)
  {
    return std::exp(-Biso * stol2);
  }
  //! Isotropic Debye-Waller factor given (sin(theta)/lambda)^2 and Uiso.
  inline double
  DebyeWallerFactorUiso(double stol2,
                        double Uiso)
  {
    return DebyeWallerFactorBiso(stol2, U_as_B(Uiso));
  }
  //! Isotropic Debye-Waller factor given Miller index and Biso.
  inline double
  DebyeWallerFactorBiso(const uctbx::UnitCell& uc,
                        const Miller::Index& MIx,
                        double Biso)
  {
    return DebyeWallerFactorBiso(uc.Q(MIx) / 4., Biso);
  }
  //! Isotropic Debye-Waller factor given Miller index and Uiso.
  inline double
  DebyeWallerFactorUiso(const uctbx::UnitCell& uc,
                        const Miller::Index& MIx,
                        double Uiso)
  {
    return DebyeWallerFactorBiso(uc, MIx, U_as_B(Uiso));
  }

  //! Anisotropic Debye-Waller factor given Miller index and Ustar.
  template <class FloatType>
  inline FloatType
  DebyeWallerFactorUstar(const Miller::Index& MIx,
                         const boost::array<FloatType, 6>& Ustar)
  {
    return std::exp(-TwoPiSquared * (
        (MIx[0] * MIx[0]) * Ustar[0]
      + (MIx[1] * MIx[1]) * Ustar[1]
      + (MIx[2] * MIx[2]) * Ustar[2]
      + (2 * MIx[0] * MIx[1]) * Ustar[3]
      + (2 * MIx[0] * MIx[2]) * Ustar[4]
      + (2 * MIx[1] * MIx[2]) * Ustar[5]));
  }

  //! Anisotropic Debye-Waller factor given Miller index and beta.
  template <class FloatType>
  inline FloatType
  DebyeWallerFactor_beta(const Miller::Index& MIx,
                         const boost::array<FloatType, 6>& beta)
  {
    return std::exp(-(
        (MIx[0] * MIx[0]) * beta[0]
      + (MIx[1] * MIx[1]) * beta[1]
      + (MIx[2] * MIx[2]) * beta[2]
      + (2 * MIx[0] * MIx[1]) * beta[3]
      + (2 * MIx[0] * MIx[2]) * beta[4]
      + (2 * MIx[1] * MIx[2]) * beta[5]));
  }

  //! Anisotropic Debye-Waller factor given Miller index and Uuvrs.
  template <class FloatType>
  inline FloatType
  DebyeWallerFactorUuvrs(const uctbx::UnitCell& uc,
                         const Miller::Index& MIx,
                         const boost::array<FloatType, 6>& Uuvrs)
  {
    return DebyeWallerFactorUstar(MIx, Uuvrs_as_Ustar(uc, Uuvrs));
  }
  //! Anisotropic Debye-Waller factor given Miller index and Ucart.
  template <class FloatType>
  inline FloatType
  DebyeWallerFactorUcart(const uctbx::UnitCell& uc,
                         const Miller::Index& MIx,
                         const boost::array<FloatType, 6>& Ucart)
  {
    return DebyeWallerFactorUstar(MIx, Ucart_as_Ustar(uc, Ucart));
  }

  //! Determine the eigenvalues of the anisotropic adp tensor.
  /*! Since the anisotropic adp tensor is a symmetric matrix, all
      eigenvalues are real. The eigenvalues lambda are determined
      as the three real roots of the cubic equation
      <p>
          |(adp - lambda * I)| = 0
      <p>
      where I is the identity matrix. The solution is
      obtained analytically using Cardan's formula.
      Detailed comments are embedded in the source code.
      <p>
      An exception is thrown if the cubic equation has
      roots that are negative or zero. This indicates that
      the anisotropic adp tensor is not positive definite.
   */
  template <class FloatType>
  boost::array<FloatType, 3>
  Eigenvalues(const boost::array<FloatType, 6>& adp)
  {
    /* The eigenvalues lambda are found by:
         1. Determining the elements of the matrix (adp - lambda * I),
            where I is the identity matrix.
         2. Computing the determinant of that matrix as a function
            of lambda. This results in a cubic equation.
         3. Finding the real roots of the cubic equation with
            Cardan's formula, taken from Taschenbuch der Mathematik
            by Bronstein & Semendjajew (p. 183 in the reprint of
            the 20th edition from 1983).
    */
    /* Mathematica code used to generate the coefficients of the
       "normal form" of the cubic equation:
         U={{adp0,adp3,adp4},{adp3,adp1,adp5},{adp4,adp5,adp2}}
         L={{lambda,0,0},{0,lambda,0},{0,0,lambda}}
         Det[U-L]*(-1)
         CForm[Det[U-L]*(-1)]
     */
    // normal form: x^3 + r x^2 + s x + t == 0
    FloatType r = -adp[0] - adp[1] - adp[2];
    FloatType s =   adp[0] * adp[1] + adp[0] * adp[2] + adp[1] * adp[2]
                  - adp[3] * adp[3] - adp[4] * adp[4] - adp[5] * adp[5];
    FloatType t =   adp[0] * adp[5] * adp[5] - adp[0] * adp[1] * adp[2]
                  + adp[2] * adp[3] * adp[3] + adp[1] * adp[4] * adp[4]
                  - 2 * adp[3] * adp[4] * adp[5];
    /* "Reduced form" of the cubic equation according to
       Taschenbuch der Mathematik.
     */
    // reduced form: y^3 + p y + q == 0
    FloatType p = s - r * r / 3.;
    FloatType q = 2. * r * r * r / 27. - r * s / 3. + t;
    // to circumvent numerical instabilities due to rounding errors the
    // roots are determined as complex numbers.
    std::complex<FloatType> D(p * p * p / 27. + q * q / 4.);
    std::complex<FloatType> sqrtD = std::sqrt(D);
    FloatType mq2 = -q / 2.;
    std::complex<FloatType> u = std::pow(mq2 + sqrtD, 1/3.);
    std::complex<FloatType> v = std::pow(mq2 - sqrtD, 1/3.);
    std::complex<FloatType> epsilon1(-0.5, std::sqrt(3.) * 0.5);
    std::complex<FloatType> epsilon2 = std::conj(epsilon1);
    // since the adp tensor is a symmetric matrix, all the imaginary
    // components of the roots must be zero.
    boost::array<FloatType, 3> result;
    result[0] = (u + v).real();
    result[1] = (epsilon1 * u + epsilon2 * v).real();
    result[2] = (epsilon2 * u + epsilon1 * v).real();
    for(std::size_t i = 0;i<3;i++) {
      // convert the solutions y of the reduced form to the
      // solutions x of the normal form.
      result[i] -= r / 3.;
      if (result[i] <= 0.) throw not_positive_definite;
    }
    return result;
  }

  namespace detail {

    template <class FloatType>
    boost::array<FloatType, 3>
    recursively_multiply(const boost::array<FloatType, 9>& M,
                         boost::array<FloatType, 3> V,
                         FloatType tolerance = 1.e-6)
    {
      unsigned int RunAwayCounter = 0;
      for (;;) {
        boost::array<FloatType, 3> MV;
        MatrixLite::multiply<FloatType>(M.elems, V.elems, 3, 3, 1, MV.elems);
        FloatType abs_lambda = std::sqrt(MV * MV);
        if (abs_lambda == 0.) return MV;
        MV = MV / abs_lambda;
        boost::array<FloatType, 3> absMV = boost::array_abs(MV);
        std::size_t iMax = boost::array_max_index(absMV);
        FloatType scaled_tolerance = absMV[iMax] * tolerance;
        bool converged = MatrixLite::approx_equal(MV, V, scaled_tolerance);
        if (!converged && MatrixLite::approx_equal(MV, -V, scaled_tolerance)) {
          throw not_positive_definite; // lambda < 0
        }
        V = MV;
        if (converged) break;
        RunAwayCounter++;
        if (RunAwayCounter > 10000000) throw cctbx_internal_error();
      }
      return V;
    }

  } // namespace detail

  //! Determine the eigenvectors of the anisotropic adp tensor.
  /*! Since the anisotropic adp tensor is a symmetric matrix, all
      eigenvalues lambda are real and the eigenvectors can
      be chosen orthonormal.
      <p>
      The eigenvectors are determined according to the procedure
      outlined in J.F. Nye, Physical Properties of Crystals,
      Oxford Science Publications, 1992, pp.165-168.
      The given tolerance is used to determine convergence.
      <p>
      An exception is thrown if any of the eigenvalues is
      less than or equal to zero. This indicates that the
      anisotropic adp tensor is not positive definite.
   */
  template <class FloatType>
  boost::array<boost::array<FloatType, 3>, 3>
  Eigenvectors(const boost::array<FloatType, 6>& adp, double tolerance = 1.e-6)
  {
    boost::array<FloatType, 9> M[2];
    M[0] = MatrixLite::CondensedSymMx33_as_FullSymMx33(adp,
           MatrixLite::return_type<FloatType>());
    FloatType d = MatrixLite::Determinant(M[0]);
    if (d == 0.) {
      throw not_positive_definite;
    }
    M[1] = MatrixLite::CoFactorMxTp(M[0]) / d;
    std::size_t iLarge[2];
    boost::array<boost::array<FloatType, 3>, 3> result;
    for(std::size_t iM=0;iM<2;iM++) {
      boost::array<FloatType, 3>
      absDiag = boost::array_abs(MatrixLite::DiagonalElements(M[iM]));
      iLarge[iM] = boost::array_max_index(absDiag);
      if (iM != 0 && iLarge[1] == iLarge[0]) {
        absDiag[iLarge[1]] = -1.;
        iLarge[1] = boost::array_max_index(absDiag);
        cctbx_assert(iLarge[1] != iLarge[0]);
      }
      boost::array<FloatType, 3> V;
      V.assign(0.);
      V[iLarge[iM]] = 1.;
      result[iM] = detail::recursively_multiply(M[iM], V);
      if (result[iM] * result[iM] == 0.) {
        throw not_positive_definite;
      }
    }
    result[2] = MatrixLite::cross_product(result[0], result[1]);
    cctbx_assert(result[2] * result[2] != 0.);
    return result;
  }

} // namespace adptbx

#endif // CCTBX_ADPTBX_H
