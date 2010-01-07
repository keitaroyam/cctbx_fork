def exercise(n=100000):
  from libtbx import easy_pickle
  import time
  obj = []
  for i in xrange(n):
    obj.append([i,i])
  for dgz in ["", ".gz"]:
    file_name = "test.dat"+dgz
    print file_name
    t0 = time.time()
    easy_pickle.dump(file_name=file_name, obj=obj)
    print "  dump: %.2f s" % (time.time()-t0)
    del obj
    t0 = time.time()
    obj = easy_pickle.load(file_name=file_name)
    print "  load buffered: %.2f s" % (time.time()-t0)
    del obj
    t0 = time.time()
    obj = easy_pickle.load(
      file_name=file_name, faster_but_using_more_memory=False)
    print "  load direct: %.2f s" % (time.time()-t0)

def run(args):
  assert len(args) == 0
  exercise()
  print "OK"

if (__name__ == "__main__"):
  import sys
  run(args=sys.argv[1:])
