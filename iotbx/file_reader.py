
# this will try to guess file type based on extensions.  since this will
# frequently break, it will also try every other file type if necessary,
# stopping when it finds an appropriate format.
#
# MTZ file handling is kludgy, but unfortunately there are circumstances
# where only an MTZ file will do, so it requires some extra code to work
# around the automatic behavior
#
# XXX note that there is some cross-importing from mmtbx here, but it is done
# inline, not globally

import sys, os, re, string
from libtbx import smart_open
from libtbx.utils import Sorry
import cPickle

standard_file_types = ["hkl", "ccp4_map", "xplor_map", "pdb", "cif", "phil",
  "seq", "xml", "pkl", "txt"]

standard_file_extensions = {
  'pdb'  : ["pdb", "ent"],
  'hkl'  : ["mtz", "hkl", "sca", "cns", "xplor", "cv", "ref", "fobs"],
  'cif'  : ["cif"],
  'seq'  : ["fa", "faa", "seq", "pir", "dat", "fasta"],
  'xplor_map' : ["xplor", "map"],
  'ccp4_map'  : ["ccp4", "map"],
  'phil' : ["params", "eff", "def", "phil"],
  'xml'  : ["xml"],
  'pkl'  : ["pickle", "pkl"],
  'txt'  : ["txt", "log", "html"],
  'mtz'  : ["mtz"],
}
compression_extensions = ["gz", "Z", "bz2", "zip"]

standard_file_descriptions = {
  'pdb'  : "Model",
  'hkl'  : "Reflections",
  'cif'  : "Restraints",
  'seq'  : "Sequence",
  'xplor_map'  : "XPLOR map",
  'ccp4_map' : "CCP4 map",
  'phil' : "Parameters",
  'xml'  : "XML",
  'pkl'  : "Python pickle",
  'txt'  : "Text",
  'mtz'  : "Reflections (MTZ)",
}

supported_file_types = ["pdb","hkl","cif","pkl","seq","phil", "txt",
  "xplor_map", "ccp4_map"]

class FormatError (Sorry) :
  pass

def splitext (file_name) :
  base, ext = os.path.splitext(file_name)
  if (ext == ".gz") :
    base, ext = os.path.splitext(base)
  return base, ext

def guess_file_type (file_name, extensions=standard_file_extensions) :
  base, ext = splitext(file_name)
  if (ext == "") :
    return None
  if (ext == ".mtz") : # XXX gross
    return "hkl"
  for known_type, known_extensions in extensions.iteritems() :
    if ext[1:] in known_extensions :
      return known_type
  return None

def sort_by_file_type (file_names, sort_order=None) :
  if (sort_order is None) :
    sort_order = standard_file_types
  def _score_extension (ext) :
    for n, format in enumerate(sort_order) :
      extensions = standard_file_extensions.get(format, [])
      if (ext[1:] in extensions) :
        return len(sort_order) - n
    return 0
  def _sort (f1, f2) :
    base1, ext1 = splitext(f1)
    base2, ext2 = splitext(f2)
    s1 = _score_extension(ext1)
    s2 = _score_extension(ext2)
    if (s1 > s2) :
      return -1
    elif (s2 > s1) :
      return 1
    else :
      return 0
  file_names.sort(_sort)
  return file_names

def any_file (file_name,
              get_processed_file=False,
              valid_types=supported_file_types,
              allow_directories=False,
              force_type=None,
              input_class=None) :
  if not os.path.exists(file_name) :
    raise Sorry("Couldn't find the file %s" % file_name)
  elif os.path.isdir(file_name) :
    if not allow_directories :
      raise Sorry("This application does not support folders as input.")
    else :
      return directory_input(file_name)
  elif not os.path.isfile(file_name) :
    raise Sorry("%s is not a valid file.")
  else :
    if input_class is None :
      input_class = any_file_input
    return input_class(file_name=file_name,
      get_processed_file=get_processed_file,
      valid_types=valid_types,
      force_type=force_type)

