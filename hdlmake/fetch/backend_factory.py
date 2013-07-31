#!/usr/bin/env python

from git import Git
from svn import Svn
import logging


class Local(object):
    def __init__(self):
        pass

    def fetch(self, module):
        pass


class BackendFactory(object):
    def __init__(self):
        pass

    def get_backend(self, module):
            if module.source == "local":
                return Local()
            else:
                logging.info("Investigating module: " + str(module) +
                             "[parent: " + str(module.parent) + "]")
                if module.source == "svn":
                    return Svn()
                if module.source == "git":
                    return Git()
