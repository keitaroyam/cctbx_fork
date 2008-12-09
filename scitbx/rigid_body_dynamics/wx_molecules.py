from scitbx.rigid_body_dynamics import tst_molecules
from scitbx.math import minimum_covering_sphere, sphere_3d
from scitbx.array_family import flex
from gltbx import wx_viewer
import wx
import sys

class viewer(wx_viewer.show_points_and_lines_mixin):

  def __init__(self, *args, **kwds):
    super(viewer, self).__init__(*args, **kwds)

  def set_points(self):
    self.points.clear()
    for B,AJA in zip(self.sim.bodies, self.sim.AJA_accu):
      for s in B.sites:
        self.points.append(AJA * s)

  def set_points_and_lines(self):
    self.sim = tst_molecules.simulation_gly_no_h()
    self.points = flex.vec3_double()
    self.set_points()
    def add_line(i, j, color):
      line = (i,j)
      self.line_i_seqs.append(line)
      self.line_colors[line] = color
    self.labels = []
    B_off = []
    for B in self.sim.bodies:
      B_off.append(len(self.labels))
      self.labels.extend(B.labels)
      def add_off(i):
        if (i < 0): return B_off[B.parent+1] + i
        else:       return B_off[-1] + i
      for bond in B.bonds:
        i,j = [add_off(b) for b in bond]
        add_line(i, j, (1,0,0))
    mcs = minimum_covering_sphere(self.points, epsilon=1.e-2)
    self.minimum_covering_sphere = sphere_3d(
      center=mcs.center(), radius=mcs.radius()*1.3)
    self.flag_show_minimum_covering_sphere = False
    self.flag_show_rotation_center = False
    self.steps_per_tab = 1
    print "Press and hold Tab key to run the simulation."
    print "Press Shift-Tab to increase speed."
    print "Press Ctrl-Tab  to decrease speed."

  def tab_callback(self, shift_down=False, control_down=False):
    if (shift_down or control_down):
      if (shift_down):
        self.steps_per_tab = min(256, self.steps_per_tab * 2)
      else:
        self.steps_per_tab = max(1, self.steps_per_tab // 2)
      print "Steps per Tab:", self.steps_per_tab
      return
    self.sim.dynamics_step(delta_t=0.05)
    self.set_points()
    self.labels_display_list = None
    self.lines_display_list = None
    self.points_display_list = None
    self.OnRedraw()

class App(wx_viewer.App):

  def __init__(self, args):
    assert len(args) == 0
    super(App, self).__init__(title="wx_molecules")

  def init_view_objects(self):
    box = wx.BoxSizer(wx.VERTICAL)
    self.view_objects = viewer(self.frame, size=(600,600))
    self.view_objects.set_points_and_lines()
    box.Add(self.view_objects, wx.EXPAND, wx.EXPAND)
    self.frame.SetSizer(box)
    box.SetSizeHints(self.frame)

def run(args):
  App(args).MainLoop()

if (__name__ == "__main__"):
  run(sys.argv[1:])
