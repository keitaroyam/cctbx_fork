# -*- coding: utf-8; py-indent-offset: 2 -*-
"""
Deals with examing the atoms around a site and recognizing distinct and useful
chemical environments.
"""

from __future__ import division
from mmtbx import ions
from iotbx.pdb import common_residue_names_get_class as get_class
from scitbx.array_family import flex
from scitbx.math import gaussian_fit_1d_analytical
from scitbx.matrix import col, distance_from_plane
from libtbx.utils import Sorry, xfrange
from libtbx import slots_getstate_setstate
from collections import Counter
from math import pi, cos, sin

# Enums for the chemical environments supported by this module
N_SUPPORTED_ENVIRONMENTS = 14
chem_carboxy, \
  chem_amide, \
  chem_backbone, \
  chem_water, \
  chem_sulfate, \
  chem_phosphate, \
  chem_disulfide, \
  chem_nitrogen_primary, \
  chem_nitrogen_secondary, \
  chem_nitrogen_tertiary, \
  chem_chlorine, \
  chem_oxygen, \
  chem_nitrogen, \
  chem_sulfur = range(N_SUPPORTED_ENVIRONMENTS)


class ScatteringEnvironment (slots_getstate_setstate):
  __slots__ = ["d_min", "wavelength", "fp", "fpp", "b_iso", "b_mean_hoh", "occ",
               "fo_density", "fofc_density", "anom_density"]
  def __init__(self,
      i_seq,
      manager,
      fo_map=None,
      fofc_map=None,
      anom_map=None,
      fo_density=None,
      fofc_density=None,
      anom_density=None):
    assert ([fo_map, fo_density].count(None) == 1)
    assert ([fofc_map, fofc_density].count(None) == 1)
    assert ([anom_map, anom_density].count(None) >= 1)
    atom = manager.pdb_atoms[i_seq]
    self.d_min = manager.fmodel.f_obs().d_min()
    self.wavelength = manager.wavelength
    self.fp, self.fpp = manager.get_fp(i_seq), manager.get_fpp(i_seq)
    if (fo_density is not None) :
      self.fo_density = fo_density
    else :
      self.fo_density = fit_gaussian(manager.unit_cell, atom.xyz, fo_map)
    if (fofc_density is not None) :
      self.fofc_density = fofc_density
    else :
      self.fofc_density = fit_gaussian(manager.unit_cell, atom.xyz, fofc_map)
    if anom_density is not None:
      self.anom_density = anom_density
    elif anom_map is not None:
      self.anom_density = fit_gaussian(manager.unit_cell, atom.xyz, anom_map)
    else:
      self.anom_density = None, None
    self.b_iso = manager.get_b_iso(i_seq)
    self.b_mean_hoh = manager.b_mean_hoh
    self.occ = atom.occ

class atom_contact (slots_getstate_setstate) :
  """
  Container for information about an interacting atom.  Most of the methods
  are simply wrappers for frequently called operations on the atom object, but
  symmetry-aware.
  """
  __slots__ = ["atom", "vector", "site_cart", "rt_mx", "is_carboxy_terminus",
               "element", "charge"]
  def __init__ (self, atom, vector, site_cart, rt_mx) :
    self.atom = atom.fetch_labels()
    self.is_carboxy_terminus = is_carboxy_terminus(atom)
    self.vector = vector
    self.site_cart = site_cart
    self.rt_mx = rt_mx
    self.element = ions.server.get_element(atom)
    self.charge = ions.server.get_charge(atom)

  def distance (self) :
    """Actual distance from target atom"""
    return abs(self.vector)

  def distance_from (self, other) :
    """Distance from another contact"""
    return abs(self.vector - other.vector)

  def id_str (self, suppress_rt_mx = False) :
    if (not self.rt_mx.is_unit_mx()) and (not suppress_rt_mx) :
      return self.atom.id_str() + " " + str(self.rt_mx)
    else :
      return self.atom.id_str()

  def atom_name (self) :
    return self.atom.name.strip()

  def resname (self) :
    return self.atom.fetch_labels().resname.strip().upper()

  @property
  def occ (self) :
    return self.atom.occ

  def atom_i_seq (self) :
    return self.atom.i_seq

  def altloc (self) :
    return self.atom.fetch_labels().altloc.strip()

  def atom_id_no_altloc (self, suppress_rt_mx = False) :
    """Unique identifier for an atom, ignoring the altloc but taking the
    symmetry operator (if any) into account."""
    labels = self.atom.fetch_labels()
    base_id = labels.chain_id + labels.resid() + self.atom.name
    if (self.rt_mx.is_unit_mx()) or (suppress_rt_mx) :
      return base_id
    else :
      return base_id + " " + str(self.rt_mx)

  def __eq__ (self, other) :
    """Equality operator, taking symmetry into account but ignoring the
    altloc identifier."""
    return (other.atom_id_no_altloc() == self.atom_id_no_altloc())

  def __abs__ (self) :
    return self.distance()

  def __str__ (self) :
    return self.id_str()

