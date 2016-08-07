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

"""Module providing the source file class and a set of classes
representing the different possible files and file extensions"""

from __future__ import print_function
import os
import logging

from .module import Module
from .util import path as path_mod
from .dep_file import DepFile, File


class SourceFile(DepFile):

    """This is a class acting as a base for the different
    HDL sources files, i.e. those that can be parsed"""

    cur_index = 0

    def __init__(self, path, module, library):
        assert isinstance(path, basestring)
        assert isinstance(module, Module)
        self.library = library
        if not library:
            self.library = "work"
        DepFile.__init__(self,
                         file_path=path,
                         module=module)

    def __hash__(self):
        return hash(self.path + self.library)


class VHDLFile(SourceFile):

    """This is the class providing the generic VHDL file"""

    def __init__(self, path, module, library=None, vcom_opt=None):
        SourceFile.__init__(self, path=path, module=module, library=library)
        if not vcom_opt:
            self.vcom_opt = ""
        else:
            self.vcom_opt = vcom_opt

    def _check_encryption(self):
        """Check if the VHDL is encrypted (in Xilinx toolchain)"""
        file_aux = open(self.path, "rb")
        text = file_aux.read(3)
        file_aux.close()
        if text == b'Xlx':
            return True
        else:
            return False


class VerilogFile(SourceFile):

    """This is the class providing the generic Verilog file"""

    def __init__(self, path, module, library=None,
                 vlog_opt=None, include_dirs=None):
        SourceFile.__init__(self, path=path, module=module, library=library)
        if not vlog_opt:
            self.vlog_opt = ""
        else:
            self.vlog_opt = vlog_opt
        self.include_dirs = []
        if include_dirs:
            self.include_dirs.extend(include_dirs)
        self.include_dirs.append(path_mod.relpath(self.dirname))


class SVFile(VerilogFile):
    """This is the class providing the generic SystemVerilog file"""
    pass


class UCFFile(File):
    """This is the class providing the User Constraint Guide file"""
    pass


class TCLFile(File):
    """This is the class providing the Tool Command Language file"""
    pass


class XISEFile(File):
    """This is the class providing the new Xilinx ISE project file"""
    pass


class CDCFile(File):
    """This is the class providing the Xilinx ChipScope Definition
    and Connection file"""
    pass


class SignalTapFile(File):
    """This is the class providing the Altera Signal Tap Language file"""
    pass


class SDCFile(File):
    """Synopsys Design Constraints"""
    pass


class QIPFile(File):
    """This is the class providing the Altera Quartus IP file"""
    pass


class QSYSFile(File):
    """Qsys - Altera's System Integration Tool"""
    pass


class DPFFile(File):
    """This is the class providing Altera Quartus Design Protocol File"""
    pass


class XMPFile(File):
    """Xilinx Embedded Micro Processor"""
    pass


class PPRFile(File):
    """Xilinx PlanAhead Project"""
    pass


class XPRFile(File):
    """Xilinx Vivado Project"""
    pass


class BDFile(File):
    """Xilinx Block Design"""
    pass


class XCOFile(File):
    """Xilinx Core Generator File"""
    pass


class NGCFile(File):
    """Xilinx Generated Netlist File"""
    pass


class LDFFile(File):
    """Lattice Diamond Project File"""
    pass


class LPFFile(File):
    """Lattice Preference/Constraint File"""
    pass


class EDFFile(File):
    """EDIF Netlist Files"""
    pass


class PDCFile(File):
    """Physical Design Constraints"""
    pass


class WBGenFile(File):
    """Wishbone generator file"""
    pass


class QSFFile(File):
    """Quartus Settings File"""
    pass


class BSFFile(File):
    """Quartus Block Symbol File"""
    pass


class BDFFile(File):
    """Quartus Block Design File"""
    pass


class TDFFile(File):
    """Quartus Text Design File"""
    pass


class GDFFile(File):
    """Quartus Graphic Design File"""
    pass


