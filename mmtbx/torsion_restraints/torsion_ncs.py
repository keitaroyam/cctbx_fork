from __future__ import division
import cctbx.geometry_restraints
from mmtbx.validation.rotalyze import rotalyze
from mmtbx.validation.ramalyze import ramalyze
from mmtbx.validation import analyze_peptides
from mmtbx.rotamer.sidechain_angles import SidechainAngles
from mmtbx.refinement import fit_rotamers
from cctbx.array_family import flex
import iotbx.phil
from libtbx.str_utils import make_sub_header
import sys, math
from mmtbx.ncs import restraints
from libtbx.utils import Sorry
from mmtbx.torsion_restraints import utils, rotamer_search
from mmtbx.geometry_restraints import c_beta
from mmtbx import ncs
import mmtbx.utils
from libtbx import Auto

TOP_OUT_FLAG = True

torsion_ncs_params = iotbx.phil.parse("""
 sigma = 2.5
   .type = float
   .short_caption = Restraint sigma (degrees)
 limit = 15.0
   .type = float
   .short_caption = Restraint limit (degrees)
 similarity = .80
   .type = float
   .short_caption = Sequence similarity cutoff
 fix_outliers = Auto
   .type = bool
   .short_caption = Fix rotamer outliers first
 check_rotamer_consistency = Auto
   .type = bool
   .short_caption = Check for consistency between NCS-related sidechains
   .help = Check for rotamer differences between NCS matched \
     sidechains and search for best fit amongst candidate rotamers
 target_damping = False
   .type = bool
   .expert_level = 1
 damping_limit = 10.0
   .type = float
   .expert_level = 1
 verbose = True
   .type = bool
 filter_phi_psi_outliers = True
   .type = bool
   .expert_level = 4
 remove_conflicting_torsion_restraints = False
   .type = bool
   .expert_level = 4
 restrain_to_master_chain = False
   .type = bool
   .expert_level = 4
 silence_warnings = False
   .type = bool
   .expert_level = 4
 restraint_group
  .multiple=True
  .optional=True
  .caption = These atom selections define groups of residues whose dihedral \
    angles will be restrained to be similar.  This is normally done \
    automatically, and the restraints are designed to release dihedral angles \
    which are genuinely different.  You do not have to enter groups now \
    unless you wish to view and/or edit them prior to running phenix.refine.
  .short_caption=Torsion NCS restraint group
  .style = noauto box caption_img:icons/custom/ncs_tb.png
 {
  selection=None
    .type=atom_selection
    .short_caption=Restrained selection
    .multiple=True
    .input_size = 540
    .style = use_list
  b_factor_weight=10
    .type=float
    .short_caption = B factor weight
  coordinate_sigma=0.5
      .type = float
 }
""")

