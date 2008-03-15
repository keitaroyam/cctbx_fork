from iotbx import pdb
from cctbx.array_family import flex
from libtbx.test_utils import Exception_expected, approx_equal, show_diff
from libtbx.str_utils import show_string
from libtbx.utils import Sorry, format_cpu_times
from cStringIO import StringIO
import libtbx.load_env
import random
import sys, os

def exercise_atom():
  a = pdb.hierarchy_v2.atom()
  assert a.name == ""
  a.name = "abcd"
  assert a.name == "abcd"
  try: a.name = "xyzhkl"
  except (ValueError, RuntimeError), e:
    assert str(e) == "string is too long for target variable " \
      "(maximum length is 4 characters, 6 given)."
  else: raise Exception_expected
  assert a.segid == ""
  a.segid = "stuv"
  assert a.segid == "stuv"
  assert a.element == ""
  a.element = "ca"
  assert a.element == "ca"
  assert a.charge == ""
  a.charge = "2+"
  assert a.charge == "2+"
  assert a.serial == ""
  a.serial = "A0000"
  assert a.serial == "A0000"
  assert a.xyz == (0,0,0)
  a.xyz = (1,-2,3)
  assert a.xyz == (1,-2,3)
  assert a.sigxyz == (0,0,0)
  a.sigxyz = (-2,3,1)
  assert a.sigxyz == (-2,3,1)
  assert a.occ == 0
  a.occ = 0.5
  assert a.occ == 0.5
  assert a.sigocc == 0
  a.sigocc = 0.7
  assert a.sigocc == 0.7
  assert a.b == 0
  a.b = 5
  assert a.b == 5
  assert a.sigb == 0
  a.sigb = 7
  assert a.sigb == 7
  assert a.uij == (-1,-1,-1,-1,-1,-1)
  assert not a.uij_is_defined()
  a.uij = (1,-2,3,4,-5,6)
  assert a.uij == (1,-2,3,4,-5,6)
  assert a.uij_is_defined()
  assert a.siguij == (-1,-1,-1,-1,-1,-1)
  assert not a.siguij_is_defined()
  a.siguij = (-2,3,4,-5,6,1)
  assert a.siguij == (-2,3,4,-5,6,1)
  assert a.siguij_is_defined()
  assert not a.hetero
  a.hetero = True
  assert a.hetero
  assert a.tmp == 0
  a.tmp = 3
  assert a.tmp == 3
  #
  a = (pdb.hierarchy_v2.atom()
    .set_name(new_name="NaMe")
    .set_segid(new_segid="sEgI")
    .set_element(new_element="El")
    .set_charge(new_charge="cH")
    .set_serial(new_serial="B1234")
    .set_xyz(new_xyz=(1.3,2.1,3.2))
    .set_sigxyz(new_sigxyz=(.1,.2,.3))
    .set_occ(new_occ=0.4)
    .set_sigocc(new_sigocc=0.1)
    .set_b(new_b=4.8)
    .set_sigb(new_sigb=0.7)
    .set_uij(new_uij=(1.3,2.1,3.2,4.3,2.7,9.3))
    .set_siguij(new_siguij=(.1,.2,.3,.6,.1,.9))
    .set_hetero(new_hetero=True))
  assert a.name == "NaMe"
  assert a.segid == "sEgI"
  assert a.element == "El"
  assert a.charge == "cH"
  assert a.serial == "B1234"
  assert approx_equal(a.xyz, (1.3,2.1,3.2))
  assert approx_equal(a.sigxyz, (.1,.2,.3))
  assert approx_equal(a.occ, 0.4)
  assert approx_equal(a.sigocc, 0.1)
  assert approx_equal(a.b, 4.8)
  assert approx_equal(a.sigb, 0.7)
  assert approx_equal(a.uij, (1.3,2.1,3.2,4.3,2.7,9.3))
  assert approx_equal(a.siguij, (.1,.2,.3,.6,.1,.9))
  assert a.hetero
  assert a.tmp == 0
  try: a.set_name(new_name="12345")
  except (ValueError, RuntimeError), e:
    assert str(e) == "string is too long for target variable " \
      "(maximum length is 4 characters, 5 given)."
  else: raise Exception_expected
  #
  a.tmp = 7
  ac = a.detached_copy()
  assert ac.tmp == 0
  assert ac.name == "1234"
  assert ac.segid == "sEgI"
  assert ac.element == "El"
  assert ac.charge == "cH"
  assert ac.serial == "B1234"
  assert approx_equal(ac.xyz, (1.3,2.1,3.2))
  assert approx_equal(ac.sigxyz, (.1,.2,.3))
  assert approx_equal(ac.occ, 0.4)
  assert approx_equal(ac.sigocc, 0.1)
  assert approx_equal(ac.b, 4.8)
  assert approx_equal(ac.sigb, 0.7)
  assert approx_equal(ac.uij, (1.3,2.1,3.2,4.3,2.7,9.3))
  assert approx_equal(ac.siguij, (.1,.2,.3,.6,.1,.9))
  assert ac.hetero
  #
  for e in ["H", "H ", " H", "D", "D ", " D"]:
    a.element = e
    assert a.element_is_hydrogen()
  for e in ["", "h", "h ", " h", "d", "d ", " d"]:
    a.element = e
    assert not a.element_is_hydrogen()
  #
  a.name = "1234"
  a.element = "El"
  assert a.determine_chemical_element_simple() is None
  a.name = "NA  "
  a.element = " N"
  assert a.determine_chemical_element_simple() == " N"
  a.element = "CU"
  assert a.determine_chemical_element_simple() == "CU"
  a.element = "  "
  assert a.determine_chemical_element_simple() == "NA"
  a.name = " D"
  assert a.determine_chemical_element_simple() == " D"
  for d in "0123456789":
    a.name = d+"H"
    assert a.determine_chemical_element_simple() == " H"
  a.set_name(new_name=None)
  a.set_segid(new_segid=None)
  a.set_element(new_element=None)
  a.set_charge(new_charge=None)
  a.set_serial(new_serial=None)
  assert a.name == ""
  assert a.segid == ""
  assert a.element == ""
  assert a.charge == ""
  assert a.serial == ""
  #
  ag = pdb.hierarchy_v2.atom_group()
  ac = pdb.hierarchy_v2.atom(parent=ag, other=a)
  assert ac.memory_id() != a.memory_id()
  assert ac.parent().memory_id() == ag.memory_id()
  assert ac.name == a.name
  assert ac.segid == a.segid
  assert ac.element == a.element
  assert ac.charge == a.charge
  assert ac.serial == a.serial
  assert ac.xyz == a.xyz
  assert ac.sigxyz == a.sigxyz
  assert ac.occ == a.occ
  assert ac.sigocc == a.sigocc
  assert ac.b == a.b
  assert ac.sigb == a.sigb
  assert ac.uij == a.uij
  assert ac.siguij == a.siguij
  assert ac.hetero == a.hetero
  assert ac.tmp == 0
  #
  assert a.pdb_label_columns() == "               "
  #
  atoms = pdb.hierarchy_v2.af_shared_atom()
  atoms.reset_tmp()
  atoms.append(pdb.hierarchy_v2.atom())
  assert [atom.tmp for atom in atoms] == [0]
  atoms.reset_tmp(first_value=2)
  assert [atom.tmp for atom in atoms] == [2]
  atoms.append(pdb.hierarchy_v2.atom())
  atoms.append(pdb.hierarchy_v2.atom())
  assert [atom.tmp for atom in atoms] == [2,0,0]
  atoms.reset_tmp()
  assert [atom.tmp for atom in atoms] == [0,1,2]
  atoms.reset_tmp(first_value=0, increment=0)
  assert [atom.tmp for atom in atoms] == [0] * 3
  atoms.reset_tmp(first_value=5, increment=-3)
  assert [atom.tmp for atom in atoms] == [5,2,-1]
  #
  atoms.reset_tmp_for_occupancy_groups_simple()
  assert [atom.tmp for atom in atoms] == [0,1,2]
  atoms[0].element = "D"
  atoms[2].element = "H"
  atoms.reset_tmp_for_occupancy_groups_simple()
  assert [atom.tmp for atom in atoms] == [-1,1,-1]

def exercise_atom_group():
  ag = pdb.hierarchy_v2.atom_group()
  assert ag.altloc == ""
  assert ag.resname == ""
  ag = pdb.hierarchy_v2.atom_group(altloc=None, resname=None)
  assert ag.altloc == ""
  assert ag.resname == ""
  ag = pdb.hierarchy_v2.atom_group(altloc="a", resname="xyz")
  assert ag.altloc == "a"
  assert ag.resname == "xyz"
  ag.altloc = None
  ag.resname = None
  assert ag.altloc == ""
  assert ag.resname == ""
  assert ag.confid() == "    "
  #
  ag.altloc = "l"
  ag.resname = "res"
  assert ag.confid() == "lres"
  ag.append_atom(atom=pdb.hierarchy_v2.atom().set_name(new_name="n"))
  rg = pdb.hierarchy_v2.residue_group()
  for i,agc in enumerate([
                 pdb.hierarchy_v2.atom_group(parent=rg, other=ag),
                 ag.detached_copy()]):
    assert agc.memory_id() != ag.memory_id()
    assert ag.parent() is None
    if (i == 0):
      assert agc.parent().memory_id() == rg.memory_id()
    else:
      assert agc.parent() is None
    assert agc.altloc == "l"
    assert agc.resname == "res"
    assert agc.atoms_size() == 1
    assert agc.atoms()[0].memory_id() != ag.atoms()[0].memory_id()
    assert agc.atoms()[0].name == "n"
    ag.append_atom(atom=pdb.hierarchy_v2.atom().set_name(new_name="o"))
    assert ag.atoms_size() == 2+i
    assert agc.atoms_size() == 1
  #
  ag = pdb.hierarchy_v2.atom_group()
  assert ag.parent() is None
  rg1 = pdb.hierarchy_v2.residue_group()
  rg2 = pdb.hierarchy_v2.residue_group()
  assert rg1.memory_id() != rg2.memory_id()
  ag = pdb.hierarchy_v2.atom_group(parent=rg1)
  assert ag.parent().memory_id() == rg1.memory_id()
  del rg1
  assert ag.parent() is None
  #
  rg1 = pdb.hierarchy_v2.residue_group()
  ag = rg1.new_atom_group(altloc="a", resname="xyz")
  assert ag.altloc == "a"
  assert ag.resname == "xyz"
  assert ag.parent().memory_id() == rg1.memory_id()
  del rg1
  assert ag.parent() is None
  #
  ag.pre_allocate_atoms(number_of_additional_atoms=2)
  assert ag.atoms_size() == 0
  assert ag.atoms().size() == 0
  ag.append_atom(atom=pdb.hierarchy_v2.atom().set_name(new_name="ca"))
  assert ag.atoms_size() == 1
  assert ag.atoms().size() == 1
  ag.append_atom(atom=pdb.hierarchy_v2.atom().set_name(new_name="n"))
  assert ag.atoms_size() == 2
  assert ag.atoms().size() == 2
  assert [atom.name for atom in ag.atoms()] == ["ca", "n"]
  ag.new_atoms(number_of_additional_atoms=3)
  assert ag.atoms_size() == 5
  assert ag.atoms().size() == 5
  for atom in ag.atoms():
    assert atom.parent().memory_id() == ag.memory_id()
  assert [a.name for a in ag.atoms()] == ["ca", "n", "", "", ""]
  #
  ag.insert_atom(i=0, atom=pdb.hierarchy_v2.atom().set_name(new_name="0"))
  assert [a.name for a in ag.atoms()] == ["0", "ca", "n", "", "", ""]
  ag.insert_atom(i=-1, atom=pdb.hierarchy_v2.atom().set_name(new_name="x"))
  assert [a.name for a in ag.atoms()] == ["0", "ca", "n", "", "", "x", ""]
  a = ag.atoms()[-1]
  assert a.parent().memory_id() == ag.memory_id()
  ag.remove_atom(i=-1)
  assert a.parent() is None
  assert [a.name for a in ag.atoms()] == ["0", "ca", "n", "", "", "x"]
  ag.remove_atom(i=1)
  assert [a.name for a in ag.atoms()] == ["0", "n", "", "", "x"]
  a = ag.atoms()[-2]
  assert a.parent().memory_id() == ag.memory_id()
  assert ag.find_atom_index(atom=a, must_be_present=True) == 3
  ag.remove_atom(i=-2)
  assert a.parent() is None
  assert [a.name for a in ag.atoms()] == ["0", "n", "", "x"]
  a = pdb.hierarchy_v2.atom().set_name(new_name="y")
  assert ag.find_atom_index(atom=a) == -1
  try: ag.find_atom_index(atom=a, must_be_present=True)
  except RuntimeError, e:
    assert str(e) == "atom not in atom_group."
  else: raise Exception_expected
  ag.insert_atom(i=4, atom=a)
  assert ag.find_atom_index(atom=a) == 4
  assert [a.name for a in ag.atoms()] == ["0", "n", "", "x", "y"]
  #
  try: pdb.hierarchy_v2.atom_group(altloc="ab")
  except (ValueError, RuntimeError), e:
    assert str(e) == "string is too long for target variable " \
      "(maximum length is 1 character, 2 given)."
  else: raise Exception_expected

def exercise_residue_group():
  rg = pdb.hierarchy_v2.residue_group()
  assert rg.resseq == ""
  assert rg.icode == ""
  assert rg.link_to_previous
  rg = pdb.hierarchy_v2.residue_group(
    resseq="   1", icode="i", link_to_previous=False)
  assert rg.resseq == "   1"
  rg.resseq = "   2"
  assert rg.resseq == "   2"
  assert rg.icode == "i"
  rg.icode = "j"
  assert rg.icode == "j"
  assert not rg.link_to_previous
  rg.link_to_previous = True
  assert rg.link_to_previous
  rg.link_to_previous = False
  #
  ag = pdb.hierarchy_v2.atom_group(altloc="a")
  assert ag.parent() is None
  rg.append_atom_group(atom_group=ag)
  assert ag.parent().memory_id() == rg.memory_id()
  c = pdb.hierarchy_v2.chain()
  for i,rgc in enumerate([
                 pdb.hierarchy_v2.residue_group(parent=c, other=rg),
                 rg.detached_copy()]):
    assert rgc.memory_id() != rg.memory_id()
    assert rg.parent() is None
    if (i == 0):
      assert rgc.parent().memory_id() == c.memory_id()
    else:
      assert rgc.parent() is None
    assert rgc.resseq == "   2"
    assert rgc.icode == "j"
    assert not rgc.link_to_previous
    assert rgc.atom_groups_size() == 1
    assert rgc.atom_groups()[0].memory_id() != rg.atom_groups()[0].memory_id()
    assert rgc.atom_groups()[0].altloc == "a"
    rg.append_atom_group(atom_group=pdb.hierarchy_v2.atom_group(altloc="%d"%i))
    assert rg.atom_groups_size() == 2+i
    assert rgc.atom_groups_size() == 1
    assert [ag.altloc for ag in rg.atom_groups()] == ["a", "0", "1"][:i+2]
  #
  c1 = pdb.hierarchy_v2.chain(id="a")
  c2 = pdb.hierarchy_v2.chain(id="b")
  assert c1.memory_id() != c2.memory_id()
  rg = pdb.hierarchy_v2.residue_group()
  assert rg.parent() is None
  rg = pdb.hierarchy_v2.residue_group(parent=c1)
  assert rg.parent().memory_id() == c1.memory_id()
  del c1
  assert rg.parent() is None
  #
  c1 = pdb.hierarchy_v2.chain(id="p")
  rg13l = c1.new_residue_group(resseq="13", icode="l")
  assert rg13l.resseq == "13"
  assert rg13l.icode == "l"
  #
  c1 = pdb.hierarchy_v2.chain(id="a")
  c1.pre_allocate_residue_groups(number_of_additional_residue_groups=2)
  assert c1.residue_groups_size() == 0
  assert len(c1.residue_groups()) == 0
  c1.new_residue_groups(number_of_additional_residue_groups=2)
  assert c1.residue_groups_size() == 2
  assert len(c1.residue_groups()) == 2
  for residue_group in c1.residue_groups():
    assert residue_group.parent().memory_id() == c1.memory_id()
  assert c1.atoms_size() == 0
  assert c1.atoms().size() == 0
  #
  for altloc in ["w", "v", "u"]:
    rg.insert_atom_group(
      i=0, atom_group=pdb.hierarchy_v2.atom_group(altloc=altloc))
  assert [ag.altloc for ag in rg.atom_groups()] == ["u", "v", "w"]
  rg.remove_atom_group(i=-1)
  assert [ag.altloc for ag in rg.atom_groups()] == ["u", "v"]
  ag = rg.atom_groups()[1]
  assert ag.parent().memory_id() == rg.memory_id()
  assert rg.find_atom_group_index(atom_group=ag) == 1
  rg.remove_atom_group(atom_group=ag)
  assert ag.parent() is None
  assert rg.find_atom_group_index(atom_group=ag) == -1
  try: rg.find_atom_group_index(atom_group=ag, must_be_present=True)
  except RuntimeError, e:
    assert str(e) == "atom_group not in residue_group."
  else: raise Exception_expected
  #
  ag1 = pdb.hierarchy_v2.atom_group()
  ag2 = pdb.hierarchy_v2.atom_group()
  a = pdb.hierarchy_v2.atom()
  ag1.append_atom(atom=a)
  try: ag2.append_atom(atom=a)
  except RuntimeError, e:
    assert str(e) == "atom has another parent atom_group already."
  else: raise Exception_expected
  #
  rg = pdb.hierarchy_v2.residue_group()
  assert rg.resid() == "     "
  rg = pdb.hierarchy_v2.residue_group(resseq="1", icode="i")
  assert rg.resid() == "   1i"
  rg = pdb.hierarchy_v2.residue_group(resseq=" 1 ", icode="j")
  assert rg.resid() == "  1 j"
  rg = pdb.hierarchy_v2.residue_group(resseq="ABCD", icode="")
  assert rg.resid() == "ABCD "
  rg = pdb.hierarchy_v2.residue_group(resseq="ABCD", icode="E")
  assert rg.resid() == "ABCDE"
  #
  rg = pdb.hierarchy_v2.residue_group()
  ag = pdb.hierarchy_v2.atom_group(altloc=" ")
  rg.append_atom_group(atom_group=ag)
  assert not rg.have_conformers()
  ag = pdb.hierarchy_v2.atom_group(altloc="")
  rg.append_atom_group(atom_group=ag)
  assert not rg.have_conformers()
  ag = pdb.hierarchy_v2.atom_group(altloc="a")
  rg.append_atom_group(atom_group=ag)
  assert rg.have_conformers()
  #
  rg = pdb.hierarchy_v2.residue_group()
  assert rg.move_blank_altloc_atom_groups_to_front() == 0
  ag = pdb.hierarchy_v2.atom_group(altloc="a")
  rg.append_atom_group(atom_group=ag)
  assert rg.move_blank_altloc_atom_groups_to_front() == 0
  ag = pdb.hierarchy_v2.atom_group(altloc=" ")
  rg.append_atom_group(atom_group=ag)
  assert rg.move_blank_altloc_atom_groups_to_front() == 1

