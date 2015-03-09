from __future__ import division
from  iotbx.pdb.multimer_reconstruction import multimer
from iotbx.ncs.ncs_preprocess import format_num_as_str
from iotbx.ncs.ncs_preprocess import ncs_group_object
from mmtbx.ncs.ncs_search import is_same_transform
from mmtbx.ncs.ncs_utils import apply_transforms
from libtbx.test_utils import approx_equal
from scitbx.array_family import flex
from scitbx import matrix
import iotbx.ncs as ncs
from iotbx import pdb
import unittest
import tempfile
import shutil
import os


class TestMultimerReconstruction(unittest.TestCase):
  '''Test multimer reconstruction from BIOMT and MTRIX records'''

  def setUp(self):
    '''
    Create temporary file: multimer_test_data.pdb
    '''
    self.currnet_dir = os.getcwd()
    self.tempdir = tempfile.mkdtemp('tempdir')
    os.chdir(self.tempdir)
    # Write the test data into a file
    open('multimer_test_data.pdb', 'w').write(pdb_test_data)
    open('multimer_test_data2.pdb', 'w').write(pdb_test_data2)

  # @unittest.SkipTest
  def test_MTRIX(self):
    '''Test MTRIX record processing'''
    # print sys._getframe().f_code.co_name
    cau_expected_results  = [
    [1.0, 1.0, 1.0], [1.0, -1.0, 1.0], [-0.366025, 1.366025, 1.0], [-1.366025, 0.366025, 1.0],
    [1.0, 1.5, 1.0], [94.618, -5.253, 91.582],
    [94.618, -91.582, -5.253], [51.858229, 79.315053, 91.582], [-42.759771, 84.568053, 91.582],
    [94.618, -4.753, 91.582], [62.395, 51.344, 80.786],
    [62.395, -80.786, 51.344], [-13.267688, 79.70763, 80.786], [-75.662688, 28.36363, 80.786],
    [62.395, 51.844, 80.786], [39.954, 51.526, 72.372],
    [39.954, -72.372, 51.526], [-24.645804, 60.364163, 72.372], [-64.599804, 8.838163, 72.372],
    [39.954, 52.026, 72.372]]

    # use MTRIX data
    multimer_data = multimer(
      file_name='multimer_test_data.pdb',
      reconstruction_type='cau')
    cau_multimer_xyz = list(multimer_data.sites_cart())

    cau_multimer_xyz.sort()
    cau_expected_results.sort()
    assert approx_equal(cau_expected_results,cau_multimer_xyz,eps=0.001)

    # Test that the number of MTRIX record to process is correct
    self.assertEqual(multimer_data.number_of_transforms,4)

    # Test getting non-rounded ASU
    source_xyz = multimer_data.get_ncs_hierarchy().atoms().extract_xyz()
    xyz = apply_transforms(
      ncs_coordinates = source_xyz,
      ncs_restraints_group_list = multimer_data.get_ncs_restraints_group_list(),
      total_asu_length = multimer_data.total_asu_length(),
      extended_ncs_selection = flex.size_t_range(source_xyz.size()),
      round_coordinates=False)
    cau_multimer_xyz = list(xyz)
    cau_multimer_xyz.sort()
    assert approx_equal(cau_expected_results,cau_multimer_xyz,eps=0.00001)

    # Test multimer without rounding
    multimer_data = multimer(
      file_name='multimer_test_data.pdb',
      round_coordinates=False,
      reconstruction_type='cau')
    cau_multimer_xyz = list(multimer_data.sites_cart())
    cau_multimer_xyz.sort()
    cau_expected_results.sort()
    assert approx_equal(cau_expected_results,cau_multimer_xyz,eps=0.00001)

  # @unittest.SkipTest
  def test_BIOMT(self):
    '''Test MTRIX record processing'''
    # print sys._getframe().f_code.co_name
    ba_expected_results  = [
    [1.0, 1.0, 1.0], [1.0, -1.0, 1.0], [1.0, 1.0, -1.0], [-1.0, 1.0, 1.0], [1.0, 1.0, -1.0],
    [-1.0, 1.0, -1.0], [-0.366025, 1.366025, 1.0], [-1.366025, 0.366025, 1.0], [1.0, 1.5, 1.0],
    [-1.366025, 0.366025, 0.0], [94.618, -5.253, 91.582], [94.618, -91.582, -5.253],
    [91.582, -5.253, -94.618], [5.253, 94.618, 91.582], [91.582, -5.253, -94.618],
    [5.253, 91.582, -94.618], [51.858229, 79.315053, 91.582], [-42.759771, 84.568053, 91.582],
    [94.618, -4.753, 91.582], [-42.759771, 84.568053, 90.582], [62.395, 51.344, 80.786],
    [62.395, -80.786, 51.344], [80.786, 51.344, -62.395], [-51.344, 62.395, 80.786],
    [80.786, 51.344, -62.395], [-51.344, 80.786, -62.395], [-13.267688, 79.70763, 80.786],
    [-75.662688, 28.36363, 80.786], [62.395, 51.844, 80.786], [-75.662688, 28.36363, 79.786],
    [39.954, 51.526, 72.372], [39.954, -72.372, 51.526], [72.372, 51.526, -39.954],
    [-51.526, 39.954, 72.372], [72.372, 51.526, -39.954], [-51.526, 72.372, -39.954],
    [-24.645804, 60.364163, 72.372], [-64.599804, 8.838163, 72.372], [39.954, 52.026, 72.372],
    [-64.599804, 8.838163, 71.372]]

    # use BIOMT data
    ba_multimer_data = multimer(
      file_name='multimer_test_data.pdb',
      reconstruction_type='ba')
    ba_multimer_xyz = list(ba_multimer_data.sites_cart())

    # The multimer processing is my chain, so we need to sort lists before we compare them
    ba_multimer_xyz.sort()
    ba_expected_results.sort()

    assert approx_equal(ba_expected_results,ba_multimer_xyz,eps=0.001)
    self.assertEqual(ba_multimer_data.number_of_transforms,9)

  # @unittest.SkipTest
  def test_ncs_copies_naming(self):
    # print sys._getframe().f_code.co_name
    transforms_obj = ncs_group_object()
    result =  transforms_obj.make_chains_names(
      ['chain A_001','chain B_001','chain A_002','chain B_002'],('A','B'))
    expected = {'chain A_001': 'C', 'chain B_001': 'D', 'chain A_002': 'E',
                'chain B_002': 'F'}
    self.assertEqual(result,expected)

  def test_identity_tranform_insertion(self):
    """
    Verify that insertion and reordering of the identity transform is done
    properly
    """
    # print sys._getframe().f_code.co_name
    for pdb_str in [pdb_test_data5,pdb_test_data6]:
      ncs_inp = ncs.input(pdb_string=pdb_test_data5)
      transform_info = ncs_inp.build_MTRIX_object()
      self.assertEqual(len(transform_info.r),3)
      self.assertEqual(len(transform_info.t),3)
      self.assertEqual(transform_info.r[0].is_r3_identity_matrix(),True)
      self.assertEqual(transform_info.t[0].is_col_zero(),True)
      sn = [int(x) for x in transform_info.serial_number]
      self.assertEqual(sn,[1,2,3])


  # @unittest.SkipTest
  def test_adding_transforms_directly(self):
    """
    Verify that processing of transforms provided manually is done properly """
    # print sys._getframe().f_code.co_name
    pdb_obj = pdb.hierarchy.input(pdb_string=pdb_test_data4)
    r = [matrix.sqr([0.1,1.0,1.0,0.2,0.5,0.6,0.7,0.8,0.9])]
    r.append(matrix.sqr([1.0,0.2,1.0,0.2,0.5,0.6,0.7,0.8,0.4]))
    t = [matrix.col([0,2,1])]
    t.append(matrix.col([-1,3,-2]))
    transforms_obj = ncs.input(
      pdb_hierarchy_inp = pdb_obj,
      rotations=r,
      translations=t)

    result = transforms_obj.transform_to_ncs
    expected = {'002': ['chain A_002', 'chain B_002'],
                '003': ['chain A_003', 'chain B_003']}
    self.assertEqual(result,expected)
    result = transforms_obj.ncs_selection_str
    expected = 'chain A or chain B'
    self.assertEqual(result,expected)
    # check that if transforms are provided MTRIX record ignored
    pdb_obj = pdb.hierarchy.input(pdb_string=pdb_test_data2)
    transforms_obj = ncs.input(
      pdb_hierarchy_inp = pdb_obj,
      rotations=r,
      translations=t)
    result = transforms_obj.transform_to_ncs
    expected = {'002': ['chain A_002', 'chain B_002'],
                '003': ['chain A_003', 'chain B_003']}
    self.assertEqual(result,expected)
    result = transforms_obj.ncs_selection_str
    expected = 'chain A or chain B'
    self.assertEqual(result,expected)
    # transforms that are not present
    result = transforms_obj.transform_to_ncs.keys()
    expected = ['003', '002']
    self.assertEqual(result,expected)
    # all transforms
    result = transforms_obj.ncs_transform.keys()
    expected = ['001', '002', '003']
    result.sort()
    self.assertEqual(result,expected)

  # @unittest.SkipTest
  def test_transform_application_order(self):
    """
    Verify that transform order is kept even when chain selection is complex
    """
    # print sys._getframe().f_code.co_name
    pdb_inp = pdb.input(source_info=None, lines=pdb_test_data2)
    pdb_obj = pdb.hierarchy.input(pdb_string=pdb_test_data2)
    transform_info = pdb_inp.process_mtrix_records()
    transforms_obj = ncs.input(
      transform_info=transform_info,
      pdb_hierarchy_inp=pdb_obj)

    expected = ['chain A_002', 'chain B_002', 'chain A_003', 'chain B_003']
    self.assertEqual(transforms_obj.transform_chain_assignment,expected)

    expected = {
      'chain A_002': 'C','chain A_003': 'E','chain A_001': 'A',
      'chain B_002': 'D','chain B_003': 'F','chain B_001': 'B'}
    self.assertEqual(transforms_obj.ncs_copies_chains_names,expected)

    expected = [0, 1, 2, 5, 6]
    results = list(transforms_obj.asu_to_ncs_map['chain A'])
    self.assertEqual(results,expected)

    expected = [3, 4]
    results = list(transforms_obj.asu_to_ncs_map['chain B'])
    self.assertEqual(results,expected)

    expected = [7, 8, 9, 12, 13]
    results = list(transforms_obj.ncs_to_asu_map['chain A_002'])
    self.assertEqual(results,expected)

    expected = [17, 18]
    results = list(transforms_obj.ncs_to_asu_map['chain B_003'])
    self.assertEqual(results,expected)

    self.assertEqual(len(transforms_obj.ncs_atom_selection),21)
    self.assertEqual(transforms_obj.ncs_atom_selection.count(True),7)

  # @unittest.SkipTest
  def test_num_to_str(self):
    # print sys._getframe().f_code.co_name
    self.assertEqual(format_num_as_str(946),'946')
    self.assertEqual(format_num_as_str(46),'046')
    self.assertEqual(format_num_as_str(6),'006')
    self.assertEqual(format_num_as_str(0),'000')

  def test_pdb_writing(self):
    # print sys._getframe().f_code.co_name
    """
    Verify that there are no errors processing the write command
    No inception of the output is done.
    To view the output change the write=False to ,write=True
    """
    transforms_obj = ncs_group_object()
    pdb_inp = pdb.input(source_info=None, lines=pdb_test_data2)
    pdb_obj = pdb.hierarchy.input(pdb_string=pdb_test_data2)
    transform_info = pdb_inp.process_mtrix_records()
    transforms_obj.preprocess_ncs_obj(
      transform_info=transform_info,
      pdb_hierarchy_inp=pdb_obj)

    multimer_data = multimer(
      pdb_str=pdb_test_data2,
      reconstruction_type='cau')

    pdb_hierarchy_asu = multimer_data.assembled_multimer

    # print '--- using ASU hierarchy ---'
    pdbstr = transforms_obj.get_transform_records(
      ncs_only=True,
      pdb_hierarchy=pdb_hierarchy_asu,
      write=False)
    # print pdbstr
    # print '='*50

    pdbstr = transforms_obj.get_transform_records(
      ncs_only=False,
      pdb_hierarchy=pdb_hierarchy_asu,
      write=False)
    # print pdbstr

    # print '--- using the hierarchy of only the master NCS ---'
    pdbstr = transforms_obj.get_transform_records(
      pdb_hierarchy=pdb_obj.hierarchy,
      biomt=True,
      write=False)
    # print pdbstr

    # print '--- from xray structure ---'
    xrs = pdb_hierarchy_asu.extract_xray_structure()
    pdbstr = transforms_obj.get_transform_records(
      # xrs=pdb_obj.xray_structure_simple(),
      xrs=xrs,
      biomt=True,
      write=False)
    # print pdbstr
    # print '='*50

  def test_spec_file_format(self):
    """ Verify that spec object are produced properly """
    # print sys._getframe().f_code.co_name

    multimer_data = multimer(
      pdb_str=pdb_test_data2,
      reconstruction_type='cau')

    trans_obj = ncs.input(pdb_string=pdb_test_data2)

    pdb_hierarchy_asu = multimer_data.assembled_multimer
    spec_output = trans_obj.get_ncs_info_as_spec(
      pdb_hierarchy_asu=pdb_hierarchy_asu,write=False)

    trans_obj2 = ncs.input(spec_ncs_groups=spec_output)

    t1 = trans_obj.ncs_transform['002'].r
    t2 = trans_obj2.ncs_transform['002'].r
    self.assertEqual(t1,t2)
    self.assertEqual(len(trans_obj.ncs_transform),len(trans_obj2.ncs_transform))

    t1 = trans_obj.ncs_to_asu_selection
    t1_expected = {'chain A': ['chain C', 'chain E'],
                   'chain B': ['chain D', 'chain F']}
    self.assertEqual(t1,t1_expected)
    t2 = trans_obj2.ncs_to_asu_selection
    t2_expected = {
      'chain A and (resseq 1:3 or resseq 6:7)':
        ['chain C and (resseq 1:3 or resseq 6:7)',
         'chain E and (resseq 1:3 or resseq 6:7)'],
      'chain B and (resseq 4:5)':
        ['chain D and (resseq 4:5)', 'chain F and (resseq 4:5)']}
    self.assertEqual(t2,t2_expected)

    t1 = trans_obj.tr_id_to_selection['chain A_003']
    t1_expected = ('chain A',
                   'chain E')
    self.assertEqual(t1,t1_expected)

    t2 = trans_obj2.tr_id_to_selection['chain A_003']
    t2_expected = ('chain A and (resseq 1:3 or resseq 6:7)',
                   'chain E and (resseq 1:3 or resseq 6:7)')
    self.assertEqual(t2,t2_expected)

  # @unittest.SkipTest
  def test_writing_spec_file(self):
    # print sys._getframe().f_code.co_name
    """
    Verify that there are no errors processing the write command
    No inception of the output is done. Just making sure it does not break
    To view the output change the write=False to ,write=True
    """
    transforms_obj = ncs_group_object()
    pdb_inp = pdb.input(source_info=None, lines=pdb_test_data2)
    pdb_obj = pdb.hierarchy.input(pdb_string=pdb_test_data2)
    transform_info = pdb_inp.process_mtrix_records()
    transforms_obj.preprocess_ncs_obj(
      # transform_info=transform_info,
      # pdb_hierarchy_inp=pdb_obj,
      pdb_inp=pdb_inp)

    asu = multimer(
      pdb_str=pdb_test_data2,
      reconstruction_type='cau')
    transforms_obj.get_ncs_info_as_spec(
      pdb_hierarchy_asu=asu.assembled_multimer,write=False)

  # @unittest.SkipTest
  def test_proper_biomat_application(self):
    """ Test that when building bio-molecule and then finding NCS relatin
    from it, we get the same rotation and translation"""
    pdb_strings = [pdb_test_data7,pdb_test_data8]
    methods = ['ba','cau']
    for method,pdb_string in zip(methods,pdb_strings):
      pdb_inp = pdb.input(source_info=None, lines=pdb_string)
      crystal_symmetry = pdb_inp.crystal_symmetry()
      m = multimer(
        pdb_str=pdb_string,
        round_coordinates=False,
        reconstruction_type=method,
        error_handle=True,eps=1e-2)
      # The exact transforms from pdb_string
      r1_expected = matrix.sqr(
        [0.309017, -0.951057, 0.0,0.951057, 0.309017,-0.0,0.0,0.0,1.0])
      r2_expected = matrix.sqr(
        [-0.809017,-0.587785,0.0,0.587785,-0.809017,-0.0,0.0,0.0,1.0])
      t1_expected = matrix.col([0,0,7])
      t2_expected = matrix.col([0,0,0])
      # Look at biomt records retrieved from PDB file
      if method == 'ba':
        rec = pdb_inp.process_BIOMT_records()
      else:
        rec = pdb_inp.process_mtrix_records()
      r1 = rec.r[1]
      r2 = rec.r[2]
      t1 = rec.t[1]
      t2 = rec.t[2]
      (the_same, transpose) = is_same_transform(r1,t1,r1_expected,t1_expected)
      self.assertTrue(the_same)
      (the_same, transpose)= is_same_transform(r2,t2,r2_expected,t2_expected)
      self.assertTrue(the_same)
      # Look at the rotation and translation found by the NCS search
      s = m.assembled_multimer.as_pdb_string(crystal_symmetry=crystal_symmetry)
      ncs_obj = ncs.input(pdb_string=s)
      r1 = ncs_obj.ncs_transform['002'].r
      t1 = ncs_obj.ncs_transform['002'].t
      r2 = ncs_obj.ncs_transform['003'].r
      t2 = ncs_obj.ncs_transform['003'].t
      (the_same, transpose) = is_same_transform(r1,t1,r1_expected,t1_expected)
      self.assertTrue(the_same)
      (the_same, transpose)= is_same_transform(r2,t2,r2_expected,t2_expected)
      self.assertTrue(the_same)
      self.assertEqual(ncs_obj.number_of_ncs_groups,1)

  # @unittest.SkipTest
  def test_ignoring_mtrix_rec(self):
    """
    Test ignoring MTRIX record when copies already present in file
    """
    pdb_inp = pdb.input(source_info=None, lines=test_pdb_9)
    m = multimer(
        pdb_str=test_pdb_9,
        round_coordinates=False,
        reconstruction_type='cau',
        error_handle=True,eps=1e-2)
    n1 = m.assembled_multimer.atoms().size()
    n2 = pdb_inp.atoms().size()
    self.assertEqual(n1,n2)


  def tearDown(self):
    '''remove temp files and folder'''
    os.chdir(self.currnet_dir)
    shutil.rmtree(self.tempdir)

