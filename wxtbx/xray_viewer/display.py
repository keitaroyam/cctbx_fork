
import wx

class XrayView (wx.Panel) :
  def __init__ (self, *args, **kwds) :
    self._img = None
    super(XrayView, self).__init__(*args, **kwds)
    self.settings = self.GetParent().settings
    self.Bind(wx.EVT_PAINT, self.OnPaint)
    self.SetupEventHandlers()
    self.xmouse = None
    self.ymouse = None
    self.line_start = None
    self.line_end = None
    self.was_dragged = False
    self._last_zoom = 0

  def SetupEventHandlers (self) :
    self.Bind(wx.EVT_SIZE, self.OnSize)
    self.Bind(wx.EVT_MOTION, self.OnMotion)
    self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
    self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
    self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
    self.Bind(wx.EVT_MIDDLE_DOWN, self.OnMiddleDown)
    self.Bind(wx.EVT_MIDDLE_UP, self.OnMiddleUp)
    self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
    self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
    self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
    self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)

  def set_image (self, image) :
    self._img = image
    self._img.set_screen_size(*(self.GetSize()))
    self.update_settings()

  def update_settings (self, layout=True) :
    self.line = None
    scales = [0, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0]
    zoom = scales[self.settings.zoom_level]
    self._img.set_zoom(zoom)
    self._img.update_settings(
      brightness=self.settings.brightness)
    if (layout) :
      self.line_start = None
      self.line_end = None
      self.OnSize(None)
    self.Refresh()
    if (self.GetParent().zoom_frame is not None) :
      self.GetParent().zoom_frame.Refresh()
    self.GetParent().settings_frame.refresh_thumbnail()

  # EVENTS
  def OnPaint (self, event) :
    dc = wx.AutoBufferedPaintDCFactory(self)
    w, h = self.GetSize()
    bitmap = self._img.get_bitmap()
    x, y = self._img.adjust_screen_coordinates(0, 0)
    dc.DrawBitmap(bitmap, x, y)
    if (self.settings.show_beam_center) :
      center_x, center_y = self._img.get_beam_center()
      xc, yc = self._img.image_coords_as_screen_coords(center_x, center_y)
      if (xc < w) and (yc < h) :
        dc.SetPen(wx.Pen('red'))
        dc.DrawLine(xc - 10, yc, xc + 10, yc)
        dc.DrawLine(xc, yc - 10, xc, yc + 10)
    if (self.line_start is not None) and (self.line_end is not None) :
      dc.SetPen(wx.Pen('red', 2, wx.DOT))
      x1, y1 = self._img.image_coords_as_screen_coords(*(self.line_start))
      x2, y2 = self._img.image_coords_as_screen_coords(*(self.line_end))
      dc.DrawLine(x1, y1, x2, y2)

  def OnSize (self, event) :
    if (self._img is not None) :
      w, h = self.GetSize()
      self._img.set_screen_size(w, h)

  def OnRecordMouse (self, event) :
    self.xmouse = event.GetX()
    self.ymouse = event.GetY()

  def OnMotion (self, event) :
    if (event.Dragging()) :
      self.was_dragged = True
      if (event.LeftIsDown()) :
        self.OnLeftDrag(event)
      elif (event.MiddleIsDown()) :
        self.OnMiddleDrag(event)
      elif (event.RightIsDown()) :
        self.OnRightDrag(event)
    else :
      x, y = self._img.screen_coords_as_image_coords(event.GetX(),event.GetY())
      img_w, img_h = self._img.get_image_size()
      if (x < 0) or (x > img_w) or (y < 0) or (y > img_h) :
        self.GetParent().update_statusbar()
      else :
        info = self._img.get_point_info(x, y)
        self.GetParent().update_statusbar(info)

  def OnMiddleDown (self, event) :
    self.was_dragged = False
    self.OnRecordMouse(event)
    wx.SetCursor(wx.StockCursor(wx.CURSOR_HAND))

  def OnMiddleUp (self, event) :
    wx.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))

  def OnLeftDown (self, event) :
    self.was_dragged = False
    self.line_end = None
    x, y = event.GetPositionTuple()
    self.line_start = self._img.screen_coords_as_image_coords(x, y)
    #self.OnRecordMouse(event)

  def OnDoubleClick (self, event) :
    pass

  def OnLeftDrag (self, event) :
    x, y = event.GetPositionTuple()
    self.line_end = self._img.screen_coords_as_image_coords(x, y)
    self.Refresh()

  def OnLeftUp (self, event) :
    if (self.was_dragged) and (self.line_start is not None) :
      x, y = event.GetPositionTuple()
      self.line_end = self._img.screen_coords_as_image_coords(x, y)
      x1, y1 = self.line_start
      x2, y2 = self.line_end
      if (x1 <= x2) :
        line = self._img.line_between_points(x1, y1, x2, y2)
      else :
        line = self._img.line_between_points(x2, y2, x1, y1)
      self.GetParent().OnShowPlot(None)
      self.GetParent().plot_frame.show_plot(line)
    else :
      self.line = None
    self.Refresh()
    self.was_dragged = False

  def OnMiddleDrag (self, event) :
    self.OnTranslate(event)

  def OnRightDown (self, event) :
    self.was_dragged = False
    self.OnZoom(event)

  def OnRightDrag (self, event) :
    self.OnZoom(event)

  def OnZoom (self, event) :
    x, y = event.GetPositionTuple()
    img_x, img_y = self._img.screen_coords_as_image_coords(x, y)
    self.GetParent().OnShowZoom(None)
    self.GetParent().zoom_frame.set_zoom(img_x, img_y)

  def OnTranslate (self, event) :
    x, y = event.GetX(), event.GetY()
    delta_x = x - self.xmouse
    delta_y = y - self.ymouse
    self.OnRecordMouse(event)
    self.TranslateImage(delta_x, delta_y)

  def TranslateImage (self, delta_x, delta_y) :
    if (self.settings.zoom_level == 0) :
      return
    self._img.translate_image(delta_x, delta_y)
    self.Refresh()
    self.GetParent().settings_frame.refresh_thumbnail()

  def OnMouseWheel (self, event) :
    d_x = d_y = 0
    if (event.ShiftDown()) :
      d_x = - 10 * event.GetWheelRotation()
    else :
      d_y = - 10 * event.GetWheelRotation()
    self.TranslateImage(d_x, d_y)

  def OnEnter (self, event) :
    if (not event.MiddleIsDown()) and (not event.RightIsDown()) :
      wx.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))

  def OnLeave (self, event) :
    self.was_dragged = False
    wx.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

class ThumbnailView (XrayView) :
  def __init__ (self, *args, **kwds) :
    XrayView.__init__(self, *args, **kwds)

  def SetupEventHandlers (self) :
    self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)

  def set_image (self, image) :
    self._img = image
    self.SetSize(tuple(image.get_thumbnail_size()))
    self.GetParent().Layout()

  def OnPaint (self, event) :
    dc = wx.AutoBufferedPaintDCFactory(self)
    bitmap = self._img.get_thumbnail_bitmap()
    dc.SetBrush(wx.TRANSPARENT_BRUSH)
    dc.DrawBitmap(bitmap, 0, 0)
    x, y, w, h = self._img.get_thumbnail_box()
    dc.SetPen(wx.Pen('red', 2))
    dc.DrawRectangle(x, y, w-3, h-3)

  def OnLeftDown (self, event) :
    x, y = event.GetPositionTuple()
    self._img.center_view_from_thumbnail(x, y)
    self.Refresh()
    self.GetParent().refresh_main()
