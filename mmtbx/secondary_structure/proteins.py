
from __future__ import division
import iotbx.pdb.secondary_structure
import iotbx.phil
import libtbx.object_oriented_patterns as oop
from libtbx.utils import Sorry
from libtbx import group_args
from math import sqrt
import sys

helix_group_params_str = """
helix
  .multiple = True
  .optional = True
  .style = noauto
{
  selection = None
    .type = atom_selection
    .style = bold
  helix_type = *alpha pi 3_10 unknown
    .type = choice
    .help = Type of helix, defaults to alpha.  Only alpha, pi, and 3_10 \
      helices are used for hydrogen-bond restraints.
    .style = bold
  restraint_sigma = None
    .type = float
  restraint_slack = None
    .type = float
  backbone_only = False
    .type = bool
    .help = Only applies to rigid-body groupings, and not H-bond restraints \
      which are already backbone-only.
}"""

sheet_group_params_str = """
sheet
  .multiple = True
  .optional = True
  .style = noauto
{
  first_strand = None
    .type = atom_selection
    .style = bold
  strand
    .multiple = True
    .optional = True
  {
    selection = None
      .type = atom_selection
      .style = bold
    sense = parallel antiparallel *unknown
      .type = choice
      .style = bold
    bond_start_current = None
      .type = atom_selection
      .style = bold
    bond_start_previous = None
      .type = atom_selection
      .style = bold
  }
  restraint_sigma = None
    .type = float
  restraint_slack = None
    .type = float
  backbone_only = False
    .type = bool
    .help = Only applies to rigid-body groupings, and not H-bond restraints \
      which are already backbone-only.
}
"""

use_resids = True # XXX: for debugging purposes only
helix_classes = ["unknown"] * 10
helix_classes[0] = "alpha"
helix_classes[2] = "pi"
helix_classes[4] = "3_10"

class _annotation (oop.injector, iotbx.pdb.secondary_structure.annotation) :
  def as_restraint_groups (self, log=sys.stderr, prefix_scope="",
      add_segid=None) :
    phil_strs = []
    for helix in self.helices :
      helix_phil = helix.as_restraint_group(log, prefix_scope, add_segid)
      if helix_phil is not None :
        phil_strs.append(helix_phil)
    for sheet in self.sheets :
      sheet_phil = sheet.as_restraint_group(log, prefix_scope, add_segid)
      if sheet_phil is not None :
        phil_strs.append(sheet_phil)
    return "\n".join(phil_strs)

class _pdb_helix (oop.injector, iotbx.pdb.secondary_structure.pdb_helix) :
  def as_restraint_group (self, log=sys.stderr, prefix_scope="",
      add_segid=None) :
    if self.start_chain_id != self.end_chain_id :
      print >> log, "Helix chain ID mismatch: starts in %s, ends in %s" % (
        self.start_chain_id, self.end_chain_id)
      return None
    segid_extra = ""
    if add_segid is not None :
      segid_extra = "and segid '%s' " % add_segid
    if use_resids :
      resid_start = "%d%s" % (self.start_resseq, self.start_icode)
      resid_end = "%d%s" % (self.end_resseq, self.end_icode)
      sele = "chain '%s' %sand resid %s through %s" % (self.start_chain_id,
        segid_extra, resid_start, resid_end)
    else :
      sele = "chain '%s' %sand resseq %d:%d" % (self.start_chain_id,
        segid_extra, self.start_resseq, self.end_resseq)
    if prefix_scope != "" and not prefix_scope.endswith(".") :
      prefix_scope += "."
    rg = """\
%shelix {
  selection = "%s"
  helix_type = %s
}""" % (prefix_scope, sele, helix_classes[self.helix_class - 1])
    return rg

