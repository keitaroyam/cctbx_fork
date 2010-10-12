
from __future__ import division
import iotbx.pdb.secondary_structure
import libtbx.object_oriented_patterns as oop
from libtbx.utils import Sorry
from libtbx import adopt_init_args, group_args
from math import sqrt
import sys

helix_group_params_str = """
helix
  .multiple = True
  .optional = True
  .style = noauto
{
  selection = None
    .type = str
    .style = bold selection
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
    .type = str
    .style = bold selection
  strand
    .multiple = True
    .optional = True
  {
    selection = None
      .type = str
      .style = bold selection
    sense = parallel antiparallel *unknown
      .type = choice
      .style = bold
    bond_start_current = None
      .type = str
      .style = bold selection
    bond_start_previous = None
      .type = str
      .style = bold selection
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

use_resids = False # XXX: for debugging purposes only
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

def donors_and_acceptors (base_sele, selection_cache, atoms, donor_name,
    ss_type) :
  isel = selection_cache.iselection
  donor_sele = "(%s) and (altloc 'A' or altloc ' ') and name %s" % (
    base_sele, donor_name)
  acceptor_sele = "(%s) and (altloc 'A' or altloc ' ') and name O"% base_sele
  donor_isel = isel(donor_sele)
  acceptor_isel = isel(acceptor_sele)
  n_donors = donor_isel.size()
  n_acceptors = acceptor_isel.size()
  n_atoms = atoms.size()
  if n_acceptors == 0 :
    raise RuntimeError("No atoms for selection %s." % acceptor_sele)
  elif n_donors != n_acceptors :
    n_pro = 0
    for k, i_seq in enumerate(acceptor_isel) :
      acceptor_atom = atoms[i_seq].fetch_labels()
      if acceptor_atom.resname.strip() == "PRO" :
        donor_isel.insert(k, n_atoms)
        n_pro += 1
    if (n_donors + n_pro) != n_acceptors :
      raise RuntimeError("""\
hydrogen_bonds_from_selections: incomplete non-PRO residues in %s.
  \"%s\" => %d donors
  \"%s\" => %d acceptors""" % (ss_type, donor_sele, donor_isel.size(),
      acceptor_sele, acceptor_isel.size()))
  return donor_isel, acceptor_isel

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

def hydrogen_bonds_from_strand_pair (atoms,
    prev_strand_donors,
    prev_strand_acceptors,
    prev_strand_start,
    curr_strand_donors,
    curr_strand_acceptors,
    curr_strand_start,
    sense) :
  n_atoms = atoms.size()
  assert sense != "unknown"
  assert prev_strand_donors.size() == prev_strand_acceptors.size()
  assert curr_strand_donors.size() == curr_strand_acceptors.size()
  start_bonding = False
  bonds = []
  n_prev_strand = prev_strand_donors.size()
  n_curr_strand = curr_strand_donors.size()
  i = j = None
  for k, donor_i_seq in enumerate(prev_strand_donors) :
    if donor_i_seq == prev_strand_start :
      i = k
      break
  #print curr_strand_start, curr_strand_acceptors
  for k, acceptor_i_seq in enumerate(curr_strand_acceptors) :
    if acceptor_i_seq == curr_strand_start :
      j = k
      break
  if None in [i, j] :
    return None
  if sense == "antiparallel" :
    while (i < n_prev_strand) and (j > 0) :
      donor1_i_seq = prev_strand_donors[i]
      acceptor1_i_seq = curr_strand_acceptors[j]
      labels1 = atoms[donor1_i_seq].fetch_labels()
      if ((donor1_i_seq != n_atoms) and (labels1.resname.strip() != "PRO")) :
        bonds.append((donor1_i_seq, acceptor1_i_seq))
      donor2_i_seq = curr_strand_donors[j]
      acceptor2_i_seq = prev_strand_acceptors[i]
      labels2 = atoms[donor2_i_seq].fetch_labels()
      if ((donor2_i_seq != n_atoms) and (labels2.resname.strip() != "PRO")) :
        bonds.append((donor2_i_seq, acceptor2_i_seq))
      i += 2
      j -= 2
  else :
    while i < n_prev_strand and j < n_curr_strand :
      donor1_i_seq = prev_strand_donors[i]
      acceptor1_i_seq = curr_strand_acceptors[j]
      labels1 = atoms[donor1_i_seq].fetch_labels()
      if ((donor1_i_seq != n_atoms) and (labels1.resname.strip() != "PRO")) :
        bonds.append((donor1_i_seq, acceptor1_i_seq))
      if (j + 2) >= n_curr_strand :
        break
      donor2_i_seq = curr_strand_donors[j+2]
      acceptor2_i_seq = prev_strand_acceptors[i]
      labels2 = atoms[donor2_i_seq].fetch_labels()
      if ((donor2_i_seq != n_atoms) and (labels2.resname.strip() != "PRO")) :
        bonds.append((donor2_i_seq, acceptor2_i_seq))
      i += 2
      j += 2
  return bonds

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
    first_strand = __strand_group_as_pdb_strand(isel=isel,
      selection=sheet.first_strand,
      atoms=atoms,
      log=log,
      sense=None)
    current_sheet.add_strand(first_strand)
    current_sheet.add_registration(None)
    base_sele = "(%s) and name N and (altloc 'A' or altloc ' ')"
    for strand in sheet.strand :
      pdb_strand = __strand_group_as_pdb_strand(isel=isel,
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

def __strand_group_as_pdb_strand (isel, selection, atoms, log, sense) :
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
