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

import logging
import re

from .new_dep_solver import DepParser


class VHDLPreprocessor(object):

    def __init__(self):
        self.vhdl_file = None

    def remove_comments_and_strings(self, s):
        pattern = re.compile( '--.*?$|".?"', re.DOTALL | re.MULTILINE )  
        return re.sub(pattern,"", s)
    
    def _preprocess_file(self, file_content, file_name, library):
        logging.debug("preprocess file %s (of length %d) in library %s" % (file_name, len(file_content), library) )
        return self.remove_comments_and_strings(file_content)
        
    def preprocess(self, vhdl_file):
        self.vhdl_file = vhdl_file
        file_path = vhdl_file.file_path
        buf = open(file_path, "r").read()
        return self._preprocess_file(file_content = buf, file_name = file_path, library = vhdl_file.library)
        

class Architecture():
    def __init__(self):
        self.model = None;
        self.components = None;
        self.entities = None;
        self.instances = None;

class Package():
    def __init__(self):
        self.model = None;
        self.components = None;

class VHDLParser(DepParser):
    
    def __init__(self, dep_file):
        DepParser.__init__(self, dep_file)
        self.preprocessor = VHDLPreprocessor()
    

    def parse(self, dep_file):
        from .dep_file import DepRelation
        if dep_file.is_parsed:
            return
        logging.info("Parsing %s" % dep_file.path)

        # Preprocess file        
        buf = self.preprocessor.preprocess(dep_file)
        
        #use packages
        use_pattern = re.compile("^\s*use\s+(\w+)\s*\.\s*(\w+)", re.DOTALL | re.MULTILINE | re.IGNORECASE )
        def do_use(s) :
            if ( s.group(1).lower() == "work" ) : #work is the current library in VHDL
                logging.debug("use package %s.%s" % (dep_file.library, s.group(2) ) )
                dep_file.add_relation(DepRelation("%s.%s" % (dep_file.library, s.group(2) ) , DepRelation.USE, DepRelation.PACKAGE)) 
            else :
                logging.debug("use package %s.%s" % (s.group(1), s.group(2)) )
                dep_file.add_relation(DepRelation("%s.%s" % (s.group(1), s.group(2)), DepRelation.USE, DepRelation.PACKAGE))
            return "<hdlmake use_pattern %s.%s>" % (s.group(1), s.group(2))
        use_packages = use_pattern.findall(buf)
        print('use package:\n %s' % use_packages)
        dep_file.used_packages = use_packages
        buf = re.sub(use_pattern, do_use, buf)

        # Provide entity
        entity_pattern = re.compile("^\s*entity\s+(?P<name>\w+)\s+is\s+(?:port|generic|end).*?(?P=name)\s*;", re.DOTALL | re.MULTILINE | re.IGNORECASE )
        provided_entities = entity_pattern.findall(buf)
        print('provide entities:\n %s' % provided_entities)
        dep_file.provided_entities = provided_entities

        # Provide architecture
        architecture_pattern = re.compile("^\s*architecture\s+(\w+)\s+of\s+(\w+)\s+is", re.DOTALL | re.MULTILINE | re.IGNORECASE )
        provided_architectures = architecture_pattern.findall(buf)
        print('provide architectures:\n %s' % provided_architectures)
        for architecture in provided_architectures:
            architecture_aux = Architecture();
            architecture_aux.model = architecture
            print('- architecture: %s(%s)' % (architecture[1], architecture[0])) 
            architecture_inner_pattern = re.compile("architecture\s+%s\s+of\s+%s\s+is(.*)end\s+%s" % (architecture[0], architecture[1], architecture[0]), re.DOTALL | re.MULTILINE | re.IGNORECASE )
            architecture_inner_content = architecture_inner_pattern.findall(buf)
            #print(architecture_inner_content)
            component_pattern = re.compile("^\s*component\s+(\w+).*?end\s+component.*?;", re.DOTALL | re.MULTILINE | re.IGNORECASE )
            print("Architecture dependencies:")
            print("content length: %s" % len(architecture_inner_content))
            if len(architecture_inner_content) == 1:
                architecture_aux.components = component_pattern.findall(architecture_inner_content[0])
                instances_pattern = re.compile("^\s*(\w+)\s*\:\s*(\w+)\s*(?:port\s+map.*?;|generic\s+map.*?;|\s*;)", re.DOTALL | re.MULTILINE | re.IGNORECASE )
                instance_from_library_pattern = re.compile("^\s*(\w+)\s*\:\s*entity\s*(\w+)\s*\.\s*(\w+)\s*(?:port\s+map.*?;|generic\s+map.*?;|\s*;)",  re.DOTALL | re.MULTILINE | re.IGNORECASE )
                architecture_aux.entities = instances_pattern.findall(architecture_inner_content[0])
                architecture_aux.instances = instance_from_library_pattern.findall(architecture_inner_content[0])
            dep_file.provided_architectures.append(architecture_aux)
            instance_from_library_pattern = re.compile("^\s*(\w+)\s*\:\s*entity\s*(\w+)\s*\.\s*(\w+)\s*(?:port\s+map.*?;|generic\s+map.*?;|\s*;)",  re.DOTALL | re.MULTILINE | re.IGNORECASE )
            print("**********************************************************************************")
            print(instance_from_library_pattern.findall(buf))
            print("**********************************************************************************")

        #new package
        package_pattern = re.compile("^\s*package\s+(\w+)\s+is",  re.DOTALL | re.MULTILINE | re.IGNORECASE )
        #def do_package(s) :
        #    logging.debug("found package %s.%s" % (dep_file.library, s.group(1) ))
        #    dep_file.add_relation(DepRelation("%s.%s" % (dep_file.library, s.group(1)),
        #                                      DepRelation.PROVIDE,
        #                                      DepRelation.PACKAGE))
        #    return "<hdlmake package %s.%s>" % (dep_file.library, s.group(1))
        #buf = re.sub(package_pattern, do_package, buf)
        provided_packages = package_pattern.findall(buf)
        print("Provided packages dependencies:")
        print(provided_packages)
        for package in provided_packages:
            package_aux = Package();
            package_aux.model = package
            package_inner_pattern = re.compile("package\s+%s\s+is(.*)end\s+%s.*?;" % (package, package), re.DOTALL | re.MULTILINE | re.IGNORECASE )
            package_inner_content = package_inner_pattern.findall(buf)
            print("******************* Package inner content ********************************")
            print(package_inner_content)
            component_pattern = re.compile("^\s*component\s+(\w+).*?end\s+component.*?;", re.DOTALL | re.MULTILINE | re.IGNORECASE )
            if len(package_inner_content) == 1:
                package_aux.components = component_pattern.findall(package_inner_content[0])
                print(package_aux.components)
            dep_file.provided_packages.append(package_aux)



        #component declaration
        component_pattern = re.compile("^\s*component\s+(\w+).*?end\s+component.*?;", re.DOTALL | re.MULTILINE | re.IGNORECASE )
        def do_component(s):
            logging.debug("found component declaration %s" % s.group(1))
            return "<hdlmake component %s>" % s.group(1)
        buf = re.sub(component_pattern, do_component, buf)

        #record declaration
        record_pattern = re.compile("^\s*type\s+(\w+)\s+is\s+record.*?end\s+record.*?;", re.DOTALL | re.MULTILINE | re.IGNORECASE )
        def do_record(s):
            logging.debug("found record declaration %s" % s.group(1))
            return "<hdlmake record %s>" % s.group(1)
        buf = re.sub(record_pattern, do_record, buf)

        #function declaration
        function_pattern = re.compile("^\s*function\s+(\w+).*?return.*?(?:is|;)", re.DOTALL | re.MULTILINE | re.IGNORECASE )
        def do_function(s):
            logging.debug("found function declaration %s" % s.group(1))
            return "<hdlmake function %s>" % s.group(1)
        buf = re.sub(function_pattern, do_function, buf)
        
        #intantions
        instance_pattern = re.compile("^\s*(\w+)\s*\:\s*(\w+)\s*(?:port\s+map.*?;|generic\s+map.*?;|\s*;)", re.DOTALL | re.MULTILINE | re.IGNORECASE )
        instance_from_library_pattern = re.compile("^\s*(\w+)\s*\:\s*entity\s*(\w+)\s*\.\s*(\w+)\s*(?:port\s+map.*?;|generic\s+map.*?;|\s*;)",  re.DOTALL | re.MULTILINE | re.IGNORECASE )
        libraries = set([dep_file.library])
        def do_instance(s) :
            for lib in libraries :
                logging.debug("-> instantiates %s.%s as %s" % (lib, s.group(2), s.group(1))  )
                dep_file.add_relation(DepRelation("%s.%s" % (lib, s.group(2)),
                                                  DepRelation.USE,
                                                  DepRelation.ARCHITECTURE))
            return "<hdlmake instance %s|%s>" % (s.group(1), s.group(2))
        def do_instance_from_library(s) :
            if ( s.group(2).lower() == "work" ) : #work is the current library in VHDL
                logging.debug("-> instantiates %s.%s as %s" % (dep_file.library, s.group(3), s.group(1))  )
                dep_file.add_relation(DepRelation("%s.%s" % (dep_file.library, s.group(3)),
                                                  DepRelation.USE,
                                                  DepRelation.ARCHITECTURE))
            else :
                logging.debug("-> instantiates %s.%s as %s" % (s.group(2), s.group(3), s.group(1))  )
                dep_file.add_relation(DepRelation("%s.%s" % (s.group(2), s.group(3)),
                                                  DepRelation.USE,
                                                  DepRelation.ARCHITECTURE))
                
            return "<hdlmake instance_from_library %s|%s>" % (s.group(1), s.group(3))
        buf = re.sub(instance_pattern, do_instance, buf)
        buf = re.sub(instance_from_library_pattern, do_instance_from_library, buf)
        
        #libraries
        library_pattern = re.compile("^\s*library\s*(\w+)\s*;",  re.DOTALL | re.MULTILINE | re.IGNORECASE )
        def do_library(s) :
            logging.debug("use library %s" % s.group(1))
            libraries.add(s.group(1))
            return "<hdlmake library %s>" % s.group(1)
        
        buf = re.sub(library_pattern, do_library, buf)
        #logging.debug("\n" + buf) # print modified buffer.
        dep_file.is_parsed = True
