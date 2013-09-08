
# FIXME: bifurcated sheets are just not handled at all right now
# FIXME: make sheet extraction much faster?  This would require moving the
# hbond and bridge classes to C++ (with accompanying scitbx.array_family
# types), which may be overkill.
# TODO: incorporate angle-dependence?
# TODO: test on entire PDB
#
# implementation of:
# Kabsch, W. & Sander, C. Dictionary of protein secondary structure: pattern
# recognition of hydrogen-bonded and geometrical features. Biopolymers 22,
# 2577-2637 (1983).
#

from __future__ import division
import libtbx.phil
from libtbx.utils import null_out
from libtbx import group_args, adopt_init_args
import cStringIO
import time
import sys

master_phil = libtbx.phil.parse("""
file_name = None
  .type = str
energy_cutoff = -0.5
  .type = float
distance_cutoff = 4.0
  .type = float
nh_bond_length = 1.01
  .type = float
verbosity = 0
  .type = int
pymol_script = None
  .type = path
""")

turn_start = 0 # XXX see comment below

class hbond (object) :
  def __init__ (self, residue1, residue2, energy) : # atom_group objects
    adopt_init_args(self, locals())
    self.i_res = residue1.atoms()[0].tmp
    self.j_res = residue2.atoms()[0].tmp
    self._i_res_offset = self.i_res + 2
    self._j_res_offset = self.j_res - 2
    self.within_chain = (residue1.parent().parent() ==
                         residue2.parent().parent())

  def show (self, out=None, prefix="") :
    if (out is None) : out = sys.stdout
    print >> out, "%s%s %s %s O --> %s %s %s N : %6.3f [%d,%d]" % (prefix,
      self.residue1.parent().parent().id,
      self.residue1.resname,
      self.residue1.parent().resid(),
      self.residue2.parent().parent().id,
      self.residue2.resname,
      self.residue2.parent().resid(),
      self.energy, self.i_res, self.j_res)

  def get_n_turn (self) :
    if (self.within_chain) :
      n_turn = self.j_res - self.i_res
      if (n_turn > 2) and (n_turn < 6) :
        return n_turn
    return None

  def is_same_chain (self, other) :
    if (other is None) : return False
    return self.residue1.parent().parent() == other.residue1.parent().parent()

  def as_pymol_cmd (self) :
    sel_fmt = "chain '%s' and resi %s and name %s"
    sel1 = sel_fmt % (self.residue1.parent().parent().id.strip(),
                      self.residue1.parent().resid(), "O")
    sel2 = sel_fmt % (self.residue2.parent().parent().id.strip(),
                      self.residue2.parent().resid(), "N")
    return "dist (%s), (%s)" % (sel1, sel2)

  def is_in_ladder (self, i_res_start, i_res_end, j_res_start, j_res_end) :
    if (((self.i_res >= i_res_start) and (self.i_res <= i_res_end) and
         (self.j_res >= j_res_start) and (self.j_res <= j_res_end)) or
        ((self.i_res >= j_res_start) and (self.i_res <= j_res_end) and
         (self.j_res >= i_res_start) and (self.j_res <= i_res_end))) :
      return True
    return False

  def is_bridge (self, other) :
    if (((other.j_res == self.i_res) and
         (other.i_res == self._j_res_offset)) or
        ((other.i_res == self.j_res) and
         (other.j_res == self._i_res_offset))) :
      return 1 # parallel
    elif (((other.i_res == self.j_res) and (other.j_res == self.i_res)) or
          ((other.i_res == self._j_res_offset) and
           (other.j_res == self._i_res_offset))) :
      return -1 # antiparallel
    return 0

