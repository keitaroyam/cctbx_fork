from cctbx.array_family import flex
from cctbx import miller
import libtbx.load_env
from libtbx.test_utils import approx_equal, show_diff
from libtbx.utils import time_log
from cStringIO import StringIO

def exercise():
  from iotbx import cif
  if not cif.has_antlr3:
    print "Skipping tst_lex_parse_build.py (antlr3 is not available)"
    return
  readers = [cif.python_reader]
  #if libtbx.env.has_module('antlr'):
    #readers.append(cif.fast_reader)
  #else:
    #print "Skipping compiled CIF reader tests"
  builders = [cif.builders.cif_model_builder]
  if libtbx.env.has_module('PyCifRW'):
    builders.append(cif.builders.PyCifRW_model_builder)
  else:
    print "Skipping PyCifRW builder tests"
  for reader in readers:
    for builder in builders:
      cif_model = reader(
        input_string=cif_xray_structure, builder=builder()).model()
      xs_builder = cif.builders.crystal_structure_builder(cif_model['global'])
      xs1 = xs_builder.structure
      # also test construction of cif model from xray structure
      xs_cif_block = xs1.as_cif_block()
      xs2 = cif.builders.crystal_structure_builder(xs_cif_block).structure
      for xs in (xs1, xs2):
        sc = xs.scatterers()
        assert list(sc.extract_labels()) == ['o','c']
        assert list(sc.extract_scattering_types()) == ['O','C']
        assert approx_equal(sc.extract_occupancies(), (0.8, 1))
        assert approx_equal(sc.extract_sites(), ((0.5,0,0),(0,0,0)))
        assert approx_equal(sc.extract_u_star(),
          [(-1, -1, -1, -1, -1, -1), (1e-3, 5e-4, (1e-3)/3, 0, 0, 0)])
        assert approx_equal(sc.extract_u_iso(), (0.1, -1))
        assert approx_equal(xs.unit_cell().parameters(),
                            (10,20,30,90,90,90))
        assert str(xs.space_group_info()) == 'C 1 2/m 1'
      #
      cif_model = reader(
        input_string=cif_miller_array, builder=builder()).model()
      ma_builder = cif.builders.miller_array_builder(cif_model['global'])
      ma1 = ma_builder.arrays()['_refln_F_squared_meas']
      # also test construction of cif model from miller array
      #ma_cif_block = cif.miller_array_as_cif_block(ma1).cif_block
      #ma2 = cif.builders.miller_array_builder(ma_cif_block).array
      for ma in (ma1,):
        sio = StringIO()
        ma.show_array(sio)
        assert not show_diff(sio.getvalue(), """\
(1, 0, 0) 748.71 13.87
(2, 0, 0) 1318.51 24.29
(3, 0, 0) 1333.51 33.75
(4, 0, 0) 196.58 10.85
(5, 0, 0) 3019.71 55.29
(6, 0, 0) 1134.38 23.94
(7, 0, 0) 124.01 15.16
(8, 0, 0) -1.22 10.49
(9, 0, 0) 189.09 20.3
(10, 0, 0) 564.68 35.61
(-10, 1, 0) 170.23 22.26
""")
        sio = StringIO()
        ma.show_summary(sio)
        assert not show_diff(sio.getvalue(), """\
Miller array info: cif:_refln_F_squared_meas,_refln_F_squared_sigma
Observation type: xray.intensity
Type of data: double, size=11
Type of sigmas: double, size=11
Number of Miller indices: 11
Anomalous flag: False
Unit cell: (7.9999, 9.3718, 14.7362, 82.625, 81.527, 81.726)
Space group: P -1 (No. 2)
""")
      arrays = miller.array.from_cif(file_object=StringIO(
        cif_miller_array_template %(
          '_refln_F_calc', '_refln_F_meas', '_refln_F_sigma')))
      assert sorted(arrays.keys()) == ['_refln_F_calc', '_refln_F_meas']
      arrays = miller.array.from_cif(file_object=StringIO(
        cif_miller_array_template %(
          '_refln_A_calc', '_refln_B_calc', '_refln_F_meas')))
      assert sorted(arrays.keys()) == ['_refln_A_calc', '_refln_F_meas']
      assert arrays['_refln_A_calc'].is_complex_array()
      arrays = miller.array.from_cif(file_object=StringIO(
        cif_miller_array_template %(
          '_refln_A_meas', '_refln_B_meas', '_refln_F_meas')))
      assert sorted(arrays.keys()) == ['_refln_A_meas', '_refln_F_meas']
      assert arrays['_refln_A_meas'].is_complex_array()
      arrays = miller.array.from_cif(file_object=StringIO(
        cif_miller_array_template %(
          '_refln_intensity_calc', '_refln_intensity_meas',
          '_refln_intensity_sigma')))
      assert sorted(arrays.keys()) == [
        '_refln_intensity_calc', '_refln_intensity_meas']
      arrays = miller.array.from_cif(file_object=StringIO(
        cif_miller_array_template %(
          '_refln_F_calc', '_refln_phase_calc', '_refln_F_sigma')))
      assert sorted(arrays.keys()) == ['_refln_F_calc']
      assert arrays['_refln_F_calc'].is_complex_array()


