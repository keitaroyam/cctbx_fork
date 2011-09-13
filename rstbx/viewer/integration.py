
from rstbx.viewer import results_base
from rstbx.viewer.results_base import ResultData, BinData
from libtbx.utils import Sorry
import wx
import os
import sys

class ListBase (wx.ListCtrl) :
  def RefreshAllItems (self) :
    n_items = self.dataSource.GetItemCount()
    self.SetItemCount(n_items)
    if (n_items > 0) :
      self.RefreshItems(0, n_items - 1)

  def OnGetItemImage (self, item) :
    return self.dataSource.GetItemImage(item)

  def OnGetItemAttr (self, item) :
    pass

  def OnGetItemText (self, item, col) :
    return self.dataSource.GetItemText(item, col)

class IntegrationTable (ListBase) :
  def __init__ (self, *args, **kwds) :
    kwds = dict(kwds)
    kwds['style'] = wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_SINGLE_SEL
    kwds['size'] = (720,200)
    ListBase.__init__(self, *args, **kwds)
    labels = ["#","Point group","Beam center","Distance","Resolution",
      "Mosaicity","RMS"]
    widths = [60,120,120,100,100,80,80]
    for i, label in enumerate(labels) :
      self.InsertColumn(i, label, wx.LIST_FORMAT_RIGHT)
      self.SetColumnWidth(i, widths[i])
    self.SetResults([])

  def SetResults (self, results) :
    self.dataSource = ResultData(results)
    self.RefreshAllItems()

class ResolutionBinTable (ListBase) :
  def __init__ (self, *args, **kwds) :
    kwds = dict(kwds)
    kwds['style'] = wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_SINGLE_SEL
    kwds['size'] = (600,240)
    ListBase.__init__(self, *args, **kwds)
    labels = ["Bin","Resolution","Completeness", "<I>", "<I/sig(I)>"]
    widths = [60,180,140,100,100]
    for i, label in enumerate(labels) :
      self.InsertColumn(i, label, wx.LIST_FORMAT_RIGHT)
      self.SetColumnWidth(i, widths[i])
    self.SetBins([])

  def SetBins (self, table) :
    self.dataSource = BinData(table)
    self.RefreshAllItems()

class ResultsFrame (wx.Frame) :
  def __init__ (self, *args, **kwds) :
    kwds['style'] = wx.DEFAULT_FRAME_STYLE
    wx.Frame.__init__(self, *args, **kwds)
    szr = wx.BoxSizer(wx.VERTICAL)
    self.SetSizer(szr)
    p = wx.Panel(self)
    szr.Add(p, 1, wx.EXPAND|wx.ALL)
    pszr = wx.BoxSizer(wx.VERTICAL)
    p.SetSizer(pszr)
    txt1 = wx.StaticText(p, -1, "Integration results:")
    f1 = txt1.GetFont()
    f1.SetWeight(wx.FONTWEIGHT_BOLD)
    txt1.SetFont(f1)
    pszr.Add(txt1, 0, wx.ALL, 5)
    self.integration_list = IntegrationTable(p)
    pszr.Add(self.integration_list, 0, wx.ALL, 5)
    box = wx.BoxSizer(wx.HORIZONTAL)
    pszr.Add(box)
    btn = wx.Button(p, -1, "View results")
    self.view_btn = btn
    box.Add(btn, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
    txt2 = wx.StaticText(p, -1, "Integration output by resolution:")
    txt2.SetFont(f1)
    pszr.Add(txt2, 0, wx.ALL, 5)
    self.bin_list = ResolutionBinTable(p)
    pszr.Add(self.bin_list, 0, wx.ALL, 5)
    szr.Fit(p)
    self.Fit()
    self._results = []
    self._summaries = []
    self.Bind(wx.EVT_BUTTON, self.OnView, btn)
    self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelect, self.integration_list)
    self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnDeSelect,
      self.integration_list)

  def SetResults (self, results, summaries) :
    assert (len(results) > 0)
    self._results = results
    self._summaries = summaries
    self.integration_list.SetResults(summaries)
    self.integration_list.Select(0)
    #self.view_btn.Enable(True)

  def OnView (self, evt) :
    sol = self.integration_list.GetFirstSelected()
    print sol

  def OnSelect (self, evt) :
    sol = self.integration_list.GetFirstSelected()
    if (sol >= 0) :
      self.view_btn.Enable(True)
      self.bin_list.SetBins(self._summaries[sol]['bins'])

  def OnDeSelect (self, evt) :
    sol = self.integration_list.GetFirstSelected()
    if (sol < 0) :
      self.view_btn.Enable(False)

def load_results () :
  file_base = sys.argv[1]
  results, summaries = results_base.load_integration_results(os.getcwd(),
    file_base)
  if (len(results) == 0) :
    raise Sorry("No files matching %s!" % file_base)
  app = wx.App(0)
  frame = ResultsFrame(None, -1, "Integration results")
  frame.SetResults(results, summaries)
  frame.Show()
  app.MainLoop()

if (__name__ == "__main__") :
  load_results()
