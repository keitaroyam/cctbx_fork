from __future__ import division
from scitbx.array_family import flex
import iotbx.pdb
from cctbx import maptbx
from cctbx import miller

def getvs(cmap, threshold):
  co = maptbx.connectivity(map_data=cmap, threshold=threshold)
  map_result = co.result()
  v=[0,0,0]
  for i in range(3):
    v[i] = (map_result==i).count(True)
  return v, list(co.regions())


def exercise1():
  pdb_str="""
CRYST1   10.000  10.000   10.000  90.00  90.00  90.00 P 1
HETATM    1  C    C      1       2.000   2.000   2.000  1.00 20.00           C
END
"""
  pdb_inp = iotbx.pdb.input(source_info=None, lines=pdb_str)
  xrs = pdb_inp.xray_structure_simple()
  cg = maptbx.crystal_gridding(unit_cell=xrs.unit_cell(),
      pre_determined_n_real=(100,100,100),
      space_group_info=xrs.space_group_info())
  fc = xrs.structure_factors(d_min = 1., algorithm = "direct").f_calc()
  fft_map = miller.fft_map(crystal_gridding=cg, fourier_coefficients=fc)
  map_data = fft_map.real_map_unpadded()
  # pass map and threshold value
  co = maptbx.connectivity(map_data=map_data, threshold=100)
  # get 'map' of the same size with integers: 0 where below threshold,
  # 1,2,3... - for connected regions
  map_result = co.result()
  # get 1d array of integer volumes and transform it to list.
  volumes = list(co.regions())
  # find max volume (except volume of 0-region which will be probably max)
  max_volume = max(volumes[1:])
  # find number of the region with max volume
  max_index = volumes.index(max_volume)
  v=[0,0,0]
  for i in range(3):
    # !!! Do not do this because it's extremely slow! Used for test purposes.
    v[i] = (map_result==i).count(True)

  assert v[2] == 0
  assert v[1] < 15000
  assert v[0]+v[1]+v[2] == 1000000
  assert volumes == v[:2]

def exercise3():
  pdb_str="""
CRYST1   10.000  10.000   10.000  90.00  90.00  90.00 P 1
HETATM    1  C    C      1       2.000   2.000   2.000  1.00  2.00           C
HETATM    1  C    C      1       3.500   2.000   2.000  1.00  2.00           C
END
"""

  pdb_inp = iotbx.pdb.input(source_info=None, lines=pdb_str)
  xrs = pdb_inp.xray_structure_simple()
  cg = maptbx.crystal_gridding(unit_cell=xrs.unit_cell(),
      pre_determined_n_real=(100,100,100),
      space_group_info=xrs.space_group_info())
  fc = xrs.structure_factors(d_min = 1., algorithm = "direct").f_calc()
  fft_map = miller.fft_map(crystal_gridding=cg, fourier_coefficients=fc)
  fft_map.apply_sigma_scaling()
  map_data = fft_map.real_map_unpadded()
  #all filled
  v, volumes = getvs(map_data, -100)
  assert v == [0, 1000000, 0]
  assert v[:2] == volumes
  # can see one blob
  v, volumes = getvs(map_data, 5)
  assert v[0]+v[1]+v[2] == 1000000
  assert v[2] == 0
  assert v[:2] == volumes
  # can see separate, approx equal volume bloobs
  v, volumes = getvs(map_data, 10)
  assert v[0]+v[1]+v[2] == 1000000
  assert abs(v[1] - v[2]) < 5
  assert v == volumes
  # nothing to see
  v, volumes = getvs(map_data, 1000)
  assert v == [1000000, 0, 0]
  assert v[:1] == volumes

def exercise4():
  cmap = flex.double(flex.grid(100,100,100))
  cmap.fill(1)
  for i in range(10,20):
    for j in range(10,20):
      for k in range(10,20):
        cmap[i,j,k] = 10
  v, volumes = getvs(cmap, 5)
  assert v == [999000, 1000, 0]
  assert v[:2] == volumes
  #print "all filled"
  v, volumes = getvs(cmap, -5)
  assert v == [0,1000000,0]
  assert v[:2] == volumes
  #print "none filled"
  v, volumes = getvs(cmap, 20)
  assert v == [1000000,0,0]
  assert v[:1] == volumes

def exercise5():
  #print "corner blob"
  cmap = flex.double(flex.grid(100,100,100))
  cmap.fill(0)
  for i in range(100):
    for j in range(100):
      for k in range(100):
        if (i<10 or i>=90) and (j<10 or j>=90) and (k<10 or k>=90):
          cmap[i,j,k] = 10
          #print i,j,k
  v, volumes = getvs(cmap, 5)
  assert v == [992000, 8000, 0]
  assert v[:2] == volumes

  #print "2 blobs"
  cmap.fill(0)
  for i in range(100):
    for j in range(100):
      for k in range(100):
        if (5<i<10) and (5<j<10) and (5<k<10):
          cmap[i,j,k] = 10
        if (15<i<20) and (15<j<20) and (15<k<20):
          cmap[i,j,k] = 20
  v, volumes = getvs(cmap, 5)
  assert v == [999872,64,64]
  assert v == volumes
  v, volumes = getvs(cmap, 15)
  assert v == [999936, 64,0]
  assert v[:2] == volumes

  #print "endless blob"
  cmap.fill(0)
  for j in range(100):
    for k in range(100):
      cmap[5,j,k] = 10
  v, volumes = getvs(cmap, 5)
  assert v == [990000, 10000, 0]
  assert v[:2] == volumes

