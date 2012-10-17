from __future__ import division
# -*- Mode: Python; c-basic-offset: 2; indent-tabs-mode: nil; tab-width: 8 -*-
#
# LIBTBX_SET_DISPATCHER_NAME cxi.xmerge
#
# $Id$

import iotbx.phil
from cctbx.array_family import flex
from cctbx.crystal import symmetry
from cctbx import uctbx
from libtbx.utils import Usage, multi_out
from libtbx import easy_pickle
import os
import time
import sys

from xfel.command_line.cxi_merge import master_phil,scaling_manager
from xfel.command_line.cxi_merge import unit_cell_distribution,show_overall_observations
from xfel.command_line.cxi_merge import scaling_result
from cctbx.crystal_orientation import crystal_orientation
from xfel import column_parser
from xfel.cxi.util import is_odd_numbered

#-----------------------------------------------------------------------
class xscaling_manager (scaling_manager) :
  def __init__ (self, miller_set, i_model, params, log=None) :
    scaling_manager.__init__(self,miller_set,i_model,params,log)

  def scale_all (self) :
    t1 = time.time()

    if self.params.mysql.runtag is None:
      self.read_all()
    else:
      self.read_all_mysql()
      self.millers = self.millers_mysql
      self.frames = self.frames_mysql
      self._frames = self._frames_mysql
      self.observations = self.observations_mysql
      self._observations = self._observations_mysql

    self.n_accepted = (self.frames["cc"]>self.params.min_corr).count(True)
    self.n_low_corr = (self.frames["cc"]>self.params.min_corr).count(False)

    t2 = time.time()
    print >> self.log, ""
    print >> self.log, "#" * 80
    print >> self.log, "FINISHED MERGING"
    print >> self.log, "  Elapsed time: %.1fs" % (t2 - t1)
    print >> self.log, "  %d integration files were accepted" % (
      self.n_accepted)
    print >> self.log, "  %d rejected due to poor correlation" % \
      self.n_low_corr

  def read_all_mysql(self):
    print "reading observations from MySQL database"
    from xfel.cxi.merging_database import manager
    CART = manager(self.params)
    self.millers_mysql = CART.read_indices()

    self.observations_mysql = CART.read_observations()
    parser = column_parser()
    parser.set_int("hkl_id",self.observations_mysql["hkl_id"])
    parser.set_double("i",self.observations_mysql["i"])
    parser.set_double("sigi",self.observations_mysql["sigi"])
    parser.set_int("frame_id",self.observations_mysql["frame_id"])
    self._observations_mysql = parser

    self.frames_mysql = CART.read_frames()
    parser = column_parser()
    parser.set_int("frame_id",self.frames_mysql["frame_id"])
    parser.set_double("wavelength",self.frames_mysql["wavelength"])
    parser.set_double("cc",self.frames_mysql["cc"])
    parser.set_double("slope",self.frames_mysql["slope"])
    parser.set_double("offset",self.frames_mysql["offset"])
    self._frames_mysql = parser

  def read_all(self):
    print "reading observations from flat-file database"
    self.frames = dict( frame_id=flex.int(),
                        wavelength=flex.double(),
                        cc=flex.double(),
                        slope=flex.double(),
                        offset=flex.double(),
                        odd_numbered=flex.bool(),
                        orientation=[],
                        unit_cell=[])
    self.millers = dict(merged_asu_hkl=flex.miller_index())
    G = open(self.params.output.prefix+"_miller.db","r")
    for line in G.xreadlines():
      tokens = line.strip().split()
      self.millers["merged_asu_hkl"].append((int(tokens[1]),int(tokens[2]),int(tokens[3])))

# --- start C++ read
    parser = column_parser()
    parser.set_int("hkl_id",0)
    parser.set_double("i",1)
    parser.set_double("sigi",2)
    parser.set_int("frame_id",5)
    G = open(self.params.output.prefix+"_observation.db","r")
    for line in G.xreadlines():
      parser.parse_from_line(line)
    self.observations = dict(hkl_id=parser.get_int("hkl_id"),
                             i=parser.get_double("i"),
                             sigi=parser.get_double("sigi"),
                             frame_id=parser.get_int("frame_id"),
                             )
    self._observations = parser
    G.close()
