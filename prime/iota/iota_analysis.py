from __future__ import division

'''
Author      : Lyubimov, A.Y.
Created     : 04/07/2015
Last Changed: 06/26/2015
Description : Analyzes integration results and outputs them in an accessible
              format. Includes unit cell analysis by hierarchical clustering
              (Zeldin, et al., Acta Cryst D, 2013). In case of multiple clusters
              outputs a file with list of integrated pickles that comprise each
              cluster. Populates a PHIL file for PRIME with information from
              integration results (e.g. unit cell, resolution, data path, etc.)
'''
import os
import numpy as np
from collections import Counter

import cPickle as pickle
from cctbx.uctbx import unit_cell
from xfel.clustering.cluster import Cluster

import prime.iota.iota_input as inp
from prime.iota.iota_input import Capturing
from prime.postrefine import mod_input


def make_prime_input(clean_results, sg, uc, data_path, iota_version, now):
  """ Imports default PRIME input parameters, modifies correct entries and
      prints out a starting PHIL file to be used with PRIME
  """

  res = np.mean([results['res'] for results in clean_results])
  img_pickle = clean_results[0]['img']
  pixel_size = pickle.load(open(img_pickle, "rb"))['PIXEL_SIZE']

  triclinic = ['P1']
  monoclinic = ['C2', 'P2']
  orthorhombic = ['P222', 'C222', 'I222', 'F222']
  tetragonal = ['I4', 'I422', 'P4', 'P422']
  hexagonal = ['P3', 'P312', 'P321', 'P6', 'P622']
  rhombohedral = ['R3', 'R32']
  cubic = ['F23', 'F432', 'I23', 'I432', 'P23', 'P432']

  if sg in triclinic:
    crystal_system = 'Triclinic'
  elif sg in monoclinic:
    crystal_system = 'Monoclinic'
  elif sg in orthorhombic:
    crystal_system = 'Orthorhombic'
  elif sg in tetragonal:
    crystal_system = 'Tetragonal'
  elif sg in hexagonal:
    crystal_system = 'Hexagonal'
  elif sg in rhombohedral:
    crystal_system = 'Rhombohedral'
  elif sg in cubic:
    crystal_system = 'Cubic'
  else:
    crystal_system = 'None'

  prime_params = mod_input.master_phil.extract()

  prime_params.data = [data_path]
  prime_params.run_no = '001'
  prime_params.title = 'Auto-generated by IOTA v{} on {}'.format(iota_version, now)
  prime_params.scale.d_min = res
  prime_params.postref.scale.d_min = res
  prime_params.postref.crystal_orientation.d_min = res
  prime_params.postref.reflecting_range.d_min = res
  prime_params.postref.unit_cell.d_min = res
  prime_params.postref.allparams.d_min = res
  prime_params.merge.d_min = res
  prime_params.target_unit_cell = unit_cell(uc)
  prime_params.target_space_group = sg
  prime_params.target_crystal_system = crystal_system
  prime_params.pixel_size_mm = pixel_size

  prime_phil = mod_input.master_phil.format(python_object=prime_params)

  with Capturing() as output:
    prime_phil.show()

  txt_out = ''
  for one_output in output:
    txt_out += one_output + '\n'

  prime_file = os.path.join(os.curdir, 'prime.phil')
  with open(prime_file, 'w') as pf:
    pf.write(txt_out)