class ChemicalEnvironment (slots_getstate_setstate):
  __slots__ = ["atom", "contacts", "contacts_no_alts", "chemistry", "geometry"]

  def __init__(self, i_seq, contacts, manager):
    self.atom = manager.pdb_atoms[i_seq].fetch_labels()

    self.contacts = contacts
    self.contacts_no_alts = []

    # Filter down the list of contacts so it doesn't include alt locs
    for index, contact in enumerate(contacts):
      if contact.element in ["H", "D"]:
        continue

      no_alt_loc = True
      for other_contact in contacts[index + 1:]:
        if same_atom_different_altloc(contact.atom, other_contact.atom) and \
          contact.rt_mx == other_contact.rt_mx:
          no_alt_loc = False
          break
      if no_alt_loc:
        self.contacts_no_alts.append(contact)

    self.chemistry = self._get_chemical_environment(
      self.contacts_no_alts, manager)
    self.geometry = ions.geometry.find_coordination_geometry(
      self.contacts_no_alts, minimizer_method = True)

    # We can either store the contacts or generate a list of valences for all of
    # the atom types we want to test. I'm choosing the former because it's more
    # flexible down the road and contacts is pickable anyways.
    # self.valences = None

  def get_valence(self, element, charge = None):
    """
    Calculates the BVS and VECSUM for a given element / charge identity.

    Parameters
    ----------
    element : str
        The element identity to calculate valences for.
    charge : int, optional
        The charge to calculate valences for.

    Returns
    -------
    float
        BVS
    float
        VECSUM

    Notes
    -----
    .. [1] Müller, P., Köpke, S. & Sheldrick, G. M. Is the bond-valence method
           able to identify metal atoms in protein structures? Acta
           Crystallogr. D. Biol. Crystallogr. 59, 32–7 (2003).
    """
    if charge is None:
      charge = ions.server.get_charge(element)
    ion_params = ions.metal_parameters(element = element, charge = charge)
    vectors = ions.server.calculate_valences(ion_params, self.contacts)
    bvs = sum([abs(i) for i in vectors])
    vecsum = abs(sum(vectors, col((0, 0, 0))))
    return bvs, vecsum

  def _get_chemical_environment(self, contacts, manager):
    """
    Examines an atom contact object for chemical properties useful to ion
    picking. These properties include degree of connectivitiy, presence in
    carboxy and amide groups, disulfide bonds, and so on.

    Parameters
    ----------
    contacts : list of mmtbx.ions.atom_contact
        The contact objects to examine the chemical environments of. Generally
        created by manager.find_nearby_atoms.
    manager : mmtbx.ions.identify.manager
        The ions manager that created contact. Used for auxillary information
        such as bond connectivity.

    Returns
    -------
    collections.Counter
        The chemical environments found for contacts.
    """
    def _non_hydrogen_neighbors(seq):
      """
      Parameters
      ----------
      seq : int
          The atom.i_seq to find the neighbors of.

      Returns
      -------
      list of int
          A list of neighboring atoms that does not include any hydrogens.
      """
      neighbors = []
      for other in manager.connectivity[seq]:
        other_atom = manager.pdb_atoms[other]
        if ions.server.get_element(other_atom) not in ["H", "D"]:
          neighbors.append(other)
      return neighbors

    def _n_non_altlocs(i_seqs):
      """
      Count the number of neighbors, filtering out those that are alt-locs of
      other neighboring atoms.
      """
      non_alt_locs = []
      for index, i_seq in enumerate(i_seqs):
        no_alt_loc = True
        for j_seq in i_seqs[index + 1:]:
          if same_atom_different_altloc(
              manager.pdb_atoms[i_seq], manager.pdb_atoms[j_seq]):
            no_alt_loc = False
            break
        if no_alt_loc:
          non_alt_locs.append(i_seq)
      return len(non_alt_locs)

    chem_env = Counter()

    for contact in contacts:
      # Add any of our included elements
      element = contact.element
      i_seq = contact.atom.i_seq
      neighbor_elements = [ ions.server.get_element(manager.pdb_atoms[i])
                           for i in _non_hydrogen_neighbors(i_seq)]

      n_neighbors = _n_non_altlocs(_non_hydrogen_neighbors(i_seq))

      # Check for waters, sulfates, phosphates, chlorides, etc
      if element == "CL":
        chem_env[chem_chlorine] += 1
      elif element == "O":
        chem_env[chem_oxygen] += 1
        if get_class(contact.resname()) in ["common_water"]:
          chem_env[chem_water] += 1
        elif "S" in neighbor_elements:
          chem_env[chem_sulfate] += 1
        elif "P" in neighbor_elements:
          chem_env[chem_phosphate] += 1
      elif element == "N":
        chem_env[chem_nitrogen] += 1
        # Check the degree of connectivity on nitrogens
        if n_neighbors == 1:
          chem_env[chem_nitrogen_primary] += 1
        elif n_neighbors == 2:
          chem_env[chem_nitrogen_secondary] += 1
        elif n_neighbors == 3:
          chem_env[chem_nitrogen_tertiary] += 1
        elif n_neighbors != 0:
          raise Sorry("Nitrogen with more than three coordinating atoms: " +
                      contact.atom.id_str())
      elif element == "S":
        chem_env[chem_sulfur] += 1
        # Check for disulfide bridges
        if "S" in neighbor_elements:
          chem_env[chem_disulfide] += 1

      # Check for backbone nitrogens
      if contact.atom.name.strip().upper() in ["N", "C", "O", "CA"] and \
        get_class(contact.resname()) in ["common_amino_acid"]:
        chem_env[chem_backbone] += 1

      # Check for carboxy / amide groups
      if element in ["O", "N"] and n_neighbors == 1:
        for j_seq in _non_hydrogen_neighbors(i_seq):
          j_atom = manager.pdb_atoms[j_seq]
          if ions.server.get_element(j_atom) in ["C"]:
            for k_seq in manager.connectivity[j_seq]:
              k_neighbors = _non_hydrogen_neighbors(k_seq)
              k_atom = manager.pdb_atoms[k_seq]
              if k_seq != i_seq and _n_non_altlocs(k_neighbors) in [1]:
                k_element = ions.server.get_element(k_atom)
                if set([element, k_element]) == set(["O", "O"]):
                  chem_env[chem_carboxy] += 1
                elif set([element, k_element]) == set(["N", "O"]):
                  chem_env[chem_amide] += 1

    return chem_env

