from cctbx import restraints
from cctbx.array_family import flex
import sys

class energies:

  def __init__(self, sites_cart,
                     bond_proxies=None,
                     repulsion_proxies=None,
                     angle_proxies=None,
                     dihedral_proxies=None,
                     chirality_proxies=None,
                     planarity_proxies=None,
                     compute_gradients=0001,
                     disable_asu_cache=00000):
    if (compute_gradients):
      self.gradients = flex.vec3_double(sites_cart.size(), [0,0,0])
    else:
      self.gradients = None
    if (bond_proxies is None):
      self.n_bond_proxies = None
      self.bond_residual_sum = 0
    else:
      self.n_bond_proxies = bond_proxies.n_total()
      self.bond_residual_sum = restraints.bond_residual_sum(
        sites_cart=sites_cart,
        sorted_asu_proxies=bond_proxies,
        gradient_array=self.gradients,
        disable_cache=disable_asu_cache)
    if (repulsion_proxies is None):
      self.n_repulsion_proxies = None
      self.repulsion_residual_sum = 0
    else:
      self.n_repulsion_proxies = repulsion_proxies.n_total()
      self.repulsion_residual_sum = restraints.repulsion_residual_sum(
        sites_cart=sites_cart,
        sorted_asu_proxies=repulsion_proxies,
        gradient_array=self.gradients,
        function=restraints.repulsion_function(),
        disable_cache=00000)
    if (angle_proxies is None):
      self.n_angle_proxies = None
      self.angle_residual_sum = 0
    else:
      self.n_angle_proxies = len(angle_proxies)
      self.angle_residual_sum = restraints.angle_residual_sum(
        sites_cart=sites_cart,
        proxies=angle_proxies,
        gradient_array=self.gradients)
    if (dihedral_proxies is None):
      self.n_dihedral_proxies = None
      self.dihedral_residual_sum = 0
    else:
      self.n_dihedral_proxies = len(dihedral_proxies)
      self.dihedral_residual_sum = restraints.dihedral_residual_sum(
          sites_cart=sites_cart,
          proxies=dihedral_proxies,
          gradient_array=self.gradients)
    if (chirality_proxies is None):
      self.n_chirality_proxies = None
      self.chirality_residual_sum = 0
    else:
      self.n_chirality_proxies = len(chirality_proxies)
      self.chirality_residual_sum = restraints.chirality_residual_sum(
          sites_cart=sites_cart,
          proxies=chirality_proxies,
          gradient_array=self.gradients)
    if (planarity_proxies is None):
      self.n_planarity_proxies = None
      self.planarity_residual_sum = 0
    else:
      self.n_planarity_proxies = len(planarity_proxies)
      self.planarity_residual_sum = restraints.planarity_residual_sum(
          sites_cart=sites_cart,
          proxies=planarity_proxies,
          gradient_array=self.gradients)

  def target(self):
    return(self.bond_residual_sum
         + self.repulsion_residual_sum
         + self.angle_residual_sum
         + self.dihedral_residual_sum
         + self.chirality_residual_sum
         + self.planarity_residual_sum)

  def gradient_norm(self):
    if (self.gradients is not None):
      return flex.sum_sq(self.gradients.as_double())

  def show(self, f=None):
    if (f is None): f = sys.stdout
    print >> f, "target: %.6g" % self.target()
    if (self.n_bond_proxies is not None):
      print >> f, "  bond_residual_sum (n=%d): %.6g" % (
        self.n_bond_proxies, self.bond_residual_sum)
    if (self.n_repulsion_proxies is not None):
      print >> f, "  repulsion_residual_sum (n=%d): %.6g" % (
        self.n_repulsion_proxies, self.repulsion_residual_sum)
    if (self.n_angle_proxies is not None):
      print >> f, "  angle_residual_sum (n=%d): %.6g" % (
        self.n_angle_proxies, self.angle_residual_sum)
    if (self.n_dihedral_proxies is not None):
      print >> f, "  dihedral_residual_sum (n=%d): %.6g" % (
        self.n_dihedral_proxies, self.dihedral_residual_sum)
    if (self.n_chirality_proxies is not None):
      print >> f, "  chirality_residual_sum (n=%d): %.6g" % (
        self.n_chirality_proxies, self.chirality_residual_sum)
    if (self.n_planarity_proxies is not None):
      print >> f, "  planarity_residual_sum (n=%d): %.6g" % (
        self.n_planarity_proxies, self.planarity_residual_sum)
    if (self.gradients is not None):
      print >> f, "  norm of gradients: %.6g" % self.gradient_norm()
