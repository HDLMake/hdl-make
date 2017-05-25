"""Module providing the synthesis functionality for writing Makefiles"""

from __future__ import absolute_import
import os, sys
import logging
import string

from .makefile import ToolMakefile
from hdlmake.util import shell


def _check_synthesis_manifest(manifest_dict):
    """Check the manifest contains all the keys for a synthesis project"""
    if not manifest_dict["syn_tool"]:
        logging.error(
            "syn_tool variable must be set in the top manifest.")
        sys.exit("Exiting")
    if not manifest_dict["syn_device"]:
        logging.error(
            "syn_device variable must be set in the top manifest.")
        sys.exit("Exiting")
    if not manifest_dict["syn_grade"]:
        logging.error(
            "syn_grade variable must be set in the top manifest.")
        sys.exit("Exiting")
    if not manifest_dict["syn_package"]:
        logging.error(
            "syn_package variable must be set in the top manifest.")
        sys.exit("Exiting")
    if not manifest_dict["syn_top"]:
        logging.error(
            "syn_top variable must be set in the top manifest.")


class ToolSyn(ToolMakefile):

    """Class that provides the synthesis Makefile writing methods and status"""

    def __init__(self):
        super(ToolSyn, self).__init__()

    def write_makefile(self, config, fileset, filename=None):
        """Generate a Makefile for the specific synthesis tool"""
        _check_synthesis_manifest(config)
        self.makefile_setup(config, fileset,
            filename=filename)
        self.makefile_check_tool('syn_path')
        self.makefile_includes()
        self._makefile_syn_top()
        self._makefile_syn_tcl()
        self._makefile_syn_local()
        self._makefile_syn_files()
        self._makefile_syn_command()
        self._makefile_syn_build()
        self._makefile_syn_clean()
        self._makefile_syn_phony()
        logging.info(self._tool_info['name'] + " synthesis makefile generated.")

    def _makefile_syn_top(self):
        """Create the top part of the synthesis Makefile"""
        if shell.check_windows():
            tcl_interpreter = self._tool_info["windows_bin"]
        else:
            tcl_interpreter = self._tool_info["linux_bin"]
        top_parameter = string.Template("""\
TOP_MODULE := ${top_module}
PWD := $$(shell pwd)
PROJECT := ${project_name}
PROJECT_FILE := $$(PROJECT).${project_ext}
TOOL_PATH := ${tool_path}
TCL_INTERPRETER := ${tcl_interpreter}
ifneq ($$(strip $$(TOOL_PATH)),)
TCL_INTERPRETER := $$(TOOL_PATH)/$$(TCL_INTERPRETER)
endif

SYN_FAMILY := ${syn_family}
SYN_DEVICE := ${syn_device}
SYN_PACKAGE := ${syn_package}
SYN_GRADE := ${syn_grade}
""")
        self.writeln(top_parameter.substitute(
            tcl_interpreter=tcl_interpreter,
            project_name=os.path.splitext(
                self.manifest_dict["syn_project"])[0],
            project_ext=self._tool_info["project_ext"],
            syn_family=self.manifest_dict.get("syn_family", ''),
            syn_device=self.manifest_dict["syn_device"],
            syn_package=self.manifest_dict["syn_package"],
            syn_grade=self.manifest_dict["syn_grade"],
            tool_path=self.manifest_dict["syn_path"],
            top_module=self.manifest_dict["syn_top"]))

    def _makefile_syn_tcl(self):
        """Create the Makefile TCL dictionary for the selected tool"""
        command_list = ["create", "open", "save", "close"]
        for command in command_list:
            if command in self._tcl_controls:
                self.writeln('TCL_{1} := {0}'.format(
                    self._tcl_controls[command], command.upper()))
        self.writeln("""\
ifneq ($(wildcard $(PROJECT_FILE)),)
TCL_CREATE := $(TCL_OPEN)
endif""")
        self.writeln()

    def _makefile_syn_files(self):
        """Write the files TCL section of the Makefile"""
        ret = []
        fileset_dict = {}
        sources_list = []
        fileset_dict.update(self._hdl_files)
        fileset_dict.update(self._supported_files)
        for filetype in fileset_dict:
            file_list = []
            for file_aux in self.fileset:
                if isinstance(file_aux, filetype):
                    file_list.append(shell.tclpath(file_aux.rel_path()))
            if not file_list == []:
                ret.append(
                   'SOURCES_{0} := \\\n'
                   '{1}\n'.format(filetype.__name__,
                               ' \\\n'.join(file_list)))
                if not fileset_dict[filetype] is None:
                    sources_list.append(filetype)
        self.writeln('\n'.join(ret))
        self.writeln('files.tcl:')
        if "files" in self._tcl_controls:
            echo_command = '\t\t@echo {0} >> $@'
            tcl_command = []
            for command in self._tcl_controls["files"].split('\n'):
                tcl_command.append(echo_command.format(command))
            command_string = "\n".join(tcl_command)
            if shell.check_windows():
                command_string = command_string.replace("'", "")
            self.writeln(command_string)
        for filetype in sources_list:
            filetype_string = ('\t\t@$(foreach sourcefile,'
                ' $(SOURCES_{0}), echo "{1}" >> $@ &)'.format(
                filetype.__name__, fileset_dict[filetype]))
            if shell.check_windows():
                filetype_string = filetype_string.replace(
                    '"', '')
            self.writeln(filetype_string)
        self.writeln()

    def _makefile_syn_local(self):
        """Generic method to write the synthesis Makefile local target"""
        self.writeln("#target for performing local synthesis\n"
                     "all: bitstream\n")

    def _makefile_syn_build(self):
        """Generate the synthesis Makefile targets for handling design build"""
        stage_previous = "files.tcl"
        stage_list = ["project", "synthesize", "translate",
                      "map", "par", "bitstream"]
        for stage in stage_list:
            if stage in self._tcl_controls:
                echo_command = '\t\techo {0} >> $@'
                tcl_command = []
                for command in self._tcl_controls[stage].split('\n'):
                    tcl_command.append(echo_command.format(command))
                command_string = "\n".join(tcl_command)
                if shell.check_windows():
                    command_string = command_string.replace(
                        "'", "")
                self.writeln("""\
{0}.tcl:
{3}

{0}: {1} {0}.tcl
\t\t$(SYN_PRE_{2}_CMD)
\t\t$(TCL_INTERPRETER) $@.tcl
\t\t$(SYN_POST_{2}_CMD)
\t\t{4} $@
""".format(stage, stage_previous, stage.upper(),
           command_string, shell.touch_command()))
                stage_previous = stage

    def _makefile_syn_command(self):
        """Create the Makefile targets for user defined commands"""
        stage_list = ["project", "synthesize", "translate",
                      "map", "par", "bitstream"]
        for stage in stage_list:
            if stage in self._tcl_controls:
                self.writeln("""\
SYN_PRE_{0}_CMD := {1}
SYN_POST_{0}_CMD := {2}
""".format(stage.upper(),
           self.manifest_dict.get("syn_pre_" + stage + "_cmd", ''),
           self.manifest_dict.get("syn_post_" + stage + "_cmd", '')))

    def _makefile_syn_clean(self):
        """Print the Makefile clean target for synthesis"""
        self.makefile_clean()
        self.writeln("\t\t" + shell.del_command() +
                     " project synthesize translate map par bitstream")
        self.writeln("\t\t" + shell.del_command() +
                     " project.tcl synthesize.tcl translate.tcl" +
                     " map.tcl par.tcl bitstream.tcl files.tcl")
        self.writeln()
        self.makefile_mrproper()

    def _makefile_syn_phony(self):
        """Print synthesis PHONY target list to the Makefile"""
        self.writeln(
            ".PHONY: mrproper clean all")