def exercise_chain():
  c = pdb.hierarchy_v2.chain()
  assert c.id == ""
  c = pdb.hierarchy_v2.chain(id="a")
  assert c.id == "a"
  c.id = "x"
  assert c.id == "x"
  #
  m1 = pdb.hierarchy_v2.model(id="1")
  m2 = pdb.hierarchy_v2.model(id="2")
  assert m1.memory_id() != m2.memory_id()
  c = pdb.hierarchy_v2.chain()
  assert c.parent() is None
  c = pdb.hierarchy_v2.chain(parent=m1)
  assert c.parent().memory_id() == m1.memory_id()
  del m1
  assert c.parent() is None
  #
  c = pdb.hierarchy_v2.chain()
  #
  c = pdb.hierarchy_v2.chain()
  c.pre_allocate_residue_groups(number_of_additional_residue_groups=2)
  assert c.residue_groups_size() == 0
  assert len(c.residue_groups()) == 0
  c.new_residue_groups(number_of_additional_residue_groups=2)
  assert c.residue_groups_size() == 2
  assert len(c.residue_groups()) == 2
  for residue_group in c.residue_groups():
    assert residue_group.parent().memory_id() == c.memory_id()
  assert c.atoms_size() == 0
  assert c.atoms().size() == 0
  #
  c.residue_groups()[0].resseq = "ugh"
  c.id = "ci"
  m = pdb.hierarchy_v2.model()
  for i,cc in enumerate([
                pdb.hierarchy_v2.chain(parent=m, other=c),
                c.detached_copy()]):
    assert cc.memory_id() != c.memory_id()
    assert c.parent() is None
    if (i == 0):
      assert cc.parent().memory_id() == m.memory_id()
    else:
      assert cc.parent() is None
    assert cc.id == "ci"
    assert cc.residue_groups_size() == 2
    assert cc.residue_groups()[0].memory_id() \
         != c.residue_groups()[0].memory_id()
    assert cc.residue_groups()[0].resseq == "ugh"
    c.append_residue_group(
      residue_group=pdb.hierarchy_v2.residue_group(resseq="%03d"%i))
    assert c.residue_groups_size() == 3+i
    assert cc.residue_groups_size() == 2
    assert [rg.resseq for rg in c.residue_groups()] \
        == ["ugh", "", "000", "001"][:i+3]
  #
  c.insert_residue_group(
    i=3, residue_group=pdb.hierarchy_v2.residue_group(resseq="b012"))
  assert [rg.resseq for rg in c.residue_groups()] \
      == ["ugh", "", "000", "b012", "001"]
  c.remove_residue_group(i=1)
  assert [rg.resseq for rg in c.residue_groups()] \
      == ["ugh", "000", "b012", "001"]
  rg = c.residue_groups()[1]
  assert rg.parent().memory_id() == c.memory_id()
  assert c.find_residue_group_index(residue_group=rg) == 1
  c.remove_residue_group(residue_group=rg)
  assert rg.parent() is None
  assert c.find_residue_group_index(residue_group=rg) == -1
  try: c.find_residue_group_index(residue_group=rg, must_be_present=True)
  except RuntimeError, e:
    assert str(e) == "residue_group not in chain."
  else: raise Exception_expected
  #
  rg1 = pdb.hierarchy_v2.residue_group()
  rg2 = pdb.hierarchy_v2.residue_group()
  ag = pdb.hierarchy_v2.atom_group()
  rg1.append_atom_group(atom_group=ag)
  try: rg2.append_atom_group(atom_group=ag)
  except RuntimeError, e:
    assert str(e) == "atom_group has another parent residue_group already."
  else: raise Exception_expected
  #
  c = pdb.hierarchy_v2.chain(id="c")
  records = []
  c.append_atom_records(pdb_records=records)
  assert len(records) == 0
  rg = c.new_residue_group(resseq="s", icode="j")
  ag = rg.new_atom_group(altloc="a", resname="r")
  ag.append_atom(pdb.hierarchy_v2.atom().set_name("n"))
  assert ag.only_atom().pdb_label_columns() == "n   a  r c   sj"
  c.append_atom_records(pdb_records=records)
  assert records == [
    "ATOM        n   a  r c   sj      0.000   0.000   0.000  0.00  0.00"]
  rg = c.new_residue_group(resseq="t", icode="k")
  ag = rg.new_atom_group(altloc="b", resname="q")
  ag.append_atom(pdb.hierarchy_v2.atom().set_name("m"))
  rg = c.new_residue_group(resseq="u", icode="l", link_to_previous=False)
  ag = rg.new_atom_group(altloc="d", resname="p")
  ag.append_atom(pdb.hierarchy_v2.atom().set_name("o"))
  records = []
  c.append_atom_records(pdb_records=records)
  assert not show_diff("\n".join(records)+"\n", """\
ATOM        n   a  r c   sj      0.000   0.000   0.000  0.00  0.00
ATOM        m   b  q c   tk      0.000   0.000   0.000  0.00  0.00
BREAK
ATOM        o   d  p c   ul      0.000   0.000   0.000  0.00  0.00
""")
  #
  a = pdb.hierarchy_v2.atom()
  assert a.pdb_label_columns() == "               "
  a.set_name("n123")
  assert a.pdb_label_columns() == "n123           "
  ag = pdb.hierarchy_v2.atom_group(altloc="a", resname="res")
  ag.append_atom(a)
  assert a.pdb_label_columns() == "n123ares       "
  rg = pdb.hierarchy_v2.residue_group(resseq="a000", icode="i")
  rg.append_atom_group(ag)
  assert a.pdb_label_columns() == "n123ares  a000i"
  c = pdb.hierarchy_v2.chain(id="ke")
  c.append_residue_group(rg)
  assert a.pdb_label_columns() == "n123areskea000i"

def exercise_model():
  m = pdb.hierarchy_v2.model()
  assert m.id == ""
  m = pdb.hierarchy_v2.model(id="42")
  assert m.id == "42"
  m.id = "-23"
  assert m.id == "-23"
  #
  m = pdb.hierarchy_v2.model(id="17")
  assert m.parent() is None
  m.pre_allocate_chains(number_of_additional_chains=2)
  assert m.chains_size() == 0
  assert len(m.chains()) == 0
  ch_a = m.new_chain(id="a")
  assert ch_a.id == "a"
  assert ch_a.parent().memory_id() == m.memory_id()
  assert m.chains_size() == 1
  assert len(m.chains()) == 1
  ch_b = pdb.hierarchy_v2.chain(id="b")
  assert ch_b.id == "b"
  assert ch_b.parent() is None
  m.append_chain(chain=ch_b)
  assert m.chains_size() == 2
  chains = m.chains()
  assert len(chains) == 2
  assert chains[0].memory_id() == ch_a.memory_id()
  assert chains[1].memory_id() == ch_b.memory_id()
  m.new_chains(number_of_additional_chains=3)
  assert m.chains_size() == 5
  assert len(m.chains()) == 5
  for chain in m.chains():
    assert chain.parent().memory_id() == m.memory_id()
  assert m.atoms_size() == 0
  assert m.atoms().size() == 0
  #
  r = pdb.hierarchy_v2.root()
  for i,mc in enumerate([
                pdb.hierarchy_v2.model(parent=r, other=m),
                m.detached_copy()]):
    assert mc.memory_id() != m.memory_id()
    assert m.parent() is None
    if (i == 0):
      assert mc.parent().memory_id() == r.memory_id()
    else:
      assert mc.parent() is None
    assert mc.id == "17"
    assert mc.chains_size() == 5
    assert mc.chains()[0].memory_id() != m.chains()[0].memory_id()
    assert mc.chains()[0].id == "a"
    m.append_chain(chain=pdb.hierarchy_v2.chain(id="%d"%i))
    assert m.chains_size() == 6+i
    assert mc.chains_size() == 5
    assert [c.id for c in m.chains()] \
        == ["a", "b", "", "", "", "0", "1"][:i+6]
  #
  m.insert_chain(i=-3, chain=pdb.hierarchy_v2.chain(id="3"))
  assert [c.id for c in m.chains()] \
      == ["a", "b", "", "", "3", "", "0", "1"]
  m.remove_chain(i=-2)
  assert [c.id for c in m.chains()] \
      == ["a", "b", "", "", "3", "", "1"]
  c = m.chains()[0]
  assert c.parent().memory_id() == m.memory_id()
  assert m.find_chain_index(chain=c) == 0
  m.remove_chain(chain=c)
  assert c.parent() is None
  assert m.find_chain_index(chain=c) == -1
  try: m.find_chain_index(chain=c, must_be_present=True)
  except RuntimeError, e:
    assert str(e) == "chain not in model."
  else: raise Exception_expected
  #
  m1 = pdb.hierarchy_v2.model()
  m2 = pdb.hierarchy_v2.model()
  c = pdb.hierarchy_v2.chain()
  m1.append_chain(chain=c)
  try: m2.append_chain(chain=c)
  except RuntimeError, e:
    assert str(e) == "chain has another parent model already."
  else: raise Exception_expected

def exercise_root():
  r = pdb.hierarchy_v2.root()
  m = pdb.hierarchy_v2.model()
  assert m.parent() is None
  m = pdb.hierarchy_v2.model(parent=r)
  assert m.parent().memory_id() == r.memory_id()
  assert m.id == ""
  m = pdb.hierarchy_v2.model(parent=r, id="2")
  assert m.parent().memory_id() == r.memory_id()
  assert m.id == "2"
  del r
  assert m.parent() is None
  #
  r = pdb.hierarchy_v2.root()
  assert r.info.size() == 0
  r.info.append("abc")
  assert r.info.size() == 1
  r.info = flex.std_string(["a", "b"])
  assert r.info.size() == 2
  r.pre_allocate_models(number_of_additional_models=2)
  assert r.models_size() == 0
  assert len(r.models()) == 0
  m_a = r.new_model(id="3")
  assert m_a.id == "3"
  assert m_a.parent().memory_id() == r.memory_id()
  assert r.models_size() == 1
  assert len(r.models()) == 1
  m_b = pdb.hierarchy_v2.model(id="5")
  assert m_b.parent() is None
  r.append_model(model=m_b)
  assert r.models_size() == 2
  models = r.models()
  assert len(models) == 2
  assert models[0].memory_id() == m_a.memory_id()
  assert models[1].memory_id() == m_b.memory_id()
  r.new_models(number_of_additional_models=3)
  assert r.models_size() == 5
  assert len(r.models()) == 5
  for model in r.models():
    assert model.parent().memory_id() == r.memory_id()
  assert r.atoms_size() == 0
  assert r.atoms().size() == 0
  #
  rc = r.deep_copy()
  assert rc.memory_id() != r.memory_id()
  assert list(rc.info) == ["a", "b"]
  assert rc.info.id() != r.info.id()
  assert rc.models_size() == 5
  assert rc.models()[0].memory_id() != r.models()[0].memory_id()
  assert rc.models()[0].id == "3"
  r.append_model(model=pdb.hierarchy_v2.model(id="7"))
  assert r.models_size() == 6
  assert rc.models_size() == 5
  assert [m.id for m in r.models()] == ["3", "5", "", "", "", "7"]
  assert [m.id for m in rc.models()] == ["3", "5", "", "", ""]
  rc.append_model(model=pdb.hierarchy_v2.model(id="8"))
  assert r.models_size() == 6
  assert rc.models_size() == 6
  assert [m.id for m in rc.models()] == ["3", "5", "", "", "", "8"]
  #
  r = rc.deep_copy()
  r.insert_model(i=4, model=pdb.hierarchy_v2.model(id="M"))
  assert [m.id for m in r.models()] \
      == ["3", "5", "", "", "M", "", "8"]
  r.remove_model(i=1)
  assert [m.id for m in r.models()] \
      == ["3", "", "", "M", "", "8"]
  m = r.models()[-1]
  assert m.parent().memory_id() == r.memory_id()
  assert r.find_model_index(model=m) == 5
  r.remove_model(model=m)
  assert m.parent() is None
  assert r.find_model_index(model=m) == -1
  try: r.find_model_index(model=m, must_be_present=True)
  except RuntimeError, e:
    assert str(e) == "model not in root."
  else: raise Exception_expected
  #
  r1 = pdb.hierarchy_v2.root()
  r2 = pdb.hierarchy_v2.root()
  m = pdb.hierarchy_v2.model()
  r1.append_model(model=m)
  try: r2.append_model(model=m)
  except RuntimeError, e:
    assert str(e) == "model has another parent root already."
  else: raise Exception_expected

def exercise_format_atom_record():
  for hetero,record_name in [(False, "ATOM  "), (True, "HETATM")]:
    a = (pdb.hierarchy_v2.atom()
      .set_name(new_name="NaMe")
      .set_segid(new_segid="sEgI")
      .set_element(new_element="El")
      .set_charge(new_charge="cH")
      .set_serial(new_serial="B1234")
      .set_xyz(new_xyz=(1.3,2.1,3.2))
      .set_sigxyz(new_sigxyz=(.1,.2,.3))
      .set_occ(new_occ=0.4)
      .set_sigocc(new_sigocc=0.1)
      .set_b(new_b=4.8)
      .set_sigb(new_sigb=0.7)
      .set_uij(new_uij=(1.3,2.1,3.2,4.3,2.7,9.3))
      .set_siguij(new_siguij=(.1,.2,.3,.6,.1,.9))
      .set_hetero(new_hetero=hetero))
    s = a.format_atom_record()
    assert not show_diff(s, """\
%sB1234 NaMe                 1.300   2.100   3.200  0.40  4.80      sEgIElcH"""
      % record_name)
    ag = pdb.hierarchy_v2.atom_group(altloc="x", resname="uvw")
    ag.append_atom(atom=a)
    s = a.format_atom_record()
    assert not show_diff(s, """\
%sB1234 NaMexuvw             1.300   2.100   3.200  0.40  4.80      sEgIElcH"""
      % record_name)
    rg = pdb.hierarchy_v2.residue_group(resseq="pqrs", icode="t")
    rg.append_atom_group(atom_group=ag)
    s = a.format_atom_record()
    assert not show_diff(s, """\
%sB1234 NaMexuvw  pqrst      1.300   2.100   3.200  0.40  4.80      sEgIElcH"""
      % record_name)
    for chain_id in ["", "g", "hi"]:
      ch = pdb.hierarchy_v2.chain(id=chain_id)
      ch.append_residue_group(residue_group=rg)
      s = a.format_atom_record()
      assert not show_diff(s, """\
%sB1234 NaMexuvw%2spqrst      1.300   2.100   3.200  0.40  4.80      sEgIElcH"""
      % (record_name, chain_id))

