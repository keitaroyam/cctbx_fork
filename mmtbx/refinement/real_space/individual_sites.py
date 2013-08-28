from __future__ import division
from cctbx.maptbx import real_space_target_and_gradients
from libtbx import adopt_init_args
import scitbx.lbfgs
from cctbx import maptbx
from cctbx.array_family import flex
from mmtbx import utils
from libtbx.test_utils import approx_equal
from cctbx import crystal

class simple(object):
  def __init__(self,
               target_map,
               selection,
               real_space_gradients_delta,
               selection_real_space=None,
               geometry_restraints_manager=None,
               max_iterations=150):
    adopt_init_args(self, locals())
    self.lbfgs_termination_params = scitbx.lbfgs.termination_parameters(
        max_iterations = max_iterations)
    self.lbfgs_exception_handling_params = scitbx.lbfgs.exception_handling_parameters(
      ignore_line_search_failed_step_at_lower_bound = True,
      ignore_line_search_failed_step_at_upper_bound = True,
      ignore_line_search_failed_maxfev              = True)
    self.refined = None
    self.crystal_symmetry = None
    self.site_symmetry_table = None

  def refine(self, weight, xray_structure):
    self.crystal_symmetry = xray_structure.crystal_symmetry()
    self.site_symmetry_table = xray_structure.site_symmetry_table()
    self.refined = maptbx.real_space_refinement_simple.lbfgs(
      selection_variable              = self.selection,
      selection_variable_real_space   = self.selection_real_space,
      sites_cart                      = xray_structure.sites_cart(),
      density_map                     = self.target_map,
      geometry_restraints_manager     = self.geometry_restraints_manager,
      real_space_target_weight        = weight,
      real_space_gradients_delta      = self.real_space_gradients_delta,
      lbfgs_termination_params        = self.lbfgs_termination_params,
      lbfgs_exception_handling_params = self.lbfgs_exception_handling_params)

  def sites_cart(self):
    assert self.refined is not None
    sites_cart = self.refined.sites_cart
    if(self.selection):
      sites_cart.set_selected(self.selection, self.refined.sites_cart_variable)
    special_position_indices = self.site_symmetry_table.special_position_indices()
    if(special_position_indices.size()>0):
      for i_seq in special_position_indices:
        sites_cart[i_seq] = crystal.correct_special_position(
          crystal_symmetry = self.crystal_symmetry,
          special_op       = self.site_symmetry_table.get(i_seq).special_op(),
          site_cart        = sites_cart[i_seq],
          site_label       = None,
          tolerance        = 1)
    return sites_cart

class diff_map(object):
  def __init__(self,
               miller_array,
               crystal_gridding,
               map_target,
               geometry_restraints_manager,
               restraints_target_weight = 1,
               max_iterations = 500,
               min_iterations = 500):
    adopt_init_args(self, locals())
    self.step = miller_array.d_min()/4.
    self.refined = None

  def refine(self, weight, sites_cart=None, xray_structure=None):
    assert xray_structure is not None and [sites_cart,xray_structure].count(None)==1
    self.refined = real_space_target_and_gradients.minimization(
      xray_structure              = xray_structure,
      miller_array                = self.miller_array,
      crystal_gridding            = self.crystal_gridding,
      map_target                  = self.map_target,
      max_iterations              = self.max_iterations,
      min_iterations              = self.min_iterations,
      step                        = self.step,
      real_space_target_weight    = weight,
      restraints_target_weight    = self.restraints_target_weight,
      geometry_restraints_manager = self.geometry_restraints_manager,
      target_type                 = "diff_map")

  def sites_cart(self):
    assert self.refined is not None
    return self.refined.xray_structure.sites_cart()

