from __future__ import division
from libtbx import adopt_init_args
import sys

class flags(object):

  def __init__(self,
        ramachandran=None,
        hydrogen_bond=None,
        rotamer=None,
        reference=None,
        den=None,
        c_beta=None,
        default=False):
    if (ramachandran is None): ramachandran = default
    if (hydrogen_bond is None): hydrogen_bond = default
    if (rotamer is None): rotamer = default
    if (reference is None): reference = default
    if (den is None): den = False #always off by default
    if (c_beta is None): c_beta = default
    adopt_init_args(self, locals())

  def show(self, f=None):
    if (f is None): f = sys.stdout
    print >> f, "generic_restraints_manager.flags:"
    print >> f, "  ramachandran:", self.ramachandran
    print >> f, "  hydrogen_bond:", self.hydrogen_bond
    print >> f, "  rotamer:", self.rotamer
    print >> f, "  reference:", self.reference
    print >> f, "  den:", self.den
    print >> f, "  c_beta:", self.c_beta
