from __future__ import division

class Test(object):

  def __init__(self):
    pass

  def run(self):

    from iotbx.xds import xparm
    import os
    import libtbx.load_env
    from libtbx.test_utils import open_tmp_file

    iotbx_dir = libtbx.env.dist_path('iotbx')
    filename = os.path.join(iotbx_dir, 'xds', 'tests', 'XPARM.XDS')
    handle = xparm.reader()
    assert handle.find_version(filename) == 1
    handle.read_file(filename)

    f = open_tmp_file(suffix='XPARM.XDS', mode='wb')
    f.close()
    writer = xparm.writer(
      handle.starting_frame,
      handle.starting_angle,
      handle.oscillation_range,
      handle.rotation_axis,
      handle.wavelength,
      handle.beam_vector,
      handle.space_group,
      handle.unit_cell,
      handle.unit_cell_a_axis,
      handle.unit_cell_b_axis,
      handle.unit_cell_c_axis,
      handle.num_segments,
      handle.detector_size,
      handle.pixel_size,
      handle.detector_origin,
      handle.detector_distance,
      handle.detector_x_axis,
      handle.detector_y_axis,
      handle.detector_normal)
    writer.write_file(f.name)
    handle_recycled = xparm.reader()
    # make sure we wrote out version 2
    assert handle_recycled.find_version(f.name) == 2
    handle_recycled.read_file(f.name)

    for handle in (handle, handle_recycled):

      # Scan and goniometer stuff
      assert handle.starting_frame == 1
      assert handle.starting_angle == 0.0
      assert handle.oscillation_range == 0.2
      assert handle.rotation_axis == (0.999964, 0.00201, 0.008234)

      # Beam stuff
      assert handle.wavelength == 0.9795
      assert handle.beam_vector == (-0.001316, 0.001644, 1.020927)

      # Detector stuff
      assert handle.detector_size == (2463, 2527)
      assert handle.pixel_size == (0.172, 0.172)

      assert handle.detector_distance == 191.594391
      assert handle.detector_origin == (1237.948853, 1277.119141)
      assert handle.detector_x_axis == (1.0, 0.0, 0.0)
      assert handle.detector_y_axis == (0.0, 1.0, 0.0)
      assert handle.detector_normal == (0.0, 0.0, 1.0)

      # Crystal stuff
      assert handle.space_group == 1
      assert handle.unit_cell == (39.7964, 42.3646, 42.4588, 90.152, 90.123, 89.985)
      assert handle.unit_cell_a_axis == (5.487486, -39.117188, -4.846367)
      assert handle.unit_cell_b_axis == (-35.442802, -7.695671, 21.893908)
      assert handle.unit_cell_c_axis == (-22.425758, 1.410394, -36.025665)

    # segment stuff
    assert handle_recycled.num_segments == 1
    assert handle_recycled.segments == [(1, 1, 0, 1, 0)]
    assert handle_recycled.orientation == [
      (0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0)]

    print 'OK'

if __name__ == '__main__':

  test = Test()
  test.run()
