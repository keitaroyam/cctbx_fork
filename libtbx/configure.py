import sys, os, os.path, pprint
from os.path import normpath, join, abspath, dirname, isdir
norm = normpath

class UserError(Exception): pass

class empty: pass

class registry:

  def __init__(self):
    self.dict = {}
    self.list = []

  def append(self, key, value):
    self.dict[key] = value
    self.list.append(key)

  def insert(self, position, key, value):
    self.dict[key] = value
    self.list.insert(position, key)

  def merge(self, other):
    i = 0
    for name in other.list:
      if (not name in self.dict):
        self.insert(i, name, other.dict[name])
        i += 1

class package:

  def __init__(self, dist_root, name):
    self.dist_root = dist_root
    self.name = name
    self.dist_path = norm(join(dist_root, name))
    if (not isdir(self.dist_path)):
      raise UserError("Not a package directory: " + self.dist_path)
    config_path = norm(join(self.dist_path, "libtbx_config"))
    try:
      f = open(config_path)
    except:
      self.config = None
    else:
      try:
        self.config = eval(" ".join(f.readlines()))
      except:
        raise UserError("Corrupt file: " + config_path)
    self._build_dependency_registry()

  def _build_dependency_registry(self):
    self.dependency_registry = registry()
    self._resolve_dependencies(self.dependency_registry)

  def _resolve_dependencies(self, registry):
    if (self.name in registry.dict):
      raise UserError("Dependency cycle detected: "
        + str(registry.list) + " + " + self.name)
    registry.append(self.name, self)
    if (self.config != None):
      for required_package_name in self.config["required_packages"]:
        package(self.dist_root, required_package_name)._resolve_dependencies(
          registry)

def insert_normed_path(path_list, addl_path):
  addl_path = norm(addl_path)
  if (not addl_path in path_list):
    i = 0
    if (path_list[:1] == ["."]): i = 1
    path_list.insert(i, addl_path)

class libtbx_info:

  def __init__(self, env):
    self.LD_LIBRARY_PATH = [norm(join(env.libtbx_build, "libtbx"))]
    self.PYTHONPATH = [norm(join(env.libtbx_build, "libtbx")), env.libtbx_dist]
    self.PATH = [norm(join(env.libtbx_dist, "libtbx/command_line")),
                 norm(join(env.libtbx_build, "libtbx/bin"))]
    self.LIBTBX_BUILD = env.libtbx_build
    self.LIBTBX_DIST = env.libtbx_dist
    self.LIBTBX_PYTHON_EXE = norm(abspath(sys.executable))

  def update(self, package):
    self.__dict__[package.name.upper() + "_DIST"] = package.dist_path
    insert_normed_path(
      self.PYTHONPATH, package.dist_path)
    insert_normed_path(
      self.PATH, join(package.dist_path, package.name, "command_line"))

def open_info(path, mode="w", info="Creating:"):
  print info, path
  return open(path, mode)

def emit_env_run_sh(libtbx_build, libtbx_info):
  env_run_sh_path = norm(join(libtbx_build, "env_run.sh"))
  f = open_info(env_run_sh_path)
  for var_name, values in libtbx_info.items():
    if (var_name.upper() != var_name): continue
    if (type(values) == type([])):
      val = os.pathsep.join(values)
      print >> f, 'if [ ! -n "$%s" ]; then' % (var_name,)
      print >> f, '  %s=""' % (var_name,)
      print >> f, 'fi'
      print >> f, '%s="%s%s$%s"' % (var_name, val, os.pathsep, var_name)
    else:
      print >> f, '%s="%s"' % (var_name, values)
    print >> f, 'export %s' % (var_name,)
  print >> f, '$LIBTBX_PYTHON_EXE "$LIBTBX_DIST/libtbx/command_line/env_run.py" $*'
  f.close()
  os.chmod(env_run_sh_path, 0755)

