"""Provides the core functionality for the HDLMake module"""

import os
import logging

from hdlmake import fetch

class ModuleCore(object):
    """This is the class providing the module core functionality"""
    def __init__(self):
        # Universal Manifest Properties
        self.library = "work"
        self.target = None
        self.action = None
        self.top_entity = None
        super(ModuleCore, self).__init__()

        # Manifest Force tool Property
        self.force_tool = None


    def process_manifest(self):
        """Method that process the core manifest section"""
        self._process_manifest_force_tool()
        self._process_manifest_universal()
        #super(ModuleCore, self).process_manifest()


    def _process_manifest_force_tool(self):
        """Method processing the force_tool manifest directive"""
        if self.manifest_dict["force_tool"]:
            force_tool = self.manifest_dict["force_tool"]
            self.force_tool = force_tool.split(' ')
            if len(self.force_tool) != 3:
                logging.warning("Incorrect force_tool format %s. Ignoring",
                    self.force_tool)
                self.force_tool = None


    def _process_manifest_universal(self):
        """Method processing the universal manifest directives"""
        #if "top_module" in self.manifest_dict:
        #    self.top_module = self.manifest_dict["top_module"]
        # Libraries
        self.library = self.manifest_dict["library"]
        self.target = self.manifest_dict["target"].lower()
        self.action = self.manifest_dict["action"].lower()


