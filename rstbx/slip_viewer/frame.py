# -*- mode: python; coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# Known issues: Recentering on resize and when switching between
# different image types.  Ring centre on image switch.
#
# $Id$

from __future__ import division

import os
import wx

from rstbx.viewer.frame import EVT_EXTERNAL_UPDATE
from rstbx.viewer.frame import XrayFrame as XFBaseClass
from rstbx.viewer import settings as rv_settings, image as rv_image
from wxtbx import bitmaps

class chooser_wrapper:
  def __init__(self, image_set, index):
    self.image_set = image_set
    self.path = os.path.basename(image_set.get_path(index))
    self.full_path = image_set.get_path(index)
    self.index = index

  def __str__(self):
    return "%s [%d]"%(self.path,self.index)

  def get_detectorbase(self):
    return self.image_set.get_detectorbase(self.index)

from rstbx.slip_viewer.slip_display import AppFrame
class XrayFrame (AppFrame,XFBaseClass) :
  def __init__ (self, *args, **kwds) :
    self.params = kwds.get("params", None)
    if "params" in kwds:
      del kwds["params"] #otherwise wx complains

    wx.Frame.__init__(self,*args,**kwds)
    self.settings = rv_settings()

    self.sizer = wx.BoxSizer(wx.VERTICAL)
    self.SetSizer(self.sizer)

    self.init_pyslip_presizer()

    self.sizer.Add(self.viewer, 1, wx.EXPAND)
    self.statusbar = self.CreateStatusBar()
    self.settings_frame = None
    self._calibration_frame = None
    self._ring_frame = None
    self._uc_frame = None
    self._score_frame = None
    self.zoom_frame = None
    self.plot_frame = None

    self.metrology_matrices = None

    # Currently displayed image.  XXX Can this be zapped?
    self._img = None

    self._distl = None
    self.toolbar = self.CreateToolBar(style=wx.TB_3DBUTTONS|wx.TB_TEXT)
    self.setup_toolbar()
    self.toolbar.Realize()
    self.mb = wx.MenuBar()
    self.setup_menus()
    self.SetMenuBar(self.mb)
    self.Fit()
    self.SetMinSize(self.GetSize())
    self.SetSize((720,720))
    self.OnShowSettings(None)
    self.Bind(EVT_EXTERNAL_UPDATE, self.OnExternalUpdate)

    self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateUICalibration,
              id=self._id_calibration)
    self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateUINext,
              id=wx.ID_FORWARD)
    self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateUIPrevious,
              id=wx.ID_BACKWARD)
    self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateUIRing,
              id=self._id_ring)
    self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateUIUC,
              id=self._id_uc)
    self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateUIScore,
              id=self._id_score)

  def setup_toolbar(self) :
    XFBaseClass.setup_toolbar(self)

    btn = self.toolbar.AddLabelTool(id=wx.ID_SAVEAS,
    label="Save As...",
    bitmap=bitmaps.fetch_icon_bitmap("actions","save_all", 32),
    shortHelp="Save As...",
    kind=wx.ITEM_NORMAL)
    self.Bind(wx.EVT_MENU, self.OnSaveAs, btn)

  def init_pyslip_presizer(self):
    self.viewer  = wx.Panel(self, wx.ID_ANY, size=(1024,640))
    self.viewer.SetMinSize((640,640))
    self.viewer.SetBackgroundColour(wx.WHITE)
    self.viewer.ClearBackground()
    # create select event dispatch directory
    self.demo_select_dispatch = {}

    #self.tile_directory = None#"/Users/nksauter/rawdata/demo/insulin_1_001.img"

    # build the GUI
    self.make_gui(self.viewer)

    from rstbx.slip_viewer import pyslip
    # finally, bind events to handlers
    self.pyslip.Bind(pyslip.EVT_PYSLIP_SELECT, self.handle_select_event)
    self.pyslip.Bind(pyslip.EVT_PYSLIP_POSITION, self.handle_position_event)
    self.pyslip.Bind(pyslip.EVT_PYSLIP_LEVEL, self.handle_level_change)

  def init_pyslip_postsizer(self):
    self.pyslip.ZoomToLevel(-2)#tiles.zoom_level
    self.pyslip.GotoPosition(
      self.pyslip.tiles.get_initial_instrument_centering_within_picture_as_lon_lat()
    )

  def setup_menus (self) :
    file_menu = wx.Menu()
    self.mb.Append(file_menu, "File")
    item = file_menu.Append(-1, "Open integration results...")
    self.Bind(wx.EVT_MENU, self.OnLoadIntegration, item)
    item = file_menu.Append(-1, "Open image...")
    self.Bind(wx.EVT_MENU, self.OnLoadFile, item)
    actions_menu = wx.Menu()
    self.mb.Append(actions_menu, "Actions")
    item = actions_menu.Append(-1, "Change beam center...")
    self.Bind(wx.EVT_MENU, self.OnChangeBeamCenter, item)
    item = actions_menu.Append(-1, "Reset beam center to header value")
    self.Bind(wx.EVT_MENU, lambda evt: self.viewer.ResetBeamCenter(), item)
    item = actions_menu.Append(-1, "Save As...")
    self.Bind(wx.EVT_MENU, self.OnSaveAs, item)

    # Known wxWidgets/wxPython issue
    # (http://trac.wxwidgets.org/ticket/12394): stock item ID is
    # expected for zero-length text.  Work around by making text
    # contain single space. XXX Placement
    self._id_calibration = wx.NewId()
    item = actions_menu.Append(self._id_calibration, " ")
    self.Bind(wx.EVT_MENU, self.OnCalibration, source=item)

    # XXX Placement
    self._id_ring = wx.NewId()
    item = actions_menu.Append(self._id_ring, " ")
    self.Bind(wx.EVT_MENU, self.OnRing, source=item)

    # XXX Placement
    self._id_uc = wx.NewId()
    item = actions_menu.Append(self._id_uc, " ")
    self.Bind(wx.EVT_MENU, self.OnUC, source=item)

    # XXX Placement
    self._id_score = wx.NewId()
    item = actions_menu.Append(self._id_score, " ")
    self.Bind(wx.EVT_MENU, self.OnScore, source=item)

  def has_four_quadrants(self):
    d = self.pyslip.tiles.raw_image.get_detector()
    return len(d) > 1 and len(d.hierarchy()) == 4

  def add_file_name_or_data (self, file_name_or_data) :
      """The add_file_name_or_data() function appends @p
      file_name_or_data to the image chooser, unless it is already
      present.  For file-backed images, the base name is displayed in
      the chooser.  If necessary, the number of entries in the chooser
      is pruned.  The function returns the index of the recently added
      entry.  XXX This is probably the place for heuristics to determine
      if the viewer was given a pattern, or a plain list of files.  XXX
      Rename this function, because it only deals with the chooser?
      """

      key = self.get_key(file_name_or_data)
      for i in xrange(self.image_chooser.GetCount()) :
        if (key == str(self.image_chooser.GetClientData(i))) :
          return i
      if (self.image_chooser.GetCount() >= self.CHOOSER_SIZE) :
        self.image_chooser.Delete(0)
      i = self.image_chooser.GetCount()
      if (type(file_name_or_data) is dict) :
        self.image_chooser.Insert(key, i, None)
      elif (isinstance(file_name_or_data, chooser_wrapper)):
        self.image_chooser.Insert(key, i, file_name_or_data)
      else :
        self.image_chooser.Insert(os.path.basename(key), i, key)
      return i

  def load_image (self, file_name_or_data) :
    """The load_image() function displays the image from @p
    file_name_or_data.  The chooser is updated appropriately.
    """

    try:
      img = rv_image(file_name_or_data.get_detectorbase())
    except AttributeError:
      img = rv_image(os.path.abspath(file_name_or_data))

    try:
      title = file_name_or_data.full_path
    except AttributeError, e:
      title = str(file_name_or_data)
    self.SetTitle(title)

    # Update the selection in the chooser.
    i = self.add_file_name_or_data(file_name_or_data)
    self.image_chooser.SetSelection(i)

    self.pyslip.tiles.set_image(
      file_name_or_data=img, metrology_matrices=self.metrology_matrices)

    # Initialise position zoom level for first image.  XXX Why do we
    # have to coll ZoomToLevel to refresh subsequent images?
    if (self._img is None):
      self.init_pyslip_postsizer()
    else:
      self.pyslip.ZoomToLevel(self.pyslip.tiles.zoom_level)

    self._img = img # XXX

    self.settings_frame.set_image(self._img)
    self.update_statusbar() # XXX Not always working?
    self.Layout()

    detector = self.get_detector()
    beam     = self.get_beam()

    # FIXME assumes all detector elements use the same millimeter-to-pixel convention
    if detector[0].get_distance() > 0:

      def map_coords(x, y, p):
        if len(self.pyslip.tiles.raw_image.get_detector()) > 1:
          y, x = self.pyslip.tiles.flex_image.tile_readout_to_picture(
            p, y - 0.5, x - 0.5)
        return self.pyslip.tiles.picture_fast_slow_to_map_relative(
          x, y)

      if len(detector) == 24 and detector[0].get_image_size() == (2463,195):
        panel_id, (x_mm,y_mm) = detector.get_ray_intersection(beam.get_s0())
        beam_pixel_fast, beam_pixel_slow = detector[panel_id].millimeter_to_pixel(
          (x_mm, y_mm))

      elif len(detector) > 1:
        panel_id = 0
        h = detector.hierarchy()
        if len(h) > 0:
          beam_pixel_fast, beam_pixel_slow = detector[0].millimeter_to_pixel(
            detector.hierarchy().get_beam_centre(beam.get_s0()))
        else:
          beam_pixel_fast, beam_pixel_slow = detector[0].millimeter_to_pixel(
            detector[0].get_beam_centre(beam.get_s0()))
      else:
        panel_id = 0
        beam_pixel_fast, beam_pixel_slow = detector[0].millimeter_to_pixel(
          detector[0].get_beam_centre(beam.get_s0()))

      self.beam_center_cross_data = [
        ((map_coords(beam_pixel_fast + 3., beam_pixel_slow, panel_id),
          map_coords(beam_pixel_fast - 3., beam_pixel_slow, panel_id)),
         {'width': 2, 'color': '#0000FFA0', 'closed': False}),
        ((map_coords(beam_pixel_fast, beam_pixel_slow + 3., panel_id),
          map_coords(beam_pixel_fast, beam_pixel_slow - 3., panel_id)),
         {'width': 2, 'color': '#0000FFA0', 'closed': False})
                               ]

    # Unconditionally delete extra layers--update_settings() will add
    # them back if appropriate.  This also creates the self.*_layer
    # variables.
    if hasattr(self, 'beam_layer') and self.beam_layer is not None:
      self.pyslip.DeleteLayer(self.beam_layer)
    self.beam_layer = None

    if hasattr(self, 'spotfinder_layer') and self.spotfinder_layer is not None:
      self.pyslip.DeleteLayer(self.spotfinder_layer)
    self.spotfinder_layer = None

    if hasattr(self, 'tile_layer') and self.tile_layer is not None:
      self.pyslip.DeleteLayer(self.tile_layer)
    self.tile_layer = None

    if hasattr(self, 'tile_text_layer') and self.tile_text_layer is not None:
      self.pyslip.DeleteLayer(self.tile_text_layer)
    self.tile_text_layer = None

    self.update_settings()

    # Destroy the calibration frame if it present but unsupported for
    # this image.  XXX Need to do something about the ring tool too
    # when switching between different kinds of images.  XXX Centering
    # is broken when switching between different kinds of images.
    if (self._calibration_frame and
        not self.has_four_quadrants()):
      self.OnCalibration(None)

  def get_detector(self):
    return self.pyslip.tiles.raw_image.get_detector()

  def get_beam(self):
    return self.pyslip.tiles.raw_image.get_beam()

  def get_key (self, file_name_or_data) :
      """This overridden get_key() function returns the key of @p file_name_or_data
      if it's an DetectorImageBase object.  Otherwise it returns the super class's
      key
      """
      from iotbx.detectors.detectorbase import DetectorImageBase
      if isinstance(file_name_or_data, DetectorImageBase):
        return file_name_or_data.filename
      elif isinstance(file_name_or_data, chooser_wrapper):
        return str(file_name_or_data)
      else: return super(XrayFrame, self).get_key(file_name_or_data)


  def update_settings (self, layout=True) :
    # XXX The zoom level from the settings panel are not taken into
    # account here.

    new_brightness = self.settings.brightness
    new_color_scheme = self.settings.color_scheme
    if new_brightness is not self.pyslip.tiles.current_brightness or \
       new_color_scheme is not self.pyslip.tiles.current_color_scheme:
      self.pyslip.tiles.update_brightness(new_brightness,new_color_scheme)
      self.pyslip.Update()#triggers redraw

    if self.settings.show_beam_center:
      if self.beam_layer is None and hasattr(self, 'beam_center_cross_data'):
        self.beam_layer = self.pyslip.AddPolygonLayer(
          self.beam_center_cross_data, name="<beam_layer>",
          show_levels=[-2, -1, 0, 1, 2, 3, 4, 5])
    elif self.beam_layer is not None:
      self.pyslip.DeleteLayer(self.beam_layer)
      self.beam_layer = None

    if self.settings.show_spotfinder_spots:
      if self.spotfinder_layer is None:
        tdata = self.pyslip.tiles.get_spotfinder_data(self.params)
        self.spotfinder_layer = self.pyslip.AddPointLayer(
          tdata, color="green", name="<spotfinder_layer>",
          radius=2,
          renderer = self.pyslip.LightweightDrawPointLayer,
          show_levels=[-2, -1, 0, 1, 2, 3, 4, 5])
    elif self.spotfinder_layer is not None:
      self.pyslip.DeleteLayer(self.spotfinder_layer)
      self.spotfinder_layer = None

    if self.settings.show_effective_tiling:
      if self.tile_layer is None:
        tdata, ttdata = self.pyslip.tiles.get_effective_tiling_data(self.params)
        self.tile_layer = self.pyslip.AddPolygonLayer(
          tdata, name="<tiling_layer>",
          show_levels=[-2, -1, 0, 1, 2, 3, 4, 5])
      if self.tile_text_layer is None:
        self.tile_text_layer = self.pyslip.AddTextLayer(
          ttdata, name="<tiling_text_layer>",
          show_levels=[-2, -1, 0, 1, 2, 3, 4, 5],
          colour='#0000FFA0',
          textcolour='#0000FFA0',
          fontsize=30,
          placement='cc',
          radius=0)
    elif (self.tile_layer is not None) and (self.tile_text_layer is not None):
        self.pyslip.DeleteLayer(self.tile_layer)
        self.tile_layer = None
        self.pyslip.DeleteLayer(self.tile_text_layer)
        self.tile_text_layer = None

    if hasattr(self,"user_callback"):
      self.user_callback(self)

  def OnCalibration(self, event):
    from rstbx.slip_viewer.calibration_frame import SBSettingsFrame

    if not self._calibration_frame:
      self._calibration_frame = SBSettingsFrame(
        self, wx.ID_ANY, "Quadrant calibration",
        style=wx.CAPTION | wx.CLOSE_BOX)
      self._calibration_frame.Show()
      self._calibration_frame.Raise()
    else:
      self._calibration_frame.Destroy()


  def OnRing(self, event):
    from rstbx.slip_viewer.ring_frame import RingSettingsFrame

    if not self._ring_frame:
      self._ring_frame = RingSettingsFrame(
        self, wx.ID_ANY, "Ring tool",
        style=wx.CAPTION | wx.CLOSE_BOX)
      self._ring_frame.Show()
      self._ring_frame.Raise()
    else:
      self._ring_frame.Destroy()

  def OnUC(self, event):
    from rstbx.slip_viewer.uc_frame import UCSettingsFrame

    if not self._uc_frame:
      self._uc_frame = UCSettingsFrame(
        self, wx.ID_ANY, "Unit cell tool",
        style=wx.CAPTION | wx.CLOSE_BOX)
      self._uc_frame.Show()
      self._uc_frame.Raise()
    else:
      self._uc_frame.Destroy()

  def OnScore(self, event):
    from rstbx.slip_viewer.score_frame import ScoreSettingsFrame

    if not self._score_frame:
      self._score_frame = ScoreSettingsFrame(
        self, wx.ID_ANY, "Score tool",
        style=wx.CAPTION | wx.CLOSE_BOX)
      self._score_frame.Show()
      self._score_frame.Raise()
    else:
      self._score_frame.Destroy()


  def OnUpdateUICalibration(self, event):
    # If quadrant calibration is not supported for this image, disable
    # the corresponding menu item.  Toggle the menu item text
    # depending on the state of the tool.

    if self.has_four_quadrants():
      event.Enable(True)
      if self._calibration_frame:
        event.SetText("Hide quadrant calibration")
      else:
        event.SetText("Show quadrant calibration")
    else:
      event.Enable(False)
      event.SetText("Show quadrant calibration")


  def OnUpdateUINext(self, event):
    # Enable/disable the "Next" button based on the image's position
    # in the list.

    event.Enable(
      self.image_chooser.GetSelection() + 1 < self.image_chooser.GetCount())


  def OnUpdateUIPrevious(self, event):
    # Enable/disable the "Previous" button based on the image's
    # position in the list.

    event.Enable(self.image_chooser.GetSelection() >= 1)


  def OnUpdateUIRing(self, event):
    # Toggle the menu item text depending on the state of the tool.

    if self._ring_frame:
      event.SetText("Hide ring tool")
    else:
      event.SetText("Show ring tool")

  def OnUpdateUIUC(self, event):
    # Toggle the menu item text depending on the state of the tool.

    if self._uc_frame:
      event.SetText("Hide unit cell tool")
    else:
      event.SetText("Show unit cell tool")


  def OnUpdateUIScore(self, event):
    # Toggle the menu item text depending on the state of the tool.

    if self._score_frame:
      event.SetText("Hide score tool")
    else:
      event.SetText("Show score tool")


  def OnSaveAs (self, event) :
    ### XXX TODO: Save overlays
    ### XXX TODO: Fix bug where multi-asic images are slightly cropped due to tranformation error'

    import Image

    dialog = wx.FileDialog(
      self,
      defaultDir='',
      message="Save PNG or PDF file",
      style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
      wildcard="PNG file (*.png)|*.png|PDF file (*.pdf)|*.pdf")
    if dialog.ShowModal() != wx.ID_OK:
      return

    file_name = dialog.GetPath()
    if file_name == '':
      return

    self.update_statusbar("Writing " + file_name + "...")
    if dialog.GetFilterIndex() == 0:
        from cStringIO import StringIO

        # XXX Copied from tile_generation.py; all its disclaimers
        # apply.
        raw_img = self.pyslip.tiles.raw_image
        detector = raw_img.get_detector()
        if len(detector) > 1:
          from tile_generation import _get_flex_image_multipanel
          flex_img = _get_flex_image_multipanel(
            brightness=self.settings.brightness / 100,
            panels=detector,
            raw_data=[raw_img.get_raw_data(i)
                      for i in range(len(detector))])
        else:
          from tile_generation import _get_flex_image
          flex_img = _get_flex_image(
            brightness=self.settings.brightness / 100,
            data=raw_img.get_raw_data(),
            saturation=detector[0].get_trusted_range()[1],
            vendortype=raw_img.__class__.__name__)

        if flex_img.supports_rotated_tiles_antialiasing_recommended:
            currentZoom = self.pyslip.level
            self.pyslip.tiles.UseLevel(0) #1:1 zoom level

            x, y, width, height = self._img._raw.bounding_box_mm()
            x1, y1 = self._img._raw.detector_coords_as_image_coords(x,y)
            x2, y2 = self._img._raw.detector_coords_as_image_coords(x+width,y+height)

            # Map > View - determine layout in X direction
            x_offset = x1
            import math
            start_x_tile = int(math.floor(x_offset / self.pyslip.tile_size_x))
            stop_x_tile = ((x2 + self.pyslip.tile_size_x - 1)/ self.pyslip.tile_size_x)
            stop_x_tile = int(stop_x_tile)
            col_list = range(start_x_tile, stop_x_tile)
            x_pix = start_x_tile * self.pyslip.tile_size_y - x_offset

            y_offset = y1
            start_y_tile = int(math.floor(y_offset / self.pyslip.tile_size_y))
            stop_y_tile = ((y2 + self.pyslip.tile_size_y - 1) / self.pyslip.tile_size_y)
            stop_y_tile = int(stop_y_tile)
            row_list = range(start_y_tile, stop_y_tile)
            y_pix_start = start_y_tile * self.pyslip.tile_size_y - y_offset

            bitmap = wx.EmptyBitmap(x2-x1, y2-y1)
            dc = wx.MemoryDC()
            dc.SelectObject(bitmap)

            # start pasting tiles
            for x in col_list:
                y_pix = y_pix_start
                for y in row_list:
                    dc.DrawBitmap(self.pyslip.tiles.GetTile(x, y), x_pix, y_pix, False)
                    y_pix += self.pyslip.tile_size_y
                x_pix += self.pyslip.tile_size_x

            dc.SelectObject(wx.NullBitmap)

            wximg = wx.ImageFromBitmap(bitmap)
            imageout = Image.new('RGB', (wximg.GetWidth(), wximg.GetHeight()))
            imageout.fromstring(wximg.GetData())

            self.pyslip.tiles.UseLevel(currentZoom)

        else: # write the image out at full resolution
            flex_img.setWindow(0.0, 0.0, 1)
            flex_img.spot_convention(0)
            flex_img.adjust(color_scheme=self.settings.color_scheme)
            flex_img.prep_string()
            data_string = flex_img.export_string
            imageout = Image.fromstring("RGB",
                                     (flex_img.ex_size2(), flex_img.ex_size1()),
                                     data_string)

        out = StringIO()
        imageout.save(out, "PNG")
        open(file_name, "wb").write(out.getvalue())

    elif dialog.GetFilterIndex() == 1:
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas

        # Dots per inch in PDF output, and fudge factor to not make
        # fine features impossibly small.  XXX The fudge factor should
        # go.
        DPI = 72
        LINE_WIDTH_FACTOR = 0.6

        flex_img = self.pyslip.tiles.raw_image.get_flex_image(
          brightness=self.settings.brightness / 100)

        flex_img.setWindow(0, 0, 1)
        flex_img.adjust(color_scheme=self.settings.color_scheme)
        flex_img.prep_string()

        # XXX Order of size1/size2 correct?
        pdf_size = (flex_img.size2() * inch / DPI,
                    flex_img.size1() * inch / DPI)
        pdf_canvas = canvas.Canvas(filename=file_name, pagesize=pdf_size)
        pil_img = Image.fromstring(
          'RGB', (flex_img.size2(), flex_img.size1()), flex_img.export_string)

        pdf_canvas.drawInlineImage(
          pil_img, 0, 0, width=pdf_size[0], height=pdf_size[1])

        for layer_id in self.pyslip.layer_z_order:
          layer = self.pyslip.layer_mapping[layer_id]

          # XXX This would probably be more elegant if these were
          # functions in some layer class.  Note repeated roundabout
          # way (via a wx.Pen object) to extract RGB values from the
          # colour parameter.
          if layer.type == self.pyslip.TypeEllipse:
            from math import atan2, degrees, hypot
            from scitbx.matrix import col

            for (p, place, width, colour, closed, filled, fillcolour,
                 x_off, y_off, pdata) in layer.data:
              if layer.map_rel:
                pp = []
                for i in range(len(p)):
                  fs = self.pyslip.tiles.map_relative_to_picture_fast_slow(
                    p[i][0], p[i][1])
                  pp.append((fs[0] * inch / DPI,
                             pdf_size[1] - fs[1] * inch / DPI))
                ellipse_center = col(pp[0])
                major = col(pp[1]) - ellipse_center
                minor = col(pp[2]) - ellipse_center
              else:
                raise NotImplementedError(
                  "PDF output in view-relative coordinates not implemented")

              pen = wx.Pen(colour)
              pdf_canvas.setLineWidth(width * LINE_WIDTH_FACTOR)
              pdf_canvas.setStrokeColorRGB(pen.Colour.Red() / 255,
                                           pen.Colour.Green() / 255,
                                           pen.Colour.Blue() / 255)

              angle = atan2(major.elems[1], major.elems[0])
              r_major = hypot(major.elems[0], major.elems[1])
              r_minor = hypot(minor.elems[0], minor.elems[1])

              pdf_canvas.saveState()
              pdf_canvas.translate(
                ellipse_center.elems[0], ellipse_center.elems[1])

              pdf_canvas.rotate(degrees(angle))
              pdf_canvas.ellipse(-r_major, -r_minor, r_major, r_minor)
              pdf_canvas.restoreState()

          elif layer.type == self.pyslip.TypeImage:
            raise NotImplementedError(
              "PDF output of image layers not implemented")

          elif layer.type == self.pyslip.TypePoint:
            for (lon, lat, place, radius, colour,
                 x_off, y_off, pdata) in layer.data:
              if layer.map_rel:
                fs = self.pyslip.tiles.map_relative_to_picture_fast_slow(
                  lon, lat)
              else:
                raise NotImplementedError(
                  "PDF output in view-relative coordinates not implemented")

              pt = (fs[0] * inch / DPI, pdf_size[1] - fs[1] * inch / DPI)
              pen = wx.Pen(colour)
              pdf_canvas.setLineWidth(radius)
              pdf_canvas.setStrokeColorRGB(pen.Colour.Red() / 255,
                                           pen.Colour.Green() / 255,
                                           pen.Colour.Blue() / 255)
              pdf_canvas.circle(pt[0], pt[1], 0.5 * radius * inch / DPI)

          elif layer.type == self.pyslip.TypePolygon:
            for (p, place, width, colour, closed, filled, fillcolour,
                 x_off, y_off, pdata) in layer.data:
              path = pdf_canvas.beginPath()
              for i in range(len(p)):
                if layer.map_rel:
                  fs = self.pyslip.tiles.map_relative_to_picture_fast_slow(
                    p[i][0], p[i][1])
                else:
                  raise NotImplementedError(
                    "PDF output in view-relative coordinates not implemented")

                pt = (fs[0] * inch / DPI, pdf_size[1] - fs[1] * inch / DPI)
                if i == 0:
                  path.moveTo(pt[0], pt[1])
                else:
                  path.lineTo(pt[0], pt[1])

              if closed:
                path.close()

              pen = wx.Pen(colour)
              pdf_canvas.setFillColorRGB(pen.Colour.Red() / 255,
                                         pen.Colour.Green() / 255,
                                         pen.Colour.Blue() / 255)
              pdf_canvas.setLineWidth(width * LINE_WIDTH_FACTOR)
              pdf_canvas.setStrokeColorRGB(pen.Colour.Red() / 255,
                                           pen.Colour.Green() / 255,
                                           pen.Colour.Blue() / 255)
              pdf_canvas.drawPath(path, fill=filled)

          elif layer.type == self.pyslip.TypeText:
            raise NotImplementedError(
              "PDF output of text layers not yet implemented")

        pdf_canvas.save()

    self.update_statusbar("Writing " + file_name + "..." + " Done.")


from rstbx.viewer.frame import SettingsFrame

def override_SF_set_image(self,image):
  self.Layout()
  self.Fit()
SettingsFrame.set_image = override_SF_set_image
