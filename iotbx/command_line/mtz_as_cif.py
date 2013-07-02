from __future__ import division
# LIBTBX_SET_DISPATCHER_NAME phenix.mtz_as_cif

import os
import sys
from cctbx.array_family import flex
from libtbx.utils import plural_s
from libtbx.utils import Usage
import iotbx.phil
import iotbx.cif.model
from iotbx import reflection_file_utils

phenix_to_cif_labels_dict = {
  'FOBS': '_refln.F_meas_au',
  'SIGFOBS': '_refln.F_meas_sigma_au',
  'IOBS': '_refln.F_squared_meas',
  'SIGIOBS': '_refln.F_squared_sigma',
  'FOBS(+)': '_refln.pdbx_F_plus',
  'SIGFOBS(+)': '_refln.pdbx_F_plus_sigma',
  'FOBS(-)': '_refln.pdbx_F_minus',
  'SIGFOBS(-)': '_refln.pdbx_F_minus_sigma',
  'IOBS(+)': '_refln.pdbx_I_plus',
  'SIGIOBS(+)': '_refln.pdbx_I_plus_sigma',
  'IOBS(-)': '_refln.pdbx_I_minus',
  'SIGIOBS(-)': '_refln.pdbx_I_minus_sigma',
  'F-obs': '_refln.F_meas_au',
  'SIGF-obs': '_refln.F_meas_sigma_au',
  'F-obs(+)': '_refln.pdbx_F_plus',
  'SIGF-obs(+)': '_refln.pdbx_F_plus_sigma',
  'F-obs(-)': '_refln.pdbx_F_minus',
  'SIGF-obs(-)': '_refln.pdbx_F_minus_sigma',
  'I-obs': '_refln.F_squared_meas',
  'SIGI-obs': '_refln.F_squared_sigma',
  'I-obs(+)': '_refln.pdbx_I_plus',
  'SIGI-obs(+)': '_refln.pdbx_I_plus_sigma',
  'I-obs(-)': '_refln.pdbx_I_minus',
  'SIGI-obs(-)': '_refln.pdbx_I_minus_sigma',
  'R-free-flags': '_refln.phenix_R_free_flags',
  'HLA': '_refln.pdbx_HL_A_iso',
  'HLB': '_refln.pdbx_HL_B_iso',
  'HLC': '_refln.pdbx_HL_C_iso',
  'HLD': '_refln.pdbx_HL_D_iso',
  '2FOFCWT': '_refln.pdbx_FWT',
  'PH2FOFCWT': '_refln.pdbx_PHWT',
  'FOFCWT': '_refln.pdbx_DELFWT',
  'PHFOFCWT': '_refln.pdbx_DELPHWT',
  }

# Source: http://www.ccp4.ac.uk/html/cif2mtz.html
ccp4_to_cif_labels_dict = {
  'FWT': '_refln.pdbx_FWT',
  'PHWT': '_refln.pdbx_PHWT',
  'DELFWT': '_refln.pdbx_DELFWT',
  'DELPHWT': '_refln.pdbx_DELPHWT',
  'FREE': '_refln.status',
  'F': '_refln.F_meas_au',
  'SIGF': '_refln.F_meas_sigma_au',
  'FP': '_refln.F_meas_au',
  'SIGFP': '_refln.F_meas_sigma_au',
  'FC': '_refln.F_calc_au',
  'PHIC': '_refln.phase_calc',
  'PHIB': '_refln.phase_meas',
  'FOM': '_refln.fom',
  'I': '_refln.intensity_meas',
  'I': '_refln.F_squared_meas', # which I to prefer?
  'SIGI': '_refln.intensity_sigma',
  'SIGI': '_refln.F_squared_sigma', # which SIGI to prefer?
  'FPART': '_refln.F_part_au',
  'PHIP': '_refln.phase_part',
  'F(+)': '_refln.pdbx_F_plus',
  'SIGF(+)': '_refln.pdbx_F_plus_sigma',
  'F(-)': '_refln.pdbx_F_minus',
  'SIGF(-)': '_refln.pdbx_F_minus_sigma',
  'DP': '_refln.pdbx_anom_difference',
  'SIGDP': '_refln.pdbx_anom_difference_sigma',
  'I(+)': '_refln.pdbx_I_plus',
  'SIGI(+)': '_refln.pdbx_I_plus_sigma',
  'I(-)': '_refln.pdbx_I_minus',
  'SIGI(-)': '_refln.pdbx_I_minus_sigma',
  'HLA': '_refln.pdbx_HL_A_iso',
  'HLB': '_refln.pdbx_HL_B_iso',
  'HLC': '_refln.pdbx_HL_C_iso',
  'HLD': '_refln.pdbx_HL_D_iso',
}

