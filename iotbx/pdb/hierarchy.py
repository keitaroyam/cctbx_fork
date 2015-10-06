from __future__ import division
import boost.python
ext = boost.python.import_ext("iotbx_pdb_hierarchy_ext")
from iotbx_pdb_hierarchy_ext import *

from cctbx.array_family import flex
from libtbx.str_utils import show_sorted_by_counts
from libtbx.utils import Sorry, plural_s, null_out
from libtbx import Auto, dict_with_default_0
from cStringIO import StringIO
import warnings
import math
import sys

class pickle_import_trigger(object): pass

level_ids = ["model", "chain", "residue_group", "atom_group", "atom"]

def _show_residue_group(rg, out, prefix):
  atoms = rg.atoms()
  if (atoms.size() == 0):
    ch = rg.parent()
    if (ch is None): ch = "  "
    else:            ch = "%s" % ch.id
    print >> out, prefix+'empty: "%s%s"' % (ch, rg.resid())
  else:
    def show_atom(atom):
      print >> out, prefix+'"%s"' % atom.format_atom_record(
        replace_floats_with=".*.")
    if (atoms.size() <= 3):
      for atom in atoms: show_atom(atom)
    else:
      show_atom(atoms[0])
      print >> out, prefix+'... %d atom%s not shown' % plural_s(
        atoms.size()-2)
      show_atom(atoms[-1])

class overall_counts(object):

  def __init__(self):
    self._errors = None
    self._warnings = None

  def show(self,
        out=None,
        prefix="",
        flag_errors=True,
        flag_warnings=True,
        residue_groups_max_show=10,
        duplicate_atom_labels_max_show=10):
    from iotbx.pdb import common_residue_names_get_class
    if (out is None): out = sys.stdout
    self._errors = []
    self._warnings = []
    def add_err(msg):
      if (flag_errors): print >> out, prefix+msg
      self._errors.append(msg.strip())
    def add_warn(msg):
      if (flag_warnings): print >> out, prefix+msg
      self._warnings.append(msg.strip())
    fmt = "%%%dd" % len(str(self.n_atoms))
    print >> out, prefix+"total number of:"
    if (self.n_duplicate_model_ids != 0):
      add_err("  ### ERROR: duplicate model ids ###")
    if (self.n_empty_models != 0):
      add_warn("  ### WARNING: empty model ###")
    print >> out, prefix+"  models:    ", fmt % self.n_models,
    infos = []
    if (self.n_duplicate_model_ids != 0):
      infos.append("%d with duplicate model id%s" % plural_s(
        self.n_duplicate_model_ids))
    if (self.n_empty_models != 0):
      infos.append("%d empty" % self.n_empty_models)
    if (len(infos) != 0): print >> out, "(%s)" % "; ".join(infos),
    print >> out
    if (self.n_duplicate_chain_ids != 0):
      add_warn("  ### WARNING: duplicate chain ids ###")
    if (self.n_empty_chains != 0):
      add_warn("  ### WARNING: empty chain ###")
    print >> out, prefix+"  chains:    ", fmt % self.n_chains,
    infos = []
    if (self.n_duplicate_chain_ids != 0):
      infos.append("%d with duplicate chain id%s" % plural_s(
        self.n_duplicate_chain_ids))
    if (self.n_empty_chains != 0):
      infos.append("%d empty" % self.n_empty_chains)
    if (self.n_explicit_chain_breaks != 0):
      infos.append("%d explicit chain break%s" % plural_s(
        self.n_explicit_chain_breaks))
    if (len(infos) != 0): print >> out, "(%s)" % "; ".join(infos),
    print >> out
    print >> out, prefix+"  alt. conf.:", fmt % self.n_alt_conf
    print >> out, prefix+"  residues:  ", fmt % (
      self.n_residues + self.n_residue_groups + self.n_empty_residue_groups),
    if (self.n_residue_groups != 0):
      print >> out, "(%d with mixed residue names)" % self.n_residue_groups,
    print >> out
    if (self.n_duplicate_atom_labels != 0):
      add_err("  ### ERROR: duplicate atom labels ###")
    print >> out, prefix+"  atoms:     ", fmt % self.n_atoms,
    if (self.n_duplicate_atom_labels != 0):
      print >> out, "(%d with duplicate labels)" %self.n_duplicate_atom_labels,
    print >> out
    print >> out, prefix+"  anisou:    ", fmt % self.n_anisou
    if (self.n_empty_residue_groups != 0):
      add_warn("  ### WARNING: empty residue_group ###")
      print >> out, prefix+"  empty residue_groups:", \
        fmt % self.n_empty_residue_groups
    if (self.n_empty_atom_groups != 0):
      add_warn("  ### WARNING: empty atom_group ###")
      print >> out, prefix+"  empty atom_groups:", \
        fmt % self.n_empty_atom_groups
    #
    c = self.element_charge_types
    print >> out, prefix+"number of atom element+charge types:", len(c)
    if (len(c) != 0):
      print >> out, prefix+"histogram of atom element+charge frequency:"
      show_sorted_by_counts(c.items(), out=out, prefix=prefix+"  ")
    #
    c = self.resname_classes
    print >> out, prefix+"residue name classes:",
    if (len(c) == 0): print >> out, None,
    print >> out
    show_sorted_by_counts(c.items(), out=out, prefix=prefix+"  ")
    #
    c = self.chain_ids
    print >> out, prefix+"number of chain ids: %d" % len(c)
    if (len(c) != 0):
      print >> out, prefix+"histogram of chain id frequency:"
      show_sorted_by_counts(c.items(), out=out, prefix=prefix+"  ")
    #
    c = self.alt_conf_ids
    print >> out, prefix+"number of alt. conf. ids: %d" % len(c)
    if (len(c) != 0):
      print >> out, prefix+"histogram of alt. conf. id frequency:"
      show_sorted_by_counts(c.items(), out=out, prefix=prefix+"  ")
      #
      fmt = "%%%dd" % len(str(max(
        self.n_alt_conf_none,
        self.n_alt_conf_pure,
        self.n_alt_conf_proper,
        self.n_alt_conf_improper)))
      print >> out, prefix+"residue alt. conf. situations:"
      print >> out, prefix+"  pure main conf.:    ", fmt%self.n_alt_conf_none
      print >> out, prefix+"  pure alt. conf.:    ", fmt%self.n_alt_conf_pure
      print >> out, prefix+"  proper alt. conf.:  ", fmt%self.n_alt_conf_proper
      if (self.n_alt_conf_improper != 0):
        add_err("  ### ERROR: improper alt. conf. ###")
      print >> out, prefix+"  improper alt. conf.:", \
        fmt % self.n_alt_conf_improper
      self.show_chains_with_mix_of_proper_and_improper_alt_conf(
        out=out, prefix=prefix)
    #
    c = self.resnames
    print >> out, prefix+"number of residue names: %d" % len(c)
    if (len(c) != 0):
      print >> out, prefix+"histogram of residue name frequency:"
      annotation_appearance = {
        "common_amino_acid": None,
        "modified_amino_acid": "   modified amino acid",
        "common_rna_dna": None,
        "modified_rna_dna": "   modified rna/dna",
        "common_water": "   common water",
        "common_small_molecule": "   common small molecule",
        "common_element": "   common element",
        "other": "   other"
      }
      show_sorted_by_counts(c.items(), out=out, prefix=prefix+"  ",
        annotations=[
          annotation_appearance[common_residue_names_get_class(name=name)]
            for name in c.keys()])
    #
    if (len(self.consecutive_residue_groups_with_same_resid) != 0):
      add_warn("### WARNING: consecutive residue_groups with same resid ###")
    self.show_consecutive_residue_groups_with_same_resid(
      out=out, prefix=prefix, max_show=residue_groups_max_show)
    #
    if (len(self.residue_groups_with_multiple_resnames_using_same_altloc)!= 0):
      add_err("### ERROR: residue group with multiple resnames using"
        " same altloc ###")
      self.show_residue_groups_with_multiple_resnames_using_same_altloc(
        out=out, prefix=prefix, max_show=residue_groups_max_show)
    #
    self.show_duplicate_atom_labels(
      out=out, prefix=prefix, max_show=duplicate_atom_labels_max_show)

  def as_str(self,
        prefix="",
        residue_groups_max_show=10,
        duplicate_atom_labels_max_show=10):
    out = StringIO()
    self.show(
      out=out,
      prefix=prefix,
      residue_groups_max_show=residue_groups_max_show,
      duplicate_atom_labels_max_show=duplicate_atom_labels_max_show)
    return out.getvalue()

  def errors(self):
    if (self._errors is None): self.show(out=null_out())
    return self._errors

  def warnings(self):
    if (self._warnings is None): self.show(out=null_out())
    return self._warnings

  def errors_and_warnings(self):
    return self.errors() + self.warnings()

  def show_improper_alt_conf(self, out=None, prefix=""):
    if (self.n_alt_conf_improper == 0): return
    if (out is None): out = sys.stdout
    for residue_group,label in [(self.alt_conf_proper, "proper"),
                                (self.alt_conf_improper, "improper")]:
      if (residue_group is None): continue
      print >> out, prefix+"residue with %s altloc" % label
      for ag in residue_group.atom_groups():
        for atom in ag.atoms():
          print >> out, prefix+'  "%s"' % atom.format_atom_record(
            replace_floats_with=".*.")

  def raise_improper_alt_conf_if_necessary(self):
    sio = StringIO()
    self.show_improper_alt_conf(out=sio)
    msg = sio.getvalue()
    if (len(msg) != 0): raise Sorry(msg.rstrip())

  def show_chains_with_mix_of_proper_and_improper_alt_conf(self,
        out=None,
        prefix=""):
    if (out is None): out = sys.stdout
    n = self.n_chains_with_mix_of_proper_and_improper_alt_conf
    print >> out, \
      prefix+"chains with mix of proper and improper alt. conf.:", n
    if (n != 0): prefix += "  "
    self.show_improper_alt_conf(out=out, prefix=prefix)

  def raise_chains_with_mix_of_proper_and_improper_alt_conf_if_necessary(self):
    if (self.n_chains_with_mix_of_proper_and_improper_alt_conf == 0):
      return
    sio = StringIO()
    self.show_chains_with_mix_of_proper_and_improper_alt_conf(out=sio)
    raise Sorry(sio.getvalue().rstrip())

  def show_consecutive_residue_groups_with_same_resid(self,
        out=None,
        prefix="",
        max_show=10):
    cons = self.consecutive_residue_groups_with_same_resid
    if (len(cons) == 0): return
    if (out is None): out = sys.stdout
    print >> out, \
      prefix+"number of consecutive residue groups with same resid: %d" % \
        len(cons)
    if (max_show is None): max_show = len(cons)
    elif (max_show <= 0): return
    delim = prefix+"  "+"-"*42
    prev_rg = None
    for rgs in cons[:max_show]:
      for next,rg in zip(["", "next "], rgs):
        if (    prev_rg is not None
            and prev_rg.memory_id() == rg.memory_id()): continue
        elif (next == "" and prev_rg is not None):
          print >> out, delim
        prev_rg = rg
        print >> out, prefix+"  %sresidue group:" % next
        _show_residue_group(rg=rg, out=out, prefix=prefix+"    ")
    if (len(cons) > max_show):
      print >> out, delim
      print >> out, prefix + "  ... %d remaining instance%s not shown" % \
        plural_s(len(cons)-max_show)

  def show_residue_groups_with_multiple_resnames_using_same_altloc(self,
        out=None,
        prefix="",
        max_show=10):
    rgs = self.residue_groups_with_multiple_resnames_using_same_altloc
    if (len(rgs) == 0): return
    print >> out, prefix+"residue groups with multiple resnames using" \
      " same altloc:", len(rgs)
    if (max_show is None): max_show = len(cons)
    elif (max_show <= 0): return
    for rg in rgs[:max_show]:
      print >> out, prefix+"  residue group:"
      _show_residue_group(rg=rg, out=out, prefix=prefix+"    ")
    if (len(rgs) > max_show):
      print >> out, prefix + "  ... %d remaining instance%s not shown" % \
        plural_s(len(rgs)-max_show)

  def \
    raise_residue_groups_with_multiple_resnames_using_same_altloc_if_necessary(
        self, max_show=10):
    sio = StringIO()
    self.show_residue_groups_with_multiple_resnames_using_same_altloc(
      out=sio, max_show=max_show)
    msg = sio.getvalue()
    if (len(msg) != 0): raise Sorry(msg.rstrip())

  def show_duplicate_atom_labels(self, out=None, prefix="", max_show=10):
    dup = self.duplicate_atom_labels
    if (len(dup) == 0): return
    if (out is None): out = sys.stdout
    fmt = "%%%dd" % len(str(self.n_duplicate_atom_labels))
    print >> out, prefix+"number of groups of duplicate atom labels:", \
      fmt % len(dup)
    print >> out, prefix+"  total number of affected atoms:         ", \
      fmt % self.n_duplicate_atom_labels
    if (max_show is None): max_show = len(dup)
    elif (max_show <= 0): return
    for atoms in dup[:max_show]:
      prfx = "  group "
      for atom in atoms:
        print >> out, prefix+prfx+'"%s"' % atom.format_atom_record(
          replace_floats_with=".*.")
        prfx = "        "
    if (len(dup) > max_show):
      print >> out, prefix+"  ... %d remaining group%s not shown" % \
        plural_s(len(dup)-max_show)

  def raise_duplicate_atom_labels_if_necessary(self, max_show=10):
    sio = StringIO()
    self.show_duplicate_atom_labels(out=sio, max_show=max_show)
    msg = sio.getvalue()
    if (len(msg) != 0): raise Sorry(msg.rstrip())