class _pdb_sheet (oop.injector, iotbx.pdb.secondary_structure.pdb_sheet) :
  def as_restraint_group (self, log=sys.stderr, prefix_scope="",
      add_segid=None) :
    if len(self.strands) == 0 :
      return None
    selections = []
    senses = []
    reg_curr = []
    reg_prev = []
    segid_extra = ""
    if add_segid is not None :
      segid_extra = "and segid '%s' " % add_segid
    for (strand,registration) in zip(self.strands, self.registrations) :
      if use_resids :
        resid_start = "%d%s" % (strand.start_resseq, strand.start_icode)
        resid_end = "%d%s" % (strand.end_resseq, strand.end_icode)
        sele = "chain '%s' %sand resid %s through %s" % (strand.start_chain_id,
          segid_extra, resid_start, resid_end)
      else :
        sele = "chain '%s' %sand resseq %d:%d" % (strand.start_chain_id,
          segid_extra, strand.start_resseq, strand.end_resseq)
      selections.append(sele)
      if strand.sense == 0 :
        senses.append("unknown")
      elif strand.sense == -1 :
        senses.append("antiparallel")
      elif strand.sense == 1 :
        senses.append("parallel")
      else :
        raise Sorry("Sense must be 0, 1, or -1.")
      if registration is not None :
        if use_resids :
          sele_base = "chain '%s' %sand resid %s"
          resid_curr = "%d%s" % (registration.cur_resseq,registration.cur_icode)
          resid_prev = "%d%s" % (registration.prev_resseq,
            registration.prev_icode)
          reg_curr.append(sele_base % (registration.cur_chain_id,segid_extra,
            resid_curr))
          reg_prev.append(sele_base % (registration.prev_chain_id,segid_extra,
            resid_prev))
        else :
          reg_curr.append("chain '%s' %sand resseq %d" % (
            registration.cur_chain_id, segid_extra, registration.cur_resseq))
          reg_prev.append("chain '%s' %sand resseq %d" % (
            registration.prev_chain_id, segid_extra, registration.prev_resseq))
      else :
        reg_curr.append(None)
        reg_prev.append(None)
    n = 0
    first_strand = None
    strands = []
    for (sele, sense, curr, prev) in zip(selections,senses,reg_curr,reg_prev) :
      if n == 0 :
        first_strand = sele
      else :
        strands.append("""\
  strand {
    selection = "%s"
    sense = %s
    bond_start_current = "%s"
    bond_start_previous = "%s"
  }""" % (sele, sense, curr, prev))
      n += 1
    assert first_strand is not None
    if prefix_scope != "" and not prefix_scope.endswith(".") :
      prefix_scope += "."
    phil_str = """
%ssheet {
  first_strand = "%s"
%s
}""" % (prefix_scope, first_strand, "\n".join(strands))
    return phil_str

def _create_hbond_proxy (
    acceptor_atoms,
    donor_atoms,
    build_proxies,
    hbond_counts,
    distance_ideal,
    distance_cut,
    hbond_params,
    remove_outliers,
    use_hydrogens,
    weight=1.0,
    sigma=None,
    slack=None,
    log=sys.stdout) :
  donor_labels = None
  acceptor_labels = None
  [donor,acceptor,acceptor_base,hydrogen] = [None] * 4
  for atom in acceptor_atoms :
    if (atom.name == ' O  ') :
      acceptor = atom
      acceptor_labels = atom.fetch_labels()
    elif (atom.name == ' C  ') :
      acceptor_base = atom
  for atom in donor_atoms :
    if (atom.name == ' N  ') :
      donor = atom
      donor_labels = atom.fetch_labels()
    elif (atom.name == ' H  ') :
      hydrogen = atom
  if ([donor,acceptor,acceptor_base].count(None) == 0) :
    if (use_hydrogens) and (hydrogen is None) :
      donor_resseq = donor_atoms[0].fetch_labels().resseq_as_int()
      print >> log, "  Missing hydrogen at %d" % donor_resseq
      return 0
    if (hbond_counts[donor.i_seq] > 0) :
      print >> log, "  WARNING: donor atom is already bonded, skipping"
      print >> log, "    %s" % donor_labels.id_str()
      return 0
    elif (hbond_counts[acceptor.i_seq] > 0) :
      print >> log, "  WARNING: acceptor atom is already bonded, skipping"
      print >> log, "    %s" % acceptor_labels.id_str()
      return 0
    if (remove_outliers) and (distance_cut > 0) :
      if (use_hydrogens) :
        dist = hydrogen.distance(acceptor)
      else :
        dist = donor.distance(acceptor)
      if (dist > distance_cut) :
        print >> log, "  removed outlier: %.3fA (cutoff: %.3fA)" % (dist,
          distance_cut)
        print >> log, "    %s --> %s" % (donor_labels.id_str(),
          acceptor_labels.id_str())
        return 0
    if (use_hydrogens) :
      donor = hydrogen
    sigma_ = sigma
    if (sigma is None) :
      sigma_ = hbond_params.sigma
    slack_ = slack
    if (slack is None) :
      slack_ = hbond_params.slack
    limit = -1
    if (hbond_params.top_out) :
      limit = (distance_cut - distance_ideal)**2 * weight/(sigma_**2)
      print "limit: %.2f" % limit
    build_proxies.add_proxy(
      i_seqs=[donor.i_seq, acceptor.i_seq],
      distance_ideal=distance_ideal,
      distance_cut=distance_cut,
      weight=weight/(sigma_ ** 2),
      slack=slack_,
      limit=limit,
      top_out=hbond_params.top_out)
    build_proxies.add_nonbonded_exclusion(donor.i_seq, acceptor.i_seq)
    return 1
  else :
    print >> log, "WARNING: missing atoms!"
    return 0