class torsion_ncs(object):
  def __init__(self,
               pdb_hierarchy=None,
               fmodel=None,
               params=None,
               b_factor_weight=None,
               coordinate_sigma=None,
               selection=None,
               ncs_groups=None,
               alignments=None,
               ncs_dihedral_proxies=None,
               log=None):
    if(log is None): log = sys.stdout
    if params is None:
      params = torsion_ncs_params.extract()
    #parameter initialization
    if params.sigma is None or params.sigma < 0:
      raise Sorry("torsion NCS sigma parameter must be >= 0.0")
    self.sigma = params.sigma
    if params.limit is None or params.limit < 0:
      raise Sorry("torsion NCS limit parameter must be >= 0.0")
    self.limit = params.limit
    self.selection = selection
    #slack is not a user parameter for now
    self.slack = 0.0
    self.filter_phi_psi_outliers = params.filter_phi_psi_outliers
    self.remove_conflicting_torsion_restraints = \
      params.remove_conflicting_torsion_restraints
    self.restrain_to_master_chain = params.restrain_to_master_chain
    self.b_factor_weight = b_factor_weight
    self.coordinate_sigma = coordinate_sigma
    self.fmodel = fmodel
    self.ncs_groups = ncs_groups
    self.log = log
    self.params = params
    self.dp_ncs = None
    self.ncs_dihedral_proxies = ncs_dihedral_proxies
    self.ncs_groups = ncs_groups
    self.alignments = alignments

    #sanity check
    if pdb_hierarchy is not None:
      pdb_hierarchy.reset_i_seq_if_necessary()
    if self.ncs_groups is None or self.alignments is None:
      self.find_ncs_groups(pdb_hierarchy=pdb_hierarchy)
    if pdb_hierarchy is not None:
      self.find_ncs_matches_from_hierarchy(pdb_hierarchy=pdb_hierarchy)

  def find_ncs_groups(self, pdb_hierarchy):
    print >> self.log, "Determining NCS matches..."
    self.ncs_groups = []
    self.found_ncs = None
    self.use_segid = False
    chains = pdb_hierarchy.models()[0].chains()
    n_ncs_groups = 0
    for i_seq, group in enumerate(self.params.restraint_group):
      n_selections = 0
      for selection in group.selection:
        if(selection is not None):
          n_selections += 1
      if n_selections == 1:
        raise Sorry(
          "Torsion NCS restraint_groups require at least 2 selections")
      elif n_selections > 1:
        n_ncs_groups += 1
    if n_ncs_groups > 0:
      sequences = {}
      padded_sequences = {}
      structures = {}
      alignments = {}
      restraint_group_check = [True]*len(self.params.restraint_group)
      for i, restraint_group in enumerate(self.params.restraint_group):
        for selection_i in restraint_group.selection:
          sel_atoms_i = (utils.phil_atom_selections_as_i_seqs_multiple(
                           cache=pdb_hierarchy.atom_selection_cache(),
                           string_list=[selection_i]))
          sel_seq, sel_seq_padded, sel_structures = \
            utils.extract_sequence_and_sites(
            pdb_hierarchy=pdb_hierarchy,
            selection=sel_atoms_i)
          if len(sel_seq) == 0:
            print >> log
            print >> log, "*** WARNING ***"
            print >> log, 'selection = %s' % selection_i
            print >> log, 'specifies no protein or nucleic acid torsions'
            print >> log, 'REMOVED RESTRAINT GROUP!!!'
            print >> log, "***************"
            print >> log
            restraint_group_check[i] = False
            break
          sequences[selection_i] = sel_seq
          padded_sequences[selection_i] = sel_seq_padded
          structures[selection_i] = sel_structures
      cleaned_restraint_groups = []
      for i, check in enumerate(restraint_group_check):
        if check:
          cleaned_restraint_groups.append(self.params.restraint_group[i])
      self.params.restraint_group = cleaned_restraint_groups
      for restraint_group in self.params.restraint_group:
        ncs_set = []
        for selection_i in restraint_group.selection:
          ncs_set.append(selection_i)
          for selection_j in restraint_group.selection:
            if selection_i == selection_j:
              continue
            seq_pair = (sequences[selection_i],
                        sequences[selection_j])
            seq_pair_padded = (padded_sequences[selection_i],
                               padded_sequences[selection_j])
            struct_pair = (structures[selection_i],
                           structures[selection_j])
            residue_match_map = \
              utils._alignment(
                params=self.params,
                sequences=seq_pair,
                padded_sequences=seq_pair_padded,
                structures=struct_pair,
                log=self.log)
            key = (selection_i, selection_j)
            alignments[key] = residue_match_map
        self.ncs_groups.append(ncs_set)
      self.alignments = alignments
    else:
      atom_labels = list(pdb_hierarchy.atoms_with_labels())
      segids = flex.std_string([ a.segid for a in atom_labels ])
      self.use_segid = not segids.all_eq('    ')
      ncs_groups_manager = get_ncs_groups(
          pdb_hierarchy=pdb_hierarchy,
          use_segid=self.use_segid,
          params=self.params,
          log=self.log)
      self.ncs_groups = ncs_groups_manager.ncs_groups
      self.alignments = ncs_groups_manager.alignments
      new_ncs_groups = None
      #sort NCS groups alphabetically
      def selection_sort(match_list):
        match_list.sort()
        return match_list[0]
      self.ncs_groups.sort(key=selection_sort)
      if len(self.ncs_groups) > 0:
        new_ncs_groups = "refinement {\n ncs {\n  torsion {\n"
        for ncs_set in self.ncs_groups:
          new_ncs_groups += "   restraint_group {\n"
          for chain in ncs_set:
            new_ncs_groups += "    selection = %s\n" % chain
          if self.b_factor_weight is not None:
            new_ncs_groups += \
              "    b_factor_weight = %.1f\n" % self.b_factor_weight
          else:
            new_ncs_groups += \
              "    b_factor_weight = None\n"
          if self.coordinate_sigma is not None:
            new_ncs_groups += \
              "    coordinate_sigma = %.1f\n" % self.coordinate_sigma
          else:
            new_ncs_groups += \
              "    coordinate_sigma = None\n"
          new_ncs_groups += "   }\n"
        new_ncs_groups += "  }\n }\n}"
      self.found_ncs = new_ncs_groups

  def find_ncs_matches_from_hierarchy(self,
                                      pdb_hierarchy):
    self.dp_ncs = []
    self.cb_dp_ncs = []
    self.phi_list = []
    self.psi_list = []
    self.omega_list = []
    self.dihedral_proxies_backup = None
    self.name_hash = utils.build_name_hash(pdb_hierarchy)
    self.segid_hash = utils.build_segid_hash(pdb_hierarchy)
    self.sym_atom_hash = utils.build_sym_atom_hash(pdb_hierarchy)
    self.njump = 1
    self.min_length = 10
    self.sa = SidechainAngles(False)
    self.sidechain_angle_hash = self.build_sidechain_angle_hash()
    self.rotamer_search_manager = None
    self.r = rotalyze()
    self.unit_cell = None
    sites_cart = pdb_hierarchy.atoms().extract_xyz()
    if self.selection is None:
      self.selection = flex.bool(len(sites_cart), True)
    complete_dihedral_proxies = utils.get_complete_dihedral_proxies(
                                  pdb_hierarchy=pdb_hierarchy)
    if len(self.ncs_groups) > 0:
      element_hash = utils.build_element_hash(pdb_hierarchy)
      i_seq_hash = utils.build_i_seq_hash(pdb_hierarchy)
      dp_hash = {}
      for dp in complete_dihedral_proxies:
        h_atom = False
        for i_seq in dp.i_seqs:
          if element_hash[i_seq] == " H":
            h_atom = True
        if not h_atom:
          complete = True
          for i_seq in dp.i_seqs:
            if not self.selection[i_seq]:
              complete = False
          if complete:
            dp_hash[dp.i_seqs] = dp

      super_hash = {}
      res_match_master = {}
      res_to_selection_hash = {}
      for i, group in enumerate(self.ncs_groups):
        for chain_i in group:
          selection = utils.selection(
                       string=chain_i,
                       cache=pdb_hierarchy.atom_selection_cache())
          c_atoms = pdb_hierarchy.select(selection).atoms()
          for atom in c_atoms:
            for chain_j in group:
              if chain_i == chain_j:
                continue
              res_key = self.name_hash[atom.i_seq][4:]
              #print res_key
              atom_key = self.name_hash[atom.i_seq][0:4]
              j_match = None
              key = (chain_i, chain_j)
              cur_align = self.alignments.get(key)
              if cur_align is not None:
                j_match = cur_align.get(res_key)
              if j_match is not None:
                j_i_seq = i_seq_hash.get(atom_key+j_match)
                if j_i_seq is None:
                  continue
                if super_hash.get(atom.i_seq) is None:
                  super_hash[atom.i_seq] = dict()
                if super_hash.get(j_i_seq) is None:
                  super_hash[j_i_seq] = dict()
                super_hash[atom.i_seq][chain_j] = j_i_seq
                super_hash[j_i_seq][chain_i] = atom.i_seq
                if res_match_master.get(res_key) is None:
                  res_match_master[res_key] = []
                if res_match_master.get(j_match) is None:
                  res_match_master[j_match] = []
                if j_match not in res_match_master[res_key]:
                  res_match_master[res_key].append(j_match)
                if res_key not in res_match_master[j_match]:
                  res_match_master[j_match].append(res_key)
                res_to_selection_hash[res_key] = chain_i
                res_to_selection_hash[j_match] = chain_j
      self.res_match_master = res_match_master
      resname = None
      atoms_key = None
      for dp in complete_dihedral_proxies:
        temp = dict()
        #filter out unwanted torsions
        atoms = []
        for i_seq in dp.i_seqs:
          atom = self.name_hash[i_seq][:4]
          atoms.append(atom)
          atoms_key = ",".join(atoms)
          resname = self.get_torsion_resname(dp)
        if resname is not None:
          if ( (resname.lower() == 'arg') and
               (atoms_key == ' CD , NE , CZ , NH2') ):
            continue
          elif ( (resname.lower() == 'tyr') and
               (atoms_key == ' CD1, CE1, CZ , OH ' or
                atoms_key == ' CE1, CZ , OH , HH ') ):
            continue
          elif ( (resname.lower() == 'ser') and
               (atoms_key == ' CA , CB , OG , HG ') ):
            continue
          elif ( (resname.lower() == 'thr') and
               (atoms_key == ' CA , CB , OG1, HG1') ):
            continue
          elif ( (resname.lower() == 'cys') and
               (atoms_key == ' CA , CB , SG , HG ') ):
            continue
          elif ( (resname.lower() == 'met') and
               (atoms_key == ' CG , SD , CE ,1HE ' or
                atoms_key == ' CG , SD , CE , HE1') ):
            continue
        ################
        for i_seq in dp.i_seqs:
          cur_matches = super_hash.get(i_seq)
          if cur_matches is None:
            continue
          for key in cur_matches.keys():
            try:
              temp[key].append(cur_matches[key])
            except Exception:
              temp[key] = []
              temp[key].append(cur_matches[key])
        dp_match = \
          cctbx.geometry_restraints.shared_dihedral_proxy()
        dp_match.append(dp)
        for key in temp.keys():
          cur_dp_hash = dp_hash.get(tuple(temp[key]))
          if cur_dp_hash is not None:
            dp_match.append(cur_dp_hash)
            dp_hash[tuple(temp[key])] = None
        dp_hash[dp.i_seqs] = None
        if len(dp_match) > 1:
          self.dp_ncs.append(dp_match)
      #initialize tracking hashes
      for dp_set in self.dp_ncs:
        for dp in dp_set:
          angle_atoms = self.get_torsion_atoms(dp)
          angle_resname = self.get_torsion_resname(dp)
          angle_id = utils.get_torsion_id(dp=dp, name_hash=self.name_hash)
          #phi
          if angle_atoms == ' C  '+' N  '+' CA '+' C  ':
            self.phi_list.append(dp.i_seqs)
          #psi
          elif angle_atoms == ' N  '+' CA '+' C  '+' N  ':
            self.psi_list.append(dp.i_seqs)
          #omega
          elif angle_atoms == ' CA '+' C  '+' N  '+' CA ':
            self.omega_list.append(dp.i_seqs)

      match_counter = {}
      inclusive_range = {}
      for group in self.ncs_groups:
        cur_len = len(group)
        for chain in group:
          match_counter[chain] = cur_len
          inclusive_range[chain] = []

      matched = []
      ncs_match_hash = {}
      for dp_set in self.dp_ncs:
        key_set = []
        for dp in dp_set:
          if len(dp_set) < 2:
            continue
          cur_key = ""
          for i_seq in dp.i_seqs:
            cur_key += self.name_hash[i_seq]
          if cur_key[4:19] == cur_key[23:38] and \
             cur_key[4:19] == cur_key[42:57]:
            key_set.append(cur_key[4:19])
        if len(dp_set) == len(key_set):
          key_set.sort()
          master_key = None
          skip = False
          for i, key in enumerate(key_set):
            if i == 0:
              master_key = key
              if master_key in matched:
                skip = True
              elif ncs_match_hash.get(key) is None:
                ncs_match_hash[key] = []
              elif len(key_set) <= len(ncs_match_hash[key]):
                skip = True
              else:
                ncs_match_hash[key] = []
            elif not skip:
              ncs_match_hash[master_key].append(key)
              matched.append(key)
      self.ncs_match_hash = ncs_match_hash
      self.reduce_redundancies()

      for res in self.ncs_match_hash.keys():
        resnum = res[6:10]
        hash_key = res_to_selection_hash[res]
        cur_len = match_counter[hash_key]
        if len(self.ncs_match_hash[res]) == (cur_len - 1):
          inclusive_range[hash_key].append(int(resnum))
          for res2 in self.ncs_match_hash[res]:
            resnum2 = res2[6:10]
            hash_key = res_to_selection_hash[res2]
            inclusive_range[hash_key].append(int(resnum2))

      #determine ranges
      self.master_ranges = {}
      for key in inclusive_range.keys():
        current = None
        previous = None
        start = None
        stop = None
        self.master_ranges[key] = []
        inclusive_range[key].sort()
        for num in inclusive_range[key]:
          if previous == None:
            start = num
            previous = num
          elif num > (previous + 1):
            finish = previous
            self.master_ranges[key].append( (start, finish) )
            start = num
            finish = None
            previous = num
          else:
            previous = num
        if previous != None:
          finish = previous
          self.master_ranges[key].append( (start, finish) )

      if self.params.verbose and self.ncs_dihedral_proxies is None:
        self.show_ncs_summary(log=self.log)
      if self.ncs_dihedral_proxies is None: #first time run
        print >> self.log, "Initializing torsion NCS restraints..."
      else:
        print >> self.log, "Verifying torsion NCS restraints..."
      self.rama = ramalyze()
      self.generate_dihedral_ncs_restraints(
        sites_cart=sites_cart,
        pdb_hierarchy=pdb_hierarchy,
        log=self.log)
    elif(not self.params.silence_warnings):
      print >> self.log, \
        "** WARNING: No torsion NCS found!!" + \
        "  Please check parameters. **"

  def add_c_beta_restraints(self,
                            geometry,
                            pdb_hierarchy):
    if geometry.generic_restraints_manager.c_beta_dihedral_proxies is None:
      print >> self.log, "Adding C-beta torsion restraints..."
      c_beta_torsion_proxies = \
        c_beta.get_c_beta_torsion_proxies(pdb_hierarchy=pdb_hierarchy)
      geometry.generic_restraints_manager.c_beta_dihedral_proxies = \
        c_beta_torsion_proxies
      geometry.generic_restraints_manager.flags.c_beta = True
      print >> self.log, "num c-beta restraints: ", \
        len(geometry.generic_restraints_manager.c_beta_dihedral_proxies)

  def show_ncs_summary(self, log=None):
    if(log is None): log = sys.stdout
    def get_key_chain_num(res):
      return res[4:]
    sorted_keys = sorted(self.ncs_match_hash, key=get_key_chain_num)
    print >> log, "--------------------------------------------------------"
    print >> log, "Torsion NCS Matching Summary:"
    for key in sorted_keys:
      if key.endswith("    "):
        print_line = key[:-4]
      else:
        print_line = key
      for match in self.ncs_match_hash[key]:
        if match.endswith("    "):
          print_line += " <=> %s" % (match[:-4])
        else:
          print_line += " <=> %s" % (match)
      print >> log, print_line
    print >> log, "--------------------------------------------------------"

  def reduce_redundancies(self):
    #clear out redundancies
    for key in self.ncs_match_hash.keys():
      for key2 in self.ncs_match_hash.keys():
        if key == key2:
          continue
        if key in self.ncs_match_hash[key2]:
          del self.ncs_match_hash[key]

  def get_torsion_atoms(self, dp):
    atoms = ''
    for i_seq in dp.i_seqs:
      atom_name = self.name_hash[i_seq][0:4]
      atoms += atom_name
    return atoms

  def get_torsion_resname(self, dp):
    resname = None
    for i_seq in dp.i_seqs:
      cur_resname = self.name_hash[i_seq][5:8]
      if resname == None:
        resname = cur_resname
      elif cur_resname != resname:
        return None
    return resname

  def get_chi_id(self, dp):
    atoms = []
    for i_seq in dp.i_seqs:
      atom = self.name_hash[i_seq][:4]
      atoms.append(atom)
    atoms_key = ",".join(atoms)
    resname = self.get_torsion_resname(dp)
    resAtomsToChi = self.sa.resAtomsToChi.get(resname.lower())
    if resAtomsToChi is None:
      chi_id = None
    else:
      chi_id = resAtomsToChi.get(atoms_key)
    return chi_id

  def build_chi_tracker(self, pdb_hierarchy):
    self.current_chi_restraints = {}
    model_hash, model_score, all_rotamers, model_chis = \
      self.get_rotamer_data(pdb_hierarchy=pdb_hierarchy)
    current_rotamers = self.r.current_rotamers
    for key in self.ncs_match_hash.keys():
      rotamer = current_rotamers.get(key)
      if rotamer is not None:
        split_rotamer = self.r.split_rotamer_names(rotamer=rotamer)
        self.current_chi_restraints[key] = split_rotamer
      key_list = self.ncs_match_hash.get(key)
      for key2 in key_list:
        rotamer = current_rotamers.get(key2)
        if rotamer is not None:
          split_rotamer = self.r.split_rotamer_names(rotamer=rotamer)
          self.current_chi_restraints[key2] = split_rotamer

  def generate_dihedral_ncs_restraints(
        self,
        sites_cart,
        pdb_hierarchy,
        log):
    self.build_chi_tracker(pdb_hierarchy)
    self.ncs_dihedral_proxies = \
      cctbx.geometry_restraints.shared_dihedral_proxy()
    target_map_data = None
    #if self.fmodel is not None and self.use_cc_for_target_angles:
    #  target_map_data, residual_map_data = self.prepare_map(
    #                                         fmodel=self.fmodel)
    model_hash, model_score, all_rotamers, model_chis = \
      self.get_rotamer_data(pdb_hierarchy=pdb_hierarchy)
    rama_outliers = None
    rama_outlier_list = []
    omega_outlier_list = []
    if self.filter_phi_psi_outliers:
      rama_outliers = \
        self.get_ramachandran_outliers(pdb_hierarchy)
      for outlier in rama_outliers.splitlines():
        temp = outlier.split(':')
        rama_outlier_list.append(temp[0])
      omega_outlier_list = \
        self.get_omega_outliers(pdb_hierarchy)
    torsion_counter = 0
    for dp_set in self.dp_ncs:
      if len(dp_set) < 2:
        continue
      angles = []
      #cc_s = []
      is_rama_outlier = []
      is_omega_outlier = []
      rotamer_state = []
      chi_ids = []
      wrap_hash = {}
      for i, dp in enumerate(dp_set):
        di = cctbx.geometry_restraints.dihedral(
               sites_cart=sites_cart, proxy=dp)
        angle = di.angle_model
        wrap_chis = self.is_symmetric_torsion(dp)
        if wrap_chis:
          if angle > 90.0 or angle < -90.0:
            sym_i_seq = dp.i_seqs[3] #4th atom
            swap_i_seq = self.sym_atom_hash.get(sym_i_seq)
            if swap_i_seq is not None:
              swap_i_seqs = (dp.i_seqs[0],
                             dp.i_seqs[1],
                             dp.i_seqs[2],
                             swap_i_seq)
              dp_temp = cctbx.geometry_restraints.dihedral_proxy(
                i_seqs=swap_i_seqs,
                angle_ideal=0.0,
                weight=1/self.sigma**2,
                limit=self.limit,
                top_out=TOP_OUT_FLAG,
                slack=self.slack)
              wrap_hash[i] = dp_temp
              di = cctbx.geometry_restraints.dihedral(
                     sites_cart=sites_cart, proxy=dp_temp)
              angle = di.angle_model
            else:
              angle = None
        angles.append(angle)
        rama_out = False
        if (dp.i_seqs in self.phi_list) or (dp.i_seqs in self.psi_list):
          angle_id = utils.get_torsion_id(
                       dp=dp,
                       name_hash=self.name_hash,
                       phi_psi=True)
          key = angle_id[4:6].strip()+angle_id[6:10]+' '+angle_id[0:4]
          if key in rama_outlier_list:
            rama_out = True
        is_rama_outlier.append(rama_out)

        omega_out = False
        if (dp.i_seqs in self.omega_list):
          angle_id = utils.get_torsion_id(
                       dp=dp,
                       name_hash=self.name_hash,
                       omega=True)
          key1 = \
            angle_id[0][4:6].strip()+angle_id[0][6:10]+' '+angle_id[0][0:4]
          key2 = \
            angle_id[1][4:6].strip()+angle_id[1][6:10]+' '+angle_id[1][0:4]
          if (key1, key2) in omega_outlier_list:
            omega_out = True
        is_omega_outlier.append(omega_out)
        #if target_map_data is not None:
        #  tor_iselection = flex.size_t()
        #  for i_seq in dp.i_seqs:
        #    tor_iselection.append(i_seq)
        #  tor_sites_cart = \
        #    sites_cart.select(tor_iselection)
        #  di_cc = self.get_sites_cc(sites_cart=tor_sites_cart,
        #                            target_map_data=target_map_data)
        #  cc_s.append(di_cc)

        angle_id = utils.get_torsion_id(
                     dp=dp,
                     name_hash=self.name_hash,
                     chi_only=True)
        if angle_id is not None:
          split_rotamer_list = self.current_chi_restraints.get(angle_id)
          which_chi = self.get_chi_id(dp)
          rotamer_state.append(split_rotamer_list)
          if which_chi is not None:
            chi_ids.append(which_chi)
      #if angle_id is not None:
      #  print >> self.log, angle_id
      #  print rotamer_state
      #else:
      #  print >> self.log, is_rama_outlier, is_omega_outlier
      target_angles = self.get_target_angles(
                        angles=angles,
                        #cc_s=cc_s,
                        is_rama_outlier=is_rama_outlier,
                        is_omega_outlier=is_omega_outlier,
                        rotamer_state=rotamer_state,
                        chi_ids=chi_ids)
      #if angle_id is not None: # and which_chi is None:
      #print angles
      #print target_angles
      for i, dp in enumerate(dp_set):
        target_angle = target_angles[i]
        angle_atoms = self.get_torsion_atoms(dp)
        angle_resname = self.get_torsion_resname(dp)
        angle_id = utils.get_torsion_id(dp=dp, name_hash=self.name_hash)
        cur_dict = self.sidechain_angle_hash.get(angle_resname)
        angle_name = None
        if cur_dict != None:
          angle_name = \
            cur_dict.get(angle_atoms)
        if target_angle is not None:
          angle_atoms = self.get_torsion_atoms(dp)
          angle_resname = self.get_torsion_resname(dp)
          angle_id = utils.get_torsion_id(dp=dp, name_hash=self.name_hash)
          cur_dict = self.sidechain_angle_hash.get(angle_resname)
          angle_name = None
          dp_sym = wrap_hash.get(i)
          if dp_sym is not None:
            dp_add = cctbx.geometry_restraints.dihedral_proxy(
              i_seqs=dp_sym.i_seqs,
              angle_ideal=target_angle,
              weight=1/self.sigma**2,
              limit=self.limit,
              top_out=TOP_OUT_FLAG,
              slack=self.slack)
          else:
            dp_add = cctbx.geometry_restraints.dihedral_proxy(
              i_seqs=dp.i_seqs,
              angle_ideal=target_angle,
              weight=1/self.sigma**2,
              limit=self.limit,
              top_out=TOP_OUT_FLAG,
              slack=self.slack)
          self.ncs_dihedral_proxies.append(dp_add)
          torsion_counter += 1

    if len(self.ncs_dihedral_proxies) == 0:
      if (not self.params.silence_warnings) :
        print >> log, \
          "** WARNING: No torsion NCS found!!" + \
          "  Please check parameters. **"
    else:
      print >> log, \
        "Number of torsion NCS restraints: %d\n" \
          % len(self.ncs_dihedral_proxies)

  def sync_dihedral_restraints(self,
                               geometry):
    pass
    #if self.dihedral_proxies_backup is None:
    #  self.dihedral_proxies_backup = geometry.dihedral_proxies.deep_copy()
    #updated_dihedral_proxies = \
    #  cctbx.geometry_restraints.shared_dihedral_proxy()
    #dp_i_seq_list = []
    #geo_dp_i_seq_list = []
    #print >> self.log, "dihedral length before = ", len(geometry.dihedral_proxies)
    #for dp in self.ncs_dihedral_proxies:
    #  dp_i_seq_list.append(dp.i_seqs)
    #for dp in geometry.dihedral_proxies:
    #  if dp.i_seqs not in dp_i_seq_list:
    #    updated_dihedral_proxies.append(dp)
    #for dp in updated_dihedral_proxies:
    #  geo_dp_i_seq_list.append(dp.i_seqs)
    #for dp in self.dihedral_proxies_backup:
    #  if ( (dp.i_seqs not in dp_i_seq_list) and
    #       (dp.i_seqs not in geo_dp_i_seq_list) ):
    #    updated_dihedral_proxies.append(dp)
    #geometry.dihedral_proxies = updated_dihedral_proxies
    #print >> self.log, "dihedral length after = ", len(geometry.dihedral_proxies)

  def update_dihedral_ncs_restraints(self,
                                     geometry,
                                     sites_cart,
                                     pdb_hierarchy,
                                     log=None):
    if log is None:
      log = sys.stdout
    make_sub_header(
      "Updating torsion NCS restraints",
      out=log)
    if self.dp_ncs is None:
      self.find_ncs_matches_from_hierarchy(pdb_hierarchy=pdb_hierarchy)
    else:
      self.generate_dihedral_ncs_restraints(sites_cart=sites_cart,
                                            pdb_hierarchy=pdb_hierarchy,
                                            log=log)
    self.add_ncs_dihedral_proxies(geometry=geometry)
    if self.remove_conflicting_torsion_restraints:
      self.sync_dihedral_restraints(geometry=geometry)

  def is_symmetric_torsion(self, dp):
    i_seqs = dp.i_seqs
    resname = self.name_hash[i_seqs[0]][5:8].upper()
    if resname not in \
      ['ASP', 'GLU', 'PHE', 'TYR']: #, 'ASN', 'GLN', 'HIS']:
      return False
    torsion_atoms = []
    for i_seq in i_seqs:
      name = self.name_hash[i_seq]
      atom = name[0:4]
      torsion_atoms.append(atom)
    if resname == 'ASP':
      if torsion_atoms == [' CA ', ' CB ', ' CG ', ' OD1'] or \
         torsion_atoms == [' CA ', ' CB ', ' CG ', ' OD2']:
        return True
    elif resname == 'GLU':
      if torsion_atoms == [' CB ', ' CG ', ' CD ', ' OE1'] or \
         torsion_atoms == [' CB ', ' CG ', ' CD ', ' OE2']:
        return True
    elif resname == 'PHE' or resname == 'TYR':
      if torsion_atoms == [' CA ', ' CB ',' CG ',' CD1'] or \
         torsion_atoms == [' CA ', ' CB ',' CG ',' CD2']:
        return True
    #elif resname == 'ASN':
    #  if torsion_atoms == [' CA ', ' CB ',' CG ',' OD1'] or \
    #     torsion_atoms == [' CA ', ' CB ',' CG ',' ND2']:
    #    return True
    #elif resname == 'GLN':
    #  if torsion_atoms == [' CB ', ' CG ',' CD ',' OE1'] or \
    #     torsion_atoms == [' CB ', ' CG ',' CD ',' NE2']:
    #    return True
    #elif resname == 'HIS':
    #  if torsion_atoms == [' CA ', ' CB ',' CG ',' ND1'] or \
    #     torsion_atoms == [' CA ', ' CB ',' CG ',' CD2']:
    #    return True
    return False

  def get_target_angles(self,
                        angles,
                        #cc_s,
                        is_rama_outlier,
                        is_omega_outlier,
                        rotamer_state,
                        chi_ids):
    assert (len(rotamer_state) == len(angles)) or \
           (len(rotamer_state) == 0)
    chi_num = None
    #print chi_ids
    if len(chi_ids) > 0:
      assert len(chi_ids) == chi_ids.count(chi_ids[0])
      if ('oh' not in chi_ids and
          'sh' not in chi_ids and
          'me' not in chi_ids):
        chi_num = chi_ids[0][-1:]
    clusters = {}
    used = []
    target_angles = [None] * len(angles)

    #check for all outliers for current target
    if ( (is_rama_outlier.count(False)  == 0) or
         (is_omega_outlier.count(False) == 0) or
         ( ( (len(rotamer_state)-rotamer_state.count(None)) < 2 and
              len(rotamer_state) > 0)) ):
      for i, target in enumerate(target_angles):
        target_angles[i] = None
      return target_angles
    ###########

    max_i = None
    #for i, cc in enumerate(cc_s):
    #  if is_rama_outlier[i]:
    #    continue
    #  if max_i is None:
    #    max_i = i
    #  elif max < cc:
    #    max_i = i
    for i, ang_i in enumerate(angles):
      if i in used:
        continue
      if ang_i is None:
        continue
      for j, ang_j in enumerate(angles):
        if i == j:
          continue
        elif j in used:
          continue
        elif ang_j is None:
          continue
        else:
          if len(rotamer_state)> 0:
            if rotamer_state[i] is None:
              continue
            elif rotamer_state[j] is None:
              continue
          nonstandard_chi = False
          is_proline = False
          chi_matching = True
          if len(rotamer_state) > 0:
            if rotamer_state[i][0] in ['OUTLIER', 'Cg_exo', 'Cg_endo']:
              nonstandard_chi = True
            elif rotamer_state[j][0] in ['OUTLIER', 'Cg_exo', 'Cg_endo']:
              nonstandard_chi = True
            if rotamer_state[i][0] in ['Cg_exo', 'Cg_endo'] or \
               rotamer_state[j][0] in ['Cg_exo', 'Cg_endo']:
              is_proline = True
          if (chi_num is not None) and not nonstandard_chi:
            chi_counter = int(chi_num)
            while chi_counter > 0:
              if (rotamer_state[i][chi_counter-1] !=
                  rotamer_state[j][chi_counter-1]):
                chi_matching = False
              chi_counter -= 1
          if not chi_matching:
            continue
          if is_proline and \
             rotamer_state[i][0] != rotamer_state[j][0]:
            continue
          if i not in used:
            clusters[i] = []
            clusters[i].append(i)
            clusters[i].append(j)
            used.append(i)
            used.append(j)
          else:
            clusters[i].append(j)
            used.append(j)
      if i not in used:
        clusters[i] = None
    for key in clusters.keys():
      cluster = clusters[key]
      if cluster is None:
        target_angles[key] = None
      else:
        cluster_angles = []
        cluster_outliers = 0
        for i in cluster:
          if is_rama_outlier[i]:
            cluster_angles.append(None)
          elif is_omega_outlier[i]:
            cluster_angles.append(None)
          elif len(rotamer_state) > 0:
            if rotamer_state[i][0] == 'OUTLIER':
              cluster_angles.append(None)
              cluster_outliers += 1
            else:
              cluster_angles.append(angles[i])
          else:
            cluster_angles.append(angles[i])
        if max_i is not None:
          target_angle = angles[max_i]
        else:
          target_angle = utils.get_angle_average(cluster_angles)
        if self.params.target_damping:
          for c in cluster:
            if target_angle is None:
              target_angles[c] = None
            else:
              c_dist = utils.angle_distance(angles[c], target_angle)
              if c_dist > self.params.damping_limit:
                d_target = \
                  utils.get_angle_average([angles[c], target_angle])
                target_angles[c] = d_target
              else:
                target_angles[c] = target_angle
        else:
          if (len(cluster) - cluster_outliers) == 1:
            for c in cluster:
              if rotamer_state[c][0] == 'OUTLIER':
                target_angles[c] = target_angle
              else:
                target_angles[c] = None
          else:
            for c in cluster:
              target_angles[c] = target_angle
        if (self.restrain_to_master_chain):
          if target_angles[cluster[0]] is not None:
            for i,c in enumerate(cluster):
              if i == 0:
                target_angles[c] = None
              else:
                target_angles[c] = angles[cluster[0]]
    return target_angles

  def add_ncs_dihedral_proxies(self, geometry):
    geometry.ncs_dihedral_proxies= \
      self.ncs_dihedral_proxies

  def get_ramachandran_outliers(self, pdb_hierarchy):
    rama_outliers, output_list = \
      self.rama.analyze_pdb(hierarchy=pdb_hierarchy,
                            outliers_only=True)
    return rama_outliers

  def get_omega_outliers(self, pdb_hierarchy):
    cis_peptides, trans_peptides, omega_outliers = \
      analyze_peptides.analyze(pdb_hierarchy=pdb_hierarchy)
    return omega_outliers

  def get_rotamer_data(self, pdb_hierarchy):
    rot_list_model, coot_model = \
      self.r.analyze_pdb(hierarchy=pdb_hierarchy)
    #print rot_list_model
    model_hash = {}
    model_score = {}
    all_rotamers = {}
    model_chis = {}
    for line in rot_list_model.splitlines():
      res, occ, rotamericity, chi1, chi2, chi3, chi4, name = line.split(':')
      model_hash[res]=name
      model_score[res]=rotamericity
    for key in self.res_match_master.keys():
      res_key = key[5:10]+' '+key[0:4]
      all_rotamers[res_key] = []
      model_rot = model_hash.get(res_key)
      if model_rot is not None and model_rot != "OUTLIER":
        all_rotamers[res_key].append(model_rot)
      for match_res in self.res_match_master[key]:
        j_key = match_res[5:10]+' '+match_res[0:4]
        j_rot = model_hash.get(j_key)
        if j_rot is not None and j_rot != "OUTLIER":
          if j_rot not in all_rotamers[res_key]:
            all_rotamers[res_key].append(j_rot)

    for model in pdb_hierarchy.models():
      for chain in model.chains():
        for residue_group in chain.residue_groups():
            all_dict = \
              self.r.construct_complete_sidechain(residue_group)
            for atom_group in residue_group.atom_groups():
              #try:
                atom_dict = all_dict.get(atom_group.altloc)
                chis = \
                  self.r.sa.measureChiAngles(atom_group, atom_dict)
                if chis is not None:
                  key = '%s%5s %s' % (
                      chain.id, residue_group.resid(),
                      atom_group.altloc+atom_group.resname)
                  model_chis[key] = chis
    return model_hash, model_score, all_rotamers, model_chis

  def fix_rotamer_outliers(self,
                           xray_structure,
                           geometry_restraints_manager,
                           pdb_hierarchy,
                           outliers_only=False,
                           log=None,
                           quiet=False):
    self.last_round_outlier_fixes = 0
    if self.rotamer_search_manager is None:
      self.rotamer_search_manager = rotamer_search.manager(
                                      pdb_hierarchy=pdb_hierarchy,
                                      xray_structure=xray_structure,
                                      name_hash=self.name_hash,
                                      selection=self.selection,
                                      log=self.log)
    if self.unit_cell is None:
      self.unit_cell = xray_structure.unit_cell()
    sites_cart = xray_structure.sites_cart()
    for atom in pdb_hierarchy.atoms():
      i_seq = atom.i_seq
      atom.xyz = sites_cart[i_seq]
    selection_radius = 5
    fmodel = self.fmodel
    if(log is None): log = self.log
    make_sub_header(
      "Correcting NCS rotamer outliers",
      out=log)

    self.rotamer_search_manager.prepare_map(fmodel=fmodel)

    model_hash, model_score, all_rotamers, model_chis = \
      self.get_rotamer_data(pdb_hierarchy=pdb_hierarchy)

    fix_list = {}
    rotamer_targets = {}

    for key in self.res_match_master.keys():
      res_key = key[5:10]+' '+key[0:4]
      model_rot = model_hash.get(res_key)
      if model_rot == "OUTLIER":
        rotamer = None
        score = 0.0
        for match_res in self.res_match_master[key]:
          j_key = match_res[5:10]+' '+match_res[0:4]
          j_rot = model_hash.get(j_key)
          j_score = model_score.get(j_key)
          if j_rot is not None and j_score is not None:
            if j_rot != "OUTLIER":
              if rotamer == None:
                rotamer = j_key
                score = j_score
                target = j_rot
              else:
                if j_score > score:
                  rotamer = j_key
                  score = j_score
                  target = j_rot
        if rotamer != None:
          fix_list[res_key] = rotamer
          rotamer_targets[res_key] = target

    sites_cart_moving = xray_structure.sites_cart()
    sites_cart_backup = sites_cart_moving.deep_copy()
    for model in pdb_hierarchy.models():
      for chain in model.chains():
        if not utils.is_protein_chain(chain=chain):
          continue
        for residue_group in chain.residue_groups():
          all_dict = \
            self.r.construct_complete_sidechain(residue_group)
          for atom_group in residue_group.atom_groups():
            if atom_group.resname in ["PRO", "GLY"]:
              continue
            key = '%s%5s %s' % (
                      chain.id, residue_group.resid(),
                      atom_group.altloc+atom_group.resname)
            if key in fix_list.keys():
              model_rot, m_chis, value = self.r.evaluate_rotamer(
                  atom_group=atom_group,
                  all_dict=all_dict,
                  sites_cart=sites_cart_moving)
              residue_name = key[-3:]
              cur_rotamer = rotamer_targets[key]
              r_chis = self.r.sa.get_rotamer_angles(
                             residue_name=residue_name,
                             rotamer_name=cur_rotamer)
              if m_chis is not None and r_chis is not None:
                status = self.rotamer_search_manager.search(
                  atom_group=atom_group,
                  all_dict=all_dict,
                  m_chis=m_chis,
                  r_chis=r_chis,
                  rotamer=cur_rotamer,
                  sites_cart_moving=sites_cart_moving,
                  xray_structure=xray_structure,
                  key=key)
                if status:
                  print >> log, "Set %s to %s rotamer" % \
                    (key, cur_rotamer)
                  self.last_round_outlier_fixes += 1

  def get_sites_cc(self,
                   sites_cart,
                   target_map_data):
    t = fit_rotamers.target(sites_cart,
                            self.unit_cell,
                            target_map_data)
    return t


  def get_sidechain_map_correlation(self,
                                    xray_structure,
                                    pdb_hierarchy):
    map_cc_hash = {}
    sigma_cutoff_hash = {}
    fmodel = self.fmodel
    target_map_data, residual_map_data = \
      utils.prepare_map(fmodel=fmodel)
    sites_cart_moving = xray_structure.sites_cart()
    for model in pdb_hierarchy.models():
      for chain in model.chains():
        #only works with protein sidechains
        if not utils.is_protein_chain(chain=chain):
          continue
        for residue_group in chain.residue_groups():
          all_dict = self.r.construct_complete_sidechain(residue_group)
          for atom_group in residue_group.atom_groups():
            if atom_group.resname in ["PRO", "GLY"]:
              continue
            key = atom_group.atoms()[0].pdb_label_columns()[4:]+\
                  atom_group.atoms()[0].segid
            residue_iselection = atom_group.atoms().extract_i_seq()
            residue_elements = atom_group.atoms().extract_element()
            sidechain_only_iselection = flex.size_t()
            for i, i_seq in enumerate(residue_iselection):
              atom_name = self.name_hash[i_seq][0:4]
              if atom_name not in [' N  ', ' CA ', ' C  ', ' O  '] and \
                 residue_elements[i].strip() not in ['H','D']:
                sidechain_only_iselection.append(i_seq)
            sites_cart_residue = \
              sites_cart_moving.select(sidechain_only_iselection)
            t_test = self.get_sites_cc(sites_cart_residue,
                                       target_map_data)
            map_cc_hash[key] = t_test
            sigma_state = fit_rotamers.all_sites_above_sigma_cutoff(
                            sites_cart_residue,
                            self.unit_cell,
                            target_map_data,
                            1.0)
            sigma_cutoff_hash[key] = sigma_state
    return map_cc_hash, sigma_cutoff_hash

  def fix_rotamer_consistency(self,
                              xray_structure,
                              geometry_restraints_manager,
                              pdb_hierarchy,
                              log=None,
                              quiet=False):
    self.last_round_rotamer_changes = 0
    if self.rotamer_search_manager is None:
      self.rotamer_search_manager = rotamer_search.manager(
                                      pdb_hierarchy=pdb_hierarchy,
                                      xray_structure=xray_structure,
                                      name_hash=self.name_hash,
                                      selection=self.selection,
                                      log=self.log)
    if self.unit_cell is None:
      self.unit_cell = xray_structure.unit_cell()
    sites_cart = xray_structure.sites_cart()
    for atom in pdb_hierarchy.atoms():
      i_seq = atom.i_seq
      atom.xyz = sites_cart[i_seq]
    fmodel = self.fmodel
    if(log is None): log = self.log
    make_sub_header(
      "Checking NCS rotamer consistency",
      out=log)
    rot_list_model, coot_model = \
      self.r.analyze_pdb(hierarchy=pdb_hierarchy)

    self.rotamer_search_manager.prepare_map(fmodel=fmodel)

    model_hash, model_score, all_rotamers, model_chis = \
      self.get_rotamer_data(pdb_hierarchy=pdb_hierarchy)

    sites_cart_moving = xray_structure.sites_cart()
    map_cc_hash, sigma_cutoff_hash = \
      self.get_sidechain_map_correlation(xray_structure, pdb_hierarchy)
    cc_candidate_list = []
    for key in self.ncs_match_hash.keys():
      whole_set = []
      value = map_cc_hash.get(key)
      max = None
      max_key = None
      if value is not None:
        whole_set.append( (key, value) )
        max = value
        max_key = key
      for member in self.ncs_match_hash[key]:
        value = map_cc_hash.get(member)
        if value is not None:
          whole_set.append( (member, value) )
          if max is None:
            max = value
            max_key = member
          else:
            if value > max:
              max = value
              max_key = member
      if max is None or max <= 0.0:
        continue
      for set in whole_set:
        cur_key = set[0]
        cur_value  = set[1]
        #fudge factor to account for zero cur_value
        if cur_value <= 0.0:
          cur_value = 0.0001
        percentage = (max - cur_value) / cur_value
        if percentage > 0.2:
          if not sigma_cutoff_hash[cur_key]:
            cc_candidate_list.append(cur_key)

    for model in pdb_hierarchy.models():
      for chain in model.chains():
        if not utils.is_protein_chain(chain=chain):
          continue
        for residue_group in chain.residue_groups():
          all_dict = self.r.construct_complete_sidechain(residue_group)
          for atom_group in residue_group.atom_groups():
            if atom_group.resname in ["PRO", "GLY"]:
              continue
            key = '%s%5s %s' % (
                      chain.id, residue_group.resid(),
                      atom_group.altloc+atom_group.resname)
            if key in all_rotamers:
              if (len(all_rotamers[key]) >= 2):
                cc_key = atom_group.atoms()[0].pdb_label_columns()[4:]+\
                  atom_group.atoms()[0].segid
                if cc_key not in cc_candidate_list:
                  continue
                model_rot, m_chis, value = self.r.evaluate_rotamer(
                  atom_group=atom_group,
                  all_dict=all_dict,
                  sites_cart=sites_cart_moving)
                residue_name = key[-3:]
                # why do I not try to fix outliers here?
                if model_rot == "OUTLIER":
                  continue
                current_best = model_rot
                #C-alpha prep
                cur_ca = None
                for atom in atom_group.atoms():
                  if atom.name == " CA ":
                    cur_ca = atom.i_seq
                for cur_rotamer in all_rotamers.get(key):
                  if cur_rotamer == model_rot:
                    continue
                  r_chis = self.r.sa.get_rotamer_angles(
                             residue_name=residue_name,
                             rotamer_name=cur_rotamer)
                  if m_chis is not None and r_chis is not None:
                    status = self.rotamer_search_manager.search(
                      atom_group=atom_group,
                      all_dict=all_dict,
                      m_chis=m_chis,
                      r_chis=r_chis,
                      rotamer=cur_rotamer,
                      sites_cart_moving=sites_cart_moving,
                      xray_structure=xray_structure,
                      key=key)
                    if status:
                      current_best = cur_rotamer
                      atom_dict = all_dict.get(atom_group.altloc)
                      m_chis = \
                        self.r.sa.measureChiAngles(atom_group,
                                                   atom_dict,
                                                   sites_cart_moving)
                if current_best != model_rot:
                  print >> self.log, "Set %s to %s rotamer" % \
                    (key,
                     current_best)
                  self.last_round_rotamer_changes += 1
                else:
                  rotamer, chis, value = self.r.evaluate_rotamer(
                      atom_group=atom_group,
                      all_dict=all_dict,
                      sites_cart=sites_cart_moving)
                  assert rotamer == model_rot

  def process_ncs_restraint_groups(self, model, processed_pdb_file):
    log = self.log
    ncs_groups = ncs.restraints.groups()
    sites_cart = None

    for param_group in self.params.restraint_group:
      master = param_group.selection[0]
      selection_strings = []
      found_offset = False
      range_text = ""
      for range in self.master_ranges[master]:
        if range_text == "":
          range_text = "(resseq %d:%d" % (range[0], range[1])
        else:
          range_text += " or resseq %d:%d" % (range[0], range[1])
      range_text += ")"
      master = master + " and " + range_text
      for selection in param_group.selection[1:]:
        range_text = ""
        for range in self.master_ranges[selection]:
          if range_text == "":
            range_text = "(resseq %d:%d" % (range[0], range[1])
          else:
            range_text += " or resseq %d:%d" % (range[0], range[1])
        range_text += ")"
        temp_selection = selection + " and " + range_text
        selection_strings.append(temp_selection)
      group = ncs.restraints.group.from_atom_selections(
        processed_pdb              = processed_pdb_file,
        reference_selection_string = master,
        selection_strings          = selection_strings,
        coordinate_sigma           = param_group.coordinate_sigma,
        b_factor_weight            = param_group.b_factor_weight,
        special_position_warnings_only
          = True,
        log = log)
      ncs_groups.members.append(group)
      print >> log
    if (len(ncs_groups.members) == 0):
      print >> log, "No NCS restraint groups specified."
      print >> log
    else:
      model.restraints_manager.torsion_ncs_groups = ncs_groups

  def build_sidechain_angle_hash(self):
    sidechain_angle_hash = {}
    for key in self.sa.atomsForAngle.keys():
      resname = key[0:3].upper()
      if sidechain_angle_hash.get(resname) is None:
        sidechain_angle_hash[resname] = {}
      new_key = ''
      for atom in self.sa.atomsForAngle[key]:
        new_key += atom
      new_value = key[4:]
      sidechain_angle_hash[resname][new_key] = new_value
    #modifications
    sidechain_angle_hash['ILE'][' N   CA  CB  CG2'] = 'chi1'
    sidechain_angle_hash['THR'][' N   CA  CB  CG2'] = 'chi1'
    sidechain_angle_hash['VAL'][' N   CA  CB  CG2'] = 'chi1'
    return sidechain_angle_hash

  def get_number_of_restraints_per_group(self, pdb_hierarchy):
    torsion_counts = {}
    sel_cache = pdb_hierarchy.atom_selection_cache()
    for group in self.ncs_groups:
      for selection in group:
        sel_atoms_i = (utils.phil_atom_selections_as_i_seqs_multiple(
                         cache=sel_cache,
                         string_list=[selection]))
        torsion_counts[selection] = 0
        for dp in self.ncs_dihedral_proxies:
          if dp.i_seqs[0] in sel_atoms_i:
            torsion_counts[selection] += 1
    return torsion_counts

  def get_torsion_rmsd(self, sites_cart):
    self.histogram_under_limit = None
    self.histogram_over_limit = None
    self.torsion_rmsd = None
    self.all_torsion_rmsd = None
    dp_proxies_under_limit = cctbx.geometry_restraints.shared_dihedral_proxy()
    dp_proxies_over_limit = cctbx.geometry_restraints.shared_dihedral_proxy()
    for dp in self.ncs_dihedral_proxies:
      di = cctbx.geometry_restraints.dihedral(
             sites_cart=sites_cart, proxy=dp)
      delta = abs(di.delta)
      if delta <= self.limit:
        dp_proxies_under_limit.append(dp)
      else:
        dp_proxies_over_limit.append(dp)
    torsion_deltas_under_limit = cctbx.geometry_restraints.dihedral_deltas(
                       sites_cart = sites_cart,
                       proxies = dp_proxies_under_limit)
    torsion_deltas_over_limit = cctbx.geometry_restraints.dihedral_deltas(
                       sites_cart = sites_cart,
                       proxies = dp_proxies_over_limit)
    torsion_deltas_all = cctbx.geometry_restraints.dihedral_deltas(
                       sites_cart = sites_cart,
                       proxies = self.ncs_dihedral_proxies)
    if len(torsion_deltas_under_limit) > 0:
      self.histogram_under_limit = \
        flex.histogram(
          data=flex.abs(torsion_deltas_under_limit),
          data_min=0.0,
          data_max=self.limit,
          n_slots=10)
      self.torsion_rmsd = self.calculate_torsion_rmsd(
                            deltas=torsion_deltas_under_limit)
    if ( (len(torsion_deltas_over_limit) > 0) and
         (self.limit < 180.0) ):
      self.histogram_over_limit = \
        flex.histogram(
          data=flex.abs(torsion_deltas_over_limit),
          data_min=self.limit,
          data_max=math.ceil(
          max(flex.abs(torsion_deltas_over_limit))),
          n_slots=10)
    if len(torsion_deltas_all) > 0:
      self.all_torsion_rmsd = self.calculate_torsion_rmsd(
                                deltas=torsion_deltas_all)

  def calculate_torsion_rmsd(self, deltas):
    assert len(deltas) > 0
    delta_sq_sum = 0.0
    for delta in deltas:
      delta_sq_sum += ( abs(delta)**2 )
    return math.sqrt(delta_sq_sum / len(deltas))

  def select (self, nseq, iselection) :
    assert (self.ncs_dihedral_proxies is not None)
    return torsion_ncs(
             fmodel=self.fmodel,
             params=self.params,
             b_factor_weight=self.b_factor_weight,
             coordinate_sigma=self.coordinate_sigma,
             selection=None, #not sure here
             ncs_groups=self.ncs_groups,
             alignments=self.alignments,
             ncs_dihedral_proxies= \
               self.ncs_dihedral_proxies.proxy_select(nseq, iselection),
             log=self.log)

