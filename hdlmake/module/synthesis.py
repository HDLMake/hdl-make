from .plugin import ModulePlugin

class ModuleSynthesis(ModulePlugin):
    def __init__(self):
        # Manifest Synthesis Properties
        self.syn_device = None
        self.syn_family = None
        self.syn_grade = None
        self.syn_package = None
        self.syn_project = None
        self.syn_top = None
        self.syn_tool = None
        self.syn_ise_version = None
        self.syn_pre_script = None
        self.syn_post_script = None
        # Manifest Included Makefiles
        self.incl_makefiles = []
        super(ModuleSynthesis, self).__init__()

    def process_manifest(self):
        self._process_manifest_synthesis()
        self._process_manifest_included_makefiles()
        super(ModuleSynthesis, self).process_manifest()

    def _process_manifest_synthesis(self):
        # Synthesis properties
        self.syn_pre_cmd = self.manifest_dict["syn_pre_cmd"]
        self.syn_pre_synthesize_cmd = self.manifest_dict["syn_pre_synthesize_cmd"]
        self.syn_post_synthesize_cmd = self.manifest_dict["syn_post_synthesize_cmd"]
        self.syn_pre_translate_cmd = self.manifest_dict["syn_pre_translate_cmd"]
        self.syn_post_translate_cmd = self.manifest_dict["syn_post_translate_cmd"]
        self.syn_pre_map_cmd = self.manifest_dict["syn_pre_map_cmd"]
        self.syn_post_map_cmd = self.manifest_dict["syn_post_map_cmd"]
        self.syn_pre_par_cmd = self.manifest_dict["syn_pre_par_cmd"]
        self.syn_post_par_cmd = self.manifest_dict["syn_post_par_cmd"]
        self.syn_pre_bitstream_cmd = self.manifest_dict["syn_pre_bitstream_cmd"]
        self.syn_post_bitstream_cmd = self.manifest_dict["syn_post_bitstream_cmd"]
        self.syn_post_cmd = self.manifest_dict["syn_post_cmd"]
        if self.manifest_dict["syn_name"] is None and self.manifest_dict["syn_project"] is not None:
            self.syn_name = self.manifest_dict["syn_project"][:-5]  # cut out .xise from the end
        else:
            self.syn_name = self.manifest_dict["syn_name"]
        self.syn_tool = self.manifest_dict["syn_tool"]
        self.syn_device = self.manifest_dict["syn_device"]
        self.syn_family = self.manifest_dict["syn_family"]
        self.syn_grade = self.manifest_dict["syn_grade"]
        self.syn_package = self.manifest_dict["syn_package"]
        self.syn_project = self.manifest_dict["syn_project"]
        self.syn_top = self.manifest_dict["syn_top"]
        if self.manifest_dict["syn_ise_version"] is not None:
            version = self.manifest_dict["syn_ise_version"]
            self.syn_ise_version = str(version)

    def _process_manifest_included_makefiles(self):
        # Included Makefiles
        mkFileList = []
        if isinstance(self.manifest_dict["incl_makefiles"], basestring):
            mkFileList.append(self.manifest_dict["incl_makefiles"])
        else:  # list
            mkFileList = self.manifest_dict["incl_makefiles"][:]

        makefiles_paths = self._make_list_of_paths(mkFileList)
        self.incl_makefiles.extend(makefiles_paths)