pdb_test_data = '''\
REMARK   0 Test molecule with BIOMOLECULE: 1
REMARK   0
REMARK   0 The test will generate the biomolecule (the multimer assembly)
REMARK   0 from the transformation matrices writen below
REMARK   0 and then compare the results to the calculated expected one
REMARK 350 CRYSTALLOGRAPHIC OPERATIONS ARE GIVEN.
REMARK 350   BIOMT1   1  1.000000  0.000000  0.000000        0.000000
REMARK 350   BIOMT2   1  0.000000  1.000000  0.000000        0.000000
REMARK 350   BIOMT3   1  0.000000  0.000000  1.000000        0.000000
REMARK 350   BIOMT1   2  1.000000  0.000000  0.000000        0.000000
REMARK 350   BIOMT2   2  0.000000  0.000000 -1.000000        0.000000
REMARK 350   BIOMT3   2  0.000000  1.000000  0.000000        0.000000
REMARK 350   BIOMT1   3  0.000000  0.000000  1.000000        0.000000
REMARK 350   BIOMT2   3  0.000000  1.000000  0.000000        0.000000
REMARK 350   BIOMT3   3 -1.000000  0.000000  0.000000        0.000000
REMARK 350   BIOMT1   4  0.000000 -1.000000  0.000000        0.000000
REMARK 350   BIOMT2   4  1.000000  0.000000  0.000000        0.000000
REMARK 350   BIOMT3   4  0.000000  0.000000  1.000000        0.000000
REMARK 350   BIOMT1   5  0.000000  0.000000  1.000000        0.000000
REMARK 350   BIOMT2   5  0.000000  1.000000  0.000000        0.000000
REMARK 350   BIOMT3   5 -1.000000  0.000000  0.000000        0.000000
REMARK 350   BIOMT1   6  0.000000 -1.000000  0.000000        0.000000
REMARK 350   BIOMT2   6  0.000000  0.000000  1.000000        0.000000
REMARK 350   BIOMT3   6 -1.000000  0.000000  0.000000        0.000000
REMARK 350   BIOMT1   7  0.500000 -0.866025  0.000000        0.000000
REMARK 350   BIOMT2   7  0.866025  0.500000  0.000000        0.000000
REMARK 350   BIOMT3   7  0.000000  0.000000  1.000000        0.000000
REMARK 350   BIOMT1   8 -0.500000 -0.866025  0.000000        0.000000
REMARK 350   BIOMT2   8  0.866025 -0.500000  0.000000        0.000000
REMARK 350   BIOMT3   8  0.000000  0.000000  1.000000        0.000000
REMARK 350   BIOMT1   9  1.000000  0.000000  0.000000        0.000000
REMARK 350   BIOMT2   9  0.000000  1.000000  0.000000        0.500000
REMARK 350   BIOMT3   9  0.000000  0.000000  1.000000        0.000000
REMARK 350   BIOMT1  10 -0.500000 -0.866025  0.000000        0.000000
REMARK 350   BIOMT2  10  0.866025 -0.500000  0.000000        0.000000
REMARK 350   BIOMT3  10  0.000000  0.000000  1.000000       -1.000000
MTRIX1   1  1.000000  0.000000  0.000000        0.00000
MTRIX2   1  0.000000  1.000000  0.000000        0.00000
MTRIX3   1  0.000000  0.000000  1.000000        0.00000
MTRIX1   1  1.000000  0.000000  0.000000        0.00000    1
MTRIX2   1  0.000000  1.000000  0.000000        0.00000    1
MTRIX3   1  0.000000  0.000000  1.000000        0.00000    1
MTRIX1   2  1.000000  0.000000  0.000000        0.00000
MTRIX2   2  0.000000  0.000000 -1.000000        0.00000
MTRIX3   2  0.000000  1.000000  0.000000        0.00000
MTRIX1   3  0.500000 -0.866025  0.000000        0.00000
MTRIX2   3  0.866025  0.500000  0.000000        0.00000
MTRIX3   3  0.000000  0.000000  1.000000        0.00000
MTRIX1   4 -0.500000 -0.866025  0.000000        0.00000
MTRIX2   4  0.866025 -0.500000  0.000000        0.00000
MTRIX3   4  0.000000  0.000000  1.000000        0.00000
MTRIX1   5  1.000000  0.000000  0.000000        0.00000
MTRIX2   5  0.000000  1.000000  0.000000        0.50000
MTRIX3   5  0.000000  0.000000  1.000000        0.00000
ATOM      1   N  ILE A  40       1.000   1.000   1.000  1.00162.33           C
ATOM      2  CA  LEU A  40      94.618  -5.253  91.582  1.00 87.10           C
ATOM      3   C  ARG B  40      62.395  51.344  80.786  1.00107.25           C
HETATM    4  C1  EDO A  40      39.954  51.526  72.372  0.33 60.93           C
'''

