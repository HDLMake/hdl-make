"""This provides the stuff related with the HDLMake module,
from files to required submodules"""

from __future__ import absolute_import
import logging
from hdlmake import fetch
from hdlmake.util import path as path_mod
from .core import ModuleCore
import six
import os


class ModuleArgs(object):

    """This class is just a container for the main Module args"""

    def __init__(self):
        self.parent = None
        self.url = None
        self.source = fetch.LOCAL
        self.fetchto = None

    def set_args(self, parent, url, source, fetchto):
        """Set the module arguments"""
        self.parent = parent
        self.url = url
        if source == None:
            self.source = fetch.LOCAL
        else:
            self.source = source
        self.fetchto = fetchto

    def get_args(self):
        """Get the module arguments"""
        return self.parent, self.url, self.source, self.fetchto


class ModuleContent(ModuleCore):

    """Class providing the HDLMake module content"""

    def __init__(self):
        # Manifest Files Properties
        self.files = None
        # Manifest Modules Properties
        self.local = []
        self.git = []
        self.svn = []
        self.incl_makefiles = []
        super(ModuleContent, self).__init__()

    def process_manifest(self):
        """Process the content section of the manifest_dic"""
        self._process_manifest_files()
        self._process_manifest_modules()
        self._process_manifest_makefiles()
        super(ModuleContent, self).process_manifest()

    def _process_manifest_files(self):
        """Process the files instantiated by the HDLMake module"""
        from hdlmake.srcfile import SourceFileSet
        # HDL files provided by the module
        if "files" not in self.manifest_dict:
            self.files = SourceFileSet()
            try:
                logging.debug("No files in the manifest at %s",
                              self.path)
            except AttributeError:
                pass
        else:
            self.manifest_dict["files"] = path_mod.flatten_list(
                self.manifest_dict["files"])
            logging.debug("Files in %s: %s",
                          self.path, str(self.manifest_dict["files"]))
            paths = self._make_list_of_paths(self.manifest_dict["files"])
            self.files = self._create_file_list_from_paths(paths=paths)

    def _get_fetchto(self):
        """Calculate the fetchto folder"""
        if ("fetchto" in self.manifest_dict and
                self.manifest_dict["fetchto"] is not None):
            fetchto = path_mod.rel2abs(self.manifest_dict["fetchto"],
                                       self.path)
        else:
            fetchto = self.fetchto()
        return fetchto

    def _process_manifest_modules(self):
        """Process the submodules required by the HDLMake module"""
        # Process required modules
        fetchto = self._get_fetchto()
        if "modules" in self.manifest_dict:

            if "local" in self.manifest_dict["modules"]:
                local_paths = path_mod.flatten_list(
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
                self.manifest_dict["modules"]["svn"] = path_mod.flatten_list(
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
                self.manifest_dict["modules"]["git"] = path_mod.flatten_list(
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

    def _process_manifest_makefiles(self):
        """Get the extra makefiles defined in the HDLMake module"""
        # Included Makefiles
        included_makefiles_aux = []
        if "incl_makefiles" in self.manifest_dict:
            if isinstance(self.manifest_dict["incl_makefiles"],
                    six.string_types):
                included_makefiles_aux.append(
                    self.manifest_dict["incl_makefiles"])
            else:  # list
                included_makefiles_aux = self.manifest_dict["incl_makefiles"][:]
        makefiles_paths = self._make_list_of_paths(included_makefiles_aux)
        self.incl_makefiles.extend(makefiles_paths)

    def _create_file_list_from_paths(self, paths):
        """
        Build a Source File Set containing the files indicated by the
        provided list of paths
        """
        from hdlmake.srcfile import create_source_file, SourceFileSet
        srcs = SourceFileSet()
        # Check if this is the top module and grab the include_dirs
        if self.parent is None:
            if 'include_dirs' in self.manifest_dict:
                include_dirs = self.manifest_dict['include_dirs']
            else:
                include_dirs = []
        else:
            if 'include_dirs' in self.manifest_dict:
                include_dirs = self.top_module.manifest_dict['include_dirs']
            else:
                include_dirs = []
        for path_aux in paths:
            if os.path.isdir(path_aux):
                dir_ = os.listdir(path_aux)
                for f_dir in dir_:
                    f_dir = os.path.join(self.path, path_aux, f_dir)
                    if not os.path.isdir(f_dir):
                        srcs.add(create_source_file(path=f_dir,
                                                    module=self,
                                                    library=self.library,
                                                    include_dirs=include_dirs))
            else:
                srcs.add(create_source_file(path=path_aux,
                                            module=self,
                                            library=self.library,
                                            include_dirs=include_dirs))
        return srcs
