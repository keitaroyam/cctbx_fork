from __future__ import division
import mmtbx.ncs.ncs_utils as nu
import iotbx.ncs as ncs
from iotbx import pdb
import unittest
import sys


class TestMtrixRecFromCif(unittest.TestCase):
  '''Compare the results of reading MTRIX records of PDB and CIF files'''

  # @unittest.SkipTest
  def test_compare_rotation_and_translation(self):
    print 'Running ',sys._getframe().f_code.co_name
    trans_obj1 = ncs.input(pdb_string=test_pdb)
    trans_obj2 = ncs.input(cif_string=test_cif)
    #
    nrg1 = trans_obj1.get_ncs_restraints_group_list()
    nrg2 = trans_obj2.get_ncs_restraints_group_list()

    x1 = nu.concatenate_rot_tran(ncs_restraints_group_list=nrg1)
    x2 = nu.concatenate_rot_tran(ncs_restraints_group_list=nrg2)

    x = (x1 - x2).as_double()
    self.assertEqual(x.min_max_mean().as_tuple(), (0,0,0))
    #
    pdb_hierarchy_inp = pdb.hierarchy.input(pdb_string=test_cif)
    transform_info = pdb_hierarchy_inp.input.process_mtrix_records()
    results = transform_info.as_pdb_string()

    pdb_hierarchy_inp = pdb.hierarchy.input(pdb_string=test_pdb)
    transform_info = pdb_hierarchy_inp.input.process_mtrix_records()
    expected = transform_info.as_pdb_string()

    self.assertEqual(results,expected)


test_pdb = """\
CRYST1   94.730   94.730  250.870  90.00  90.00 120.00 P 65         12
SCALE1      0.010556  0.006095  0.000000        0.00000
SCALE2      0.000000  0.012189  0.000000        0.00000
SCALE3      0.000000  0.000000  0.003986        0.00000
MTRIX1   1  1.000000  0.000000  0.000000        0.00000    1
MTRIX2   1  0.000000  1.000000  0.000000        0.00000    1
MTRIX3   1  0.000000  0.000000  1.000000        0.00000    1
MTRIX1   2 -0.997443  0.000760 -0.071468       59.52120
MTRIX2   2 -0.000162 -0.999965 -0.008376       80.32820
MTRIX3   2 -0.071472 -0.008343  0.997408        2.38680
ATOM      1  N   MET A   1      10.710  38.460  14.825  1.00 89.21           N
ATOM      2  CA  MET A   1      11.257  39.553  13.961  1.00 89.21           C
ATOM      3  C   MET A   1      11.385  40.985  14.516  1.00 89.21           C
ATOM      4  O   MET A   1      12.376  41.648  14.218  1.00 89.21           O
ATOM      5  CB  MET A   1      10.514  39.584  12.633  1.00 72.05           C
ATOM      6  CG  MET A   1      11.115  38.664  11.596  1.00 72.05           C
ATOM      7  SD  MET A   1      12.048  39.609  10.386  1.00 72.05           S
ATOM      8  CE  MET A   1      13.456  40.084  11.391  1.00 72.05           C
ATOM      9  N   ASP A   2      10.381  41.467  15.263  1.00 81.99           N
ATOM     10  CA  ASP A   2      10.350  42.822  15.886  1.00 81.99           C
ATOM     11  C   ASP A   2      10.651  44.060  15.038  1.00 81.99           C
ATOM     12  O   ASP A   2      11.725  44.645  15.140  1.00 81.99           O
ATOM     13  CB  ASP A   2      11.208  42.882  17.167  1.00 70.41           C
ATOM     14  CG  ASP A   2      11.000  44.178  17.963  1.00 70.41           C
ATOM     15  OD1 ASP A   2      10.015  44.907  17.702  1.00 70.41           O
ATOM     16  OD2 ASP A   2      11.821  44.453  18.866  1.00 70.41           O
END
"""