def create_helix_hydrogen_bond_proxies (
    params,
    pdb_hierarchy,
    selection_cache,
    build_proxies,
    weight,
    hbond_params,
    hbond_counts,
    distance_ideal,
    distance_cut,
    remove_outliers,
    use_hydrogens,
    master_selection,
    log=sys.stdout) :
  assert (not None in [distance_ideal, distance_cut])
  helix_class = params.helix_type
  if helix_class == "alpha" :
    helix_step = 4
  elif helix_class == "pi" :
    helix_step = 5
  elif helix_class == "3_10" :
    helix_step = 3
  else :
    print >> log, "  Don't know bonding for helix class %s." % helix_class
    return 0
  try :
    helix_selection = selection_cache.selection(params.selection)
  except Exception, e :
    print >> log, str(e)
    return 0
  assert (helix_step in [3, 4, 5])
  if (not master_selection.is_super_set(helix_selection)) :
    return 0
  n_proxies = 0
  helix_i_seqs = helix_selection.iselection()
  for model in pdb_hierarchy.models() :
    for chain in model.chains() :
      for conformer in chain.conformers() :
        chain_i_seqs = conformer.atoms().extract_i_seq()
        both_i_seqs = chain_i_seqs.intersection(helix_i_seqs)
        if (both_i_seqs.size() == 0) :
          continue
        residues = conformer.residues()
        n_residues = len(residues)
        j_seq = 0
        while (j_seq < n_residues - helix_step) :
          residue = residues[j_seq]
          resi_atoms = residue.atoms()
          resseq = residue.resseq_as_int()
          donor = None
          acceptor = None
          acceptor_base = None
          hydrogen = None
          if(helix_selection[resi_atoms[0].i_seq]):
            k_seq = j_seq + helix_step
            bonded_resi = residues[k_seq]
            bonded_resseq = bonded_resi.resseq_as_int()
            if (bonded_resi.resname == "PRO") :
              print >> log, "  Proline residue at %s %s - end of helix" % \
                (chain.id, bonded_resseq)
              j_seq += 3
              continue # XXX is this safe?
            elif (bonded_resseq != (resseq + helix_step)) :
              print >> log, "  Confusing residue numbering: %s %s -> %s %s" \
                % (chain.id, residue.resid(), chain.id, bonded_resi.resid())
              j_seq += 1
              continue
            bonded_atoms = bonded_resi.atoms()
            if (helix_selection[bonded_atoms[0].i_seq] == True) :
              n_proxies += _create_hbond_proxy(
                acceptor_atoms=resi_atoms,
                donor_atoms=bonded_atoms,
                build_proxies=build_proxies,
                hbond_counts=hbond_counts,
                distance_ideal=distance_ideal,
                distance_cut=distance_cut,
                hbond_params=hbond_params,
                remove_outliers=remove_outliers,
                use_hydrogens=use_hydrogens,
                weight=weight,
                sigma=params.restraint_sigma,
                slack=params.restraint_slack,
                log=log)
          j_seq += 1
  return n_proxies