class __hash_eq_mixin(object):

  def __hash__(self):
    return hash(self.memory_id())

  def __eq__(self, other):
    if (isinstance(other, self.__class__)):
      return (self.memory_id() == other.memory_id())
    return False

  def __ne__(self, other):
    return not ( self == other )

class _(boost.python.injector, ext.root, __hash_eq_mixin):
  __doc__ = """
  Root node of the PDB hierarchy object.  This is returned by the method
  construct_hierarchy() of the PDB/mmCIF input objects, but it may also be
  created programatically.  Note that it does not contain any reference to
  crystal symmetry or source scattering information, meaning that in practice
  it must often be tracked alongside an equivalent cctbx.xray.structure object.
  Pickling is supported, simply by writing out and reading back the PDB-format
  representation of the hierarchy.

  Examples
  --------
  >>> hierarchy = iotbx.pdb.hierarchy.root()
  """

  def __getstate__(self):
    version = 2
    pdb_string = StringIO()
    self._as_pdb_string_cstringio(
      cstringio=pdb_string,
      append_end=True,
      interleaved_conf=0,
      atoms_reset_serial_first_value=None,
      atom_hetatm=True,
      sigatm=True,
      anisou=True,
      siguij=True)
    return (version, pickle_import_trigger(), self.info, pdb_string.getvalue())

  def __setstate__(self, state):
    assert len(state) >= 3
    version = state[0]
    if   (version == 1): assert len(state) == 3
    elif (version == 2): assert len(state) == 4
    else: raise RuntimeError("Unknown version of pickled state.")
    self.info = state[-2]
    import iotbx.pdb
    models = iotbx.pdb.input(
      source_info="pickle",
      lines=flex.split_lines(state[-1])).construct_hierarchy().models()
    self.pre_allocate_models(number_of_additional_models=len(models))
    for model in models:
      self.append_model(model=model)

  def chains(self):
    """
    Iterate over all chains in all models.
    """
    for model in self.models():
      for chain in model.chains():
        yield chain

  def residue_groups(self):
    """Iterate over all residue groups (by model and then chain)"""
    for model in self.models():
      for chain in model.chains():
        for rg in chain.residue_groups():
          yield rg

  def atom_groups(self):
    """
    Iterate over all atom groups (by model, then chain, then residue group)
    """
    for model in self.models():
      for chain in model.chains():
        for rg in chain.residue_groups():
          for ag in rg.atom_groups():
            yield ag

  def only_model(self):
    assert self.models_size() == 1
    return self.models()[0]

  def only_chain(self):
    return self.only_model().only_chain()

  def only_residue_group(self):
    return self.only_chain().only_residue_group()

  def only_conformer(self):
    return self.only_chain().only_conformer()

  def only_atom_group(self):
    return self.only_residue_group().only_atom_group()

  def only_residue(self):
    return self.only_conformer().only_residue()

  def only_atom(self):
    return self.only_atom_group().only_atom()

  def overall_counts(self):
    """
    Calculate basic statistics for contents of the PDB hierarchy, including
    number of residues of each type.

    :returns: iotbx.pdb.hierarchy.overall_counts object
    """
    result = overall_counts()
    self.get_overall_counts(result)
    return result

  def show(self,
        out=None,
        prefix="",
        level_id=None,
        level_id_exception=ValueError):
    """
    Display a summary of hierarchy contents.
    """
    if (level_id == None): level_id = "atom"
    try: level_no = level_ids.index(level_id)
    except ValueError:
      raise level_id_exception('Unknown level_id="%s"' % level_id)
    if (out is None): out = sys.stdout
    if (self.models_size() == 0):
      print >> out, prefix+'### WARNING: empty hierarchy ###'
    model_ids = dict_with_default_0()
    for model in self.models():
      model_ids[model.id] += 1
    for model in self.models():
      chains = model.chains()
      if (model_ids[model.id] != 1):
        s = "  ### ERROR: duplicate model id ###"
      else: s = ""
      print >> out, prefix+'model id="%s"' % model.id, \
        "#chains=%d%s" % (len(chains), s)
      if (level_no == 0): continue
      if (model.chains_size() == 0):
        print >> out, prefix+'  ### WARNING: empty model ###'
      model_chain_ids = dict_with_default_0()
      for chain in chains:
        model_chain_ids[chain.id] += 1
      for chain in chains:
        rgs = chain.residue_groups()
        if (model_chain_ids[chain.id] != 1):
          s = "  ### WARNING: duplicate chain id ###"
        else: s = ""
        print >> out, prefix+'  chain id="%s"' % chain.id, \
          "#residue_groups=%d%s" % (len(rgs), s)
        if (level_no == 1): continue
        if (chain.residue_groups_size() == 0):
          print >> out, prefix+'    ### WARNING: empty chain ###'
        suppress_chain_break = True
        prev_resid = ""
        for rg in rgs:
          if (not rg.link_to_previous and not suppress_chain_break):
            print >> out, prefix+"    ### chain break ###"
          suppress_chain_break = False
          ags = rg.atom_groups()
          resnames = set()
          for ag in rg.atom_groups():
            resnames.add(ag.resname)
          infos = []
          if (len(resnames) > 1): infos.append("with mixed residue names")
          resid = rg.resid()
          if (prev_resid == resid): infos.append("same as previous resid")
          prev_resid = resid
          if (len(infos) != 0): s = "  ### Info: %s ###" % "; ".join(infos)
          else: s = ""
          print >> out, prefix+'    resid="%s"' % resid, \
            "#atom_groups=%d%s" % (len(ags), s)
          if (level_no == 2): continue
          if (rg.atom_groups_size() == 0):
            print >> out, prefix+'      ### WARNING: empty residue_group ###'
          for ag in ags:
            atoms = ag.atoms()
            print >> out, prefix+'      altloc="%s"' % ag.altloc, \
              'resname="%s"' % ag.resname, \
              "#atoms=%d" % len(atoms)
            if (level_no == 3): continue
            if (ag.atoms_size() == 0):
              print >> out, prefix+'        ### WARNING: empty atom_group ###'
            for atom in atoms:
              print >> out, prefix+'        "%s"' % atom.name

  def as_str(self,
        prefix="",
        level_id=None,
        level_id_exception=ValueError):
    """
    Alias for show().
    """
    out = StringIO()
    self.show(
      out=out,
      prefix=prefix,
      level_id=level_id,
      level_id_exception=level_id_exception)
    return out.getvalue()

  def as_pdb_string(self,
        crystal_symmetry=None,
        cryst1_z=None,
        write_scale_records=True,
        append_end=False,
        interleaved_conf=0,
        atoms_reset_serial_first_value=None,
        atom_hetatm=True,
        sigatm=True,
        anisou=True,
        siguij=True,
        output_break_records=True, # TODO deprecate
        cstringio=None,
        return_cstringio=Auto):
    """
    Generate complete PDB-format string representation.  External crystal
    symmetry is strongly recommended if this is being output to a file.

    :param crystal_symmetry: cctbx.crystal.symmetry object or equivalent (such
      as an xray.structure object or Miller array)
    :param write_scale_records: write fractional scaling records (SCALE) if
      crystal symmetry is provided
    :param anisou: write ANISOU records for anisotropic atoms
    :param sigatm: write SIGATM records if applicable
    :param siguij: write SIGUIJ records if applicable
    :returns: Python str
    """
    if (cstringio is None):
      cstringio = StringIO()
      if (return_cstringio is Auto):
        return_cstringio = False
    elif (return_cstringio is Auto):
      return_cstringio = True
    if (crystal_symmetry is not None or cryst1_z is not None):
      from iotbx.pdb import format_cryst1_and_scale_records
      print >> cstringio, format_cryst1_and_scale_records(
        crystal_symmetry=crystal_symmetry,
        cryst1_z=cryst1_z,
        write_scale_records=write_scale_records)
    self._as_pdb_string_cstringio(
      cstringio=cstringio,
      append_end=append_end,
      interleaved_conf=interleaved_conf,
      atoms_reset_serial_first_value=atoms_reset_serial_first_value,
      atom_hetatm=atom_hetatm,
      sigatm=sigatm,
      anisou=anisou,
      siguij=siguij,
      output_break_records=output_break_records)
    if (return_cstringio):
      return cstringio
    return cstringio.getvalue()

  def as_pdb_input (self, crystal_symmetry=None) :
    """
    Generate corresponding pdb.input object.
    """
    import iotbx.pdb
    pdb_str = self.as_pdb_string(crystal_symmetry=crystal_symmetry)
    pdb_inp = iotbx.pdb.input(
      source_info="pdb_hierarchy",
      lines=flex.split_lines(pdb_str))
    return pdb_inp

  def as_cif_input(self, crystal_symmetry=None):
    """
    Generate corresponding mmcif input object.
    """
    import iotbx.cif.model
    from iotbx.pdb import mmcif
    cif_block = self.as_cif_block(crystal_symmetry=crystal_symmetry)
    cif_model = iotbx.cif.model.cif()
    cif_model['pdb_hierarchy'] = cif_block
    cif_input = mmcif.cif_input(cif_object=cif_model)
    return cif_input

  def extract_xray_structure(self, crystal_symmetry=None) :
    """
    Generate the equivalent cctbx.xray.structure object.  If the crystal
    symmetry is not provided, this will be placed in a P1 box.  In practice it
    is usually best to keep the original xray structure object around, but this
    method is helpful in corner cases.
    """
    return self.as_pdb_input(crystal_symmetry).xray_structure_simple()

  def adopt_xray_structure(self, xray_structure, assert_identical_id_str=True):
    """
    Apply the current (refined) atomic parameters from the cctbx.xray.structure
    object to the atoms in the PDB hierarchy.  This will fail if the labels of
    the scatterers do not match the atom labels.
    """
    from iotbx.pdb import common_residue_names_get_class as gc
    from cctbx import adptbx
    if(self.atoms().size() != xray_structure.scatterers().size()):
      raise RuntimeError("Incompatible size of hierarchy and scatterers array.")
    awl = self.atoms_with_labels()
    scatterers = xray_structure.scatterers()
    uc = xray_structure.unit_cell()
    orth = uc.orthogonalize
    def set_attr(sc, a):
      a.set_xyz(new_xyz=orth(sc.site))
      a.set_occ(new_occ=sc.occupancy)
      if(sc.u_iso != -1):
        a.set_b(new_b=adptbx.u_as_b(sc.u_iso))
      if(sc.flags.use_u_aniso() and sc.u_star != (-1.0, -1.0, -1.0, -1.0, -1.0, -1.0)):
        a.set_uij(new_uij = adptbx.u_star_as_u_cart(uc,sc.u_star))
      else:
        a.uij_erase()
      a.set_fp(new_fp=sc.fp)
      a.set_fdp(new_fdp=sc.fdp)
      a.set_element(sc.element_symbol())
    for sc, a in zip(scatterers, awl):
      id_str = a.id_str()
      resname_from_sc = id_str[10:13]
      cl1 = gc(resname_from_sc)
      cl2 = gc(a.resname)
      if([cl1,cl2].count("common_water")==2 or
         (id_str.strip()=="" and cl2=="common_water")):
        assert sc.scattering_type.strip().lower() in ["o","h","d"]
        set_attr(sc=sc, a=a)
      else:
        # XXX may be fix it when creating IS ? or make another special case?
        if(assert_identical_id_str and sc.scattering_type[:2] != "IS"):
          l1 = sc.label.replace("pdb=","").replace(" ","")
          l2 = a.id_str().replace("pdb=","").replace(" ","")
          if(l1 != l2):
            raise RuntimeError("Mismatch: \n %s \n %s \n"%(sc.label,a.id_str()))
        set_attr(sc=sc, a=a)

  def expand_to_p1(self, crystal_symmetry):
    # ANISIU will be invalid
    import string
    import scitbx.matrix
    r = root()
    m = model()
    idl = [i for i in string.ascii_lowercase]
    idu = [i for i in string.ascii_uppercase]
    taken = [c.id for c in self.chains()]
    n_atoms = []
    for m_ in self.models():
      for smx in crystal_symmetry.space_group().smx():
        m3 = smx.r().as_double()
        m3 = scitbx.matrix.sqr(m3)
        t = smx.t().as_double()
        t = scitbx.matrix.col((t[0],t[1],t[2]))
        for c_ in m_.chains():
          n_at = len(c_.atoms())
          if(not n_at in n_atoms): n_atoms.append(n_at)
          c_ = c_.detached_copy()
          xyz = c_.atoms().extract_xyz()
          xyz = crystal_symmetry.unit_cell().fractionalize(xyz)
          new_xyz = crystal_symmetry.unit_cell().orthogonalize(m3.elems*xyz+t)
          c_.atoms().set_xyz(new_xyz)
          #
          if(not (smx.r().is_unit_mx() and smx.t().is_zero())):
            found = False
            for idu_ in idu:
              for idl_ in idl:
                id_ = idu_+idl_
                if(not id_ in taken):
                  taken.append(id_)
                  found = id_
                  break
              if(found): break
            c_.id = found
          #
          m.append_chain(c_)
    r.append_model(m)
    return r

  def write_pdb_file(self,
        file_name,
        open_append=False,
        crystal_symmetry=None,
        cryst1_z=None,
        write_scale_records=True,
        append_end=False,
        interleaved_conf=0,
        atoms_reset_serial_first_value=None,
        atom_hetatm=True,
        sigatm=True,
        anisou=True,
        siguij=True,
        link_records=None,
        ):
    if link_records:
      if (open_append): mode = "ab"
      else:             mode = "wb"
      print >> open(file_name, mode), link_records
      open_append = True
    if (crystal_symmetry is not None or cryst1_z is not None):
      from iotbx.pdb import format_cryst1_and_scale_records
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
      interleaved_conf=interleaved_conf,
      atoms_reset_serial_first_value=atoms_reset_serial_first_value,
      atom_hetatm=atom_hetatm,
      sigatm=sigatm,
      anisou=anisou,
      siguij=siguij,
      )

  def as_cif_block(self, crystal_symmetry=None):
    from iotbx.pdb.mmcif import pdb_hierarchy_as_cif_block
    return pdb_hierarchy_as_cif_block(
      self, crystal_symmetry=crystal_symmetry).cif_block

  def write_mmcif_file(self,
                       file_name,
                       crystal_symmetry=None,
                       data_block_name=None):
    import iotbx.cif.model
    cif_object = iotbx.cif.model.cif()
    if data_block_name is None:
      data_block_name = "phenix"
    cif_object[data_block_name] = self.as_cif_block(
      crystal_symmetry=crystal_symmetry)
    f = open(file_name, "wb")
    print >> f, cif_object
    f.close()

  def atoms_with_labels(self):
    """
    Generator for atom_with_labels objects, presented in the same order as
    the array returned by the atoms() method.
    """
    for model in self.models():
      for chain in model.chains():
        is_first_in_chain = True
        for rg in chain.residue_groups():
          is_first_after_break = not (is_first_in_chain or rg.link_to_previous)
          for ag in rg.atom_groups():
            for atom in ag.atoms():
              yield atom_with_labels(
                atom=atom,
                model_id=model.id,
                chain_id=chain.id,
                resseq=rg.resseq,
                icode=rg.icode,
                altloc=ag.altloc,
                resname=ag.resname,
                is_first_in_chain=is_first_in_chain,
                is_first_after_break=is_first_after_break)
              is_first_in_chain = False
              is_first_after_break = False

  def get_conformer_indices (self) :
    n_seq = self.atoms_size()
    conformer_indices = flex.size_t(n_seq, 0)
    altloc_indices = self.altloc_indices()
    if ("" in altloc_indices): p = 0
    else:                      p = 1
    altlocs = sorted(altloc_indices.keys())
    for i,altloc in enumerate(altlocs):
      if (altloc == ""): continue
      conformer_indices.set_selected(altloc_indices[altloc], i+p)
    return conformer_indices

  def transfer_chains_from_other(self, other):
    from iotbx.pdb import hy36encode
    i_model = 0
    other_models = other.models()
    for md,other_md in zip(self.models(), other_models):
      i_model += 1
      md.id = hy36encode(width=4, value=i_model)
      md.transfer_chains_from_other(other=other_md)
    msz, omsz = self.models_size(), other.models_size()
    if (omsz > msz):
      for other_md in other_models[msz:]:
        i_model += 1
        md = model(id = hy36encode(width=4, value=i_model))
        md.transfer_chains_from_other(other=other_md)
        self.append_model(model=md)

  def atom_selection_cache(self, special_position_settings=None):
    from iotbx.pdb.atom_selection import cache
    return cache(root=self,
      special_position_settings=special_position_settings)

  def occupancy_groups_simple(self, common_residue_name_class_only=None,
                              always_group_adjacent=True,
                              ignore_hydrogens=True):
    if(ignore_hydrogens):
      sentinel = self.atoms().reset_tmp_for_occupancy_groups_simple()
    else:
      sentinel = self.atoms().reset_tmp(first_value=0, increment=1)
    result = []
    for chain in self.chains():
      if(common_residue_name_class_only is None):
        if(chain.is_protein()):
          common_residue_name_class_only = "common_amino_acid"
        if(chain.is_na()):
          common_residue_name_class_only = "common_rna_dna"
      result.extend(chain.occupancy_groups_simple(
        common_residue_name_class_only=common_residue_name_class_only,
        always_group_adjacent=always_group_adjacent))
    del sentinel
    return result

  def chunk_selections(self, residues_per_chunk):
    result = []
    if(residues_per_chunk<1): return result
    for model in self.models():
      for chain in model.chains():
        residue_range_sel = flex.size_t()
        cntr = 0
        for rg in chain.residue_groups():
          i_seqs = rg.atoms().extract_i_seq()
          last_added=True
          if(cntr!=residues_per_chunk):
            residue_range_sel.extend(i_seqs)
            last_added=False
          else:
            result.append(residue_range_sel)
            residue_range_sel = flex.size_t()
            residue_range_sel.extend(i_seqs)
            cntr = 0
            last_added=False
          cntr += 1
        if(len(result)==0 or not last_added):
          assert residue_range_sel.size()>0
          result.append(residue_range_sel)
    return result

  def distance_based_simple_two_way_bond_sets(self,
        fallback_expected_bond_length=1.4,
        fallback_search_max_distance=2.5) :
    from cctbx.crystal import distance_based_connectivity
    atoms = self.atoms().deep_copy() # XXX potential bottleneck
    atoms.set_chemical_element_simple_if_necessary()
    sites_cart = atoms.extract_xyz()
    elements = atoms.extract_element()
    conformer_indices = self.get_conformer_indices()
    return distance_based_connectivity.build_simple_two_way_bond_sets(
      sites_cart=sites_cart,
      elements=elements,
      conformer_indices=conformer_indices,
      fallback_expected_bond_length=fallback_expected_bond_length,
      fallback_search_max_distance=fallback_search_max_distance)

  def reset_i_seq_if_necessary (self) :
    atoms = self.atoms()
    i_seqs = atoms.extract_i_seq()
    if (i_seqs.all_eq(0)) :
      atoms.reset_i_seq()

  def get_peptide_c_alpha_selection(self):
    """
    Extract atom selection (flex.size_t) for protein C-alpha atoms.
    """
    result = flex.size_t()
    import iotbx.pdb
    get_class = iotbx.pdb.common_residue_names_get_class
    i_seqs = self.atoms().extract_i_seq()
    if(i_seqs.size()>1): assert i_seqs[1:].all_ne(0)
    for model in self.models():
      for chain in model.chains():
        for rg in chain.residue_groups():
          for ag in rg.atom_groups():
            if(get_class(ag.resname) == "common_amino_acid"):
              for atom in ag.atoms():
                if(atom.name.strip() == "CA"):
                  result.append(atom.i_seq)
    return result

  def contains_protein (self) :
    """
    Inspect residue names (stored in atom_group objects) to determine if any of
    them are protein.
    """
    for model in self.models() :
      for chain in self.chains() :
        if chain.is_protein() : return True
    return False

  def contains_nucleic_acid (self) :
    """
    Inspect residue names (stored in atom_group objects) to determine if any of
    them are RNA or DNA.
    """
    import iotbx.pdb
    for model in self.models() :
      for chain in self.chains() :
        if chain.is_na() : return True
    return False

  def contains_rna (self) :
    """
    Inspect residue names (stored in atom_group objects) to determine if any of
    them are RNA.
    """
    import iotbx.pdb
    get_class = iotbx.pdb.common_residue_names_get_class
    for model in self.models():
      for chain in model.chains():
        for rg in chain.residue_groups():
          for ag in rg.atom_groups():
            if ((get_class(ag.resname) == "common_rna_dna") and
                (not "D" in ag.resname.upper())) :
              return True
    return False

  def remove_hd (self, reset_i_seq=False) :
    """
    Remove all hydrogen/deuterium atoms in-place.  Returns the number of atoms
    deleted.
    """
    n_removed = 0
    for pdb_model in self.models() :
      for pdb_chain in pdb_model.chains() :
        for pdb_residue_group in pdb_chain.residue_groups() :
          for pdb_atom_group in pdb_residue_group.atom_groups() :
            for pdb_atom in pdb_atom_group.atoms() :
              if (pdb_atom.element.strip().upper() in ["H","D"]) :
                pdb_atom_group.remove_atom(pdb_atom)
                n_removed += 1
            if (pdb_atom_group.atoms_size() == 0) :
              pdb_residue_group.remove_atom_group(pdb_atom_group)
          if (pdb_residue_group.atom_groups_size() == 0) :
            pdb_chain.remove_residue_group(pdb_residue_group)
        if (pdb_chain.residue_groups_size() == 0) :
          pdb_model.remove_chain(pdb_chain)
      if (pdb_model.chains_size() == 0) :
        self.remove_model(pdb_model)
    if (reset_i_seq) :
      self.atoms().reset_i_seq()
    return n_removed