def exercise6():
  cmap = flex.double(flex.grid(100,100,100))
  #print "corner touch"
  cmap.fill(0)
  cmap[1,1,1] = cmap[2,2,2] = 10
  v, volumes = getvs(cmap, 5)
  assert v == [999998, 1, 1]
  assert v == volumes
  #print "edges touch"
  cmap.fill(0)
  cmap[1,1,1] = cmap[2,2,1] = 10
  v, volumes = getvs(cmap, 5)
  assert v == [999998, 1, 1]
  assert v == volumes
  #print "face touch"
  cmap.fill(0)
  cmap[1,1,1] = cmap[2,1,1] = 10
  v, volumes = getvs(cmap, 5)
  assert v == [999998, 2, 0]
  assert v[:2] == volumes

def exercise_volume_cutoff():
  cmap = flex.double(flex.grid(100,100,100))
  cmap.fill(0)
  for i in range(100):
    for j in range(100):
      for k in range(100):
        if (5<i<10) and (5<j<10) and (5<k<10):
          cmap[i,j,k] = 10
        if (15<i<25) and (15<j<25) and (15<k<25):
          cmap[i,j,k] = 20

  co = maptbx.connectivity(map_data=cmap, threshold=5)
  map_result = co.result()
  volumes = list(co.regions())
  #print volumes
  #[999207, 64, 729]
  vol_mask = co.volume_cutoff_mask(volume_cutoff=10)
  assert (vol_mask==1).count(True) == 793
  assert (vol_mask==0).count(True) == 999207
  vol_mask = co.volume_cutoff_mask(volume_cutoff=100)
  assert (vol_mask==1).count(True) == 729
  assert (vol_mask==0).count(True) == 999271
  vol_mask = co.volume_cutoff_mask(volume_cutoff=1000)
  assert (vol_mask==1).count(True) == 0
  assert (vol_mask==0).count(True) == 1000000

def exercise_max_values():
  cmap = flex.double(flex.grid(100,100,100))
  cmap.fill(0)
  for i in range(100):
    for j in range(100):
      for k in range(100):
        if (5<i<10) and (5<j<10) and (5<k<10):
          cmap[i,j,k] = 10
        if (15<i<25) and (15<j<25) and (15<k<25):
          cmap[i,j,k] = 20

  cmap[7,7,7] = 15
  cmap[20,20,20] = 25
  co = maptbx.connectivity(map_data=cmap, threshold=5)
  m_coors = list(co.maximum_coors())
  m_vals = list(co.maximum_values())
  assert m_coors == [(0, 0, 0), (7, 7, 7), (20, 20, 20)]
  assert m_vals == [0.0, 15.0, 25.0]

def debug_printing(co):
  print "volumes    :",  list(co.regions())
  print "values     :",  list(co.maximum_values())
  print "coordinates:",  list(co.maximum_coors())
  print "============"


def exercise_noise_elimination_two_cutoffs():
  #map preparation
  cmap = flex.double(flex.grid(100,2,2))
  cmap.fill(10)
  for i in range(10,40):
    cmap[i,1,1] = i
  for i,v in zip(range(40,60), range(40,20,-1)):
    cmap[i,1,1] = v
  for i,v in zip(range(60,70), range(20,30)):
    cmap[i,1,1] = v
  for i,v in zip(range(70,90), range(30,10,-1)):
    cmap[i,1,1] = v
  #for i in range(100):
  #  print "%d   : %d" % (i,  cmap[i,1,1])

  co1 = maptbx.connectivity(map_data=cmap, threshold=25)
  co2 = maptbx.connectivity(map_data=cmap, threshold=22)
  co3 = maptbx.connectivity(map_data=cmap, threshold=18)

  # 1 good, 1 bad ===> 2 separate
  res_mask = co2.noise_elimination_two_cutoffs(connectivity_t1=co1,
                                               volume_threshold_t1=12)
  assert (res_mask!=0).count(True) == 35
  # 2 good ===> 2 separate
  res_mask = co2.noise_elimination_two_cutoffs(connectivity_t1=co1,
                                               volume_threshold_t1=8)
  assert (res_mask!=0).count(True) == 50
  # 1 good, 1 bad ===> 1 big
  res_mask = co3.noise_elimination_two_cutoffs(connectivity_t1=co1,
                                               volume_threshold_t1=12)
  assert (res_mask!=0).count(True) == 63
  # 2 good ===> 1 big
  res_mask = co3.noise_elimination_two_cutoffs(connectivity_t1=co1,
                                               volume_threshold_t1=8)
  assert (res_mask!=0).count(True) == 63
  # 2 bad ===> 1 big
  res_mask = co3.noise_elimination_two_cutoffs(connectivity_t1=co1,
                                               volume_threshold_t1=30)
  assert (res_mask!=0).count(True) == 0

  # extreme case: nothing above t1 ==> result: everything is 0 on the mask
  co1 = maptbx.connectivity(map_data=cmap, threshold=40)
  co2 = maptbx.connectivity(map_data=cmap, threshold=22)
  assert (res_mask!=0).count(True) == 0

  # extreme case: everything above t1 ==> result is undefined.

if __name__ == "__main__" :
  exercise1()  # examples of usage are here!
  exercise3()
  exercise4()
  exercise5()
  exercise6()
  exercise_volume_cutoff()
  exercise_max_values()
  exercise_noise_elimination_two_cutoffs()