pdb_test_data2="""\
MTRIX1   1  1.000000  0.000000  0.000000        0.00000    1
MTRIX2   1  0.000000  1.000000  0.000000        0.00000    1
MTRIX3   1  0.000000  0.000000  1.000000        0.00000    1
MTRIX1   2  0.496590 -0.643597  0.582393        0.00000
MTRIX2   2  0.867925  0.376088 -0.324443        0.00000
MTRIX3   2 -0.010221  0.666588  0.745356        0.00000
MTRIX1   3 -0.317946 -0.173437  0.932111        0.00000
MTRIX2   3  0.760735 -0.633422  0.141629        0.00000
MTRIX3   3  0.565855  0.754120  0.333333        0.00000
ATOM      1  N   THR A   1       9.670  10.289  11.135  1.00 20.00           N
ATOM      2  CA  THR A   2       9.559   8.931  10.615  1.00 20.00           C
ATOM      3  C   THR A   3       9.634   7.903  11.739  1.00 20.00           C
ATOM      4  O   THR B   4      10.449   8.027  12.653  1.00 20.00           O
ATOM      5  CB  THR B   5      10.660   8.630   9.582  1.00 20.00           C
ATOM      6  OG1 THR A   6      10.560   9.552   8.490  1.00 20.00           O
ATOM      7  CG2 THR A   7      10.523   7.209   9.055  1.00 20.00           C
TER
"""

