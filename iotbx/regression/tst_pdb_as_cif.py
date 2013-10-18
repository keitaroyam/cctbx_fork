
from __future__ import division
from libtbx.utils import null_out
from cStringIO import StringIO
import os.path

def exercise () :
  from iotbx.command_line import pdb_as_cif
  from iotbx.file_reader import any_file
  if (os.path.isfile("tst_pdb_as_cif_1.cif")) :
    os.remove("tst_pdb_as_cif_1.cif")
  open("tst_pdb_as_cif_1.pdb", "w").write("""\
CRYST1   97.470  113.870  196.190  90.00  90.00  90.00 P 21 21 21   16
SCALE1      0.010260  0.000000  0.000000        0.00000
SCALE2      0.000000  0.008782  0.000000        0.00000
SCALE3      0.000000  0.000000  0.005097        0.00000
ATOM      1  N   MET A  43       8.153  31.407  59.548  1.00182.68           N
ATOM      2  CA  MET A  43       8.561  30.228  58.722  1.00182.68           C
ATOM      3  C   MET A  43       9.997  29.817  59.022  1.00182.68           C
ATOM      4  O   MET A  43      10.910  30.123  58.254  1.00182.68           O
ATOM      5  CB  MET A  43       8.435  30.557  57.229  1.00182.68           C
ATOM      6  CG  MET A  43       7.111  30.162  56.605  1.00182.68           C
ATOM      7  SD  MET A  43       6.779  28.394  56.836  1.00182.68           S
ATOM      8  CE  MET A  43       7.824  27.649  55.560  1.00182.68           C
ATOM      9  N   LEU A  44      10.187  29.092  60.119  1.00182.68           N
ATOM     10  CA  LEU A  44      11.515  28.652  60.526  1.00182.68           C
ATOM     11  C   LEU A  44      12.314  27.929  59.481  1.00182.68           C
ATOM     12  O   LEU A  44      11.991  26.807  59.098  1.00182.68           O
ATOM     13  CB  LEU A  44      11.428  27.808  61.775  1.00182.68           C
ATOM     14  CG  LEU A  44      11.367  28.820  62.893  1.00182.68           C
ATOM     15  CD1 LEU A  44      10.820  28.175  64.124  1.00182.68           C
ATOM     16  CD2 LEU A  44      12.755  29.420  63.073  1.00182.68           C
""")
  pdb_as_cif.run(["tst_pdb_as_cif_1.pdb"], out=null_out())
  assert os.path.isfile("tst_pdb_as_cif_1.cif")
  cif_in = any_file("tst_pdb_as_cif_1.cif")
  hierarchy = cif_in.file_object.construct_hierarchy()
  open("tst_pdb_as_cif_2.pdb", "w").write("""\
CRYST1    1.000    1.000    1.000  90.00  90.00  90.00 P 1
SCALE1      1.000000  0.000000  0.000000        0.00000
SCALE2      0.000000  1.000000  0.000000        0.00000
SCALE3      0.000000  0.000000  1.000000        0.00000
ATOM      1 N    ALA     1      26.216  26.069  22.329  1.00  4.70
ATOM      2 CA   ALA     1      25.368  26.545  21.218  1.00  6.09
ATOM      3 C    ALA     1      26.005  26.154  19.885  1.00 11.13
ATOM      4 O    ALA     1      27.207  25.902  19.835  1.00 16.15
ATOM      5 CB   ALA     1      25.434  28.079  21.272  1.00  4.53
ATOM      6 N    GLY     2      25.198  26.203  18.856  1.00  8.14
ATOM      7 CA   GLY     2      25.677  25.977  17.535  1.00 10.65
ATOM      8 C    GLY     2      26.113  24.580  17.267  1.00  9.83
ATOM      9 O    GLY     2      26.154  23.705  18.108  1.00  9.22
""")
  out = StringIO()
  pdb_as_cif.run(["tst_pdb_as_cif_2.pdb"], out=out)
  assert (out.getvalue() == """\
Converting tst_pdb_as_cif_2.pdb to mmCIF format.
Error converting tst_pdb_as_cif_2.pdb to mmCIF format:
  Missing element symbol for 7 atoms.
""")
  assert not os.path.isfile("tst_pdb_as_cif_2.cif")

if (__name__ == "__main__") :
  exercise()
  print "OK"
