#
# Shelx .ins file processing
#
# PAVEL AFONINE
#
from cctbx import xray
import math
import sys
from cctbx import crystal
from cctbx import adptbx
from cctbx.eltbx.xray_scattering import wk1995
from iotbx.shelx import crystal_symmetry_from_ins

def from_ins(file_name=None,
             crystal_symmetry=None, force_symmetry=00000,
             ignore_atom_element_q=0001,
             scan_atom_element_columns=0001,
             fractional_coordinates=00000,
             min_distance_sym_equiv=0.5):

  file = open(file_name)
  pdb_records = collect_records(raw_records=file)

  crystal_symmetry = None
  crystal_symmetry = crystal_symmetry_from_ins.extract_from(
    file_name=file_name)
  assert crystal_symmetry is not None, "Unknown crystal symmetry."
  assert crystal_symmetry.unit_cell() is not None, "Unknown unit cell."
  assert crystal_symmetry.space_group_info() is not None,"Unknown space group."

  structure = xray.structure(
    special_position_settings = crystal.special_position_settings(
      crystal_symmetry=crystal_symmetry,
      min_distance_sym_equiv=min_distance_sym_equiv))

  k=0
  dict_allowed_atoms = {}
  for record in pdb_records:
    if(record.record_name == "SFAC"):
      for x in record.dict_sfac_content.values():
        k += 1
        dict_allowed_atoms[k] = x

  u_iso_negative = 0
  scatterer = None
  for i in xrange(len(pdb_records)):
    record = pdb_records[i]
    if(record.record_iden == "ATOM" and record.rec_part == 1):
      record_next = pdb_records[i+1]
      b = record.tempFactor + record_next.tempFactor
      scatterer = xray.scatterer(
        label     = " %s" % record.name,
        site      = record.coordinates,
        b         = record.tempFactor + record_next.tempFactor,
        occupancy = record.occupancy,
        scattering_type = wk1995(
          dict_allowed_atoms[record.name_id], 1).label())
      scatterer = scatterer.copy(
        u=adptbx.u_cif_as_u_star(structure.unit_cell(), b))
      structure.add_scatterer(scatterer)
    elif(record.record_iden == "ATOM" and record.rec_part == 0):
      u_cif_iso_diag = record.tempFactor
      u_star=adptbx.u_cif_as_u_star(structure.unit_cell(), u_cif_iso_diag)
      u_iso = adptbx.u_star_as_u_iso(structure.unit_cell(), u_star)
      if(u_iso < 0.0): u_iso_negative = 1
      scatterer = xray.scatterer(
        label     = " %s" % record.name,
        site      = record.coordinates,
        u         = u_iso,
        occupancy = record.occupancy,
        scattering_type = wk1995(
          dict_allowed_atoms[record.name_id], 1).label())
      structure.add_scatterer(scatterer)
  if(u_iso_negative == 1): if_u_iso_negative(structure)
  return structure

def if_u_iso_negative(structure):
  for j in xrange(structure.scatterers().size()):
    atom_chem_type = wk1995(structure.scatterers()[j].label).label()
    if(atom_chem_type == "H" and structure.scatterers()[j].u_iso < 0.0):
      check_bond_number = 0
      for i in xrange(structure.scatterers().size()):
        site_i = structure.unit_cell().orthogonalize(
          structure.scatterers()[i].site)
        site_j = structure.unit_cell().orthogonalize(
          structure.scatterers()[j].site)
        atom_chem_type = wk1995(structure.scatterers()[i].label).label()
        if(atom_chem_type != "H"):
          dist = math.sqrt((site_i[0]-site_j[0])**2 +
                           (site_i[1]-site_j[1])**2 +
                           (site_i[2]-site_j[2])**2)
          if(dist < 1.2 and dist > 0.6):
            check_bond_number += 1
            assert check_bond_number == 1, "multiple choice of bond possible"
            u_iso = adptbx.u_star_as_u_iso(
              structure.unit_cell(), structure.scatterers()[i].u_star)
            u_iso_new = u_iso * abs(structure.scatterers()[j].u_iso)
            structure.scatterers()[j].u_iso = u_iso_new
      assert structure.scatterers()[j].u_iso > 0.0