cif_xray_structure = """\
data_global
loop_
    _symmetry_equiv_pos_as_xyz
    'x, y, z'
    '-x, y, -z'
    '-x, -y, -z'
    'x, -y, z'
    'x+1/2, y+1/2, z'
    '-x+1/2, y+1/2, -z'
    '-x+1/2, -y+1/2, -z'
    'x+1/2, -y+1/2, z'
_cell_length_a 10
_cell_length_b 20
_cell_length_c 30
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
loop_
    _atom_site_label
    _atom_site_fract_x
    _atom_site_fract_y
    _atom_site_fract_z
    _atom_site_U_iso_or_equiv
    _atom_site_occupancy
    _atom_site_type_symbol
    'o' 0.5 0 0 0.1 0.8 'O'
    'c' 0 0 0 0.2 1 'C'
loop_
    _atom_site_aniso_label
    _atom_site_aniso_U_11
    _atom_site_aniso_U_22
    _atom_site_aniso_U_33
    _atom_site_aniso_U_12
    _atom_site_aniso_U_13
    _atom_site_aniso_U_23
    'c' 0.1 0.2 0.3 0 0 0
"""

cif_miller_array = """\
data_global
loop_
 _symmetry_equiv_pos_as_xyz
 'x, y, z'
 '-x, -y, -z'

_cell_length_a     7.9999
_cell_length_b     9.3718
_cell_length_c    14.7362
_cell_angle_alpha  82.625
_cell_angle_beta   81.527
_cell_angle_gamma  81.726

loop_
 _refln_index_h
 _refln_index_k
 _refln_index_l
 _refln_F_squared_calc
 _refln_F_squared_meas
 _refln_F_squared_sigma
 _refln_observed_status
   1   0   0      756.07      748.71     13.87 o
   2   0   0     1266.94     1318.51     24.29 o
   3   0   0     1381.53     1333.51     33.75 o
   4   0   0      194.77      196.58     10.85 o
   5   0   0     3102.74     3019.71     55.29 o
   6   0   0     1145.05     1134.38     23.94 o
   7   0   0      103.98      124.01     15.16 o
   8   0   0       16.94       -1.22     10.49 o
   9   0   0      194.74      189.09     20.30 o
  10   0   0      581.30      564.68     35.61 o
 -10   1   0      148.83      170.23     22.26 o
"""


cif_miller_array_template = """\
data_global

loop_
 _symmetry_equiv_pos_as_xyz
 'x, y, z'
 '-x, -y, -z'

_cell_length_a     7.9999
_cell_length_b     9.3718
_cell_length_c    14.7362
_cell_angle_alpha  82.625
_cell_angle_beta   81.527
_cell_angle_gamma  81.726

loop_
 _refln_index_h
 _refln_index_k
 _refln_index_l
 %s
 %s
 %s
   1 0 0 1.2 1.3 0.1
   2 0 0 2.3 2.4 0.2
   3 0 0 3.4 3.5 0.3
   4 0 0 4.5 6.7 0.4
"""

if __name__ == '__main__':
  exercise()
  print "OK"
