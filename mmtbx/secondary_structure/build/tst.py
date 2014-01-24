from mmtbx.secondary_structure import build as ssb
import iotbx.pdb
from libtbx.test_utils import Exception_expected, approx_equal, show_diff
from scitbx import matrix
from libtbx.utils import Sorry


t_pdb_str = """\
ATOM      1  N   ALA     2       1.643  -2.366  -1.408  1.00
ATOM      3  CA  ALA     2       1.280  -3.608  -2.069  1.00
ATOM      6  CB  ALA     2       1.361  -4.762  -1.068  1.00
ATOM     10  C   ALA     2      -0.114  -3.466  -2.684  1.00
ATOM     11  O   ALA     2      -0.327  -3.827  -3.840  1.00
"""

alpha_pdb_str = """\
ATOM      1  N   ALA     2       1.643  -2.366  -1.408  1.00
ATOM      3  CA  ALA     2       1.280  -3.608  -2.069  1.00
ATOM      6  CB  ALA     2       1.361  -4.762  -1.068  1.00
ATOM     10  C   ALA     2      -0.114  -3.466  -2.684  1.00
ATOM     11  O   ALA     2      -0.327  -3.827  -3.840  1.00
ATOM     12  N   ALA     3      -1.028  -2.938  -1.882  1.00
ATOM     14  CA  ALA     3      -2.395  -2.743  -2.333  1.00
ATOM     17  CB  ALA     3      -3.228  -2.150  -1.194  1.00
ATOM     21  C   ALA     3      -2.396  -1.855  -3.579  1.00
ATOM     22  O   ALA     3      -3.059  -2.167  -4.567  1.00
"""

