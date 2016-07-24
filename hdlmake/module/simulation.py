from .plugin import ModulePlugin

class ModuleSimulation(ModulePlugin):

    def __init__(self):
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
        # Includes Manifest Properties
        self.include_dirs = None
        super(ModuleSimulation, self).__init__()

    def process_manifest(self):
        self._process_manifest_simulation()
        self._process_manifest_includes()
        super(ModuleSimulation, self).process_manifest()

    def _process_manifest_simulation(self):
        from hdlmake.srcfile import SourceFileSet
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


    def _process_manifest_includes(self):
        # Include dirs
        self.include_dirs = []
        if self.manifest_dict["include_dirs"] is not None:
            if isinstance(self.manifest_dict["include_dirs"], basestring):
                ll = os.path.relpath(os.path.abspath(os.path.join(self.path, self.manifest_dict["include_dirs"])))
                self.include_dirs.append(ll)
            else:
                ll = map(lambda x: os.path.relpath(os.path.abspath(os.path.join(self.path, x))),
                         self.manifest_dict["include_dirs"])
                self.include_dirs.extend(ll)
        # Analyze included dirs and report if any issue is found
        for dir_ in self.include_dirs:
            if path_mod.is_abs_path(dir_):
                logging.warning("%s contains absolute path to an include directory: %s" % (self.path, dir_))
            if not os.path.exists(dir_):
                logging.warning(self.path + " has an unexisting include directory: " + dir_)

