// $Id$
/* Copyright (c) 2001 The Regents of the University of California through
   E.O. Lawrence Berkeley National Laboratory, subject to approval by the
   U.S. Department of Energy. See files COPYRIGHT.txt and
   cctbx/LICENSE.txt for further details.

   Revision history:
     2001 Oct 11: Created (R.W. Grosse-Kunstleve)
 */

/*! \file
    Toolbox for the handling of anisotropic displacement parameters.
 */

#ifndef CCTBX_ADPTBX_H
#define CCTBX_ADPTBX_H

#include <cctbx/uctbx.h>

//! ADP Toolbox namespace.
namespace adptbx {

  using namespace cctbx;

  const double   TwoPiSquared = 2. * constants::pi * constants::pi;
  const double EightPiSquared = 8. * constants::pi * constants::pi;

  template <class FloatType>
  struct return_type {};

  template <class FloatType6, class FloatType33>
  boost::array<FloatType33, 3*3>
  Xaniso_as_SymMx33(const boost::array<FloatType6, 6>& Xaniso,
                    return_type<FloatType33> t)
  {
    boost::array<FloatType33, 3*3> M;
    M[0] = Xaniso[0];
    M[1] = Xaniso[3];
    M[2] = Xaniso[4];
    M[3] = Xaniso[3];
    M[4] = Xaniso[1];
    M[5] = Xaniso[5];
    M[6] = Xaniso[4];
    M[7] = Xaniso[5];
    M[8] = Xaniso[2];
    return M;
  }

  template <class FloatType33, class FloatType6>
  inline boost::array<FloatType6, 6>
  SymMx33_as_Xaniso(const boost::array<FloatType33, 3*3>& M,
                    return_type<FloatType6> t)
  {
    boost::array<FloatType6, 6> Xaniso;
    Xaniso[0] = M[0];
    Xaniso[1] = M[4];
    Xaniso[2] = M[8];
    Xaniso[3] = M[1];
    Xaniso[4] = M[2];
    Xaniso[5] = M[5];
    return Xaniso;
  }

  template <class FloatType>
  boost::array<FloatType, 9>
  A_X_At(const boost::array<FloatType, 9>& A,
         const boost::array<FloatType, 9>& X)
  {
    boost::array<FloatType, 9> AX;
    MatrixLite::multiply<FloatType>(A.elems, X.elems, 3, 3, 3, AX.elems);
    boost::array<FloatType, 9> At;
    MatrixLite::transpose<FloatType>(A.elems, 3, 3, At.elems);
    boost::array<FloatType, 9> AXAt;
    MatrixLite::multiply<FloatType>(AX.elems, At.elems, 3, 3, 3, AXAt.elems);
    return AXAt;
  }

  template <class FloatType>
  inline boost::array<FloatType, 6>
  A_Xaniso_At(const uctbx::Mx33& A, const boost::array<FloatType, 6>& Xaniso)
  {
    boost::array<FloatType, 9>
    X = Xaniso_as_SymMx33(Xaniso, return_type<FloatType>());
    return SymMx33_as_Xaniso(A_X_At(A, X), return_type<FloatType>());
  }

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
  template <class FloatType>
  boost::array<FloatType, 6>
  Ucart_as_Ustar(const uctbx::UnitCell& uc,
                 const boost::array<FloatType, 6>& Ucart) {
    return A_Xaniso_At(uc.getFractionalizationMatrix(), Ucart);
  }
  //! Convert anisotropic adp Ustar -> Ucart.
  template <class FloatType>
  boost::array<FloatType, 6>
  Ustar_as_Ucart(const uctbx::UnitCell& uc,
                 const boost::array<FloatType, 6>& Ustar) {
    return A_Xaniso_At(uc.getOrthogonalizationMatrix(), Ustar);
  }