def exercise_construct_hierarchy():
  def check(pdb_string,
        expected_root_as_str=None,
        expected_overall_counts_as_str=None,
        level_id=None,
        prefix=""):
    pdb_inp = pdb.input(source_info=None, lines=flex.split_lines(pdb_string))
    root = pdb_inp.construct_hierarchy_v2()
    if (expected_root_as_str is not None):
      s = root.as_str(prefix=prefix, level_id=level_id)
      if (len(expected_root_as_str) == 0):
        sys.stdout.write(s)
      else:
        assert not show_diff(s, expected_root_as_str)
    if (expected_overall_counts_as_str is not None):
      s = root.overall_counts().as_str(
        prefix=prefix,
        consecutive_residue_groups_max_show=3,
        duplicate_atom_labels_max_show=3)
      if (len(expected_overall_counts_as_str) == 0):
        sys.stdout.write(s)
      else:
        assert not show_diff(s, expected_overall_counts_as_str)
  #
  check("""\
MODEL        1
ATOM      1  N   MET A   1       6.215  22.789  24.067  1.00  0.00           N
ATOM      2  CA  MET A   1       6.963  22.789  22.822  1.00  0.00           C
HETATM    3  C   MET A   2       7.478  21.387  22.491  1.00  0.00           C
ATOM      4  O   MET A   2       8.406  20.895  23.132  1.00  0.00           O
ENDMDL
MODEL 3
HETATM    9 2H3  MPR B   5      16.388   0.289   6.613  1.00  0.08
SIGATM    9 2H3  MPR B   5       0.155   0.175   0.155  0.00  0.05
ANISOU    9 2H3  MPR B   5      848    848    848      0      0      0
SIGUIJ    9 2H3  MPR B   5      510    510    510      0      0      0
TER
ATOM     10  N   CYSCH   6      14.270   2.464   3.364  1.00  0.07
SIGATM   10  N   CYSCH   6       0.012   0.012   0.011  0.00  0.00
ANISOU   10  N   CYSCH   6      788    626    677   -344    621   -232
SIGUIJ   10  N   CYSCH   6        3     13      4     11      6     13
TER
ENDMDL
END
""", """\
model id="   1" #chains=1
  chain id="A" #residue_groups=2
    resid="   1 " #atom_groups=1
      altloc="" resname="MET" #atoms=2
        " N  "
        " CA "
    resid="   2 " #atom_groups=1
      altloc="" resname="MET" #atoms=2
        " C  "
        " O  "
model id="   3" #chains=2
  chain id="B" #residue_groups=1
    resid="   5 " #atom_groups=1
      altloc="" resname="MPR" #atoms=1
        "2H3 "
  chain id="CH" #residue_groups=1
    resid="   6 " #atom_groups=1
      altloc="" resname="CYS" #atoms=1
        " N  "
""", """\
total number of:
  models:     2
  chains:     3
  alt. conf.: 0
  residues:   4
  atoms:      6
number of atom element+charge types: 4
histogram of atom element+charge frequency:
  "    " 2
  " C  " 2
  " N  " 1
  " O  " 1
residue name classes:
  "common_amino_acid" 3
  "other"             1
number of chain ids: 3
histogram of chain id frequency:
  "A"  1
  "B"  1
  "CH" 1
number of alt. conf. ids: 0
number of residue names: 3
histogram of residue name frequency:
  "MET" 2
  "CYS" 1
  "MPR" 1    other
""")
  #
  check("""\
ATOM         N1 AR01
ATOM         N2 BR01
ATOM         N1 CR02
ATOM         N2  R02
""", """\
model id="   0" #chains=1
  chain id=" " #residue_groups=2
    resid="     " #atom_groups=2
      altloc="A" resname="R01" #atoms=1
        " N1 "
      altloc="B" resname="R01" #atoms=1
        " N2 "
    resid="     " #atom_groups=2  ### Info: same as previous resid ###
      altloc="" resname="R02" #atoms=1
        " N2 "
      altloc="C" resname="R02" #atoms=1
        " N1 "
""")
  #
  check("""\
ATOM         N1 BR01
ATOM         N1  R01
ATOM         N2  R01
ATOM         N3 BR01
ATOM         N3  R01
ATOM         N1  R02
ATOM         N1 BR02
ATOM         N2  R02
ATOM         N3 BR02
ATOM         N3  R02
ATOM         N1  R03
ATOM         N1 BR03
ATOM         N2  R03
ATOM         N3 BR03
ATOM         N3  R03
""", """\
model id="   0" #chains=1
  chain id=" " #residue_groups=3
    resid="     " #atom_groups=3
      altloc="" resname="R01" #atoms=1
        " N2 "
      altloc=" " resname="R01" #atoms=2
        " N1 "
        " N3 "
      altloc="B" resname="R01" #atoms=2
        " N1 "
        " N3 "
    resid="     " #atom_groups=3  ### Info: same as previous resid ###
      altloc="" resname="R02" #atoms=1
        " N2 "
      altloc=" " resname="R02" #atoms=2
        " N1 "
        " N3 "
      altloc="B" resname="R02" #atoms=2
        " N1 "
        " N3 "
    resid="     " #atom_groups=3  ### Info: same as previous resid ###
      altloc="" resname="R03" #atoms=1
        " N2 "
      altloc=" " resname="R03" #atoms=2
        " N1 "
        " N3 "
      altloc="B" resname="R03" #atoms=2
        " N1 "
        " N3 "
""")
  #
  check("""\
ATOM         N1 BR01
ATOM         N1  R01
ATOM         N2  R01
ATOM         N3 BR01
ATOM         N3  R01
ATOM         N1 AR02
ATOM         N1 BR02
ATOM         N2  R02
ATOM         N3 BR02
ATOM         N3 AR02
ATOM         N1  R03
ATOM         N1 BR03
ATOM         N2  R03
ATOM         N3 BR03
ATOM         N3  R03
""", """\
  model id="   0" #chains=1
    chain id=" " #residue_groups=3
      resid="     " #atom_groups=3
        altloc="" resname="R01" #atoms=1
          " N2 "
        altloc=" " resname="R01" #atoms=2
          " N1 "
          " N3 "
        altloc="B" resname="R01" #atoms=2
          " N1 "
          " N3 "
      resid="     " #atom_groups=3  ### Info: same as previous resid ###
        altloc="" resname="R02" #atoms=1
          " N2 "
        altloc="A" resname="R02" #atoms=2
          " N1 "
          " N3 "
        altloc="B" resname="R02" #atoms=2
          " N1 "
          " N3 "
      resid="     " #atom_groups=3  ### Info: same as previous resid ###
        altloc="" resname="R03" #atoms=1
          " N2 "
        altloc=" " resname="R03" #atoms=2
          " N1 "
          " N3 "
        altloc="B" resname="R03" #atoms=2
          " N1 "
          " N3 "
""", """\
  total number of:
    models:      1
    chains:      1
    alt. conf.:  3
    residues:    3
    atoms:      15
  number of atom element+charge types: 1
  histogram of atom element+charge frequency:
    "    " 15
  residue name classes:
    "other" 3
  number of chain ids: 1
  histogram of chain id frequency:
    " " 1
  number of alt. conf. ids: 3
  histogram of alt. conf. id frequency:
    " " 1
    "A" 1
    "B" 1
  residue alt. conf. situations:
    pure main conf.:     0
    pure alt. conf.:     0
    proper alt. conf.:   1
    improper alt. conf.: 2
  residue with proper altloc
    ATOM         N2  R02
    ATOM         N1 AR02
    ATOM         N3 AR02
    ATOM         N1 BR02
    ATOM         N3 BR02
  residue with improper altloc
    ATOM         N2  R01
    ATOM         N1  R01
    ATOM         N3  R01
    ATOM         N1 BR01
    ATOM         N3 BR01
  chains with mix of proper and improper alt. conf.: 0
  number of residue names: 3
  histogram of residue name frequency:
    "R01" 1    other
    "R02" 1    other
    "R03" 1    other
  number of consecutive residue groups with same resid: 2
    residue group:
      "ATOM         N2  R01       "
      ... 3 atoms not shown
      "ATOM         N3 BR01       "
    next residue group:
      "ATOM         N2  R02       "
      ... 3 atoms not shown
      "ATOM         N3 BR02       "
    next residue group:
      "ATOM         N2  R03       "
      ... 3 atoms not shown
      "ATOM         N3 BR03       "
""", prefix="  ")
  #
  check("""\
ATOM         N1 BR01
ATOM         N1 AR01
ATOM         N2 CR01
ATOM         N3 BR01
ATOM         N3 AR01
ATOM         N1  R02
ATOM         N1 BR02
ATOM         N2  R02
ATOM         N3 BR02
ATOM         N3  R02
ATOM         N1 CR03
ATOM         N1 BR03
ATOM         N2 BR03
ATOM         N2 CR03
ATOM         N3  R03
""", """\
model id="   0" #chains=1
  chain id=" " #residue_groups=3
    resid="     " #atom_groups=3
      altloc="B" resname="R01" #atoms=2
        " N1 "
        " N3 "
      altloc="A" resname="R01" #atoms=2
        " N1 "
        " N3 "
      altloc="C" resname="R01" #atoms=1
        " N2 "
    resid="     " #atom_groups=3  ### Info: same as previous resid ###
      altloc="" resname="R02" #atoms=1
        " N2 "
      altloc=" " resname="R02" #atoms=2
        " N1 "
        " N3 "
      altloc="B" resname="R02" #atoms=2
        " N1 "
        " N3 "
    resid="     " #atom_groups=3  ### Info: same as previous resid ###
      altloc="" resname="R03" #atoms=1
        " N3 "
      altloc="C" resname="R03" #atoms=2
        " N1 "
        " N2 "
      altloc="B" resname="R03" #atoms=2
        " N1 "
        " N2 "
""", """\
total number of:
  models:      1
  chains:      1
  alt. conf.:  4
  residues:    3
  atoms:      15
number of atom element+charge types: 1
histogram of atom element+charge frequency:
  "    " 15
residue name classes:
  "other" 3
number of chain ids: 1
histogram of chain id frequency:
  " " 1
number of alt. conf. ids: 4
histogram of alt. conf. id frequency:
  " " 1
  "A" 1
  "B" 1
  "C" 1
residue alt. conf. situations:
  pure main conf.:     0
  pure alt. conf.:     1
  proper alt. conf.:   1
  improper alt. conf.: 1
residue with proper altloc
  ATOM         N3  R03
  ATOM         N1 CR03
  ATOM         N2 CR03
  ATOM         N1 BR03
  ATOM         N2 BR03
residue with improper altloc
  ATOM         N2  R02
  ATOM         N1  R02
  ATOM         N3  R02
  ATOM         N1 BR02
  ATOM         N3 BR02
chains with mix of proper and improper alt. conf.: 0
number of residue names: 3
histogram of residue name frequency:
  "R01" 1    other
  "R02" 1    other
  "R03" 1    other
number of consecutive residue groups with same resid: 2
  residue group:
    "ATOM         N1 BR01       "
    ... 3 atoms not shown
    "ATOM         N2 CR01       "
  next residue group:
    "ATOM         N2  R02       "
    ... 3 atoms not shown
    "ATOM         N3 BR02       "
  next residue group:
    "ATOM         N3  R03       "
    ... 3 atoms not shown
    "ATOM         N2 BR03       "
""")
  #
  check("""\
REMARK    ANTIBIOTIC                              26-JUL-06   2IZQ
ATOM    220  N  ATRP A  11      20.498  12.832  34.558  0.50  6.03           N
ATOM    221  CA ATRP A  11      21.094  12.032  35.602  0.50  5.24           C
ATOM    222  C  ATRP A  11      22.601  12.088  35.532  0.50  6.49           C
ATOM    223  O  ATRP A  11      23.174  12.012  34.439  0.50  7.24           O
ATOM    234  H  ATRP A  11      20.540  12.567  33.741  0.50  7.24           H
ATOM    235  HA ATRP A  11      20.771  12.306  36.485  0.50  6.28           H
ATOM    244  N  CPHE A  11      20.226  13.044  34.556  0.15  6.35           N
ATOM    245  CA CPHE A  11      20.950  12.135  35.430  0.15  5.92           C
ATOM    246  C  CPHE A  11      22.448  12.425  35.436  0.15  6.32           C
ATOM    247  O  CPHE A  11      22.961  12.790  34.373  0.15  6.08           O
ATOM    255  N  BTYR A  11      20.553  12.751  34.549  0.35  5.21           N
ATOM    256  CA BTYR A  11      21.106  11.838  35.524  0.35  5.51           C
ATOM    257  C  BTYR A  11      22.625  11.920  35.572  0.35  5.42           C
ATOM    258  O  BTYR A  11      23.299  11.781  34.538  0.35  5.30           O
ATOM    262  HB2CPHE A  11      21.221  10.536  34.146  0.15  7.21           H
ATOM    263  CD2BTYR A  11      18.463  10.012  36.681  0.35  9.08           C
ATOM    264  HB3CPHE A  11      21.198  10.093  35.647  0.15  7.21           H
ATOM    265  CE1BTYR A  11      17.195   9.960  34.223  0.35 10.76           C
ATOM    266  HD1CPHE A  11      19.394   9.937  32.837  0.15 10.53           H
ATOM    267  CE2BTYR A  11      17.100   9.826  36.693  0.35 11.29           C
ATOM    268  HD2CPHE A  11      18.873  10.410  36.828  0.15  9.24           H
ATOM    269  CZ BTYR A  11      16.546   9.812  35.432  0.35 11.90           C
ATOM    270  HE1CPHE A  11      17.206   9.172  32.650  0.15 12.52           H
ATOM    271  OH BTYR A  11      15.178   9.650  35.313  0.35 19.29           O
ATOM    272  HE2CPHE A  11      16.661   9.708  36.588  0.15 11.13           H
ATOM    273  HZ CPHE A  11      15.908   9.110  34.509  0.15 13.18           H
ATOM    274  H  BTYR A  11      20.634  12.539  33.720  0.35  6.25           H
ATOM    275  HA BTYR A  11      20.773  12.116  36.402  0.35  6.61           H
ATOM    276  HB2BTYR A  11      20.949  10.064  34.437  0.35  6.78           H
""", """\
model id="   0" #chains=1
  chain id="A" #residue_groups=1
    resid="  11 " #atom_groups=3  ### Info: with mixed residue names ###
      altloc="A" resname="TRP" #atoms=6
      altloc="C" resname="PHE" #atoms=11
      altloc="B" resname="TYR" #atoms=12
""", """\
total number of:
  models:      1
  chains:      1
  alt. conf.:  3
  residues:    1 (1 with mixed residue names)
  atoms:      29
number of atom element+charge types: 4
histogram of atom element+charge frequency:
  " H  " 12
  " C  " 10
  " O  "  4
  " N  "  3
residue name classes:
  "common_amino_acid" 3
number of chain ids: 1
histogram of chain id frequency:
  "A" 1
number of alt. conf. ids: 3
histogram of alt. conf. id frequency:
  "A" 1
  "B" 1
  "C" 1
residue alt. conf. situations:
  pure main conf.:     0
  pure alt. conf.:     1
  proper alt. conf.:   0
  improper alt. conf.: 0
chains with mix of proper and improper alt. conf.: 0
number of residue names: 3
histogram of residue name frequency:
  "PHE" 1
  "TRP" 1
  "TYR" 1
""", level_id="atom_group")
  #
  root = pdb.input(
    source_info=None,
    lines=flex.split_lines("""\
BREAK
""")).construct_hierarchy_v2()
  assert root.models_size() == 0
  root = pdb.input(
    source_info=None,
    lines=flex.split_lines("""\
BREAK
ATOM      1  CB  LYS   109
BREAK
TER
""")).construct_hierarchy_v2()
  assert not root.only_residue_group().link_to_previous
  root = pdb.input(
    source_info=None,
    lines=flex.split_lines("""\
BREAK
ATOM      1  CB  LYS   109
ATOM      2  CG  LYS   109
BREAK
TER
""")).construct_hierarchy_v2()
  assert not root.only_residue_group().link_to_previous
  pdb_str = """\
ATOM      1  CB  LYS   109
ATOM      2  CG  LYS   109
ATOM      3  CA  LYS   110
ATOM      4  CB  LYS   110
BREAK
ATOM      5  CA  LYS   111
ATOM      6  CB  LYS   111
ATOM      7  CA  LYS   112
ATOM      8  CB  LYS   112
"""
  lines = flex.split_lines(pdb_str)
  for i_proc in [0,1]:
    root = pdb.input(source_info=None, lines=lines).construct_hierarchy_v2()
    residue_groups = root.only_chain().residue_groups()
    assert len(residue_groups) == 4
    assert not residue_groups[0].link_to_previous
    assert residue_groups[1].link_to_previous
    assert not residue_groups[2].link_to_previous
    assert residue_groups[3].link_to_previous
    if (i_proc == 0):
      lines = lines.select(flex.size_t([0,2,4,5,7]))
  try: pdb.input(
    source_info=None,
    lines=flex.split_lines("""\
REMARK
ATOM      1  CB  LYS   109
BREAK
ATOM      2  CG  LYS   109
""")).construct_hierarchy_v2()
  except RuntimeError, e:
    assert not show_diff(str(e), "Misplaced BREAK record (input line 3).")
  else: raise Exception_expected
  try: pdb.input(
    source_info="file abc",
    lines=flex.split_lines("""\
REMARK
ATOM      1  CA  LYS   109
ATOM      2  CB  LYS   109
BREAK
ATOM      3  CA  LYS   110
BREAK
ATOM      4  CB  LYS   110
""")).construct_hierarchy_v2()
  except RuntimeError, e:
    assert not show_diff(str(e), "Misplaced BREAK record (file abc, line 6).")
  else: raise Exception_expected
  #
  check(pdb_str, """\
:=model id="   0" #chains=1
:=  chain id=" " #residue_groups=4
:=    resid=" 109 " #atom_groups=1
:=      altloc="" resname="LYS" #atoms=2
:=        " CB "
:=        " CG "
:=    resid=" 110 " #atom_groups=1
:=      altloc="" resname="LYS" #atoms=2
:=        " CA "
:=        " CB "
:=    ### chain break ###
:=    resid=" 111 " #atom_groups=1
:=      altloc="" resname="LYS" #atoms=2
:=        " CA "
:=        " CB "
:=    resid=" 112 " #atom_groups=1
:=      altloc="" resname="LYS" #atoms=2
:=        " CA "
:=        " CB "
""", """\
:=total number of:
:=  models:     1
:=  chains:     1 (1 explicit chain break)
:=  alt. conf.: 0
:=  residues:   4
:=  atoms:      8
:=number of atom element+charge types: 1
:=histogram of atom element+charge frequency:
:=  "    " 8
:=residue name classes:
:=  "common_amino_acid" 4
:=number of chain ids: 1
:=histogram of chain id frequency:
:=  " " 1
:=number of alt. conf. ids: 0
:=number of residue names: 1
:=histogram of residue name frequency:
:=  "LYS" 4
""", prefix=":=")
  #
  check(pdb_str, """\
model id="   0" #chains=1
  chain id=" " #residue_groups=4
    resid=" 109 " #atom_groups=1
      altloc="" resname="LYS" #atoms=2
    resid=" 110 " #atom_groups=1
      altloc="" resname="LYS" #atoms=2
    ### chain break ###
    resid=" 111 " #atom_groups=1
      altloc="" resname="LYS" #atoms=2
    resid=" 112 " #atom_groups=1
      altloc="" resname="LYS" #atoms=2
""", level_id="atom_group")
  #
  check(pdb_str, """\
model id="   0" #chains=1
  chain id=" " #residue_groups=4
    resid=" 109 " #atom_groups=1
    resid=" 110 " #atom_groups=1
    ### chain break ###
    resid=" 111 " #atom_groups=1
    resid=" 112 " #atom_groups=1
""", level_id="residue_group")
  #
  check(pdb_str, """\
model id="   0" #chains=1
  chain id=" " #residue_groups=4
""", level_id="chain")
  #
  check(pdb_str, """\
model id="   0" #chains=1
""", level_id="model")
  #
  check("""\
MODEL        1
ENDMDL
MODEL 1
ENDMDL
MODEL     1
ENDMDL
""", """\
model id="   1" #chains=0  ### WARNING: duplicate model id ###
model id="   1" #chains=0  ### WARNING: duplicate model id ###
model id="   1" #chains=0  ### WARNING: duplicate model id ###
""", """\
total number of:
  models:     3 (3 with duplicate model ids)
  chains:     0
  alt. conf.: 0
  residues:   0
  atoms:      0
number of atom element+charge types: 0
residue name classes: None
number of chain ids: 0
number of alt. conf. ids: 0
number of residue names: 0
""")
  #
  check("""\
MODEL        1
ATOM                 A
ATOM                 B
ATOM                 A
ENDMDL
MODEL 1
ATOM                 A   1
BREAK
ATOM                 A   2
ATOM                 B
ATOM                 A
ENDMDL
MODEL     2
ATOM                 A
BREAK
ATOM                 A    I
ATOM                 B
ENDMDL
""", """\
model id="   1" #chains=3  ### WARNING: duplicate model id ###
  chain id="A" #residue_groups=1  ### WARNING: duplicate chain id ###
    resid="     " #atom_groups=1
      altloc="" resname="   " #atoms=1
        "    "
  chain id="B" #residue_groups=1
    resid="     " #atom_groups=1
      altloc="" resname="   " #atoms=1
        "    "
  chain id="A" #residue_groups=1  ### WARNING: duplicate chain id ###
    resid="     " #atom_groups=1
      altloc="" resname="   " #atoms=1
        "    "
model id="   1" #chains=3  ### WARNING: duplicate model id ###
  chain id="A" #residue_groups=2  ### WARNING: duplicate chain id ###
    resid="   1 " #atom_groups=1
      altloc="" resname="   " #atoms=1
        "    "
    ### chain break ###
    resid="   2 " #atom_groups=1
      altloc="" resname="   " #atoms=1
        "    "
  chain id="B" #residue_groups=1
    resid="     " #atom_groups=1
      altloc="" resname="   " #atoms=1
        "    "
  chain id="A" #residue_groups=1  ### WARNING: duplicate chain id ###
    resid="     " #atom_groups=1
      altloc="" resname="   " #atoms=1
        "    "
model id="   2" #chains=2
  chain id="A" #residue_groups=2
    resid="     " #atom_groups=1
      altloc="" resname="   " #atoms=1
        "    "
    ### chain break ###
    resid="    I" #atom_groups=1
      altloc="" resname="   " #atoms=1
        "    "
  chain id="B" #residue_groups=1
    resid="     " #atom_groups=1
      altloc="" resname="   " #atoms=1
        "    "
""", """\
total number of:
  models:      3 (2 with duplicate model ids)
  chains:      8 (4 with duplicate chain ids; 2 explicit chain breaks)
  alt. conf.:  0
  residues:   10
  atoms:      10 (2 with duplicate labels)
number of atom element+charge types: 1
histogram of atom element+charge frequency:
  "    " 10
residue name classes:
  "other" 10
number of chain ids: 2
histogram of chain id frequency:
  "A" 5
  "B" 3
number of alt. conf. ids: 0
number of residue names: 1
histogram of residue name frequency:
  "   " 10    other
number of consecutive residue groups with same resid: 3
  residue group:
    "ATOM                 A     "
  next residue group:
    "ATOM                 B     "
  next residue group:
    "ATOM                 A     "
  -------------------------------
  residue group:
    "ATOM                 B     "
  next residue group:
    "ATOM                 A     "
number of groups of duplicate atom labels: 1
  total number of affected atoms:          2
  group "ATOM                 A     "
        "ATOM                 A     "
""")
  #
  check("""\
ATOM     54  CA  GLY A   9
ATOM     55  CA  GLY A   9
ATOM     56  CA BGLY A   9
""", """\
model id="   0" #chains=1
  chain id="A" #residue_groups=1
    resid="   9 " #atom_groups=2
      altloc=" " resname="GLY" #atoms=2
        " CA "
        " CA "
      altloc="B" resname="GLY" #atoms=1
        " CA "
""", """\
total number of:
  models:     1
  chains:     1
  alt. conf.: 2
  residues:   1
  atoms:      3 (2 with duplicate labels)
number of atom element+charge types: 1
histogram of atom element+charge frequency:
  "    " 3
residue name classes:
  "common_amino_acid" 1
number of chain ids: 1
histogram of chain id frequency:
  "A" 1
number of alt. conf. ids: 2
histogram of alt. conf. id frequency:
  " " 1
  "B" 1
residue alt. conf. situations:
  pure main conf.:     0
  pure alt. conf.:     0
  proper alt. conf.:   0
  improper alt. conf.: 1
residue with improper altloc
  ATOM     54  CA  GLY A   9
  ATOM     55  CA  GLY A   9
  ATOM     56  CA BGLY A   9
chains with mix of proper and improper alt. conf.: 0
number of residue names: 1
histogram of residue name frequency:
  "GLY" 1
number of groups of duplicate atom labels: 1
  total number of affected atoms:          2
  group "ATOM     54  CA  GLY A   9 "
        "ATOM     55  CA  GLY A   9 "
""")
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM     68  HD1 LEU B 441
ATOM     69  HD1 LEU B 441
ATOM     70  HD1 LEU B 441
ATOM     71  HD2 LEU B 441
ATOM     72  HD2 LEU B 441
ATOM     73  HD2 LEU B 441
"""))
  oc = pdb_inp.construct_hierarchy_v2().overall_counts()
  try: oc.raise_duplicate_atom_labels_if_necessary(max_show=1)
  except Sorry, e:
    assert not show_diff(str(e), '''\
number of groups of duplicate atom labels: 2
  total number of affected atoms:          6
  group "ATOM     68  HD1 LEU B 441 "
        "ATOM     69  HD1 LEU B 441 "
        "ATOM     70  HD1 LEU B 441 "
  ... 1 remaining group not shown''')
  else: raise Exception_expected
  assert not show_diff(oc.have_duplicate_atom_labels_message(), '''\
number of groups of duplicate atom labels: 2
  total number of affected atoms:          6
  group "ATOM     68  HD1 LEU B 441 "
        "ATOM     69  HD1 LEU B 441 "
        "ATOM     70  HD1 LEU B 441 "
  group "ATOM     71  HD2 LEU B 441 "
        "ATOM     72  HD2 LEU B 441 "
        "ATOM     73  HD2 LEU B 441 "''')
  #
  check("""\
