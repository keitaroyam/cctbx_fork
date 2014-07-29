# -*- coding: utf-8; py-indent-offset: 2 -*-

from __future__ import division

from math import exp
import time
import os

import iotbx.cif
from libtbx import group_args, Auto, slots_getstate_setstate
from libtbx.utils import Sorry
from libtbx import group_args

DEFAULT_IONS = ["MG", "CA", "ZN", "CL"]
HALIDES = ["F", "CL", "BR", "IOD"]
TRANSITION_METALS = ["MN", "FE", "CO", "CU", "NI", "ZN", "PT"]
SUPPORTED = TRANSITION_METALS + HALIDES + ["NA", "MG", "K", "CA", "CD", "HG"]

def _cif_param_as_list (param) :
  if (param == ".") : return None
  return param.split(",")

def _cif_param_as_int (param) :
  if (param == ".") : return None
  return int(param)

def _cif_param_as_float (param) :
  if (param == ".") : return None
  return float(param)

class metal_parameters (group_args) :
  def __str__ (self) :
    return "%s%+d" % (self.element.upper(), self.charge)

  def charge_as_int (self):
    """
    Gets the charge of a parameter as an integer.

    Returns
    -------
    int
    """
    return self.charge

  def scattering_type (self):
    """
    Makes a string showing the element and its associated charge.

    Returns
    -------
    str

    Examples
    --------
    >>> from mmtbx.ions import metal_parameters
    >>> print metal_parameters(element="FE", charge=3).scattering_type()
    FE3+
    >>> print metal_parameters(element="CL", charge=-1).scattering_type()
    CL1-
    """
    charge_symbol = ""
    if (self.charge > 0) :
      charge_symbol = "+"
    elif (self.charge < 0) :
      charge_symbol = "-"
    s = "%2s%1d%s" % (self.element.strip(), abs(self.charge), charge_symbol)
    return s

