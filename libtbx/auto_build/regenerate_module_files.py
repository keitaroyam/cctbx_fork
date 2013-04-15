#!/usr/bin/python

from __future__ import division
from optparse import OptionParser
from installer_utils import *
import os
import sys

def run (args, out=sys.stdout) :
  if (sys.platform == "darwin") :
    print >> out, "This script is only applicable to Linux - exiting."
    return
  parser = OptionParser(
    description="Generate new config files for various third-party modules "+
      "required for the graphical interface (if any).")
  parser.add_option("--build_dir", dest="build_dir", action="store",
    help="CCTBX build directory", default=os.getcwd())
  options, args = parser.parse_args(args)
  build_dir = options.build_dir
  base_dir = os.path.join(build_dir, "base")
  if (not os.path.exists(base_dir)) :
    raise OSError("Base directory '%s' does not exist." % base_dir)
  #--- Pango
  pango_dir = os.path.join(base_dir, "etc", "pango")
  if (os.path.isdir(pango_dir)) :
    # pangorc
    print >> out, "generating pangorc file"
    open(os.path.join(pango_dir, "pangorc"), "w").write("""
#
# Auto-generated by CCTBX or PHENIX installer, do not change
#
#
[Pango]
ModuleFiles = %s/etc/pango/pango.modules

[PangoX]
AliasFiles = %s/etc/pango/pangox.aliases
""" % (base_dir, base_dir))
    # pango.modules
    print >> out, "generating pango.modules file"
    call(("%s/bin/pango-querymodules %s/lib/pango/1.6.0/modules/*.so > "+
          "%s/pango.modules") % (base_dir, base_dir, pango_dir), log=out)
  else : # XXX should this raise an exception?
    print >> out, "%s not present, could not regenerate pango files" % \
      pango_dir
  #--- Gtk+
  gtk_dir = os.path.join(base_dir, "etc", "gtk-2.0")
  if (os.path.isdir(gtk_dir)) :
    # gtk.immodules
    print >> out, "generating gtk.immodules file"
    call(("%s/bin/gtk-query-immodules-2.0 %s/lib/gtk-2.0/2.10.0/immodules/*.so"
          + "> %s/etc/gtk-2.0/gtk.immodules") % (base_dir, base_dir, base_dir),
          log=out)
    # gdk-pixbuf.loaders
    print >> out, "generating gdk-pixbuf.loaders file"
    call(("%s/bin/gdk-pixbuf-query-loaders %s/lib/gtk-2.0/2.10.0/loaders/*.so"+
          " > %s/etc/gtk-2.0/gdk-pixbuf.loaders") % (base_dir, base_dir,
            base_dir), log=out)
  else :
    print >> out, "%s not present, could not regenerate gdk-pixbuf.loaders" %\
      gtk_dir
  #--- Fonts
  fonts_share_dir = os.path.join(base_dir, "share", "fonts")
  fonts_etc_dir = os.path.join(base_dir, "etc", "fonts")
  if (os.path.isdir(fonts_etc_dir)) :
    print >> out, "updating fonts/local.conf file"
    fonts_in = open(os.path.join(fonts_share_dir, "local.conf.in"))
    fonts_out = open(os.path.join(fonts_etc_dir, "local.conf"), "w")
    for line in fonts_in.readlines() :
      fonts_out.write(line.replace("FONTCONFIG_PATH", fonts_share_dir))
    fonts_out.close()
    print >> out, "running mkfontdir"
    call("mkfontscale %s" % fonts_share_dir, log=out)
    call("mkfontdir %s" % fonts_share_dir, log=out)
    print >> out, "rebuilding font cache"
    call("fc-cache -v %s" % fonts_share_dir, log=out)
  else :
    print >> out, "%s not present, could not rebuild fonts" % fonts_etc_dir
  #--- Themes
  share_dir = os.path.join(base_dir, "share")
  if (os.path.isdir(share_dir)) :
    print >> out, "generating index.theme file"
    hicolor_dir = os.path.join(share_dir, "icons", "hicolor")
    if (not os.path.isdir(hicolor_dir)) :
      os.makedirs(hicolor_dir)
    open(os.path.join(hicolor_dir, "index.theme"), "w").write("""
#
# Auto-generated by PHENIX installer, do not change'
#
[Icon Theme]
Name=Hicolor
Comment=Fallback icon theme
Hidden=true
Directories=48x48/filesystems

[48x48/filesystems]
Size=48
Context=FileSystems
Type=Threshold
""")
  else :
    print "problem with installation, could not make index.theme file"

if (__name__ == "__main__") :
  run(sys.argv[1:])