class _(boost.python.injector, ext.model, __hash_eq_mixin):
  """
  Class representing MODEL blocks in a PDB file (or equivalent mmCIF).  There
  will always be at least one of these in a hierarchy root extracted from a
  PDB file even if no MODEL records are present.

  Example
  -------
  >>> hierarchy = iotbx.pdb.hierarchy.root()
  >>> model = iotbx.pdb.hierarchy.model(id="1")
  >>> hierarchy.append_model(model)
  >>> model = hierarchy.only_model()
  """

  def residue_groups(self):
    for chain in self.chains():
      for rg in chain.residue_groups():
        yield rg

  def atom_groups(self):
    for chain in self.chains():
      for rg in chain.residue_groups():
        for ag in rg.atom_groups():
          yield ag

  def only_chain(self):
    assert self.chains_size() == 1
    return self.chains()[0]

  def only_residue_group(self):
    return self.only_chain().only_residue_group()

  def only_conformer(self):
    return self.only_chain().only_conformer()

  def only_atom_group(self):
    return self.only_residue_group().only_atom_group()

  def only_residue(self):
    return self.only_conformer().only_residue()

  def only_atom(self):
    return self.only_atom_group().only_atom()

class _(boost.python.injector, ext.chain, __hash_eq_mixin):
  """
  Class representing a continuous chain of atoms, as defined by the combination
  of chain ID field and TER records (or the chain index in mmCIF format).  Note
  that this does not necessarily correspond to a covalently linked entity, as
  it may be used to group various heteroatoms (including water), but
  chemically distinct protein or nucleic acid chains will typically be
  grouped into exactly one chain object apiece.
  """

  def atom_groups(self):
    for rg in self.residue_groups():
      for ag in rg.atom_groups():
        yield ag

  def only_residue_group(self):
    assert self.residue_groups_size() == 1
    return self.residue_groups()[0]

  def only_conformer(self):
    conformers = self.conformers()
    assert len(conformers) == 1
    return conformers[0]

  def only_atom_group(self):
    return self.only_residue_group().only_atom_group()

  def only_residue(self):
    return self.only_conformer().only_residue()

  def only_atom(self):
    return self.only_atom_group().only_atom()

  def residues(self):
    return self.only_conformer().residues()

  def occupancy_groups_simple(self, common_residue_name_class_only=None,
        always_group_adjacent=True):
    result = []
    residue_groups = self.residue_groups()
    n_rg = len(residue_groups)
    done = [False] * n_rg
    def process_range(i_begin, i_end):
      isolated_var_occ = []
      groups = {}
      for i_rg in xrange(i_begin, i_end):
        done[i_rg] = True
        rg = residue_groups[i_rg]
        for ag in residue_groups[i_rg].atom_groups():
          altloc = ag.altloc
          if (altloc == ""):
            for atom in ag.atoms():
              if (atom.tmp < 0): continue
              if (atom.occ > 0 and atom.occ < 1):
                isolated_var_occ.append(atom.tmp)
          else:
            group = []
            for atom in ag.atoms():
              if (atom.tmp < 0): continue
              group.append(atom.tmp)
            if (len(group) != 0):
              groups.setdefault(altloc, []).extend(group)
      groups = groups.values()
      if (len(groups) != 0):
        for group in groups: group.sort()
        def group_cmp(a, b): return cmp(a[0], b[0])
        groups.sort(group_cmp)
        result.append(groups)
      for i in isolated_var_occ:
        result.append([[i]])
    for i_begin,i_end in self.find_pure_altloc_ranges(
          common_residue_name_class_only=common_residue_name_class_only):
      # use always_group_adjacent
      do_this_step = True
      nc = None
      for i_rg in xrange(i_begin, i_end):
        rg = residue_groups[i_rg]
        n_conf = len(residue_groups[i_rg].conformers())
        if(nc is None): nc = n_conf
        else:
          if(nc != n_conf):
            do_this_step = False
      #
      if(always_group_adjacent):
        process_range(i_begin, i_end)
      else:
        if(do_this_step):
          process_range(i_begin, i_end)
    for i_rg in xrange(n_rg):
      if (done[i_rg]): continue
      process_range(i_rg, i_rg+1)
    def groups_cmp(a, b):
      return cmp(a[0][0], b[0][0])
    result.sort(groups_cmp)
    return result

  def get_residue_names_and_classes (self) :
    """
    Extract the residue names and counts of each residue type (protein,
    nucleic acid, etc) within the chain.

    :returns: a tuple containing a list of residue names, and a dictionary of
      residue type frequencies.
    """
    from iotbx.pdb import common_residue_names_get_class
    from iotbx.pdb import residue_name_plus_atom_names_interpreter
    rn_seq = []
    residue_classes = dict_with_default_0()
    for residue_group in self.residue_groups():
      # XXX should we iterate over all atom_groups or just take the first one?
      #for atom_group in residue_group.atom_groups():
      atom_group = residue_group.atom_groups()[0]
      rnpani = residue_name_plus_atom_names_interpreter(
        residue_name=atom_group.resname,
        atom_names=[atom.name for atom in atom_group.atoms()])
      rn = rnpani.work_residue_name
      rn_seq.append(rn)
      if (rn is None):
        c = None
      else:
        c = common_residue_names_get_class(name=rn)
      residue_classes[c] += 1
    return (rn_seq, residue_classes)

  def as_sequence (self, substitute_unknown='X') :
    """
    Naively extract single-character protein or nucleic acid sequence, without
    accounting for residue numbering.

    :param substitute_unknown: character to use for unrecognized 3-letter codes
    """
    assert ((isinstance(substitute_unknown, str)) and
            (len(substitute_unknown) == 1))
    rn_seq, residue_classes = self.get_residue_names_and_classes()
    n_aa = residue_classes["common_amino_acid"]
    n_na = residue_classes["common_rna_dna"]
    seq = []
    if (n_aa > n_na):
      from iotbx.pdb import amino_acid_codes
      aa_3_as_1 = amino_acid_codes.one_letter_given_three_letter
      aa_3_as_1_mod = \
        amino_acid_codes.one_letter_given_three_letter_modified_aa
      for rn in rn_seq:
        if (rn in aa_3_as_1_mod) :
          seq.append(aa_3_as_1_mod.get(rn, substitute_unknown))
        else :
          seq.append(aa_3_as_1.get(rn, substitute_unknown))
    elif (n_na != 0):
      for rn in rn_seq:
        seq.append({
          "A": "A",
          "C": "C",
          "G": "G",
          "U": "U",
          "DA": "A",
          "DC": "C",
          "DG": "G",
          "DT": "T"}.get(rn, "N"))
    return seq

  def as_padded_sequence(self, missing_char='X', skip_insertions=False,
                         pad=True, substitute_unknown='X', pad_at_start=True):
    """
    Extract protein or nucleic acid sequence, taking residue numbering into
    account so that apparent gaps will be filled with substitute characters.
    """
    seq = self.as_sequence()
    padded_seq = []
    last_resseq = 0
    last_icode = " "
    i = 0
    for i, residue_group in enumerate(self.residue_groups()) :
      if (skip_insertions) and (residue_group.icode != " ") :
        continue
      resseq = residue_group.resseq_as_int()
      if (pad) and (resseq > (last_resseq + 1)) :
        for x in range(resseq - last_resseq - 1) :
          if last_resseq == 0 and not pad_at_start: break
          padded_seq.append(missing_char)
      last_resseq = resseq
      padded_seq.append(seq[i])
    return "".join(padded_seq)

  def get_residue_ids (self, skip_insertions=False, pad=True, pad_at_start=True) :
    resids = []
    last_resseq = 0
    last_icode = " "
    for i, residue_group in enumerate(self.residue_groups()) :
      if (skip_insertions) and (residue.icode != " ") :
        continue
      resseq = residue_group.resseq_as_int()
      if (pad) and (resseq > (last_resseq + 1)) :
        for x in range(resseq - last_resseq - 1) :
          if last_resseq == 0 and not pad_at_start: break
          resids.append(None)
      last_resseq = resseq
      resids.append(residue_group.resid())
    return resids

  def get_residue_names_padded(
      self, skip_insertions=False, pad=True, pad_at_start=True):
    resnames = []
    last_resseq = 0
    last_icode = " "
    for i, residue_group in enumerate(self.residue_groups()) :
      if (skip_insertions) and (residue.icode != " ") :
        continue
      resseq = residue_group.resseq_as_int()
      if (pad) and (resseq > (last_resseq + 1)) :
        for x in range(resseq - last_resseq - 1) :
          if last_resseq == 0 and not pad_at_start: break
          resnames.append(None)
      last_resseq = resseq
      resnames.append(residue_group.unique_resnames()[0])
    return resnames

  def is_protein (self, min_content=0.8, ignore_water=True) :
    """
    Determine whether the chain represents an amino acid polymer, based on the
    frequency of residue names.
    Very slow due to usage of residue_name_plus_atom_names_interpreter in
    get_residue_names_and_classes (majority of the processing is unnecessary)
    """
    rn_seq, residue_classes = self.get_residue_names_and_classes()
    n_aa = residue_classes["common_amino_acid"]
    n_na = residue_classes["common_rna_dna"]
    if (ignore_water) :
      while rn_seq.count("HOH") > 0 :
        rn_seq.remove("HOH")
    if (len(rn_seq) == 0) :
      return False
    elif ((n_aa > n_na) and ((n_aa / len(rn_seq)) >= min_content)) :
      return True
    elif (rn_seq == (["UNK"] * len(rn_seq))) :
      return True
    return False

  def is_na (self, min_content=0.8, ignore_water=True) :
    """
    Determine whether the chain represents a nucleic acid polymer, based on the
    frequency of base names.
    Very slow due to usage of residue_name_plus_atom_names_interpreter in
    get_residue_names_and_classes (majority of the processing is unnecessary)
    """
    rn_seq, residue_classes = self.get_residue_names_and_classes()
    n_aa = residue_classes["common_amino_acid"]
    n_na = residue_classes["common_rna_dna"]
    if (ignore_water) :
      while rn_seq.count("HOH") > 0 :
        rn_seq.remove("HOH")
    if (len(rn_seq) == 0) :
      return False
    elif ((n_na > n_aa) and ((n_na / len(rn_seq)) >= min_content)) :
      return True
    return False

