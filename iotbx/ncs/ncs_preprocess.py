from __future__ import division
from mmtbx.utils.ncs_utils import apply_transforms
from scitbx.linalg import eigensystem
from scitbx.array_family import flex
from libtbx.utils import null_out
from scitbx.math import superpose
from libtbx.phil import parse
import iotbx.pdb.hierarchy
from mmtbx.ncs import ncs
from scitbx import matrix
from iotbx import pdb
import string
import math
import re
import os
import sys


# parameters for manual specification of NCS - ASU mapping
master_phil = parse("""
  ncs_group
    .multiple = True
    {
    master_ncs_selection = ''
      .type = str
      .help = 'Residue selection string for the complete master NCS copy'
    selection_copy = ''
      .type = str
      .help = 'Residue selection string for each NCS copy location in ASU'
      .multiple = True
  }
  """)


class ncs_group_object(object):

  def __init__(self):
    """
    process MTRIX, BOIMT and PHIL parameters and produce an object
    with information for NCS refinement

    Argument:
    transform_info:  an object produced from the PDB MTRIX or BIOMT records
    ncs_refinement_params: an object produced by the PHIL parameters
    """
    self.total_asu_length = None
    # iselection maps, each master ncs to its copies position in the asu
    self.ncs_to_asu_map = {}
    # iselection maps of each ncs copy to its master ncs
    self.asu_to_ncs_map = {}
    # keys are items in ncs_chain_selection, values are lists of selection str
    self.ncs_to_asu_selection = {}
    self.ncs_copies_chains_names = {}
    self.tr_id_to_selection = {}
    # dictionary of transform names, same keys as ncs_to_asu_map
    self.chain_transform_assignment = {}
    self.number_of_ncs_groups = 1
    self.ncs_group_map = {}
    # map transform name (s1,s2,...) to transform object
    self.ncs_transform = {}
    # list of transform to chain assignment
    self.transform_chain_assignment = []
    # map transform to list of master ncs parts in its ncs groups
    self.transform_to_ncs = {}
    # master ncs and non-ncs selection in a string and a flex.bool types
    self.ncs_atom_selection = None
    self.ncs_selection_str = ''
    # iselection of all part in ASU that are not related via NCS operators
    self.non_ncs_region_selection = flex.size_t()
    self.all_master_ncs_selections = flex.size_t()
    # list of selection strings of master NCS
    self.ncs_chain_selection = []
    # unique chains or selection identifiers
    self.model_unique_chains_ids = tuple()
    self.selection_ids = set()
    # transform application order
    self.model_order_chain_ids = []
    self.transform_to_be_used = set()
    # order of transforms  - used when concatenating or separating them
    self.transform_order = []
    # keep hierarchy for writing (To have a source of atoms labels)
    self.hierarchy = None
    # residues related via NCS operators. same keys as ncs_copies_chains_names
    self.common_res_dict = {}

  def preprocess_ncs_obj(self,
                         pdb_hierarchy_inp=None,
                         pdb_inp=None,
                         transform_info=None,
                         rotations = None,
                         translations = None,
                         ncs_selection_params = None,
                         ncs_phil_groups = None,
                         file_name=None,
                         file_path='',
                         spec_file_str='',
                         spec_source_info='',
                         cif_string = '',
                         quiet=True,
                         spec_ncs_groups=None,
                         pdb_string=None,
                         use_cctbx_find_ncs_tools=True,
                         use_simple_ncs_from_pdb=True,
                         use_minimal_master_ncs=True):
    """
    Select method to build ncs_group_object

    order of implementation:
    1) rotations,translations
    2) transform_info
    3) ncs_selection_params
    4) ncs_phil_groups
    5) spec file
    6) mmcif file
    7) iotbx.pdb.hierarchy.input object

    Args:
    -----
      pdb_hierarchy_inp: iotbx.pdb.hierarchy.input
      transform_info: object containing MTRIX or BIOMT transformation info
      rotations: matrix.sqr 3x3 object
      translations: matrix.col 3x1 object
      ncs_selection_params: Phil parameters
        Phil structure
           ncs_group (multiple)
           {
             master_ncs_selection = ''
             selection_copy = ''   (multiple)
           }
      ncs_phil_groups: a list of ncs_groups_container object, containing
        master NCS selection and a list of NCS copies selection
      file_name: (str) .ncs_spec or .mmcif  or .pdb file name
      file_path: (str)
      spec_file_str: (str) spec format data
      spec_source_info:
      quiet: (bool) When True -> quiet output when processing files
      spec_ncs_groups: ncs_groups object as produced by simple_ncs_from_pdb
      cif_string: (str) string of cif type data
      use_cctbx_find_ncs_tools: (bool) Enable using of chain base NCS search
      use_simple_ncs_from_pdb: (bool) Enable using use_simple_ncs_from_pdb
      use_minimal_master_ncs: (bool) use maximal or minimal common chains
        in master ncs groups
    """
    extension = ''
    if file_name: extension = os.path.splitext(file_name)[1]
    if pdb_hierarchy_inp:
      msg = 'pdb_hierarchy_inp is not iotbx.pdb.hierarchy.input object'
      assert isinstance(pdb_hierarchy_inp,iotbx.pdb.hierarchy.input),msg
    elif pdb_inp:
      ph = pdb_inp.construct_hierarchy()
      pdb_hierarchy_inp = iotbx.pdb.hierarchy.input_hierarchy_pair(pdb_inp,ph)
    if extension.lower() in ['.pdb','.cif', '.mmcif']:
      pdb_hierarchy_inp = pdb.hierarchy.input(file_name=file_name)
    elif (not pdb_hierarchy_inp) and (pdb_string or cif_string):
      if pdb_string: input_str = pdb_string
      else: input_str = cif_string
      pdb_hierarchy_inp = pdb.hierarchy.input(pdb_string=input_str)
    if pdb_hierarchy_inp and (not transform_info):
      transform_info = pdb_hierarchy_inp.input.process_mtrix_records()
      if transform_info.as_pdb_string() == '': transform_info = None
    if transform_info or rotations:
      self.build_ncs_obj_from_pdb_ncs(
        pdb_hierarchy_inp = pdb_hierarchy_inp,
        rotations=rotations,
        translations=translations,
        transform_info=transform_info)
    elif ncs_selection_params or ncs_phil_groups:
      self.build_ncs_obj_from_phil(
        ncs_selection_params=ncs_selection_params,
        ncs_phil_groups=ncs_phil_groups,
        pdb_hierarchy_inp=pdb_hierarchy_inp)
    elif extension.lower() == '.ncs_spec' or \
            spec_file_str or spec_source_info or spec_ncs_groups:
      self.build_ncs_obj_from_spec_file(
        file_name=file_name,
        file_path=file_path,
        file_str=spec_file_str,
        source_info=spec_source_info,
        pdb_hierarchy_inp=pdb_hierarchy_inp,
        spec_ncs_groups=spec_ncs_groups,
        quiet=quiet)
    elif extension.lower() == '.mmcif' or cif_string:
      self.build_ncs_obj_from_mmcif(
        file_name=file_name,
        file_path=file_path,
        mmcif_string=cif_string)
    elif pdb_hierarchy_inp:
      self.build_ncs_obj_from_pdb_asu(
        pdb_hierarchy_inp=pdb_hierarchy_inp,
        use_cctbx_find_ncs_tools=use_cctbx_find_ncs_tools,
        use_simple_ncs_from_pdb=use_simple_ncs_from_pdb,
        use_minimal_master_ncs=use_minimal_master_ncs)
    else:
      raise IOError,'Please provide one of the supported input'

  def build_ncs_obj_from_pdb_ncs(self,
                                 pdb_hierarchy_inp,
                                 transform_info=None,
                                 rotations = None,
                                 translations = None):
    """
    Build transforms objects and NCS <-> ASU mapping using PDB file containing
    a single NCS copy and MTRIX  or BIOMT records

    Arguments:
    pdb_hierarchy_inp : iotbx.pdb.hierarchy.input
    transform_info : an object containing MTRIX or BIOMT transformation info
    rotations : matrix.sqr 3x3 object
    translations : matrix.col 3x1 object
    """
    self.collect_basic_info_from_pdb(pdb_hierarchy_inp=pdb_hierarchy_inp)
    assert bool(transform_info or (rotations and translations))
    if rotations:
      # add rotations,translations to ncs_refinement_groups
      self.add_transforms_to_ncs_refinement_groups(
        rotations=rotations,
        translations=translations)
    else:
      # use only MTRIX/BIOMT records from PDB
      assert_test = all_ncs_copies_not_present(transform_info)
      msg = 'MTRIX record error : Mixed present and not-present NCS copies'
      assert assert_test,msg
      self.process_pdb(transform_info=transform_info)
    self.transform_chain_assignment = get_transform_order(self.transform_to_ncs)
    self.ncs_copies_chains_names = self.make_chains_names(
      transform_assignment=self.transform_chain_assignment,
      unique_chain_names = self.model_unique_chains_ids)
    # build self.ncs_to_asu_selection
    for k in self.transform_chain_assignment:
      selection_str = 'chain ' + self.ncs_copies_chains_names[k]
      key =  k.split('_')[0]
      self.tr_id_to_selection[k] = (key,selection_str)
      self.ncs_to_asu_selection = add_to_dict(
        d=self.ncs_to_asu_selection,k=key,v=selection_str)
    self.finalize_pre_process(pdb_hierarchy_inp=pdb_hierarchy_inp)

  def build_ncs_obj_from_phil(self,
                              ncs_selection_params = None,
                              ncs_phil_groups = None,
                              pdb_hierarchy_inp = None):
    """
    Build transforms objects and NCS <-> ASU mapping using phil selection
    strings and complete ASU

    Arguments:
    ncs_selection_params : Phil parameters
    pdb_hierarchy_inp : iotbx.pdb.hierarchy.input

    Phil structure
    ncs_group (multiple)
    {
      master_ncs_selection = ''
      selection_copy = ''   (multiple)
    }
    """
    # process params
    if ncs_selection_params:
      if isinstance(ncs_selection_params,str):
        ncs_selection_params = parse(ncs_selection_params)
      phil_param =  master_phil.fetch(
        source=ncs_selection_params,track_unused_definitions=True)
      working_phil = phil_param[0].extract()
      assert  phil_param[1] == [],'Check phil parameters...'
      ncs_phil_groups = working_phil.ncs_group
    else:
      assert not (ncs_phil_groups is None)
    assert self.ncs_selection_str == ''
    unique_selections = set()
    transform_sn = 0
    ncs_group_id = 0
    # populate ncs selection and ncs to copies location
    for group in ncs_phil_groups:
      gns = group.master_ncs_selection
      self.ncs_chain_selection.append(gns)
      unique_selections = uniqueness_test(unique_selections,gns)
      master_ncs_atoms = get_pdb_selection(ph=pdb_hierarchy_inp,
                                           selection_str=gns)
      ncs_group_id += 1
      transform_sn += 1
      self.add_identity_transform(
        ncs_selection=gns,
        ncs_group_id=ncs_group_id,
        transform_sn=transform_sn)
      key = 's' + format_num_as_str(transform_sn)
      # update with identity transform
      self.update_ncs_copies_chains_names(
            masters = gns,copies = gns, tr_id = key)
      self.update_tr_id_to_selection(gns,gns,key)
      asu_locations = []
      for asu_select in group.selection_copy:
        unique_selections = uniqueness_test(unique_selections,asu_select)
        ncs_copy_atoms = get_pdb_selection(
          ph=pdb_hierarchy_inp,selection_str=asu_select)
        r, t = get_rot_trans(
          master_atoms=master_ncs_atoms,copy_atoms= ncs_copy_atoms,
          rms_eps=100)
        assert r,'Master NCS and Copy are very poorly related, check selection.'
        asu_locations.append(asu_select)
        transform_sn += 1
        key = 's' + format_num_as_str(transform_sn)
        self.update_tr_id_to_selection(gns,asu_select,key)
        tr = transform(
          rotation = r,
          translation = t,
          serial_num = transform_sn,
          coordinates_present = True,
          ncs_group_id = ncs_group_id)
        # Update ncs_group dictionary and transform_to_ncs list
        self.build_transform_dict(
          transform_id = key,
          transform = tr,
          selection_id = gns)
        self.ncs_group_map = update_ncs_group_map(
          ncs_group_map=self.ncs_group_map,
          ncs_group_id = ncs_group_id,
          selection_ids = gns,
          transform_id = key)
        assert not self.ncs_transform.has_key(key)
        self.ncs_transform[key] = tr
        self.selection_ids.add(gns)
        self.update_ncs_copies_chains_names(
            masters = gns,copies = asu_select, tr_id = key)
      self.ncs_to_asu_selection[gns] = asu_locations
      self.number_of_ncs_groups = ncs_group_id

    self.ncs_selection_str = '('+ self.ncs_chain_selection[0] +')'
    for i in range(1,len(self.ncs_chain_selection)):
      self.ncs_selection_str += ' or (' + self.ncs_chain_selection[i] + ')'

    self.transform_chain_assignment = get_transform_order(self.transform_to_ncs)
    self.finalize_pre_process(pdb_hierarchy_inp=pdb_hierarchy_inp)

  def build_ncs_obj_from_pdb_asu(self,pdb_hierarchy_inp,
                                 use_cctbx_find_ncs_tools=True,
                                 use_simple_ncs_from_pdb=True,
                                 use_minimal_master_ncs=True):
    """
    Build transforms objects and NCS <-> ASU mapping from a complete ASU
    Note that the MTRIX record are ignored, they are produced in the
    process of identifying the master NCS

    Arguments:
    pdb_hierarchy_inp : iotbx.pdb.hierarchy.input
    use_cctbx_find_ncs_tools (bool): Enable using of chain base NCS search
    use_simple_ncs_from_pdb (bool): Enable using use_simple_ncs_from_pdb
    use_minimal_master_ncs (bool): indicate if using maximal or minimal NCS
    groups
    """
    ncs_phil_groups = []
    if use_cctbx_find_ncs_tools:
      if use_minimal_master_ncs:
        ncs_phil_groups = get_minimal_master_ncs_group(pdb_hierarchy_inp)
      else:
        ncs_phil_groups = get_largest_common_ncs_groups(pdb_hierarchy_inp)

    if (ncs_phil_groups != []):
      self.build_ncs_obj_from_phil(
        pdb_hierarchy_inp=pdb_hierarchy_inp,
        ncs_phil_groups=ncs_phil_groups)
    elif use_simple_ncs_from_pdb:
      import libtbx.load_env
      if libtbx.env.has_module(name="phenix"):
        from phenix.command_line.simple_ncs_from_pdb import simple_ncs_from_pdb
        from phenix.command_line.simple_ncs_from_pdb import ncs_master_params
        params = ncs_master_params.extract()
        params.simple_ncs_from_pdb.min_length = 1
        ncs_from_pdb=simple_ncs_from_pdb(
          pdb_inp=pdb_hierarchy_inp.input,
          hierarchy=pdb_hierarchy_inp.hierarchy,
          quiet=True,
          log=null_out(),
          suppress_print=True,
          params=params)
        spec_ncs_groups = ncs_from_pdb.ncs_object.ncs_groups()
        self.build_ncs_obj_from_spec_file(
          pdb_hierarchy_inp=pdb_hierarchy_inp,
          spec_ncs_groups=spec_ncs_groups)

  def build_ncs_obj_from_spec_file(self,file_name=None,file_path='',
                                   file_str='',source_info="",quiet=True,
                                   pdb_hierarchy_inp=None,
                                   spec_ncs_groups=[],
                                   join_same_spec_groups = True):
    """
    read .spec files and build transforms object and NCS <-> ASU mapping

    Arguments:
    spec file information using a file, file_str (str) of a source_info (str)
    quite: (bool) quite output when True
    pdb_hierarchy_inp: pdb hierarchy input
    spec_ncs_groups: ncs_groups object
    join_same_spec_groups: (bool) True: combine groups with similar transforms
    """
    if (not bool(spec_ncs_groups)) and (file_name or file_str):
      fn = os.path.join(file_path,file_name)
      lines = file_str.splitlines()
      assert lines != [] or os.path.isfile(fn)
      spec_object = ncs.ncs()
      spec_object.read_ncs(
        file_name=fn,lines=lines,source_info=source_info,quiet=quiet)
      spec_ncs_groups = spec_object.ncs_groups()

    if isinstance(spec_ncs_groups, ncs.ncs):
      spec_ncs_groups = spec_ncs_groups.ncs_groups()

    if spec_ncs_groups:
      transform_sn = 0
      ncs_group_id = 0
      for gr in spec_ncs_groups:
        # create selection
        ncs_group_selection_list =get_ncs_group_selection(gr.chain_residue_id())
        gs = ncs_group_selection_list[0]
        if join_same_spec_groups:
          # leave groups with the same transforms separate
          group_exist =self.look_and_combine_groups(gr,ncs_group_selection_list)
          if group_exist: continue
        ncs_group_id += 1
        self.ncs_chain_selection.append(gs)
        asu_locations = []
        for i,ncs_copy_select in enumerate(ncs_group_selection_list):
          # invert transform - the rotation in gr is from the copy to the master
          r = gr.rota_matrices()[i]
          t = gr.translations_orth()[i]
          r,t = inverse_transform(r,t)
          transform_sn += 1
          key = 's' + format_num_as_str(transform_sn)
          self.update_tr_id_to_selection(gs,ncs_copy_select,key)
          if not is_identity(r,t):
            asu_locations.append(ncs_copy_select)
          tr = transform(
            rotation = r,
            translation = t,
            serial_num = transform_sn,
            coordinates_present = True,
            ncs_group_id = ncs_group_id)
          # Update ncs_group dictionary and transform_to_ncs list
          self.build_transform_dict(
            transform_id = key,
            transform = tr,
            selection_id = gs)
          self.ncs_group_map = update_ncs_group_map(
            ncs_group_map=self.ncs_group_map,
            ncs_group_id = ncs_group_id,
            selection_ids = gs,
            transform_id = key)
          assert not self.ncs_transform.has_key(key)
          self.ncs_transform[key] = tr
          self.selection_ids.add(gs)
          self.update_ncs_copies_chains_names(
            masters = gs,copies = ncs_copy_select,tr_id = key)
        self.ncs_to_asu_selection[gs] = asu_locations
        self.number_of_ncs_groups = ncs_group_id

      self.ncs_selection_str = '('+ self.ncs_chain_selection[0] +')'
      for i in range(1,len(self.ncs_chain_selection)):
        self.ncs_selection_str += ' or (' + self.ncs_chain_selection[i] + ')'
      self.transform_chain_assignment = \
        get_transform_order(self.transform_to_ncs)
      self.finalize_pre_process(pdb_hierarchy_inp=pdb_hierarchy_inp)

  def look_and_combine_groups(self,gr_new,ncs_group_selection_list):
    """
    """
    gs_new = ncs_group_selection_list[0]
    found_same_group = False
    gr_r_list = gr_new.rota_matrices()
    gr_t_list = gr_new.translations_orth()
    # in spec files transforms are inverted
    gr_new_list = [inverse_transform(r,t) for (r,t) in zip(gr_r_list,gr_t_list)]
    for k,[gs, tr_set] in self.ncs_group_map.iteritems():
      # all transforms need to be the same to join
      if len(gr_r_list) != len(tr_set): continue
      same_transforms = [None,]*len(tr_set)
      tr_list = list(tr_set)
      tr_list.sort()
      for tr_key1 in tr_list:
        r1 = self.ncs_transform[tr_key1].r
        t1 = self.ncs_transform[tr_key1].t
        for i,(r2,t2) in enumerate(gr_new_list):
          if not (same_transforms[i] is None): continue
          same,transpose = is_same_transform(r1,t1,r2,t2)
          test = (same and (not transpose))
          if test:
            same_transforms[i] = i
            break
      found_same_group = (same_transforms.count(None) == 0)
      if found_same_group: break
    # update dictionaries
    if found_same_group:
      self.selection_ids.add(gs_new)
      asu_locations = []
      for i in same_transforms:
        transform_id = tr_list[i]
        ncs_copy_select = ncs_group_selection_list[i]
        key = gs_new + '_' + transform_id
        # look at self.ncs_copies_chains_names
        self.update_ncs_copies_chains_names(
          masters=gs_new, copies=ncs_copy_select, tr_id=transform_id)
        r,t = gr_new_list[i]
        if not is_identity(r,t):
          self.chain_transform_assignment[key] = transform_id
          self.transform_to_ncs = add_to_dict(
            d=self.transform_to_ncs,k=transform_id,v=key)
          asu_locations.append(ncs_copy_select)

      self.ncs_to_asu_selection[gs_new] = asu_locations
      self.ncs_group_map[k][0].add(gs_new)

    return found_same_group

  def update_ncs_copies_chains_names(self,masters, copies, tr_id):
    masters = get_list_of_chains_selection(masters)
    copies = get_list_of_chains_selection(copies)
    for m,c in zip(masters,copies):
      self.ncs_copies_chains_names[m +'_' + tr_id] = c.replace('chain ','')

  def update_tr_id_to_selection(self,masters, copies,tr_id):
    """
    Args:
      masters: (str) selection of master ncs
      copies: (str) selection of copy
      tr_id: (str) string like s_001 where 001 is the transform number
    """
    tr_keys = get_list_of_chains_selection(masters)
    master_selection_list = separate_selection_string(masters)
    copies_selection_list = separate_selection_string(copies)
    for k,c,m in zip(tr_keys,copies_selection_list,master_selection_list):
      key = k + '_' + tr_id
      self.tr_id_to_selection[key] = (m,c)

  def add_transforms_to_ncs_refinement_groups(self,rotations,translations):
    """
    Add rotation matrices and translations vectors
    to ncs_refinement_groups
    """
    assert len(rotations) == len(translations)
    assert not self.ncs_transform, 'ncs_transform should be empty'
    sn = {1}
    self.add_identity_transform(ncs_selection=self.ncs_selection_str)
    n = 1
    for (r,t) in zip(rotations,translations):
      # check if transforms are the identity transform
      if not is_identity(r,t):
        n += 1
        sn.add(n)
        key = 's' + format_num_as_str(n)
        tr = transform(
          rotation = r,
          translation = t,
          serial_num = n,
          coordinates_present = False,
          ncs_group_id = 1)
        assert not self.ncs_transform.has_key(key)
        self.ncs_transform[key] = tr
        for select in self.ncs_chain_selection:
          self.build_transform_dict(
            transform_id = key,
            transform = tr,
            selection_id = select)
          self.selection_ids.add(select)
          self.tr_id_to_selection[select + '_' + key] = (select,select)
        self.ncs_group_map = update_ncs_group_map(
          ncs_group_map=self.ncs_group_map,
          ncs_group_id = 1,
          selection_ids = self.ncs_chain_selection,
          transform_id = key)

  def collect_basic_info_from_pdb(self,pdb_hierarchy_inp):
    """  Build chain selection string and collect chains IDs from pdb """
    if pdb_hierarchy_inp:
      model  = pdb_hierarchy_inp.hierarchy.models()[0]
      chain_ids = {x.id for x in model.chains()}
      # Collect order if chains IDs and unique IDs
      self.model_unique_chains_ids = tuple(sorted(chain_ids))
      model_order_ch_ids = [(x.id,x.atoms().size()) for x in model.chains()]
      ch_n_atoms = {x:None for x in self.model_unique_chains_ids}
      for (ch,n) in model_order_ch_ids:
        if ch_n_atoms[ch] is None:
          ch_n_atoms[ch] = [(0,n)]
        else:
          _,last_n = ch_n_atoms[ch][-1]
          ch_n_atoms[ch].append((last_n, last_n + n))
      for ch,n in model_order_ch_ids:
        selection_range = ch_n_atoms[ch].pop(0)
        self.model_order_chain_ids.append((ch,selection_range))
      s = ' or chain '.join(self.model_unique_chains_ids)
      self.ncs_selection_str = 'chain ' + s
      assert self.ncs_chain_selection == []
      self.ncs_chain_selection =\
        ['chain ' + s for s in self.model_unique_chains_ids]
      self.ncs_chain_selection.sort()

  def compute_ncs_asu_coordinates_map(self,pdb_hierarchy_inp):
    """ Calculates coordinates maps from ncs to asu and from asu to ncs """
    temp = pdb_hierarchy_inp.hierarchy.atom_selection_cache()
    # check if pdb_hierarchy_inp contain only the master NCS copy
    pdb_length = len(pdb_hierarchy_inp.hierarchy.atoms())
    self.ncs_atom_selection = temp.selection(self.ncs_selection_str)
    ncs_length = self.ncs_atom_selection.count(True)
    # keep track on the asu copy number
    copy_count = {}

    if pdb_length > ncs_length:
      self.total_asu_length = pdb_length
      selection_ref = flex.bool([False]*pdb_length)
      for k in self.transform_chain_assignment:
        key =  k.split('_')[0]
        ncs_selection = temp.selection(key)
        if not self.asu_to_ncs_map.has_key(key):
          copy_count[key] = 0
          selection_ref = update_selection_ref(selection_ref,ncs_selection)
          self.asu_to_ncs_map[key] = ncs_selection.iselection()
        else:
          copy_count[key] += 1
        asu_copy_ref = self.ncs_to_asu_selection[key][copy_count[key]]
        asu_selection = temp.selection(asu_copy_ref)
        selection_ref = update_selection_ref(selection_ref,asu_selection)
        self.ncs_to_asu_map[k] = asu_selection.iselection()
      self.non_ncs_region_selection = (~selection_ref).iselection()
      # add the non ncs regions to the master ncs copy
      self.all_master_ncs_selections = self.ncs_atom_selection.iselection()
      self.ncs_atom_selection = self.ncs_atom_selection | (~selection_ref)
      assert set(self.non_ncs_region_selection).intersection(
        set(self.all_master_ncs_selections)) == set()
    elif pdb_length == ncs_length:
      # this case is when the pdb hierarchy contain only the master NCS copy
      self.total_asu_length = self.get_asu_length(temp)
      ns = [True]*pdb_length + [False]*(self.total_asu_length - pdb_length)
      self.ncs_atom_selection = flex.bool(ns)
      self.all_master_ncs_selections=self.ncs_atom_selection.iselection()
      sorted_keys = sorted(self.transform_to_ncs)
      i = 0
      for k in sorted_keys:
        v = self.transform_to_ncs[k]
        i += 1
        for transform_key in v:
          key =  transform_key.split('_')[0]
          ncs_basic_selection = temp.selection(key)
          ncs_selection = flex.bool(self.total_asu_length,temp.iselection(key))
          if not self.asu_to_ncs_map.has_key(key):
            self.asu_to_ncs_map[key] = ncs_selection.iselection()
          # make the selection at the proper location at the ASU
          selection_list = list(ncs_basic_selection)
          temp_selection = flex.bool([False]*i*ncs_length + selection_list)
          asu_selection =flex.bool(self.total_asu_length,
                                   temp_selection.iselection())
          self.ncs_to_asu_map[transform_key] = asu_selection.iselection()


  def add_identity_transform(self,ncs_selection,ncs_group_id=1,transform_sn=1):
    """    Add identity transform
    Argument:

    ncs_selection: (str) selection string for the NCS master copy
    ncs_group_id: (int) the NCS group ID
    transform_sn: (int) Over all transform serial number
    """
    transform_obj = transform(
      rotation = matrix.sqr([1,0,0,0,1,0,0,0,1]),
      translation = matrix.col([0,0,0]),
      serial_num = transform_sn,
      coordinates_present = True,
      ncs_group_id = ncs_group_id)
    id_str = 's' + format_num_as_str(transform_sn)
    self.ncs_transform[id_str] = transform_obj
    self.build_transform_dict(
      transform_id = id_str,
      transform = transform_obj,
      selection_id = ncs_selection)
    self.selection_ids.add(ncs_selection)
    self.ncs_group_map = update_ncs_group_map(
      ncs_group_map=self.ncs_group_map,
      ncs_group_id = ncs_group_id,
      selection_ids = ncs_selection,
      transform_id = id_str)

  def process_pdb(self,transform_info):
    """
    Process PDB Hierarchy object

    Remarks:
    The information on a chain in a PDB file does not have to be continuous.
    Every time the chain name changes in the pdb file, a new chain is added
    to the model, even if the chain ID already exist. so there model.
    chains() might contain several chains that have the same chain ID
    """
    transform_info_available = bool(transform_info) and bool(transform_info.r)
    if transform_info_available:
      ti = transform_info
      for (r,t,n,cp) in zip(ti.r,ti.t,ti.serial_number,ti.coordinates_present):
        n = int(n)
        key = 's' + format_num_as_str(n)
        tr = transform(
          rotation = r,
          translation = t,
          serial_num = n,
          coordinates_present = cp,
          ncs_group_id = 1)
        for select in self.ncs_chain_selection:
          self.build_transform_dict(
            transform_id = key,
            transform = tr,
            selection_id = select)
          self.selection_ids.add(select)
        self.ncs_group_map = update_ncs_group_map(
          ncs_group_map=self.ncs_group_map,
          ncs_group_id = 1,
          selection_ids = self.ncs_chain_selection,
          transform_id = key)
        # if ncs selection was not provided in phil parameter
        assert not self.ncs_transform.has_key(key)
        self.ncs_transform[key] = tr

  def build_transform_dict(self,
                           transform_id,
                           transform,
                           selection_id):
    """
    Apply all non-identity transforms

    Arguments:
    transform_id : (str) s001,s002...
    transform : transform object, containing information on transformation
    selection_id : (str) NCS selection string

    Build transform_to_ncs dictionary, which provides the location of the
    particular chains or selections in the NCS
    """
    if not is_identity(transform.r,transform.t):
      self.transform_to_be_used.add(transform.serial_num)
      key = selection_id + '_s' + format_num_as_str(transform.serial_num)
      # key = selection_id
      self.chain_transform_assignment[key] = transform_id
      self.transform_to_ncs = add_to_dict(
        d=self.transform_to_ncs,k=transform_id,v=key)

  def get_asu_length(self,atom_selection_cache):
    """" Collect the length of all ncs copies """
    asu_total_length = self.ncs_atom_selection.count(True)
    for k in self.transform_chain_assignment:
      key =  k.split('_')[0]
      ncs_selection = atom_selection_cache.selection(key)
      asu_total_length += ncs_selection.count(True)
    return asu_total_length

  def build_MTRIX_object(self,ncs_only=True):
    """
    Build a MTRIX object from ncs_group_object
    Used for testing
    """
    assert  self.number_of_ncs_groups == 1
    result = iotbx.pdb._._mtrix_and_biomt_records_container()
    tr_dict = self.ncs_transform
    tr_sorted = sorted(tr_dict,key=lambda k:tr_dict[k].serial_num)
    for key in tr_sorted:
      transform = self.ncs_transform[key]
      r = transform.r
      t = transform.t
      identity_test = is_identity(r,t)
      cp = (not ncs_only) or identity_test
      result.add(
        r=r,
        t=t,
        coordinates_present=cp,
        serial_number=transform.serial_num)
    return result

  def make_chains_names(self,
                        transform_assignment,
                        unique_chain_names):
    """
    Create a dictionary names for the new NCS copies
    keys: (str) chain_name + '_s' + serial_num
    values: (str) (one or two chr long)

    Chain names might repeat themselves several times in a pdb file
    We want copies of chains with the same name to still have the
    same name after similar BIOMT/MTRIX transformation

    Arguments:
    transform_assignment : (list) transformation assignment order
    unique_chain_names : (tuple) a set of unique chain names

    Returns:
    new_names : a dictionary. {'A_1': 'G', 'A_2': 'H',....} map a chain
    name and a transform number to a new chain name
    """
    if not transform_assignment or not unique_chain_names: return {}
    # create list of character from which to assemble the list of names
    # total_chains_number = len(i_transforms)*len(unique_chain_names)
    total_chains_number = len(transform_assignment)
    # start naming chains with a single letter
    chr_list1 = list(set(string.ascii_uppercase) - set(unique_chain_names))
    chr_list2 = list(set(string.ascii_lowercase) - set(unique_chain_names))
    chr_list1.sort()
    chr_list2.sort()
    new_names_list = chr_list1 + chr_list2
    # check if we need more chain names
    if len(new_names_list) < total_chains_number:
      n_names =  total_chains_number - len(new_names_list)
      # the number of character needed to produce new names
      chr_number = int(math.sqrt(n_names)) + 1
      # build character list
      chr_list = list(string.ascii_uppercase) + \
                 list(string.ascii_lowercase) + \
                 list(string.digits)
      # take only as many characters as needed
      chr_list = chr_list[:chr_number]
      extra_names = set([ x+y for x in chr_list for y in chr_list])
      # make sure not using existing names
      extra_names = list(extra_names - unique_chain_names)
      extra_names.sort()
      new_names_list.extend(extra_names)
    assert len(new_names_list) >= total_chains_number
    dictionary_values = new_names_list[:total_chains_number]
    # create the dictionary
    zippedlists = zip(transform_assignment,dictionary_values)
    new_names_dictionary = {x:y for (x,y) in zippedlists}
    # add the master NCS to dictionary
    tr_set  = {'s' + format_num_as_str(x) for x in self.transform_to_be_used}
    for k,v in self.ncs_group_map.iteritems():
      tr_str = (v[1] - tr_set)
      assert len(tr_str) == 1
      tr_str = tr_str.pop()
      for ch_sel in v[0]:
        if not ' or ' in ch_sel:
          new_names_dictionary[ch_sel+'_'+tr_str] = ch_sel.replace('chain ','')
    return new_names_dictionary

  def finalize_pre_process(self,pdb_hierarchy_inp=None):
    """
    Steps that are common to most method of transform info
    """
    if pdb_hierarchy_inp:
      self.compute_ncs_asu_coordinates_map(pdb_hierarchy_inp=pdb_hierarchy_inp)
      # keep hierarchy for writing
      self.hierarchy = pdb_hierarchy_inp.hierarchy
      self.set_common_res_dict()

    self.transform_order = sort_dict_keys(self.transform_to_ncs)

  def set_common_res_dict(self):
    """
    Build common residues list and related RMSD
    for use when writing spec files
    :return: list of common residues for each chain - transform pair
    """
    sorted_keys = sort_dict_keys(self.ncs_copies_chains_names)
    only_master_ncs_in_hierarchy = False
    if self.ncs_atom_selection.count(True) == self.hierarchy.atoms().size():
      only_master_ncs_in_hierarchy = True
    sc = self.hierarchy.atom_selection_cache()
    # build a temp chain dictionary
    chains_dict = {}
    if len(self.hierarchy.models()) > 0:
      chains = self.hierarchy.models()[0].chains()
      for chain in chains:
        chains_dict = add_to_dict(d=chains_dict,k=chain.id,v=chain)

    for key in sorted_keys:
      ncs_chain_name = self.ncs_copies_chains_names[key]
      if not self.tr_id_to_selection.has_key(key):
        self.tr_id_to_selection[key] = (key.split('_')[0],key.split('_')[0])
      master_sel_str, ncs_selection_str = self.tr_id_to_selection[key]

      if only_master_ncs_in_hierarchy:
        # use master ncs for ncs copy residues indices
        chain_residues_list = chains_dict[master_sel_str.split()[1]]
        copy_selection_indices = sc.selection(master_sel_str).iselection()
        rmsd = 0
      else:
        chain_residues_list = chains_dict[ncs_chain_name]
        copy_selection_indices = sc.selection(ncs_selection_str).iselection()
        master_selection_indices = sc.selection(master_sel_str).iselection()
        xyz_copy = self.hierarchy.atoms().select(copy_selection_indices)
        xyz_master = self.hierarchy.atoms().select(master_selection_indices)
        xyz_copy = xyz_copy.extract_xyz()
        xyz_master = xyz_master.extract_xyz()
        tr = self.ncs_transform[key.split('_')[1]]
        xyz_master = tr.r.elems * xyz_master + tr.t
        rmsd = round(xyz_master.rms_difference(xyz_copy),4)

      # get continuous res ids
      range_list = []
      for chain in chain_residues_list:
        res_id = []
        for rs in chain.residue_groups():
          ch_id,j = rs.id_str().split()
          res_id.append(int(j))
        range_list.append([min(res_id),max(res_id)])
      self.common_res_dict[key] = ([range_list,copy_selection_indices],rmsd)

  def get_ncs_restraints_group_list(self):
    """
    :return: a list of ncs_restraint_group objects
    """
    ncs_restraints_group_list = []
    group_id_list = sort_dict_keys(self.ncs_group_map)
    for k in group_id_list:
      v = self.ncs_group_map[k]
      master_isel = flex.size_t()
      for key in v[0]:
        if self.asu_to_ncs_map.has_key(key):
          master_isel.extend(self.asu_to_ncs_map[key])
      new_nrg = ncs_restraint_group(master_isel)

      for tr in sorted(list(v[1])):
        if self.transform_to_ncs.has_key(tr):
          r = self.ncs_transform[tr].r
          t = self.ncs_transform[tr].t
          ncs_isel = flex.size_t()
          for sel in self.transform_to_ncs[tr]:
            ncs_isel.extend(self.ncs_to_asu_map[sel])
          new_ncs_copy = ncs_copy(copy_iselection=ncs_isel, rot=r, tran=t)
          new_nrg.copies.append(new_ncs_copy)
      # compare master_isel_test and master_isel
      ncs_restraints_group_list.append(new_nrg)
    return ncs_restraints_group_list

  def update_using_ncs_restraints_group_list(self,ncs_restraints_group_list):
    """
    Update ncs_group_object rotations and transformations.

    Note that to insure proper assignment the ncs_restraints_group_list
    should be produced using the get_ncs_restraints_group_list method

    Args:
      ncs_restraints_group_list: a list of ncs_restraint_group objects
    """
    assert len(ncs_restraints_group_list) == len(self.ncs_group_map)
    group_id_list = sort_dict_keys(self.ncs_group_map)
    for k in group_id_list:
      v = self.ncs_group_map[k]
      nrg = ncs_restraints_group_list.pop(0)
      for tr in sorted(list(v[1])):
        if self.transform_to_ncs.has_key(tr):
          ncs_copy = nrg.copies.pop(0)
          self.ncs_transform[tr].r = ncs_copy.r
          self.ncs_transform[tr].t = ncs_copy.t
          # Test that the correct transforms are updated
          ncs_isel = flex.size_t()
          for sel in self.transform_to_ncs[tr]:
            ncs_isel.extend(self.ncs_to_asu_map[sel])
          assert ncs_copy.copy_iselection == ncs_isel

  def get_transform_records(self, file_name=None,
                          ncs_only=True,
                          pdb_hierarchy=None,
                          xrs=None,
                          fmodel=None,
                          crystal_symmetry=None,
                          mtrix=None,
                          biomt=None,
                          write=False,
                          log = sys.stdout):
    """
    Write to a file or prints transformation records.
    with or without PDB atoms and Cryst records.
    If no pdb_hierarchy, xray structure or fmodel are provided, the function
    will return only the MTRIX/BIOMT records

    Arguments:
    file_name: (str) output file name
    ncs_only: (bool) When False, the comple ASU will be printed (applicable
              only with MTRIX records)
    pdb_hierarchy: (pdb_hierarchy object)
    xrs: (xray structure) for crystal symmetry
    fmodel: (fmodel object)
    crystal_symmetry: crystal symmetry records
    mtrix: (bool) When True -> write MTRIX records
    biomt: (bool) When True -> write BIOMT records
    write: (bool) when False, will will not write to file or print

    Return:
    PDB string
    """
    if (not mtrix) and (not biomt):
      mtrix = True
      biomt = False
    assert bool(mtrix) == (not bool(biomt))
    if biomt: ncs_only = True
    mtrix_object = self.build_MTRIX_object(ncs_only=ncs_only)
    pdb_header_str = ''
    new_ph_str = ''
    #
    if fmodel:
      xrs = fmodel.xray_structure
    if xrs and self.hierarchy and (not pdb_hierarchy):
      pdb_hierarchy = self.hierarchy
      pdb_str = xrs.as_pdb_file()
      pdb_header_str = get_pdb_header(pdb_str)
      xyz = pdb_hierarchy.atoms().extract_xyz()
      new_xyz = xrs.sites_cart()
      if new_xyz.size() > xyz.size():
        ncs_only = True
        xrs = xrs.select(self.ncs_atom_selection.iselection())
        new_xyz = xrs.sites_cart()
      assert new_xyz.size() == xyz.size()
      pdb_hierarchy.atoms().set_xyz(new_xyz)
    if pdb_hierarchy:
      ph = pdb_hierarchy
      if xrs:
        crystal_symmetry = xrs.crystal_symmetry()
      pdb_str = ph.as_pdb_string(crystal_symmetry=crystal_symmetry)
      if not pdb_header_str:
       pdb_header_str = get_pdb_header(pdb_str)
      if ncs_only:
        new_ph = ph.select(self.ncs_atom_selection.iselection())
      else:
        msg = 'The complete ASU hierarchy need to be provided !!!'
        assert len(self.ncs_atom_selection) == len(ph.atoms()),msg
        new_ph = ph
      new_ph_str = new_ph.as_pdb_string(crystal_symmetry=None)
    #
    if mtrix:
      transform_rec = mtrix_object.as_pdb_string()
    elif biomt:
      transform_rec = mtrix_object.format_BOIMT_pdb_string()
    #
    if write:
      if file_name:
        f = open(file_name,'w')
        print >> f, pdb_header_str
        print >> f, transform_rec
        print >> f, new_ph_str
        f.close()
      else:
        print >> log,pdb_header_str
        print >> log,transform_rec
        print >> log,new_ph_str

    return '\n'.join([pdb_header_str,transform_rec,new_ph_str])

  def get_ncs_info_as_spec(
          self,
          pdb_hierarchy_asu=None,
          xrs=None,
          fmodel=None,
          file_name=None,
          log = sys.stdout,
          write=False):
    """
    Returns and writes to a ncs spec file or prints transformation records.
    Note that the spec_object has methods format_all_for_resolve
    and format_all_for_phenix_refine

    Note that while ncs_groups can master ncs can be comprised from several
    chains, the spec groups can not. So groups with multiple chains in the
    master selection are splitted

    Arguments:
    file_name: (str) output file name
    pdb_hierarchy: (pdb_hierarchy object)
    xrs: (xray structure) for crystal symmetry
    fmodel: (fmodel object)
    write: (bool) when False, will not write to file or print

    Return:
    spec_object
    """
    spec_object = ncs.ncs()
    if fmodel:
      xrs = fmodel.xray_structure
    if xrs and (not pdb_hierarchy_asu):
      xyz = xrs.sites_cart()
    else:
      xyz = pdb_hierarchy_asu.atoms().extract_xyz()

    for gn,gr in self.ncs_group_map.iteritems():
      for gr_chains in gr[0]:
        gr_dict = {}
        # gr -> [master selection str, set of transforms]
        # Process one chain, in the master ncs, at a time
        for gr_chain in get_list_of_chains_selection(gr_chains):
          for s_str in gr[1]:
            # get ncs copy chain name, that corresponds to master and transform
            gr_key = gr_chain + '_' + s_str
            gr_dict[gr_key] = self.ncs_copies_chains_names[gr_key]
        sorted_keys = sort_dict_keys(gr_dict)
        center_orth = []
        rotations = []
        translations = []
        chain_residue_id_list = []
        chain_residue_range_list = []
        rmsd_list = []
        residues_in_common_list = []
        for k in sorted_keys:
          chain_id = gr_dict[k]
          chain_residue_id_list.append(chain_id)
          [range_list,ncs_sel],rmsd = self.common_res_dict[k]
          chain_residue_range_list.append(range_list)
          center_orth.append(get_center_orth(xyz,ncs_sel))
          transform_key = k.split('_')[1]
          tr = self.ncs_transform[transform_key]
          # use the rmsd of the ncs related atoms rather than the transform
          # rmsd_list.append(tr.rmsd)
          rmsd_list.append(rmsd)
          # in spec files transform is copy -> master, not master -> copy
          r,t = inverse_transform(tr.r,tr.t)
          rotations.append(r)
          translations.append(t)
          residues_in_common_list.append(len(ncs_sel))
        # build group
        spec_object.import_ncs_group(
          center_orth = center_orth,
          ncs_rota_matr = rotations,
          trans_orth = translations,
          rmsd_list = rmsd_list,
          chain_residue_id = [chain_residue_id_list,chain_residue_range_list],
          residues_in_common_list = residues_in_common_list,
          ncs_domain_pdb = None)
    if write:
      spec_object.format_all_for_group_specification(
        file_name=file_name,log=log)
    return spec_object

  def build_asu_hierarchy(self,
                          pdb_hierarchy,
                          round_coordinates=True):
    """
    Build ASU hierarchy

    Arguments:
    pdb_hierarchy: pdb hierarchy of the master NCS
    round_coordinates: (bool) round coordinates of new NCS copies,
                        for sites_cart constancy
    Return:
    ASU hierarchy
    """
    # Build only for PDB when there is a single NCS group
    assert self.number_of_ncs_groups == 1
    new_ph = pdb_hierarchy.deep_copy()
    ncs_restraints_group_list = self.get_ncs_restraints_group_list()
    new_sites = apply_transforms(
      ncs_coordinates = pdb_hierarchy.atoms().extract_xyz(),
      ncs_restraints_group_list = ncs_restraints_group_list,
      total_asu_length =  self.total_asu_length,
      extended_ncs_selection = flex.size_t_range(pdb_hierarchy.atoms().size()),
      round_coordinates = round_coordinates)
    model = new_ph.models()[0]
    tr_assignment_order = []
    for tr in self.transform_order:
      for (ch_id, (sel_start,sel_end)) in self.model_order_chain_ids:
        key = 'chain ' + ch_id
        tr_key  =  key + '_' + tr

        ncs_selection = self.asu_to_ncs_map[key][sel_start:sel_end]
        tr_assignment_order.append([tr_key,ncs_selection])

    for tr,ncs_selection in tr_assignment_order:
      new_part = pdb_hierarchy.select(ncs_selection).deep_copy()
      new_chain = iotbx.pdb.hierarchy.ext.chain()
      new_chain.id = self.ncs_copies_chains_names[tr]
      for res in new_part.residue_groups():
        new_chain.append_residue_group(res.detached_copy())
      model.append_chain(new_chain)
    new_ph.atoms().set_xyz(new_sites)
    return new_ph