ATOM     68  HD1 LEU B 441
ATOM     69  HD2 LEU B 441
ATOM     70  HD3 LEU B 441
ATOM     71  HD4 LEU B 441
ATOM     72  HD1 LEU B 441
ATOM     73  HD2 LEU B 441
ATOM     74  HD3 LEU B 441
ATOM     75  HD4 LEU B 441
""", None, """\
total number of:
  models:     1
  chains:     1
  alt. conf.: 0
  residues:   1
  atoms:      8 (8 with duplicate labels)
number of atom element+charge types: 1
histogram of atom element+charge frequency:
  "    " 8
residue name classes:
  "common_amino_acid" 1
number of chain ids: 1
histogram of chain id frequency:
  "B" 1
number of alt. conf. ids: 0
number of residue names: 1
histogram of residue name frequency:
  "LEU" 1
number of groups of duplicate atom labels: 4
  total number of affected atoms:          8
  group "ATOM     68  HD1 LEU B 441 "
        "ATOM     72  HD1 LEU B 441 "
  group "ATOM     69  HD2 LEU B 441 "
        "ATOM     73  HD2 LEU B 441 "
  group "ATOM     70  HD3 LEU B 441 "
        "ATOM     74  HD3 LEU B 441 "
  ... 1 remaining group not shown
""")
  #
  check("""\
HEADER    HYDROLASE                               19-JUL-05   2BWX
ATOM   2038  N   CYS A 249      68.746  44.381  71.143  0.70 21.04           N
ATOM   2039  CA  CYS A 249      68.957  43.022  71.606  0.70 21.28           C
ATOM   2040  C   CYS A 249      70.359  42.507  71.362  0.70 19.80           C
ATOM   2041  O   CYS A 249      71.055  42.917  70.439  0.70 19.80           O
ATOM   2042  CB ACYS A 249      67.945  42.064  70.987  0.40 24.99           C
ATOM   2044  SG ACYS A 249      66.261  42.472  71.389  0.40 27.94           S
ATOM   2043  CB BCYS A 249      67.928  42.101  70.948  0.30 23.34           C
ATOM   2045  SG BCYS A 249      67.977  40.404  71.507  0.30 26.46           S
HETATM 2046  N  CCSO A 249      68.746  44.381  71.143  0.30 21.04           N
HETATM 2047  CA CCSO A 249      68.957  43.022  71.606  0.30 21.28           C
HETATM 2048  CB CCSO A 249      67.945  42.064  70.987  0.30 24.99           C
HETATM 2049  SG CCSO A 249      66.261  42.472  71.389  0.30 27.94           S
HETATM 2050  C  CCSO A 249      70.359  42.507  71.362  0.30 19.80           C
HETATM 2051  O  CCSO A 249      71.055  42.917  70.439  0.30 19.80           O
HETATM 2052  OD CCSO A 249      66.275  42.201  72.870  0.30 23.67           O
""", """\
model id="   0" #chains=1
  chain id="A" #residue_groups=2
    resid=" 249 " #atom_groups=3
      altloc="" resname="CYS" #atoms=4
      altloc="A" resname="CYS" #atoms=2
      altloc="B" resname="CYS" #atoms=2
    resid=" 249 " #atom_groups=1  ### Info: same as previous resid ###
      altloc="C" resname="CSO" #atoms=7
""", """\
total number of:
  models:      1
  chains:      1
  alt. conf.:  3
  residues:    2
  atoms:      15
number of atom element+charge types: 4
histogram of atom element+charge frequency:
  " C  " 7
  " O  " 3
  " S  " 3
  " N  " 2
residue name classes:
  "common_amino_acid" 1
  "other"             1
number of chain ids: 1
histogram of chain id frequency:
  "A" 1
number of alt. conf. ids: 3
histogram of alt. conf. id frequency:
  "A" 1
  "B" 1
  "C" 1
residue alt. conf. situations:
  pure main conf.:     0
  pure alt. conf.:     1
  proper alt. conf.:   1
  improper alt. conf.: 0
chains with mix of proper and improper alt. conf.: 0
number of residue names: 2
histogram of residue name frequency:
  "CSO" 1    other
  "CYS" 1
number of consecutive residue groups with same resid: 1
  residue group:
    "ATOM   2038  N   CYS A 249 "
    ... 6 atoms not shown
    "ATOM   2045  SG BCYS A 249 "
  next residue group:
    "HETATM 2046  N  CCSO A 249 "
    ... 5 atoms not shown
    "HETATM 2052  OD CCSO A 249 "
""", level_id="atom_group")
  #
  check("""\
HEADER    OXIDOREDUCTASE                          17-SEP-97   1OHJ
HETATM 1552  C3  COP   188      11.436  28.065  13.009  1.00  8.51           C
HETATM 1553  C1  COP   188      13.269  26.907  13.759  1.00  8.86           C
HETATM 1582  O24 COP   188      13.931  34.344  22.009  1.00 20.08           O
HETATM 1583  O25 COP   188      13.443  32.717  20.451  1.00 20.18           O
HETATM 1608  O   HOH   188      20.354  30.097  11.632  1.00 21.33           O
HETATM 1569  C28ACOP   188      14.231  36.006  18.087  0.50 25.20           C
HETATM 1571  C29ACOP   188      13.126  36.948  17.945  0.50 26.88           C
HETATM 1604  O40ACOP   188      15.720  40.117  14.909  0.50 31.54           O
HETATM 1606  O41ACOP   188      15.816  42.243  14.385  0.50 31.73           O
HETATM 1570  C28BCOP   188      14.190  36.055  18.102  0.50 24.97           C
HETATM 1572  C29BCOP   188      13.133  37.048  18.009  0.50 26.45           C
HETATM 1605  O40BCOP   188      10.794  41.093  18.747  0.50 30.51           O
HETATM 1607  O41BCOP   188      12.838  40.007  19.337  0.50 30.37           O
""", """\
model id="   0" #chains=1
  chain id=" " #residue_groups=3
    resid=" 188 " #atom_groups=1
      altloc="" resname="COP" #atoms=4
    resid=" 188 " #atom_groups=1  ### Info: same as previous resid ###
      altloc="" resname="HOH" #atoms=1
    resid=" 188 " #atom_groups=2  ### Info: same as previous resid ###
      altloc="A" resname="COP" #atoms=4
      altloc="B" resname="COP" #atoms=4
""", """\
total number of:
  models:      1
  chains:      1
  alt. conf.:  2
  residues:    3
  atoms:      13
number of atom element+charge types: 2
histogram of atom element+charge frequency:
  " O  " 7
  " C  " 6
residue name classes:
  "other"        2
  "common_water" 1
number of chain ids: 1
histogram of chain id frequency:
  " " 1
number of alt. conf. ids: 2
histogram of alt. conf. id frequency:
  "A" 1
  "B" 1
residue alt. conf. situations:
  pure main conf.:     2
  pure alt. conf.:     1
  proper alt. conf.:   0
  improper alt. conf.: 0
