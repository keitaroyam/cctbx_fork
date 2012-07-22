import math
from cctbx.array_family import flex
from scitbx import matrix
from libtbx.utils import Sorry

#234567890123456789212345678931234567894123456789512345678961234567897123456789812

from labelit.dptbx.profile_support import show_profile
from rstbx.apps.slip_helpers import slip_callbacks
from rstbx.dials_core.integration_core import integration_core

class IntegrationMetaProcedure(integration_core,slip_callbacks):

  def basic_algorithm(self,verbose=False):
    Amat = matrix.sqr(self.inputai.getOrientation().direct_matrix())
    self.frames = self.inputpd['osc_start'].keys()
    self.incr_focus = []
    for frame in self.frames:
      focus = self.inputpd['masks'][frame][0:2]
      if len(self.inputpd['masks'][frame]) < 3 or self.inputpd['masks'][frame][2] is None:
        self.incr_focus.append( None )
        continue; #no average profile; no pred/obs agreement; nothing possible
      average_profile = self.inputpd['masks'][frame][2]
      if verbose:
        box = self.inputpd['masks'][frame][3]
        print average_profile.focus()
        print box.focus()
        print "Average Profile:"
        show_profile( average_profile )
        print "Box:"
        show_profile( box )
      self.incr_focus.append( average_profile.focus() )

  def get_predictions_accounting_for_centering(self,cb_op_to_primitive=None):

    if (self.horizons_phil.known_setting is None or self.horizons_phil.known_setting == self.setting_id ) and \
        self.horizons_phil.integration.model in ["use_case_3_simulated_annealing",
                                                "use_case_3_simulated_annealing_7",
                                                "use_case_3_simulated_annealing_9"]:
      if cb_op_to_primitive==None:
        raise Sorry("Can't use model_3 simulated annealing for non-primitive cells, contact authors.")
      if self.horizons_phil.integration.model=="use_case_3_simulated_annealing":
        best_params=self.use_case_3_simulated_annealing(self.horizons_phil.integration.use_subpixel_translations)
      elif self.horizons_phil.integration.model=="use_case_3_simulated_annealing_7":
        best_params=self.use_case_3_simulated_annealing_7(self.horizons_phil.integration.use_subpixel_translations)
      elif self.horizons_phil.integration.model=="use_case_3_simulated_annealing_9":
        best_params=self.use_case_3_simulated_annealing_9(self.horizons_phil.integration.use_subpixel_translations)
      #best_params is the tuple (half_mos_deg, waveHE, waveLE, ori, angle1, angle2, angle3)
      BPpredicted = self.bp3_wrapper.ucbp3.selected_predictions_labelit_format()
      BPhkllist = self.bp3_wrapper.ucbp3.selected_hkls()
      self.predicted,self.hkllist = BPpredicted, BPhkllist
      if self.inputai.active_areas != None:
        self.predicted,self.hkllist = self.inputai.active_areas(
                                      self.predicted,self.hkllist,self.pixel_size)
      return

    if cb_op_to_primitive==None:

      predicted = self.inputai.predict_all(
                  self.image_centers[self.image_number],self.limiting_resolution)
      self.predicted = predicted.vec3() #only good for integrating one frame...
      self.hkllist = predicted.hkl()

    else:
      rot_mat = matrix.sqr(cb_op_to_primitive.c().r().as_double()).transpose()
      centered_orientation = self.inputai.getOrientation()
      primitive_orientation = centered_orientation.change_basis(rot_mat)
      self.inputai.setOrientation(primitive_orientation)
      predicted = self.inputai.predict_all(
                  self.image_centers[self.image_number],self.limiting_resolution)
      self.predicted = predicted.vec3() #only good for integrating one frame...
      primitive_hkllist = predicted.hkl()
      #not sure if matrix needs to be transposed first for outputting HKL's???:
      self.hkllist = cb_op_to_primitive.inverse().apply(primitive_hkllist)
      self.inputai.setOrientation(centered_orientation)
    if self.inputai.active_areas != None:
      self.predicted,self.hkllist = self.inputai.active_areas(
                                    self.predicted,self.hkllist,self.pixel_size)

    if False: #development only; compare the two methods:
      from matplotlib import pyplot as plt
      plt.plot([i[0] for i in BPpredicted],[i[1] for i in BPpredicted],"r.")
      plt.plot([i[0] for i in predicted],[i[1] for i in predicted],"b.")
      plt.show()

  def get_observations_with_outlier_removal(self):
    spots = self.spotfinder.images[self.frames[self.image_number]]["inlier_spots"]
    return spots

  def integration_concept(self,image_number=0,cb_op_to_primitive=None,verbose=False,**kwargs):
    self.image_number = image_number
    NEAR = 10
    pxlsz = self.pixel_size
    self.get_predictions_accounting_for_centering(cb_op_to_primitive)
    from annlib_ext import AnnAdaptor
    self.cell = self.inputai.getOrientation().unit_cell()
    query = flex.double()
    for pred in self.predicted: # predicted spot coord in pixels
      query.append(pred[0]/pxlsz)
      query.append(pred[1]/pxlsz)

    reference = flex.double()
    spots = self.get_observations_with_outlier_removal()

    assert len(spots)>NEAR# Can't do spot/pred matching with too few spots
    for spot in spots:
      reference.append(spot.ctr_mass_x())
      reference.append(spot.ctr_mass_y())

    IS_adapt = AnnAdaptor(data=reference,dim=2,k=NEAR)
    IS_adapt.query(query)
    print "Calculate correction vectors for %d observations & %d predictions"%(len(spots),len(self.predicted))
    indexed_pairs_provisional = []
    correction_vectors_provisional = []
    idx_cutoff = float(min(self.inputpd['masks'][self.frames[self.image_number]][0:2]))
    if verbose:
      print "idx_cutoff distance in pixels",idx_cutoff
    for i in xrange(len(self.predicted)): # loop over predicteds
      #for n in xrange(NEAR): # loop over near spotfinder spots
      for n in xrange(1): # only consider the nearest spotfinder spots
        Match = dict(spot=IS_adapt.nn[i*NEAR+n],pred=i)
        if n==0 and math.sqrt(IS_adapt.distances[i*NEAR+n]) < idx_cutoff:
          indexed_pairs_provisional.append(Match)

          vector = matrix.col(
            [spots[Match["spot"]].ctr_mass_x() - self.predicted[Match["pred"]][0]/pxlsz,
             spots[Match["spot"]].ctr_mass_y() - self.predicted[Match["pred"]][1]/pxlsz])
          correction_vectors_provisional.append(vector)
    print "... %d provisional matches"%len(correction_vectors_provisional)
    #insert code here to remove correction length outliers...
    # they are causing terrible
    # problems for finding legitimate correction vectors (print out the list)
    # also remove outliers for the purpose of reporting RMS
    outlier_rejection = True
    if outlier_rejection:
      correction_lengths = flex.double([v.length() for v in correction_vectors_provisional])
      clorder = flex.sort_permutation(correction_lengths)
      sorted_cl = correction_lengths.select(clorder)

      ACCEPTABLE_LIMIT = 2
      limit = int(0.33 * len(sorted_cl)) # best 1/3 of data are assumed to be correctly modeled.
      if (limit <= ACCEPTABLE_LIMIT):
        raise Sorry("Not enough indexed spots to reject outliers; have %d need >%d" % (limit, ACCEPTABLE_LIMIT))

      y_data = flex.double(len(sorted_cl))
      for i in xrange(len(y_data)):
        y_data[i] = float(i)/float(len(y_data))

      # ideas are explained in Sauter & Poon (2010) J Appl Cryst 43, 611-616.
      from labelit.outlier_spots.fit_distribution import fit_cdf,rayleigh
      fitted_rayleigh = fit_cdf(x_data = sorted_cl[0:limit],
                                y_data = y_data[0:limit],
                                distribution=rayleigh)

      inv_cdf = [fitted_rayleigh.distribution.inv_cdf(cdf) for cdf in y_data]

      #print "SORTED LIST OF ",len(sorted_cl), "with sigma",fitted_rayleigh.distribution.sigma
      indexed_pairs = []
      correction_vectors = []
      for icand in xrange(len(sorted_cl)):
        # somewhat arbitrary sigma = 1.0 cutoff for outliers
        if (sorted_cl[icand]-inv_cdf[icand])/fitted_rayleigh.distribution.sigma > 1.0:
          break
        indexed_pairs.append(indexed_pairs_provisional[clorder[icand]])
        correction_vectors.append(correction_vectors_provisional[clorder[icand]])

        if kwargs.get("verbose_cv")==True:
            print "CV OBSCENTER %7.2f %7.2f REFINEDCENTER %7.2f %7.2f"%(
              float(self.inputpd["size1"])/2.,float(self.inputpd["size2"])/2.,
              self.inputai.xbeam()/pxlsz, self.inputai.ybeam()/pxlsz),
            print "OBSSPOT %7.2f %7.2f PREDSPOT %7.2f %7.2f"%(
              spots[indexed_pairs[-1]["spot"]].ctr_mass_x(),
              spots[indexed_pairs[-1]["spot"]].ctr_mass_y(),
              self.predicted[indexed_pairs[-1]["pred"]][0]/pxlsz,
              self.predicted[indexed_pairs[-1]["pred"]][1]/pxlsz)
      #print "After outlier rejection %d indexed spotfinder spots remain."%len(indexed_pairs)
      if False:
        rayleigh_cdf = [
          fitted_rayleigh.distribution.cdf(x=sorted_cl[c]) for c in xrange(len(sorted_cl))]
        from matplotlib import pyplot as plt
        plt.plot(sorted_cl,y_data,"r+")
        #plt.plot(sorted_cl,rayleigh_cdf,"g.")
        plt.plot(inv_cdf,y_data,"b.")
        plt.show()
    else:
      indexed_pairs = indexed_pairs_provisional
      correction_vectors = correction_vectors_provisional
    ########### finished with outlier rejection

    if self.horizons_phil.integration.spot_shape_verbose:
        from rstbx.new_horizons.spot_shape import spot_shape_verbose
        spot_shape_verbose(rawdata = self.imagefiles.images[self.image_number].linearintdata,
           beam_center_pix = matrix.col((self.inputai.xbeam()/pxlsz, self.inputai.ybeam()/pxlsz)),
           indexed_pairs = indexed_pairs,
           spotfinder_observations = spots,
           distance_mm = self.inputai.distance(),
           mm_per_pixel = pxlsz,
           hkllist = self.hkllist,
           unit_cell = self.cell,
           wavelength_ang = self.inputai.wavelength
        )

    #Other checks to be implemented (future):
    # spot is within active area of detector on a circular detector such as the Mar IP
    # integration masks do not overlap; or deconvolute

    correction_lengths=flex.double([v.length() for v in correction_vectors])
    if verbose:
      print "average correction %5.2f over %d vectors"%(flex.mean(correction_lengths),
      len(correction_lengths)),
      print "or %5.2f mm."%(pxlsz*flex.mean(correction_lengths))
    self.r_residual = pxlsz*flex.mean(correction_lengths)

    #assert len(indexed_pairs)>NEAR # must have enough indexed spots
    if (len(indexed_pairs) <= NEAR):
      raise Sorry("Not enough indexed spots, only found %d, need %d" % (len(indexed_pairs), NEAR))

    reference = flex.double()
    for item in indexed_pairs:
      reference.append(spots[item["spot"]].ctr_mass_x())
      reference.append(spots[item["spot"]].ctr_mass_y())

    PS_adapt = AnnAdaptor(data=reference,dim=2,k=NEAR)
    PS_adapt.query(query)

    self.BSmasks = []
    self.positional_correction_mapping( predicted=self.predicted,
                                        correction_vectors = correction_vectors,
                                        PS_adapt = PS_adapt,
                                        IS_adapt = IS_adapt,
                                        spots = spots)

    # which spots are close enough to interfere with background?
    MAXOVER=6
    OS_adapt = AnnAdaptor(data=query,dim=2,k=MAXOVER) #six near nbrs
    OS_adapt.query(query)
    if self.incr_focus[self.image_number] is None:
      raise Sorry("No observed/predicted spot agreement; no Spotfinder masks; skip integration")
    nbr_cutoff = 2.0* max(self.incr_focus[self.image_number])
    FRAME = int(nbr_cutoff/2)
    #print "The overlap cutoff is %d pixels"%nbr_cutoff
    nbr_cutoff_sq = nbr_cutoff * nbr_cutoff

    #print "Optimized C++ section...",
    self.set_frame(FRAME)
    self.set_background_factor(kwargs["background_factor"])
    self.set_nbr_cutoff_sq(nbr_cutoff_sq)
    flex_sorted = flex.int()
    for item in self.sorted:
      flex_sorted.append(item[0]);flex_sorted.append(item[1]);

    if self.inputai.active_areas != None:
      self.detector_xy_draft = self.safe_background( predicted=self.predicted,
                          OS_adapt=OS_adapt,
                          sorted=flex_sorted,
                          tiles=self.inputai.active_areas.IT,
                          tile_id=self.inputai.active_areas.tile_id);
    else:
      self.detector_xy_draft = self.safe_background( predicted=self.predicted,
                          OS_adapt=OS_adapt,
                          sorted=flex_sorted);
    for i in xrange(len(self.predicted)): # loop over predicteds
      B_S_mask = {}
      keys = self.get_bsmask(i)
      for k in xrange(0,len(keys),2):
        B_S_mask[(keys[k],keys[k+1])]=True
      self.BSmasks.append(B_S_mask)
    #print "Done"
    return

    # Never get here...replaced with C++ code
    for i in xrange(len(predicted)): # loop over predicteds
      pred = predicted[i]
      predX = pred[0]/pxlsz
      predY = pred[1]/pxlsz
      correction = corrections[i]
      I_S_mask = self.ISmasks[i]
      # now consider the background
      B_S_mask = {}
      i_bs = 0
      spot_position = matrix.col(( round(predX + correction[0]),
                                  round(predY + correction[1]) ))
      self.detector_xy_draft.append(( round(predX + correction[0]),
                                  round(predY + correction[1]) ))

      #insert a test to make sure spot is within FRAME
      if spot_position[0] > FRAME and spot_position[1] > FRAME and \
         spot_position[0] < int(self.inputpd["size1"]) - FRAME and \
         spot_position[1] < int(self.inputpd["size2"]) - FRAME:

         spot_keys = I_S_mask.keys()
         spot_size = len(spot_keys)

         #Look for potential overlaps
         for n in xrange(MAXOVER):
           distance = OS_adapt.distances[i*MAXOVER+n]
           if distance < nbr_cutoff_sq:
             spot_keys += self.ISmasks[ OS_adapt.nn[i*MAXOVER+n] ].keys()

         for increment in self.sorted:
           candidate_bkgd = spot_position + increment
           b_s_key = (candidate_bkgd[0],candidate_bkgd[1])
           if b_s_key not in spot_keys:
             #eliminate if in guard region
             guard = False
             for key in spot_keys:
               if (b_s_key[0]-key[0])**2 + (b_s_key[1]-key[1])**2  < 10:
                 guard = True
                 break
             if guard: continue
             i_bs += 1
             B_S_mask[b_s_key] = True
           if i_bs == spot_size: break
      self.BSmasks.append(B_S_mask)
      # private interface.  If B_S_mask is the empty dictionary, the spot
      # was out of boundary and it is not possible to integrate

  def integration_proper(self):
    rawdata = self.imagefiles.images[self.image_number].linearintdata # assume image #1
    self.integration_proper_fast(rawdata,self.predicted,self.hkllist,self.detector_xy_draft)
    self.integrated_data = self.get_integrated_data()
    self.integrated_sigma= self.get_integrated_sigma()
    self.integrated_miller=self.get_integrated_miller()
    self.detector_xy = self.get_detector_xy()
    return # function has been recoded in C++

  def get_obs(self,space_group_symbol):
    from cctbx.crystal import symmetry
    from cctbx import miller

    xsym = symmetry(unit_cell = self.cell,
                    space_group_symbol=space_group_symbol)

    miller_set = miller.set(crystal_symmetry=xsym,
      indices=self.integrated_miller,anomalous_flag=True)
    miller_array = miller.array(miller_set,self.integrated_data,
      self.integrated_sigma)
    miller_array.set_observation_type_xray_intensity()
    miller_array.set_info("Raw partials from rstbx, not in ASU, no polarization correction")
    return miller_array

  def user_callback(self,dc,wxpanel,wx):
    # arguments are a wx Device Context, an Xray Frame, and the wx Module itself
    # BLUE: predictions
    for ix,pred in enumerate(self.predicted):
        if self.BSmasks[ix].keys()==[]:continue
        x,y = wxpanel._img.image_coords_as_screen_coords(
          pred[1]/self.pixel_size,
          pred[0]/self.pixel_size)
        dc.SetPen(wx.Pen('blue'))
        dc.SetBrush(wx.BLUE_BRUSH)
        dc.DrawCircle(x,y,1)

    for imsk in xrange(len(self.BSmasks)):
      smask_keys = self.get_ISmask(imsk)
      bmask = self.BSmasks[imsk]
      if len(bmask.keys())==0: continue

      # CYAN: integration mask
      for ks in xrange(0,len(smask_keys),2):
        x,y = wxpanel._img.image_coords_as_screen_coords(smask_keys[ks+1],
                                                         smask_keys[ks])
        dc.SetPen(wx.Pen('cyan'))
        dc.SetBrush(wx.CYAN_BRUSH)
        dc.DrawCircle(x,y,1)

      # YELLOW: background mask
      for key in bmask.keys():
        x,y = wxpanel._img.image_coords_as_screen_coords(key[1],key[0])
        dc.SetPen(wx.Pen('yellow'))
        dc.SetBrush(wx.CYAN_BRUSH)
        dc.DrawCircle(x,y,1)

    for spot in self.spotfinder.images[self.frames[self.image_number]]["inlier_spots"]:
      # RED: spotfinder spot pixels
      for pxl in spot.bodypixels:
        x,y = wxpanel._img.image_coords_as_screen_coords(
          pxl.y,
          pxl.x)
        dc.SetPen(wx.Pen('red'))
        dc.SetBrush(wx.RED_BRUSH)
        dc.DrawCircle(x,y,1)

      # GREEN: spotfinder centers of mass
      x,y = wxpanel._img.image_coords_as_screen_coords(
        spot.ctr_mass_y(),
        spot.ctr_mass_x())
      dc.SetPen(wx.Pen('green'))
      dc.SetBrush(wx.GREEN_BRUSH)
      dc.DrawCircle(x,y,1)

  def initialize_increments(self,image_number=0):
    #initialize a data structure that contains possible vectors
    # background_pixel - spot_center
    # consider a large box 4x as large as the presumptive mask.
    from scitbx.array_family import flex
    Incr = []
    Distsq = flex.double()
    if self.incr_focus[image_number] == None: return []
    for i in xrange(-self.incr_focus[image_number][0],1+self.incr_focus[image_number][0]):
      for j in xrange(-self.incr_focus[image_number][1],1+self.incr_focus[image_number][1]):
        Incr.append(matrix.col((i,j)))
        Distsq.append(i*i+j*j)
    order = flex.sort_permutation(Distsq)
    self.sorted = [] # a generic list of points close in distance to a central point
    for i in xrange(len(order)):
      #print i,order[i],Distsq[order[i]],Incr[order[i]]
      self.sorted.append(Incr[order[i]])
