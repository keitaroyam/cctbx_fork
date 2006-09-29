from __future__ import division
from __future__ import generators
from libtbx.phil import tokenizer
from libtbx.str_utils import line_breaker
from libtbx.utils import Sorry, format_exception, import_python_object
from libtbx.itertbx import count
from cStringIO import StringIO
import tokenize as python_tokenize
import math
import weakref
import sys, os

default_print_width = 79

def is_reserved_identifier(string):
  if (len(string) < 5): return False
  return (string.startswith("__") and string.endswith("__"))

standard_identifier_start_characters = {}
for c in "_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz":
  standard_identifier_start_characters[c] = None
standard_identifier_continuation_characters = dict(
  standard_identifier_start_characters)
for c in ".0123456789":
  standard_identifier_continuation_characters[c] = None

def is_standard_identifier(string):
  if (len(string) == 0): return False
  if (string[0] not in standard_identifier_start_characters): return False
  for c in string[1:]:
    if (c not in standard_identifier_continuation_characters): return False
  sub_strings = string.split(".")
  if (len(sub_strings) > 1):
    for sub in sub_strings:
      if (not is_standard_identifier(sub)): return False
  return True

class words_converters(object):

  def __str__(self): return "words"

  def from_words(self, words, master):
    if (len(words) == 1
        and words[0].quote_token is None
        and words[0].value.lower() == "none"):
      return None
    return words

  def as_words(self, python_object, master):
    if (python_object is None):
      return [tokenizer.word(value="None")]
    for word in python_object:
      assert isinstance(word, tokenizer.word)
    return python_object

def strings_from_words(words):
  if (len(words) == 1
      and words[0].quote_token is None
      and words[0].value.lower() == "none"):
    return None
  return [word.value for word in words]

def strings_as_words(python_object):
  if (python_object is None):
    return [tokenizer.word(value="None")]
  words = []
  for value in python_object:
    if (is_standard_identifier(value)):
      words.append(tokenizer.word(value=value))
    else:
      words.append(tokenizer.word(value=value, quote_token='"'))
  return words

class strings_converters(object):

  def __str__(self): return "strings"

  def from_words(self, words, master):
    return strings_from_words(words)

  def as_words(self, python_object, master):
    return strings_as_words(python_object)

def str_from_words(words):
  if (len(words) == 1 and words[0].value.lower() == "none"):
    return None
  return " ".join([word.value for word in words])

class str_converters(object):

  def __str__(self): return "str"

  def from_words(self, words, master):
    return str_from_words(words=words)

  def as_words(self, python_object, master):
    if (python_object is None):
      return [tokenizer.word(value="None")]
    return [tokenizer.word(value=python_object, quote_token='"')]

class path_converters(str_converters):

  def __str__(self): return "path"

class key_converters(str_converters):

  def __str__(self): return "key"

def bool_from_words(words):
  value_string = str_from_words(words)
  if (value_string is None): return None
  word_lower = words[0].value.lower()
  if (word_lower == "none"): return None
  if (word_lower in ["false", "no", "off", "0"]): return False
  if (word_lower in ["true", "yes", "on", "1"]): return True
  assert len(words) > 0
  raise RuntimeError(
    'One True or False value expected, "%s" found%s' % (
      value_string, words[0].where_str()))

class bool_converters(object):

  def __str__(self): return "bool"

  def from_words(self, words, master):
    return bool_from_words(words)

  def as_words(self, python_object, master):
    if (python_object is None):
      return [tokenizer.word(value="None")]
    if (python_object):
      return [tokenizer.word(value="True")]
    else:
      return [tokenizer.word(value="False")]

def number_from_words(words):
  value_string = str_from_words(words)
  if (value_string is None): return None
  try: return eval(value_string, math.__dict__, {})
  except KeyboardInterrupt: raise
  except:
    raise RuntimeError(
      'Error interpreting "%s" as a numeric expression: %s%s' % (
        value_string, format_exception(), words[0].where_str()))

def int_from_words(words):
  result = number_from_words(words)
  if (result is not None):
    if (isinstance(result, float)
        and round(result) == result):
      result = int(result)
    elif (not isinstance(result, int)):
      raise RuntimeError(
        'Integer expression expected, "%s" found%s' % (
          str_from_words(words),
          words[0].where_str()))
  return result

class int_converters(object):

  def __str__(self): return "int"

  def from_words(self, words, master):
    return int_from_words(words)

  def as_words(self, python_object, master):
    if (python_object is None):
      return [tokenizer.word(value="None")]
    return [tokenizer.word(value=str(python_object))]

def float_from_words(words):
  result = number_from_words(words)
  if (result is not None):
    if (isinstance(result, int)):
      result = float(result)
    elif (not isinstance(result, float)):
      raise RuntimeError(
        'Floating-point expression expected, "%s" found%s' % (
          str_from_words(words),
          words[0].where_str()))
  return result

class float_converters(object):

  def __str__(self): return "float"

  def from_words(self, words, master):
    return float_from_words(words)

  def as_words(self, python_object, master):
    if (python_object is None):
      return [tokenizer.word(value="None")]
    return [tokenizer.word(value="%.10g" % python_object)]

