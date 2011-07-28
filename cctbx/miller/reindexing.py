import libtbx

class assistant(libtbx.slots_getstate_setstate):

  __slots__ = [
    "lattice_group",
    "intensity_group",
    "miller_indices",
    "cb_ops",
    "perms",
    "inv_perms",
    "i_j_multiplication_table",
    "i_j_inv_multiplication_table"]

  def __init__(O, lattice_group, intensity_group, miller_indices):
    O.lattice_group = lattice_group
    O.intensity_group = intensity_group
    O.miller_indices = miller_indices
    import cctbx.miller
    import cctbx.sgtbx.cosets
    cosets = cctbx.sgtbx.cosets.left_decomposition_point_groups_only(
      g=lattice_group,
      h=intensity_group)
    reps = cosets.best_partition_representatives(omit_first_partition=False)
    O.cb_ops = []
    O.perms = []
    O.inv_perms = []
    for rep in reps:
      assert rep.t().is_zero()
      cb_op = cctbx.sgtbx.change_of_basis_op(rep)
      O.cb_ops.append(cb_op)
      mi_cb = cb_op.apply(miller_indices)
      matches = cctbx.miller.match_indices(mi_cb, miller_indices)
      assert not matches.have_singles()
      perm = matches.permutation()
      O.perms.append(perm)
      O.inv_perms.append(perm.inverse_permutation())
    lookup_dict = {}
    for i_part,part in enumerate(cosets.partitions):
      for s in part:
        assert s.t().is_zero()
        key = str(s.r().as_hkl())
        lookup_dict[key] = i_part
    def multiplication_table(j_inv):
      result = []
      for rep_i in reps:
        row = []
        for rep_j in reps:
          def rep_j_or_inverse():
            if (j_inv): return rep_j.inverse()
            return rep_j
          s = rep_i.multiply(rep_j_or_inverse())
          assert s.t().is_zero()
          key = str(s.r().as_hkl())
          row.append(lookup_dict[key])
        result.append(row)
      return result
    O.i_j_multiplication_table = multiplication_table(j_inv=0)
    O.i_j_inv_multiplication_table = multiplication_table(j_inv=1)