class SourceFileSet(set):

    """Class providing a extension of the 'set' object that includes
    methods that allow for an easier management of a collection of HDL
    source files"""

    def __init__(self):
        super(SourceFileSet, self).__init__()
        self = []

    def __str__(self):
        return str([str(f) for f in self])

    def add(self, files):
        """Add a set of files to the source fileset instance"""
        if isinstance(files, str):
            raise RuntimeError("Expected object, not a string")
        elif files is None:
            logging.debug("Got None as a file.\n Ommiting")
        else:
            try:
                for file_aux in files:
                    super(SourceFileSet, self).add(file_aux)
            except TypeError:  # single file, not a list
                super(SourceFileSet, self).add(files)

    def filter(self, filetype):
        """Method that filters and returns all of the HDL source files
        contained in the instance SourceFileSet matching the provided type"""
        out = SourceFileSet()
        for file_aux in self:
            if isinstance(file_aux, filetype):
                out.add(file_aux)
        return out

    def inversed_filter(self, filetype):
        """Method that filters and returns all of the HDL source files
        contained in the instance SourceFileSet NOT matching the provided
        type"""
        out = SourceFileSet()
        for file_aux in self:
            if not isinstance(file_aux, filetype):
                out.add(file_aux)
        return out

    def get_libs(self):
        """Method that returns a set containing all of the libraries that are
        provided by any of the source files in the SourceFileSet"""
        ret = set()
        for file_aux in self:
            try:
                ret.add(file_aux.library)
            except TypeError:
                pass
        return ret


def create_source_file(path, module, library=None,
        vcom_opt=None, vlog_opt=None, include_dirs=None):
    """Function that analyzes the given arguments and returns a new HDL source
    file of the appropriated type"""
    if path is None or path == "":
        raise RuntimeError("Expected a file path, got: " + str(path))
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    tmp = path.rsplit('.')
    extension = tmp[len(tmp) - 1]
    logging.debug("add file " + path)

    new_file = None
    if extension in ['vhd', 'vhdl', 'vho']:
        new_file = VHDLFile(path=path,
                            module=module,
                            library=library,
                            vcom_opt=vcom_opt)
    elif extension in ['v', 'vh', 'vo', 'vm']:
        new_file = VerilogFile(path=path,
                               module=module,
                               library=library,
                               vlog_opt=vlog_opt,
                               include_dirs=include_dirs)
    elif extension == 'sv' or extension == 'svh':
        new_file = SVFile(path=path,
                          module=module,
                          library=library,
                          vlog_opt=vlog_opt,
                          include_dirs=include_dirs)
    elif extension == 'ngc':
        new_file = NGCFile(path=path, module=module)
    elif extension == 'ucf':
        new_file = UCFFile(path=path, module=module)
    elif extension == 'cdc':
        new_file = CDCFile(path=path, module=module)
    elif extension == 'wb':
        new_file = WBGenFile(path=path, module=module)
    elif extension == 'tcl':
        new_file = TCLFile(path=path, module=module)
    elif extension == 'xise' or extension == 'ise':
        new_file = XISEFile(path=path, module=module)
    elif extension == 'stp':
        new_file = SignalTapFile(path=path, module=module)
    elif extension == 'sdc':
        new_file = SDCFile(path=path, module=module)
    elif extension == 'qip':
        new_file = QIPFile(path=path, module=module)
    elif extension == 'qsys':
        new_file = QSYSFile(path=path, module=module)
    elif extension == 'dpf':
        new_file = DPFFile(path=path, module=module)
    elif extension == 'xmp':
        new_file = XMPFile(path=path, module=module)
    elif extension == 'ppr':
        new_file = PPRFile(path=path, module=module)
    elif extension == 'xpr':
        new_file = XPRFile(path=path, module=module)
    elif extension == 'bd':
        new_file = BDFile(path=path, module=module)
    elif extension == 'xco':
        new_file = XCOFile(path=path, module=module)
    elif extension == 'ldf':
        new_file = LDFFile(path=path, module=module)
    elif extension == 'lpf':
        new_file = LPFFile(path=path, module=module)
    elif extension in ['edf', 'edif', 'edi', 'edn']:
        new_file = EDFFile(path=path, module=module)
    elif extension == 'pdc':
        new_file = PDCFile(path=path, module=module)
    elif extension == 'qsf':
        new_file = QSFFile(path=path, module=module)
    elif extension == 'bsf':
        new_file = BSFFile(path=path, module=module)
    elif extension == 'bdf':
        new_file = BDFFile(path=path, module=module)
    elif extension == 'tdf':
        new_file = TDFFile(path=path, module=module)
    elif extension == 'gdf':
        new_file = GDFFile(path=path, module=module)
    return new_file
