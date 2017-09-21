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

"""Module providing the VHDL parser capabilities"""

from __future__ import absolute_import
import logging
import re

from .new_dep_solver import DepParser


class VHDLParser(DepParser):

    """Class providing the container for VHDL parser instances"""

    def __init__(self, dep_file):
        DepParser.__init__(self, dep_file)
        # self.preprocessor = VHDLPreprocessor()

    def parse(self, dep_file):
        """Parse the provided VHDL file and add the detected relations to it"""
        from .dep_file import DepRelation
        if dep_file.is_parsed:
            return
        logging.debug("Parsing %s", dep_file.path)

        def _preprocess(vhdl_file):
            """Preprocess the supplied VHDL file instance"""
            def _preprocess_file(file_content, file_name, library):
                """Preprocess the suplied string using the arguments"""
                def _remove_comments_and_strings(text):
                    """Remove the comments and strings from the VHDL code"""
                    pattern = re.compile('--.*?$|".?"',
                                         re.DOTALL | re.MULTILINE)
                    return re.sub(pattern, "", text)
                logging.debug(
                    "preprocess file %s (of length %d) in library %s",
                    file_name, len(file_content), library)
                return _remove_comments_and_strings(file_content)
            file_path = vhdl_file.file_path
            buf = open(file_path, "r").read()
            return _preprocess_file(file_content=buf,
                                    file_name=file_path,
                                    library=vhdl_file.library)
        buf = _preprocess(dep_file)
        # use packages
        use_pattern = re.compile(
            r"^\s*use\s+(\w+)\s*\.\s*(\w+)",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_use(text):
            """Function to be applied by re.sub to every match of the
            use_pattern in the VHDL code -- group() returns positive matches
            as indexed plain strings. It adds the found USE relations to the
            file"""
            if text.group(1).lower() == "work":
                logging.debug("use package %s.%s",
                              dep_file.library, text.group(2))
                dep_file.add_relation(
                    DepRelation("%s.%s" % (dep_file.library, text.group(2)),
                                DepRelation.USE,
                                DepRelation.PACKAGE))
            else:
                logging.debug("use package %s.%s",
                              text.group(1), text.group(2))
                dep_file.add_relation(
                    DepRelation("%s.%s" % (text.group(1), text.group(2)),
                                DepRelation.USE,
                                DepRelation.PACKAGE))
            return "<hdlmake use_pattern %s.%s>" % (text.group(1),
                                                    text.group(2))
        buf = re.sub(use_pattern, do_use, buf)
        # new entity
        entity_pattern = re.compile(
            r"^\s*entity\s+(?P<name>\w+)\s+is\s+(?:port|generic|end)"
            r".*?((?P=name)|entity)\s*;",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)
        def do_entity(text):
            """Function to be applied by re.sub to every match of the
            entity_pattern in the VHDL code -- group() returns positive matches
            as indexed plain strings. It adds the found PROVIDE relations
            to the file"""
            logging.debug("found entity %s.%s",
                          dep_file.library, text.group(1))
            dep_file.add_relation(
                DepRelation("%s.%s" % (dep_file.library, text.group(1)),
                            DepRelation.PROVIDE,
                            DepRelation.ENTITY))
            dep_file.add_relation(
                DepRelation("%s.%s" % (dep_file.library, text.group(1)),
                            DepRelation.USE,
                            DepRelation.ARCHITECTURE))
            return "<hdlmake entity_pattern %s.%s>" % (dep_file.library,
                                                       text.group(1))

        buf = re.sub(entity_pattern, do_entity, buf)

        # new architecture
        architecture_pattern = re.compile(
            r"^\s*architecture\s+(?P<name>\w+)\s+of\s+(\w+)\s+is"
            r".*end\s*((|architecture)\s*(?P=name)|architecture)\s*;",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)
        architecture_split_pattern = re.compile(
            r"^\s*architecture\s+(?P<name>\w+)\s+of\s+(\w+)\s+is",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_architecture(text):
            """Function to be applied by re.sub to every match of the
            architecture_pattern in the VHDL code -- group() returns positive
            matches as indexed plain strings. It adds the found PROVIDE
            relations to the file"""
            logging.debug("found architecture %s of entity %s.%s",
                          text.group(1), dep_file.library, text.group(2))
            dep_file.add_relation(
                DepRelation("%s.%s" % (dep_file.library, text.group(2)),
                            DepRelation.PROVIDE,
                            DepRelation.ARCHITECTURE))
            return "<hdlmake architecture %s.%s>" % (dep_file.library,
                                                     text.group(2))
        buf = re.sub(architecture_split_pattern, do_architecture, buf)

        # new package
        package_pattern = re.compile(
            r"^\s*package\s+(\w+)\s+is",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_package(text):
            """Function to be applied by re.sub to every match of the
            package_pattern in the VHDL code -- group() returns positive
            matches as indexed plain strings. It adds the found PROVIDE
            relations to the file"""
            logging.debug("found package %s.%s", dep_file.library,
                          text.group(1))
            dep_file.add_relation(
                DepRelation("%s.%s" % (dep_file.library, text.group(1)),
                            DepRelation.PROVIDE,
                            DepRelation.PACKAGE))
            return "<hdlmake package %s.%s>" % (dep_file.library,
                                                text.group(1))
        buf = re.sub(package_pattern, do_package, buf)

        # component declaration
        component_pattern = re.compile(
            r"^\s*component\s+(\w+).*?end\s+component.*?;",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_component(text):
            """Function to be applied by re.sub to every match of the
            component_pattern in the VHDL code -- group() returns positive
            matches as indexed plain strings. It doesn't add any relation
            to the file"""
            logging.debug("found component declaration %s", text.group(1))
            #dep_file.add_relation(
            #    DepRelation("%s.%s" % (dep_file.library, text.group(1)),
            #                DepRelation.USE,
            #                DepRelation.ENTITY))
            return "<hdlmake component %s>" % text.group(1)

        buf = re.sub(component_pattern, do_component, buf)

        # Signal declaration
        signal_pattern = re.compile(
            r"^\s*signal\s+(\w+).*?;",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_signal(text):
            """Function to be applied by re.sub to every match of the
            signal_pattern in the VHDL code -- group() returns positive
            matches as indexed plain strings. It doesn't add any relation
            to the file"""
            logging.debug("found signal declaration %s", text.group(1))
            return "<hdlmake signal %s>" % text.group(1)

        buf = re.sub(signal_pattern, do_signal, buf)

        # Constant declaration
        constant_pattern = re.compile(
            r"^\s*constant\s+(\w+).*?;",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_constant(text):
            """Function to be applied by re.sub to every match of the
            constant_pattern in the VHDL code -- group() returns positive
            matches as indexed plain strings. It doesn't add any relation
            to the file"""
            logging.debug("found constant declaration %s", text.group(1))
            return "<hdlmake constant %s>" % text.group(1)

        buf = re.sub(constant_pattern, do_constant, buf)


        # record declaration
        record_pattern = re.compile(
            r"^\s*type\s+(\w+)\s+is\s+record.*?end\s+record.*?;",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_record(text):
            """Function to be applied by re.sub to every match of the
            record_pattern in the VHDL code -- group() returns positive matches
            as indexed plain strings. It doesn't add any relation to the
            file"""
            logging.debug("found record declaration %s", text.group(1))
            return "<hdlmake record %s>" % text.group(1)

        buf = re.sub(record_pattern, do_record, buf)

        # function declaration
        function_pattern = re.compile(
            r"^\s*function\s+(?P<name>\w+)",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_function(text):
            """Function to be applied by re.sub to every match of the
            funtion_pattern in the VHDL code -- group() returns positive
            matches as indexed plain strings. It doesn't add the relations
            to the file"""
            logging.debug("found function declaration %s", text.group(1))
            return "<hdlmake function %s>" % text.group(1)

        buf = re.sub(function_pattern, do_function, buf)

        # instantions
        libraries = set([dep_file.library])
        instance_pattern = re.compile(
            r"^\s*(\w+)\s*:\s*(?:entity\s+\w+\.)?(\w+)\s*(?:port\s+map.*?|generic\s+map.*?)",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_instance(text):
            """Function to be applied by re.sub to every match of the
            instance_pattern in the VHDL code -- group() returns positive
            matches as indexed plain strings. It adds the found USE
            relations to the file"""
            for lib in libraries:
                logging.debug("-> instantiates %s.%s as %s",
                              lib, text.group(2), text.group(1))
                dep_file.add_relation(DepRelation(
                    "%s.%s" % (lib, text.group(2)),
                    DepRelation.USE, DepRelation.ENTITY))
            return "<hdlmake instance %s|%s>" % (text.group(1),
                                                 text.group(2))
        buf = re.sub(instance_pattern, do_instance, buf)

        instance_from_library_pattern = re.compile(
            r"^\s*(\w+)\s*\:\s*entity\s*(\w+)\s*\.\s*(\w+)\s*(?:port"
            r"\s+map.*?;|generic\s+map.*?;|\s*;)",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_instance_from_library(text):
            """Function to be applied by re.sub to every match of the
            instance_from_library_pattern in the VHDL code -- group()
            returns positive matches as indexed plain strings.
            It adds the found USE relations to the file"""
            if text.group(2).lower() == "work":
                logging.debug("-> instantiates %s.%s as %s",
                              dep_file.library, text.group(3), text.group(1))
                #dep_file.add_relation(
                #    DepRelation("%s.%s" % (dep_file.library, text.group(3)),
                #                DepRelation.USE,
                #                DepRelation.ARCHITECTURE))
            else:
                logging.debug("-> instantiates %s.%s as %s",
                              text.group(2), text.group(3), text.group(1))
                #dep_file.add_relation(
                #    DepRelation("%s.%s" % (text.group(2), text.group(3)),
                #                DepRelation.USE,
                #                DepRelation.ARCHITECTURE))
            return "<hdlmake instance_from_library %s|%s>" % (text.group(1),
                                                              text.group(3))
        buf = re.sub(instance_from_library_pattern,
                     do_instance_from_library, buf)
        # libraries
        library_pattern = re.compile(
            r"^\s*library\s*(\w+)\s*;",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_library(text):
            """Function to be applied by re.sub to every match of the
            library_pattern in the VHDL code -- group() returns positive
            matches as indexed plain strings. It adds the used libraries
            to the file's 'library' property"""
            logging.debug("use library %s", text.group(1))
            libraries.add(text.group(1))
            return "<hdlmake library %s>" % text.group(1)
        buf = re.sub(library_pattern, do_library, buf)
        # logging.debug("\n" + buf) # print modified buffer.
        dep_file.is_parsed = True