def create_sheet_hydrogen_bond_proxies (
    sheet_params,
    pdb_hierarchy,
    build_proxies,
    weight,
    hbond_params,
    hbond_counts,
    distance_ideal,
    distance_cut,
    remove_outliers,
    use_hydrogens,
    master_selection,
    log=sys.stdout) :
  assert (not None in [distance_ideal, distance_cut])
  cache = pdb_hierarchy.atom_selection_cache()
  prev_strand = sheet_params.first_strand
  prev_selection = cache.selection(prev_strand)
  if (not master_selection.is_super_set(prev_selection)) :
    return 0
  prev_residues = _get_strand_residues(
    pdb_hierarchy=pdb_hierarchy,
    strand_selection=prev_selection)
  n_proxies = 0
  k = 0
  while k < len(sheet_params.strand) :
    curr_strand = sheet_params.strand[k]
    curr_selection = cache.selection(curr_strand.selection)
    curr_start = cache.selection(curr_strand.bond_start_current)
    prev_start = cache.selection(curr_strand.bond_start_previous)
    curr_residues = _get_strand_residues(
      pdb_hierarchy=pdb_hierarchy,
      strand_selection=curr_selection)
    i = j = 0
    if (len(curr_residues) > 0) and (len(prev_residues) > 0) :
      i = _find_start_residue(
        residues=prev_residues,
        start_selection=prev_start)
      j = _find_start_residue(
        residues=curr_residues,
        start_selection=curr_start)
      if (i >= 0) and (j >= 0) :
        if (curr_strand.sense == "parallel") :
          while (i < len(prev_residues)) and (j < len(curr_residues)) :
            if (prev_residues[i].resname.strip() != "PRO") :
              n_proxies += _create_hbond_proxy(
                acceptor_atoms=curr_residues[j].atoms(),
                donor_atoms=prev_residues[i].atoms(),
                build_proxies=build_proxies,
                hbond_counts=hbond_counts,
                distance_ideal=distance_ideal,
                distance_cut=distance_cut,
                hbond_params=hbond_params,
                remove_outliers=remove_outliers,
                use_hydrogens=use_hydrogens,
                weight=weight,
                sigma=sheet_params.restraint_sigma,
                slack=sheet_params.restraint_slack,
                log=log)
            if ((j + 2) >= len(curr_residues)) :
              break
            if (curr_residues[j+2].resname.strip() != "PRO") :
              n_proxies += _create_hbond_proxy(
                acceptor_atoms=prev_residues[i].atoms(),
                donor_atoms=curr_residues[j+2].atoms(),
                build_proxies=build_proxies,
                hbond_counts=hbond_counts,
                distance_ideal=distance_ideal,
                distance_cut=distance_cut,
                hbond_params=hbond_params,
                remove_outliers=remove_outliers,
                use_hydrogens=use_hydrogens,
                weight=weight,
                sigma=sheet_params.restraint_sigma,
                slack=sheet_params.restraint_slack,
                log=log)
            i += 2
            j += 2
        elif (curr_strand.sense == "antiparallel") :
          len_prev_residues = len(prev_residues)
          while(i < len_prev_residues and j >= 0):
            if (prev_residues[i].resname.strip() != "PRO") :
              n_proxies += _create_hbond_proxy(
                acceptor_atoms=curr_residues[j].atoms(),
                donor_atoms=prev_residues[i].atoms(),
                build_proxies=build_proxies,
                hbond_counts=hbond_counts,
                distance_ideal=distance_ideal,
                distance_cut=distance_cut,
                hbond_params=hbond_params,
                remove_outliers=remove_outliers,
                use_hydrogens=use_hydrogens,
                weight=weight,
                sigma=sheet_params.restraint_sigma,
                slack=sheet_params.restraint_slack,
                log=log)
            if (curr_residues[j].resname.strip() != "PRO") :
              n_proxies += _create_hbond_proxy(
                acceptor_atoms=prev_residues[i].atoms(),
                donor_atoms=curr_residues[j].atoms(),
                build_proxies=build_proxies,
                hbond_counts=hbond_counts,
                distance_ideal=distance_ideal,
                distance_cut=distance_cut,
                hbond_params=hbond_params,
                remove_outliers=remove_outliers,
                use_hydrogens=use_hydrogens,
                weight=weight,
                sigma=sheet_params.restraint_sigma,
                slack=sheet_params.restraint_slack,
                log=log)
            i += 2; i = min(i, len_prev_residues)
            j -= 2; j = max(0, j)
        else :
          print >> log, "  WARNING: strand direction not defined!"
          print >> log, "    previous: %s" % prev_strand
          print >> log, "    current: %s" % curr_strand.selection
      else :
        print >> log, "  WARNING: can't find start of bonding for strands!"
        print >> log, "    previous: %s" % prev_strand
        print >> log, "    current: %s" % curr_strand.selection
    else :
      print >> log, "  WARNING: can't find one or more strands!"
      print >> log, "    previous: %s" % prev_strand
      print >> log, "    current: %s" % curr_strand.selection
    k += 1
    prev_strand = curr_strand
    prev_selection = curr_selection
    prev_residues = curr_residues
  return n_proxies

