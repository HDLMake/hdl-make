"""Module providing the synthesis functionality for writing Makefiles"""

import os
import sys
import string
import platform

from hdlmake.action import ActionMakefile
from hdlmake.util import path as path_mod

class ToolSim(ActionMakefile):

    """Class that provides the Makefile writing methods and status"""

    def __init__(self):
        super(ToolSim, self).__init__()

    def makefile_sim_top(self, top_module):
        top_parameter = string.Template("""\
TOP_MODULE := ${top_module}
PWD := $$(shell pwd)
""")
        self.writeln(top_parameter.substitute(
            top_module=top_module.manifest_dict["sim_top"]))

    def makefile_sim_options(self, top_module):
        pass

    def makefile_sim_local(self, top_module):
        self.writeln("#target for performing local simulation\n"
                     "local: sim_pre_cmd simulation sim_post_cmd\n")
    def makefile_sim_sources(self, fileset):
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

    def makefile_sim_command(self, top_module):
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

    def makefile_sim_clean(self, clean_targets):
        """Print the Makefile clean target for synthesis"""
        self._print_tool_clean(clean_targets)
        self._print_tool_mrproper(clean_targets)

    def makefile_sim_phony(self, top_module):
        """Print simulation PHONY target list to the Makefile"""
        self.writeln(
            ".PHONY: mrproper clean sim_pre_cmd sim_post_cmd simulation")

