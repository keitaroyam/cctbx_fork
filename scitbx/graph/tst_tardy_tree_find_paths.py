from scitbx.graph.tardy_tree import find_paths, find_paths_v3, construct
from scitbx.graph import rigidity
from scitbx.graph import utils
from libtbx.option_parser import libtbx_option_parser
from libtbx.utils import host_and_user, show_times_at_exit
import sys

def exercise_minimal():
  edge_sets = utils.construct_edge_sets(n_vertices=1, edge_list=[])
  assert find_paths(edge_sets=edge_sets, iv=0) == {0: {}}
  edge_sets = utils.construct_edge_sets(n_vertices=2, edge_list=[(0,1)])
  for iv in [0,1]:
    assert find_paths(edge_sets=edge_sets, iv=iv) == {0: {1: []}, 1: {0: []}}

def exercise_simple_loops(loop_size_max=8):
  for n_vertices in xrange(3, loop_size_max+1):
    edge_list = [tuple(sorted((i,(i+1)%n_vertices)))
      for i in xrange(n_vertices)]
    edge_sets = utils.construct_edge_sets(
      n_vertices=n_vertices, edge_list=edge_list)
    jv_kv_paths = find_paths(edge_sets=edge_sets, iv=0)
    assert len(jv_kv_paths[0]) == 2
    if (n_vertices <= 6):
      jv_kv_paths[0][1] == n_vertices-2
      jv_kv_paths[0][n_vertices-1] == n_vertices-2
    else:
      jv_kv_paths[0][1] == 0
      jv_kv_paths[0][n_vertices-1] == 0
    if (n_vertices == 3):
      assert jv_kv_paths == {
        0: {1: [[2]], 2: [[1]]},
        1: {0: [], 2: []},
        2: {0: [], 1: []}}
    elif (n_vertices == 4):
      assert jv_kv_paths == {
        0: {1: [[3, 2]], 3: [[1, 2]]},
        1: {0: [], 2: [[3]]},
        2: {1: [], 3: []},
        3: {0: [], 2: [[1]]}}
    #
    print "n_vertices:", n_vertices
    p = find_paths_v3(edge_sets=edge_sets, iv=0)
    print p

def exercise_knot():
  edge_sets = utils.construct_edge_sets(
    n_vertices=4,
    edge_list=[(0,1), (1,2), (2,3), (1,3)])
  expected_jv_kb_paths = [
    {0: {1: []},
     1: {0: [], 2: [[1, 3]], 3: [[1, 2]]},
     2: {1: [], 3: [[1]]},
     3: {1: [], 2: [[1]]}},
    {0: {1: []},
     1: {0: [], 2: [[3]], 3: [[2]]},
     2: {1: [], 3: []},
     3: {1: [], 2: []}},
    {0: {1: [[3]]},
     1: {2: [], 3: []},
     2: {1: [[3]], 3: [[1]]},
     3: {1: [], 2: []}},
    {0: {1: [[2]]},
     1: {2: [], 3: []},
     2: {1: [], 3: []},
     3: {1: [[2]], 2: [[1]]}}]
  for iv in xrange(4):
    jv_kv_paths = find_paths(edge_sets=edge_sets, iv=iv)
    assert jv_kv_paths == expected_jv_kb_paths[iv]
    p = find_paths_v3(edge_sets=edge_sets, iv=iv)
    print "knot", iv, p

def exercise_hexagon_wheel():
  edge_sets = utils.construct_edge_sets(
    n_vertices=7,
    edge_list=[
      (0,1), (0,2), (0,3), (0,4), (0,5), (0,6),
      (1,2), (1,6), (2,3), (3,4), (4,5), (5,6)])
  for iv in xrange(7):
    jv_kv_paths = find_paths(edge_sets=edge_sets, iv=iv)
    if (0):
        print "iv:", iv
        for jv,kv_paths in jv_kv_paths.items():
          print "  jv:", jv
          for kv,paths in kv_paths.items():
            print "    kv:", kv, paths
        print
  p = find_paths_v3(edge_sets=edge_sets, iv=0)
  print "wheel", 0, p
  p = find_paths_v3(edge_sets=edge_sets, iv=1)
  print "wheel", 1, p

