from __future__ import division
from libtbx import easy_pickle
from cctbx import miller # import dependency
import os

# jiffy script specifically for xppk4715, where some background effects require splitting integrated data into two halfs
# Run this script in a cctbx.xfel 'results' directory.  The script will search the directory for trials and rungroups,
# find integration pickles, and split them into left, right and middle, according to the key applied_absorption_correction

for runroot in os.listdir("."):
  if not os.path.isdir(runroot):
    continue
  for rg in os.listdir(runroot):
    intpath = os.path.join(runroot, rg, "integration")
    destroot_l = os.path.join(intpath, "left")
    destroot_r = os.path.join(intpath, "right")
    destroot_m = os.path.join(intpath, "middle")
    if not os.path.exists(destroot_l):
      os.makedirs(destroot_l)
    if not os.path.exists(destroot_r):
      os.makedirs(destroot_r)
    if not os.path.exists(destroot_m):
      os.makedirs(destroot_m)
    for picklename in os.listdir(intpath):
      if os.path.splitext(picklename)[1] != ".pickle":
        continue
      picklepath = os.path.join(intpath, picklename)
      print picklepath
      destpath_l = os.path.join(destroot_l, os.path.splitext(picklename)[0] + "_l.pickle")
      destpath_r = os.path.join(destroot_r, os.path.splitext(picklename)[0] + "_r.pickle")
      destpath_m = os.path.join(destroot_m, os.path.splitext(picklename)[0] + "_m.pickle")
      data = easy_pickle.load(picklepath)
      if not "applied_absorption_correction" in data:
        continue

      corr = data["applied_absorption_correction"]

      from xfel.cxi.cspad_ana.rayonix_tbx import get_rayonix_pixel_size
      from scitbx.array_family import flex
      pixel_size = get_rayonix_pixel_size(2)
      bx = data['xbeam'] / pixel_size
      by = data['ybeam'] / pixel_size

      preds = data['mapped_predictions']

      sel_l = []
      sel_r = []
      sel_mid = []

      for i in xrange(len(preds)):
        # all preds left of the beam center
        p1_sel = preds[i].parts()[1] < bx
        # mostly will be preds right of the beam center, but includes a few to the left of middle strip
        p2_sel = (corr[i] != 1.0) & (corr[i] <= 1.5)
        # the rest
        mid_sel = (~p1_sel) & (~p2_sel)
        mid = preds[i].select(mid_sel)

        # p2 should really be all preds right of the middle strip, ignoring the odd ones to the left of it
        if len(mid) > 0:
          meanx = flex.mean(mid.parts()[1])
          p2_sel = p2_sel & (preds[i].parts()[1] > meanx)

        # the rest, this time including the odd bits from the right half
        mid_sel = (~p1_sel) & (~p2_sel)

        sel_l.append(p1_sel)
        sel_r.append(p1_sel)
        sel_mid.append(mid_sel)

      dl = {}
      dr = {}
      dm = {}

      for key in data:
        if key == "correction_vectors":
          # drop correction_vectors as they aren't as easy to split up
          continue
        elif key in ["current_cb_op_to_primitive", "effective_tiling", "pointgroup", "identified_isoform"]:
          dl[key] = data[key]
          dr[key] = data[key]
          dm[key] = data[key]
          continue
        elif key == "current_orientation":
          from cctbx import crystal_orientation
          dl[key] = [crystal_orientation.crystal_orientation(c) for c in data[key]]
          dr[key] = [crystal_orientation.crystal_orientation(c) for c in data[key]]
          dm[key] = [crystal_orientation.crystal_orientation(c) for c in data[key]]
          continue
        try:
          assert len(data[key]) == len(sel_l)
          islist = True
        except TypeError, e:
          islist = False

        if islist:
          val_l = []
          val_r = []
          val_m = []
          for i, item in enumerate(data[key]):
            if hasattr(item, "select"):
              val_l.append(item.select(sel_l[i]))
              val_r.append(item.select(sel_r[i]))
              val_m.append(item.select(sel_mid[i]))
            else:
              val_l.append(item)
              val_r.append(item)
              val_m.append(item)
          dl[key] = val_l
          dr[key] = val_r
          dm[key] = val_m
        else:
          dl[key] = data[key]
          dr[key] = data[key]
          dm[key] = data[key]
      easy_pickle.dump(destpath_l, dl)
      easy_pickle.dump(destpath_r, dr)
      easy_pickle.dump(destpath_m, dm)
