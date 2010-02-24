
import os, sys
import libtbx.phil
from libtbx.phil import interface
from libtbx.utils import Sorry
from libtbx import easy_pickle

def exercise () :
  master_phil = libtbx.phil.parse("""
refinement {
  input {
    pdb {
      file_name = None
        .type = path
        .multiple = True
    }
  }
  refine {
    strategy = *individual_sites *individual_adp *occupancies tls rigid_body
      .type = choice(multi=True)
    adp {
      tls = None
        .type = str
        .multiple = True
        .help = Selection for TLS group
    }
  }
  main {
    ncs = False
      .type = bool
      .help = This turns on NCS restraints
    ordered_solvent = False
      .type = bool
    number_of_macro_cycles = 3
      .type = int
    ias = False
      .type = bool
  }
  ncs {
    restraint_group
      .multiple = True
      .optional = True
      .short_caption = Restraint group
    {
      reference = None
        .type = str
        .help = Reference selection for restraint group
      selection = None
        .type = str
        .multiple = True
        .optional = False
        .help = Restrained selection
    }
  }
}
""")
  refine_phil1 = libtbx.phil.parse("""
refinement {
  input {
    pdb {
      file_name = protein.pdb
      file_name = ligand.pdb
    }
  }
  refine {
    adp {
      tls = "chain A"
      tls = "chain B"
    }
  }
  main {
    ncs = True
    ordered_solvent = True
  }
  ncs {
    restraint_group {
      reference = "chain A"
      selection = "chain B"
      selection = "chain C"
      selection = "chain D"
    }
  }
}
""")
  refine_phil2_str = """
refinement {
  input {
    pdb {
      file_name = model1.pdb
    }
  }
  main {
    ncs = True
    ordered_solvent = False
  }
  ncs {
    restraint_group {
      reference = "chain A"
      selection = "chain B"
    }
    restraint_group {
      reference = "chain C"
      selection = "chain D"
    }
  }
}"""
  refine_phil3 = libtbx.phil.parse("refinement.main.number_of_macro_cycles=5")
  refine_phil4_str = """
refinement.refine.adp.tls = None
refinement.ncs.restraint_group {
  reference = "chain C and resseq 1:100"
  selection = "chain D and resseq 1:100"
}"""
  i = libtbx.phil.interface.index(master_phil=master_phil,
                                  working_phil=refine_phil1)
  params = i.get_python_object()
  assert len(params.refinement.ncs.restraint_group) == 1
  i.update(refine_phil2_str)
  # object retrieval
  ncs_phil = i.get_scope_by_name("refinement.ncs.restraint_group")
  assert len(ncs_phil) == 2
  pdb_phil = i.get_scope_by_name("refinement.input.pdb.file_name")
  assert len(pdb_phil) == 1
  os_phil = i.get_scope_by_name("refinement.main.ordered_solvent")
  assert os_phil.full_path() == "refinement.main.ordered_solvent"
  os_param = os_phil.extract()
  assert os_param == False
  params = i.get_python_object()
  assert len(params.refinement.refine.adp.tls) == 2
  # more updating, object extraction
  i.merge_phil(phil_object=refine_phil3)
  params = i.get_python_object()
  assert len(params.refinement.ncs.restraint_group) == 2
  assert params.refinement.main.ncs == True
  assert params.refinement.main.ordered_solvent == False
  assert params.refinement.main.number_of_macro_cycles == 5
  assert params.refinement.input.pdb.file_name == ["model1.pdb"]
  i.merge_phil(phil_string=refine_phil4_str)
  params = i.get_python_object()
  assert len(params.refinement.refine.adp.tls) == 0
  phil1 = libtbx.phil.parse("""refinement.refine.strategy = *tls""")
  phil2 = libtbx.phil.parse("""refinement.input.pdb.file_name = ligand2.pdb""")
  i.save_param_file(
    file_name="tst_params.eff",
    sources=[phil1, phil2],
    extra_phil="refinement.main.ias = True",
    diff_only=True)
  params = i.get_python_from_file("tst_params.eff")
  assert params.refinement.refine.strategy == ["tls"]
  assert params.refinement.input.pdb.file_name == ["model1.pdb","ligand2.pdb"]
  assert params.refinement.main.ias == True
  i2 = i.copy(preserve_changes=False)
  params2 = i2.get_python_object()
  assert not params2.refinement.main.ncs
  i3 = i.copy(preserve_changes=True)
  params3 = i3.get_python_object()
  assert params3.refinement.main.ncs == True

  # text searching (we can assume this will break quickly, but easily checked
  # by uncommenting the print statements)
  names = i.search_phil_text("Restraint group", match_all=True,
    labels_only=True)
  assert len(names) == 0
  names = i.search_phil_text("Restraint group", match_all=True,
    labels_only=False)
  assert len(names) == 3
  names = i.search_phil_text("selection group", match_all=True,
    labels_only=False)
  assert len(names) == 3

  assert (libtbx.phil.interface.get_adjoining_phil_path(
    "refinement.input.xray_data.file_name", "labels") ==
    "refinement.input.xray_data.labels")
  print "OK"

if __name__ == "__main__" :
  exercise()

#---end
