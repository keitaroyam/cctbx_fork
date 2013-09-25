from __future__ import division
from cctbx.array_family import flex

import boost.python
ext = boost.python.import_ext("iotbx_pdb_ext")
from iotbx_pdb_ext import *

import iotbx.pdb.records
import iotbx.pdb.hierarchy
from scitbx import matrix
from libtbx.test_utils import approx_equal

from iotbx.pdb.atom_name_interpretation import \
  interpreters as protein_atom_name_interpreters
import scitbx.array_family.shared # import dependency
import scitbx.stl.set
from libtbx import smart_open
from libtbx.str_utils import show_string
from libtbx.utils import plural_s, hashlib_md5, date_and_time, Sorry
from libtbx import Auto
from cStringIO import StringIO
import sys
import os
op = os.path

def is_pdb_file(file_name):
  pdb_raw_records = smart_open.for_reading(
    file_name = file_name).read().splitlines()
  for pdb_str in pdb_raw_records:
    if (pdb_str.startswith("CRYST1")):
      try: cryst1 = iotbx.pdb.records.cryst1(pdb_str=pdb_str)
      except iotbx.pdb.records.FormatError: continue
      if (cryst1.ucparams is not None and cryst1.sgroup is not None):
        return True
    elif (   pdb_str.startswith("ATOM  ")
          or pdb_str.startswith("HETATM")):
      try: pdb_inp = ext.input(
        source_info=None, lines=flex.std_string([pdb_str]))
      except KeyboardInterrupt: raise
      except Exception: continue
      if (pdb_inp.atoms().size() == 1):
        atom = pdb_inp.atoms()[0]
        if (atom.name != "    "):
          return True
  return False

def is_pdb_mmcif_file(file_name):
  try:
    cif_model = iotbx.cif.reader(file_path=file_name).model()
    cif_block = cif_model.values()[0]
    if "_atom_site" in cif_block:
      return True
  except Exception, e:
    return False

def ent_path_local_mirror(pdb_id, environ_key="PDB_MIRROR_PDB"):
  if (len(pdb_id) != 4):
    raise RuntimeError("Invalid PDB ID: %s (must be four characters)" % pdb_id)
  pdb_id = pdb_id.lower()
  pdb_mirror = os.environ[environ_key]
  result = op.join(pdb_mirror, pdb_id[1:3], "pdb%s.ent.gz" % pdb_id)
  if (not op.isfile(result)):
    raise RuntimeError("No file with PDB ID %s (%s)" % (pdb_id, result))
  return result

def systematic_chain_ids():
  import string
  u, l, d = string.ascii_uppercase, string.ascii_lowercase, string.digits
  _ = result = list(u)
  _.extend(l)
  _.extend(d)
  def xy(first, second):
    for f in first:
      for s in second:
        _.append(f+s)
  a = u+l+d
  xy(u, a)
  xy(l, a)
  xy(d, a)
  return result

cns_dna_rna_residue_names = {
  "ADE": "A",
  "CYT": "C",
  "GUA": "G",
  "THY": "T",
  "URI": "U"
}

mon_lib_dna_rna_cif = set(["AD", "A", "CD", "C", "GD", "G", "TD", "U"])

rna_dna_reference_residue_names = {
  "A": "?A",
  "C": "?C",
  "G": "?G",
  "U": "U",
  "T": "DT",
  "+A": "?A",
  "+C": "?C",
  "+G": "?G",
  "+U": "U",
  "+T": "DT",
  "DA": "DA",
  "DC": "DC",
  "DG": "DG",
  "DT": "DT",
  "ADE": "?A",
  "CYT": "?C",
  "GUA": "?G",
  "URI": "U",
  "THY": "DT",
  "AR": "A",
  "CR": "C",
  "GR": "G",
  "UR": "U",
  "AD": "DA",
  "CD": "DC",
  "GD": "DG",
  "TD": "DT"
}

def rna_dna_reference_residue_name(common_name):
  return rna_dna_reference_residue_names.get(common_name.strip().upper())

rna_dna_atom_names_reference_to_mon_lib_translation_dict = {
  " C1'": "C1*",
  " C2 ": "C2",
  " C2'": "C2*",
  " C3'": "C3*",
  " C4 ": "C4",
  " C4'": "C4*",
  " C5 ": "C5",
  " C5'": "C5*",
  " C6 ": "C6",
  " C7 ": "C5M",
  " C8 ": "C8",
  " H1 ": "H1",
  " H1'": "H1*",
  " H2 ": "H2",
# " H2'": special case: rna: "H2*", dna: "H2*1"
  " H21": "H21",
  " H22": "H22",
  " H3 ": "H3",
  " H3'": "H3*",
  " H4'": "H4*",
  " H41": "H41",
  " H42": "H42",
  " H5 ": "H5",
  " H5'": "H5*1",
  " H6 ": "H6",
  " H61": "H61",
  " H62": "H62",
  " H71": "H5M1",
  " H72": "H5M2",
  " H73": "H5M3",
  " H8 ": "H8",
  " N1 ": "N1",
  " N2 ": "N2",
  " N3 ": "N3",
  " N4 ": "N4",
  " N6 ": "N6",
  " N7 ": "N7",
  " N9 ": "N9",
  " O2 ": "O2",
  " O2'": "O2*",
  " O3'": "O3*",
  " O4 ": "O4",
  " O4'": "O4*",
  " O5'": "O5*",
  " O6 ": "O6",
  " OP1": "O1P",
  " OP2": "O2P",
  " OP3": "O3T",
  " P  ": "P",
  "H2''": "H2*2",
  "H5''": "H5*2",
  "HO2'": "HO2*",
  "HO3'": "HO3*",
  "HO5'": "HO5*",
  "HOP3": "HOP3" # added to monomer library
}

rna_dna_atom_names_backbone_reference_set = set([
  " C1'",
  " C2'",
  " C3'",
  " C4'",
  " C5'",
  " H1'",
  " H2'",
  " H3'",
  " H4'",
  " H5'",
  " O2'",
  " O3'",
  " O4'",
  " O5'",
  " OP1",
  " OP2",
  " OP3",
  " P  ",
  "H2''",
  "H5''",
  "HO2'",
  "HO3'",
  "HO5'",
  "HOP3"
])