class parameter_server (slots_getstate_setstate) :
  """
  Class for retrieving information from ion_parameters.cif
  """

  __slots__ = ["params", "_metal_params", "_charge_params", "_resname_elem",
               "_default_charges"]
  def __init__ (self) :
    params_path = os.path.join(os.path.split(__file__)[0],
      "ion_parameters.cif")
    assert os.path.isfile(params_path)
    cif_model = iotbx.cif.reader(file_path=params_path).model()
    self.params = cif_model["ions"]
    self._metal_params = {}
    self._charge_params = {}
    self._resname_elem = {}
    self._default_charges = {}

  def is_supported_element (self, symbol):
    """
    Checks if symbol is a supported element by this parameter server.

    Parameters
    ----------
    symbol : str

    Returns
    -------
    bool
    """
    return symbol in self.params['_lib_valence.atom_symbol']

  def is_supported_donor (self, symbol) :
    """
    Checks if an element is a supported donor atom.

    Parameters
    ----------
    symbol : str

    Returns
    -------
    bool
    """
    return symbol in self.params['_lib_valence.donor_symbol']

  def get_valence_params (self, atom1, atom2):
    """
    Gets the valence parameters (r_0 and b) used for calculating valences from
    bond distances.

    Parameters
    ----------
    atom1 : mmtbx.ions.metal_parameters
    atom2 : mmtbx.ions.metal_parameters

    Returns
    -------
    float or None
        r_0 in the equation exp((r - r_0) / b)
    float or None
        b in the equation exp((r - r_0) / b)

    Examples
    --------
    >>> from mmtbx.ions import server, metal_parameters
    >>> print server.get_valence_params(
    ...   metal_parameters(element="ZN", charge=2),
    ...   metal_parameters(element="N", charge=-3))
    (1.77, 0.37)
    """
    for i_elem, symbol in enumerate(self.params['_lib_valence.atom_symbol']) :
      if (symbol == atom1.element) :
        i_charge = int(self.params['_lib_valence.atom_charge'][i_elem])
        i_other = self.params['_lib_valence.donor_symbol'][i_elem]
        i_other_charge = int(self.params['_lib_valence.donor_charge'][i_elem])
        if ((i_charge == atom1.charge_as_int()) and
            (i_other == atom2.element) and
            (i_other_charge == atom2.charge_as_int())) :
          valence = float(self.params['_lib_valence.value'][i_elem])
          return valence, 0.37
    charge1 = atom1.charge_as_int()
    charge2 = atom2.charge_as_int()
    return None, None

  def _get_default_charge(self, element):
    if element in self._default_charges:
      return self._default_charges[element]
    p = self.params
    for i_elem, elem in enumerate(p["_lib_charge.element"]):
      if elem == element:
        charge = int(p["_lib_charge.charge"][i_elem])
        self._default_charges[element] = charge
        return charge
    return 0

  def _get_charge_params(self, resname, element=None):
    resname = resname.strip().upper()
    if element is not None:
      element = element.strip().upper()
    p = self.params
    if element is None:
      # Determine the element from the residue name (I.E. "HOH" => "O")
      if resname in self._resname_elem:
        element = self._resname_elem[resname]
      else:
        resn_elements = [(resn, p["_lib_charge.element"][i_resn])
                         for i_resn, resn in enumerate(p["_lib_charge.resname"])
                         if resn == resname]
        if len(resn_elements) > 1:
          raise Sorry("Ambiguous element for residue: " + resname)
        elif len(resn_elements) < 1:
          raise Sorry("Unknown element for residue: " + resname)
        element = resn_elements[0][1]
        self._resname_elem[resname] = element
    if (resname, element) in self._charge_params:
      return self._charge_params[(resname, element)]
    for i_resn, resn in enumerate(p["_lib_charge.resname"]):
      if resn == resname and element == p["_lib_charge.element"][i_resn]:
        elem_charge = \
          p["_lib_charge.element"][i_resn], int(p["_lib_charge.charge"][i_resn])
        break
    else:
      elem_charge = element, self._get_default_charge(element)
    self._charge_params[(resname, element)] = elem_charge
    return elem_charge

  def get_element(self, atom):
    """
    Gets the element associated with an atom.

    Parameters
    ----------
    atom : iotbx.pdb.hierarchy.atom or str

    Returns
    -------
    str
    """
    if isinstance(atom, str):
      resname = atom.strip().upper()
      if resname in self.params["_lib_charge.element"]:
        return resname
    else:
      if hasattr(atom, "element") and isinstance(atom.element, str):
        return atom.element.strip().upper()
      resname = atom.fetch_labels().resname.strip().upper()
    return self._get_charge_params(resname=resname)[0]

  def get_charge(self, atom):
    """
    Gets the charge associated with an atom or element.

    Parameters
    ----------
    atom : iotbx.pdb.hierarchy.atom or str

    Returns
    -------
    int

    Examples
    --------
    >>> from iotbx.pdb.hierarchy import atom
    >>> from mmtbx.ions import server
    >>> atom_dummy = atom()
    >>> atom_dummy.element = "N"
    >>> atom_dummy.charge = "-3"
    >>> print server.get_charge(atom_dummy)
    -3
    >>> print server.get_charge("N")
    -3
    """
    if isinstance(atom, str):
      atom = atom.strip().upper()
      try:
        charge = self._get_charge_params(resname=atom)[1]
      except Sorry:
        charge = self._get_charge_params(resname="", element=atom)[1]
    else:
      charge = atom.charge
      if not isinstance(charge, int):
        charge = atom.charge_as_int()
      if charge != 0:
        return charge
      resname = atom.fetch_labels().resname.strip().upper()
      element = atom.element.strip().upper()
      charge = self._get_charge_params(resname=resname, element=element)[1]
    return charge

  def get_charges(self, atom):
    """
    Retrieves all charges that are expected to be associated with an atom or
    element within ion_parameters.cif. This list is manually updated based on
    the ligand IDs listed by the PDB.

    Parameters
    ----------
    atom : iotbx.pdb.hierarchy.atom or str

    Returns
    -------
    list of int

    Examples
    --------
    >>> from mmtbx.ions import server
    >>> print server.get_charges("CU")
    [1, 2, 3]
    >>> print server.get_charges("ZN")
    [1, 2, 3]
   """
    element = self.get_element(atom)
    p = self.params
    charges = set()
    for i_elem, elem in enumerate(p["_lib_charge.element"]):
      if elem == element:
        charges.add(int(p["_lib_charge.charge"][i_elem]))
    return sorted(charges)

  def get_metal_parameters (self, element):
    """
    Gets all metal parameters associated with an element.

    Parameters
    ----------
    element : str

    Returns
    -------
    mmtbx.ions.metal_parameters or None
    """
    p = self.params
    for i_elem, symbol in enumerate(p['_lib_elems.element']) :
      if (symbol == element.upper()) :
        if (symbol in self._metal_params) :
          return self._metal_params[symbol]
        assert (p['_lib_ligands.element'][i_elem] == symbol)
        params = metal_parameters(
          element=symbol,
          charge=_cif_param_as_int(p['_lib_elems.charge'][i_elem]),
          vec_sum_cutoff=_cif_param_as_float(
            p["_lib_elems.vec_sum_cutoff"][i_elem]),
          coord_num_lower=_cif_param_as_int(
            p["_lib_elems.coord_num_lower"][i_elem]),
          coord_num_upper=_cif_param_as_int(
            p["_lib_elems.coord_num_upper"][i_elem]),
          min_coordinating_non_waters=_cif_param_as_int(
            p["_lib_elems.min_coordinating_non_waters"][i_elem]),
          cvbs_lower=_cif_param_as_float(p['_lib_elems.cvbs_lower'][i_elem]),
          cvbs_upper=_cif_param_as_float(p['_lib_elems.cvbs_upper'][i_elem]),
          cvbs_expected=_cif_param_as_float(
            p['_lib_elems.cvbs_expected'][i_elem]),
          allowed_coordinating_atoms=_cif_param_as_list(
            p['_lib_ligands.allowed_coordinating_atoms'][i_elem]),
          allowed_coordinating_residues=_cif_param_as_list(
            p['_lib_ligands.allowed_coordinating_residues'][i_elem]),
          allowed_geometries=_cif_param_as_list(
            p['_lib_ligands.allowed_geometries'][i_elem]),
          allowed_backbone_atoms=_cif_param_as_list(
            p['_lib_ligands.allowed_backbone_atoms'][i_elem]))
        self._metal_params[symbol] = params
        return params
    return None

  def calculate_valence (self, ion, donor, distance):
    """
    Calculates the single valence contribution of one ion donor pair,
    separated by distance. ion and donor should be AtomGuess objects.

    Parameters
    ----------
    ion : mmtbx.ions.metal_parameters
    donor : mmtbx.ions.metal_parameters
    distance : float

    Returns
    -------
    float

    Examples
    --------
    >>> from mmtbx.ions import server, metal_parameters
    >>> ion = server.get_metal_parameters("ZN")
    >>> donor = metal_parameters(element="N", charge="-3")
    >>> valence = server.calculate_valence(ion, donor, 2.20)
    >>> print round(valence, 2)
    0.31
    """
    element = donor.element
    if (not self.is_supported_donor(element)) :
      return 0
    r_0, b = self.get_valence_params(ion, donor)
    if (r_0 is None) :
      # Try again, this time using the default charge for the donor
      donor = metal_parameters(
        charge=self.get_charge(element),
        element=element)
      r_0, b = self.get_valence_params(ion, donor)
      if r_0 is None:
        return 0
    return exp((r_0 - distance) / b)

  def calculate_valences (self, ion, nearby_atoms):
    """
    Calculates all of the valence contributions between ion and each
    atom of nearby_atoms, each element of which should be a tuple of an
    atom and a vector from the ion's location.

    Parameters
    ----------
    ion : mmtbx.ions.metal_parameters
    nearby_atoms : list of mmtbx.ions.environment.atom_contact

    Returns
    -------
    list of scitbx.matrix.rec
        List of vectors, whose magnitudes are equal to the valence contributions
        from each donor atom.

    Examples
    --------
    >>> from libtbx import group_args
    >>> from iotbx.pdb.hierarchy import atom
    >>> from mmtbx.ions import server
    >>> from mmtbx.ions.environment import atom_contact
    >>> from scitbx.matrix import rec
    >>> ion = server.get_metal_parameters("ZN")
    >>> vector_1 = rec([2.0, 0, 0], [1, 3])
    >>> vector_2 = rec([-2.0, 0, 0], [1, 3])
    >>> vector_3 = rec([0, 2.0, 0], [1, 3])
    >>> vector_4 = rec([0, 0, 2.0], [1, 3])
    >>> atom_dummy = atom()
    >>> atom_dummy.element = "N"
    >>> atom_dummy.charge = "-3"
    >>> atom_dummy.occ = 1
    >>> atom_dummy.parent = lambda: group_args(atoms=lambda: [])
    >>> donors = [atom_contact(atom_dummy, vector_1, None, None),
    ...           atom_contact(atom_dummy, vector_2, None, None),
    ...           atom_contact(atom_dummy, vector_3, None, None),
    ...           atom_contact(atom_dummy, vector_4, None, None)]
    >>> vectors = server.calculate_valences(ion, donors)
    >>> bvs = sum(abs(i) for i in vectors)
    >>> print round(bvs, 2)
    2.15
    """
    vectors = []
    for contact in nearby_atoms:
      donor = metal_parameters(
        element=contact.element,
        charge=contact.charge)
      distance = abs(contact.vector)
      valence = self.calculate_valence(ion, donor, distance) * contact.occ
      if valence == 0:
        if ((donor.element not in ["H", "C", "AX"]) and
            (not self.is_supported_donor(donor.element))) :
          pass
      elif distance != 0:
        vectors.append(contact.vector / distance * valence)
    return vectors

def check_supported (elements):
  """
  Checks if elements are supported by ion identitication process.

  Parameters
  ----------
  elements : list of str

  Returns
  -------
  bool

  Raises
  ------
  libtbx.utils.Sorry

  Examples
  --------
  >>> from mmtbx.ions import check_supported
  >>> check_supported(["CA", "ZN", "FE"])
  True
  """
  if (elements is None) :
    raise Sorry("No elements specified for ion picking - must be either "+
      "'Auto' or a comma-separated list of element symbols.")
  elif (elements is not Auto) :
    # XXX somehow comma-separation of phil strings fields doesn't work
    if isinstance(elements, str) or isinstance(elements, unicode) :
      elements = elements.replace(",", " ").split()
    elif (isinstance(elements, list)) and (len(elements) == 1) :
      elements = elements[0].split(",")
    if (elements == ['X']) : # XXX hack for testing - X is "dummy" element
      return True
    for elem in elements :
      if (not elem.strip().upper() in SUPPORTED) :
        raise Sorry(
          ("Identification of ions with element symbol '%s' is not supported! "+
          "Choices are: %s") % (elem, " ".join(SUPPORTED)))
  return True

# global parameter_server instance
server = parameter_server()
