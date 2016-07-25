"""Provides the core functionality for the HDLMake module"""

import os
import logging

from .plugin import ModulePlugin
from hdlmake.util import path as path_mod
from hdlmake import fetch

class ModuleCore(ModulePlugin):
    """This is the class providing the module core functionality"""
    def __init__(self):
        # Universal Manifest Properties
        self.library = "work"
        self.target = None
        self.action = None
        super(ModuleCore, self).__init__()

        # Manifest Force tool Property
        self.force_tool = None

        # Origin attributes
        self.isfetched = False
        # raw_url is the full url, including: branch, revision, commit, tag
        self.raw_url = None
        # url is stripped down web url, not including any other parameter
        self.url = None
        self.parent = None
        self.source = None
        self.branch = None
        self.path = None
        self.fetchto = None
        self.revision = None


    def __str__(self):
        return self.raw_url

    @property
    def basename(self):
        """Get the basename for a module instance"""
        if self.source == fetch.SVN:
            return path_mod.svn_basename(self.url)
        else:
            return path_mod.url_basename(self.url)


    def process_manifest(self):
        """Method that process the core manifest section"""
        self._process_manifest_force_tool()
        self._process_manifest_universal()
        super(ModuleCore, self).process_manifest()


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


    def _set_origin(self, parent, url, source, fetchto):
        """Calculate and initialize the origin attributes: path, source..."""
        self.source = source
        self.parent = parent
        self.fetchto = fetchto
        self.raw_url = url
        if source != fetch.LOCAL:
            self.url, self.branch, self.revision = path_mod.url_parse(url)
            if (
                    os.path.exists(
                        os.path.abspath(
                            os.path.join(fetchto, self.basename)
                        )
                    ) and
                    os.listdir(
                        os.path.abspath(os.path.join(fetchto, self.basename))
                    )
               ):
                self.path = os.path.abspath(
                    os.path.join(fetchto, self.basename))
                self.isfetched = True
                logging.debug("Module %s (parent: %s) is fetched.",
                    url, parent.path)
            else:
                self.path = None
                self.isfetched = False
                logging.debug("Module %s (parent: %s) is NOT fetched.",
                    url, parent.path)
        else:
            self.url, self.branch, self.revision = url, None, None

            if not os.path.exists(url):
                logging.error(
                    "Path to the local module doesn't exist:\n" + url
                    + "\nThis module was instantiated in: " + str(parent))
                quit()
            self.path = url
            self.isfetched = True

