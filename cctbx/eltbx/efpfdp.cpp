// $Id$
/* Copyright (c) 2001 The Regents of the University of California through
   E.O. Lawrence Berkeley National Laboratory, subject to approval by the
   U.S. Department of Energy. See files COPYRIGHT.txt and
   cctbx/LICENSE.txt for further details.

   Revision history:
     2001 May 31: merged from CVS branch sgtbx_type (R.W. Grosse-Kunstleve)
     Apr 2001: SourceForge release (R.W. Grosse-Kunstleve)
               Based on C code contributed by Vincent Favre-Nicolin.
 */

#include <string>
#include <ctype.h> // cannot use cctype b/o non-conforming compilers
#include <cctbx/eltbx/basic.h>
#include <cctbx/eltbx/efpfdp.h>

namespace eltbx {
  namespace detail {

    const Label_Z_Efpfdp* FindEntry(const Label_Z_Efpfdp* Tables,
                                    const std::string& WorkLabel,
                                    bool Exact)
    {
      // map D to H
      std::string WL = WorkLabel;
      if (WL == "D") WL = "H";
      int m = 0;
      const Label_Z_Efpfdp* mEntry = 0;
      for (const Label_Z_Efpfdp* Entry = Tables; Entry->Label; Entry++)
      {
        int i = MatchLabels(WL, Entry->Label);
        if (i < 0) return Entry;
        if (i > m && !isdigit(Entry->Label[i - 1])) {
          m = i;
          mEntry = Entry;
        }
      }
      if (Exact || !mEntry) {
        throw error("Unknown scattering factor label.");
      }
      return mEntry;
    }

    fpfdp interpolate(const Label_Z_Efpfdp* m_Label_Z_Efpfdp, double Energy)
    {
      float fp = Efpfdp_undefined;
      float fdp = Efpfdp_undefined;
      const Efpfdp* Data = m_Label_Z_Efpfdp->Data;
      float Energy1 = Data[0].E;
      float Energy2 = Data[1].E;
      int i;
      for(i = 2; Energy2 > 0. && Energy2 < Energy; i++) {
        Energy1 = Energy2;
        Energy2 = Data[i].E;
      }
      if (Energy >= Energy1 && Energy2 > 0.) {
        float f = (Energy - Energy1) / (Energy2 - Energy1);
        if (   Data[i-2].fp != Efpfdp_undefined
            && Data[i-1].fp != Efpfdp_undefined) {
          fp = Data[i-2].fp + f * (Data[i-1].fp - Data[i-2].fp);
        }
        fdp = Data[i-2].fdp + f * (Data[i-1].fdp - Data[i-2].fdp);
      }
      return fpfdp(fp, fdp);
    }

  } // namespace detail
} // namespace eltbx
