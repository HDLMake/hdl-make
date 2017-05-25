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
from __future__ import absolute_import
import os
import logging

from .util import path as path_mod
from .dep_file import DepFile, File
import six


class SourceFile(DepFile):

    """This is a class acting as a base for the different
    HDL sources files, i.e. those that can be parsed"""

    cur_index = 0

    def __init__(self, path, module, library):
        assert isinstance(path, six.string_types)
        self.library = library
        if not library:
            self.library = "work"
        DepFile.__init__(self,
                         file_path=path,
                         module=module)

    def __hash__(self):
        return hash(self.path + self.library)


# SOURCE FILES

class VHDLFile(SourceFile):

    """This is the class providing the generic VHDL file"""

    def __init__(self, path, module, library=None):
        SourceFile.__init__(self, path=path, module=module, library=library)
        from hdlmake.vhdl_parser import VHDLParser
        self.parser = VHDLParser(self)

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
                 include_dirs=None):
        SourceFile.__init__(self, path=path, module=module, library=library)
        from hdlmake.vlog_parser import VerilogParser
        self.include_dirs = []
        if include_dirs:
            self.include_dirs.extend(include_dirs)
        self.include_dirs.append(path_mod.relpath(self.dirname))
        self.parser = VerilogParser(self)
        for dir_aux in self.include_paths:
            self.parser.add_search_path(dir_aux)


class SVFile(VerilogFile):
    """This is the class providing the generic SystemVerilog file"""
    pass


# TCL COMMAND FILE

class TCLFile(File):
    """This is the class providing the Tool Command Language file"""
    pass


# XILINX FILES

class UCFFile(File):
    """This is the class providing the User Constraint Guide file"""
    pass


class XISEFile(File):
    """This is the class providing the new Xilinx ISE project file"""
    pass


class CDCFile(File):
    """This is the class providing the Xilinx ChipScope Definition
    and Connection file"""
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


class XDCFile(File):
    """Xilinx Design Constraint File"""
    pass


class COEFile(File):
    """Xilinx Coefficient File"""
    pass


class MIFFile(File):
    """Xilinx Memory Initialization File"""
    pass


class RAMFile(File):
    """Xilinx RAM  File"""
    pass


class VHOFile(File):
    """Xilinx VHDL Template File"""
    pass


class VEOFile(File):
    """Xilinx Verilog Template File"""
    pass


class XCIFile(File):
    """Xilinx Core IP File"""
    pass


XILINX_FILE_DICT = {
    'xise': XISEFile,
    'ise': XISEFile,
    'ngc': NGCFile,
    'ucf': UCFFile,
    'cdc': CDCFile,
    'xmp': XMPFile,
    'ppr': PPRFile,
    'xpr': XPRFile,
    'bd': BDFile,
    'xco': XCOFile,
    'xdc': XDCFile,
    'coe': COEFile,
    'mif': MIFFile,
    'ram': RAMFile,
    'vho': VHOFile,
    'veo': VEOFile,
    'xci': XCIFile}


# SYNOPSYS FILES

class SDCFile(File):
    """Synopsys Design Constraints"""
    pass


# LATTICE FILES

class LDFFile(File):
    """Lattice Diamond Project File"""
    pass


class LPFFile(File):
    """Lattice Preference/Constraint File"""
    pass

class PCFFile(File):
    """Icestorm Physical constraints File"""
    pass

class EDFFile(File):
    """EDIF Netlist Files"""
    pass


LATTICE_FILE_DICT = {
    'ldf': LDFFile,
    'lpf': LPFFile,
    'edf': EDFFile,
    'edif': EDFFile,
    'edi': EDFFile,
    'edn': EDFFile,
    'pcf': PCFFile}


# MICROSEMI/ACTEL FILES

class PDCFile(File):
    """Physical Design Constraints"""
    pass


MICROSEMI_FILE_DICT = {
    'pdc': PDCFile}


# OHR FILES

class WBGenFile(File):
    """Wishbone generator file"""
    pass


# INTEL/ALTERA FILES

class QIPFile(File):
    """This is the class providing the Altera Quartus IP file"""
    pass


class QSYSFile(File):
    """Qsys - Altera's System Integration Tool"""
    pass


class DPFFile(File):
    """This is the class providing Altera Quartus Design Protocol File"""
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


class SignalTapFile(File):
    """This is the class providing the Altera Signal Tap Language file"""
    pass


ALTERA_FILE_DICT = {
    'stp': SignalTapFile,
    'qip': QIPFile,
    'qsys': QSYSFile,
    'dpf': DPFFile,
    'qsf': QSFFile,
    'bsf': BSFFile,
    'bdf': BDFFile,
    'tdf': TDFFile,
    'gdf': GDFFile}


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
                       include_dirs=None):
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
                            library=library)
    elif extension in ['v', 'vh', 'vo', 'vm']:
        new_file = VerilogFile(path=path,
                               module=module,
                               library=library,
                               include_dirs=include_dirs)
    elif extension == 'sv' or extension == 'svh':
        new_file = SVFile(path=path,
                          module=module,
                          library=library,
                          include_dirs=include_dirs)
    elif extension == 'wb':
        new_file = WBGenFile(path=path, module=module)
    elif extension == 'tcl':
        new_file = TCLFile(path=path, module=module)
    elif extension == 'sdc':
        new_file = SDCFile(path=path, module=module)
    elif extension in XILINX_FILE_DICT:
        new_file = XILINX_FILE_DICT[extension](path=path, module=module)
    elif extension in ALTERA_FILE_DICT:
        new_file = ALTERA_FILE_DICT[extension](path=path, module=module)
    elif extension in LATTICE_FILE_DICT:
        new_file = LATTICE_FILE_DICT[extension](path=path, module=module)
    elif extension in MICROSEMI_FILE_DICT:
        new_file = MICROSEMI_FILE_DICT[extension](path=path, module=module)
    return new_file