def find_nearby_atoms (
    i_seq,
    xray_structure,
    pdb_atoms,
    asu_mappings,
    asu_table,
    connectivity,
    far_distance_cutoff = 3.0,
    near_distance_cutoff = 1.5,
    filter_by_bonding = True) :
  """
  Given site in the structure, return a list of nearby atoms with the
  supplied cutoff, and the vectors between them and the atom's site. Takes
  into account symmetry operations when finding nearby sites.
  """
  contacts = []
  unit_cell = xray_structure.unit_cell()
  sites_frac = xray_structure.sites_frac()
  site_frac = sites_frac[i_seq]
  asu_dict = asu_table[i_seq]
  site_i = sites_frac[i_seq]
  rt_mx_i_inv = asu_mappings.get_rt_mx(i_seq, 0).inverse()
  atom_i = pdb_atoms[i_seq]
  # Create the primary list of contacts
  for j_seq, j_sym_groups in asu_dict.items():
    site_j = sites_frac[j_seq]
    atom_j = pdb_atoms[j_seq]
    # Filter out hydrogens
    if atom_j.element.upper().strip() in ["H", "D"]:
      continue
    # Filter out alternate conformations of this atom
    if same_atom_different_altloc(atom_i, atom_j):
      continue
    # Gather up contacts with all symmetric copies
    for j_sym_group in j_sym_groups:
      for j_sym_id in j_sym_group :
        rt_mx = rt_mx_i_inv.multiply(asu_mappings.get_rt_mx(j_seq, j_sym_id))
        site_ji = rt_mx * site_j
        site_ji_cart = unit_cell.orthogonalize(site_ji)
        vec_i = col(unit_cell.orthogonalize(site_frac=site_frac))
        vec_ji = col(site_ji_cart)
        assert abs(vec_i - vec_ji) < far_distance_cutoff + 0.5
        contact = atom_contact(
          atom = atom_j,
          vector = vec_i - vec_ji,
          site_cart = site_ji_cart,
          rt_mx = rt_mx)
        # XXX I have no idea why the built-in handling of special positions
        # doesn't catch this for us
        if (j_seq == i_seq) and (not rt_mx.is_unit_mx()) :
          continue
        if contact.distance() < near_distance_cutoff:
          continue
        contacts.append(contact)
  # Filter out carbons that are judged to be "contacts", but are actually
  # just bonded to genuine coordinating atoms.  This is basically just a
  # way to handle sidechains such as His, Asp/Glu, or Cys where the carbons
  # may be relatively close to the metal site.
  if filter_by_bonding and (connectivity is not None) :
    filtered = []
    all_i_seqs = [contact.atom_i_seq() for contact in contacts]
    for contact in contacts:
      # oxygen is always allowed, other elements may not be
      if contact.element not in ["C", "P", "S", "N"]:
        filtered.append(contact)
        continue
      # Remove atoms within 1.9 A contact distance
      if any(other_contact != contact and
             contact.distance_from(other_contact) < 1.9 and
             contact.distance() > other_contact.distance()
             for other_contact in contacts):
        continue
      # Examine the mode connectivity to catch more closely bonded atoms
      bonded_j_seqs = []
      for j_seq in connectivity[contact.atom_i_seq()]:
        if (j_seq in all_i_seqs) :
          bonded_j_seqs.append(j_seq)
      for j_seq in bonded_j_seqs:
        other_contact = contacts[all_i_seqs.index(j_seq)]
        if other_contact.element in ["N", "O", "S"] and \
          abs(other_contact) < abs(contact):
          break
      else:
        filtered.append(contact)
    contacts = filtered
  return contacts

