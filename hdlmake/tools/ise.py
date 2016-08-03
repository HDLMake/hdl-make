#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 - 2015 CERN
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

"""Module providing the classes that are used to handle Xilinx ISE"""

from __future__ import print_function
import xml.dom.minidom
import xml.parsers.expat
import logging
import re
import os
import sys
import string
from subprocess import Popen, PIPE

import hdlmake.new_dep_solver as dep_solver
from hdlmake.action import ActionMakefile
from hdlmake.util import path as path_mod

from hdlmake.srcfile import (UCFFile, VHDLFile, VerilogFile,
                             CDCFile, NGCFile, SourceFileSet)

XML_IMPL = xml.dom.minidom.getDOMImplementation()

FAMILY_NAMES = {
    "XC6S": "Spartan6",
    "XC3S": "Spartan3",
    "XC6V": "Virtex6",
    "XC5V": "Virtex5",
    "XC4V": "Virtex4",
    "XC7Z": "Zynq",
    "XC7V": "Virtex7",
    "XC7K": "Kintex7",
    "XC7A": "Artix7"}

ISE_STANDARD_LIBS = ['ieee', 'ieee_proposed', 'iSE', 'simprims', 'std',
                     'synopsys', 'unimacro', 'unisim', 'XilinxCoreLib']