def add_to_dict(d,k,v):
  if d.has_key(k):
    d[k].append(v)
  else:
    d[k] = [v]
  return d

def find_same_transform(r,t,transforms,eps=0.1,angle_eps=5):
  """
  Check if the rotation r and translation t exist in the transform dictionary.

  Comparing rotations and the result of applying rotation and translation on
  a test vector

  Args:
    angle_eps: (float) allowed difference in similar rotations
    eps: (float) allowed difference in the average distance between
  :return tr_num: (str) transform serial number
  :return is_transpose: (bool) True if the matching transform is transpose
  """
  is_transpose = False
  tr_num = None
  for k,v in transforms.iteritems():
    if hasattr(v,'r'):
      rr = v.r
      tt = v.t
    else:
      (rr,tt) = v[2]
    is_the_same, is_transpose = is_same_transform(
      r, t, rr, tt, eps=eps, angle_eps=angle_eps)
    if is_the_same:
      return k, is_transpose
  return tr_num, is_transpose

def is_same_transform(r1,t1,r2,t2,eps=0.1,angle_eps=5):
  """
  Args:
    r1, r2: Rotation matrices
    t1, t2: Translation vectors
    eps, angle_eps: allowed numerical difference

  Returns:
  :return: (bool,bool) (is_the_same, is_transpose)
  """
  assert r1.is_r3_rotation_matrix(rms_tolerance=0.001)
  assert r2.is_r3_rotation_matrix(rms_tolerance=0.001)
  # test vector
  xyz = flex.vec3_double([(11,103,523),(-500.0,2.0,10.0),(0.0,523.0,-103.0)])
  a_ref = (r1.elems * xyz + t1).as_double()
  rt, tt = inverse_transform(r1,t1)
  a_ref_transpose = (rt.elems * xyz + tt).as_double()
  v1 = get_rotation_vec(r1)
  v2 = get_rotation_vec(r2)
  a = (r2.elems * xyz + t2).as_double()
  d = (a_ref-a)
  d = (d.dot(d))**.5/a.size()
  dt = (a_ref_transpose-a)
  dt = (dt.dot(dt))**.5/a.size()
  ang = angle_between_rotations(v1,v2)
  d_ang = min(ang, (180 - ang))
  if (d_ang < angle_eps) and (d < eps):
    return True, False
  elif (d_ang < angle_eps) and (dt < eps):
    return True, True
  else:
    return False, False