class choice_converters(object):

  def __init__(self, multi=False):
    self.multi = multi

  def __str__(self):
    if (self.multi): return "choice(multi=True)"
    return "choice"

  def from_words(self, words, master):
    if (self.multi):
      result = []
      for word in words:
        if (word.value.startswith("*")):
          result.append(word.value[1:])
    else:
      result = None
      for word in words:
        if (word.value.startswith("*")):
          if (result is not None):
            raise RuntimeError(
              "Multiple choices for %s; only one is possible%s" % (
                master.full_path(), words[0].where_str()))
          result = word.value[1:]
      if (result is None and not master.optional):
        raise RuntimeError("Unspecified choice for %s%s" % (
          master.full_path(), words[0].where_str()))
    return result

  def as_words(self, python_object, master):
    n_choices = 0
    if (python_object is not None):
      words = []
      for word in master.words:
        if (word.value.startswith("*")): value = word.value[1:]
        else: value = word.value
        if (not self.multi):
          if (value == python_object):
            value = "*" + value
            n_choices += 1
            if (n_choices > 1):
              raise RuntimeError("Improper master choice definition: %s%s" % (
                master.as_str().rstrip(), master.words[0].where_str()))
        else:
          if (value in python_object):
            value = "*" + value
            n_choices += 1
        words.append(tokenizer.word(
          value=value, quote_token=word.quote_token))
    if (n_choices == 0
        and (not master.optional or python_object is not None)):
      raise RuntimeError("Not a valid choice: %s=%s" % (
        master.full_path(), str(python_object)))
    if (python_object is None):
      return [tokenizer.word(value="None")]
    return words

  def fetch(self, source_words, master):
    flags = {}
    for word in master.words:
      if (word.value.startswith("*")): value = word.value[1:]
      else: value = word.value
      flags[value] = False
    have_quote_or_star = False
    have_plus = False
    for word in source_words:
      if (word.quote_token is not None or word.value.startswith("*")):
        have_quote_or_star = True
        break
      if (word.value.find("+") >= 0):
        have_plus = True
    process_plus = False
    if (not have_quote_or_star and have_plus):
      values = "".join([word.value for word in source_words]).split("+")
      for value in values[1:]:
        if (len(value.strip()) == 0):
          break
      else:
        process_plus = True
    if (process_plus):
      for word in source_words:
        for value in word.value.split("+"):
          if (len(value) == 0): continue
          if (value not in flags):
            raise Sorry("Not a possible choice for %s: %s%s" % (
              master.full_path(), value, word.where_str()))
          flags[value] = True
    else:
      for word in source_words:
        if (word.value.startswith("*")):
          value = word.value[1:]
          flag = True
        else:
          value = word.value
          if (len(source_words) == 1):
            flag = True
          else:
            flag = False
        if (flag and value not in flags):
          raise Sorry("Not a possible choice for %s: %s%s" % (
            master.full_path(), str(word), word.where_str()))
        flags[value] = flag
    words = []
    for word in master.words:
      if (word.value.startswith("*")): value = word.value[1:]
      else: value = word.value
      if (flags[value]): value = "*" + value
      words.append(tokenizer.word(
        value=value,
        line_number=word.line_number,
        source_info=word.source_info))
    return master.customized_copy(words=words)

default_converter_registry = dict([(str(converters()), converters)
  for converters in [
     words_converters,
     strings_converters,
     str_converters,
     path_converters,
     key_converters,
     bool_converters,
     int_converters,
     float_converters,
     choice_converters]])

def extract_args(*args, **keyword_args):
  return args, keyword_args

def normalize_call_expression(expression):
  result = []
  p = ""
  for info in python_tokenize.generate_tokens(StringIO(expression).readline):
    t = info[1]
    if (len(t) == 0): continue
    if (    t != "."
        and t[0] in standard_identifier_start_characters
        and len(p) > 0
        and p != "."
        and p[-1] in standard_identifier_continuation_characters):
      result.append(" ")
    result.append(t)
    if (t[0] == ","):
      result.append(" ")
    p = t
  return "".join(result)

def definition_converters_from_words(
      words,
      converter_registry,
      converter_cache):
  name = words[0].value
  if (len(words) == 1
      and name.lower() == "none" and words[0].quote_token is None):
    return None
  call_expression_raw = str_from_words(words).strip()
  try:
    call_expression = normalize_call_expression(expression=call_expression_raw)
  except python_tokenize.TokenError, e:
    raise RuntimeError(
      'Error evaluating definition type "%s": %s%s' % (
        call_expression_raw, str(e), words[0].where_str()))
  converters_weakref = converter_cache.get(call_expression, None)
  if (converters_weakref is not None):
    converters_instance = converters_weakref()
    if (converters_instance is not None):
      return converters_instance
  flds = call_expression.split("(", 1)
  converters = converter_registry.get(flds[0], None)
  if (converters is not None):
    if (len(flds) == 1): parens = "()"
    else:                parens = ""
    try:
      converters_instance = eval(
        call_expression+parens, math.__dict__, {flds[0]: converters})
    except KeyboardInterrupt: raise
    except:
      raise RuntimeError(
        'Error constructing definition type "%s": %s%s' % (
        call_expression, format_exception(), words[0].where_str()))
  else:
    import_path = flds[0] + "_phil_converters"
    if (len(flds) == 1):
      keyword_args = {}
    else:
      extractor = "__extract_args__(" + flds[1]
      try:
        args, keyword_args = eval(
          extractor, math.__dict__, {"__extract_args__": extract_args})
      except KeyboardInterrupt: raise
      except:
        raise RuntimeError(
          'Error evaluating definition type "%s": %s%s' % (
          call_expression, format_exception(), words[0].where_str()))
    try:
      imported = import_python_object(
        import_path=import_path,
        error_prefix='.type=%s: ' % call_expression,
        target_must_be="; target must be a callable Python object",
        where_str=words[0].where_str())
    except (ValueError, ImportError):
      raise RuntimeError(
        'Unexpected definition type: "%s"%s' % (
          call_expression, words[0].where_str()))
    if (not callable(imported.object)):
      raise TypeError(
        '"%s" is not a callable Python object%s' % (
          import_path, words[0].where_str()))
    try:
      converters_instance = imported.object(**keyword_args)
    except KeyboardInterrupt: raise
    except:
      raise RuntimeError(
        'Error constructing definition type "%s": %s%s' % (
        call_expression, format_exception(), words[0].where_str()))
  converter_cache[call_expression] = weakref.ref(converters_instance)
  return converters_instance

def full_path(self):
  result = [self.name]
  pps = self.primary_parent_scope
  while (pps is not None):
    if (pps.name == ""): break
    result.append(pps.name)
    pps = pps.primary_parent_scope
  result.reverse()
  return ".".join(result)