#split out functions
class get_ncs_groups(object):
  def __init__(self,
               pdb_hierarchy,
               use_segid,
               params,
               log):
    ncs_groups = []
    alignments = {}
    used_chains = []
    pair_hash = {}
    chains = pdb_hierarchy.models()[0].chains()
    am = utils.alignment_manager(pdb_hierarchy, use_segid, log)

    for i, chain_i in enumerate(chains):
      found_conformer = False
      for conformer in chain_i.conformers():
        if not conformer.is_protein() and not conformer.is_na():
          continue
        else:
          found_conformer = True
      if not found_conformer:
        continue
      segid_i = utils.get_unique_segid(chain_i)
      if segid_i == None:
        continue
      if (use_segid) :
        chain_i_str = "chain '%s' and segid '%s'" % \
          (chain_i.id, segid_i)
      else :
        chain_i_str = "chain '%s'" % chain_i.id
      for chain_j in chains[i+1:]:
        found_conformer = False
        for conformer in chain_j.conformers():
          if not conformer.is_protein() and not conformer.is_na():
            continue
          else:
            found_conformer = True
        if not found_conformer:
          continue
        segid_j = utils.get_unique_segid(chain_j)
        if segid_j == None:
          continue
        if (use_segid) :
          chain_j_str = "chain '%s' and segid '%s'" % (chain_j.id, segid_j)
        else :
          chain_j_str = "chain '%s'" % chain_j.id
        seq_pair = (am.sequences[chain_i_str],
                    am.sequences[chain_j_str])
        seq_pair_padded = (am.padded_sequences[chain_i_str],
                           am.padded_sequences[chain_j_str])
        struct_pair = (am.structures[chain_i_str],
                       am.structures[chain_j_str])
        if ( (len(seq_pair[0])==0 and len(seq_pair[1])==0) or
             (len(seq_pair_padded[0])==0 and len(seq_pair_padded[1])==0) ):
          continue
        residue_match_map = \
          utils._alignment(
            params=params,
            sequences=seq_pair,
            padded_sequences=seq_pair_padded,
            structures=struct_pair,
            log=log)
        key = (chain_i_str, chain_j_str)
        alignments[key] = residue_match_map
        if ( min(len(residue_match_map),
                 chain_i.residue_groups_size(),
                 chain_j.residue_groups_size()) \
             / max(len(residue_match_map),
                   chain_i.residue_groups_size(),
                   chain_j.residue_groups_size()) \
             >= params.similarity ):
          pair_key = (chain_i.id, segid_i)
          match_key = (chain_j.id, segid_j)
          if used_chains is not None:
            if match_key in used_chains:
              continue
          assign_key = None
          if pair_key in used_chains:
            for group_key in pair_hash.keys():
              if pair_key in pair_hash[group_key]:
                assign_key = group_key
          if assign_key is None:
            assign_key = pair_key
          if (not assign_key in pair_hash) :
            pair_hash[assign_key] = []
          pair_hash[assign_key].append(match_key)
          used_chains.append(match_key)

    for key in pair_hash.keys():
      ncs_set = []
      if (use_segid) :
        chain_str = "chain '%s' and segid '%s'" % (key[0], key[1])
      else :
        chain_str = "chain '%s'" % (key[0])
      ncs_set.append(chain_str)
      for add_chain in pair_hash[key]:
        if (use_segid) :
          chain_str = "chain '%s' and segid '%s'" % \
            (add_chain[0], add_chain[1])
        else :
          chain_str = "chain '%s'" % (add_chain[0])
        ncs_set.append(chain_str)
      ncs_groups.append(ncs_set)

    self.alignments = alignments
    self.ncs_groups = ncs_groups

def determine_ncs_groups(pdb_hierarchy,
                         params=None,
                         log=None):
  pdb_hierarchy.reset_i_seq_if_necessary()
  if params is None:
    params = torsion_ncs_params.extract()
  if log is None:
    log = sys.stdout
  atom_labels = list(pdb_hierarchy.atoms_with_labels())
  segids = flex.std_string([ a.segid for a in atom_labels ])
  use_segid = not segids.all_eq('    ')
  ncs_groups_manager = get_ncs_groups(
                         pdb_hierarchy=pdb_hierarchy,
                         use_segid=use_segid,
                         params=params,
                         log=log)
  return ncs_groups_manager.ncs_groups

# XXX wrapper for running in Phenix GUI
class _run_determine_ncs_groups (object) :
  def __init__ (self, params, pdb_hierarchy) :
    self.params = params
    self.pdb_hierarchy = pdb_hierarchy

  def __call__ (self, *args, **kwds) :
    return determine_ncs_groups(
      params=self.params,
      pdb_hierarchy=self.pdb_hierarchy)