pdb_test_data3="""\
MTRIX1   1  1.000000  0.000000  0.000000        0.00000    1
MTRIX2   1  0.000000  1.000000  0.000000        0.00000    1
MTRIX3   1  0.000000  0.000000  1.000000        0.00000    1
MTRIX1   2  0.309017 -0.809017  0.500000        0.00000
MTRIX2   2  0.809017  0.500000  0.309017        0.00000
MTRIX3   2 -0.500000  0.309017  0.809017        0.00000
MTRIX1   3 -0.809017 -0.500000  0.309017        0.00000
MTRIX2   3  0.500000 -0.309017  0.809017        0.00000
MTRIX3   3 -0.309017  0.809017  0.500000        0.00000
ATOM    749  O   UNK A  90      28.392  67.262  97.682  1.00  0.00           O
ATOM    750  N   UNK A  91      30.420  66.924  98.358  1.00  0.00           N
TER
ATOM   1495  N   UNK B  67      33.124   2.704 114.920  1.00  0.00           N
END
"""

pdb_test_data4="""\
ATOM      1  N   THR A   1       9.670  10.289  11.135  1.00 20.00           N
ATOM      2  CA  THR A   2       9.559   8.931  10.615  1.00 20.00           C
ATOM      3  C   THR A   3       9.634   7.903  11.739  1.00 20.00           C
ATOM      4  O   THR B   4      10.449   8.027  12.653  1.00 20.00           O
ATOM      5  CB  THR B   5      10.660   8.630   9.582  1.00 20.00           C
ATOM      6  OG1 THR A   6      10.560   9.552   8.490  1.00 20.00           O
ATOM      7  CG2 THR A   7      10.523   7.209   9.055  1.00 20.00           C
"""