def print_results(clean_results, gs_range, logfile):
  """ Prints diagnostics from the final integration run.

      input: clean_results - list of integrated pickles w/ integration data
             gs_range - range of the grid search

  """
  images = [results['img'] for results in clean_results]
  spot_heights = [results['sph'] for results in clean_results]
  sig_heights = [results['sih'] for results in clean_results]
  spot_areas = [results['spa'] for results in clean_results]
  resolutions = [results['res'] for results in clean_results]
  num_spots = [results['strong'] for results in clean_results]
  mosaicities = [results['mos'] for results in clean_results]

  cons_s = Counter(spot_heights).most_common(1)[0][0]
  cons_h = Counter(spot_heights).most_common(1)[0][0]
  cons_a = Counter(spot_areas).most_common(1)[0][0]

  final_table = []
  final_table.append("\n\n{:-^80}\n".format('ANALYSIS OF RESULTS'))
  final_table.append("Total images:          {}".format(len(images)))
  final_table.append("Avg. signal height:    {:<8.3f}  std. dev:    {:<6.2f}"\
                     "  max: {:<3}  min: {:<3}  consensus: {:<3}"\
                     "".format(np.mean(sig_heights), np.std(sig_heights),
                               max(sig_heights), min(sig_heights), cons_s))
  final_table.append("Avg. spot height:      {:<8.3f}  std. dev:    {:<6.2f}"\
                     "  max: {:<3}  min: {:<3}  consensus: {:<3}"\
                     "".format(np.mean(spot_heights), np.std(spot_heights),
                               max(spot_heights), min(spot_heights), cons_h))
  final_table.append("Avg. spot areas:       {:<8.3f}  std. dev:    {:<6.2f}"\
                    "  max: {:<3}  min: {:<3}  consensus: {:<3}"\
                    "".format(np.mean(spot_areas), np.std(spot_areas),
                              max(spot_areas), min(spot_areas), cons_a))
  final_table.append("Avg. resolution:       {:<8.3f}  std. dev:    {:<6.2f}"\
                     "  lowest: {:<6.3f}  highest: {:<6.3f}"\
                    "".format(np.mean(resolutions), np.std(resolutions),
                              max(resolutions), min(resolutions)))
  final_table.append("Avg. number of spots:  {:<8.3f}  std. dev:    {:<6.2f}"\
                    "".format(np.mean(num_spots), np.std(num_spots)))
  final_table.append("Avg. mosaicity:        {:<8.3f}  std. dev:    {:<6.2f}"\
                    "".format(np.mean(mosaicities), np.std(mosaicities)))

  for item in final_table:
      print item
      inp.main_log(logfile, item)


def unit_cell_single(logfile, clean_results):
  """ Generates unit cell, etc. info if only a single integration result exists.
  """
  int_file = clean_results[0]
  unit_cell = (int_file['a'], int_file['b'], int_file['c'],
               int_file['alpha'], int_file['beta'], int_file['gamma'])
  point_group = int_file['sg']

  print "\n\n{:-^80}\n".format(' UNIT CELL ANALYSIS ')
  inp.main_log(logfile, "\n\n{:-^80}\n".format(' UNIT CELL ANALYSIS '))

  uc_line = "{:<6} {:^4}:  {:<6.2f}, {:<6.2f}, {:<6.2f}, {:<6.2f}, "\
            "{:<6.2f}, {:<6.2f}".format('({})'.format(len(clean_results)),
                        point_group, unit_cell[0], unit_cell[1], unit_cell[2],
                        unit_cell[3], unit_cell[4], unit_cell[5])

  print uc_line
  inp.main_log(logfile, uc_line)

  return point_group, unit_cell


def unit_cell_analysis(cluster_threshold, logfile, int_pickle_file):
  """ Calls unit cell analysis module, which uses hierarchical clustering
      (Zeldin, et al, Acta D, 2015) to split integration results according to
      detected morphological groupings (if any). Most useful with preliminary
      integration without target unit cell specified.
      input: cluster_threshold - used for separating tree into clusters
             int_pickle_file - file with paths to integrated pickles

      output: uc_pick[1] - consensus point group
              uc_pick[2] - average consensus unit cell
              uc-pick[3] - output filename

  """

  uc_table = []
  uc_summary = []
  counter = 1

  # read full list of output pickles from file
  with open(int_pickle_file, 'r') as f:
    img_list = f.read().splitlines()

  # run hierarchical clustering analysis
  ucs = Cluster.from_files(img_list, use_b=True)
  clusters, _ = ucs.ab_cluster(cluster_threshold, log=False, write_file_lists=False,
                               schnell=False, doplot=False)

  uc_table.append("\n\n{:-^80}\n"\
                  "".format(' UNIT CELL ANALYSIS '))

  # extract clustering info and add to summary output list
  for cluster in clusters:
    sorted_pg_comp = sorted(cluster.pg_composition.items(),
                              key=lambda x: -1 * x[1])
    pg_nums = [pg[1] for pg in sorted_pg_comp]
    cons_pg = sorted_pg_comp[np.argmax(pg_nums)]

    output_dir = os.path.dirname(int_pickle_file)
    output_file = os.path.join(output_dir, "uc_cluster_{}.lst".format(counter))

    # write out lists of output pickles that comprise clusters with > 1 members
    if len(cluster.members) > 1:
      counter += 1
      cluster.dump_file_list(out_file_name=output_file)
      mark_output = os.path.basename(output_file)
    else:
      mark_output = ''

    # format and record output
    uc_line = "{:<6} {:^4}:  {:<6.2f} ({:>5.2f}), {:<6.2f} ({:>5.2f}), "\
              "{:<6.2f} ({:>5.2f}), {:<6.2f} ({:>5.2f}), "\
              "{:<6.2f} ({:>5.2f}), {:<6.2f} ({:>5.2f})   "\
              "{}".format('({})'.format(len(cluster.members)), cons_pg[0],
                          cluster.medians[0], cluster.stdevs[0],
                          cluster.medians[1], cluster.stdevs[1],
                          cluster.medians[2], cluster.stdevs[2],
                          cluster.medians[3], cluster.stdevs[3],
                          cluster.medians[4], cluster.stdevs[4],
                          cluster.medians[5], cluster.stdevs[5],
                          mark_output)
    uc_table.append(uc_line)

    if mark_output != '':
      out_file = os.path.abspath(output_file)
    else:
      out_file = os.path.abspath(int_pickle_file)

    uc_info = [len(cluster.members), cons_pg[0], cluster.medians, out_file, uc_line]
    uc_summary.append(uc_info)

  uc_table.append('\nMost common unit cell:\n')

  # select the most prevalent unit cell (most members in cluster)
  uc_freqs = [i[0] for i in uc_summary]
  uc_pick = uc_summary[np.argmax(uc_freqs)]
  uc_table.append(uc_pick[4])

  for item in uc_table:
      print item
      inp.main_log(logfile, item)

  return uc_pick[1], uc_pick[2], uc_pick[3]



