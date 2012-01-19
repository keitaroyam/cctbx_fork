
# simple frontend to mmtbx.find_peaks, primarily intended for use in quickly
# analyzing structures in the PDB (and storing results)
#
# TODO (???) plugin for Coot

from mmtbx import utils
from scitbx.array_family import flex
from libtbx.str_utils import make_header
import libtbx.phil
from libtbx import adopt_init_args, group_args
from cStringIO import StringIO
import sys

master_phil = libtbx.phil.parse("""
%s
find_peaks {
  include scope mmtbx.find_peaks.master_params
}
map_cutoff = 3.0
  .type = float
anom_map_cutoff = 3.0
  .type = float
write_pdb = False
  .type = bool
""" % utils.cmdline_input_phil_str,
  process_includes=True)

class peaks_holes_container (object) :
  def __init__ (self, peaks, holes, map_cutoff=3.0, anom_peaks=None,
      anom_map_cutoff=3.0, water_peaks=None, water_anom_peaks=None) :
    adopt_init_args(self, locals())

  def show_summary (self, out=sys.stdout) :
    print >> out, ""
    print >> out, "SUMMARY OF MAP PEAKS:"
    cutoffs = [self.map_cutoff, self.map_cutoff + 3.0, self.map_cutoff + 6.0]
    for cutoff in cutoffs :
      n_peaks = (self.peaks.heights > cutoff).count(True)
      print >> out, "  mFo-DFc >  %-4g   : %6d" % (cutoff, n_peaks)
    peak_max = flex.max(self.peaks.heights)
    print >> out, "  mFo-DFc max       : %6.2f" % peak_max
    for cutoff in cutoffs :
      n_holes = (self.holes.heights < -cutoff).count(True)
      print >> out, "  mFo-DFc < -%-4g   : %6d" % (cutoff, n_holes)
    hole_max = flex.min(self.holes.heights)
    print >> out, "  mFo-DFc min       : %6.2f" % hole_max
    if (self.anom_peaks is not None) :
      print >> out, "  anomalous > %-4g : %6d" % (self.anom_map_cutoff,
        len(self.anom_peaks.heights))
    if (self.water_peaks is not None) :
      print >> out, "  suspicious H2O (mFo-DFC > %g) : %6d" % (self.map_cutoff,
        len(self.water_peaks))
    if (self.water_anom_peaks is not None) :
      print >> out, "  anomalous H2O (anomalous > %g): %6d" % (self.map_cutoff,
        len(self.water_anom_peaks))
    print >> out, ""

  def get_summary (self) :
    """
    Returns a simple object for harvesting statistics elsewhere.
    """
    n_anom_peaks = None
    if (self.anom_peaks is not None) :
      n_anom_peaks = len(self.anom_peaks.heights)
    n_water_peaks = None
    if (self.water_peaks is not None) :
      n_water_peaks = len(self.water_peaks)
    if (self.water_anom_peaks is not None) :
      n_water_anom_peaks = len(self.water_anom_peaks)
    return group_args(
      n_peaks_1=(self.peaks.heights > self.map_cutoff).count(True),
      n_peaks_2=(self.peaks.heights > self.map_cutoff + 3).count(True),
      n_peaks_3=(self.peaks.heights > self.map_cutoff + 6).count(True),
      n_holes_1=(self.holes.heights < -self.map_cutoff).count(True),
      n_holes_2=(self.holes.heights < -self.map_cutoff - 3).count(True),
      n_holes_3=(self.holes.heights < -self.map_cutoff - 6).count(True),
      peak_max=flex.max(self.peaks.heights),
      hole_max=flex.min(self.holes.heights),
      n_anom_peaks=n_anom_peaks,
      n_water_peaks=n_water_peaks,
      n_water_anom_peaks=n_water_anom_peaks)

  def n_peaks_above_cutoff (self, cutoff) :
    assert (cutoff > 0)
    return (self.peaks.heights > cutoff).count(True)

  def n_holes_below_cutoff (self, cutoff) :
    assert (cutoff < 0)
    return (self.holes.heights < cutoff).count(True)

  def save_pdb_file (self,
      file_name="peaks.pdb",
      include_holes=True,
      include_anom=True,
      log=None) :
    """
    Write out a PDB file with up to three chains: A for peaks, B for holes,
    C for anomalous peaks.  Atoms are UNK, with the B-factor set to the height
    or depth of the peak or hole.
    """
    if (log is None) : log = sys.stdout
    import iotbx.pdb.hierarchy
    selection = flex.sort_permutation(self.peaks.heights, reverse=True)
    peaks_sorted = self.peaks.heights.select(selection)
    sites_sorted = self.peaks.sites.select(selection)
    root = iotbx.pdb.hierarchy.root()
    model = iotbx.pdb.hierarchy.model()
    root.append_model(model)
    peaks_chain = iotbx.pdb.hierarchy.chain(id="A")
    model.append_chain(peaks_chain)
    def create_atom (xyz, peak, serial) :
      rg = iotbx.pdb.hierarchy.residue_group(resseq=str(serial))
      ag = iotbx.pdb.hierarchy.atom_group(resname="UNK")
      rg.append_atom_group(ag)
      a = iotbx.pdb.hierarchy.atom()
      ag.append_atom(a)
      a.name = " UNK"
      a.element = "X"
      a.xyz = xyz
      a.b = peak
      a.occ = 1.
      a.serial = serial
      return rg
    k = 1
    for peak, xyz in zip(peaks_sorted, sites_sorted) :
      rg = create_atom(xyz, peak, k)
      peaks_chain.append_residue_group(rg)
      k += 1
    f = open(file_name, "w")
    f.write("REMARK  Interesting sites from mmtbx.find_peaks_holes\n")
    f.write("REMARK  Chain A is mFo-DFc peaks (> %g sigma)\n" % self.map_cutoff)
    if (include_holes) :
      f.write("REMARK  Chain B is mFo-DFc holes (< -%g sigma)\n" %
        (- self.map_cutoff))
      holes_chain = iotbx.pdb.hierarchy.chain(id="B")
      model.append_chain(holes_chain)
      selection = flex.sort_permutation(self.holes.heights)
      holes_sorted = self.holes.heights.select(selection)
      sites_sorted = self.holes.sites.select(selection)
      k = 1
      for hole, xyz in zip(holes_sorted, sites_sorted) :
        rg = create_atom(xyz, hole, k)
        holes_chain.append_residue_group(rg)
        k += 1
    if (include_anom) and (self.anom_peaks is not None) :
      f.write("REMARK  Chain C is anomalous peaks (> %g sigma)\n" %
        self.anom_map_cutoff)
      anom_chain = iotbx.pdb.hierarchy.chain(id="C")
      model.append_chain(anom_chain)
      selection = flex.sort_permutation(self.anom_peaks.heights, reverse=True)
      anom_sorted = self.anom_peaks.heights.select(selection)
      sites_sorted = self.anom_peaks.sites.select(selection)
      k = 1
      for peak, xyz in zip(anom_sorted, sites_sorted) :
        rg = create_atom(xyz, peak, k)
        anom_chain.append_residue_group(rg)
        k += 1
    f.write(root.as_pdb_string())
    f.close()
    print >> log, "Wrote %s" % file_name