pdb_test_data5="""\
MTRIX1   1  0.309017 -0.809017  0.500000        0.00000
MTRIX2   1  0.809017  0.500000  0.309017        0.00000
MTRIX3   1 -0.500000  0.309017  0.809017        0.00000
MTRIX1   2 -0.809017 -0.500000  0.309017        0.00000
MTRIX2   2  0.500000 -0.309017  0.809017        0.00000
MTRIX3   2 -0.309017  0.809017  0.500000        0.00000
MTRIX1   3  1.000000  0.000000  0.000000        0.00000    1
MTRIX2   3  0.000000  1.000000  0.000000        0.00000    1
MTRIX3   3  0.000000  0.000000  1.000000        0.00000    1
ATOM    749  O   UNK A  90      28.392  67.262  97.682  1.00  0.00           O
ATOM    750  N   UNK A  91      30.420  66.924  98.358  1.00  0.00           N
TER
ATOM   1495  N   UNK B  67      33.124   2.704 114.920  1.00  0.00           N
END
"""

pdb_test_data6="""\
MTRIX1   1  0.309017 -0.809017  0.500000        0.00000
MTRIX2   1  0.809017  0.500000  0.309017        0.00000
MTRIX3   1 -0.500000  0.309017  0.809017        0.00000
MTRIX1   2 -0.809017 -0.500000  0.309017        0.00000
MTRIX2   2  0.500000 -0.309017  0.809017        0.00000
MTRIX3   2 -0.309017  0.809017  0.500000        0.00000
ATOM    749  O   UNK A  90      28.392  67.262  97.682  1.00  0.00           O
ATOM    750  N   UNK A  91      30.420  66.924  98.358  1.00  0.00           N
TER
ATOM   1495  N   UNK B  67      33.124   2.704 114.920  1.00  0.00           N
END
"""

