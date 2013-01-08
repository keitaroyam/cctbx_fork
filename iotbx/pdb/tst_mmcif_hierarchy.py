from __future__ import division
from cStringIO import StringIO

from libtbx.test_utils import approx_equal
from libtbx.test_utils import Exception_expected
from libtbx.test_utils import show_diff

import iotbx.cif
from iotbx.pdb.mmcif import pdb_hierarchy_builder


def exercise_pdb_hierachy_builder():
  input_1ab1 = """\
data_1AB1
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_entity_id
_atom_site.label_seq_id
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.auth_seq_id
_atom_site.auth_comp_id
_atom_site.auth_asym_id
_atom_site.auth_atom_id
_atom_site.pdbx_PDB_model_num
ATOM   17  C CA   A THR A 1 2 13.800 11.354 5.944  0.70 2.98  2  THR A CA   1
ATOM   18  C CA   B THR A 1 2 13.872 10.918 5.772  0.30 5.01  2  THR A CA   1
ATOM   19  C C    . THR A 1 2 14.118 10.664 7.274  1.00 2.92  2  THR A C    1
ATOM   20  O O    . THR A 1 2 15.013 9.787  7.376  1.00 3.70  2  THR A O    1
ATOM   21  C CB   A THR A 1 2 12.784 10.610 5.099  0.70 4.35  2  THR A CB   1
ATOM   22  C CB   B THR A 1 2 12.938 9.905  5.108  0.30 1.07  2  THR A CB   1
ATOM   23  O OG1  A THR A 1 2 13.364 9.360  4.756  0.70 5.60  2  THR A OG1  1
ATOM   24  O OG1  B THR A 1 2 12.559 10.450 3.917  0.30 5.43  2  THR A OG1  1
ATOM   25  C CG2  A THR A 1 2 12.451 11.323 3.797  0.70 7.65  2  THR A CG2  1
ATOM   26  C CG2  B THR A 1 2 11.642 9.729  5.862  0.30 2.71  2  THR A CG2  1
ATOM   27  H H    . THR A 1 2 15.500 10.728 5.006  1.00 1.74  2  THR A H    1
ATOM   28  H HA   . THR A 1 2 13.437 12.241 6.128  1.00 4.09  2  THR A HA   1
ATOM   29  H HB   A THR A 1 2 11.947 10.457 5.635  0.70 1.11  2  THR A HB   1
ATOM   30  H HB   B THR A 1 2 13.426 9.030  5.019  0.30 4.20  2  THR A HB   1
ATOM   31  H HG21 A THR A 1 2 13.241 11.856 3.510  0.70 1.00  2  THR A HG21 1
ATOM   32  H HG21 B THR A 1 2 11.196 10.615 5.970  0.30 2.01  2  THR A HG21 1
ATOM   33  H HG22 A THR A 1 2 12.211 10.692 3.092  0.70 5.54  2  THR A HG22 1
ATOM   34  H HG22 B THR A 1 2 11.027 9.120  5.405  0.30 10.62 2  THR A HG22 1
ATOM   35  H HG23 A THR A 1 2 11.693 11.979 3.928  0.70 9.26  2  THR A HG23 1
ATOM   36  H HG23 B THR A 1 2 11.801 9.381  6.801  0.30 8.15  2  THR A HG23 1
# ...trunacted...
HETATM 679 C C1   A EOH B 2 . 16.083 0.909  12.713 0.60 15.95 66 EOH A C1   1
HETATM 680 C C1   B EOH B 2 . 15.565 1.042  13.226 0.40 14.21 66 EOH A C1   1
HETATM 681 C C2   A EOH B 2 . 15.130 -0.269 13.016 0.60 14.85 66 EOH A C2   1
HETATM 682 C C2   B EOH B 2 . 14.830 -0.303 13.058 0.40 15.17 66 EOH A C2   1
HETATM 683 O O    A EOH B 2 . 15.378 1.984  12.104 0.60 12.07 66 EOH A O    1
HETATM 684 O O    B EOH B 2 . 14.811 2.078  12.602 0.40 5.53  66 EOH A O    1
"""
  cif_model = iotbx.cif.reader(input_string=input_1ab1).model()
  builder = pdb_hierarchy_builder(cif_model["1AB1"])
  #assert builder.crystal_symmetry is None
  hierarchy = builder.hierarchy
  atoms = hierarchy.atoms()
  assert atoms[0].segid == "    " # some code relies on this
  s = StringIO()
  hierarchy.show(out=s)
  assert not show_diff(s.getvalue(), """\
model id="" #chains=2
  chain id="A" #residue_groups=1  ### WARNING: duplicate chain id ###
    resid="   2 " #atom_groups=3
      altloc="" resname="THR" #atoms=4
        " C  "
        " O  "
        " H  "
        " HA "
      altloc="A" resname="THR" #atoms=8
        " CA "
        " CB "
        " OG1"
        " CG2"
        " HB "
        "HG21"
        "HG22"
        "HG23"
      altloc="B" resname="THR" #atoms=8
        " CA "
        " CB "
        " OG1"
        " CG2"
        " HB "
        "HG21"
        "HG22"
        "HG23"
  chain id="A" #residue_groups=1  ### WARNING: duplicate chain id ###
    resid="  66 " #atom_groups=2
      altloc="A" resname="EOH" #atoms=3
        " C1 "
        " C2 "
        " O  "
      altloc="B" resname="EOH" #atoms=3
        " C1 "
        " C2 "
        " O  "
""")
  cif_block = hierarchy.as_cif_block()
  builder = pdb_hierarchy_builder(cif_block)
  hierarchy_recycled = builder.hierarchy
  s1 = StringIO()
  hierarchy_recycled.show(out=s1)
  assert not show_diff(s.getvalue(), s1.getvalue())
  #
  input_missing_mandatory_items = """\
data_1AB1
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_entity_id
_atom_site.label_seq_id
_atom_site.occupancy
_atom_site.B_iso_or_equiv
ATOM   17  C A THR A 1 2 0.70 2.98
ATOM   18  C B THR A 1 2 0.30 5.01
ATOM   19  C . THR A 1 2 1.00 2.92
ATOM   20  O . THR A 1 2 1.00 3.70
"""
  cif_model = iotbx.cif.reader(input_string=input_missing_mandatory_items).model()
  try: pdb_hierarchy_builder(cif_model["1AB1"])
  except AssertionError, e: pass
  else:
    # TODO: raise a better error here
    raise Exception_expected

  input_4edr = """\
data_4EDR
_cell.length_a           150.582
_cell.length_b           150.582
_cell.length_c           38.633
_cell.angle_alpha        90.000
_cell.angle_beta         90.000
_cell.angle_gamma        120.000
#
_symmetry.space_group_name_H-M             'P 61'
#
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_entity_id
_atom_site.label_seq_id
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.auth_seq_id
_atom_site.auth_comp_id
_atom_site.auth_asym_id
_atom_site.auth_atom_id
_atom_site.pdbx_PDB_model_num
ATOM   1    N  N     . SER A 1 1 21.138  -69.073 17.360  1.00 23.68 108 SER A N     1
ATOM   2    C  CA    . SER A 1 1 22.164  -68.793 18.358  1.00 22.98 108 SER A CA    1
ATOM   3    C  C     . SER A 1 1 23.173  -67.799 17.805  1.00 21.13 108 SER A C     1
ATOM   4    O  O     . SER A 1 1 23.251  -67.594 16.595  1.00 19.34 108 SER A O     1
ATOM   5    C  CB    . SER A 1 1 22.882  -70.080 18.766  1.00 22.68 108 SER A CB    1
ATOM   6    O  OG    . SER A 1 1 23.683  -70.569 17.703  1.00 24.00 108 SER A OG    1
HETATM 2650 MN MN    . MN  F 4 . 9.296   -44.783 -6.320  1.00 44.18 505 MN  A MN    1
#
loop_
_atom_site_anisotrop.id
_atom_site_anisotrop.type_symbol
_atom_site_anisotrop.pdbx_label_atom_id
_atom_site_anisotrop.pdbx_label_alt_id
_atom_site_anisotrop.pdbx_label_comp_id
_atom_site_anisotrop.pdbx_label_asym_id
_atom_site_anisotrop.pdbx_label_seq_id
_atom_site_anisotrop.U[1][1]
_atom_site_anisotrop.U[2][2]
_atom_site_anisotrop.U[3][3]
_atom_site_anisotrop.U[1][2]
_atom_site_anisotrop.U[1][3]
_atom_site_anisotrop.U[2][3]
1    N N   . SER A 1   0.4097 0.2916 0.1984 0.1130  0.0328  0.0375
2    C CA  . SER A 1   0.4035 0.2848 0.1847 0.1242  0.0297  0.0347
3    C C   . SER A 1   0.3744 0.2637 0.1648 0.1278  0.0215  0.0258
4    O O   . SER A 1   0.3494 0.2393 0.1463 0.1236  0.0185  0.0236
5    C CB  . SER A 1   0.4085 0.2738 0.1795 0.1267  0.0311  0.0373
6    O OG  . SER A 1   0.4276 0.2843 0.1998 0.1252  0.0273  0.0344
"""

  cif_model = iotbx.cif.reader(input_string=input_4edr).model()
  cif_block = cif_model["4EDR"]
  builder = pdb_hierarchy_builder(cif_block)
  assert approx_equal(builder.crystal_symmetry.unit_cell().parameters(),
                      (150.582, 150.582, 38.633, 90, 90, 120))
  assert builder.crystal_symmetry.space_group_info().symbol_and_number() == \
         'P 61 (No. 169)'
  hierarchy = builder.hierarchy
  s = StringIO()
  hierarchy.show(out=s)
  assert not show_diff(s.getvalue(), """\
model id="" #chains=2
  chain id="A" #residue_groups=1  ### WARNING: duplicate chain id ###
    resid=" 108 " #atom_groups=1
      altloc="" resname="SER" #atoms=6
        " N  "
        " CA "
        " C  "
        " O  "
        " CB "
        " OG "
  chain id="A" #residue_groups=1  ### WARNING: duplicate chain id ###
    resid=" 505 " #atom_groups=1
      altloc="" resname="MN" #atoms=1
        "MN  "
""")
  cif_block = hierarchy.as_cif_block(crystal_symmetry=builder.crystal_symmetry)
  assert "_space_group_symop.operation_xyz" in cif_block
  assert "_cell.length_a" in cif_block
  builder = pdb_hierarchy_builder(cif_block)
  hierarchy_recycled = builder.hierarchy
  s1 = StringIO()
  hierarchy_recycled.show(out=s1)
  assert not show_diff(s.getvalue(), s1.getvalue())
  for hierarchy in (hierarchy, hierarchy_recycled):
    residue_group = hierarchy.residue_groups().next()
    assert residue_group.resseq == ' 108'
    assert residue_group.resseq_as_int() == 108
    atoms = hierarchy.atoms()
    assert atoms[0].serial == '1'
    assert atoms[0].name == ' N  '
    assert atoms[0].b == 23.68
    assert atoms[0].uij_is_defined()
    assert approx_equal(
      atoms[0].uij, (0.4097, 0.2916, 0.1984, 0.113, 0.0328, 0.0375))
    assert atoms[1].serial == '2'
    assert atoms[1].name == ' CA '
    assert atoms[1].b == 22.98
    assert atoms[1].uij_is_defined()
    assert approx_equal(
      atoms[1].uij, (0.4035, 0.2848, 0.1847, 0.1242, 0.0297, 0.0347))
    assert not atoms[6].uij_is_defined()
    assert atoms[6].serial == '2650'
    assert atoms[6].name == 'MN  '
    assert atoms[6].b == 44.18
    assert approx_equal(atoms[6].uij, (-1, -1, -1, -1, -1, -1))
  #
  input_1ezu = """\
data_1EZU
#
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_entity_id
_atom_site.label_seq_id
_atom_site.pdbx_PDB_ins_code
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.auth_seq_id
_atom_site.auth_comp_id
_atom_site.auth_asym_id
_atom_site.auth_atom_id
_atom_site.pdbx_PDB_model_num
ATOM   3422 N  N   . GLY C 2 164 ? -25.713 -9.765  41.937  1.00 38.56 584 GLY C N   1
ATOM   3423 C  CA  . GLY C 2 164 ? -27.027 -9.485  41.364  1.00 38.07 584 GLY C CA  1
ATOM   3424 C  C   . GLY C 2 164 ? -27.645 -10.541 40.476  1.00 35.83 584 GLY C C   1
ATOM   3425 O  O   . GLY C 2 164 ? -27.554 -11.745 40.752  1.00 35.99 584 GLY C O   1
ATOM   3426 N  N   . PHE C 2 165 A -28.265 -10.093 39.385  1.00 34.13 584 PHE C N   1
ATOM   3427 C  CA  . PHE C 2 165 A -28.937 -11.016 38.471  1.00 36.09 584 PHE C CA  1
ATOM   3428 C  C   . PHE C 2 165 A -28.697 -10.685 37.018  1.00 36.74 584 PHE C C   1
ATOM   3429 O  O   . PHE C 2 165 A -28.853 -9.536  36.627  1.00 39.19 584 PHE C O   1
ATOM   3430 C  CB  . PHE C 2 165 A -30.444 -10.982 38.748  1.00 35.84 584 PHE C CB  1
ATOM   3431 C  CG  . PHE C 2 165 A -30.802 -11.298 40.174  1.00 39.04 584 PHE C CG  1
ATOM   3432 C  CD1 . PHE C 2 165 A -30.914 -10.282 41.119  1.00 39.32 584 PHE C CD1 1
ATOM   3433 C  CD2 . PHE C 2 165 A -30.983 -12.614 40.579  1.00 36.86 584 PHE C CD2 1
ATOM   3434 C  CE1 . PHE C 2 165 A -31.203 -10.572 42.458  1.00 35.08 584 PHE C CE1 1
ATOM   3435 C  CE2 . PHE C 2 165 A -31.271 -12.924 41.904  1.00 32.57 584 PHE C CE2 1
ATOM   3436 C  CZ  . PHE C 2 165 A -31.379 -11.898 42.850  1.00 32.97 584 PHE C CZ  1
"""
  cif_model = iotbx.cif.reader(input_string=input_1ezu).model()
  cif_block = cif_model["1EZU"]
  builder = pdb_hierarchy_builder(cif_block)
  hierarchy = builder.hierarchy
  residue_groups = list(hierarchy.residue_groups())
  assert residue_groups[0].icode == " "
  assert residue_groups[1].icode == "A"
  s = StringIO()
  hierarchy.show(out=s)
  assert not show_diff(s.getvalue(), """\
model id="" #chains=1
  chain id="C" #residue_groups=2
    resid=" 584 " #atom_groups=1
      altloc="" resname="GLY" #atoms=4
        " N  "
        " CA "
        " C  "
        " O  "
    resid=" 584A" #atom_groups=1
      altloc="" resname="PHE" #atoms=11
        " N  "
        " CA "
        " C  "
        " O  "
        " CB "
        " CG "
        " CD1"
        " CD2"
        " CE1"
        " CE2"
        " CZ "
""")
  cif_block = hierarchy.as_cif_block()
  builder = pdb_hierarchy_builder(cif_block)
  hierarchy_recycled = builder.hierarchy
  s1 = StringIO()
  hierarchy_recycled.show(out=s1)
  assert not show_diff(s.getvalue(), s1.getvalue())

  input_charges = """\
data_charges
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_entity_id
_atom_site.label_seq_id
_atom_site.pdbx_PDB_ins_code
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.Cartn_x_esd
_atom_site.Cartn_y_esd
_atom_site.Cartn_z_esd
_atom_site.occupancy_esd
_atom_site.B_iso_or_equiv_esd
_atom_site.pdbx_formal_charge
_atom_site.auth_seq_id
_atom_site.auth_comp_id
_atom_site.auth_asym_id
_atom_site.auth_atom_id
_atom_site.pdbx_PDB_model_num
  HETATM 2932 CA CA  . CA  J 2 .   ? 221.154 27.397 60.094 1.00 49.40  ? ? ? ? ? 2 1123 CA  C CA  1
  HETATM 2996 O  O1S . MES D 4 .   ? 47.470 -6.157  23.319 1.00 13.84 ? ? ? ? ? -1 1653 MES F O1S 1
  HETATM 2997 O  O2S . MES D 4 .   ? 47.327 -5.296  20.939 1.00 15.26 ? ? ? ? ? 1-  1653 MES F O2S 1
"""
  hierarchy = iotbx.pdb.input(
    lines=input_charges.splitlines(),
    source_info=None).construct_hierarchy()
  atoms = hierarchy.atoms()
  assert atoms[0].charge == "2+"
  assert atoms[1].charge == "1-"
  assert atoms[2].charge == "1-"
  s = StringIO()
  hierarchy.show(out=s)
  assert not show_diff(s.getvalue(), """\
model id="" #chains=2
  chain id="C" #residue_groups=1
    resid="1123 " #atom_groups=1
      altloc="" resname="CA" #atoms=1
        "CA  "
  chain id="F" #residue_groups=1
    resid="1653 " #atom_groups=1
      altloc="" resname="MES" #atoms=2
        " O1S"
        " O2S"
""")
  cif_block = hierarchy.as_cif_block()
  builder = pdb_hierarchy_builder(cif_block)
  hierarchy_recycled = builder.hierarchy
  s1 = StringIO()
  hierarchy_recycled.show(out=s1)
  assert not show_diff(s.getvalue(), s1.getvalue())
  atoms = hierarchy.atoms()
  assert atoms[0].charge == "2+"
  assert atoms[1].charge == "1-"
  assert atoms[2].charge == "1-"