########################################################################
# UTILITY METHODS
#
def _get_points_within_radius(point, radius, radius_step = 0.2,
                              angle_step = pi / 5):
  """
  Generates a list of points and their associated radius in steps around a
  sphere.

  Parameters
  ----------
  point : tuple of float, float, float
      X, Y, Z, coordinates to center the sampling around.
  radius : float
      Max radius around the center to sample.
  radius_step : float, optional
      Steps along the radius to use when sampling.
  angle_step : float, optional
      Steps around each radii distance to use when sampling. Amount is in
      radians.

  Returns
  -------
  list of tuple of float, float, float
      List of points to be sampled.
  list of float
      List of radii corresponding to each point.
  """

  points = [point]
  radiuses = [0]
  for r in xfrange(radius_step, radius, radius_step):
    for theta in xfrange(-pi, pi, angle_step):
      for phi in xfrange(-pi, pi, angle_step):
        x = r * cos(theta) * sin(phi) + point[0]
        y = r * sin(theta) * sin(phi) + point[1]
        z = r * cos(phi) + point[2]
        points.append((x, y, z))
        radiuses.append(r)

  return points, radiuses

def fit_gaussian(unit_cell, site_cart, real_map, radius = 1.6):
  """
  Fit a gaussian function to the map around a site. Samples points in concentric
  spheres up to radius away from the site.

  f(x) = a * exp(-b * x ** 2)

  Parameters
  ----------
  unit_cell : uctbx.unit_cell object
  site_cart : tuple of float, float, float
      The site's cartesian coordinates to sample the density around.
  real_map : scitbx.array_family.flex
      Real space map of the electron density in the unit cell.
  radius : float, optional
      The max radius to use for sampling.

  Returns
  -------
  float
      Height of gaussian curve.
  float
      Spread of guassian curve.
  """
  points, radiuses = _get_points_within_radius(site_cart, radius)

  map_heights = \
    [real_map.tricubic_interpolation(unit_cell.fractionalize(i))
     for i in points]

  # Gaussian functions can't have negative values, filter sampled points below
  # zero to allow us to find the analytical solution (radius = 2.0 is too big
  # for most atoms anyways)
  x, y = flex.double(), flex.double()
  for rad, height in zip(radiuses, map_heights):
    if height > 0:
      x.append(rad)
      y.append(height)

  try:
    fit = gaussian_fit_1d_analytical(x = x, y = y)
  except RuntimeError as err:
    print(err)
    return 0., 0.
  else:
    return fit.a, fit.b

