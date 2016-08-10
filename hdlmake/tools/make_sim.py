"""Module providing the simulation functionality for writing Makefiles"""

import os
import sys
import string
import logging

from .makefile import ToolMakefile
from hdlmake.util import path as path_mod
from hdlmake.srcfile import VerilogFile, VHDLFile, SVFile
from hdlmake.dep_file import DepFile


def _check_simulation_manifest(manifest_dict):
    """Check if the simulation keys are provided by the top manifest"""
    if not manifest_dict["sim_top"]:
        logging.error("sim_top variable must be set in the top manifest.")
        sys.exit("Exiting")
    if not manifest_dict["sim_tool"]:
        logging.error("sim_tool variable must be set in the top manifest.")
        sys.exit("Exiting")


class ToolSim(ToolMakefile):

    """Class that provides the Makefile writing methods and status"""

    def __init__(self):
        super(ToolSim, self).__init__()
        self._simulator_controls = {}

    def simulation_makefile(self, pool):
        """Execute the simulation action"""
        _check_simulation_manifest(pool.top_module.manifest_dict)
        pool.check_all_fetched_or_quit()
        pool.env.check_tool(self)
        logging.info("Generating " + self._tool_info['name'] +
                     " makefile for simulation.")
        top_module = pool.get_top_module()
        fset = pool.build_file_set(
            top_module.manifest_dict["sim_top"],
            standard_libs=self._standard_libs)
        # Filter the not parseable files!
        dep_files = fset.filter(DepFile)
        # dep_solver.solve(dep_files)
        self.makefile_setup(top_module, dep_files)
        self.makefile_sim_top()
        self.makefile_sim_options()
        self.makefile_sim_local()
        self.makefile_sim_sources()
        self.makefile_sim_compilation()
        self.makefile_sim_command()
        self.makefile_sim_clean()
        self.makefile_sim_phony()

    def makefile_sim_top(self):
        """Generic method to write the simulation Makefile top section"""
        top_parameter = string.Template("""\
TOP_MODULE := ${top_module}
PWD := $$(shell pwd)
""")
        self.writeln(top_parameter.substitute(
            top_module=self.top_module.manifest_dict["sim_top"]))

    def makefile_sim_options(self):
        """End stub method to write the simulation Makefile options section"""
        pass

    def makefile_sim_compilation(self):
        """End stub method to write the simulation Makefile compilation
        section"""
        pass

    def makefile_sim_local(self):
        """Generic method to write the simulation Makefile local target"""
        self.writeln("#target for performing local simulation\n"
                     "local: sim_pre_cmd simulation sim_post_cmd\n")

    def makefile_sim_sources(self):
        """Generic method to write the simulation Makefile HDL sources"""
        fileset = self.fileset
        self.write("VERILOG_SRC := ")
        for vlog in fileset.filter(VerilogFile):
            self.writeln(vlog.rel_path() + " \\")
        self.writeln()
        self.write("VERILOG_OBJ := ")
        for vlog in fileset.filter(VerilogFile):
            # make a file compilation indicator (these .dat files are made even
            # if the compilation process fails) and add an ending according
            # to file's extension (.sv and .vhd files may have the same
            # corename and this causes a mess
            self.writeln(
                os.path.join(
                    vlog.library,
                    vlog.purename,
                    "." +
                    vlog.purename +
                    "_" +
                    vlog.extension(
                    )) +
                " \\")
        self.writeln()
        self.write("VHDL_SRC := ")
        for vhdl in fileset.filter(VHDLFile):
            self.write(vhdl.rel_path() + " \\\n")
        self.writeln()
        # list vhdl objects (_primary.dat files)
        self.write("VHDL_OBJ := ")
        for vhdl in fileset.filter(VHDLFile):
            # file compilation indicator (important: add _vhd ending)
            self.writeln(
                os.path.join(
                    vhdl.library,
                    vhdl.purename,
                    "." +
                    vhdl.purename +
                    "_" +
                    vhdl.extension(
                    )) +
                " \\")
        self.writeln()

    def makefile_sim_dep_files(self):
        """Print dummy targets to handle file dependencies"""
        fileset = self.fileset
        for file_aux in fileset:
            if any(isinstance(file_aux, file_type)
                   for file_type in self._hdl_files):
                self.write("%s: %s" % (os.path.join(
                    file_aux.library, file_aux.purename,
                    ".%s_%s" % (file_aux.purename, file_aux.extension())),
                    file_aux.rel_path()))
                # list dependencies, do not include the target file
                for dep_file in [dfile for dfile in file_aux.depends_on
                                 if dfile is not file_aux]:
                    if dep_file in fileset:
                        name = dep_file.purename
                        extension = dep_file.extension()
                        self.write(" \\\n" + os.path.join(
                            dep_file.library, name, ".%s_%s" %
                            (name, extension)))
                    else:
                        # the file is included -> we depend directly on it
                        self.write(" \\\n" + dep_file.rel_path())
                self.writeln()
                if isinstance(file_aux, VHDLFile):
                    command_key = 'vhdl'
                elif (isinstance(file_aux, VerilogFile) or
                      isinstance(file_aux, SVFile)):
                    command_key = 'vlog'
                self.writeln("\t\t" + self._simulator_controls[command_key])
                self.write("\t\t@" + path_mod.mkdir_command() + " $(dir $@)")
                self.writeln(" && touch $@ \n")
                self.writeln()

    def makefile_sim_command(self):
        """Generic method to write the simulation Makefile user commands"""
        if self.top_module.manifest_dict["sim_pre_cmd"]:
            sim_pre_cmd = self.top_module.manifest_dict["sim_pre_cmd"]
        else:
            sim_pre_cmd = ''
        if self.top_module.manifest_dict["sim_post_cmd"]:
            sim_post_cmd = self.top_module.manifest_dict["sim_post_cmd"]
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

    def makefile_sim_clean(self):
        """Generic method to write the simulation Makefile user clean target"""
        self.makefile_clean()
        self.makefile_mrproper()

    def makefile_sim_phony(self):
        """Print simulation PHONY target list to the Makefile"""
        self.writeln(
            ".PHONY: mrproper clean sim_pre_cmd sim_post_cmd simulation")