def show_attributes(self, out, prefix, attributes_level, print_width):
  if (attributes_level <= 0): return
  for name in self.attribute_names:
    value = getattr(self, name)
    if ((name == "help" and value is not None)
        or (value is not None and attributes_level > 1)
        or attributes_level > 2):
      if (not isinstance(value, str)):
        # Python 2.2 workaround
        if (name in ["optional", "multiple", "disable_add", "disable_delete"]):
          if   (value is False): value = "False"
          elif (value is True):  value = "True"
        print >> out, prefix+"  ."+name, "=", value
      else:
        indent = " " * (len(prefix) + 3 + len(name) + 3)
        fits_on_one_line = len(indent+value) < print_width
        if (not is_standard_identifier(value) or not fits_on_one_line):
          value = str(tokenizer.word(value=value, quote_token='"'))
          fits_on_one_line = len(indent+value) < print_width
        if (fits_on_one_line):
          print >> out, prefix+"  ."+name, "=", value
        else:
          is_first = True
          for block in line_breaker(value[1:-1], print_width-2-len(indent)):
            if (is_first):
              print >> out, prefix+"  ."+name, "=", '"'+block+'"'
              is_first = False
            else:
              print >> out, indent+'"'+block+'"'

class object_locator(object):

  def __init__(self, parent, path, object):
    self.parent = parent
    self.path = path
    self.object = object

  def __str__(self):
    return "%s%s" % (self.path, self.object.where_str)

class definition: # FUTURE definition(object)

  attribute_names = [
    "help", "caption", "short_caption", "optional",
    "type", "multiple", "input_size", "expert_level"]

  __slots__ = ["name", "words", "primary_id", "primary_parent_scope",
               "is_disabled", "where_str", "merge_names", "tmp"] \
              + attribute_names

  def __init__(self,
        name,
        words,
        primary_id=None,
        primary_parent_scope=None,
        is_disabled=False,
        where_str="",
        merge_names=False,
        tmp=None,
        help=None,
        caption=None,
        short_caption=None,
        optional=None,
        type=None,
        multiple=None,
        input_size=None,
        expert_level=None):
    if (is_reserved_identifier(name)):
      raise RuntimeError('Reserved identifier: "%s"%s' % (name, where_str))
    if (name != "include" and "include" in name.split(".")):
      raise RuntimeError('Reserved identifier: "include"%s' % where_str)
    self.name = name
    self.words = words
    self.primary_id = primary_id
    self.primary_parent_scope = primary_parent_scope
    self.is_disabled = is_disabled
    self.where_str = where_str
    self.merge_names = merge_names
    self.tmp = tmp
    self.help = help
    self.caption = caption
    self.short_caption = short_caption
    self.optional = optional
    self.type = type
    self.multiple = multiple
    self.input_size = input_size
    self.expert_level = expert_level

  def copy(self):
    keyword_args = {}
    for keyword in self.__slots__:
      keyword_args[keyword] = getattr(self, keyword)
    return definition(**keyword_args)

  def customized_copy(self, name=None, words=None):
    result = self.copy()
    if (name is not None): result.name = name
    if (words is not None): result.words = words
    return result

  def full_path(self):
    return full_path(self)

  def assign_tmp(self, value, active_only=False):
    if (not active_only or not self.is_disabled):
      self.tmp = value

  def fetch(self, source, disable_empty=True):
    if (not isinstance(source, definition)):
      raise RuntimeError('Incompatible parameter objects "%s"%s and "%s"%s' %
        (self.name, self.where_str, source.name, source.where_str))
    source.tmp = True
    source = source.resolve_variables()
    type_fetch = getattr(self.type, "fetch", None)
    if (type_fetch is None):
      return self.customized_copy(words=source.words)
    return type_fetch(source_words=source.words, master=self)

  def has_attribute_with_name(self, name):
    return name in self.attribute_names

  def assign_attribute(self, name, words, converter_registry, converter_cache):
    assert self.has_attribute_with_name(name)
    if (name in ["optional", "multiple"]):
      value = bool_from_words(words)
    elif (name == "type"):
      value = definition_converters_from_words(
        words=words,
        converter_registry=converter_registry,
        converter_cache=converter_cache)
    elif (name in ["input_size", "expert_level"]):
      value = int_from_words(words)
    else:
      value = str_from_words(words)
    setattr(self, name, value)

  def show(self,
        out=None,
        merged_names=[],
        prefix="",
        expert_level=None,
        attributes_level=0,
        print_width=None):
    if (self.expert_level is not None
        and expert_level is not None
        and expert_level >= 0
        and self.expert_level > expert_level): return
    if (out is None): out = sys.stdout
    if (print_width is None): print_width = default_print_width
    if (self.is_disabled): hash = "!"
    else:                  hash = ""
    line = prefix + hash + ".".join(merged_names + [self.name])
    if (self.name != "include"): line += " ="
    indent = " " * len(line)
    for word in self.words:
      line_plus = line + " " + str(word)
      if (len(line_plus) > print_width-2 and len(line) > len(indent)):
        print >> out, line + " \\"
        line = indent + " " + str(word)
      else:
        line = line_plus
    print >> out, line
    show_attributes(
      self=self,
      out=out,
      prefix=prefix,
      attributes_level=attributes_level,
      print_width=print_width)

  def as_str(self,
        prefix="",
        expert_level=None,
        attributes_level=0,
        print_width=None):
    out = StringIO()
    self.show(
      out=out,
      prefix=prefix,
      expert_level=expert_level,
      attributes_level=attributes_level,
      print_width=print_width)
    return out.getvalue()

  def all_definitions_are_none(self):
    if (self.name == "include"): return False
    return self.extract() is None

  def _all_definitions(self,
        suppress_multiple,
        select_tmp,
        parent,
        parent_path,
        result):
    if (suppress_multiple and self.multiple): return
    if (select_tmp is not None and not (self.tmp == select_tmp)): return
    if (self.name == "include"): return
    result.append(object_locator(
      parent=parent, path=parent_path+self.name, object=self))

  def get_without_substitution(self, path):
    if (self.is_disabled or self.name != path): return []
    return [self]

  def extract(self, parent=None):
    if (self.type is None):
      return strings_from_words(words=self.words)
    try: type_from_words = self.type.from_words
    except AttributeError:
      raise RuntimeError('.type=%s does not have a from_words method%s: %s' %
        (str(self.type), self.where_str, format_exception()))
    return type_from_words(self.words, master=self)

  def format(self, python_object):
    if (self.type is None):
      words = strings_as_words(python_object=python_object)
    else:
      try: type_as_words = self.type.as_words
      except AttributeError:
        raise RuntimeError('.type=%s does not have an as_words method%s: %s' %
          (str(self.type), self.where_str, format_exception()))
      words = type_as_words(python_object=python_object, master=self)
    return self.customized_copy(words=words)

  def unique(self):
    return self

  def resolve_variables(self):
    new_words = []
    for word in self.words:
      if (word.quote_token == "'"):
        new_words.append(word)
        continue
      substitution_proxy = variable_substitution_proxy(word)
      for fragment in substitution_proxy.fragments:
        if (not fragment.is_variable):
          fragment.result = tokenizer.word(
            value=fragment.value, quote_token='"')
          continue
        variable_words = None
        if (self.primary_parent_scope is not None):
          substitution_source = self.primary_parent_scope.lexical_get(
            path=fragment.value, stop_id=self.primary_id)
          if (substitution_source is not None):
            if (not isinstance(substitution_source, definition)):
              raise RuntimeError("Not a definition: $%s%s" % (
                fragment.value, word.where_str()))
            substitution_source.tmp = True
            variable_words = substitution_source.resolve_variables().words
        if (variable_words is None):
          env_var = os.environ.get(fragment.value, None)
          if (env_var is not None):
            variable_words = [tokenizer.word(
              value=env_var,
              quote_token='"',
              source_info='environment: "%s"'%fragment.value)]
        if (variable_words is None):
          raise RuntimeError("Undefined variable: $%s%s" % (
            fragment.value, word.where_str()))
        if (not substitution_proxy.force_string):
          fragment.result = variable_words
        else:
          fragment.result = tokenizer.word(
            value=" ".join([word.value for word in variable_words]),
            quote_token='"')
      new_words.extend(substitution_proxy.get_new_words())
    return self.customized_copy(words=new_words)

