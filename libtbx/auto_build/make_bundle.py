#!/usr/bin/python

"""
Create a "bundle" (.tar.gz) of all Python modules and compiled code in a
product.  The target directory is expected to look something like this:

CCTBX-<version>/
CCTBX-<version>/build/
CCTBX-<version>/build/<mtype>/
CCTBX-<version>/build/<mtype>/base/
CCTBX-<version>/build/<mtype>/lib/
CCTBX-<version>/cctbx_project/

plus any number of module directories in the top level.  The resulting bundle
will be named bundle-<version>-<mtype>.tar.gz.

Since the base modules take an especially long time to compile, they are now
part of a separate bundle.  This will allow re-use of precompiled base packages
with the latest source, which should speed up installer generation.
"""

from __future__ import division
from optparse import OptionParser
from cStringIO import StringIO
import os.path as op
import shutil
import time
import os
import sys
# local imports
# XXX HACK
libtbx_path = op.abspath(op.dirname(op.dirname(op.dirname(__file__))))
if (not libtbx_path in sys.path) :
  print libtbx_path
  sys.path.append(libtbx_path)
from libtbx.auto_build.installer_utils import *
from libtbx.auto_build import rpath


def run (args, out=sys.stdout) :
  datestamp = time.strftime("%Y_%m_%d", time.localtime())
  parser = OptionParser()
  parser.add_option("--tmp_dir", dest="tmp_dir", action="store",
    help="Temporary staging directory", default=os.getcwd())
  parser.add_option("--version", dest="version", action="store",
    help="Version number or code", default=datestamp)
  parser.add_option("--mtype", dest="mtype", action="store",
    help="Architecture type", default=machine_type())
  parser.add_option("--ignore", dest="ignore", action="store",
    help="Subdirectories to ignore", default="")
  parser.add_option("--remove_src", dest="remove_src", action="store",
    help="Remove compiled source files (.h, .cpp, etc.)", default=False)
  parser.add_option("--keep_base", dest="keep_base", action="store",
    help="Keep base packages with main bundle", default=False)
  parser.add_option("--dest", dest="dest", action="store",
    help="Destination directory for bundle tarfiles", default=None)
  options, args = parser.parse_args(args)
  target_dir = args[0]
  assert op.isdir(target_dir), target_dir
  os.chdir(options.tmp_dir)
  pkg_dir = op.basename(target_dir)
  build_dir = op.join(target_dir, "build", options.mtype)
  print >> out, "Setting rpath in shared libraries..."
  stdout_old = sys.stdout
  sys.stdout = StringIO()
  rpath.run([build_dir])
  sys.stdout = stdout_old
  # create temp dir
  tmp_dir = op.join(options.tmp_dir, "%s_tmp" % pkg_dir)
  assert op.isdir(build_dir), build_dir
  if op.exists(tmp_dir) :
    shutil.rmtree(tmp_dir)
  os.mkdir(tmp_dir)
  os.chdir(tmp_dir)
  # copy over non-compiled files
  print >> out, "Copying base modules..."
  ignore_dirs = options.ignore.split(",")
  for file_name in os.listdir(target_dir) :
    if (file_name == "build") or (file_name in ignore_dirs) :
      continue
    full_path = op.join(target_dir, file_name)
    if op.isdir(full_path) :
      print >> out, "  copying %s..." % file_name
      copy_tree(full_path, op.join(tmp_dir, file_name))
  # build directory
  tmp_build_dir = op.join(tmp_dir, "build", options.mtype)
  os.makedirs(tmp_build_dir)
  for dir_name in ["lib", "base"] :
    full_path = op.join(build_dir, dir_name)
    assert op.isdir(full_path)
    copy_tree(full_path, op.join(tmp_build_dir, dir_name))
  # remove unnecessary base directories/files
  for dir_name in [
      "base/bin/gtk-demo",
      "base/man",
      "base/doc",
      "base/info",
      "base/share/gtk-doc",
      "base/share/locale",
    ] :
    full_path = op.join(tmp_build_dir, dir_name)
    if op.exists(full_path) :
      shutil.rmtree(full_path)
  # XXX what about base/include?
  # copy over build executable directories
  for file_name in os.listdir(build_dir) :
    full_path = op.join(build_dir)
    if op.isdir(full_path) :
      module_name = file_name
      for file_name in os.listdir(full_path) :
        if (file_name == "exe") :
          copy_tree(op.join(full_path, file_name),
                    op.join(tmp_build_dir, module_name, file_name))
  # delete unnecessary files
  find_and_delete_files(tmp_dir, file_ext=".pyc")
  find_and_delete_files(tmp_dir, file_ext=".o")
  find_and_delete_files(tmp_dir, file_ext=".pyo")
  find_and_delete_files(tmp_dir, file_name=".sconsign")
  find_and_delete_files(tmp_dir, file_name="CVS")
  find_and_delete_files(tmp_dir, file_name=".svn")
  if (options.remove_src) :
    find_and_delete_files(tmp_dir, file_ext=".cpp")
    find_and_delete_files(tmp_dir, file_ext=".hpp")
    find_and_delete_files(tmp_dir, file_ext=".cc")
    find_and_delete_files(tmp_dir, file_ext=".c")
    find_and_delete_files(tmp_dir, file_ext=".h")
  # TODO strip objects?
  os.chdir(tmp_dir)
  # create base bundle
  if (not options.keep_base) :
    base_dir = op.join("build", options.mtype, "base")
    base_tarfile = "../base-%(version)s-%(mtype)s.tar.gz" % \
      {"version":options.version, "mtype":options.mtype}
    call("tar -czf %(tarfile)s %(base)s" %
      {"tarfile":base_tarfile, "base":base_dir}, log=out)
    shutil.rmtree(base_dir)
    assert op.isfile(base_tarfile)
    if (options.dest is not None) :
      shutil.move(base_tarfile, options.dest)
      base_tarfile = op.join(options.dest, op.basename(base_tarfile))
    print >> out, "  created base bundle %s" % base_tarfile
  # create the product bundle
  pkg_tarfile = "../bundle-%(version)s-%(mtype)s.tar.gz" % \
    {"version":options.version, "mtype":options.mtype}
  call("tar -czf %(tarfile)s ." % {"tarfile":pkg_tarfile}, log=out)
  assert op.isfile(pkg_tarfile)
  if (options.dest is not None) :
    shutil.move(pkg_tarfile, options.dest)
    pkg_tarfile = op.join(options.dest, op.basename(pkg_tarfile))
  print >> out, "  created bundle %s" % pkg_tarfile
  shutil.rmtree(tmp_dir)

if (__name__ == "__main__") :
  run(sys.argv[1:])
