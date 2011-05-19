# -*- coding: utf-8 -*-
import path as path_mod
import msg as p
import os
from configparser import ConfigParser

class Manifest:
    def __init__(self, path = None, url = None):
        if not isinstance(path, basestring):
            raise ValueError("Path must be an instance of basestring")
        if path == None and url == None:
            raise ValueError("When creating a manifest a path or an URL must be given")
        if path != None and url == None:
            self.url = path
        if path_mod.is_abs_path(path):
            self.path = path
        else:
            raise ValueError("When creating a Manifest, path must be absolute path")

    def __str__(self):
        return self.url
    def exists(self):
        return os.path.exists(self.path)



class ManifestParser(ConfigParser):
    def __init__(self):
        ConfigParser.__init__(self,description="Configuration options description")
        self.add_option('fetchto', default=None, help="Destination for fetched modules", type='')
        self.add_option('root_module', default=None, help="Path to root module for currently parsed", type='')
        self.add_option('name', default=None, help="Name of the folder at remote synthesis machine", type='')

        self.add_delimiter()
        self.add_option('syn_device', default=None, help = "Target FPGA device", type = '');
        self.add_option('syn_grade', default=None, help = "Speed grade of target FPGA", type = '');
        self.add_option('syn_package', default=None, help = "Package variant of target FPGA", type = '');
        self.add_option('syn_top', default=None, help = "Top level module for synthesis", type = '');
        self.add_option('syn_project', default=None, help = "Vendor flow project file", type = '');

        self.add_delimiter()
        self.add_option('vsim_opt', default="", help="Additional options for vsim", type='')
        self.add_option('vcom_opt', default="", help="Additional options for vcom", type='')
        self.add_option('vlog_opt', default="", help="Additional options for vlog", type='')
        self.add_option('vmap_opt', default="", help="Additional options for vmap", type='')

        self.add_delimiter()
        self.add_option('modules', default={}, help="List of local modules", type={})
        self.add_option('target', default=None, help="Target architecture for synthesis", type='')

        self.add_allowed_key('modules', key="svn")
        self.add_allowed_key('modules', key="git")
        self.add_allowed_key('modules', key="local")

        #self.add_delimiter()
        self.add_option('library', default="work",
        help="Destination library for module's VHDL files", type="")
        self.add_option('files', default=[], help="List of files from the current module", type='')
        self.add_type('files', type=[])
        self.add_option('root', default=None, type='', help="Root catalog for local modules")
    def add_manifest(self, manifest):
        return self.add_config_file(manifest.path)

    def parse(self):
        return ConfigParser.parse(self)

    def print_help():
        self.parser.print_help()

class PawelSourceFile:
    def __init__(self, path, type=None):
        self.path = path
        self.name = os.path.basename(self.path)
        self.type = type
        self.purename = os.path.splitext(self.name)[0]

    def __str__(self):
        return self.path

    def write(self, lines):
        file = open(os.path.join(self.path,self.name), "w")
        file.write(''.join(new_ise))
        file.close()

    def extension(self):
        tmp = self.path.rsplit('.')
        ext = tmp[len(tmp)-1]
        return ext

    def isdir(self):
        return os.path.isdir(self.path)

    def search_for_use(self):
        """
        Reads a file and looks for 'use' clause. For every 'use' with
        non-standard library a tuple (lib, file) is returned in a list.
        """
        import re
        std_libs = ['ieee', 'altera_mf', 'cycloneiii', 'lpm', 'std', 'unisim']

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
        self.use = ret

    def search_for_package(self):
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
        self.package = ret

class IseProjectFile(PawelSourceFile):
    def __init__(self, path=None, type="ise"):
        SourceFile.__init__(self, path=path, type=type)

    def inject_file_list(self, files_list):
        ise = open(self.path, "r")
        ise_lines = ise.readlines()

        file_template = '    '+ "<file xil_pn:name=\"{0}\" xil_pn:type=\"FILE_VHDL\"/>\n"
        files_pattern = re.compile('[ \t]*<files>[ \t]*')
        new_ise = []
        for line in ise_lines:
            new_ise.append(line)

            if re.match(files_pattern, line) != None:
                for file in files_list:
                    new_ise.append(file_template.format(os.path.relpath(file)))
        new_ise_file = SourceFile(path=self.path, name=self.name+".new")
    def __init__(self, path=None, type="vhdl", library="work"):
        SourceFile.__init__(self,path= path, type=type)
        self.library = library
        self.use = self.search_for_use_()
        self.package = self.search_for_package_()