def mtz_to_cif_label(mtz_to_cif_label_dict, mtz_label):
  if mtz_label.endswith("xray"):
    mtz_label = mtz_label[:-5]
  elif mtz_label.endswith("neutron"):
    mtz_label = mtz_label[:-8]
  elif mtz_label.endswith(("_X", "_N")):
    mtz_label = mtz_label[:-2]
  cif_label = mtz_to_cif_label_dict.get(mtz_label)
  if cif_label is None:
    # to catch e.g. IOBS_N(+), SIGIOBS_N(+), IOBS_N(-), SIGIOBS_N(-)
    mtz_label = mtz_label.replace("_N", "").replace("_X", "")
    cif_label = mtz_to_cif_label_dict.get(mtz_label)
  return cif_label

master_phil = iotbx.phil.parse("""
mtz_as_cif
  .short_caption = MTZ as mmCIF
  .caption = This program will convert reflections in MTZ format to mmCIF, \
    suitable for PDB deposition.  Note that phenix.refine can also write \
    mmCIF files directly if desired.
  .style = auto_align box \
    caption_img:icons/custom/phenix.reflection_file_editor.png
{
mtz_file = None
  .type = path
  .multiple = True
  .short_caption = MTZ file
  .style = file_type:mtz input_file bold
output_file = None
  .type = path
  .help = Optional output file name to override default
  .optional = True
  .help = 'Enter a .cif output name'
  .style = file_type:cif bold new_file
mtz_labels = None
  .help = Custom input labels for unknown MTZ columns
  .short_caption = Custom input labels
  .type = strings
cif_labels = None
  .help = Custom output labels for unknown mmCIF columns
  .short_caption = Custom output labels
  .type = strings
}
""")

def run(args, params=None, out=sys.stdout):
  from iotbx import file_reader
  work_params = params
  if (work_params is None) :
    cmdline = iotbx.phil.process_command_line_with_files(
      args=args,
      master_phil=master_phil,
      reflection_file_def="mtz_as_cif.mtz_file")
    work_params = cmdline.work.extract()
  if (len(work_params.mtz_as_cif.mtz_file) == 0) :
    raise Usage("phenix.mtz_as_cif data.mtz [params.eff] [options ...]")
  work_params = work_params.mtz_as_cif
  mtz_objects = []
  for file_name in work_params.mtz_file :
    input_file = file_reader.any_file(file_name)
    input_file.check_file_type("hkl")
    if (input_file.file_object.file_type() != 'ccp4_mtz') :
      raise Sorry("Error reading '%s' - only MTZ files may be used as input."
        % file_name)
    mtz_objects.append(input_file.file_object.file_content())
  assert (len(mtz_objects) != 0)
  custom_cif_labels_dict = {}
  if work_params.mtz_labels is not None and work_params.cif_labels is not None:
    assert len(work_params.mtz_labels) == len(work_params.cif_labels)
    for mtz_label, cif_label in zip(work_params.mtz_labels, work_params.cif_labels):
      custom_cif_labels_dict.setdefault(mtz_label, cif_label)
  output_files = []
  for mtz_file_name, mtz_object in zip(work_params.mtz_file, mtz_objects):
    print >> out, "Converting %s" %mtz_file_name
    cif_blocks = mtz_as_cif_blocks(
      mtz_object, custom_cif_labels_dict=custom_cif_labels_dict).cif_blocks

    prefix = os.path.splitext(os.path.basename(mtz_file_name))[0]
    output_file = work_params.output_file
    if output_file is None:
      output_file = prefix + ".reflections.cif"
    cif_model = iotbx.cif.model.cif()
    if cif_blocks["xray"] is not None:
      cif_model[prefix] = cif_blocks["xray"].cif_block
    if cif_blocks["neutron"] is not None:
      cif_model[prefix+"_neutron"] = cif_blocks["neutron"].cif_block
    with open(output_file, "wb") as f:
      print >> out, "Writing data and map coefficients to CIF file:\n  %s" % \
        (f.name)
      print >> f, cif_model
      output_files.append(output_file)
  return output_files

