
"""
Classes for MolProbity validation, combining all other analyses in
mmtbx.validation, which use the same APIs for storing and displaying results.
"""

# TODO combine with some parts of mmtbx.kinemage.validation

from __future__ import division
from mmtbx.validation import validation, residue
from mmtbx.validation import model_properties
from mmtbx.validation import experimental
from mmtbx.validation import rna_validate
from mmtbx.validation import clashscore
from mmtbx.validation import restraints
from mmtbx.validation import ramalyze
from mmtbx.validation import rotalyze
from mmtbx.validation import cbetadev
from mmtbx.validation import waters
from libtbx.str_utils import make_header, make_sub_header, format_value
from libtbx import slots_getstate_setstate, \
    slots_getstate_setstate_default_initializer
from libtbx.utils import null_out, Sorry
import libtbx.load_env
import libtbx.phil
import os.path
import sys

master_phil_str = """
clashscore = True
  .type = bool
ramalyze = True
  .type = bool
rotalyze = True
  .type = bool
cbetadev = True
  .type = bool
nqh = True
  .type = bool
rna = True
  .type = bool
model_stats = True
  .type = bool
restraints = True
  .type = bool
rfactors = True
  .type = bool
real_space = True
  .type = bool
waters = True
  .type = bool
seq = True
  .type = bool
xtriage = False
  .type = bool
"""

def molprobity_flags () :
  """
  Default flags for analyses to perform (all True).
  """
  return libtbx.phil.parse(master_phil_str).extract()