  //! Convert Uuvrs -> Uiso.
  // From Xtal 3.7.1 source code.
  template <class FloatType>
  inline FloatType
  Uuvrs_as_Uiso(const uctbx::UnitCell& uc,
                const boost::array<FloatType, 6>& Uuvrs)
  {
    const uctbx::Vec3&   Len = uc.getLen(false);
    const uctbx::Vec3& R_Len = uc.getLen(true);
    const uctbx::Vec3& cosAng = uc.get_cosAng(false);
    FloatType Uiso = 0.;
    FloatType LRL[3];
    for(std::size_t i=0;i<3;i++) {
      LRL[i] = Len[i] * R_Len[i];
      Uiso += Uuvrs[i] * LRL[i] * LRL[i];
    }
    Uiso += Uuvrs[3] * 2. * LRL[0] * LRL[1] * cosAng[2];
    Uiso += Uuvrs[4] * 2. * LRL[0] * LRL[2] * cosAng[1];
    Uiso += Uuvrs[5] * 2. * LRL[1] * LRL[2] * cosAng[0];
    return Uiso / 3.;
  }
  //! Convert Uiso -> Uuvrs.
  // From Xtal 3.7.1 source code.
  template <class FloatType>
  inline boost::array<FloatType, 6>
  Uiso_as_Uuvrs(const uctbx::UnitCell& uc,
                const FloatType& Uiso)
  {
    const uctbx::Vec3& R_cosAng = uc.get_cosAng(true);
    boost::array<FloatType, 6> Uuvrs;
    Uuvrs.assign(Uiso);
    Uuvrs[3] *= R_cosAng[2];
    Uuvrs[4] *= R_cosAng[1];
    Uuvrs[5] *= R_cosAng[0];
    return Uuvrs;
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

  //! Test if adp tensor is positive definite.
  /*! Necessary and sufficient conditions for positive-definiteness
      are:
      <p>
      det(U) > 0<br>
      Uii > 0<br>
      Uii Uij > 0 for i,j=1,2,3
      <p>
      If the above conditions are violated then atomic
      displacements could be described by imaginary
      ellipsoids or by paraboloids or hyperboloids,
      with the obvious meaning that the experimental
      data are not of sufficient accuracy to
      justify the use of anisotropic displacement
      parameters.
      (Giacovazzo, Fundamentals of Crystallography 1992,
      p. 188-189).
   */
  template <class FloatType>
  bool
  isPositiveDefinite_adpTensor(const boost::array<FloatType, 6>& adp)
  {
    for(std::size_t i=0;i<6;i++) {
      if (adp[i] <= 0.) return false;
    }
    FloatType
    det =  adp[0] * (adp[1] * adp[2] - adp[5] * adp[5]);
    det -= adp[3] * (adp[3] * adp[2] - adp[5] * adp[4]);
    det += adp[4] * (adp[3] * adp[5] - adp[1] * adp[4]);
    if (det < 0.) return false;
    return true;
  }

  template <class FloatType>
  boost::array<FloatType, 3>
  EigenValues(const boost::array<FloatType, 6>& adp)
  {
    // normal form: x^3 + r x^2 + s x + t == 0
    FloatType r = -adp[0] - adp[1] - adp[2];
    FloatType s =   adp[0] * adp[1] + adp[0] * adp[2] + adp[1] * adp[2]
                  - adp[3] * adp[3] - adp[4] * adp[4] - adp[5] * adp[5];
    FloatType t =   adp[0] * adp[5] * adp[5] - adp[0] * adp[1] * adp[2]
                  + adp[2] * adp[3] * adp[3] + adp[1] * adp[4] * adp[4]
                  - 2 * adp[3] * adp[4] * adp[5];
    // reduced form: y^3 + p y + q == 0
    FloatType p = s - r * r / 3.;
    FloatType q = 2. * r * r * r / 27. - r * s / 3. + t;
    FloatType p3 = p * p * p;
    FloatType q2 = q * q;
    FloatType D = p3 / 27. + q2 / 4.;
    if (D >= 0.) throw error("adp tensor is not positive definite.");
    FloatType zeta = std::sqrt(-p3 / 27);
    FloatType phi = std::acos(-q / (2. * zeta));
    FloatType rzeta = 2. * std::pow(zeta, FloatType(1/3.));
    boost::array<FloatType, 3> result;
    for (int i = 0; i < 3; i++) {
      result[i] =   rzeta * std::cos((phi + (i * 2) * constants::pi) / 3.)
                  - r / 3.;
    }
    return result;
  }

} // namespace adptbx

#endif // CCTBX_ADPTBX_H