def print_summary(gs_params, n_img, logfile, iota_version, now):
  """ Prints summary by reading contents of files listing
      a) images not integrated
      b) images that failed unit cell filter
      c) total images input
      d) final images successfully processed

      Appends summary to general log file. Also outputs some of it on stdout.

      input: gs_params - parameters from *.param file in PHIL format
  """

  summary = []
  int_fail_count = 0
  bad_int_count = 0
  final_count = 0

  print "\n\n{:-^80}\n".format('SUMMARY')
  inp.main_log(logfile, "\n\n{:-^80}\n".format('SUMMARY'))

  summary.append('raw images processed:                {}'.format(n_img))

  if os.path.isfile('{0}/blank_images.lst'.format(os.path.abspath(gs_params.output))):
    with open('{0}/blank_images.lst'.format(os.path.abspath(gs_params.output)),
              'r') as blank_img_list:
      blank_img_list_contents = blank_img_list.read()
      blank_img_count = len(blank_img_list_contents.splitlines())
    summary.append('raw images with no diffraction:      {}'.format(blank_img_count))

  if os.path.isfile('{0}/not_integrated.lst'.format(os.path.abspath(gs_params.output))):
    with open('{0}/not_integrated.lst'.format(os.path.abspath(gs_params.output)),
              'r') as int_fail_list:
      int_fail_list_contents = int_fail_list.read()
      int_fail_count = len(int_fail_list_contents.splitlines())
    summary.append('raw images not integrated:           {}'.format(int_fail_count))

  if os.path.isfile('{0}/prefilter_fail.lst'.format(os.path.abspath(gs_params.output))):
    with open('{0}/prefilter_fail.lst'.format(os.path.abspath(gs_params.output)),
            'r') as bad_int_list:
      bad_int_list_contents = bad_int_list.read()
      bad_int_count = len(bad_int_list_contents.splitlines())
    summary.append('images failed prefilter:             {}'.format(bad_int_count))

  if os.path.isfile('{0}/gs_selected.lst'.format(os.path.abspath(gs_params.output))):
    with open('{0}/gs_selected.lst'.format(os.path.abspath(gs_params.output)),
              'r') as sel_list:
      sel_list_contents = sel_list.read()
      sel_gs_count = len(sel_list_contents.splitlines())
    summary.append('images in grid search selection:     {}'.format(sel_gs_count))

  if os.path.isfile('{0}/integrated.lst'.format(os.path.abspath(gs_params.output))):
    with open('{0}/integrated.lst'.format(os.path.abspath(gs_params.output)),
              'r') as final_list:
      final_list_contents = final_list.read()
      final_count = len(final_list_contents.splitlines())
    summary.append('final integrated pickles:            {}'.format(final_count))

  for item in summary:
    print item
    inp.main_log(logfile, "{}".format(item))

  inp.main_log(logfile, '\n\nIOTA version {0}'.format(iota_version))
  inp.main_log(logfile, "{}\n".format(now))