class molprobity (slots_getstate_setstate) :
  """
  Comprehensive validation.  At a minimum this performs the standard MolProbity
  analyses (ramalyze, rotalyze, cbetadev, clashscore).  If a geometry
  restraints manager is available, the deviations from standard covalent
  geometry will also be displayed.  Passing an fmodel object enables the
  re-calculation of R-factors and real-space correlation.

  :param pdb_hierarchy: model PDB hierarchy (required)
  :param xray_structure: model X-ray scatterers
  :param fmodel: mmtbx.f_model.manager object, after bulk solvent/scaling
  :param fmodel_neutron: separate Fmodel manager for neutron data (used in
                         phenix.refine for join X/N refinement)
  :param geometry_restraints_manager: geometry restraints extracted by \
                                      mmtbx.monomer_library.pdb_interpretation
  :param sequences: parsed sequence objects (from iotbx.bioinformatics)
  :param crystal_symmetry: cctbx.crystal.symmetry object
  :param flags: object containing boolean flags for analyses to perform
  :param header_info: extracted statistics from PDB file header
  :param raw_data: input data before French-Wilson treatment, etc.
  :param unmerged_data: separate unmerged intensities for merging statistics
  :param all_chain_proxies: object containing restraints information and \
      advanced selections from mmtbx.monomer_library.pdb_interpretation
  :param keep_hydrogens: don't discard and replace existing hydrogens for \
      clashscore calculation
  :param nuclear: use nuclear hydrogen distances (for neutron experiments)
  :param save_probe_unformatted_file: file name for Probe output suitable for \
      display in Coot
  :param show_hydrogen_outliers: show geometry outliers for hydrogen atoms
  :param min_cc_two_fofc: Fo-Fc map cutoff for real-space outliers
  :param n_bins_data: Number of resolution bins for data statistics
  :param count_anomalous_pairs_separately: count F+ and F- as separate \
      reflections (default=False)
  :param outliers_only: only display validation outliers
  :param use_pdb_header_resolution_cutoffs: use resolution cutoff(s) \
      specified in PDB header for data statistics
  """

  # XXX this is used to distinguish objects of this type from an older (and
  # now obsolete) class in the phenix tree.
  molprobity_version_number = (4,1)

  __slots__ = [
    "ramalyze",
    "rotalyze",
    "cbetadev",
    "clashes",
    "nqh_flips",
    "rna",
    "restraints",
    "missing_atoms",
    "data_stats",
    "neutron_stats",
    "real_space",
    "crystal_symmetry",
    "model_stats",
    "waters",
    "header_info",
    "merging",
    "sequence",
    "xtriage",
    "_multi_criterion",
    "file_name",
  ]

  # backwards compatibility with saved results
  def __setstate__(self, state):
    for name,value in state.items(): setattr(self, name, value)
    for name in self.__slots__ :
      if not hasattr(self, name) : setattr(self, name, None)

  def __init__ (self,
      pdb_hierarchy,
      xray_structure=None,
      fmodel=None,
      fmodel_neutron=None,
      geometry_restraints_manager=None,
      crystal_symmetry=None,
      sequences=None,
      flags=None,
      header_info=None,
      raw_data=None,
      unmerged_data=None,
      all_chain_proxies=None,
      keep_hydrogens=True,
      nuclear=False,
      save_probe_unformatted_file=None,
      show_hydrogen_outliers=False,
      min_cc_two_fofc=0.8,
      n_bins_data=10,
      count_anomalous_pairs_separately=False,
      outliers_only=True,
      use_pdb_header_resolution_cutoffs=False,
      file_name=None,
      ligand_selection=None,
      rotamer_library="500") :
    for name in self.__slots__ :
      setattr(self, name, None)
    # very important - the i_seq attributes may be extracted later
    pdb_hierarchy.atoms().reset_i_seq()
    if (xray_structure is None) :
      if (fmodel is not None) :
        xray_structure = fmodel.xray_structure
      elif (crystal_symmetry is not None) :
        xray_structure = pdb_hierarchy.extract_xray_structure(
          crystal_symmetry=crystal_symmetry)
    self.crystal_symmetry = crystal_symmetry
    if (crystal_symmetry is None) and (fmodel is not None) :
      self.crystal_symmetry = fmodel.f_obs().crystal_symmetry()
    self.header_info = header_info
    if (flags is None) :
      flags = molprobity_flags()
    if pdb_hierarchy.contains_protein() :
      if (flags.ramalyze) :
        self.ramalyze = ramalyze.ramalyze(
          pdb_hierarchy=pdb_hierarchy,
          outliers_only=outliers_only,
          out=null_out(),
          quiet=True)
      if (flags.rotalyze) :
        self.rotalyze = rotalyze.rotalyze(
          pdb_hierarchy=pdb_hierarchy,
          data_version=rotamer_library,
          outliers_only=outliers_only,
          out=null_out(),
          quiet=True)
      if (flags.cbetadev) :
        self.cbetadev = cbetadev.cbetadev(
          pdb_hierarchy=pdb_hierarchy,
          outliers_only=outliers_only,
          out=null_out(),
          quiet=True)
      if (flags.nqh) :
        self.nqh_flips = clashscore.nqh_flips(
          pdb_hierarchy=pdb_hierarchy)
    if (pdb_hierarchy.contains_rna() and flags.rna and
        libtbx.env.has_module(name="suitename")) :
      if (geometry_restraints_manager is not None) :
        self.rna = rna_validate.rna_validation(
          pdb_hierarchy=pdb_hierarchy,
          geometry_restraints_manager=geometry_restraints_manager,
          outliers_only=outliers_only,
          params=None)
    if (flags.clashscore) :
      self.clashes = clashscore.clashscore(
        pdb_hierarchy=pdb_hierarchy,
        save_probe_unformatted_file=save_probe_unformatted_file,
        nuclear=nuclear,
        keep_hydrogens=keep_hydrogens,
        out=null_out(),
        verbose=False)
    if (flags.model_stats) and (xray_structure is not None) :
      self.model_stats = model_properties.model_statistics(
        pdb_hierarchy=pdb_hierarchy,
        xray_structure=xray_structure,
        all_chain_proxies=all_chain_proxies,
        ignore_hd=(not nuclear),
        ligand_selection=ligand_selection)
    if (geometry_restraints_manager is not None) and (flags.restraints) :
      assert (xray_structure is not None)
      self.restraints = restraints.combined(
        pdb_hierarchy=pdb_hierarchy,
        xray_structure=xray_structure,
        geometry_restraints_manager=geometry_restraints_manager,
        ignore_hd=(not nuclear))
    if (sequences is not None) and (flags.seq) :
      self.sequence = sequence.validation(
        pdb_hierarchy=pdb_hierarchy,
        sequences=sequences,
        log=null_out(),
        include_secondary_structure=True,
        extract_coordinates=True)
    if (fmodel is not None) :
      if (use_pdb_header_resolution_cutoffs) and (header_info is not None) :
        fmodel = fmodel.resolution_filter(
          d_min=header_info.d_min,
          d_max=header_info.d_max)
      if (flags.rfactors) :
        self.data_stats = experimental.data_statistics(fmodel,
          raw_data=raw_data,
          n_bins=n_bins_data,
          count_anomalous_pairs_separately=count_anomalous_pairs_separately)
      if (flags.waters) :
        self.waters = waters.waters(
          pdb_hierarchy=pdb_hierarchy,
          xray_structure=xray_structure,
          fmodel=fmodel,
          collect_all=False)
      if (flags.real_space) :
        self.real_space = experimental.real_space(
          fmodel=fmodel,
          pdb_hierarchy=pdb_hierarchy,
          cc_min=min_cc_two_fofc)
      if (unmerged_data is not None) :
        self.merging = experimental.merging_and_model_statistics(
          f_obs=fmodel.f_obs(),
          f_model=fmodel.f_model(),
          r_free_flags=fmodel.r_free_flags(),
          unmerged_i_obs=unmerged_data,
          anomalous=count_anomalous_pairs_separately,
          n_bins=n_bins_data)
      if (flags.xtriage) :
        import mmtbx.scaling.xtriage
        f_model = abs(fmodel.f_model()).set_observation_type_xray_amplitude()
        if (raw_data is not None) :
          f_model, obs = f_model.common_sets(other=raw_data)
        else :
          obs = fmodel.f_obs()
        self.xtriage = mmtbx.scaling.xtriage.xtriage_analyses(
          miller_obs=obs,
          miller_calc=f_model,
          unmerged_obs=unmerged_data,
          text_out=null_out())
    if (fmodel_neutron is not None) and (flags.rfactors) :
      self.neutron_stats = experimental.data_statistics(fmodel_neutron,
        n_bins=n_bins_data,
        count_anomalous_pairs_separately=False)
    if (pdb_hierarchy.models_size() == 1) :
      self._multi_criterion = multi_criterion_view(pdb_hierarchy)

  def molprobity_score (self) :
    """
    Compute overall measure of (protein!) structure quality based on an
    empirical formula combining clashscore, rotamer outliers, and Ramachandran
    favored statistics.  The result is on approximately the same scale as
    resolution.
    """
    if (None in [self.ramalyze, self.rotalyze, self.clashes]) :
      return None
    from mmtbx.validation import utils
    return utils.molprobity_score(
      clashscore=self.clashes.get_clashscore(),
      rota_out=self.rotalyze.out_percent,
      rama_fav=self.ramalyze.fav_percent)

  def show (self, out=sys.stdout, outliers_only=True, suppress_summary=False,
      show_percentiles=False) :
    """
    Comprehensive output with individual outlier lists, plus summary.
    """
    if (self.xtriage is not None) :
      self.xtriage.summarize_issues().show(out=out)
    if (self.data_stats is not None) :
      make_header("Experimental data", out=out)
      self.data_stats.show(out=out, prefix="  ")
      if (self.real_space is not None) :
        make_sub_header("Residues with poor real-space CC", out=out)
        self.real_space.show(out=out, prefix="  ")
      if (self.waters is not None) :
        make_sub_header("Suspicious water molecules", out=out)
        self.waters.show(out=out, prefix="  ")
    if (self.model_stats is not None) :
      make_header("Model properties", out=out)
      self.model_stats.show(prefix="  ", out=out)
    if (self.restraints is not None) :
      make_header("Geometry restraints", out=out)
      self.restraints.show(out=out, prefix="  ")
    make_header("Molprobity validation", out=out)
    if (self.ramalyze is not None) :
      make_sub_header("Ramachandran angles", out=out)
      self.ramalyze.show(out=out, prefix="  ", outliers_only=outliers_only)
    if (self.rotalyze is not None) :
      make_sub_header("Sidechain rotamers", out=out)
      self.rotalyze.show(out=out, prefix="  ", outliers_only=outliers_only)
    if (self.cbetadev is not None) :
      make_sub_header("C-beta deviations", out=out)
      self.cbetadev.show(out=out, prefix="  ", outliers_only=outliers_only)
    if (self.clashes is not None) :
      make_sub_header("Bad clashes", out=out)
      self.clashes.show(out=out, prefix="  ")
    if (self.nqh_flips is not None) :
      make_sub_header("Asn/Gln/His flips", out=out)
      self.nqh_flips.show(out=out, prefix="  ")
    if (self.rna is not None) :
      make_header("RNA validation", out=out)
      self.rna.show(out=out, prefix="  ", outliers_only=outliers_only)
    if (not suppress_summary) :
      make_header("Summary", out=out)
      self.show_summary(out=out, prefix="  ",
        show_percentiles=show_percentiles)
    return self

  def summarize (self) :
    """
    Condense results into a compact object - for compatibility with
    (now obsolete) mmtbx.validation_summary, and use in high-throughput
    analyses
    """
    clashscore = r_work = r_free = rms_bonds = rms_angles = d_min = None
    if (self.clashes is not None) :
      clashscore = self.clashes.get_clashscore()
    if (self.restraints is not None) :
      rms_bonds, rms_angles = self.restraints.get_bonds_angles_rmsds()
    if (self.data_stats is not None) :
      r_work, r_free = self.data_stats.r_work, self.data_stats.r_free
      d_min = self.data_stats.d_min
    elif (self.header_info is not None) :
      r_work, r_free = self.header_info.r_work, self.header_info.r_free
      d_min = self.header_info.d_min
      if (self.restraints is None) :
        rms_bonds = self.header_info.rms_bonds
        rms_angles = self.header_info.rms_angles
    mpscore = self.molprobity_score()
    return summary(
      rama_outliers=getattr(self.ramalyze, "out_percent", None),
      rama_favored=getattr(self.ramalyze, "fav_percent", None),
      rotamer_outliers=getattr(self.rotalyze, "out_percent", None),
      c_beta_deviations=getattr(self.cbetadev, "n_outliers", None),
      clashscore=clashscore,
      bond_rmsd=rms_bonds,
      angle_rmsd=rms_angles,
      mpscore=mpscore,
      d_min=d_min,
      r_work=r_work,
      r_free=r_free,
      program=getattr(self.header_info, "refinement_program", None))

  def show_summary (self, *args, **kwds) :
    """
    Print summary of outliers or scores for each analysis.
    """
    return self.summarize().show(*args, **kwds)

  def r_work (self, outer_shell=False) :
    if (outer_shell) :
      return getattr(self.data_stats, "r_work_outer", None)
    else :
      return getattr(self.data_stats, "r_work",
        getattr(self.header_info, "r_work", None))

  def r_free (self, outer_shell=False) :
    if (outer_shell) :
      return getattr(self.data_stats, "r_free_outer", None)
    else :
      return getattr(self.data_stats, "r_free",
        getattr(self.header_info, "r_free", None))

  def d_min (self) :
    if (self.data_stats is not None) :
      return self.data_stats.d_min
    elif (self.header_info is not None) :
      return self.header_info.d_min

  def d_max_min (self, outer_shell=False) :
    if (self.data_stats is not None) :
      if (outer_shell) :
        return self.data_stats.d_max_outer, self.data_stats.d_min_outer
      else :
        return self.data_stats.d_max, self.data_stats.d_min

  def rms_bonds (self) :
    if (self.restraints is not None) :
      rms_bonds, rms_angles = self.restraints.get_bonds_angles_rmsds()
      return rms_bonds

  def rms_angles (self) :
    if (self.restraints is not None) :
      rms_bonds, rms_angles = self.restraints.get_bonds_angles_rmsds()
      return rms_angles

  def rama_favored (self) :
    return getattr(self.ramalyze, "fav_percent", None)

  def rama_outliers (self) :
    return getattr(self.ramalyze, "out_percent", None)

  def rama_allowed (self) :
    if (self.ramalyze is not None) :
      return self.ramalyze.percent_allowed
    return None

  def rota_outliers (self) :
    return getattr(self.rotalyze, "out_percent", None)

  def cbeta_outliers (self) :
    return getattr(self.cbetadev, "n_outliers", None)

  def clashscore (self) :
    return getattr(self.clashes, "get_clashscore", lambda: None)()

  def b_iso_mean (self) :
    overall_stats = getattr(self.model_stats, "all", None)
    return getattr(overall_stats, "b_mean", None)

  def space_group (self) :
    return getattr(self.crystal_symmetry, "space_group", lambda: None)()

  def space_group_info (self) :
    return getattr(self.crystal_symmetry, "space_group_info", lambda: None)()

  def unit_cell (self) :
    return getattr(self.crystal_symmetry, "unit_cell", lambda: None)()

  def twin_law (self) :
    return getattr(self.data_stats, "twin_law", None)

  def fmodel_statistics_by_resolution (self) :
    """
    Returns the resolution bins containing F(model) statistics; see
    mmtbx.f_model_info for details.
    """
    fmodel_info = getattr(self.data_stats, "info", None)
    return getattr(fmodel_info, "bins", None)

  def fmodel_statistics_graph_data (self) :
    """
    Wrapper for fmodel_statistics_by_resolution(), returns object suitable for
    routines in wxtbx.plots.
    """
    bins = self.fmodel_statistics_by_resolution()
    if (bins is not None) :
      from mmtbx.f_model_info import export_bins_table_data
      return export_bins_table_data(bins)
    return None

  def atoms_to_observations_ratio (self, assume_riding_hydrogens=True) :
    n_atoms = self.model_stats.n_atoms
    if (assume_riding_hydrogens) :
      n_atoms -= self.model_stats.n_hydrogens
    n_refl = self.data_stats.n_refl
    assert (n_refl > 0)
    return n_atoms / n_refl

  def as_mmcif_records (self) : # TODO
    raise NotImplementedError()

  def as_multi_criterion_view (self) :
    if (self._multi_criterion is None) :
      return None
    if (not self._multi_criterion.is_populated) :
      if (self.real_space is not None) :
        self._multi_criterion.process_outliers(self.real_space.results)
      if (self.waters is not None) :
        self._multi_criterion.process_outliers(self.waters.results)
      if (self.ramalyze is not None) :
        self._multi_criterion.process_outliers(self.ramalyze.results)
      if (self.rotalyze is not None) :
        self._multi_criterion.process_outliers(self.rotalyze.results)
      if (self.cbetadev is not None) :
        self._multi_criterion.process_outliers(self.cbetadev.results)
      if (self.clashes is not None) :
        self._multi_criterion.process_outliers(self.clashes.results)
    return self._multi_criterion

  def display_wx_plots (self) :
    if (self.ramalyze is not None) :
      self.ramalyze.display_wx_plots()
    if (self.rotalyze is not None) :
      self.rotalyze.display_wx_plots()
    mc = self.as_multi_criterion_view()
    mc.display_wx_plots()

  def write_coot_script (self, file_name) :
    """
    Write a Python script for displaying outlier lists with click-to-recenter
    enabled.
    """
    coot_script = libtbx.env.find_in_repositories(
      relative_path="cctbx_project/cootbx/validation_lists.py",
      test=os.path.isfile)
    if (coot_script is None) :
      raise Sorry("Can't find template Python script for Coot.")
    f = open(file_name, "w")
    f.write("# script auto-generated by phenix.molprobity\n")
    f.write("\n")
    f.write(open(coot_script).read())
    f.write("\n")
    f.write("data = {}\n")
    if (self.ramalyze is not None) :
      f.write("data['rama'] = %s\n" % self.ramalyze.as_coot_data())
    if (self.rotalyze is not None) :
      f.write("data['rota'] = %s\n" % self.rotalyze.as_coot_data())
    if (self.cbetadev is not None) :
      f.write("data['cbeta'] = %s\n" % self.cbetadev.as_coot_data())
    if (self.clashes is not None) :
      f.write("data['probe'] = %s\n" % self.clashes.as_coot_data())
      if (self.clashes.probe_file is not None) :
        f.write("handle_read_draw_probe_dots_unformatted(\"%s\", 0, 0)\n" %
          self.clashes.probe_file)
        f.write("show_probe_dots(True, True)\n")
    f.write("gui = coot_molprobity_todo_list_gui(data=data)\n")
    f.close()

  def get_polygon_statistics (self, stat_names) :
    stats = {}
    for name in stat_names :
      val = None
      if (name == "r_work") : val = self.r_work()
      elif (name == "r_free") : val = self.r_free()
      elif (name == "wilson_b") : pass
      elif (name == "rama_favored") : val = self.rama_favored()
      elif (name == "rama_outliers") : val =  self.rama_outliers()
      elif (name == "rotamer_outliers") : val = self.rota_outliers()
      elif (name == "clashscore") : val = self.clashscore()
      elif (name == "bond_rmsd") : val = self.rms_bonds()
      elif (name == "angle_rmsd") : val = self.rms_angles()
      elif (name == "adp_mean_all") : val = self.b_iso_mean()
      stats[name] = val
    return stats

  def get_statistics_for_phenix_gui (self) :
    mp = self
    stats = [
      ("R-work", format_value("%.4f", mp.r_work())),
      ("R-free", format_value("%.4f", mp.r_free())),
      ("RMS(bonds)", format_value("%.3f", mp.rms_bonds())),
      ("RMS(angles)", format_value("%.4f", mp.rms_angles())),
      ("Clashscore", format_value("%.2f", mp.clashscore())),
      ("MolProbity score", format_value("%.3f", mp.molprobity_score())),
    ]
    if (self.neutron_stats is not None) :
      stats.extend([
        ("R-work (neutron)", format_value("%.4f", self.neutron_stats.r_work)),
        ("R-free (neutron)", format_value("%.4f", self.neutron_stats.r_free)),
      ])
    return stats

