
"""
Module for querying the RCSB web server using the REST API, as described here:
http://www.rcsb.org/pdb/software/rest.do

There is some overlap with iotbx.pdb.fetch, which really should have gone here
instead, but this module is intended to be used in higher-level automation
pipelines.
"""

from __future__ import division
from xml.dom.minidom import parseString
import urllib
import sys

url_base = "http://www.rcsb.org/pdb/rest"
url_search = url_base + "/search"

def post_query (query_xml, xray_only=True, d_max=None, d_min=None,
    protein_only=False) :
  """Generate the full XML for a multi-part query with generic search options,
  starting from the basic query passed by another function, post it to the
  RCSB's web service, and return a list of matching PDB IDs."""
  other_queries = []
  if (xray_only) :
    other_queries.append(
      "<queryType>org.pdb.query.simple.ExpTypeQuery</queryType>\n" +
      "<mvStructure.expMethod.value>X-RAY</mvStructure.expMethod.value>")
  if (d_max is not None) or (d_min is not None) :
    base_clause = "<queryType>org.pdb.query.simple.ResolutionQuery</queryType>"
    base_clause += "\n<refine.ls_d_res_high.comparator>between" + \
      "</refine.ls_d_res_high.comparator>"
    if (d_min is not None) :
      assert (d_min >= 0)
      base_clause += \
        "\n<refine.ls_d_res_high.min>%f</refine.ls_d_res_high.min>" % d_min
    if (d_max is not None) :
      assert (d_max >= 0)
      base_clause += \
        "\n<refine.ls_d_res_high.max>%f</refine.ls_d_res_high.max>" % d_max
    other_queries.append(base_clause)
  if (protein_only) :
    other_queries.append(
      "<queryType>org.pdb.query.simple.ChainTypeQuery</queryType>\n" +
      "<containsProtein>Y</containsProtein>")
  other_queries_full = ""
  if (len(other_queries) > 0) :
    k = 1
    for other in other_queries :
      other_queries_full += """\
        <queryRefinement>
          <queryRefinementLevel>%d</queryRefinementLevel>
          <conjunctionType>and</conjunctionType>
          <orgPdbQuery>
            %s
          </orgPdbQuery>
        </queryRefinement>""" % (k, other)
      k += 1
  query_str = """\
<orgPdbCompositeQuery version="1.0">
 <queryRefinement>
  <queryRefinementLevel>0</queryRefinementLevel>
  <orgPdbQuery>
  %s
  </orgPdbQuery>
 </queryRefinement>
  %s
</orgPdbCompositeQuery>
""" % (query_xml, other_queries_full)
  parsed = parseString(query_str)
  result = urllib.urlopen(url_search, query_str).read()
  return result.splitlines()

def sequence_search (sequence, **kwds) :
  search_type = kwds.pop("search_type", "blast")
  expect = kwds.pop("expect", 0.01)
  """
  Homology search for an amino acid sequence.  The advantage of using this
  service over the NCBI/EBI BLAST servers (in iotbx.pdb.fetch) is the ability
  to exclude non-Xray structures.
  """
  assert (search_type in ["blast", "fasta", "psiblast"])
  query_str = """\
    <queryType>org.pdb.query.simple.SequenceQuery</queryType>
      <description>Sequence Search (expect = %g, search = %s)</description>
      <sequence>%s</sequence>
      <eCutOff>%g</eCutOff>
    <searchTool>%s</searchTool>""" % (expect, search_type, sequence, expect,
      search_type)
  return post_query(query_str, **kwds)

def chemical_id_search (resname, **kwds) :
  """Find all entry IDs with the specified chemical ID."""
  assert (1 <= len(resname) <= 3)
  polymeric_type = kwds.pop("polymeric_type", "Any")
  assert (polymeric_type in ["Any", "Free", "Polymeric"])
  polymer_limit = ""# "<polymericType>%s</polymericType>" % polymeric_type
  query_str = """\
    <queryType>org.pdb.query.simple.ChemCompIdQuery</queryType>
    <description>Chemical ID: %s</description>
    <chemCompId>%s</chemCompId>
    %s""" % (resname, resname, polymer_limit)
  return post_query(query_str, **kwds)

def get_custom_report_table (pdb_ids, columns, log=sys.stdout) :
  """Given a list of PDB IDs and a list of attribute identifiers, returns a
  Python list of lists for the IDs and attributes."""
  assert (len(columns) > 0)
  if (len(pdb_ids) == 0) : return []
  url_base = "http://www.rcsb.org/pdb/rest/customReport?"
  url = url_base + "pdbids=%s" % ",".join(pdb_ids)
  all_columns = ["structureId"] + columns
  url += "&customReportColumns=%s" % ",".join(all_columns)
  result = urllib.urlopen(url).read()
  # The RCSB's custom report follows this format (using the high-resolution
  # limit as an example):
  #
  # <?xml version='1.0' standalone='no' ?>
  # <dataset>
  #   <record>
  #     <dimStructure.structureId>1A0I</dimStructure.structureId>
  #     <dimStructure.highResolutionLimit>2.6</dimStructure.highResolutionLimit>
  #   </record>
  # </dataset>
  xmlrec = parseString(result)
  table = []
  report_ids = set([])
  records = xmlrec.getElementsByTagName("record")
  for record in records :
    pdb_id_nodes = record.getElementsByTagName("dimStructure.structureId")
    assert (len(pdb_id_nodes) == 1)
    pdb_id = pdb_id_nodes[0].childNodes[0].data
    report_ids.add(pdb_id)
    row = [ pdb_id ] # pdb_id
    for col_name in columns :
      row_col = record.getElementsByTagName("dimStructure.%s" % col_name)
      assert (len(row_col) == 1)
      row.append(row_col[0].childNodes[0].data)
    table.append(row)
  missing_ids = set(pdb_ids) - report_ids
  if (len(missing_ids) > 0) :
    print >> log, "WARNING: missing report info for %d IDs:" % len(missing_ids)
    print >> log, "  %s" % " ".join(sorted(list(missing_ids)))
  return table

def get_high_resolution_for_structures (pdb_ids) :
  return get_custom_report_table(pdb_ids, columns=["highResolutionLimit"])