class water_peak (object) :
  def __init__ (self, id_str, xyz, peak_height, map_type="mFo-DFc") :
    adopt_init_args(self, locals())

  def show (self, out=sys.stdout) :
    print >> out, "  %s  map_type=%s  peak=%g" % (self.id_str,
      self.map_type, self.peak_height)

def find_peaks_holes (
    fmodel,
    pdb_hierarchy,
    params,
    map_cutoff=3.0,
    anom_map_cutoff=3.0,
    out=None) :
  """
  Find peaks and holes in mFo-DFc map, plus flag solvent atoms with
  suspiciously high mFo-DFc values, plus anomalous peaks if anomalous data are
  present.  Returns a pickle-able object storing all this information (with
  the ability to write out a PDB file with the sites of interest).
  """
  if (out is None) : out = sys.stdout
  pdb_atoms = pdb_hierarchy.atoms()
  unit_cell = fmodel.xray_structure.unit_cell()
  from mmtbx import find_peaks
  from cctbx import maptbx
  make_header("Positive difference map peaks", out=out)
  peaks_result = find_peaks.manager(
    fmodel=fmodel,
    map_type="mFo-DFc",
    map_cutoff=map_cutoff,
    params=params,
    log=out)
  peaks_result.peaks_mapped()
  peaks_result.show_mapped(pdb_atoms)
  peaks = peaks_result.peaks()
  # XXX very important - sites are initially fractional coordinates!
  peaks.sites = unit_cell.orthogonalize(peaks.sites)
  print >> out, ""
  make_header("Negative difference map holes", out=out)
  holes_result = find_peaks.manager(
    fmodel=fmodel,
    map_type="mFo-DFc",
    map_cutoff=-map_cutoff,
    params=params,
    log=out)
  holes_result.peaks_mapped()
  holes_result.show_mapped(pdb_atoms)
  holes = holes_result.peaks()
  holes.sites = unit_cell.orthogonalize(holes.sites)
  print >> out, ""
  anom = None
  if (fmodel.f_obs().anomalous_flag()) :
    make_header("Anomalous difference map peaks", out=out)
    anom_result = find_peaks.manager(
      fmodel=fmodel,
      map_type="anomalous",
      map_cutoff=anom_map_cutoff,
      params=params,
      log=out)
    anom_result.peaks_mapped()
    anom_result.show_mapped(pdb_atoms)
    anom = anom_result.peaks()
    anom.sites = unit_cell.orthogonalize(anom.sites)
    print >> out, ""
  cache = pdb_hierarchy.atom_selection_cache()
  water_isel = cache.selection("resname HOH").iselection()
  waters_out = [None, None]
  if (len(water_isel) > 0) :
    sites_frac = fmodel.xray_structure.sites_frac()
    map_types = ["mFo-DFc"]
    if (fmodel.f_obs().anomalous_flag()) :
      map_types.append("anomalous")
    for k, map_type in enumerate(map_types) :
      fft_map = fmodel.electron_density_map().fft_map(
        resolution_factor=params.resolution_factor,
        symmetry_flags=maptbx.use_space_group_symmetry,
        map_type=map_type,
        use_all_data=True)
      fft_map.apply_sigma_scaling()
      real_map = fft_map.real_map_unpadded()
      suspicious_waters = []
      for i_seq in water_isel :
        atom = pdb_atoms[i_seq]
        rho = real_map.tricubic_interpolation(sites_frac[i_seq])
        if (rho >= map_cutoff) :
          peak = water_peak(
            id_str=atom.id_str(),
            xyz=atom.xyz,
            peak_height=rho,
            map_type=map_type)
          suspicious_waters.append(peak)
      if (len(suspicious_waters) > 0) :
        make_header("Water molecules with %s peaks" % map_type, out=out)
        for peak in suspicious_waters :
          peak.show(out=out)
        print >> out, ""
        waters_out[k] = suspicious_waters
  all_results = peaks_holes_container(
    peaks=peaks,
    holes=holes,
    anom_peaks=anom,
    map_cutoff=map_cutoff,
    anom_map_cutoff=anom_map_cutoff,
    water_peaks=waters_out[0],
    water_anom_peaks=waters_out[1])
  all_results.show_summary(out=out)
  return all_results

def run (args, out=None) :
  if (out is None) : out = sys.stdout
  if (len(args) == 0) :
    phil_out = StringIO()
    master_phil.show(f=phil_out)
    raise Usage("""
mmtbx.find_peaks_holes - difference map analysis
  Prints a summary of all peaks and holes above the specified cutoff in the
  mFo-DFc map, and flag any water molecules with suspiciously high peaks
  (possible ions).  Will also check the anomalous map if available.

%s""" % phil_out.getvalue())
  cmdline = utils.cmdline_load_pdb_and_data(
    args=args,
    master_phil=master_phil,
    out=out,
    process_pdb_file=False,
    create_fmodel=True)
  result = find_peaks_holes(
    fmodel=cmdline.fmodel,
    pdb_hierarchy=cmdline.pdb_hierarchy,
    params=cmdline.params.find_peaks,
    map_cutoff=cmdline.params.map_cutoff,
    anom_map_cutoff=cmdline.params.anom_map_cutoff,
    out=out)
  if (cmdline.params.write_pdb) :
    result.save_pdb_file(log=out)
  return result

if (__name__ == "__main__") :
  run(sys.argv[1:])