class summary (slots_getstate_setstate_default_initializer) :
  """
  Simplified container for overall statistics; replaces class of the same
  name in mmtbx.command_line.validation_summary.  The more complete molprobity
  class is prefered when analyzing a single structure, but it is considerably
  larger.
  """
  __slots__ = [
    "rama_outliers",
    "rama_favored",
    "rotamer_outliers",
    "c_beta_deviations",
    "clashscore",
    "bond_rmsd",
    "angle_rmsd",
    "mpscore",
    "d_min",
    "r_work",
    "r_free",
    "program",
  ]
  labels = [
    "Ramachandran outliers",
    "              favored",
    "Rotamer outliers",
    "C-beta deviations",
    "Clashscore",
    "RMS(bonds)",
    "RMS(angles)",
    "MolProbity score",
    "Resolution",
    "R-work",
    "R-free",
    "Refinement program",
  ]
  formats = [
    "%6.2f", "%6.2f", "%6.2f", "%5d", "%6.2f", "%8.4f", "%6.2f", "%6.2f",
    "%6.2f", "%8.4f", "%8.4f", "%s",
  ]

  def show (self, out=sys.stdout, prefix="  ", show_percentiles=False) :
    def fs (format, value) :
      return format_value(format, value, replace_none_with=("(none)"))
    maxlen = max([ len(label) for label in self.labels ])
    percentiles = {}
    if (show_percentiles) :
      perc_attr = ["clashscore", "mpscore", "r_work", "r_free"]
      stats = dict([ (name, getattr(self, name)) for name in perc_attr ])
      from mmtbx.polygon import get_statistics_percentiles
      percentiles = get_statistics_percentiles(self.d_min, stats)
    for k, name in enumerate(self.__slots__) :
      format = "%%s%%-%ds = %%s" % maxlen
      if (k < 3) :
        format += " %%"
      percentile_info = ""
      if (show_percentiles) :
        percentile = percentiles.get(name, None)
        if (percentile is not None) :
          format += " (percentile: %s)"
          percentile_info = "%.1f" % percentile
        else :
          format += "%s"
      else :
        format += "%s"
      value = getattr(self, name)
      if (value is not None) :
        print >> out, format % (prefix, self.labels[k], fs(self.formats[k],
          value), percentile_info)
    return self

  def iter_molprobity_gui_fields (self) :
    stats = [
      ("Ramachandran outliers","%6.2f%%",self.rama_outliers,0.5,0.2,"< 0.2%"),
      ("Ramachandran favored", "%6.2f%%",self.rama_favored,None,None,"> 98%"),
      ("Rotamer outliers", "%6.2f%%", self.rotamer_outliers, 2, 1, "1%"),
      ("C-beta outliers", "%3d   ", self.c_beta_deviations, 2, 0, "0"),
      ("Clashscore", "%6.2f", self.clashscore, 40, 20, None),
      ("Overall score", "%6.2f", self.mpscore, None, None, None),
    ]
    for stat_info in stats :
      yield stat_info