class bridge (object) :
  def __init__ (self, hbond1, hbond2, direction, i_res=None, j_res=None) :
    adopt_init_args(self, locals())
    assert ([i_res,j_res].count(None) in [0,2])
    if (i_res is None) :
      if (direction == 1) :
        if (hbond1.i_res == hbond2.j_res) :
          i_res = hbond1.i_res
          j_res = hbond1.j_res - 1
        else :
          assert (hbond1.j_res == hbond2.i_res)
          i_res = hbond1.i_res + 1
          j_res = hbond1.j_res
      else :
        if (hbond1.i_res == hbond2.j_res) :
          i_res = hbond1.i_res
          j_res = hbond2.i_res
        else :
          i_res = hbond1.i_res + 1
          j_res = hbond2.i_res + 1
      self.i_res = min(i_res, j_res)
      self.j_res = max(i_res, j_res)

  def invert (self) :
    return bridge(
      hbond1=self.hbond2,
      hbond2=self.hbond1,
      direction=self.direction,
      i_res=self.j_res,
      j_res=self.i_res)

  def show (self, out=None, prefix="", show_direction=True) :
    if (out is None) : out = sys.stdout
    direction = ""
    if (show_direction) :
      if (self.direction == 1) :
        direction = " (parallel)"
      else :
        direction = " (antiparallel)"
    print >> out, "%sBridge%s [%d,%d]:" % (prefix, direction, self.i_res,
      self.j_res)
    self.hbond1.show(out=out, prefix=prefix+"  ")
    self.hbond2.show(out=out, prefix=prefix+"  ")

class ladder (object) :
  def __init__ (self) :
    self.bridges = []
    self.bridge_i_res = []
    self.direction = None

  def add_bridge (self, b) :
    if (self.direction is None) :
      self.direction = b.direction
    else :
      assert (self.direction == b.direction)
    if (not (b.i_res,b.j_res) in self.bridge_i_res) :
      self.bridges.append(b)
      self.bridge_i_res.append((b.i_res, b.j_res))

  def show (self, out=None, prefix="") :
    if (out is None) : out = sys.stdout
    if (self.direction == 1) :
      direction = "parallel"
    else :
      direction = "antiparallel"
    print >> out, "%sLadder (%s):" % (prefix, direction)
    for bridge in self.bridges :
      bridge.show(out, prefix=prefix+"  ", show_direction=False)

  def get_initial_strand (self, sheet_id, pdb_labels) :
    from iotbx.pdb import secondary_structure
    start_i_res = min(self.bridges[0].i_res, self.bridges[-1].i_res)
    end_i_res = max(self.bridges[0].i_res, self.bridges[-1].i_res)
    start = pdb_labels[start_i_res]
    end = pdb_labels[end_i_res]
    first_strand = secondary_structure.pdb_strand(
      sheet_id=sheet_id,
      strand_id=1,
      start_resname=start.resname,
      start_chain_id=start.chain_id,
      start_resseq=start.resseq,
      start_icode=start.icode,
      end_resname=end.resname,
      end_chain_id=end.chain_id,
      end_resseq=end.resseq,
      end_icode=end.icode,
      sense=0)
    return first_strand

  def get_next_strand (self, sheet_id, strand_id, pdb_labels,
      next_ladder=None) :
    from iotbx.pdb import secondary_structure
    start_i_res = end_i_res = None
    next_ladder_i_start = sys.maxint
    next_ladder_i_end = - sys.maxint
    if (next_ladder is not None) :
      next_ladder_i_start = min(next_ladder.bridges[0].i_res,
                                next_ladder.bridges[-1].i_res)
      next_ladder_i_end = max(next_ladder.bridges[-1].i_res,
                              next_ladder.bridges[0].i_res)
    j_res_start = min(self.bridges[0].j_res, self.bridges[-1].j_res)
    j_res_end = max(self.bridges[-1].j_res, self.bridges[0].j_res)
    start_i_res = min(j_res_start, next_ladder_i_start)
    end_i_res = max(j_res_end, next_ladder_i_end)
    if (start_i_res > end_i_res) :
      out = cStringIO.StringIO()
      self.show(out=out)
      raise RuntimeError("start_i_res(%d) > end_i_res(%d):\n%s" %
        (start_i_res, end_i_res, out.getvalue()))
    start = pdb_labels[start_i_res]
    end = pdb_labels[end_i_res]
    strand = secondary_structure.pdb_strand(
      sheet_id=sheet_id,
      strand_id=strand_id,
      start_resname=start.resname,
      start_chain_id=start.chain_id,
      start_resseq=start.resseq,
      start_icode=start.icode,
      end_resname=end.resname,
      end_chain_id=end.chain_id,
      end_resseq=end.resseq,
      end_icode=end.icode,
      sense=self.direction)
    return strand

  def get_strand_register (self, hbonds, pdb_labels, is_last_strand=False) :
    from iotbx.pdb import secondary_structure
    i_res_start = min(self.bridges[0].i_res, self.bridges[-1].i_res)
    i_res_end = max(self.bridges[0].i_res, self.bridges[-1].i_res)
    j_res_start = min(self.bridges[0].j_res, self.bridges[-1].j_res)
    j_res_end = max(self.bridges[0].j_res, self.bridges[-1].j_res)
    start_hbond = None
    start_on_n = False
    min_i_res = sys.maxint
    # XXX this is incorrect - it is not picking the first possible H-bond
    for hbond in hbonds :
      if (hbond.is_in_ladder(i_res_start,i_res_end,j_res_start,j_res_end)) :
        if ((hbond.i_res < min_i_res) and (hbond.i_res >= i_res_start) and
            (hbond.i_res <= i_res_end)) : # O atom
          start_hbond = hbond
          min_i_res = hbond.i_res
          start_on_n = False
        if ((hbond.j_res <= min_i_res) and (hbond.j_res >= i_res_start) and
            (hbond.j_res <= i_res_end)) : # N atom (takes precedence)
          start_hbond = hbond
          min_i_res = hbond.j_res
          start_on_n = True
    if (start_hbond is None) :
      out = cStringIO.StringIO()
      self.show(out=out)
      return None
      raise RuntimeError("Can't find start of H-bonding:\n%s" % out.getvalue())
    if (start_on_n) :
      curr_atom = " N  "
      prev_atom = " O  "
      curr_res = pdb_labels[start_hbond.i_res]
      prev_res = pdb_labels[start_hbond.j_res]
    else :
      curr_atom = " O  "
      prev_atom = " N  "
      curr_res = pdb_labels[start_hbond.j_res]
      prev_res = pdb_labels[start_hbond.i_res]
    #start_hbond.show()
    return secondary_structure.pdb_strand_register(
      cur_atom=curr_atom,
      cur_resname=curr_res.resname,
      cur_chain_id=curr_res.chain_id,
      cur_resseq=curr_res.resseq,
      cur_icode=curr_res.icode,
      prev_atom=prev_atom,
      prev_resname=prev_res.resname,
      prev_chain_id=prev_res.chain_id,
      prev_resseq=prev_res.resseq,
      prev_icode=prev_res.icode)