chains with mix of proper and improper alt. conf.: 0
number of residue names: 2
histogram of residue name frequency:
  "COP" 2    other
  "HOH" 1    common water
number of consecutive residue groups with same resid: 2
  residue group:
    "HETATM 1552  C3  COP   188 "
    ... 2 atoms not shown
    "HETATM 1583  O25 COP   188 "
  next residue group:
    "HETATM 1608  O   HOH   188 "
  next residue group:
    "HETATM 1569  C28ACOP   188 "
    ... 6 atoms not shown
    "HETATM 1607  O41BCOP   188 "
""", level_id="atom_group")
  #
  check("""\
ATOM      1  N   R01     1I
ATOM      2  N   R02     1I
ATOM      3  N   R03     1I
ATOM      4  N   R04     1I
ATOM      5  N   R05     1I
""", None, """\
total number of:
  models:     1
  chains:     1
  alt. conf.: 0
  residues:   5
  atoms:      5
number of atom element+charge types: 1
histogram of atom element+charge frequency:
  "    " 5
residue name classes:
  "other" 5
number of chain ids: 1
histogram of chain id frequency:
  " " 1
number of alt. conf. ids: 0
number of residue names: 5
histogram of residue name frequency:
  "R01" 1    other
  "R02" 1    other
  "R03" 1    other
  "R04" 1    other
  "R05" 1    other
number of consecutive residue groups with same resid: 4
  residue group:
    "ATOM      1  N   R01     1I"
  next residue group:
    "ATOM      2  N   R02     1I"
  next residue group:
    "ATOM      3  N   R03     1I"
  next residue group:
    "ATOM      4  N   R04     1I"
  -------------------------------
  ... 1 remaining instance not shown
""")

def exercise_convenience_generators():
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
MODEL        1
ATOM      1  N  AR11 A   1
ATOM      2  O  AR11 A   1
ATOM      3  N  BR21 A   1
ATOM      4  O  BR21 A   1
ATOM      5  N  AR12 A   2
ATOM      6  O  AR12 A   2
ATOM      7  N  BR22 A   2
ATOM      8  O  BR22 A   2
TER
ATOM      9  N  AR11 B   1
ATOM     10  O  AR11 B   1
ATOM     11  N  BR21 B   1
ATOM     12  O  BR21 B   1
ATOM     13  N  AR12 B   2
ATOM     14  O  AR12 B   2
ATOM     15  N  BR22 B   2
ATOM     16  O  BR22 B   2
TER
ENDMDL
MODEL        2
ATOM      1  N  AR11 A   1
ATOM      2  O  AR11 A   1
ATOM      3  N  BR21 A   1
ATOM      4  O  BR21 A   1
ATOM      5  N  AR12 A   2
ATOM      6  O  AR12 A   2
ATOM      7  N  BR22 A   2
ATOM      8  O  BR22 A   2
TER
ATOM      9  N  AR11 B   1
ATOM     10  O  AR11 B   1
ATOM     11  N  BR21 B   1
ATOM     12  O  BR21 B   1
ATOM     13  N  AR12 B   2
ATOM     14  O  AR12 B   2
ATOM     15  N  BR22 B   2
ATOM     16  O  BR22 B   2
TER
ENDMDL
"""))
  obj = pdb_inp.construct_hierarchy_v2(residue_group_post_processing=False)
  assert [model.id for model in obj.models()] == ["   1", "   2"]
  assert [chain.id for chain in obj.chains()] == ["A", "B"] * 2
  assert [rg.resid() for rg in obj.residue_groups()] == ["   1 ", "   2 "] * 4
  assert [ag.confid() for ag in obj.atom_groups()] \
      == ["AR11", "BR21", "AR12", "BR22"] * 4
  assert obj.atoms_size() == 32
  assert obj.atoms().size() == 32
  assert [atom.name for atom in obj.atoms()] == [" N  ", " O  "] * 16
  obj = obj.models()[0]
  assert [chain.id for chain in obj.chains()] == ["A", "B"]
  assert [rg.resid() for rg in obj.residue_groups()] == ["   1 ", "   2 "] * 2
  assert [ag.confid() for ag in obj.atom_groups()] \
      == ["AR11", "BR21", "AR12", "BR22"] * 2
  assert obj.atoms_size() == 16
  assert obj.atoms().size() == 16
  assert [atom.name for atom in obj.atoms()] == [" N  ", " O  "] * 8
  obj = obj.chains()[0]
  assert [rg.resid() for rg in obj.residue_groups()] == ["   1 ", "   2 "]
  assert [ag.confid() for ag in obj.atom_groups()] \
      == ["AR11", "BR21", "AR12", "BR22"]
  assert obj.atoms_size() == 8
  assert obj.atoms().size() == 8
  assert [atom.name for atom in obj.atoms()] == [" N  ", " O  "] * 4
  obj = obj.residue_groups()[0]
  assert [ag.confid() for ag in obj.atom_groups()] \
      == ["AR11", "BR21"]
  assert obj.atoms_size() == 4
  assert obj.atoms().size() == 4
  assert [atom.name for atom in obj.atoms()] == [" N  ", " O  "] * 2
  obj = obj.atom_groups()[0]
  assert obj.atoms_size() == 2
  assert obj.atoms().size() == 2
  assert [atom.name for atom in obj.atoms()] == [" N  ", " O  "]

def exercise_only():
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
MODEL        1
ATOM      2  N  ARES C   3I
ENDMDL
"""))
  obj = pdb_inp.construct_hierarchy_v2(residue_group_post_processing=False)
  assert obj.only_model().id == "   1"
  assert obj.only_chain().id == "C"
  assert obj.only_residue_group().resid() == "   3I"
  assert obj.only_atom_group().altloc == "A"
  assert obj.only_atom().name == " N  "
  obj = obj.only_model()
  assert obj.only_chain().id == "C"
  assert obj.only_residue_group().resid() == "   3I"
  assert obj.only_atom_group().resname == "RES"
  assert obj.only_atom().name == " N  "
  obj = obj.only_chain()
  assert obj.only_residue_group().resid() == "   3I"
  assert obj.only_atom_group().altloc == "A"
  assert obj.only_atom().name == " N  "
  obj = obj.only_residue_group()
  assert obj.only_atom_group().resname == "RES"
  assert obj.only_atom().name == " N  "
  obj = obj.only_atom_group()
  assert obj.only_atom().name == " N  "

exercise_merge_pdb_inp = pdb.input(
  source_info=None, lines=flex.split_lines("""\
ATOM   1716  N  ALEU   190      28.628   4.549  20.230  0.70  3.78           N
ATOM   1717  CA ALEU   190      27.606   5.007  19.274  0.70  3.71           C
ATOM   1718  CB ALEU   190      26.715   3.852  18.800  0.70  4.15           C
ATOM   1719  CG ALEU   190      25.758   4.277  17.672  0.70  4.34           C
ATOM   1829  N  BLEU   190      28.428   4.746  20.343  0.30  5.13           N
ATOM   1830  CA BLEU   190      27.378   5.229  19.418  0.30  4.89           C
ATOM   1831  CB BLEU   190      26.539   4.062  18.892  0.30  4.88           C
ATOM   1832  CG BLEU   190      25.427   4.359  17.878  0.30  5.95           C
ATOM   1724  N  ATHR   191      27.350   7.274  20.124  0.70  3.35           N
ATOM   1725  CA ATHR   191      26.814   8.243  21.048  0.70  3.27           C
ATOM   1726  CB ATHR   191      27.925   9.229  21.468  0.70  3.73           C
ATOM   1727  OG1ATHR   191      28.519   9.718  20.259  0.70  5.22           O
ATOM   1728  CG2ATHR   191      28.924   8.567  22.345  0.70  4.21           C
ATOM   1729  C  ATHR   191      25.587   8.983  20.559  0.70  3.53           C
ATOM   1730  O  ATHR   191      24.872   9.566  21.383  0.70  3.93           O
ATOM   1833  CD1BLEU   190      26.014   4.711  16.521  0.30  6.21           C
ATOM   1835  C  BLEU   190      26.506   6.219  20.135  0.30  4.99           C
ATOM   1836  O  BLEU   190      25.418   5.939  20.669  0.30  5.91           O
ATOM   1721  CD2ALEU   190      24.674   3.225  17.536  0.70  5.31           C
ATOM   1722  C  ALEU   190      26.781   6.055  20.023  0.70  3.36           C
ATOM   1723  O  ALEU   190      25.693   5.796  20.563  0.70  3.68           O
ATOM   8722  C  DLEU   190      26.781   6.055  20.023  0.70  3.36           C
ATOM   8723  O  DLEU   190      25.693   5.796  20.563  0.70  3.68           O
ATOM   9722  C  CLEU   190      26.781   6.055  20.023  0.70  3.36           C
ATOM   9723  O  CLEU   190      25.693   5.796  20.563  0.70  3.68           O
"""))

def exercise_merge_atom_groups():
  lines = []
  root = exercise_merge_pdb_inp.construct_hierarchy_v2(
    residue_group_post_processing=False)
  chain = root.models()[0].chains()[0]
  residue_groups = chain.residue_groups()
  assert len(residue_groups) == 3
  for i_ag in [0,1]:
    primary_atom_group = residue_groups[0].atom_groups()[i_ag]
    assert (primary_atom_group.altloc, primary_atom_group.resname) \
        == ("AB"[i_ag], "LEU")
    secondary_atom_group = residue_groups[2].atom_groups()[1-i_ag]
    try:
      residue_groups[0].merge_atom_groups(
        primary=secondary_atom_group,
        secondary=primary_atom_group)
    except RuntimeError, e:
      assert not show_diff(str(e), """\
"primary" atom_group has a different or no parent\
 (this residue_group must be the parent).""")
    else: raise Exception_expected
    try:
      residue_groups[0].merge_atom_groups(
        primary=primary_atom_group,
        secondary=primary_atom_group)
    except RuntimeError, e:
      assert not show_diff(str(e), """\
"primary" and "secondary" atom_groups are identical.""")
    else: raise Exception_expected
    try:
      residue_groups[0].merge_atom_groups(
        primary=primary_atom_group,
        secondary=residue_groups[2].atom_groups()[i_ag])
    except RuntimeError, e:
      assert str(e).find("secondary.data->altloc == primary.data->altloc") > 0
    else: raise Exception_expected
    assert primary_atom_group.atoms_size() == 4
    assert secondary_atom_group.atoms_size() == 3
    residue_groups[0].merge_atom_groups(
      primary=primary_atom_group,
      secondary=secondary_atom_group)
    assert primary_atom_group.atoms_size() == 7
    assert secondary_atom_group.atoms_size() == 0
    sio = StringIO()
    for atom in primary_atom_group.atoms():
      print >> sio, atom.format_atom_record()
    assert not show_diff(sio.getvalue(), ["""\
ATOM   1716  N  ALEU   190      28.628   4.549  20.230  0.70  3.78           N
ATOM   1717  CA ALEU   190      27.606   5.007  19.274  0.70  3.71           C
ATOM   1718  CB ALEU   190      26.715   3.852  18.800  0.70  4.15           C
ATOM   1719  CG ALEU   190      25.758   4.277  17.672  0.70  4.34           C
ATOM   1721  CD2ALEU   190      24.674   3.225  17.536  0.70  5.31           C
ATOM   1722  C  ALEU   190      26.781   6.055  20.023  0.70  3.36           C
ATOM   1723  O  ALEU   190      25.693   5.796  20.563  0.70  3.68           O
""", """\
ATOM   1829  N  BLEU   190      28.428   4.746  20.343  0.30  5.13           N
ATOM   1830  CA BLEU   190      27.378   5.229  19.418  0.30  4.89           C
ATOM   1831  CB BLEU   190      26.539   4.062  18.892  0.30  4.88           C
ATOM   1832  CG BLEU   190      25.427   4.359  17.878  0.30  5.95           C
ATOM   1833  CD1BLEU   190      26.014   4.711  16.521  0.30  6.21           C
ATOM   1835  C  BLEU   190      26.506   6.219  20.135  0.30  4.99           C
ATOM   1836  O  BLEU   190      25.418   5.939  20.669  0.30  5.91           O
"""][i_ag])

def exercise_merge_residue_groups():
  root = exercise_merge_pdb_inp.construct_hierarchy_v2(
    residue_group_post_processing=False)
  chain = root.models()[0].chains()[0]
  residue_groups = chain.residue_groups()
  assert len(residue_groups) == 3
  try:
    chain.merge_residue_groups(
      primary=residue_groups[0],
      secondary=residue_groups[1])
  except RuntimeError, e:
    assert str(e).find("secondary.data->resseq == primary.data->resseq") > 0
  else: raise Exception_expected
  assert residue_groups[0].atom_groups_size() == 2
  assert residue_groups[2].atom_groups_size() == 4
  assert residue_groups[2].parent().memory_id() == chain.memory_id()
  assert chain.residue_groups_size() == 3
  chain.merge_residue_groups(
    primary=residue_groups[0],
    secondary=residue_groups[2])
  assert residue_groups[0].atom_groups_size() == 4
  assert residue_groups[2].atom_groups_size() == 0
  assert residue_groups[2].parent() is None
  assert chain.residue_groups_size() == 2
  sio = StringIO()
  for atom_group in residue_groups[0].atom_groups():
    for atom in atom_group.atoms():
      print >> sio, atom.format_atom_record()
  assert not show_diff(sio.getvalue(), """\
ATOM   1716  N  ALEU   190      28.628   4.549  20.230  0.70  3.78           N
ATOM   1717  CA ALEU   190      27.606   5.007  19.274  0.70  3.71           C
ATOM   1718  CB ALEU   190      26.715   3.852  18.800  0.70  4.15           C
ATOM   1719  CG ALEU   190      25.758   4.277  17.672  0.70  4.34           C
ATOM   1721  CD2ALEU   190      24.674   3.225  17.536  0.70  5.31           C
ATOM   1722  C  ALEU   190      26.781   6.055  20.023  0.70  3.36           C
ATOM   1723  O  ALEU   190      25.693   5.796  20.563  0.70  3.68           O
ATOM   1829  N  BLEU   190      28.428   4.746  20.343  0.30  5.13           N
ATOM   1830  CA BLEU   190      27.378   5.229  19.418  0.30  4.89           C
ATOM   1831  CB BLEU   190      26.539   4.062  18.892  0.30  4.88           C
ATOM   1832  CG BLEU   190      25.427   4.359  17.878  0.30  5.95           C
ATOM   1833  CD1BLEU   190      26.014   4.711  16.521  0.30  6.21           C
ATOM   1835  C  BLEU   190      26.506   6.219  20.135  0.30  4.99           C
ATOM   1836  O  BLEU   190      25.418   5.939  20.669  0.30  5.91           O
ATOM   8722  C  DLEU   190      26.781   6.055  20.023  0.70  3.36           C
ATOM   8723  O  DLEU   190      25.693   5.796  20.563  0.70  3.68           O
ATOM   9722  C  CLEU   190      26.781   6.055  20.023  0.70  3.36           C
ATOM   9723  O  CLEU   190      25.693   5.796  20.563  0.70  3.68           O
""")
  for i_rg,j_rg,s in [(2,2,"primary"),(0,2,"secondary")]:
    try:
      chain.merge_residue_groups(
        primary=residue_groups[i_rg],
        secondary=residue_groups[j_rg])
    except RuntimeError, e:
      assert not show_diff(str(e), """\