# --- done with C++ read

    G = open(self.params.output.prefix+"_frame.db","r")
    for line in G.xreadlines():
      tokens = line.strip().split()
      self.frames["frame_id"].append(int(tokens[0]))
      self.frames["wavelength"].append(float(tokens[1]))
      self.frames["cc"].append(float(tokens[5]))
      self.frames["slope"].append(float(tokens[6]))
      self.frames["offset"].append(float(tokens[7]))
      self.frames["odd_numbered"].append( is_odd_numbered(tokens[24]) )
      # components of orientation direct matrix
      odm = (float(tokens[8]), float(tokens[9]), float(tokens[10]),
             float(tokens[11]), float(tokens[12]), float(tokens[13]),
             float(tokens[14]), float(tokens[15]), float(tokens[16]),)
      CO = crystal_orientation(odm, False)
      self.frames["orientation"].append(CO)
      self.frames["unit_cell"].append(CO.unit_cell())
    G.close()
    parser = column_parser()
    parser.set_int("frame_id",0)
    parser.set_double("wavelength",1)
    parser.set_double("cc",5)
    parser.set_double("slope",6)
    parser.set_double("offset",7)
    G = open(self.params.output.prefix+"_frame.db","r")
    for line in G.xreadlines():
      parser.parse_from_line(line)
    self._frames = parser

#-----------------------------------------------------------------------
def run(args):
  phil = iotbx.phil.process_command_line(args=args, master_string=master_phil).show()
  work_params = phil.work.extract()
  if ("--help" in args) :
    libtbx.phil.parse(master_phil.show())
    return

  if ((work_params.d_min is None) or
      (work_params.data is None) or
      (work_params.model is None)) :
    raise Usage("cxi.merge "
                "d_min=4.0 "
                "data=~/scratch/r0220/006/strong/ "
                "model=3bz1_3bz2_core.pdb")
  if ((work_params.rescale_with_average_cell) and
      (not work_params.set_average_unit_cell)) :
    raise Usage("If rescale_with_average_cell=True, you must also specify "+
      "set_average_unit_cell=True.")
  # Read Nat's reference model from an MTZ file.  XXX The observation
  # type is given as F, not I--should they be squared?  Check with Nat!
  log = open("%s_%s.log" % (work_params.output.prefix,work_params.scaling.algorithm), "w")
  out = multi_out()
  out.register("log", log, atexit_send_to=None)
  out.register("stdout", sys.stdout)
  print >> out, "I model"
  from xfel.cxi.merging.general_fcalc import run
  i_model = run(work_params)
  i_model.show_summary()
  if (work_params.target_unit_cell is None) :
    work_params.target_unit_cell = i_model.unit_cell()
  if (work_params.target_space_group is None) :
    work_params.target_space_group = i_model.space_group_info()

  print >> out, "Target unit cell and space group:"
  print >> out, "  ", work_params.target_unit_cell
  print >> out, "  ", work_params.target_space_group

  miller_set = symmetry(
      unit_cell=work_params.target_unit_cell,
      space_group_info=work_params.target_space_group
    ).build_miller_set(
      anomalous_flag=not work_params.merge_anomalous,
      d_min=work_params.d_min)

# ---- Augment this code with any special procedures for x scaling
  scaler = xscaling_manager(
    miller_set=miller_set,
    i_model=i_model,
    params=work_params,
    log=out)
  scaler.scale_all()