def exercise_pdb_hierarchy_sequence_as_cif_block():
  pdb_atom_site_loop_header = """\
data_mmcif
  loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_entity_id
_atom_site.label_seq_id
_atom_site.pdbx_PDB_ins_code
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.Cartn_x_esd
_atom_site.Cartn_y_esd
_atom_site.Cartn_z_esd
_atom_site.occupancy_esd
_atom_site.B_iso_or_equiv_esd
_atom_site.pdbx_formal_charge
_atom_site.auth_seq_id
_atom_site.auth_comp_id
_atom_site.auth_asym_id
_atom_site.auth_atom_id
_atom_site.pdbx_PDB_model_num
"""

  # simple example with multiple copies of chain
  input_4ehz = """\
ATOM   2    C CA  . GLU A 1 6   ? -35.647 65.380  -11.775 1.00 65.78  ? ? ? ? ? ? 858  GLU A CA  1
ATOM   11   C CA  . LYS A 1 7   ? -34.996 68.963  -10.712 1.00 89.52  ? ? ? ? ? ? 859  LYS A CA  1
ATOM   20   C CA  . LYS A 1 8   ? -31.415 68.325  -9.529  1.00 98.54  ? ? ? ? ? ? 860  LYS A CA  1
ATOM   29   C CA  . PRO A 1 9   ? -29.858 70.569  -6.813  1.00 103.45 ? ? ? ? ? ? 861  PRO A CA  1
ATOM   36   C CA  . ALA A 1 10  ? -26.545 72.463  -7.079  1.00 98.87  ? ? ? ? ? ? 862  ALA A CA  1
ATOM   41   C CA  . THR A 1 11  ? -23.410 70.412  -7.767  1.00 90.75  ? ? ? ? ? ? 863  THR A CA  1
ATOM   48   C CA  . GLU A 1 12  ? -21.306 71.534  -4.804  1.00 75.15  ? ? ? ? ? ? 864  GLU A CA  1
ATOM   57   C CA  . VAL A 1 13  ? -17.543 70.954  -4.809  1.00 49.52  ? ? ? ? ? ? 865  VAL A CA  1
ATOM   64   C CA  . ASP A 1 14  ? -16.048 68.671  -2.185  1.00 26.98  ? ? ? ? ? ? 866  ASP A CA  1
ATOM   72   C CA  . PRO A 1 15  ? -12.276 69.450  -2.061  1.00 27.34  ? ? ? ? ? ? 867  PRO A CA  1
ATOM   79   C CA  . THR A 1 16  ? -11.669 65.942  -0.699  1.00 23.73  ? ? ? ? ? ? 868  THR A CA  1
ATOM   86   C CA  . HIS A 1 17  ? -13.266 64.157  -3.671  1.00 23.80  ? ? ? ? ? ? 869  HIS A CA  1
ATOM   96   C CA  . PHE A 1 18  ? -10.664 63.252  -6.277  1.00 14.88  ? ? ? ? ? ? 870  PHE A CA  1
ATOM   107  C CA  . GLU A 1 19  ? -12.022 62.182  -9.666  1.00 23.47  ? ? ? ? ? ? 871  GLU A CA  1
ATOM   116  C CA  . LYS A 1 20  ? -10.351 59.111  -11.117 1.00 17.57  ? ? ? ? ? ? 872  LYS A CA  1
ATOM   125  C CA  . ARG A 1 21  ? -10.204 60.546  -14.661 1.00 19.09  ? ? ? ? ? ? 873  ARG A CA  1
ATOM   136  C CA  . PHE A 1 22  ? -7.912  63.384  -13.545 1.00 22.03  ? ? ? ? ? ? 874  PHE A CA  1
ATOM   147  C CA  . LEU A 1 23  ? -5.613  61.332  -11.271 1.00 18.20  ? ? ? ? ? ? 875  LEU A CA  1
ATOM   155  C CA  . LYS A 1 24  ? -2.583  60.745  -13.513 1.00 26.05  ? ? ? ? ? ? 876  LYS A CA  1
ATOM   2365 C CA  . VAL B 1 13  ? 38.084  -8.470  -5.157  1.00 57.98  ? ? ? ? ? ? 865  VAL B CA  1
ATOM   2372 C CA  . ASP B 1 14  ? 36.468  -6.229  -2.536  1.00 51.96  ? ? ? ? ? ? 866  ASP B CA  1
ATOM   2380 C CA  . PRO B 1 15  ? 32.749  -7.130  -2.340  1.00 48.96  ? ? ? ? ? ? 867  PRO B CA  1
ATOM   2387 C CA  . THR B 1 16  ? 31.935  -3.705  -0.847  1.00 26.72  ? ? ? ? ? ? 868  THR B CA  1
ATOM   2394 C CA  . HIS B 1 17  ? 33.519  -1.814  -3.754  1.00 33.15  ? ? ? ? ? ? 869  HIS B CA  1
ATOM   2404 C CA  . PHE B 1 18  ? 31.094  -0.811  -6.488  1.00 26.55  ? ? ? ? ? ? 870  PHE B CA  1
ATOM   2415 C CA  . GLU B 1 19  ? 32.359  0.467   -9.861  1.00 38.45  ? ? ? ? ? ? 871  GLU B CA  1
ATOM   2424 C CA  . LYS B 1 20  ? 30.409  3.510   -11.036 1.00 33.69  ? ? ? ? ? ? 872  LYS B CA  1
ATOM   2433 C CA  . ARG B 1 21  ? 30.400  2.430   -14.663 1.00 36.58  ? ? ? ? ? ? 873  ARG B CA  1
ATOM   2444 C CA  . PHE B 1 22  ? 28.294  -0.647  -13.791 1.00 38.39  ? ? ? ? ? ? 874  PHE B CA  1
ATOM   2455 C CA  . LEU B 1 23  ? 25.763  1.275   -11.703 1.00 32.87  ? ? ? ? ? ? 875  LEU B CA  1
ATOM   2463 C CA  . LYS B 1 24  ? 22.588  1.723   -13.713 1.00 30.22  ? ? ? ? ? ? 876  LYS B CA  1
"""
  import iotbx.bioinformatics
  from iotbx.pdb.amino_acid_codes import three_letter_given_one_letter
  from cctbx.array_family import flex
  sequence_4ehz = iotbx.bioinformatics.sequence("GDIVSEKKPATEVDPTHFEKRFLK")#RIRDLGEGHF"
  pdb_in = iotbx.pdb.input(
    lines=(pdb_atom_site_loop_header+input_4ehz).splitlines(),
    source_info=None)
  pdb_hierarchy = pdb_in.construct_hierarchy()
  cif_block = iotbx.pdb.mmcif.pdb_hierarchy_as_cif_block_with_sequence(
    pdb_hierarchy, sequences=[sequence_4ehz],
    crystal_symmetry=pdb_in.crystal_symmetry()).cif_block
  assert cif_block['_entity.id'][0] == '1'
  assert cif_block['_entity.type'][0] == 'polymer'
  assert cif_block['_entity.pdbx_number_of_molecules'][0] == '2'
  assert cif_block['_entity_poly.pdbx_seq_one_letter_code'][0] == sequence_4ehz.sequence
  assert cif_block['_entity_poly.pdbx_seq_one_letter_code_can'][0] == sequence_4ehz.sequence
  assert cif_block['_entity_poly.pdbx_strand_id'] == 'A,B'
  assert approx_equal(flex.int(cif_block['_entity_poly_seq.num']), range(1, 25))
  assert cif_block['_entity_poly_seq.entity_id'].all_eq('1')
  assert list(cif_block['_entity_poly_seq.mon_id']) == [
    three_letter_given_one_letter.get(i) for i in sequence_4ehz.sequence]
  #
  # example with modified amino acid - PTR
  input_3zdi = """\
ATOM   1422 C  CA  . ASN A 1 179 ? -11.025 -26.833 -3.747  1.00 86.68  ? ? ? ? ? ? 213  ASN A CA  1
ATOM   1430 C  CA  . VAL A 1 180 ? -7.831  -26.493 -1.696  1.00 82.40  ? ? ? ? ? ? 214  VAL A CA  1
ATOM   1437 C  CA  . SER A 1 181 ? -8.142  -28.602 1.444   1.00 89.69  ? ? ? ? ? ? 215  SER A CA  1
ATOM   1443 C  CA  . PTR A 1 182 ? -5.406  -26.622 3.177   1.00 88.05  ? ? ? ? ? ? 216  PTR A CA  1
ATOM   1459 C  CA  . ILE A 1 183 ? -7.514  -23.621 4.117   1.00 83.90  ? ? ? ? ? ? 217  ILE A CA  1
ATOM   1467 C  CA  . CYS A 1 184 ? -8.907  -21.533 7.009   1.00 86.39  ? ? ? ? ? ? 218  CYS A CA  1
ATOM   1473 C  CA  . SER A 1 185 ? -6.795  -21.356 10.148  1.00 91.03  ? ? ? ? ? ? 219  SER A CA  1
"""
  sequence_3zdi = iotbx.bioinformatics.sequence("NVSYICSR")
  pdb_in = iotbx.pdb.input(
    lines=(pdb_atom_site_loop_header+input_3zdi).splitlines(),
    source_info=None)
  pdb_hierarchy = pdb_in.construct_hierarchy()
  cif_block = iotbx.pdb.mmcif.pdb_hierarchy_as_cif_block_with_sequence(
    pdb_hierarchy, sequences=[sequence_3zdi],
    crystal_symmetry=pdb_in.crystal_symmetry()).cif_block
  assert cif_block['_entity_poly.pdbx_seq_one_letter_code'][0] == 'NVS(PTR)ICSR'
  assert cif_block['_entity_poly.pdbx_seq_one_letter_code_can'][0] == sequence_3zdi.sequence
  assert approx_equal(flex.int(cif_block['_entity_poly_seq.num']), range(1, 9))
  assert list(cif_block['_entity_poly_seq.mon_id']) == [
    'ASN', 'VAL', 'SER', 'PTR', 'ILE', 'CYS', 'SER', 'ARG']
  #
  input_4gln = """\
ATOM   2    C CA  . DTH A 1 1   ? -2.916  5.861  2.629   1.00 16.39 ? ? ? ? ? ? 1   DTH D CA  1
ATOM   9    C CA  . DTY A 1 2   ? 0.533   4.844  3.866   1.00 10.74 ? ? ? ? ? ? 2   DTY D CA  1
ATOM   21   C CA  . DLY A 1 3   ? 3.161   3.111  1.736   1.00 8.24  ? ? ? ? ? ? 3   DLY D CA  1
ATOM   30   C CA  . DLE A 1 4   ? 6.958   3.293  1.625   1.00 7.95  ? ? ? ? ? ? 4   DLE D CA  1
ATOM   38   C CA  . DIL A 1 5   ? 9.053   0.443  0.257   1.00 8.44  ? ? ? ? ? ? 5   DIL D CA  1
ATOM   46   C CA  . DLE A 1 6   ? 12.622  1.402  -0.674  1.00 8.62  ? ? ? ? ? ? 6   DLE D CA  1
ATOM   54   C CA  A DSG A 1 7   ? 14.930  -1.609 -0.756  0.60 11.27 ? ? ? ? ? ? 7   DSG D CA  1
ATOM   55   C CA  B DSG A 1 7   ? 14.934  -1.617 -0.732  0.40 11.77 ? ? ? ? ? ? 7   DSG D CA  1
ATOM   67   C CA  . GLY A 1 8   ? 18.113  -0.249 -2.284  1.00 13.02 ? ? ? ? ? ? 8   GLY D CA  1
ATOM   71   C CA  . DLY A 1 9   ? 21.326  -1.954 -3.288  1.00 17.83 ? ? ? ? ? ? 9   DLY D CA  1
ATOM   80   C CA  . DTH A 1 10  ? 20.765  -0.934 -6.926  1.00 16.38 ? ? ? ? ? ? 10  DTH D CA  1
#
ATOM   472  C CA  . GLU B 2 6   ? 15.798  -6.874 23.843  1.00 31.74 ? ? ? ? ? ? 6   GLU E CA  1
ATOM   477  C CA  . VAL B 2 7   ? 16.644  -3.926 21.599  1.00 15.99 ? ? ? ? ? ? 7   VAL E CA  1
ATOM   484  C CA  . VAL B 2 8   ? 13.767  -1.465 21.234  1.00 10.37 ? ? ? ? ? ? 8   VAL E CA  1
ATOM   491  C CA  . LYS B 2 9   ? 12.953  -1.088 17.521  1.00 8.44  ? ? ? ? ? ? 9   LYS E CA  1
#
HETATM 2537 O O   . HOH E 3 .   ? 8.196   -3.708 8.277   1.00 15.02 ? ? ? ? ? ? 101 HOH D O   1
HETATM 2538 O O   . HOH E 3 .   ? 4.901   -4.298 5.515   1.00 13.08 ? ? ? ? ? ? 102 HOH D O   1
HETATM 2663 O O   . HOH F 3 .   ? 10.535  -2.721 20.049  1.00 15.44 ? ? ? ? ? ? 201 HOH E O   1
HETATM 2664 O O   . HOH F 3 .   ? 0.790   8.695  30.909  1.00 17.06 ? ? ? ? ? ? 202 HOH E O   1
HETATM 2795 O O   . HOH G 3 .   ? 11.265  2.914  43.878  1.00 13.92 ? ? ? ? ? ? 201 HOH F O   1
HETATM 2796 O O   . HOH G 3 .   ? 11.197  11.667 36.108  1.00 17.00 ? ? ? ? ? ? 202 HOH F O   1
"""
  sequence_4gln = [iotbx.bioinformatics.sequence("TYKLILNGKT"),
                   iotbx.bioinformatics.sequence("GQNHHEVVK")]
  pdb_in = iotbx.pdb.input(
    lines=(pdb_atom_site_loop_header+input_4gln).splitlines(),
    source_info=None)
  pdb_hierarchy = pdb_in.construct_hierarchy()
  cif_block = iotbx.pdb.mmcif.pdb_hierarchy_as_cif_block_with_sequence(
    pdb_hierarchy, sequences=sequence_4gln,
    crystal_symmetry=pdb_in.crystal_symmetry()).cif_block
  assert list(cif_block['_entity.id']) == ['1', '2', '3']
  assert list(cif_block['_entity.type']) == ['polymer', 'polymer', 'water']
  assert approx_equal(flex.int(cif_block['_entity_poly_seq.num']),
                      range(1, 11)+range(1, 10))
  assert list(cif_block['_entity_poly_seq.mon_id']) == [
    'DTH', 'DTY', 'DLY', 'DLE', 'DIL', 'DLE', 'DSG', 'GLY', 'DLY', 'DTH',
    'GLY', 'GLN', 'ASN', 'HIS', 'HIS', 'GLU', 'VAL', 'VAL', 'LYS']
  assert list(cif_block['_entity_poly.pdbx_seq_one_letter_code']) == [
    '(DTH)(DTY)(DLY)(DLE)(DIL)(DLE)(DSG)G(DLY)(DTH)', sequence_4gln[1].sequence]
  assert list(cif_block['_entity_poly.pdbx_seq_one_letter_code_can']) == [
    sequence_4gln[0].sequence, sequence_4gln[1].sequence]
  assert approx_equal(flex.int(cif_block['_atom_site.label_entity_id']),
                      [1]*11 + [2]*4 + [3]*6)
  assert list(cif_block['_atom_site.label_seq_id']) == [
    '1', '2', '3', '4', '5', '6', '7', '7', '8', '9', '10', '6', '7', '8', '9',
     '.', '.', '.', '.', '.', '.']
  #
  input_1ezu = """\
ATOM   3971 C  CA  . VAL D 2 16  ? 24.971  -4.493  -3.652  1.00 33.12  ? ? ? ? ? ? 731 VAL D CA  1
ATOM   3978 C  CA  . SER D 2 17  ? 27.194  -3.056  -0.946  1.00 35.47  ? ? ? ? ? ? 732 SER D CA  1
ATOM   3984 C  CA  . LEU D 2 18  ? 26.541  0.123   0.961   1.00 45.29  ? ? ? ? ? ? 733 LEU D CA  1
ATOM   3992 C  CA  . ASN D 2 19  ? 29.777  2.032   1.598   1.00 53.09  ? ? ? ? ? ? 734 ASN D CA  1
ATOM   4000 C  CA  . SER D 2 20  ? 30.737  4.963   3.775   1.00 61.92  ? ? ? ? ? ? 737 SER D CA  1
ATOM   4006 C  CA  . GLY D 2 21  ? 34.478  4.622   4.207   1.00 62.21  ? ? ? ? ? ? 738 GLY D CA  1
ATOM   4010 C  CA  . TYR D 2 22  ? 33.903  0.885   4.483   1.00 54.81  ? ? ? ? ? ? 739 TYR D CA  1
"""
  sequence_1ezu = iotbx.bioinformatics.sequence('VSLNSGY')
  pdb_in = iotbx.pdb.input(
    lines=(pdb_atom_site_loop_header+input_1ezu).splitlines(),
    source_info=None)
  pdb_hierarchy = pdb_in.construct_hierarchy()
  cif_block = iotbx.pdb.mmcif.pdb_hierarchy_as_cif_block_with_sequence(
    pdb_hierarchy, sequences=[sequence_1ezu]).cif_block
  assert list(cif_block['_entity_poly_seq.mon_id']) == [
    'VAL', 'SER', 'LEU', 'ASN', 'SER', 'GLY', 'TYR']
  assert cif_block['_entity_poly.pdbx_seq_one_letter_code'][0] == sequence_1ezu.sequence
  assert cif_block['_entity_poly.pdbx_seq_one_letter_code_can'][0] == sequence_1ezu.sequence
  assert list(cif_block['_atom_site.auth_seq_id']) == [
    '731', '732', '733', '734', '737', '738', '739']
  assert list(cif_block['_atom_site.label_seq_id']) == [
    '1', '2', '3', '4', '5', '6', '7']

def run():
  exercise_pdb_hierarchy_sequence_as_cif_block()
  exercise_pdb_hierachy_builder()


if __name__ == '__main__':
  run()
  print "OK"