class mtz_as_cif_blocks(object):

  def __init__(self, mtz_object, custom_cif_labels_dict=None, log=None,
      test_flag_value=None):

    self.cif_blocks = {
      'xray': None,
      'neutron': None
    }

    if log is None: log = sys.stdout

    miller_arrays = mtz_object.as_miller_arrays()

    miller_arrays_as_cif_block = None

    input_observations_xray = None
    input_observations_neutron = None
    r_free_xray = None
    r_free_neutron = None
    f_obs_filtered_xray = None
    f_obs_filtered_neutron = None

    mtz_to_cif_labels_dict = {}
    mtz_to_cif_labels_dict.update(phenix_to_cif_labels_dict)
    mtz_to_cif_labels_dict.update(ccp4_to_cif_labels_dict)
    if custom_cif_labels_dict is not None:
      mtz_to_cif_labels_dict.update(custom_cif_labels_dict)

    unknown_mtz_labels = []

    for array in miller_arrays:
      labels = array.info().labels
      label = labels[0]
      if reflection_file_utils.looks_like_r_free_flags_info(array.info()):
        if "(+)" in label:
          array = array.average_bijvoet_mates()
          labels = [label.replace("(+)", "")]
        if label.endswith(("neutron", "_N")):
          r_free_neutron = array
        else:
          r_free_xray = array
        continue # deal with these later
      elif label.startswith("F-obs-filtered"):
        if label.endswith(("neutron", "_N")):
          f_obs_filtered_neutron = array
        else:
          f_obs_filtered_xray = array
      elif label.startswith("F-obs") or label.startswith("I-obs"):
        if label.strip("(+)").endswith(("neutron", "_N")):
          input_observations_neutron = array
        else:
          input_observations_xray = array
      #elif label.startswith("R-free-flags"):
      column_names = []
      for mtz_label in labels:
        cif_label = mtz_to_cif_label(mtz_to_cif_labels_dict, mtz_label)
        column_names.append(cif_label)
      if column_names.count(None) > 0:
        # I don't know what to do with this array
        for i, mtz_label in enumerate(labels):
          if column_names[i] is None:
            unknown_mtz_labels.append(mtz_label)
        continue
      assert column_names.count(None) == 0
      if labels[0].strip("(+)").endswith(("neutron", "_N")):
        data_type = "neutron"
      else:
        data_type = "xray"
      if column_names[0].startswith(("_refln.F_meas",
                                     "_refln.F_squared_meas",
                                     "_refln.pdbx_F_",
                                     "_refln.pdbx_I_")):
        if data_type == "neutron":
          input_observations_neutron = array
        else:
          input_observations_xray = array

      if self.cif_blocks.get(data_type) is None:
        self.cif_blocks[data_type] = iotbx.cif.miller_arrays_as_cif_block(
          array=array, column_names=column_names, format="mmcif")
      else:
        self.cif_blocks[data_type].add_miller_array(array, column_names=column_names)

    if len(unknown_mtz_labels):
      print >> log, "Warning: Unknown mtz label%s: %s" %(
        plural_s(len(unknown_mtz_labels))[1], ", ".join(unknown_mtz_labels))
      print >> log, "  Use mtz_labels and cif_labels keywords to provide translation for custom labels."

    data_types = set(["xray"])
    if self.cif_blocks['neutron'] is not None:
      data_types.add("neutron")

    if input_observations_xray is None and f_obs_filtered_xray is not None:
      self.cif_blocks["xray"].add_miller_array(
        array=f_obs_filtered_xray,
        column_names=('_refln.F_meas_au','_refln.F_meas_sigma_au'))
    if input_observations_neutron is None and f_obs_filtered_neutron is not None:
      self.cif_blocks["neutron"].add_miller_array(
        array=f_obs_filtered_neutron,
        column_names=('_refln.F_meas_au','_refln.F_meas_sigma_au'))

    for data_type in data_types:
      if data_type == "xray":
        r_free = r_free_xray
        input_obs = input_observations_xray
        f_obs_filtered = f_obs_filtered_xray
        if (self.cif_blocks["xray"] is None and r_free_xray is not None and
            self.cif_blocks["neutron"] is not None and r_free_neutron is None):
          r_free_neutron = r_free_xray
      elif data_type == "neutron":
        r_free = r_free_neutron
        input_obs = input_observations_neutron
        f_obs_filtered = f_obs_filtered_neutron
      if self.cif_blocks[data_type] is not None and r_free is not None:
        self.cif_blocks[data_type].add_miller_array(
          array=r_free, column_name='_refln.phenix_R_free_flags')

      if input_obs is None or r_free is None: continue
      if (test_flag_value is None) :
        test_flag_value = reflection_file_utils.guess_r_free_flag_value(
          miller_array=r_free)
      assert (test_flag_value is not None)
      refln_status = r_free.array(data=flex.std_string(r_free.size(), "."))
      input_obs_non_anom = input_obs.average_bijvoet_mates()
      match = r_free.match_indices(input_obs_non_anom)
      refln_status.data().set_selected(match.pair_selection(0), "o")
      refln_status.data().set_selected(r_free.data() == test_flag_value, "f")
      if f_obs_filtered is not None:
        f_obs_filtered_non_anom = f_obs_filtered.average_bijvoet_mates()
        match = r_free.match_indices(f_obs_filtered_non_anom)
        refln_status.data().set_selected(match.single_selection(0), "<") # XXX
      self.cif_blocks[data_type].add_miller_array(
        array=refln_status, column_name="_refln.status")

def validate_params (params) :
  if (len(params.mtz_as_cif.mtz_file) == 0) :
    raise Sorry("No MTZ file(s) specified!")
  return True

if __name__ == '__main__':
  run(sys.argv[1:])
