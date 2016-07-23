from .module_plugin import ModulePlugin

class ModuleCore(ModulePlugin):
    def __init__(self):
        # Universal Manifest Properties
        self.library = "work"
        self.target = None
        self.action = None
        super(ModuleCore, self).__init__()

        # Manifest Force tool Property
        self.force_tool = None

    def process_manifest(self):
        self._process_manifest_force_tool()
        self._process_manifest_universal()
        super(ModuleCore, self).process_manifest()

    def _process_manifest_force_tool(self):
        if self.manifest_dict["force_tool"]:
            ft = self.manifest_dict["force_tool"]
            self.force_tool = ft.split(' ')
            if len(self.force_tool) != 3:
                logging.warning("Incorrect force_tool format %s. Ignoring" % self.force_tool)
                self.force_tool = None


    def _process_manifest_universal(self):
        if "top_module" in self.manifest_dict:
            self.top_module = self.manifest_dict["top_module"]
        # Libraries
        self.library = self.manifest_dict["library"]
        self.target = self.manifest_dict["target"].lower()
        self.action = self.manifest_dict["action"].lower()

