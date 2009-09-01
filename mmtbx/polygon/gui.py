
import sys, os
from mmtbx import polygon, model_vs_data
import iotbx.phil
from math import pi, cos, sin, radians, degrees, floor
import cStringIO

stat_names = { "r_work_pdb" : "R-work(PDB)",
               "r_free_pdb" : "R-free(PDB)",
               "r_work_re_computed" : "R-work",
               "r_free_re_computed" : "R-free",
               "r_work_cutoff" : "R-work with cutoff",
               "r_free_cutoff" : "R-free with cutoff",
               "adp_mean" : "Average B",
               "adp_min" : "Minimum B",
               "adp_max" : "Maximum B",
               "cmpl_in_range" : "Completeness in range",
               "cmpl_d_min_inf" : "Completeness (d_min-inf)",
               "cmpl_6A_inf" : "Completeness (6A-inf)",
               "rama_favored" : "Ramachandran favored",
               "rama_allowed" : "Ramachandran allowed",
               "rama_general" : "Ramachandran general",
               "rama_outliers" : "Ramachandran outliers",
               "k_sol" : "K(sol)",
               "b_sol" : "B(sol)",
               "solvent_cont" : "Solvent content",
               "matthews_coeff" : "Matthews coefficient (Vm)",
               "wilson_b" : "Wilson B",
               "bonds_rmsd" : "RMSD(bonds)",
               "bonds_max" : "Max. bond deviation",
               "angles_rmsd" : "RMSD(angles)",
               "angles_max" : "Max. angle deviation",
               "dihedrals_rmsd" : "RMSD(dihedrals)",
               "dihedrals_max" : "Max. dihedral deviation",
               "chirality_rmsd" : "RMSD(chirality)",
               "chirality_max" : "Max. chirality deviation",
               "planarity_rmsd" : "RMSD(planarity)",
               "planarity_max" : "Max. planarity deviation",
             }
stat_formats = { "r_work_pdb" : "%.4f",
                 "r_free_pdb" : "%.4f",
                 "bonds_rmsd" : "%.3f",
                 "angles_rmsd" : "%.2f",
                 "adp_mean" : "%.1f" }

# XXX: not pickle-able - run this in GUI thread
def convert_histogram_data (polygon_result) :
  histograms = {}
  for (stat, data) in polygon_result :
    histograms[stat] = polygon.convert_to_histogram(data=data,
                                                    n_slots=10)
  return histograms

def get_stats_and_histogram_data (mvd_object, params, debug=False) :
  pdb_file = mvd_object.pdb_file
  mvd_log = cStringIO.StringIO()
  mvd_object.show(log=mvd_log)
  mvd_lines = mvd_log.getvalue().splitlines()
  mvd_results = model_vs_data.read_mvd_output(mvd_lines, None)
  if debug :
    print mvd_log.getvalue()
  fmodel = mvd_object.fmodel
  d_min = fmodel.info().d_min

  stats = {}
  invalid_stats = []
  for stat_name in params.polygon.keys_to_show :
    value = getattr(mvd_results, stat_name, None)
    if value is not None :
      print stat_name, value
      stats[stat_name] = value
    else :
      print "Error: got 'None' for %s" % stat_name
      invalid_stats.append(stat_name)
  for stat_name in invalid_stats :
    params.polygon.keys_to_show.remove(stat_name)
  histograms = polygon.polygon(params=params,
                               d_min=d_min,
                               show_histograms=debug,
                               extract_gui_data=True)
  return stats, histograms

