from __future__ import division
def slip_callback(self,frame):
  #best_params=self.use_case_3_simulated_annealing()
  #best_params = self.use_case_3_grid_refine(frame)
  #self.inputai.setOrientation(best_params[3])
  #self.use_case_3_refactor(frame,best_params[0],best_params[1], best_params[2])
  #self.inputai.set_orientation_reciprocal_matrix( (0.001096321006219932, -0.0007452314870693856, 0.007577824826005684, 0.0009042576974140007, -0.010205656871417366, -0.0009746502046169632, 0.012357726864252296, 0.00701297199602489, -0.0005717102325987258))
  #self.use_case_3_refactor(frame,0.0995603664049, 1.29155605957, 1.30470696644 )
  #self.use_case_3_refactor(frame,0.0995603664049, 1.29155605957, 1.30470696644,domain_size=2000. )

  normal = True
  # BLUE: predictions
  blue_data = []
  for ix,pred in enumerate(self.predicted):
      if self.BSmasks[ix].keys()==[]:continue
      x,y = frame.pyslip.tiles.picture_fast_slow_to_map_relative(
        (pred[1]/self.pixel_size) +0.5,
        (pred[0]/self.pixel_size) +0.5)
      blue_data.append((x,y))
  if False and normal: self.blue_layer = frame.pyslip.AddPointLayer(
        blue_data, color="blue", name="<blue_layer>",
        radius=2,
        renderer = frame.pyslip.LightweightDrawPointLayer,
        show_levels=[-2, -1, 0, 1, 2, 3, 4, 5])

  yellow_data = []; cyan_data = []
  for imsk in xrange(len(self.BSmasks)):
    smask_keys = self.get_ISmask(imsk)
    bmask = self.BSmasks[imsk]
    if len(bmask.keys())==0: continue

    # CYAN: integration mask
    for ks in xrange(0,len(smask_keys),2):
      cyan_data.append(
        frame.pyslip.tiles.picture_fast_slow_to_map_relative(
         smask_keys[ks+1] + 0.5,smask_keys[ks] + 0.5))

    # YELLOW: background mask
    for key in bmask.keys():
      yellow_data.append(
        frame.pyslip.tiles.picture_fast_slow_to_map_relative(
          key[1] + 0.5 ,key[0] + 0.5))
  if normal: self.cyan_layer = frame.pyslip.AddPointLayer(
        cyan_data, color="cyan", name="<cyan_layer>",
        radius=1.5,
        renderer = frame.pyslip.LightweightDrawPointLayer,
        show_levels=[-2, -1, 0, 1, 2, 3, 4, 5])
  if normal: self.yellow_layer = frame.pyslip.AddPointLayer(
        yellow_data, color="blue", name="<yellow_layer>",
        radius=1.5,
        renderer = frame.pyslip.LightweightDrawPointLayer,
        show_levels=[-2, -1, 0, 1, 2, 3, 4, 5])

  red_data = []; green_data = []
  print "User callback plotting %d spots"%len(self.spotfinder.images[self.frame_numbers[self.image_number]]["goodspots"])
  for spot in self.spotfinder.images[self.frame_numbers[self.image_number]]["goodspots"]:
    # RED: spotfinder spot pixels
    for pxl in spot.bodypixels:
      red_data.append(
        frame.pyslip.tiles.picture_fast_slow_to_map_relative(
          pxl.y + 0.5, pxl.x + 0.5))

    # GREEN: spotfinder centers of mass
    #green_data.append(
    #    frame.pyslip.tiles.picture_fast_slow_to_map_relative(
    #      spot.ctr_mass_y() + 0.5, spot.ctr_mass_x() + 0.5))

  print "User callback plotting %d spots"%len(self.spotfinder.images[self.frame_numbers[self.image_number]]["refinement_spots"])
  for spot in self.spotfinder.images[self.frame_numbers[self.image_number]]["refinement_spots"]:
    # RED: spotfinder spot pixels
    for pxl in spot.bodypixels:
      green_data.append(
        frame.pyslip.tiles.picture_fast_slow_to_map_relative(
          pxl.y + 0.5, pxl.x + 0.5))

  self.red_layer = frame.pyslip.AddPointLayer(
        red_data, color="red", name="<red_layer>",
        radius=1.5,
        renderer = frame.pyslip.LightweightDrawPointLayer,
        show_levels=[-2, -1, 0, 1, 2, 3, 4, 5])
  if normal: self.green_layer = frame.pyslip.AddPointLayer(
        green_data, color="yellow", name="<green_layer>",
        radius=2.0,
        renderer = frame.pyslip.LightweightDrawPointLayer,
        show_levels=[-2, -1, 0, 1, 2, 3, 4, 5])

setattr(slip_callback,"requires_refinement_spots",True)

