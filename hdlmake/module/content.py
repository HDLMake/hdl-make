import logging
from hdlmake import fetch
from .plugin import ModulePlugin
from hdlmake.util import path as path_mod

class ModuleContent(ModulePlugin):
    def __init__(self):
        # Manifest Files Properties
        self.files = None
        # Manifest Modules Properties
        self.local = []
        self.git = []
        self.svn = []
        self.git_submodules = []
        super(ModuleContent, self).__init__()

    def process_manifest(self):
        self._process_manifest_fetch()
        self._process_manifest_files()
        self._process_manifest_modules()
        super(ModuleContent, self).process_manifest()

    def _process_manifest_files(self):
        from hdlmake.srcfile import (TCLFile, VerilogFile, VHDLFile,
            SourceFileSet)
        # HDL files provided by the module
        if self.manifest_dict["files"] == []:
            self.files = SourceFileSet()
            try:
                logging.debug("No files in the manifest %s",
                    self.manifest.path)
            except AttributeError:
                pass
        else:
            self.manifest_dict["files"] = ModulePlugin.flatten_list(
                self.manifest_dict["files"])
            logging.debug("Files in %s: %s",
                self.path, str(self.manifest_dict["files"]))
            paths = self._make_list_of_paths(self.manifest_dict["files"])
            self.files = self._create_file_list_from_paths(paths=paths)
            for f in self.files:
                if isinstance(f, VerilogFile):
                    f.vsim_opt = self.vsim_opt
                elif isinstance(f, VHDLFile):
                    f.vcom_opt = self.vcom_opt

    def _process_manifest_fetch(self):
        # Fetch configuration
        if self.manifest_dict["fetchto"] is not None:
            fetchto = path_mod.rel2abs(self.manifest_dict["fetchto"],
                self.path)
            self.fetchto = fetchto
        else:
            fetchto = self.fetchto

        self.fetch_pre_cmd = self.manifest_dict["fetch_pre_cmd"]
        self.fetch_post_cmd = self.manifest_dict["fetch_post_cmd"]

    def _process_manifest_modules(self):
        fetchto = self.fetchto
        # Process required modules
        if "local" in self.manifest_dict["modules"]:
            local_paths = ModulePlugin.flatten_list(
                self.manifest_dict["modules"]["local"])
            local_mods = []
            for path in local_paths:
                if path_mod.is_abs_path(path):
                    logging.error("Found an absolute path (" + path +
                        ") in a manifest(" + self.path + ")")
                    quit()
                path = path_mod.rel2abs(path, self.path)
                local_mods.append(self.pool.new_module(parent=self,
                                                       url=path,
                                                       source=fetch.LOCAL,
                                                       fetchto=fetchto))
            self.local = local_mods
        else:
            self.local = []

        if "svn" in self.manifest_dict["modules"]:
            self.manifest_dict["modules"]["svn"] = ModulePlugin.flatten_list(
                self.manifest_dict["modules"]["svn"])
            svn_mods = []
            for url in self.manifest_dict["modules"]["svn"]:
                svn_mods.append(self.pool.new_module(parent=self,
                                                     url=url,
                                                     source=fetch.SVN,
                                                     fetchto=fetchto))
            self.svn = svn_mods
        else:
            self.svn = []

        if "git" in self.manifest_dict["modules"]:
            self.manifest_dict["modules"]["git"] = ModulePlugin.flatten_list(
                self.manifest_dict["modules"]["git"])
            git_mods = []
            for url in self.manifest_dict["modules"]["git"]:
                git_mods.append(self.pool.new_module(parent=self,
                                                     url=url,
                                                     source=fetch.GIT,
                                                     fetchto=fetchto))
            self.git = git_mods
        else:
            self.git = []

        # Git submodules are temporarly disabled!
        # -- we need to clearly define the expected behavior
        # git_submodule_dict = fetch.Git.get_git_submodules(self)
        # git_toplevel = fetch.Git.get_git_toplevel(self)
        # for submodule_key in git_submodule_dict.keys():
        #    url = git_submodule_dict[submodule_key]["url"]
        #    path = git_submodule_dict[submodule_key]["path"]
        #    path = os.path.join(git_toplevel, path)
        #    path = os.path.normpath(path)
        #    fetchto = os.path.sep.join(path.split(os.path.sep)[:-1])
        #    self.git_submodules.append(self.pool.new_module(parent=self,
        #        url=url,
        #        fetchto=fetchto,
        #        source=fetch.GITSUBMODULE))