class any_file_input (object) :
  __extensions__ = standard_file_extensions
  __descriptions__ = standard_file_descriptions

  def __init__ (self, file_name, get_processed_file, valid_types, force_type) :
    self.valid_types = valid_types
    self.file_name = file_name
    self.file_object = None
    self.file_type = None
    self.file_server = None
    self.file_description = None
    self._cached_file = None # XXX: used in phenix.file_reader
    self._errors = {}
    self.file_size = os.path.getsize(file_name)
    self.get_processed_file = get_processed_file

    (file_base, file_ext) = os.path.splitext(file_name)
    if file_ext in [".gz"] : # XXX: does this work for anything other than pdb?
      (base2, ext2) = os.path.splitext(file_base)
      if ext2 != "" :
        file_ext = ext2
    if force_type is not None :
      read_method = getattr(self, "try_as_%s" % force_type, None)
      if read_method is None :
        raise Sorry("Couldn't force file type to '%s' - unrecognized format." %
                    force_type)
      else :
        read_method()
    else :
      for file_type in valid_types :
        if file_ext[1:] in self.__extensions__[file_type] :
          read_method = getattr(self, "try_as_%s" % file_type)
          try :
            read_method()
          except KeyboardInterrupt :
            raise
          except FormatError, e :
            raise e
          except Exception, e :
            self._errors[file_type] = str(e)
            self.file_type = None
            self.file_object = None
          else :
            break
      if self.file_type is None :
        self.try_all_types()
    if self.file_type is not None :
      self.file_description = self.__descriptions__[self.file_type]

  def try_as_pdb (self) :
    from iotbx.pdb import is_pdb_file
    if is_pdb_file(self.file_name) :
      from iotbx.pdb import input as pdb_input
      from scitbx.array_family import flex
      raw_records = flex.std_string()
      pdb_file = smart_open.for_reading(file_name=self.file_name)
      raw_records.extend(flex.split_lines(pdb_file.read()))
      structure = pdb_input(source_info=None, lines=raw_records)
      self.file_type = "pdb"
      self.file_object = structure

  def try_as_hkl (self) :
    from iotbx.reflection_file_reader import any_reflection_file
    from iotbx.reflection_file_utils import reflection_file_server
    try :
      hkl_file = any_reflection_file(self.file_name)
    except Exception, e :
      print e
      raise
    assert hkl_file.file_type() is not None
    self.file_server = reflection_file_server(
      crystal_symmetry=None,
      force_symmetry=True,
      reflection_files=[hkl_file],
      err=sys.stderr)
    self.file_type = "hkl"
    self.file_object = hkl_file

  def try_as_cif (self) :
    from mmtbx.monomer_library import server
    cif_object = server.read_cif(file_name=self.file_name)
    assert len(cif_object) != 0
    self.file_type = "cif"
    self.file_object = cif_object

  def try_as_phil (self) :
    from iotbx.phil import parse as parse_phil
    phil_object = parse_phil(file_name=self.file_name, process_includes=True)
    assert (len(phil_object.objects) > 0)
    self.file_type = "phil"
    self.file_object = phil_object

  def try_as_seq (self) :
    from iotbx.bioinformatics import any_sequence_format
    try :
      objects, non_compliant = any_sequence_format(self.file_name)
    except Exception, e :
      print e
      raise
    assert (objects is not None)
    #assert (len(non_compliant) == 0)
    self.file_object = objects
