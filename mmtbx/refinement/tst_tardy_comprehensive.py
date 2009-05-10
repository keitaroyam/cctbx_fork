from __future__ import division
from mmtbx.refinement import tst_tardy_pdb
import iotbx.phil
from scitbx.array_family import flex
from libtbx.utils import show_times_at_exit
import libtbx.phil.command_line
from libtbx.queuing_system_utils import chunk_manager
from libtbx import Auto
from cStringIO import StringIO
import pprint
import traceback
import sys, os
op = os.path

def report_exception(context_info):
  print ">Begin exception"
  print "Exception:", context_info
  sys.stdout.flush()
  sys.stderr.flush()
  traceback.print_exc()
  print ">End exception"
  sys.stdout.flush()
  sys.stderr.flush()
  print

class collector(object):

  def __init__(O):
    O.sim = None
    O.rmsd = flex.double()

  def __call__(O, sim=None):
    if (sim is not None):
      assert O.sim is None
      O.sim = sim
    else:
      assert O.sim is not None
    sites_moved = flex.vec3_double(O.sim.sites_moved())
    O.rmsd.append(O.sim.potential_obj.ideal_sites_cart.rms_difference(
      sites_moved))

common_parameter_trial_table = [
  ("tardy_displacements_auto.rmsd", (0.5, 0.75, 1.0, 1.25, 1.5)),
  ("structure_factors_high_resolution", (1, 2, 3, 4, 5)),
  ("real_space_target_weight", (1, 10, 100, 1000)),
  ("real_space_gradients_delta_resolution_factor", (1/2, 1/3, 1/4)),
  ("emulate_cartesian", (False, True))
]

def number_of_trials(table):
  result = 1
  for name,values in table:
    result *= len(values)
  return result

def set_parameters(params, trial_table, cp_i_trial):
  rest = cp_i_trial
  for i in reversed(range(len(trial_table))):
    name, values = trial_table[i]
    n = len(values)
    j = rest % n
    rest //= n
    phil_path = name.split(".")
    assert len(phil_path) > 0
    scope = params
    for scope_name in phil_path[:-1]:
      scope = getattr(scope, scope_name)
    setattr(scope, phil_path[-1], values[j])
  assert rest == 0

def get_master_phil():
  return iotbx.phil.parse(
    input_string="""\
pdb_file = None
  .type = path
number_of_random_trials = 2
  .type = int
hot = False
  .type = bool
verbose = False
  .type = bool
keep_going = False
  .type = bool
chunk = 1 0
  .type = ints(size=2, value_min=0)
""")

def run(args):
  local_master_phil = get_master_phil()
  argument_interpreter = libtbx.phil.command_line.argument_interpreter(
    master_phil=local_master_phil)
  phil_objects = []
  for arg in args:
    phil_objects.append(argument_interpreter.process(arg=arg))
  local_params = local_master_phil.fetch(sources=phil_objects).extract()
  chunk = chunk_manager(
    n=local_params.chunk[0],
    i=local_params.chunk[1]).easy_all()
  local_master_phil.format(local_params).show()
  print
  #
  assert local_params.pdb_file is not None
  assert op.isfile(local_params.pdb_file)
  #
  tst_tardy_pdb_master_phil = tst_tardy_pdb.get_master_phil()
  tst_tardy_pdb_params = tst_tardy_pdb_master_phil.extract()
  tst_tardy_pdb_params.tardy_displacements = Auto
  cp_n_trials = number_of_trials(table=common_parameter_trial_table)
  print "Number of common parameter trials:", cp_n_trials
  print "common_parameter_trial_table:"
  pprint.pprint(common_parameter_trial_table)
  print
  #
  show_times_at_exit()
  #
  first_pass = True
  for cp_i_trial in xrange(cp_n_trials):
    if (chunk.skip_iteration(i=cp_i_trial)): continue
    print "cp_i_trial: %d / %d = %.2f %%" % (
      cp_i_trial, cp_n_trials, 100 * (cp_i_trial+1) / cp_n_trials)
    if (local_params.verbose):
      print
    sys.stdout.flush()
    set_parameters(
      params=tst_tardy_pdb_params,
      trial_table=common_parameter_trial_table,
      cp_i_trial=cp_i_trial)
    tst_tardy_pdb_params.number_of_cooling_steps = 0
    tst_tardy_pdb_params.minimization_max_iterations = None
    for random_seed in xrange(local_params.number_of_random_trials):
      tst_tardy_pdb_params.random_seed = random_seed
      if (local_params.verbose or first_pass):
        tst_tardy_pdb_master_phil.format(tst_tardy_pdb_params).show()
        print
        sys.stdout.flush()
      first_pass = False
      if (local_params.hot):
        if (local_params.verbose):
          tst_tardy_pdb_log = sys.stdout
        else:
          tst_tardy_pdb_log = StringIO()
        coll = collector()
        try:
          tst_tardy_pdb.run_test(
            params=tst_tardy_pdb_params,
            pdb_files=[local_params.pdb_file],
            other_files=[],
            callback=coll,
            log=tst_tardy_pdb_log)
        except KeyboardInterrupt: raise
        except:
          if (not local_params.verbose):
            sys.stdout.write(tst_tardy_pdb_log.getvalue())
            sys.stdout.flush()
          if (not local_params.keep_going):
            raise
          report_exception(
            context_info="cp_i_trial=%d, random_seed=%d" % (
              cp_i_trial, random_seed))
        else:
          print "RESULT_cp_i_trial_random_seed_rmsd:", \
            cp_i_trial, random_seed, list(coll.rmsd)
          sys.stdout.flush()
    if (local_params.hot):
      print

if (__name__ == "__main__"):
  run(args=sys.argv[1:])
