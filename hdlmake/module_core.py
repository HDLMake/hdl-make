
class ModuleCore(object):
    def __init__(self):
        super(ModuleCore, self).__init__()
        # Universal Manifest Properties
        self.library = "work"
        self.target = None
        self.action = None

        # Manifest Force tool Property
        self.force_tool = None

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

