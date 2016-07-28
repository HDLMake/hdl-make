"""This Python module is where the synthesis stuff is processed and stored"""

from .core import ModuleCore

class ModuleSynthesis(ModuleCore):
    """This class provides the container for the synthesis sub-module"""
    def __init__(self):
        # Device constructor
        self.syn_project = None
        self.syn_top = None
        self.syn_tool = None
        self.syn_ise_version = None
        # Manifest Included Makefiles
        self.incl_makefiles = []


        super(ModuleSynthesis, self).__init__()

    def process_manifest(self):
        """Process the synthesis section of the manifest dict"""
        self._process_manifest_synthesis()
        self._process_included_makefiles()
        super(ModuleSynthesis, self).process_manifest()

    def _process_manifest_synthesis(self):
        """Init generic synthesis properties"""
        # Synthesis tool
        self.syn_tool = self.manifest_dict["syn_tool"]

        # Project parameters
        self.syn_project = self.manifest_dict["syn_project"]
        self.syn_top = self.manifest_dict["syn_top"]

        # This is a Xilinx ISE specific value
        if self.manifest_dict["syn_ise_version"] is not None:
            version = self.manifest_dict["syn_ise_version"]
            self.syn_ise_version = str(version)


    def _process_included_makefiles(self):
        """Get the extra makefiles defined in the HDLMake module"""
        # Included Makefiles
        included_makefiles_aux = []
        if isinstance(self.manifest_dict["incl_makefiles"], basestring):
            included_makefiles_aux.append(self.manifest_dict["incl_makefiles"])
        else:  # list
            included_makefiles_aux = self.manifest_dict["incl_makefiles"][:]

        makefiles_paths = self._make_list_of_paths(included_makefiles_aux)
        self.incl_makefiles.extend(makefiles_paths)

