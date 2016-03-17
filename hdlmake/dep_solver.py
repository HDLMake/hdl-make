# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Modified to allow ISim simulation by Lucas Russo (lucas.russo@lnls.br)
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
#

import re
import os
import logging

from . import global_mod
from .srcfile import SourceFileFactory, SourceFileSet, SourceFile
from .srcfile import VHDLFile, VerilogFile, SVFile
from .dependable_file import DependableFile


class DependencySolver(object):
    def __init__(self):
        self.entities = {}

    def _find_provider_file(self, req, vhdl_file, fset):
        raise NotImplementedError()

    def solve(self):
        raise NotImplementedError()


class VHDLDependencySolver(DependencySolver):
    def _find_provider_file(self, req, vhdl_file, fset):
        assert isinstance(req, tuple)
        assert isinstance(vhdl_file, VHDLFile)
        for f in fset:
            if req in f.dep_provides:
                return f

        return None

    def solve(self, vhdl_files):
        for f in vhdl_files:
            logging.debug("solving deps for " + f.path)
            if f.dep_requires:
                for req in f.dep_requires:
                    pf = self._find_provider_file(req=req, vhdl_file=f, fset=vhdl_files)
                    assert isinstance(pf, SourceFile)
                    if not pf:
                        logging.error("Missing dependency in file "+str(f)+": " + req[0]+'.'+req[1])
                    else:
                        logging.debug("%s depends on %s" % (f.path, pf.path))
                        if pf.path != f.path:
                            f.dep_depends_on.append(pf)
            #get rid of duplicates by making a set from the list and vice versa
            f.dep_depends_on = list(set(f.dep_depends_on))
            f.dep_resolved = True


class VerilogDependencySolver(DependencySolver):
    def solve(self, verilog_files):
        assert isinstance(verilog_files, list)
        assert len(verilog_files) == 0 or isinstance(verilog_files[0], VerilogFile)
        for f in verilog_files:
            logging.debug("solving deps for " + f.path)
            if f.dep_requires:
                for req in f.dep_requires:
                    pf = self._find_provider_file(req, f, verilog_files)
                    if not pf:
                        logging.warning("Cannot find depending for file "+str(f)+": "+req)
                    else:
                        logging.debug("%s depends on %s " % (f.path, pf.path))
                        f.dep_depends_on.append(pf)
            f.dep_resolved = True
            #get rid of duplicates by making a set from the list and vice versa
            f.dep_depends_on = list(set(f.dep_depends_on))

    def _find_provider_file(self, req, v_file, fset):
        assert isinstance(v_file, VerilogFile)
        assert isinstance(fset, list)

        sff = SourceFileFactory()
        #TODO: Can this be done elsewhere?
        if global_mod.top_module.sim_tool == "iverilog":
            for f in fset:
                if f.rel_path() == os.path.relpath(req):
                    return f
            return sff.new(req, module=None)

        import os
        vf_dirname = v_file.dirname
        h_file = os.path.join(vf_dirname, req)
        if os.path.exists(h_file) and not os.path.isdir(h_file):
            return sff.new(h_file, v_file.module)

        inc_dirs = self._parse_vlog_opt(v_file.vlog_opt)

        for dir in inc_dirs:
            dir = os.path.join(global_mod.current_path, dir)
            if not os.path.exists(dir) or not os.path.isdir(dir):
                logging.warning("Include path "+dir+" doesn't exist")
                continue
            h_file = os.path.join(dir, req)
            if os.path.exists(h_file) and not os.path.isdir(h_file):
                return sff.new(h_file, module=v_file.module)
        return None

    def _parse_vlog_opt(self, vlog_opt):
        assert isinstance(vlog_opt, basestring)
        ret = []
        inc_vsim_vlog = re.compile(".*?\+incdir\+([^ ]+)")
        # Either a normal (non-special) character or an escaped special character repeated >= 1 times
        #unix_path = re.compile(r"([^\0 \!\$\`\&\*\(\)\+]|\\(:? |\!|\$|\`|\&|\*|\(|\)|\+))+")

        # -i <unix_path> one or more times
        inc_isim_vlog = re.compile(r"\s*\-i\s*((\w|/|\\ |\.|\.\.)+)\s*")
        vlog_vsim_opt = vlog_opt
        # Try ModelSim include format (+incdir+<path>)
        while True:
            vsim_inc = re.match(inc_vsim_vlog, vlog_vsim_opt)
            if vsim_inc:
                ret.append(vsim_inc.group(1))
                vlog_vsim_opt = vlog_vsim_opt[vsim_inc.end():]
            else:
                break

        # Could use vlog_opt directly here
        # Try ISim include format (-i <path>)
        if not ret:
            vlog_isim_opt = vlog_opt
            while True:
                isim_inc = re.match(inc_isim_vlog, vlog_isim_opt)
                if isim_inc:
                    ret.append(isim_inc.group(1))
                    vlog_isim_opt = vlog_isim_opt[isim_inc.end():]
                else:
                    break

            logging.debug("Include paths are: " + ' '.join(ret))
        return ret