class scope_extract_call_proxy_object:

  def __init__(self, where_str, expression, callable, keyword_args):
    self.where_str = where_str
    self.expression = expression
    self.callable = callable
    self.keyword_args = keyword_args

  def __str__(self):
    return self.expression

def scope_extract_call_proxy(full_path, words, cache):
  name = words[0].value
  if (len(words) == 1
      and name.lower() == "none" and words[0].quote_token is None):
    return None
  call_expression_raw = str_from_words(words).strip()
  try:
    call_expression = normalize_call_expression(expression=call_expression_raw)
  except python_tokenize.TokenError, e:
    raise RuntimeError('scope "%s" .call=%s: %s%s' % (
      full_path, call_expression_raw, str(e), words[0].where_str()))
  call_proxy = cache.get(call_expression, None)
  if (call_proxy is None):
    where_str = words[0].where_str()
    flds = call_expression.split("(", 1)
    import_path = flds[0]
    if (len(flds) == 1):
      keyword_args = {}
    else:
      extractor = "__extract_args__(" + flds[1]
      try:
        args, keyword_args = eval(
          extractor, math.__dict__, {"__extract_args__": extract_args})
      except KeyboardInterrupt: raise
      except:
        raise RuntimeError('scope "%s" .call=%s: %s%s' % (
          full_path, call_expression, format_exception(), where_str))
    imported = import_python_object(
      import_path=import_path,
      error_prefix='scope "%s" .call: ' % full_path,
      target_must_be="; target must be a callable Python object",
      where_str=where_str)
    if (not callable(imported.object)):
      raise TypeError(
        'scope "%s" .call: "%s" is not a callable Python object%s' % (
          full_path, import_path, where_str))
    call_proxy = scope_extract_call_proxy_object(
      where_str=where_str,
      expression=call_expression,
      callable=imported.object,
      keyword_args=keyword_args)
    cache[call_expression] = call_proxy
  return call_proxy

class scope_extract_attribute_error(object): pass
class scope_extract_is_disabled(object): pass

class scope_extract_list(list):

  def __init__(self, optional):
    self.__phil_optional__ = optional
    list.__init__(self)