"%s" residue_group has a different or no parent\
 (this chain must be the parent).""" % s)
    else: raise Exception_expected

def exercise_chain_merge_residue_groups(n_trials=30):
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
HEADER    HYDROLASE                               22-NOV-07   2VHL
HETATM 6362  O   HOH B2048      47.616  10.724 150.212  1.00 46.48           O
HETATM 6363  O  AHOH B2049      46.408  16.672 146.066  0.50 12.81           O
HETATM 6364  O   HOH B2050      29.343  12.806 185.898  1.00 35.57           O
HETATM 6365  O  BHOH B2049      43.786  12.615 147.734  0.50 28.43           O
HETATM 6366  O   HOH B2052      35.068  19.167 155.349  1.00 15.97           O
"""))
  for rgpp in [False, True]:
    chain = pdb_inp.construct_hierarchy_v2(
      residue_group_post_processing=rgpp).only_chain()
    if (not rgpp):
      assert chain.residue_groups_size() == 5
      indices = chain.merge_disconnected_residue_groups_with_pure_altloc()
      assert list(indices) == [1]
    assert chain.residue_groups_size() == 4
    indices = chain.merge_disconnected_residue_groups_with_pure_altloc()
    assert indices.size() == 0
    del chain
  lines = flex.split_lines("""\
HETATM 6363  O  AHOH B2049
HETATM 6364  O  ZHOH B2050
HETATM 6365  O  BHOH B2049
HETATM 6366  O  YHOH B2052
HETATM 9365  O  CHOH B2049
HETATM 9367  O  XHOH B2052
""")
  pdb_inp = pdb.input(source_info=None, lines=lines)
  chain = pdb_inp.construct_hierarchy_v2(
    residue_group_post_processing=False).only_chain()
  assert chain.residue_groups_size() == 6
  indices = chain.merge_disconnected_residue_groups_with_pure_altloc()
  assert list(indices) == [0, 2]
  assert chain.residue_groups_size() == 3
  indices = chain.merge_disconnected_residue_groups_with_pure_altloc()
  assert indices.size() == 0
  for i_trial in xrange(n_trials):
    pdb_inp = pdb.input(
      source_info=None,
      lines=lines.select(flex.random_permutation(size=lines.size())))
    chain = pdb_inp.construct_hierarchy_v2(
      residue_group_post_processing=False).only_chain()
    indices = chain.merge_disconnected_residue_groups_with_pure_altloc()
    assert indices.size() <= 2
    indices = chain.merge_disconnected_residue_groups_with_pure_altloc()
    assert indices.size() == 0
    del chain
    chain = pdb_inp.construct_hierarchy_v2().only_chain()
    indices = chain.merge_disconnected_residue_groups_with_pure_altloc()
    assert indices.size() == 0
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
HEADER    SERINE PROTEASE                         10-NOV-95   1RTF
HETATM 2397  P   PO4     1      -7.520  25.376  38.369  1.00 39.37           P
HETATM 2398  O1  PO4     1      -6.610  24.262  38.967  1.00 40.00           O
HETATM 2399  O2  PO4     1      -6.901  25.919  37.049  1.00 41.07           O
HETATM 2400  O3  PO4     1      -8.894  24.741  38.097  1.00 45.09           O
HETATM 2401  O4  PO4     1      -7.722  26.556  39.350  1.00 42.48           O
HETATM 2402  C1  BEN     1      -6.921  31.206  33.893  1.00 23.35           C
HETATM 2403  C2  BEN     1      -8.189  30.836  34.344  1.00 23.15           C
HETATM 2404  C3  BEN     1      -8.335  29.863  35.342  1.00 20.74           C
HETATM 2405  C4  BEN     1      -7.206  29.254  35.893  1.00 19.45           C
HETATM 2406  C5  BEN     1      -5.932  29.618  35.445  1.00 20.83           C
HETATM 2407  C6  BEN     1      -5.794  30.589  34.450  1.00 20.99           C
HETATM 2408  C   BEN     1      -6.767  32.249  32.859  1.00 24.30           C
HETATM 2409  N1  BEN     1      -5.570  32.641  32.497  1.00 24.56           N
HETATM 2410  N2  BEN     1      -7.824  32.785  32.299  1.00 24.58           N
HETATM 2415  O   HOH     1       4.020  20.521  19.336  1.00 38.74           O
HETATM 2418  O   WAT     2      14.154  16.852  21.753  1.00 49.41           O
"""))
  chain = pdb_inp.construct_hierarchy_v2(
    residue_group_post_processing=False).only_chain()
  assert chain.residue_groups_size() == 4
  assert [residue_group.resid() for residue_group in chain.residue_groups()] \
      == ["   1 ", "   1 ", "   1 ", "   2 "]
  for residue_group in chain.residue_groups():
    assert residue_group.atom_groups_size() == 1
    assert residue_group.atom_groups()[0].parent().memory_id() \
        == residue_group.memory_id()
  assert [residue_group.atom_groups()[0].resname
           for residue_group in chain.residue_groups()] \
      == ["PO4", "BEN", "HOH", "WAT"]
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
HETATM 2418  O   WAT     2
HETATM 2397  P   PO4     1
HETATM 2398  O1  PO4     1
HETATM 2402  C1  BEN     1
HETATM 2403  C2  BEN     1
HETATM 2404  C3  BEN     1
HETATM 2415  O   HOH     1
HETATM 9418  O   WAT     2
HETATM 9397  P   PO4     1
HETATM 9398  O1  PO4     1
HETATM 9402  C1  BEN     1
HETATM 9403  C2  BEN     1
HETATM 9404  C3  BEN     1
HETATM 9415  O   HOH     1
"""))
  chain = pdb_inp.construct_hierarchy_v2(
    residue_group_post_processing=False).only_chain()
  assert chain.residue_groups_size() == 8
  for residue_group in chain.residue_groups():
    assert residue_group.atom_groups_size() == 1
    assert residue_group.atom_groups()[0].parent().memory_id() \
        == residue_group.memory_id()
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
HETATM 6362  O  CHOH B   1
HETATM 6363  O  AHOH B   1
HETATM 6364  O   HOH B   2
HETATM 6365  O   HOH B   1
"""))
  chain = pdb_inp.construct_hierarchy_v2(
    residue_group_post_processing=False).only_chain()
  assert chain.residue_groups_size() == 3
  assert chain.residue_groups()[2].only_atom_group().altloc == " "
  for rg in chain.residue_groups():
    rg.edit_blank_altloc()
  assert chain.residue_groups()[2].only_atom_group().altloc == ""
  indices = chain.merge_disconnected_residue_groups_with_pure_altloc()
  assert indices.size() == 0
  assert chain.residue_groups_size() == 3

def exercise_edit_blank_altloc(n_trials=30):
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM         N1
ATOM         N2
"""))
  for rgpp in [False, True]:
    residue_group = pdb_inp.construct_hierarchy_v2(
      residue_group_post_processing=rgpp).only_residue_group()
    for i_proc in [0,1]:
      assert residue_group.edit_blank_altloc() == (1,0)
    del residue_group
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM         N1 A
ATOM         N2 B
"""))
  for rgpp in [False, True]:
    residue_group = pdb_inp.construct_hierarchy_v2(
      residue_group_post_processing=rgpp).only_residue_group()
    rgc = residue_group.detached_copy()
    assert rgc.move_blank_altloc_atom_groups_to_front() == 0
    for i_proc in [0,1]:
      assert residue_group.edit_blank_altloc() == (0,0)
    del residue_group
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM         N1
ATOM         N2 B
"""))
  for rgpp in [False, True]:
    residue_group = pdb_inp.construct_hierarchy_v2(
      residue_group_post_processing=rgpp).only_residue_group()
    if (not rgpp):
      atom_groups = residue_group.atom_groups()
      assert len(atom_groups) == 2
      assert atom_groups[0].altloc == " "
      assert atom_groups[1].altloc == "B"
    for i_proc in [0,1]:
      if (not rgpp or i_proc != 0):
        assert residue_group.edit_blank_altloc() == (1,0)
      atom_groups = residue_group.atom_groups()
      assert len(atom_groups) == 2
      assert atom_groups[0].altloc == ""
      assert atom_groups[1].altloc == "B"
    del atom_groups
    del residue_group
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM         N1
ATOM         N1 B
"""))
  residue_group = pdb_inp.construct_hierarchy_v2(
    residue_group_post_processing=False).only_residue_group()
  atom_groups = residue_group.atom_groups()
  assert len(atom_groups) == 2
  assert atom_groups[0].altloc == " "
  assert atom_groups[1].altloc == "B"
  rgc = residue_group.detached_copy()
  assert rgc.move_blank_altloc_atom_groups_to_front() == 1
  for i_proc in [0,1]:
    assert residue_group.edit_blank_altloc() == (0,1)
    atom_groups = residue_group.atom_groups()
    assert len(atom_groups) == 2
    assert atom_groups[0].altloc == " "
    assert atom_groups[1].altloc == "B"
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM         N1 B
ATOM         N1
"""))
  for edit_chain in [False, True]:
    chain = pdb_inp.construct_hierarchy_v2(
      residue_group_post_processing=False).only_chain()
    residue_group = chain.only_residue_group()
    atom_groups = residue_group.atom_groups()
    assert len(atom_groups) == 2
    assert atom_groups[0].altloc == "B"
    assert atom_groups[1].altloc == " "
    rgc = residue_group.detached_copy()
    assert rgc.move_blank_altloc_atom_groups_to_front() == 1
    for i_proc in [0,1]:
      if (not edit_chain):
        assert residue_group.edit_blank_altloc() == (0,1)
      else:
        for rg in chain.residue_groups():
          rg.edit_blank_altloc()
      atom_groups = residue_group.atom_groups()
      assert len(atom_groups) == 2
      assert atom_groups[0].altloc == " "
      assert atom_groups[1].altloc == "B"
    del atom_groups
    del residue_group
    del chain
  #
  lines = flex.split_lines("""\
ATOM         N1 B
ATOM         N1
ATOM         N2
ATOM         N3 B
ATOM         N3
""")
  for i_trial in xrange(n_trials):
    pdb_inp = pdb.input(source_info=None, lines=lines)
    residue_group = pdb_inp.construct_hierarchy_v2(
      residue_group_post_processing=False).only_residue_group()
    atom_groups = residue_group.atom_groups()
    assert len(atom_groups) == 2
    if (i_trial == 0):
      assert atom_groups[0].altloc == "B"
      assert atom_groups[1].altloc == " "
    else:
      assert sorted([atom_group.altloc for atom_group in atom_groups]) \
          == [" ", "B"]
    for i_proc in [0,1]:
      assert residue_group.edit_blank_altloc() == (1,1)
      atom_groups = residue_group.atom_groups()
      assert len(atom_groups) == 3
      assert atom_groups[0].altloc == ""
      assert atom_groups[1].altloc == " "
      assert atom_groups[2].altloc == "B"
      lines = lines.select(flex.random_permutation(size=lines.size()))

