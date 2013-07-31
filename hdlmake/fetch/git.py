#!/usr/bin/env python

import os
from util import path
import logging
from tempfile import TemporaryFile
from subprocess import Popen, PIPE


class Git(object):
    def __init__(self):
        pass

    def fetch(self, module):
        if not os.path.exists(module.fetchto):
            os.mkdir(module.fetchto)

        cur_dir = os.getcwd()
        if module.branch is None:
            module.branch = "master"

        basename = path.url_basename(module.url)
        mod_path = os.path.join(module.fetchto, basename)

        if basename.endswith(".git"):
            basename = basename[:-4]  # remove trailing .git

        if module.isfetched:
            update_only = True
        else:
            update_only = False

        if update_only:
            logging.info("Updating module %s" % mod_path)
            cmd = "(cd {0} && git checkout {1})"
            cmd = cmd.format(mod_path, module.branch)
        else:
            logging.info("Cloning module %s" % mod_path)
            cmd = "(cd {0} && git clone -b {2} {1})"
            cmd = cmd.format(module.fetchto, module.url, module.branch)

        success = True

        logging.debug("Running %s" % cmd)
        if os.system(cmd) != 0:
            success = False

        if success is True:
            os.chdir(mod_path)
            os.system("git submodule init")
            os.system("git submodule update")
            os.chdir(cur_dir)

        if module.revision is not None and success is True:
            logging.debug("cd %s" % mod_path)
            os.chdir(mod_path)
            cmd = "git checkout " + module.revision
            logging.debug("Running %s" % cmd)
            if os.system(cmd) != 0:
                success = False
            os.chdir(cur_dir)

        module.isfetched = True
        module.path = mod_path
        return success

    @staticmethod
    def check_commit_id(path):
        cur_dir = os.getcwd()
        commit = None
        stderr = TemporaryFile()
        try:
            os.chdir(path)
            git_cmd = 'git log -1 --format="%H" | cut -c1-32'
            git_out = Popen(git_cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=stderr, close_fds=True)
            errmsg = stderr.readlines()
            if errmsg:
                logging.debug("git error message (in %s): %s" % (path, '\n'.join(errmsg)))

            try:
                commit = git_out.stdout.readlines()[0].strip()
            except IndexError:
                pass
        finally:
            os.chdir(cur_dir)
            stderr.close()
        return commit