class _(boost.python.injector, ext.residue_group, __hash_eq_mixin):

  def only_atom_group(self):
    assert self.atom_groups_size() == 1
    return self.atom_groups()[0]

  def only_atom(self):
    return self.only_atom_group().only_atom()

  def id_str (self) :
    chain_id = ""
    chain = self.parent()
    if (chain is not None) :
      chain_id = chain.id
    return "%2s%4s%1s" % (chain_id, self.resseq, self.icode)

class _(boost.python.injector, ext.atom_group, __hash_eq_mixin):

  def only_atom(self):
    assert self.atoms_size() == 1
    return self.atoms()[0]

  def get_atom (self, name) :
    """
    Extract the child atom with the given (unaligned) name.

    :param name: atom name, explicit case but no spaces.
    :returns: atom object if found, otherwise None
    """
    for atom in self.atoms() :
      if (atom.name.strip() == name) :
        return atom
    return None

  # FIXME suppress_segid has no effect here
  def id_str (self, suppress_segid=None) :
    chain_id = ""
    resid = ""
    rg = self.parent()
    if (rg is not None) :
      resid = rg.resid()
      chain = rg.parent()
      if (chain is not None) :
        chain_id = chain.id
    return "%1s%3s%2s%5s" % (self.altloc, self.resname, chain_id, resid)

  def occupancy (self, raise_error_if_non_uniform=False) :
    """
    Calculate the mean occupancy for atoms in this group, with option of
    raising ValueError if they differ.
    """
    atom_occupancies = self.atoms().extract_occ()
    assert (len(atom_occupancies) > 0)
    min_max_mean = atom_occupancies.min_max_mean()
    if (min_max_mean.min != min_max_mean.max) :
      if (raise_error_if_non_uniform) :
        raise ValueError(("Non-uniform occupancies for atom group %s "+
          "(range: %.2f - %.2f).") % (self.id_str(), min_max_mean.min,
          min_max_mean.max))
    return min_max_mean.mean

