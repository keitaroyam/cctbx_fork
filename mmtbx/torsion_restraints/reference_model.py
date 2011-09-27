import mmtbx.alignment
from iotbx.pdb import amino_acid_codes
from libtbx import group_args
import cctbx.geometry_restraints
from mmtbx.validation.rotalyze import rotalyze
from mmtbx.refinement import fit_rotamers
from mmtbx.rotamer.sidechain_angles import SidechainAngles
import mmtbx.monomer_library
from cctbx.array_family import flex
import iotbx.phil
import libtbx.load_env
from libtbx.utils import Sorry
from mmtbx import secondary_structure
from scitbx.matrix import rotate_point_around_axis
from libtbx.str_utils import make_sub_header
from mmtbx.torsion_restraints import utils
import sys, re

TOP_OUT_FLAG = True

reference_model_params = iotbx.phil.parse("""
 file = None
   .type = path
   .short_caption = Reference model
   .style = bold file_type:pdb hidden
 sigma = 1.0
   .type = float
 limit = 15.0
   .type = float
 slack = 0.0
   .type = float
 hydrogens = False
   .type = bool
 main_chain = True
   .type = bool
 side_chain = True
   .type = bool
 fix_outliers = True
   .type = bool
 strict_rotamer_matching = False
   .type = bool
 auto_shutoff_for_ncs = False
   .type = bool
 auto_align = False
   .type = bool
 secondary_structure_only = False
   .type = bool
 edits
   .short_caption = Edit reference model restraints
   .style = menu_item parent_submenu:reference_model auto_align noauto
   .expert_level = 2
 {
   include scope \
     mmtbx.monomer_library.pdb_interpretation.geometry_restraints_edits_str
 }
 remove
   .short_caption = Remove geometry restraints from reference model
   .expert_level = 2
   .style = menu_item parent_submenu:reference_model auto_align noauto
 {
   include scope \
   mmtbx.monomer_library.pdb_interpretation.geometry_restraints_remove_str
 }
 reference_group
  .multiple=True
  .optional=True
  .short_caption=Reference group
  .style = noauto auto_align menu_item parent_submenu:reference_model
{
  reference=None
    .type=atom_selection
    .short_caption=Reference selection
  selection=None
    .type=atom_selection
    .short_caption=Restrained selection
}
 alignment
    .help = Set of parameters for sequence alignment. Defaults are good for most \
            of cases
    .short_caption = Sequence alignment
    .style = box auto_align
{
  alignment_style =  local *global
    .type = choice
  gap_opening_penalty = 1
    .type = float
  gap_extension_penalty = 1
    .type = float
  similarity_matrix =  blosum50  dayhoff *identity
    .type = choice
}
 alignment_group
  .multiple=True
  .optional=True
  .short_caption=Sequence alignment group
  .style = noauto auto_align menu_item parent_submenu:reference_model
{
  reference=None
    .type=atom_selection
    .short_caption=Reference selection
  selection=None
    .type=atom_selection
    .short_caption=Restrained selection
}
""")

