# $Id$

import sys
import random
import string

TidyCBOp = "--TidyCBOp" in sys.argv
QuickMode = "--Quick" in sys.argv
ShortCut = "--ShortCut" in sys.argv

import sgtbx

RBFerr = "out of rotation-base-factor range"
TBFerr = "out of translation-base-factor range"

if (ShortCut):
  table_hall = (" P 2c 2",)
else:
  table_hall = []
  for i in sgtbx.SpaceGroupSymbolIterator():
    table_hall.append(i.Hall())

def random_expand(SgOps):
  s = sgtbx.SgOps()
  OrderZ = SgOps.OrderZ()
  l = range(OrderZ)
  while (len(l)):
    i = random.randrange(len(l))
    s.expandSMx(SgOps[l[i]])
    if (s.OrderZ() == OrderZ): return s
    del l[i]
  raise RuntimeError, "random_expand"

for HallSymbol in table_hall:
  for Z in "PABCIRHF":
    HSym = HallSymbol[0] + Z + HallSymbol[2:]
    SgOps = sgtbx.SgOps(HSym)
    SgNumber = SgOps.getSpaceGroupType().SgNumber()
    RefSgOps = sgtbx.SgOps(sgtbx.SpaceGroupSymbols(SgNumber).Hall())
    if (SgNumber < 75):
      RotOps = sgtbx.SgOps('P 1')
    else:
      RotOps = sgtbx.SgOps('P 3*')
    for Rot in RotOps:
      CBOp = sgtbx.ChOfBasisOp(Rot)
      SgOpsRot = SgOps.ChangeBasis(CBOp)
      print HSym, CBOp.M().as_xyz()
      s = SgOpsRot.ChangeBasis(CBOp)
      s = random_expand(s)
      print s.OrderZ()
      try:
        t = s.getSpaceGroupType(TidyCBOp)
      except RuntimeError, e:
        e = str(e)
        if (string.find(e, RBFerr) >= 0 or string.find(e, TBFerr) >= 0):
          print e
        else:
          raise
      else:
        print "Space group number:", t.SgNumber()
        print "CBMx:", t.CBOp().M().as_xyz()
        print "InvCBMx:", t.CBOp().InvM().as_xyz()
        assert t.SgNumber() == SgNumber
        if (not QuickMode):
          assert s.ChangeBasis(t.CBOp()) == RefSgOps
          assert s == RefSgOps.ChangeBasis(t.CBOp().swap())
        try:
          l = s.BuildLookupSymbol()
        except RuntimeError, e:
          e = str(e)
          if (string.find(e, RBFerr) >= 0 or string.find(e, TBFerr) >= 0):
            print e
          else:
            raise
        else:
          print "LookupSymbol:", l
          if (not QuickMode):
            assert s == sgtbx.SgOps(sgtbx.SpaceGroupSymbols(l).Hall())
      print
