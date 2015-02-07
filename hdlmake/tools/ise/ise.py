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

from __future__ import print_function
import xml.dom.minidom
import xml.parsers.expat
import logging
import re
import global_mod
import os
import sys
from subprocess import Popen, PIPE

import new_dep_solver as dep_solver

import string
from string import Template
import fetch

from makefile_writer import MakefileWriter

XmlImpl = xml.dom.minidom.getDOMImplementation()


FAMILY_NAMES = {
    "XC6S": "Spartan6",
    "XC3S": "Spartan3",
    "XC6V": "Virtex6",
    "XC5V": "Virtex5",
    "XC4V": "Virtex4",
    "XC7K": "Kintex7",
    "XC7A": "Artix7"}


class ToolControls(MakefileWriter):

    def get_keys(self):
        tool_info = {
            'name': 'ISE',
            'id': 'ise',
            'windows_bin': 'ise',
            'linux_bin': 'ise',
            'project_ext': 'xise'
        }
        return tool_info

    def get_standard_libraries(self):
        ISE_STANDARD_LIBS = ['ieee', 'ieee_proposed', 'iSE', 'simprims', 'std',
                     'synopsys', 'unimacro', 'unisim', 'XilinxCoreLib']
        return ISE_STANDARD_LIBS

    def detect_version(self, path):
        
        #xst = Popen('which xst', shell=True, stdin=PIPE,
        #            stdout=PIPE, close_fds=True)
        #lines = xst.stdout.readlines()
        #if not lines:
        #    return None

        #xst = str(lines[0].strip())
        
        version_pattern = re.compile('.*?(?P<major>\d|\d\d)[^\d](?P<minor>\d|\d\d).*')
        # First check if we have version in path

        match = re.match(version_pattern, path)
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


    def generate_remote_synthesis_makefile(self, files, name, cwd, user, server):
        from subprocess import PIPE, Popen
        if name is None:
            import random
            name = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
        whoami = Popen('whoami', shell=True, stdin=PIPE, stdout=PIPE, close_fds=True)
        name = whoami.stdout.readlines()[0].strip() + '/' + name
        user_tmpl = "USER:={0}"
        server_tmpl = "SERVER:={0}"
        ise_path_tmpl = "ISE_PATH:={0}"
        port_tmpl = "PORT:=22"
        remote_name_tmpl = "R_NAME:={0}"
        files_tmpl = "FILES := {0}"

        user_tmpl = user_tmpl.format("$(HDLMAKE_RSYNTH_USER)#take the value from the environment")
        test_tmpl = """__test_for_remote_synthesis_variables:
ifeq (x$(USER),x)
\t@echo "Remote synthesis user is not set.\
You can set it by editing variable USER in the makefile or setting env. variable HDLMAKE_RSYNTH_USER." && false
endif
ifeq (x$(SERVER),x)
\t@echo "Remote synthesis server is not set.\
You can set it by editing variable SERVER in the makefile or setting env. variable HDLMAKE_RSYNTH_SERVER." && false
endif
ifeq (x$(ISE_PATH),x)
\t@echo "Remote synthesis server is not set.\
You can set it by editing variable ISE_PATH in the makefile or setting env. variable HDLMAKE_RSYNTH_ISE_PATH." && false
endif
"""
        if server is None:
            server_tmpl = server_tmpl.format("$(HDLMAKE_RSYNTH_SERVER)#take the value from the environment")
        else:
            server_tmpl = server_tmpl.format(server)

        remote_name_tmpl = remote_name_tmpl.format(name)
        self.initialize()
        self.writeln(user_tmpl)
        self.writeln(server_tmpl)
        self.writeln(ise_path_tmpl.format("$(HDLMAKE_RSYNTH_ISE_PATH)"))
        self.writeln(remote_name_tmpl)
        self.writeln(port_tmpl)
        self.writeln()
        self.writeln(test_tmpl)
        self.writeln("CWD := $(shell pwd)")
        self.writeln("")
        self.writeln(files_tmpl.format(' \\\n'.join([s.rel_path() for s in files])))
        self.writeln("")
        self.writeln("#target for running synthesis in the remote location")
        self.writeln("remote: __test_for_remote_synthesis_variables __send __do_synthesis")
        self.writeln("__send_back: __do_synthesis")
        self.writeln("__do_synthesis: __send")
        self.writeln("__send: __test_for_remote_synthesis_variables")
        self.writeln("")

        mkdir_cmd = "ssh $(USER)@$(SERVER) 'mkdir -p $(R_NAME)'"
        rsync_cmd = "rsync -e 'ssh -p $(PORT)' -Ravl $(foreach file, $(FILES), $(shell readlink -f $(file))) $(USER)@$(SERVER):$(R_NAME)"
        send_cmd = "__send:\n\t\t{0}\n\t\t{1}".format(mkdir_cmd, rsync_cmd)
        self.writeln(send_cmd)
        self.writeln("")

        tcl = "run.tcl"
        synthesis_cmd = """__do_synthesis:
ifeq (x$(HDLMAKE_RSYNTH_USE_SCREEN), x1)
\t\tssh -t $(USER)@$(SERVER) 'screen bash -c "cd $(R_NAME)$(CWD) && $(HDLMAKE_RSYNTH_ISE_PATH)/xtclsh {0}"'
else
\t\tssh $(USER)@$(SERVER) 'cd $(R_NAME)$(CWD) && $(HDLMAKE_RSYNTH_ISE_PATH)/xtclsh {0}'
endif
"""
        self.writeln(synthesis_cmd.format(tcl))

        self.writeln()
        send_back_cmd = "sync: \n\t\tcd .. && rsync -av $(USER)@$(SERVER):$(R_NAME)/$(CWD) . && cd $(CWD)"
        self.write(send_back_cmd)
        self.write("\n\n")

        cln_cmd = "cleanremote:\n\t\tssh $(USER)@$(SERVER) 'rm -rf $(R_NAME)'"
        self.writeln("#target for removing stuff from the remote location")
        self.writeln(cln_cmd)
        self.writeln()


    def generate_synthesis_makefile(self, top_mod, tool_path):
        makefile_tmplt = string.Template("""PROJECT := ${project_name}
ISE_CRAP := \
*.b \
${syn_top}_summary.html \
*.tcl \
${syn_top}.bld \
${syn_top}.cmd_log \
*.drc \
${syn_top}.lso \
*.ncd \
${syn_top}.ngc \
${syn_top}.ngd \
${syn_top}.ngr \
${syn_top}.pad \
${syn_top}.par \
${syn_top}.pcf \
${syn_top}.prj \
${syn_top}.ptwx \
${syn_top}.stx \
${syn_top}.syr \
${syn_top}.twr \
${syn_top}.twx \
${syn_top}.gise \
$$(PROJECT).gise \
${syn_top}.bgn \
${syn_top}.unroutes \
${syn_top}.ut \
${syn_top}.xpi \
${syn_top}.xst \
${syn_top}_bitgen.xwbt \
${syn_top}_envsettings.html \
${syn_top}_guide.ncd \
${syn_top}_map.map \
${syn_top}_map.mrp \
${syn_top}_map.ncd \
${syn_top}_map.ngm \
${syn_top}_map.xrpt \
${syn_top}_ngdbuild.xrpt \
${syn_top}_pad.csv \
${syn_top}_pad.txt \
${syn_top}_par.xrpt \
${syn_top}_summary.xml \
${syn_top}_usage.xml \
${syn_top}_xst.xrpt \
usage_statistics_webtalk.html \
par_usage_statistics.html \
webtalk.log \
webtalk_pn.xml \
run.tcl

#target for performing local synthesis
local: syn_pre_cmd check_tool synthesis syn_post_cmd

synthesis:
\t\techo "project open $$(PROJECT)" > run.tcl
\t\techo "process run {Synthesize - XST}" >> run.tcl
\t\techo "process run {Translate}" >> run.tcl
\t\techo "process run {Map}" >> run.tcl
\t\techo "process run {Place & Route}" >> run.tcl
\t\techo "process run {Generate Programming File}" >> run.tcl
\t\t${xtclsh_path} run.tcl

check_tool:
\t\t${check_tool}

syn_post_cmd:
\t\t${syn_post_cmd}

syn_pre_cmd:
\t\t${syn_pre_cmd}

#target for cleaning all intermediate stuff
clean:
\t\trm -f $$(ISE_CRAP)
\t\trm -rf xst xlnx_auto_*_xdb iseconfig _xmsgs _ngo

#target for cleaning final files
mrproper:
\t\trm -f *.bit *.bin *.mcs

.PHONY: mrproper clean syn_pre_cmd syn_post_cmd synthesis local check_tool

""")
        if top_mod.syn_pre_cmd:
            syn_pre_cmd = top_mod.syn_pre_cmd
        else:
            syn_pre_cmd = ''

        if top_mod.syn_post_cmd:
            syn_post_cmd = top_mod.syn_post_cmd
        else:
            syn_post_cmd = ''

        if top_mod.force_tool:
            ft = top_mod.force_tool
            check_tool = """python $(HDLMAKE_HDLMAKE_PATH)/hdlmake _conditioncheck --tool {tool} --reference {reference} --condition "{condition}"\\
|| (echo "{tool} version does not meet condition: {condition} {reference}" && false)
""".format(tool=ft[0],
                condition=ft[1],
                reference=ft[2])
        else:
            check_tool = ''

        makefile_text = makefile_tmplt.substitute(syn_top=top_mod.syn_top,
                                  project_name=top_mod.syn_project,
                                  ise_path=tool_path,
                                  check_tool=check_tool,
                                  syn_pre_cmd=syn_pre_cmd,
                                  syn_post_cmd=syn_post_cmd,
                                  xtclsh_path=os.path.join(tool_path, "xtclsh"))
        self.write(makefile_text)
        for f in top_mod.incl_makefiles:
            if os.path.exists(f):
                self.write("include %s\n" % f)


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


    def generate_synthesis_project(self, update=False, tool_version='', top_mod=None, fileset=None):
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
        self.ise = tool_version

        self.fileset = fileset
        self.flist = dep_solver.make_dependency_sorted_list(fileset)
        assert isinstance(self.flist, list)

        self.add_files(self.flist)

        self.add_libs(self.fileset.get_libs())
        
        if update is True:
            try:
                self.load_xml(top_mod.syn_project)
            except:
                logging.error("Error while reading the project file.\n"
                              "Are you sure that syn_project indicates a correct ISE project file?")
                raise
        else:
            self.add_initial_properties()
        
        logging.info("Writing down .xise project file")
        self.emit_xml(self.top_mod.syn_project)       


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
        self.add_property("Create Binary Configuration File", "true")

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


