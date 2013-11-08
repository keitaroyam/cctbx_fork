from __future__ import division
#Phil parameters required to process data from Stanford LCLS CXI instrument

def cxi_basic_start():
  from labelit import preferences
  from rstbx.command_line.index import special_defaults_for_new_horizons
  new_horizons_phil = preferences.RunTimePreferences()
  special_defaults_for_new_horizons( new_horizons_phil )

  common_arguments = [
          "distl.bins.verbose=True",
          "distl.minimum_spot_area=3",
          "distl.peripheral_margin=1",
          "distl.peak_intensity_maximum_factor=10000.", #avoids intensity filter
          "distl.compactness_filter=True",
  ]

  new_horizons_phil.merge_command_line(common_arguments)

  return new_horizons_phil

def cxi_versioned_extract(*args):

  # args is one or more lists of phil parameters, as would be passed
  # in through the command line; to be processed sequentially.

  working_phil = cxi_basic_start()

  for arg in args:
    working_phil.merge_command_line(arg)

  #distl_args = [a.object.as_str().strip() for a in working_phil.phil_scope.all_definitions()]

  cxi_version = working_phil.phil_scope.get("distl.detector_format_version"
                ).extract().detector_format_version

  if cxi_version in ["CXI 3.1","CXI 3.2"]:
    from spotfinder.applications.xfel import cxi_run3
    # run 3 tiles from distl.find_active_area, plus initial tile translations
    #   derived from a lysozyme powder pattern, before auxiliary adjustments from Bragg spots
    run_3_tiling_arguments = [
       "distl.detector_tiling=%s"%cxi_run3.run3_cxi_limits().as_string(),
    ] + cxi_run3.lysozyme_calibration()

    working_phil.merge_command_line(run_3_tiling_arguments)

    working_extract = working_phil.command_extractor

    corrected_auxiliary_translations = [ 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,
                               0,1,0,0,0,0,0,0,0,0,-1,3,-1,4,2,0,3,0,0,0,
                               0,0,0,0,1,3,-1,4,4,0,-1,1,0,4,3,-3,2,-1,1,3,
                               0,0,5,0,-1,2,0,0,1,0,0,0,-1,1,0,2,2,1,2,-1,
                               2,0,1,2,1,1,1,-6,0,0,2,3,0,2,2,3,2,-2,0,0,
                               0,0,0,0,0,0,0,0,-2,1,0,0,0,2,0,0,0,0,0,0,]
    from scitbx.array_family import flex
    total_tile_translations = flex.int(
      [int(a) for a in working_extract.distl.tile_translations]
      )+flex.int(corrected_auxiliary_translations)

    TT = list(total_tile_translations)
    working_extract.distl.tile_translations = TT

    return working_extract
  elif cxi_version in ["CXI 4.1"]:
    working_extract = working_phil.command_extractor

    corrected_auxiliary_translations = [
                               0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                               0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,0,-1,
                               0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                               0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                               0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-2,
                               0,0,0,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                               0,0,0,0,0,0,0,0]

    from scitbx.array_family import flex
    total_tile_translations = flex.int(corrected_auxiliary_translations)

    TT = list(total_tile_translations)
    working_extract.distl.tile_translations = TT
    #working_extract.distl.quad_translations = [0,0,0,0,0,0,0,0]
    #working_extract.distl.quad_translations = [5,-5,6,-9,-5,-2,0,-8]
    working_extract.distl.quad_translations = [6,-2,7,-4,-4,1,1,-5]
    return working_extract

  elif cxi_version in ["CXI 5.1"]:
    working_extract = working_phil.command_extractor

    # The auxiliary translations are modified with respect to CXI 4.1.  If the
    # SLAC-provided metrology were to be trusted, this would be be all
    # zeros?
    corrected_auxiliary_translations = [
                               1,-1,1,0,0,-1,0,-1,2,0,0,0,3,1,2,0,2,-1,2,-1,
                               0,0,1,0,1,-2,1,-3,0,-1,0,-1,-2,1,0,1,-1,0,0,0,
                               0,2,-1,1,0,2,-1,2,0,0,0,0,0,0,1,1,1,0,0,0,
                               -1,0,-1,0,1,1,0,0,0,1,0,1,0,-1,0,0,1,-2,0,0,
                               -1,-2,-1,-1,0,0,-1,-1,0,0,0,1,-1,-1,0,0,1,-2,1,-1,
                               1,-1,0,0,0,-2,0,-3,1,-4,1,-4,-2,0,-1,-1,0,0,-1,-1,
                               -1,1,-1,0,0,1,0,1]

    from scitbx.array_family import flex
    total_tile_translations = flex.int(corrected_auxiliary_translations)

    TT = list(total_tile_translations)
    working_extract.distl.tile_translations = TT

    # Order: UL x, UL y, UR x, UR y, LL x, LL y, LR x, LR y
    working_extract.distl.quad_translations = [-3,-1,-1,-5,-13,2,-7,-4]
    return working_extract

  elif cxi_version in ["CXI 6.1"]:
    working_extract = working_phil.command_extractor
    corrected_auxiliary_translations = [
       2,  1,  1,  1,  1,  3, -1,  2,  3,  1,
       1,  0,  5,  2,  4,  1,  2, -1,  2,  0,
       2,  1,  2,  0, -1, -2, -1, -2, -1,  0,
      -2,  1, -1,  0,  0,  1,  1,  0,  1,  1,
      -1,  0, -1,  0, -1,  0, -1,  0,  0,  0,
      -1,  0,  1,  0,  1,  0,  0,  1,  1,  2,
      -1,  1,  0,  2, -1,  1,  0,  1,  0,  0,
       1,  0, -2,  0, -1,  1, -2, -1, -2,  1,
      -2,  0, -1,  1, -3, -1, -3,  0,  0,  1,
       0,  1,  0,  0,  1,  0,  2,  0,  2, -1,
       1,  0,  0, -1,  0,  0,  1, -2,  1, -1,
       2, -2, -1,  0,  0, -1, -2,  1,  0,  0,
      -1,  0, -1, -1,  1,  1,  1, -1]

    from scitbx.array_family import flex
    total_tile_translations = flex.int(corrected_auxiliary_translations)

    TT = list(total_tile_translations)
    working_extract.distl.tile_translations = TT

    # Order: UL x, UL y, UR x, UR y, LL x, LL y, LR x, LR y
    working_extract.distl.quad_translations = [0,7,13,8,-8,0,11,-3]
    return working_extract

  elif cxi_version in ["CXI 7.1"]:
    working_extract = working_phil.command_extractor
    corrected_auxiliary_translations = [
       2,  1,  1,  1,  1,  2,  0,  2,  3,  0,
       0,  0,  4,  1,  3,  1,  1, -2,  2, -1,
      -1, -1,  1, -1, -1, -2, -1, -1, -1,  0,
      -1,  1, -2,  0,  0,  1,  0,  0,  1,  1,
      -1,  1, -2,  1, -1,  0, -1,  1, -1,  1,
      -1,  1, -2,  1, -1,  1,  1,  1,  0,  2,
      -1,  1,  0,  1,  0,  1,  0,  1,  0,  0,
       0,  1, -1,  0,  0,  1,  0, -1, -1,  1,
      -1,  0, -1,  1, -1,  0, -2,  0,  0,  1,
       0,  1, -1,  0,  1,  0,  2, -1,  2, -1,
       1,  0,  0,  0,  1, -1,  1, -2,  2, -2,
       2, -2,  0, -1,  1, -1,  2,  1,  0,  0,
       0,  0,  0, -2,  1,  1,  1,  0]

    from scitbx.array_family import flex
    total_tile_translations = flex.int(corrected_auxiliary_translations)

    TT = list(total_tile_translations)
    working_extract.distl.tile_translations = TT

    # Order: UL x, UL y, UR x, UR y, LL x, LL y, LR x, LR y
    working_extract.distl.quad_translations = [2,-6,3,-6,-7,0,-1,-4]
    return working_extract

  elif cxi_version in ["CXI 7.d"]:
    working_extract = working_phil.command_extractor

    corrected_auxiliary_translations = [
       1,  1,  1,  0,  0,  0,  0,  0, -2, -1,
      -1, -1, -1, -3,  0, -3,  2,  3,  2,  1,
      -1,  4, -1,  2,  0,  1,  1,  1,  0,  2,
      -1,  2,  0,  0,  0,  0,  0,  0,  0,  0,
      -3, -2, -3, -1, -2, -1, -2, -1,  3, -3,
       3, -3,  5, -2,  4, -2,  2, -1,  2, -1,
       2, -2,  2, -1,  1,  1,  1,  0,  0,  0,
       0, -1, -1,  2, -2,  2, -2,  0, -1,  0,
      -1, -2, -1, -1, -3, -1, -3, -1,  3,  0,
       2,  0,  2,  0,  2,  0,  1,  0,  0,  0,
       0,  0, -1,  0,  0, -1,  0, -1,  1, -2,
       1, -2, -6,  0, -6,  0, -5,  1, -5,  1,
      -5, -2, -5, -3, -4, -2, -4, -2]

    from scitbx.array_family import flex
    total_tile_translations = flex.int(corrected_auxiliary_translations)

    TT = list(total_tile_translations)
    working_extract.distl.tile_translations = TT

    # Order: UL x, UL y, UR x, UR y, LL x, LL y, LR x, LR y
    working_extract.distl.quad_translations = [-6,-2,9,2,-14,-8,7,-12]
    return working_extract

  elif cxi_version in ["XPP 7.1"]:
    working_extract = working_phil.command_extractor

    corrected_auxiliary_translations = [
       0,  0, -1, -1,  0,  0, -1,  0,  0,  0,
       0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
       0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
       1, -1, -2,  0, -2,  1, -1, -1, -1,  0,
       0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
       0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
       0,  0, -1,  3,  0,  0,  0, -1,  1,  0,
       0, -1,  0,  0,  0,  0,  0,  0,  0,  0,
       0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
       0,  0,  0,  0,  0, -1,  0,  0,  1,  0,
       0,  0,  1,  0,  0,  0,  0,  0,  0,  0,
       0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
       0,  0,  0,  0,  0,  0,  0, -1]

    from scitbx.array_family import flex
    total_tile_translations = flex.int(corrected_auxiliary_translations)

    TT = list(total_tile_translations)
    working_extract.distl.tile_translations = TT

    # Order: UL x, UL y, UR x, UR y, LL x, LL y, LR x, LR y.  For the
    # XPP CSPAD, this is effectively correcting for the beam center.
    working_extract.distl.quad_translations = [-3, -21,
                                               -3, -22,
                                               -3, -21,
                                                2, -21]
    return working_extract

  elif cxi_version in ["XPP 7.marccd"]:
    working_extract = working_phil.command_extractor
    working_extract.distl.quad_translations = None
    working_extract.distl.tile_translations = [0, 0]
    return working_extract

  elif cxi_version in ["CXI 8.1inheritedfrom7.1"]:
    working_extract = working_phil.command_extractor
    corrected_auxiliary_translations = [
       2,  1,  1,  1,  1,  2,  0,  2,  3,  0,
       0,  0,  4,  1,  3,  1,  1, -2,  2, -1,
      -1, -1,  1, -1, -1, -2, -1, -1, -1,  0,
      -1,  1, -2,  0,  0,  1,  0,  0,  1,  1,
      -1,  1, -2,  1, -1,  0, -1,  1, -1,  1,
      -1,  1, -2,  1, -1,  1,  1,  1,  0,  2,
      -1,  1,  0,  1,  0,  1,  0,  1,  0,  0,
       0,  1, -1,  0,  0,  1,  0, -1, -1,  1,
      -1,  0, -1,  1, -1,  0, -2,  0,  0,  1,
       0,  1, -1,  0,  1,  0,  2, -1,  2, -1,
       1,  0,  0,  0,  1, -1,  1, -2,  2, -2,
       2, -2,  0, -1,  1, -1,  2,  1,  0,  0,
       0,  0,  0, -2,  1,  1,  1,  0]

    from scitbx.array_family import flex
    total_tile_translations = flex.int(corrected_auxiliary_translations)

    TT = list(total_tile_translations)
    working_extract.distl.tile_translations = TT

    # Order: UL x, UL y, UR x, UR y, LL x, LL y, LR x, LR y
    working_extract.distl.quad_translations = [-22,-4,-14,11,0,8,2,-5]
    return working_extract

  elif cxi_version in ["CXI 8.1"]: # developed against "run 4 optical metrology"
    working_extract = working_phil.command_extractor
    corrected_auxiliary_translations = [
      -1,  3,  2,  2, -1, -1,  1, -1,  0,  1,
      -1,  2, -1,  2, -1,  3,  2,  2,  2,  2,
       0,  2,  0,  2,  1,  1,  3, -1,  3,  4,
       3,  2,  1,  0,  1, -3, -1,  0, -2, -3,
       0,  1,  1,  0,  1,  2,  2,  2,  2, -1,
       3, -1,  4,  1,  4,  1,  2, -4,  1, -5,
       2, -5,  0, -5,  2, -2, -1, -2,  1,  1,
      -2,  1,  0, -3,  0, -3,  1, -4,  1, -5,
      -2, -1, -2, -2, -2, -1, -2, -1, -2, -1,
      -4,  1, -3, -2, -4,  1, -1, -2,  0,  1,
       2, -1,  2,  2, -1,  1, -2,  0, -2, -1,
      -2, -2, -3,  2, -5,  3, -5,  3, -5,  3,
      -1,  3,  0,  4, -1,  4,  1,  4]

    from scitbx.array_family import flex
    total_tile_translations = flex.int(corrected_auxiliary_translations)

    TT = list(total_tile_translations)
    working_extract.distl.tile_translations = TT

    # Order: UL x, UL y, UR x, UR y, LL x, LL y, LR x, LR y
    # Note, these numbers are valid for the CSPAD detector at roughly 100 mm distance
    working_extract.distl.quad_translations = [-14,7,-4,7,-22,0,-12,-4]

    # Due to a slight angle in the rail, if the detector is at the back of its
    # stage, around 548 mm, use these numbers instead.  They represent a change
    # of beam center due to a small translation at that distance
    #working_extract.distl.quad_translations = [-10,5,0,5,-18,-2,-8,-6]

    return working_extract

  else:
    return working_phil.command_extractor