def inverse_transform(r,t):
  r = r.transpose()
  t = - r*t
  return r,t

def get_list_of_chains_selection(selection_str):
  """
  Args:
    selection_str: (str) selection string

  Returns:
  :return: (list of str) of the format ['chain X', 'chain Y',...]
  """
  sstr = selection_str.replace(')',' ')
  sstr = sstr.replace('CHAIN','chain')
  sstr = sstr.replace('Chain','chain') + ' '
  pos_list = [x.end() for x in re.finditer('chain ',sstr)]
  ch_id_list = [sstr[i:sstr.find(' ',i)] for i in pos_list]
  chain_list = ['chain ' + x for x in ch_id_list]
  return chain_list

def separate_selection_string(s):
  s.replace('Chain ','chain ')
  s.replace('CHAIN ','chain ')
  s.replace(' or chain ','chain ')
  s.replace(') or (chain ','chain ')
  s.replace(')or(chain ','chain ')
  if (s[-1] == ')') and (s[0] == '('): s = s[:-1]
  s = s.split('chain ')
  s_list = []
  for sel_str in s:
    sel_str = sel_str.strip()
    if sel_str.endswith(' or'): sel_str = sel_str[:-3]
    if not sel_str in ['','(']:
      s_list.append('chain ' + sel_str)
  return s_list


