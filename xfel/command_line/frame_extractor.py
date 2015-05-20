from __future__ import division
# -*- mode: python; coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# LIBTBX_SET_DISPATCHER_NAME cxi.frame_extractor
# LIBTBX_SET_DISPATCHER_NAME xfel.frame_extractor
#
# $Id: frame_extractor.py idyoung $

from dials.array_family import flex
from dials.util.options import Importer, flatten_reflections, flatten_experiments, OptionParser
from cctbx import crystal, miller
from cctbx.crystal_orientation import crystal_orientation
import iotbx.phil
import cctbx, os
from libtbx import easy_pickle

class ConstructFrame(object):
  def get_template_pickle(self):
    return {'current_cb_op_to_primitive': 0,
                       'current_orientation':0,
                       'distance':0,
                       'effective_tiling':0,
                       'mapped_predictions':[[]],
                       'max_signal':0,
                       'ML_domain_size_ang':[0],
                       'ML_half_mosaicity_deg':[0],
                       'mosaicity':0,
                       'model_partialities':[None],
                       'observations':[0],
                       'pointgroup':0,
                       'residual':0,
                       'sa_parameters':['None'],
                       'wavelength':0,
                       'xbeam':0,
                       'ybeam':0}

  def __init__(self, reflections, experiment):
    # assemble template and unpack files
    self.frame = self.get_template_pickle()
    self.pixel_size = experiment.detector[0].get_pixel_size()[0]

    if reflections.has_key('intensity.prf.value'):
      self.method = 'prf' # integration by profile fitting
    elif reflections.has_key('intensity.sum.value'):
      self.method = 'sum' # integration by simple summation
    self.reflections = reflections.select(reflections['intensity.' + self.method + '.variance'] > 0) # keep only spots with sigmas above zero

    self.xtal = experiment.crystal
    self.beam_obj = experiment.beam
    self.det = experiment.detector
    self.gonio = experiment.goniometer
    self.scan = experiment.scan
    self.img_sweep = experiment.imageset

  # experiment-dependent components ---------------------------------------------------------------------------

  # get wavelength
  def populate_wavelength(self):
    assert self.beam_obj.get_wavelength() is not None, "no wavelength"
    self.frame['wavelength'] = self.beam_obj.get_wavelength()

  # get detector distance in mm
  def populate_distance(self):
    assert self.det[0].get_distance() is not None, "no detector distance"
    self.frame['distance'] = self.det[0].get_distance()

  # get xbeam and ybeam in mm
  def populate_beam_dir(self):
    assert self.beam_obj.get_s0() is not None, "no beam direction"
    self.frame['xbeam'], self.frame['ybeam'] = self.det[0].get_beam_centre(self.beam_obj.get_s0())

  # get max signal
  def populate_max_signal(self):
    pass

  # get effective tiling
  def populate_effective_tiling(self):
    pass

  # indicate simulated annealing parameters, if present
  def populate_sa_params(self):
    pass

  # crystal-dependent components ------------------------------------------------------------------------------

  # generate a crystal orientation object from the A* matrix
  def populate_orientation(self):
    assert self.xtal.get_A() is not None, "no crystal orientation matrix"
    self.frame['current_orientation'] = [crystal_orientation(self.xtal.get_A().elems, True)]

  # generate change-of-basis operation for current to primitive cell
  def populate_op_to_primitive(self):
    assert self.xtal.get_space_group() is not None, "no space group"
    self.frame['current_cb_op_to_primitive'] = [self.xtal.get_space_group().z2p_op()]

  # fetch the point group associated with the crystal
  def populate_point_group(self):
    assert self.xtal.get_space_group() is not None, "no space group"
    self.frame['pointgroup'] = str(self.xtal.get_space_group().build_derived_point_group().info())

  # get mosaicity
  def populate_mosaicity(self):
    assert self.xtal.get_mosaicity() is not None, "no mosaicity"
    self.frame['mosaicity'] = self.xtal.get_mosaicity()

  # get any available ML values
  def populate_ML_values(self):
    try:
      self.frame['ML_half_mosaicity_deg'] = [self.xtal._ML_half_mosaicity_deg]
    except AttributeError:
      pass
    try:
      self.frame['ML_domain_size_ang'] = [self.xtal._ML_domain_size_ang]
    except AttributeError:
      pass

  # observations-dependent components -------------------------------------------------------------------------

  # generate a miller array containing the Miller indices, intensities and variances for one frame
  def populate_observations(self):
    intensities = self.reflections['intensity.' + self.method + '.value']
    variances = self.reflections['intensity.' + self.method + '.variance']
    space_group = crystal.symmetry(self.xtal.get_unit_cell(), str(self.xtal.get_space_group().info()))
    miller_set = miller.set(space_group, self.reflections['miller_index'])
    self.frame['observations'][0] = cctbx.miller.array(miller_set, intensities, flex.sqrt(variances)).set_observation_type_xray_intensity()

  # collect predicted spot positions
  def populate_pixel_positions(self):
    assert self.reflections.has_key('xyzcal.px'), "no calculated spot positions"
    self.frame['mapped_predictions'][0] = flex.vec2_double()
    for i in xrange(len(self.reflections['xyzcal.px'])):
      self.frame['mapped_predictions'][0].append(tuple(self.reflections['xyzcal.px'][i][0:2]))

  # generate a list of dictionaries containing a series of corrections for each predicted reflection
  def populate_corrections(self):
    assert self.reflections.has_key('xyzobs.px.value') and self.reflections.has_key('xyzcal.px'), "no calculated or observed spot positions"
    assert self.frame['xbeam'] is not 0 and self.frame['ybeam'] is not 0, "invalid beam center"
    self.frame['correction_vectors'] = [[]]
    for idx in xrange(len(self.reflections['xyzobs.px.value'])):
      if self.reflections['xyzcal.px'][idx][0:2] != self.reflections['xyzobs.px.value'][idx][0:2]:
        theoret_center = 1765/2, 1765/2
        refined_center = self.frame['xbeam']/self.pixel_size, self.frame['ybeam']/self.pixel_size # px to mm conversion
        hkl = self.reflections['miller_index'][idx]
        obsspot = tuple(self.reflections['xyzobs.px.value'][idx][0:2])
        predspot = tuple(self.reflections['xyzcal.px'][idx][0:2])
        self.frame['correction_vectors'][0].append({'refinedcenter':refined_center, 'hkl':hkl, 'setting_id':0, 'azimuthal':0, 'radial':0,
          'obsspot':obsspot, 'obscenter':theoret_center, 'predspot':predspot})

  # get partialities
  def populate_partialities(self):
    pass

  # produce residuals
  def populate_residuals(self):
    pass

  # combine all of the above
  def make_frame(self):
    self.populate_wavelength()
    self.populate_distance()
    self.populate_beam_dir()
    self.populate_max_signal()
    self.populate_effective_tiling()
    self.populate_sa_params()
    self.populate_orientation()
    self.populate_op_to_primitive()
    self.populate_point_group()
    self.populate_mosaicity()
    self.populate_ML_values()
    self.populate_observations()
    self.populate_pixel_positions()
    # self.populate_corrections() # works, but unnecessary
    self.populate_partialities()
    self.populate_residuals()
    return self.frame

