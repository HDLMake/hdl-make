#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
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
from manifest_parser import Manifest, ManifestParser
from srcfile import VerilogFile, VHDLFile, SourceFileFactory, SourceFileSet
from util import path as path_mod
import os
import global_mod
import logging
import fetch
import sys


class Module(object):
    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, value):
        if value not in ["svn", "git", "local"]:
            raise ValueError("Inproper source: " + value)
        self._source = value

    @source.deleter
    def source(self):
        del self._source

    @property
    def basename(self):
        from util import path
        if self.source == "svn":
            return path.svn_basename(self.url)
        else:
            return path.url_basename(self.url)

    #PLEASE don't use this constructor. Create all modules with ModulePool.new_module()
    def __init__(self, parent, url, source, fetchto, pool):
        from util import path

        assert url is not None
        assert source is not None

        self.manifest_dict = None
        self.fetchto = fetchto
        self.pool = pool
        self.source = source
        self.parent = parent
        self.isparsed = False
        self.include_dirs = None
        self.library = "work"
        self.local = []
        self.git = []
        self.svn = []
        self.target = None
        self.action = None
        self.vmap_opt = None
        self.vlog_opt = None
        self.vcom_opt = None
        self.revision = None
        self._files = None
        self.manifest = None
        self.incl_makefiles = []
        self.force_tool = None
        self.syn_device = None
        self.syn_grade = None
        self.syn_package = None
        self.syn_project = None
        self.syn_top = None
        self.syn_ise_version = None
        self.syn_pre_script = None
        self.syn_post_script = None
        self.sim_only_files = None
        self.sim_pre_script = None
        self.sim_post_script = None
        self.top_module = None
        self.commit_id = None

        if source != "local":
            self.url, self.branch, self.revision = path.url_parse(url)
        else:
            self.url, self.branch, self.revision = url, None, None

        if source == "local" and not os.path.exists(url):
            logging.error("Path to the local module doesn't exist:\n" + url
                          + "\nThis module was instantiated in: " + str(parent))
            quit()

        if source == "local":
            self.path = url
            self.isfetched = True
        else:
            if os.path.exists(os.path.abspath(os.path.join(fetchto, self.basename))):
                self.path = os.path.abspath(os.path.join(fetchto, self.basename))
                self.isfetched = True
            else:
                self.path = None
                self.isfetched = False

        if self.path is not None:
            self.manifest = self._search_for_manifest()
        else:
            self.manifest = None

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
        import os

        logging.debug("Removing " + self.path)
        shutil.rmtree(self.path)

        while True:
            try:
                logging.debug("Trying to remove " + os.path.dirname(self.path))
                os.rmdir(os.path.dirname(self.path))
            except OSError:  # a catologue is not empty - we are done
                break

    def parse_manifest(self):
        if self.manifest_dict:
            return
        logging.debug(self.path)
        if self.isparsed is True or self.isfetched is False:
            return
        if self.manifest is None:
            self.manifest = self._search_for_manifest()
        if self.path is None:
            raise RuntimeError()

        manifest_parser = ManifestParser()

        manifest_parser.add_arbitrary_code(global_mod.options.arbitrary_code)

        if self.manifest is None:
            logging.debug("No manifest found in module "+str(self))
        else:
            manifest_parser.add_manifest(self.manifest)

        if self.parent is None:
            allow_unknown = True
            extra_context = {}
        else:
            allow_unknown = False
            extra_context = dict(global_mod.top_module.manifest_dict)  # copy the dictionary
            del extra_context["modules"]
            del extra_context["files"]
            del extra_context["include_dirs"]
            del extra_context["sim_only_files"]
            del extra_context["incl_makefiles"]
            del extra_context["bit_file_targets"]
            del extra_context["library"]
        extra_context["__manifest"] = self.path

        opt_map = None
        try:
            opt_map = manifest_parser.parse(allow_unknown=allow_unknown,
                                            extra_context=extra_context)
        except NameError as ne:
            logging.error("Error while parsing {0}:\n{1}: {2}.".format(self.manifest, type(ne), ne))
            quit()
        self.manifest_dict = opt_map

    def process_manifest(self):
        if self.manifest_dict is None:
            logging.debug("there is no manifest to be processed")
            return
        logging.debug(self.path)
        if self.manifest_dict["syn_ise_version"] is not None:
            version = self.manifest_dict["syn_ise_version"]
            self.syn_ise_version = str(version)
        if self.manifest_dict["fetchto"] is not None:
            fetchto = path_mod.rel2abs(self.manifest_dict["fetchto"], self.path)
            self.fetchto = fetchto
        else:
            fetchto = self.fetchto

        if "local" in self.manifest_dict["modules"]:
            local_paths = self._flatten_list(self.manifest_dict["modules"]["local"])
            local_mods = []
            for path in local_paths:
                if path_mod.is_abs_path(path):
                    logging.error("Found an absolute path (" + path + ") in a manifest"
                                  "(" + self.path + ")")
                    quit()
                path = path_mod.rel2abs(path, self.path)
                local_mods.append(self.pool.new_module(parent=self, url=path, source="local", fetchto=fetchto))
            self.local = local_mods
        else:
            self.local = []

        self.vmap_opt = self.manifest_dict["vmap_opt"]
        self.vcom_opt = self.manifest_dict["vcom_opt"]
        self.vsim_opt = self.manifest_dict["vsim_opt"]
        self.vlog_opt = self.manifest_dict["vlog_opt"]
        self.iverilog_opt = self.manifest_dict["iverilog_opt"]
        self.sim_tool = self.manifest_dict["sim_tool"]
        if self.manifest_dict["force_tool"]:
            ft = self.manifest_dict["force_tool"]
            self.force_tool = ft.split(' ')
            if len(self.force_tool) != 3:
                logging.warning("Incorrect force_tool format %s. Ignoring" % self.force_tool)
                self.force_tool = None

        if "top_module" in self.manifest_dict:
            self.top_module = self.manifest_dict["top_module"]

        mkFileList = []
        if isinstance(self.manifest_dict["incl_makefiles"], basestring):
            mkFileList.append(self.manifest_dict["incl_makefiles"])
        else:  # list
            mkFileList = self.manifest_dict["incl_makefiles"][:]

        makefiles_paths = self._make_list_of_paths(mkFileList)
        self.incl_makefiles.extend(makefiles_paths)

        #if self.vlog_opt == "":
        #    self.vlog_opt = global_mod.top_module.vlog_opt
        #if self.vcom_opt == "":
        #    self.vcom_opt = global_mod.top_module.vcom_opt
        #if self.vsim_opt == "":
        #    self.vsim_opt = global_mod.top_module.vsim_opt
       # if self.vmap_opt == "":
        #    self.vmap_opt = global_mod.top_module.vmap_opt

        self.library = self.manifest_dict["library"]
        self.include_dirs = []
        if self.manifest_dict["include_dirs"] is not None:
            if isinstance(self.manifest_dict["include_dirs"], basestring):
