// $Id$

#include <string>
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

    // C++ version of C function contributed by Vincent Favre-Nicolin
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
          fp -= m_Label_Z_Efpfdp->Z; // subtract the number of electrons
        }
        fdp = Data[i-2].fdp + f * (Data[i-1].fdp - Data[i-2].fdp);
      }
      return fpfdp(fp, fdp);
    }

  } // namespace detail
} // namespace eltbx
