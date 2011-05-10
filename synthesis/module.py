# -*- coding: utf-8 -*-
import path as path_mod
import msg as p
import os
import configparser
import global_mod
from helper_classes import Manifest, ManifestParser, IseProjectFile, ManifestOptions
from srcfile import *

from fetch import *


class Module(object):
    def __init__(self, parent, url=None, files=None, manifest=None,
    path=None, isfetched=False, source=None, fetchto=None):
        self.options = ManifestOptions()
        if source == "local" and path != None:
            if not os.path.exists(path):
                raise ValueError("Path to the local module doesn't exist: " + path)

        self.parent = parent

        if files == None:
            self.options["files"] = []
        elif not isinstance(files, list):
            self.options["files"] = [files]
        else:
            self.options["files"] = files

        if manifest != None and fetchto == None:
            options["fetchto"] = os.path.dirname(manifest.path)

        if manifest != None and url == None and path == None:
            self.options["url"] = os.path.dirname(manifest.path)
            self.options["path"] = os.path.dirname(manifest.path)
        else:
            if path != None and url == None:
                self.options["path"] = path
                self.options["url"] = path
            else:
                self.options["path"] = path
                self.options["url"] = url
        if manifest == None:
            if path != None:
                self.options["manifest"] = self.search_for_manifest()
            else:
                self.options["manifest"] = None
        else:
            self.options["manifest"] = manifest

        if source == "local":
            self.options["isfetched"] = True
        else:
            self.options["isfetched"] = isfetched

        if source != None:
            if source not in ["local", "svn", "git"]:
                raise ValueError("Inproper source: " + source)
            self.options["source"] = source
        else:
            self.options["source"] = "local"

        if fetchto != None:
            self.options["fetchto"] = fetchto
        else:
            self.options["fetchto"] = parent

        self.options["isparsed"] = False
        basename = path_mod.url_basename(self.options["url"])
        if source == "local":
            self.options["isfetched"] = True
        elif self.options["path"] != None:
            self.options["isfetched"] = True
        elif os.path.exists(os.path.join(self.options["fetchto"], basename)):
            self.options["isfetched"] = True
            self.path = os.path.join(self.options["fetchto"], basename)

        self.options["library"] = "work"
        self.parse_manifest()

    def __getattr__(self, attr):
        #options = object.__getattribute__(self, "options")
        return self.options[attr]

  #  def __str__(self):
  #      return self.url

    def search_for_manifest(self):
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
        # no manifest file found
        return None

    def __make_list(self, sth):
        if sth != None:
            if not isinstance(sth, (list,tuple)):
                sth = [sth]
        else:
            sth = []
        return sth

    def parse_manifest(self):
        p.vprint(self);
        p.vprint("IsParsed "+str(self.isparsed)+" isFetched " + str(self.isfetched));
        if self.isparsed == True:
            return
        if self.isfetched == False:
            return

        manifest_parser = ManifestParser()
        if(self.parent != None):
            print("GlobMod " +str(global_mod.top_module))
            manifest_parser.add_arbitrary_code("target=\""+global_mod.top_module.target+"\"")
        else:
            print("NoParent")
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


        #derivate fetchto from the root_module
        if opt_map["root_module"] != None:
            self.fetchto = self.root_module.fetchto
        else:
            if not path_mod.is_rel_path(opt_map["fetchto"]):
                p.echo(' '.join([os.path.basename(sys.argv[0]), "accepts relative paths only:", opt_map["fetchto"]]))
                quit()

            if(opt_map["fetchto"] != None):
                fetchto = path_mod.rel2abs(opt_map["fetchto"], self.path)
            else:
                fetchto = None

        #this is the previous solution - no derivation 
        #if opt_map["fetchto"] == None:
        #    fetchto = self.path
        # else:
        #    if not path_mod.is_rel_path(opt_map["fetchto"]):
        #       p.echo(' '.join([os.path.basename(sys.argv[0]), "accepts relative paths only:", opt_map["fetchto"]]))
        #       quit()
        #   fetchto = path_mod.rel2abs(opt_map["fetchto"], self.path)

        if self.ise == None:
            self.ise = "13.1"
        if "local" in opt_map["modules"]:
            local_paths = self.__make_list(opt_map["modules"]["local"])
            local_mods = []
            for path in local_paths:
                path = path_mod.rel2abs(path, self.path)
                local_mods.append(Module(path=path, source="local", parent=self))
            self.local = local_mods
        else:
            self.local = []

        self.library = opt_map["library"]
        if opt_map["files"] == []:

# don't scan if there a manifest exists but contains no files (i.e. only sub-modules)
#            fact = SourceFileFactory ()

