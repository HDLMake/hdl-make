#!/usr/bin/env python

import os
import logging
import path


class Svn(object):
    def __init__(self):
        pass

    def fetch(self, module):
        if not os.path.exists(module.fetchto):
            os.mkdir(module.fetchto)

        cur_dir = os.getcwd()
        os.chdir(module.fetchto)

        basename = path.url_basename(module.url)
        mod_path = os.path.join(module.fetchto, basename)

        cmd = "svn checkout {0} " + module.basename
        if module.revision:
            cmd = cmd.format(module.url + '@' + module.revision)
        else:
            cmd = cmd.format(module.url)

        success = True

        logging.info("Checking out module %s" % mod_path)
        logging.debug(cmd)
        if os.system(cmd) != 0:
            success = False
        os.chdir(cur_dir)

        module.isfetched = True
        module.path = os.path.join(module.fetchto, module.basename)
        return success