class scope_extract(object):

  def __init__(self, name, parent, call):
    object.__setattr__(self, "__phil_name__", name)
    object.__setattr__(self, "__phil_parent__", parent)
    object.__setattr__(self, "__phil_call__", call)

  def __phil_path__(self):
    if (   self.__phil_parent__ is None
        or self.__phil_parent__.__phil_name__ is None
        or self.__phil_parent__.__phil_name__ == ""):
      return self.__phil_name__
    return ".".join([self.__phil_parent__.__phil_path__(),
                     self.__phil_name__])

  def __setattr__(self, name, value):
    if (getattr(self, name, scope_extract_attribute_error)
          is scope_extract_attribute_error):
      pp = self.__phil_path__()
      if (pp == ""): pp = name
      else:          pp += "." + name
      raise AttributeError(
        'Assignment to non-existing attribute "%s"\n' % pp
          + '  Please correct the attribute name, or to create\n'
          + '  a new attribute use: obj.__inject__(name, value)')
    object.__setattr__(self, name, value)

  def __inject__(self, name, value):
    if (getattr(self, name, scope_extract_attribute_error)
          is not scope_extract_attribute_error):
      pp = self.__phil_path__()
      if (pp == ""): pp = name
      else:          pp += "." + name
      raise AttributeError(
        'Attribute "%s" exists already.' % pp)
    object.__setattr__(self, name, value)

  def __phil_join__(self, other):
    for key,other_value in other.__dict__.items():
      if (is_reserved_identifier(key)): continue
      self_value = self.__dict__.get(key, None)
      if (self_value is None):
        self.__dict__[key] = other_value
      elif (isinstance(self_value, scope_extract_list)):
        assert isinstance(other_value, scope_extract_list)
        for item in other_value:
          if (item is not None):
            self_value.append(item)
        if (len(self_value) > 1 and self_value[0] is None):
          del self_value[0]
      else:
        self_value_phil_join = getattr(self_value, "__phil_join__", None)
        if (self_value_phil_join is None):
          self.__dict__[key] = other_value
        else:
          self_value_phil_join(other_value)

  def __phil_set__(self, name, optional, multiple, value):
    assert not "." in name
    node = getattr(self, name, scope_extract_attribute_error)
    if (not multiple):
      if (value is scope_extract_is_disabled):
        value = None
      if (node is scope_extract_attribute_error
          or not isinstance(value, scope_extract)
          or not isinstance(node, scope_extract)):
        object.__setattr__(self, name, value)
      else:
        node.__phil_join__(value)
    else:
      if (node is scope_extract_attribute_error):
        node = scope_extract_list(optional=optional)
        object.__setattr__(self, name, node)
      if (not value is scope_extract_is_disabled
          and (value is not None or optional is not True)):
        node.append(value)

  def __phil_get__(self, name):
    assert not "." in name
    return getattr(self, name, scope_extract_attribute_error)

  def __phil_is_empty__(self):
    for name,value in self.__dict__.items():
      if (value is None): continue
      if (name.startswith("__") and name.endswith("__")): continue
      if (isinstance(value, scope_extract)):
        if (not value.__phil_is_empty__()): return False
      if (isinstance(value, list) and len(value) == 0): continue
      return False
    return True

  def __call__(self, **keyword_args):
    call_proxy = self.__phil_call__
    if (call_proxy is None):
      raise RuntimeError('scope "%s" is not callable.' % self.__phil_path__())
    if (len(keyword_args) == 0):
      return call_proxy.callable(self, **call_proxy.keyword_args)
    effective_keyword_args = dict(call_proxy.keyword_args)
    effective_keyword_args.update(keyword_args)
    try:
      return call_proxy.callable(self, **effective_keyword_args)
    except KeyboardInterrupt: raise
    except:
      raise RuntimeError('scope "%s" .call=%s execution: %s%s' % (
        self.__phil_path__(), call_proxy.expression, format_exception(),
        call_proxy.where_str))

