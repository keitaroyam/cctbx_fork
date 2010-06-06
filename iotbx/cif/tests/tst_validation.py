from libtbx.test_utils import Exception_expected
from iotbx import cif
from iotbx.cif import validation
from iotbx.cif.validation import dictionary, ValidationError

from urllib2 import urlopen, URLError
from cStringIO import StringIO

cif_core_dic_url = "ftp://ftp.iucr.org/pub/cif_core.dic"
cif_mm_dic_url = "ftp://ftp.iucr.org/pub/cif_mm.dic"

def exercise():
  if not cif.has_antlr3:
    print "Skipping tst_validation.py (antlr3 is not available)"
    return
  exercise_validation()

def exercise_validation():
  try:
    cd = dictionary(cif.fast_reader(file_object=urlopen(
      cif_core_dic_url)).model())
  except URLError:
    print "Skipping cif validation tests because of URLError"
    return
  #
  cm_invalid = cif.fast_reader(input_string=cif_invalid).model()
  s = StringIO()
  cm_invalid.validate(cd, out=s)
  assert sorted(cd.err.errors.keys()) == [
    2001, 2002, 2101, 2102, 2501, 2503, 2504, 2505, 2506]
  assert sorted(cd.err.warnings.keys()) == [1001]
  cm_valid = cif.fast_reader(input_string=cif_valid).model()
  cd.err.reset()
  s = StringIO()
  cm_valid.validate(cd, out=s)
  assert len(cd.err.errors.keys()) == 0
  assert len(cd.err.warnings.keys()) == 0
  try:
    cd2 = dictionary(cif.fast_reader(file_object=urlopen(
      cif_mm_dic_url)).model())
  except NotImplementedError: pass
  else: raise Exception_expected


cif_invalid = """data_1
_made_up_name a                            # warning 1001
_space_group_IT_number b                   # error 2001
_diffrn_reflns_number 2000(1)              # error 2002
_refine_ls_abs_structure_Flack -0.3        # error 2101
_diffrn_radiation_probe rubbish            # error 2102

loop_
_cell_length_a 10 10                       # error 2501

# error 2504
loop_
_atom_site_label
_atom_site_chemical_conn_number
O1 1

# error 2503
loop_
_atom_site_aniso_label
N1
N2

# error 2505
loop_
_space_group_symop_operation_xyz
x,y,z
-x,-y,-z

_atom_site_adp_type Uani                   # error 2506
"""

cif_valid = """data_1
_space_group_IT_number 2
_diffrn_reflns_number 2000
_refine_ls_abs_structure_Flack 0.3
_diffrn_radiation_probe x-ray
_cell_length_a 10

loop_
_atom_site_label
_atom_site_chemical_conn_number
_atom_site_adp_type
O1 1 Uani
N1 2 Uani
N2 3 Uani

loop_
_chemical_conn_atom_number
_chemical_conn_atom_type_symbol
1 O
2 N
3 N

loop_
_atom_site_aniso_label
N1
N2

loop_
_space_group_symop_id
_space_group_symop_operation_xyz
1 x,y,z
2 -x,-y,-z
"""

if __name__ == "__main__":
  exercise()
  print "OK"
