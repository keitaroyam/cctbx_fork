from __future__ import division
from mmtbx.utils.simple_alignment import simple_alignment
from iotbx.ncs.ncs_preprocess import align_residues
from iotbx import pdb
import unittest
import time
import sys


class TestSimpleAlignment(unittest.TestCase):
  """ Test alignment of closely similar sequences  """

  def setUp(self):
    a = "ssssAESSADKFKRQxxxHMDTEGPSKSSPTYCNQMMKRQGMTKGSCKPVNTFVHEPLEDVQ" \
        "NGRNNCHKSSSTLRITDCRLKGSSKYPNCDYTTTDSQKHIIIACDGNPYVPVHFDASV"
    b = "AESSADKFKRQHMDTEGPSKSSPTYCNQMMKRQGMTKGSCKPVNTFVHEPLEDVQ" \
        "NGRNNCHKSSSTLRITDCRLKGSSKYPNCDYTTTDSQkhIIIACDGNPYVPVHFDASVtttt"
    self.seq_a = list(a)
    self.seq_b = list(b)
    self.length_diff = len(b)/len(a)
    # Gaps needed for the inserted, not aligned, letters
    self.gaps_needed = 4 + 3 + 4
    #
    pdb_obj = pdb.hierarchy.input(pdb_string=pdb_str)
    self.ph = pdb_obj.hierarchy
    cache = self.ph.atom_selection_cache()
    self.chain_a = self.ph.models()[0].chains()[0]
    self.chain_b = self.ph.models()[0].chains()[1]
    self.hierarchy_a = self.ph.select(cache.selection('chain A'))
    self.hierarchy_b = self.ph.select(cache.selection('chain B'))

  def test_1(self):
    print sys._getframe().f_code.co_name
    a = 'abcfadx'
    b = 'cabfa'
    seq_a = list(a)
    seq_b = list(b)
    sel_a, sel_b = simple_alignment(seq_a, seq_b, similarity=0.1)
    self.assertEqual([0,1,3,4],list(sel_a))
    self.assertEqual([1,2,3,4],list(sel_b))

  def test_2(self):
    print sys._getframe().f_code.co_name
    sel_a, sel_b = simple_alignment(self.seq_a, self.seq_b, similarity=0.90)
    expected_1 = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 18, 19,
                  20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31,
                  32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43,
                  44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55,
                  56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67,
                  68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79,
                  80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91,
                  92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102,
                  103, 104, 105, 106, 107, 108, 109, 110, 111, 112,
                  113, 114, 115, 116, 117, 118, 119]
    expected_2 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
                  14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
                  26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37,
                  38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49,
                  50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61,
                  62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73,
                  74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85,
                  86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97,
                  98, 99, 100, 101, 102, 103, 104, 105, 106, 107,
                  108, 109, 110, 111, 112]
    self.assertEqual(expected_1,list(sel_a))
    self.assertEqual(expected_2,list(sel_b))

  def test_3(self):
    print sys._getframe().f_code.co_name
    sel_a, sel_b = simple_alignment(self.seq_a, self.seq_b, similarity=0.95)
    # difference is to large
    expected_1 = []
    expected_2 = []
    self.assertEqual(expected_1,list(sel_a))
    self.assertEqual(expected_2,list(sel_b))

  def test_4(self):
    print sys._getframe().f_code.co_name
    sel_a, sel_b, not_sel_a, not_sel_b, chain_a_id, chain_b_id = \
      align_residues(self.hierarchy_a, self.hierarchy_b)
    #
    self.assertEqual(chain_a_id,'A')
    self.assertEqual(chain_b_id,'B')
    #
    atoms_in_A = self.hierarchy_a.atoms().size()
    atoms_in_B = self.hierarchy_b.atoms().size()
    # atom count including  water
    self.assertEqual(32,atoms_in_A)
    self.assertEqual(44,atoms_in_B)
    #
    self.assertEqual(sel_a.size(),25)
    self.assertEqual(sel_b.size(),25)
    #
    self.assertEqual(not_sel_a.size(),7)
    self.assertEqual(not_sel_b.size(),19)
    #
    # note that the side chain of ILE in chain B is removed and that the
    # number of waters is different as well
    expected_sel_a = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
                      16, 17, 21, 22, 23, 24, 25, 26, 27]
    expected_not_sel_a = [18, 19, 20, 28, 29, 30, 31]
    expected_sel_b = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
                      16, 17, 18, 19, 20, 21, 22, 23, 24]
    expected_not_sel_b = [25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37,
                          38, 39, 40, 41, 42, 43]
    self.assertEqual(list(sel_a), expected_sel_a)
    self.assertEqual(list(sel_b), expected_sel_b)
    self.assertEqual(list(not_sel_a), expected_not_sel_a)
    self.assertEqual(list(not_sel_b), expected_not_sel_b)

