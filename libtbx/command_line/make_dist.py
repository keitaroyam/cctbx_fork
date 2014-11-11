
"""
Master script for making distributable installers on Linux and Mac.
"""

from __future__ import division
from libtbx.auto_build.installer_utils import *
import libtbx.phil.command_line
import libtbx.load_env
from optparse import OptionParser
import shutil
import os.path as op
import time
import os
import sys

master_phil_str = """
product_name = CCTBX
  .type = str
pkg_prefix = cctbx
  .type = str
hide_mac_package_contents = False
  .type = bool
installer_script = cctbx_project/libtbx/auto_build/plus_installer.py
  .type = path
license = cctbx_project/libtbx/LICENSE_2_0.txt
  .type = path
background = None
  .type = path
bin_dir = None
  .type = path
readme = None
  .type = path
source_module = None
  .type = str
  .multiple = True
base_module = None
  .type = str
  .multiple = True
exclude_build_module = None
  .type = str
  .multiple = True
organization = gov.lbl.cci
  .type = str
"""

def run (args) :
  parser = OptionParser()
  parser.add_option("--tmp-dir", dest="tmp_dir", action="store",
    help="Temporary directory for assembling packages", default=None)
  parser.add_option("--debug", dest="debug", action="store_true")
  parser.add_option("--destination", dest="destination", action="store",
    help="Destination directory for rsync", default=None)
  parser.add_option("--mac-pkg-contents", dest="mac_pkg_contents",
    action="store", help="Location of Mac installation in /Applications",
    default=None)
  parser.add_option("--mtype", dest="mtype", action="store",
    help="Architecture type", default=machine_type())
  parser.add_option("--host-tag", dest="host_tag", action="store",
    help="Host tag (OS/distribution label)", default=None)
  parser.add_option("--version", dest="version", action="store",
    help="Package version",
    default=time.strftime("%Y_%m_%d", time.localtime()))
  parser.add_option("--remove_src", dest="remove_src")
  # TODO installer background?
  options, args = parser.parse_args(args)
  if (len(args) == 0) :
    # XXX defaults for CCTBX installer if no parameter file specified
    args = [
      "source_module=cbflib",
      "source_module=annlib",
      "source_module=cbflib_adaptbx",
      "exclude_build_module=phenix_regression",
      "exclude_build_module=phenix_dev",
      "exclude_build_module=chem_data",
    ]
  phil_cmdline = libtbx.phil.command_line.process(
    args=args,
    master_string=master_phil_str)
  params = phil_cmdlline.work.extract()
  print "This will be %s-%s" % (params.package_name, options.version)
  root_dir = op.dirname(op.dirname(libtbx.env.find_in_repositories(
    relative_path="cctbx_project",
    test=op.isdir)))
  print "Root directory is %s" % root_dir
  modules_dir = op.join(root_dir, "modules")
  build_dir = op.join(root_dir, "build")
  base_dir = op.join(root_dir, "base")
  if (not (op.isdir(modules_dir) and op.isdir(build_dir) and
           op.isdir(base_dir))) :
    raise RuntimeError(
      "Expected 'modules', 'build', and 'base' in root directory")
  if (options.tmp_dir is None) :
    options.tmp_dir = op.join(root_dir, "tmp")
  if (not op.isdir(options.tmp_dir)) :
    os.makedirs(options.tmp_dir)
  print "temporary directory is %s" % options.tmp_dir
  os.chdir(options.tmp_dir)
  installer_dir = "%s-installer-%s" % (params.pkg_prefix, options.version)
  if op.exists(installer_dir) :
    shutil.rmtree(installer_dir)
  installer_tar = installer_dir + "-" + options.host_tag + ".tar.gz"
  def full_path (path_name) :
    if op.isabs(path_name) :
      return path_name
    else :
      path_name_ = libtbx.env.find_in_repositories(
        relative_path=path_name,
        test=op.isfile)
      if (path_name_ is None) :
        raise RuntimeError("Can't find path %s" % path_name)
      return path_name_
  # setup basic installer directory
  setup_args = [
    "--version=%s" % options.version,
    "--binary",
    "--script=%s"%full_path(params.installer_script),
    "--product_name=%s" % params.product_name,
    "--pkg_dir=%s" % modules_dir,
  ]
  if (len(params.readme_files) > 0) :
    for readme in params.readme_files :
      setup_args.append("--readme=%s" % full_path(readme))
  if (len(params.base_modules) > 0) :
    setup_args.append("--base-modules=%s" % ",".join(params.base_modules))
  if (params.license) :
    setup_args.append("--license=%s" % full_path(params.license))
  print "Arguments for setup_installer.py:"
  for arg_ in setup_args :
    print "  %s" % arg_
  setup_installer.run(args=setup_args + [ params.pkg_prefix ])
  assert op.isdir(installer_dir), installer_dir
  bundle_dir = op.join(options.tmp_dir, installer_dir, "bundles")
  os.mkdir(bundle_dir)
  # create bundles of base, build, and module directories
  bundle_args = [
    "--dest=%s" % bundle_dir,
    "--version=%s" % options.version,
    #"--verbose",
  ]
  if (len(params.exclude_build_modules) > 0) :
    for module in params.exclude_build_modules :
      bundle_args.append("--ignore=%s" % module)
  if (len(params.base_modules) > 0) :
    for module in params.base_modules :
      bundle_args.append("--ignore=%s" % module)
  print "Arguments for make_bundle.py:"
  for arg_ in bundle_args :
    print "  %s" % arg_
  make_bundle.run(args=bundle_args + [ builder_dir ])
  # package the entire mess into the complete installer
  find_and_delete_files(installer_dir, file_ext=".pyc")
  os.chdir(options.tmp_dir)
  tar_prefix = installer_dir
  suffix = ""
  if (options.host_tag is not None) :
    suffix = options.host_tag
  else :
    suffix = options.mtype
  if (suffix != "") :
    tar_name += "-" + suffix
  installer_tar = tar_prefix + ".tar.gz"
  call("tar czf %s %s" % (installer_tar, installer_dir))
  print "Wrote %s" % installer_tar
  # 
  # Mac .pkg creation
  if (sys.platform == "darwin") :
    os.chdir(installer_dir)
    pkg_prefix = "/Applications"
    app_root_dir = pkg_prefix + "/" + "%s-%s" % (params.pkg_prefix,
      options.version)
    if params.hide_mac_package_contents :
      app_root_dir = "/Applications/%s-%s" %(params.package_name,
        options.version)
      pkg_prefix = app_root_dir + "/Contents"
      os.makedirs(pkg_prefix)
    call("./install --prefix=%s --compact --no-app" % pkg_prefix)
    create_mac_pkg.run(args=[
      "--package_name=%s" % params.package_name,
      "--version=%s" % options.version,
      "--license=%s" % full_path(params.license),
      "--organization=%s "% params.organization,
      "--machine_type=%s" % suffix,
      app_root_dir,
    ])
    installer_pkg = "%s-%s-%s.pkg.zip" % (params.package_name.lower(),
      options.version, options.h
    if (options.destination is not None) :
      call("rsync -avz %s %s" % (installer_pkg, options.destination))
  # rsync and cleanup
  remove_installer = False
  if (options.destination is not None) :
    call("rsync -avz %s %s" % (installer_tar, options.destination))
    remove_installer = True
  if (not options.debug) :
    shutil.rmtree(installer_dir)
    if remove_installer :
      shutil.rmtree(installer_tar)
  return 0

if (__name__ == "__main__") :
  sys.exit(run(sys.argv[1:]))
