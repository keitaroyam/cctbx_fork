// $Id$

#include <cctbx/eltbx/basic.h>
#include <cctbx/eltbx/icsd_radii.h>

namespace eltbx {
  namespace tables {

/* Table of ionic radii

   Reference:
                          U s e r ' s  M a n u a l
                         I C S D  -  C R Y S T I N
                         =========================
                    Inorganic Crystal Structure Database
                            in conjunction with
                   Crystal Structure Information System
                           and its application to
                CCDF - Cambridge Crystallographic Data File
                                    and
                           MDF - Metal Data File
                    G.Bergerhoff, B.Kilger, C.Witthauer,
                            R.Hundt, R.Sievers
                                    Bonn
                                    1986
             Institut fuer Anorganische Chemie der Universitaet
            -------------------------------------------------------------
            ICSD/CRYSTIN User's Manual.
            English Version. Translated by Ruth Schubert.
            Updated Dec. 1986.


            These radii are also the basis of the distance tests,  which are
            routinely  carried  out when collecting data in the ICSD system.
            In  this  connection,   negative increments are obtained for the
            specially small atoms C+4, D+1, H+1 and N+5.


   Radii "not in ICSD manual" were taken from Xtal 3.2 routine SX20
 */

    const detail::Label_Radius ICSD_Radii[] = {
      {"H",     0.78},
      {"H1+",  -0.38},
      {"H1-",   1.40},
      {"D",     0.78},
      {"D1+",  -0.24},
      {"D1-",   1.40},
      {"He",    1.00},
      {"Li",    1.56},
      {"Li1+",  0.59},
      {"Be",    1.13},
      {"Be2+",  0.17},
      {"B",     0.95},
      {"B1+",   0.58},
      {"B2+",   0.40},
      {"B3+",   0.02},
      {"B2-",   1.06},
      {"B3-",   1.22},
      {"C",     0.86},
      {"C1+",   0.79},
      {"C2+",   0.60},
      {"C3+",   0.55},
      {"C4+",  -0.08},
      {"C1-",   1.10},
      {"C2-",   1.38},
      {"C4-",   1.77},
      {"N",     0.80},
      {"N1+",   0.59},
      {"N2+",   0.37},
      {"N3+",   0.16},
      {"N4+",   0.15},
      {"N5+",  -0.12},
      {"N1-",   1.10},
      {"N2-",   1.29},
      {"N3-",   1.48},
      {"O",     0.66},
      {"O1-",   0.93},
      {"O2-",   1.21},
      {"F",     0.64},
      {"F7+",   0.08},
      {"F1-",   1.15},
      {"Ne",    1.00},
      {"Na",    1.91},
      {"Na1+",  0.97},
      {"Mg",    1.60},
      {"Mg2+",  0.49},
      {"Al",    1.43},
      {"Al3+",  0.39},
      {"Si",    1.34},
      {"Si2+",  1.25},
      {"Si3+",  1.17},
      {"Si4+",  0.26},
      {"Si1-",  1.41},
      {"Si4-",  2.72},
      {"P",     1.30},
      {"P1+",   1.01},
      {"P2+",   0.73},
      {"P3+",   0.44},
      {"P4+",   0.40},
      {"P5+",   0.17},
      {"P1-",   1.59},
      {"P2-",   1.20},
      {"P3-",   2.17},
      {"S",     1.04},
      {"S1+",   1.26},
      {"S2+",   0.87},
      {"S3+",   0.62},
      {"S4+",   0.37},
      {"S5+",   0.34},
      {"S6+",   0.12},
      {"S1-",   1.44},
      {"S2-",   1.84},
      {"Cl",    1.62},
      {"Cl1+",  1.30},
      {"Cl3+",  1.05},
      {"Cl5+",  0.12},
      {"Cl7+",  0.20},
      {"Cl1-",  1.81},
      {"Ar",    1.00},
      {"K",     2.34},
      {"K1+",   1.33},
      {"Ca",    1.97},
      {"Ca1+",  1.70},
      {"Ca2+",  0.99},
      {"Sc",    1.64},
      {"Sc1+",  1.36},
      {"Sc2+",  1.09},
      {"Sc3+",  0.73},
      {"Ti",    1.45},
      {"Ti2+",  0.86},
      {"Ti3+",  0.67},
      {"Ti4+",  0.53},
      {"V",     1.35},
      {"V1+",   1.02},
      {"V2+",   0.79},
      {"V3+",   0.64},
      {"V4+",   0.59},
      {"V5+",   0.36},
      {"Cr",    1.27},
      {"Cr1+",  1.07},
      {"Cr2+",  0.73},
      {"Cr3+",  0.62},
      {"Cr4+",  0.44},
      {"Cr5+",  0.35},
      {"Cr6+",  0.30},
      {"Mn",    1.32},
      {"Mn1+",  0.88},
      {"Mn2+",  0.67},
      {"Mn3+",  0.58},
      {"Mn4+",  0.54},
      {"Mn5+",  0.55},
      {"Mn6+",  0.27},
      {"Mn7+",  0.26},
      {"Mn1-",  1.06},
      {"Fe",    1.27},
      {"Fe1+",  0.84},
      {"Fe2+",  0.61},
      {"Fe3+",  0.49},
      {"Fe4+",  0.54},
      {"Fe6+",  0.30},
      {"Co",    1.26},
      {"Co1+",  0.80},
      {"Co2+",  0.65},
      {"Co3+",  0.52},
      {"Co4+",  0.54},
      {"Co1-",  1.30},
      {"Ni",    1.24},
      {"Ni1+",  0.68},
      {"Ni2+",  0.69},
      {"Ni3+",  0.60},
      {"Ni4+",  0.56},
      {"Cu",    1.28},
      {"Cu1+",  0.46},
      {"Cu2+",  0.62},
      {"Cu3+",  0.60},
      {"Zn",    1.39},
      {"Zn2+",  0.60},
      {"Ga",    1.40},
      {"Ga1+",  1.14},
      {"Ga2+",  0.88},
      {"Ga3+",  0.47},
      {"Ge",    1.40},
      {"Ge2+",  0.73},
      {"Ge3+",  0.63},
      {"Ge4+",  0.40},
      {"Ge4-",  2.72},
      {"As",    1.50},
      {"As2+",  0.52},
      {"As3+",  0.58},
      {"As4+",  0.64},
      {"As5+",  0.33},
      {"As1-",  1.59},
      {"As2-",  1.85},
      {"As3-",  2.11},
      {"Se",    1.60},
      {"Se1+",  1.39},
      {"Se2+",  1.08},
      {"Se4+",  0.50},
      {"Se6+",  0.29},
      {"Se1-",  1.77},
      {"Se2-",  1.98},
      {"Br",    1.11},
      {"Br1+",  1.06},
      {"Br3+",  0.82},
      {"Br5+",  0.59},
      {"Br7+",  0.39},
      {"Br1-",  1.96},
      {"Kr",    1.14}, /* not in ICSD manual */
      {"Kr2+",  0.74},
      {"Rb",    2.50},
      {"Rb1+",  1.47},
      {"Sr",    2.15},
      {"Sr2+",  1.12},
      {"Y",     1.80},
      {"Y1+",   1.11},
      {"Y2+",   1.30},
      {"Y3+",   0.89},
      {"Zr",    1.60},
      {"Zr1+",  1.42},
      {"Zr2+",  1.21},
      {"Zr3+",  0.89},
      {"Zr4+",  0.72},
      {"Nb",    1.48},
      {"Nb1+",  1.00},
      {"Nb2+",  0.71},
      {"Nb3+",  0.70},
      {"Nb4+",  0.69},
      {"Nb5+",  0.32},
      {"Mo",    1.40},
      {"Mo1+",  1.00},
      {"Mo2+",  0.92},
      {"Mo3+",  0.67},
      {"Mo4+",  0.65},
      {"Mo5+",  0.63},
      {"Mo6+",  0.42},
      {"Tc",    1.35},
      {"Tc2+",  1.00},
      {"Tc3+",  0.80},
      {"Tc4+",  0.64},
      {"Tc6+",  0.56},
      {"Tc7+",  0.98},
      {"Ru",    1.32},
      {"Ru2+",  0.90},
      {"Ru3+",  0.68},
      {"Ru4+",  0.62},
      {"Ru5+",  0.52},
      {"Ru6+",  0.37},
      {"Ru7+",  0.54},
      {"Rh",    1.34},
      {"Rh1+",  0.82},
      {"Rh2+",  0.75},
      {"Rh3+",  0.67},
      {"Rh4+",  0.62},
      {"Rh5+",  0.55},
      {"Rh1-",  1.54},
      {"Pd",    1.37},
      {"Pd1+",  0.59},
      {"Pd2+",  0.64},
      {"Pd3+",  0.76},
      {"Pd4+",  0.62},
      {"Ag",    1.44},
      {"Ag1+",  0.67},
      {"Ag2+",  0.89},
      {"Ag3+",  0.65},
      {"Cd",    1.57},
      {"Cd2+",  0.84},
      {"In",    1.66},
      {"In1+",  1.35},
      {"In2+",  1.08},
      {"In3+",  0.79},
      {"Sn",    1.58},
      {"Sn2+",  0.93},
      {"Sn3+",  0.82},
      {"Sn4+",  0.69},
      {"Sb",    1.60},
      {"Sb2+",  0.83},
      {"Sb3+",  0.76},
      {"Sb4+",  0.69},
      {"Sb5+",  0.61},
      {"Sb6+",  0.75},
      {"Sb2-",  2.16},
      {"Sb3-",  2.44},
      {"Te",    1.70},
      {"Te1+",  1.45},
      {"Te2+",  1.20},
      {"Te4+",  0.52},
      {"Te6+",  0.56},
      {"Te1-",  1.95},
      {"Te2-",  2.21},
      {"I",     1.95},
      {"I1+",   1.70},
      {"I3+",   1.39},
      {"I5+",   0.62},
      {"I7+",   0.50},
      {"I1-",   2.20},
      {"Xe",    1.33}, /* not in ICSD manual */
      {"Xe2+",  1.10},
      {"Xe4+",  0.83},
      {"Xe6+",  0.55},
      {"Xe8+",  0.40},
      {"Cs",    2.71},
      {"Cs1+",  1.67},
      {"Ba",    2.24},
      {"Ba2+",  1.34},
      {"La",    1.87},
      {"La1+",  1.40},
      {"La2+",  1.27},
      {"La3+",  1.06},
      {"La4+",  1.01},
      {"Ce",    1.82},
      {"Ce2+",  1.30},
      {"Ce3+",  1.03},
      {"Ce4+",  0.80},
      {"Pr",    1.83},
      {"Pr2+",  1.00},
      {"Pr3+",  1.01},
      {"Pr4+",  0.78},
      {"Nd",    1.82},
      {"Nd2+",  1.30},
      {"Nd3+",  1.00},
      {"Nd4+",  0.90},
      {"Pm",    1.63}, /* not in ICSD manual */
      {"Pm3+",  0.98},
      {"Sm",    1.80},
      {"Sm2+",  1.10},
      {"Sm3+",  0.96},
      {"Eu",    2.04},
      {"Eu2+",  1.17},
      {"Eu3+",  0.95},
      {"Eu4+",  0.65},
      {"Gd",    1.80},
      {"Gd1+",  0.91},
      {"Gd2+",  0.94},
      {"Gd3+",  0.94},
      {"Gd4+",  1.00},
      {"Tb",    1.78},
      {"Tb1+",  1.50},
      {"Tb2+",  1.22},
      {"Tb3+",  0.92},
      {"Tb4+",  0.76},
      {"Dy",    1.77},
      {"Dy2+",  1.10},
      {"Dy3+",  0.91},
      {"Ho",    1.77},
      {"Ho2+",  1.10},
      {"Ho3+",  0.89},
      {"Er",    1.76},
      {"Er1+",  1.50},
      {"Er2+",  1.20},
      {"Er3+",  0.88},
      {"Tm",    1.75},
      {"Tm2+",  1.16},
      {"Tm3+",  0.87},
      {"Yb",    1.94},
      {"Yb2+",  0.90},
      {"Yb3+",  0.86},
      {"Lu",    1.73},
      {"Lu2+",  1.20},
      {"Lu3+",  0.85},
      {"Hf",    1.59},
      {"Hf2+",  1.10},
      {"Hf3+",  0.97},
      {"Hf4+",  0.71},
      {"Ta",    1.48},
      {"Ta1+",  0.88},
      {"Ta2+",  0.83},
      {"Ta3+",  0.67},
      {"Ta4+",  0.66},
      {"Ta5+",  0.64},
      {"W",     1.41},
      {"W2+",   0.80},
      {"W3+",   0.75},
      {"W4+",   0.65},
      {"W5+",   0.66},
      {"W6+",   0.41},
      {"Re",    1.46},
      {"Re1+",  1.23},
      {"Re2+",  1.00},
      {"Re3+",  0.77},
      {"Re4+",  0.63},
      {"Re5+",  0.52},
      {"Re6+",  0.52},
      {"Re7+",  0.40},
      {"Os",    1.34},
      {"Os1+",  1.20},
      {"Os2+",  1.05},
      {"Os4+",  0.63},
      {"Os5+",  0.51},
      {"Os6+",  0.33},
      {"Os7+",  0.27},
      {"Os8+",  0.20},
      {"Ir",    1.36},
      {"Ir1+",  1.37},
      {"Ir2+",  1.00},
      {"Ir3+",  0.73},
      {"Ir4+",  0.63},
      {"Ir5+",  0.68},
      {"Pt",    1.39},
      {"Pt2+",  0.80},
      {"Pt3+",  0.73},
      {"Pt4+",  0.63},
      {"Pt5+",  0.58},
      {"Pt6+",  0.50},
      {"Au",    1.44},
      {"Au1+",  1.37},
      {"Au2+",  1.11},
      {"Au3+",  0.70},
      {"Au5+",  0.70},
      {"Hg",    1.62},
      {"Hg1+",  0.97},
      {"Hg2+",  0.69},
      {"Tl",    1.73},
      {"Tl1+",  1.47},
      {"Tl3+",  0.88},
      {"Pb",    1.75},
      {"Pb2+",  0.94},
      {"Pb4+",  0.77},
      {"Bi",    1.70},
      {"Bi1+",  1.45},
      {"Bi2+",  1.16},
      {"Bi3+",  0.96},
      {"Bi5+",  0.74},
      {"Bi2-",  1.70},
      {"Po",    1.70},
      {"Po2+",  1.40},
      {"Po4+",  1.10},
      {"Po6+",  0.67},
      {"At",    1.53}, /* not in ICSD manual */
      {"At7+",  0.62},
      {"Rn",    1.53}, /* not in ICSD manual */
      {"Fr",    1.53}, /* not in ICSD manual */
      {"Fr1+",  1.80},
      {"Ra",    1.53}, /* not in ICSD manual */
      {"Ra2+",  1.43},
      {"Ac",    1.88},
      {"Ac3+",  1.18},
      {"Th",    1.80},
      {"Th2+",  0.80},
      {"Th3+",  0.90},
      {"Th4+",  1.00},
      {"Pa",    1.61},
      {"Pa3+",  1.13},
      {"Pa4+",  0.98},
      {"Pa5+",  0.89},
      {"U",     1.55},
      {"U1+",   1.40},
      {"U2+",   1.30},
      {"U3+",   1.06},
      {"U4+",   0.97},
      {"U5+",   0.76},
      {"U6+",   0.45},
      {"Np",    1.58},
      {"Np2+",  1.10},
      {"Np3+",  1.04},
      {"Np4+",  0.95},
      {"Np5+",  0.80},
      {"Np6+",  0.80},
      {"Np7+",  0.71},
      {"Pu",    1.64},
      {"Pu2+",  0.90},
      {"Pu3+",  1.00},
      {"Pu4+",  0.80},
      {"Pu5+",  0.70},
      {"Pu6+",  0.60},
      {"Am",    1.73},
      {"Am2+",  1.20},
      {"Am3+",  1.01},
      {"Am4+",  0.92},
      {"Am5+",  0.69},
      {"Am6+",  0.50},
      {"Cm",    1.42}, /* was 0.00 in ICSD manual */
      {"Cm3+",  0.98},
      {"Cm4+",  0.95},
      {"Bk",    1.42}, /* not in ICSD manual */
      {"Bk3+",  0.96},
      {"Bk4+",  0.93},
      {"Cf",    1.42}, /* not in ICSD manual */
      {"Cf3+",  0.95},
      {"Es",    1.42}, /* not in ICSD manual */
      {"Fm",    1.42}, /* not in ICSD manual */
      {"Md",    1.42}, /* not in ICSD manual */
      {"No",    1.42}, /* not in ICSD manual */
      {"Lr",    1.42}, /* not in ICSD manual */
      {0, 0}
    };

  } // namespace tables
} // namespace eltbx

namespace {

  const eltbx::detail::Label_Radius* FindEntry(const std::string& WorkLabel,
                                               bool Exact)
  {
    int m = 0;
    const eltbx::detail::Label_Radius* mEntry = 0;
    for (const eltbx::detail::Label_Radius*
         Entry = eltbx::tables::ICSD_Radii; Entry->Label; Entry++)
    {
      int i = eltbx::MatchLabels(WorkLabel, Entry->Label);
      if (i < 0) return Entry;
      if (i > m) {
        m = i;
        mEntry = Entry;
      }
    }
    if (Exact || !mEntry) {
      throw eltbx::error("Unknown ion label.");
    }
    return mEntry;
  }

} // namespace <anonymous>

namespace eltbx {

  ICSD_Radius::ICSD_Radius(const std::string& Label, bool Exact)
  {
    std::string WorkLabel = StripLabel(Label, Exact);
    m_Label_Radius = FindEntry(WorkLabel, Exact);
  }

} // namespace eltbx