rna_dna_atom_name_aliases = [
  ("1D2", " H21", "G DG"),
  ("1D2'", " H2'", "ANY"),
  ("1D2*", " H2'", "ANY"),
  ("1D4", " H41", "C DC"),
  ("1D5'", " H5'", "ANY"),
  ("1D5*", " H5'", "ANY"),
  ("1D5M", " H71", "DT"),
  ("1D6", " H61", "A DA"),
  ("1H2", " H21", "G DG"),
  ("1H2'", " H2'", "ANY"),
  ("1H2*", " H2'", "ANY"),
  ("1H4", " H41", "C DC"),
  ("1H5'", " H5'", "ANY"),
  ("1H5*", " H5'", "ANY"),
  ("1H5M", " H71", "DT"),
  ("1H6", " H61", "A DA"),
  ("2D2", " H22", "G DG"),
  ("2D2'", "H2''", "DA DC DG DT"),
  ("2D2*", "H2''", "DA DC DG DT"),
  ("2D4", " H42", "C DC"),
  ("2D5'", "H5''", "ANY"),
  ("2D5*", "H5''", "ANY"),
  ("2D5M", " H72", "DT"),
  ("2D6", " H62", "A DA"),
  ("2DO'", "HO2'", "A C G U"),
  ("2DO*", "HO2'", "A C G U"),
  ("2DOP", "HOP2", "ANY"),
  ("2H2", " H22", "G DG"),
  ("2H2'", "H2''", "DA DC DG DT"),
  ("2H2*", "H2''", "DA DC DG DT"),
  ("2H4", " H42", "C DC"),
  ("2H5'", "H5''", "ANY"),
  ("2H5*", "H5''", "ANY"),
  ("2H5M", " H72", "DT"),
  ("2H6", " H62", "A DA"),
  ("2HO'", "HO2'", "A C G U"),
  ("2HO*", "HO2'", "A C G U"),
  ("2HOP", "HOP2", "ANY"),
  ("3D5M", " H73", "DT"),
  ("3DOP", "HOP3", "ANY"),
  ("3H5M", " H73", "DT"),
  ("3HOP", "HOP3", "ANY"),
  ("C1'", " C1'", "ANY"),
  ("C1*", " C1'", "ANY"),
  ("C2", " C2 ", "ANY"),
  ("C2'", " C2'", "ANY"),
  ("C2*", " C2'", "ANY"),
  ("C3'", " C3'", "ANY"),
  ("C3*", " C3'", "ANY"),
  ("C4", " C4 ", "ANY"),
  ("C4'", " C4'", "ANY"),
  ("C4*", " C4'", "ANY"),
  ("C5", " C5 ", "ANY"),
  ("C5'", " C5'", "ANY"),
  ("C5*", " C5'", "ANY"),
  ("C5M", " C7 ", "DT"),
  ("C6", " C6 ", "ANY"),
  ("C7", " C7 ", "DT"),
  ("C8", " C8 ", "A G DA DG"),
  ("D1", " H1 ", "G DG"),
  ("D1'", " H1'", "ANY"),
  ("D1*", " H1'", "ANY"),
  ("D2", " H2 ", "A DA"),
  ("D2'", " H2'", "ANY"),
  ("D2*", " H2'", "ANY"),
  ("D2''", "H2''", "DA DC DG DT"),
  ("D2'1", " H2'", "ANY"),
  ("D2*1", " H2'", "ANY"),
  ("D2'2", "H2''", "DA DC DG DT"),
  ("D2*2", "H2''", "DA DC DG DT"),
  ("D21", " H21", "G DG"),
  ("D22", " H22", "G DG"),
  ("D3", " H3 ", "U DT"),
  ("D3'", " H3'", "ANY"),
  ("D3*", " H3'", "ANY"),
  ("D3T", "HO3'", "ANY"),
  ("D4'", " H4'", "ANY"),
  ("D4*", " H4'", "ANY"),
  ("D41", " H41", "C DC"),
  ("D42", " H42", "C DC"),
  ("D5", " H5 ", "C U DC"),
  ("D5'", " H5'", "ANY"),
  ("D5*", "HO5'", "ANY"),
  ("D5''", "H5''", "ANY"),
  ("D5'1", " H5'", "ANY"),
  ("D5*1", " H5'", "ANY"),
  ("D5'2", "H5''", "ANY"),
  ("D5*2", "H5''", "ANY"),
  ("D5M1", " H71", "DT"),
  ("D5M2", " H72", "DT"),
  ("D5M3", " H73", "DT"),
  ("D5T", "HO5'", "ANY"),
  ("D6", " H6 ", "C U DC DT"),
  ("D61", " H61", "A DA"),
  ("D62", " H62", "A DA"),
  ("D71", " H71", "DT"),
  ("D72", " H72", "DT"),
  ("D73", " H73", "DT"),
  ("D8", " H8 ", "A G DA DG"),
  ("DO2'", "HO2'", "A C G U"),
  ("DO2*", "HO2'", "A C G U"),
  ("H1", " H1 ", "G DG"),
  ("H1'", " H1'", "ANY"),
  ("H1*", " H1'", "ANY"),
  ("H2", " H2 ", "A DA"),
  ("H2'", " H2'", "ANY"),
  ("H2*", " H2'", "ANY"),
  ("H2''", "H2''", "DA DC DG DT"),
  ("H2'1", " H2'", "ANY"),
  ("H2*1", " H2'", "ANY"),
  ("H2'2", "H2''", "DA DC DG DT"),
  ("H2*2", "H2''", "DA DC DG DT"),
  ("H21", " H21", "G DG"),
  ("H22", " H22", "G DG"),
  ("H3", " H3 ", "U DT"),
  ("H3'", " H3'", "ANY"),
  ("H3*", " H3'", "ANY"),
  ("H3T", "HO3'", "ANY"),
  ("H4'", " H4'", "ANY"),
  ("H4*", " H4'", "ANY"),
  ("H41", " H41", "C DC"),
  ("H42", " H42", "C DC"),
  ("H5", " H5 ", "C U DC"),
  ("H5'", " H5'", "ANY"),
  ("H5*", "HO5'", "ANY"),
  ("H5''", "H5''", "ANY"),
  ("H5'1", " H5'", "ANY"),
  ("H5*1", " H5'", "ANY"),
  ("H5'2", "H5''", "ANY"),
  ("H5*2", "H5''", "ANY"),
  ("H5M1", " H71", "DT"),
  ("H5M2", " H72", "DT"),
  ("H5M3", " H73", "DT"),
  ("H5T", "HO5'", "ANY"),
  ("H6", " H6 ", "C U DC DT"),
  ("H61", " H61", "A DA"),
  ("H62", " H62", "A DA"),
  ("H71", " H71", "DT"),
  ("H72", " H72", "DT"),
  ("H73", " H73", "DT"),
  ("H8", " H8 ", "A G DA DG"),
  ("HO2'", "HO2'", "A C G U"),
  ("HO2*", "HO2'", "A C G U"),
  ("HO3'", "HO3'", "ANY"),
  ("HO3*", "HO3'", "ANY"),
  ("HO5'", "HO5'", "ANY"),
  ("HO5*", "HO5'", "ANY"),
  ("HOP2", "HOP2", "ANY"),
  ("HOP3", "HOP3", "ANY"),
  ("N1", " N1 ", "ANY"),
  ("N2", " N2 ", "G DG"),
  ("N3", " N3 ", "ANY"),
  ("N4", " N4 ", "C DC"),
  ("N6", " N6 ", "A DA"),
  ("N7", " N7 ", "A G DA DG"),
  ("N9", " N9 ", "A G DA DG"),
  ("O1P", " OP1", "ANY"),
  ("O2", " O2 ", "C U DC DT"),
  ("O2'", " O2'", "A C G U"),
  ("O2*", " O2'", "A C G U"),
  ("O2P", " OP2", "ANY"),
  ("O3'", " O3'", "ANY"),
  ("O3*", " O3'", "ANY"),
  ("O3P", " OP3", "ANY"),
  ("O3T", " OP3", "ANY"),
  ("O4", " O4 ", "U DT"),
  ("O4'", " O4'", "ANY"),
  ("O4*", " O4'", "ANY"),
  ("O5'", " O5'", "ANY"),
  ("O5*", " O5'", "ANY"),
  ("O5T", " OP3", "ANY"),
  ("O6", " O6 ", "G DG"),
  ("OP1", " OP1", "ANY"),
  ("OP2", " OP2", "ANY"),
  ("OP3", " OP3", "ANY"),
  ("P", " P  ", "ANY")]

def __rna_dna_atom_names_backbone_aliases():
  result = {}
  for a,r,f in rna_dna_atom_name_aliases:
    if (r in rna_dna_atom_names_backbone_reference_set):
      result[a] = r
  return result
rna_dna_atom_names_backbone_aliases = __rna_dna_atom_names_backbone_aliases()

class rna_dna_atom_names_interpretation(object):

  def __init__(self, residue_name, atom_names):
    if (residue_name == "T"):
      residue_name = "DT"
    else:
      assert residue_name in ["?A", "?C", "?G",
                              "A", "C", "G", "U",
                              "DA", "DC", "DG", "DT", "T"]
    self.residue_name = residue_name
    self.atom_names = atom_names
    rna_dna_atom_names_interpretation_core(self)

  def unexpected_atom_names(self):
    result = []
    for atom_name,info in zip(self.atom_names, self.infos):
      if (info.reference_name is None):
        result.append(atom_name)
    return result

  def mon_lib_names(self):
    result = []
    for info in self.infos:
      rn = info.reference_name
      if (rn is None):
        result.append(None)
      else:
        mn = rna_dna_atom_names_reference_to_mon_lib_translation_dict.get(rn)
        if (mn is not None):
          result.append(mn)
        elif (rn == " H2'"):
          if (self.residue_name.startswith("D")):
            result.append("H2*1")
          else:
            result.append("H2*")
        else:
          assert rn == "HOP3" # only atom not covered by monomer library
          result.append(None)
    return result

