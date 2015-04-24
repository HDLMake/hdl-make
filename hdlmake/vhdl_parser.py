#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013-2015 CERN
# Author: 
#     Tomasz Wlostowski (tomasz.wlostowski@cern.ch)
#     Adrian Fiergolski (Adrian.Fiergolski@cern.ch)
#
# This file is part of Hdlmake.
#
# Hdlmake is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hdlmake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Hdlmake.  If not, see <http://www.gnu.org/licenses/>.


from new_dep_solver import DepParser
import logging
import re


class VHDLPreprocessor(object):

    def __init__(self):
        self.vhdl_file = None

    def remove_comments_and_strings(self, s):
        pattern = re.compile( '--.*?$|".?"', re.DOTALL | re.MULTILINE )  
        return re.sub(pattern,"", s)
    
    def _preporcess_file(self, file_content, file_name, library):
        logging.debug("preprocess file %s (of length %d) in library %s" % (file_name, len(file_content), library) )
        return self.remove_comments_and_strings(file_content)
        
    def preprocess(self, vhdl_file):
        self.vhdl_file = vhdl_file
        file_path = vhdl_file.file_path
        buf = open(file_path, "r").read()
        return self._preporcess_file(file_content = buf, file_name = file_path, library = vhdl_file.library)
        

class VHDLParser(DepParser):
    
    def __init__(self, dep_file):
        DepParser.__init__(self, dep_file)
        self.preprocessor = VHDLPreprocessor()
    

    def parse(self, dep_file):
        from dep_file import DepRelation
        if dep_file.is_parsed:
            return
        logging.info("Parsing %s" % dep_file.path)
        
        buf = self.preprocessor.preprocess(dep_file)
        
        #use packages
        use_pattern = re.compile("^\s*use\s+(\w+)\s*\.\s*(\w+)", re.DOTALL | re.MULTILINE | re.IGNORECASE )
        def do_use(s) :
            if ( s.group(1).lower() == "work" ) : #work is the current library in VHDL
                logging.debug("use package %s.%s" % (dep_file.library, s.group(2) ) )
                dep_file.add_relation(DepRelation("%s.%s" % (dep_file.library, s.group(2).lower() ) , DepRelation.USE, DepRelation.PACKAGE)) 
            else :
                logging.debug("use package %s.%s" % (s.group(1), s.group(2)) )
                dep_file.add_relation(DepRelation("%s.%s" % (s.group(1).lower(), s.group(2).lower()), DepRelation.USE, DepRelation.PACKAGE))
        re.subn(use_pattern, do_use, buf)

        #new entity
        entity_pattern = re.compile("^\s*entity\s+(\w+)\s+is\s+(?:port|generic|end)", re.DOTALL | re.MULTILINE | re.IGNORECASE )
        def do_entity(s) :
            logging.debug("found entity %s.%s" % ( dep_file.library, s.group(1) ) )
            dep_file.add_relation(DepRelation("%s.%s" % (dep_file.library, s.group(1).lower()),
                                              DepRelation.PROVIDE,
                                              DepRelation.ENTITY))
        re.subn(entity_pattern, do_entity, buf)
        
        #new package
        package_pattern = re.compile("^\s*package\s+(\w+)\s+is",  re.DOTALL | re.MULTILINE | re.IGNORECASE )
        def do_package(s) :
            logging.debug("found package %s.%s" % (dep_file.library, s.group(1) ))
            dep_file.add_relation(DepRelation("%s.%s" % (dep_file.library, s.group(1).lower()),
                                              DepRelation.PROVIDE,
                                              DepRelation.PACKAGE))
        re.subn(package_pattern, do_package, buf)
        
        #intantions
        instance_pattern = re.compile("^\s*(\w+)\s*\:\s*(\w+)\s*(?:port\s+map|generic\s+map|\s*;)", re.DOTALL | re.MULTILINE | re.IGNORECASE )
        instance_from_library_pattern = re.compile("^\s*(\w+)\s*\:\s*entity\s*(\w+)\s*\.\s*(\w+)\s*(?:port\s+map|generic\s+map|\s*;)",  re.DOTALL | re.MULTILINE | re.IGNORECASE )
        libraries = set([dep_file.library])
        def do_instance(s) :
            for lib in libraries :
                logging.debug("-> instantiates %s.%s as %s" % (lib, s.group(2), s.group(1))  )
                dep_file.add_relation(DepRelation("%s.%s" % (lib, s.group(2).lower()),
                                                  DepRelation.USE,
                                                  DepRelation.ENTITY))
        def do_instance_from_library(s) :
            if ( s.group(2).lower() == "work" ) : #work is the current library in VHDL
                logging.debug("-> instantiates %s.%s as %s" % (dep_file.library, s.group(3), s.group(1))  )
                dep_file.add_relation(DepRelation("%s.%s" % (dep_file.library, s.group(3).lower()),
                                                  DepRelation.USE,
                                                  DepRelation.ENTITY))
            else :
                logging.debug("-> instantiates %s.%s as %s" % (s.group(2), s.group(3), s.group(1))  )
                dep_file.add_relation(DepRelation("%s.%s" % (s.group(2).lower(), s.group(3).lower()),
                                                  DepRelation.USE,
                                                  DepRelation.ENTITY))
        re.subn(instance_pattern, do_instance, buf)
        re.subn(instance_from_library_pattern, do_instance_from_library, buf)
        
        #libraries
        library_pattern = re.compile("^\s*library\s*(\w+)\s*;",  re.DOTALL | re.MULTILINE | re.IGNORECASE )
        def do_library(s) :
            logging.debug("use library %s" % s.group(1))
            libraries.add(s.group(1).lower())
        re.subn(library_pattern, do_library, buf)
        dep_file.is_parsed = True