#            files = []
#            for filename in os.listdir(self.path):
#                path = os.path.join(self.path, filename)
#                if not os.path.isdir(path):
#                    file = fact.new(path=path)
#                    file.library = self.library
#                    files.append(file)
#            self.files = files
            self.fileset = SourceFileSet()
            pass
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

            self.fileset = self.create_flat_file_list(paths=paths);
            
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

        self.name = opt_map["name"]
        self.target = opt_map["target"]

        self.syn_device = opt_map["syn_device"];
        self.syn_grade = opt_map["syn_grade"];
        self.syn_package= opt_map["syn_package"];
        self.syn_project = opt_map["syn_project"];
        self.syn_top = opt_map["syn_top"];

        self.isparsed = True

    def is_fetched(self):
        return self.isfetched

    def fetch(self):

        if self.source == "local":
            self.path = self.url

        involved_modules = [self]
        modules_queue = [self]

        p.vprint("Fetching manifest: " + str(self.manifest))

        while len(modules_queue) > 0:
            if(self.source == "local"):
                cur_mod = modules_queue.pop()
                p.vprint("ModPath: " + cur_mod.path);
                cur_mod.parse_manifest()
            
            if cur_mod.root_module != None:
                root_module = cur_mod.root_module
                p.vprint("Encountered root manifest: " + str(root_module))
                new_modules = root_module.fetch()
                involved_modules.extend(new_modules)
                modules_queue.extend(new_modules)

            for i in cur_mod.local:
                p.vprint("Modules waiting in fetch queue:"+
                ' '.join([str(cur_mod.git), str(cur_mod.svn), str(cur_mod.local)]))

            for module in cur_mod.svn:
                p.vprint("Fetching to " + module.fetchto)
                path = module.__fetch_from_svn()
                module.path = path
                module.source = "local"
                module.isparsed = False;
                involved_modules.append(module)
                modules_queue.append(module)

            for module in cur_mod.git:
                p.vprint("[git] Fetching to " + module.fetchto)
                path = module.__fetch_from_git()
                module.path = path
                module.source = "local"
                module.isparsed = False;
                module.manifest = module.search_for_manifest();
                p.vprint("[git] Local path " + module.path);
                involved_modules.append(module)
                modules_queue.append(module)

            for module in cur_mod.local:
                involved_modules.append(module)
                modules_queue.append(module)

            p.vprint("Modules scan queue: " + str(modules_queue))

        p.vprint("All found manifests have been scanned")
        return involved_modules

    def __fetch_from_svn(self):
        fetchto = self.fetchto
        if not os.path.exists(fetchto):
            os.mkdir(fetchto)

        cur_dir = os.getcwd()
        os.chdir(fetchto)
        p.echo(os.getcwd())
        basename = path_mod.url_basename(self.url)

        cmd = "svn checkout {0} {1}"
        cmd = cmd.format(self.url, basename)

        p.vprint(cmd)
        os.system(cmd)
        os.chdir(cur_dir)
        self.isfetched = True
        self.path = os.path.join(fetchto, basename)

        return os.path.join(fetchto, basename)

    def __fetch_from_git(self):
#        p.vprint(self.fetchto);
        basename = path_mod.url_basename(self.url)
        self.isfetched = fetch_from_git(self.url, None, self.fetchto);
        return os.path.join(self.fetchto, basename)

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


    def create_flat_file_list(self, paths):
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

    def generate_deps_for_vhdl_in_modules(self):
        all_files = self.extract_files_from_all_modules(extensions="vhd")
        p.vprint("All vhdl files:")
        for file in all_files:
            p.vprint(str(file) + ':' + file.library)
        for file in all_files:
            file.search_for_package()
            file.search_for_use()

        package_file_dict = {}
        for file in all_files:
            packages = file.package #look for package definitions
            if len(packages) != 0: #if there are some packages in the file
                for package in packages:
                    if package in package_file_dict:
                        p.echo("There might be a problem... Compilation unit " + package +
                        " has several instances:\n\t" + str(file) + "\n\t" + str(package_file_dict[package]))
                        package_file_dict[package.lower()] = [package_file_dict[package.lower()], file]#///////////////////////////////////////////////////
                    package_file_dict[package.lower()] = file #map found package to scanned file
            file_purename = os.path.splitext(file.name)[0]
            if file_purename in package_file_dict and package_file_dict[file_purename.lower()] != file:
                p.echo("There might be a problem... Compilation unit " + file_purename +
                    " has several instances:\n\t" + str(file) + "\n\t" + str(package_file_dict[file_purename]))
            package_file_dict[file_purename.lower()] = file

        p.vpprint(package_file_dict)

        file_file_dict = {}
        for file in all_files:
            for unit in file.use:
                if unit[1].lower() in package_file_dict:
                    if unit[0].lower() == package_file_dict[unit[1].lower()].library:
                        if file in file_file_dict:
                            file_file_dict[file].append(package_file_dict[unit[1].lower()])
                        else:
                            file_file_dict[file] = [package_file_dict[unit[1].lower()]]
                else:
                    p.echo("Cannot resolve dependency: " + str(file) + " depends on "
                        +"compilation unit " + str(unit) + ", which cannot be found")
        for file in all_files:
            if file not in file_file_dict:
                file_file_dict[file] = []
        p.vpprint(file_file_dict)
        return file_file_dict
