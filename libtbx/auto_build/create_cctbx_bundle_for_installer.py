#!/usr/bin/python

"""
Package the CCTBX bundle used for various installers (Phenix, etc.) using
sources in the specified repositories directory.
"""

from __future__ import division
import optparse
import os.path as op
import time
import os
import sys
from installer_utils import *

def run (args) :
  datestamp = time.strftime("%Y_%m_%d", time.localtime())
  parser = optparse.OptionParser()
  parser.add_option("--tag", dest="tag", action="store",
    help="Bundle identifier", default=datestamp)
  parser.add_option("--ignore-missing", dest="ignore_missing", action="store",
    help="Skip missing secondary packages", default=False)
  parser.add_option("--require-all", dest="require_all", action="store",
    help="Require all listed packages, even optional ones", default=False)
  parser.add_option("--tmp", dest="tmp_dir", action="store",
    help="Temporary directory", default=os.getcwd())
  parser.add_option("--tarfile", dest="tarfile", action="store",
    help="Output tarfile name", default="cctbx_bundle_for_installer.tar.gz")
  parser.add_option("--dest", dest="destination", action="store",
    help="Final destination for tarfile", default=None)
  options, args = parser.parse_args(args)
  if (len(args) == 1) :
    repositories = op.abspath(args[0])
  else :
    assert (len(args) == 0)
    repositories = op.dirname(op.dirname(op.dirname(op.dirname(__file__))))
  print "Using '%s' as repository directory" % repositories
  assert op.isdir(repositories)
  assert (repositories != op.abspath(options.tmp_dir))
  os.chdir(options.tmp_dir)
  if op.exists("cctbx_tmp") :
    shutil.rmtree("cctbx_tmp")
  os.mkdir("cctbx_tmp")
  os.chdir("cctbx_tmp")
  # Packages that are absolutely required for CCTBX installation
  required = [
    "boost",
    "cctbx_project",
    "scons",
  ]
  # Strongly recommended, but not essential
  recommended = [
    "cbflib",
    "ccp4io",
    "ccp4io_adaptbx",
  ]
  # Provided if available, but not especially important
  optional = [
    "clipper",
    "tntbx",
    "gui_resources",
    "lapack_fem",
    "opt_resources",
  ]
  # create tag file
  open("cctbx_bundle_TAG", "w").write(options.tag)
  have_modules = ["cctbx_bundle_TAG"]
  # copy over directories
  for module_name in required :
    module_path = op.join(repositories, module_name)
    if (not op.isdir(module_path)) :
      raise OSError("Essential module '%s' not found in %s!" % (module_name,
        repositories))
    print "Copying %s..." % module_path
    archive_dist(module_path, create_tarfile=False)
    have_modules.append(module_name)
  # recommended modules - can be skipped if necessary
  for module_name in recommended :
    module_path = op.join(repositories, module_name)
    if (not op.isdir(module_path)) :
      if (options.ignore_missing) :
        warnings.warn(("Skipping recommended module '%s' (not found in "+
          "repositories directory %s)") % (module_name, repositories))
        continue
      else :
        raise OSError(("Recommended module '%s' not found in %s!  If you want "+
          "to continue without this module, re-run with --ignore-missing.") %
          (module_name, repositories))
    print "Copying %s..." % module_path
    archive_dist(module_path, create_tarfile=False)
    have_modules.append(module_name)
  # optional
  for module_name in optional :
    module_path = op.join(repositories, module_name)
    if (not op.isdir(module_path)) :
      if (not options.require_all) :
        warnings.warn(("Skipping optional module '%s' (not found in "+
          "repositories directory %s)") % (module_name, repositories))
        continue
      else :
        raise OSError(("Required module '%s' not found in %s!  If you want "+
          "to continue without this module, re-run without --require-all.") %
          (module_name, repositories))
    print "Copying %s..." % module_path
    archive_dist(module_path, create_tarfile=False)
    have_modules.append(module_name)
  # create the archive
  call("tar -cvzf %s %s" % (options.tarfile, " ".join(have_modules)),
    log=sys.stdout)
  print "Wrote %s" % options.tarfile
  if (options.destination is not None) :
    assert op.isdir(options.destination)
    shutil.move(options.tarfile, options.destination)
  # cleanup
  os.chdir(options.tmp_dir)
  shutil.rmtree("cctbx_tmp")

if (__name__ == "__main__") :
  run(sys.argv[1:])