def get_rotation_vec(r):
  eigen = eigensystem.real_symmetric(r.as_sym_mat3())
  eigenvectors = eigen.vectors()
  eigenvalues = eigen.values()
  i = list(eigenvalues.round(4)).index(1)
  return eigenvectors[i:(i+3)]

def angle_between_rotations(v1,v2):
    cos_angle = v1.dot(v2)
    result = math.acos(min(1,cos_angle))
    result *= 180/math.pi
    return result

def get_pdb_header(pdb_str):
  """
  Collect CRYST and SCALE records

  Args:
    pdb_str: (str) pdb type string

  Returns:
  :return: the portion of the pdb_str till the first ATOM
  """
  pdb_str = pdb_str.splitlines()
  pdb_header_lines = []
  for x in pdb_str:
    if x.startswith('ATOM'): break
    else: pdb_header_lines.append(x)
  return '\n'.join(pdb_header_lines)

def get_center_orth(xyz,selection):
  """
  Args:
    xyz:(flex.vec3_double) the complete asu sites cart (atoms coordinates)
    selection:

  Returns:
  :return:(flex.vec3_double) center of coordinates for the selected coordinates
  """
  new_xyz = xyz.select(selection)
  return new_xyz.mean()

def format_num_as_str(n):
  """  return a 3 digit string of n  """
  if n > 999 or n < 0:
    raise IOError('Input out of the range 0 - 999.')
  else:
    s1 = n//100
    s2 = (n%100)//10
    s3 = n%10
    return str(s1) + str(s2) + str(s3)