########################################################################

class pdb_header_info (slots_getstate_setstate) :
  """
  Container for information extracted from the PDB header (if available).
  """
  __slots__ = ["d_min", "d_max", "r_work", "r_free", "rms_bonds", "rms_angles",
    "refinement_program", "n_tls_groups"]
  def __init__ (self, pdb_file, pdb_hierarchy=None) :
    for name in self.__slots__ :
      setattr(self, name, None)
    if (pdb_file is not None) :
      import iotbx.pdb.hierarchy
      from iotbx.pdb import extract_rfactors_resolutions_sigma
      pdb_in = iotbx.pdb.hierarchy.input(file_name=pdb_file)
      published_results = extract_rfactors_resolutions_sigma.extract(
        file_lines=pdb_in.input.remark_section(), file_name=None)
      if (published_results is not None) :
        self.r_work = published_results.r_work
        self.r_free = published_results.r_free
        self.d_min = published_results.high
        self.d_max = published_results.low
      self.refinement_program = pdb_in.input.get_program_name()
      # XXX phenix.refine hack, won't work for other programs
      lines = open(pdb_file).readlines()
      for line in lines :
        if (line.startswith("REMARK Final:")) :
          fields = line.strip().split()
          self.rms_bonds = float(fields[-4])
          self.rms_angles = float(fields[-1])
          break
      if (pdb_hierarchy is not None) :
        tls_groups = pdb_in.input.extract_tls_params(pdb_hierarchy).tls_params
        if (tls_groups is not None) :
          self.n_tls_groups = len(tls_groups)

  def is_phenix_refinement (self) :
    return (self.refinement_program is not None and
            "phenix" in self.refinement_program.lower())

  def show (self, out=sys.stdout, prefix="", include_r_factors=True,
      include_rms_geom=True) :
    if (self.refinement_program is not None) :
      print >> out, "%sRefinement program    = %s" % (prefix,
        self.refinement_program)
    if (include_r_factors) :
      if (self.d_min is not None) :
        print >> out, "%sHigh resolution       = %6.2f" % (prefix, self.d_min)
      if (self.r_work is not None) :
        print >> out, "%sR-work                = %8.4f" % (prefix, self.r_work)
      if (self.r_free is not None) :
        print >> out, "%sR-free                = %8.4f" % (prefix, self.r_free)
    if (include_rms_geom) :
      if (self.rms_bonds is not None) :
        print >> out, "%sRMS(bonds)            = %8.4f" % (prefix,
          self.rms_bonds)
      if (self.rms_angles is not None) :
        print >> out, "%sRMS(angles)           = %6.2f" % (prefix,
          self.rms_angles)

