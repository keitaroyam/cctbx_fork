
"""
Base classes for visualization of MolProbity analysis using matplotlib.
"""

from __future__ import division
from libtbx import slots_getstate_setstate

class rotarama_plot_mixin (object) :
  extent = [0, 360, 0, 360]
  def __init__ (self) :
    assert hasattr(self, "figure")
    self._points = []
    self._xyz = [] # only used by Phenix GUI (not offline plotting)
    self.plot = self.figure.add_subplot(111)
    self.plot.set_position([0.1, 0.1, 0.85, 0.85])

  def draw_plot (self,
                 stats,
                 title,
                 points=None,
                 show_labels=True,
                 colormap='jet',
                 contours=None,
                 xyz=None,
                 extent=None,
                 y_marks=None) :
    import matplotlib.cm
    self._points = []
    self._xyz = []
    cm = getattr(matplotlib.cm, colormap)
    self.plot.clear()
    if (extent is None) :
      extent = self.extent
    else :
      assert (len(extent) == 4)
    print extent
    self.plot.imshow(stats, origin="lower", cmap=cm, extent=extent)
    if (contours is not None) :
      self.plot.contour(stats, contours,
        origin="lower",
        colors='k',
        extent=extent)
    if (y_marks is None) :
      self.set_labels()
    else :
      self.set_labels(y_marks=y_marks)
    self.plot.set_title(title)
    if (points is not None) :
      if (xyz is not None) : assert (len(xyz) == len(points))
      for i, (x, y, label, is_outlier) in enumerate(points) :
        if is_outlier :
          self.plot.plot((x,),(y,), 'bo', markerfacecolor='red')
          if show_labels :
            self.plot.text(x, y, label, color='black')
          self._points.append((x,y))
          if (xyz is not None) :
            self._xyz.append(xyz[i])
        else :
          self.plot.plot((x,),(y,), 'bo', markerfacecolor='white')
    self.canvas.draw()

class residue_bin (slots_getstate_setstate) :
  __slots__ = ["residues", "marks", "labels"]
  def __init__ (self) :
    self.residues = []
    self.marks = []
    self.labels = []

  def add_residue (self, residue) :
    self.residues.append(residue)
    n_res = len(self.residues)
    if (n_res % 10 == 0) :
      self.marks.append(n_res)
      if (residue is not None) :
        self.labels.append(residue.residue_group_id_str())
      else :
        self.labels.append("")

  def add_empty (self, n) :
    for i in range(n) :
      self.add_residue(None)

  def n_res (self) :
    return len(self.residues)

  def get_residue_range (self) :
    bin_start = bin_end = None
    i = 0
    while (i < len(self.residues)) :
      if (self.residues[i] is not None) :
        bin_start = self.residues[i].residue_group_id_str()
        break
      i += 1
    i = len(self.residues) - 1
    while (i >= 0) :
      if (self.residues[i] is not None) :
        bin_end = self.residues[i].residue_group_id_str()
        break
      i -= 1
    return "%s - %s" % (bin_start, bin_end)

  def x_values (self) :
    return range(len(self.residues))

  def get_selected (self, index) :
    return self.residues[index]

  def get_real_space_plot_values (self) :
    import numpy
    y = []
    for residue in self.residues :
      if (residue is not None) :
        y.append(residue.get_real_space_plot_values())
      else :
        y.append([numpy.NaN] * 4)
    return numpy.array(y).transpose()

  def get_outlier_plot_values (self) :
    import numpy
    y = []
    for residue in self.residues :
      if (residue is not None) :
        y.append(residue.get_outlier_plot_values())
      else :
        y.append([numpy.NaN] * 4)
    return numpy.array(y).transpose()

