# LIBTBX_PRE_DISPATCHER_INCLUDE_SH PHENIX_GUI_ENVIRONMENT=1
# LIBTBX_PRE_DISPATCHER_INCLUDE_SH export PHENIX_GUI_ENVIRONMENT

if (__name__ == "__main__"):
  from rstbx.simage.wx_display import run
  import sys
  run(args=sys.argv[1:])