class residue_multi_criterion (residue) :
  """
  Container for multiple outliers associated with a single residue.  If data
  are used, this may include real-space statistics regardless of whether the
  residue is technically an outlier or not.
  """
  __slots__ = residue.__slots__ + ["outliers", "n_confs", "i_seq"]
  def __init__ (self, **kwds) :
    residue.__init__(self, **kwds)
    self.outliers = []

  def add_outlier (self, outlier) :
    if isinstance(outlier, residue) :
      assert self.is_same_residue_group(outlier)
    self.outliers.append(outlier)

  def _find_outlier_type (self, outlier_type=None, outlier_types=(),
      retrieve_all=False) :
    assert (outlier_type is not None) or (len(outlier_types) > 0)
    for outlier in self.outliers :
      if (not outlier.is_outlier()) and (not retrieve_all) :
        continue
      otype = type(outlier).__name__
      if (otype == outlier_type) or (otype in outlier_types) :
        return True
    return False

  def is_ramachandran_outlier (self) :
    return self._find_outlier_type("ramachandran")

  def is_rotamer_outlier (self) :
    return self._find_outlier_type("rotamer")

  def is_cbeta_outlier (self) :
    return self._find_outlier_type("cbeta")

  def is_clash_outlier (self) :
    return self._find_outlier_type("clash")

  def is_geometry_outlier (self) :
    return self._find_outlier_type(
      outlier_types=["bond","angle","dihedral","chirality","planarity"])

  def __str__ (self) :
    outliers = []
    if self.is_ramachandran_outlier() : outliers.append("rama")
    if self.is_rotamer_outlier() : outliers.append("rota")
    if self.is_cbeta_outlier() : outliers.append("cb")
    if self.is_clash_outlier() : outliers.append("clash")
    if self.is_geometry_outlier() : outliers.append("geo")
    if (len(outliers) == 0) : outliers = ["---"]
    return "%s  %s" % (self.id_str(), ",".join(outliers))

  def __hash__ (self) :
    return self.residue_group_id_str().__hash__()

  def __cmp__ (self, other) :
    return cmp(self.i_seq, other.i_seq)

  def get_real_space_plot_values (self, use_numpy_NaN=True) :
    for outlier in self.outliers :
      if (type(outlier).__name__ == 'residue_real_space') :
        values = [ outlier.b_iso, outlier.cc, outlier.two_fofc, outlier.fmodel ]
        return values
    if (use_numpy_NaN) :
      import numpy
      return [ numpy.NaN ] * 4
    else :
      return [ None ] * 4

  def is_map_outlier (self, cc_min=0.8) :
    b_iso, cc, two_fofc, fmodel = self.get_real_space_plot_values(False)
    if (cc is None) :
      return None
    elif (cc < cc_min) :
      return True
    return False

  def get_outlier_plot_values (self, use_numpy_NaN=True) :
    y = []
    if self.is_ramachandran_outlier() : y.append(1)
    else : y.append(None)
    if self.is_rotamer_outlier() : y.append(1)
    else : y.append(None)
    if self.is_cbeta_outlier() : y.append(1)
    else : y.append(None)
    if self.is_clash_outlier() : y.append(1)
    else : y.append(None)
    if (use_numpy_NaN) :
      import numpy
      y_ = []
      for yval in y :
        if (yval is None) : y_.append(numpy.NaN)
        else :              y_.append(yval)
      return y_
    return y

