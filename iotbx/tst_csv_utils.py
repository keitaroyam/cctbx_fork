import csv_utils
import tempfile
from scitbx.array_family import flex
from libtbx.test_utils import Exception_expected

def exercise():
  exercise_writer()
  exercise_reader()

def exercise_writer():
  x = (1,2,3,4,5)
  y = (6,7,8,9,10)
  filename = tempfile.mktemp()
  f = open(filename, 'w')
  field_names = ('x','y')
  csv_utils.writer(f, (x,y), field_names=field_names)
  f.close()
  f = open(filename, 'r')
  content = f.readlines()
  text = ['x,y\r\n']
  text += ['%s,%s\r\n' %(row[0],row[1]) for row in zip(x,y)]
  assert content == text

  x = (1,2,3,4,5)
  y = (6,7,8,9,10)
  filename = tempfile.mktemp()
  f = open(filename, 'w')
  csv_utils.writer(f, (x,y), delimiter=';')
  f.close()
  f = open(filename, 'r')
  content = f.readlines()
  text = ['%s;%s\r\n' %(row[0],row[1]) for row in zip(x,y)]
  assert content == text

  x = flex.int(x)
  y = flex.int(y)
  f = open(filename, 'w')
  csv_utils.writer(f, (x,y), field_names=field_names)
  f.close()
  f = open(filename, 'r')
  content = f.readlines()
  text = ['x,y\r\n']
  text += ['%s,%s\r\n' %(row[0],row[1]) for row in zip(x,y)]
  assert content == text

  y.append(11)
  f = open(filename, 'w')
  try:
    csv_utils.writer(f, (x,y), field_names=field_names)
  except AssertionError:
    pass
  else:
    raise Exception_expected
  f.close()


def exercise_reader():
  x = (1,2,3,4,5)
  y = (6,7,8,9,10)
  filename = tempfile.mktemp()
  f = open(filename, 'w')
  field_names = ('x','y')
  csv_utils.writer(f, (x,y), field_names=field_names,delimiter=';')
  f.close()
  f = open(filename, 'r')
  a = csv_utils.reader(f, data_type=int, field_names=True,delimiter=';')
  assert tuple(a.data[0]) == x
  assert tuple(a.data[1]) == y

  x = (1,2,3,4,5)
  y = (1.1,2.2,3.3,4.4,5.5)
  filename = tempfile.mktemp()
  f = open(filename, 'w')
  field_names = ('x','y')
  csv_utils.writer(f, (x,y), field_names=field_names,delimiter=';')
  f.close()
  f = open(filename, 'r')
  data_type = (int, float)
  a = csv_utils.reader(f, data_type=data_type, field_names=True,delimiter=';')
  assert tuple(a.data[0]) == x
  assert tuple(a.data[1]) == y

def run():
  exercise()
  print "OK"

if __name__ == '__main__':
  run()
