from cctbx import sgtbx
from scitbx.python_utils.command_line import parse_options
from libtbx.utils import format_cpu_times
import libtbx.load_env
import sys, os, time, random

def get_test_space_group_symbols(flag_AllSpaceGroups,
                                 flag_ChiralSpaceGroups,
                                 flag_AllSettings,
                                 flag_UnusualSettings):
  if (flag_UnusualSettings):
    namespace = {}
    execfile(os.path.join(
      libtbx.env.find_in_repositories("regression"), "settings.py"), namespace)
    return namespace["settings"]
  if (flag_AllSettings):
    return [symbols.extended_hermann_mauguin()
            for symbols in sgtbx.space_group_symbol_iterator()]
  if (flag_AllSpaceGroups):
    sg_numbers = xrange(1, 231)
  elif (flag_ChiralSpaceGroups):
    sg_numbers = (1, 3, 4, 5, 16, 17, 18, 19, 20, 21, 22, 23, 24, 75,
                  76, 77, 78, 79, 80, 89, 90, 91, 92, 93, 94, 95, 96,
                  97, 98, 143, 144, 145, 146, 149, 150, 151, 152, 153,
                  154, 155, 168, 169, 170, 171, 172, 173, 177, 178,
                  179, 180, 181, 182, 195, 196, 197, 198, 199, 207,
                  208, 209, 210, 211, 212, 213, 214)
  else:
    sg_numbers = (1,2,3,15,16,74,75,76,142,143,144,157,167,168,194,195,230)
  return [sgtbx.space_group_symbols(n).extended_hermann_mauguin()
          for n in sg_numbers] + ["Hall: -F 4 21 (1,5,3)"]

def random_origin_shift(space_group_info, grid=12):
  xyz = []
  for i in xrange(3):
    xyz.append("%s+%d/%d" % ("xyz"[i], random.randrange(grid), grid))
  xyz = ",".join(xyz)
  return space_group_info.change_basis(sgtbx.change_of_basis_op(xyz))

def loop_space_groups(argv, flags, call_back, symbols_to_stdout=0):
  chunk_size = 1
  chunk_member = 0
  if (flags.ChunkSize != False):
    chunk_size = int(flags.ChunkSize)
  if (flags.ChunkMember != False):
    chunk_member = int(flags.ChunkMember)
  assert chunk_size > 0 and chunk_member < chunk_size
  n_threads = int(flags.Threads)
  threading = None
  if (n_threads > 1):
    import threading
    print "Number of threads:", n_threads
  if (not flags.RandomSeed): random.seed(0)
  if (len(argv) > 0 + flags.n):
    symbols = argv
  else:
    symbols = get_test_space_group_symbols(
      flags.AllSpaceGroups,
      flags.ChiralSpaceGroups,
      flags.AllSettings,
      flags.UnusualSettings)
  i_loop = -1
  for symbol in symbols:
    if (symbol.startswith("--")): continue
    i_loop += 1
    if (i_loop % chunk_size != chunk_member): continue
    space_group_info = sgtbx.space_group_info(symbol)
    sys.stdout.flush()
    print >> sys.stderr, space_group_info
    sys.stderr.flush()
    if (symbols_to_stdout):
      print space_group_info
      sys.stdout.flush()
    if (threading is None):
      continue_flag = call_back(flags, space_group_info)
      sys.stdout.flush()
      if (continue_flag == False): break
    else:
      while 1:
        if (threading.activeCount() < n_threads): break
        time.sleep(1)
      t = threading.Thread(target=call_back, args=(flags, space_group_info))
      t.setDaemon(True)
      t.start()
  if (threading is not None):
    while 1:
      if (threading.activeCount() == 1): break
      time.sleep(1)
  sys.stdout.flush()
  print format_cpu_times()

def parse_options_loop_space_groups(argv, call_back,
                                    keywords=(),
                                    symbols_to_stdout=0):
  flags = parse_options(argv, (
    "Verbose",
    "Threads",
    "ChunkSize",
    "ChunkMember",
    "RandomSeed",
    "AllSpaceGroups",
    "ChiralSpaceGroups",
    "AllSettings",
    "UnusualSettings") + keywords
  )
  loop_space_groups(argv, flags, call_back, symbols_to_stdout)