pdb_str = '''\
CRYST1   37.760   43.710  107.440  90.00 108.54  90.00 P 1 21 1      4
ATOM      1  N   GLY A   1      10.100  14.506  -6.813  1.00 11.02           N
ATOM      2  CA  GLY A   1       9.618  15.911  -6.685  1.00  9.34           C
ATOM      3  C   GLY A   1      10.369  16.727  -7.707  1.00  7.85           C
ATOM      4  O   GLY A   1      11.481  16.388  -8.042  1.00  8.86           O
ATOM      5  N   LYS A   2       9.783  17.791  -8.213  1.00  7.53           N
ATOM      6  CA  LYS A   2      10.481  18.573  -9.209  1.00  7.43           C
ATOM      7  C   LYS A   2      10.199  20.063  -9.068  1.00  6.50           C
ATOM      8  O   LYS A   2       9.065  20.460  -8.837  1.00  4.58           O
ATOM      9  CB  LYS A   2      10.064  18.096 -10.596  1.00 10.22           C
ATOM     10  CG  LYS A   2      10.871  18.687 -11.722  1.00 11.46           C
ATOM     11  CD  LYS A   2      10.092  18.615 -13.014  1.00 19.76           C
ATOM     12  CE  LYS A   2       9.725  17.195 -13.381  1.00 20.40           C
ATOM     13  NZ  LYS A   2      10.922  16.324 -13.540  1.00 26.54           N
ATOM     14  N   ILE A   3      11.226  20.875  -9.282  1.00  6.47           N
ATOM     15  CA  ILE A   3      11.128  22.321  -9.186  1.00  4.49           C
ATOM     16  C   ILE A   3      12.072  22.938 -10.224  1.00  4.38           C
ATOM     17  O   ILE A   3      13.107  22.372 -10.517  1.00  3.75           O
ATOM     18  CB  ILE A   3      11.550  22.813  -7.771  1.00  2.00           C
ATOM     19  CG1 ILE A   3      11.272  24.308  -7.617  1.00  2.44           C
ATOM     20  CG2 ILE A   3      13.048  22.554  -7.541  1.00  2.00           C
ATOM     21  CD1 ILE A   3      11.435  24.816  -6.208  1.00  2.18           C
ATOM     22  N   THR A   4      11.699  24.079 -10.788  1.00  4.32           N
ATOM     23  CA  THR A   4      12.543  24.760 -11.751  1.00  7.18           C
ATOM     24  C   THR A   4      12.633  26.205 -11.328  1.00  5.50           C
ATOM     25  O   THR A   4      11.602  26.824 -11.045  1.00  5.90           O
ATOM     26  CB  THR A   4      11.950  24.736 -13.155  1.00  8.96           C
ATOM     27  OG1 THR A   4      11.629  23.389 -13.508  1.00 14.82           O
ATOM     28  CG2 THR A   4      12.954  25.288 -14.146  1.00 10.81           C
TER
ATOM   1492  N   GLY B   3      30.298  10.660  57.402  1.00  8.41           N
ATOM   1493  CA  GLY B   3      30.111   9.211  57.319  1.00  6.72           C
ATOM   1494  C   GLY B   3      30.875   8.547  58.431  1.00  6.27           C
ATOM   1495  O   GLY B   3      31.907   9.064  58.860  1.00  6.95           O
ATOM   1496  N   LYS B   4      30.353   7.443  58.946  1.00  6.16           N
ATOM   1497  CA  LYS B   4      31.044   6.737  60.009  1.00  9.57           C
ATOM   1498  C   LYS B   4      30.699   5.272  59.908  1.00  8.82           C
ATOM   1499  O   LYS B   4      29.544   4.909  59.671  1.00 10.99           O
ATOM   1500  CB  LYS B   4      30.681   7.309  61.385  1.00 15.37           C
ATOM   1501  CG  LYS B   4      31.286   6.548  62.561  1.00 17.25           C
ATOM   1502  CD  LYS B   4      30.583   6.873  63.875  1.00 19.93           C
ATOM   1503  CE  LYS B   4      30.944   8.264  64.374  1.00 25.63           C
ATOM   1504  NZ  LYS B   4      32.411   8.433  64.713  1.00 32.30           N
ATOM   1505  N   ILE B   5      31.719   4.436  60.038  1.00  6.78           N
ATOM   1506  CA  ILE B   5      31.566   3.002  59.948  1.00  2.83           C
ATOM   1507  C   ILE B   5      32.501   2.424  60.999  1.00  3.23           C
ATOM   1508  O   ILE B   5      33.516   3.037  61.326  1.00  5.50           O
ATOM   1509  CB  ILE B   5      31.947   2.522  58.541  1.00  2.00           C
ATOM   1513  N   THR B   6      32.140   1.279  61.559  1.00  2.00           N
ATOM   1514  CA  THR B   6      32.944   0.619  62.593  1.00  2.91           C
ATOM   1515  C   THR B   6      33.142  -0.836  62.182  1.00  2.66           C
ATOM   1516  O   THR B   6      32.180  -1.560  61.883  1.00  2.00           O
ATOM   1517  CB  THR B   6      32.226   0.656  63.970  1.00  5.04           C
ATOM   1518  OG1 THR B   6      31.894   2.006  64.303  1.00  7.93           O
ATOM   1519  CG2 THR B   6      33.099   0.080  65.064  1.00  5.59           C
ATOM   1520  N   PHE B   7      34.393  -1.258  62.142  1.00  3.13           N
ATOM   1521  CA  PHE B   7      34.709  -2.610  61.743  1.00  4.16           C
ATOM   1522  C   PHE B   7      35.004  -3.435  62.989  1.00  7.18           C
ATOM   1523  O   PHE B   7      35.698  -2.951  63.889  1.00  8.29           O
ATOM   1524  CB  PHE B   7      35.936  -2.591  60.832  1.00  4.23           C
ATOM   1525  CG  PHE B   7      35.889  -1.521  59.766  1.00  5.16           C
ATOM   1526  CD1 PHE B   7      35.279  -1.760  58.545  1.00  4.71           C
ATOM   1527  CD2 PHE B   7      36.474  -0.268  59.990  1.00  4.91           C
ATOM   1528  CE1 PHE B   7      35.248  -0.782  57.557  1.00  5.29           C
ATOM   1529  CE2 PHE B   7      36.447   0.709  59.016  1.00  3.36           C
ATOM   1530  CZ  PHE B   7      35.826   0.443  57.791  1.00  8.22           C
TER
HETATM 2976  O   HOH A 200      -5.015  35.539  13.500  1.00 13.39           O
HETATM 2977  O   HOH A 201      27.397  33.353  -7.193  1.00 42.92           O
HETATM 2978  O   HOH A 202       9.999  12.737  -8.741  1.00 22.09           O
HETATM 2979  O   HOH A 203      20.918  31.300   9.008  1.00 11.57           O
HETATM 3128  O   HOH B 303      38.892  -4.641  42.351  1.00 28.05           O
HETATM 3129  O   HOH B 304      23.863   8.189  55.409  1.00  9.33           O
HETATM 3130  O   HOH B 305      37.020   0.527  42.707  1.00  6.39           O
HETATM 3131  O   HOH B 306      29.889  -7.894  21.701  1.00 17.26           O
HETATM 3132  O   HOH B 307      36.038  -0.748  40.367  1.00  8.62           O
HETATM 3133  O   HOH B 308      31.840 -18.209  58.265  1.00 34.09           O
HETATM 3134  O   HOH B 309      21.378  -6.597  55.543  1.00 21.44           O
HETATM 3135  O   HOH B 310      39.908 -13.756  54.831  1.00 11.05           O
END
'''



def run_selected_tests():
  """  Run selected tests

  1) List in "tests" the names of the particular test you want to run
  2) Comment out unittest.main()
  3) Un-comment unittest.TextTestRunner().run(run_selected_tests())
  """
  tests = ['']
  suite = unittest.TestSuite(map(TestSimpleAlignment,tests))
  return suite

if __name__=='__main__':
  # use for individual tests
  # unittest.TextTestRunner().run(run_selected_tests())

  # Use to run all tests
  t0 = time.time()
  unittest.main()
  print 'Test took {0:.3f} sec'.format(time.time()-t0)