def emit_setpaths_csh(libtbx_build, libtbx_info):
  setpaths_csh_path = norm(join(libtbx_build, "setpaths.csh"))
  f = open_info(setpaths_csh_path)
  for var_name, values in libtbx_info.items():
    if (var_name.upper() != var_name): continue
    if (var_name == "LD_LIBRARY_PATH" and sys.platform.startswith("darwin")):
      var_name = "DYLD_LIBRARY_PATH"
    if (type(values) == type([])):
      val = os.pathsep.join(values)
      print >> f, 'if (! $?%s) then' % (var_name,)
      print >> f, '  setenv %s ""' % (var_name,)
      print >> f, 'endif'
      print >> f, 'setenv %s "%s%s$%s"' % (var_name, val, os.pathsep, var_name)
    else:
      print >> f, 'setenv %s "%s"' % (var_name, values)
  f.close()

def join_path_ld_library_path(libtbx_info):
  joined_path = libtbx_info["PATH"]
  for path in libtbx_info["LD_LIBRARY_PATH"]:
    if (not path in joined_path):
      joined_path.append(path)
  return joined_path

def emit_setpaths_bat(libtbx_build, libtbx_info):
  setpaths_bat_path = norm(join(libtbx_build, "setpaths.bat"))
  f = open_info(setpaths_bat_path)
  print >> f, '@ECHO off'
  for var_name, values in libtbx_info.items():
    if (var_name.upper() != var_name): continue
    if (type(values) == type([])):
      if (var_name == "LD_LIBRARY_PATH"): continue
      if (var_name == "PATH"):
        values = join_path_ld_library_path(libtbx_info)
      val = os.pathsep.join(values)
      print >> f, 'if not defined %s set %s=' % (var_name, var_name)
      print >> f, 'set %s=%s%s%%%s%%' % (var_name, val, os.pathsep, var_name)
    else:
      print >> f, 'set %s=%s' % (var_name, values)
  print >> f, 'if not defined PATHEXT set PATHEXT='
  print >> f, 'set PATHEXT=.PY;%PATHEXT%'
  f.close()

def emit_SConstruct(env, libtbx_info):
  package_list = env.packages.list[:]
  package_list.reverse()
  SConstruct_path = norm(join(env.libtbx_build, "SConstruct"))
  f = open_info(SConstruct_path)
  print >> f, 'import os, os.path'
  print >> f, 'norm = os.path.normpath'
  print >> f, 'assert norm(os.getcwd()) == norm(os.environ["LIBTBX_BUILD"])'
  print >> f, 'Repository(r"%s")' % (env.dist_root,)
  print >> f, 'try:'
  print >> f, '  CScanSetFlags('
  print >> f, '    python=0,'
  for package_name in package_list:
    flag = 1
    if (package_name == "boost"): flag = 0
    print >> f, '    %s=%d,' % (package_name, flag)
  print >> f, '  )'
  print >> f, 'except:'
  print >> f, '  pass'
  print >> f, '#SetContentSignatureType("timestamp")'
  print >> f, 'SConscript("libtbx/SConscript")'
  print >> f, '''\

def use_SConscript_if_present(package_name):
  dist = os.environ[package_name.upper() + "_DIST"]
  if (os.path.isfile(dist + "/SConscript")):
    SConscript(package_name + "/SConscript")
'''
  for package_name in package_list:
    print >> f, 'use_SConscript_if_present("%s")' % package_name
  f.close()

def run(args):
  env = empty()
  env.libtbx_build = norm(abspath(os.getcwd()))
  env.libtbx_dist = norm(dirname(norm(abspath(args[0]))))
  env.dist_root = norm(dirname(env.libtbx_dist))
  env.packages = registry()
  for arg in args[1:]:
    env.packages.merge(package(env.dist_root, arg).dependency_registry)
  if (len(env.packages.list) == 0):
    print "Error: At least one package must be specified."
    return
  info = libtbx_info(env)
  print "Top-down list of all packages involved:"
  for package_name in env.packages.list:
    print " ", package_name
    info.update(env.packages.dict[package_name])
  if (hasattr(os, "symlink")):
    emit_env_run_sh(env.libtbx_build, info.__dict__)
    emit_setpaths_csh(env.libtbx_build, info.__dict__)
  else:
    emit_setpaths_bat(env.libtbx_build, info.__dict__)
  emit_SConstruct(env, info)

if (__name__ == "__main__"):
  try:
    run(sys.argv)
  except UserError, e:
    print "Error:", e