def all_ncs_copies_not_present(transform_info):
  """
  Check if a single NCS is in transform_info, all transforms, but the
  identity should no be present

  Args:
    transform_info: (transformation object)

  Returns:
  :return: (bool)
  """
  test = False
  ti = transform_info
  for (r,t,n,cp) in zip(ti.r,ti.t,ti.serial_number,ti.coordinates_present):
    if not is_identity(r,t):
      test = test or cp
  return not test

def is_identity(r,t):
  return (r.is_r3_identity_matrix() and t.is_col_zero())

def all_ncs_copies_present(transform_info):
  """
  Check if all transforms coordinates are present,
  if the complete ASU is present

  Args:
    transform_info: (transformation object)

  Returns:
  :return: (bool)
  """
  test = True
  for cp in transform_info.coordinates_present:
    test = test and cp
  return test

def order_transforms(transform_to_ncs):
  """ set transformation application order  """
  return sorted(transform_to_ncs,key=lambda key: int(key[1:]))

def uniqueness_test(unique_selection_set,new_item):
  """
  When processing phil parameters. Insert new item to set, if not there,
  raise an error if already in set

  Args:
    unique_selection_set: (set)
    new_item: (str)

  Returns:
  :return: updated set
  """
  if new_item in unique_selection_set:
    raise IOError,'Phil selection strings are not unique !!!'
  else:
    unique_selection_set.add(new_item)
    return unique_selection_set