def _find_start_residue (
    residues,
    start_selection) :
  start_i_seqs = start_selection.iselection()
  for i, residue in enumerate(residues) :
    atom_i_seqs = residue.atoms().extract_i_seq()
    if (atom_i_seqs.intersection(start_i_seqs).size() > 0) :
      return i
  return -1

def _get_strand_residues (
    pdb_hierarchy,
    strand_selection) :
  strand_i_seqs = strand_selection.iselection()
  strand_residues = []
  for model in pdb_hierarchy.models() :
    for chain in model.chains() :
      for conformer in chain.conformers() :
        chain_i_seqs = conformer.atoms().extract_i_seq()
        both_i_seqs = chain_i_seqs.intersection(strand_i_seqs)
        if (both_i_seqs.size() == 0) :
          continue
        residues = conformer.residues()
        n_residues = len(residues)
        for j_seq, residue in enumerate(residues) :
          resi_atoms = residue.atoms()
          if (strand_selection[resi_atoms[0].i_seq] == True) :
            strand_residues.append(residue)
        if (len(strand_residues) > 0) :
          break
      if (len(strand_residues) > 0) :
        break
    if (len(strand_residues) > 0) :
      break
  return strand_residues

def restraint_groups_as_pdb_helices (pdb_hierarchy, helices, log=sys.stderr) :
  isel = pdb_hierarchy.atom_selection_cache().iselection
  atoms = [ a for a in pdb_hierarchy.atoms_with_labels() ]
  pdb_helices = []
  for i, helix_params in enumerate(helices) :
    if helix_params.selection is None :
      print >> log, "Empty helix at serial %d." % (i+1)
      continue
    sele_str = ("(%s) and (name N) and (altloc 'A' or altloc ' ')" %
                helix_params.selection)
    amide_isel = isel(sele_str)
    start_atom = atoms[amide_isel[0]]
    end_atom = atoms[amide_isel[-1]]
    if helix_params.helix_type == "unknown" :
      helix_class = 2
    else :
      helix_class = helix_classes.index(helix_params.helix_type)
    current_helix = iotbx.pdb.secondary_structure.pdb_helix(
      serial=i+1,
      helix_id=i+1,
      start_resname=start_atom.resname,
      start_chain_id=start_atom.chain_id,
      start_resseq=start_atom.resseq,
      start_icode=start_atom.icode,
      end_resname=end_atom.resname,
      end_chain_id=end_atom.chain_id,
      end_resseq=end_atom.resseq,
      end_icode=end_atom.icode,
      helix_class=helix_class,
      comment="",
      length=amide_isel.size())
    pdb_helices.append(current_helix)
  return pdb_helices