#-----------------------------------------------------------------------
# TODO: tests for everything else
class canvas_layout (object) :
  ratio_cutoffs = [ 0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0 ]

  def __init__ (self, histogram_data, structure_stats, histogram_length=0.30,
      center=(0.5, 0.5), center_offset=0.025) :
    self.units = 1
    histograms = convert_histogram_data(histogram_data)
    self.stats = structure_stats
    self.n_pdb = 0
    max = - sys.maxint
    self.slot_avg = None
    for stat_key, histogram in histograms.iteritems() :
      n_pdb = 0
      for slot in histogram.slots() :
        n_pdb += slot
        if slot > max :
          max = slot
      if self.slot_avg is None :
        self.slot_avg = float(n_pdb) / float(histogram.slots().size())
        self.n_pdb = n_pdb
    self.max = max
    self._histograms = []
    initial_angle = radians(90)
    i = 0
    n_stats = len(histograms)
    interval = 2.0 * pi / float(n_stats)
    for stat_key, histogram in histograms.iteritems() :
      angle = initial_angle + ((i - 0.5) * interval)
      layout = canvas_layout.histogram_layout(stat_key, histogram, angle,
        histogram_length, center, center_offset)
      self._histograms.append(layout)
      i += 1
    self._polygon = canvas_layout.polygon_layout(self.stats, self._histograms)
    self.set_color_model("original")
    self.relative_scale_colors = True

  def resize (self, size) :
    self.w, self.h = size
    self.units = min([self.w, self.h])

  def set_color_model (self, model_name, relative_scaling=True) :
    self.relative_scale_colors = relative_scaling
    if model_name == "original" :
      self.colors = original_color_model()
    elif model_name == "rainbow" :
      self.colors = rainbow_color_model()
    elif model_name == "rmb" :
      self.colors = rmb_color_model()

  def get_color_key (self) :
    if self.relative_scale_colors :
      return (self.colors.ratio_gradient, self.colors.ratio_cutoffs)
    else :
      levels = [0.0, 0.5, 1.0]
      cutoffs = [ int(x * self.max) for x in levels ]
      colors = [ self.colors.get_bin_color(x) for x in levels ]
      return (colors, cutoffs)

  def draw (self, out) :
    colors = self.colors.get_histogram_colors(
      histograms=self._histograms,
      max=self.max,
      mean=self.slot_avg,
      relative_scaling=self.relative_scale_colors)
    for i, histogram in enumerate(self._histograms) :
      for j, (_start, _end) in enumerate(histogram.lines) :
        start = (_start[0] * self.units, _start[1] * self.units)
        end = (_end[0] * self.units, _end[1] * self.units)
        self.draw_bin(out, start, end, colors[i][j])
      anchor = (histogram.text_anchor[0] * self.units,
                histogram.text_anchor[1] * self.units)
      self.draw_labels(
        out=out,
        label=histogram.label,
        min=self.format_value(histogram.min, histogram.name),
        max=self.format_value(histogram.max, histogram.name),
        value=self.format_value(self.stats[histogram.name], histogram.name),
        pos=anchor,
        angle=histogram.angle)
    for (start, end, dashed) in self._polygon.get_line_segments(self.units) :
      if dashed :
        self.draw_dashed_line(out, start, end, (0, 0, 0))
      else :
        self.draw_solid_line(out, start, end, (0, 0, 0))

  def draw_bin (self, out, start, end, color) :
    print "NotImplemented"

  def draw_solid_line (self, out, start, end, color) :
    pass

  def draw_dashed_line (self, out, start, end, color) :
    pass

  def draw_labels (self, out, label, min, max, value, pos, angle) :
    pass

  def format_value (self, value, stat_name) :
    if stat_name in stat_formats :
      return stat_formats[stat_name] % value
    else :
      return "%.3f" % value

  class histogram_layout (object) :
    def __init__ (self, name, histogram, angle, length, center, center_offset) :
      self.name = name
      if name in stat_names :
        self.label = stat_names[name]
      else :
        self.label = name
      min = histogram.data_min()
      max = histogram.data_max()
      bins = [ slot for slot in histogram.slots() ]
      n_bins = len(bins)
      #print "starting at angle %.1f" % (degrees(angle_start))
      (center_x, center_y) = center
      x_start = center_x + (cos(angle) * center_offset)
      y_start = center_y - (sin(angle) * center_offset)
      self.lines = []
      self.text_anchor = (x_start + (cos(angle) * (length + 0.01)),
                          y_start - (sin(angle) * (length + 0.01)))
      for i, bin in enumerate(bins) :
        start_frac = length * (float(i) / float(n_bins))
        end_frac = length * (float(i + 1) / float(n_bins))
        (line_x_start, line_y_start) = (x_start + (cos(angle) * start_frac),
                                        y_start - (sin(angle) * start_frac))
        (line_x_end, line_y_end) = (x_start + (cos(angle) * end_frac),
                                    y_start - (sin(angle) * end_frac))
        self.lines.append(( (line_x_start, line_y_start),
                            (line_x_end, line_y_end) ))
      self.max = max
      self.min = min
      self.bins = bins
      self.angle = angle
      self.length = length
      self.n_bins = n_bins
      self.x_start = x_start
      self.y_start = y_start

    def set_colors (self, bin_colors) :
      self.bin_colors = bin_colors

    def get_polygon_intersection (self, stat) :
      point_on_histogram = True
      hist_x = (stat - self.min) / (self.max - self.min)
      if hist_x > 1.0 :
        hist_x = 1.02
        point_on_histogram = False
      elif hist_x < 0.0 :
        hist_x = -0.02
        point_on_histogram = False
      poly_x = self.x_start + (cos(self.angle) * self.length * hist_x)
      poly_y = self.y_start - (sin(self.angle) * self.length * hist_x)
      return (poly_x, poly_y), point_on_histogram

    def get_absolute_label_position (self, units) :
      angle = self.angle
      x,y = self.text_anchor
      if angle >= radians(60) and angle < radians(120) :
        text_x = x - (w/2) - 5
        text_y = y - h - 15
      elif angle >= radians(120) and angle < radians(240) :
        text_x = x - w - 15
        text_y = y - (h/2)
      elif angle >= radians(240) and angle < radians(300) :
        text_x = x - (w/2)
        text_y = y
      else : # 300 =< angle < 420
        text_x = x + 5
        text_y = y - (h/2)
      return (text_x, text_y)

  class polygon_layout (object) :
    def __init__ (self, stats, histogram_layouts) :
      intersections = []
      on_histogram = []
      for histogram in histogram_layouts :
        stat = stats[histogram.name]
        (x, y), point_on_histogram = histogram.get_polygon_intersection(stat)
        intersections.append((x,y))
        on_histogram.append(point_on_histogram)
      self.intersections = intersections
      for i, (x, y) in enumerate(intersections) :
        if on_histogram[i] :
          pass # TODO: dashed line segments for outliers

    def get_line_segments (self, units=1.0) :
      for i, _end in enumerate(self.intersections) :
        _start = self.intersections[i - 1]
        start = (_start[0] * units, _start[1] * units)
        end = (_end[0] * units, _end[1] * units)
        yield (start, end, False)