class _(boost.python.injector, ext.atom, __hash_eq_mixin):
  __doc__ = """
  The basic unit of the PDB hierarchy (or the PDB input object in general),
  representing a single point scatterer corresponding to an ATOM or HETATM
  record in PDB format (plus associated ANISOU or related records if present).
  Note that this does not directly store attributes of higher-level entities
  whose identity is also recorded in ATOM records, such as the chain ID or
  residue name.  These may be retrieved either by walking up the hierarchy
  starting with atom.parent(), or by calling atom.fetch_labels().
  """
  def chain (self) :
    """
    Convenience method for fetching the chain object associated with this
    atom (or None of not defined).
    """
    ag = self.parent()
    if (ag is not None) :
      rg = ag.parent()
      if (rg is not None) :
        return rg.parent()
    return None

  def is_in_same_conformer_as(self, other):
    """
    Indicate whether two atoms are part of the same conformer and thus are
    capable of interacting directly, as defined by the parent atom_group and
    model object(s).
    """
    ag_i = self.parent(optional=False)
    ag_j = other.parent(optional=False)
    altloc_i = ag_i.altloc
    altloc_j = ag_j.altloc
    if (    len(altloc_i) != 0
        and len(altloc_j) != 0
        and altloc_i != altloc_j):
      return False
    def p3(ag):
      return ag.parent(optional=False) \
               .parent(optional=False) \
               .parent(optional=False)
    model_i = p3(ag_i)
    model_j = p3(ag_j)
    return model_i.memory_id() == model_j.memory_id()

  def set_element_and_charge_from_scattering_type_if_necessary(self,
        scattering_type):
    from cctbx.eltbx.xray_scattering \
      import get_element_and_charge_symbols \
        as gec
    sct_e, sct_c = gec(scattering_type=scattering_type, exact=False)
    pdb_ec = self.element.strip() + self.charge.strip()
    if (len(pdb_ec) != 0):
      if (sct_e == "" and sct_c == ""):
        return False
      pdb_e, pdb_c = gec(scattering_type=pdb_ec, exact=False)
      if (    pdb_e == sct_e
          and pdb_c == sct_c):
        return False
    self.element = "%2s" % sct_e.upper()
    self.charge = "%-2s" % sct_c
    return True

  def charge_as_int(self):
    """
    Extract the atomic charge from the (string) charge field.

    :returns: Python int, defaulting to zero
    """
    charge = self.charge_tidy()
    if charge is None:
      return 0
    if charge.endswith("-"):
      sign = -1
    else:
      sign = 1
    charge = charge.strip(" -+")
    if charge != "":
      return sign * int(charge)
    else:
      return 0