def exercise_find_pure_altloc_ranges():
  c = pdb.hierarchy_v2.chain()
  assert c.find_pure_altloc_ranges().size() == 0
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM            A        1
"""))
  c = pdb_inp.construct_hierarchy_v2().only_chain()
  assert c.find_pure_altloc_ranges().size() == 0
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM            A        1
ATOM            B        1
"""))
  c = pdb_inp.construct_hierarchy_v2().only_chain()
  assert c.find_pure_altloc_ranges().size() == 0
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM            A        1
ATOM            B        2
"""))
  c = pdb_inp.construct_hierarchy_v2().only_chain()
  assert list(c.find_pure_altloc_ranges()) == [(0,2)]
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM            A        1
BREAK
ATOM            B        2
"""))
  c = pdb_inp.construct_hierarchy_v2().only_chain()
  assert c.find_pure_altloc_ranges().size() == 0
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM            A        1
ATOM            B        1
ATOM                     2
"""))
  c = pdb_inp.construct_hierarchy_v2().only_chain()
  assert c.find_pure_altloc_ranges().size() == 0
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM            A        1
ATOM            B        2
ATOM            C        3
ATOM                     4
ATOM            E        5
ATOM            F        6
ATOM            G        6
ATOM            H        6
ATOM                     7
ATOM                     8
ATOM            I        9
ATOM            J       10
BREAK
ATOM            L       11
ATOM            M       12
ATOM         N1 N       13
ATOM         N2         13
ATOM            O       14
ATOM                    14
ATOM            P       15
ATOM                    15
"""))
  c = pdb_inp.construct_hierarchy_v2().only_chain()
  assert list(c.find_pure_altloc_ranges()) \
      == [(0,3),(4,6),(8,10),(10,12),(13,15)]
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
HEADER    CELL CYCLE                              13-SEP-05   2B05
HETATM10989  O   HOH    29     -66.337 -28.299 -26.997  1.00 40.05           O
HETATM10990  O  AHOH    32     -57.432 -22.290 -45.876  0.50  2.46           O
HETATM10991  O  BHOH    32     -59.435 -22.422 -45.055  0.50 17.09           O
HETATM10992  O   HOH    36     -56.803 -18.433 -29.790  1.00 43.00           O
HETATM10993  O   HOH    37     -51.860 -26.755 -35.092  1.00 35.90           O
HETATM10994  O  AHOH    39     -68.867 -23.643 -49.077  0.50 12.37           O
HETATM10995  O  BHOH    39     -69.097 -21.979 -50.740  0.50 21.64           O
HETATM10996  O   HOH    40     -65.221 -13.774 -33.183  1.00 36.14           O
"""))
  c = pdb_inp.construct_hierarchy_v2().only_chain()
  assert c.find_pure_altloc_ranges().size() == 0
  #
  caa = "common_amino_acid"
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM            AALA     1
ATOM            BGLY     1
ATOM            ATYR     2
ATOM            BTHR     2
ATOM            AHOH     3
ATOM            BHOH     3
"""))
  c = pdb_inp.construct_hierarchy_v2().only_chain()
  assert list(c.find_pure_altloc_ranges()) == [(0,3)]
  assert list(c.find_pure_altloc_ranges(common_residue_name_class_only=caa)) \
    == [(0,2)]
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM            AHOH     3
ATOM            BHOH     3
ATOM            AALA     1
ATOM            BGLY     1
ATOM            ATYR     2
ATOM            BTHR     2
"""))
  c = pdb_inp.construct_hierarchy_v2().only_chain()
  assert list(c.find_pure_altloc_ranges()) == [(0,3)]
  assert list(c.find_pure_altloc_ranges(common_residue_name_class_only=caa)) \
    == [(1,3)]
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM            AALA     1
ATOM            BGLY     1
ATOM            AHOH     3
ATOM            BHOH     3
ATOM            ATYR     2
ATOM            BTHR     2
"""))
  c = pdb_inp.construct_hierarchy_v2().only_chain()
  assert list(c.find_pure_altloc_ranges()) == [(0,3)]
  assert c.find_pure_altloc_ranges(common_residue_name_class_only=caa).size() \
    == 0
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM            AALA     1
ATOM            BGLY     1
ATOM            AHOH     3
ATOM            BHOH     3
ATOM            ATYR     2
ATOM            BTHR     2
ATOM            ASER     4
ATOM            BSER     4
"""))
  c = pdb_inp.construct_hierarchy_v2().only_chain()
  assert list(c.find_pure_altloc_ranges()) == [(0,4)]
  assert list(c.find_pure_altloc_ranges(common_residue_name_class_only=caa)) \
    == [(2,4)]
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM            ASER     4
ATOM            BSER     4
ATOM            AALA     1
ATOM            BGLY     1
ATOM            AHOH     3
ATOM            BHOH     3
ATOM            ATYR     2
ATOM            BTHR     2
"""))
  c = pdb_inp.construct_hierarchy_v2().only_chain()
  assert list(c.find_pure_altloc_ranges()) == [(0,4)]
  assert list(c.find_pure_altloc_ranges(common_residue_name_class_only=caa)) \
    == [(0,2)]
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM             MET     1
ATOM            ALEU     2
ATOM            ASER     3
ATOM            BSER     3
ATOM            AALA     4
ATOM            BGLY     4
ATOM            AHOH     5
ATOM            BHOH     5
ATOM            AHOH     6
ATOM            ATYR     7
ATOM            BTHR     7
ATOM            AGLY     8
ATOM            BGLY     8
"""))
  c = pdb_inp.construct_hierarchy_v2().only_chain()
  assert list(c.find_pure_altloc_ranges()) == [(1,8)]
  assert list(c.find_pure_altloc_ranges(common_residue_name_class_only=caa)) \
      == [(1,4), (6,8)]

pdb_1nym_60 = """\
HEADER    HYDROLASE                               12-FEB-03   1NYM
ATOM     60  CA  LYS A  32      10.574   8.177  11.768  1.00 11.49           C
ATOM     63  CB ALYS A  32       9.197   8.686  12.246  0.29 14.71           C
ATOM     64  CB BLYS A  32       9.193   8.732  12.170  0.71 12.23           C
ATOM     74  CA  VAL A  33      11.708   5.617  14.332  1.00 11.42           C
ATOM     77  CB  VAL A  33      11.101   4.227  14.591  1.00 11.47           C
ATOM     82  CA ALYS A  34      14.979   4.895  12.608  0.60 15.67           C
ATOM     83  CA BLYS A  34      14.977   5.207  12.331  0.40 16.38           C
ATOM     88  CB ALYS A  34      15.128   3.896  11.472  0.60 12.11           C
ATOM     89  CB BLYS A  34      15.132   4.867  10.839  0.40 13.86           C
ATOM    100  CA AASP A  35      15.328   8.688  12.044  0.60 16.75           C
ATOM    101  CA BASP A  35      15.474   8.937  12.096  0.40 17.43           C
ATOM    106  CB AASP A  35      14.367   9.683  11.373  0.60 16.80           C
ATOM    107  CB BASP A  35      14.491   9.903  11.431  0.40 18.66           C
ATOM    115  CA  ALA A  36      14.978   9.140  15.828  1.00 12.65           C
ATOM    118  CB  ALA A  36      13.768   8.688  16.639  1.00 13.00           C
ATOM    121  CA AGLU A  37      17.683   6.514  16.549  0.59 12.26           C
ATOM    122  CA BGLU A  37      17.999   6.949  16.048  0.41 12.47           C
ATOM    127  CB AGLU A  37      17.694   5.030  16.164  0.59 11.08           C
ATOM    128  CB BGLU A  37      18.148   5.560  15.440  0.41 12.53           C
ATOM    139  CA AASP A  38      19.923   8.463  14.202  0.59 17.31           C
ATOM    140  CA BASP A  38      19.789   9.284  13.597  0.41 19.32           C
ATOM    145  CB AASP A  38      19.615   8.739  12.727  0.59 24.06           C
ATOM    146  CB BASP A  38      19.279   9.626  12.201  0.41 26.28           C
ATOM    155  CA AGLN A  39      19.069  11.941  15.596  0.62 19.31           C
ATOM    156  CA BGLN A  39      18.919  12.283  15.753  0.38 20.06           C
ATOM    161  CB AGLN A  39      17.681  12.586  15.630  0.62 21.92           C
ATOM    162  CB BGLN A  39      17.560  12.987  15.681  0.38 21.79           C
ATOM    172  CA  LEU A  40      19.526  10.711  19.160  1.00 13.99           C
ATOM    175  CB  LEU A  40      18.478   9.858  19.880  1.00 13.56           C
"""

pdb_2izq_220 = """\
HEADER    ANTIBIOTIC                              26-JUL-06   2IZQ
ATOM    220  N  ATRP A  11      20.498  12.832  34.558  0.50  6.03           N
ATOM    221  CA ATRP A  11      21.094  12.032  35.602  0.50  5.24           C
ATOM    222  C  ATRP A  11      22.601  12.088  35.532  0.50  6.49           C
ATOM    223  O  ATRP A  11      23.174  12.012  34.439  0.50  7.24           O
ATOM    224  CB ATRP A  11      20.690  10.588  35.288  0.50  6.15           C
ATOM    225  CG ATRP A  11      19.252  10.269  35.140  0.50  5.91           C
ATOM    226  CD1ATRP A  11      18.524  10.178  33.986  0.50  7.01           C
ATOM    227  CD2ATRP A  11      18.371   9.973  36.236  0.50  5.97           C
ATOM    228  NE1ATRP A  11      17.252   9.820  34.321  0.50  9.83           N
ATOM    229  CE2ATRP A  11      17.132   9.708  35.665  0.50  7.37           C
ATOM    230  CE3ATRP A  11      18.543   9.924  37.615  0.50  6.38           C
ATOM    231  CZ2ATRP A  11      16.033   9.388  36.460  0.50  8.25           C
ATOM    232  CZ3ATRP A  11      17.448   9.586  38.402  0.50  8.04           C
ATOM    233  CH2ATRP A  11      16.240   9.320  37.784  0.50  8.66           C
ATOM    234  H  ATRP A  11      20.540  12.567  33.741  0.50  7.24           H
ATOM    235  HA ATRP A  11      20.771  12.306  36.485  0.50  6.28           H
ATOM    236  HB2ATRP A  11      21.135  10.330  34.466  0.50  7.38           H
ATOM    237  HB3ATRP A  11      21.045  10.023  35.993  0.50  7.38           H
ATOM    244  N  CPHE A  11      20.226  13.044  34.556  0.15  6.35           N
ATOM    245  CA CPHE A  11      20.950  12.135  35.430  0.15  5.92           C
ATOM    246  C  CPHE A  11      22.448  12.425  35.436  0.15  6.32           C
ATOM    247  O  CPHE A  11      22.961  12.790  34.373  0.15  6.08           O
ATOM    248  CB CPHE A  11      20.768  10.667  34.994  0.15  6.01           C
ATOM    249  CG CPHE A  11      19.330  10.235  34.845  0.15  7.05           C
ATOM    250  CD1CPHE A  11      18.847   9.877  33.587  0.15  8.78           C
ATOM    251  CD2CPHE A  11      18.533  10.174  35.995  0.15  7.70           C
ATOM    252  CE1CPHE A  11      17.551   9.436  33.473  0.15 10.43           C
ATOM    253  CE2CPHE A  11      17.230   9.752  35.854  0.15  9.27           C
ATOM    254  CZ CPHE A  11      16.789   9.396  34.594  0.15 10.98           C
ATOM    255  N  BTYR A  11      20.553  12.751  34.549  0.35  5.21           N
ATOM    256  CA BTYR A  11      21.106  11.838  35.524  0.35  5.51           C
ATOM    257  C  BTYR A  11      22.625  11.920  35.572  0.35  5.42           C
ATOM    258  O  BTYR A  11      23.299  11.781  34.538  0.35  5.30           O
ATOM    259  CB BTYR A  11      20.694  10.354  35.327  0.35  5.65           C
ATOM    260  CG BTYR A  11      19.188  10.175  35.507  0.35  7.68           C
ATOM    261  CD1BTYR A  11      18.548  10.134  34.268  0.35  9.45           C
ATOM    262  HB2CPHE A  11      21.221  10.536  34.146  0.15  7.21           H
ATOM    263  CD2BTYR A  11      18.463  10.012  36.681  0.35  9.08           C
ATOM    264  HB3CPHE A  11      21.198  10.093  35.647  0.15  7.21           H
ATOM    265  CE1BTYR A  11      17.195   9.960  34.223  0.35 10.76           C
ATOM    266  HD1CPHE A  11      19.394   9.937  32.837  0.15 10.53           H
ATOM    267  CE2BTYR A  11      17.100   9.826  36.693  0.35 11.29           C
ATOM    268  HD2CPHE A  11      18.873  10.410  36.828  0.15  9.24           H
ATOM    269  CZ BTYR A  11      16.546   9.812  35.432  0.35 11.90           C
ATOM    270  HE1CPHE A  11      17.206   9.172  32.650  0.15 12.52           H
ATOM    271  OH BTYR A  11      15.178   9.650  35.313  0.35 19.29           O
ATOM    272  HE2CPHE A  11      16.661   9.708  36.588  0.15 11.13           H
ATOM    273  HZ CPHE A  11      15.908   9.110  34.509  0.15 13.18           H
ATOM    274  H  BTYR A  11      20.634  12.539  33.720  0.35  6.25           H
ATOM    275  HA BTYR A  11      20.773  12.116  36.402  0.35  6.61           H
HETATM  283  N   DLE A  12      23.179  12.148  36.720  1.00  7.16           N
HETATM  284  CA  DLE A  12      24.625  12.084  36.893  1.00  8.29           C
HETATM  285  CB ADLE A  12      25.039  10.717  37.621  0.65  9.02           C
HETATM  286  CB BDLE A  12      25.209  10.741  37.032  0.35 12.70           C
HETATM  287  CG ADLE A  12      24.658   9.548  36.780  0.65 12.06           C
HETATM  288  CG BDLE A  12      25.429   9.378  36.572  0.35 15.20           C
HETATM  289  CD1ADLE A  12      25.656   9.433  35.596  0.65 16.84           C
HETATM  290  CD1BDLE A  12      26.192   8.543  37.585  0.35 16.77           C
HETATM  291  CD2ADLE A  12      24.682   8.288  37.613  0.65 15.34           C
HETATM  292  CD2BDLE A  12      24.065   8.724  36.277  0.35 16.96           C
HETATM  293  C   DLE A  12      25.029  13.153  37.899  1.00  8.11           C
HETATM  294  O   DLE A  12      24.343  13.330  38.907  1.00 11.62           O
HETATM  295  H  ADLE A  12      22.682  12.228  37.418  0.50  8.60           H
HETATM  296  HA ADLE A  12      25.095  12.196  36.041  0.50  9.94           H
HETATM  297  HB1ADLE A  12      25.997  10.708  37.775  0.65 10.83           H
HETATM  298  HB1BDLE A  12      26.135  11.000  37.162  0.35 15.23           H
HETATM  299  HB2ADLE A  12      24.595  10.659  38.481  0.65 10.83           H
HETATM  300  HB2BDLE A  12      24.897  10.541  37.929  0.35 15.23           H
HETATM  301  HG ADLE A  12      23.753   9.685  36.429  0.65 14.47           H
HETATM  302  HG BDLE A  12      25.946   9.409  35.740  0.35 18.24           H
"""

def exercise_occupancy_groups_simple():
  def atom_serials(atoms, list_of_occ_groups):
    result = []
    for groups in list_of_occ_groups:
      group_names = []
      for group in groups:
        group_names.append([int(atoms[i].serial) for i in group])
      result.append(group_names)
    return result
  #
  def grouped_serials(
        pdb_inp,
        common_residue_name_class_only="common_amino_acid"):
    hierarchy = pdb_inp.construct_hierarchy_v2()
    atoms = hierarchy.atoms()
    atoms.reset_tmp_for_occupancy_groups_simple()
    chain = hierarchy.only_chain()
    return atom_serials(atoms, chain.occupancy_groups_simple(
      common_residue_name_class_only=common_residue_name_class_only))
  #
  for altloc_o2_a in ["A", " "]:
    pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM      0  S   SO4
ATOM      1  O1  SO4
ATOM      2  O2 %sSO4
ATOM      3  O2 BSO4
ATOM      4  O3  SO4
ATOM      5  O4  SO4
""" % altloc_o2_a))
    assert grouped_serials(pdb_inp) == [[[2], [3]]]
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM      6  S  ASO4     1       1.302   1.419   1.560  0.70 10.00           S
ATOM      7  O1 ASO4     1       1.497   1.295   0.118  0.70 10.00           O
ATOM      8  O2 ASO4     1       1.098   0.095   2.140  0.70 10.00           O
ATOM      9  O3 ASO4     1       2.481   2.037   2.159  0.70 10.00           O
ATOM     10  O4 ASO4     1       0.131   2.251   1.823  0.70 10.00           O
ATOM     11  S  BSO4     1       3.302   3.419   3.560  0.30 10.00           S
ATOM     12  O1 BSO4     1       3.497   3.295   2.118  0.30 10.00           O
ATOM     13  O2 BSO4     1       3.098   2.095   4.140  0.30 10.00           O
ATOM     14  O3 BSO4     1       4.481   4.037   4.159  0.30 10.00           O
ATOM     15  O4 BSO4     1       2.131   4.251   3.823  0.30 10.00           O
"""))
  assert grouped_serials(pdb_inp) == [[[6,7,8,9,10], [11,12,13,14,15]]]
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM     16  O  AHOH     2       5.131   5.251   5.823  0.60 10.00           O
ATOM     17  O  BHOH     2       6.131   6.251   6.823  0.40 10.00           O
"""))
  assert grouped_serials(pdb_inp) == [[[16], [17]]]
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM     18  O   HOH     3       1.132   5.963   7.065  1.00 15.00           O
ATOM     19  H1  HOH     3       1.160   5.211   6.437  1.00 15.00           H
ATOM     20  H2  HOH     3       1.122   5.579   7.967  1.00 15.00           H
"""))
  assert grouped_serials(pdb_inp) == []
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM     21  O   HOH     4       6.131   7.251   5.000  0.50 15.00           O
"""))
  assert grouped_serials(pdb_inp) == [[[21]]]
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM     22  O   HOH     5       0.131   7.251   5.000  0.00 15.00           O
"""))
  assert grouped_serials(pdb_inp) == []
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM     23  S   SO4     6       6.302   6.419   1.560  0.50 10.00           S
ATOM     24  O1 ASO4     6       6.497   6.295   0.118  0.60 10.00           O
ATOM     25  O2 ASO4     6       6.098   5.095   2.140  0.60 10.00           O
ATOM     26  O3 ASO4     6       7.481   7.037   2.159  0.60 10.00           O
ATOM     27  O4 ASO4     6       5.131   7.251   1.823  0.60 10.00           O
ATOM     28  O1 BSO4     6       8.497   8.295   2.118  0.40 10.00           O
ATOM     29  O2 BSO4     6       8.098   7.095   4.140  0.40 10.00           O
ATOM     30  O3 BSO4     6       9.481   9.037   4.159  0.40 10.00           O
ATOM     31  O4 BSO4     6       7.131   9.251   3.823  0.40 10.00           O
"""))
  assert grouped_serials(pdb_inp) == [[[23]], [[24,25,26,27], [28,29,30,31]]]
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM      1  O  AHOH     1                                                   O
ATOM      2  O  BHOH     1                                                   O
ATOM      3  H1 AHOH     1                                                   H
ATOM      4  H1 BHOH     1                                                   H
ATOM      5  H2 AHOH     1                                                   H
ATOM      6  H2 BHOH     1                                                   H
"""))
  assert grouped_serials(pdb_inp) == [[[1],[2]]]
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM      1  O   HOH     1                              0.60                 O
ATOM      2  H1  HOH     1                              0.60                 H
ATOM      3  H2  HOH     1                              0.60                 H
"""))
  assert grouped_serials(pdb_inp) == [[[1]]]
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines(pdb_1nym_60))
  assert grouped_serials(pdb_inp) == [
    [[63],[64]],
    [[82,88,100,106],[83,89,101,107]],
    [[121,127,139,145,155,161],[122,128,140,146,156,162]]]
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM     82  CA AMOD A  34      14.979   4.895  12.608  0.60 15.67           C
ATOM     83  CA BMOD A  34      14.977   5.207  12.331  0.40 16.38           C
ATOM     88  CB AMOD A  34      15.128   3.896  11.472  0.60 12.11           C
ATOM     89  CB BMOD A  34      15.132   4.867  10.839  0.40 13.86           C
ATOM    100  CA AASP A  35      15.328   8.688  12.044  0.60 16.75           C
ATOM    101  CA BASP A  35      15.474   8.937  12.096  0.40 17.43           C
ATOM    106  CB AASP A  35      14.367   9.683  11.373  0.60 16.80           C
ATOM    107  CB BASP A  35      14.491   9.903  11.431  0.40 18.66           C
"""))
  assert grouped_serials(pdb_inp) == [
    [[82,88],[83,89]],
    [[100,106],[101,107]]]
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines(pdb_2izq_220))
  assert grouped_serials(pdb_inp) == [
    [[220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233],
     [244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254],
     [255, 256, 257, 258, 259, 260, 261, 263, 265, 267, 269, 271]],
    [[285, 287, 289, 291], [286, 288, 290, 292]]]
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM    221  CA ATRP A  11      21.094  12.032  35.602  0.50  5.24           C
ATOM    224  CB ATRP A  11      20.690  10.588  35.288  0.50  6.15           C
ATOM    245  CA CPHE A  11      20.950  12.135  35.430  0.15  5.92           C
ATOM    248  CB CPHE A  11      20.768  10.667  34.994  0.15  6.01           C
ATOM    256  CA BTYR A  11      21.106  11.838  35.524  0.35  5.51           C
ATOM    259  CB BTYR A  11      20.694  10.354  35.327  0.35  5.65           C
HETATM  285  CB ADLE A  12      25.039  10.717  37.621  0.65  9.02           C
HETATM  286  CB BDLE A  12      25.209  10.741  37.032  0.35 12.70           C
HETATM  287  CG ADLE A  12      24.658   9.548  36.780  0.65 12.06           C
HETATM  288  CG BDLE A  12      25.429   9.378  36.572  0.35 15.20           C
"""))
  assert grouped_serials(pdb_inp) == [
    [[221, 224], [245, 248], [256, 259]], [[285, 287], [286, 288]]]
  assert grouped_serials(pdb_inp, common_residue_name_class_only=None) == [
    [[221, 224, 285, 287], [245, 248], [256, 259, 286, 288]]]
  #
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines("""\
ATOM      1  O  AHOH A   1                                                   O
ATOM      2  O  BHOH A   1                                                   O
ATOM      3  O  AHOH B   1                                                   O
ATOM      4  O  BHOH B   1                                                   O
"""))
  hierarchy = pdb_inp.construct_hierarchy_v2()
  list_of_groups = hierarchy.occupancy_groups_simple(
    common_residue_name_class_only="common_amino_acid")
  assert list_of_groups == [[[0], [1]], [[2], [3]]]

def conformers_as_str(conformers):
  s = StringIO()
  for cf in conformers:
    print >> s, "conformer:", show_string(cf.altloc)
    for rd in cf.residues():
      print >> s, "  residue:", \
        show_string(rd.resname), \
        show_string(rd.resseq), \
        show_string(rd.icode), \
        int(rd.link_to_previous), \
        int(rd.is_pure_primary)
      for atom in rd.atoms():
        print >> s, "    atom:", show_string(atom.name)
  return s.getvalue()

