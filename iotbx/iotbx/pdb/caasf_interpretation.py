from iotbx.pdb import residue_info
from cctbx.eltbx.caasf import wk1995
import string

class scan_atom_element_columns:

  def __init__(self, pdb_records):
    self.n_uninterpretable = 0
    self.n_interpretable = 0
    self.n_q = 0
    for record in pdb_records:
      if (record.record_name in ("ATOM", "HETATM")):
        if (record.element == " Q"):
          self.n_q += 1
        else:
          try: wk1995(record.element, 1)
          except: self.n_uninterpretable += 1
          else: self.n_interpretable += 1

def from_pdb_atom_record(record, have_useful_atom_element_columns=None):
  try:
    scattering_label = residue_info.get(
      residue_name=record.resName,
      atom_name=record.name).scattering_label
  except KeyError: pass
  else: return wk1995(scattering_label, 1)
  if (have_useful_atom_element_columns and len(record.element.strip()) > 0):
    try: return wk1995(record.element + record.charge, 0)
    except: pass
    try: return wk1995(record.element, 1)
    except: pass
  try: return wk1995(record.name, 0)
  except: pass
  if (record.name[0] in string.digits and record.name[1] == "H"):
    return wk1995("H", 1)
  raise RuntimeError(
    '%sUnknown x-ray scattering coefficients for "%s" "%s"' % (
      record.error_prefix(), record.name, record.resName))