class _(boost.python.injector, ext.conformer):
  __doc__ = """
  Alternate view into a chain object, grouping sequential residues with
  equivalent altlocs.  As a general rule it is preferrable to iterate over
  chain.residue_groups() instead.
  """
  def only_residue(self):
    residues = self.residues()
    assert len(residues) == 1
    return residues[0]

  def only_atom(self):
    return self.only_residue().only_atom()

  def get_residue_names_and_classes (self) :
    # XXX This function should probably be deprecated, since it has been
    # duplicated in chain.get_residue_names_and_classes which should probably
    # be preferred to this function
    from iotbx.pdb import common_residue_names_get_class
    rn_seq = []
    residue_classes = dict_with_default_0()
    for residue in self.residues():
      rnpani = residue.residue_name_plus_atom_names_interpreter()
      rn = rnpani.work_residue_name
      rn_seq.append(rn)
      if (rn is None):
        c = None
      else:
        c = common_residue_names_get_class(name=rn)
      residue_classes[c] += 1
    return (rn_seq, residue_classes)

  def is_protein (self, min_content=0.8) :
    # XXX DEPRECATED
    rn_seq, residue_classes = self.get_residue_names_and_classes()
    n_aa = residue_classes["common_amino_acid"]
    n_na = residue_classes["common_rna_dna"]
    if ((n_aa > n_na) and ((n_aa / len(rn_seq)) >= min_content)) :
      return True
    return False

  def is_na (self, min_content=0.8) :
    # XXX DEPRECATED
    rn_seq, residue_classes = self.get_residue_names_and_classes()
    n_aa = residue_classes["common_amino_acid"]
    n_na = residue_classes["common_rna_dna"]
    if ((n_na > n_aa) and ((n_na / len(rn_seq)) >= min_content)) :
      return True
    return False

  def as_sequence (self, substitute_unknown='X') :
    # XXX This function should probably be deprecated, since it has been
    # duplicated in chain.as_sequence which should probably be preferred to
    # this function
    assert ((isinstance(substitute_unknown, str)) and
            (len(substitute_unknown) == 1))
    rn_seq, residue_classes = self.get_residue_names_and_classes()
    n_aa = residue_classes["common_amino_acid"]
    n_na = residue_classes["common_rna_dna"]
    seq = []
    if (n_aa > n_na):
      from iotbx.pdb import amino_acid_codes
      aa_3_as_1 = amino_acid_codes.one_letter_given_three_letter
      aa_3_as_1_mod = \
        amino_acid_codes.one_letter_given_three_letter_modified_aa
      for rn in rn_seq:
        if (rn in aa_3_as_1_mod) :
          seq.append(aa_3_as_1_mod.get(rn, substitute_unknown))
        else :
          seq.append(aa_3_as_1.get(rn, substitute_unknown))
    elif (n_na != 0):
      for rn in rn_seq:
        seq.append({
          "A": "A",
          "C": "C",
          "G": "G",
          "U": "U",
          "DA": "A",
          "DC": "C",
          "DG": "G",
          "DT": "T"}.get(rn, "N"))
    return seq

  def format_fasta(self, max_line_length=79):
    seq = self.as_sequence()
    n = len(seq)
    if (n == 0): return None
    comment = [">"]
    p = self.parent()
    if (p is not None):
      comment.append('chain "%2s"' % p.id)
    comment.append('conformer "%s"' % self.altloc)
    result = [" ".join(comment)]
    i = 0
    while True:
      j = min(n, i+max_line_length)
      if (j == i): break
      result.append("".join(seq[i:j]))
      i = j
    return result

  def as_padded_sequence (self, missing_char='X', skip_insertions=False,
      pad=True, substitute_unknown='X', pad_at_start=True) :
    # XXX This function should probably be deprecated, since it has been
    # duplicated in chain.as_padded_sequence which should probably be preferred
    # to this function
    seq = self.as_sequence()
    padded_seq = []
    last_resseq = 0
    last_icode = " "
    i = 0
    for i, residue in enumerate(self.residues()) :
      if (skip_insertions) and (residue.icode != " ") :
        continue
      resseq = residue.resseq_as_int()
      if (pad) and (resseq > (last_resseq + 1)) :
        for x in range(resseq - last_resseq - 1) :
          if last_resseq == 0 and not pad_at_start: break
          padded_seq.append(missing_char)
      last_resseq = resseq
      padded_seq.append(seq[i])
    return "".join(padded_seq)

  def as_sec_str_sequence (self, helix_sele, sheet_sele, missing_char='X',
                           pad=True, pad_at_start=True) :
    ss_seq = []
    last_resseq = 0
    for i, residue in enumerate(self.residues()) :
      resseq = residue.resseq_as_int()
      if pad and resseq > (last_resseq + 1) :
        for x in range(resseq - last_resseq - 1) :
          if last_resseq == 0 and not pad_at_start: break
          ss_seq.append(missing_char)
      found = False
      for atom in residue.atoms() :
        if helix_sele[atom.i_seq] :
          ss_seq.append('H')
          found = True
          break
        elif sheet_sele[atom.i_seq] :
          ss_seq.append('S')
          found = True
          break
      if not found :
        ss_seq.append('L')
      last_resseq = resseq
    return "".join(ss_seq)

  def get_residue_ids (self, skip_insertions=False, pad=True, pad_at_start=True) :
    # XXX This function should probably be deprecated, since it has been
    # duplicated in chain.get_residue_ids which should probably be preferred
    # to this function
    resids = []
    last_resseq = 0
    last_icode = " "
    for i, residue in enumerate(self.residues()) :
      if (skip_insertions) and (residue.icode != " ") :
        continue
      resseq = residue.resseq_as_int()
      if (pad) and (resseq > (last_resseq + 1)) :
        for x in range(resseq - last_resseq - 1) :
          if last_resseq == 0 and not pad_at_start: break
          resids.append(None)
      last_resseq = resseq
      resids.append(residue.resid())
    return resids

  def get_residue_names_padded(
      self, skip_insertions=False, pad=True, pad_at_start=True):
    # XXX This function should probably be deprecated, since it has been
    # duplicated in chain.get_residue_names_padded which should probably be
    # preferred to this function
    resnames = []
    last_resseq = 0
    last_icode = " "
    for i, residue in enumerate(self.residues()) :
      if (skip_insertions) and (residue.icode != " ") :
        continue
      resseq = residue.resseq_as_int()
      if (pad) and (resseq > (last_resseq + 1)) :
        for x in range(resseq - last_resseq - 1) :
          if last_resseq == 0 and not pad_at_start: break
          resnames.append(None)
      last_resseq = resseq
      resnames.append(residue.resname)
    return resnames



