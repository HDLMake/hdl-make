#!/usr/bin/python
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

import os
import msg as p
import path
import global_mod

class ModulePool(list):
    class ModuleFetcher:
        def __init__(self):
            pass
        def fetch_single_module(self, module):
            import global_mod
            new_modules = []
            p.vprint("Fetching module: " + str(module))

            if module.source == "local":
                p.vprint("ModPath: " + module.path)
            else:
                p.printhr()
                p.info("Fetching module: " + str(module) +\
                    " [parent: " + str(module.parent) + "]")
                if module.source == "svn":
                    p.info("[svn] Fetching to " + module.fetchto)
                    self.__fetch_from_svn(module)
                if module.source == "git":
                    p.info("[git] Fetching to " + module.fetchto)
                    self.__fetch_from_git(module)

            module.parse_manifest()

            new_modules.extend(module.local)
            new_modules.extend(module.svn)
            new_modules.extend(module.git)
            return new_modules

        def __fetch_from_svn(self, module):
            if not os.path.exists(module.fetchto):
                os.mkdir(module.fetchto)

            cur_dir = os.getcwd()
            os.chdir(module.fetchto)

            cmd = "svn checkout {0} " + module.basename
            if module.revision:
                cmd = cmd.format(module.url + '@' + module.revision)
            else:
                cmd = cmd.format(module.url)

            rval = True

            p.vprint(cmd)
            if os.system(cmd) != 0:
                rval = False
            os.chdir(cur_dir)

            module.isfetched = True
            module.path = os.path.join(module.fetchto, module.basename)
            return rval

        def __fetch_from_git(self, module):
            if not os.path.exists(module.fetchto):
                os.mkdir(module.fetchto)

            cur_dir = os.getcwd()
            if module.branch == None:
                module.branch = "master"

            basename = path.url_basename(module.url)
            mod_path = os.path.join(module.fetchto, basename)

            if basename.endswith(".git"):
                basename = basename[:-4] #remove trailing .git

            if module.isfetched:
                update_only = True
            else:
                update_only = False

            if update_only:
                cmd = "(cd {0} && git checkout {1})"
                cmd = cmd.format(mod_path, module.branch)
            else:
                cmd = "(cd {0} && git clone -b {2} {1})"
                cmd = cmd.format(module.fetchto, module.url, module.branch)

            rval = True

            p.vprint(cmd)
            if os.system(cmd) != 0:
                rval = False

            if module.revision and rval:
                os.chdir(mod_path)
                cmd = "git checkout " + module.revision
                p.vprint(cmd)
                if os.system(cmd) != 0:
                    rval = False
                os.chdir(cur_dir)

            module.isfetched = True
            module.path = mod_path
            return rval


    def __init__(self, *args):
        list.__init__(self, *args)
        self.top_module = None 
        self.global_fetch = os.getenv("HDLMAKE_COREDIR")

    def get_fetchable_modules(self):
        return [m for m in self if m.source != "local"]

    def __str__(self):
        return str([str(m) for m in self])

    def __contains(self, module):
        for mod in self:
            if mod.url == module.url:
                return True
        return False
        
    def new_module(self, parent, url, source, fetchto):
        from module import Module
        if url in [m.url for m in self]:
            return [m for m in self if m.url == url][0]
        else:
            if self.global_fetch:            # if there is global fetch parameter (HDLMAKE_COREDIR env variable)
                fetchto  = self.global_fetch # screw module's particular fetchto
            elif global_mod.top_module:
                fetchto = global_mod.top_module.fetchto

            new_module = Module(parent=parent, url=url, source=source, fetchto=fetchto, pool=self)
            self._add(new_module)
            if not self.top_module:
                global_mod.top_module = new_module
                self.top_module = new_module
                new_module.parse_manifest()
            return new_module

    def _add(self, new_module):
        from module import Module
        if not isinstance(new_module, Module):
            raise RuntimeError("Expecting a Module instance")
        if self.__contains(new_module):
            return False
        if new_module.isfetched:
            for mod in new_module.submodules():
                self._add(mod)
        self.append(new_module)
        return True

    def fetch_all(self, unfetched_only = False):
        fetcher = self.ModuleFetcher()
        fetch_queue = [m for m in self]

        while len(fetch_queue) > 0:
            cur_mod = fetch_queue.pop()
            new_modules = []
            if unfetched_only:
                if cur_mod.isfetched:
                    new_modules = cur_mod.submodules()
                else:
                    new_modules = fetcher.fetch_single_module(cur_mod)
            else:
                new_modules = fetcher.fetch_single_module(cur_mod)
            for mod in new_modules:
                if not mod.isfetched:
                    p.vprint("Appended to fetch queue: " +str(mod.url))
                    self._add(mod)
                    fetch_queue.append(mod)
                else:
                    p.vprint("NOT appended to fetch queue: " +str(mod.url))

    def build_global_file_list(self):
        from srcfile import SourceFileSet
        ret = SourceFileSet()
        for module in self:
            ret.add(module.files)
        return ret

    def build_very_global_file_list(self):
        from srcfile import SourceFileFactory, VerilogFile
        sff = SourceFileFactory()

        files = self.build_global_file_list()
        extra_verilog_files = set() 
        manifest_verilog_files = files.filter(VerilogFile)
        queue = manifest_verilog_files

        while len(queue) > 0:
            verilog_file = queue.pop()
            for f_required in verilog_file.dep_requires:
                new_vl = sff.new(os.path.join(verilog_file.dirname, f_required))
                queue.append(new_vl)
                if f_required not in extra_verilog_files and \
                    f_required not in manifest_verilog_files:
                    extra_verilog_files.add(new_vl)

        p.vprint("Extra verilog files, not listed in manifests:")
        for extra_vl in extra_verilog_files:
            p.vprint(str(extra_vl))
        for extra_vl in extra_verilog_files:
            files.add(extra_vl)
        return files

    def get_top_module(self):
        return self.top_module

    def is_everything_fetched(self):
        if len([m for m in self if not m.isfetched]) == 0:
            return True
        else:
            return False
