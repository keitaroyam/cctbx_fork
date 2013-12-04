
from __future__ import division
from libtbx.test_utils import show_diff

def exercise () :
  from iotbx.scalepack import no_merge_original_index
  from cctbx import crystal
  # input from xia2 with one slight modification to the (44,0,-25) observation,
  # as pointless/aimless seem to have a slightly different convention for ASU
  # mapping.  (Scalepack itself is even more deviant.)
  sca_raw = """\
    2 P 1 21 1
  1  0  0  0  1  0  0  0  1
  0  0  0
 -1  0  0  0  1  0  0  0 -1
  0  6  0
  44   0 -25 -44   0  25   316 0 0  2    91.7   108.2
 -44   1  11 -44   1  11    35 1 0  1   110.2   112.9
 -44  -1  11 -44   1  11    34 2 0  2    28.7   115.0
 -44   1  12 -44   1  12    34 1 0  1   129.1   116.3
 -44  -1  12 -44   1  12    33 2 0  2   133.1   118.2
 -44   1  14 -44   1  14    31 1 0  1   159.7   116.1
 -44  -1  14 -44   1  14    30 2 0  2   136.8    90.9
 -44   1  15 -44   1  15    30 1 0  1   106.4    85.8
 -44  -1  15 -44   1  15    29 2 0  2    39.1    87.4
 -44   1  17 -44   1  17    27 1 0  1   115.9    87.0
 -44  -1  17 -44   1  17    26 2 0  2   138.1    89.8
 -44  -1  18 -44   1  18    25 2 0  2    10.3    84.4
 -38   2  53 -38   2  53   212 1 0  1   246.7   141.4
  38  -2 -53 -38   2  53   272 2 0  1     6.1   157.7
  38   2 -53 -38   2  53   272 1 0  2   322.5   159.5
  38  -2 -54 -38   2  54   271 2 0  1   -68.4   152.1
  38   2 -54 -38   2  54   271 1 0  2   211.0   153.3
  38  -2 -55 -38   2  55   270 2 0  1    78.6   153.6
  38   2 -55 -38   2  55   270 1 0  2   220.4   157.0
  38  -2 -56 -38   2  56   269 2 0  1   -25.5   148.6
  38   2 -56 -38   2  56   269 1 0  2   -55.1   143.6
  38   2 -57 -38   2  57   268 1 0  2   -32.3    89.2
  38  -2 -57 -38   2  57   268 2 0  1  -265.7   138.8
  38   2 -58 -38   2  58   267 1 0  2    69.6    92.7
  38  -2 -58 -38   2  58   267 2 0  1  -153.1   132.2
"""
  hkl_in = "tst_scalepack_unmerged_writer.sca"
  hkl_out = "tst_scalepack_unmerged_writer_out.sca"
  open(hkl_in, "w").write(sca_raw)
  reader = no_merge_original_index.reader(hkl_in)
  symm = crystal.symmetry(
    space_group_symbol="P21",
    unit_cell=(80.882, 51.511, 141.371, 90., 106.588, 90.))
  i_obs = reader.as_miller_array(
    crystal_symmetry=symm,
    merge_equivalents=False)
  i_obs.export_as_scalepack_unmerged(
    file_name=hkl_out,
    batch_numbers=reader.batch_numbers,
    spindle_flags=reader.spindle_flags)
  sca_recycled = open(hkl_out).read()
  assert not show_diff(sca_recycled, sca_raw)

if (__name__ == "__main__") :
  exercise()
  print "OK"