# --- End of x scaling
  scaler.uc_values = unit_cell_distribution()
  for icell in xrange(len(scaler.frames["unit_cell"])):
    scaler.uc_values.add_cell(
      unit_cell=scaler.frames["unit_cell"][icell],
      rejected=(scaler.frames["cc"][icell] < scaler.params.min_corr))

  scaler.show_unit_cell_histograms()
  if (work_params.rescale_with_average_cell) :
    average_cell_abc = scaler.uc_values.get_average_cell_dimensions()
    average_cell = uctbx.unit_cell(list(average_cell_abc) +
      list(work_params.target_unit_cell.parameters()[3:]))
    work_params.target_unit_cell = average_cell
    print >> out, ""
    print >> out, "#" * 80
    print >> out, "RESCALING WITH NEW TARGET CELL"
    print >> out, "  average cell: %g %g %g %g %g %g" % \
      work_params.target_unit_cell.parameters()
    print >> out, ""
    scaler.reset()
    scaler = xscaling_manager(
      miller_set=miller_set,
      i_model=i_model,
      params=work_params,
      log=out)
    scaler.scale_all()
    scaler.uc_values = unit_cell_distribution()
    for icell in xrange(len(scaler.frames["unit_cell"])):
      scaler.uc_values.add_cell(
        unit_cell=scaler.frames["unit_cell"][icell],
        rejected=(scaler.frames["cc"][icell] < scaler.params.min_corr))
    scaler.show_unit_cell_histograms()
  if False : #(work_params.output.show_plots) :
    try :
      plot_overall_completeness(completeness)
    except Exception, e :
      print "ERROR: can't show plots"
      print "  %s" % str(e)
  print >> out, "\n"

  reserve_prefix = work_params.output.prefix
  for data_subset in [1,2,0]:
    work_params.data_subset = data_subset
    work_params.output.prefix = "%s_s%1d_%s"%(reserve_prefix,data_subset,work_params.scaling.algorithm)

    if work_params.data_subset == 0:
      scaler.frames["data_subset"] = flex.bool(scaler.frames["frame_id"].size(),True)
    elif work_params.data_subset == 1:
      scaler.frames["data_subset"] = scaler.frames["odd_numbered"]
    elif work_params.data_subset == 2:
      scaler.frames["data_subset"] = scaler.frames["odd_numbered"]==False

  # --------- New code ------------------
    #sanity check
    for mod,obs in zip(i_model.indices(),scaler.millers["merged_asu_hkl"]):
      assert mod==obs

    """Sum the observations of I and I/sig(I) for each reflection.
    sum_I = flex.double(i_model.size(), 0.)
    sum_I_SIGI = flex.double(i_model.size(), 0.)
    scaler.completeness = flex.int(i_model.size(), 0)
    scaler.summed_N = flex.int(i_model.size(), 0)
    scaler.summed_wt_I = flex.double(i_model.size(), 0.)
    scaler.summed_weight = flex.double(i_model.size(), 0.)
    scaler.n_rejected = flex.double(scaler.frames["frame_id"].size(), 0.)
    scaler.n_obs = flex.double(scaler.frames["frame_id"].size(), 0.)
    scaler.d_min_values = flex.double(scaler.frames["frame_id"].size(), 0.)
    scaler.ISIGI = {}"""

    from xfel import scaling_results, get_scaling_results, get_isigi_dict
    results = scaling_results(scaler._observations, scaler._frames,
              scaler.millers["merged_asu_hkl"],scaler.frames["data_subset"])
    results.__getattribute__(
      work_params.scaling.algorithm)(
      scaler.params.min_corr, scaler.params.target_unit_cell)

    sum_I, sum_I_SIGI, \
    scaler.completeness, scaler.summed_N, \
    scaler.summed_wt_I, scaler.summed_weight, scaler.n_rejected, scaler.n_obs, \
    scaler.d_min_values, i_sigi_list = get_scaling_results(results)

    scaler.ISIGI = get_isigi_dict(results)

    scaler.wavelength = scaler.frames["wavelength"]
    scaler.corr_values = scaler.frames["cc"]

    scaler.rejected_fractions = flex.double(scaler.frames["frame_id"].size(), 0.)
    for irej in xrange(len(scaler.rejected_fractions)):
      if scaler.n_obs[irej] > 0:
        scaler.rejected_fractions = scaler.n_rejected[irej]/scaler.n_obs[irej]
  # ---------- End of new code ----------------

    j_model = i_model.customized_copy(
      unit_cell=work_params.target_unit_cell)

    table1 = show_overall_observations(
      obs=j_model,
      redundancy=scaler.completeness,
      ISIGI=scaler.ISIGI,
      n_bins=work_params.output.n_bins,
      title="Statistics for all reflections",
      out=out,
      work_params=work_params)
    print >> out, ""
    n_refl, corr = scaler.get_overall_correlation(sum_I)
    print >> out, "\n"
    table2 = show_overall_observations(
      obs=j_model,
      redundancy=scaler.summed_N,
      ISIGI=scaler.ISIGI,
      n_bins=work_params.output.n_bins,
      title="Statistics for reflections where I > 0",
      out=out,
      work_params=work_params)

    print >> out, ""
    mtz_file, miller_array = scaler.finalize_and_save_data()

    loggraph_file = os.path.abspath("%s_graphs.log" % work_params.output.prefix)
    f = open(loggraph_file, "w")
    f.write(table1.format_loggraph())
    f.write("\n")
    f.write(table2.format_loggraph())
    f.close()
    result = scaling_result(
      miller_array=miller_array,
      plots=scaler.get_plot_statistics(),
      mtz_file=mtz_file,
      loggraph_file=loggraph_file,
      obs_table=table1,
      all_obs_table=table2,
      n_reflections=n_refl,
      overall_correlation=corr)
    easy_pickle.dump("%s.pkl" % work_params.output.prefix, result)
  work_params.output.prefix = reserve_prefix

  from xfel.cxi.cxi_cc import run_cc
  run_cc(work_params,output=out)

  return result

if (__name__ == "__main__"):
  show_plots = False
  if ("--plots" in sys.argv) :
    sys.argv.remove("--plots")
    show_plots = True
  result = run(args=sys.argv[1:])
  if (show_plots) :
    try :
      result.plots.show_all_pyplot()
      from wxtbx.command_line import loggraph
      loggraph.run([result.loggraph_file])
    except Exception, e :
      print "Can't display plots"
      print "You should be able to view them by running this command:"
      print "  wxtbx.loggraph %s" % result.loggraph_file
      raise e