def archs_grow_edge_list(edge_list, offs, size, av=0, bv=1):
  result = list(edge_list)
  i = av
  for j in xrange(offs, offs+size):
    result.append((i,j))
    i = j
  result.append((bv,i))
  return result

def arch_dof(n_vertices, edge_list):
  es = utils.construct_edge_sets(n_vertices=n_vertices, edge_list=edge_list)
  bbes = utils.bond_bending_edge_sets(edge_sets=es)
  bbel = utils.extract_edge_list(edge_sets=bbes)
  dofs = [rigidity.determine_degrees_of_freedom(
    n_dim=3, n_vertices=n_vertices, edge_list=bbel, method=method)
      for method in ["float", "integer"]]
  assert dofs[0] == dofs[1]
  return es, dofs[0]

def exercise_fused_loops(arch_size_max=8):
  for arch_size_1 in xrange(1, arch_size_max+1):
    edge_list_1 = archs_grow_edge_list(
      [(0,1)], 2, arch_size_1)
    for arch_size_2 in xrange(1, arch_size_max+1):
      n_vertices = 2 + arch_size_1 + arch_size_2
      edge_list_12 = archs_grow_edge_list(
        edge_list_1, 2+arch_size_1, arch_size_2)
      es, dof = arch_dof(n_vertices=n_vertices, edge_list=edge_list_12)
      is_rigid = (dof == 6)
      inferred_is_rigid = (
            arch_size_1 < 6
        and arch_size_2 < 6
        and arch_size_1 + arch_size_2 < 10)
      assert inferred_is_rigid == is_rigid

def fourth_arch(arch_sizes, edge_list_123, es_123, arch_size_max):
  def vertex_info(i):
    off = 2
    if (i < off): return str(i)
    for ia,s in enumerate(arch_sizes):
      poff = off
      off += s
      if (i < off): return "%d%s" % (i-poff+1, "abc"[ia])
  def analyze():
    n_vertices = len(es_123) + arch_size_4
    edge_list_1234 = archs_grow_edge_list(
      edge_list_123, len(es_123), arch_size_4, av, bv)
    tt = construct(n_vertices=n_vertices, edge_list=edge_list_1234)
    tt.finalize()
    cm = tt.cluster_manager
    es, dof = arch_dof(n_vertices=n_vertices, edge_list=edge_list_1234)
    print vertex_info(av), vertex_info(bv), arch_size_4,
    have_failure = False
    r_rm = (dof == 6)
    r_tt = (len(cm.clusters) == 1)
    if (r_rm):
      print "r",
    else:
      assert dof > 6
      print "f",
    if (r_tt):
      print "r",
    else:
      print "f",
    if (r_rm and not r_tt):
      print "FAILURE",
      have_failure = True
    print arch_sizes
    if (not r_rm): assert not r_tt
    if (have_failure):
      print "n_vertices, edge_list:", n_vertices, edge_list_1234
  av = 0
  bv = 1
  for arch_size_4 in xrange(1, arch_size_max+1):
    analyze()
  for bv in xrange(2,len(es_123)):
    for arch_size_4 in xrange(1, arch_size_max+1):
      analyze()
  for av in xrange(2,len(es_123)-1):
    for bv in xrange(av+1,len(es_123)):
      if (bv in es_123[av]): continue
      analyze()