pdb_test_data3_expected_results = """\
ATOM    749  O   UNK A  90      28.392  67.262  97.682  1.00  0.00           O
ATOM    750  N   UNK A  91      30.420  66.924  98.358  1.00  0.00           N
TER
ATOM   1495  N   UNK B  67      33.124   2.704 114.920  1.00  0.00           N
TER
ATOM    749  O   UNK C  90       3.199  86.786  85.616  1.00  0.00           O
ATOM    750  N   UNK C  91       4.437  88.467  85.044  1.00  0.00           N
TER
ATOM   1495  N   UNK D  67      65.508  63.662  77.246  1.00  0.00           N
TER
ATOM    749  O   UNK E  90     -26.415  72.437  94.483  1.00  0.00           O
ATOM    750  N   UNK E  91     -27.678  74.103  93.921  1.00  0.00           N
TER
ATOM   1495  N   UNK F  67       7.362 108.699  49.412  1.00  0.00           N
TER
"""

pdb_test_data7 = '''\
REMARK 350   BIOMT1   1  1.000000  0.000000  0.000000        0.00000
REMARK 350   BIOMT2   1  0.000000  1.000000  0.000000        0.00000
REMARK 350   BIOMT3   1  0.000000  0.000000  1.000000        0.00000
REMARK 350   BIOMT1   2  0.309017 -0.951057  0.000000        0.00000
REMARK 350   BIOMT2   2  0.951057  0.309017 -0.000000        0.00000
REMARK 350   BIOMT3   2  0.000000  0.000000  1.000000        7.00000
REMARK 350   BIOMT1   3 -0.809017 -0.587785  0.000000        0.00000
REMARK 350   BIOMT2   3  0.587785 -0.809017 -0.000000        0.00000
REMARK 350   BIOMT3   3  0.000000  0.000000  1.000000        0.00000
CRYST1    1.000    1.000    1.000  90.00  90.00  90.00 P 1           1
ATOM      1  N   ALA A   2      64.807-112.186 260.746  1.00160.99           N
ATOM      2  CA  ALA A   2      64.727-111.450 262.002  1.00159.36           C
ATOM      3  C   ALA A   2      63.960-110.148 261.805  1.00154.38           C
ATOM      4  O   ALA A   2      62.935-109.914 262.452  1.00149.47           O
ATOM      5  CB  ALA A   2      66.123-111.175 262.542  1.00156.98           C
ATOM      6  N   SER A   3      64.474-109.323 260.896  1.00135.75           N
ATOM      7  CA  SER A   3      63.887-108.040 260.510  1.00131.97           C
ATOM      8  C   SER A   3      64.863-107.340 259.575  1.00140.51           C
ATOM      9  O   SER A   3      65.864-107.925 259.165  1.00148.46           O
ATOM     10  CB  SER A   3      63.641-107.147 261.726  1.00126.01           C
ATOM     11  OG  SER A   3      64.002-105.804 261.453  1.00119.04           O
END
'''