class _(boost.python.injector, ext.residue):

  def __getinitargs__(self):
    result_root = self.root()
    if (result_root is None):
      orig_conformer = self.parent()
      assert orig_conformer is not None
      orig_chain = orig_conformer.parent()
      assert orig_chain is not None
      orig_model = orig_chain.parent()
      assert orig_model is not None
      result_atom_group = atom_group(
        altloc=orig_conformer.altloc, resname=self.resname)
      result_residue_group = residue_group(
        resseq=self.resseq, icode=self.icode)
      result_chain = chain(id=orig_chain.id)
      result_model = model(id=orig_model.id)
      result_root = root()
      result_root.append_model(result_model)
      result_model.append_chain(result_chain)
      result_chain.append_residue_group(result_residue_group)
      result_residue_group.append_atom_group(result_atom_group)
      for atom in self.atoms():
        result_atom_group.append_atom(atom.detached_copy())
    return (result_root,)

  def standalone_copy(self):
    return residue(root=self.__getinitargs__()[0])

  def only_atom(self):
    assert self.atoms_size() == 1
    return self.atoms()[0]

  def residue_name_plus_atom_names_interpreter(self,
        translate_cns_dna_rna_residue_names=None,
        return_mon_lib_dna_name=False):
    from iotbx.pdb import residue_name_plus_atom_names_interpreter
    return residue_name_plus_atom_names_interpreter(
      residue_name=self.resname,
      atom_names=[atom.name for atom in self.atoms()],
      translate_cns_dna_rna_residue_names=translate_cns_dna_rna_residue_names,
      return_mon_lib_dna_name=return_mon_lib_dna_name)

class _(boost.python.injector, ext.atom_with_labels):
  __doc__ = """
  Stand-in for atom object, which explicitly records the attributes normally
  reserved for parent classes such as residue name, chain ID, etc.
  """
  def __getstate__ (self) :
    labels_dict = {}
    for attr in [ "xyz", "sigxyz", "occ", "sigocc", "b", "sigb", "uij",
                  "siguij", "hetero", "serial", "name", "segid", "element",
                  "charge", "model_id", "chain_id", "resseq", "icode",
                  "altloc", "resname", ] :
      labels_dict[attr] = getattr(self, attr, None)
    return labels_dict

  def __setstate__ (self, state) :
    from iotbx.pdb import make_atom_with_labels
    state = dict(state)
    make_atom_with_labels(self, **state)

  def fetch_labels (self) :
    return self

class input_hierarchy_pair(object):

  def __init__(self, input, hierarchy=None):
    self.input = input
    if (hierarchy is None):
      hierarchy = self.input.construct_hierarchy(set_atom_i_seq=True)
    self.hierarchy = hierarchy

  def __getinitargs__(self):
    from pickle import PicklingError
    raise PicklingError

  def hierarchy_to_input_atom_permutation(self):
    """
    Return the permutation selection
    (:py:class:`scitbx.array_family.flex.size_t`) mapping the atoms as ordered
    by the hierarchy to their original positions in the PDB/mmCIF file.
    """
    h_atoms = self.hierarchy.atoms()
    sentinel = h_atoms.reset_tmp(first_value=0, increment=1)
    return self.input.atoms().extract_tmp_as_size_t()

  def input_to_hierarchy_atom_permutation(self):
    """
    Return the permutation selection
    (:py:class:`scitbx.array_family.flex.size_t`) mapping the atoms as ordered
    in the original PDB/mmCIF file to their positions in the hierarchy.
    """
    i_atoms = self.input.atoms()
    sentinel = i_atoms.reset_tmp(first_value=0, increment=1)
    return self.hierarchy.atoms().extract_tmp_as_size_t()

  def xray_structure_simple (self, *args, **kwds) :
    """
    Wrapper for the equivalent method of the input object - extracts the
    :py:class:`cctbx.xray.structure` with scatterers in the same order as in
    the hierarchy.
    """
    perm = self.input_to_hierarchy_atom_permutation()
    xrs = self.input.xray_structure_simple(*args, **kwds)
    return xrs.select(perm)

  def construct_hierarchy (self, *args, **kwds) : # TODO remove eventually
    """
    Returns a reference to the existing hierarchy.  For backwards compatibility
    only, and issues a :py:class:`warnings.DeprecationWarning`.
    """
    warnings.warn("Please access input.hierarchy directly.",
      DeprecationWarning)
    return self.hierarchy

  def crystal_symmetry (self, *args, **kwds) :
    return self.input.crystal_symmetry(*args, **kwds)

class input(input_hierarchy_pair):
  """
  Class used for reading a PDB hierarchy from a file or string.

  Attributes
  ----------
  input : iotbx.pdb.pdb_input_from_any
  hierarchy : iotbx.pdb.hierarchy.root

  Examples
  --------
  >>> import iotbx.pdb.hierarchy
  >>> pdb_in = iotbx.pdb.hierarchy.input(pdb_string='''
  ... ATOM      1  N   ASP A  37      10.710  14.456   9.568  1.00 15.78           N
  ... ATOM      2  CA  ASP A  37       9.318  14.587   9.999  1.00 18.38           C
  ... ''')
  >>> print pdb_in.hierarchy.atoms_size()
  2
  "")
  """

  def __init__(self, file_name=None, pdb_string=None, source_info=Auto):
    """
    Initializes an input from a file or string.

    Parameters
    ----------
    file_name : str, optional
    pdb_string : str, optional
    source_info : str, optional
        Indicates where this PDB came from (i.e. "string")
    """
    assert [file_name, pdb_string].count(None) == 1
    import iotbx.pdb
    if (file_name is not None):
      assert source_info is Auto
      pdb_inp = iotbx.pdb.input(file_name=file_name)
    else:
      if (source_info is Auto): source_info = "string"
      pdb_inp = iotbx.pdb.input(
        source_info=source_info, lines=flex.split_lines(pdb_string))
    super(input, self).__init__(input=pdb_inp)

class show_summary(input):

  def __init__(self,
        file_name=None,
        pdb_string=None,
        out=None,
        prefix="",
        flag_errors=True,
        flag_warnings=True,
        residue_groups_max_show=10,
        duplicate_atom_labels_max_show=10,
        level_id=None,
        level_id_exception=ValueError):
    input.__init__(self, file_name=file_name, pdb_string=pdb_string)
    print >> out, prefix+self.input.source_info()
    self.overall_counts = self.hierarchy.overall_counts()
    self.overall_counts.show(
      out=out,
      prefix=prefix+"  ",
      residue_groups_max_show=residue_groups_max_show,
      duplicate_atom_labels_max_show=duplicate_atom_labels_max_show)
    if (level_id is not None):
      self.hierarchy.show(
        out=out,
        prefix=prefix+"  ",
        level_id=level_id,
        level_id_exception=level_id_exception)

def append_chain_id_suffixes(roots, suffixes=Auto):
  if (suffixes is Auto):
    suffixes="123456789" \
             "ABCDEFGHIJKLMNOPQRSTUVWXYZ" \
             "abcdefghijklmnopqrstuvwxyz"
  assert len(roots) <= len(suffixes)
  for root,suffix in zip(roots, suffixes):
    for model in root.models():
      for chain in model.chains():
        assert len(chain.id) == 1
        chain.id += suffix

def join_roots(roots, chain_id_suffixes=Auto):
  """
  Combine two root objects.
  """
  if (chain_id_suffixes is not None):
    append_chain_id_suffixes(roots=roots, suffixes=chain_id_suffixes)
  result = root()
  for rt in roots:
    result.transfer_chains_from_other(other=rt)
  return result

# XXX: Nat's utility functions
def new_hierarchy_from_chain (chain) :
  """
  Given a chain object, create an entirely new hierarchy object contaning only
  this chain (using a new copy).
  """
  import iotbx.pdb.hierarchy
  hierarchy = iotbx.pdb.hierarchy.root()
  model = iotbx.pdb.hierarchy.model()
  model.append_chain(chain.detached_copy())
  hierarchy.append_model(model)
  return hierarchy

