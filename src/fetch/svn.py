#!/usr/bin/env python

import os
import logging
from util import path
from subprocess import Popen, PIPE


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

    @staticmethod
    def check_revision_number(path):
        cur_dir = os.getcwd()
        try:
            os.chdir(path)
            svn_cmd = "svn info | awk '{if(NR == 5) {print $2}}'"
            svn_out = Popen(svn_cmd, shell=True, stdin=PIPE, stdout=PIPE, close_fds=True)
            revision = svn_out.stdout.readlines()[0].strip()
        finally:
            os.chdir(cur_dir)
        return revision
