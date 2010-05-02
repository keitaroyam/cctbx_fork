from libtbx.containers import OrderedDict
import sys
if 0 and sys.version_info[0] >= 2 and sys.version_info[1] >= 6:
  from collections import MutableMapping as DictMixin
else:
  from UserDict import DictMixin
import copy
from cStringIO import StringIO

from cctbx.array_family import flex

class cif(DictMixin):
  def __init__(self, blocks=None):
    if blocks is not None:
      self.blocks = blocks
    else:
      self.blocks = OrderedDict()

  def __setitem__(self, key, value):
    assert isinstance(value, block)
    self.blocks[key] = value

  def __getitem__(self, key):
    return self.blocks[key]

  def __delitem__(self, key):
    del self.blocks[key]

  def keys(self):
    return self.blocks.keys()

  def __repr__(self):
    return repr(OrderedDict(self.iteritems()))

  def copy(self):
    return cif(self.blocks.copy())

  def deepcopy(self):
    return cif(copy.deepcopy(self.blocks))

  def show(self, out=None, indent="  ", data_name_field_width=34):
    if out is None:
      out = sys.stdout
    for name, block in self.items():
      print >> out, "data_%s" %name
      block.show(
        out=out, indent=indent, data_name_field_width=data_name_field_width)

  def __str__(self):
    s = StringIO()
    self.show(out=s)
    return s.getvalue()


class block(DictMixin):
  def __init__(self):
    self._items = OrderedDict()
    self.loops = OrderedDict()

  def __setitem__(self, key, value):
    if isinstance(value, loop):
      self.loops[key] = value
    else:
      self._items[key] = str(value)

  def __getitem__(self, key):
    if self._items.has_key(key):
      return self._items[key]
    else:
      for loop in self.loops.values():
        if loop.has_key(key):
          return loop[key]
      raise KeyError

  def __delitem__(self, key):
    if self._items.has_key(key):
      del self._items[key]
    elif self.loops.has_key(key):
      del self.loops[key]
    else:
      raise KeyError

  def keys(self):
    keys = self._items.keys()
    for loop in self.loops.values():
      keys.extend(loop.keys())
    return keys

  def __repr__(self):
    return repr(OrderedDict(self.iteritems()))

  def update(self, other=None, **kwargs):
    if other is None:
      pass
    self._items.update(other._items)
    self.loops.update(other.loops)

  def add_data_item(self, tag, value):
    self[tag] = value

  def add_loop(self, loop):
    self.loops.setdefault(loop.name(), loop)

  def copy(self):
    new = block()
    new._items = self._items.copy()
    new.loops = self.loops.copy()
    return new

  def deepcopy(self):
    new = block()
    new._items = copy.deepcopy(self._items)
    new.loops = copy.deepcopy(self.loops)
    return new

  def show(self, out=None, indent="  ", data_name_field_width=34):
    if out is None:
      out = sys.stdout
    format_str = "%%-%is" %(data_name_field_width-1)
    for k, v in self._items.items():
      print >> out, format_str %k, format_value(v)
    for loop in self.loops.values():
      print >> out
      loop.show(out=out, indent=indent)

  def __str__(self):
    s = StringIO()
    self.show(out=s)
    return s.getvalue()


class loop(DictMixin):
  def __init__(self, header=None, data=None):
    self._columns = OrderedDict()
    if header is not None:
      for key in header:
        self.setdefault(key, flex.std_string())
      if data is not None:
        # the number of data items must be an exact multiple of the number of headers
        assert len(data) % len(header) == 0
        n_rows = len(data)/len(header)
        n_columns = len(header)
        for i in range(n_rows):
          self.add_row([data[i*n_columns+j] for j in range(n_columns)])
    elif header is None and data is not None:
      assert isinstance(data, dict) or isinstance(data, OrderedDict)
      self.add_columns(data)

  def __setitem__(self, key, value):
    if len(self) > 0:
      assert len(value) == self.size()
    if not isinstance(value, flex.std_string):
      for flex_numeric_type in (flex.int, flex.double):
        if not isinstance(value, flex_numeric_type):
          try:
            value = flex_numeric_type(value).as_string()
          except TypeError:
            continue
          else:
            break
      if not isinstance(value, flex.std_string):
        value = flex.std_string(value)
    # value must be a mutable type
    assert hasattr(value, '__setitem__')
    self._columns[key] = value

  def __getitem__(self, key):
    return self._columns[key]

  def __delitem__(self, key):
    del self._columns[key]

  def keys(self):
    return self._columns.keys()

  def __repr__(self):
    return repr(OrderedDict(self.iteritems()))

  def name(self):
    return common_prefix(self.keys())

  def size(self):
    size = 0
    for column in self.values():
      size = max(size, len(column))
    return size

  def add_row(self, row):
    assert len(row) == len(self)
    for i, key in enumerate(self):
      self[key].append(str(row[i]))

  def add_column(self, key, values):
    if self.size() != 0:
      assert len(values) == self.size()
    self[key] = values

  def add_columns(self, columns):
    assert isinstance(columns, dict) or isinstance(columns, OrderedDict)
    for key, value in columns.iteritems():
      self.add_column(key, value)

  def copy(self):
    new = loop()
    new._columns = self._columns.copy()
    return new

  def deepcopy(self):
    new = loop()
    new._columns = copy.deepcopy(self._columns)
    return new

  def show(self, out=None, indent="  "):
    if out is None:
      out = sys.stdout
    print >> out, "loop_"
    for k in self.keys():
      print >> out, indent + k
    values = self._columns.values()
    for i in range(self.size()):
      values_to_print = [format_value(values[j][i]) for j in range(len(values))]
      print >> out, ' '.join([indent] + values_to_print)

  def __str__(self):
    s = StringIO()
    self.show(out=s)
    return s.getvalue()


def common_prefix(seq):
  if not seq:return ""
  seq.sort()
  s1, s2 = seq[0], seq[-1]
  l = min(len(s1), len(s2))
  if l == 0 :
    return ""
  for i in xrange(l) :
    if s1[i] != s2[i] :
      return s1[0:i]
  return s1[0:l]

def format_value(value_string):
  import re
  m = re.match(r"(?!'|\").*?(?!'|\")", value_string)
  string_is_quoted = m is None
  if not string_is_quoted:
    if re.match(r"(\s*)(;).*?(;)(\s*)", value_string, re.DOTALL) is not None:
      # a semicolon text field
      return "\n%s\n" %value_string.strip()
    elif re.search(r"\s", value_string) is not None:
      # string needs quoting
      return "'%s'" %value_string
  return value_string