class reference_model(object):

  def __init__(self,
               geometry,
               pdb_hierarchy,
               xray_structure,
               geometry_ref,
               sites_cart_ref,
               pdb_hierarchy_ref,
               params=None,
               log=None):
    if(log is None):
      self.log = sys.stdout
    else:
      self.log = log
    self.params = params
    self.geometry = geometry
    self.pdb_hierarchy = pdb_hierarchy
    self.geometry_ref = geometry_ref
    self.sites_cart_ref = sites_cart_ref
    self.pdb_hierarchy_ref = pdb_hierarchy_ref
    self.i_seq_name_hash = utils.build_name_hash(
                             pdb_hierarchy=self.pdb_hierarchy)
    self.i_seq_name_hash_ref = utils.build_name_hash(
                                 pdb_hierarchy=self.pdb_hierarchy_ref)
    self.reference_dihedral_hash = self.build_dihedral_hash(
                           geometry=self.geometry_ref,
                           sites_cart=self.sites_cart_ref,
                           pdb_hierarchy=self.pdb_hierarchy_ref,
                           include_hydrogens=self.params.hydrogens,
                           include_main_chain=self.params.main_chain,
                           include_side_chain=self.params.side_chain)
    self.dihedral_proxies_ref = geometry_ref.dihedral_proxies
    self.chirality_proxies_ref = geometry_ref.chirality_proxies
    self.reference_dihedral_proxies = None
    self.match_map = None
    self.proxy_map = None
    self.build_reference_dihedral_proxy_hash()
    self.get_reference_dihedral_proxies()

  def update_reference_dihedral_proxies(self,
                                        geometry,
                                        sites_cart_ref):
    for rdp in geometry.reference_dihedral_proxies:
      key = ""
      for i_seq in rdp.i_seqs:
        key += self.i_seq_name_hash_ref[self.match_map[i_seq]]
      ref_proxy = self.reference_dihedral_proxy_hash[key]
      di = cctbx.geometry_restraints.dihedral(
             sites_cart=sites_cart_ref,
             proxy=ref_proxy)
      rdp.angle_ideal = di.angle_model

  def top_out_function(self, x, weight, top):
    return top*(1-exp(-weight*x**2/top))

  def top_out_gradient(self, x, weight, top):
    return (2*weight*x)*exp(-(weight*x**2)/top)

  def top_out_curvature(self, x, weight, top):
    return (2*weight*(top - 2*weight*x**2))/top**2*exp(-(weight*x**2)/top)

  def extract_sequence_and_sites(self, pdb_hierarchy, selection):
    seq = []
    result = []
    counter = 0
    for model in pdb_hierarchy.models():
      for chain in model.chains():
        for rg in chain.residue_groups():
          if(len(rg.unique_resnames())==1):
            resname = rg.unique_resnames()[0]
            olc=amino_acid_codes.one_letter_given_three_letter.get(resname,"X")
            atoms = rg.atoms()
            i_seqs = utils.get_i_seqs(atoms)
            if(olc!="X") and utils.is_residue_in_selection(i_seqs, selection):
              seq.append(olc)
              result.append(group_args(i_seq = counter, rg = rg))
              counter += 1
    return "".join(seq), result

  def _alignment(self, pdb_hierarchy,
                    pdb_hierarchy_ref,
                    params,
                    selections,
                    log=None):
    if(log is None): log = sys.stdout
    res_match_hash = {}
    model_mseq_res_hash = {}
    model_seq, model_structures = self.extract_sequence_and_sites(
      pdb_hierarchy=pdb_hierarchy,
      selection=selections[0])
    ref_mseq_res_hash = {}
    ref_seq, ref_structures = self.extract_sequence_and_sites(
      pdb_hierarchy = pdb_hierarchy_ref,
      selection=selections[1])
    for struct in model_structures:
      model_mseq_res_hash[struct.i_seq] = struct.rg.atoms()[0].pdb_label_columns()[4:]
    for struct in ref_structures:
      ref_mseq_res_hash[struct.i_seq] = struct.rg.atoms()[0].pdb_label_columns()[4:]
    align_obj = mmtbx.alignment.align(
      seq_a                 = model_seq,
      seq_b                 = ref_seq,
      gap_opening_penalty   = params.alignment.gap_opening_penalty,
      gap_extension_penalty = params.alignment.gap_extension_penalty,
      similarity_function   = params.alignment.similarity_matrix,
      style                 = params.alignment.alignment_style)
    alignment = align_obj.extract_alignment()
    matches = alignment.matches()
    exact_match_selections = alignment.exact_match_selections()
    exact_a = tuple(exact_match_selections[0])
    exact_b = tuple(exact_match_selections[1])
    for i, i_seq in enumerate(alignment.i_seqs_a):
      if i_seq != None:
        if alignment.i_seqs_b[i] != None and matches[i] in ['*','|']:
          res_match_hash[model_mseq_res_hash[i_seq]] = \
            ref_mseq_res_hash[alignment.i_seqs_b[i]]
    print >> log, "  --> aligning model sequence to reference sequence"
    alignment.pretty_print(block_size  = 50,
                           n_block     = 1,
                           top_name    = "model",
                           bottom_name = "ref",
                           out         = log)
    return res_match_hash

  def process_reference_groups(self,
                               pdb_hierarchy,
                               pdb_hierarchy_ref,
                               params,
                               log=None):
    if(log is None): log = sys.stdout
    model_iseq_hash = utils.build_i_seq_hash(pdb_hierarchy=pdb_hierarchy)
    model_name_hash = utils.build_name_hash(pdb_hierarchy=pdb_hierarchy)
    ref_iseq_hash = utils.build_i_seq_hash(pdb_hierarchy=pdb_hierarchy_ref)
    sel_cache = pdb_hierarchy.atom_selection_cache()
    sel_cache_ref = pdb_hierarchy_ref.atom_selection_cache()
    match_map = {}
    #check for auto alignment compatability
    if params.auto_align == True:
      try:
        assert len(params.reference_group) == 0
      except Exception:
        raise Sorry("""
  Cannot use reference_group selections with automatic alignment.
  Please use alignment_group selections.  See documentation for details."
  """)
      if len(params.alignment_group) == 0:
        ref_list = ['ALL']
        selection_list = ['ALL']
        sel_atoms = (utils.phil_atom_selections_as_i_seqs_multiple(
                     cache=sel_cache,
                     string_list=selection_list))
        sel_atoms_ref = (utils.phil_atom_selections_as_i_seqs_multiple(
                         cache=sel_cache_ref,
                         string_list=ref_list))
        selections = (sel_atoms, sel_atoms_ref)
        residue_match_map = self._alignment(pdb_hierarchy=pdb_hierarchy,
                                            pdb_hierarchy_ref=pdb_hierarchy_ref,
                                            params=params,
                                            selections=selections,
                                            log=log)
        for i_seq in sel_atoms:
          key = model_name_hash[i_seq]
          atom = key[0:4]
          res_key = key[4:]
          try:
            match_key = atom+residue_match_map[res_key]
            match_map[i_seq] = ref_iseq_hash[match_key]
          except Exception:
            continue

      else:
        for ag in params.alignment_group:
          sel_atoms = (utils.phil_atom_selections_as_i_seqs_multiple(
                       cache=sel_cache,
                       string_list=[ag.selection]))
          sel_atoms_ref = (utils.phil_atom_selections_as_i_seqs_multiple(
                           cache=sel_cache_ref,
                           string_list=[ag.reference]))
          selections = (sel_atoms, sel_atoms_ref)
          residue_match_map = self._alignment(pdb_hierarchy=pdb_hierarchy,
                                                pdb_hierarchy_ref=pdb_hierarchy_ref,
                                                params=params,
                                                selections=selections,
                                                log=log)
          for i_seq in sel_atoms:
            key = model_name_hash[i_seq]
            atom = key[0:4]
            res_key = key[4:]
            try:
              match_key = atom+residue_match_map[res_key]
              match_map[i_seq] = ref_iseq_hash[match_key]
            except Exception:
              continue
    else:
      if len(params.reference_group) == 0:
        ref_list = ['ALL']
        selection_list = ['ALL']
        sel_atoms = utils.phil_atom_selections_as_i_seqs_multiple(
                        cache=sel_cache,
                        string_list=selection_list)
        for i_seq in sel_atoms:
          key = model_name_hash[i_seq]
          try:
            match_map[i_seq] = ref_iseq_hash[key]
          except Exception:
            #print >> self.log, "CANNOT match %s" % key
            continue
      #specified reference groups
      #test_match_map = {}
      for rg in params.reference_group:
        model_chain = None
        ref_chain = None
        model_res_min = None
        model_res_max = None
        ref_res_min = None
        ref_res_max = None
        #check for selection sanity
        sel_model = re.split(r"AND|OR|NOT",rg.selection.upper())
        sel_ref = re.split(r"AND|OR|NOT",rg.reference.upper())
        for sel in sel_model:
          if sel.strip().startswith("CHAIN"):
            if model_chain is None:
              model_chain = sel.strip().split(' ')[-1]
            else:
              raise Sorry("Cannot specify more than one chain per selection")
          if sel.strip().startswith("RESSEQ") or sel.strip().startswith("RESID"):
            res = sel.strip().split(' ')[-1].split(':')
            if len(res) > 1:
              if model_res_min is None and model_res_max is None:
                model_res_min = res[0]
                model_res_max = res[1]
              else:
                raise Sorry("Cannot specify more than one residue or residue range per selection")
            elif len(res) == 1:
              if model_res_min is None and model_res_max is None:
                model_res_min = res[0]
                model_res_max = res[0]
            else:
              raise Sorry("Do not understand residue selection")
        for sel in sel_ref:
          if sel.strip().startswith("CHAIN"):
            if ref_chain is None:
              ref_chain = sel.strip().split(' ')[-1]
            else:
              raise Sorry("Cannot specify more than one chain per selection")
          if sel.strip().startswith("RESSEQ") or sel.strip().startswith("RESID"):
            res = sel.strip().split(' ')[-1].split(':')
            if len(res) > 1:
              if ref_res_min is None and ref_res_max is None:
                ref_res_min = res[0]
                ref_res_max = res[1]
              else:
                raise Sorry("Cannot specify more than one residue or residue range per selection")
            elif len(res) == 1:
              if ref_res_min is None and model_res_max is None:
                ref_res_min = res[0]
                ref_res_max = res[0]
            else:
              raise Sorry("Do not understand residue selection")
        #check consistency
        assert (ref_chain is None and model_chain is None) or \
               (ref_chain is not None and model_chain is not None)
        assert (ref_res_min is None and ref_res_max is None \
                and model_res_min is None and model_res_max is None) or \
                (ref_res_min is not None and ref_res_max is not None \
                and model_res_min is not None and model_res_max is not None)
        #prep for SSM alignment
        sel_atoms = (utils.phil_atom_selections_as_i_seqs_multiple(
                      cache=sel_cache,
                      string_list=[rg.selection]))
        sel_atoms_ref = (utils.phil_atom_selections_as_i_seqs_multiple(
                      cache=sel_cache_ref,
                      string_list=[rg.reference]))
        chains = pdb_hierarchy.models()[0].chains()
        sel = utils.selection(rg.selection, sel_cache)
        sel_ref = utils.selection(rg.reference, sel_cache_ref)
        mod_h = utils.hierarchy_from_selection(
                  pdb_hierarchy=pdb_hierarchy,
                  selection = sel,
                  log=log).models()[0].chains()[0]
        ref_h = utils.hierarchy_from_selection(
                  pdb_hierarchy=pdb_hierarchy_ref,
                  selection = sel_ref,
                  log=log).models()[0].chains()[0]
        ssm = None
        try: #do SSM alignment
          ssm, ssm_align = utils._ssm_align(
                      reference_chain = ref_h,
                      moving_chain = mod_h)
        except RuntimeError, e:
          if str(e) != "can't make graph for first structure":
            raise e
          else:
            print >> log, "SSM alignment failed...trying simple matching..."
        if ssm != None:
          for pair in ssm_align.pairs:
            model_res = pair[0]
            ref_res = pair[1]
            if model_res is None or ref_res is None:
              continue
            temp_model_atoms = {}
            temp_ref_atoms = {}
            key = "%s %s%s%s" % (model_res.unique_resnames()[0],
                                 model_res.parent().id,
                                 model_res.resseq,
                                 model_res.icode)
            key_ref = "%s %s%s%s" % (ref_res.unique_resnames()[0],
                                     ref_res.parent().id,
                                     ref_res.resseq,
                                     ref_res.icode)
            for atom in model_res.atoms():
              atom_temp = atom.name+' '+key
              temp_model_atoms[atom.name] = model_iseq_hash[atom_temp]
            for atom in ref_res.atoms():
              atom_temp = atom.name+' '+key_ref
              temp_ref_atoms[atom.name] = ref_iseq_hash[atom_temp]
            for key in temp_model_atoms.keys():
              ref_atom = temp_ref_atoms.get(key)
              if ref_atom != None:
                match_map[temp_model_atoms[key]] = temp_ref_atoms[key]

        else: #ssm failed
          #calculate residue offset
          offset = 0
          if (ref_res_min is not None and ref_res_max is not None \
              and model_res_min is not None and model_res_max is not None):
            offset = int(model_res_min) - int(ref_res_min)
            assert offset == (int(model_res_max) - int(ref_res_max))
          for i_seq in sel_atoms:
            key = model_name_hash[i_seq]
            if ref_chain is not None:
              if len(ref_chain)==1:
                ref_chain = ' '+ref_chain
              key = re.sub(r"(.{5}\D{3})(.{2})(.{4})",r"\1"+ref_chain+r"\3",key)
            if offset != 0:
              resnum = key[10:14]
              new_num = "%4d" % (int(resnum) - offset)
              key = re.sub(r"(.{5}\D{3})(.{2})(.{4})",r"\1"+ref_chain+new_num,key)
            try:
              assert ref_iseq_hash[key] in sel_atoms_ref
              match_map[i_seq] = ref_iseq_hash[key]
            except Exception:
              continue
    return match_map

  def build_reference_dihedral_proxy_hash(self):
    self.reference_dihedral_proxy_hash = {}
    for dp in self.dihedral_proxies_ref:
      key = ""
      for i_seq in dp.i_seqs:
        key += self.i_seq_name_hash_ref[i_seq]
      self.reference_dihedral_proxy_hash[key] = dp
    for cp in self.chirality_proxies_ref:
      key = ""
      CAsite = None
      Csite = None
      Nsite = None
      CBsite = None
      CAkey = None
      Ckey = None
      Nkey = None
      CBkey = None
      cbeta = True
      for i_seq in cp.i_seqs:
        if self.i_seq_name_hash_ref[i_seq][0:4] not in \
          [' CA ', ' N  ', ' C  ', ' CB ']:
          cbeta = False
        if self.i_seq_name_hash_ref[i_seq][0:4] == ' CA ':
          CAkey = self.i_seq_name_hash_ref[i_seq]
          CAsite = i_seq
        elif self.i_seq_name_hash_ref[i_seq][0:4] == ' CB ':
          CBkey = self.i_seq_name_hash_ref[i_seq]
          CBsite = i_seq
        elif self.i_seq_name_hash_ref[i_seq][0:4] == ' C  ':
          Ckey = self.i_seq_name_hash_ref[i_seq]
          Csite = i_seq
        elif self.i_seq_name_hash_ref[i_seq][0:4] == ' N  ':
          Nkey = self.i_seq_name_hash_ref[i_seq]
          Nsite = i_seq
      if cbeta:
        i_seqs = [Csite, Nsite, CAsite, CBsite]
        key = Ckey+Nkey+CAkey+CBkey
        dp = cctbx.geometry_restraints.dihedral_proxy(
               i_seqs=cp.i_seqs,
               angle_ideal=0.0,
               weight=1.0)
        self.reference_dihedral_proxy_hash[key] = dp
        i_seqs = [Nsite, Csite, CAsite, CBsite]
        key = Nkey+Ckey+CAkey+CBkey
        dp = cctbx.geometry_restraints.dihedral_proxy(
               i_seqs=cp.i_seqs,
               angle_ideal=0.0,
               weight=1.0)
        self.reference_dihedral_proxy_hash[key] = dp

  def build_dihedral_hash(self,
                          geometry=None,
                          sites_cart=None,
                          pdb_hierarchy=None,
                          include_hydrogens=False,
                          include_main_chain=True,
                          include_side_chain=True):
    if not include_hydrogens:
      i_seq_element_hash = utils.build_element_hash(pdb_hierarchy=pdb_hierarchy)
    i_seq_name_hash = utils.build_name_hash(pdb_hierarchy=pdb_hierarchy)
    dihedral_hash = dict()

    for dp in geometry.dihedral_proxies:
      try:
        #check for H atoms if required
        if not include_hydrogens:
          for i_seq in dp.i_seqs:
            if i_seq_element_hash[i_seq] == " H":
              raise StopIteration()
        #ignore backbone dihedrals
        if not include_main_chain:
          sc_atoms = False
          for i_seq in dp.i_seqs:
            if i_seq_name_hash[i_seq][0:4] not in [' CA ', ' N  ', ' C  ', ' O  ']:
              sc_atoms = True
              break
          if not sc_atoms:
            raise StopIteration()
        if not include_side_chain:
          sc_atoms = False
          for i_seq in dp.i_seqs:
            if i_seq_name_hash[i_seq][0:4] not in [' CA ', ' N  ', ' C  ', ' O  ']:
              sc_atoms = True
              break
          if sc_atoms:
            raise StopIteration()
        key = ""
        for i_seq in dp.i_seqs:
          key = key+i_seq_name_hash[i_seq]
        di = cctbx.geometry_restraints.dihedral(sites_cart=sites_cart, proxy=dp)
        dihedral_hash[key] = di.angle_model
      except StopIteration:
        pass

    #add dihedral for CB
    cbetadev_hash = utils.build_cbetadev_hash(pdb_hierarchy=pdb_hierarchy)
    for cp in geometry.chirality_proxies:
      c_beta = True
      key = ""
      CAxyz = None
      Cxyz = None
      Nxyz = None
      CBxyz = None
      CAkey = None
      Ckey = None
      Nkey = None
      CBkey = None
      for i_seq in cp.i_seqs:
        if i_seq_name_hash[i_seq][0:4] not in [' CA ', ' N  ', ' C  ', ' CB ']:
          c_beta = False
        if i_seq_name_hash[i_seq][0:4] == ' CA ':
          CAxyz = sites_cart[i_seq]
          CAkey = i_seq_name_hash[i_seq]
        elif i_seq_name_hash[i_seq][0:4] == ' C  ':
          Cxyz = sites_cart[i_seq]
          Ckey = i_seq_name_hash[i_seq]
        elif i_seq_name_hash[i_seq][0:4] == ' N  ':
          Nxyz = sites_cart[i_seq]
          Nkey = i_seq_name_hash[i_seq]
        elif i_seq_name_hash[i_seq][0:4] == ' CB ':
          CBxyz = sites_cart[i_seq]
          CBkey = i_seq_name_hash[i_seq]
          try:
            if float(cbetadev_hash[i_seq_name_hash[i_seq][4:14]]) >= 0.25:
              c_beta = False
              print >> self.log, "skipping C-beta restraint for %s" % \
                i_seq_name_hash[i_seq][4:14]
          except Exception:
              c_beta = False
      if c_beta:
        assert CAxyz is not None
        assert Cxyz is not None
        assert Nxyz is not None
        assert CBxyz is not None
        sites = [Cxyz, Nxyz, CAxyz, CBxyz]
        key = Ckey + Nkey + CAkey + CBkey
        d = cctbx.geometry_restraints.dihedral(
          sites=sites,
          angle_ideal=0,
          weight=1)
        dihedral_hash[key] = d.angle_model
        sites = [Nxyz, Cxyz, CAxyz, CBxyz]
        key = Nkey + Ckey + CAkey + CBkey
        d = cctbx.geometry_restraints.dihedral(
          sites=sites,
          angle_ideal=0,
          weight=1)
        dihedral_hash[key] = d.angle_model
    return dihedral_hash

  def get_reference_dihedral_proxies(self):
    ss_selection = None
    residue_match_hash = {}
    self.reference_dihedral_proxies = \
      cctbx.geometry_restraints.shared_dihedral_proxy()
    sigma = self.params.sigma
    limit = self.params.limit
    match_map = self.process_reference_groups(
                               pdb_hierarchy=self.pdb_hierarchy,
                               pdb_hierarchy_ref=self.pdb_hierarchy_ref,
                               params=self.params,
                               log=self.log)
    self.match_map = match_map
    if self.params.secondary_structure_only:
      if (not libtbx.env.has_module(name="ksdssp")):
        raise RuntimeError(
          "ksdssp module is not configured, cannot generate secondary structure reference")
      ref_ss_m = secondary_structure.manager(
                   pdb_hierarchy=self.pdb_hierarchy_ref,
                   xray_structure=self.pdb_hierarchy_ref.extract_xray_structure(),
                   sec_str_from_pdb_file=None)
      ref_ss_m.find_automatically()
      pdb_str = self.pdb_hierarchy_ref.as_pdb_string()
      (records, stderr) = secondary_structure.run_ksdssp_direct(pdb_str)
      sec_str_from_pdb_file = iotbx.pdb.secondary_structure.process_records(
                                records=records,
                                allow_none=True)
      if sec_str_from_pdb_file != None:
        overall_helix_selection = sec_str_from_pdb_file.overall_helix_selection()
        overall_sheet_selection = sec_str_from_pdb_file.overall_sheet_selection()
        overall_selection = overall_helix_selection +' or ' + overall_sheet_selection
        sel_cache_ref = self.pdb_hierarchy_ref.atom_selection_cache()
        ss_selection = (utils.phil_atom_selections_as_i_seqs_multiple(
                        cache=sel_cache_ref,
                        string_list=[overall_selection]))
    for dp in self.geometry.dihedral_proxies:
      key = ""
      key_work = ""
      for i_seq in dp.i_seqs:
        key_work = key_work + self.i_seq_name_hash[i_seq]
        try:
          key = key+self.i_seq_name_hash_ref[match_map[i_seq]]
        except Exception:
          continue
      try:
        reference_angle = self.reference_dihedral_hash[key]
        if key[5:14] == key[20:29] and \
           key[5:14] == key[35:44] and \
           key_work[5:14] == key_work[20:29] and \
           key_work[5:14] == key_work[35:44]:
          residue_match_hash[key_work[5:14]] = key[5:14]
      except Exception:
        continue
      if self.params.secondary_structure_only and ss_selection != None:
          if match_map[dp.i_seqs[0]] in ss_selection and \
             match_map[dp.i_seqs[1]] in ss_selection and \
             match_map[dp.i_seqs[2]] in ss_selection and \
             match_map[dp.i_seqs[3]] in ss_selection:
            dp_add = cctbx.geometry_restraints.dihedral_proxy(
              i_seqs=dp.i_seqs,
              angle_ideal=reference_angle,
              weight=1/(1.0**2),
              limit=30.0,
              top_out=TOP_OUT_FLAG)
            self.reference_dihedral_proxies.append(dp_add)
          else:
            dp_add = cctbx.geometry_restraints.dihedral_proxy(
              i_seqs=dp.i_seqs,
              angle_ideal=reference_angle,
              weight=1/(5.0**2),
              limit=15.0,
              top_out=TOP_OUT_FLAG)
            self.reference_dihedral_proxies.append(dp_add)
      else:
        dp_add = cctbx.geometry_restraints.dihedral_proxy(
          i_seqs=dp.i_seqs,
          angle_ideal=reference_angle,
          weight=1/sigma**2,
          limit=limit,
          top_out=TOP_OUT_FLAG)
        self.reference_dihedral_proxies.append(dp_add)
    for cp in self.geometry.chirality_proxies:
      CAsite = None
      Csite = None
      Nsite = None
      CBsite = None
      CAkey = None
      Ckey = None
      Nkey = None
      CBkey = None
      for i_seq in cp.i_seqs:
        try:
          key_check = self.i_seq_name_hash_ref[match_map[i_seq]]
        except Exception:
          continue
        if self.i_seq_name_hash_ref[match_map[i_seq]][0:4] == ' CA ':
          CAsite = i_seq
          CAkey = key_check
        elif self.i_seq_name_hash_ref[match_map[i_seq]][0:4] == ' CB ':
          CBsite = i_seq
          CBkey = key_check
        elif self.i_seq_name_hash_ref[match_map[i_seq]][0:4] == ' C  ':
          Csite = i_seq
          Ckey = key_check
        elif self.i_seq_name_hash_ref[match_map[i_seq]][0:4] == ' N  ':
          Nsite = i_seq
          Nkey = key_check
      if CAsite is None or Csite is None or CBsite is None or Nsite is None:
        continue
      try:
        key = Ckey + Nkey + CAkey + CBkey
        reference_angle = self.reference_dihedral_hash[key]

        i_seqs = [Csite, Nsite, CAsite, CBsite]
        if self.params.secondary_structure_only and ss_selection != None:
            if match_map[i_seqs[0]] in ss_selection and \
               match_map[i_seqs[1]] in ss_selection and \
               match_map[i_seqs[2]] in ss_selection and \
               match_map[i_seqs[3]] in ss_selection:
              dp_add = cctbx.geometry_restraints.dihedral_proxy(
                i_seqs=i_seqs,
                angle_ideal=reference_angle,
                weight=1/(1.0**2),
                limit=30.0,
                top_out=TOP_OUT_FLAG)
              self.reference_dihedral_proxies.append(dp_add)
            else:
              dp_add = cctbx.geometry_restraints.dihedral_proxy(
                i_seqs=i_seqs,
                angle_ideal=reference_angle,
                weight=1/(5.0**2),
                limit=15.0,
                top_out=TOP_OUT_FLAG)
              self.reference_dihedral_proxies.append(dp_add)
        else:
          dp_add = cctbx.geometry_restraints.dihedral_proxy(
            i_seqs=i_seqs,
            angle_ideal=reference_angle,
            weight=1/sigma**2,
            limit=limit,
            top_out=TOP_OUT_FLAG)
          self.reference_dihedral_proxies.append(dp_add)
      except Exception:
        pass
      try:
        key = Nkey + Ckey + CAkey + CBkey
        reference_angle = self.reference_dihedral_hash[key]
      except Exception:
        continue
      i_seqs = [Nsite, Csite, CAsite, CBsite]
      if self.params.secondary_structure_only and ss_selection != None:
          if match_map[i_seqs[0]] in ss_selection and \
             match_map[i_seqs[1]] in ss_selection and \
             match_map[i_seqs[2]] in ss_selection and \
             match_map[i_seqs[3]] in ss_selection:
            dp_add = cctbx.geometry_restraints.dihedral_proxy(
              i_seqs=i_seqs,
              angle_ideal=reference_angle,
              weight=1/(1.0**2),
              limit=30.0,
              top_out=TOP_OUT_FLAG)
            self.reference_dihedral_proxies.append(dp_add)
          else:
            dp_add = cctbx.geometry_restraints.dihedral_proxy(
              i_seqs=i_seqs,
              angle_ideal=reference_angle,
              weight=1/(5.0**2),
              limit=15.0,
              top_out=TOP_OUT_FLAG)
            self.reference_dihedral_proxies.append(dp_add)
      else:
        dp_add = cctbx.geometry_restraints.dihedral_proxy(
          i_seqs=i_seqs,
          angle_ideal=reference_angle,
          weight=1/sigma**2,
          limit=limit,
          top_out=TOP_OUT_FLAG)
        self.reference_dihedral_proxies.append(dp_add)
    self.residue_match_hash = residue_match_hash

  def show_reference_summary(self, log=None):
    if(log is None): log = sys.stdout
    print >> log, "--------------------------------------------------------"
    print >> log, "Reference Model Matching Summary:"
    print >> log, "Model:              Reference:"
    keys = self.residue_match_hash.keys()
    def get_key_chain_num(res):
      return res[4:]
    keys.sort(key=get_key_chain_num)
    for key in keys:
      print >> log, "%s  <=====>  %s" % (key, self.residue_match_hash[key])
    print >> log, "Total # of matched residue pairs: %d" % len(keys)
    print >> log, "--------------------------------------------------------"

  def add_reference_dihedral_proxies(self, geometry):
    geometry.reference_dihedral_proxies= \
      self.reference_dihedral_proxies

  def set_rotamer_to_reference(self,
                               xray_structure,
                               log=None,
                               quiet=False):
    pdb_hierarchy=self.pdb_hierarchy
    pdb_hierarchy_ref=self.pdb_hierarchy_ref
    if(log is None): log = self.log
    make_sub_header(
      "Correcting rotamer outliers to match reference model",
      out=log)
    r = rotalyze()
    sa = SidechainAngles(False)
    mon_lib_srv = mmtbx.monomer_library.server.server()
    rot_list_model, coot_model = r.analyze_pdb(hierarchy=pdb_hierarchy)
    rot_list_reference, coot_reference = r.analyze_pdb(hierarchy=pdb_hierarchy_ref)
    model_hash = {}
    model_chis = {}
    reference_hash = {}
    reference_chis = {}
    model_outliers = 0
    for line in rot_list_model.splitlines():
      res, rotamericity, chi1, chi2, chi3, chi4, name = line.split(':')
      model_hash[res]=name
      if name == "OUTLIER":
        model_outliers += 1

    for line in rot_list_reference.splitlines():
      res, rotamericity, chi1, chi2, chi3, chi4, name = line.split(':')
      reference_hash[res]=name

    print >> log, "** evaluating rotamers for working model **"
    for model in pdb_hierarchy.models():
      for chain in model.chains():
        for residue_group in chain.residue_groups():
            all_dict = r.construct_complete_sidechain(residue_group)
            for atom_group in residue_group.atom_groups():
              try:
                atom_dict = all_dict.get(atom_group.altloc)
                chis = sa.measureChiAngles(atom_group, atom_dict)
                if chis is not None:
                  key = '%s%5s %s' % (
                      chain.id, residue_group.resid(),
                      atom_group.altloc+atom_group.resname)
                  model_chis[key] = chis
              except Exception:
                print >> log, \
                  '  %s%5s %s is missing some sidechain atoms, **skipping**' % (
                      chain.id, residue_group.resid(),
                      atom_group.altloc+atom_group.resname)
    if model_outliers == 0:
      print >> log, "No rotamer outliers detected in working model"
      return
    else:
      print >> log, "Number of rotamer outliers: %d" % model_outliers

    print >> log, "\n** evaluating rotamers for reference model **"
    for model in pdb_hierarchy_ref.models():
      for chain in model.chains():
        for residue_group in chain.residue_groups():
            all_dict = r.construct_complete_sidechain(residue_group)
            for atom_group in residue_group.atom_groups():
              try:
                atom_dict = all_dict.get(atom_group.altloc)
                chis = sa.measureChiAngles(atom_group, atom_dict)
                if chis is not None:
                  key = '%s%5s %s' % (
                      chain.id, residue_group.resid(),
                      atom_group.altloc+atom_group.resname)
                  reference_chis[key] = chis
              except Exception:
                print >> log, \
                  '  %s%5s %s is missing some sidechain atoms, **skipping**' % (
                      chain.id, residue_group.resid(),
                      atom_group.altloc+atom_group.resname)

    print >> log, "\n** fixing outliers **"
    sites_cart_start = xray_structure.sites_cart()
    for model in pdb_hierarchy.models():
      for chain in model.chains():
        for residue_group in chain.residue_groups():
          if len(residue_group.conformers()) > 1:
            print >> log, "%s%5s %s has multiple conformations, **skipping**" % (
              chain.id, residue_group.resid(),
              " "+residue_group.atom_groups()[0].resname)
            continue
          for conformer in residue_group.conformers():
            for residue in conformer.residues():
              if residue.resname == "PRO":
                continue
              key = '%s%5s %s' % (
                        chain.id, residue_group.resid(),
                        conformer.altloc+residue.resname)
              model_rot = model_hash.get(key)
              reference_rot = reference_hash.get(key)
              m_chis = model_chis.get(key)
              r_chis = reference_chis.get(key)
              if model_rot is not None and reference_rot is not None and \
                 m_chis is not None and r_chis is not None:
                if (model_hash[key] == 'OUTLIER' and \
                    reference_hash[key] != 'OUTLIER'): # or \
                    #atom_group.resname in ["LEU", "VAL", "THR"]:
                  axis_and_atoms_to_rotate= \
                    fit_rotamers.axes_and_atoms_aa_specific(
                        residue=residue,
                        mon_lib_srv=mon_lib_srv,
                        remove_clusters_with_all_h=True,
                        log=None)
                  assert len(m_chis) == len(r_chis)
                  assert len(m_chis) == len(axis_and_atoms_to_rotate)
                  counter = 0
                  residue_iselection = residue.atoms().extract_i_seq()
                  sites_cart_residue = \
                    xray_structure.sites_cart().select(residue_iselection)
                  for aa in axis_and_atoms_to_rotate:
                    axis = aa[0]
                    atoms = aa[1]
                    residue.atoms().set_xyz(new_xyz=sites_cart_residue)
                    new_xyz = flex.vec3_double()
                    angle_deg = r_chis[counter] - m_chis[counter]
                    if angle_deg < 0:
                      angle_deg += 360.0
                    for atom in atoms:
                      new_xyz = rotate_point_around_axis(
                                  axis_point_1=sites_cart_residue[axis[0]],
                                  axis_point_2=sites_cart_residue[axis[1]],
                                  point=sites_cart_residue[atom],
                                  angle=angle_deg, deg=True)
                      sites_cart_residue[atom] = new_xyz
                    sites_cart_start = sites_cart_start.set_selected(
                          residue_iselection, sites_cart_residue)
                    counter += 1
                  xray_structure.set_sites_cart(sites_cart_start)

                elif self.params.strict_rotamer_matching and \
                  (model_rot != 'OUTLIER' and reference_rot != 'OUTLIER'):
                  if model_rot != reference_rot:
                    axis_and_atoms_to_rotate= \
                      fit_rotamers.axes_and_atoms_aa_specific(
                        residue=residue,
                        mon_lib_srv=mon_lib_srv,
                        remove_clusters_with_all_h=True,
                        log=None)
                    counter = 0
                    residue_iselection = residue.atoms().extract_i_seq()
                    sites_cart_residue = \
                      xray_structure.sites_cart().select(residue_iselection)
                    for aa in axis_and_atoms_to_rotate:
                      axis = aa[0]
                      atoms = aa[1]
                      residue.atoms().set_xyz(new_xyz=sites_cart_residue)
                      new_xyz = flex.vec3_double()
                      angle_deg = r_chis[counter] - m_chis[counter]
                      if angle_deg < 0:
                        angle_deg += 360.0
                      for atom in atoms:
                        new_xyz = rotate_point_around_axis(
                                    axis_point_1=sites_cart_residue[axis[0]],
                                    axis_point_2=sites_cart_residue[axis[1]],
                                    point=sites_cart_residue[atom],
                                    angle=angle_deg, deg=True)
                        sites_cart_residue[atom] = new_xyz
                      sites_cart_start = sites_cart_start.set_selected(
                        residue_iselection, sites_cart_residue)
                      counter += 1
                    xray_structure.set_sites_cart(sites_cart_start)

  def remove_restraints_with_ncs_matches(self,
                                         ncs_dihedral_proxies,
                                         ncs_match_hash):
    proxy_list = []
    remaining_proxies = cctbx.geometry_restraints.shared_dihedral_proxy()
    remaining_match_hash = {}
    for dp in ncs_dihedral_proxies:
      proxy_list.append(dp.i_seqs)
    print len(self.reference_dihedral_proxies)
    for dp in self.reference_dihedral_proxies:
      if dp.i_seqs not in proxy_list:
        remaining_proxies.append(dp)
    for key in self.residue_match_hash:
      found_match = False
      for key2 in ncs_match_hash:
        if key == key2:
          found_match = True
        else:
          for match in ncs_match_hash[key2]:
            if key == match:
              found_match = True
      if not found_match:
        remaining_match_hash[key] = self.residue_match_hash[key]
    print len(remaining_proxies)
    self.reference_dihedral_proxies = remaining_proxies
    self.residue_match_hash = remaining_match_hash
    print >> self.log, "\n**Removed reference restraints that overlap "+ \
                       "with torsion NCS restraints**\n"
    print >> self.log, "Updated Reference Model Restraints:"
    self.show_reference_summary()
