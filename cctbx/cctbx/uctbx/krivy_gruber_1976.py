from cctbx.uctbx.reduction_base import iteration_limit_exceeded
from cctbx.uctbx.reduction_base import reduction_base
from cctbx.uctbx.reduction_base import minimal_reduction_mixin

class reduction(reduction_base):

  def __init__(self, unit_cell, relative_epsilon=None, iteration_limit=None):
    reduction_base.__init__(self, unit_cell, relative_epsilon, iteration_limit)
    while (self.step()): pass

  def _name(self):
    return "Krivy-Gruber"

  def step(s):
    eq = s.eps_eq
    lt = s.eps_lt
    gt = s.eps_gt
    # A1
    if (gt(s.a, s.b) or (eq(s.a, s.b) and gt(abs(s.d), abs(s.e)))):
      s.a1_action()
    # A2
    if (gt(s.b, s.c) or (eq(s.b, s.c) and gt(abs(s.e), abs(s.f)))):
      s.a2_action()
      return 0001
    # A3
    if (s.def_gt_0()):
      s.a3_action()
    # A4
    else:
      s.a4_action()
    # A5
    if (gt(abs(s.d), s.b)
        or (eq(s.d, s.b) and lt(s.e+s.e, s.f))
        or (eq(s.d, -s.b) and lt(s.f, 0))):
      s.a5_action()
      return 0001
    # A6
    if (gt(abs(s.e), s.a)
        or (eq(s.e, s.a) and lt(s.d+s.d, s.f))
        or (eq(s.e, -s.a) and lt(s.f, 0))):
      s.a6_action()
      return 0001
    # A7
    if (gt(abs(s.f), s.a)
        or (eq(s.f, s.a) and lt(s.d+s.d, s.e))
        or (eq(s.f, -s.a) and lt(s.e, 0))):
      s.a7_action()
      return 0001
    # A8
    if (lt(s.d+s.e+s.f+s.a+s.b, 0)
        or (eq(s.d+s.e+s.f+s.a+s.b, 0) and gt(s.a+s.a+s.e+s.e+s.f, 0))):
      s.a8_action()
      return 0001
    return 00000

  def a1_action(s):
    s.n1_action()

  def a2_action(s):
    s.n2_action()

  def a3_action(s):
    s.n3_true_action()

  def a4_action(s):
    s.n3_false_action()

  def a5_action(s):
    if (s.d > 0):
      s.c += s.b - s.d
      s.d -= s.b + s.b
      s.e -= s.f
      s.cb_update((1,0,0,0,1,-1,0,0,1))
    else:
      s.c += s.b + s.d
      s.d += s.b + s.b
      s.e += s.f
      s.cb_update((1,0,0,0,1,1,0,0,1))
    assert s.c > 0

  def a6_action(s):
    if (s.e > 0):
      s.c += s.a - s.e
      s.d -= s.f
      s.e -= s.a + s.a
      s.cb_update((1,0,-1,0,1,0,0,0,1))
    else:
      s.c += s.a + s.e
      s.d += s.f
      s.e += s.a + s.a
      s.cb_update((1,0,1,0,1,0,0,0,1))
    assert s.c > 0

  def a7_action(s):
    if (s.f > 0):
      s.b += s.a - s.f
      s.d -= s.e
      s.f -= s.a + s.a
      s.cb_update((1,-1,0,0,1,0,0,0,1))
    else:
      s.b += s.a + s.f
      s.d += s.e
      s.f += s.a + s.a
      s.cb_update((1,1,0,0,1,0,0,0,1))
    assert s.b > 0

  def a8_action(s):
    s.cb_update((1,0,1,0,1,1,0,0,1))
    s.c += s.a+s.b+s.d+s.e+s.f
    s.d += s.b+s.b+s.f
    s.e += s.a+s.a+s.f
    assert s.c > 0

class minimal_reduction(minimal_reduction_mixin, reduction):

  def __init__(self, unit_cell, expected_cycle_limit=None,
                                iteration_limit=None):
    minimal_reduction_mixin.__init__(self,
      unit_cell, expected_cycle_limit, iteration_limit)

  def a4_action(self):
    self.current_cycle_id = 1
    reduction.a4_action(self)

  def a8_action(self):
    self.current_cycle_id = 2
    reduction.a8_action(self)
