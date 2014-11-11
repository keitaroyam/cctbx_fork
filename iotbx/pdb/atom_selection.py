
"""
Tools for creating atom selection arrays (flex.bool or flex.size_t) based on
a simple keyword syntax and boolean operators.
"""

from __future__ import division
from iotbx import simple_parser
from iotbx import wildcard
from cctbx import crystal
from scitbx.array_family import flex
from scitbx import stl
import scitbx.stl.map
from libtbx.phil import tokenizer
from libtbx.utils import Sorry, format_exception
from libtbx import slots_getstate_setstate
from mmtbx.ncs.ncs_search import get_chains_info

def _character_case_id(strings):
  have_upper = False
  have_lower = False
  for s in strings:
    for c in s:
      if   (c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        if (have_lower): return 0
        have_upper = True
      elif (c in "abcdefghijklmnopqrstuvwxyz"):
        if (have_upper): return 0
        have_lower = True
  if (have_upper): return 1
  if (have_lower): return -1
  return 0

def _get_map_string(
      map,
      pattern,
      wildcard_escape_char='\\',
      unconditionally_case_insensitive=True):
  pattern_was_quoted = True
  if (not isinstance(pattern, str)):
    if (pattern.quote_token is None):
      pattern_was_quoted = False
    pattern = pattern.value
    if (not pattern_was_quoted): pattern = pattern.strip()
    if (unconditionally_case_insensitive): pattern = pattern.upper()
  result = []
  def match():
    for key,value in map.items():
      if (not pattern_was_quoted): key = key.strip()
      if (unconditionally_case_insensitive): key = key.upper()
      if (wildcard.is_match(
            string=key,
            pattern=pattern,
            escape_char=wildcard_escape_char)):
        result.append(value)
  match()
  if (    len(result) == 0
      and not pattern_was_quoted
      and not unconditionally_case_insensitive
      and _character_case_id(strings=[pattern]) != 0):
    keys_case_id = _character_case_id(strings=map.keys())
    if (keys_case_id != 0):
      if (keys_case_id > 0):
        pattern = pattern.upper()
      else:
        pattern = pattern.lower()
      match()
  return result

def _get_serial_range(sel_keyword, map, start, stop):
  from iotbx.pdb import utils_base_256_ordinal as o
  o_start = None
  o_stop = None
  if (start is not None and start.count(" ") != len(start)):
    o_start = o(start)
  if (stop is not None and stop.count(" ") != len(stop)):
    o_stop = o(stop)
  if (    o_start is not None
      and o_stop is not None
      and o_start > o_stop):
    raise RuntimeError(
      "range with first index > last index: %s %s:%s" % (
        sel_keyword, start, stop))
  result = []
  for s,iselection in map.items():
    os = o(s)
    if (o_start is not None and os < o_start): continue
    if (o_stop  is not None and os > o_stop): continue
    result.append(iselection)
  return result

class selection_tokenizer(tokenizer.word_iterator):

  def __init__(self, string, contiguous_word_characters=None):
    if (contiguous_word_characters is None):
      contiguous_word_characters \
        = tokenizer.default_contiguous_word_characters \
        + r"\*?[]^+-.:"
    tokenizer.word_iterator.__init__(self,
      input_string=string,
      list_of_settings=[tokenizer.settings(
        contiguous_word_characters=contiguous_word_characters)])

  def pop_argument(self, keyword):
    word = self.try_pop()
    if (word is None): raise RuntimeError("Missing argument for %s." % keyword)
    return word

def resid_shift(s):
  if (len(s) < 5 and s[-1] in "0123456789"): return s + " "
  return s

class AtomSelectionError(Sorry):
  __orig_module__ = __module__
  __module__ = "exceptions"

class cache(slots_getstate_setstate):
  """
  Manager for interpreting atom selection strings, with caching of partial
  selections.  This has some limited understanding of chemical identities via
  keywords like pepnames, water, or single_atom_residue, but more advanced
  selections require the use of a callback.  In practice this would usually
  involve wrapping the cache in another object, for example the class
  build_all_chain_proxies in mmtbx.monomer_library.pdb_interpretation.

  Because the selections available here are used in some situations where setup
  speed is important, the "within" keyword may optionally be supported if the
  special_position_settings attribute is not None.
  """

  __slots__ = [
    "root",
    "wildcard_escape_char",
    "n_seq",
    "name",
    "altloc",
    "resname",
    "chain_id",
    "resseq",
    "icode",
    "resid",
    "resid_list",
    "chain_break_list",
    "segid",
    "model_id",
    "element",
    "charge",
    "anisou",
    "pepnames",
    "single_atom_residue",
    "water",
    "hetero",
    "special_position_settings"]

  def __init__(self, root, wildcard_escape_char='\\',
      special_position_settings=None):
    self.root = root
    self.wildcard_escape_char = wildcard_escape_char
    root.get_atom_selection_cache(self)
    self.pepnames = None
    self.single_atom_residue = None
    self.water = None
    self.hetero = None
    self.special_position_settings = special_position_settings

  def get_name(self, pattern):
    return _get_map_string(
      map=self.name,
      pattern=pattern,
      wildcard_escape_char=self.wildcard_escape_char)

  def get_altloc(self, pattern):
    return _get_map_string(
      map=self.altloc,
      pattern=pattern,
      wildcard_escape_char=self.wildcard_escape_char)

  def get_resname(self, pattern):
    return _get_map_string(
      map=self.resname,
      pattern=pattern,
      wildcard_escape_char=self.wildcard_escape_char)

  def get_chain_id(self, pattern):
    return _get_map_string(
      map=self.chain_id,
      pattern=pattern,
      wildcard_escape_char=self.wildcard_escape_char,
      unconditionally_case_insensitive=False)

  def get_resseq(self, pattern):
    return _get_map_string(
      map=self.resseq,
      pattern=pattern,
      wildcard_escape_char=self.wildcard_escape_char)

  def get_resseq_range(self, start, stop):
    return _get_serial_range(
      sel_keyword="resseq", map=self.resseq, start=start, stop=stop)

  def get_icode(self, pattern):
    return _get_map_string(
      map=self.icode,
      pattern=pattern,
      wildcard_escape_char=self.wildcard_escape_char)

  def get_resid(self, pattern):
    return _get_map_string(
      map=self.resid,
      pattern=pattern,
      wildcard_escape_char=self.wildcard_escape_char)

  def get_resid_range(self, start, stop):
    from iotbx.pdb import utils_base_256_ordinal as o
    o_start = None
    o_stop = None
    if (start is not None and start.count(" ") != len(start)):
      o_start = o(resid_shift(start))
    if (stop is not None and stop.count(" ") != len(stop)):
      o_stop = o(resid_shift(stop))
    if (    o_start is not None
        and o_stop is not None
        and o_start > o_stop):
      raise RuntimeError(
        "range with first index > last index: resid %s:%s" % (start, stop))
    result = []
    for s,iselection in self.resid.items():
      os = o(s)
      if (o_start is not None and os < o_start): continue
      if (o_stop  is not None and os > o_stop): continue
      result.append(iselection)
    return result

  def get_resid_sequence (self, start, stop) :
    assert (not None in [start, stop])
    import iotbx.pdb.hierarchy
    result = iotbx.pdb.hierarchy.get_resid_sequence(
      resid_list=self.resid_list,
      chain_break_list=self.chain_break_list,
      start=resid_shift(start),
      stop=resid_shift(stop))
    return [result]

  def get_segid(self, pattern):
    return _get_map_string(
      map=self.segid,
      pattern=pattern,
      wildcard_escape_char=self.wildcard_escape_char)

  def get_model_id(self, pattern):
    return _get_map_string(
      map=self.model_id,
      pattern=pattern,
      wildcard_escape_char=self.wildcard_escape_char)

  def get_model_id_range(self, start, stop):
    return _get_serial_range(
      sel_keyword="model", map=self.model_id, start=start, stop=stop)

  def get_element(self, pattern):
    return _get_map_string(
      map=self.element,
      pattern=pattern,
      wildcard_escape_char=self.wildcard_escape_char)

  def get_charge(self, pattern):
    return _get_map_string(
      map=self.charge,
      pattern=pattern,
      wildcard_escape_char=self.wildcard_escape_char)

  def get_anisou(self):
    return [self.anisou]

  def get_water(self):
    if (self.water is None):
      import iotbx.pdb
      get_class = iotbx.pdb.common_residue_names_get_class
      atoms = self.root.atoms()
      sentinel = atoms.reset_tmp(first_value=0, increment=0)
      for model in self.root.models():
        for chain in model.chains():
          for conformer in chain.conformers():
            for residue in conformer.residues():
              if(get_class(name = residue.resname) == "common_water"):
                for atom in residue.atoms():
                  atom.tmp = 1
      self.water = (atoms.extract_tmp_as_size_t() == 1).iselection()
    return [self.water]

  def get_hetero (self) :
    if (self.hetero is None) :
      atoms = self.root.atoms()
      self.hetero = atoms.extract_hetero()
    return [self.hetero]

  def get_pepnames(self):
    if (self.pepnames is None):
      import iotbx.pdb
      get_class = iotbx.pdb.common_residue_names_get_class
      n_ca_c_o = set([" N  ", " CA ", " C  ", " O  "])
      atoms = self.root.atoms()
      sentinel = atoms.reset_tmp(first_value=0, increment=0)
      for model in self.root.models():
        for chain in model.chains():
          for conformer in chain.conformers():
            for residue in conformer.residues():
              if(get_class(name = residue.resname) == "common_amino_acid"):
                for atom in residue.atoms():
                  atom.tmp = 1
              elif(residue.resname.strip() != "CA"):
                ca = residue.find_atom_by(name=" CA ")
                if (ca is not None):
                  if (residue.atoms_size() == 1):
                    ca.tmp = 1
                  else:
                    residue_atoms = residue.atoms()
                    if (n_ca_c_o.issubset(set([atom.name
                          for atom in residue_atoms]))):
                      for atom in residue_atoms:
                        atom.tmp = 1
      self.pepnames = (atoms.extract_tmp_as_size_t() == 1).iselection()
    return [self.pepnames]

  def get_single_atom_residue(self):
    if (self.single_atom_residue is None):
      atoms = self.root.atoms()
      sentinel = atoms.reset_tmp(first_value=0, increment=0)
      for model in self.root.models():
        for chain in model.chains():
          for rg in chain.residue_groups():
            for cf in rg.conformers():
              for res in cf.residues():
                if (res.atoms_size() == 1):
                  res.atoms()[0].tmp = 1
      self.single_atom_residue = (
        atoms.extract_tmp_as_size_t() == 1).iselection()
    return [self.single_atom_residue]

  def get_bfactor (self, op, value) :
    assert (op in [">", "<", "="])
    atoms = self.root.atoms()
    b_iso = atoms.extract_b()
    selection = None
    if (op == ">") :
      selection = b_iso > value
    elif (op == "<") :
      selection = b_iso < value
    elif (op == "=") :
      selection = b_iso == value
    return [ selection.iselection() ]

  def get_occupancy (self, op, value) :
    assert (op in [">", "<", "="])
    atoms = self.root.atoms()
    occ = atoms.extract_occ()
    selection = None
    if (op == ">") :
      selection = occ > value
    elif (op == "<") :
      selection = occ < value
    elif (op == "=") :
      selection = occ == value
    return [ selection.iselection() ]

  def union(self, iselections):
    return flex.union(
      size=self.n_seq,
      iselections=iselections)

  def intersection(self, iselections):
    return flex.intersection(
      size=self.n_seq,
      iselections=iselections)

  def sel_name(self, pattern):
    return self.union(iselections=self.get_name(pattern=pattern))

  def sel_altloc(self, pattern):
    return self.union(iselections=self.get_altloc(pattern=pattern))

  def sel_resname(self, pattern):
    return self.union(iselections=self.get_resname(pattern=pattern))

  def sel_chain_id(self, pattern):
    return self.union(iselections=self.get_chain_id(pattern=pattern))

  def sel_resseq(self, pattern):
    return self.union(iselections=self.get_resseq(pattern=pattern))

  def sel_resseq_range(self, start, stop):
    return self.union(iselections=self.get_resseq_range(start=start,stop=stop))

  def sel_icode(self, pattern):
    return self.union(iselections=self.get_icode(pattern=pattern))

  def sel_resid(self, pattern):
    return self.union(iselections=self.get_resid(pattern=pattern))

  def sel_resid_range(self, start, stop):
    return self.union(iselections=self.get_resid_range(start=start,stop=stop))

  def sel_resid_sequence(self, start, stop) :
    return self.union(iselections=self.get_resid_sequence(start=start,
      stop=stop))

  def sel_segid(self, pattern):
    return self.union(iselections=self.get_segid(pattern=pattern))

  def sel_model_id(self, pattern):
    return self.union(iselections=self.get_model_id(pattern=pattern))

  def sel_model_id_range(self, start, stop):
    return self.union(iselections=self.get_model_id_range(
      start=start,stop=stop))

  def sel_element(self, pattern):
    return self.union(iselections=self.get_element(pattern=pattern))

  def sel_charge(self, pattern):
    return self.union(iselections=self.get_charge(pattern=pattern))

  def sel_anisou(self):
    return self.union(iselections=self.get_anisou())

  def sel_pepnames(self):
    return self.union(iselections=self.get_pepnames())

  def sel_single_atom_residue(self):
    return self.union(iselections=self.get_single_atom_residue())

  def sel_water(self):
    return self.union(iselections=self.get_water())

  def sel_hetero(self):
    return self.union(iselections=self.get_hetero())

  def sel_bfactor (self, op, value) :
    return self.union(iselections=self.get_bfactor(op, value))

  def sel_occupancy (self, op, value) :
    return self.union(iselections=self.get_occupancy(op, value))

  def sel_within(self, radius, primary_selection):
    assert radius > 0
    assert self.special_position_settings is not None
    return crystal.neighbors_fast_pair_generator(
      asu_mappings=self.special_position_settings.asu_mappings(
        buffer_thickness=radius,
        sites_cart=self.root.atoms().extract_xyz()),
      distance_cutoff=radius).neighbors_of(
        primary_selection=primary_selection)

  def selection_tokenizer(self, string, contiguous_word_characters=None):
    return selection_tokenizer(string, contiguous_word_characters)

  def selection_parser(self,
        word_iterator,
        optional=True,
        callback=None,
        stop_word=None,
        expect_nonmatching_closing_parenthesis=False):
    have_optional = False
    result_stack = []
    for word,word_iterator in simple_parser.infix_as_postfix(
          word_iterator=word_iterator,
          stop_word=stop_word,
          expect_nonmatching_closing_parenthesis
            =expect_nonmatching_closing_parenthesis):
      lword = word.value.lower()
      def raise_syntax_error():
        if (lword in ["peptide", "protein"]):
          raise Sorry(
            '"%s" atom selection keyword not available:\n'
            '  Please try using "pepnames" instead.' % lword)
        raise RuntimeError(
          'Atom selection syntax error at word "%s".' % lword)
      if (lword == "optional"):
        if (len(result_stack) != 0):
          raise Sorry('"optional" can appear only at the beginning.')
        if (have_optional):
          raise Sorry('"optional" can appear only once.')
        have_optional = True
      elif (lword == "not"):
        assert len(result_stack) >= 1
        arg = result_stack.pop()
        result_stack.append(~arg)
      elif (lword in ["and", "or"]):
        assert len(result_stack) >= 2
        rhs = result_stack.pop()
        lhs = result_stack.pop()
        if (lword == "and"):
          result_stack.append(lhs & rhs)
        else:
          result_stack.append(lhs | rhs)
      else:
        if (lword == "all"):
          result_stack.append(flex.bool(self.n_seq, True))
        elif (lword == "none"):
          result_stack.append(flex.bool(self.n_seq, False))
        elif (lword == "name"):
          result_stack.append(
            self.sel_name(pattern=word_iterator.pop_argument(word.value)))
        elif (lword in ["altloc", "altid"]):
          result_stack.append(
            self.sel_altloc(pattern=word_iterator.pop_argument(word.value)))
        elif (lword == "resname"):
          result_stack.append(
            self.sel_resname(pattern=word_iterator.pop_argument(word.value)))
        elif (lword == "chain"):
          result_stack.append(
            self.sel_chain_id(pattern=word_iterator.pop_argument(word.value)))
        elif (lword in ["resseq", "resid", "resi", "model"]):
          arg = word_iterator.pop_argument(word.value)
          def try_compose_range():
            def is_cont():
              if (len(arg_cont.value) == 0): return False
              return ("0123456789".find(arg_cont.value[0]) >= 0)
            i_colon = arg.value.find(":")
            if (i_colon < 0):
              arg_cont = word_iterator.try_pop()
              if (arg_cont is None):
                return arg.value, -1
              if (not arg_cont.value.startswith(":")):
                word_iterator.backup()
                return arg.value, -1
              if (len(arg_cont.value) == 1):
                arg_cont = word_iterator.try_pop()
                if (arg_cont is None):
                  return arg.value+":", len(arg.value)
                if (not is_cont()):
                  word_iterator.backup()
                  return arg.value+":", len(arg.value)
                return arg.value+":"+arg_cont.value, len(arg.value)
              return arg.value+arg_cont.value, len(arg.value)
            elif (i_colon+1 == len(arg.value)):
              arg_cont = word_iterator.try_pop()
              if (arg_cont is not None):
                if (is_cont()):
                  return arg.value+arg_cont.value, i_colon
                word_iterator.backup()
            return arg.value, i_colon
          def try_compose_sequence () :
            arg_next = word_iterator.try_pop()
            if (arg_next is None) :
              word_iterator.backup()
              return None, None
            lnext = arg_next.value.lower()
            if (lnext == "through") :
              arg_final = word_iterator.pop_argument(arg_next.value)
              return arg.value, arg_final.value
            word_iterator.backup()
            return (None, None)
          val, i_colon = try_compose_range()
          if (i_colon < 0):
            if (lword == "resseq"):
              result_stack.append(self.sel_resseq(pattern=arg))
            elif (lword in ["resid", "resi"]):
              start, stop = try_compose_sequence()
              if (start is None) :
                result_stack.append(self.sel_resid(pattern=arg))
              else :
                result_stack.append(self.sel_resid_sequence(start=start,
                  stop=stop))
            else:
              result_stack.append(self.sel_model_id(pattern=arg))
          else:
            start = val[:i_colon]
            stop = val[i_colon+1:]
            if (lword == "resseq"):
              result_stack.append(
                self.sel_resseq_range(start=start, stop=stop))
            elif (lword in ["resid", "resi"]):
              result_stack.append(
                self.sel_resid_range(start=start, stop=stop))
            else:
              result_stack.append(
                self.sel_model_id_range(start=start, stop=stop))
        elif (lword == "icode"):
          result_stack.append(
            self.sel_icode(pattern=word_iterator.pop_argument(word.value)))
        elif (lword == "segid"):
          result_stack.append(
            self.sel_segid(pattern=word_iterator.pop_argument(word.value)))
        elif (lword == "element"):
          result_stack.append(
            self.sel_element(pattern=word_iterator.pop_argument(word.value)))
        elif (lword == "charge"):
          result_stack.append(
            self.sel_charge(pattern=word_iterator.pop_argument(word.value)))
        elif (lword == "anisou"):
          result_stack.append(self.sel_anisou())
        elif (lword == "pepnames"):
          result_stack.append(self.sel_pepnames())
        elif (lword == "single_atom_residue"):
          result_stack.append(self.sel_single_atom_residue())
        elif (lword == "water"):
          result_stack.append(self.sel_water())
        elif (lword == "hetero") or (lword == "hetatm") :
          result_stack.append(self.sel_hetero())
        elif (lword == "bfactor") or (lword == "occupancy") :
          op = word_iterator.pop_argument(word.value).value
          if (not op in [">", "<", "="]) :
            raise_syntax_error()
          else :
            arg_next = word_iterator.try_pop()
            lnext = arg_next.value
            try :
              val = float(lnext)
            except ValueError :
              raise_syntax_error()
            else :
              if (lword == "bfactor") :
                result_stack.append(self.sel_bfactor(op, val))
              else :
                result_stack.append(self.sel_occupancy(op, val))
        elif ((lword == "within") and
              (self.special_position_settings is not None)) :
          assert word_iterator.pop().value == "("
          radius = float(word_iterator.pop().value)
          assert word_iterator.pop().value == ","
          sel = self.selection_parser(
            word_iterator=word_iterator,
            callback=callback,
            expect_nonmatching_closing_parenthesis=True)
          result_stack.append(self.sel_within(radius=radius,
            primary_selection=sel))
        elif (callback is not None):
          if (not callback(
                    word=word,
                    word_iterator=word_iterator,
                    result_stack=result_stack)):
            raise_syntax_error()
        else:
          raise_syntax_error()
    if (optional): have_optional = False
    if (len(result_stack) == 0):
      if (have_optional): return None
      return flex.bool(self.n_seq, False)
    selection = result_stack[0]
    for result in result_stack[1:]:
      selection &= result
    if (have_optional and selection.all_eq(False)):
      return None
    return selection

  def selection(self,
        string,
        optional=True,
        contiguous_word_characters=None,
        callback=None):
    """
    Given a selection string, return the corresponding flex.bool selection
    of the same size as root.atoms().
    """
    try:
      return self.selection_parser(
        word_iterator=self.selection_tokenizer(
          string=string,
          contiguous_word_characters=contiguous_word_characters),
        optional=optional,
        callback=callback)
    except (AtomSelectionError, KeyboardInterrupt): raise
    except Exception:
      msg = format_exception().splitlines()
      msg.extend(["Atom selection string leading to error:\n  %s" % string])
      raise AtomSelectionError("\n".join(msg))

  def iselection(self, string, optional=True, contiguous_word_characters=None):
    """
    Given a selection string, return the corresponding flex.size_t array
    specifying atom indices.
    """
    result = self.selection(
      string=string,
      optional=optional,
      contiguous_word_characters=contiguous_word_characters)
    if (result is None):
      return None
    return result.iselection()

  def get_labels(self,
        name=None,
        altloc=None,
        resname=None,
        chain_id=None,
        resseq=None,
        icode=None,
        segid=None,
        model_id=None):
    result = []
    for arg,attr in [(name, self.name),
                     (altloc, self.altloc),
                     (resname, self.resname),
                     (chain_id, self.chain_id),
                     (resseq, self.resseq),
                     (icode, self.icode),
                     (segid, self.segid),
                     (model_id, self.model_id)]:
      if (arg is not None):
        isel = attr.get(arg, None)
        if (isel is not None): result.append(isel)
    return result

  def link_iselections(self, link_record):
    sel_null = stl.vector.unsigned()
    fs = flex.size_t
    return [
                    fs(self.name.get(link_record.name1, sel_null))
      .intersection(fs(self.altloc.get(link_record.altloc1, sel_null)))
      .intersection(fs(self.resname.get(link_record.resname1, sel_null)))
      .intersection(fs(self.chain_id.get(link_record.chain_id1, sel_null)))
      .intersection(fs(self.resseq.get(link_record.resseq1, sel_null)))
      .intersection(fs(self.icode.get(link_record.icode1, sel_null))),
                    fs(self.name.get(link_record.name2, sel_null))
      .intersection(fs(self.altloc.get(link_record.altloc2, sel_null)))
      .intersection(fs(self.resname.get(link_record.resname2, sel_null)))
      .intersection(fs(self.chain_id.get(link_record.chain_id2, sel_null)))
      .intersection(fs(self.resseq.get(link_record.resseq2, sel_null)))
      .intersection(fs(self.icode.get(link_record.icode2, sel_null)))]

def expand_selection_to_entire_atom_groups (selection, pdb_atoms) :
  assert not pdb_atoms.extract_i_seq().all_eq(0)
  selection_complete = flex.bool(pdb_atoms.size(), False)
  if (type(selection).__name__ == 'bool') :
    selection = selection.iselection()
  for i_seq in selection :
    atom_group = pdb_atoms[i_seq].parent()
    group_atoms = atom_group.atoms().extract_i_seq()
    selection_complete.set_selected(group_atoms, True)
  return selection_complete

def selection_string_from_selection(pdb_hierarchy_inp,
                                    selection,
                                    chains_info=None):
  """
  Convert a selection array to a selection string.
  The function tries to minimise the selection string as possible,
  using chain names, resseq ranges and when there is not other option
  residues IDs

  Limitations:
    When pdb_hierarchy_inp contains multiple confirmations, selection must
    not include residues with alternate locations.

  Args:
    pdb_hierarchy_inp : iotbx.pdb.hierarchy.input (or iotbx.pdb.hierarchy)
    selection (flex.bool or flex.size_t)
    chains_info : object containing
      chains (str): chain IDs OR selections string
      res_name (list of str): list of residues names
      resid (list of str): list of residues sequence number, resid
      atom_names (list of list of str): list of atoms in residues
      atom_selection (list of list of list of int): the location of atoms in ph
      chains_atom_number (list of int): list of number of atoms in each chain

  Returns:
    sel_str (str): atom selection string
  """
  # create a hierarchy from the selection
  if hasattr(pdb_hierarchy_inp,"hierarchy"):
    pdb_hierarchy_inp = pdb_hierarchy_inp.hierarchy
  # pdb_hierarchy_inp is a hierarchy
  if isinstance(selection,flex.bool): selection = selection.iselection(True)
  selection_set = set(selection)
  sel_list = []
  # using chains_info to improve performance
  if not chains_info:
    chains_info = get_chains_info(pdb_hierarchy_inp,exclude_water=False)
  chain_ids = sorted(chains_info)
  for ch_id in chain_ids:
    a_sel = {x for xi in chains_info[ch_id].atom_selection for x in xi}
    ch_sel = 'chain {}'.format(ch_id)
    test_set = a_sel.intersection(selection_set)
    if not test_set: continue
    # if there is water in chain, specify residues numbers
    water_present = (len(a_sel) != chains_info[ch_id].chains_atom_number)
    complete_ch_not_present = (test_set != a_sel) or water_present
    res_sel = []
    first_n = None
    pre_res_n = -10000
    no_altloc = chains_info[ch_id].no_altloc
    no_altloc_present = bool(no_altloc)
    # exclude residues with alternative locations
    complete_ch_not_present |= no_altloc_present
    if complete_ch_not_present:
      # collect continuous ranges of residues when possible
      res_len = len(chains_info[ch_id].resid)
      for i in xrange(res_len):
        # test that all atoms in residue are included in selection
        a_sel = set(chains_info[ch_id].atom_selection[i])
        test_set = a_sel.intersection(selection_set)
        if not test_set: continue
        if no_altloc_present and not no_altloc[i]: continue
        all_atoms_present = (test_set == a_sel)
        res_id = chains_info[ch_id].resid[i]
        # ensure that insertion are not included if shouldn't
        next_res_id = '0'
        if i < (res_len - 1):
          next_res_id = chains_info[ch_id].resid[i+1]
        try:
          # check that res_id is a number and not insertion residue
          res_num = int(res_id)
          # int will fail if the next residue is insertion
          int(next_res_id)
        except ValueError:
          # res_id is an insertion type residue
          res_num = -10000
        if all_atoms_present:
          if res_num != -10000:
            # normal case
            if pre_res_n == -10000:
              # start new range
              first_n = res_num
              pre_res_n = res_num
            elif res_num == (pre_res_n + 1):
              pre_res_n += 1
            else:
              res_seq = resseq_string(first_n,pre_res_n)
              res_sel.append(res_seq)
              first_n = res_num
              pre_res_n = res_num
          else:
            # insertion in sequence
            res_sel,first_n,pre_res_n =update_res_sel(res_sel,first_n,pre_res_n)
            res_sel.append('resid ' + res_id )
        else:
          # not all residue's atoms are in selection
          s = '(resid ' + res_id + ' and (name '
          res_sel,first_n,pre_res_n = update_res_sel(res_sel,first_n,pre_res_n)
          # get present atoms
          atom_names = chains_info[ch_id].atom_names[i]
          test_set = sorted(test_set)
          dx = test_set[0]
          selected_atoms = [atom_names[x-dx] for x in test_set]
          atom_str = ' or name '.join(selected_atoms)
          res_sel.append(s + atom_str + '))')
      res_sel,first_n,pre_res_n = update_res_sel(res_sel,first_n,pre_res_n)
    s = get_clean_selection_string(ch_sel,res_sel)
    sel_list.append(s)
  # add parenthesis what selection is more than just a chain
  s_l = []
  sel_list.sort()
  for s in sel_list:
    if len(s) > 8:
      s = '(' + s + ')'
    s_l.append(s)
  sel_str = ' or '.join(s_l)
  return sel_str

def get_clean_selection_string(ch_sel,res_selection):
  """
  Args:
    ch_sel (str): such as 'chain A'
    res_selection (list of str): such as ['resseq 1:10','resid 27c and name CA']

  Returns:
    s (str): such as 'chain A and (resseq 1:10 or (resid 27c and name CA))'
  """
  if res_selection:
    if len(res_selection) > 1:
      s = ch_sel + ' and (' + ' or '.join(res_selection) + ')'
    else:
      s = ch_sel + ' and ' + res_selection[0]
  else:
    s = ch_sel
  # remove extra spaces
  s = s.replace('  ',' ')
  s = s.replace('  ',' ')
  return s

def resseq_string(first_res_num,previous_res_num):
  """ Creates resseq string """
  if previous_res_num > first_res_num:
    res_seq = 'resseq {}:{}'.format(first_res_num,previous_res_num)
  else:
    res_seq = 'resseq {}'.format(first_res_num)
  return res_seq

def update_res_sel(res_sel,first_res_n,pre_res_n):
  """ update the residue selection list and markers of continuous section """
  if pre_res_n != -10000:
    res_seq = resseq_string(first_res_n,pre_res_n)
    first_res_n = None
    pre_res_n = -10000
    res_sel.append(res_seq)
  return res_sel,first_res_n,pre_res_n