correct_answer1 = """\
ATOM      1  N   ALA     1       1.643  -2.366  -1.408  1.00  0.00
ATOM      2  CA  ALA     1       1.280  -3.608  -2.069  1.00  0.00
ATOM      3  CB  ALA     1       1.361  -4.762  -1.068  1.00  0.00
ATOM      4  C   ALA     1      -0.114  -3.466  -2.684  1.00  0.00
ATOM      5  O   ALA     1      -0.327  -3.827  -3.840  1.00  0.00
ATOM      6  N   CYS     2       1.325  -0.000   0.001  1.00  0.00
ATOM      7  CA  CYS     2       2.073  -0.000  -1.244  1.00  0.00
ATOM      8  CB  CYS     2       3.572   0.033  -0.939  1.00  0.00
ATOM      9  C   CYS     2       1.674  -1.221  -2.075  1.00  0.00
ATOM     10  O   CYS     2       1.409  -1.105  -3.270  1.00  0.00
ATOM     11  SG  CYS     2       4.118   1.483  -0.009  1.00  0.00           S
ATOM     12  N   GLU     3      -0.002  -1.004   2.218  1.00  0.00
ATOM     13  CA  GLU     3      -0.647  -0.001   1.388  1.00  0.00
ATOM     14  CB  GLU     3      -0.557   1.364   2.073  1.00  0.00
ATOM     15  C   GLU     3      -0.001  -0.000   0.001  1.00  0.00
ATOM     16  O   GLU     3      -0.697  -0.001  -1.013  1.00  0.00
ATOM     17  CG  GLU     3      -1.241   1.432   3.428  1.00  0.00           C
ATOM     18  CD  GLU     3      -1.144   2.803   4.068  1.00  0.00           C
ATOM     19  OE1 GLU     3      -1.671   2.977   5.187  1.00  0.00           O
ATOM     20  OE2 GLU     3      -0.542   3.708   3.452  1.00  0.00           O
ATOM     21  N   ASP     4       2.012  -2.624   3.218  1.00  0.00
ATOM     22  CA  ASP     4       0.743  -3.214   2.827  1.00  0.00
ATOM     23  CB  ASP     4      -0.093  -3.501   4.076  1.00  0.00
ATOM     24  C   ASP     4       0.029  -2.277   1.850  1.00  0.00
ATOM     25  O   ASP     4      -0.464  -2.714   0.812  1.00  0.00
ATOM     26  CG  ASP     4      -1.443  -4.121   3.737  1.00  0.00           C
ATOM     27  OD1 ASP     4      -1.527  -5.366   3.671  1.00  0.00           O
ATOM     28  OD2 ASP     4      -2.415  -3.362   3.538  1.00  0.00           O
ATOM     29  N   GLY     5       3.868  -0.660   3.835  1.00  0.00
ATOM     30  CA  GLY     5       4.210  -1.696   2.876  1.00  0.00
ATOM     31  C   GLY     5       2.926  -2.308   2.312  1.00  0.00
ATOM     32  O   GLY     5       2.793  -2.475   1.101  1.00  0.00
ATOM     33  N   PHE     6       2.438   0.669   5.803  1.00  0.00
ATOM     34  CA  PHE     6       2.842   1.381   4.603  1.00  0.00
ATOM     35  CB  PHE     6       4.058   2.255   4.913  1.00  0.00
ATOM     36  C   PHE     6       3.117   0.374   3.484  1.00  0.00
ATOM     37  O   PHE     6       2.655   0.549   2.358  1.00  0.00
ATOM     38  CG  PHE     6       3.811   3.307   5.955  1.00  0.00           C
ATOM     39  CD1 PHE     6       3.297   4.545   5.607  1.00  0.00           C
ATOM     40  CD2 PHE     6       4.091   3.053   7.289  1.00  0.00           C
ATOM     41  CE1 PHE     6       3.066   5.511   6.568  1.00  0.00           C
ATOM     42  CE2 PHE     6       3.862   4.015   8.255  1.00  0.00           C
ATOM     43  CZ  PHE     6       3.348   5.245   7.893  1.00  0.00           C
ATOM     44  N   ILE     7       2.314  -1.365   7.682  1.00  0.00
ATOM     45  CA  ILE     7       1.085  -0.817   7.135  1.00  0.00
ATOM     46  CB  ILE     7       0.458   0.142   8.148  1.00  0.00
ATOM     47  C   ILE     7       1.386  -0.137   5.797  1.00  0.00
ATOM     48  O   ILE     7       0.679  -0.351   4.814  1.00  0.00
ATOM     49  CG1 ILE     7       1.441   1.234   8.578  1.00  0.00           C
ATOM     50  CG2 ILE     7      -0.073  -0.610   9.360  1.00  0.00           C
ATOM     51  CD1 ILE     7       0.842   2.326   9.444  1.00  0.00           C
ATOM     52  N   HIS     8       5.020  -1.589   8.242  1.00  0.00
ATOM     53  CA  HIS     8       4.300  -2.731   7.707  1.00  0.00
ATOM     54  CB  HIS     8       3.996  -3.718   8.836  1.00  0.00
ATOM     55  C   HIS     8       3.032  -2.246   7.000  1.00  0.00
ATOM     56  O   HIS     8       2.739  -2.667   5.882  1.00  0.00
ATOM     57  CG  HIS     8       5.212  -4.257   9.520  1.00  0.00           C
ATOM     58  ND1 HIS     8       5.865  -5.395   9.101  1.00  0.00           N
ATOM     59  CD2 HIS     8       5.898  -3.805  10.597  1.00  0.00           C
ATOM     60  CE1 HIS     8       6.899  -5.623   9.889  1.00  0.00           C
ATOM     61  NE2 HIS     8       6.942  -4.673  10.806  1.00  0.00           N
ATOM     62  N   LYS     9       5.431   0.918   9.351  1.00  0.00
ATOM     63  CA  LYS     9       6.166   0.530   8.159  1.00  0.00
ATOM     64  CB  LYS     9       7.593   0.139   8.544  1.00  0.00
ATOM     65  C   LYS     9       5.420  -0.603   7.451  1.00  0.00
ATOM     66  O   LYS     9       5.228  -0.563   6.237  1.00  0.00
ATOM     67  CG  LYS     9       8.396   1.251   9.196  1.00  0.00           C
ATOM     68  CD  LYS     9       9.807   0.800   9.537  1.00  0.00           C
ATOM     69  CE  LYS     9      10.604   1.915  10.194  1.00  0.00           C
ATOM     70  NZ  LYS     9      11.989   1.487  10.534  1.00  0.00           N
ATOM     71  N   MET    10       3.814   0.661  11.588  1.00  0.00
ATOM     72  CA  MET    10       3.532   1.700  10.613  1.00  0.00
ATOM     73  CB  MET    10       4.031   3.046  11.142  1.00  0.00
ATOM     74  C   MET    10       4.172   1.326   9.274  1.00  0.00
ATOM     75  O   MET    10       3.531   1.412   8.228  1.00  0.00
ATOM     76  CG  MET    10       3.378   3.489  12.440  1.00  0.00           C
ATOM     77  SD  MET    10       3.674   2.332  13.791  1.00  0.00           S
ATOM     78  CE  MET    10       2.791   3.137  15.126  1.00  0.00           C
ATOM     79  N   LEU    11       5.201  -1.362  12.881  1.00  0.00
ATOM     80  CA  LEU    11       3.819  -1.576  12.487  1.00  0.00
ATOM     81  CB  LEU    11       2.911  -1.432  13.710  1.00  0.00
ATOM     82  C   LEU    11       3.453  -0.596  11.370  1.00  0.00
ATOM     83  O   LEU    11       2.867  -0.987  10.362  1.00  0.00
ATOM     84  CG  LEU    11       3.187  -2.361  14.896  1.00  0.00           C
ATOM     85  CD1 LEU    11       2.873  -3.811  14.554  1.00  0.00           C
ATOM     86  CD2 LEU    11       2.397  -1.915  16.117  1.00  0.00           C
ATOM     87  N   ASN    12       7.566  -0.003  13.376  1.00  0.00
ATOM     88  CA  ASN    12       7.585  -1.206  12.562  1.00  0.00
ATOM     89  CB  ASN    12       8.097  -2.380  13.398  1.00  0.00
ATOM     90  C   ASN    12       6.185  -1.459  11.998  1.00  0.00
ATOM     91  O   ASN    12       6.029  -1.729  10.809  1.00  0.00
ATOM     92  CG  ASN    12       9.502  -2.164  13.921  1.00  0.00           C
ATOM     93  OD1 ASN    12       9.976  -1.031  13.997  1.00  0.00           O
ATOM     94  ND2 ASN    12      10.177  -3.248  14.286  1.00  0.00           N
ATOM     95  N   GLN    13       6.585   1.940  15.094  1.00  0.00
ATOM     96  CA  GLN    13       7.215   2.335  13.845  1.00  0.00
ATOM     97  CB  GLN    13       8.638   2.824  14.123  1.00  0.00
ATOM     98  C   GLN    13       7.182   1.159  12.866  1.00  0.00
ATOM     99  O   GLN    13       6.820   1.324  11.703  1.00  0.00
ATOM    100  CG  GLN    13       9.364   3.353  12.886  1.00  0.00           C
ATOM    101  CD  GLN    13      10.749   3.882  13.203  1.00  0.00           C
ATOM    102  OE1 GLN    13      11.189   3.853  14.353  1.00  0.00           O
ATOM    103  NE2 GLN    13      11.445   4.370  12.183  1.00  0.00           N
ATOM    104  N   PRO    14       5.796   0.297  17.182  1.00  0.00
ATOM    105  CA  PRO    14       4.811   1.123  16.505  1.00  0.00
ATOM    106  CB  PRO    14       4.495   2.349  17.365  1.00  0.00
ATOM    107  C   PRO    14       5.334   1.503  15.118  1.00  0.00
ATOM    108  O   PRO    14       4.615   1.394  14.127  1.00  0.00
ATOM    109  CG  PRO    14       4.826   1.810  18.747  1.00  0.00           C
ATOM    110  CD  PRO    14       5.953   0.833  18.586  1.00  0.00           C
ATOM    111  N   SER    15       8.284  -0.677  17.918  1.00  0.00
ATOM    112  CA  SER    15       7.253  -1.600  17.476  1.00  0.00
ATOM    113  CB  SER    15       6.635  -2.294  18.691  1.00  0.00
ATOM    114  C   SER    15       6.215  -0.841  16.647  1.00  0.00
ATOM    115  O   SER    15       5.827  -1.289  15.570  1.00  0.00
ATOM    116  OG  SER    15       5.619  -3.208  18.288  1.00  0.00           O
ATOM    117  N   ARG    16       9.437   1.701  18.756  1.00  0.00
ATOM    118  CA  ARG    16      10.037   0.958  17.661  1.00  0.00
ATOM    119  CB  ARG    16      11.262   0.197  18.170  1.00  0.00
ATOM    120  C   ARG    16       8.988   0.029  17.045  1.00  0.00
ATOM    121  O   ARG    16       8.842  -0.027  15.825  1.00  0.00
ATOM    122  CG  ARG    16      12.381   1.077  18.717  1.00 10.00           C
ATOM    123  CD  ARG    16      13.171   1.786  17.619  1.00 10.00           C
ATOM    124  NE  ARG    16      13.977   0.858  16.822  1.00 10.00           N
ATOM    125  CZ  ARG    16      13.640   0.343  15.637  1.00 10.00           C
ATOM    126  NH1 ARG    16      12.487   0.636  15.035  1.00 10.00           N
ATOM    127  NH2 ARG    16      14.480  -0.488  15.036  1.00 10.00           N
ATOM    128  N   THR    17       7.778   2.238  20.911  1.00  0.00
ATOM    129  CA  THR    17       7.854   3.182  19.809  1.00  0.00
ATOM    130  CB  THR    17       8.738   4.365  20.209  1.00  0.00
ATOM    131  C   THR    17       8.371   2.464  18.561  1.00  0.00
ATOM    132  O   THR    17       7.809   2.610  17.477  1.00  0.00
ATOM    133  OG1 THR    17      10.066   3.925  20.513  1.00  0.00           O
ATOM    134  CG2 THR    17       8.165   5.118  21.399  1.00  0.00           C
ATOM    135  N   TRP    18       8.438   0.068  22.504  1.00  0.00
ATOM    136  CA  TRP    18       7.066   0.242  22.058  1.00  0.00
ATOM    137  CB  TRP    18       6.225   0.812  23.202  1.00  0.00
ATOM    138  C   TRP    18       7.046   1.138  20.817  1.00  0.00
ATOM    139  O   TRP    18       6.387   0.821  19.828  1.00  0.00
ATOM    140  CG  TRP    18       6.181  -0.062  24.415  1.00  0.00           C
ATOM    141  CD1 TRP    18       7.036  -0.028  25.478  1.00  0.00           C
ATOM    142  CD2 TRP    18       5.237  -1.105  24.694  1.00  0.00           C
ATOM    143  NE1 TRP    18       6.685  -0.985  26.400  1.00  0.00           N
ATOM    144  CE2 TRP    18       5.583  -1.659  25.942  1.00  0.00           C
ATOM    145  CE3 TRP    18       4.133  -1.623  24.009  1.00  0.00           C
ATOM    146  CZ2 TRP    18       4.867  -2.704  26.520  1.00  0.00           C
ATOM    147  CZ3 TRP    18       3.423  -2.661  24.584  1.00  0.00           C
ATOM    148  CH2 TRP    18       3.792  -3.191  25.827  1.00  0.00           C
ATOM    149  N   VAL    19      11.099   0.683  22.976  1.00  0.00
ATOM    150  CA  VAL    19      10.756  -0.560  22.307  1.00  0.00
ATOM    151  CB  VAL    19      10.860  -1.720  23.300  1.00  0.00
ATOM    152  C   VAL    19       9.359  -0.439  21.696  1.00  0.00
ATOM    153  O   VAL    19       9.149  -0.796  20.538  1.00  0.00
ATOM    154  CG1 VAL    19      12.223  -1.766  23.971  1.00  0.00           C
ATOM    155  CG2 VAL    19      10.584  -3.057  22.579  1.00  0.00           C
ATOM    156  N   TYR    20      10.742   3.034  24.402  1.00  0.00
ATOM    157  CA  TYR    20      11.488   3.055  23.155  1.00  0.00
ATOM    158  CB  TYR    20      12.986   3.112  23.457  1.00  0.00
ATOM    159  C   TYR    20      11.108   1.833  22.316  1.00  0.00
ATOM    160  O   TYR    20      10.838   1.953  21.123  1.00  0.00
ATOM    161  CG  TYR    20      13.418   4.341  24.224  1.00  0.00           C
ATOM    162  CD1 TYR    20      13.489   4.323  25.611  1.00  0.00           C
ATOM    163  CD2 TYR    20      13.749   5.518  23.566  1.00  0.00           C
ATOM    164  CE1 TYR    20      13.877   5.444  26.322  1.00  0.00           C
ATOM    165  CE2 TYR    20      14.140   6.644  24.268  1.00  0.00           C
ATOM    166  CZ  TYR    20      14.202   6.600  25.645  1.00  0.00           C
ATOM    167  OH  TYR    20      14.590   7.719  26.348  1.00  0.00           O
TER
"""
correct_answer2 = """\
ATOM      1  N   ALA     1       1.643  -2.366  -1.408  1.00  0.00
ATOM      2  CA  ALA     1       1.280  -3.608  -2.069  1.00  0.00
ATOM      3  CB  ALA     1       1.361  -4.762  -1.068  1.00  0.00
ATOM      4  C   ALA     1      -0.114  -3.466  -2.684  1.00  0.00
ATOM      5  O   ALA     1      -0.327  -3.827  -3.840  1.00  0.00
ATOM      6  N   CYS     2       1.325  -0.000   0.001  1.00  0.00
ATOM      7  CA  CYS     2       2.073  -0.000  -1.244  1.00  0.00
ATOM      8  CB  CYS     2       3.572   0.033  -0.939  1.00  0.00
ATOM      9  C   CYS     2       1.674  -1.221  -2.075  1.00  0.00
ATOM     10  O   CYS     2       1.409  -1.105  -3.270  1.00  0.00
ATOM     11  SG  CYS     2       4.118   1.483  -0.009  1.00  0.00           S
ATOM     12  N   GLU     3      -0.002  -1.004   2.218  1.00  0.00
ATOM     13  CA  GLU     3      -0.647  -0.001   1.388  1.00  0.00
ATOM     14  CB  GLU     3      -0.557   1.364   2.073  1.00  0.00
ATOM     15  C   GLU     3      -0.001  -0.000   0.001  1.00  0.00
ATOM     16  O   GLU     3      -0.697  -0.001  -1.013  1.00  0.00
ATOM     17  CG  GLU     3      -1.241   1.432   3.428  1.00  0.00           C
ATOM     18  CD  GLU     3      -1.144   2.803   4.068  1.00  0.00           C
ATOM     19  OE1 GLU     3      -1.671   2.977   5.187  1.00  0.00           O
ATOM     20  OE2 GLU     3      -0.542   3.708   3.452  1.00  0.00           O
ATOM     21  N   ASP     4       2.012  -2.624   3.218  1.00  0.00
ATOM     22  CA  ASP     4       0.743  -3.214   2.827  1.00  0.00
ATOM     23  CB  ASP     4      -0.093  -3.501   4.076  1.00  0.00
ATOM     24  C   ASP     4       0.029  -2.277   1.850  1.00  0.00
ATOM     25  O   ASP     4      -0.464  -2.714   0.812  1.00  0.00
ATOM     26  CG  ASP     4      -1.443  -4.121   3.737  1.00  0.00           C
ATOM     27  OD1 ASP     4      -1.527  -5.366   3.671  1.00  0.00           O
ATOM     28  OD2 ASP     4      -2.415  -3.362   3.538  1.00  0.00           O
ATOM     29  N   GLY     5       3.868  -0.660   3.835  1.00  0.00
ATOM     30  CA  GLY     5       4.210  -1.696   2.876  1.00  0.00
ATOM     31  C   GLY     5       2.926  -2.308   2.312  1.00  0.00
ATOM     32  O   GLY     5       2.793  -2.475   1.101  1.00  0.00
ATOM     33  N   PHE     6       2.438   0.669   5.803  1.00  0.00
ATOM     34  CA  PHE     6       2.842   1.381   4.603  1.00  0.00
ATOM     35  CB  PHE     6       4.058   2.255   4.913  1.00  0.00
ATOM     36  C   PHE     6       3.117   0.374   3.484  1.00  0.00
ATOM     37  O   PHE     6       2.655   0.549   2.358  1.00  0.00
ATOM     38  CG  PHE     6       3.811   3.307   5.955  1.00  0.00           C
ATOM     39  CD1 PHE     6       3.297   4.545   5.607  1.00  0.00           C
ATOM     40  CD2 PHE     6       4.091   3.053   7.289  1.00  0.00           C
ATOM     41  CE1 PHE     6       3.066   5.511   6.568  1.00  0.00           C
ATOM     42  CE2 PHE     6       3.862   4.015   8.255  1.00  0.00           C
ATOM     43  CZ  PHE     6       3.348   5.245   7.893  1.00  0.00           C
ATOM     44  N   ILE     7       2.314  -1.365   7.682  1.00  0.00
ATOM     45  CA  ILE     7       1.085  -0.817   7.135  1.00  0.00
ATOM     46  CB  ILE     7       0.458   0.142   8.148  1.00  0.00
ATOM     47  C   ILE     7       1.386  -0.137   5.797  1.00  0.00
ATOM     48  O   ILE     7       0.679  -0.351   4.814  1.00  0.00
ATOM     49  CG1 ILE     7       1.441   1.234   8.578  1.00  0.00           C
ATOM     50  CG2 ILE     7      -0.073  -0.610   9.360  1.00  0.00           C
ATOM     51  CD1 ILE     7       0.842   2.326   9.444  1.00  0.00           C
ATOM     52  N   HIS     8       5.020  -1.589   8.242  1.00  0.00
ATOM     53  CA  HIS     8       4.300  -2.731   7.707  1.00  0.00
ATOM     54  CB  HIS     8       3.996  -3.718   8.836  1.00  0.00
ATOM     55  C   HIS     8       3.032  -2.246   7.000  1.00  0.00
ATOM     56  O   HIS     8       2.739  -2.667   5.882  1.00  0.00
ATOM     57  CG  HIS     8       5.212  -4.257   9.520  1.00  0.00           C
ATOM     58  ND1 HIS     8       5.865  -5.395   9.101  1.00  0.00           N
ATOM     59  CD2 HIS     8       5.898  -3.805  10.597  1.00  0.00           C
ATOM     60  CE1 HIS     8       6.899  -5.623   9.889  1.00  0.00           C
ATOM     61  NE2 HIS     8       6.942  -4.673  10.806  1.00  0.00           N
ATOM     62  N   LYS     9       5.431   0.918   9.351  1.00  0.00
ATOM     63  CA  LYS     9       6.166   0.530   8.159  1.00  0.00
ATOM     64  CB  LYS     9       7.593   0.139   8.544  1.00  0.00
ATOM     65  C   LYS     9       5.420  -0.603   7.451  1.00  0.00
ATOM     66  O   LYS     9       5.228  -0.563   6.237  1.00  0.00
ATOM     67  CG  LYS     9       8.396   1.251   9.196  1.00  0.00           C
ATOM     68  CD  LYS     9       9.807   0.800   9.537  1.00  0.00           C
ATOM     69  CE  LYS     9      10.604   1.915  10.194  1.00  0.00           C
ATOM     70  NZ  LYS     9      11.989   1.487  10.534  1.00  0.00           N
ATOM     71  N   MET    10       3.814   0.661  11.588  1.00  0.00
ATOM     72  CA  MET    10       3.532   1.700  10.613  1.00  0.00
ATOM     73  CB  MET    10       4.031   3.046  11.142  1.00  0.00
ATOM     74  C   MET    10       4.172   1.326   9.274  1.00  0.00
ATOM     75  O   MET    10       3.531   1.412   8.228  1.00  0.00
ATOM     76  CG  MET    10       3.378   3.489  12.440  1.00  0.00           C
ATOM     77  SD  MET    10       3.674   2.332  13.791  1.00  0.00           S
ATOM     78  CE  MET    10       2.791   3.137  15.126  1.00  0.00           C
ATOM     79  N   LEU    11       5.201  -1.362  12.881  1.00  0.00
ATOM     80  CA  LEU    11       3.819  -1.576  12.487  1.00  0.00
ATOM     81  CB  LEU    11       2.911  -1.432  13.710  1.00  0.00
ATOM     82  C   LEU    11       3.453  -0.596  11.370  1.00  0.00
ATOM     83  O   LEU    11       2.867  -0.987  10.362  1.00  0.00
ATOM     84  CG  LEU    11       3.187  -2.361  14.896  1.00  0.00           C
ATOM     85  CD1 LEU    11       2.873  -3.811  14.554  1.00  0.00           C
ATOM     86  CD2 LEU    11       2.397  -1.915  16.117  1.00  0.00           C
ATOM     87  N   ASN    12       7.566  -0.003  13.376  1.00  0.00
ATOM     88  CA  ASN    12       7.585  -1.206  12.562  1.00  0.00
ATOM     89  CB  ASN    12       8.097  -2.380  13.398  1.00  0.00
ATOM     90  C   ASN    12       6.185  -1.459  11.998  1.00  0.00
ATOM     91  O   ASN    12       6.029  -1.729  10.809  1.00  0.00
ATOM     92  CG  ASN    12       9.502  -2.164  13.921  1.00  0.00           C
ATOM     93  OD1 ASN    12       9.976  -1.031  13.997  1.00  0.00           O
ATOM     94  ND2 ASN    12      10.177  -3.248  14.286  1.00  0.00           N
ATOM     95  N   GLN    13       6.585   1.940  15.094  1.00  0.00
ATOM     96  CA  GLN    13       7.215   2.335  13.845  1.00  0.00
ATOM     97  CB  GLN    13       8.638   2.824  14.123  1.00  0.00
ATOM     98  C   GLN    13       7.182   1.159  12.866  1.00  0.00
ATOM     99  O   GLN    13       6.820   1.324  11.703  1.00  0.00
ATOM    100  CG  GLN    13       9.364   3.353  12.886  1.00  0.00           C
ATOM    101  CD  GLN    13      10.749   3.882  13.203  1.00  0.00           C
ATOM    102  OE1 GLN    13      11.189   3.853  14.353  1.00  0.00           O
ATOM    103  NE2 GLN    13      11.445   4.370  12.183  1.00  0.00           N
ATOM    104  N   PRO    14       5.796   0.297  17.182  1.00  0.00
ATOM    105  CA  PRO    14       4.811   1.123  16.505  1.00  0.00
ATOM    106  CB  PRO    14       4.495   2.349  17.365  1.00  0.00
ATOM    107  C   PRO    14       5.334   1.503  15.118  1.00  0.00
ATOM    108  O   PRO    14       4.615   1.394  14.127  1.00  0.00
ATOM    109  CG  PRO    14       4.826   1.810  18.747  1.00  0.00           C
ATOM    110  CD  PRO    14       5.953   0.833  18.586  1.00  0.00           C
ATOM    111  N   SER    15       8.284  -0.677  17.918  1.00  0.00
ATOM    112  CA  SER    15       7.253  -1.600  17.476  1.00  0.00
ATOM    113  CB  SER    15       6.635  -2.294  18.691  1.00  0.00
ATOM    114  C   SER    15       6.215  -0.841  16.647  1.00  0.00
ATOM    115  O   SER    15       5.827  -1.289  15.570  1.00  0.00
ATOM    116  OG  SER    15       5.619  -3.208  18.288  1.00  0.00           O
ATOM    117  N   ARG    16       9.437   1.701  18.756  1.00  0.00
ATOM    118  CA  ARG    16      10.037   0.958  17.661  1.00  0.00
ATOM    119  CB  ARG    16      11.262   0.197  18.170  1.00  0.00
ATOM    120  C   ARG    16       8.988   0.029  17.045  1.00  0.00
ATOM    121  O   ARG    16       8.842  -0.027  15.825  1.00  0.00
ATOM    122  CG  ARG    16      12.381   1.077  18.717  1.00 10.00           C
ATOM    123  CD  ARG    16      13.171   1.786  17.619  1.00 10.00           C
ATOM    124  NE  ARG    16      13.977   0.858  16.822  1.00 10.00           N
ATOM    125  CZ  ARG    16      13.640   0.343  15.637  1.00 10.00           C
ATOM    126  NH1 ARG    16      12.487   0.636  15.035  1.00 10.00           N
ATOM    127  NH2 ARG    16      14.480  -0.488  15.036  1.00 10.00           N
ATOM    128  N   THR    17       7.778   2.238  20.911  1.00  0.00
ATOM    129  CA  THR    17       7.854   3.182  19.809  1.00  0.00
ATOM    130  CB  THR    17       8.738   4.365  20.209  1.00  0.00
ATOM    131  C   THR    17       8.371   2.464  18.561  1.00  0.00
ATOM    132  O   THR    17       7.809   2.610  17.477  1.00  0.00
ATOM    133  OG1 THR    17      10.066   3.925  20.513  1.00  0.00           O
ATOM    134  CG2 THR    17       8.165   5.118  21.399  1.00  0.00           C
ATOM    135  N   TRP    18       8.438   0.068  22.504  1.00  0.00
ATOM    136  CA  TRP    18       7.066   0.242  22.058  1.00  0.00
ATOM    137  CB  TRP    18       6.225   0.812  23.202  1.00  0.00
ATOM    138  C   TRP    18       7.046   1.138  20.817  1.00  0.00
ATOM    139  O   TRP    18       6.387   0.821  19.828  1.00  0.00
ATOM    140  CG  TRP    18       6.181  -0.062  24.415  1.00  0.00           C
ATOM    141  CD1 TRP    18       7.036  -0.028  25.478  1.00  0.00           C
ATOM    142  CD2 TRP    18       5.237  -1.105  24.694  1.00  0.00           C
ATOM    143  NE1 TRP    18       6.685  -0.985  26.400  1.00  0.00           N
ATOM    144  CE2 TRP    18       5.583  -1.659  25.942  1.00  0.00           C
ATOM    145  CE3 TRP    18       4.133  -1.623  24.009  1.00  0.00           C
ATOM    146  CZ2 TRP    18       4.867  -2.704  26.520  1.00  0.00           C
ATOM    147  CZ3 TRP    18       3.423  -2.661  24.584  1.00  0.00           C
ATOM    148  CH2 TRP    18       3.792  -3.191  25.827  1.00  0.00           C
ATOM    149  N   VAL    19      11.099   0.683  22.976  1.00  0.00
ATOM    150  CA  VAL    19      10.756  -0.560  22.307  1.00  0.00
ATOM    151  CB  VAL    19      10.860  -1.720  23.300  1.00  0.00
ATOM    152  C   VAL    19       9.359  -0.439  21.696  1.00  0.00
ATOM    153  O   VAL    19       9.149  -0.796  20.538  1.00  0.00
ATOM    154  CG1 VAL    19      12.223  -1.766  23.971  1.00  0.00           C
ATOM    155  CG2 VAL    19      10.584  -3.057  22.579  1.00  0.00           C
ATOM    156  N   TYR    20      10.742   3.034  24.402  1.00  0.00
ATOM    157  CA  TYR    20      11.488   3.055  23.155  1.00  0.00
ATOM    158  CB  TYR    20      12.986   3.112  23.457  1.00  0.00
ATOM    159  C   TYR    20      11.108   1.833  22.316  1.00  0.00
ATOM    160  O   TYR    20      10.838   1.953  21.123  1.00  0.00
ATOM    161  CG  TYR    20      13.418   4.341  24.224  1.00  0.00           C
ATOM    162  CD1 TYR    20      13.489   4.323  25.611  1.00  0.00           C
ATOM    163  CD2 TYR    20      13.749   5.518  23.566  1.00  0.00           C
ATOM    164  CE1 TYR    20      13.877   5.444  26.322  1.00  0.00           C
ATOM    165  CE2 TYR    20      14.140   6.644  24.268  1.00  0.00           C
ATOM    166  CZ  TYR    20      14.202   6.600  25.645  1.00  0.00           C
ATOM    167  OH  TYR    20      14.590   7.719  26.348  1.00  0.00           O
TER
"""

