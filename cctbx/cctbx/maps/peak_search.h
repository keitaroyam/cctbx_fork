// $Id$
/* Copyright (c) 2001 The Regents of the University of California through
   E.O. Lawrence Berkeley National Laboratory, subject to approval by the
   U.S. Department of Energy. See files COPYRIGHT.txt and
   cctbx/LICENSE.txt for further details.

   Revision history:
     Jan 2002: Created (R.W. Grosse-Kunstleve)
 */

#ifndef CCTBX_MAPS_PEAK_SEARCH_H
#define CCTBX_MAPS_PEAK_SEARCH_H

namespace cctbx { namespace maps {

  /*
    requirements:
      physical dimensions of maps are equal to generic dimensions
      dimensions of data and flags are equal

    flags:
      on input: < 0: independent grid point
                >= 0: dependent grid point,
                      flag is 1d-index of corresponding independent grid point
      on output: -1: independent, not a peak
                 -2: independent, peak
                 flags for dependent grid points are unchanged

    level = 1: compare to the 6 nearest neighbors
          = 2: also compare to the 12 second-nearest neighbors
          > 2: also compare to the 8 third-nearest neighbors
  */
  template <typename VecRefNdDataType,
            typename VecRefNdFlagsType>
  void peak_search_p1(const VecRefNdDataType& data,
                      VecRefNdFlagsType& flags,
                      int level)
  {
    typedef typename VecRefNdDataType::value_type data_value_type;
    typedef typename VecRefNdFlagsType::value_type flags_value_type;

    data_value_type* pdata = data.begin();
    flags_value_type* pflags = flags.begin();
    int Nx = data.dim()[0];
    int Ny = data.dim()[1];
    int Nz = data.dim()[2];
    int       nk =           Nz;
    int    nj_nk =      Ny * Nz;
    int ni_nj_nk = Nx * Ny * Nz;

    int im, jm, km;
    int i0, j0, k0;
    int ip, jp, kp;
    int ibreak, jbreak, kbreak;

    // reset flags for independent grid points
    for (int i = 0; i < ni_nj_nk; i++) {
      if (pflags[i] < 0) pflags[i] = -1;
    }

    data_value_type* pd = pdata;
    flags_value_type* pf = pflags;
    im = ni_nj_nk - nj_nk;
    i0 = 0;
    ip = nj_nk;
    ibreak = ni_nj_nk;
    while (ip < ibreak) {
      jm = nj_nk - nk;
      j0 = 0;
      jp = nk;
      jbreak = nj_nk;
      while (jp < jbreak) {
        km = nk - 1;
        k0 = 0;
        kp = 1;
        kbreak = nk;
        while (kp < kbreak) {
          flags_value_type* indep_pf;
          if (*pf < 0) indep_pf = pf;
          else         indep_pf = &pflags[*pf];
          while (! (*indep_pf < -1)) {
            if (level >= 1) {
              /* m00 0m0 00m
                 p00 0p0 00p
               */
              if (*pd < pdata[im + j0 + k0]) break;
              if (*pd < pdata[ip + j0 + k0]) break;
              if (*pd < pdata[i0 + jm + k0]) break;
              if (*pd < pdata[i0 + jp + k0]) break;
              if (*pd < pdata[i0 + j0 + km]) break;
              if (*pd < pdata[i0 + j0 + kp]) break;
              if (level >= 2) {
                /* mm0 m0m 0mm mp0 m0p 0mp
                   pp0 p0p 0pp pm0 p0m 0pm
                 */
                if (*pd < pdata[im + jm + k0]) break;
                if (*pd < pdata[ip + jp + k0]) break;
                if (*pd < pdata[im + j0 + km]) break;
                if (*pd < pdata[ip + j0 + kp]) break;
                if (*pd < pdata[i0 + jm + km]) break;
                if (*pd < pdata[i0 + jp + kp]) break;
                if (*pd < pdata[im + jp + k0]) break;
                if (*pd < pdata[ip + jm + k0]) break;
                if (*pd < pdata[im + j0 + kp]) break;
                if (*pd < pdata[ip + j0 + km]) break;
                if (*pd < pdata[i0 + jm + kp]) break;
                if (*pd < pdata[i0 + jp + km]) break;
                if (level >= 3) {
                  /* mmm mmp mpm mpp
                     ppp ppm pmp pmm
                   */
                  if (*pd < pdata[im + jm + km]) break;
                  if (*pd < pdata[ip + jp + kp]) break;
                  if (*pd < pdata[im + jm + kp]) break;
                  if (*pd < pdata[ip + jp + km]) break;
                  if (*pd < pdata[im + jp + km]) break;
                  if (*pd < pdata[ip + jm + kp]) break;
                  if (*pd < pdata[im + jp + kp]) break;
                  if (*pd < pdata[ip + jm + km]) break;
                }
              }
            }
            *indep_pf = -2;
            break;
          }
          pd++;
          pf++;
          km = k0;
          k0 = kp;
          kp++;
          if (kp == nk) { kp = 0; kbreak = 1; }
        }
        jm = j0;
        j0 = jp;
        jp += nk;
        if (jp == nj_nk) { jp = 0; jbreak = nk; }
      }
      im = i0;
      i0 = ip;
      ip += nj_nk;
      if (ip == ni_nj_nk) { ip = 0; ibreak = nj_nk; }
    }
  }

}} // namespace phenix::maps

#endif // CCTBX_MAPS_PEAK_SEARCH_H