class residue_name_plus_atom_names_interpreter(object):

  def __init__(self,
        residue_name,
        atom_names,
        translate_cns_dna_rna_residue_names=None,
        return_mon_lib_dna_name=False):
    work_residue_name = residue_name.strip().upper()
    if (len(work_residue_name) == 0):
      self.work_residue_name = None
      self.atom_name_interpretation = None
      return
    from iotbx.pdb.amino_acid_codes import three_letter_l_given_three_letter_d
    l_aa_rn = three_letter_l_given_three_letter_d.get(work_residue_name)
    if (l_aa_rn is None):
      d_aa_rn = None
    else:
      d_aa_rn = work_residue_name
      work_residue_name = l_aa_rn
    protein_interpreter = protein_atom_name_interpreters.get(
      work_residue_name)
    atom_name_interpretation = None
    if (protein_interpreter is not None):
      atom_name_interpretation = protein_interpreter.match_atom_names(
        atom_names=atom_names)
      if (atom_name_interpretation is not None):
        atom_name_interpretation.d_aa_residue_name = d_aa_rn
    else:
      assert d_aa_rn is None
      if (    translate_cns_dna_rna_residue_names is not None
          and not translate_cns_dna_rna_residue_names
          and work_residue_name in cns_dna_rna_residue_names):
        rna_dna_ref_residue_name = None
      else:
        rna_dna_ref_residue_name = rna_dna_reference_residue_name(
          common_name=work_residue_name)
      if (rna_dna_ref_residue_name is not None):
        atom_name_interpretation = rna_dna_atom_names_interpretation(
          residue_name=rna_dna_ref_residue_name,
          atom_names=atom_names)
        if (atom_name_interpretation.n_unexpected != 0):
          if (    len(atom_names) == 1
              and work_residue_name in mon_lib_dna_rna_cif):
            self.work_residue_name = None
            self.atom_name_interpretation = None
            return
          if (    translate_cns_dna_rna_residue_names is None
              and work_residue_name in cns_dna_rna_residue_names):
            atom_name_interpretation = None
        if (atom_name_interpretation is not None):
          work_residue_name = atom_name_interpretation.residue_name
          if (return_mon_lib_dna_name):
            work_residue_name = {
              "A": "A",
              "C": "C",
              "G": "G",
              "U": "U",
              "DA": "AD",
              "DC": "CD",
              "DG": "GD",
              "DT": "TD"}[work_residue_name]
    self.work_residue_name = work_residue_name
    self.atom_name_interpretation = atom_name_interpretation

class combine_unique_pdb_files(object):

  def __init__(self, file_names):
    self.file_name_registry = {}
    self.md5_registry = {}
    self.unique_file_names = []
    self.raw_records = []
    for file_name in file_names:
      if (file_name in self.file_name_registry):
        self.file_name_registry[file_name] += 1
      else:
        self.file_name_registry[file_name] = 1
        r = [s.expandtabs().rstrip()
          for s in smart_open.for_reading(
            file_name=file_name).read().splitlines()]
        m = hashlib_md5()
        m.update("\n".join(r))
        m = m.hexdigest()
        l = self.md5_registry.get(m)
        if (l is not None):
          l.append(file_name)
        else:
          self.md5_registry[m] = [file_name]
          self.unique_file_names.append(file_name)
          self.raw_records.extend(r)

  def report_non_unique(self, out=None, prefix=""):
    if (out is None): out = sys.stdout
    n_ignored = 0
    for file_name in sorted(self.file_name_registry.keys()):
      n = self.file_name_registry[file_name]
      if (n != 1):
        print >> out, prefix+"INFO: PDB file name appears %d times: %s" % (
          n, show_string(file_name))
        n_ignored += (n-1)
    if (n_ignored != 0):
      print >> out, prefix+"  %d repeated file name%s ignored." % \
        plural_s(n=n_ignored)
    n_identical = 0
    for file_names in self.md5_registry.values():
      if (len(file_names) != 1):
        print >> out, prefix+"INFO: PDB files with identical content:"
        for file_name in file_names:
          print >> out, prefix+"  %s" % show_string(file_name)
        n_identical += len(file_names)-1
    if (n_identical != 0):
      print >> out, prefix+"%d file%s with repeated content ignored." % \
        plural_s(n=n_identical)
    if (n_ignored != 0 or n_identical != 0):
      print >> out, prefix.rstrip()

