
"""
Collection of miscellaneous tests for iotbx.reflection_file_reader; this is
tested more thoroughly elsewhere.
"""

from __future__ import division
from iotbx import reflection_file_reader

def exercise_sigma_filtering () :
  xds_raw = """\
!FORMAT=XDS_ASCII    MERGE=FALSE    FRIEDEL'S_LAW=FALSE
!OUTPUT_FILE=XDS_ASCII.HKL        DATE=23-Jan-2014
!Generated by CORRECT   (VERSION March 30, 2013)
!PROFILE_FITTING= TRUE
!NAME_TEMPLATE_OF_DATA_FRAMES=lysozyme_1.???? TIFF
!DATA_RANGE=       1     180
!ROTATION_AXIS=  0.999949  0.004913  0.008775
!OSCILLATION_RANGE=  0.500000
!STARTING_ANGLE=     0.000
!STARTING_FRAME=       1
!INCLUDE_RESOLUTION_RANGE=    50.000     2.9
!SPACE_GROUP_NUMBER=  150
!UNIT_CELL_CONSTANTS=   160.000   160.000    90.000  90.000  90.000 120.000
!REFLECTING_RANGE_E.S.D.=     0.139
!BEAM_DIVERGENCE_E.S.D.=     0.038
!X-RAY_WAVELENGTH=  1.746250
!INCIDENT_BEAM_DIRECTION= -0.002021 -0.001420  0.572650
!FRACTION_OF_POLARIZATION=   0.950
!POLARIZATION_PLANE_NORMAL=  0.000000  1.000000  0.000000
!AIR=  0.001981
!SILICON= 20.291441
!SENSOR_THICKNESS=  0.000000
!DETECTOR=CCDCHESS
!OVERLOAD=     65000
!NX=  4096  NY=  4096    QX=  0.073242  QY=  0.073242
!ORGX=   2062.24  ORGY=   2069.99
!DETECTOR_DISTANCE=   225.252
!DIRECTION_OF_DETECTOR_X-AXIS=   1.00000   0.00000   0.00000
!DIRECTION_OF_DETECTOR_Y-AXIS=   0.00000   1.00000   0.00000
!VARIANCE_MODEL=  4.530E+00  3.238E-04
!NUMBER_OF_ITEMS_IN_EACH_DATA_RECORD=12
!ITEM_H=1
!ITEM_K=2
!ITEM_L=3
!ITEM_IOBS=4
!ITEM_SIGMA(IOBS)=5
!ITEM_XD=6
!ITEM_YD=7
!ITEM_ZD=8
!ITEM_RLP=9
!ITEM_PEAK=10
!ITEM_CORR=11
!ITEM_PSI=12
!END_OF_HEADER
    -9    -2     0  1.229E+03 -4.897E+01  1686.8  1965.1     96.6 0.03139 100  70  -27.03
     9     2     0  1.427E+03 -5.665E+01  2416.2  2159.0     42.0 0.03114 100  67    0.58
    -2    -9     0  1.687E+03 -6.973E+01  1825.4  1759.3     23.1 0.09835  99  64  -34.39
     2   -11     0  1.614E+03  6.764E+01  1938.8  1701.4     14.2 0.11686 100  67  -45.67
     9   -11     0  1.802E+03  7.375E+01  2196.5  1713.5      2.0 0.11339 100  66  -55.56
     2     9     0  1.661E+03  6.853E+01  2277.7  2365.4      5.5 0.09825 100  66   29.11
"""
  open("tst_iotbx_hkl_reader.hkl", "w").write(xds_raw)
  hkl_in = reflection_file_reader.any_reflection_file(
    "tst_iotbx_hkl_reader.hkl")
  ma = hkl_in.as_miller_arrays(merge_equivalents=False)
  assert (ma[0].size() == 6)
  ma = hkl_in.as_miller_arrays(merge_equivalents=False,
    enforce_positive_sigmas=True)
  assert (ma[0].size() == 3)


if (__name__ == "__main__") :
  exercise_sigma_filtering()
  print "OK"
