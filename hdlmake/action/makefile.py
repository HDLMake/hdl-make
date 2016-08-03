#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013, 2014 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Modified to allow ISim simulation by Lucas Russo (lucas.russo@lnls.br)
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

"""Module providing the core functionality for writing Makefiles"""

import os
import sys
import string
import platform

from .action import Action
from hdlmake.util import path as path_mod


class ActionMakefile(Action):

    """Class that provides the Makefile writing methods and status"""

    def __init__(self, filename=None):
        self._file = None
        self._initialized = False
        if filename:
            self._filename = filename
        else:
            self._filename = "Makefile"
        super(ActionMakefile, self).__init__()

    def __del__(self):
        if self._file:
            self._file.close()

    def _print_incl_makefiles(self, top_module):
        """Add the included makefiles that need to be previously loaded"""
        for file_aux in top_module.incl_makefiles:
            if os.path.exists(file_aux):
                self.write("include %s\n" % file_aux)

    def _print_sim_top(self, top_module):
        top_parameter = string.Template("""\
TOP_MODULE := ${top_module}
PWD := $$(shell pwd)
""")
        self.writeln(top_parameter.substitute(
            top_module=top_module.manifest_dict["sim_top"]))

    def _print_syn_top(self, top_module, tool_path, tcl_controls):
        """Create the top part of the synthesis Makefile"""
        if path_mod.check_windows():
            tcl_interpreter = tcl_controls["windows_interpreter"]
        else:
            tcl_interpreter = tcl_controls["linux_interpreter"]
        top_parameter = string.Template("""\
TOP_MODULE := ${top_module}
PWD := $$(shell pwd)
PROJECT := ${project_name}
TOOL_PATH := ${tool_path}
TCL_INTERPRETER := $$(TOOL_PATH)/${tcl_interpreter}

define TCL_OPEN
${tcl_open}
endef
export TCL_OPEN

define TCL_SAVE
${tcl_save}
endef
export TCL_SAVE

define TCL_CLOSE
${tcl_close}
endef
export TCL_CLOSE

define TCL_SYNTHESIZE
$$(TCL_OPEN)
${tcl_synthesize}
$$(TCL_SAVE)
$$(TCL_CLOSE)
endef
export TCL_SYNTHESIZE

define TCL_TRANSLATE
$$(TCL_OPEN)
${tcl_translate}
$$(TCL_SAVE)
$$(TCL_CLOSE)
endef
export TCL_SYNTHESIZE

define TCL_MAP
$$(TCL_OPEN)
${tcl_map}
$$(TCL_SAVE)
$$(TCL_CLOSE)
endef
export TCL_MAP

define TCL_PAR
$$(TCL_OPEN)
${tcl_par}
$$(TCL_SAVE)
$$(TCL_CLOSE)
endef
export TCL_PAR

define TCL_BITSTREAM
$$(TCL_OPEN)
${tcl_bitstream}
$$(TCL_SAVE)
$$(TCL_CLOSE)
endef
export TCL_BITSTREAM

""")
        self.writeln(top_parameter.substitute(
            project_name=top_module.manifest_dict["syn_project"],
            tool_path=tool_path,
            tcl_interpreter=tcl_interpreter,
            tcl_open=tcl_controls["open"],
            tcl_save=tcl_controls["save"],
            tcl_close=tcl_controls["close"],
            tcl_synthesize=tcl_controls["synthesize"],
            tcl_translate=tcl_controls["translate"],
            tcl_map=tcl_controls["map"],
            tcl_par=tcl_controls["par"],
            tcl_bitstream=tcl_controls["bitstream"],
            top_module=top_module.manifest_dict["syn_top"]))

    def _print_sim_options(self, top_module):
        pass

    def _print_sim_local(self, top_module):
        self.writeln("#target for performing local simulation\n"
                     "local: sim_pre_cmd simulation sim_post_cmd\n")

    def _print_syn_local(self):
        self.writeln("#target for performing local synthesis\n"
                     "local: syn_pre_cmd synthesis syn_post_cmd\n")

    def _print_syn_build(self):
        """Generate a Makefile to handle a synthesis project"""
        self.writeln("""\
#target for performing local synthesis
synthesis: __gen_tcl_bitstream __run_tcl_bitstream

__gen_tcl_synthesize:
\t\techo "$$TCL_SYNTHESIZE" > run_synthesize.tcl

__gen_tcl_translate:
\t\techo "$$TCL_TRANSLATE)" > run_translate.tcl

__gen_tcl_map:
\t\techo "$$TCL_MAP" > run_map.tcl

__gen_tcl_par:
\t\techo "$$TCL_PAR" > run_par.tcl

__gen_tcl_bitstream:
\t\techo "$$TCL_BITSTREAM" > run_bitstream.tcl


__run_tcl_synthesize:
\t\t$(TCL_INTERPRETER)run_synthesize.tcl

__run_tcl_translate:
\t\t$(TCL_INTERPRETER)run_translate.tcl

__run_tcl_map:
\t\t$(TCL_INTERPRETER)run_map.tcl

__run_tcl_par:
\t\t$(TCL_INTERPRETER)run_par.tcl

__run_tcl_bitstream:
\t\t$(TCL_INTERPRETER)run_bitstream.tcl


synthesize: __syn_pre_synthesize_cmd __gen_tcl_synthesize __run_tcl_synthesize __syn_post_synthesize_cmd

translate: __syn_pre_translate_cmd __gen_tcl_translate __run_tcl_translate __syn_post_translate_cmd

map: __syn_pre_map_cmd __gen_tcl_map __run_tcl_map __syn_post_map_cmd

par: __syn_pre_par_cmd __gen_tcl_par __run_tcl_par __syn_post_par_cmd

bitstream: __syn_pre_bitstream_cmd __gen_tcl_bitstream __run_tcl_bitstream __syn_post_bitstream_cmd

""")

    def _print_sim_sources(self, fileset):
        from hdlmake.srcfile import VerilogFile, VHDLFile
        self.write("VERILOG_SRC := ")
        for vl in fileset.filter(VerilogFile):
            self.write(vl.rel_path() + " \\\n")
        self.write("\n")

        self.write("VERILOG_OBJ := ")
        for vl in fileset.filter(VerilogFile):
            # make a file compilation indicator (these .dat files are made even if
            # the compilation process fails) and add an ending according to file's
            # extension (.sv and .vhd files may have the same corename and this
            # causes a mess
            self.write(
                os.path.join(
                    vl.library,
                    vl.purename,
                    "." +
                    vl.purename +
                    "_" +
                    vl.extension(
                    )) +
                " \\\n")
        self.write('\n')

        self.write("VHDL_SRC := ")
        for vhdl in fileset.filter(VHDLFile):
            self.write(vhdl.rel_path() + " \\\n")
        self.writeln()

        # list vhdl objects (_primary.dat files)
        self.write("VHDL_OBJ := ")
        for vhdl in fileset.filter(VHDLFile):
            # file compilation indicator (important: add _vhd ending)
            self.write(
                os.path.join(
                    vhdl.library,
                    vhdl.purename,
                    "." +
                    vhdl.purename +
                    "_" +
                    vhdl.extension(
                    )) +
                " \\\n")
        self.write('\n')

    def _print_syn_command(self, top_module):
        """Create the Makefile targets for user defined commands"""
        syn_command = string.Template("""\
# User defined commands
syn_pre_cmd:
\t\t${syn_pre_cmd}
syn_post_cmd:
\t\t${syn_post_cmd}

__syn_pre_synthesize_cmd:
\t\t${syn_pre_synthesize_cmd}
__syn_post_synthesize_cmd:
\t\t${syn_post_synthesize_cmd}

__syn_pre_translate_cmd:
\t\t${syn_pre_translate_cmd}
__syn_post_translate_cmd:
\t\t${syn_post_translate_cmd}

__syn_pre_map_cmd:
\t\t${syn_pre_map_cmd}
__syn_post_map_cmd:
\t\t${syn_post_map_cmd}

__syn_pre_par_cmd:
\t\t${syn_pre_par_cmd}
__syn_post_par_cmd:
\t\t${syn_post_par_cmd}

__syn_pre_bitstream_cmd:
\t\t${syn_pre_bitstream_cmd}
__syn_post_bitstream_cmd:
\t\t${syn_post_bitstream_cmd}

""")
        self.writeln(syn_command.substitute(
            syn_pre_cmd=top_module.manifest_dict[
            "syn_pre_cmd"],
            syn_post_cmd=top_module.manifest_dict[
                "syn_post_cmd"],
            syn_pre_synthesize_cmd=top_module.manifest_dict[
                "syn_pre_synthesize_cmd"],
            syn_post_synthesize_cmd=top_module.manifest_dict[
                "syn_post_synthesize_cmd"],
            syn_pre_translate_cmd=top_module.manifest_dict[
                "syn_pre_translate_cmd"],
            syn_post_translate_cmd=top_module.manifest_dict[
                "syn_post_translate_cmd"],
            syn_pre_map_cmd=top_module.manifest_dict[
                "syn_pre_map_cmd"],
            syn_post_map_cmd=top_module.manifest_dict[
                "syn_post_map_cmd"],
            syn_pre_par_cmd=top_module.manifest_dict[
                "syn_pre_par_cmd"],
            syn_post_par_cmd=top_module.manifest_dict[
                "syn_post_par_cmd"],
            syn_pre_bitstream_cmd=top_module.manifest_dict[
                "syn_pre_bitstream_cmd"],
            syn_post_bitstream_cmd=top_module.manifest_dict[
                "syn_post_bitstream_cmd"]))

    def _print_sim_command(self, top_module):
        if top_module.manifest_dict["sim_pre_cmd"]:
            sim_pre_cmd = top_module.manifest_dict["sim_pre_cmd"]
        else:
            sim_pre_cmd = ''

        if top_module.manifest_dict["sim_post_cmd"]:
            sim_post_cmd = top_module.manifest_dict["sim_post_cmd"]
        else:
            sim_post_cmd = ''

        sim_command = string.Template("""# USER SIM COMMANDS
sim_pre_cmd:
\t\t${sim_pre_cmd}
sim_post_cmd:
\t\t${sim_post_cmd}
""")

        self.writeln(sim_command.substitute(sim_pre_cmd=sim_pre_cmd,
                                            sim_post_cmd=sim_post_cmd))

    def _print_clean(self, clean_targets):
        """Print the Makefile clean target"""
        if platform.system() == 'Windows':
            del_command = "rm -rf"
        else:
            del_command = "rm -rf"
        self.writeln("#target for cleaning intermediate files")
        self.writeln("clean:")
        tmp = "\t\t" + del_command + \
            " $(LIBS) " + ' '.join(clean_targets["clean"])
        self.writeln(tmp)
        self.writeln()
        self.writeln("#target for cleaning final files")
        self.writeln("mrproper: clean")
        tmp = "\t\t" + del_command + \
            " " + ' '.join(clean_targets["mrproper"])
        self.writeln(tmp)
        self.writeln()

    def _print_sim_phony(self, top_module):
        """Print simulation PHONY target list to the Makefile"""
        self.writeln(
            ".PHONY: mrproper clean sim_pre_cmd sim_post_cmd simulation")

    def _print_syn_phony(self):
        """Print synthesis PHONY target list to the Makefile"""
        self.writeln(
            ".PHONY: mrproper clean syn_pre_cmd syn_post_cmd synthesis")

    def initialize(self):
        """Open the Makefile file and print a header if not initialized"""
        if not self._initialized:
            if os.path.exists(self._filename):
                if os.path.isfile(self._filename):
                    os.remove(self._filename)
                elif os.path.isdir(self._filename):
                    os.rmdir(self._filename)

            self._file = open(self._filename, "a+")
            self._initialized = True
            self.writeln("########################################")
            self.writeln("#  This file was generated by hdlmake  #")
            self.writeln("#  http://ohwr.org/projects/hdl-make/  #")
            self.writeln("########################################")
            self.writeln()
        elif not self._file:
            self._file = open(self._filename, "a+")

    def write(self, line=None):
        """Write a string in the manifest, no new line"""
        if not self._initialized:
            self.initialize()
        self._file.write(line)

    def writeln(self, text=None):
        """Write a string in the manifest, automatically add new line"""
        if text is None:
            self.write("\n")
        else:
            self.write(text + "\n")