def find_and_replace_chains (original_hierarchy, partial_hierarchy,
    log=sys.stdout) :
  """
  Delete and replace the first chain in the original hierarchy corresponding
  to each model/ID combination in the partial hierarchy.  Note that this means
  that if waters and heteroatoms are given the same ID as a protein chain
  (separated by other chains or TER record(s)), but the partial hierarchy only
  contains a substitute protein chain, the heteroatom chain will be kept.
  """
  for original_model in original_hierarchy.models() :
    for partial_model in partial_hierarchy.models() :
      if original_model.id == partial_model.id :
        #print >> log, "    found model '%s'" % partial_model.id
        i = 0
        while i < len(original_model.chains()) :
          original_chain = original_model.chains()[i]
          j = 0
          while j < len(partial_model.chains()) :
            partial_chain = partial_model.chains()[j]
            if original_chain.id == partial_chain.id :
              #print >> log, "      found chain '%s' at index %d" % (
              #  partial_chain.id, i)
              original_model.remove_chain(i)
              original_model.insert_chain(i, partial_chain.detached_copy())
              partial_model.remove_chain(j)
              break
            j += 1
          i += 1

def get_contiguous_ranges (hierarchy) :
  assert (len(hierarchy.models()) == 1)
  chain_clauses = []
  for chain in hierarchy.models()[0].chains() :
    resid_ranges = []
    start_resid = None
    last_resid = None
    last_resseq = - sys.maxint
    for residue_group in chain.residue_groups() :
      resseq = residue_group.resseq_as_int()
      resid = residue_group.resid()
      if (resseq != last_resseq) and (resseq != (last_resseq + 1)) :
        if (start_resid is not None) :
          resid_ranges.append((start_resid, last_resid))
        start_resid = resid
        last_resid = resid
      else :
        if (start_resid is None) :
          start_resid = resid
        last_resid = resid
      last_resseq = resseq
    if (start_resid is not None) :
      resid_ranges.append((start_resid, last_resid))
    resid_clauses = []
    for r1, r2 in resid_ranges :
      if (r1 == r2) :
        resid_clauses.append("resid %s" % r1)
      else :
        resid_clauses.append("resid %s through %s" % (r1,r2))
    sele = ("chain '%s' and ((" + ") or (".join(resid_clauses) + "))") % \
      chain.id
    chain_clauses.append(sele)
  return chain_clauses

# used for reporting build results in phenix
def get_residue_and_fragment_count (pdb_file=None, pdb_hierarchy=None) :
  from iotbx.pdb import amino_acid_codes
  import iotbx.pdb
  from libtbx import smart_open
  covalent_residues = amino_acid_codes.one_letter_given_three_letter.keys()
  covalent_residues.extend(iotbx.pdb.cns_dna_rna_residue_names.keys())
  if (pdb_file is not None) :
    raw_records = flex.std_string()
    f = smart_open.for_reading(file_name=pdb_file)
    raw_records.extend(flex.split_lines(f.read()))
    pdb_in = iotbx.pdb.input(source_info=pdb_file, lines=raw_records)
    pdb_hierarchy = pdb_in.construct_hierarchy()
  assert (pdb_hierarchy is not None)
  models = pdb_hierarchy.models()
  if len(models) == 0 :
    return (0, 0, 0)
  chains = models[0].chains()
  if len(chains) == 0 :
    return (0, 0, 0)
  n_res = 0
  n_frag = 0
  n_h2o = 0
  for chain in chains :
    i = -999
    for res in chain.conformers()[0].residues() :
      if res.resname.strip() in covalent_residues :
        n_res += 1
        resseq = res.resseq_as_int()
        if resseq > (i + 1) :
          n_frag += 1
        i = resseq
      elif res.resname.strip() in ['HOH','WAT','H2O'] :
        n_h2o += 1
  return (n_res, n_frag, n_h2o)

def sites_diff (hierarchy_1,
                hierarchy_2,
                exclude_waters=True,
                return_hierarchy=True,
                log=None) :
  """
  Given two PDB hierarchies, calculate the shift of each atom (accounting for
  possible insertions/deletions) and (optionally) apply it to the B-factor for
  display in PyMOL, plotting in PHENIX GUI, etc.
  """
  if (log is None) : log = null_out()
  atom_lookup = {}
  deltas = flex.double(hierarchy_2.atoms().size(), -1.)
  for atom in hierarchy_1.atoms_with_labels() :
    if (atom.resname in ["HOH", "WAT"]) and (exclude_waters) :
      continue
    atom_id = atom.id_str()
    if (atom_id in atom_lookup) :
      raise RuntimeError("Duplicate atom ID - can't extract coordinates.")
    atom_lookup[atom_id] = atom.xyz
  for i_seq, atom in enumerate(hierarchy_2.atoms_with_labels()) :
    if (atom.resname in ["HOH", "WAT"]) and (exclude_waters) :
      continue
    atom_id = atom.id_str()
    if (atom_id in atom_lookup) :
      x1,y1,z1 = atom_lookup[atom_id]
      x2,y2,z2 = atom.xyz
      delta = math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
      deltas[i_seq] = delta
  if (return_hierarchy) :
    hierarchy_new = hierarchy_2.deep_copy()
    hierarchy_new.atoms().set_b(deltas)
    return hierarchy_new
  else :
    return deltas

def expand_ncs (
    pdb_hierarchy,
    processed_mtrix_records,
    write_segid=True,
    log=None) :
  pmr = processed_mtrix_records
  if (log is None) : log = null_out()
  assert len(pmr.r) == len(pmr.t)
  if (len(pmr.r) == 0) :
    raise Sorry("No MTRIX records found in PDB file!")
  if (len(pdb_hierarchy.models()) > 1) :
    raise Sorry("Multi-MODEL PDB files not supported.")
  hierarchy_new = root()
  model_new = model()
  hierarchy_new.append_model(model_new)
  for chain_ in pdb_hierarchy.models()[0].chains() :
    chain_new = chain_.detached_copy()
    atoms_tmp = chain_new.atoms()
    if (write_segid) :
      for atom in atoms_tmp :
        atom.set_segid("0")
    model_new.append_chain(chain_new)
  print >> log, "Applying %d MTRIX records..." % len(pmr.r)
  for rm, tv, sn, cpf in zip(pmr.r, pmr.t, pmr.serial_number,
                             pmr.coordinates_present):
    if (cpf) :
      print >> log, "  skipping matrix %s, coordinates already present" % sn
      continue
    for chain_ in pdb_hierarchy.models()[0].chains() :
      chain_new = chain_.detached_copy()
      atoms_tmp = chain_new.atoms()
      if (write_segid) :
        for atom in atoms_tmp :
          atom.set_segid("%s" % sn)
      xyz = atoms_tmp.extract_xyz()
      atoms_tmp.set_xyz(rm.elems * xyz + tv)
      model_new.append_chain(chain_new)
  return hierarchy_new

def substitute_atom_group (
    current_group,
    new_group,
    backbone_only=True,
    exclude_hydrogens=False,
    ignore_b_factors=False,
    is_amino_acid=Auto,
    log=None) :
  """
  Substitute the sidechain atoms from one residue for another, using
  least-squares superposition to align the backbone atoms.
  """
  if (log is None) : log = null_out()
  from iotbx.pdb import common_residue_names_get_class
  from scitbx.math import superpose
  new_atoms = new_group.detached_copy().atoms()
  selection_fixed = flex.size_t()
  selection_moving = flex.size_t()
  res_class = common_residue_names_get_class(current_group.resname)
  if (is_amino_acid is Auto) :
    is_amino_acid = (res_class == "common_amino_acid")
  # TODO nucleic acids?
  backbone_atoms = [" CA ", " C  ", " N  ", " CB "]
  for i_seq, atom in enumerate(current_group.atoms()) :
    if (atom.element == " H") and (exclude_hydrogens) :
      continue
    if (is_amino_acid and backbone_only) :
      if (not atom.name in backbone_atoms) :
        continue
    for j_seq, other_atom in enumerate(new_group.atoms()) :
      if (atom.name == other_atom.name) :
        selection_fixed.append(i_seq)
        selection_moving.append(j_seq)
  sites_fixed = current_group.atoms().extract_xyz().select(selection_fixed)
  sites_moving = new_atoms.extract_xyz().select(selection_moving)
  assert (len(sites_fixed) == len(sites_moving))
  lsq_fit = superpose.least_squares_fit(
    reference_sites=sites_fixed,
    other_sites=sites_moving)
  sites_new = new_atoms.extract_xyz()
  sites_new = lsq_fit.r.elems * sites_new + lsq_fit.t.elems
  new_atoms.set_xyz(sites_new)
  keep_atoms = []
  if (is_amino_acid and backbone_only) :
    keep_atoms = backbone_atoms + [" O  "] # XXX definitely keep peptide O!
  atom_b_iso = {}
  max_b = flex.max(current_group.atoms().extract_b())
  for atom in current_group.atoms() :
    if (not atom.name in keep_atoms) :
      current_group.remove_atom(atom)
      atom_b_iso[atom.name] = atom.b
  for atom in new_atoms :
    if ((not atom.name in keep_atoms) and
        ((atom.element != "H ") or (not exclude_hydrogens))) :
      if (not ignore_b_factors) :
        # XXX a more sophisticated approach would probably be helpful here,
        # but this seems safer than using B-factors of unknown origin
        if (atom.name in atom_b_iso) :
          atom.b = atom_b_iso[atom.name]
        else :
          atom.b = max_b
      current_group.append_atom(atom)
  current_group.resname = new_group.resname
  return current_group