def get_rot_trans(master_ncs_ph=None,
                  ncs_copy_ph=None,
                  master_atoms=None,
                  copy_atoms=None,
                  rms_eps=0.02):
  """
  Get rotation and translation using superpose

  Args:
    master_ncs_ph: pdb hierarchy input object
    ncs_copy_ph: pdb hierarchy input object
    master_atoms: (flex.vec3_double) master atoms sites cart
    copy_atoms: (flex.vec3_double) copy atoms sites cart

  Returns:
  :return r: rotation matrix
  :return t: translation vector
  If can't match the two selection or if it is a bad match return: None, None
  """
  if (not master_atoms) and bool(master_ncs_ph): master_ncs_ph.atoms()
  if (not copy_atoms) and bool(ncs_copy_ph): copy_atoms = ncs_copy_ph.atoms()
  t1 = not (master_atoms is None)
  t2 = not (copy_atoms is None)
  if t1 and t2:
    test_length = master_atoms.size() != copy_atoms.size()
    if test_length: return None,None
    reference_sites = copy_atoms.extract_xyz()
    other_sites     = master_atoms.extract_xyz()
    lsq_fit_obj = superpose.least_squares_fit(
      reference_sites = reference_sites,
      other_sites     = other_sites)
    r = lsq_fit_obj.r
    t = lsq_fit_obj.t
    # test fit quality
    xyz = r.elems * other_sites + t
    delta = reference_sites.rms_difference(xyz)
    if delta > rms_eps: return None,None
  else:
    r = matrix.sqr([0]*9)
    t = matrix.col([0,0,0])
  return r,t

