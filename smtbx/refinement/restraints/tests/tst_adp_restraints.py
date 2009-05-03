from libtbx.test_utils import approx_equal
from smtbx.refinement.restraints import adp_restraints
from iotbx import shelx
from cctbx.array_family import flex
from cctbx import crystal
import cStringIO

def trial_structure():
  builder = shelx.afixed_crystal_structure_builder()
  stream = shelx.command_stream(
    file=cStringIO.StringIO(sucrose))
  l_cs = shelx.crystal_symmetry_parser(stream, builder)
  l_afix = shelx.afix_parser(l_cs.filtered_commands(), builder)
  l_xs = shelx.atom_parser(l_afix.filtered_commands(), builder)
  l_xs.parse()
  return l_xs.builder.structure

def get_pair_sym_table(xray_structure):
  asu_mappings = xray_structure.asu_mappings(buffer_thickness=3.5)
  pair_asu_table = crystal.pair_asu_table(asu_mappings=asu_mappings)
  scattering_types = xray_structure.scatterers().extract_scattering_types()
  pair_asu_table.add_covalent_pairs(
    scattering_types, exclude_scattering_types=flex.std_string(("H","D")))
  return pair_asu_table.extract_pair_sym_table()

def exercise_adp_similarity():
  xray_structure = trial_structure()
  pair_sym_table = get_pair_sym_table(xray_structure)
  for table in (None,pair_sym_table):
    if table is None: xs = xray_structure
    else: xs = None
    restraints = \
      adp_restraints.adp_similarity_restraints(
        xray_structure=xs,
        pair_sym_table=table)
    assert restraints.proxies.size() == 24
    i_seqs = (9,14,28,32,36,38)
    restraints = \
      adp_restraints.adp_similarity_restraints(
        xray_structure=xs,
        pair_sym_table=table,
        i_seqs=i_seqs)
    expected_i_seqs = ((9,32),(14,36),(32,36),(36,38))
    expected_weights = (625,156.25,625,625)
    proxies = restraints.proxies
    assert proxies.size() == len(expected_i_seqs)
    for i in range(proxies.size()):
      assert approx_equal(proxies[i].i_seqs, expected_i_seqs[i])
      assert approx_equal(proxies[i].weight, expected_weights[i])

def exercise_rigid_bond():
  xray_structure = trial_structure()
  pair_sym_table = get_pair_sym_table(xray_structure)
  for table in (None,pair_sym_table):
    if table is None: xs = xray_structure
    else: xs = None
    restraints = \
      adp_restraints.rigid_bond_restraints(
        xray_structure=xs,
        pair_sym_table=table)
    assert restraints.proxies.size() == 60
    i_seqs = (9,14,28,32,36,38)
    restraints = \
      adp_restraints.rigid_bond_restraints(
        xray_structure=xs,
        pair_sym_table=table,
        i_seqs=i_seqs)
    expected_i_seqs = (
      (9,32),(9,36),(14,36),(14,32),(14,38),(32,36),(32,38),(36,38))
    expected_weights = [10000]*len(expected_i_seqs)
    proxies = restraints.proxies
    assert proxies.size() == len(expected_i_seqs)
    for i in range(proxies.size()):
      assert approx_equal(proxies[i].i_seqs, expected_i_seqs[i])
      assert approx_equal(proxies[i].weight, expected_weights[i])

def exercise_isotropic_adp():
  xray_structure = trial_structure()
  pair_sym_table = get_pair_sym_table(xray_structure)
  for table in (None,pair_sym_table):
    restraints = \
      adp_restraints.isotropic_adp_restraints(
        xray_structure=xray_structure,
        pair_sym_table=table)
    assert restraints.proxies.size() == 23
    i_seqs = (9,14,28,32,36,38)
    expected_weights = (100,25,100,100,100,100)
    restraints = \
      adp_restraints.isotropic_adp_restraints(
        xray_structure=xray_structure,
        pair_sym_table=table,
        i_seqs=i_seqs)
    proxies = restraints.proxies
    assert proxies.size() == len(i_seqs)
    for i in range(proxies.size()):
      assert approx_equal(proxies[i].i_seq, i_seqs[i])
      assert approx_equal(proxies[i].weight, expected_weights[i])