def exercise_three_archs(arch_size_max, chunk_i):
  if (chunk_i is not None):
    assert 0 <= chunk_i < arch_size_max**2
  for arch_size_1 in xrange(1, arch_size_max+1):
    edge_list_1 = archs_grow_edge_list(
      [], 2, arch_size_1)
    for arch_size_2 in xrange(1, arch_size_max+1):
      edge_list_12 = archs_grow_edge_list(
        edge_list_1, 2+arch_size_1, arch_size_2)
      i_12 = (arch_size_1-1)*arch_size_max+(arch_size_2-1)
      if (chunk_i is not None and i_12 != chunk_i): continue
      for arch_size_3 in xrange(1, arch_size_max+1):
        n_vertices = 2 + arch_size_1 + arch_size_2 + arch_size_3
        edge_list_123 = archs_grow_edge_list(
          edge_list_12, 2+arch_size_1+arch_size_2, arch_size_3)
        es, dof = arch_dof(n_vertices=n_vertices, edge_list=edge_list_123)
        expected = max(
          6,
          max(arch_size_1, arch_size_2, arch_size_3) + 1,
          arch_size_1 + arch_size_2 + arch_size_3 - 3)
        assert expected == dof
        if (chunk_i is not None):
          print "dof:", dof, "archs:", arch_size_1, arch_size_2, arch_size_3
          fourth_arch(
            arch_sizes=(arch_size_1, arch_size_2, arch_size_3),
            edge_list_123=edge_list_123,
            es_123=es,
            arch_size_max=arch_size_max)
        is_rigid = (dof == 6)
        inferred_is_rigid = (
              arch_size_1 < 6
          and arch_size_2 < 6
          and arch_size_3 < 6
          and arch_size_1 + arch_size_2 + arch_size_3 < 10)
        assert inferred_is_rigid == is_rigid
        s = (arch_size_1 < 6) \
          + (arch_size_2 < 6) \
          + (arch_size_3 < 6)
        for iv in [0,1]:
          jv_kv_paths = find_paths(edge_sets=es, iv=iv)
          kv_paths = jv_kv_paths.get(1-iv, [])
          assert len(kv_paths) == s
          if (len(kv_paths) == 3):
            sum_len = 0
            for paths in kv_paths.values():
              assert len(paths) in [0,1]
              if (len(paths) == 1):
                sum_len += len(paths[0])
            inferred_is_rigid = sum_len < 7
            assert inferred_is_rigid == is_rigid
          else:
            assert not is_rigid
        #
        arch_sizes = sorted([arch_size_1, arch_size_2, arch_size_3])
        for iv in [0,1]:
          loops, dendrites = find_paths_v3(edge_sets=es, iv=iv)
          # XXX crude tests only
          if (len(loops) != 0):
            for loop in loops:
              assert 1-iv in loop
              if (len(loop) != 6):
                assert arch_sizes[0] + arch_sizes[1] < 5
                inferred_is_rigid = arch_sizes[2] < 6
                assert inferred_is_rigid == is_rigid
          else:
            assert arch_sizes[0] + arch_sizes[1] > 3
            inferred_is_rigid = sum(arch_sizes) < 10
            assert inferred_is_rigid == is_rigid
            for path in dendrites:
              sp = set(path)
              assert iv not in sp
              assert len(sp) == len(path)

def run(args):
  command_line = (libtbx_option_parser(
    usage="scitbx.python tst_tardy_tree_find_paths.py [options]")
    .enable_chunk()
    .option(None, "--arch_size_max",
      type="int",
      default=8,
      metavar="INT")
  ).process(args=args, nargs=0).queuing_system_overrides_chunk()
  co = command_line.options
  #
  chunk_n = command_line.chunk_n
  chunk_i = command_line.chunk_i
  if (chunk_n != 1):
    assert chunk_n == co.arch_size_max**2
    i = command_line.queuing_system_info
    if (i is not None and i.have_array()):
      log = open("log%03d" % chunk_i, "w")
      sys.stdout = log
      sys.stderr = log
    host_and_user().show()
    if (i is not None): i.show()
    print "chunk_n:", chunk_n
    print "chunk_i: %03d" % chunk_i
    print
  else:
    chunk_i = None
  #
  show_times_at_exit()
  #
  exercise_minimal()
  exercise_simple_loops()
  exercise_knot()
  exercise_hexagon_wheel()
  exercise_fused_loops()
  exercise_three_archs(arch_size_max=co.arch_size_max, chunk_i=chunk_i)
  print "OK"

if (__name__ == "__main__"):
  run(sys.argv[1:])