class refinery(object):
  def __init__(self,
               refiner,
               xray_structure,
               start_trial_weight_value = 50.,
               weight_sample_rate = 10,
               rms_bonds_limit = 0.03,
               rms_angles_limit = 3.0,
               optimize_weight = True):
    self.rms_angles_start = None
    self.rms_bonds_start = None
    self.refiner = refiner
    self.weight_start=start_trial_weight_value
    sites_cart_start = xray_structure.sites_cart()
    self.rms_bonds_start, self.rms_angles_start  = \
      self.rmsds(sites_cart=xray_structure.sites_cart())
    self.weight_sample_rate = weight_sample_rate
    # results
    self.weight_final = None
    self.sites_cart_result = None
    self.rms_bonds_final,self.rms_angles_final = None,None
    #
    pool = {}
    bonds = flex.double()
    angles = flex.double()
    weights = flex.double()
    #
    weight = start_trial_weight_value
    weight_last = weight
    self.adjust_weight_sample_rate(weight=weight)
    if(optimize_weight):
      while True:
        self.rmsds(sites_cart=sites_cart_start) # DUMMY
        self.adjust_weight_sample_rate(weight=weight_last)
        refiner.refine(
          xray_structure = xray_structure.deep_copy_scatterers(), # XXX
          weight     = weight)
        sites_cart_result = refiner.sites_cart()
        bd, ad = self.rmsds(sites_cart=sites_cart_result)
        bonds.append(bd)
        angles.append(ad)
        weights.append(weight)
        pool.setdefault(weight,[]).append([sites_cart_result.deep_copy(),bd,ad])
        if(refiner.geometry_restraints_manager is None): break
        weight_last = weight
        if(ad>rms_angles_limit or bd > rms_bonds_limit):
          weight -= self.weight_sample_rate
        else:
          weight += self.weight_sample_rate
        if(weight<0 or abs(weight)<1.e-6):
          self.adjust_weight_sample_rate(weight=weight)
          weight = weight_last
          weight -= self.weight_sample_rate
        #print ">>> ", "%8.4f %8.4f"%(weight, weight_last), "%6.4f %5.2f"%(bd, ad),\
        #  self.weight_sample_rate, "  f (start/final):", refiner.refined.f_start, refiner.refined.f_final
        if((weight<0 or weight>1000) or weight in weights): break
    else:
      refiner.refine(
        xray_structure = xray_structure.deep_copy_scatterers(), # XXX
        weight     = weight)
      sites_cart_result = refiner.sites_cart()
    # select results
    if(optimize_weight):
      delta = bonds-rms_bonds_limit
      ind = (delta == flex.max_default(delta.select(delta<=0),
        flex.min(delta))).iselection()[0]
      self.weight_final = weights[ind]
      self.sites_cart_result = pool[self.weight_final][0][0]
      self.rms_bonds_final,self.rms_angles_final = \
        self.rmsds(sites_cart=self.sites_cart_result)
      assert approx_equal(pool[self.weight_final][0][2], angles[ind])
      assert approx_equal(pool[self.weight_final][0][1], bonds[ind])
      assert approx_equal(self.rms_angles_final, angles[ind])
      assert approx_equal(self.rms_bonds_final, bonds[ind])
    else:
      self.weight_final = self.weight_start
      self.sites_cart_result = sites_cart_result

  def rmsds(self, sites_cart):
    b,a = None,None
    if(self.refiner.geometry_restraints_manager is not None):
      es = self.refiner.geometry_restraints_manager.energies_sites(
        sites_cart = sites_cart)
      a = es.angle_deviations()[2]
      b = es.bond_deviations()[2]
    return b,a

  def adjust_weight_sample_rate(self, weight):
    if(  weight <= 0.01 ): self.weight_sample_rate=0.001
    elif(weight <= 0.1  ): self.weight_sample_rate=0.01
    elif(weight <= 1.0  ): self.weight_sample_rate=0.1
    elif(weight <= 10.  ): self.weight_sample_rate=1.
    elif(weight <= 100. ): self.weight_sample_rate=10.
    elif(weight <= 1000.): self.weight_sample_rate=100.


class box_refinement_manager(object):
  def __init__(self,
               xray_structure,
               target_map,
               geometry_restraints_manager,
               real_space_gradients_delta=1./4,
               max_iterations = 50):
    self.xray_structure = xray_structure
    self.sites_cart = xray_structure.sites_cart()
    self.target_map = target_map
    self.geometry_restraints_manager = geometry_restraints_manager
    self.max_iterations=max_iterations
    self.real_space_gradients_delta = real_space_gradients_delta
    self.weight_optimal = None

  def update_xray_structure(self, new_xray_structure):
    self.xray_structure = new_xray_structure

  def update_target_map(self, new_target_map):
    self.target_map = new_target_map

  def refine(self,
             selection,
             optimize_weight = True,
             start_trial_weight_value = 50,
             selection_buffer_radius=5,
             box_cushion=2,
             rms_bonds_limit = 0.03,
             rms_angles_limit = 3.0):
    sites_cart_moving = self.sites_cart
    selection_within = self.xray_structure.selection_within(
      radius    = selection_buffer_radius,
      selection = selection)
    sel = selection.select(selection_within)
    iselection = flex.size_t()
    for i, state in enumerate(selection):
      if state:
        iselection.append(i)
    box = utils.extract_box_around_model_and_map(
      xray_structure = self.xray_structure,
      map_data       = self.target_map,
      selection      = selection_within,
      box_cushion    = box_cushion)
    new_unit_cell = box.xray_structure_box.unit_cell()
    geo_box = \
      self.geometry_restraints_manager.select(box.selection_within)
    geo_box = geo_box.discard_symmetry(new_unit_cell=new_unit_cell)
    map_box = box.map_box
    sites_cart_box = box.xray_structure_box.sites_cart()
    selection = flex.bool(sites_cart_box.size(), True)
    rsr_simple_refiner = simple(
      target_map                  = map_box,
      selection                   = sel,
      real_space_gradients_delta  = self.real_space_gradients_delta,
      max_iterations              = self.max_iterations,
      geometry_restraints_manager = geo_box)
    real_space_result = refinery(
      refiner                  = rsr_simple_refiner,
      xray_structure           = box.xray_structure_box,
      optimize_weight          = optimize_weight,
      start_trial_weight_value = start_trial_weight_value,
      rms_bonds_limit = rms_bonds_limit,
      rms_angles_limit = rms_angles_limit)
    self.weight_optimal = real_space_result.weight_final
    sites_cart_box_refined = real_space_result.sites_cart_result
    sites_cart_box_refined_shifted_back = \
      sites_cart_box_refined + box.shift_to_map_boxed_sites_back
    sites_cart_refined = sites_cart_box_refined_shifted_back.select(
                           sel)
    sites_cart_moving = sites_cart_moving.set_selected(
      iselection, sites_cart_refined)
    self.xray_structure.set_sites_cart(sites_cart_moving)
    self.sites_cart = self.xray_structure.sites_cart()