#                self.include_dirs.append(self.manifest_dict["include_dirs"])
                ll = os.path.relpath(os.path.abspath(os.path.join(self.path, self.manifest_dict["include_dirs"])))
                self.include_dirs.append(ll)
            else:
#                self.include_dirs.extend(self.manifest_dict["include_dirs"])
                ll = map(lambda x: os.path.relpath(os.path.abspath(os.path.join(self.path, x))),
                         self.manifest_dict["include_dirs"])
                self.include_dirs.extend(ll)

        for dir in self.include_dirs:
            if path_mod.is_abs_path(dir):
                logging.warning("%s contains absolute path to an include directory: %s" % (self.path, dir))
            if not os.path.exists(dir):
                logging.warning(self.path + " has an unexisting include directory: " + dir)

        if self.manifest_dict["files"] == []:
            self.files = SourceFileSet()
            logging.debug("No files in the manifest")
        else:
            self.manifest_dict["files"] = self._flatten_list(self.manifest_dict["files"])
            logging.debug(self.path + str(self.manifest_dict["files"]))
            paths = self._make_list_of_paths(self.manifest_dict["files"])
            self.files = self._create_file_list_from_paths(paths=paths)
            for f in self.files:
                if isinstance(f, VerilogFile):
                    f.vsim_opt = self.vsim_opt
                elif isinstance(f, VHDLFile):
                    f.vcom_opt = self.vcom_opt

        if len(self.manifest_dict["sim_only_files"]) == 0:
            self.sim_only_files = SourceFileSet()
        else:
            self.manifest_dict["sim_only_files"] = self._flatten_list(self.manifest_dict["sim_only_files"])
            paths = self._make_list_of_paths(self.manifest_dict["sim_only_files"])
            self.sim_only_files = self._create_file_list_from_paths(paths=paths)

        self.syn_pre_cmd = self.manifest_dict["syn_pre_cmd"]
        self.syn_post_cmd = self.manifest_dict["syn_post_cmd"]
        self.sim_pre_cmd = self.manifest_dict["sim_pre_cmd"]
        self.sim_post_cmd = self.manifest_dict["sim_post_cmd"]

        self.bit_file_targets = SourceFileSet()
        if len(self.manifest_dict["bit_file_targets"]) != 0:
            paths = self._make_list_of_paths(self.manifest_dict["bit_file_targets"])
            self.bit_file_targets = self._create_file_list_from_paths(paths=paths)

        if "svn" in self.manifest_dict["modules"]:
            self.manifest_dict["modules"]["svn"] = self._flatten_list(self.manifest_dict["modules"]["svn"])
            svn_mods = []
            for url in self.manifest_dict["modules"]["svn"]:
                svn_mods.append(self.pool.new_module(parent=self, url=url, source="svn", fetchto=fetchto))
            self.svn = svn_mods
        else:
            self.svn = []

        if "git" in self.manifest_dict["modules"]:
            self.manifest_dict["modules"]["git"] = self._flatten_list(self.manifest_dict["modules"]["git"])
            git_mods = []
            for url in self.manifest_dict["modules"]["git"]:
                git_mods.append(self.pool.new_module(parent=self, url=url, source="git", fetchto=fetchto))
            self.git = git_mods
        else:
            self.git = []

        self.target = self.manifest_dict["target"].lower()
        self.action = self.manifest_dict["action"].lower()

        if self.manifest_dict["syn_name"] is None and self.manifest_dict["syn_project"] is not None:
            self.syn_name = self.manifest_dict["syn_project"][:-5]  # cut out .xise from the end
        else:
            self.syn_name = self.manifest_dict["syn_name"]
        self.syn_device = self.manifest_dict["syn_device"]
        self.syn_grade = self.manifest_dict["syn_grade"]
        self.syn_package = self.manifest_dict["syn_package"]
        self.syn_project = self.manifest_dict["syn_project"]
        self.syn_top = self.manifest_dict["syn_top"]

        self.isparsed = True

        for m in self.submodules():
            m.parse_manifest()
            m.process_manifest()

        if self == global_mod.top_module:
            revision = fetch.Svn.check_revision_number(self.path)
            if revision is None:
                commit = fetch.Git.check_commit_id(self.path)
                self.revision = commit
            else:
                self.revision = revision
        else:
            if self.source == "svn":
                self.revision = fetch.Svn.check_revision_number(self.path)
            elif self.source == "git":
                self.revision = fetch.Git.check_commit_id(self.path)

    def _make_list_of_paths(self, list_of_paths):
        paths = []
        logging.debug(str(list_of_paths))
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
                logging.error("Path specified in %s doesn't exist: %s" % (self.path, filepath))
                sys.exit("Exiting")


            filepath = path_mod.rel2abs(filepath, self.path)

            if os.path.isdir(filepath):
                logging.warning("Path specified in %s is a directory: %s" % (self.path, filepath))
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
        sff = SourceFileFactory()
        srcs = SourceFileSet()
        for p in paths:
            if os.path.isdir(p):
                dir = os.listdir(p)
                for f_dir in dir:
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

    def build_global_file_list(self):
        f_set = SourceFileSet()
        modules = self.make_list_of_modules()
        for m in modules:
            f_set.add(m.files)

        return f_set