test_cif = """\
data_1A37
#
loop_
_database_PDB_rev_record.rev_num
_database_PDB_rev_record.type
_database_PDB_rev_record.details
2 SOURCE ?
2 COMPND ?
2 REMARK ?
2 SEQRES ?
2 KEYWDS ?
2 HEADER ?
3 VERSN  ?
4 MTRIX1 ?
4 MTRIX2 ?
4 MTRIX3 ?
#
_cell.entry_id           1A37
_cell.length_a           94.730
_cell.length_b           94.730
_cell.length_c           250.870
_cell.angle_alpha        90.00
_cell.angle_beta         90.00
_cell.angle_gamma        120.00
_cell.Z_PDB              12
#
_symmetry.entry_id                         1A37
_symmetry.space_group_name_H-M             'P 65'
_symmetry.pdbx_full_space_group_name_H-M   ?
_symmetry.cell_setting                     ?
_symmetry.Int_Tables_number                ?
_symmetry.space_group_name_Hall            ?
#
loop_
_struct_ncs_oper.id
_struct_ncs_oper.code
_struct_ncs_oper.details
_struct_ncs_oper.matrix[1][1]
_struct_ncs_oper.matrix[1][2]
_struct_ncs_oper.matrix[1][3]
_struct_ncs_oper.matrix[2][1]
_struct_ncs_oper.matrix[2][2]
_struct_ncs_oper.matrix[2][3]
_struct_ncs_oper.matrix[3][1]
_struct_ncs_oper.matrix[3][2]
_struct_ncs_oper.matrix[3][3]
_struct_ncs_oper.vector[1]
_struct_ncs_oper.vector[2]
_struct_ncs_oper.vector[3]
1 given    ? 1.000000  0.000000 0.000000  0.000000  1.000000  0.000000  0.000000  0.000000  1.000000 0.00000  0.00000  0.00000
2 generate ? -0.997443 0.000760 -0.071468 -0.000162 -0.999965 -0.008376 -0.071472 -0.008343 0.997408 59.52120 80.32820 2.38680
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
ATOM 1    N N   . MET A 1 1   ? 10.710 38.460 14.825  1.00 89.21  ? ? ? ? ? ? 1   MET A N   1
ATOM 2    C CA  . MET A 1 1   ? 11.257 39.553 13.961  1.00 89.21  ? ? ? ? ? ? 1   MET A CA  1
ATOM 3    C C   . MET A 1 1   ? 11.385 40.985 14.516  1.00 89.21  ? ? ? ? ? ? 1   MET A C   1
ATOM 4    O O   . MET A 1 1   ? 12.376 41.648 14.218  1.00 89.21  ? ? ? ? ? ? 1   MET A O   1
ATOM 5    C CB  . MET A 1 1   ? 10.514 39.584 12.633  1.00 72.05  ? ? ? ? ? ? 1   MET A CB  1
ATOM 6    C CG  . MET A 1 1   ? 11.115 38.664 11.596  1.00 72.05  ? ? ? ? ? ? 1   MET A CG  1
ATOM 7    S SD  . MET A 1 1   ? 12.048 39.609 10.386  1.00 72.05  ? ? ? ? ? ? 1   MET A SD  1
ATOM 8    C CE  . MET A 1 1   ? 13.456 40.084 11.391  1.00 72.05  ? ? ? ? ? ? 1   MET A CE  1
ATOM 9    N N   . ASP A 1 2   ? 10.381 41.467 15.263  1.00 81.99  ? ? ? ? ? ? 2   ASP A N   1
ATOM 10   C CA  . ASP A 1 2   ? 10.350 42.822 15.886  1.00 81.99  ? ? ? ? ? ? 2   ASP A CA  1
ATOM 11   C C   . ASP A 1 2   ? 10.651 44.060 15.038  1.00 81.99  ? ? ? ? ? ? 2   ASP A C   1
ATOM 12   O O   . ASP A 1 2   ? 11.725 44.645 15.140  1.00 81.99  ? ? ? ? ? ? 2   ASP A O   1
ATOM 13   C CB  . ASP A 1 2   ? 11.208 42.882 17.167  1.00 70.41  ? ? ? ? ? ? 2   ASP A CB  1
ATOM 14   C CG  . ASP A 1 2   ? 11.000 44.178 17.963  1.00 70.41  ? ? ? ? ? ? 2   ASP A CG  1
ATOM 15   O OD1 . ASP A 1 2   ? 10.015 44.907 17.702  1.00 70.41  ? ? ? ? ? ? 2   ASP A OD1 1
ATOM 16   O OD2 . ASP A 1 2   ? 11.821 44.453 18.866  1.00 70.41  ? ? ? ? ? ? 2   ASP A OD2 1
#
"""

if __name__ == "__main__":
  unittest.main(verbosity=0)