#    self.try_as_txt()
#    assert len(self.file_object) != 0
#    for _line in self.file_object.splitlines() :
#      assert not _line.startswith(" ")
#      line = re.sub(" ", "", _line)
#      assert ((len(line) == 0) or
#              (line[0] == ">") or
#              (line == "*") or
#              ((line[-1] == '*') and line[:-1].isalpha()) or
#              line.isalpha())
    self.file_type = "seq"

  def try_as_xplor_map (self) :
    import iotbx.xplor.map
    map_object = iotbx.xplor.map.reader(file_name=self.file_name)
    self.file_type = "xplor_map"
    self.file_object = map_object

  def try_as_ccp4_map (self) :
    import iotbx.ccp4_map
    map_object = iotbx.ccp4_map.map_reader(file_name=self.file_name)
    self.file_type = "ccp4_map"
    self.file_object = map_object

  def try_as_pkl (self) :
    pkl_object = cPickle.load(open(self.file_name, "rb"))
    self.file_type = "pkl"
    self.file_object = pkl_object

  def try_as_txt (self) :
    file_as_string = open(self.file_name).read()
    file_as_ascii = file_as_string.decode("ascii")
    self.file_type = "txt"
    self.file_object = file_as_string

  def try_all_types (self) :
    for filetype in self.valid_types :
      read_method = getattr(self, "try_as_%s" % filetype)
      try :
        read_method()
      except KeyboardInterrupt :
        raise
      except Exception, e :
        self._errors[filetype] = str(e)
        self.file_type = None
        self.file_object = None
        continue
      else :
        if self.file_type is not None :
          break

  def file_info (self, show_file_size=True) :
    file_size_str = ""
    if show_file_size :
      file_size = self.file_size
      if file_size > 10000000 :
        file_size_str = " (%.1f MB)" % (self.file_size / 1000000.0)
      elif file_size > 1000000 :
        file_size_str = " (%.2f MB)" % (self.file_size / 1000000.0)
      elif file_size > 100000 :
        file_size_str = " (%d KB)" % (self.file_size / 1000.0)
      elif file_size > 1000 :
        file_size_str = " (%.1f KB)" % (self.file_size / 1000.0)
      else :
        file_size_str = " (%d B)" % self.file_size
    if self.file_type == None :
      return "Unknown file%s" % file_size_str
    else :
      return "%s%s" % (self.__descriptions__[self.file_type],
        file_size_str)

  def assert_file_type (self, expected_type) :
    if (expected_type is None) :
      return None
    elif (self.file_type == expected_type) :
      return True
    else :
      raise Sorry(("Expected file type '%s' for %s, got '%s'.  This is " +
        "almost certainly a bug; please contact the developers.") %
        (str(self.file_name), expected_type, str(self.file_type)))

class directory_input (object) :
  def __init__ (self, dir_name) :
    self.file_name = dir_name
    self.file_object = dircache.listdir(dir_name)
    self.file_server = None
    self.file_type = "dir"
    self.file_size = os.path.getsize(dir_name)

  def file_info (self, show_file_size=False) :
    return "Folder"

class group_files (object) :
  def __init__ (self,
                file_names,
                template_format="pdb",
                group_by_directory=True) :
    import iotbx.pdb
    self.file_names = file_names
    self.grouped_files = []
    self.ungrouped_files = []
    self.ambiguous_files = []
    templates = []
    other_files = []
    template_dirs = []
    for file_name in file_names :
      file_type = guess_file_type(file_name)
      if (file_type == template_format) :
        base, ext = splitext(file_name)
        templates.append(base)
        template_dirs.append(os.path.dirname(file_name))
        self.grouped_files.append([file_name])
      else :
        other_files.append(file_name)
    if (len(templates) == 0) :
      raise Sorry("Can't find any files of the expected format ('%s')." %
        template_format)
    if (len(set(templates)) != len(templates)) :
      raise Sorry("Multiple files with identical root names.")
    for file_name in other_files :
      group_name = find_closest_base_name(
        file_name=file_name,
        base_name=splitext(file_name)[0],
        templates=templates)
      if (group_name == "") :
        self.ambiguous_files.append(file_name)
      elif (group_name is not None) :
        i = templates.index(group_name)
        self.grouped_files[i].append(file_name)
      else :
        if group_by_directory :
          dir_name = os.path.dirname(file_name)
          group_name = find_closest_base_name(
            file_name=dir_name,
            base_name=dir_name,
            templates=template_dirs)
          if (group_name == "") :
            self.ambiguous_files.append(file_name)
          elif (group_name is not None) :
            i = template_dirs.index(group_name)
            self.grouped_files[i].append(file_name)
          else :
            self.ungrouped_files.append(file_name)
        else :
          self.ungrouped_files.append(file_name)

def find_closest_base_name (file_name, base_name, templates) :
  groups = []
  for base in templates :
    if file_name.startswith(base) or base.startswith(base_name) :
      groups.append(base)
  if (len(groups) == 1) :
#    print file_name, groups[0]
    return groups[0]
  elif (len(groups) > 1) :
#    print file_name, groups
    prefix_len = [ os.path.commonprefix([g, file_name]) for g in groups ]
    max_common_prefix = max(prefix_len)
    if (prefix_len.count(max_common_prefix) > 1) :
      return ""
    else :
      return groups[ prefix_len.index(max_common_prefix) ]
  return None

#---end
