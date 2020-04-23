#This file is NOT licensed under the GPLv3, which is the license for the rest
#of YouCompleteMe.
#
#Here's the license text for this file:
#
#This is free and unencumbered software released into the public domain.
#
#Anyone is free to copy, modify, publish, use, compile, sell, or
#distribute this software, either in source code form or as a compiled
#binary, for any purpose, commercial or non - commercial, and by any
#means.
#
#In jurisdictions that recognize copyright laws, the author or authors
#of this software dedicate any and all copyright interest in the
#software to the public domain.We make this dedication for the benefit
#of the public at large and to the detriment of our heirs and
#successors.We intend this dedication to be an overt act of
#relinquishment in perpetuity of all present and future rights to this
#software under copyright law.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
#OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#OTHER DEALINGS IN THE SOFTWARE.
#
#For more information, please refer to < http:  // unlicense.org/>

from distutils.sysconfig import get_python_inc
import platform
import os
import subprocess
import ycm_core
import logging
import shlex
import json
from jsonmerge import merge

#FORMAT = '%(asctime)-15s %(message)s'
#logging.basicConfig(filename='/tmp/ycm.log', format=FORMAT, level=logging.INFO)
logger = logging.getLogger('ycm-extra-conf')

#These are the compilation flags that will be used in case there's no
#compilation database set(by default, one is not set).
#CHANGE THIS LIST OF FLAGS.YES, THIS IS THE DROID YOU HAVE BEEN LOOKING FOR.
flags = [
'-Wall',
'-Wextra',
'-Werror',
'-Wno-long-long',
'-Wno-variadic-macros',
'-fexceptions',
'-DNDEBUG',
#You 100 % do NOT need - \
#        DUSE_CLANG_COMPLETER and / # or \ DYCM_EXPORT in your flags;
#only the YCM source code needs it.
'-DUSE_CLANG_COMPLETER',
'-DYCM_EXPORT=',
#THIS IS IMPORTANT !Without the '-x' flag, Clang won't know which language to
#use when compiling headers.So it will guess.Badly.So C++ headers will be
#compiled as C headers.You don 't want that so ALWAYS specify the ' - x' flag.
#For a C project, you would set this to 'c' instead of 'c++'.
'-x',
'c++',
'-isystem',
'../BoostParts',
'-isystem',
'../llvm/include',
'-isystem',
'../llvm/tools/clang/include',
'-I',
'.',
'-I',
'./ClangCompleter',
'-isystem',
'./tests/gmock/gtest',
'-isystem',
'./tests/gmock/gtest/include',
'-isystem',
'./tests/gmock',
'-isystem',
'./tests/gmock/include',
'-isystem',
'./benchmarks/benchmark/include',
]

#Clang automatically sets the '-std=' flag to 'c++14' for MSVC 2015 or later,
#which is required for compiling the standard library, and to 'c++11' for older
#versions.
if platform.system() != 'Windows':
  flags.append( '-std=c++11' )

#Set this to the absolute path to the folder(NOT the file !) containing the
#compile_commands.json file to use that instead of 'flags'.See here for
#more details : http:  // clang.llvm.org/docs/JSONCompilationDatabase.html
#
#You can get CMake to generate this file for you by adding:
#set(CMAKE_EXPORT_COMPILE_COMMANDS 1)
#to your CMakeLists.txt file.
#
#Most projects will NOT need to set this to anything; you can just change the
#'flags' list of compilation flags.Notice that YCM itself uses that approach.
compilation_database_folder = '/home/test/path/to/your/compdb/'

SOURCE_EXTENSIONS = [ '.cpp', '.cxx', '.cc', '.c', '.m', '.mm' ]


def ParseNinjaRules( compdb_folder ):
  parent = os.path.abspath(os.path.join(compdb_folder, os.pardir))
  logger.debug("Parent %s", parent)
  # For this project there are multiple destination folders containing the
  # rules.ninja file, they all follow a pattern of having appl on their names
  lsdir = [appl for appl in next(os.walk(parent))[1] if 'appl' in appl]
  if not os.path.exists(compdb_folder):
    os.makedirs( compdb_folder )
   
  complete = []

  for folder in lsdir:
    build = '{}/{}'.format(parent, folder)
    rules = f"{build}/rules.ninja"
    if os.path.isfile(rules):
        awk = 'awk \'/^rule (C|CXX)_COMPILER__/ {{ print $2 }}\' {build}/rules.ninja'.format(build=build)
        output = subprocess.check_output(shlex.split(awk), stderr=subprocess.STDOUT)
        output = output.replace(b'\n', b' ')
        cmd = 'ninja -C {b} -t compdb -t query {ak}'.format(b=build, ak=output.decode())
        jsonbytes = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)
        jsonlist = json.loads(jsonbytes)#.decode())
        for item in jsonlist:
            complete.append(item)


  finalout = '{}/{}'.format(compdb_folder, 'compile_commands.json')
  with open(finalout, "w") as outfile:
    json.dump(complete, outfile, sort_keys=True, indent=2, separators=(',', ':'))

ParseNinjaRules(compilation_database_folder)
if os.path.exists( compilation_database_folder ):
  database = ycm_core.CompilationDatabase( compilation_database_folder )
else:
  database = None

def DirectoryOfThisScript():
  return os.path.dirname( os.path.abspath( __file__ ) )


def IsHeaderFile( filename ):
  extension = os.path.splitext( filename )[ 1 ]
  return extension in [ '.h', '.hxx', '.hpp', '.hh' ]


def GetCompilationInfoForFile( filename ):
#The compilation_commands.json file generated by CMake does not have entries
#for header files.So we do our best by asking the db for flags for a
#corresponding source file, if any.If one exists, the flags for that file
#should be good enough.
  if IsHeaderFile( filename ):
    basename = os.path.splitext( filename )[ 0 ]
    for extension in SOURCE_EXTENSIONS:
      replacement_file = basename + extension
      if os.path.exists( replacement_file ):
        compilation_info = database.GetCompilationInfoForFile(
          replacement_file )
        if compilation_info.compiler_flags_:
          return compilation_info
    return None
  return database.GetCompilationInfoForFile( filename )


def FlagsForFile( filename, **kwargs ):
  if not database:
    return {
      'flags': flags,
      'include_paths_relative_to_dir': DirectoryOfThisScript()
    }

  compilation_info = GetCompilationInfoForFile( filename )
  if not compilation_info:
    return None

#Bear in mind that compilation_info.compiler_flags_ does NOT return a
#python list, but a "list-like" StringVec object.
  final_flags = list( compilation_info.compiler_flags_ )

#NOTE : This is just for YouCompleteMe; it's highly likely that your project
#does NOT need to remove the stdlib flag.DO NOT USE THIS IN YOUR
#ycm_extra_conf IF YOU'RE NOT 100% SURE YOU NEED IT.
  try:
    final_flags.remove('-stdlib=libc++')
  except ValueError:
      pass

  return{
    'flags' : final_flags,
    'include_paths_relative_to_dir' : compilation_info.compiler_working_dir_,
  }