class ToolISE(ActionMakefile):

    """Class providing the methods to create and build a Xilinx ISE project"""

    TOOL_INFO = {
        'name': 'ISE',
        'id': 'ise',
        'windows_bin': 'ise',
        'linux_bin': 'ise',
        'project_ext': 'xise'}

    SUPPORTED_FILES = [UCFFile, CDCFile, NGCFile]

    CLEAN_TARGETS = {'clean': ["xst xlnx_auto_*_xdb", "iseconfig _xmsgs",
                               "_ngo", "*.b", "*_summary.html", "*.tcl",
                               "*.bld", "*.cmd_log", "*.drc", "*.lso", "*.ncd",
                               "*.ngc", "*.ngd", "*.ngr", "*.pad", "*.par",
                               "*.pcf", "*.prj", "*.ptwx", "*.stx", "*.syr",
                               "*.twr", "*.twx", "*.gise", "*.gise", "*.bgn",
                               "*.unroutes", "*.ut", "*.xpi", "*.xst",
                               "*.xwbt", "*_envsettings.html", "*_guide.ncd",
                               "*_map.map", "*_map.mrp", "*_map.ncd",
                               "*_map.ngm", "*_map.xrpt", "*_ngdbuild.xrpt",
                               "*_pad.csv", "*_pad.txt", "*_par.xrpt",
                               "*_summary.xml", "*_usage.xml", "*_xst.xrpt",
                               "usage_statistics_webtalk.html", "webtalk.log",
                               "par_usage_statistics.html", "webtalk_pn.xml",
                               "run_synthesize.tcl", "run_translate.tcl",
                               "run_map.tcl", "run_par.tcl",
                               "run_bitstream.tcl"],
                     'mrproper': ["*.bit", "*.bin", "*.mcs"]}

    TCL_CONTROLS = {'windows_interpreter': 'xtclsh ',
                    'linux_interpreter': 'xtclsh ',
                    'open': 'project open $(PROJECT)',
                    'save': 'project save',
                    'close': 'project close',
                    'synthesize': 'process run {Synthesize - XST}',
                    'translate': 'process run {Translate}',
                    'map': 'process run {Map}',
                    'par': 'process run {Place & Route}',
                    'bitstream': 'process run {Generate Programming File}',
                    'install_source': '*.bit *.bin'}

    def __init__(self):
        super(ToolISE, self).__init__()
        self.props = {}
        self.files = []
        self.libs = []
        self.xml_doc = None
        self.xml_files = []
        self.xml_props = []
        self.xml_libs = []
        self.xml_ise = None
        self.xml_project = None
        self.xml_bindings = None
        self.top_mod = None
        self.ise = None
        self.fileset = []
        self.flist = []

    def detect_version(self, path):
        """Method returning a string with the Xilinx ISE version from path"""
        is_windows = path_mod.check_windows()
        version_pattern = re.compile(
            r'.*?(?P<major>\d|\d\d)[^\d](?P<minor>\d|\d\d).*')
        # First check if we have version in path
        match = re.match(version_pattern, path)
        if match:
            ise_version = "%s.%s" % (
                match.group('major'),
                match.group('minor'))
        else:  # If it is not the case call the "xst -h" to get version
            xst_output = Popen('xst -h', shell=True, stdin=PIPE,
                               stdout=PIPE, close_fds=not is_windows)
            xst_output = xst_output.stdout.readlines()[0]
            xst_output = xst_output.strip()
            version_pattern = re.compile(
                r'Release\s(?P<major>\d|\d\d)[^\d](?P<minor>\d|\d\d)\s.*')
            match = re.match(version_pattern, xst_output)
            if match:
                ise_version = "%s.%s" % (
                    match.group('major'),
                    match.group('minor'))
            else:
                logging.error("xst output is not in expected format: %s\n",
                    xst_output + "Can't determine ISE version")
                return None
        return ise_version

    class StringBuffer(list):

        """Auxiliar class providing a convenient string storage"""

        def __init__(self):
            self.append("")
            self.__blank = re.compile("^[ \t\n]+$")

        def write(self, what):
            """Write a new string into the buffer"""
            if what == "":
                return
            elif re.match(self.__blank, what):
                if self[len(self) - 1] != "":
                    self.append("")
                else:
                    pass
            elif what[len(what) - 1] == "\n":
                self[len(self) - 1] += what[:len(what) - 1]
                self.append("")
            else:
                self[len(self) - 1] += what

    def generate_synthesis_project(
            self, update=False, tool_version='', top_mod=None, fileset=None):
        """Generate a synthesis project for Xilinx ISE"""
        self.top_mod = top_mod
        self.ise = tool_version
        self.fileset = fileset
        self.flist = dep_solver.make_dependency_sorted_list(fileset)
        assert isinstance(self.flist, list)
        self.add_files(self.flist)
        self.add_libs(self.fileset.get_libs())
        if update is True:
            try:
                self._load_xml(top_mod.manifest_dict["syn_project"])
            except:
                logging.error("Error while reading the project file.\n"
                              "Are you sure that syn_project indicates "
                              "a correct ISE project file?")
                raise
        else:
            self.add_initial_properties()
        logging.info("Writing down .xise project file")
        self.emit_xml(self.top_mod.manifest_dict["syn_project"])

    def add_files(self, files):
        """Add files to the ISE project"""
        self.files.extend(files)

    def _add_lib(self, lib):
        """Check if a library is in the ISE project before adding it"""
        if lib not in self.libs:
            self.libs.append(lib)

    def add_libs(self, libs):
        """Add a list of libraries to the ISE project"""
        for lib_aux in libs:
            self._add_lib(lib_aux)
        self.libs.remove('work')

    def add_property(self, name, value, is_default=False):
        """Add a property to the Xilinx ISE project"""
        self.props[name] = ISEProjectProperty(name=name,
                                              value=value,
                                              is_default=is_default)

    def add_initial_properties(self):
        """Add initial properties to the Xilinx ISE project"""
        self._set_values_from_manifest()
        self.add_property("Enable Multi-Threading", "2")
        self.add_property("Enable Multi-Threading par", "4")
        self.add_property("Manual Implementation Compile Order", "true")
        self.add_property("Auto Implementation Top", "false")
        self.add_property("Create Binary Configuration File", "true")

    def _set_values_from_manifest(self):
        """Add the synthesis properties from the Manifest to the project"""
        top_module = self.top_mod
        syn_family = top_module.manifest_dict["syn_family"]
        if syn_family is None:
            syn_family = FAMILY_NAMES.get(
                top_module.manifest_dict["syn_device"][0:4].upper())
            if syn_family is None:
                logging.error(
                    "syn_family is not definied in Manifest.py"
                    " and can not be guessed!")
                quit(-1)
        self.add_property("Device", top_module.manifest_dict["syn_device"])
        self.add_property("Device Family", syn_family)
        self.add_property("Speed Grade", top_module.manifest_dict["syn_grade"])
        self.add_property("Package", top_module.manifest_dict["syn_package"])
        self.add_property(
            "Implementation Top",
            "Architecture|" +
            top_module.manifest_dict[
                "syn_top"])
        self.add_property(
            "Implementation Top Instance Path",
            "/" + top_module.manifest_dict["syn_top"])

    def _parse_props(self):
        """Parse properties from the existing ISE project"""
        properties_temp = self.xml_project.getElementsByTagName("properties")
        for xmlp in properties_temp[0].getElementsByTagName("property"):
            self.add_property(
                name=xmlp.getAttribute("xil_pn:name"),
                value=xmlp.getAttribute("xil_pn:value"),
                is_default=(
                    xmlp.getAttribute("xil_pn:valueState") == "default")
            )

        self.xml_props = self._purge_dom_node(
            name="properties",
            where=self.xml_doc.documentElement)

    def _parse_libs(self):
        """Parse libraries from the existing ISE project"""
        libraries_temp = self.xml_project.getElementsByTagName("libraries")
        for lib_aux in libraries_temp[0].getElementsByTagName("library"):
            self._add_lib(lib_aux.getAttribute("xil_pn:name"))
        self.xml_libs = self._purge_dom_node(
            name="libraries",
            where=self.xml_doc.documentElement)

    def _load_xml(self, filename):
        """Load Xilinx ISE project as a XML file"""
        file_xml = open(filename)
        self.xml_doc = xml.dom.minidom.parse(file_xml)
        self.xml_project = self.xml_doc.getElementsByTagName("project")[0]
        try:
            self._parse_props()
        except xml.parsers.expat.ExpatError:
            print("Error while parsing existing file's properties:")
            print(str(sys.exc_info()))
            quit()
        try:
            self._parse_libs()
        except xml.parsers.expat.ExpatError:
            print("Error while parsing existing file's libraries:")
            print(str(sys.exc_info()))
            quit()
        where = self.xml_doc.documentElement
        self.xml_files = self._purge_dom_node(name="files", where=where)
        self.xml_bindings = self._purge_dom_node(name="bindings", where=where)
        try:
            node = where.getElementsByTagName("version")[0]
            if not self.ise:
                self.ise = tuple(
                    node.getAttribute(
                        "xil_pn:ise_version").split(
                    '.'))
            where.removeChild(node)
        except xml.parsers.expat.ExpatError:
            pass
        file_xml.close()
        self._set_values_from_manifest()

    def _purge_dom_node(self, name, where):
        """Purge node at the XML file to accomodate a new value"""
        try:
            node = where.getElementsByTagName(name)[0]
            where.removeChild(node)
        except xml.parsers.expat.ExpatError:
            pass
        new = self.xml_doc.createElement(name)
        where.appendChild(new)
        return new

    def _output_files(self, node):
        """Add the HDL design files to the Xilinx ISE Project"""
        for file_aux in self.files:
            file_project = self.xml_doc.createElement("file")
            file_project.setAttribute("xil_pn:name",
                os.path.relpath(file_aux.path))
            if isinstance(file_aux, VHDLFile):
                file_project.setAttribute("xil_pn:type", "FILE_VHDL")
            elif isinstance(file_aux, VerilogFile):
                file_project.setAttribute("xil_pn:type", "FILE_VERILOG")
            elif isinstance(file_aux, UCFFile):
                file_project.setAttribute("xil_pn:type", "FILE_UCF")
            elif isinstance(file_aux, CDCFile):
                file_project.setAttribute("xil_pn:type", "FILE_CDC")
            elif isinstance(file_aux, NGCFile):
                file_project.setAttribute("xil_pn:type", "FILE_NGC")
            else:
                continue
            assoc = self.xml_doc.createElement("association")
            assoc.setAttribute("xil_pn:name", "Implementation")
            assoc.setAttribute("xil_pn:seqID",
                str(self.files.index(file_aux) + 1))
            try:
                if file_aux.library != "work":
                    lib = self.xml_doc.createElement("library")
                    lib.setAttribute("xil_pn:name", file_aux.library)
                    file_project.appendChild(lib)
            except:
                pass
            file_project.appendChild(assoc)
            node.appendChild(file_project)

    def _output_bindings(self, node):
        """Add ChipScope bindings to the Xilinx ISE project"""
        for binding in [file_aux for file_aux in self.files
                        if isinstance(file_aux, CDCFile)]:
            binding_project = self.xml_doc.createElement("binding")
            binding_project.setAttribute(
                "xil_pn:location",
                self.top_mod.manifest_dict["syn_top"])
            binding_project.setAttribute("xil_pn:name", binding.rel_path())
            node.appendChild(binding_project)

    def _output_props(self, node):
        """Insert the list of properties into the Xilinx ISE Project"""
        for name, prop in self.props.iteritems():
            node.appendChild(prop.emit_xml(self.xml_doc))

    def _output_libs(self, node):
        """Insert the list of libraries into the Xilinx ISE Project"""
        for lib_aux in self.libs:
            lib_project = self.xml_doc.createElement("library")
            lib_project.setAttribute("xil_pn:name", lib_aux)
            node.appendChild(lib_project)

    def _output_ise(self, node):
        """Insert project atributes into the Xilinx ISE Project"""
        ise_ver_project = self.xml_doc.createElement("version")
        ise_ver_project.setAttribute("xil_pn:ise_version", '%s' % (self.ise))
        ise_ver_project.setAttribute("xil_pn:schema_version", "2")
        node.appendChild(ise_ver_project)

    def emit_xml(self, filename=None):
        """Process the required outputs and write an ISE Project"""
        if not self.xml_doc:
            self.create_empty_project()
        else:
            self._output_ise(self.xml_doc.documentElement)
        logging.debug("Writing .xise file for version " + str(self.ise))
        self._output_bindings(self.xml_bindings)
        self._output_files(self.xml_files)
        self._output_props(self.xml_props)
        self._output_libs(self.xml_libs)
        output_file = open(filename, "w")
        string_buffer = self.StringBuffer()
        self.xml_doc.writexml(string_buffer, newl="\n", addindent="\t")
        output_file.write('\n'.join(string_buffer))
        output_file.close()

    def create_empty_project(self):
        """Create an empty XML docmument to accomodate the ISE Project"""
        self.xml_doc = XML_IMPL.createDocument(
            "http://www.xilinx.com/XMLSchema",
            "project",
            None)
        top_element = self.xml_doc.documentElement
        top_element.setAttribute("xmlns", "http://www.xilinx.com/XMLSchema")
        top_element.setAttribute(
            "xmlns:xil_pn",
            "http://www.xilinx.com/XMLSchema")
        header = self.xml_doc.createElement("header")
        header.appendChild(self.xml_doc.createTextNode(""))
        amf = self.xml_doc.createElement("autoManagedFiles")
        amf.appendChild(self.xml_doc.createTextNode(""))
        self.xml_props = self.xml_doc.createElement("properties")
        self.xml_files = self.xml_doc.createElement("files")
        self.xml_libs = self.xml_doc.createElement("libraries")
        self.xml_bindings = self.xml_doc.createElement("bindings")
        version = self.xml_doc.createElement("version")
        version.setAttribute("xil_pn:ise_version", self.ise)
        version.setAttribute("xil_pn:schema_version", "2")
        top_element.appendChild(header)
        top_element.appendChild(amf)
        top_element.appendChild(self.xml_props)
        top_element.appendChild(self.xml_libs)
        top_element.appendChild(self.xml_files)
        top_element.appendChild(self.xml_bindings)
        top_element.appendChild(version)


class ISEProjectProperty(object):

    """Class that serves as container for the Xilinx ISE project properties"""

    def __init__(self, name, value, is_default=False):
        self.name = name
        self.value = value
        self.is_default = is_default

    def emit_xml(self, doc):
        """Return a XML doc property calculated from inner class parameters"""
        prop = doc.createElement("property")
        prop.setAttribute("xil_pn:name", self.name)
        prop.setAttribute("xil_pn:value", self.value)
        if self.is_default:
            prop.setAttribute("xil_pn:valueState", "default")
        else:
            prop.setAttribute("xil_pn:valueState", "non-default")
        return prop
