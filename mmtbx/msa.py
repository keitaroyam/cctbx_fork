
from libtbx import easy_run
import libtbx.phil
import libtbx.load_env
from libtbx.utils import Sorry
from libtbx import adopt_init_args
import os
import sys

# XXX this is more complex than ideal, in order to support long and
# potentially problematic "sequence names", which in some applications will
# actually be file paths + chain IDs.  to ensure that MUSCLE doesn't choke
# on these, the option is given to substitute numerical sequence names
# internally, while still allowing retrieval using the original names.
class align_pdb_residues (object) :
  def __init__ (self,
                pdb_sequences,
                pdb_names,
                pdb_offsets,
                reference_sequence=None,
                reference_sequence_name="sequence",
                reference_sequence_offset=0,
                reference_index=None,
                substitute_names=False) :
    adopt_init_args(self, locals())
    n_models = len(pdb_sequences)
    assert ((n_models >= 1) and (n_models==len(pdb_names)==len(pdb_offsets)))
    use_pdb_sequence = False
    self.fasta_names = []
    self._name_lookup = None
    # build index of sequence names given to MUSCLE
    if substitute_names :
      self._name_lookup = {}
      for i, name in enumerate(pdb_names) :
        self._name_lookup[name] = str(i)
        self.fasta_names.append(str(i))
    else :
      self.fasta_names = pdb_names
    # determine sequence for reference numbering
    if (reference_sequence is not None) :
      assert (reference_index is None)
    else :
      use_pdb_sequence = True
      if (reference_index is None) :
        reference_index = 0
      reference_sequence = pdb_sequences[reference_index]
      reference_sequence_offset = pdb_offsets[reference_index]
      if substitute_names :
        reference_sequence_name = self.fasta_names[reference_index]
      else :
        reference_sequence_name = pdb_names[reference_index]
    fasta = "\n".join([ ">%s\n%s" % (n,s) for n,s in zip(self.fasta_names,
                        pdb_sequences) ])
    if (not use_pdb_sequence) :
      ref_seq_fasta = ">%s\n%s" % (reference_sequence_name, reference_sequence)
      fasta = ref_seq_fasta + "\n" + fasta
    self.muscle_aln = get_muscle_alignment(fasta)
    assert (self.muscle_aln is not None)
    # find sequences and determine equivalent numbering
    self._lookup_table = {}
    i_ref = self.muscle_aln.names.index(reference_sequence_name)
    self._reference_alignment = self.muscle_aln.alignments[i_ref]
    assert (i_ref is not None)
    for i, name in enumerate(self.muscle_aln.names) :
      if (i == i_ref) :
        self._lookup_table[name] = None
      else :
        i_pdb = self.fasta_names.index(name)
        aln = self.muscle_aln.alignments[i]
        j = k = 0
        new_resseqs = []
        for res1, res2 in zip(aln, self._reference_alignment) :
          if (res2 != '-') :
            k += 1
          if (res1 == '-') :
            continue
          else :
            if (res2 == '-') :
              new_resseqs.append(None)
            else :
              new_resseqs.append(k - reference_sequence_offset)
            j += 1
        assert (j == len(new_resseqs))
        self._lookup_table[name] = new_resseqs

  def write_file (self, file_name) :
    f = open(file_name, "w")
    f.write(str(self.muscle_aln))
    f.close()

  def get_name_index (self, pdb_name) :
    if (self._name_lookup is not None) :
      return self._name_lookup[pdb_name]
    else :
      return pdb_name
      #return self.pdb_names.index(pdb_name)

  def convert_residue_number (self, pdb_name, resseq) :
    seq_name = self.get_name_index(pdb_name)
    assert isinstance(resseq, int)
    if (self._lookup_table[seq_name] is None) :
      return resseq
    i_pdb = self.pdb_names.index(pdb_name)
    offset = self.pdb_offsets[i_pdb]
    i_res = resseq + offset - 1
    try :
      return self._lookup_table[seq_name][i_res]
    except IndexError, e :
      raise RuntimeError("""\
Encountered IndexError attempting to convert residue number!
Values:
  pdb_name = %s
  resseq = %s
  seq_name = %s
  i_res = %s

Dump of full alignment:
  %s
""" % (pdb_name, resseq, seq_name, i_res, self.muscle_aln))