class ins_record:

  def __init__(self, raw_record, line_number=None):
    self.raw = (raw_record + " " * 80)[:80]
    self.line_number = line_number
    self.record_name = (self.raw)[:4].upper().strip()
    self.record_iden = "!ATOM"
    if(self.if_atom_rec()):
      function_name = "read_" + "ATOM_XYZQU"
      self.record_iden = "ATOM"
    else:
      function_name = "read_" + self.record_name
    bound_function_object = getattr(self, function_name, None)
    if (bound_function_object is not None):
      bound_function_object()

  def if_atom_rec(self):
    atom_rec        = self.raw
    atom_rec_items  = atom_rec.split()
    atom_rec_length = len(atom_rec_items)
    atom_rec_dot    = atom_rec.count(".")
    atom_rec_eql    = atom_rec_items.count("=")
    self.atom_rec_ok8 = (atom_rec_length == 8 and
                         atom_rec_dot    == 5 and
                         atom_rec_eql    == 1)
    self.atom_rec_ok5 = (atom_rec_length == 5 and
                         atom_rec_dot    == 5 and
                         atom_rec_eql    == 0)
    self.atom_rec_ok9 = (atom_rec_length == 9 and
                         atom_rec_dot    == 6 and
                         atom_rec_eql    == 1)
    self.atom_rec_ok4 = (atom_rec_length == 4 and
                         atom_rec_dot    == 4 and
                         atom_rec_eql    == 0)
    self.atom_rec_ok7 = (atom_rec_length == 7 and
                         atom_rec_dot    == 5 and
                         atom_rec_eql    == 0)
    if(self.atom_rec_ok8 or self.atom_rec_ok5 or
       self.atom_rec_ok7 or self.atom_rec_ok9 or
       self.atom_rec_ok4):
      result = 1
    else:
      result = 0
    return result

  def Error(self, message=None):
    if(message is not None):
      sys.stdout.write(message)
      sys.exit(1)

  def read_ATOM_XYZQU(self):
    atom_rec        = self.raw
    atom_rec_items  = atom_rec.split()
    atom_rec_length = len(atom_rec_items)
    if(self.atom_rec_ok8):
      self.rec_part = 1
      self.name         = atom_rec_items[0]
      try: self.name_id = int(atom_rec_items[1])
      except: self.Error("ERROR: atom IDs must be integer (> 0) numbers.")
      try: self.coordinates = [float(x) for x in (atom_rec_items[2],
                                                  atom_rec_items[3],
                                                  atom_rec_items[4])]
      except: self.Error("ERROR: coordinates must be floating point numbers.")
      try: self.occupancy  = float(atom_rec_items[5])
      except: self.Error("ERROR: occupancies must be floating point numbers.")
      try: self.tempFactor= [float(atom_rec_items[6])]
      except: self.Error("ERROR: b-factors must be floating point numbers.")
    elif(self.atom_rec_ok5):
      self.rec_part = 2
      try: self.tempFactor = [float(x) for x in (atom_rec_items[0],
                                                 atom_rec_items[1],
                                                 atom_rec_items[4],
                                                 atom_rec_items[3],
                                                 atom_rec_items[2])]
      except: self.Error("ERROR: b-factors must be floating point numbers.")
    if(self.atom_rec_ok9):
      self.rec_part = 1
      self.name           = atom_rec_items[0]
      try: self.name_id = int(atom_rec_items[1])
      except: self.Error("ERROR: atom IDs must be integer (> 0) numbers.")
      try: self.coordinates = [float(x) for x in (atom_rec_items[2],
                                                  atom_rec_items[3],
                                                  atom_rec_items[4])]
      except: self.Error("ERROR: coordinates must be floating point numbers.")
      try: self.occupancy  = float(atom_rec_items[5])
      except: self.Error("ERROR: occupancies must be floating point numbers.")
      try: self.tempFactor= [float(atom_rec_items[6]),float(atom_rec_items[7])]
      except: self.Error("ERROR: b-factors must be floating point numbers.")
    elif(self.atom_rec_ok4):
      self.rec_part = 2
      try: self.tempFactor = [float(x) for x in (atom_rec_items[0],
                                                 atom_rec_items[3],
                                                 atom_rec_items[2],
                                                 atom_rec_items[1])]
      except: self.Error("ERROR: b-factors must be floating point numbers.")
    elif(self.atom_rec_ok7):
      self.rec_part = 0
      self.name           = atom_rec_items[0]
      try: self.name_id = int(atom_rec_items[1])
      except: self.Error("ERROR: atom IDs must be integer (> 0) numbers.")
      try: self.coordinates = [float(x) for x in (atom_rec_items[2],
                                                  atom_rec_items[3],
                                                  atom_rec_items[4])]
      except: self.Error("ERROR: coordinates must be floating point numbers.")
      try: self.occupancy  = float(atom_rec_items[5])
      except: self.Error("ERROR: occupancies must be floating point numbers.")
      try: self.tempFactor = [float(atom_rec_items[6]),
                              float(atom_rec_items[6]),
                              float(atom_rec_items[6]),0.0,0.0,0.0]
      except: self.Error("ERROR: b-factors must be floating point numbers.")
    self.if_10_added()

  def if_10_added(self):
    if(self.rec_part == 1 or self.rec_part == 0):
      for i in xrange(3):
        if(abs(self.coordinates[i]) > 5.0): self.coordinates[i] -= 10.0
      if(abs(self.occupancy) > 5.0): self.occupancy -= 10.0
      for i in xrange(len(self.tempFactor)):
        if(abs(self.tempFactor[i]) > 5.0): self.tempFactor[i] -= 10.0
    elif(self.rec_part == 2):
      for i in xrange(len(self.tempFactor)):
        if(abs(self.tempFactor[i]) > 5.0): self.tempFactor[i] -= 10.0

  def read_SFAC(self):
    atom_rec        = self.raw
    atom_rec_items  = atom_rec.split()
    atom_rec_length = len(atom_rec_items)
    self.dict_sfac_content = {}
    for i in range(1,atom_rec_length,1):
       assert atom_rec_items[i] == wk1995(atom_rec_items[i]).label()
       self.dict_sfac_content[i] = wk1995(atom_rec_items[i]).label()

def collect_records(raw_records):
  line_number = 0
  records = []
  for raw_record in raw_records:
    line_number += 1
    r = ins_record(raw_record, line_number)
    records.append(r)
  return records
