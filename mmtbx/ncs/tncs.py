from __future__ import division
import cctbx.array_family.flex # import dependency
import boost.python
ext = boost.python.import_ext("mmtbx_ncs_ext")
from scitbx.array_family import flex
from cctbx import sgtbx
from libtbx import adopt_init_args
from scitbx import lbfgsb
import math
import scitbx.math
from scitbx.math import matrix
import sys
from scitbx.math import superpose
import mmtbx.alignment
from libtbx.test_utils import approx_equal

class groups(object):

  def __init__(self,
               pdb_hierarchy,
               crystal_symmetry,
               angular_difference_threshold_deg=10.,
               sequence_identity_threshold=90.):
    h = pdb_hierarchy
    n_atoms_all = h.atoms_size()
    s_str = "altloc ' ' and not water and pepnames"
    h = h.select(h.atom_selection_cache().selection(s_str))
    h1 = h.deep_copy()
    unit_cell = crystal_symmetry.unit_cell()
    result = []
    # double loop over chains to find matching pairs related by pure translation
    for c1 in h1.chains():
      c1.parent().remove_chain(c1)
      if([c1.is_protein(), c1.is_na()].count(True)==0): continue
      r1 = list(c1.residues())
      c1_seq = "".join(c1.as_sequence())
      sc_1_tmp = c1.atoms().extract_xyz()
      h1_p1 = h1.expand_to_p1(crystal_symmetry=crystal_symmetry)
      for c2 in h1_p1.chains():
        r2 = list(c2.residues())
        c2_seq = "".join(c2.as_sequence())
        sites_cart_1, sites_cart_2 = None,None
        sc_2_tmp = c2.atoms().extract_xyz()
        # chains are identical
        if(c1_seq==c2_seq and sc_1_tmp.size()==sc_2_tmp.size()):
          sites_cart_1 = sc_1_tmp
          sites_cart_2 = sc_2_tmp
        # chains are not identical, do alignment
        else:
          align_obj = mmtbx.alignment.align(seq_a = c1_seq, seq_b = c2_seq)
          alignment = align_obj.extract_alignment()
          matches = alignment.matches()
          equal = matches.count("|")
          total = len(alignment.a) - alignment.a.count("-")
          p_identity = 100.*equal/max(1,total)
          if(p_identity>sequence_identity_threshold):
            sites_cart_1 = flex.vec3_double()
            sites_cart_2 = flex.vec3_double()
            for i1, i2, match in zip(alignment.i_seqs_a, alignment.i_seqs_b,
                                     matches):
              if(i1 is not None and i2 is not None and match=="|"):
                r1i, r2i = r1[i1], r2[i2]
                assert r1i.resname==r2i.resname, [r1i.resname,r2i.resname,i1,i2]
                for a1 in r1i.atoms():
                  for a2 in r2i.atoms():
                    if(a1.name == a2.name):
                      sites_cart_1.append(a1.xyz)
                      sites_cart_2.append(a2.xyz)
                      break
        # superpose two sequence-aligned chains
        if([sites_cart_1,sites_cart_2].count(None)==0):
          lsq_fit_obj = superpose.least_squares_fit(
            reference_sites = sites_cart_1,
            other_sites     = sites_cart_2)
          angle = lsq_fit_obj.r.rotation_angle()
          if(angle < angular_difference_threshold_deg):
            t_frac = unit_cell.fractionalize((sites_cart_1-sites_cart_2).mean())
            t_frac = [math.modf(t)[0] for t in t_frac] # put into [-1,1]
            radius = flex.sum(flex.sqrt((sites_cart_1-
              sites_cart_1.mean()).dot()))/sites_cart_1.size()*4./3.
            fracscat = c1.atoms_size()/n_atoms_all
            result.append([lsq_fit_obj.r, t_frac, angle, radius, fracscat])
            # show tNCS group
            fmt="chains %s <> %s angle: %4.2f trans.vect.: (%s) fracscat: %5.3f"
            t = ",".join([("%6.3f"%t_).strip() for t_ in t_frac]).strip()
            print fmt%(c1.id, c2.id, angle, t, fracscat)
    # compose final tNCS pairs object
    self.ncs_pairs = []
    for _ in result:
      r, t, angle, rad, fs = _
      ncs_pair = ext.pair(
        r = r,
        t = t,
        radius=rad,
        radius_estimate=rad,
        fracscat=fs,
        rho_mn=flex.double()) # rho_mn undefined, needs to be set later
      self.ncs_pairs.append(ncs_pair)

