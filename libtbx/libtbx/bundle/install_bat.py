import sys

def create_script(bundle, top_modules):
  py_major, py_minor = sys.version_info[:2]
  return r"""\
@echo off

echo Build tag:
type %(bundle)s_sources\TAG

echo Trying to find Python:
set python=python
call %%python%% -V
if %%errorlevel%% == 0 goto have_python
set python=C:\python%(py_major)d%(py_minor)d\python
call %%python%% -V
if %%errorlevel%% == 0 goto have_python
echo.
echo Cannot find Python. Stop.
echo.
goto end

:have_python
echo.
echo Configuring %(bundle)s build directory
cd %(bundle)s_build
call %%python%% ..\%(bundle)s_sources\libtbx\configure.py %(top_modules)s
set el=%%errorlevel%%
cd ..
if not %%el%% == 0 goto end
call %(bundle)s_build\setpaths.bat

echo.
echo Running a selected test
call python "%%SCITBX_DIST%%\lbfgs\boost_python\tst_lbfgs.py"
if not %%errorlevel%% == 0 goto end

echo.
echo ***
echo *** To use this installation in a new shell or process run the command:
echo ***
echo ***     %%LIBTBX_BUILD%%\setpaths.bat
echo ***
echo *** You may want to add this line to some startup file.
echo ***

:end
pause
""" % vars()

if (__name__ == "__main__"):
  assert len(sys.argv) == 3
  sys.stdout.write(create_script(sys.argv[1], sys.argv[2]))
