from cctbx import crystal
symmetry = crystal.symmetry(
  unit_cell=(11, 12, 13, 90, 100, 90),
  space_group_symbol="C 2")
symmetry.show_summary()
for s in symmetry.space_group(): print s