def exercise_conformers():
  def check(pdb_string, expected):
    pdb_inp = pdb.input(source_info=None, lines=flex.split_lines(pdb_string))
    chain = pdb_inp.construct_hierarchy_v2().only_chain()
    conformers = chain.conformers()
    s = conformers_as_str(conformers)
    if (len(expected) == 0):
      sys.stdout.write(s)
    else:
      assert not show_diff(s, expected)
  #
  check("""\
ATOM         N   RES     1I
""", """\
conformer: ""
  residue: "RES" "   1" "I" 0 1
    atom: " N  "
""")
  #
  check("""\
ATOM         N  ARES     1I
""", """\
conformer: "A"
  residue: "RES" "   1" "I" 0 0
    atom: " N  "
""")
  #
  check("""\
ATOM         N1  RES     1I
ATOM         N2 ARES     1I
""", """\
conformer: "A"
  residue: "RES" "   1" "I" 0 0
    atom: " N1 "
    atom: " N2 "
""")
  #
  for altloc_o2_a in ["A", " "]:
    check("""\
ATOM         S   SO4     1I
ATOM         O1 %sSO4     1I
ATOM         O1 BSO4     1I
""" % altloc_o2_a, """\
conformer: "%s"
  residue: "SO4" "   1" "I" 0 0
    atom: " S  "
    atom: " O1 "
conformer: "B"
  residue: "SO4" "   1" "I" 0 0
    atom: " S  "
    atom: " O1 "
""" % altloc_o2_a)
  #
  check("""\
ATOM         S  ASO4     1
ATOM         O1 ASO4     1
ATOM         O2 ASO4     1
ATOM         S  BSO4     1
ATOM         O1 BSO4     1
ATOM         O2 BSO4     1
""", """\
conformer: "A"
  residue: "SO4" "   1" " " 0 0
    atom: " S  "
    atom: " O1 "
    atom: " O2 "
conformer: "B"
  residue: "SO4" "   1" " " 0 0
    atom: " S  "
    atom: " O1 "
    atom: " O2 "
""")
  #
  check("""\
ATOM         S  ASO4     1
ATOM         O1 ASO4     1
ATOM         O2 ASO4     1
ATOM         S  BSO4     1
ATOM         O1 BSO4     1
ATOM         O2 BSO4     1
ATOM         O   HOH     2
""", """\
conformer: "A"
  residue: "SO4" "   1" " " 0 0
    atom: " S  "
    atom: " O1 "
    atom: " O2 "
  residue: "HOH" "   2" " " 1 1
    atom: " O  "
conformer: "B"
  residue: "SO4" "   1" " " 0 0
    atom: " S  "
    atom: " O1 "
    atom: " O2 "
  residue: "HOH" "   2" " " 1 1
    atom: " O  "
""")
  #
  check("""\
ATOM         S   SO4     6
ATOM         O1 ASO4     6
ATOM         O2 ASO4     6
ATOM         O3 BSO4     6
ATOM         O4 BSO4     6
""", """\
conformer: "A"
  residue: "SO4" "   6" " " 0 0
    atom: " S  "
    atom: " O1 "
    atom: " O2 "
conformer: "B"
  residue: "SO4" "   6" " " 0 0
    atom: " S  "
    atom: " O3 "
    atom: " O4 "
""")
  #
  check("""\
ATOM         N1  R01     1I
ATOM         N2  R01     1I
ATOM         N1  R02     1I
ATOM         N2  R02     1I
""", """\
conformer: ""
  residue: "R01" "   1" "I" 0 1
    atom: " N1 "
    atom: " N2 "
  residue: "R02" "   1" "I" 1 1
    atom: " N1 "
    atom: " N2 "
""")
  #
  check("""\
ATOM         N1 AR01     1I
ATOM         N2  R01     1I
ATOM         N1  R02     1I
ATOM         N2  R02     1I
""", """\
conformer: "A"
  residue: "R01" "   1" "I" 0 0
    atom: " N2 "
    atom: " N1 "
  residue: "R02" "   1" "I" 1 1
    atom: " N1 "
    atom: " N2 "
""")
  #
  check("""\
ATOM         N1 AR01     1I
ATOM         N2  R01     1I
ATOM         N1 AR02     1I
ATOM         N2  R02     1I
""", """\
conformer: "A"
  residue: "R01" "   1" "I" 0 0
    atom: " N2 "
    atom: " N1 "
  residue: "R02" "   1" "I" 1 0
    atom: " N2 "
    atom: " N1 "
""")
  #
  check("""\
ATOM         N1 AR01     1I
ATOM         N2  R01     1I
ATOM         N1 BR02     1I
ATOM         N2  R02     1I
""", """\
conformer: "A"
  residue: "R01" "   1" "I" 0 0
    atom: " N2 "
    atom: " N1 "
  residue: "R02" "   1" "I" 1 1
    atom: " N2 "
conformer: "B"
  residue: "R01" "   1" "I" 0 1
    atom: " N2 "
  residue: "R02" "   1" "I" 1 0
    atom: " N2 "
    atom: " N1 "
""")
  #
  check("""\
ATOM         N1 AR01     1I
ATOM         N2 BR01     1I
ATOM         N1  R02     1I
ATOM         N2  R02     1I
""", """\
conformer: "A"
  residue: "R01" "   1" "I" 0 0
    atom: " N1 "
  residue: "R02" "   1" "I" 1 1
    atom: " N1 "
    atom: " N2 "
conformer: "B"
  residue: "R01" "   1" "I" 0 0
    atom: " N2 "
  residue: "R02" "   1" "I" 1 1
    atom: " N1 "
    atom: " N2 "
""")
  #
  check("""\
ATOM         N1 AR01     1I
ATOM         N2 BR01     1I
ATOM         N1 CR02     1I
ATOM         N2  R02     1I
""", """\
conformer: "A"
  residue: "R01" "   1" "I" 0 0
    atom: " N1 "
  residue: "R02" "   1" "I" 1 1
    atom: " N2 "
conformer: "B"
  residue: "R01" "   1" "I" 0 0
    atom: " N2 "
  residue: "R02" "   1" "I" 1 1
    atom: " N2 "
conformer: "C"
  residue: "R02" "   1" "I" 1 0
    atom: " N2 "
    atom: " N1 "
""")
  #
  check("""\
ATOM         N1 AR01     1I
ATOM         N2 BR01     1I
ATOM         N1 CR02     1I
ATOM         N2 DR02     1I
""", """\
conformer: "A"
  residue: "R01" "   1" "I" 0 0
    atom: " N1 "
conformer: "B"
  residue: "R01" "   1" "I" 0 0
    atom: " N2 "
conformer: "C"
  residue: "R02" "   1" "I" 0 0
    atom: " N1 "
conformer: "D"
  residue: "R02" "   1" "I" 0 0
    atom: " N2 "
""")
  #
  check(pdb_1nym_60, """\
conformer: "A"
  residue: "LYS" "  32" " " 0 0
    atom: " CA "
    atom: " CB "
  residue: "VAL" "  33" " " 1 1
    atom: " CA "
    atom: " CB "
  residue: "LYS" "  34" " " 1 0
    atom: " CA "
    atom: " CB "
  residue: "ASP" "  35" " " 1 0
    atom: " CA "
    atom: " CB "
  residue: "ALA" "  36" " " 1 1
    atom: " CA "
    atom: " CB "
  residue: "GLU" "  37" " " 1 0
    atom: " CA "
    atom: " CB "
  residue: "ASP" "  38" " " 1 0
    atom: " CA "
    atom: " CB "
  residue: "GLN" "  39" " " 1 0
    atom: " CA "
    atom: " CB "
  residue: "LEU" "  40" " " 1 1
    atom: " CA "
    atom: " CB "
conformer: "B"
  residue: "LYS" "  32" " " 0 0
    atom: " CA "
    atom: " CB "
  residue: "VAL" "  33" " " 1 1
    atom: " CA "
    atom: " CB "
  residue: "LYS" "  34" " " 1 0
    atom: " CA "
    atom: " CB "
  residue: "ASP" "  35" " " 1 0
    atom: " CA "
    atom: " CB "
  residue: "ALA" "  36" " " 1 1
    atom: " CA "
    atom: " CB "
  residue: "GLU" "  37" " " 1 0
    atom: " CA "
    atom: " CB "
  residue: "ASP" "  38" " " 1 0
    atom: " CA "
    atom: " CB "
  residue: "GLN" "  39" " " 1 0
    atom: " CA "
    atom: " CB "
  residue: "LEU" "  40" " " 1 1
    atom: " CA "
    atom: " CB "
""")
  #
  check(pdb_2izq_220, """\
conformer: "A"
  residue: "TRP" "  11" " " 0 0
    atom: " N  "
    atom: " CA "
    atom: " C  "
    atom: " O  "
    atom: " CB "
    atom: " CG "
    atom: " CD1"
    atom: " CD2"
    atom: " NE1"
    atom: " CE2"
    atom: " CE3"
    atom: " CZ2"
    atom: " CZ3"
    atom: " CH2"
    atom: " H  "
    atom: " HA "
    atom: " HB2"
    atom: " HB3"
  residue: "DLE" "  12" " " 1 0
    atom: " N  "
    atom: " CA "
    atom: " C  "
    atom: " O  "
    atom: " CB "
    atom: " CG "
    atom: " CD1"
    atom: " CD2"
    atom: " H  "
    atom: " HA "
    atom: " HB1"
    atom: " HB2"
    atom: " HG "
conformer: "C"
  residue: "PHE" "  11" " " 0 0
    atom: " N  "
    atom: " CA "
    atom: " C  "
    atom: " O  "
    atom: " CB "
    atom: " CG "
    atom: " CD1"
    atom: " CD2"
    atom: " CE1"
    atom: " CE2"
    atom: " CZ "
    atom: " HB2"
    atom: " HB3"
    atom: " HD1"
    atom: " HD2"
    atom: " HE1"
    atom: " HE2"
    atom: " HZ "
  residue: "DLE" "  12" " " 1 1
    atom: " N  "
    atom: " CA "
    atom: " C  "
    atom: " O  "
conformer: "B"
  residue: "TYR" "  11" " " 0 0
    atom: " N  "
    atom: " CA "
    atom: " C  "
    atom: " O  "
    atom: " CB "
    atom: " CG "
    atom: " CD1"
    atom: " CD2"
    atom: " CE1"
    atom: " CE2"
    atom: " CZ "
    atom: " OH "
    atom: " H  "
    atom: " HA "
  residue: "DLE" "  12" " " 1 0
    atom: " N  "
    atom: " CA "
    atom: " C  "
    atom: " O  "
    atom: " CB "
    atom: " CG "
    atom: " CD1"
    atom: " CD2"
    atom: " HB1"
    atom: " HB2"
    atom: " HG "
""")
  #
  check("""\
HEADER    HORMONE                                 01-MAY-98   1ZEH
HETATM  878  C1 ACRS     5      12.880  14.021   1.197  0.50 33.23           C
HETATM  879  C1 BCRS     5      12.880  14.007   1.210  0.50 34.27           C
HETATM  880  C2 ACRS     5      12.755  14.853   0.093  0.50 33.88           C
HETATM  881  C2 BCRS     5      13.935  13.115   1.278  0.50 34.25           C
HETATM  882  C3 ACRS     5      13.668  14.754  -0.945  0.50 33.82           C
HETATM  883  C3 BCRS     5      14.848  13.014   0.238  0.50 34.30           C
HETATM  884  C4 ACRS     5      14.707  13.834  -0.888  0.50 33.46           C
HETATM  885  C4 BCRS     5      14.695  13.821  -0.884  0.50 34.40           C
HETATM  886  C5 ACRS     5      14.835  13.001   0.219  0.50 33.30           C
HETATM  887  C5 BCRS     5      13.635  14.719  -0.957  0.50 34.78           C
HETATM  888  C6 ACRS     5      13.916  13.105   1.252  0.50 33.26           C
HETATM  889  C6 BCRS     5      12.731  14.813   0.090  0.50 34.86           C
HETATM  890  C7 ACRS     5      13.552  15.660  -2.169  0.50 33.90           C
HETATM  891  C7 BCRS     5      16.001  12.014   0.353  0.50 34.77           C
HETATM  892  O1 ACRS     5      11.973  14.116   2.233  0.50 34.24           O
HETATM  893  O1 BCRS     5      11.973  14.107   2.248  0.50 35.28           O
HETATM  894  O   HOH     5      -0.924  19.122  -8.629  1.00 11.73           O
HETATM  895  O   HOH     6     -19.752  11.918   3.524  1.00 13.44           O
""", """\
conformer: "A"
  residue: "CRS" "   5" " " 0 0
    atom: " C1 "
    atom: " C2 "
    atom: " C3 "
    atom: " C4 "
    atom: " C5 "
    atom: " C6 "
    atom: " C7 "
    atom: " O1 "
  residue: "HOH" "   5" " " 1 1
    atom: " O  "
  residue: "HOH" "   6" " " 1 1
    atom: " O  "
conformer: "B"
  residue: "CRS" "   5" " " 0 0
    atom: " C1 "
    atom: " C2 "
    atom: " C3 "
    atom: " C4 "
    atom: " C5 "
    atom: " C6 "
    atom: " C7 "
    atom: " O1 "
  residue: "HOH" "   5" " " 1 1
    atom: " O  "
  residue: "HOH" "   6" " " 1 1
    atom: " O  "
""")
  check("""\
HEADER    HYDROLASE                               22-NOV-07   2VHL
HETATM 6362  O   HOH B2048      47.616  10.724 150.212  1.00 46.48           O
HETATM 6363  O  AHOH B2049      46.408  16.672 146.066  0.50 12.81           O
HETATM 6364  O   HOH B2050      29.343  12.806 185.898  1.00 35.57           O
HETATM 6365  O  BHOH B2049      43.786  12.615 147.734  0.50 28.43           O
HETATM 6366  O   HOH B2052      35.068  19.167 155.349  1.00 15.97           O
""", """\
conformer: "A"
  residue: "HOH" "2048" " " 0 1
    atom: " O  "
  residue: "HOH" "2049" " " 1 0
    atom: " O  "
  residue: "HOH" "2050" " " 1 1
    atom: " O  "
  residue: "HOH" "2052" " " 1 1
    atom: " O  "
conformer: "B"
  residue: "HOH" "2048" " " 0 1
    atom: " O  "
  residue: "HOH" "2049" " " 1 0
    atom: " O  "
  residue: "HOH" "2050" " " 1 1
    atom: " O  "
  residue: "HOH" "2052" " " 1 1
    atom: " O  "
""")

def exercise_as_pdb_string(pdb_file_names, comprehensive):
  pdb_string = """\
HETATM  145  C21 DA7  3014      18.627   3.558  25.202  0.50 29.50           C
ATOM    146  C8 ADA7  3015       9.021 -13.845  22.131  0.50 26.57           C
"""
  pdb_inp = pdb.input(source_info=None, lines=flex.split_lines(pdb_string))
  hierarchy = pdb_inp.construct_hierarchy_v2()
  assert not show_diff(hierarchy.as_pdb_string(), pdb_string+"TER\n")
  #
  if (pdb_file_names is None):
    print "Skipping exercise_as_pdb_string(): input files not available"
    return
  for file_name in pdb_file_names:
    if (not comprehensive and random.random() > 0.1):
      continue
    pdb_inp_1 = pdb.input(file_name=file_name)
    hierarchy_1 = pdb_inp_1.construct_hierarchy_v2()
    pdb_str_1 = hierarchy_1.as_pdb_string(append_end=True)
    pdb_inp_2 = pdb.input(
      source_info=None, lines=flex.split_lines(pdb_str_1))
    hierarchy_2 = pdb_inp_2.construct_hierarchy_v2()
    pdb_str_2 = hierarchy_2.as_pdb_string(append_end=False)
    assert not show_diff(pdb_str_1, pdb_str_2+"END\n")

def get_phenix_regression_pdb_file_names():
  pdb_dir = libtbx.env.find_in_repositories("phenix_regression/pdb")
  if (pdb_dir is None): return None
  result = []
  for node in os.listdir(pdb_dir):
    if (not (node.endswith(".pdb") or node.endswith(".ent"))): continue
    result.append(os.path.join(pdb_dir, node))
  assert len(result) != 0
  return result

def exercise(args):
  comprehensive = "--comprehensive" in args
  forever = "--forever" in args
  print "iotbx.pdb.hierarchy_v2.atom.sizeof_data():", \
    pdb.hierarchy_v2.atom.sizeof_data()
  phenix_regression_pdb_file_names = get_phenix_regression_pdb_file_names()
  while True:
    exercise_atom()
    exercise_atom_group()
    exercise_residue_group()
    exercise_chain()
    exercise_model()
    exercise_root()
    exercise_format_atom_record()
    exercise_construct_hierarchy()
    exercise_convenience_generators()
    exercise_only()
    exercise_merge_atom_groups()
    exercise_merge_residue_groups()
    exercise_chain_merge_residue_groups()
    exercise_edit_blank_altloc()
    exercise_find_pure_altloc_ranges()
    exercise_occupancy_groups_simple()
    exercise_conformers()
    exercise_as_pdb_string(
      pdb_file_names=phenix_regression_pdb_file_names,
      comprehensive=comprehensive)
    if (not forever): break
  print format_cpu_times()

if (__name__ == "__main__"):
  exercise(sys.argv[1:])
