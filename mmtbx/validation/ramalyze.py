from __future__ import division
# (jEdit options) :folding=explicit:collapseFolds=1:

#{{{ coot_script_header
coot_script_header = """
def molprobity_fascinating_clusters_things_gui(window_name, sorting_option, cluster_list):

    ncluster_max = 75

    # a callback function
    def callback_recentre(widget, x, y, z):
        set_rotation_centre(x, y, z)

    # utility function
    def add_feature_buttons(feature_list, cluster_vbox):
        frame = gtk.Frame("Ramachandran Outliers")
        vbox = gtk.VBox(False, 0)
        cluster_vbox.pack_start(frame, False, False, 2)
        frame.add(vbox)

        # add buttons to vbox for each feature
        #
        for feature in feature_list:
            # print "feature: ", feature
            button = gtk.Button(feature[0])
            button.connect("clicked",
                           callback_recentre,
                           feature[4],
                           feature[5],
                           feature[6])
            vbox.pack_start(button, False, False, 1)

    # main body
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    scrolled_win = gtk.ScrolledWindow()
    outside_vbox = gtk.VBox(False, 2)
    inside_vbox = gtk.VBox(False, 0)

    print "Maximum number of clusters displayed:  ", ncluster_max

    window.set_default_size(300, 200)
    window.set_title(window_name)
    inside_vbox.set_border_width(2)
    window.add(outside_vbox)
    outside_vbox.pack_start(scrolled_win, True, True, 0) # expand fill padding
    scrolled_win.add_with_viewport(inside_vbox)
    scrolled_win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)

    count = 0

    for cluster_info in cluster_list:

        if (count == ncluster_max):
            break
        else:
            frame = gtk.Frame()
            vbox = gtk.VBox(False, 2)

            frame.set_border_width(6)
            frame.add(vbox)
            inside_vbox.pack_start(frame, False, False, 10)

            # now we have a list of individual features:
            features = cluster_info[0]
            if (len(features) > 0):
                add_feature_buttons(features, vbox)

    outside_vbox.set_border_width(2)
    ok_button = gtk.Button("  Close  ")
    outside_vbox.pack_end(ok_button, False, False, 0)
    ok_button.connect("clicked", lambda x: window.destroy())
    window.show_all()

molprobity_fascinating_clusters_things_gui(
    "MolProbity Multi-Chart",
    [],
    [[
      [
"""
#}}}

import sys, os
from mmtbx.validation import utils
import mmtbx.rotamer
from mmtbx.rotamer import ramachandran_eval
from mmtbx.rotamer import graphics
import libtbx.phil
from libtbx.utils import Usage

def get_master_phil():
  return libtbx.phil.parse(
    input_string="""
    ramalyze {
      pdb = None
        .type = path
        .help = '''Enter a PDB file name'''

      outliers_only = False
      .type = bool
      .help = '''Only print Ramachandran outliers'''

      verbose = True
      .type = bool
      .help = '''Verbose'''

      plot = False
        .type = bool
        .help = Create graphics of plots (if Matplotlib is installed)
}
""")

header = """residue:score%:phi:psi:evaluation:type"""

