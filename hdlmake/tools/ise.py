#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Modified to allow ISim simulation by Lucas Russo (lucas.russo@lnls.br)
# Modified to allow ISim simulation by Adrian Byszuk (adrian.byszuk@lnls.br)
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
import xml.dom.minidom
import xml.parsers.expat
import logging
import re
import global_mod
import os
from subprocess import Popen, PIPE


XmlImpl = xml.dom.minidom.getDOMImplementation()

ISE_STANDARD_LIBS = ['ieee', 'ieee_proposed', 'iSE', 'simprims', 'std',
                     'synopsys', 'unimacro', 'unisim', 'XilinxCoreLib']

FAMILY_NAMES = {
    "XC6S": "Spartan6",
    "XC3S": "Spartan3",
    "XC6V": "Virtex6",
    "XC5V": "Virtex5",
    "XC4V": "Virtex4",
    "XC7K": "Kintex7",
    "XC7A": "Artix7"}


def detect_ise_version(path):
    xst = Popen('which xst', shell=True, stdin=PIPE,
                stdout=PIPE, close_fds=True)
    lines = xst.stdout.readlines()
    if not lines:
        return None

    xst = str(lines[0].strip())
    version_pattern = re.compile('.*?(?P<major>\d|\d\d)[^\d](?P<minor>\d|\d\d).*')
    # First check if we have version in path

    match = re.match(version_pattern, xst)
    if match:
        ise_version = "%s.%s" % (match.group('major'), match.group('minor'))
    else:  # If it is not the case call the "xst -h" to get version
        xst_output = Popen('xst -h', shell=True, stdin=PIPE,
                           stdout=PIPE, close_fds=True)
        xst_output = xst_output.stdout.readlines()[0]
        xst_output = xst_output.strip()
        version_pattern = re.compile('Release\s(?P<major>\d|\d\d)[^\d](?P<minor>\d|\d\d)\s.*')
        match = re.match(version_pattern, xst_output)
        if match:
            ise_version = "%s.%s" % (match.group('major'), match.group('minor'))
        else:
            logging.error("xst output is not in expected format: %s\n" % xst_output +
                          "Can't determine ISE version")
            return None

    return ise_version

class ISEProjectProperty:
    def __init__(self,  name, value, is_default=False):
        self.name = name
        self.value = value
        self.is_default = is_default

    def emit_xml(self, doc):
        prop = doc.createElement("property")
        prop.setAttribute("xil_pn:name", self.name)
        prop.setAttribute("xil_pn:value", self.value)
        if self.is_default:
            prop.setAttribute("xil_pn:valueState", "default")
        else:
            prop.setAttribute("xil_pn:valueState", "non-default")

        return prop