class scope: # FUTURE scope(object)

  attribute_names = [
    "style",
    "help",
    "caption",
    "short_caption",
    "optional",
    "call",
    "multiple",
    "sequential_format",
    "disable_add",
    "disable_delete",
    "expert_level"]

  __slots__ = [
    "name",
    "objects",
    "primary_id",
    "primary_parent_scope",
    "is_disabled",
    "where_str",
    "merge_names"] + attribute_names

  def __init__(self,
        name,
        objects=None,
        primary_id=None,
        primary_parent_scope=None,
        is_disabled=False,
        where_str="",
        merge_names=False,
        style=None,
        help=None,
        caption=None,
        short_caption=None,
        optional=None,
        call=None,
        multiple=None,
        sequential_format=None,
        disable_add=None,
        disable_delete=None,
        expert_level=None):
    self.name = name
    self.objects = objects
    self.primary_id = primary_id
    self.primary_parent_scope = primary_parent_scope
    self.is_disabled = is_disabled
    self.where_str = where_str
    self.merge_names = merge_names
    self.style = style
    self.help = help
    self.caption = caption
    self.short_caption = short_caption
    self.optional = optional
    self.call = call
    self.multiple = multiple
    self.sequential_format = sequential_format
    self.disable_add = disable_add
    self.disable_delete = disable_delete
    self.expert_level = expert_level
    if (objects is None):
      self.objects = []
    assert style in [None, "row", "column", "block", "page"]
    if (is_reserved_identifier(name)):
      raise RuntimeError('Reserved identifier: "%s"%s' % (name, where_str))
    if ("include" in name.split(".")):
      raise RuntimeError('Reserved identifier: "include"%s' % where_str)
    if (sequential_format is not None):
      assert isinstance(sequential_format % 0, str)

  def copy(self):
    keyword_args = {}
    for keyword in self.__slots__:
      keyword_args[keyword] = getattr(self, keyword)
    return scope(**keyword_args)

  def customized_copy(self, name=None, objects=None):
    result = self.copy()
    if (name is not None): result.name = name
    if (objects is not None): result.objects = objects
    return result

  def full_path(self):
    return full_path(self)

  def assign_tmp(self, value, active_only=False):
    if (not active_only):
      for object in self.objects:
        object.assign_tmp(value=value)
    else:
      for object in self.objects:
        if (self.is_disabled): continue
        object.assign_tmp(value=value, active_only=True)

  def adopt(self, object):
    assert len(object.name) > 0
    primary_parent_scope = self
    name_components = object.name.split(".")
    merge_names = False
    for name in name_components[:-1]:
      child_scope = scope(name=name)
      child_scope.merge_names = merge_names
      primary_parent_scope.adopt(child_scope)
      primary_parent_scope = child_scope
      merge_names = True
    if (len(name_components) > 1):
      object.name = name_components[-1]
      object.merge_names = True
    object.primary_parent_scope = primary_parent_scope
    primary_parent_scope.objects.append(object)

  def change_primary_parent_scope(self, new_value):
    objects = []
    for object in self.objects:
      obj = object.copy()
      obj.primary_parent_scope = new_value
      objects.append(obj)
    return self.customized_copy(objects=objects)

  def has_attribute_with_name(self, name):
    return name in self.attribute_names

  def assign_attribute(self, name, words, scope_extract_call_proxy_cache):
    assert self.has_attribute_with_name(name)
    if (name in ["optional", "multiple", "disable_add", "disable_delete"]):
      value = bool_from_words(words)
    elif (name == "expert_level"):
      value = int_from_words(words)
    elif (name == "call"):
      value = scope_extract_call_proxy(
        full_path=self.full_path(),
        words=words,
        cache=scope_extract_call_proxy_cache)
    else:
      value = str_from_words(words)
      if (name == "style"):
        style = value
        assert style in [None, "row", "column", "block", "page"]
      elif (name == "sequential_format"):
        sequential_format = value
        if (sequential_format is not None):
          assert isinstance(sequential_format % 0, str)
    setattr(self, name, value)

  def active_objects(self):
    for object in self.objects:
      if (object.is_disabled): continue
      yield object

  def master_active_objects(self):
    flags = {}
    for object in self.objects:
      if (object.is_disabled): continue
      if (flags.get(object.name, False)): continue
      flags[object.name] = object.multiple
      yield object

  def show(self,
        out=None,
        merged_names=[],
        prefix="",
        expert_level=None,
        attributes_level=0,
        print_width=None):
    if (self.expert_level is not None
        and expert_level is not None
        and expert_level >= 0
        and self.expert_level > expert_level): return
    if (out is None): out = sys.stdout
    if (print_width is None): print_width = default_print_width
    is_proper_scope = False
    if (len(self.name) == 0):
      assert len(merged_names) == 0
    elif (len(self.objects) == 1 and self.objects[0].merge_names):
      merged_names = merged_names + [self.name]
    else:
      is_proper_scope = True
      if (self.is_disabled): hash = "!"
      else:                  hash = ""
      out_attributes = StringIO()
      show_attributes(
        self=self,
        out=out_attributes,
        prefix=prefix,
        attributes_level=attributes_level,
        print_width=print_width)
      out_attributes = out_attributes.getvalue()
      merged_name = ".".join(merged_names + [self.name])
      merged_names = []
      if (len(out_attributes) == 0):
        print >> out, prefix + hash + merged_name, "{"
      else:
        print >> out, prefix + hash + merged_name
        out.write(out_attributes)
        print >> out, prefix+"{"
      prefix += "  "
    for object in self.objects:
      object.show(
        out=out,
        merged_names=merged_names,
        prefix=prefix,
        expert_level=expert_level,
        attributes_level=attributes_level,
        print_width=print_width)
    if (is_proper_scope):
      print >> out, prefix[:-2] + "}"

  def as_str(self,
        prefix="",
        expert_level=None,
        attributes_level=0,
        print_width=None):
    out = StringIO()
    self.show(
      out=out,
      prefix=prefix,
      expert_level=expert_level,
      attributes_level=attributes_level,
      print_width=print_width)
    return out.getvalue()

  def all_definitions_are_none(self):
    for obj_loc in self.all_definitions():
      if (obj_loc.object.extract() is not None):
        return False
    return True

  def _all_definitions(self,
        suppress_multiple,
        select_tmp,
        parent,
        parent_path,
        result):
    parent_path += self.name+"."
    for object in self.active_objects():
      if (suppress_multiple and object.multiple): continue
      object._all_definitions(
        suppress_multiple=suppress_multiple,
        select_tmp=select_tmp,
        parent=self,
        parent_path=parent_path,
        result=result)

  def all_definitions(self, suppress_multiple=False, select_tmp=None):
    result = []
    for object in self.active_objects():
      if (suppress_multiple and object.multiple): continue
      object._all_definitions(
        suppress_multiple=suppress_multiple,
        select_tmp=select_tmp,
        parent=self,
        parent_path="",
        result=result)
    return result

  def get_without_substitution(self, path):
    if (self.is_disabled): return []
    if (len(self.name) == 0):
      if (len(path) == 0): return self.objects
    elif (self.name == path):
      return [self]
    elif (path.startswith(self.name+".")):
      path = path[len(self.name)+1:]
    else:
      return []
    result = []
    for object in self.active_objects():
      result.extend(object.get_without_substitution(path=path))
    return result

  def get(self, path, with_substitution=True):
    result = scope(name="", objects=self.get_without_substitution(path=path))
    if (not with_substitution): return result
    return result.resolve_variables()

  def resolve_variables(self):
    result = []
    for object in self.active_objects():
      result.append(object.resolve_variables())
    return self.customized_copy(objects=result)

  def lexical_get(self, path, stop_id, search_up=True):
    if (path.startswith(".")):
      while (self.primary_parent_scope is not None):
        self = self.primary_parent_scope
      path = path[1:]
    candidates = []
    for object in self.objects:
      if (object.primary_id >= stop_id): break
      if (isinstance(object, definition)):
        if (object.name == path):
          candidates.append(object)
      elif (object.name == path
            or path.startswith(object.name+".")):
        candidates.append(object)
    while (len(candidates) > 0):
      object = candidates.pop()
      if (object.name == path): return object
      object = object.lexical_get(
        path=path[len(object.name)+1:], stop_id=stop_id, search_up=False)
      if (object is not None): return object
    if (not search_up): return None
    if (self.primary_parent_scope is None): return None
    return self.primary_parent_scope.lexical_get(path=path, stop_id=stop_id)

  def extract(self, parent=None):
    result = scope_extract(name=self.name, parent=parent, call=self.call)
    for object in self.objects:
      if (object.is_disabled):
        value = scope_extract_is_disabled
      else:
        value = object.extract(parent=result)
      result.__phil_set__(
        name=object.name,
        optional=object.optional,
        multiple=object.multiple,
        value=value)
    return result

  def format(self, python_object):
    result = []
    for object in self.master_active_objects():
      if (python_object is None):
        result.append(object.format(None))
      else:
        if (isinstance(python_object, scope_extract)):
          python_object = [python_object]
        for python_object_i in python_object:
          sub_python_object = python_object_i.__phil_get__(object.name)
          if (sub_python_object is not scope_extract_attribute_error):
            if (not object.multiple):
              result.append(object.format(sub_python_object))
            else:
              if (len(sub_python_object) == 0):
                sub_python_object.append(None)
              for sub_python_object_i in sub_python_object:
                result.append(object.format(sub_python_object_i))
    return self.customized_copy(objects=result)

  def clone(self, python_object, converter_registry=None):
    return parse(
      input_string=self.format(python_object=python_object)
        .as_str(attributes_level=3),
      converter_registry=converter_registry).extract()

  def fetch(self,
        source=None,
        sources=None,
        disable_empty=True,
        track_unused_definitions=False):
    assert [source, sources].count(None) == 1
    combined_objects = []
    if (sources is None): sources = [source]
    for source in sources:
      assert source.name == self.name
      if (not isinstance(source, scope)):
        raise RuntimeError(
          'Incompatible parameter objects "%s"%s and "%s"%s' %
            (self.name, self.where_str, source.name, source.where_str))
      combined_objects.extend(source.objects)
    source = self.customized_copy(objects=combined_objects)
    if (track_unused_definitions):
      source.assign_tmp(value=False, active_only=True)
    result_objects = []
    for master_object in self.master_active_objects():
      if (len(self.name) == 0):
        path = master_object.name
      else:
        path = self.name + "." + master_object.name
      matching_sources = source.get(path=path, with_substitution=False)
      if (master_object.multiple):
        all_master_definitions_are_none = \
          master_object.all_definitions_are_none()
        matching_sources.objects \
          = self.get(path=path, with_substitution=False).objects \
          + matching_sources.objects
        processed_as_str = {}
        result_objs = []
        for matching_source in matching_sources.active_objects():
          if (matching_source is master_object
              and all_master_definitions_are_none):
            continue
          candidate = master_object.fetch(
            source=matching_source, disable_empty=disable_empty)
          candidate_extract = candidate.extract()
          if (isinstance(candidate, scope)):
            if (candidate_extract.__phil_is_empty__()): continue
          elif (candidate_extract is None): continue
          candidate_as_str = master_object.format(candidate_extract).as_str()
          prev_index = processed_as_str.get(candidate_as_str, None)
          if (prev_index is not None):
            result_objs[prev_index] = None
          processed_as_str[candidate_as_str] = len(result_objs)
          result_objs.append(candidate)
        if (len(processed_as_str) == 0):
          result_objects.append(master_object.copy())
          if (master_object.optional
              and all_master_definitions_are_none):
            result_objects[-1].is_disabled = disable_empty
        else:
          del processed_as_str
          for candidate in result_objs:
            if (candidate is not None):
              result_objects.append(candidate)
          del result_objs
      else:
        fetch_count = 0
        result_object = master_object
        for matching_source in matching_sources.active_objects():
          fetch_count += 1
          result_object = result_object.fetch(
            source=matching_source, disable_empty=False)
        if (fetch_count == 0):
          result_objects.append(master_object.copy())
        else:
          result_objects.append(result_object)
    result = self.customized_copy(
      objects=clean_fetched_scope(fetched_objects=result_objects))
    if (track_unused_definitions):
      return result, source.all_definitions(select_tmp=False)
    return result

  def tidy_master(self):
    return self.fetch(self, disable_empty=False)

  def process_includes(self,
        converter_registry,
        reference_directory,
        include_stack=None):
    if (converter_registry is None):
      converter_registry = default_converter_registry
    if (include_stack is None): include_stack = []
    result = []
    for object in self.objects:
      if (object.is_disabled):
        result.append(object)
      elif (isinstance(object, definition)):
        if (object.name != "include"):
          result.append(object)
        else:
          object_sub = object.resolve_variables()
          if (len(object_sub.words) < 2):
            raise RuntimeError(
              '"include" must be followed by at least two arguments%s' % (
                object.where_str))
          include_type = object_sub.words[0].value.lower()
          if (include_type == "file"):
            if (len(object_sub.words) != 2):
              raise RuntimeError(
                '"include file" must be followed exactly one argument%s' % (
                  object.where_str))
            file_name = object_sub.words[1].value
            if (reference_directory is not None
                and not os.path.isabs(file_name)):
              file_name = os.path.join(reference_directory, file_name)
            result.extend(parse(
              file_name=file_name,
              converter_registry=converter_registry,
              process_includes=True,
              include_stack=include_stack).objects)
          elif (include_type == "scope"):
            if (len(object_sub.words) > 3):
              raise RuntimeError(
                '"include scope" must be followed one or two arguments,'
                ' i.e. an import path and optionally a phil path%s' % (
                  object.where_str))
            import_path = object_sub.words[1].value
            if (len(object_sub.words) > 2):
              phil_path = object_sub.words[2].value
            else:
              phil_path = None
            result.extend(process_include_scope(
              converter_registry=converter_registry,
              include_stack=include_stack,
              object=object,
              import_path=import_path,
              phil_path=phil_path).objects)
          else:
            raise RuntimeError("Unknown include type: %s%s" % (
              include_type, object.where_str))
      else:
        result.append(object.process_includes(
          converter_registry=converter_registry,
          reference_directory=reference_directory,
          include_stack=include_stack))
    return self.customized_copy(objects=result)

  def unique(self):
    selection = {}
    result = []
    for i_object,object in enumerate(self.active_objects()):
      selection[object.name] = i_object
    for i_object,object in enumerate(self.active_objects()):
      if (selection[object.name] == i_object):
        result.append(object.unique())
    return self.customized_copy(objects=result)

