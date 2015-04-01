"""
PDBe RESTful web services API
"""

from __future__ import division

from iotbx.pdb.download import openurl, NotFound

import json

def get_request(url, identifier):

  lcase = identifier.lower()

  stream = openurl( url = ( url + lcase ).encode() )
  result_for = json.load( stream )
  assert lcase in result_for
  return result_for[ lcase ]


def multiple_get_requests(url, identifiers):

  for ident in identifiers:
    try:
      result = get_request( url = url, identifier = ident )

    except NotFound:
      yield None

    else:
      yield result


def post_request(url, identifiers):

  if len( identifiers ) == 0:
    return ( i for i in () )

  try:
    stream = openurl( url = url, data = ( ",".join( identifiers ) ).encode() )

  except NotFound:
    return ( None for i in identifiers )

  result_for = json.load( stream )

  return ( result_for.get( ident.lower() ) for ident in identifiers )


class RESTService(object):
  """
  Unified interface for services offering GET and POST requests
  """

  def __init__(self, url, get, post):

    self.url = url
    self.get = get
    self.post = post


  def single(self, identifier):

    return self.get( url = self.url, identifier = identifier )


  def multiple(self, identifiers):

    return self.post( url = self.url, identifiers = identifiers )


class FTPService(object):
  """
  Interface to access PDB files
  """

  def __init__(self, url, namer):

    self.url = url
    self.namer = namer


  def single(self, identifier):

    stream = openurl(
      url = ( self.url + self.namer( identifier = identifier ) ).encode(),
      )
    return stream


  def multiple(self, identifiers):

    for ident in identifiers:
      try:
        stream = openurl(
          url = ( self.url + self.namer( identifier = ident ) ).encode(),
          )

      except NotFound:
        yield None

      else:
        yield stream


def identifier_to_pdb_entry_name(identifier):

  return "pdb%s.ent" % identifier.lower()


def identifier_to_cif_entry_name(identifier):

  return "%s.cif" % identifier.lower()


PDB_ENTRYFILE_PDB = FTPService(
  url = "http://www.ebi.ac.uk/pdbe/entry-files/",
  namer = identifier_to_pdb_entry_name,
  )

PDB_ENTRYFILE_CIF = FTPService(
  url = "http://www.ebi.ac.uk/pdbe/entry-files/",
  namer = identifier_to_cif_entry_name,
  )

PDBE_API_BASE = "http://www.ebi.ac.uk/pdbe/api/"

PDB_ENTRY_STATUS = RESTService(
  url = PDBE_API_BASE + "pdb/entry/status/",
  get = get_request,
  post = post_request,
  )

PDB_SIFTS_MAPPING_CATH = RESTService(
  url = PDBE_API_BASE + "mappings/cath/",
  get = get_request,
  post = multiple_get_requests,
  )

PDB_SIFTS_MAPPING_SCOP = RESTService(
  url = PDBE_API_BASE + "mappings/scop/",
  get = get_request,
  post = multiple_get_requests,
  )


class Redirections(object):
  """
  Use status queries
  """

  def __init__(self):

    self._currents = set()
    self._retracteds = set()
    self._replaced_by = {}


  def obsoleted(self, identifier):

    std = self._check_and_fetch( identifier = identifier )
    return std in self._replaced_by


  def replacement_for(self, identifier):

    std = self._check_and_fetch( identifier = identifier )
    return self._replaced_by[ std ]


  def retracted(self, identifier):

    std = self._check_and_fetch( identifier = identifier )
    return std in self._retracteds


  def seed(self, identifiers):

    import itertools

    blocks = PDB_ENTRY_STATUS.multiple( identifiers = identifiers )

    for ( code, data ) in itertools.izip( identifiers, blocks ):
      if not data:
        continue

      self._insert( code = self._standardize( identifier = code ), data = data )


  def _standardize(self, identifier):

    return identifier.lower()


  def _check_and_fetch(self, identifier):

    std = self._standardize( identifier = identifier )

    if std in self._currents or std in self._retracteds or std in self._replaced_by:
      return std

    data = PDB_ENTRY_STATUS.single( identifier = std )
    self._insert( code = std, data = data )
    return std


  def _insert(self, code, data):

    status = data[0][ "status_code" ]

    if status == "REL":
      self._currents.add( code )

    elif status == "OBS":
      successor = data[0][ "superceded_by" ][0]

      if successor is None:
        self._retracteds.add( code )

      else:
        self._replaced_by[ code ] = successor


from libtbx.object_oriented_patterns import lazy_initialization
redirection = lazy_initialization( func = Redirections )
