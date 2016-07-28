"""This module is in charge of providing everything related with simulation
at the Module level"""

import os
import logging

from .core import ModuleCore
from hdlmake.util import path as path_mod

class SimulatorOptions(object):
    """Class providing a storage for simulator options"""
    def __init__(self):
        self.vsim_opt = None
        self.vmap_opt = None
        self.vlog_opt = None
        self.vcom_opt = None
        self.iverilog_opt = None

    def set_standard_options(self, vsim_opt, vmap_opt, vlog_opt, vcom_opt):
        """Set the standard simulator options, i.e. vsim, vmap, vlog, vcom"""
        self.vsim_opt = vsim_opt
        self.vmap_opt = vmap_opt
        self.vlog_opt = vlog_opt
        self.vcom_opt = vcom_opt

    def set_iverilog_options(self, iverilog_opt):
        """Set the specific options for Icarus Verilog"""
        self.iverilog_opt = iverilog_opt


class ModuleSimulation(ModuleCore):
    """This Class provides the HDLMake properties and methods
    the Module requires for the simulation action"""

    def __init__(self):
        # Manifest Simulation Properties
        self.sim_top = None
        self.sim_tool = None
        self.sim_pre_cmd = None
        self.sim_post_cmd = None
        self.sim_only_files = None
        self.sim_opt = SimulatorOptions()
        # Includes Manifest Properties
        self.include_dirs = None
        super(ModuleSimulation, self).__init__()

    def process_manifest(self):
        """Method that processes the simulation section in the manifest"""
        self._process_manifest_simulation()
        self._process_manifest_includes()
        super(ModuleSimulation, self).process_manifest()

    def _process_manifest_simulation(self):
        """Private method that processes options and universal sim keys"""
        from hdlmake.srcfile import SourceFileSet
        # Simulation properties
        self.sim_tool = self.manifest_dict["sim_tool"]
        self.sim_top = self.manifest_dict["sim_top"]
        self.sim_pre_cmd = self.manifest_dict["sim_pre_cmd"]
        self.sim_post_cmd = self.manifest_dict["sim_post_cmd"]

        self.sim_opt.vsim_opt = self.manifest_dict["vsim_opt"]
        self.sim_opt.vmap_opt = self.manifest_dict["vmap_opt"]
        self.sim_opt.vlog_opt = self.manifest_dict["vlog_opt"]
        self.sim_opt.vcom_opt = self.manifest_dict["vcom_opt"]

        self.sim_opt.set_standard_options(
            self.manifest_dict["vsim_opt"],
            self.manifest_dict["vmap_opt"],
            self.manifest_dict["vlog_opt"],
            self.manifest_dict["vcom_opt"]
            )

        self.sim_opt.set_iverilog_options(self.manifest_dict["iverilog_opt"])

        if len(self.manifest_dict["sim_only_files"]) == 0:
            self.sim_only_files = SourceFileSet()
        else:
            self.manifest_dict["sim_only_files"] = path_mod.flatten_list(
                self.manifest_dict["sim_only_files"])
            paths = self._make_list_of_paths(
                self.manifest_dict["sim_only_files"])
            self.sim_only_files = self._create_file_list_from_paths(
                paths=paths)


    def _process_manifest_includes(self):
        """Private method that processes the included directory list"""
        # Include dirs
        self.include_dirs = []
        if self.manifest_dict["include_dirs"] is not None:
            if isinstance(self.manifest_dict["include_dirs"], basestring):
                dir_list = path_mod.compose(
                    self.path, self.manifest_dict["include_dirs"])
                self.include_dirs.append(dir_list)
            else:
                dir_list = [path_mod.compose(self.path, x) for
                    x in self.manifest_dict["include_dirs"]]
                self.include_dirs.extend(dir_list)
        # Analyze included dirs and report if any issue is found
        for dir_ in self.include_dirs:
            if path_mod.is_abs_path(dir_):
                logging.warning(
                    "%s contains absolute path to an include directory: %s",
                     self.path, dir_)
            if not os.path.exists(dir_):
                logging.warning(self.path +
                    " has an unexisting include directory: " + dir_)

