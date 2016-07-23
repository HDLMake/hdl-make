
class ModuleSimulation(object):
    def __init__(self):
        super(ModuleSimulation, self).__init__()
        # Manifest Simulation Properties
        self.sim_top = None
        self.sim_tool = None
        self.sim_pre_script = None
        self.sim_post_script = None
        self.sim_only_files = None
        self.vsim_opt = None
        self.vmap_opt = None
        self.vlog_opt = None
        self.vcom_opt = None
        self.iverilog_opt = None


    def _process_manifest_simulation(self):
        from .srcfile import SourceFileSet
        # Simulation properties
        self.sim_tool = self.manifest_dict["sim_tool"]
        self.sim_top = self.manifest_dict["sim_top"]
        self.sim_pre_cmd = self.manifest_dict["sim_pre_cmd"]
        self.sim_post_cmd = self.manifest_dict["sim_post_cmd"]

        self.vmap_opt = self.manifest_dict["vmap_opt"]
        self.vcom_opt = self.manifest_dict["vcom_opt"]
        self.vsim_opt = self.manifest_dict["vsim_opt"]
        self.vlog_opt = self.manifest_dict["vlog_opt"]
        self.iverilog_opt = self.manifest_dict["iverilog_opt"]

        if len(self.manifest_dict["sim_only_files"]) == 0:
            self.sim_only_files = SourceFileSet()
        else:
            self.manifest_dict["sim_only_files"] = self._flatten_list(self.manifest_dict["sim_only_files"])
            paths = self._make_list_of_paths(self.manifest_dict["sim_only_files"])
            self.sim_only_files = self._create_file_list_from_paths(paths=paths)


