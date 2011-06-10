# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 Pawel Szostek (pawel.szostek@cern.ch)
#
#    This source code is free software; you can redistribute it
#    and/or modify it in source code form under the terms of the GNU
#    General Public License as published by the Free Software
#    Foundation; either version 2 of the License, or (at your option)
#    any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA
#

from dep_solver import IDependable 
import os
import msg as p

class File(object):
        def __init__(self, path):
                self.path = path
        @property
        def name(self):
            return os.path.basename(self.path)
        @property
        def purename(self):
            return os.path.splitext(self.name)[0]
        @property
        def dirname(self):
            return os.path.dirname(self.path)
        
        def rel_path(self, dir=None):
            import path
            if dir == None:
                dir = os.getcwd()
            return path.relpath(self.path, dir)

        def __str__(self):
                return self.path

        def __eq__(self, other):
                _NOTFOUND = object()
                v1, v2 = [getattr(obj, "path", _NOTFOUND) for obj in [self, other]] 
                if v1 is _NOTFOUND or v2 is _NOTFOUND:
                    return False
                elif v1 != v2:
                    return False
                return True

        def __hash__(self):
                return hash(self.path)

        def __cmp__(self, other):
                if self.path < other.path:
                    return -1
                if self.path == other.path:
                    return 0
                if self.path > other.path:
                    return 1

        def __ne__(self, other):
                return not self.__eq__(other)

        def isdir(self):
                return os.path.isdir(self.path)

        def show(self):
                p.rawprint(self.path)

        def extension(self):
                tmp = self.path.rsplit('.')
                ext = tmp[len(tmp)-1]
                return ext

class SourceFile(IDependable, File):
        cur_index = 0
        def __init__(self, path, library = None):
                IDependable.__init__(self)
                File.__init__(self, path)
                if not library:
                        library = "work"

                self.library = library

        def gen_index(self):    
                self.__class__.cur_index = self.__class__.cur_index+1
                return self.__class__.cur_index


class VHDLFile(SourceFile):
        def __init__(self, path, library = None):
                SourceFile.__init__(self, path, library);
                self.__create_deps();

        def __check_encryption(self):
                f = open(self.path, "rb");
                s = f.read(3);
                f.close()
                if(s == b'Xlx'):
                        return True
                else:
                        return False

        def __create_deps(self):
                if self.__check_encryption():
                        self.dep_index = SourceFile.gen_index(self)
                        self.dep_fixed = True
                else:
                        self.dep_requires = self.__search_use_clauses()
                        self.dep_provides = self.__search_packages()

        def __search_use_clauses(self):
                """
                Reads a file and looks for 'use' clause. For every 'use' with
                non-standard library a tuple (lib, file) is returned in a list.

                """

                import re
                std_libs = ['ieee', 'altera_mf', 'cycloneiii', 'lpm', 'std', 'unisim', 'XilinxCoreLib', 'simprims']

                f = open(self.path, "r")
                try:
                        text = f.readlines()
                except UnicodeDecodeError:
                        return []

                use_pattern = re.compile("^[ \t]*use[ \t]+([^; ]+)[ \t]*;.*$")
                lib_pattern = re.compile("([^.]+)\.([^.]+)\.all")

                use_lines = []
                for line in text:
                        m = re.match(use_pattern, line)
                        if m != None:
                                use_lines.append(m.group(1))

                ret = []
                for line in use_lines:
                        m = re.match(lib_pattern, line)
                        if m != None:
                                if (m.group(1)).lower() in std_libs:
                                        continue
                                ret.append(m.group(1).lower()+"::"+m.group(2).lower())

                f.close()
                return ret

        def __search_packages(self):
                """
                Reads a file and looks for package clase. Returns list of packages' names
                from the file
                """

                import re
                f = open(self.path, "r")
                try:
                        text = f.readlines()
                except UnicodeDecodeError:
                        return []

                package_pattern = re.compile("^[ \t]*package[ \t]+([^ \t]+)[ \t]+is[ \t]*.*$")

                ret = []
                for line in text:
                        m = re.match(package_pattern, line)
                        if m != None:
                                ret.append(self.library.lower()+"::"+m.group(1).lower())

                f.close()
                return ret

class VerilogFile(SourceFile):
        def __init__(self, path, library = None):
                if not library:
                        library = "work"
                SourceFile.__init__(self, path, library);
                self.__create_deps();

        def __create_deps(self):
                self.dep_requires = self.__search_includes()
                self.dep_provides = self.name 

        def __search_includes(self):
            import re
            f = open(self.path, "r")
            try:
                text = f.readlines()
            except UnicodeDecodeError:
                return []
            include_pattern = re.compile("^[ \t]*`include[ \t]+\"([^ \"]+)\".*$")
            ret = []
            for line in text:
                    m = re.match(include_pattern, line)
                    if m != None:
                            ret.append(m.group(1))
            f.close()
            return ret

class UCFFile(SourceFile):
        def __init__(self, path):
                SourceFile.__init__(self, path);

class TCLFile(File):
        def __init__(self, path):
                File.__init__(self, path)

class XISEFile(File):
        def __init__(self, path):
                File.__init__(self, path)

class NGCFile(SourceFile):
        def __init__(self, path):
                SourceFile.__init__(self, path);

class WBGenFile(SourceFile):
        def __init__(self, path):
                SourceFile.__init__(self, path);

class SourceFileSet(object):
        def __init__(self):
                self.files = [];

        def __iter__(self):
                return self.files.__iter__()

        def __len__(self):
                return len(self.files)

        def __contains__(self,v):
                return v in self.files

        def __getitem__(self,v):
                return self.files[v]

        def __str__(self):
                return str([str(f) for f in self.files])

        def add(self, files):
                if isinstance(files, str):
                        raise RuntimeError("Expected object, not a string")
                elif files == None:
                        p.vprint("Got None as a file.\n Ommiting")
                else:
                        try:
                                for f in files:
                                        if f not in self.files:
                                                self.files.append(f)
                        except: #single file, not a list
                                if files not in self.files:
                                        self.files.append(files)

        def filter(self, type):
                out = []
                for f in self.files:
                        if isinstance(f, type):
                                out.append(f)
                return out

        def get_libs(self):
                return set(file.library for file in self.files)

class SourceFileFactory:
        def new (self, path, library = None):
                if path == None or path == "":
                    raise RuntimeError("Expected a file path, got: "+str(path))
                if not os.path.isabs(path):
                    path = os.path.abspath(path)
                tmp = path.rsplit('.')
                extension = tmp[len(tmp)-1]
                p.vprint("SFF> " + path);

                nf = None
                if extension == 'vhd' or extension == 'vhdl':
                        nf = VHDLFile(path, library)
                elif extension == 'v' or extension == 'sv':
                        nf = VerilogFile(path, library);
                elif extension == 'ngc':
                        nf = NGCFile(path);
                elif extension == 'ucf':
                        nf = UCFFile(path);
                elif extension == 'wb':
                        nf = WBGenFile(path);
                elif extension == 'tcl':
                        nf = TCLFile(path)
                elif extension == 'xise':
                        nf = XISEFile(path)
                return nf
