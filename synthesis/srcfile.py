# -*- coding: utf-8 -*-
from dep_solver import *
import os


class SourceFile(IDependable):
        cur_index = 0
        def __init__(self, path, library = None):
                IDependable.__init__(self)
                self.path = path;
                self.name = os.path.basename(self.path)
                self.purename = os.path.splitext(self.name)[0]
                if not library:
                        library = "work"

                self.library = library

        def __str__(self):
                return self.path

        def extension(self):
                tmp = self.path.rsplit('.')
                ext = tmp[len(tmp)-1]
                return ext

        def isdir(self):
                return os.path.isdir(self.path)

        def gen_index(self):    
                self.__class__.cur_index = self.__class__.cur_index+1
                return self.__class__.cur_index

        def show(self):
                p.rawprint(self.path);

class VHDLFile(SourceFile):
        def __init__(self, path, library = None):
                SourceFile.__init__(self, path, library);
                self.create_deps();
#                if self.dep_fixed:
 #                       p.rawprint("File " + self.path + " fixed dep [idx " + str(self.dep_index) + "]")
#                else:
#                        p.rawprint("File " + self.path + " uses: " + str(self.dep_requires) + " provides: " + str(self.dep_provides))

        def check_encryption(self):
                f = open(self.path, "rb");
                s = f.read(3);
                f.close()
                if(s == b'Xlx'):
                        return True
                else:
                        return False
                        
        def create_deps(self):
                if self.check_encryption():
                        self.dep_index = SourceFile.gen_index(self)
                        self.dep_fixed = True
                else:
                        self.dep_requires = self.search_use_clauses()
                        self.dep_provides = self.search_packages()

        def search_use_clauses(self):
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
                                ret.append(m.group(1)+"::"+m.group(2))

                f.close()
                return ret
        
        def search_packages(self):
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

                package_pattern = re.compile("^[ \t]*package[ \t]+([^ \t]+)[ \t]+is[ \t]*$")

                ret = []
                for line in text:
                        m = re.match(package_pattern, line)
                        if m != None:
                                ret.append(self.library+"::"+m.group(1))

                f.close()
                return ret
        
class VerilogFile(SourceFile):
        def __init__(self, path, library = None):
                if not library:
                        library = "work"
                SourceFile.__init__(self, path, library);
                self.create_deps();

        def create_deps(self):
                self.dep_requires = self.search_includes()
                self.dep_provides = os.path.basename(self.path);

        def search_includes(self):
                pass

class UCFFile(SourceFile):
        def __init__(self, path):
                SourceFile.__init__(self, path);

class NGCFile(SourceFile):
        def __init__(self, path):
                SourceFile.__init__(self, path);

class WBGenFile(SourceFile):
        def __init__(self, path):
                SourceFile.__init__(self, path);

class SourceFileSet(list):
        def __init__(self):
                self.files = [];

        def __iter__(self):
                return self.files.__iter__()
            
        def __len__(self):
                return len(self.files)
            
        def __contains__(self,v):
                return v in self.files
            
        def __getitem__(self,v):
                return self.files(v)

        def __str__(self):
                return str([str(f) for f in self.files])

        def add(self, files):
                if isinstance(files, basestring):
                        raise RuntimeError("Expected object, not a string")
                elif isinstance(files, list):
                        self.files.extend(files)
                else: #single file, not a list
                        self.files.append(files)
                #if(isinstance(files, SourceFileSet)):
                #        for f in files.files:
                #               self.files.append(f)
                #elif(isinstance(files, list)):
                #        for f in files:
                #                self.files.append(f)
                #else:
                #        self.files.append(files)

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
                tmp = path.rsplit('.')
                extension = tmp[len(tmp)-1]
                p.vprint("SFF> " + path);

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

                return nf
      
