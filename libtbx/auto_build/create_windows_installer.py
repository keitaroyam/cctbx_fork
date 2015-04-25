
# Script for compiling a Windows installer using the NSIS compiler which must be present on the PC.
# The main body of the script is immutable and stored in the file by the mainNSISscript variable
# Just a few custom definitions are prepended to this file which is subsequently compiled by as to
# create the Windows installer.



import shutil
import optparse
import os, sys, subprocess, platform



def WriteNSISpreamble(productname="Phenix",
                      version="dev-2015",
                      company="PHENIX Industrial Consortium",
                      website="http://www.phenix-online.org/",
                      sourcedir="phenix-installer-dev-2015-win_7_vc90",
                      tmpdir="tmp", # location of sourcedir
                      mainNSISscript = ""):

  # Makensis can only generate a 32bit installer.
  # Such an installer defaults all users program folders to "C:\program files (x86)"
  # regardless of architecture. If we have a 64 bit program we must specify all users program
  # folders to be "C:\program files" according to architecture.
  bitness = platform.architecture()[0][0:2]
  alluserprogfiles = "64"
  if not platform.architecture()[0] == '64bit':
    alluserprogfiles = ""

  NSIScustomdefs = """

  ; Custom definitions begin
  ; Written by libtbx\\auto_build\\create_windows_installer.WriteNSISpreamble()

  !define PRODUCT_NAME \"%s\"
  !define PRODUCT_VERSION \"%s\"
  !define PRODUCT_PUBLISHER \"%s\"
  !define PRODUCT_WEB_SITE \"%s\"
  !define SOURCEDIR \"%s\"
  !define COPYDIR \"%s\"
  !define IS_64_BIT_PROGRAM %s

  OutFile "${PRODUCT_NAME}-${PRODUCT_VERSION}-x%s-Setup.exe"

  ; Custom definitions end

  """ %(productname, version, company, website, sourcedir, tmpdir, alluserprogfiles, bitness)

  NSISmainbodytext = open(mainNSISscript,"r").read()
  NSISinstallerscript = NSIScustomdefs + NSISmainbodytext
  scriptname = os.path.join(tmpdir,"tmpinstscript.nsi")
  open(scriptname,"w").write(NSISinstallerscript)
  return scriptname


def run (args, out=sys.stdout) :
  if (sys.platform != "win32") :
    print >> out, "This application will only run on Windows systems."
    return 1
  parser = optparse.OptionParser(
    description="Utility for creating a Windows installer for the specified command, which must be present in %LIBTBX_BUILD%\\bin.")

  parser.add_option("--productname", dest="productname", action="store",
    help="Name of program", default="")
  parser.add_option("--versionstring", dest="version", action="store",
    help="version string of program", default="")
  parser.add_option("--company", dest="company", action="store",
    help="company producing the program", default="")
  parser.add_option("--website", dest="website", action="store",
    help="company website", default="")
  parser.add_option("--sourcedir", dest="sourcedir", action="store",
    help="name of source directory of program", default="")
  parser.add_option("--tmpdir", dest="tmpdir", action="store",
    help="location of source directory", default="")
  parser.add_option("--outdir", dest="outdir", action="store",
    help="directory where installer is being written to", default="")
  parser.add_option("--mainNSISscript", dest="mainNSISscript", action="store",
    help="main NSISscript to be prepended by the custom definitions", default="")

  options, args = parser.parse_args(args)
  print "Creating windows installer in", options.outdir
  print "Writing log file to", os.path.join(options.outdir, "MakeWindowsInstaller.log")
  #import code, traceback; code.interact(local=locals(), banner="".join( traceback.format_stack(limit=10) ) )
  scriptname = WriteNSISpreamble(options.productname, options.version,
                    options.company, options.website, options.sourcedir,
                    options.tmpdir, options.mainNSISscript)

  cmd = ["makensis", "/OMakeWindowsInstaller.log", "/NOCD", "/V4", scriptname]
  print "args= ", str(cmd)
  try:
    p = subprocess.Popen(
      cmd,
      cwd=options.outdir,
      stdout=sys.stdout,
      stderr=sys.stderr
    )
  except Exception, e:
    raise e
  p.wait()
  if p.returncode != 0:
    raise RuntimeError, "create_windows_installer() failed with return code %s"%(p.returncode)

  print "Windows installer stored in", options.outdir



if (__name__ == "__main__") :
  sys.exit(run(sys.argv[1:]))
