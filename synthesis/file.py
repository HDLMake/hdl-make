
from dep_solver import *
from os import path


class SourceFile(IDependable):
        cur_index = 0
        def __init__(self, path):
                IDependable.__init__(self)
                self.path = path;

        def gen_index(self):    
                self.__class__.cur_index = self.__class__.cur_index+1
                return self.__class__.cur_index

class VHDLFile(SourceFile):
        def __init__(self, path):
                SourceFile.__init__(self, path);
                self.create_deps();
                if self.dep_fixed:
                        print("File " + self.path + " fixed dep [idx " + str(self.dep_index) + "]")
                else:
                        print("File " + self.path + " uses: " + str(self.dep_requires) + " provides: " + str(self.dep_provides))

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
                                ret.append((m.group(1),m.group(2)))

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
                                ret.append(m.group(1))

                f.close()
                return ret
        
class VerilogFile(SourceFile):
        def __init__(self, path):
                self.path = path;
                self.create_deps(path);

        def create_deps(self):
                self.dep_requires = self.search_includes()
                self.dep_provides = os.path.basename(self.path);

        def search_includes(self):
                pass

class UCFFile(SourceFile):
        pass

class NGCFile(SourceFile):
        pass


class SourceFileSet:
        def __init__(self):
                self.files = [];
        
        def add(self, files):
                for f in files:
                        if f.endswith('.vhd') or f.endswith('.vhdl'):
                                nf = VHDLFile(f)
                        elif f.endwith('.v') or f.endswith('.sv'):
                                nf = VerilogFile(f);
                        elif f.endwith('.ngc'):
                                nf = NGCFile(f);
                        elif f.endwith('.ucf'):
                                nf = UCFFile(f);

                        self.files.append(nf);
                        
