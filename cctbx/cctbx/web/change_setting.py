# It is common that a certain crystal structure is published in the
# literature in two or more different settings of the same space group. A
# typical example is that of a rhombohedral space group (e.g. R 3) where
# either a hexagonal basis system or a rhombohedral basis system is used.
# Other examples are space groups with two origin choices (e.g. P n n n),
# or orthorhombic space groups where the basis vectors are permuted (e.g.
# P 2 2 21, P 2 21 2, P 21 2 2). Unusual settings can also arise from
# group-subgroup or relations (e.g. the monoclinic subgroup of space
# group P 3 1 2 which is generated by the two-fold axis parallel [-1,1,0]).
# This script can be used to determine the change-of-basis matrix
# between two settings of the same space group. Optionally, this
# change-of-basis matrix is used to transform unit cell parameters and
# atomic coordinates.

from cctbx import sgtbx
from cctbx import uctbx
from cctbx.web import utils

class empty: pass

def interpret_form_data(form):
  inp = empty()
  for key in (("ucparams_old", "1 1 1 90 90 90"),
              ("sgsymbol_old", "P1"),
              ("convention_old", ""),
              ("sgsymbol_new", ""),
              ("convention_new", ""),
              ("coor_type", None),
              ("skip_columns", "0")):
    if (form.has_key(key[0])):
      inp.__dict__[key[0]] = form[key[0]].value.strip()
    else:
      inp.__dict__[key[0]] = key[1]
  inp.coordinates = []
  if (form.has_key("coordinates")):
    lines = form["coordinates"].value.split("\015\012")
    for l in lines:
      s = l.strip()
      if (len(s) != 0): inp.coordinates.append(s)
  return inp

def run(server_info, inp, status):
  print "<pre>"

  unit_cell_old = uctbx.unit_cell(inp.ucparams_old)
  print "Old symmetry:"
  print " ",
  uctbx.show_parameters(unit_cell_old)
  space_group_info_old = sgtbx.space_group_info(
    symbol=inp.sgsymbol_old,
    table_id=inp.convention_old)
  print " ",
  space_group_info_old.show_summary()
  print

  if (len(inp.sgsymbol_new.strip()) == 0):
    space_group_info_new = space_group_info_old.reference_setting()
    inp.convention_new = ""
  else:
    space_group_info_new = sgtbx.space_group_info(
      symbol=inp.sgsymbol_new,
      table_id=inp.convention_new)
  print "New space group symbol:"
  print " ",
  space_group_info_new.show_summary()
  print

  if (   space_group_info_new.type().number()
      != space_group_info_old.type().number()):
    print "Space group numbers are not equal!"
  else:
    c = space_group_info_new.type().cb_op().c_inv().multiply(
        space_group_info_old.type().cb_op().c()).new_denominators(
          sgtbx.cb_r_den, sgtbx.cb_t_den)
    cb_op = sgtbx.change_of_basis_op(c)
    print "Change-of-basis matrix:", cb_op.c()
    print "               Inverse:", cb_op.c_inv()
    print

    assert space_group_info_old.group().is_compatible_unit_cell(unit_cell_old)
    unit_cell_new = cb_op.apply(unit_cell_old)
    print "New unit cell parameters:"
    print " ",
    uctbx.show_parameters(unit_cell_new)
    assert space_group_info_new.group().is_compatible_unit_cell(unit_cell_new)
    print

    print inp.coor_type, "coordinates:"
    print

    skip_columns = utils.interpret_skip_columns(inp.skip_columns)

    for line in inp.coordinates:
      skipped, coordinates = utils.interpret_coordinate_line(line,skip_columns)
      if (inp.coor_type != "Fractional"):
        coordinates = unit_cell_old.fractionalize(coordinates)
      new_coordinates = cb_op(coordinates)
      if (inp.coor_type != "Fractional"):
        new_coordinates = unit_cell_new.orthogonalize(new_coordinates)
      print skipped, "%.6g %.6g %.6g" % tuple(new_coordinates)

  print "</pre>"
