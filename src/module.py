# -*- coding: utf-8 -*-
import path as path_mod
import msg as p
import os
import global_mod
from helper_classes import Manifest, ManifestParser
from srcfile import SourceFileSet, SourceFileFactory 

class ManifestOptions(object):
    def __init__(self):
        self.items = { "files" : None, #files from the module that should be taken
                "fetchto" : None, #where this module should be fetched to, when fetching
                "path" : None, #where the module is storek
                "url" : None, #URL to the module
                "manifest" : None, #manifest object
                "source" : None, #where it should be fetched from
                "isparsed" : None, #
                "isfetched" : None,
                "library" : None, #target library for the vhdl compilation
                "root_module" : None, #root module object
                "local" : None, #local modules
                "target" : None,
                "action" : None,
                "git" : None, #git modules
                "svn" : None, #svn modules
                "ise" : None,
                "tcl" : None,
                "vmap_opt" : None,
                "vlog_opt" : None,
                "vcom_opt" : None
                }
    def __setitem__(self, key, value):
        if key in self.items:
            self.items[key] = value
        else:
            raise KeyError("__setitem__: there is no such key: "+str(key))

    def __getitem__(self, key):
        if key in self.items:
            return self.items[key]
        else:
            raise KeyError("__getitem__:there is no such key: "+str(key))