def run_muscle (fasta_sequences, group_sequences=True) :
  assert group_sequences # XXX this isn't actually optional!
  if not libtbx.env.has_module(name="muscle") :
    raise RuntimeError("MUSCLE not available or not configured.")
  exe_path = libtbx.env.under_build("muscle/exe/muscle")
  if (os.name == "nt") :
    exe_path += ".exe"
  if (not os.path.isfile(exe_path)) :
    raise RuntimeError("muscle executable is not available.")
  assert isinstance(fasta_sequences, str)
  cmd = "%s -quiet -clw" % exe_path
  if group_sequences :
    cmd += " -group"
  #else :
  #  cmd += " -stable"
  muscle_out = easy_run.fully_buffered(cmd,
    stdin_lines=fasta_sequences)
  return muscle_out.stdout_lines

def get_muscle_alignment (fasta_sequences, group_sequences=True) :
  muscle_out = run_muscle(fasta_sequences, group_sequences)
  from iotbx.bioinformatics import clustal_alignment_parse
  alignment, null = clustal_alignment_parse("\n".join(muscle_out))
  return alignment

########################################################################
# PHENIX GUI ADAPTOR
master_phil = libtbx.phil.parse("""
muscle
  .caption = PHENIX includes the open-source multiple sequence alignment \
    program MUSCLE, written by Bob Edgar.  It can produce output identical in \
    format to CLUSTALW, which is suitable for input to the Sculptor model \
    preparation program.  You may provide all sequences in a single file, \
    or in as many different files as desired.  Alternately, you may provide \
    one or more PDB files from which the chain sequence(s) will be extracted \
    (note however that this is only useful for homogenous models).
  .style = caption_img:icons/custom/msa64.png caption_width:480
{
  seq_file = None
    .type = path
    .multiple = True
    .short_caption = Sequence file
    .style = file_type:seq,pdb use_list
  output_file = None
    .type = path
    .style = bold file_type:aln new_file
  load_in_text_editor = True
    .type = bool
    .short_caption = Open alignment in text editor when complete
}""")

def run (args=(), params=None, out=sys.stdout) :
  assert (params is not None)
  seq_files = params.muscle.seq_file
  output_file = params.muscle.output_file
  if (output_file is None) or (output_file == "") :
    output_file = os.path.join(os.getcwd(), "muscle.aln")
  from iotbx import file_reader
  from iotbx.bioinformatics import any_sequence_format, sequence
  seqs = []
  for file_name in seq_files :
    if (file_name.endswith(".pdb") or file_name.endswith(".ent") or
        file_name.endswith(".pdb.gz") or file_name.endswith(".ent.gz")) :
      pdb_in = file_reader.any_file(file_name, force_type="pdb").file_object
      hierarchy = pdb_in.construct_hierarchy()
      first_model = hierarchy.models()[0]
      found_protein = False
      for chain in first_model.chains() :
        first_conf = chain.conformers()[0]
        if first_conf.is_protein() :
          chain_seq = first_conf.as_padded_sequence()
          base_name = os.path.basename(file_name)
          seq_name = "%s_%s" % (os.path.splitext(base_name)[0], chain.id)
          seqs.append(sequence(chain_seq, seq_name))
          found_protein = True
      if (not found_protein) :
        raise Sorry(("The PDB file %s does not contain any recognizable "+
          "protein chains.") % file_name)
    else :
      try :
        seq_objects, non_compliant = any_sequence_format(file_name,
          assign_name_if_not_defined=True)
        seqs.extend(seq_objects)
      except Exception, e :
        raise Sorry(("Error parsing '%s' - not a recognizable sequence "+
          "format.  (Original message: %s)") % (file_name, str(e)))
  if (len(seqs) < 2) :
    raise Sorry("Need at least two valid sequences to run MUSCLE.")
  combined = "\n".join([ seq.format(80) for seq in seqs ])
  muscle_out = run_muscle(combined)
  open(output_file, "w").write("\n".join(muscle_out))
  return (output_file, "\n".join(muscle_out))

def validate_params (params) :
  if (len(params.muscle.seq_file) == 0) :
    raise Sorry("No sequence files provided!")