def restraint_groups_as_pdb_sheets (pdb_hierarchy, sheets, log=sys.stderr) :
  isel = pdb_hierarchy.atom_selection_cache().iselection
  atoms = [ a for a in pdb_hierarchy.atoms_with_labels() ]
  pdb_sheets = []
  for i, sheet in enumerate(sheets) :
    sheet_id = string.uppercase[i]
    if sheet.first_strand is None :
      print >> log, "Missing first strand in sheet %s" % sheet_id
    current_sheet = iotbx.pdb.secondary_structure.pdb_sheet(
      sheet_id=sheet_id,
      n_strands=1+len(sheet.strand),
      strands=[],
      registrations=[])
    first_strand = _strand_group_as_pdb_strand(isel=isel,
      selection=sheet.first_strand,
      atoms=atoms,
      log=log,
      sense=None)
    current_sheet.add_strand(first_strand)
    current_sheet.add_registration(None)
    base_sele = "(%s) and name N and (altloc 'A' or altloc ' ')"
    for strand in sheet.strand :
      pdb_strand = _strand_group_as_pdb_strand(isel=isel,
        selection=strand.selection,
        atoms=atoms,
        log=log,
        sense=strand.sense)
      current_sheet.add_strand(pdb_strand)
      s1 = base_sele % strand.bond_start_current
      s2 = base_sele % strand.bond_start_previous
      reg_curr_isel = isel(s1)
      reg_prev_isel = isel(s2)
      if reg_curr_isel.size() == 0 or reg_prev_isel.size() == 0 :
        current_sheet.add_registration(None)
        continue
      reg_curr_atom = atoms[reg_curr_isel[0]]
      reg_prev_atom = atoms[reg_prev_isel[0]]
      registration = group_args(
        cur_atom=donor_name, #reg_curr_atom.name,
        cur_resname=reg_curr_atom.resname,
        cur_chain_id=reg_curr_atom.chain_id,
        cur_resseq=reg_curr_atom.resseq,
        cur_icode=reg_curr_atom.icode,
        prev_atom=reg_prev_atom.name,
        prev_resname="O", #reg_prev_atom.resname,
        prev_chain_id=reg_prev_atom.chain_id,
        prev_resseq=reg_prev_atom.resseq,
        prev_icode=reg_prev_atom.icode)
      current_sheet.add_registration(registration)
    pdb_sheets.append(current_sheet)
  return pdb_sheets

def _strand_group_as_pdb_strand (isel, selection, atoms, log, sense) :
  if sense is None or sense == "unknown" :
    int_sense = 0
  elif sense == "parallel" :
    int_sense = 1
  elif sense == "antiparallel" :
    int_sense = -1
  strand_isel = isel("(%s) and name N and (altloc 'A' or altloc ' ')" % (
    selection))
  start_atom = atoms[strand_isel[0]]
  end_atom = atoms[strand_isel[-1]]
  pdb_strand = group_args(
    sheet_id=sheet_id,
    strand_id=i+1,
    start_resname=start_atom.resname,
    start_chain_id=start_atom.chain_id,
    start_resseq=start_atom.resseq,
    start_icode=start_atom.icode,
    end_resname=end_atom.resname,
    end_chain_id=end_atom.chain_id,
    end_resseq=end_atom.resseq,
    end_icode=end_atom.icode,
    sense=int_sense)
  return pdb_strand