#-----------------------------------------------------------------------
class color_model (object) :
  def __init__ (self) :
    self.ratio_cutoffs = []
    self.ratio_gradient = []

  def get_histogram_colors (self, histograms, max, mean,
      relative_scaling=True) :
    assert len(self.ratio_gradient) == len(self.ratio_cutoffs) + 1
    colors = []
    ratio_cutoffs = self.ratio_cutoffs
    for histogram in histograms :
      bin_colors = []
      if relative_scaling :
        for bin in histogram.bins :
          val = bin / mean
          c = None
          for i, cutoff in enumerate(ratio_cutoffs) :
            if cutoff >= val :
              c = self.ratio_gradient[i]
              break
          if c is None :
            c = self.ratio_gradient[-1]
          bin_colors.append(c)
      else :
        for bin in histogram.bins :
          val = float(bin) / float(max)
          bin_colors.append(self.get_bin_color(val))
      colors.append(bin_colors)
    return colors

  def get_bin_color (self, value) :
    return (0, 0, 0)

class original_color_model (color_model) :
  def __init__ (self) :
    self.ratio_cutoffs = [ 0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0 ]
    self.ratio_gradient = [ (240, 240, 240),  # off-white
                            (255,   0,   0),  # red
                            (255, 150,   0),  # orange
                            (255, 255,   0),  # yellow
                            (  0, 255,   0),  # green
                            (  0, 255, 255),  # cyan
                            (  0,   0, 255),  # blue
                            (130,   0, 255) ] # purple

class rainbow_color_model (color_model) :
  def __init__ (self) :
    self.ratio_cutoffs = [ 0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0 ]
    self.ratio_gradient = [ hsv2rgb(240.0-(240.0*x), 1, 1) for x in
                            [ float(x) / 7.0 for x in range(8) ] ]

  def get_bin_color (self, value) :
    color = hsv2rgb(240.0 - (240.0 * value), 1, 1)
    return color

class rmb_color_model (color_model) :
  def __init__ (self) :
    self.ratio_cutoffs = [ 0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0 ]
    self.ratio_gradient = [ hsv2rgb(240.0+(120.0*x), 1, 1) for x in
                            [ float(x) / 7.0 for x in range(8) ] ]

  def get_bin_color (self, value) :
    print 240.0 + (120.0 * value)
    color = hsv2rgb(240.0 + (120.0 * value), 1, 1)
    print value, color
    return color

def hsv2rgb (h, s, v) :
  if h >= 360 :
    h -= 360
  h /= 60
  v *= 255

  i = floor(h)
  f = h - i
  p = v * (1 - s)
  q = v * (1 - (s * f))
  t = v * (1 - (s * (1 - f)))

  if   i == 0 : return (v, t, p)
  elif i == 1 : return (q, v, p)
  elif i == 2 : return (p, v, t)
  elif i == 3 : return (p, q, v)
  elif i == 4 : return (t, p, v)
  else        : return (v, p, q)

#---end