sucrose = """
CELL 0.71073 7.783 8.7364 10.9002 90 102.984 90
ZERR 2 0.001 0.0012 0.0015 0 0.009 0
LATT -1
SYMM -X,0.5+Y,-Z
SFAC C H O
UNIT 24 44 22
L.S. 4
PLAN  20
FMAP 2.0
WGHT 0.0337 0.571
FVAR 0.84821

O1    3    -0.13179  0.93570  0.87720  11.00000  0.02420  0.01729  0.01969 =
 0.00001  0.00918 -0.00107
O2    3    -0.21408  0.78843  1.08112  11.00000  0.04672  0.03240  0.02508 =
 0.00423  0.01458  0.00726
AFIX 147
H2    2    -0.22836  0.87667  1.10246  11.00000 -1.50000
AFIX 0
O3    3    -0.14520  0.52065  0.84834  11.00000  0.04916  0.01846  0.06605 =
 -0.00844  0.02398 -0.01033
AFIX 147
H3    2    -0.07328  0.45411  0.84224  11.00000 -1.50000
AFIX 0
O4    3     0.20238  0.58702  0.80890  11.00000  0.04854  0.02741  0.03541 =
 0.01068  0.02069  0.01991
AFIX 147
H4    2     0.23477  0.57046  0.74356  11.00000 -1.50000
AFIX 0
O5    3     0.24774  0.89795  0.72923  11.00000  0.02167  0.02879  0.03082 =
 0.00009  0.00845 -0.00120
AFIX 147
H5    2     0.32331  0.95866  0.76431  11.00000 -1.50000
AFIX 0
O6    3    -0.18368  1.23984  0.71226  11.00000  0.01343  0.02056  0.02345 =
 -0.00511  0.00016  0.00224
O7    3    -0.46084  1.09572  0.82680  11.00000  0.03193
AFIX 147
H7    2    -0.36045  1.06261  0.85160  11.00000 -1.50000
AFIX 0
O8    3    -0.59003  1.23524  0.47746  11.00000  0.01945  0.02878  0.03112 =
 0.00434 -0.00153  0.00405
AFIX 147
H8    2    -0.60003  1.32509  0.49648  11.00000 -1.50000
AFIX 0
O9    3    -0.29487  1.01637  0.42547  11.00000  0.02894  0.02031  0.02185 =
 -0.00443  0.00461 -0.00199
AFIX 147
H9    2    -0.30544  0.93748  0.46386  11.00000 -1.50000
AFIX 0
O10   3     0.12117  1.09915  0.52951  11.00000  0.02408  0.03396  0.02988 =
 0.00616  0.01181  0.00272
AFIX 147
H10   2     0.16551  1.02705  0.57361  11.00000 -1.50000
AFIX 0
O11   3    -0.10850  0.98726  0.67142  11.00000  0.01689  0.01235  0.01998 =
 -0.00027  0.00248 -0.00141
C1    1    -0.20579  0.78238  0.85937  11.00000  0.02203  0.01926  0.02402 =
 0.00066  0.00157 -0.00320
AFIX 13
H1    2    -0.28211  0.77406  0.77488  11.00000 -1.50000
AFIX 0
C2    1    -0.31566  0.76328  0.95681  11.00000  0.02734  0.03029  0.03031 =
 0.00751  0.00884  0.00006
AFIX 23
H2b   2    -0.41313  0.83513  0.93926  11.00000 -1.50000
H2a   2    -0.36441  0.66066  0.95100  11.00000 -1.50000
AFIX 0
C3    1    -0.05753  0.66367  0.87424  11.00000  0.02805  0.01552  0.02369 =
 -0.00248  0.00826 -0.00241
AFIX 13
H3a   2     0.01094  0.66439  0.96147  11.00000 -1.50000
AFIX 0
C4    1     0.06457  0.69830  0.78593  11.00000  0.02946  0.01896  0.01925 =
 0.00047  0.00519  0.00685
AFIX 13
H4a   2    -0.00161  0.69098  0.69831  11.00000 -1.50000
AFIX 0
C5    1     0.13455  0.85930  0.81269  11.00000  0.01963  0.02443  0.01324 =
 0.00326  0.00219  0.00051
AFIX 13
H5a   2     0.20480  0.86278  0.89936  11.00000 -1.50000
AFIX 0
C6    1    -0.01407  0.97572  0.80019  11.00000  0.01816  0.01494  0.01401 =
 -0.00043  0.00314 -0.00227
AFIX 13
H6    2     0.03755  1.07584  0.82727  11.00000 -1.50000
AFIX 0
C7    1    -0.13016  1.14185  0.62426  11.00000  0.01817  0.01093  0.02059 =
 0.00019  0.00363  0.00050
C8    1     0.04340  1.20325  0.60328  11.00000  0.02033  0.02094  0.02775 =
 0.00263  0.00662 -0.00120
AFIX 23
H8a   2     0.02338  1.30117  0.56050  11.00000 -1.50000
H8b   2     0.12414  1.21943  0.68402  11.00000 -1.50000
AFIX 0
C9    1    -0.28541  1.14328  0.50742  11.00000  0.01633  0.01541  0.02062 =
 0.00363  0.00498  0.00048
AFIX 13
H9a   2    -0.27300  1.23532  0.45876  11.00000 -1.50000
AFIX 0
C10   1    -0.44459  1.16723  0.56511  11.00000  0.01591  0.01798  0.02366 =
 0.00332  0.00262  0.00083
AFIX 13
H10a  2    -0.48086  1.06939  0.59531  11.00000 -1.50000
AFIX 0
C11   1    -0.37215  1.27287  0.67684  11.00000  0.01825  0.01498  0.03036 =
 0.00066  0.00738  0.00339
AFIX 13
H11   2    -0.38844  1.37938  0.64840  11.00000 -1.50000
AFIX 0
C12   1    -0.45320  1.25220  0.78867  11.00000  0.02288  0.03162  0.02954 =
 -0.00536  0.00988  0.00324
AFIX 23
H12b  2    -0.38539  1.31048  0.85880  11.00000 -1.50000
H12a  2    -0.57182  1.29371  0.76852  11.00000 -1.50000
AFIX 0
HKLF 4
END
"""

def run():
  exercise_isotropic_adp()
  exercise_rigid_bond()
  exercise_adp_similarity()
  print "OK"

if __name__ == "__main__":
  run()
