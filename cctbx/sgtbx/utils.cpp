// $Id$
/* Copyright (c) 2001 The Regents of the University of California through
   E.O. Lawrence Berkeley National Laboratory, subject to approval by the
   U.S. Department of Energy. See files COPYRIGHT.txt and
   cctbx/LICENSE.txt for further details.

   Revision history:
     Apr 2001: SourceForge release (R.W. Grosse-Kunstleve)
 */

#include <cctype>
#include <stdio.h>
#include <cctbx/sgtbx/utils.h>
#include <cctbx/sgtbx/math.h>
#include <cctbx/basic/define_range.h>

namespace sgtbx {

  int ChangeBaseFactor(const int *Old, int OldBF, int *New, int NewBF, int n)
  {
    rangei(n) {
          New[i] = Old[i] * NewBF;
      if (New[i] %  OldBF) return -1;
          New[i] /= OldBF;
    }
    return 0;
  }

  int rationalize(double fVal, int& iVal, int BF)
  {
    if (BF == 0) return -1;
        fVal *= BF;
    if (fVal < 0.) iVal = static_cast<int>(fVal - .5);
    else           iVal = static_cast<int>(fVal + .5);
        fVal -= iVal;
        fVal /= BF;
    if (fVal < 0.) fVal = -fVal;
    if (fVal > .0001) return -1;
    return 0;
  }

  std::string rational::format(bool Decimal) const
  {
    if (numerator() == 0) return std::string("0");
    char buf[32];
    if (Decimal) {
      sprintf(buf, "%.6g", static_cast<double>(numerator()) / denominator());
      char* cp = buf;
      if (*cp == '-') cp++;
      if (*cp == '0') {
        char* cpp = cp + 1; while (*cp) *cp++ = *cpp++;
      }
    }
    else if (denominator() == 1) {
      sprintf(buf, "%d", numerator());
    }
    else {
      sprintf(buf, "%d/%d", numerator(), denominator());
    }
    return std::string(buf);
  }

  int SignHemisphere(const Vec3& v)
  {
    if (v[2] >  0) return  1;
    if (v[2] == 0) {
      if (v[1] >  0) return  1;
      if (v[1] == 0) {
        if (v[0] >  0) return  1;
        if (v[0] == 0)
          return 0;
      }
    }
    return -1;
  }

} // namespace sgtbx