def initialize_rho_mn(ncs_pairs, d_spacings_data, binner, rms=0.5):
  """
  Initialize rho_mn
    rhoMN = exp(-(2*pi^2/3)*(rms/d)^2, and rms=0.4-0.8 is probably a good.
  """
  n_bins = binner.n_bins_used()
  rho_mn_initial = flex.double(n_bins, 0)
  cntr=0
  for i_bin in binner.range_used():
    sel_bin = binner.selection(i_bin)
    if(sel_bin.count(True)>0):
      arg = (2*math.pi**2/3)*(rms/flex.mean(d_spacings_data.select(sel_bin)))**2
      rho_mn_initial[cntr] = math.exp(-1*arg)
    cntr+=1
  for p in ncs_pairs:
    p.set_rhoMN(rho_mn_initial)

def lbfgs_run(target_evaluator, use_bounds, lower_bound, upper_bound):
  minimizer = lbfgsb.minimizer(
    n   = target_evaluator.n,
    #factr=1.e+1, XXX Affects speed significantly
    l   = lower_bound, # lower bound
    u   = upper_bound, # upper bound
    nbd = flex.int(target_evaluator.n, use_bounds)) # flag to apply both bounds
  minimizer.error = None
  try:
    icall = 0
    while 1:
      icall += 1
      x, f, g = target_evaluator()
      #print "x,f:", ",".join(["%6.3f"%x_ for x_ in x]), f, icall
      have_request = minimizer.process(x, f, g)
      if(have_request):
        requests_f_and_g = minimizer.requests_f_and_g()
        continue
      assert not minimizer.requests_f_and_g()
      if(minimizer.is_terminated()): break
  except RuntimeError, e:
    minimizer.error = str(e)
  minimizer.n_calls = icall
  return minimizer

class minimizer(object):

  def __init__(self,
               potential,
               use_bounds,
               lower_bound,
               upper_bound,
               initial_values):
    adopt_init_args(self, locals())
    self.x = initial_values
    self.n = self.x.size()

  def run(self):
    self.minimizer = lbfgs_run(
      target_evaluator=self,
      use_bounds=self.use_bounds,
      lower_bound = self.lower_bound,
      upper_bound = self.upper_bound)
    self()
    return self

  def __call__(self):
    self.potential.update(x = self.x)
    self.f = self.potential.target()
    self.g = self.potential.gradient()
    return self.x, self.f, self.g

class potential(object):

  def __init__(self, f_obs, ncs_pairs, reflections_per_bin):
    adopt_init_args(self, locals())
    # Create bins
    f_obs.setup_binner(reflections_per_bin = reflections_per_bin)
    self.binner = f_obs.binner()
    n_bins = self.binner.n_bins_used()
    self.n_bins = n_bins
    self.SigmaN = None
    self.update_SigmaN()
    #
    self.rbin = flex.int(f_obs.data().size(), -1)
    for i_bin in self.binner.range_used():
      for i_seq in self.binner.array_indices(i_bin):
        self.rbin[i_seq] = i_bin-1 # i_bin starts with 1, not 0 !
    assert flex.min(self.rbin)==0
    assert flex.max(self.rbin)==n_bins-1
    # Extract symmetry matrices
    self.sym_matrices = []
    for m_as_string in f_obs.space_group().smx():
      o = sgtbx.rt_mx(symbol=str(m_as_string), t_den=f_obs.space_group().t_den())
      m_as_double = o.r().as_double()
      self.sym_matrices.append(m_as_double)
    self.gradient_evaluator = None
    self.target_and_grads = ext.tncs_eps_factor_refinery(
        tncs_pairs               = self.ncs_pairs,
        f_obs                    = self.f_obs.data(),
        sigma_f_obs              = self.f_obs.sigmas(),
        rbin                     = self.rbin,
        SigmaN                   = self.SigmaN,
        space_group              = self.f_obs.space_group(),
        miller_indices           = self.f_obs.indices(),
        fractionalization_matrix = self.f_obs.unit_cell().fractionalization_matrix(),
        sym_matrices             = self.sym_matrices)

    self.update()

  def update(self, x=None):
    if(self.gradient_evaluator=="rhoMN"):
      size = len(self.ncs_pairs)
      for i, ncs_pair in enumerate(self.ncs_pairs):
        ncs_pair.set_rhoMN(x[i*self.n_bins:(i+1)*self.n_bins])
      self.target_and_grads.update_pairs(self.ncs_pairs)
    elif(self.gradient_evaluator=="radius"):
      for ncs_pair, x_ in zip(self.ncs_pairs, x):
        ncs_pair.set_radius(x_)
      self.target_and_grads = ext.tncs_eps_factor_refinery(
        tncs_pairs               = self.ncs_pairs,
        f_obs                    = self.f_obs.data(),
        sigma_f_obs              = self.f_obs.sigmas(),
        rbin                     = self.rbin,
        SigmaN                   = self.SigmaN,
        space_group              = self.f_obs.space_group(),
        miller_indices           = self.f_obs.indices(),
        fractionalization_matrix = self.f_obs.unit_cell().fractionalization_matrix(),
        sym_matrices             = self.sym_matrices)
      self.target_and_grads.set_compute_gradients_radius()

  def update_SigmaN(self):
    if(self.SigmaN is None):
      eps = self.f_obs.epsilons().data().as_double()
    else:
      eps = self.target_and_grads.tncs_epsfac()
    self.SigmaN = flex.double(self.f_obs.data().size(), 0)
    for i_bin in self.binner.range_used():
      bin_sel = self.f_obs.binner().selection(i_bin)
      f_obs_bin = self.f_obs.select(bin_sel)
      f_obs_bin_data = f_obs_bin.data()
      f_obs_bin_data_size = f_obs_bin_data.size()
      if(f_obs_bin_data_size>0):
        eps_bin = eps.select(bin_sel)
        sn = flex.sum(f_obs_bin_data*f_obs_bin_data/eps_bin)/f_obs_bin_data_size
        self.SigmaN = self.SigmaN.set_selected(bin_sel, sn)
    assert self.SigmaN.all_gt(0)

  def set_refine_radius(self):
    self.gradient_evaluator = "radius"
    self.target_and_grads.set_compute_gradients_radius()
    return self

  def set_refine_rhoMN(self):
    self.gradient_evaluator = "rhoMN"
    self.target_and_grads.set_compute_gradients_rho_mn()
    return self

  def target(self):
    return self.target_and_grads.target()

  def gradient(self):
    if(self.gradient_evaluator=="rhoMN"):
      return self.target_and_grads.gradient_rhoMN()
    elif(self.gradient_evaluator=="radius"):
      return self.target_and_grads.gradient_radius()
    else: assert 0

