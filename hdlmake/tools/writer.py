"""Package containing the classes required to print a Makefile"""

import logging
import sys

from hdlmake.dep_file import DepFile

from hdlmake.tools import (
    ToolIVerilog, ToolISim, ToolModelsim,
    ToolActiveHDL, ToolRiviera, ToolGHDL)

from hdlmake.tools import (
    ToolISE, ToolPlanAhead, ToolVivado,
    ToolQuartus, ToolDiamond, ToolLibero)


class WriterSim(object):

    """Class that is in charge of writing simulation Makefiles"""

    def __init__(self, module_pool):
        self.pool = module_pool
        self.iverilog = ToolIVerilog()
        self.isim = ToolISim()
        self.modelsim = ToolModelsim()
        self.active_hdl = ToolActiveHDL()
        self.riviera = ToolRiviera()
        self.ghdl = ToolGHDL()
        self.vivado = ToolVivado()

    def _check_simulation_makefile(self):
        """Check if the simulation keys are provided by the top manifest"""
        if not self.pool.get_top_module().manifest_dict["sim_top"]:
            logging.error("sim_top variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not self.pool.get_top_module().manifest_dict["sim_tool"]:
            logging.error("sim_tool variable must be set in the top manifest.")
            sys.exit("Exiting")

    def simulation_makefile(self):
        """Execute the simulation action"""
        self.pool._check_all_fetched_or_quit()
        self._check_simulation_makefile()
        tool_name = self.pool.get_top_module().manifest_dict["sim_tool"]
        tool_dict = {"iverilog": self.iverilog,
                     "isim": self.isim,
                     "modelsim": self.modelsim,
                     "active-hdl": self.active_hdl,
                     "riviera": self.riviera,
                     "ghdl": self.ghdl,
                     "vivado": self.vivado}
        if not tool_name in tool_dict:
            logging.error("Unknown sim_tool: %s", tool_name)
            sys.exit("Exiting")
        tool_object = tool_dict[tool_name]
        tool_info = tool_object.TOOL_INFO
        name = tool_info['name']
        self.pool.env.check_tool(tool_object)
        logging.info("Generating " + name + " makefile for simulation.")
        top_module = self.pool.get_top_module()
        fset = self.pool.build_file_set(
            top_module.manifest_dict["sim_top"],
            standard_libs=tool_object.STANDARD_LIBS)
        # Filter the not parseable files!
        dep_files = fset.filter(DepFile)
        # dep_solver.solve(dep_files)
        tool_object.makefile_setup(top_module, dep_files)
        tool_object.makefile_sim_top()
        tool_object.makefile_sim_options()
        tool_object.makefile_sim_local()
        tool_object.makefile_sim_sources()
        tool_object.makefile_sim_compilation()
        tool_object.makefile_sim_command()
        tool_object.makefile_sim_clean()
        tool_object.makefile_sim_phony()


class WriterSyn(object):

    """Class that is in charge of writing synthesis Makefiles"""

    def __init__(self, module_pool):
        self.pool = module_pool
        self.ise = ToolISE()
        self.planahead = ToolPlanAhead()
        self.vivado = ToolVivado()
        self.quartus = ToolQuartus()
        self.diamond = ToolDiamond()
        self.libero = ToolLibero()

    def _load_synthesis_tool(self):
        """Returns a tool_object that provides the synthesis tool interface"""
        tool_name = self.pool.get_top_module().manifest_dict["syn_tool"]
        tool_dict = {"ise": self.ise,
                     "planahead": self.planahead,
                     "vivado": self.vivado,
                     "quartus": self.quartus,
                     "diamond": self.diamond,
                     "libero": self.libero}
        if not tool_name in tool_dict:
            logging.error("Synthesis tool not recognized: %s", tool_name)
            quit()
        return tool_dict[tool_name]


    def _check_synthesis_project(self):
        """Check the manifest contains all the keys for a synthesis project"""
        manifest = self.pool.get_top_module().manifest_dict
        if not manifest["syn_tool"]:
            logging.error(
                "syn_tool variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not manifest["syn_device"]:
            logging.error(
                "syn_device variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not manifest["syn_grade"]:
            logging.error(
                "syn_grade variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not manifest["syn_package"]:
            logging.error(
                "syn_package variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not manifest["syn_top"]:
            logging.error(
                "syn_top variable must be set in the top manifest.")
            sys.exit("Exiting")

    def synthesis_project(self):
        """Generate a project for the specific synthesis tool"""
        self.pool._check_all_fetched_or_quit()
        self._check_synthesis_project()
        tool_object = self._load_synthesis_tool()
        tool_info = tool_object.TOOL_INFO
        path_key = tool_info['id'] + '_path'
        name = tool_info['name']
        env = self.pool.env
        env.check_tool(tool_object)
        top_module = self.pool.get_top_module()
        if env[path_key]:
            tool_path = env[path_key]
        else:
            tool_path = ""
        fileset = self.pool.build_file_set(
            top_module.manifest_dict["syn_top"],
            standard_libs=tool_object.STANDARD_LIBS)
        sup_files = self.pool.build_complete_file_set()
        privative_files = []
        for file_aux in sup_files:
            if any(isinstance(file_aux, file_type)
                   for file_type in tool_object.SUPPORTED_FILES):
                privative_files.append(file_aux)
        if len(privative_files) > 0:
            logging.info("Detected %d supported files that are not parseable",
                         len(privative_files))
            fileset.add(privative_files)
        tool_object.makefile_setup(top_module, fileset)
        tool_object.makefile_includes()
        tool_object.makefile_syn_top(tool_path)
        tool_object.makefile_syn_tcl()
        tool_object.makefile_syn_files()
        tool_object.makefile_syn_local()
        tool_object.makefile_syn_command()
        tool_object.makefile_syn_build()
        tool_object.makefile_syn_clean()
        tool_object.makefile_syn_phony()
        logging.info(name + " project file generated.")