def get_pdb_selection(ph,selection_str):
  """
  Args:
    ph: pdb hierarchy input object
    selection_str:

  Returns:
  :return: atoms of the portion of the hierarchy according to the
           selection
  """
  if not (ph is None):
    temp = ph.hierarchy.atom_selection_cache()
    selection_str_list = selection_str.split(' or ')
    selection_indices = flex.size_t()
    for sel_str in selection_str_list:
      selection_indices.extend(temp.selection(sel_str).iselection())
    atoms = ph.hierarchy.atoms()
    return atoms.select(selection_indices)
  else:
    return None

def update_selection_ref(selection_ref,new_selection):
  """
  Test for overlapping selection and then updates the selection_ref
  with the new_selection

  Both received and return arguments are flex.bool
  """
  test = (selection_ref & new_selection).count(True) == 0
  assert test,'Overlapping atom selection. Check phil parameters..'
  return selection_ref | new_selection

def get_ncs_group_selection(chain_residue_id):
  """
  Args:
    chain_residue_id: [[chain id's],[[[residues range]],[[...]]]

  Returns:
  :return: selection lists, with selection string for each ncs copy in the group
  """
  chains = chain_residue_id[0]
  res_ranges = chain_residue_id[1]
  assert len(chains) == len(res_ranges)
  ncs_selection = []
  for c,rr in zip(chains, res_ranges):
    c = c.strip()
    assert c.find(' ') < 0,'Multiple chains in a single spec ncs group'
    ch_selection = 'chain ' + c
    res_range = ['resseq {0}:{1}'.format(s,e) for s,e in rr]
    res_range = '(' + ' or '.join(res_range) + ')'
    ncs_selection.append(ch_selection + ' and ' + res_range)
  return ncs_selection

def get_transform_order(transform_to_ncs):
  """ order transforms mainly for proper chain naming """
  transform_order = order_transforms(transform_to_ncs)
  transform_chain_assignment = []
  for tr_id in transform_order:
    for tr_selection in transform_to_ncs[tr_id]:
      transform_chain_assignment.append(tr_selection)
  return transform_chain_assignment

def update_ncs_group_map(
        ncs_group_map, ncs_group_id, selection_ids, transform_id):
  """  Update ncs_group_map that maps a group ID to a master selection and a
  list of objects containing transforms and copies selections """
  if isinstance(selection_ids, str): selection_ids = [selection_ids]
  if ncs_group_map.has_key(ncs_group_id):
    ncs_group_map[ncs_group_id][0].update(set(selection_ids))
    ncs_group_map[ncs_group_id][1].add(transform_id)
  else:
    ncs_group_map[ncs_group_id] = [set(selection_ids),{transform_id}]
  return ncs_group_map

def sort_dict_keys(dict):
  return sorted(dict,key=lambda k:dict[k])

def g(x,y):
  """ Cantor pairing
  Args:
    x: (int)
    y: (int)

  Returns:
  :return: unique key
  """
  x = abs(x)
  y = abs(y)
  return math.floor(0.5*(1 + x + y)*(x + y) + y)

def f(r):
  """
  Use Cantor pairing to get a numerical key for a rotation and the rotation
  transpose

  Args:
    r: rotation matrix

  Returns:
  :return: key1,key2
  """
  (r11,r12,r13,r21,r22,r23,r31,r32,r33) = (10*r).round(0).elems
  key1 = str(int(g(r11,g(r22,r33))))

  (r11,r12,r13,r21,r22,r23,r31,r32,r33) = (10*r.transpose()).round(0).elems
  key2 = str(int(g(r11,g(r22,r33))))
  return key1,key2


def get_minimal_master_ncs_group(pdb_hierarchy_inp):
  """
  Finds minimal number ncs relations, the largest common ncs groups

  Args:
    pdb_hierarchy_inp: iotbx.pdb.hierarchy.input

  Returns:
    ncs_phil_groups: (list) list of ncs_groups_container
  """
  # initialize parameters
  ncs_phil_groups = []
  transform_dict = {}
  transform_to_group = {}
  chains_in_groups = set()
  tr_sn = 0
  # collect unique chain IDs
  ph = pdb_hierarchy_inp
  model  = ph.hierarchy.models()[0]
  chain_ids = list({x.id for x in model.chains()})
  # loop over all chains
  n_chains = len(chain_ids)
  ph_chains = model.chains()
  for i in xrange(n_chains-1):
    master_ch_id = ph_chains[i].id
    if master_ch_id in chains_in_groups: continue
    master_sel = 'chain ' + master_ch_id
    master_atoms = get_pdb_selection(ph=ph,selection_str=master_sel)
    for j in xrange(i+1,n_chains):
      copy_ch_id = ph_chains[j].id
      if copy_ch_id in chains_in_groups: continue
      copy_sel = 'chain ' + copy_ch_id
      copy_atoms = get_pdb_selection(ph=ph,selection_str=copy_sel)
      r,t = get_rot_trans(master_atoms=master_atoms,copy_atoms= copy_atoms)
      if r:
        # the chains relates by ncs operation
        tr_num, is_transpose = find_same_transform(r,t,transform_to_group)
        if is_transpose:
          temp_master, temp_copy = copy_ch_id, master_ch_id
        else:
          temp_master, temp_copy = master_ch_id, copy_ch_id
        if tr_num:
          # update dictionaries with additions to master and copies
          transform_to_group[tr_num][0].append(temp_master)
          transform_to_group[tr_num][1].append(temp_copy)
          chains_in_groups.add(temp_copy)
        else:
          # create a new transform object and update groups
          tr_sn += 1
          transform_to_group[tr_sn] = [[temp_master],[temp_copy],(r,t)]
          chains_in_groups.add(temp_copy)

  # remove overlapping selection
  master_size = [[len(v[0]),k] for k,v in transform_to_group.iteritems()]
  master_size.sort()
  chain_left_to_add = set(chain_ids)
  transform_to_use = set()
  while bool(chain_left_to_add) and bool(master_size):
    [n,k] = master_size.pop(0)
    tr = transform_to_group[k]
    if bool(set(tr[1]) & chain_left_to_add):
      transform_to_use.add(k)
      chain_left_to_add -= set(tr[1])
      chain_left_to_add -= set(tr[0])

  # delete all but transform_to_use
  keys = transform_to_group.keys()
  for key in keys:
    if not key in transform_to_use:
      transform_to_group.pop(key)

  # find all groups with common masters and organize at same order
  for k,v in transform_to_group.iteritems():
    sorted_key = sorted(v[0])
    # organize at same order
    sort_map = [v[0].index(x) for x in sorted_key]
    v[1] = [v[1][i] for i in sort_map]
    key = '_'.join(sorted_key)
    if transform_dict.has_key(key):
      transform_dict[key][1].append(v[1])
    else:
      transform_dict[key] = [sorted_key,[v[1]]]

  # build ncs group selection list
  for v in transform_dict.itervalues():
    new_ncs_group = ncs_groups_container()
    masters = ['chain ' + x for x in v[0]]
    copies  = []
    for cp in v[1]:
      temp = ['chain ' + x for x in cp]
      copies.append(' or '.join(temp))

    new_ncs_group.master_ncs_selection = ' or '.join(masters)
    new_ncs_group.selection_copy = copies
    ncs_phil_groups.append(new_ncs_group)

  return ncs_phil_groups


