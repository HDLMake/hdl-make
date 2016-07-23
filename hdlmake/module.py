#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013-2016 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Multi-tool support by Javier D. Garcia-Lasheras (javier@garcialasheras.com)
#
# This file is part of Hdlmake.
#
# Hdlmake is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hdlmake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Hdlmake.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
import os
import sys
import logging

from .manifest_parser import Manifest, ManifestParser
from .util import path as path_mod
from . import fetch


class Module(object):
    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, value):
        if value not in [fetch.GIT, fetch.SVN, fetch.LOCAL, fetch.GITSUBMODULE]:
            raise ValueError("Improper source: " + value)
        self._source = value

    @source.deleter
    def source(self):
        del self._source

    @property
    def basename(self):
        from .util import path
        if self.source == fetch.SVN:
            return path.svn_basename(self.url)
        else:
            return path.url_basename(self.url)

    #PLEASE don't use this constructor. Create all modules with ModulePool.new_module()
    def __init__(self, parent, url, source, fetchto, pool):
        assert url is not None
        assert source is not None

        self.manifest = None
        self.manifest_dict = None
        self.pool = pool
        self.source = source
        self.parent = parent
        self.isparsed = False
        self.top_entity = None
        self.revision = None

        # Includes Manifest Properties
        self.include_dirs = None

        # Universal Manifest Properties
        self.top_module = pool.get_top_module()
        self.library = "work"
        self.target = None
        self.action = None

        # Manifest Files Properties
        self.files = None

        # Manifest Modules Properties
        self.fetchto = fetchto
        self.local = []
        self.git = []
        self.svn = []
        self.git_submodules = []

        # Manifest Altera Properties
        self.quartus_preflow = None
        self.quartus_postmodule = None
        self.quartus_postflow = None
        self.hw_tcl_filename = None

        # Manifest Included Makefiles
        self.incl_makefiles = []

        # Manifest Force tool Property
        self.force_tool = None

        # Manifest Synthesis Properties
        self.syn_device = None
        self.syn_family = None
        self.syn_grade = None
        self.syn_package = None
        self.syn_project = None
        self.syn_top = None
        self.syn_tool = None
        self.syn_ise_version = None
        self.syn_pre_script = None
        self.syn_post_script = None

        # Manifest Simulation Properties
        self.sim_top = None
        self.sim_tool = None
        self.sim_pre_script = None
        self.sim_post_script = None
        self.sim_only_files = None
        self.vsim_opt = None
        self.vmap_opt = None
        self.vlog_opt = None
        self.vcom_opt = None
        self.iverilog_opt = None


        
        self.raw_url = url
        if source != fetch.LOCAL:
            self.url, self.branch, self.revision = path_mod.url_parse(url)
        else:
            self.url, self.branch, self.revision = url, None, None

        if source == fetch.LOCAL and not os.path.exists(url):
            logging.error("Path to the local module doesn't exist:\n" + url
                          + "\nThis module was instantiated in: " + str(parent))
            quit()

        if source == fetch.LOCAL:
            self.path = url
            self.isfetched = True
        else:
            if os.path.exists(os.path.abspath(os.path.join(fetchto, self.basename))) and os.listdir(os.path.abspath(os.path.join(fetchto, self.basename))):
                self.path = os.path.abspath(os.path.join(fetchto, self.basename))
                self.isfetched = True
                logging.debug("Module %s (parent: %s) is fetched." % (url, parent.path))
            else:
                self.path = None
                self.isfetched = False
                logging.debug("Module %s (parent: %s) is NOT fetched." % (url, parent.path))



    def __str__(self):
        return self.raw_url

    @property
    def is_fetched_to(self):
        return os.path.dirname(self.path)

    def submodules(self):
        def __nonull(x):
            if not x:
                return []
            else:
                return x

        return __nonull(self.local) + __nonull(self.git) + __nonull(self.svn) + __nonull(self.git_submodules)

    def _search_for_manifest(self):
        """
        Look for manifest in the given folder
        """
        logging.debug("Looking for manifest in " + self.path)
        dir_files = os.listdir(self.path)
        if "manifest.py" in dir_files and "Manifest.py" in dir_files:
            logging.error("Both manifest.py and Manifest.py found in the module directory: %s" % self.path)
            sys.exit("\nExiting")
        for filename in dir_files:
            if filename == "manifest.py" or filename == "Manifest.py":
                if not os.path.isdir(filename):
                    logging.debug("Found manifest for module %s: %s" % (self.path, filename))
                    manifest = Manifest(path=os.path.abspath(os.path.join(self.path, filename)))
                    return manifest
        return None

    def _flatten_list(self, sth):
        if sth is not None:
            if not isinstance(sth, (list, tuple)):
                sth = [sth]
        else:
            sth = []
        return sth

    def remove_dir_from_disk(self):
        if not self.isfetched:
            return

        import shutil

        logging.debug("Removing " + self.path)
        shutil.rmtree(self.path)

        while True:
            try:
                logging.debug("Trying to remove " + os.path.dirname(self.path))
                os.rmdir(os.path.dirname(self.path))
            except OSError:  # a catologue is not empty - we are done
                break

    def parse_manifest(self):
        """
        Create a dictionary from the module Manifest.py and assign it to the manifest_dict property.
        In order to do this, it creates a ManifestParser object and feed it with:
        - the arbitrary code from pool's top_module options (it assumes a top_module exists before any parsing!)
        - the Manifest.py (if exists)
        - the extra_context:
          - If this is the root module (has not parent), use an empty extra_context in the parser
          - If this is a submodule (has a parent), inherit the extra_context as:
            - the full manifest_dict from the top_module...
            - ...but deleting some key fields that needs to be respected (files, modules...).
        """

        if self.manifest_dict:
            return
        if self.isparsed is True or self.isfetched is False:
            return
        if self.manifest is None:
            self.manifest = self._search_for_manifest()
        if self.path is None:
            raise RuntimeError()

        if self.source == fetch.SVN:
            self.revision = fetch.Svn.check_revision_number(self.path)
        elif self.source == fetch.GIT:
            self.revision = fetch.Git.check_commit_id(self.path)

        manifest_parser = ManifestParser()

        #manifest_parser.add_arbitrary_code(self.pool.top_module.options.arbitrary_code)

        if self.manifest is None:
            logging.debug("No manifest found in module "+str(self))
        else:
            logging.debug("Parse manifest in: %s" % self.path)
            manifest_parser.add_manifest(self.manifest)

        if self.parent is None:
            extra_context = {}
        else:
            extra_context = dict(self.top_module.manifest_dict)  # copy the dictionary
            del extra_context["modules"]
            del extra_context["files"]
            del extra_context["include_dirs"]
            del extra_context["sim_only_files"]
            del extra_context["incl_makefiles"]
            del extra_context["bit_file_targets"]
            del extra_context["library"]
        extra_context["__manifest"] = self.path

        # In the ManifestParser.parse method is where the most of the parser action takes place!
        opt_map = None
        try:
            opt_map = manifest_parser.parse(extra_context=extra_context)
        except NameError as ne:
            logging.error("Error while parsing {0}:\n{1}: {2}.".format(self.manifest, type(ne), ne))
            quit()
        self.manifest_dict = opt_map

        # Process the parsed manifest_dict to assign the module properties
        self._process_manifest_universal()
        self._process_manifest_synthesis()
        self._process_manifest_simulation()
        self._process_manifest_includes()
        self._process_manifest_files()
        self._process_manifest_modules()
        self._process_manifest_altera()
        self._process_manifest_bitfile_targets()
        self._process_manifest_force_tool()
        self._process_manifest_included_makefiles()

        # Tag the module as parsed
        self.isparsed = True

        # Parse every detected submodule
        for m in self.submodules():
            m.parse_manifest()



    def _process_manifest_synthesis(self):
        # Synthesis properties
        self.syn_pre_cmd = self.manifest_dict["syn_pre_cmd"]
        self.syn_pre_synthesize_cmd = self.manifest_dict["syn_pre_synthesize_cmd"]
        self.syn_post_synthesize_cmd = self.manifest_dict["syn_post_synthesize_cmd"]
        self.syn_pre_translate_cmd = self.manifest_dict["syn_pre_translate_cmd"]
        self.syn_post_translate_cmd = self.manifest_dict["syn_post_translate_cmd"]
        self.syn_pre_map_cmd = self.manifest_dict["syn_pre_map_cmd"]
        self.syn_post_map_cmd = self.manifest_dict["syn_post_map_cmd"]
        self.syn_pre_par_cmd = self.manifest_dict["syn_pre_par_cmd"]
        self.syn_post_par_cmd = self.manifest_dict["syn_post_par_cmd"]
        self.syn_pre_bitstream_cmd = self.manifest_dict["syn_pre_bitstream_cmd"]
        self.syn_post_bitstream_cmd = self.manifest_dict["syn_post_bitstream_cmd"]
        self.syn_post_cmd = self.manifest_dict["syn_post_cmd"]
        if self.manifest_dict["syn_name"] is None and self.manifest_dict["syn_project"] is not None:
            self.syn_name = self.manifest_dict["syn_project"][:-5]  # cut out .xise from the end
        else:
            self.syn_name = self.manifest_dict["syn_name"]
        self.syn_tool = self.manifest_dict["syn_tool"]
        self.syn_device = self.manifest_dict["syn_device"]
        self.syn_family = self.manifest_dict["syn_family"]
        self.syn_grade = self.manifest_dict["syn_grade"]
        self.syn_package = self.manifest_dict["syn_package"]
        self.syn_project = self.manifest_dict["syn_project"]
        self.syn_top = self.manifest_dict["syn_top"]
        if self.manifest_dict["syn_ise_version"] is not None:
            version = self.manifest_dict["syn_ise_version"]
            self.syn_ise_version = str(version)


    def _process_manifest_simulation(self):
        from .srcfile import SourceFileSet
        # Simulation properties
        self.sim_tool = self.manifest_dict["sim_tool"]
        self.sim_top = self.manifest_dict["sim_top"]
        self.sim_pre_cmd = self.manifest_dict["sim_pre_cmd"]
        self.sim_post_cmd = self.manifest_dict["sim_post_cmd"]

        self.vmap_opt = self.manifest_dict["vmap_opt"]
        self.vcom_opt = self.manifest_dict["vcom_opt"]
        self.vsim_opt = self.manifest_dict["vsim_opt"]
        self.vlog_opt = self.manifest_dict["vlog_opt"]
        self.iverilog_opt = self.manifest_dict["iverilog_opt"]

        if len(self.manifest_dict["sim_only_files"]) == 0:
            self.sim_only_files = SourceFileSet()
        else:
            self.manifest_dict["sim_only_files"] = self._flatten_list(self.manifest_dict["sim_only_files"])
            paths = self._make_list_of_paths(self.manifest_dict["sim_only_files"])
            self.sim_only_files = self._create_file_list_from_paths(paths=paths)


    def _process_manifest_files(self):
        from .srcfile import TCLFile, VerilogFile, VHDLFile, SourceFileSet
        # HDL files provided by the module
        if self.manifest_dict["files"] == []:
            self.files = SourceFileSet()
            try:
                logging.debug("No files in the manifest %s" % self.manifest.path)
            except AttributeError:
                pass
        else:
            self.manifest_dict["files"] = self._flatten_list(self.manifest_dict["files"])
            logging.debug("Files in %s: %s" % (self.path, str(self.manifest_dict["files"])))
            paths = self._make_list_of_paths(self.manifest_dict["files"])
            self.files = self._create_file_list_from_paths(paths=paths)
            for f in self.files:
                if isinstance(f, VerilogFile):
                    f.vsim_opt = self.vsim_opt
                elif isinstance(f, VHDLFile):
                    f.vcom_opt = self.vcom_opt


    def _process_manifest_includes(self):
        # Include dirs
        self.include_dirs = []
        if self.manifest_dict["include_dirs"] is not None:
            if isinstance(self.manifest_dict["include_dirs"], basestring):
                ll = os.path.relpath(os.path.abspath(os.path.join(self.path, self.manifest_dict["include_dirs"])))
                self.include_dirs.append(ll)
            else:
                ll = map(lambda x: os.path.relpath(os.path.abspath(os.path.join(self.path, x))),
                         self.manifest_dict["include_dirs"])
                self.include_dirs.extend(ll)
        # Analyze included dirs and report if any issue is found
        for dir_ in self.include_dirs:
            if path_mod.is_abs_path(dir_):
                logging.warning("%s contains absolute path to an include directory: %s" % (self.path, dir_))
            if not os.path.exists(dir_):
                logging.warning(self.path + " has an unexisting include directory: " + dir_)


    def _process_manifest_modules(self):
        # Fetch configuration
        if self.manifest_dict["fetchto"] is not None:
            fetchto = path_mod.rel2abs(self.manifest_dict["fetchto"], self.path)
            self.fetchto = fetchto
        else:
            fetchto = self.fetchto

        self.fetch_pre_cmd = self.manifest_dict["fetch_pre_cmd"]
        self.fetch_post_cmd = self.manifest_dict["fetch_post_cmd"]

        # Process required modules
        if "local" in self.manifest_dict["modules"]:
            local_paths = self._flatten_list(self.manifest_dict["modules"]["local"])
            local_mods = []
            for path in local_paths:
                if path_mod.is_abs_path(path):
                    logging.error("Found an absolute path (" + path + ") in a manifest"
                                  "(" + self.path + ")")
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
            self.manifest_dict["modules"]["svn"] = self._flatten_list(self.manifest_dict["modules"]["svn"])
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
            self.manifest_dict["modules"]["git"] = self._flatten_list(self.manifest_dict["modules"]["git"])
            git_mods = []
            for url in self.manifest_dict["modules"]["git"]:
                git_mods.append(self.pool.new_module(parent=self,
                                                     url=url,
                                                     source=fetch.GIT,
                                                     fetchto=fetchto))
            self.git = git_mods
        else:
            self.git = []

        # TODO: Git submodules are temporarly disabled until the expected behavior is depicted
        # git_submodule_dict = fetch.Git.get_git_submodules(self)
        # git_toplevel = fetch.Git.get_git_toplevel(self)
        # for submodule_key in git_submodule_dict.keys():
        #    url = git_submodule_dict[submodule_key]["url"]
        #    path = git_submodule_dict[submodule_key]["path"]
        #    path = os.path.join(git_toplevel, path)
        #    path = os.path.normpath(path)
        #    fetchto = os.path.sep.join(path.split(os.path.sep)[:-1])
        #    self.git_submodules.append(self.pool.new_module(parent=self,
        #                                                    url=url,
        #                                                    fetchto=fetchto,
        #                                                    source=fetch.GITSUBMODULE))


    def _process_manifest_altera(self):
        if self.manifest_dict["quartus_preflow"] != None:
            path = path_mod.rel2abs(self.manifest_dict["quartus_preflow"], self.path);
            if not os.path.exists(path):
                p.error("quartus_preflow file listed in " + self.manifest.path + " doesn't exist: "
                        + path + ".\nExiting.")
                quit()
            self.quartus_preflow = TCLFile(path)

        if self.manifest_dict["quartus_postmodule"] != None:
            path = path_mod.rel2abs(self.manifest_dict["quartus_postmodule"], self.path);
            if not os.path.exists(path):
                p.error("quartus_postmodule file listed in " + self.manifest.path + " doesn't exist: "
                        + path + ".\nExiting.")
                quit()
            self.quartus_postmodule = TCLFile(path)

        if self.manifest_dict["quartus_postflow"] != None:
            path = path_mod.rel2abs(self.manifest_dict["quartus_postflow"], self.path);
            if not os.path.exists(path):
                p.error("quartus_postflow file listed in " + self.manifest.path + " doesn't exist: "
                        + path + ".\nExiting.")
                quit()
            self.quartus_postflow = TCLFile(path)

        if "hw_tcl_filename" in self.manifest_dict:
            self.hw_tcl_filename = self.manifest_dict["hw_tcl_filename"]


    def _process_manifest_bitfile_targets(self):
        from .srcfile import SourceFileSet
        # Bit file targets
        self.bit_file_targets = SourceFileSet()
        if len(self.manifest_dict["bit_file_targets"]) != 0:
            paths = self._make_list_of_paths(self.manifest_dict["bit_file_targets"])
            self.bit_file_targets = self._create_file_list_from_paths(paths=paths)


    def _process_manifest_force_tool(self):
        if self.manifest_dict["force_tool"]:
            ft = self.manifest_dict["force_tool"]
            self.force_tool = ft.split(' ')
            if len(self.force_tool) != 3:
                logging.warning("Incorrect force_tool format %s. Ignoring" % self.force_tool)
                self.force_tool = None


    def _process_manifest_universal(self):
        if "top_module" in self.manifest_dict:
            self.top_module = self.manifest_dict["top_module"]
        # Libraries
        self.library = self.manifest_dict["library"]

        self.target = self.manifest_dict["target"].lower()
        self.action = self.manifest_dict["action"].lower()


    def _process_manifest_included_makefiles(self):
        # Included Makefiles
        mkFileList = []
        if isinstance(self.manifest_dict["incl_makefiles"], basestring):
            mkFileList.append(self.manifest_dict["incl_makefiles"])
        else:  # list
            mkFileList = self.manifest_dict["incl_makefiles"][:]

        makefiles_paths = self._make_list_of_paths(mkFileList)
        self.incl_makefiles.extend(makefiles_paths)


    def _make_list_of_paths(self, list_of_paths):
        paths = []
        for filepath in list_of_paths:
            if self._check_filepath(filepath):
                paths.append(path_mod.rel2abs(filepath, self.path))
        return paths

    def _check_filepath(self, filepath):
        if filepath:
            if path_mod.is_abs_path(filepath):
                logging.warning("Specified path seems to be an absolute path: %s\nOmitting." % filepath)
                return False
            filepath = os.path.join(self.path, filepath)
            if not os.path.exists(filepath):
                logging.error("Path specified in manifest in %s doesn't exist: %s" % (self.path, filepath))
                sys.exit("Exiting")


            filepath = path_mod.rel2abs(filepath, self.path)

            if os.path.isdir(filepath):
                logging.warning("Path specified in manifest %s is a directory: %s" % (self.path, filepath))
        return True

    def is_fetched_recursively(self):
        if not self.isfetched:
            return False
        for mod in self.submodules():
            if mod.is_fetched_recursively() is False:
                return False
        return True

    def make_list_of_modules(self):
        logging.debug("Making list of modules for " + str(self))
        new_modules = [self]
        modules = [self]
        while len(new_modules) > 0:
            cur_module = new_modules.pop()

            if not cur_module.isfetched:
                logging.error("Unfetched module in modules list: " + str(cur_module))
                quit()
            if cur_module.manifest is None:
                logging.debug("No manifest in " + str(cur_module))
                continue
            cur_module.parse_manifest()

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
            logging.debug("No modules were found in " + self.fetchto)
        return modules

    def _create_file_list_from_paths(self, paths):
        from .srcfile import SourceFileFactory, SourceFileSet
        sff = SourceFileFactory()
        srcs = SourceFileSet()
        for p in paths:
            if os.path.isdir(p):
                dir_ = os.listdir(p)
                for f_dir in dir_:
                    f_dir = os.path.join(self.path, p, f_dir)
                    if not os.path.isdir(f_dir):
                        srcs.add(sff.new(path=f_dir,
                                         module=self,
                                         library=self.library,
                                         vcom_opt=self.vcom_opt,
                                         vlog_opt=self.vlog_opt,
                                         include_dirs=self.include_dirs))
            else:
                srcs.add(sff.new(path=p,
                                 module=self,
                                 library=self.library,
                                 vcom_opt=self.vcom_opt,
                                 vlog_opt=self.vlog_opt,
                                 include_dirs=self.include_dirs))
        return srcs