def process_include_scope(
      converter_registry,
      include_stack,
      object,
      import_path,
      phil_path):
  imported = import_python_object(
    import_path=import_path,
    error_prefix="include scope: ",
    target_must_be="; target must be a phil scope",
    where_str=object.where_str)
  source_scope = imported.object
  if (not isinstance(source_scope, scope)):
    raise RuntimeError(
      'include scope: python object "%s" in module "%s" is not a'
      ' libtbx.phil.scope instance%s' % (
        imported.path_elements[-1], imported.module_path, object.where_str))
  source_scope = source_scope.process_includes(
    converter_registry=converter_registry,
    reference_directory=None,
    include_stack=include_stack)
  if (phil_path is None):
    result = source_scope
  else:
    result = source_scope.get(path=phil_path)
    if (len(result.objects) == 0):
      raise RuntimeError(
        'include scope: path "%s" not found in phil scope object "%s"' \
        ' in module "%s"%s' % (
          phil_path, imported.path_elements[-1], imported.module_path,
          object.where_str))
  return result.change_primary_parent_scope(object.primary_parent_scope)

def clean_fetched_scope(fetched_objects):
  result = []
  for object in fetched_objects:
    if (not isinstance(object, scope) or len(object.objects) < 2):
      result.append(object)
    else:
      child_group = []
      for child in object.objects:
        if (not child.merge_names):
          child_group.append(child)
        else:
          if (len(child_group) > 0):
            result.append(object.customized_copy(objects=child_group))
            child_groups = []
          result.append(object.customized_copy(objects=[child]))
      if (len(child_group) > 0):
        result.append(object.customized_copy(objects=child_group))
  return result

