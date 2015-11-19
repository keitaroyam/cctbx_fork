from __future__ import division

from mmtbx.rotamer import ramachandran_eval
from mmtbx.building.loop_closure import utils
from mmtbx.validation.ramalyze import ramalyze,
from mmtbx.validation.ramalyze import RAMALYZE_FAVORED # import dependency
from mmtbx.validation.ramalyze import RAMALYZE_ALLOWED # import dependency
from mmtbx.validation.ramalyze import RAMALYZE_OUTLIER # import dependency
import itertools


def set_rama_angles(moving_h, angles):
  """
  angles = [(phi, psi), (phi, psi), ... (phi, psi)]
  phi or psi == None means we don't change this angle
  returns deep-copied hierarchy with new angles. Change occurs from first to
  last angle so starting point would be in the same place.
  This function should produce up to all possible favored conformations.
  This function doesn't change moving_h

  """
  # print "angles", angles
  # STOP()
  result_h = moving_h.deep_copy()
  result_h.reset_atom_i_seqs()
  phi_psi_atoms = utils.get_phi_psi_atoms(moving_h)
  assert len(phi_psi_atoms) == len(angles)
  for ps_atoms, target_angle_pair in zip(phi_psi_atoms, angles):
    phi_psi_pair = ps_atoms[0]
    phi_psi_angles = utils.get_pair_angles(phi_psi_pair)
    # phi
    if target_angle_pair[0] is not None:
      utils.rotate_atoms_around_bond(
          result_h,
          phi_psi_pair[0][1],
          phi_psi_pair[0][2],
          angle=-phi_psi_angles[0]+target_angle_pair[0])
    # psi
    if target_angle_pair[1] is not None:
      utils.rotate_atoms_around_bond(
          result_h,
          phi_psi_pair[1][1],
          phi_psi_pair[1][2],
          angle=-phi_psi_angles[1]+target_angle_pair[1])
  return result_h

def is_not_none_combination(comb):
  for pair in comb:
    if pair != (None, None):
      return True
  return False

# Refactoring idea: combine these two functions
def get_all_starting_conformations(moving_h, change_radius, cutoff=50):
  variants = []
  r = ramachandran_eval.RamachandranEval()
  phi_psi_atoms = utils.get_phi_psi_atoms(moving_h)
  n_rama = len(phi_psi_atoms)
  change_angles = range((n_rama)//2-change_radius, (n_rama)//2+change_radius+1)
  # print "  change_angles", change_angles
  for i, (phi_psi_pair, rama_key) in enumerate(phi_psi_atoms):
    if i in change_angles or (utils.rama_evaluate(phi_psi_pair, r, rama_key) == RAMALYZE_OUTLIER):
      variants.append(ramalyze.get_favored_regions(rama_key))
    else:
      variants.append([(None, None)])
  print "variants", variants
  all_angles_combination = list(itertools.product(*variants))
  result = []
  i = 0
  for comb in all_angles_combination:
    if is_not_none_combination(comb):
      result.append(set_rama_angles(moving_h, list(comb)))
      print "Model %d, angles:" % i, comb
      i += 1
  # STOP()
  return result[:cutoff]

def get_starting_conformations(moving_h, cutoff=50):
  """
  modify only ramachandran outliers.
  """
  variants = []
  r = ramachandran_eval.RamachandranEval()
  phi_psi_atoms = utils.get_phi_psi_atoms(moving_h)
  for phi_psi_pair, rama_key in phi_psi_atoms:
    if (utils.rama_evaluate(phi_psi_pair, r, rama_key) == RAMALYZE_OUTLIER):
      variants.append(ramalyze.get_favored_regions(rama_key))
    else:
      variants.append([(None, None)])
  result = []
  print "variants", variants
  if variants.count([(None, None)]) == len(variants):
    print "Nothing to CCD"
    return result
  all_angles_combination = list(itertools.product(*variants))
  i = 0
  for comb in all_angles_combination:
    print "Model %d, angles:" % i, comb
    if is_not_none_combination(comb):
      result.append(set_rama_angles(moving_h, list(comb)))
    i += 1
  return result[:cutoff]