class residue_binner (object) :
  def __init__ (self, res_list, bin_size=100, one_chain_per_bin=False) :
    self.bins = []
    last_chain = last_resseq = None
    for i, residue in enumerate(res_list) :
      if (len(self.bins) == 0) or (self.bins[-1].n_res() == bin_size) :
        self.bins.append(residue_bin())
      chain = residue.chain_id
      resseq = residue.resseq_as_int()
      if (last_chain is not None) :
        # FIXME needs to take icode into account!
        if (chain != last_chain) or (resseq > (last_resseq + 10)) :
          if ((chain != last_chain and one_chain_per_bin) or
              (self.bins[-1].n_res() > (bin_size - 20))) :
            self.bins.append(residue_bin())
          else :
            self.bins[-1].add_empty(10)
        elif (resseq > (last_resseq + 1)) and (self.bins[-1].n_res() > 0) :
          gap = resseq - (last_resseq + 1)
          i = 0
          while (i < gap) and (self.bins[-1].n_res() < bin_size) :
            self.bins[-1].add_empty(1)
            i += 1
      self.bins[-1].add_residue(residue)
      last_chain = chain
      last_resseq = resseq

  def get_bin (self, i_bin) :
    return self.bins[i_bin]

  def get_ranges (self) :
    return [ bin.get_residue_range() for bin in self.bins ]

class multi_criterion_plot_mixin (object) :
  def __init__ (self, binner, y_limits) :
    self.binner = binner
    self.y_limits = y_limits
    self.disabled = False

  def plot_range (self, i_bin) :
    if (self.disabled) : return
    # TODO: fix y-ticks, x-ticks width residue ID, add legend
    self.figure.clear()
    bin = self.binner.get_bin(i_bin)
    self._current_bin = bin
    n_plots = 2
    x = bin.x_values()
    # b_iso, cc, fmodel, two_fofc
    y = bin.get_real_space_plot_values()
    (b_iso, cc, fmodel, two_fofc) = bin.get_real_space_plot_values()
    # electron density (observed and calculated)
    p1 = self.figure.add_subplot(n_plots, 1, n_plots)
    p1.set_position([0.075, 0.625, 0.825, 0.325])
    p1.plot(x, y[2], "-", linewidth=1, color="g")
    p1.plot(x, y[3], "-", linewidth=1, color="k")
    p1.set_title("Multi-criterion validation")
    a1 = p1.get_axes()
    a1.set_ylabel("Density", fontproperties=self.get_font("label"))
    a1.set_xlim(-1, 101)
    rho_min, rho_max = self.y_limits["rho"]
    a1.set_ylim(rho_min, rho_max)
    a1.xaxis.set_major_formatter(self.null_fmt)
    # CC
    p2 = self.figure.add_subplot(n_plots, 1, n_plots - 1, sharex=p1)
    p2.set_position([0.075, 0.075, 0.825, 0.55])
    p2.plot(x, y[1], "-", linewidth=1, color="b")
    a2 = p2.get_axes()
    a2.set_ylabel("Local real-space CC", fontproperties=self.get_font("label"),
      color='b')
    a2.set_xlim(-1, 101)
    cc_min, cc_max = self.y_limits["cc"]
    a2.set_ylim(cc_min, cc_max)
    a2.get_yticklabels()[-1].set_visible(False)
    # B_iso
    p3 = p2.twinx()
    p3.set_position([0.075, 0.075, 0.825, 0.55])
    p3.plot(x, y[0], "-", linewidth=1, color="r")
    a3 = p3.get_axes()
    a3.set_ylabel("B-factor", fontproperties=self.get_font("label"),
      color='r')
    b_min, b_max = self.y_limits["b"]
    a3.set_ylim(b_min, b_max)
    a3.get_yticklabels()[-1].set_visible(False)
    # labels
    a2 = p2.get_axes()
    a2.set_xlabel("Residue", fontproperties=self.get_font("label"))
    a2.set_xticks(bin.marks)
    a2.set_xticklabels(bin.labels, fontproperties=self.get_font("basic"))
    a2.get_yticklabels()[-1].set_visible(False)
    # rama, rota, cbeta, clash
    y2 = bin.get_outlier_plot_values()
    p2.plot(x, y2[0] * 0.99, "o")
    p2.plot(x, y2[1] * 0.98, "^")
    p2.plot(x, y2[2] * 0.97, "s")
    p2.plot(x, y2[3] * 0.96, "d")
    self.figure.legend(p2.lines + p3.lines + p1.lines, ["CC", "Ramachandran",
      "Rotamer", "C-beta", "Bad clash", "B-factor", "Fc", "2mFo-DFc"],
      prop=self.get_font("legend"))
    self.canvas.draw()