class variable_substitution_fragment(object):

  __slots__ = ["is_variable", "value", "result"]

  def __init__(self, is_variable, value):
    self.is_variable = is_variable
    self.value = value

class variable_substitution_proxy(object):

  __slots__ = ["word", "force_string", "have_variables", "fragments"]

  def __init__(self, word):
    self.word = word
    self.force_string = word.quote_token is not None
    self.have_variables = False
    self.fragments = []
    fragment_value = ""
    char_iter = tokenizer.character_iterator(word.value)
    c = char_iter.next()
    while (c is not None):
      if (c != "$"):
        fragment_value += c
        if (c == "\\" and char_iter.look_ahead_1() == "$"):
          fragment_value += char_iter.next()
        c = char_iter.next()
      else:
        self.have_variables = True
        if (len(fragment_value) > 0):
          self.fragments.append(variable_substitution_fragment(
            is_variable=False,
            value=fragment_value))
          fragment_value = ""
        c = char_iter.next()
        if (c is None):
          word.raise_syntax_error("$ must be followed by an identifier: ")
        if (c == "("):
          while True:
            c = char_iter.next()
            if (c is None):
              word.raise_syntax_error('missing ")": ')
            if (c == ")"):
              c = char_iter.next()
              break
            fragment_value += c
          offs = int(fragment_value.startswith("."))
          if (not is_standard_identifier(fragment_value[offs:])):
            word.raise_syntax_error("improper variable name ")
          self.fragments.append(variable_substitution_fragment(
            is_variable=True,
            value=fragment_value))
        else:
          if (c not in standard_identifier_start_characters):
            word.raise_syntax_error("improper variable name ")
          fragment_value = c
          while True:
            c = char_iter.next()
            if (c is None): break
            if (c == "."): break
            if (c not in standard_identifier_continuation_characters): break
            fragment_value += c
          self.fragments.append(variable_substitution_fragment(
            is_variable=True,
            value=fragment_value))
        fragment_value = ""
    if (len(fragment_value) > 0):
      self.fragments.append(variable_substitution_fragment(
        is_variable=False,
        value=fragment_value))
    if (len(self.fragments) > 1):
      self.force_string = True

  def get_new_words(self):
    if (not self.have_variables):
      return [self.word]
    if (not self.force_string):
      return self.fragments[0].result
    return [tokenizer.word(
      value="".join([fragment.result.value for fragment in self.fragments]),
      quote_token='"')]

def parse(
      input_string=None,
      source_info=None,
      file_name=None,
      converter_registry=None,
      process_includes=False,
      include_stack=None):
  from libtbx.phil import parser
  assert source_info is None or file_name is None
  if (input_string is None):
    assert file_name is not None
    input_string = open(file_name).read()
  if (converter_registry is None):
    converter_registry = default_converter_registry
  result = scope(name="", primary_id=0)
  parser.collect_objects(
    word_iterator=tokenizer.word_iterator(
      input_string=input_string,
      source_info=source_info,
      file_name=file_name,
      list_of_settings=[
        tokenizer.settings(
          unquoted_single_character_words="{}=",
          contiguous_word_characters="",
          comment_characters="#",
          meta_comment="phil"),
        tokenizer.settings(
          unquoted_single_character_words="{};",
          contiguous_word_characters="")]),
    converter_registry=converter_registry,
    primary_id_generator=count(1),
    primary_parent_scope=result)
  if (process_includes):
    if (file_name is None):
      file_name_normalized = None
      reference_directory = None
    else:
      file_name_normalized = os.path.normpath(os.path.abspath(file_name))
      reference_directory = os.path.dirname(file_name_normalized)
      if (include_stack is None):
        include_stack = []
      elif (file_name_normalized in include_stack):
        raise RuntimeError("Include dependency cycle: %s"
          % ", ".join(include_stack+[file_name_normalized]))
      include_stack.append(file_name_normalized)
    result = result.process_includes(
      converter_registry=converter_registry,
      reference_directory=reference_directory,
      include_stack=include_stack)
    if (include_stack is not None):
      include_stack.pop()
  return result

def read_default(
      caller_file_name,
      params_extension=".params",
      converter_registry=None,
      process_includes=True):
  params_file_name = os.path.splitext(caller_file_name)[0] + params_extension
  if (not os.path.isfile(params_file_name)):
    raise RuntimeError("Missing parameter file: %s" % params_file_name)
  return parse(
    file_name=params_file_name,
    converter_registry=converter_registry,
    process_includes=process_includes).tidy_master()