########################################################################
# ANNOTATION
#
class find_helices_simple (object) :
  """
  Identify helical regions, defined as any three or more contiguous residues
  with phi and psi within specified limits:
    -120 < phi < -20
    -80 < psi < -10
  This is much more tolerant of distorted models than KSDSSP, but will still
  miss helices in poor structures.
  """
  def __init__ (self, pdb_hierarchy) :
    self.pdb_hierarchy = pdb_hierarchy
    self._helices = []
    self._current_helix = []
    self.run()

  def process_break (self) :
    if (len(self._current_helix) > 3) :
      self._helices.append(self._current_helix)
    self._current_helix = []

  def push_back (self, chain_id, resseq) :
    if (len(self._current_helix) > 0) :
      last_chain, last_resseq = self._current_helix[-1]
      if (last_chain == chain_id) :
        self._current_helix.append((chain_id,resseq))
    else :
      self._current_helix = [(chain_id, resseq)]

  def run (self) :
    import mmtbx.rotamer
    import iotbx.pdb
    get_class = iotbx.pdb.common_residue_names_get_class
    atoms = self.pdb_hierarchy.atoms()
    sites_cart = atoms.extract_xyz()
    current_helix = []
    for model in self.pdb_hierarchy.models() :
      for chain in model.chains() :
        main_conf = chain.conformers()[0]
        residues = main_conf.residues()
        for i_res in range(len(residues) - 1) :
          residue1 = residues[i_res]
          if (get_class(residue1.resname) == "common_amino_acid") :
            residue0 = None
            if (i_res > 0) :
              residue0 = residues[i_res - 1]
            residue2 = residues[i_res+1]
            resseq1 = residue1.resseq_as_int()
            resseq2 = residue2.resseq_as_int()
            if (residue0 is not None) :
              if ((resseq2 == (resseq1 + 1)) or
                  ((resseq2 == resseq1) and
                   (residue1.icode != residue2.icode))) :
                resseq0 = residue0.resseq_as_int()
                if ((resseq0 == (resseq1 - 1)) or ((resseq0 == resseq1) and
                    (residue0.icode != residue1.icode))) :
                  phi_psi_i_seqs = mmtbx.rotamer.get_phi_psi_indices(
                    prev_res=residue0,
                    residue=residue1,
                    next_res=residue2)
                  if (phi_psi_i_seqs.count(None) > 0) :
                    continue
                  (phi, psi) = mmtbx.rotamer.phi_psi_from_sites(
                    i_seqs=phi_psi_i_seqs,
                    sites_cart=sites_cart)
                  if is_approximately_helical(phi, psi) :
                    self.push_back(chain.id, resseq1)
                    continue
                  else :
                    pass
            self.process_break()

  def build_selections (self) :
    atom_selections = []
    for helix in self._helices :
      chain_id = helix[0][0]
      selection = """chain '%s' and resseq %d:%d""" % (helix[0][0],
        helix[0][1], helix[-1][1])
      atom_selections.append(selection)
    return atom_selections

  def as_restraint_group_phil (self) :
    phil_strs = []
    for selection in self.build_selections() :
      helix_str = """helix {\n  selection = "%s"\n}""" % selection
      phil_strs.append(helix_str)
    if (len(phil_strs) > 0) :
      master_phil = iotbx.phil.parse(helix_group_params_str)
      helix_phil = iotbx.phil.parse("\n".join(phil_strs))
      return master_phil.fetch(source=helix_phil)
    return None

  def as_restraint_groups (self) :
    helix_phil = self.as_restraint_group_phil()
    if (helix_phil is not None) :
      return helix_phil.extract()
    return None

  def as_pdb_records (self) :
    pass

  def show (self, out=sys.stdout) :
    if (len(self._helices) == 0) :
      print >> out, "No recognizable helices."
    else :
      print >> out, "%d helix-like regions found:" % len(self._helices)
    for selection in self.build_selections() :
      print >> out, "  %s" % selection

def is_approximately_helical (phi, psi) :
  if (-120 < phi < -20) and (-80 < psi < -10) :
    return True
  return False

# FIXME
def _find_strand_bonding_start (atoms,
    prev_strand_donors,
    prev_strand_acceptors,
    curr_strand_donors,
    curr_strand_acceptors,
    sense,
    max_distance_cutoff=4.5) :
  assert sense != "unknown"
  assert prev_strand_donors.size() == prev_strand_acceptors.size()
  assert curr_strand_donors.size() == curr_strand_acceptors.size()
  sites_cart = atoms.extract_xyz()
  min_dist = max_distance_cutoff
  best_pair = (None, None)
  for donor_i_seq in prev_strand_donors :
    for acceptor_j_seq in curr_strand_acceptors :
      (x1, y1, z1) = sites_cart[donor_i_seq]
      (x2, y2, z2) = sites_cart[acceptor_j_seq]
      dist = sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
      if (dist < min_dist) :
        best_pair = (donor_i_seq, acceptor_i_seq)
  return best_pair
