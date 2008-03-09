from __future__ import generators

import boost.python
ext = boost.python.import_ext("iotbx_pdb_hierarchy_v2_ext")
from iotbx_pdb_hierarchy_v2_ext import *

class _root(boost.python.injector, ext.root):

  def chains(self):
    for model in self.models():
      for chain in model.chains():
        yield chain

  def residue_groups(self):
    for model in self.models():
      for chain in model.chains():
        for rg in chain.residue_groups():
          yield rg

  def atom_groups(self):
    for model in self.models():
      for chain in model.chains():
        for rg in chain.residue_groups():
          for ag in rg.atom_groups():
            yield ag

  def atoms(self):
    for model in self.models():
      for chain in model.chains():
        for rg in chain.residue_groups():
          for ag in rg.atom_groups():
            for atom in ag.atoms():
              yield atom

  def only_model(self):
    assert self.models_size() == 1
    return self.models()[0]

  def only_chain(self):
    return self.only_model().only_chain()

  def only_residue_group(self):
    return self.only_chain().only_residue_group()

  def only_atom_group(self):
    return self.only_residue_group().only_atom_group()

  def only_atom(self):
    return self.only_atom_group().only_atom()

  def as_pdb_records(self, append_end=False):
    result = []
    models = self.models()
    for model in models:
      if (len(models) != 1):
        result.append("MODEL %7s" % model.id)
      for chain in model.chains():
        atom_serial = chain.append_atom_records(
          pdb_records=result)
        result.append("TER")
      if (len(models) != 1):
        result.append("ENDMDL")
    if (append_end):
      result.append("END")
    return result

  def as_pdb_string(self, append_end=False):
    return "\n".join(self.as_pdb_records(append_end=append_end))+"\n"

class _model(boost.python.injector, ext.model):

  def residue_groups(self):
    for chain in self.chains():
      for rg in chain.residue_groups():
        yield rg

  def atom_groups(self):
    for chain in self.chains():
      for rg in chain.residue_groups():
        for ag in rg.atom_groups():
          yield ag

  def atoms(self):
    for chain in self.chains():
      for rg in chain.residue_groups():
        for ag in rg.atom_groups():
          for atom in ag.atoms():
            yield atom

  def only_chain(self):
    assert self.chains_size() == 1
    return self.chains()[0]

  def only_residue_group(self):
    return self.only_chain().only_residue_group()

  def only_atom_group(self):
    return self.only_residue_group().only_atom_group()

  def only_atom(self):
    return self.only_atom_group().only_atom()

class _chain(boost.python.injector, ext.chain):

  def atom_groups(self):
    for rg in self.residue_groups():
      for ag in rg.atom_groups():
        yield ag

  def atoms(self):
    for rg in self.residue_groups():
      for ag in rg.atom_groups():
        for atom in ag.atoms():
          yield atom

  def only_residue_group(self):
    assert self.residue_groups_size() == 1
    return self.residue_groups()[0]

  def only_atom_group(self):
    return self.only_residue_group().only_atom_group()

  def only_atom(self):
    return self.only_atom_group().only_atom()

  def find_pure_altloc_ranges(self, common_residue_name_class_only=None):
    result = []
    n_rg = self.residue_groups_size()
    range_start = n_rg
    for i_rg,rg in enumerate(self.residue_groups()):
      ags = rg.atom_groups()
      skip = 0
      if (common_residue_name_class_only is not None):
        from iotbx.pdb import common_residue_names_get_class
        for ag in ags:
          if (   common_residue_names_get_class(name=ag.resname)
              == common_residue_name_class_only):
            break
        else:
          skip = 1
      if (skip != 0 or not rg.link_to_previous):
        if (range_start+1 < i_rg):
          result.append((range_start, i_rg))
        if (len(ags) == 0 or ags[0].altloc == ""):
          range_start = n_rg
        else:
          range_start = i_rg + skip
      else:
        if (len(ags) == 0 or ags[0].altloc == ""):
          if (range_start+1 < i_rg):
            result.append((range_start, i_rg))
          range_start = n_rg
        elif (range_start == n_rg):
          range_start = i_rg + skip
    if (range_start+1 < n_rg):
      result.append((range_start, n_rg))
    return result

class _residue_group(boost.python.injector, ext.residue_group):

  def atoms(self):
    for ag in self.atom_groups():
      for atom in ag.atoms():
        yield atom

  def only_atom_group(self):
    assert self.atom_groups_size() == 1
    return self.atom_groups()[0]

  def only_atom(self):
    return self.only_atom_group().only_atom()

class _atom_group(boost.python.injector, ext.atom_group):

  def only_atom(self):
    assert self.atoms_size() == 1
    return self.atoms()[0]