def exercise_r_t_matrices():
  r,t = ssb.get_r_t_matrices_from_structure(alpha_pdb_str)
  assert approx_equal(r.elems, 
                      (-0.02358, -0.86374, 0.50337, 
                        0.96052, -0.15919,-0.22815, 
                        0.27720,  0.47811, 0.83340),                      
                      eps = 0.0001)
  assert approx_equal(t.elems, 
                      (0.02846, -2.27608, 1.85022),
                      eps = 0.0001)
  
  try: ssb.get_r_t_matrices_from_structure(t_pdb_str)
  except Sorry: pass
  else: raise Exception_expected
    

def exercise_ss_structure_from_seq():
  pdb_inp1 = iotbx.pdb.input(source_info=None, lines=correct_answer1)
  correct_h1 = pdb_inp1.construct_hierarchy()
  pdb_inp2 = iotbx.pdb.input(source_info=None, lines=correct_answer1)
  correct_h2 = pdb_inp2.construct_hierarchy()

  test_h = ssb.make_ss_structure_from_seq(alpha_pdb_str, "ACEDGFIHKMLNQPSRTWVY")

  assert correct_h1.is_similar_hierarchy(other=correct_h2)
  
  #assert test_h.is_similar_hierarchy(other=correct_h1)
  
  #print test_h.overall_counts().show()
  #print correct_h1.overall_counts().show()
  
  assert approx_equal(test_h.atoms().extract_xyz(), 
                      test_h.atoms().extract_xyz(), eps=0.002)
  
  try: ssb.make_ss_structure_from_seq(alpha_pdb_str, "")
  except Sorry: pass
  else: raise Exception_expected
  
  

def exercise():
  exercise_r_t_matrices()
  exercise_ss_structure_from_seq()
  #sys.stdout.flush()
  #unittest.TextTestRunner(stream=sys.stdout, verbosity = 2 ).run( alltests )

if (__name__ == "__main__"):
  exercise()