pdb_test_data8 = '''\
MTRIX1   1  1.000000  0.000000  0.000000        0.00000    1
MTRIX2   1  0.000000  1.000000  0.000000        0.00000    1
MTRIX3   1  0.000000  0.000000  1.000000        0.00000    1
MTRIX1   2  0.309017 -0.951057  0.000000        0.00000
MTRIX2   2  0.951057  0.309017 -0.000000        0.00000
MTRIX3   2  0.000000  0.000000  1.000000        7.00000
MTRIX1   3 -0.809017 -0.587785  0.000000        0.00000
MTRIX2   3  0.587785 -0.809017 -0.000000        0.00000
MTRIX3   3  0.000000  0.000000  1.000000        0.00000
CRYST1    1.000    1.000    1.000  90.00  90.00  90.00 P 1           1
ATOM    757  N   ASP A 247      16.068 -20.882 -28.984  1.00 35.93           N
ATOM    758  CA  ASP A 247      15.914 -22.265 -28.600  1.00 47.90           C
ATOM    759  C   ASP A 247      17.130 -23.042 -29.116  1.00 42.32           C
ATOM    760  O   ASP A 247      17.461 -22.986 -30.301  1.00 47.25           O
ATOM    761  CB  ASP A 247      14.621 -22.814 -29.198  1.00 47.22           C
ATOM    762  CG  ASP A 247      14.068 -23.974 -28.412  1.00 61.15           C
ATOM    763  OD1 ASP A 247      14.359 -24.061 -27.196  1.00 63.66           O
ATOM    764  OD2 ASP A 247      13.341 -24.798 -29.012  1.00 77.01           O
ATOM    765  N   VAL A 248      17.808 -23.746 -28.218  1.00 44.08           N
ATOM    766  CA  VAL A 248      19.008 -24.503 -28.584  1.00 46.18           C
ATOM    767  C   VAL A 248      18.668 -25.988 -28.583  1.00 53.97           C
ATOM    768  O   VAL A 248      18.049 -26.478 -27.638  1.00 51.48           O
ATOM    769  CB  VAL A 248      20.185 -24.226 -27.608  1.00 47.55           C
ATOM    770  CG1 VAL A 248      21.414 -25.015 -28.012  1.00 41.43           C
ATOM    771  CG2 VAL A 248      20.513 -22.743 -27.567  1.00 41.64           C
ATOM    772  N   VAL A 249      19.057 -26.697 -29.641  1.00 54.29           N
ATOM    773  CA  VAL A 249      18.662 -28.097 -29.810  1.00 60.17           C
ATOM    774  C   VAL A 249      19.859 -29.041 -29.982  1.00 57.98           C
ATOM    775  O   VAL A 249      20.731 -28.827 -30.828  1.00 58.31           O
ATOM    776  CB  VAL A 249      17.671 -28.280 -30.997  1.00 60.85           C
ATOM    777  CG1 VAL A 249      16.500 -27.300 -30.884  1.00 48.00           C
ATOM    778  CG2 VAL A 249      18.386 -28.110 -32.337  1.00 59.99           C
TER
ATOM    780  N   LYS B 151       4.045  -6.858 -32.823  1.00 45.22           N
ATOM    781  CA  LYS B 151       4.686  -6.715 -34.123  1.00 50.40           C
ATOM    782  C   LYS B 151       5.707  -5.554 -34.172  1.00 47.13           C
ATOM    783  O   LYS B 151       6.820  -5.764 -34.625  1.00 52.91           O
ATOM    784  CB  LYS B 151       3.657  -6.646 -35.268  1.00 40.73           C
ATOM    785  CG  LYS B 151       4.264  -6.627 -36.661  1.00 55.98           C
ATOM    786  CD  LYS B 151       3.272  -7.051 -37.745  1.00 72.14           C
ATOM    787  CE  LYS B 151       2.529  -8.338 -37.375  1.00 75.11           C
ATOM    788  NZ  LYS B 151       3.451  -9.400 -36.884  1.00 75.46           N
ATOM    789  N   ARG B 152       5.369  -4.349 -33.709  1.00 42.01           N
ATOM    790  CA  ARG B 152       6.399  -3.290 -33.702  1.00 40.51           C
ATOM    791  C   ARG B 152       6.155  -2.002 -32.909  1.00 34.21           C
ATOM    792  O   ARG B 152       5.015  -1.605 -32.636  1.00 33.77           O
ATOM    793  CB  ARG B 152       6.845  -2.937 -35.130  1.00 40.62           C
ATOM    794  CG  ARG B 152       5.842  -2.126 -35.925  1.00 45.94           C
ATOM    795  CD  ARG B 152       6.341  -1.926 -37.341  1.00 42.75           C
ATOM    796  NE  ARG B 152       7.478  -1.006 -37.404  1.00 45.27           N
ATOM    797  CZ  ARG B 152       8.177  -0.763 -38.509  1.00 49.68           C
ATOM    798  NH1 ARG B 152       7.860  -1.382 -39.644  1.00 47.81           N
ATOM    799  NH2 ARG B 152       9.192   0.096 -38.482  1.00 48.06           N
END
'''

