#! /bin/csh -f

source "`libtbx.show_build_path`/setpaths_all.csh"
set echo

mkdir -p dist
cd dist
cp -r $LIBTBX_DIST .
cp -r $CCP4IO_DIST .
mkdir -p boost_adaptbx
cp -r $BOOST_ADAPTBX_DIST/boost boost_adaptbx
mkdir -p scitbx
cp -r $SCITBX_DIST/{scitbx,libtbx_config} scitbx
mkdir -p cctbx
cp -r $CCTBX_DIST/{cctbx,libtbx_config} cctbx
mkdir -p iotbx
cp -r $IOTBX_DIST/{iotbx,libtbx_config} iotbx
cd ..

if ($#argv == 0) then
  mkdir -p bintbx
  cd bintbx
  cp -r `libtbx.show_build_path`/libtbx .
  python ../dist/libtbx/configure.py iotbx
  cd ..
endif

echo '#! /bin/sh -f' > cctbx_web.cgi
echo "exec ./bintbx/bin/libtbx.env_run CCTBX_DIST cctbx/web/dispatcher.py" >> cctbx_web.cgi
chmod 755 cctbx_web.cgi

cp dist/cctbx/cctbx/web/*.html .
python dist/cctbx/cctbx/web/multiple_cell.py > multiple_cell.html