class ramalyze(object):

  #{{{ flag routines
  #flag routines-----------------------------------------------------------------------------------
  def usage(self):
    return """
phenix.ramalyze file.pdb [params.eff] [options ...]

Options:

  pdb=input_file        input PDB file
  outliers_only=False   only print outliers
  verbose=False         verbose text output
  plot=False            Create graphics of plots (if Matplotlib is installed)

Example:

  phenix.ramalyze pdb=1ubq.pdb outliers_only=True

"""
  def get_summary_and_header(self,command_name):
    header="\n"
    header+="\n#                       "+str(command_name)
    header+="\n#"
    header+="\n# Analyze protein backbone ramachandran"
    header+="\n# type phenix."+str(command_name)+": --help for help"

    summary= "phenix.%s mypdb.pdb" % command_name
    return summary,header


  #------------------------------------------------------------------------------------------------
  #}}}

  #{{{ run
  def run(self, args, out=sys.stdout, quiet=False):
    if (len(args) == 0 or "--help" in args or "--h" in args or "-h" in args):
      raise Usage(self.usage())
    master_phil = get_master_phil()
    import iotbx.utils
    args = list(args)
    for i, arg in enumerate(args) :
      if (arg == "--plot") :
        args[i] = "ramalyze.plot=True"
    input_objects = iotbx.utils.process_command_line_inputs(
      args=args,
      master_phil=master_phil,
      input_types=("pdb",))
    work_phil = master_phil.fetch(sources=input_objects["phil"])
    work_params = work_phil.extract()
    if len(input_objects["pdb"]) != 1:
      summary, header = self.get_summary_and_header("ramalyze")
      raise Usage(summary)
    file_obj = input_objects["pdb"][0]
    filename = file_obj.file_name

    command_name = "ramalyze"
    summary,header=self.get_summary_and_header(command_name)
    if not quiet: print >>out, header

    #TO DO:  make this a working help section
    #if help or (params and params.ramalyze.verbose):
    #  pass
      # XXX: disabled for GUI
      #print "Values of all params:"
      #master_params.format(python_object=params).show(out=out)

    self.params=work_params # makes params available to whole class

    log=out
    if (log is None): log = sys.stdout
    if filename and os.path.exists(filename):
      try:
        import iotbx.pdb
      except ImportError:
        print "iotbx not loaded"
        return None, None
      pdb_io = iotbx.pdb.input(filename)
    else:
      print "Please enter a file name"
      return None, None

    output_text, output_list = self.analyze_pdb(pdb_io,
      outliers_only=self.params.ramalyze.outliers_only)
    out_count, out_percent = self.get_outliers_count_and_fraction()
    fav_count, fav_percent = self.get_favored_count_and_fraction()
    if self.params.ramalyze.verbose:
      print >> out, "residue:score%:phi:psi:evaluation:type"
      print >> out, output_text
      print >> out, 'SUMMARY: %.2f%% outliers (Goal: %s)' % \
        (out_percent*100, self.get_outliers_goal())
      print >> out, 'SUMMARY: %.2f%% favored (Goal: %s)' % \
        (fav_percent*100, self.get_favored_goal())
    todo_list = self.coot_todo(output_list)
    self.out_percent = out_percent * 100.0
    self.fav_percent = fav_percent * 100.0
    if (self.params.ramalyze.plot) :
      print >> out, ""
      print >> out, "Creating images of plots..."
      base_name = os.path.basename(filename)
      file_base = os.path.splitext(base_name)[0]
      for pos in ["general", "glycine", "cis-proline", "trans-proline",
                  "pre-proline", "isoleucine or valine"] :
        stats = utils.get_rotarama_data(
          pos_type=pos,
          convert_to_numpy_array=True)
        plot_file_name = file_base + "_rama_%s.png" % pos
        graphics.draw_ramachandran_plot(
          ramalyze_data=output_list,
          rotarama_data=stats,
          position_type=pos,
          file_name=plot_file_name)
        print >> out, "  wrote %s" % plot_file_name
    return output_list, todo_list
  #}}}

  #{{{ analyze_pdb
  def analyze_pdb(self, pdb_io=None, hierarchy=None, outliers_only=None):
    assert [pdb_io, hierarchy].count(None) == 1
    if(pdb_io is not None):
      hierarchy = pdb_io.construct_hierarchy()
    use_segids = utils.use_segids_in_place_of_chainids(
                   hierarchy=hierarchy)
    analysis = ""
    output_list = []
    self.numoutliers = 0
    self.numallowed = 0
    self.numfavored = 0
    self.numgen = 0
    self.numgly = 0
    self.numcispro = 0
    self.numtranspro = 0
    self.numprepro = 0
    self.numileval = 0
    self.numtotal = 0
    r = ramachandran_eval.RamachandranEval()
    prev_rezes, next_rezes = None, None
    prev_resid = None
    cur_resseq = None
    next_resseq = None
    for model in hierarchy.models():
      for chain in model.chains():
        if use_segids:
          chain_id = utils.get_segid_as_chainid(chain=chain)
        else:
          chain_id = chain.id
        residues = list(chain.residue_groups())
        for i, residue_group in enumerate(residues):
          # The reason I pass lists of atom_groups to get_phi and get_psi is to
          # deal with the particular issue where some residues have an A alt
          # conf that needs some atoms from a "" alt conf to get calculated
          # correctly.  See 1jxt.pdb for examples.  This way I can search both
          # the alt conf atoms and the "" atoms if necessary.
          prev_atom_list, next_atom_list, atom_list = None, None, None
          if cur_resseq is not None:
            prev_rezes = rezes
            prev_resseq = cur_resseq
          rezes = self.construct_complete_residues(residues[i])
          cur_resseq = residue_group.resseq_as_int()
          cur_icode = residue_group.icode.strip()
          if (i > 0):
            #check for insertion codes
            if (cur_resseq == residues[i-1].resseq_as_int()) :
              if (cur_icode == '') and (residues[i-1].icode.strip() == '') :
                continue
            elif (cur_resseq != (residues[i-1].resseq_as_int())+1):
              continue
          if (i < len(residues)-1):
            #find next residue
            if residue_group.resseq_as_int() == \
               residues[i+1].resseq_as_int():
              if (cur_icode == '') and (residues[i+1].icode.strip() == '') :
                continue
            elif residue_group.resseq_as_int() != \
               (residues[i+1].resseq_as_int())-1:
              continue
            next_rezes = self.construct_complete_residues(residues[i+1])
            next_resid = residues[i+1].resseq_as_int()
          else:
            next_rezes = None
            next_resid = None
          for atom_group in residue_group.atom_groups():
            alt_conf = atom_group.altloc
            if rezes is not None:
              atom_list = rezes.get(alt_conf)
            if prev_rezes is not None:
              prev_atom_list = prev_rezes.get(alt_conf)
              if (prev_atom_list is None):
                prev_keys = sorted(prev_rezes.keys())
                prev_atom_list = prev_rezes.get(prev_keys[0])
            if next_rezes is not None:
              next_atom_list = next_rezes.get(alt_conf)
              if (next_atom_list is None):
                next_keys = sorted(next_rezes.keys())
                next_atom_list = next_rezes.get(next_keys[0])
            phi = self.get_phi(prev_atom_list, atom_list)
            psi = self.get_psi(atom_list, next_atom_list)
            coords = self.get_center(atom_group)
            if (phi is not None and psi is not None):
              resType = None
              self.numtotal += 1
              if (atom_group.resname[0:3] == "GLY"):
                resType = "glycine"
                self.numgly += 1
              elif (atom_group.resname[0:3] == "PRO"):
                is_cis = self.is_cis_peptide(prev_atom_list, atom_list)
                if is_cis:
                  resType = "cis-proline"
                  self.numcispro += 1
                else:
                  resType = "trans-proline"
                  self.numtranspro += 1
              elif (self.isPrePro(residues, i)):
                resType = "pre-proline"
                self.numprepro += 1
              elif (atom_group.resname[0:3] == "ILE" or \
                    atom_group.resname[0:3] == "VAL"):
                resType = "isoleucine or valine"
                self.numileval += 1
              else:
                resType = "general"
                self.numgen += 1

              value = r.evaluate(resType, [phi, psi])
              ramaType = self.evaluateScore(resType, value)
              if (not outliers_only or self.isOutlier(resType, value)):
                analysis += '%s%5s %s%s:%.2f:%.2f:%.2f:%s:%s\n' % \
                  (chain_id,
                   residue_group.resid(),atom_group.altloc,
                   atom_group.resname,
                   value*100,
                   phi,
                   psi,
                   ramaType,
                   resType.capitalize())

                output_list.append([chain_id,
                                    residue_group.resid(),
                                    atom_group.altloc+atom_group.resname,
                                    value*100,
                                    phi,
                                    psi,
                                    ramaType,
                                    resType.capitalize(),
                                    coords])
    return analysis.rstrip(), output_list
  #}}}

  #{{{ coot_todo
  def coot_todo(self, output_list):
    #print coot_script_header
    text=coot_script_header
    for chain_id,resnum,resname,rama_value,phi,psi,ramaType,resType,coords in output_list:
       if (coords is not None):
         button='       ["Ramachandran Outlier at %s%s %s (%.2f)", 0, 1, 0, %f, %f, %f],\n' % \
           (chain_id, resnum, resname, rama_value, coords[0], coords[1], coords[2])
         #print button
         text+=button
    text+="      ]\n"
    text+="     ]\n"
    text+="    ])\n"
    #print text
    return text
  #}}}

  #{{{ get_matching_atom_group
  def get_matching_atom_group(self, residue_group, altloc):
    match = None
    if (residue_group != None):
      for ag in residue_group.atom_groups():
        if (ag.altloc == "" and match == None): match = ag
        if (ag.altloc == altloc): match = ag
    return match
  #}}}

  #{{{ get_phi
  def get_phi(self, prev_atoms, atoms):
    prevC, resN, resCA, resC = None, None, None, None;
    if (prev_atoms is not None):
      for atom in prev_atoms:
        if (atom.name == " C  "): prevC = atom
    if (atoms is not None):
      for atom in atoms:
        if (atom.name == " N  "): resN = atom
        if (atom.name == " CA "): resCA = atom
        if (atom.name == " C  "): resC = atom
    if (prevC is not None and resN is not None and resCA is not None and resC is not None):
      return mmtbx.rotamer.phi_from_atoms(prevC, resN, resCA, resC)
  #}}}

  #{{{ get_psi
  def get_psi(self, atoms, next_atoms):
    resN, resCA, resC, nextN = None, None, None, None
    if (next_atoms is not None):
      for atom in next_atoms:
        if (atom.name == " N  "): nextN = atom
    if (atoms is not None):
      for atom in atoms:
        if (atom.name == " N  "): resN = atom
        if (atom.name == " CA "): resCA = atom
        if (atom.name == " C  "): resC = atom
    if (nextN is not None and resN is not None and resCA is not None and resC is not None):
      return mmtbx.rotamer.psi_from_atoms(resN, resCA, resC, nextN)
  #}}}

  #{{{ get_omega
  def get_omega(self, prev_atoms, atoms):
    prevCA, prevC, thisN, thisCA = None, None, None, None
    if (prev_atoms is not None):
      for atom in prev_atoms:
        if (atom.name == " CA "): prevCA = atom
        if (atom.name == " C  "): prevC = atom
    if (atoms is not None):
      for atom in atoms:
        if (atom.name == " N  "): thisN = atom
        if (atom.name == " CA "): thisCA = atom
    if (prevCA is not None and prevC is not None and thisN is not None and thisCA is not None):
      return mmtbx.rotamer.omega_from_atoms(prevCA, prevC, thisN, thisCA)

  #{{{is_cis_peptide
  def is_cis_peptide(self, prev_atoms, atoms):
    omega = self.get_omega(prev_atoms, atoms)
    if(omega > -30 and omega < 30):
      return True
    else:
      return False

  #{{{ construct_complete_residues
  def construct_complete_residues(self, res_group):
    if (res_group is not None):
      complete_dict = {}
      nit, ca, co, oxy = None, None, None, None
      atom_groups = res_group.atom_groups()
      reordered = []
      # XXX always process blank-altloc atom group first
      for ag in atom_groups :
        if (ag.altloc == '') :
          reordered.insert(0, ag)
        else :
          reordered.append(ag)
      for ag in reordered :
        changed = False
        for atom in ag.atoms():
          if (atom.name == " N  "): nit = atom
          if (atom.name == " CA "): ca = atom
          if (atom.name == " C  "): co = atom
          if (atom.name == " O  "): oxy = atom
          if (atom.name in [" N  ", " CA ", " C  ", " O  "]) :
            changed = True
        if (not None in [nit, ca, co, oxy]) and (changed) :
          # complete residue backbone found
          complete_dict[ag.altloc] = [nit, ca, co, oxy]
      if len(complete_dict) > 0:
        return complete_dict
    return None
  #}}}

  #{{{ get_center
  def get_center(self, ag):
    coords = None

    for atom in ag.atoms():
      if (atom.name == " CA "):
        coords = atom.xyz
    return coords
  #}}}

  #{{{ isPrePro
  def isPrePro(self, residues, i):
    if (i < 0 or i >= len(residues) - 1): return False
    else:
      next = residues[i+1]
      for ag in next.atom_groups():
        if (ag.resname[0:3] == "PRO"): return True
    return False
  #}}}

  #{{{ isOutlier
  def isOutlier(self, resType, value):
    if (resType == "general"):
      if (value < 0.0005): return True
      else: return False
    elif (resType == "cis-proline"):
      if (value < 0.0020): return True
      else: return False
    else:
      if (value < 0.0010): return True
      else: return False
  #}}}

  #{{{ evaluateScore
  def evaluateScore(self, resType, value):
    if (value >= 0.02):
      self.numfavored += 1
      return "Favored"
    if (resType == "general"):
      if (value >= 0.0005):
        self.numallowed += 1
        return "Allowed"
      else:
        self.numoutliers += 1
        return "OUTLIER"
    elif (resType == "cis-proline"):
      if (value >=0.0020):
        self.numallowed += 1
        return "Allowed"
      else:
        self.numoutliers += 1
        return "OUTLIER"
    else:
      if (value >= 0.0010):
        self.numallowed += 1
        return "Allowed"
      else:
        self.numoutliers += 1
        return "OUTLIER"
  #}}}

  #{{{ get functions
  def get_outliers_count_and_fraction(self):
    if (self.numtotal != 0):
      fraction = float(self.numoutliers)/self.numtotal
      assert fraction <= 1.0
      return self.numoutliers, fraction
    return 0, 0.

  def get_outliers_goal(self):
    return "< 0.2%"

  def get_allowed_count_and_fraction(self):
    if (self.numtotal != 0):
      fraction = float(self.numallowed)/self.numtotal
      assert fraction <= 1.0
      return self.numallowed, fraction
    return 0, 0.

  def get_allowed_goal(self):
    return "> 99.8%"

  def get_favored_count_and_fraction(self):
    if (self.numtotal != 0):
      fraction = float(self.numfavored)/self.numtotal
      assert fraction <= 1.0
      return self.numfavored, fraction
    return 0, 0.

  def get_favored_goal(self):
    return "> 98%"

  def get_general_count_and_fraction(self):
    if (self.numtotal != 0):
      fraction = (float(self.numgen)/self.numtotal)
      assert fraction <= 1.0
      return self.numgen, fraction
    return 0, 0.

  def get_gly_count_and_fraction(self):
    if (self.numtotal != 0):
      fraction = (float(self.numgly)/self.numtotal)
      assert fraction <= 1.0
      return self.numgly, fraction
    return 0, 0.

  def get_cis_pro_count_and_fraction(self):
    if (self.numtotal != 0):
      fraction = (float(self.numcispro)/self.numtotal)
      assert fraction <= 1.0
      return self.numcispro, fraction
    return 0, 0.

  def get_trans_pro_count_and_fraction(self):
    if (self.numtotal != 0):
      fraction = (float(self.numtranspro)/self.numtotal)
      assert fraction <= 1.0
      return self.numtranspro, fraction
    return 0, 0.

  def get_prepro_count_and_fraction(self):
    if (self.numtotal != 0):
      fraction = (float(self.numprepro)/self.numtotal)
      assert fraction <= 1.0
      return self.numprepro, fraction
    return 0, 0.

  def get_ileval_count_and_fraction(self):
    if (self.numtotal != 0):
      fraction = (float(self.numileval)/self.numtotal)
      assert fraction <= 1.0
      return self.numileval, fraction
    return 0, 0.

  def get_phi_psi_residues_count(self):
    # n.b. this function returns the number of residues that have a valid phi/psi pair.
    return self.numtotal
  #}}}