class multi_criterion_view (slots_getstate_setstate) :
  """
  Container for generating multi-criterion plots and tables from separate lists
  of outliers.
  """
  __slots__ = ["residues", "is_populated"]
  def __init__ (self, pdb_hierarchy, include_all=False) :
    self.is_populated = False
    self.residues = {}
    i_seq = 0
    for chain in pdb_hierarchy.only_model().chains() :
      if (not include_all) :
        if (not chain.is_protein()) and (not chain.is_na()) :
          continue
      for residue_group in chain.residue_groups() :
        resname = residue_group.atom_groups()[0].resname
        if (resname == "HOH") : continue
        combined = residue_multi_criterion(
          chain_id=chain.id,
          resseq=residue_group.resseq,
          icode=residue_group.icode,
          resname=residue_group.atom_groups()[0].resname,
          altloc="",
          i_seq=i_seq,
          n_confs=len(residue_group.atom_groups()))
        id_str = combined.residue_group_id_str()
        self.residues[id_str] = combined
        i_seq += 1

  def process_outliers (self, outliers, log=sys.stderr) :
    self.is_populated = True
    for outlier in outliers :
      if outlier.is_single_residue_object() :
        if (outlier.resname == "HOH") : continue
        id_str = outlier.residue_group_id_str()
        if (id_str in self.residues) :
          self.residues[id_str].add_outlier(outlier)
        else :
          print >> log, "missing residue group '%s'" % id_str
      else :
        have_ids = set([])
        for atom in outlier.atoms_info :
          id_str = atom.residue_group_id_str()
          if (atom.resname == "HOH") or (id_str in have_ids) : continue
          if (id_str in self.residues) :
            self.residues[id_str].add_outlier(outlier)
            have_ids.add(id_str)
          else :
            print >> log, "missing residue group '%s'" % id_str

  def get_residue_group_data (self, residue_group) :
    residue_validation = self.residues.get(residue_group.id_str(), None)
    if (residue_validation is None) :
      raise RuntimeError("Can't find residue '%s'" % residue_group.id_str())
    return residue_validation

  def data (self) :
    return sorted(self.residues.values())

  def binned_data (self) :
    from mmtbx.validation import graphics
    return graphics.residue_binner(self.data())

  def get_y_limits (self) :
    import numpy
    values = []
    for outlier in self.data() :
      values.append(outlier.get_real_space_plot_values())
    values = numpy.array(values).transpose()
    rho_min = min(min(values[2]), min(values[3]))
    rho_max = max(max(values[2]), max(values[3]))
    return {
      "rho" : (rho_min, rho_max),
      "b" : (min(values[0]), max(values[0])),
      "cc" : (min(values[1]), max(values[1])),
    }

  def display_wx_plots (self) :
    import wxtbx.plots.molprobity
    frame = wxtbx.plots.molprobity.multi_criterion_frame(
      parent=None,
      title="MolProbity multi-criterion plot",
      validation=self)
    frame.Show()