class ConstructFrameFromFiles(ConstructFrame):
  def __init__(self, pickle_name, json_name):
    # load the integration.pickle file (reflection table) into memory and
    # load the experiments.json file (json) into memory, piecewise.
    # check_format=False because we don't wont to load any imagesets in the
    # experiement list
    importer = Importer([pickle_name, json_name], read_experiments=True, read_reflections=True, check_format=False)
    if importer.unhandled:
      print "unable to process:", importer.unhandled

    ConstructFrame.__init__(self, flatten_reflections(importer.reflections)[0],
                                  flatten_experiments(importer.experiments)[0])

if __name__ == "__main__":
  master_phil_scope = iotbx.phil.parse("""
    pickle_name = None
      .type = path
      .help = path to a reflection table (integrated.pickle) file
    json_name = None
      .type = path
      .help = path to an experiments.json file
    output_dir = None
      .type = path
      .help = if set, path to directory to save the new pickle file
      """)
  parser = OptionParser(phil=master_phil_scope)
  params, options = parser.parse_args(show_diff_phil=True)
  frame = ConstructFrameFromFiles(params.pickle_name, params.json_name).make_frame()
  if not params.output_dir is None:
    assert os.path.isdir(params.output_dir)
    dest_path = os.path.splitext(params.pickle_name)[0] + "_extracted.pickle"
    assert not os.path.isfile(dest_path)
    easy_pickle.dump(dest_path, frame)