def get_pdb_fields (atom_group) :
  residue_group = atom_group.parent()
  chain = residue_group.parent()
  return group_args(
    resname=atom_group.resname,
    chain_id=chain.id,
    resseq=residue_group.resseq_as_int(),
    icode=residue_group.icode)

class dssp (object) :
  def __init__ (self,
          pdb_hierarchy,
          xray_structure=None,
          pdb_atoms=None,
          params=None,
          out=None,
          log=None) :
    if (out is None) : out = sys.stdout
    if (log is None) : log = null_out()
    if (params is None) : params = master_phil.extract()
    if (pdb_atoms is None) : pdb_atoms = pdb_hierarchy.atoms()
    if (xray_structure is None) :
      xray_structure = pdb_hierarchy.extract_xray_structure()
    self.hbonds = []
    self.pdb_hierarchy = pdb_hierarchy
    self.pdb_atoms = pdb_atoms
    self.params = params
    self.log = log
    t1 = time.time()
    assert (not pdb_atoms.extract_i_seq().all_eq(0))
    unit_cell = xray_structure.unit_cell()
    pair_asu_table = xray_structure.pair_asu_table(
      distance_cutoff=params.distance_cutoff)
    asu_mappings = pair_asu_table.asu_mappings()
    self.asu_table = pair_asu_table.table()
    self.pdb_labels = []
    # first mark atoms in each residue with position in sequence
    k = 0
    for chain in pdb_hierarchy.only_model().chains() :
      last_resseq = None
      for residue_group in chain.residue_groups() :
        resseq = residue_group.resseq_as_int()
        if (last_resseq is not None) and ((resseq - last_resseq) > 1) :
          self.pdb_labels.append(None)
          k += 1 # extra increment to handle probable chain breaks
        last_resseq = resseq
        atom_group = residue_group.atom_groups()[0]
        self.pdb_labels.append(get_pdb_fields(atom_group))
        for atom in atom_group.atoms() :
          #if (atom.name.strip() in ["N","C","O"]) :
          atom.tmp = k
        k += 1
    # now iterate over backbone O atoms and look for H-bonds
    # XXX this loop takes up most of the runtime
    t1 = time.time()
    t_process = 0
    t_find = 0
    for chain in pdb_hierarchy.only_model().chains() :
      if (not chain.is_protein()) :
        continue
      for residue_group in chain.residue_groups() :
        atom_group = residue_group.atom_groups()[0]
        ag_atoms = atom_group.atoms()
        for atom in ag_atoms :
          if (atom.name == " O  ") :
            tf0 = time.time()
            n_atoms = self.find_nearby_backbone_n(atom)
            t_find += time.time() - tf0
            tp0 = time.time()
            for n_atom in n_atoms :
              hbond = self.process_o_n_interaction(atom, n_atom)
              if (hbond is not None) :
                self.hbonds.append(hbond)
            t_process += time.time() - tp0
            break
    t2 = time.time()
    if (self.params.verbosity >= 1) :
      print >> log, "Time to find H-bonds: %.3f" % (t2 - t1)
      print >> log, "  local atom detection: %.3f" % t_find
      print >> log, "  analysis: %.3f" % t_process
    if (self.params.verbosity >= 2) :
      print >> log, "All hydrogen bonds:"
      for hbond in self.hbonds :
        hbond.show(log, prefix="  ")
    if (self.params.pymol_script is not None) :
      self._pml = open(self.params.pymol_script, "w")
    else :
      self._pml = null_out()
    t1 = time.time()
    self.helices = self.find_helices()
    t2 = time.time()
    if (self.params.verbosity >= 1) :
      print >> log, "Time to find helices: %.3f" % (t2 - t1)
    self.sheets = self.find_sheets()
    t3 = time.time()
    if (self.params.verbosity >= 1) :
      print >> log, "Time to find sheets: %.3f" % (t3 - t2)
    self.show(out=out)
    self._pml.close()
    self.log = None

  def show (self, out=None) :
    if (out is None) : out = sys.stdout
    for helix in self.helices :
      print >> out, helix.as_pdb_str()
    for sheet in self.sheets :
      print >> out, sheet.as_pdb_str()

  def get_annotation (self) :
    from iotbx.pdb import secondary_structure
    return secondary_structure.annotation(
      helices=self.helices,
      sheets=self.sheets)

  def find_nearby_backbone_n (self, o_atom) :
    from scitbx.matrix import col
    n_atoms = []
    asu_dict = self.asu_table[o_atom.i_seq]
    for j_seq, j_sym_groups in asu_dict.items() :
      other = self.pdb_atoms[j_seq]
      if (other.name.strip() == "N") :
        n_atom = other
        n_atom_group = n_atom.parent()
        if (n_atom_group.resname == "PRO") :
          continue
        o_chain = o_atom.parent().parent().parent()
        other_chain = n_atom.parent().parent().parent()
        o_resseq = o_atom.parent().parent().resseq_as_int()
        n_resseq = n_atom_group.parent().resseq_as_int()
        # filter out supposed H-bonds between residues very close in sequence;
        # have to rely on the resseq being realistic here...
        if (o_chain == other_chain) and (abs(n_resseq - o_resseq) < 3) :
          continue
        dxyz = abs(col(n_atom.xyz) - col(o_atom.xyz))
        if (dxyz > self.params.distance_cutoff) :
          continue
        n_atoms.append(n_atom)
    return n_atoms

  def process_o_n_interaction (self, o_atom, n_atom) :
    import boost.python
    ext = boost.python.import_ext("mmtbx_dssp_ext")
    energy = ext.get_o_n_hbond_energy(O=o_atom, N=n_atom)
    # TODO incorporate angle filtering - need to ask Jane and/or look at
    # Reduce source code for ideas
    #angle = hbond_base_angle(
    #  c_xyz=c_xyz,
    #  h_xyz=h_xyz,
    #  o_xyz=col(o_atom.xyz),
    #  n_xyz=col(n_atom.xyz))
    if (energy is not None) and (energy < self.params.energy_cutoff) :
      return hbond(residue1=o_atom.parent(),
                   residue2=n_atom.parent(),
                   energy=energy)
    return None

  def find_helices (self) :
    from iotbx.pdb import secondary_structure
    turns = []
    i_prev = j_prev = -sys.maxint
    current_turn = []
    prev_n_turn = None
    prev_hbond = None
    for hb in self.hbonds :
      n_turn = hb.get_n_turn()
      if (n_turn is not None) :
        if ((not hb.is_same_chain(prev_hbond)) or
            (n_turn != prev_n_turn) or
            (hb.i_res != i_prev + 1)) :
          if (len(current_turn) > 0) :
            turns.append(current_turn)
          current_turn = [hb]
        else :
          current_turn.append(hb)
        i_prev = hb.i_res
        prev_n_turn = n_turn
        prev_hbond = hb
    if (len(current_turn) > 0) :
      turns.append(current_turn)
    if (self.params.verbosity >= 1) :
      print >> self.log, "%d basic turns" % len(turns)
    helices = []
    helix_classes = { 4:1, 5:3, 3:5 } # alpha, 3_10, pi
    ignore_previous = False
    prev_turn = None
    for k, turn in enumerate(turns) :
      n_turn = turn[0].get_n_turn()
      if (len(turn) < 2) : #and (n_turn != 3) :
        prev_turn = None # ignore when processing next turn
        continue
      if (prev_turn is not None) :
        # XXX if previous turn overlaps with this one (and was not discarded),
        # skip to next.  I'm not actually sure this is correct...
        last_hbond_prev_turn = prev_turn[-1]
        first_hbond_curr_turn = turn[0]
        if ((first_hbond_curr_turn.is_same_chain(last_hbond_prev_turn)) and
            (first_hbond_curr_turn.i_res < last_hbond_prev_turn.j_res)) :
          prev_turn = None
          continue
      # XXX in Kabsch & Sander, the helix officially starts at the
      # second turn.  This appears to be consistent with ksdssp, but not with
      # the HELIX records in the PDB.  I am inclined to follow the latter
      # since we will miss valid H-bonds otherwise.  Need to ask Jane.
      start = get_pdb_fields(turn[turn_start].residue1)
      end = get_pdb_fields(turn[-1].residue2)
      helix = secondary_structure.pdb_helix(
        serial=k+1,
        helix_id=k+1,
        start_resname=start.resname,
        start_chain_id=start.chain_id,
        start_resseq=start.resseq,
        start_icode=start.icode,
        end_resname=end.resname,
        end_chain_id=end.chain_id,
        end_resseq=end.resseq,
        end_icode=end.icode,
        helix_class=helix_classes[n_turn],
        comment="",
        length=end.resseq-start.resseq+1) # XXX is this safe?
      helices.append(helix)
      prev_turn = turn
      for hb in turn[turn_start:] :
        print >> self._pml, hb.as_pymol_cmd()
    return helices

  def find_sheets (self) : # FIXME very slow!
    from iotbx.pdb import secondary_structure
    i_max = len(self.hbonds) - 1
    # first collect bridges
    # XXX this is the slow step
    bridges = []
    for k, hbond1 in enumerate(self.hbonds) :
      for hbond2 in self.hbonds[k+1:] :
        is_bridge = hbond1.is_bridge(hbond2)
        if (is_bridge != 0) :
          B = bridge(hbond1, hbond2, is_bridge)
          bridges.append(B)
    bridges.sort(lambda a,b: cmp(a.i_res, b.i_res))
    if (self.params.verbosity >= 2) :
      for B in bridges :
        B.show(out=self.log)
    # now collect indices of all residues involved in bridges, and identify
    # continuous segments (i.e. strands)
    all_i_res = set([ B.i_res for B in bridges ])
    all_j_res = set([ B.j_res for B in bridges ])
    all_indices = sorted(list(all_i_res.union(all_j_res)))
    strands = []
    curr_strand = []
    prev_i_res = -sys.maxint
    for i_res in all_indices :
      if (i_res == prev_i_res + 1) :
        curr_strand.append(i_res)
      else :
        if (len(curr_strand) > 1) :
          strands.append(curr_strand)
        curr_strand = [i_res]
      prev_i_res = i_res
    if (len(curr_strand) > 0) :
      strands.append(curr_strand)
    # figure out which strands are connected by bridges
    connections = []
    n_connected = 0
    for u, strand in enumerate(strands) :
      linked = set([])
      for i_res in strand :
        for B in bridges :
          other_i_res = None
          if (B.i_res == i_res) :
            other_i_res = B.j_res
          elif (B.j_res == i_res) :
            other_i_res = B.i_res
          if (other_i_res is not None) :
            for v, other_strand in enumerate(strands) :
              if (u == v) :
                continue
              elif (other_i_res in other_strand) :
                #print i_res, u, other_i_res, v
                linked.add(v)
                break
      #assert (len(linked) in [1,2])
      # FIXME why does this happen?  maybe bifurcated sheets?
      if (len(linked) > 0) :
        n_connected += 1
      connections.append(linked)
    # now sort the bridges into ladders based on the strand connections
    all_sheet_ladders = []
    sheet_ladders = []
    n_processed = 0
    # FIXME this is not working properly for bifurcated sheets and possibly
    # other corner cases as well
    # XXX actually, the real problem is that it's just not very smart about
    # which path to follow - ideally it should try to maximize both the sheet
    # size (at the expense of smaller sheets), both in number of strands and
    # total number of residues.  Currently it will pick the longest strand
    # where multiple are possible, which is not necessarily the best choice.
    # XXX it also needs to be smarter about where to start!
    n_left_last = -sys.maxint
    start_on_next_strand = False
    #print connections
    while (n_processed < n_connected) :
      u = 0
      n_left = 0
      while (u < len(connections)) :
        linked = connections[u]
        if (len(linked) == 1) or (start_on_next_strand) :
          L = ladder()
          strand = strands[u]
          max_connecting_strand_length = 0
          best_strand_index = v = None
          if (len(linked) > 1) :
            # multiple strands linked, so pick the longest one
            for v_ in sorted(linked) :
              other_ = strands[v_]
              if (len(other_) > max_connecting_strand_length) :
                best_strand_index = v_
                max_connecting_strand_length = len(other_)
            assert (best_strand_index is not None)
            v = best_strand_index
            linked.remove(v)
          else :
            v = linked.pop()
          assert (v is not None)
          other_strand = strands[v]
          for i_res in strand :
            for B in bridges :
              if ((B.j_res in strand) and (B.i_res in other_strand)) :
                L.add_bridge(B.invert())
              elif ((B.i_res in strand) and (B.j_res in other_strand)) :
                L.add_bridge(B)
          sheet_ladders.append(L)
          next_linked = connections[v]
          start_on_next_strand = True
          next_linked.remove(u)
          n_processed += 1
          u = v
          if (len(next_linked) == 0) :
            all_sheet_ladders.append(sheet_ladders)
            sheet_ladders = []
            n_processed += 1
            start_on_next_strand = False
            break
        else :
          u += 1
          n_left += 1
      if (n_left == n_left_last) :
        # XXX this means that the last loop did not process any connections,
        # because there are no strands with only a single connection.  this
        # could mean a beta barrel - any other explanations?
        start_on_next_strand = True
        u = 0
      n_left_last = n_left
    # convert collections of ladders into SHEET objects
    sheets = []
    for k, ladders in enumerate(all_sheet_ladders) :
      if (self.params.verbosity >= 2) :
        print >> self.log, "SHEET:"
        for L in ladders :
          L.show(self.log, prefix="  ")
      sheet_id = k+1
      current_sheet = secondary_structure.pdb_sheet(
        sheet_id=sheet_id,
        n_strands=len(ladders)+1,
        strands=[],
        registrations=[])
      first_strand = ladders[0].get_initial_strand(sheet_id, self.pdb_labels)
      current_sheet.add_strand(first_strand)
      current_sheet.add_registration(None)
      sheets.append(current_sheet)
      for i_ladder, L in enumerate(ladders) :
        next_ladder = None
        if (i_ladder < len(ladders) - 1) :
          next_ladder = ladders[i_ladder+1]
        next_strand = L.get_next_strand(
          sheet_id=sheet_id,
          strand_id=i_ladder+2,
          pdb_labels=self.pdb_labels,
          next_ladder=next_ladder)
        register = L.get_strand_register(
          hbonds=self.hbonds,
          pdb_labels=self.pdb_labels,
          is_last_strand=(next_ladder is None))
        if (register is None) : break
        current_sheet.add_strand(next_strand)
        current_sheet.add_registration(register)
    return sheets