def finite_differences_grad_radius(ncs_pairs, f_obs, reflections_per_bin,
      tolerance):
  reflections_per_bin = min(f_obs.data().size(), reflections_per_bin)
  f_obs.setup_binner(reflections_per_bin = reflections_per_bin)
  binner = f_obs.binner()
  n_bins = binner.n_bins_used()
  #
  radii = flex.double()
  for ncs_pair in ncs_pairs:
    radii.append(ncs_pair.radius)
  #
  pot = potential(f_obs = f_obs, ncs_pairs = ncs_pairs,
      reflections_per_bin = reflections_per_bin)
  pot = pot.set_refine_radius()
  t = pot.target()
  g_exact = pot.gradient()
  #print "Exact:", list(g_exact)
  #
  eps = 1.e-4
  #
  g_fd = []
  for i, rad in enumerate(radii):
    radii_p = radii.deep_copy()
    radii_m = radii.deep_copy()
    radii_p[i] = radii[i]+eps
    radii_m[i] = radii[i]-eps
    #
    pot.update(x = flex.double(radii_p))
    t1 = pot.target()
    #
    pot.update(x = flex.double(radii_m))
    t2 = pot.target()
    #
    g_fd_ = (t1-t2)/(2*eps)
    g_fd.append(g_fd_)
  #print "Finite diff.:",g_fd
  relative_error = flex.double()
  for g1,g2 in zip(g_exact, g_fd):
    #print "exact: %10.6f fd: %10.6f"%(g1,g2)
    relative_error.append( abs((g1-g2)/(g1+g2))*2.*100. )
  mmm = relative_error.min_max_mean().as_tuple()
  print "min/max/mean of |(g_eaxct-g_fd)/(g_eaxct+g_fd)|*100.*2:",\
    "%6.4f %6.4f %6.4f"%mmm
  assert approx_equal(mmm, [0,0,0], tolerance)