class Module(object):
    def __init__(self, parent, url=None, files=None, manifest=None,
    path=None, isfetched=False, source=None, fetchto=None):
        self.options = ManifestOptions()
        if source == "local" and path != None:
            if not os.path.exists(path):
                p.rawprint("Path to the local module doesn't exist:\n" + path)
                p.rawprint("This module was instantiated in: " + str(parent))
        self.parent = parent
        self.revision = None

        if files == None:
            self.files = []
        elif not isinstance(files, list):
            self.files = [files]
        else:
            self.files = files

        if manifest != None and fetchto == None:
            self.fetchto = os.path.dirname(manifest.path)

        if manifest != None and url == None and path == None:
            self.url = os.path.dirname(manifest.path)
            self.path = os.path.dirname(manifest.path)
        else:
            if path != None and url == None:
                self.path = path
                self.url = path
            else:
                self.path = path
                self.url = url
        if manifest == None:
            if path != None:
                self.manifest = self.__search_for_manifest()
            else:
                self.manifest = None
        else:
            self.manifest = manifest

        if source == "local":
            self.path = self.url
            self.isfetched = True
        else:
            self.isfetched = isfetched

        if source != None:
            if source not in ["local", "svn", "git"]:
                raise ValueError("Inproper source: " + source)
            self.source = source
        else:
            self.source = "local"

        if fetchto != None:
            self.fetchto = fetchto
        else:
            if parent == None:
                self.fetchto = self.path
            else:
                self.fetchto = parent.fetchto

        self.isparsed = False
        basename = path_mod.url_basename(self.url)

        if source == "local":
            self.isfetched = True
        elif self.path != None:
            self.isfetched = True
        elif os.path.exists(os.path.join(self.fetchto, basename)):
            self.isfetched = True
            self.path = os.path.join(self.fetchto, basename)
            self.manifest = self.__search_for_manifest()

        self.library = "work"
        self.parse_manifest()

    def __getattr__(self, attr):
        #options = object.__getattribute__(self, "options")
        return self.options[attr]

    def __str__(self):
        return self.url

    @property
    def is_fetched_to(self):
        return os.path.dirname(self.path)

    def submodules(self):
        def __nonull(x):
            if not x:
                return []
            else:
                return x

        return __nonull(self.local) + __nonull(self.git) + __nonull(self.svn)

    def basename(self):
        import path
        return path.url_basename(self.url)

    def __search_for_manifest(self):
        """
        Look for manifest in the given folder
        """
        p.vprint("Looking for manifest in " + self.path)
        for filename in os.listdir(self.path):
            if filename == "manifest.py" or filename == "Manifest.py":
                if not os.path.isdir(filename):
                    p.vprint("*** found manifest for module "+self.path);
                    manifest = Manifest(path=os.path.abspath(os.path.join(self.path, filename)))
                    return manifest
        return None

    def __make_list(self, sth):
        if sth != None:
            if not isinstance(sth, (list,tuple)):
                sth = [sth]
        else:
            sth = []
        return sth

    def parse_manifest(self):
        if self.isparsed == True:
            return
        if self.isfetched == False:
            return
        if self.manifest == None:
            self.manifest = self.__search_for_manifest()

        manifest_parser = ManifestParser()
        if(self.parent != None):
            manifest_parser.add_arbitrary_code("target=\""+str(global_mod.top_module.target)+"\"")
        else:
            global_mod.top_module = self

        manifest_parser.add_arbitrary_code("__manifest=\""+self.url+"\"")
        manifest_parser.add_arbitrary_code(global_mod.options.arbitrary_code)

        if self.manifest == None:
            p.vprint("No manifest found in module "+str(self))
        else:
            manifest_parser.add_manifest(self.manifest)
            p.vprint("Parsing manifest file: " + str(self.manifest))

        opt_map = None
        try:
            opt_map = manifest_parser.parse()
        except NameError as ne:
            p.echo("Error while parsing {0}:\n{1}: {2}.".format(self.manifest, type(ne), ne))
            quit()
        if opt_map["root_module"] != None:
            root_path = path_mod.rel2abs(opt_map["root_module"], self.path)
            self.root_module = Module(path=root_path, source="local", isfetched=True, parent=self)
            self.root_module.parse_manifest()

        self.target = opt_map["target"]

        if(opt_map["fetchto"] != None):
            print ">>>" + opt_map["fetchto"]
            fetchto = path_mod.rel2abs(opt_map["fetchto"], self.path)
        else:
            if self.fetchto == None:
                fetchto = self.is_fetched_to
            else:
                fetchto = self.fetchto

        if self.ise == None:
            self.ise = "13.1"
        if "local" in opt_map["modules"]:
            local_paths = self.__make_list(opt_map["modules"]["local"])
            local_mods = []
            for path in local_paths:
                path = path_mod.rel2abs(path, self.path)
                local_mods.append(Module(path=path, source="local", parent=self, fetchto=fetchto))
            self.local = local_mods
        else:
            self.local = []

        self.library = opt_map["library"]
        if opt_map["files"] == []:
            self.fileset = SourceFileSet()
        else:
            opt_map["files"] = self.__make_list(opt_map["files"])
            paths = []
            for path in opt_map["files"]:
                if not path_mod.is_abs_path(path):
                    path = path_mod.rel2abs(path, self.path)
                    paths.append(path)
                else:
                    p.echo(path + " is an absolute path. Omitting.")
                if not os.path.exists(path):
                    p.echo("File listed in " + self.manifest.path + " doesn't exist: "
                    + path +".\nExiting.")
                    quit()

            self.fileset = self.__create_flat_file_list(paths=paths);

        if "svn" in opt_map["modules"]:
            opt_map["modules"]["svn"] = self.__make_list(opt_map["modules"]["svn"])
            svn = []
            for url in opt_map["modules"]["svn"]:
                svn.append(Module(url=url, source="svn", fetchto=fetchto, parent=self))
            self.svn = svn
        else:
            self.svn = []

        if "git" in opt_map["modules"]:
            opt_map["modules"]["git"] = self.__make_list(opt_map["modules"]["git"])
            git = []
            for url in opt_map["modules"]["git"]:
                git.append(Module(url=url, source="git", fetchto=fetchto, parent=self))
            self.git = git
        else:
            self.git = []

        self.vmap_opt = opt_map["vmap_opt"]
        self.vcom_opt = opt_map["vcom_opt"]
        self.vlog_opt = opt_map["vlog_opt"]
        self.vsim_opt = opt_map["vsim_opt"]

        self.target = opt_map["target"]
        self.action = opt_map["action"]

        if opt_map["syn_name"] == None and opt_map["syn_project"] != None:
            self.syn_name = opt_map["syn_project"][:-5] #cut out .xise from the end
        else:
            self.syn_name = opt_map["syn_name"]
        self.syn_device = opt_map["syn_device"];
        self.syn_grade = opt_map["syn_grade"];
        self.syn_package= opt_map["syn_package"];
        self.syn_project = opt_map["syn_project"];
        self.syn_top = opt_map["syn_top"];

        self.isparsed = True

    def is_fetched_recursively(self):
        if not self.isfetched:
            return False
        for mod in self.submodules():
            if mod.is_fetched_recursively() == False:
                return False
        return True

    def make_list_of_modules(self):
        p.vprint("Making list of modules for " + str(self))
        new_modules = [self]
        modules = [self]
        while len(new_modules) > 0:
            cur_module = new_modules.pop()
#            p.vprint("Current: " + str(cur_module))
            if not cur_module.isfetched:
                p.echo("Error in modules list - unfetched module: " + str(cur_module))
                quit()
            if cur_module.manifest == None:
                p.vprint("No manifest in " + str(cur_module))
                continue
            cur_module.parse_manifest()
            if cur_module.root_module != None:
                root_module = cur_module.root_module
                modules_from_root = root_module.make_list_of_modules()
                modules.extend(modules_from_root)

            for module in cur_module.local:
                modules.append(module)
                new_modules.append(module)

            for module in cur_module.git:
                modules.append(module)
                new_modules.append(module)

            for module in cur_module.svn:
                modules.append(module)
                new_modules.append(module)

        if len(modules) == 0:
            p.vprint("No modules were found in " + self.fetchto)
        return modules


    def __create_flat_file_list(self, paths):
        fact = SourceFileFactory();
        srcs = SourceFileSet();
        for p in paths:
            srcs.add(fact.new(p, self.library))
        return srcs

    def build_global_file_list(self):
        f_set = SourceFileSet();
#        self.create_flat_file_list();
        modules = self.make_list_of_modules()
        for m in modules:
            f_set.add(m.fileset);

        return f_set