def get_largest_common_ncs_groups(pdb_hierarchy_inp):
  """
  Finds minimal number ncs relations, the largest common ncs groups

  Args:
    pdb_hierarchy_inp: iotbx.pdb.hierarchy.input

  Returns:
  :return ncs_phil_groups: (list) list of ncs_groups_container
  """
  # Todo : redo all test for this section
  # initialize parameters
  ncs_phil_groups = []
  transform_dict = {}
  transform_to_group = {}
  copy_to_trnasform = {}
  chains_in_groups = set()
  tr_sn = 0
  # collect unique chain IDs
  ph = pdb_hierarchy_inp
  model  = ph.hierarchy.models()[0]
  chain_ids = list({x.id for x in model.chains()})
  # loop over all chains
  n_chains = len(chain_ids)
  ph_chains = model.chains()
  for i in xrange(n_chains-1):
    master_ch_id = ph_chains[i].id
    master_sel = 'chain ' + master_ch_id
    master_atoms = get_pdb_selection(ph=ph,selection_str=master_sel)
    for j in xrange(i+1,n_chains):
      copy_ch_id = ph_chains[j].id
      copy_sel = 'chain ' + copy_ch_id
      copy_atoms = get_pdb_selection(ph=ph,selection_str=copy_sel)
      r,t = get_rot_trans(master_atoms=master_atoms,copy_atoms= copy_atoms)
      if r:
        # the chains relates by ncs operation
        tr_num, is_transpose = find_same_transform(r,t,transform_to_group)
        if is_transpose:
          temp_master, temp_copy = copy_ch_id, master_ch_id
        else:
          temp_master, temp_copy = master_ch_id, copy_ch_id
        if tr_num:
          copies_ids = transform_to_group[tr_num][1]
          if not (temp_master in copies_ids):
            # clean up when adding to new group
            if copy_to_trnasform.has_key(temp_copy):
              tr_list = copy_to_trnasform.pop(temp_copy,None)
              for tr in tr_list:
                t1 = transform_to_group.has_key(tr)
                if t1 and (len(transform_to_group[tr][1]) == 1):
                  transform_to_group.pop(tr,None)
              copy_to_trnasform = add_to_dict(
                d=copy_to_trnasform,k=temp_copy,v=tr_num)
            # clean up new master
            if copy_to_trnasform.has_key(temp_master):
              tr_list = copy_to_trnasform.pop(temp_master,None)
              for tr in tr_list:
                t1 = transform_to_group.has_key(tr)
                if t1 and (len(transform_to_group[tr][1]) == 1):
                  transform_to_group.pop(tr,None)
            # update dictionaries with additions to master and copies
            transform_to_group[tr_num][0].append(temp_master)
            transform_to_group[tr_num][1].append(temp_copy)
            chains_in_groups.update(set(transform_to_group[tr_num][1]))
        else:
          # create a new transform object and update groups
          tr_sn += 1
          transform_to_group[tr_sn] = [[temp_master],[temp_copy],(r,t)]
          copy_to_trnasform = add_to_dict(
            d=copy_to_trnasform,k=temp_copy,v=tr_sn)

  # remove masters if appear in copies
  for k,v in transform_to_group.iteritems():
    masters = v[0]
    copies = v[1]
    common_ids = set(masters) & set(copies)
    while common_ids:
      ch_id = common_ids.pop()
      i = masters.index(ch_id)
      masters.pop(i)
      copies.pop(i)
      common_ids = set(masters) & set(copies)
    transform_to_group[k][0] = masters
    transform_to_group[k][1] = copies

  #clean up singles
  multiple_tr_num = [k for k,v in transform_to_group.iteritems() if
                    (len(v[0]) > 1)]
  singles_tr_num = [k for k,v in transform_to_group.iteritems() if
                    (len(v[0]) == 1)]
  for m_tr_num in multiple_tr_num:
    m_m = transform_to_group[m_tr_num][0]
    m_c = transform_to_group[m_tr_num][1]
    for s_tr_num in singles_tr_num:
      if transform_to_group.has_key(s_tr_num):
        s_m = transform_to_group[s_tr_num][0][0]
        s_c = transform_to_group[s_tr_num][1][0]
        if (s_m in m_m) and (s_c in m_c):
          transform_to_group.pop(s_tr_num,None)
        elif (s_c in m_m) and (s_m in m_c):
          transform_to_group.pop(s_tr_num,None)
        elif (s_c in m_c) and (s_m in m_c):
          transform_to_group.pop(s_tr_num,None)
        elif (s_c in m_m) and (s_m in m_m):
          transform_to_group.pop(s_tr_num,None)
        elif (s_c in chains_in_groups) and (s_m in chains_in_groups):
          transform_to_group.pop(s_tr_num,None)

  # remove overlapping selection
  master_size = [[len(v[0]),k] for k,v in transform_to_group.iteritems()]
  master_size.sort()
  chain_left_to_add = set(chain_ids)
  transform_to_use = set()
  while bool(chain_left_to_add) and bool(master_size):
    [n,k] = master_size.pop()
    tr = transform_to_group[k]
    if bool(set(tr[1]) & chain_left_to_add):
      transform_to_use.add(k)
      chain_left_to_add -= set(tr[1])
      chain_left_to_add -= set(tr[0])

  # delete all but transform_to_use
  keys = transform_to_group.keys()
  for key in keys:
    if not key in transform_to_use:
      transform_to_group.pop(key)

  # find all groups with common masters and organize at same order
  for k,v in transform_to_group.iteritems():
    sorted_key = sorted(v[0])
    # organize at same order
    sort_map = [v[0].index(x) for x in sorted_key]
    v[1] = [v[1][i] for i in sort_map]
    key = '_'.join(sorted_key)
    if transform_dict.has_key(key):
      transform_dict[key][1].append(v[1])
    else:
      transform_dict[key] = [sorted_key,[v[1]]]

  # build ncs group selection list
  for v in transform_dict.itervalues():
    new_ncs_group = ncs_groups_container()
    masters = ['chain ' + x for x in v[0]]
    copies  = []
    for cp in v[1]:
      temp = ['chain ' + x for x in cp]
      copies.append(' or '.join(temp))

    new_ncs_group.master_ncs_selection = ' or '.join(masters)
    new_ncs_group.selection_copy = copies
    ncs_phil_groups.append(new_ncs_group)

  return ncs_phil_groups

class ncs_copy():

  def __init__(self,copy_iselection, rot, tran):
    self.copy_iselection = copy_iselection
    self.r = rot
    self.t = tran

class ncs_restraint_group(object):

  def __init__(self,master_iselection):
    self.master_iselection = master_iselection
    self.copies = []

class ncs_groups_container(object):

  def __init__(self):
    self.master_ncs_selection = ''
    self.selection_copy = []


class transform(object):

  def __init__(self,
               rotation = None,
               translation = None,
               serial_num = None,
               coordinates_present = None,
               ncs_group_id = None,
               rmsd = 0):
    """
    Basic transformation properties

    Argument:
    rotation : Rotation matrix object
    translation: Translation matrix object
    serial_num : (int) Transform serial number
    coordinates_present: equals 1 when coordinates are presents in PDB file
    ncs_group_id : (int) ncs groups in, all the selections that the same
                   transforms are being applied to
    """
    self.r = rotation
    self.t = translation
    self.serial_num = serial_num
    self.coordinates_present = bool(coordinates_present)
    self.ncs_group_id = ncs_group_id
    self.rmsd = rmsd
