from __future__ import division
import os

def integrate_one_image(data, **kwargs):
  from xfel.cxi.display_spots import run_one_index_core
  from labelit.dptbx.error import NoAutoIndex
  from libtbx.utils import Sorry
  from spotfinder.exception import SpotfinderError
  from labelit.exception import AutoIndexError

  basename = kwargs.get("integration_basename")
  if (basename is None):
    basename = ""

  dirname  = kwargs.get("integration_dirname")
  if (dirname is None):
    dirname = "integration"
  if (not os.path.isdir(dirname)):
    os.makedirs(dirname)

  path = os.path.join(dirname, basename          \
                        +      data['TIMESTAMP'] \
                        +      ("_%05d.pickle" % data['SEQUENCE_NUMBER']))

  args = ["indexing.data=dummy",
          "beam_search_scope=0.5",
          "lepage_max_delta = 3.0",
          "spots_pickle = None",
          "subgroups_pickle = None",
          "refinements_pickle = None",
          "rmsd_tolerance = 5.0",
          "mosflm_rmsd_tolerance = 5.0",
          "indexing.completeness_pickle=%s"%path,
          "difflimit_sigma_cutoff=2.0",
          #"indexing.open_wx_viewer=True"
          ]

  from xfel.phil_preferences import load_cxi_phil
  horizons_phil = load_cxi_phil(data["xtal_target"], args)
  horizons_phil.indexing.data = data
  print "XFEL processing: %s"%path
  try:
    return run_one_index_core(horizons_phil)
  except NoAutoIndex,e:
    print "NoAutoIndex"
    print e
  except AutoIndexError,e:
    print "FailedAutoIndex"
    print e
  except Sorry,e:
    print "Sorry"
    print e
  except ZeroDivisionError,e:
    print "ZeroDivisionError"
    print e
  except SpotfinderError,e:
    print "Too few spots from Spotfinder"
    print e
  except Exception,e:
    print "ANOTHER exception"
    print e
    import traceback
    traceback.print_exc()

if __name__=="__main__":
  pass