test_pdb_9 = """\
MTRIX1   1  1.000000  0.000000  0.000000        0.00000    1
MTRIX2   1  0.000000  1.000000  0.000000        0.00000    1
MTRIX3   1  0.000000  0.000000  1.000000        0.00000    1
MTRIX1   2  0.496590 -0.643597  0.582393        0.00000    1
MTRIX2   2  0.867925  0.376088 -0.324443        0.00000    1
MTRIX3   2 -0.010221  0.666588  0.745356        0.00000    1
MTRIX1   3 -0.317946 -0.173437  0.932111        0.00000    1
MTRIX2   3  0.760735 -0.633422  0.141629        0.00000    1
MTRIX3   3  0.565855  0.754120  0.333333        0.00000    1
ATOM      1  N   THR A   1       9.670  10.289  11.135  1.00 20.00           N
ATOM      2  CA  THR A   2       9.559   8.931  10.615  1.00 20.00           C
ATOM      3  C   THR A   3       9.634   7.903  11.739  1.00 20.00           C
ATOM      4  O   THR B   4      10.449   8.027  12.653  1.00 20.00           O
ATOM      5  CB  THR B   5      10.660   8.630   9.582  1.00 20.00           C
ATOM      6  OG1 THR A   6      10.560   9.552   8.490  1.00 20.00           O
ATOM      7  CG2 THR A   7      10.523   7.209   9.055  1.00 20.00           C
END
"""

def run_selected_tests():
  """  Run selected tests

  1) List in "tests" the names of the particular test you want to run
  2) Comment out unittest.main()
  3) Un-comment unittest.TextTestRunner().run(run_selected_tests())
  """
  tests = ['test_proper_biomat_application']
  suite = unittest.TestSuite(map(TestMultimerReconstruction,tests))
  return suite

if __name__=='__main__':
  # use for individual tests
  # unittest.TextTestRunner().run(run_selected_tests())

  # Use to run all tests
  unittest.main(verbosity=0)
