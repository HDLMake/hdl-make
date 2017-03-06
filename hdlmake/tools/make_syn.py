"""Module providing the synthesis functionality for writing Makefiles"""

from __future__ import absolute_import
import os, sys
import logging
import string

from .makefile import ToolMakefile
from hdlmake.util import path as path_mod


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

    def synthesis_project(self, pool):
        """Generate a project for the specific synthesis tool"""
        pool.check_all_fetched_or_quit()
        manifest_project_dict = {}
        for mod in pool:
            manifest_project_dict.update(mod.manifest_dict)
            if 'fetchto' in mod.manifest_dict:
                self.repo_list.append(
                    os.path.abspath(
                        os.path.join(
                            mod.path,
                            mod.manifest_dict['fetchto'])))
        _check_synthesis_manifest(manifest_project_dict)
        top_module = pool.get_top_module()
        fileset = pool.build_file_set(
            manifest_project_dict["syn_top"],
            standard_libs=self._standard_libs)
        sup_files = pool.build_complete_file_set()
        privative_files = []
        for file_aux in sup_files:
            if any(isinstance(file_aux, file_type)
                   for file_type in self._supported_files):
                privative_files.append(file_aux)
        if len(privative_files) > 0:
            logging.info("Detected %d supported files that are not parseable",
                         len(privative_files))
            fileset.add(privative_files)
        self.makefile_setup(manifest_project_dict, fileset)
        self.makefile_check_tool('syn_path')
        self.makefile_includes()
        self.makefile_syn_top()
        self.makefile_syn_tcl()
        self.makefile_syn_files()
        self.makefile_syn_local()
        self.makefile_syn_command()
        self.makefile_syn_build()
        self.makefile_syn_clean()
        self.makefile_syn_phony()
        logging.info(self._tool_info['name'] + " synthesis makefile generated.")

    def makefile_syn_top(self):
        """Create the top part of the synthesis Makefile"""
        if path_mod.check_windows():
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

""")
        self.writeln(top_parameter.substitute(
            tcl_interpreter=tcl_interpreter,
            project_name=os.path.splitext(
                self.manifest_dict["syn_project"])[0],
            project_ext=self._tool_info["project_ext"],
            tool_path=self.manifest_dict["syn_path"],
            top_module=self.manifest_dict["syn_top"]))

    def makefile_syn_tcl(self):
        """Create the Makefile TCL dictionary for the selected tool"""
        tcl_string = string.Template("""\
define TCL_CREATE
${tcl_create}
endef
export TCL_CREATE

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
""")
        self.writeln(tcl_string.substitute(
            tcl_create=self._tcl_controls["create"],
            tcl_open=self._tcl_controls["open"],
            tcl_save=self._tcl_controls["save"],
            tcl_close=self._tcl_controls["close"]))
        stage_list = ["synthesize", "translate", "map", "par", "bitstream"]
        for stage in stage_list:
            if not self._tcl_controls[stage] == "":
                self.writeln("""\
define TCL_{1}
{0}
endef
export TCL_{1}
""".format(self._tcl_controls[stage], stage.upper()))

    def makefile_syn_files(self):
        """End stub method to write the synthesis files section"""
        pass

    def makefile_syn_local(self):
        """Generic method to write the synthesis Makefile local target"""
        self.writeln("#target for performing local synthesis\n"
                     "all: bitstream\n")

    def makefile_syn_build(self):
        """Generate the synthesis Makefile targets for handling design build"""
        stage_previous = "project"
        stage_list = ["synthesize", "translate", "map", "par", "bitstream"]
        self.writeln("""\
project.tcl:
\t\techo "$$TCL_CREATE" > $@
\t\techo "$$TCL_FILES" >> $@
\t\techo "$$TCL_SAVE" >> $@
\t\techo "$$TCL_CLOSE" >> $@

project: project.tcl
\t\t$(SYN_PRE_PROJECT_CMD)
\t\t$(TCL_INTERPRETER) $@.tcl
\t\t$(SYN_POST_PROJECT_CMD)
\t\ttouch $@
""") 
        for stage in stage_list:
            if not self._tcl_controls[stage] == "":
                self.writeln("""\
{0}.tcl:
\t\techo "$$TCL_OPEN" > $@
\t\techo "$$TCL_{2}" >> $@
\t\techo "$$TCL_SAVE" >> $@
\t\techo "$$TCL_CLOSE" >> $@

{0}: {1} {0}.tcl
\t\t$(SYN_PRE_{2}_CMD)
\t\t$(TCL_INTERPRETER) $@.tcl
\t\t$(SYN_POST_{2}_CMD)
\t\ttouch $@
""".format(stage, stage_previous, stage.upper()))
                stage_previous = stage

    def makefile_syn_command(self):
        """Create the Makefile targets for user defined commands"""
        stage_list = ["project", "synthesize", "translate",
                      "map", "par", "bitstream"]
        for stage in stage_list:
            if not self._tcl_controls.get(stage) == "":
                self.writeln("""\
SYN_PRE_{0}_CMD := {1}
SYN_POST_{0}_CMD := {2}
""".format(stage.upper(),
           self.manifest_dict.get("syn_pre_" + stage + "_cmd", ''),
           self.manifest_dict.get("syn_post_" + stage + "_cmd", '')))

    def makefile_syn_clean(self):
        """Print the Makefile clean target for synthesis"""
        self.makefile_clean()
        self.writeln("\t\t" + path_mod.del_command() +
                     " project synthesize translate map par bitstream")
        self.writeln("\t\t" + path_mod.del_command() +
                     " project.tcl synthesize.tcl translate.tcl" +
                     " map.tcl par.tcl bitstream.tcl")
        self.makefile_mrproper()

    def makefile_syn_phony(self):
        """Print synthesis PHONY target list to the Makefile"""
        self.writeln(
            ".PHONY: mrproper clean all")
