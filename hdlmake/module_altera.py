import os
from .util import path as path_mod

class ModuleAltera(object):
    def __init__(self):
        super(ModuleAltera, self).__init__()
        # Manifest Altera Properties
        self.quartus_preflow = None
        self.quartus_postmodule = None
        self.quartus_postflow = None
        self.hw_tcl_filename = None

    def _process_manifest_altera(self):
        from .srcfile import TCLFile
        if self.manifest_dict["quartus_preflow"] != None:
            path = path_mod.rel2abs(self.manifest_dict["quartus_preflow"], self.path);
            if not os.path.exists(path):
                p.error("quartus_preflow file listed in " + self.manifest.path + " doesn't exist: "
                        + path + ".\nExiting.")
                quit()
            self.quartus_preflow = TCLFile(path)

        if self.manifest_dict["quartus_postmodule"] != None:
            path = path_mod.rel2abs(self.manifest_dict["quartus_postmodule"], self.path);
            if not os.path.exists(path):
                p.error("quartus_postmodule file listed in " + self.manifest.path + " doesn't exist: "
                        + path + ".\nExiting.")
                quit()
            self.quartus_postmodule = TCLFile(path)

        if self.manifest_dict["quartus_postflow"] != None:
            path = path_mod.rel2abs(self.manifest_dict["quartus_postflow"], self.path);
            if not os.path.exists(path):
                p.error("quartus_postflow file listed in " + self.manifest.path + " doesn't exist: "
                        + path + ".\nExiting.")
                quit()
            self.quartus_postflow = TCLFile(path)

        if "hw_tcl_filename" in self.manifest_dict:
            self.hw_tcl_filename = self.manifest_dict["hw_tcl_filename"]

