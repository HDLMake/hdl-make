# -*- coding: utf-8 -*-
#
# Copyright (c) 2013, 2014 CERN
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
#

from __future__ import print_function
#from dependable_file import DependableFile
import os
import logging

from .module import Module
from .util import path as path_mod
from .dep_file import DepFile, File


class SourceFile(DepFile):
    cur_index = 0

    def __init__(self, path, module, library=None):
        from .dep_file import DepFile
        assert isinstance(path, basestring)
        assert isinstance(module, Module)
        self.library = library
        if not library:
            self.library = "work"
        DepFile.__init__(self,
                         file_path=path,
                         module=module,
                         include_paths=module.include_dirs[:])

    def __hash__(self):
        return hash(self.path + self.library)


class VHDLFile(SourceFile):
    def __init__(self, path, module, library=None, vcom_opt=None):
        SourceFile.__init__(self, path=path, module=module, library=library)
        if not vcom_opt:
            self.vcom_opt = ""
        else:
            self.vcom_opt = vcom_opt

    def _check_encryption(self):
        f = open(self.path, "rb")
        s = f.read(3)
        f.close()
        if(s == b'Xlx'):
            return True
        else:
            return False


class VerilogFile(SourceFile):
    def __init__(self, path, module, library=None, vlog_opt=None, include_dirs=None):
        SourceFile.__init__(self, path=path, module=module, library=library)
        if not vlog_opt:
            self.vlog_opt = ""
        else:
            self.vlog_opt = vlog_opt
        self.include_dirs = []
        if include_dirs:
            self.include_dirs.extend(include_dirs)
        self.include_dirs.append(path_mod.relpath(self.dirname))
        self.provided_modules = []

class SVFile(VerilogFile):
    pass


class UCFFile(File):
    pass


class TCLFile(File):
    pass


class XISEFile(File):
    pass


class CDCFile(File):
    pass


class SignalTapFile(File):
    pass


class SDCFile(File):
    # Synopsys Design Constraints
    pass


class QIPFile(File):
    pass


class QSYSFile(File):
    # Qsys - Altera's System Integration Tool
    pass


class DPFFile(File):
    pass


class XMPFile(File):
    # Xilinx Embedded Micro Processor
    pass

class PPRFile(File):
    # Xilinx PlanAhead Project
    pass

class XPRFile(File):
    # Xilinx Vivado Project
    pass

class BDFile(File):
    # Xilinx Block Design
    pass

class XCOFile(File):
    # Xilinx Core Generator File
    pass

# class NGCFile(SourceFile):
#     def __init__(self, path, module):
#         SourceFile.__init__(self, path=path, module=module)
class NGCFile(File):
    # Xilinx Generated Netlist File
    pass

class LDFFile(File):
    # Lattice Diamond Project File
    pass

class LPFFile(File):
    # Lattice Preference/Constraint File
    pass

class EDFFile(File):
    # EDIF Netlist Files
    pass

class PDCFile(File):
    # Physical Design Constraints
    pass

class WBGenFile(File):
    pass

class QSFFile(File):
    # Quartus Settings File
    pass

class BSFFile(File):
    # Quartus Block Symbol File
    pass

class BDFFile(File):
    # Quartus Block Design File
    pass

class TDFFile(File):
    # Quartus Text Design File
    pass

class GDFFile(File):
    # Quartus Graphic Design File
    pass



class SourceFileSet(set):
    def __init__(self):
        super(SourceFileSet, self).__init__()
        self = []

    def __str__(self):
        return str([str(f) for f in self])

    def add(self, files):
        if isinstance(files, str):
            raise RuntimeError("Expected object, not a string")
        elif files is None:
            logging.debug("Got None as a file.\n Ommiting")
        else:
            try:
                for f in files:
                    super(SourceFileSet, self).add(f)
            except:  # single file, not a list
                super(SourceFileSet, self).add(files)

    def filter(self, type):
        out = SourceFileSet()
        for f in self:
            if isinstance(f, type):
                out.add(f)
        return out

    def inversed_filter(self, type):
        out = SourceFileSet()
        for f in self:
            if not isinstance(f, type):
                out.add(f)
        return out

    def get_libs(self):
        ret = set()
        for file in self:
            try:
                ret.add(file.library)
            except:
                pass
        return ret


class SourceFileFactory:
    def new(self, path, module, library=None, vcom_opt=None, vlog_opt=None, include_dirs=None):
        if path == "/home/pawel/cern/wr-cores/testbench/top_level/gn4124_bfm.svh":
            raise Exception()
        if path is None or path == "":
            raise RuntimeError("Expected a file path, got: "+str(path))
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        tmp = path.rsplit('.')
        extension = tmp[len(tmp)-1]
        logging.debug("add file " + path)

        nf = None
        if extension == 'vhd' or extension == 'vhdl' or extension == 'vho':
            nf = VHDLFile(path=path,
                          module=module,
                          library=library,
                          vcom_opt=vcom_opt)
        elif extension == 'v' or extension == 'vh' or extension == 'vo' or extension == 'vm':
            nf = VerilogFile(path=path,
                             module=module,
                             library=library,
                             vlog_opt=vlog_opt,
                             include_dirs=include_dirs)
        elif extension == 'sv' or extension == 'svh':
            nf = SVFile(path=path,
                        module=module,
                        library=library,
                        vlog_opt=vlog_opt,
                        include_dirs=include_dirs)
        elif extension == 'ngc':
            nf = NGCFile(path=path, module=module)
        elif extension == 'ucf':
            nf = UCFFile(path=path, module=module)
        elif extension == 'cdc':
            nf = CDCFile(path=path, module=module)
        elif extension == 'wb':
            nf = WBGenFile(path=path, module=module)
        elif extension == 'tcl':
            nf = TCLFile(path=path, module=module)
        elif extension == 'xise' or extension == 'ise':
            nf = XISEFile(path=path, module=module)
        elif extension == 'stp':
            nf = SignalTapFile(path=path, module=module)
        elif extension == 'sdc':
            nf = SDCFile(path=path, module=module)
        elif extension == 'qip':
            nf = QIPFile(path=path, module=module)
        elif extension == 'qsys':
            nf = QSYSFile(path=path, module=module)
        elif extension == 'dpf':
            nf = DPFFile(path=path, module=module)
        elif extension == 'xmp':
            nf = XMPFile(path=path, module=module)
        elif extension == 'ppr':
            nf = PPRFile(path=path, module=module)
        elif extension == 'xpr':
            nf = XPRFile(path=path, module=module)
        elif extension == 'bd':
            nf = BDFile(path=path, module=module)
        elif extension == 'xco':
            nf = XCOFile(path=path, module=module)
        elif extension == 'ldf':
            nf = LDFFile(path=path, module=module)
        elif extension == 'lpf':
            nf = LPFFile(path=path, module=module)
        elif extension == 'edf' or extension == 'edif' or extension == 'edi' or extension == 'edn':
            nf = EDFFile(path=path, module=module)
        elif extension == 'pdc':
            nf = PDCFile(path=path, module=module)
        elif extension == 'qsf':
            nf = QSFFile(path=path, module=module)
        elif extension == 'bsf':
            nf = BSFFile(path=path, module=module)
        elif extension == 'bdf':
            nf = BDFFile(path=path, module=module)
        elif extension == 'tdf':
            nf = TDFFile(path=path, module=module)
        elif extension == 'gdf':
            nf = GDFFile(path=path, module=module)
        return nf