class header_date(object):

  def __init__(self, field):
    "Expected format: DD-MMM-YY"
    self.dd = None
    self.mmm = None
    self.yy = None
    self.yyyy = None
    if (len(field) != 9): return
    if (field.count("-") != 2): return
    if (field[2] != "-" or field[6] != "-"): return
    dd, mmm, yy = field.split("-")
    try: self.dd = int(dd)
    except ValueError: pass
    else:
      if (self.dd < 1 or self.dd > 31): self.dd = None
    if (mmm.upper() in [
          "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]):
      self.mmm = mmm.upper()
    try: self.yy = int(yy)
    except ValueError: pass
    else:
      if (self.yy < 0 or self.yy > 99): self.yy = None
    if self.yy is not None:
      if self.yy < 60: # I hope by 2060 no one uses the PDB format seriously!
        self.yyyy = 2000 + self.yy
      else:
        self.yyyy = 1900 + self.yy

  def is_fully_defined(self):
    return self.dd is not None \
       and self.mmm is not None \
       and self.yy is not None \
       and self.yyyy is not None

def header_year(record):
  if (record.startswith("HEADER")):
    date = header_date(field=record[50:59])
    if (date.is_fully_defined()): return date.yyyy
    fields = record.split()
    fields.reverse()
    for field in fields:
      date = header_date(field=field)
      if (date.is_fully_defined()): return date.yyyy
  return None

class Please_pass_string_or_None(object): pass

class pdb_input_from_any(object):

  def __init__(self,
               file_name=None,
               source_info=Please_pass_string_or_None,
               lines=None,
               pdb_id=None,
               raise_sorry_if_format_error=False):
    self.file_format = None
    content = None
    from iotbx.pdb.mmcif import cif_input
    mmcif_exts = ('.cif', '.mmcif')
    if file_name is not None and file_name.endswith(mmcif_exts):
      file_inputs = (cif_input, pdb_input)
    else:
      file_inputs = (pdb_input, cif_input)
    exc_info = None
    for file_input in file_inputs:
      try:
        content = file_input(
          file_name=file_name,
          source_info=source_info,
          lines=lines,
          pdb_id=pdb_id,
          raise_sorry_if_format_error=raise_sorry_if_format_error)
      except Exception, e:
        # store the first error encountered and re-raise later if can't
        # interpret as any file type
        if exc_info is None: exc_info = sys.exc_info()
        continue
      else: exc_info = None
      if file_input is pdb_input:
        # XXX nasty hack:
        #   pdb_input only raises an error if there are lines starting with
        #   "ATOM  " or "HETATM" and it subsequently fails to interpret these
        #   lines as ATOM/HETATM records
        n_unknown_records = content.unknown_section().size()
        n_records = sum(content.record_type_counts().values())
        n_blank_records = content.record_type_counts().get('      ', 0)
        if (n_unknown_records == n_records or
            n_unknown_records == (n_records - n_blank_records)):
          continue
        self.file_format = "pdb"
      else :
        self.file_format = "cif"
      break
    if exc_info is not None:
      raise exc_info[0], exc_info[1], exc_info[2]
    if content is None:
      raise Sorry("Could not interpret input as any file type.")
    self._file_content = content

  def file_content(self):
    return self._file_content

def pdb_input(
    file_name=None,
    source_info=Please_pass_string_or_None,
    lines=None,
    pdb_id=None,
    raise_sorry_if_format_error=False):
  if (pdb_id is not None):
    assert file_name is None
    file_name = ent_path_local_mirror(pdb_id=pdb_id)
  if (file_name is not None):
    try :
      return ext.input(
        source_info="file " + str(file_name), # XXX unicode hack - dangerous
        lines=flex.split_lines(smart_open.for_reading(file_name).read()))
    except ValueError, e :
      if (raise_sorry_if_format_error) :
        raise Sorry("Format error in %s:\n%s" % (str(file_name), str(e)))
      else :
        raise
  assert source_info is not Please_pass_string_or_None
  if (isinstance(lines, str)):
    lines = flex.split_lines(lines)
  elif (isinstance(lines, (list, tuple))):
    lines = flex.std_string(lines)
  try :
    return ext.input(source_info=source_info, lines=lines)
  except ValueError, e :
    if (raise_sorry_if_format_error) :
      raise Sorry("Format error:\n%s" % str(e))
    else :
      raise

def input(
    file_name=None,
    source_info=Please_pass_string_or_None,
    lines=None,
    pdb_id=None,
    raise_sorry_if_format_error=False):
  return pdb_input_from_any(
    file_name=file_name,
    source_info=source_info,
    lines=lines,
    pdb_id=pdb_id,
    raise_sorry_if_format_error=raise_sorry_if_format_error).file_content()

default_atom_names_scattering_type_const = ["PEAK", "SITE"]

input_sections = (
  "unknown_section",
  "title_section",
  "remark_section",
  "primary_structure_section",
  "heterogen_section",
  "secondary_structure_section",
  "connectivity_annotation_section",
  "miscellaneous_features_section",
  "crystallographic_section",
  "connectivity_section",
  "bookkeeping_section")


class pdb_input_mixin(object):

  def special_position_settings(self,
        special_position_settings=None,
        weak_symmetry=False,
        min_distance_sym_equiv=0.5,
        u_star_tolerance=0):
    crystal_symmetry = self.crystal_symmetry(
      crystal_symmetry=special_position_settings,
      weak_symmetry=weak_symmetry)
    if (crystal_symmetry is None): return None
    if (special_position_settings is not None):
      min_distance_sym_equiv=special_position_settings.min_distance_sym_equiv()
      u_star_tolerance = special_position_settings.u_star_tolerance()
    return crystal_symmetry.special_position_settings(
      min_distance_sym_equiv=min_distance_sym_equiv,
      u_star_tolerance=u_star_tolerance)

  def as_pdb_string(self,
        crystal_symmetry=Auto,
        cryst1_z=Auto,
        write_scale_records=True,
        append_end=False,
        atom_hetatm=True,
        sigatm=True,
        anisou=True,
        siguij=True,
        cstringio=None,
        return_cstringio=Auto):
    if (cstringio is None):
      cstringio = StringIO()
      if (return_cstringio is Auto):
        return_cstringio = False
    elif (return_cstringio is Auto):
      return_cstringio = True
    if (crystal_symmetry is Auto):
      crystal_symmetry = self.crystal_symmetry()
    if (cryst1_z is Auto):
      cryst1_z = self.extract_cryst1_z_columns()
    if (crystal_symmetry is not None or cryst1_z is not None):
      print >> cstringio, format_cryst1_and_scale_records(
        crystal_symmetry=crystal_symmetry,
        cryst1_z=cryst1_z,
        write_scale_records=write_scale_records)
    self._as_pdb_string_cstringio(
      cstringio=cstringio,
      append_end=append_end,
      atom_hetatm=atom_hetatm,
      sigatm=sigatm,
      anisou=anisou,
      siguij=siguij)
    if (return_cstringio):
      return cstringio
    return cstringio.getvalue()

  def write_pdb_file(self,
        file_name,
        open_append=False,
        crystal_symmetry=Auto,
        cryst1_z=Auto,
        write_scale_records=True,
        append_end=False,
        atom_hetatm=True,
        sigatm=True,
        anisou=True,
        siguij=True):
    if (crystal_symmetry is Auto):
      crystal_symmetry = self.crystal_symmetry()
    if (cryst1_z is Auto):
      cryst1_z = self.extract_cryst1_z_columns()
    if (crystal_symmetry is not None or cryst1_z is not None):
      if (open_append): mode = "ab"
      else:             mode = "wb"
      print >> open(file_name, mode), format_cryst1_and_scale_records(
        crystal_symmetry=crystal_symmetry,
        cryst1_z=cryst1_z,
        write_scale_records=write_scale_records)
      open_append = True
    self._write_pdb_file(
      file_name=file_name,
      open_append=open_append,
      append_end=append_end,
      atom_hetatm=atom_hetatm,
      sigatm=sigatm,
      anisou=anisou,
      siguij=siguij)

  def xray_structure_simple(self,
        crystal_symmetry=None,
        weak_symmetry=False,
        cryst1_substitution_buffer_layer=None,
        unit_cube_pseudo_crystal=False,
        fractional_coordinates=False,
        use_scale_matrix_if_available=True,
        min_distance_sym_equiv=0.5,
        non_unit_occupancy_implies_min_distance_sym_equiv_zero=True,
        scattering_type_exact=False,
        enable_scattering_type_unknown=False,
        atom_names_scattering_type_const
          =default_atom_names_scattering_type_const):
    return self.xray_structures_simple(
      one_structure_for_each_model=False,
      crystal_symmetry=crystal_symmetry,
      weak_symmetry=weak_symmetry,
      cryst1_substitution_buffer_layer=cryst1_substitution_buffer_layer,
      unit_cube_pseudo_crystal=unit_cube_pseudo_crystal,
      fractional_coordinates=fractional_coordinates,
      use_scale_matrix_if_available=use_scale_matrix_if_available,
      min_distance_sym_equiv=min_distance_sym_equiv,
      non_unit_occupancy_implies_min_distance_sym_equiv_zero=
        non_unit_occupancy_implies_min_distance_sym_equiv_zero,
      scattering_type_exact=scattering_type_exact,
      enable_scattering_type_unknown=enable_scattering_type_unknown,
      atom_names_scattering_type_const=atom_names_scattering_type_const)[0]

  def xray_structures_simple(self,
        one_structure_for_each_model=True,
        crystal_symmetry=None,
        weak_symmetry=False,
        cryst1_substitution_buffer_layer=None,
        unit_cube_pseudo_crystal=False,
        fractional_coordinates=False,
        min_distance_sym_equiv=0.5,
        non_unit_occupancy_implies_min_distance_sym_equiv_zero=True,
        use_scale_matrix_if_available=True,
        scattering_type_exact=False,
        enable_scattering_type_unknown=False,
        atom_names_scattering_type_const
          =default_atom_names_scattering_type_const):
    from cctbx import xray
    from cctbx import crystal
    from cctbx import uctbx
    if (unit_cube_pseudo_crystal):
      assert crystal_symmetry is None and cryst1_substitution_buffer_layer is None
      crystal_symmetry = crystal.symmetry(
        unit_cell=(1,1,1,90,90,90),
        space_group_symbol="P1")
    else:
      crystal_symmetry = self.crystal_symmetry(
        crystal_symmetry=crystal_symmetry,
        weak_symmetry=weak_symmetry)
      if (crystal_symmetry is None):
        crystal_symmetry = crystal.symmetry()
      if (crystal_symmetry.unit_cell() is None):
        crystal_symmetry = crystal_symmetry.customized_copy(
          unit_cell=uctbx.non_crystallographic_unit_cell(
            sites_cart=self.atoms().extract_xyz(),
            buffer_layer=cryst1_substitution_buffer_layer))
      if (crystal_symmetry.space_group_info() is None):
        crystal_symmetry = crystal_symmetry.cell_equivalent_p1()
    unit_cell = crystal_symmetry.unit_cell()
    scale_r = (0,0,0,0,0,0,0,0,0)
    scale_t = (0,0,0)
    if (not unit_cube_pseudo_crystal):
      if (use_scale_matrix_if_available):
        scale_matrix = self.scale_matrix()
        if (scale_matrix is not None):
          # Avoid subtle inconsistencies due to rounding errors.
          # 1.e-6 is the precision of the values on the SCALE records.
          if (max([abs(s-f) for s,f in zip(
                     scale_matrix[0],
                     unit_cell.fractionalization_matrix())]) < 1.e-6):
            if (scale_matrix[1] != [0,0,0]):
              scale_matrix[0] = unit_cell.fractionalization_matrix()
            else:
              scale_matrix = None
      else:
        scale_matrix = None
      if (scale_matrix is not None):
        scale_r = scale_matrix[0]
        scale_t = scale_matrix[1]
    result = []
    if (atom_names_scattering_type_const is None):
      atom_names_scattering_type_const = []
    loop = xray_structures_simple_extension(
      one_structure_for_each_model,
      unit_cube_pseudo_crystal,
      fractional_coordinates,
      scattering_type_exact,
      enable_scattering_type_unknown,
      self.atoms_with_labels(),
      self.model_indices(),
      scitbx.stl.set.stl_string(atom_names_scattering_type_const),
      unit_cell,
      scale_r,
      scale_t)
    special_position_settings = crystal_symmetry.special_position_settings(
      min_distance_sym_equiv=min_distance_sym_equiv)
    try :
      while (loop.next()):
        result.append(xray.structure(
          special_position_settings=special_position_settings,
          scatterers=loop.scatterers,
          non_unit_occupancy_implies_min_distance_sym_equiv_zero=
            non_unit_occupancy_implies_min_distance_sym_equiv_zero))
    except ValueError, e :
      raise Sorry(str(e))
    return result

class _(boost.python.injector, ext.input, pdb_input_mixin):

  def __getinitargs__(self):
    lines = flex.std_string()
    for section in input_sections[:-2]:
      lines.extend(getattr(self, section)())
    pdb_string = StringIO()
    self._as_pdb_string_cstringio(
      cstringio=pdb_string,
      append_end=False,
      atom_hetatm=True,
      sigatm=True,
      anisou=True,
      siguij=True)
    lines.extend(flex.split_lines(pdb_string.getvalue()))
    for section in input_sections[-2:]:
      lines.extend(getattr(self, section)())
    return ("pickle", lines)

  def file_type (self) :
    return "pdb"

  def extract_header_year(self):
    for line in self.title_section():
      if (line.startswith("HEADER ")):
        return header_year(line)
    return None

  def extract_remark_iii_records(self, iii):
    result = []
    pattern = "REMARK %3d " % iii
    for line in self.remark_section():
      if (line.startswith(pattern)):
        result.append(line)
    return result

  def extract_secondary_structure (self) :
    from iotbx.pdb import secondary_structure
    records = self.secondary_structure_section()
    if records.size() != 0 :
      return secondary_structure.annotation(records)
    return None

  def extract_LINK_records(self):
    '''
    Collect link records from PDB file
    '''
    result = []
    for line in self.connectivity_annotation_section():
      if (line.startswith('LINK') or line.startswith('link')):
        result.append(line)
    return result

  def crystal_symmetry_from_cryst1(self):
    from iotbx.pdb import cryst1_interpretation
    for line in self.crystallographic_section():
      if (line.startswith("CRYST1")):
        return cryst1_interpretation.crystal_symmetry(cryst1_record=line)
    return None

  def extract_cryst1_z_columns(self):
    for line in self.crystallographic_section():
      if (line.startswith("CRYST1")):
        result = line[66:]
        if (len(result) < 4): result += " " * (4-len(result))
        return result
    return None

  def crystal_symmetry_from_cns_remark_sg(self):
    from iotbx.cns import pdb_remarks
    for line in self.remark_section():
      if (line.startswith("REMARK sg=")):
        crystal_symmetry = pdb_remarks.extract_symmetry(pdb_record=line)
        if (crystal_symmetry is not None):
          return crystal_symmetry
    return None

  def crystal_symmetry(self,
        crystal_symmetry=None,
        weak_symmetry=False):
    self_symmetry = self.crystal_symmetry_from_cryst1()
    if (self_symmetry is None):
      self_symmetry = self.crystal_symmetry_from_cns_remark_sg()
    if (crystal_symmetry is None):
      return self_symmetry
    if (self_symmetry is None):
      return crystal_symmetry
    return self_symmetry.join_symmetry(
      other_symmetry=crystal_symmetry,
      force=not weak_symmetry)

  def scale_matrix(self):
    if (not hasattr(self, "_scale_matrix")):
      source_info = self.source_info()
      if (len(source_info) > 0): source_info = " (%s)" % source_info
      self._scale_matrix = [[None]*9,[None]*3]
      done_set = set()
      done_list = []
      for line in self.crystallographic_section():
        if (line.startswith("SCALE") and line[5:6] in ["1", "2", "3"]):
          r = read_scale_record(line=line, source_info=source_info)
          if (r.n not in done_set):
            for i_col,v in enumerate(r.r):
              self._scale_matrix[0][(r.n-1)*3+i_col] = v
            self._scale_matrix[1][r.n-1] = r.t
            done_set.add(r.n)
          done_list.append(r.n)
      if (len(done_list) == 0):
        self._scale_matrix = None
      elif (sorted(done_list[:3]) != [1,2,3]):
        raise ValueError(
          "Improper set of PDB SCALE records%s" % source_info)
    return self._scale_matrix

  def process_BIOMT_records(self,error_handle=True,eps=1e-4):
    '''(pdb_data,boolean,float) -> group of lists
    extract REMARK 350 BIOMT information, information that provides rotation matrices
    and translation  data, required for generating  a complete multimer from the asymmetric unit.

    BIOMT data sample:
    REMARK 350   BIOMT1   1  1.000000  0.000000  0.000000        0.00000
    REMARK 350   BIOMT2   1  0.000000  1.000000  0.000000        0.00000
    REMARK 350   BIOMT3   1  0.000000  0.000000  1.000000        0.00000
    REMARK 350   BIOMT1   2  0.559048 -0.789435  0.253492        0.30000
    REMARK 350   BIOMT2   2  0.722264  0.313528 -0.616470        0.00100
    REMARK 350   BIOMT3   2  0.407186  0.527724  0.745457        0.05000

    The data from every 3 lines will be combined to a list
    [[x11,x12,x13,x21,x22,x23,x31,x32,x33],[x1,x2,x3]]
    the first component, with the 9 numbers are the rotation matrix,
    and the second component, with the 3 numbers is the translation information
    x is the serial number of the operation

    Arguments:
    error_handle -- True: will stop execution on improper retation matrices
                    False: will continue execution but will replace the values in the
                           rotation matrix with [0,0,0,0,0,0,0,0,0]
    eps -- Rounding accuracy for avoiding numerical issue when when testing proper rotation

    error_handle can be use if one does not want a 'Sorry' to be raised. The program will continue to execute
    but all coordinates of the bad rotation matrix will zero out

    for x=2 the transformation_data will be
    [[0.559048,-0.789435,0.253492,0.722264,0.313528,-0.616470,0.407186,0.527724,0.745457][0.30000,0.00100,0.05000]]

    the result is a list of libtx group_arg constructs, each one contains
      pdb_inp.process_BIOMT_records()[1].values              # give a list containing float type numbers
      pdb_inp.process_BIOMT_records()[1].coordinates_present # True when transformatin included in pdb file
      pdb_inp.process_BIOMT_records()[1].serial_number       # is an integer

    @author: Youval Dar (2013)
    '''
    from libtbx import group_args
    source_info = self.extract_remark_iii_records(350)
    result = []                         # the returned list of rotation and translation data
    if source_info:                     # check if any BIOMT info is available
      # collecting the data from the remarks. Checking that we are collecting only data
      # and not part of the remarks header by verifying that the 3rd component contains "BIOMT"
      # and that the length of that component is 6
      biomt_data = [map(float,x.split()[3:]) for x in source_info if (x.split()[2].find('BIOMT') > -1)
                    and (len(x.split()[2]) == 6)]
      # test that there is no missing data
      if len(biomt_data)%3 != 0:
        raise RuntimeError("Improper or missing set of PDB BIOMAT records. Data length = %s" % str(len(biomt_data)))
      # test that the length of the data match the serial number, that there are no missing records
      temp = int(source_info[-1].split()[3])    # expected number of records
      if len(biomt_data)/3.0 != int(source_info[-1].split()[3]):
        raise RuntimeError("Missing record sets in PDB BIOMAT records \n" + \
                           "Actual number of BIOMT matrices: {} \n".format(len(biomt_data)/3.0) + \
                           "expected according to serial number: {} \n".format(temp))
      for i in range(len(biomt_data)//3):
        # i is the group number in biomt_data
        # Each group composed from 3 data sets.
        j = 3*i;
        rotation_data = biomt_data[j][1:4] + biomt_data[j+1][1:4] + biomt_data[j+2][1:4]
        translation_data = [biomt_data[j][-1], biomt_data[j+1][-1], biomt_data[j+2][-1]]
        # Test rotation matrix
        if self._test_matrix(rotation_data,eps=eps):
          if error_handle:
            raise Sorry('Rotation matrices are not proper! ')
          else:
            rotation_data = [0,0,0,0,0,0,0,0,0]
        # done following the format in the MTRIX records
        result.append(group_args(
          values = [rotation_data,translation_data],
          coordinates_present=(i == 0),         # Only the first transformation included in pdb file
          serial_number=i + 1))
    return result

  def process_mtrix_records(self,error_handle=True,eps=1e-4):
    '''
    Read MTRIX records from a pdb file

    Arguments:
    error_handle -- True: will stop execution on improper retation matrices
                    False: will continue execution but will replace the values in the
                           rotation matrix with [0,0,0,0,0,0,0,0,0]
    eps -- Rounding accuracy for avoiding numerical issue when when testing proper rotation

    error_handle can be use if one does not want a 'Sorry' to be raised. The program will continue to execute
    but all coordinates of the bad rotation matrix will zero out

    @edited: Youval Dar (2013)
    '''
    source_info = self.source_info()
    if (len(source_info) > 0): source_info = " (%s)" % source_info
    storage = {}
    for line in self.crystallographic_section():
      if (line.startswith("MTRIX") and line[5:6] in ["1", "2", "3"]):
        r = read_mtrix_record(line=line, source_info=source_info)
        stored = storage.get(r.serial_number)
        if (stored is None):
          values = [[None]*9,[None]*3]
          done = []
          present = []
          stored = storage[r.serial_number] = (values, done, present)
        else:
          values, done, present = stored
        for i_col,v in enumerate(r.r):
          values[0][(r.n-1)*3+i_col] = v
        values[1][r.n-1] = r.t
        done.append(r.n)
        present.append(r.coordinates_present)
    from libtbx import group_args
    result = []
    for serial_number in sorted(storage.keys()):
      values, done, present = storage[serial_number]
      # Test rotation matrices
      if self._test_matrix(values[0],eps=eps):
        if error_handle:
          raise Sorry('Rotation matrices are not proper! ')
        else:
          values[0] = [0,0,0,0,0,0,0,0,0]
      if (sorted(done) != [1,2,3] or len(set(present)) != 1):
        raise RuntimeError(
          "Improper set of PDB MTRIX records%s" % source_info)
      result.append(group_args(
        values=values,
        coordinates_present=present[0],
        serial_number=serial_number))
    return result

  def _test_matrix(self,s,eps=1e-6):
    ''' (list) -> boolean
    Test if a matrix is a proper rotation
    Should have the properties:
    1)R_inverse = R_transpose
    2)Det(R) = 1
        R = matrix.sqr(rotation_data)
        t1 = R*R.transpose()
        t2 = R.transpose()*R

    Arguments:
    s -- a list of 9 float numbers
    eps -- Rounding accuracy for avoiding numerical issue when when testing proper rotation

    >>> test_matrix()
    True
    >>> test_matrix()
    False

    @author: Youval Dar (2013)
    '''
    R = matrix.sqr(s)
    t1 = R*R.transpose()
    t2 = matrix.identity(3)
    return not approx_equal(R.determinant(),1,eps=eps) or not approx_equal(t1,t2,eps=eps)

  def get_r_rfree_sigma(self, file_name=None):
    from iotbx.pdb import extract_rfactors_resolutions_sigma
    remark_2_and_3_records = self.extract_remark_iii_records(2)
    remark_2_and_3_records.extend(self.extract_remark_iii_records(3))
    return extract_rfactors_resolutions_sigma.get_r_rfree_sigma(
      remark_2_and_3_records, file_name)

  def get_program_name(self):
    remark_3_lines = self.extract_remark_iii_records(3)
    result = None
    for line in remark_3_lines:
      line = line.strip()
      result = iotbx.pdb.remark_3_interpretation.get_program(st = line)
      if(result is not None): return result
    if(result is not None):
      result = "_".join(result.split())
    return result

  def get_solvent_content(self):
    remark_280_lines = self.extract_remark_iii_records(280)
    mc = []
    for remark in remark_280_lines:
      remark = remark.upper()
      if(remark.count("SOLVENT")==1 and
         remark.count("CONTENT")==1):
        try:
          mc.append(remark.split()[6])
        except Exception:
          try:
            mc.append(remark[remark.index(":")+1:])
          except Exception:
            mc.append(remark)
    result = None
    if(len(mc) == 1):
      try: result = float(mc[0])
      except IndexError: pass
      except ValueError: pass
    return result

  def get_matthews_coeff(self):
    remark_280_lines = self.extract_remark_iii_records(280)
    mc = []
    for remark in remark_280_lines:
      remark = remark.upper()
      if(remark.count("MATTHEWS")==1 and
         remark.count("COEFFICIENT")==1):
        try:
          mc.append(remark.split()[6])
        except Exception:
          try:
            mc.append(remark[remark.index(":")+1:])
          except Exception:
            mc.append(remark)
    result = None
    if(len(mc) == 1):
      try: result = float(mc[0])
      except IndexError: pass
      except ValueError: pass
    return result

  def extract_tls_params(self, pdb_hierarchy):
    import iotbx.pdb.remark_3_interpretation
    remark_3_records = self.extract_remark_iii_records(3)
    chain_ids = []
    for model in pdb_hierarchy.models():
      for chain in model.chains():
        chain_ids.append(chain.id)
    return iotbx.pdb.remark_3_interpretation.extract_tls_parameters(
      remark_3_records = remark_3_records,
      pdb_hierarchy    = pdb_hierarchy,
      chain_ids        = chain_ids)

  def extract_f_model_core_constants(self):
    import iotbx.pdb.remark_3_interpretation
    remark_3_records = self.extract_remark_iii_records(3)
    return remark_3_interpretation.extract_f_model_core_constants(remark_3_records)

  def extract_wavelength (self, first_only=True) :
    for line in self.remark_section() :
      # XXX this will miss multi-line records!
      if (line.startswith("REMARK 200  WAVELENGTH OR RANGE")) :
        fields = line.split(":")
        assert (len(fields) == 2)
        subfields = fields[1].replace(";", ",").strip().split(",")
        wavelengths = []
        for field in subfields :
          if (field.strip() == "") :
            continue
          elif (field.strip() == "NULL") :
            wavelengths.append(None)
          else :
            wavelengths.append(float(field.strip()))
        if (first_only) :
          if (len(wavelengths) > 0) :
            return wavelengths[0]
          return None
        return wavelengths
    return None

  def get_experiment_type (self) :
    for line in self.title_section() :
      if (line.startswith("EXPDTA")) :
        return records.expdta(line).technique.strip()
    return None

  def extract_connectivity (self) :
    """
    Parse CONECT records and extract the indices of bonded atoms.  Returns
    a scitbx.array_family.shared.stl_set_unsigned object corresponding to the
    atoms array, with each element being the list of indices of bonded atoms
    (if any).  If no CONECT records are found, returns None.

    Note that the ordering of atoms may be altered by construct_hierarchy(), so
    this method should probably be called after the hierarchy is made.
    """
    lines = self.connectivity_section()
    if (len(lines) == 0) :
      return None
    from scitbx.array_family import shared
    bonds = shared.stl_set_unsigned(len(self.atoms()), [])
    serial_ref_hash = {}
    for i_seq, atom in enumerate(self.atoms()) :
      serial = atom.serial.strip()
      serial_ref_hash[serial] = i_seq
    for line in lines :
      assert (line.startswith("CONECT"))
      record = iotbx.pdb.records.conect(line)
      i_seq = serial_ref_hash[record.serial.strip()]
      assert (record.serial_numbers_bonded_atoms.count('') != 4)
      for j_seq_str in record.serial_numbers_bonded_atoms :
        if (j_seq_str != '') :
          bonds[i_seq].append(serial_ref_hash[j_seq_str.strip()])
    return bonds

class rewrite_normalized(object):

  def __init__(self,
        input_file_name,
        output_file_name,
        keep_original_crystallographic_section=False,
        keep_original_atom_serial=False):
    self.input = input(file_name=input_file_name)
    if (keep_original_crystallographic_section):
      print >> open(output_file_name, "wb"), \
        "\n".join(self.input.crystallographic_section())
      crystal_symmetry = None
    else:
      crystal_symmetry = self.input.crystal_symmetry()
    self.hierarchy = self.input.construct_hierarchy()
    if (keep_original_atom_serial):
      atoms_reset_serial_first_value = None
    else:
      atoms_reset_serial_first_value = 1
    self.hierarchy.write_pdb_file(
      file_name=output_file_name,
      open_append=keep_original_crystallographic_section,
      crystal_symmetry=crystal_symmetry,
      append_end=True,
      atoms_reset_serial_first_value=atoms_reset_serial_first_value)

# Table of structures split into multiple PDB files.
# Assembled manually.
# Based on 46377 PDB files as of Tuesday Oct 02, 2007
#   noticed in passing: misleading REMARK 400 in 1VSA (1vs9 and 2i1c
#   don't exist)
# Updated 2009-04-07, based on 56751 PDB files, using SPLIT records.
pdb_codes_fragment_files = """\
1bgl 1bgm
1crp 1crr
1f49 1gho
1gix 1giy
1j4z 1kpo
1jgo 1jgp 1jgq
1jyy 1jyz
1jz0 1jz1
1otz 1p0t
1pns 1pnu
1pnx 1pny
1s1h 1s1i
1ti2 1vld
1ti4 1vle
1ti6 1vlf
1utf 1utv
1voq 1vor 1vos 1vou 1vov 1vow 1vox 1voy 1voz 1vp0
1vs5 1vs6 1vs7 1vs8
1vsa 2ow8
1vsp 2qnh
1we3 1wf4
1yl3 1yl4
2avy 2aw4 2aw7 2awb
2b64 2b66
2b9m 2b9n
2b9o 2b9p
2bld 2bvi
2gy9 2gya
2gyb 2gyc
2hgi 2hgj
2hgp 2hgq
2hgr 2hgu
2i2p 2i2t 2i2u 2i2v
2j00 2j01 2j02 2j03
2jl5 2jl6 2jl7 2jl8
2qal 2qam 2qan 2qao
2qb9 2qba 2qbb 2qbc
2qbd 2qbe 2qbf 2qbg
2qbh 2qbi 2qbj 2qbk
2qou 2qov 2qow 2qox
2qoy 2qoz 2qp0 2qp1
2uv9 2uva
2uvb 2uvc
2v46 2v47 2v48 2v49
2vhm 2vhn 2vho 2vhp
2z4k 2z4l 2z4m 2z4n
2zkq 2zkr
2zuo 2zv4 2zv5
3bz1 3bz2
3d5a 3d5b 3d5c 3d5d
3df1 3df2 3df3 3df4
3f1e 3f1f 3f1g 3f1h
"""

class join_fragment_files(object):
  def __init__(self, file_names):
    info = flex.std_string()
    info.append("REMARK JOINED FRAGMENT FILES (iotbx.pdb)")
    info.append("REMARK " + date_and_time())
    roots = []
    z = None
    from cctbx import crystal
    self.crystal_symmetry = crystal.symmetry()
    z_warning = 'REMARK ' \
      'Warning: CRYST1 Z field (columns 67-70) is not an integer: "%-4.4s"'
    for file_name in file_names:
      pdb_inp = iotbx.pdb.input(file_name=file_name)
      z_ = pdb_inp.extract_cryst1_z_columns()
      if (z_ is not None) :
        z_ = z_.strip()
        if (z_ != "") : z_ = int(z_)
        else : z_ = None
      else: z_ = None
      if z is None:
        z = z_
      else:
        z = max(z, z_)
      cs = pdb_inp.crystal_symmetry()
      info.append("REMARK %s" % show_string(file_name))
      if cs is not None and cs.unit_cell() is not None:
        info.append("REMARK %s" % iotbx.pdb.format_cryst1_record(cs, z=z_))
        self.crystal_symmetry = self.crystal_symmetry.join_symmetry(
          cs, force=True)
      roots.append(pdb_inp.construct_hierarchy())
    if self.crystal_symmetry.unit_cell() is not None:
      info.append(iotbx.pdb.format_cryst1_record(
        crystal_symmetry=self.crystal_symmetry, z=z))
    result = iotbx.pdb.hierarchy.join_roots(roots=roots)
    result.info.extend(info)
    result.reset_i_seq_if_necessary()
    self.joined = result

def merge_files_and_check_for_overlap (file_names, output_file,
    site_clash_cutoff=0.5, log=sys.stdout) :
  assert len(file_names) > 0
  merged_records = combine_unique_pdb_files(file_names)
  warnings = StringIO()
  merged_records.report_non_unique(out=warnings)
  merged_hierarchy = join_fragment_files(file_names).joined
  f = open(output_file, "w")
  f.write(merged_hierarchy.as_pdb_string())
  f.close()
  n_clashes = quick_clash_check(output_file,
    site_clash_cutoff=site_clash_cutoff,
    out=log)
  return n_clashes

def quick_clash_check (file_name, site_clash_cutoff=0.5, out=sys.stdout,
    show_outliers=5) :
  pdb_inp = input(file_name=file_name)
  pdb_atoms = pdb_inp.atoms_with_labels()
  xray_structure = pdb_inp.xray_structure_simple(
    cryst1_substitution_buffer_layer=10,
    enable_scattering_type_unknown=True)
  sites_frac = xray_structure.sites_frac()
  unit_cell = xray_structure.unit_cell()
  pair_asu_table = xray_structure.pair_asu_table(
    distance_cutoff=site_clash_cutoff)
  pair_sym_table = pair_asu_table.extract_pair_sym_table()
  atom_pairs = pair_sym_table.simple_edge_list()
  return len(atom_pairs)

standard_rhombohedral_space_group_symbols = [
"R 3 :H",
"R 3 :R",
"R -3 :H",
"R -3 :R",
"R 3 2 :H",
"R 3 2 :R",
"R 3 m :H",
"R 3 m :R",
"R 3 c :H",
"R 3 c :R",
"R -3 m :H",
"R -3 m :R",
"R -3 c :H",
"R -3 c :R"]
if ("set" in __builtins__):
  standard_rhombohedral_space_group_symbols = set(
    standard_rhombohedral_space_group_symbols)

def format_cryst1_sgroup(space_group_info):
  result = space_group_info.type().lookup_symbol()
  if (result in standard_rhombohedral_space_group_symbols):
    result = result[-1] + result[1:-3]
  def compress(s):
    if (len(s) > 11): return s.replace(" ", "")
    return s
  result = compress(result)
  if (len(result) > 11 and not space_group_info.group().is_centric()):
    from iotbx.mtz.extract_from_symmetry_lib import ccp4_symbol
    alt = ccp4_symbol(
      space_group_info=space_group_info,
      lib_name="syminfo.lib",
      require_at_least_one_lib=False)
    if (alt is not None and alt != result.replace(" ", "")):
      result = compress(alt)
  return result

def format_cryst1_record(crystal_symmetry, z=None):
  # CRYST1
  #  7 - 15       Real(9.3)      a             a (Angstroms).
  # 16 - 24       Real(9.3)      b             b (Angstroms).
  # 25 - 33       Real(9.3)      c             c (Angstroms).
  # 34 - 40       Real(7.2)      alpha         alpha (degrees).
  # 41 - 47       Real(7.2)      beta          beta (degrees).
  # 48 - 54       Real(7.2)      gamma         gamma (degrees).
  # 56 - 66       LString        sGroup        Space group.
  # 67 - 70       Integer        z             Z value.
  if (z is None): z = ""
  else: z = str(z)
  return ("CRYST1%9.3f%9.3f%9.3f%7.2f%7.2f%7.2f %-11.11s%4.4s" % (
    crystal_symmetry.unit_cell().parameters()
    + (format_cryst1_sgroup(
         space_group_info=crystal_symmetry.space_group_info()),
       z))).rstrip()

def format_scale_records(unit_cell=None,
                         fractionalization_matrix=None,
                         u=[0,0,0]):
  #  1 -  6       Record name    "SCALEn"       n=1, 2, or 3
  # 11 - 20       Real(10.6)     s[n][1]        Sn1
  # 21 - 30       Real(10.6)     s[n][2]        Sn2
  # 31 - 40       Real(10.6)     s[n][3]        Sn3
  # 46 - 55       Real(10.5)     u[n]           Un
  assert [unit_cell, fractionalization_matrix].count(None) == 1
  if (unit_cell is not None):
    f = unit_cell.fractionalization_matrix()
  else:
    assert len(fractionalization_matrix) == 9
    f = fractionalization_matrix
  assert len(u) == 3
  return (("SCALE1    %10.6f%10.6f%10.6f     %10.5f\n"
           "SCALE2    %10.6f%10.6f%10.6f     %10.5f\n"
           "SCALE3    %10.6f%10.6f%10.6f     %10.5f") % (
    f[0], f[1], f[2], u[0],
    f[3], f[4], f[5], u[1],
    f[6], f[7], f[8], u[2])).replace(" -0.000000", "  0.000000")

def format_cryst1_and_scale_records(
      crystal_symmetry=None,
      cryst1_z=None,
      write_scale_records=True,
      scale_fractionalization_matrix=None,
      scale_u=[0,0,0]):
  from cctbx import crystal
  from cctbx import sgtbx
  from cctbx import uctbx
  from scitbx import matrix
  if (crystal_symmetry is None):
    unit_cell = None
    space_group_info = None
  elif (isinstance(crystal_symmetry, crystal.symmetry)):
    unit_cell = crystal_symmetry.unit_cell()
    space_group_info = crystal_symmetry.space_group_info()
  elif (isinstance(crystal_symmetry, uctbx.ext.unit_cell)):
    unit_cell = crystal_symmetry
    space_group_info = None
  elif (isinstance(crystal_symmetry, (list, tuple))):
    assert len(crystal_symmetry) == 6 # unit cell parameters
    unit_cell = uctbx.unit_cell(crystal_symmetry)
    space_group_info = None
  else:
    raise ValueError("invalid crystal_symmetry object")
  if (unit_cell is None):
    if (scale_fractionalization_matrix is None):
      unit_cell = uctbx.unit_cell((1,1,1,90,90,90))
    else:
      unit_cell = uctbx.unit_cell(
        orthogonalization_matrix=matrix.sqr(
          scale_fractionalization_matrix).inverse())
  if (space_group_info is None):
    space_group_info = sgtbx.space_group_info(symbol="P 1")
  result = format_cryst1_record(
    crystal_symmetry=crystal.symmetry(
      unit_cell=unit_cell, space_group_info=space_group_info),
    z=cryst1_z)
  if (write_scale_records):
    if (scale_fractionalization_matrix is None):
      scale_fractionalization_matrix = unit_cell.fractionalization_matrix()
    result += "\n" + format_scale_records(
      fractionalization_matrix=scale_fractionalization_matrix,
      u=scale_u)
  return result

class read_scale_record(object):

  __slots__ = ["n", "r", "t"]

  def __init__(O, line, source_info=""):
    try: O.n = int(line[5:6])
    except ValueError: O.n = None
    if (O.n not in [1,2,3]):
      raise RuntimeError(
        "Unknown PDB record %s%s" % (show_string(line[:6]), source_info))
    values = []
    for i in [10,20,30,45]:
      fld = line[i:i+10]
      if (len(fld.strip()) == 0):
        value = 0
      else:
        try: value = float(fld)
        except ValueError:
          raise RuntimeError(
            "Not a floating-point value, PDB record %s%s:\n" % (
              show_string(line[:6]), source_info)
            + "  " + line + "\n"
            + "  %s%s" % (" "*i, "^"*10))
      values.append(value)
    O.r, O.t = values[:3], values[3]

class read_mtrix_record(read_scale_record):

  __slots__ = read_scale_record.__slots__ + [
    "serial_number", "coordinates_present"]

  def __init__(O, line, source_info=""):
    read_scale_record.__init__(O, line=line, source_info=source_info)
    O.serial_number = line[7:10]
    O.coordinates_present = (len(line) >= 60 and line[59] != " ")

def resseq_decode(s):
  try: return hy36decode(width=4, s="%4s" % s)
  except ValueError:
    raise ValueError('invalid residue sequence number: "%4s"' % s)

def resseq_encode(value):
  return hy36encode(width=4, value=value)

def encode_serial_number(width, value):
  if (isinstance(value, str)):
    assert len(value) <= width
    return value
  if (isinstance(value, int)):
    return hy36encode(width=width, value=value)
  raise RuntimeError("serial number value must be str or int.")

def make_atom_with_labels(
      xyz=None,
      sigxyz=None,
      occ=None,
      sigocc=None,
      b=None,
      sigb=None,
      uij=None,
      siguij=None,
      hetero=None,
      serial=None,
      name=None,
      segid=None,
      element=None,
      charge=None,
      model_id=None,
      chain_id=None,
      resseq=None,
      icode=None,
      altloc=None,
      resname=None):
  result = hierarchy.atom_with_labels()
  if (xyz is not None): result.xyz = xyz
  if (sigxyz is not None): result.sigxyz = sigxyz
  if (occ is not None): result.occ = occ
  if (sigocc is not None): result.sigocc = sigocc
  if (b is not None): result.b = b
  if (sigb is not None): result.sigb = sigb
  if (uij is not None): result.uij = uij
  if (siguij is not None): result.siguij = siguij
  if (hetero is not None): result.hetero = hetero
  if (serial is not None): result.serial = serial
  if (name is not None): result.name = name
  if (segid is not None): result.segid = segid
  if (element is not None): result.element = element
  if (charge is not None): result.charge = charge
  if (model_id is not None): result.model_id = model_id
  if (chain_id is not None): result.chain_id = chain_id
  if (resseq is not None): result.resseq = resseq
  if (icode is not None): result.icode = icode
  if (altloc is not None): result.altloc = altloc
  if (resname is not None): result.resname = resname
  return result

def get_file_summary (pdb_in, hierarchy=None) :
  if (hierarchy is None) :
    hierarchy = pdb_in.construct_hierarchy()
  counts = hierarchy.overall_counts()
  chain_ids = []
  for id in sorted(counts.chain_ids.keys()) :
    if (id == " ") :
      chain_ids.append("' '")
    else :
      chain_ids.append(id)
  info_list = [
    ("Number of atoms", counts.n_atoms),
    ("Number of chains", counts.n_chains),
    ("Chain IDs", ", ".join(chain_ids)),
    ("Alternate conformations", counts.n_alt_conf_pure),
  ]
  if (counts.n_models > 1) :
    info_list.insert(0, ("Number of models", counts.n_models))
  cl = counts.resname_classes
  if ("common_amino_acid" in cl) :
    info_list.append(("Amino acid residues", cl['common_amino_acid']))
  if ("common_nucleic_acid" in cl) or ("ccp4_mon_lib_rna_dna" in cl) :
    n_atoms = cl.get("common_nucleic_acid", 0) + \
              cl.get("ccp4_mon_lib_rna_dna", 0)
    info_list.append(("Nucleic acid residues", n_atoms))
  if ("common_water" in cl) :
    info_list.append(("Water molecules", cl['common_water']))
  if ("common_element" in cl) :
    names = []
    for name in counts.resnames :
      if (iotbx.pdb.common_residue_names_get_class(name)=="common_element") :
        names.append(name)
    value = "%d (%s)" % (cl['common_element'], ", ".join(names))
    info_list.append(("Elemental ions", value))
  if ("common_small_molecule" in cl) or ("other" in cl) :
    names = []
    for name in counts.resnames :
      res_class = iotbx.pdb.common_residue_names_get_class(name)
      if (res_class in ["common_small_molecule", "other"]) :
        names.append(name)
    n_atoms = cl.get("common_small_molecule", 0) + cl.get("other", 0)
    value = "%d (%s)" % (n_atoms, ", ".join(names))
    info_list.append(("Other molecules", value))
  atoms = hierarchy.atoms()
  b_factors = atoms.extract_b()
  mean_b = flex.mean(b_factors)
  min_b = flex.min(b_factors)
  max_b = flex.max(b_factors)
  info_list.append(("Mean isotropic B-factor", "%.2f (range: %.2f - %.2f)" %
    (mean_b, min_b, max_b)))
  if (min_b <= 0) :
    n_bad_adp = (b_factors <= 0).count(True)
    info_list.append(("Atoms with iso. B <= 0", "%d ***" % n_bad_adp))
  occ = atoms.extract_occ()
  if (flex.min(occ) <= 0) :
    n_zero_occ = (occ <= 0).count(True)
    info_list.append(("Atoms with zero ocupancy", "%d ***" % n_zero_occ))
  symm = pdb_in.crystal_symmetry()
  if (symm is not None) :
    space_group = symm.space_group_info()
    info_list.append(("Space group", str(space_group)))
    unit_cell = symm.unit_cell()
    if (unit_cell is not None) :
      uc_str = " ".join([ "%g" % x for x in unit_cell.parameters() ])
      info_list.append(("Unit cell", uc_str))
  return info_list

def show_file_summary (pdb_in, hierarchy=None, out=None) :
  if (out is None) :
    out = sys.stdout
  info = get_file_summary(pdb_in, hierarchy)
  label_width = max([ len(l) for l,v in info ]) + 2
  format = "%%-%ds %%s" % label_width
  for label, value in info :
    print >> out, format % (label + ":", str(value))
  return info