class ISEProject(object):
    class StringBuffer(list):
        def __init__(self):
            self.append("")
            self.__blank = re.compile("^[ \t\n]+$")

        def write(self, what):
            if what == "":
                return
            elif re.match(self.__blank, what):
                if self[len(self)-1] != "":
                    self.append("")
                else:
                    pass
            elif what[len(what)-1] == "\n":
                self[len(self)-1] += what[:len(what)-1]
                self.append("")
            else:
                self[len(self)-1] += what

    def __init__(self, ise, top_mod=None):
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
        self.top_mod = top_mod
        self.ise = ise

    def add_files(self, files):
        self.files.extend(files)

    def _add_lib(self, lib):
        if lib not in self.libs:
            self.libs.append(lib)

    def add_libs(self, libs):
        for l in libs:
            self._add_lib(l)
        self.libs.remove('work')

    def add_property(self, name, value, is_default=False):
        self.props[name] = ISEProjectProperty(name=name,
                                              value=value,
                                              is_default=is_default)

    def add_initial_properties(self):
        self._set_values_from_manifest()
        self.add_property("Enable Multi-Threading", "2")
        self.add_property("Enable Multi-Threading par", "4")
        self.add_property("Manual Implementation Compile Order", "true")
        self.add_property("Auto Implementation Top", "false")
        self.add_property("Hierarchy Separator", "_")

    def _set_values_from_manifest(self):
        tm = global_mod.mod_pool.get_top_module()
        self.add_property("Device", tm.syn_device)
        self.add_property("Device Family", FAMILY_NAMES[tm.syn_device[0:4].upper()])
        self.add_property("Speed Grade", tm.syn_grade)
        self.add_property("Package", tm.syn_package)
        self.add_property("Implementation Top", "Architecture|"+tm.syn_top)
        self.add_property("Implementation Top Instance Path", "/"+tm.syn_top)

    def _parse_props(self):
        for xmlp in self.xml_project.getElementsByTagName("properties")[0].getElementsByTagName("property"):
            self.add_property(
                name=xmlp.getAttribute("xil_pn:name"),
                value=xmlp.getAttribute("xil_pn:value"),
                is_default=(xmlp.getAttribute("xil_pn:valueState") == "default")
            )

        self.xml_props = self._purge_dom_node(name="properties", where=self.xml_doc.documentElement)

    def _parse_libs(self):
        for l in self.xml_project.getElementsByTagName("libraries")[0].getElementsByTagName("library"):
            self._add_lib(l.getAttribute("xil_pn:name"))
        self.xml_libs = self._purge_dom_node(name="libraries", where=self.xml_doc.documentElement)

    def load_xml(self, filename):
        f = open(filename)
        self.xml_doc = xml.dom.minidom.parse(f)
        self.xml_project = self.xml_doc.getElementsByTagName("project")[0]
        import sys
        try:
            self._parse_props()
        except xml.parsers.expat.ExpatError:
            print("Error while parsing existng file's properties:")
            print(str(sys.exc_info()))
            quit()

        try:
            self._parse_libs()
        except xml.parsers.expat.ExpatError:
            print("Error while parsing existng file's libraries:")
            print(str(sys.exc_info()))
            quit()

        where = self.xml_doc.documentElement
        self.xml_files = self._purge_dom_node(name="files", where=where)
        self.xml_bindings = self._purge_dom_node(name="bindings", where=where)
        try:
            node = where.getElementsByTagName("version")[0]
            if not self.ise:
                self.ise = tuple(node.getAttribute("xil_pn:ise_version").split('.'))
            where.removeChild(node)
        except:
            pass
        f.close()
        self._set_values_from_manifest()

    def _purge_dom_node(self, name, where):
        try:
            node = where.getElementsByTagName(name)[0]
            where.removeChild(node)
        except:
            pass
        new = self.xml_doc.createElement(name)
        where.appendChild(new)
        return new

    def _output_files(self, node):
        from srcfile import UCFFile, VHDLFile, VerilogFile, CDCFile, NGCFile

        for f in self.files:
            fp = self.xml_doc.createElement("file")
            fp.setAttribute("xil_pn:name", os.path.relpath(f.path))
            if isinstance(f, VHDLFile):
                fp.setAttribute("xil_pn:type", "FILE_VHDL")
            elif isinstance(f, VerilogFile):
                fp.setAttribute("xil_pn:type", "FILE_VERILOG")
            elif isinstance(f, UCFFile):
                fp.setAttribute("xil_pn:type", "FILE_UCF")
            elif isinstance(f, CDCFile):
                fp.setAttribute("xil_pn:type", "FILE_CDC")
            elif isinstance(f, NGCFile):
                fp.setAttribute("xil_pn:type", "FILE_NGC")
            else:
                continue

            assoc = self.xml_doc.createElement("association")
            assoc.setAttribute("xil_pn:name", "Implementation")
            assoc.setAttribute("xil_pn:seqID", str(self.files.index(f)+1))

            try:
                if(f.library != "work"):
                    lib = self.xml_doc.createElement("library")
                    lib.setAttribute("xil_pn:name", f.library)
                    fp.appendChild(lib)
            except:
                pass

            fp.appendChild(assoc)
            node.appendChild(fp)

    def _output_bindings(self, node):
        from srcfile import CDCFile
        for b in [f for f in self.files if isinstance(f, CDCFile)]:
            bp = self.xml_doc.createElement("binding")
            bp.setAttribute("xil_pn:location", self.top_mod.syn_top)
            bp.setAttribute("xil_pn:name", b.rel_path())
            node.appendChild(bp)

    def _output_props(self, node):
        for name, prop in self.props.iteritems():
            node.appendChild(prop.emit_xml(self.xml_doc))

    def _output_libs(self, node):
        for l in self.libs:
            ll = self.xml_doc.createElement("library")
            ll.setAttribute("xil_pn:name", l)
            node.appendChild(ll)

    def _output_ise(self, node):
        i = self.xml_doc.createElement("version")
        i.setAttribute("xil_pn:ise_version", '%s' % (self.ise))
        i.setAttribute("xil_pn:schema_version", "2")
        node.appendChild(i)

    def emit_xml(self, filename=None):
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
        self.xml_doc = XmlImpl.createDocument("http://www.xilinx.com/XMLSchema", "project", None)
        top_element = self.xml_doc.documentElement
        top_element.setAttribute("xmlns", "http://www.xilinx.com/XMLSchema")
        top_element.setAttribute("xmlns:xil_pn", "http://www.xilinx.com/XMLSchema")

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


class XilinxsiminiReader(object):
    def __init__(self, path=None):
        if path is None:
            path = self.xilinxsim_ini_dir() + "/xilinxsim.ini"
        self.path = path

    # Parse the xilinxsim.ini file to get the referenced libraries
    def get_libraries(self):
        libs = []

        try:
            ini = open(self.path, "r")
        except Exception:
            raise RuntimeError("Can't open existing xilinxsim.ini file")

        #p.info("Reading 'xilinxsim.ini' located in: '"+ str(self.path))

        # Read loggical libraries name, skipping comments and other
        #possible sections
        for line in ini:
            # Read line by line, skipping comments and striping newline
            line = line.split('--')[0].strip()
            # Still in comments section
            if line == "":
                continue

            # Not in comments section. Library section:
            #<logical_library> = <phisical_path>
            line = line.split('=')
            lib = line[0].strip()
            libs.append(lib.lower())
        return libs

    @staticmethod
    def xilinxsim_ini_dir():
        # Does not really need this
        # try:
        #     host_platform = os.environ["HOST_PLATFORM"]
        # except KeyError:
        #     logging.error("Please set the environment variable HOST_PLATFORM")
        #     quit()
        xilinx_ini_path = str(os.path.join(global_mod.env["xilinx"],
                              "vhdl",
                              "hdp",
                              "lin" if global_mod.env["architecture"] == 32 else "lin64"))
        # Ensure the path is absolute and normalized
        return os.path.abspath(xilinx_ini_path)