# XXX distance cutoff may be too generous, but 0.5 is too strict
def is_coplanar_with_sidechain (atom, residue, distance_cutoff = 0.75) :
  """
  Given an isolated atom and an interacting residue with one or more amine
  groups, determine whether the atom is approximately coplanar with the terminus
  of the sidechain (and thus interacting with the amine hydrogen(s) along
  approximately the same axis as the N-H bond).
  """
  sidechain_sites = []
  resname = residue.resname
  for other in residue.atoms() :
    name = other.name.strip()
    if (resname == "ARG") and (name in ["NH1","NH2","NE"]) :
      sidechain_sites.append(other.xyz)
    elif (resname == "GLN") and (name in ["OE1","NE2","CD"]) :
      sidechain_sites.append(other.xyz)
    elif (resname == "ASN") and (name in ["OD1","ND2","CG"]) :
      sidechain_sites.append(other.xyz)
  if (len(sidechain_sites) != 3) : # XXX probably shouldn't happen
    return False
  D = distance_from_plane(atom.xyz, sidechain_sites)
  #print atom.id_str(), D
  return (D <= distance_cutoff)

def is_negatively_charged_oxygen (atom_name, resname) :
  """
  Determine whether the oxygen atom of interest is either negatively charged
  (usually a carboxyl group or sulfate/phosphate), or has a lone pair (and
  no hydrogen atom) that would similarly repel anions.
  """
  if ((atom_name in ["OD1","OD2","OE1","OE2"]) and
      (resname in ["GLU","ASP","GLN","ASN"])) :
    return True
  elif ((atom_name == "O") and (not resname in ["HOH","WAT"])) :
    return True # sort of - the lone pair acts this way
  elif ((len(atom_name) == 3) and (atom_name[0:2] in ["O1","O2","O3"]) and
        (atom_name[2] in ["A","B","G"])) :
    return True
  elif (resname in ["SO4","PO4"]) :
    return True
  return False

def is_carboxy_terminus (pdb_object) :
  atoms = None
  if (type(pdb_object).__name__ == "atom") :
    atoms = pdb_object.parent().atoms()
  else :
    assert (type(pdb_object).__name__ in ['residue_group','atom_group'])
    atoms = pdb_object.atoms()
  for atom in atoms :
    if (atom.name.strip() == "OXT") :
      return True
  return False

def same_atom_different_altloc(atom1, atom2):
  """
  Determines whether atom1 and atom2 differ only by their alternate location.
  """

  label1, label2 = [i.fetch_labels() for i in [atom1, atom2]]
  name1, name2 = atom1.name.strip(), atom2.name.strip()
  chain1, chain2 = label1.chain_id, label2.chain_id
  res1, res2 = label1.resid(), label2.resid()
  return name1 == name2 and chain1 == chain2 and res1 == res2

def count_coordinating_residues (nearby_atoms, distance_cutoff = 3.0) :
  """
  Count the number of residues of each type involved in the coordination
  sphere.  This may yield additional clues to the identity of ions, e.g. only
  Zn will have 4 Cys residues.
  """
  unique_residues = []
  residue_counts = {}
  for contact in nearby_atoms :
    if (contact.distance() <= distance_cutoff) :
      parent = contact.atom.parent()
      for residue in unique_residues :
        if (residue == parent) :
          break
      else :
        resname = parent.resname
        if (not resname in residue_counts) :
          residue_counts[resname] = 0
        residue_counts[resname] += 1
        unique_residues.append(parent)
  return residue_counts
