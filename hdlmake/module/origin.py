import os
import logging

from hdlmake import fetch
from hdlmake.util import path as path_mod

class ModuleOrigin(object):
    def set_origin(self, parent, url, source, fetchto):
        # Manifest Module Origin Properties
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

        #super(ModuleOrigin, self).__init__(parent, url, source, fetchto)


