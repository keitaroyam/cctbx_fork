
"""
Embedded browser windows with a minimal frame.  This will use the native web
browser library on Mac (WebKit) and Windows (IE); on Linux it will default to
the simpler wx.html.HtmlWindow.  This is used in the Phenix GUI to display
documentation.
"""

from __future__ import division
import wxtbx.bitmaps
import wx.html
import wx

class browser_frame (wx.Frame) :
  def __init__ (self, *args, **kwds) :
    wx.Frame.__init__(self, *args, **kwds)
    szr = wx.BoxSizer(wx.VERTICAL)
    self.SetSizer(szr)
    self._was_shown = False
    self._is_default_viewer = False
    self.viewer = None
    _import_error = None
    if (wx.Platform == '__WXMAC__') :
      try :
        from wx import webkit
      except ImportError, e :
        _import_error = str(e)
      else :
        self.viewer = webkit.WebKitCtrl(self, -1)
        self.Bind(webkit.EVT_WEBKIT_STATE_CHANGED, self.OnChangeState,
          self.viewer)
        self.Bind(webkit.EVT_WEBKIT_BEFORE_LOAD, self.OnBeforeLoad, self.viewer)
    elif (wx.Platform == '__WXMSW__') :
      try :
        from wx.lib import iewin
      except ImportError, e :
        _import_error = str(e)
      else :
        self.viewer = iewin.IEHtmlWindow(self, -1)
    if (self.viewer is None) : # fallback (default on Linux)
      self.viewer = HtmlPanel(self)
      self._is_default_viewer = True
    szr.Add(self.viewer, 1, wx.EXPAND)
    self.SetupToolbar()
    self.statusbar = self.CreateStatusBar()
    if (wx.Platform != "__WXMSW__") :
      self.SetInitialSize((1024,640))
    #self.Bind(wx.EVT_WINDOW_CREATE, self.OnShow)

  def SetHomepage (self, url) :
    self.home_url = url

  def SetupToolbar (self) :
    if (wxtbx.bitmaps.icon_lib is None) :
      return
    self.toolbar = self.CreateToolBar(style=wx.TB_3DBUTTONS|wx.TB_TEXT)
    commands = [
      ("filesystems", "folder_home", "OnHome", "Home"),
      ("actions", "back", "OnBack", "Back"),
      ("actions", "forward", "OnForward", "Forward"),
      ("actions", "stop", "OnStop", "Stop"),
    ]
    if (not self._is_default_viewer) :
      commands.append(("actions", "reload", "OnReload", "Reload"))
    for (icon_class, icon_name, fname, label) in commands :
      bmp = wxtbx.bitmaps.fetch_icon_bitmap(icon_class, icon_name, 32)
      tool_button = self.toolbar.AddLabelTool(-1, label, bmp,
        shortHelp=label, kind=wx.ITEM_NORMAL)
      self.Bind(wx.EVT_MENU, getattr(self, fname), tool_button)
    self.toolbar.AddSeparator()
    if (not self._is_default_viewer) :
      phenix_bmp = wxtbx.bitmaps.fetch_custom_icon_bitmap("phenix.refine")
      phenix_btn = self.toolbar.AddLabelTool(-1, "PHENIX homepage", phenix_bmp,
        shortHelp="PHENIX homepage", kind=wx.ITEM_NORMAL)
      self.Bind(wx.EVT_MENU, self.OnPhenixWeb, phenix_btn)
    self.toolbar.Realize()

  def LoadURL (self, url) :
    if (wx.Platform == '__WXMSW__') :
      self.viewer.LoadUrl(url)
    else :
      self.viewer.LoadURL(url)

  def OnShow (self, event) :
    if (not self._was_shown) :
      self.LoadURL(self.home_url)
      self._was_shown = True

  def OnHome (self, event) :
    self.LoadURL(self.home_url)

  def OnBack (self, event) :
    if self.viewer.CanGoBack() :
      self.viewer.GoBack()

  def OnForward (self, event) :
    if self.viewer.CanGoForward() :
      self.viewer.GoForward()

  def OnReload (self, event) :
    if (wx.Platform == '__WXMAC__') :
      self.viewer.Reload()
    elif (wx.Platform == '__WXMSW__') :
      self.viewer.RefreshPage()

  def OnStop (self, event) :
    self.viewer.Stop()

  def Open (self, url) :
    self.LoadURL(url)

  def OnPhenixWeb (self, event) :
    self.LoadURL("http://www.phenix-online.org")

  # XXX Mac only
  def OnChangeState (self, event) :
    import wx.webkit
    state = event.GetState()
    url = event.GetURL()
    if (state == wx.webkit.WEBKIT_STATE_START) :
      self.statusbar.SetStatusText("Opening %s" % url)
    elif (state == wx.webkit.WEBKIT_STATE_TRANSFERRING) :
      self.statusbar.SetStatusText("Loading %s" % url)
    elif (state == wx.webkit.WEBKIT_STATE_STOP) :
      self.statusbar.SetStatusText("Viewing %s" % url)
    elif (state == wx.webkit.WEBKIT_STATE_FAILED) :
      self.statusbar.SetStatusText("Failed loading %s" % url)
    else :
      self.statusbar.SetStatusText("")

  def OnBeforeLoad (self, event) :
    pass
    #print event.GetNavigationType()

class HtmlPanel (wx.html.HtmlWindow) :
  """
  Adapter class to provide an API equivalent to WebKit/IE
  """
  def Stop (self) :
    pass

  def CanGoForward (self) :
    return self.HistoryCanForward()

  def GoForward (self) :
    return self.HistoryForward()

  def CanGoBack (self) :
    return self.HistoryCanBack()

  def GoBack (self) :
    return self.HistoryBack()

  def LoadURL (self, url) :
    return self.LoadPage(url)

if __name__ == "__main__" :
  app = wx.App(0)
  frame = browser_frame(None, -1, "wxtbx.browser example")
  #  size=(800,600))
  frame.SetHomepage("http://cci.lbl.gov")
  frame.Show()
  app.MainLoop()