def finite_differences_rho_mn(ncs_pairs, f_obs, reflections_per_bin,
      tolerance):
  reflections_per_bin = min(f_obs.data().size(), reflections_per_bin)
  f_obs.setup_binner(reflections_per_bin = reflections_per_bin)
  binner = f_obs.binner()
  n_bins = binner.n_bins_used()
  #
  pot = potential(f_obs = f_obs, ncs_pairs = ncs_pairs,
      reflections_per_bin = reflections_per_bin)
  pot = pot.set_refine_rhoMN()
  t = pot.target()
  g_exact = pot.gradient()
  #
  rho_mn = flex.double()
  for p in ncs_pairs:
    rho_mn.extend(p.rho_mn)
  #
  eps = 1.e-6
  #
  g_fd = []
  for i, rho_mn_i in enumerate(rho_mn):
    rho_mn_p = rho_mn.deep_copy()
    rho_mn_p[i] = rho_mn_i + eps
    rho_mn_m = rho_mn.deep_copy()
    rho_mn_m[i] = rho_mn_i - eps
    #
    pot.update(x = rho_mn_p)
    t1 = pot.target()
    #
    pot.update(x = rho_mn_m)
    t2 = pot.target()
    #
    g_fd_ = (t1-t2)/(2*eps)
    g_fd.append(g_fd_)
  relative_error = flex.double()
  for g1,g2 in zip(g_exact, g_fd):
    #print "exact: %10.6f fd: %10.6f"%(g1,g2)
    relative_error.append( abs((g1-g2)/(g1+g2))*2.*100. )
  mmm = relative_error.min_max_mean().as_tuple()
  print "min/max/mean of |(g_eaxct-g_fd)/(g_eaxct+g_fd)|*100.*2:",\
    "%6.4f %6.4f %6.4f"%mmm
  assert approx_equal(mmm, [0,0,0], tolerance)

class compute_eps_factor(object):

  def __init__(self, f_obs, pdb_hierarchy, reflections_per_bin):
    f_obs = f_obs.deep_copy()
    if(not f_obs.sigmas_are_sensible()):
      f_obs.set_sigmas(sigmas = flex.double(f_obs.data().size(), 0.0))
    reflections_per_bin = min(f_obs.data().size(), reflections_per_bin)
    f_obs.setup_binner(reflections_per_bin = reflections_per_bin)
    self.unit_cell = f_obs.unit_cell()
    #
    self.ncs_pairs = groups(
      pdb_hierarchy    = pdb_hierarchy,
      crystal_symmetry = f_obs.crystal_symmetry()).ncs_pairs
    initialize_rho_mn(
      ncs_pairs       = self.ncs_pairs,
      d_spacings_data = f_obs.d_spacings().data(),
      binner          = f_obs.binner())
    self.epsfac = None
    if(len(self.ncs_pairs)>0):
      # Radii
      radii = flex.double()
      rad_lower_bound = flex.double()
      rad_upper_bound = flex.double()
      for ncs_pair in self.ncs_pairs:
        radii.append(ncs_pair.radius)
        rad_lower_bound.append(ncs_pair.radius/3)
        rad_upper_bound.append(ncs_pair.radius*3)
      # Target and gradients evaluator
      pot = potential(f_obs = f_obs, ncs_pairs = self.ncs_pairs,
        reflections_per_bin = reflections_per_bin)
      for it in xrange(2):
        # refine eps fac
        rho_mn = flex.double()
        for ncs_pair in self.ncs_pairs:
          rho_mn.extend(ncs_pair.rho_mn)
        m = minimizer(
          potential      = pot.set_refine_rhoMN(),
          use_bounds     = 2,
          lower_bound    = flex.double(rho_mn.size(), 0.),
          upper_bound    = flex.double(rho_mn.size(), 1.),
          initial_values = rho_mn).run()
        # refine radius
        radii = flex.double()
        for ncs_pair in self.ncs_pairs:
          radii.append(ncs_pair.radius)
        m = minimizer(
          potential      = pot.set_refine_radius(),
          use_bounds     = 2,
          lower_bound    = rad_lower_bound,
          upper_bound    = rad_upper_bound,
          initial_values = radii).run()
      self.epsfac = pot.target_and_grads.tncs_epsfac()

  def show_summary(self, log=None):
    if(self.epsfac is None): return None
    if(log is None): log = sys.stdout
    for i, ncs_pair in enumerate(self.ncs_pairs):
      print >> log, "tNCS group: %d"%i
      angle = matrix.sqr(ncs_pair.r).rotation_angle()
      t = ",".join([("%6.3f"%t_).strip() for t_ in ncs_pair.t]).strip()
      t_cart = ",".join([("%6.3f"%t_).strip()
        for t_ in self.unit_cell.orthogonalize(ncs_pair.t)]).strip()
      r = ",".join([("%8.6f"%r_).strip() for r_ in ncs_pair.r]).strip()
      print >> log, "  Translation (fractional): (%s)"%t
      print >> log, "  Translation (Cartesian):  (%s)"%t_cart
      print >> log, "  Rotation (deg): %-5.2f"%angle
      print >> log, "  Rotation matrix: (%s)"%r
      print >> log, "  Radius: %-6.1f"%ncs_pair.radius
      print >> log, "  Radius (estimate): %-6.1f"%ncs_pair.radius_estimate
      print >> log, "  fracscat:", ncs_pair.fracscat
    print >> log, "tNCS eps factor: min,max,mean: %6.4f %6.4f %6.4f"%\
      self.epsfac.min_max_mean().as_tuple()