class SVDependencySolver(VerilogDependencySolver):
    def solve(self, sv_files):
        assert len(sv_files) == 0 or isinstance(sv_files[0], VerilogFile)
        for f in sv_files:
            stack = f.dep_depends_on[:]
            while stack:
                qf = stack.pop(0)
                if qf.dep_requires:
                    f.dep_requires.extend(qf.dep_requires)
                    for req in qf.dep_requires:
                        pf = self._find_provider_file(req, f, [])
                        if not pf:
                            logging.warning("Cannot find include for file "+str(f)+": "+req)
                        else:
                            logging.debug("%s is provider file for %s", pf.path, f.path)
                            f.dep_depends_on.append(pf)
                            stack.append(pf)
             #get rid of duplicates by making a set from the list and vice versa
            f.dep_depends_on = list(set(f.dep_depends_on))
            f.dep_resolved = True


def _lookup_provider_index(files, start_index, srcfile):
    assert isinstance(start_index, int)
    assert isinstance(srcfile, SourceFile)
    requires = srcfile.dep_requires
    if not requires:
        return None
    for cur_idx in xrange(start_index, len(files)):
        if type(files[cur_idx]) == type(srcfile):
            for req in requires:
                if req in files[cur_idx].dep_provides:
                    return cur_idx
    return None


def solve(fileset):
    assert isinstance(fileset, SourceFileSet)

    n_iter = 0
    max_iter = 100
    import copy

    fset = fileset.filter(DependableFile)
    independent_files = []

    done = False
    while not done and (n_iter < max_iter):
        n_iter = n_iter+1
        done = True
        for f in fset:
            idx = fset.index(f)
            k = _lookup_provider_index(files=fset, start_index=idx+1, srcfile=f)

            if k:
                done = False
                #swap
                fset[idx], fset[k] = fset[k], fset[idx]

    if(n_iter == max_iter):
        logging.error("Maximum number of iterations reached when trying to solve the dependencies.\n"
                      "Perhaps a cyclic inter-dependency problem.")
        return None

    for f in fset:
        if not f.dep_requires:
            independent_files.append(copy.copy(f))
            del f

    independent_files.sort(key=lambda f: f.dep_index)
    vhdl_files = [file for file in fset if isinstance(file, VHDLFile)]
    vhdl_solver = VHDLDependencySolver()
    vhdl_solver.solve(vhdl_files)

    from . import srcfile as sf

    verilog_files = [file for file in fset if isinstance(file, VerilogFile)]
    verilog_solver = VerilogDependencySolver()
    verilog_solver.solve(verilog_files)

    sv_files = [file for file in fset if isinstance(file, SVFile)]
    sv_solver = SVDependencySolver()
    sv_solver.solve(sv_files)

    sorted_list = sf.SourceFileSet()
    sorted_list.add(independent_files)
    sorted_list.add(fset)

    for k in sorted_list:
        logging.debug("DEP_IDX " + str(k.dep_index) + " " + k.path)
    return sorted_list
