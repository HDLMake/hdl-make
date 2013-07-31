#!/usr/bin/env python

import sys
import logging
from makefile_writer import MakefileWriter


class Action(object):
    def __init__(self, modules_pool, options, env):
        self.modules_pool = modules_pool
        self.options = options
        self.env = env
        self.make_writer = MakefileWriter()

        self._check_manifest()
        self._check_env()
        self._check_options()

    @property
    def top_module(self):
        return self.modules_pool.get_top_module()

    def _check_manifest(self):
        pass

    def _check_env(self):
        pass

    def _check_options(self):
        pass

    def run(self):
        raise NotImplementedError()

    def _check_all_fetched_or_quit(self):
        pool = self.modules_pool
        if not pool.is_everything_fetched():
            logging.error("A module remains unfetched. "
                          "Fetching must be done prior to makefile generation")
            print(str([str(m) for m in self.modules_pool if not m.isfetched]))
            sys.exit("Exiting.")

    def _check_manifest_variable_is_set(self, name):
        if getattr(self.top_module, name) is None:
            logging.error("Variable %s must be set in the manifest to perform current action", name)
            sys.exit("Exiting")

    def _check_manifest_variable_is_equal_to(self, name, value):
        ok = False
        try:
            manifest_value = getattr(self.top_module, name)
            if manifest_value == value:
                ok = True
        except:
            pass

        if ok is False:
            logging.error("Variable %s must be set in the manifest and equal to '%s'." % (name, value))
            sys.exit("Exiting")
