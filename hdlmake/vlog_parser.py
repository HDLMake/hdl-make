#!/usr/bin/python
#
# Copyright (c) 2013 CERN
# Author: Tomasz Wlostowski
#         Adrian Fiergolski
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
#

# A Verilog preprocessor. Still lots of stuff to be done,
# but it's already quite useful for calculating dependencies.

"""This module provides the Verilog parser for HDLMake"""

from __future__ import print_function
from __future__ import absolute_import
import os
import re
import sys
import logging

from .new_dep_solver import DepParser
from .dep_file import DepRelation
from hdlmake.srcfile import create_source_file
import six


class VerilogPreprocessor(object):

    """This class provides the Verilog Preprocessor"""

    # Reserved verilog preprocessor keywords. The list is certainly not full
    vpp_keywords = [
        "define",
        "line",
        "include",
        "elsif",
        "ifdef",
        "endif",
        "else",
        "undef",
        "timescale"]

    class VLDefine(object):

        """Class that provides a container for Verilog Defines"""

        def __init__(self, name, args, expansion):
            self.name = name
            self.args = args
            self.expansion = expansion

    class VLStack(object):

        """Class that provides a simple binary (true/false) stack
        for Verilog Defines for nested `ifdefs evaluation"""

        def __init__(self):
            self.stack = []

        def push(self, v_element):
            """Push element to the stack"""
            self.stack.append(v_element)

        def pop(self):
            "Pop element from the stack"""
            return self.stack.pop()

        def all_true(self):
            """Returns true if the stack is empty or all the contained
            elements are True"""
            return len(self.stack) == 0 or all(self.stack)

        def flip(self):
            """Toggle the following element"""
            self.push(not self.pop())

    def __init__(self):
        self.vpp_stack = self.VLStack()
        self.vlog_file = None
        # List of `include search paths
        self.vpp_searchdir = ["."]
        # List of macro definitions
        self.vpp_macros = []
        # Dictionary of files sub-included by each file parsed
        self.vpp_filedeps = {}

    def _find_macro(self, name):
        """Get the Verilog preprocessor macro named 'name'"""
        for macro_aux in self.vpp_macros:
            if macro_aux.name == name:
                return macro_aux
        return None

    def _search_include(self, filename, parent_dir=None):
        """Look for the 'filename' Verilog include file in the
        provided 'parent_dir'. If the directory is not provided, the method
        will search for the Verilog include in every defined Verilog
        preprocessor search directory"""
        if parent_dir is not None:
            possible_file = os.path.join(parent_dir, filename)
            if os.path.isfile(possible_file):
                return os.path.abspath(possible_file)
        for searchdir in self.vlog_file.include_dirs:
            probable_file = os.path.join(searchdir, filename)
            if os.path.isfile(probable_file):
                return os.path.abspath(probable_file)
        logging.error("Can't find %s for %s in any of the include "
                      "directories: %s", filename, self.vlog_file.file_path,
                      ', '.join(self.vlog_file.include_dirs))
        sys.exit("\nExiting")

    def _parse_macro_def(self, macro):
        """Parse the provided 'macro' and, if it's not a reserved keyword,
        create a new VLDefine instance and add it to the Verilog preprocessor
        list of macros"""
        name = macro.group(1)
        expansion = macro.group(3)
        if macro.group(2):
            params = macro.group(2).split(",")
        else:
            params = []
        if name in self.vpp_keywords:
            logging.error("Attempt to `define a reserved preprocessor keyword")
            quit()
        mdef = self.VLDefine(name, params, expansion)
        self.vpp_macros.append(mdef)
        return mdef

    def _preprocess_file(self, file_content, file_name, library):
        """Preprocess the content of the Verilog file"""
        def _remove_comment(text):
            """Function that removes the comments from the Verilog code"""
            def replacer(match):
                """Funtion that replace the matching comments"""
                text = match.group(0)
                if text.startswith('/'):
                    return ""
                else:
                    return text
            pattern = re.compile(
                r'//.*?$|/\*.*?\*/|"(?:\\.|[^\\"])*"',
                re.DOTALL | re.MULTILINE)
            return re.sub(pattern, replacer, text)

        def _degapize(text):
            """ Create a list in which the verilog sentences are
            stored in an ordered way -- and without empty 'gaps'"""
            lempty = re.compile(r"^\s*$")
            cline = None
            lines = []
            for line_aux in text.splitlines(False):
                if re.match(lempty, line_aux) is not None:
                    continue
                if line_aux.endswith('\\'):
                    if cline is None:
                        cline = ""
                    cline += line_aux[:len(line_aux) - 1]
                    continue
                elif cline:
                    line_aux = cline + line_aux
                    cline = None
                else:
                    cline = None
                lines.append(line_aux)
            return lines
        exps = {"include": re.compile(r"^\s*`include\s+\"(.+)\""),
                "define":
                re.compile(r"^\s*`define\s+(\w+)(?:\(([\w\s,]*)\))?(.*)"),
                "ifdef_elsif":
                re.compile(r"^\s*`(ifdef|ifndef|elsif)\s+(\w+)\s*$"),
                "endif_else": re.compile(r"^\s*`(endif|else)\s*$"),
                "begin_protected":
                re.compile(r"^\s*`pragma\s*protect\s*begin_protected\s*$"),
                "end_protected":
                re.compile(r"^\s*`pragma\s*protect\s*end_protected\s*$")}
        vl_macro_expand = re.compile(r"`(\w+)(?:\(([\w\s,]*)\))?")
        # init dependencies
        self.vpp_filedeps[file_name + library] = []
        cur_iter = 0
        logging.debug("preprocess file %s (of length %d) in library %s",
                      file_name, len(file_content), library)
        buf = _remove_comment(file_content)
        protected_region = False
        while True:
            new_buf = ""
            n_expansions = 0
            cur_iter += 1
            if cur_iter > 30:
                raise Exception("Recursion level exceeded. Nested `includes?")
            for line in _degapize(buf):
                matches = {}
                last = None
                for statement, stmt_regex in six.iteritems(exps):
                    matches[statement] = re.match(stmt_regex, line)
                    if matches[statement]:
                        last = matches[statement]
                if matches["begin_protected"]:
                    protected_region = True
                    continue
                if matches["end_protected"]:
                    protected_region = False
                    continue
                if protected_region:
                    continue
                if matches["ifdef_elsif"]:
                    cond_true = self._find_macro(last.group(2)) is not None
                    if last.group(1) == "ifndef":
                        cond_true = not cond_true
                    elif last.group(1) == "elsif":
                        self.vpp_stack.pop()
                    self.vpp_stack.push(cond_true)
                    continue
                elif matches["endif_else"]:
                    if last.group(1) == "endif":
                        self.vpp_stack.pop()
                    else:  # `else
                        self.vpp_stack.flip()
                    continue
                if not self.vpp_stack.all_true():
                    continue
                if matches["include"]:
                    included_file_path = self._search_include(
                        last.group(1), os.path.dirname(file_name))
                    logging.debug("File being parsed %s (library %s) "
                                  "includes %s",
                                  file_name, library, included_file_path)
                    line = self._preprocess_file(
                        file_content=open(included_file_path, "r").read(),
                        file_name=included_file_path, library=library)
                    self.vpp_filedeps[
                        file_name +
                        library].append(
                        included_file_path)
                    # add the whole include chain to the dependencies of the
                    # currently parsed file
                    self.vpp_filedeps[file_name + library].extend(
                        self.vpp_filedeps[included_file_path + library])
                    new_buf += line + '\n'
                    n_expansions += 1
                    continue
                elif matches["define"]:
                    self._parse_macro_def(matches["define"])

                def do_expand(what):
                    """Function to be applied by re.sub to every match of the
                    vl_macro_expand in the Verilof code -- group() returns
                    positive matches as indexed plain strings."""
                    if what.group(1) in self.vpp_keywords:
                        return '`' + what.group(1)
                    macro = self._find_macro(what.group(1))
                    if macro:
                        return macro.expansion
                    else:
                        logging.error("No expansion for macro '`%s' (%s) (%s)",
                                      what.group(1), line[:50]
                                      if len(line) > 50 else line, file_name)
                repl_line = re.sub(vl_macro_expand, do_expand, line)
                new_buf += repl_line + '\n'
                # if there was any expansion, then keep on iterating
                if repl_line != line:
                    n_expansions += 1
            buf = new_buf
            if n_expansions == 0:
                return new_buf

    def _define(self, name, expansion):
        """Define a new expansion Verilog macro and add it to the macro
        collection"""
        mdef = self.VLDefine(name, [], expansion)
        self.vpp_macros.append(mdef)

    def add_path(self, path):
        """Add a new path to the search directory list so that HDLMake
        will search for found includes on it"""
        self.vpp_searchdir.append(path)

    def preprocess(self, vlog_file):
        """Assign the provided 'vlog_file' to the associated class property
        and then preprocess and return the Verilog code"""
        # assert isinstance(vlog_file, VerilogFile)
        # assert isinstance(vlog_file, DepFile)
        self.vlog_file = vlog_file
        file_path = vlog_file.file_path
        buf = open(file_path, "r").read()
        return self._preprocess_file(file_content=buf,
                                     file_name=file_path,
                                     library=vlog_file.library)

    def get_file_deps(self):
        """Look for all of the defined preprocessor filedeps and return a list
        containing all of them"""
        deps = []
        for filedep_key in six.iterkeys(self.vpp_filedeps):
            for filedep in self.vpp_filedeps[filedep_key]:
                deps.append(filedep)
        return list(set(deps))


class VerilogParser(DepParser):

    """Class providing the Verilog Parser functionality"""

    reserved_words = ["accept_on",
                      "alias",
                      "always",
                      "always_comb",
                      "always_ff",
                      "always_latch",
                      "assert",
                      "assign",
                      "assume",
                      "automatic",
                      "before",
                      "begin",
                      "bind",
                      "bins",
                      "binsof",
                      "bit",
                      "break",
                      "buf",
                      "bufif0",
                      "bufif1",
                      "byte",
                      "case",
                      "casex",
                      "casez",
                      "cell",
                      "chandle",
                      "checker",
                      "class",
                      "clocking",
                      "cmos",
                      "config",
                      "const",
                      "constraint",
                      "context",
                      "continue",
                      "cover",
                      "covergroup",
                      "coverpoint",
                      "cross",
                      "deassign",
                      "default",
                      "defparam",
                      "disable",
                      "dist",
                      "do",
                      "edge",
                      "else",
                      "end",
                      "endcase",
                      "endchecker",
                      "endclass",
                      "endclocking",
                      "endconfig",
                      "endfunction",
                      "endgenerate",
                      "endgroup",
                      "endinterface",
                      "endmodule",
                      "endpackage",
                      "endprimitive",
                      "endprogram",
                      "endproperty",
                      "endsequence",
                      "endspecify",
                      "endtable",
                      "endtask",
                      "enum",
                      "event",
                      "eventually",
                      "expect",
                      "export",
                      "extends",
                      "extern",
                      "final",
                      "first_match",
                      "for",
                      "force",
                      "foreach",
                      "forever",
                      "fork",
                      "forkjoin",
                      "function",
                      "generate",
                      "genvar",
                      "global",
                      "highz0",
                      "highz1",
                      "if",
                      "iff",
                      "ifnone",
                      "ignore_bins",
                      "illegal_bins",
                      "implies",
                      "import",
                      "incdir",
                      "include",
                      "initial",
                      "inout",
                      "input",
                      "inside",
                      "instance",
                      "int",
                      "integer",
                      "interface",
                      "intersect",
                      "join",
                      "join_any",
                      "join_none",
                      "large",
                      "let",
                      "liblist",
                      "library",
                      "local",
                      "localparam",
                      "logic",
                      "longint",
                      "macromodule",
                      "matches",
                      "medium",
                      "modport",
                      "module",
                      "nand",
                      "negedge",
                      "new",
                      "nexttime",
                      "nmos",
                      "nor",
                      "noshowcancelled",
                      "not",
                      "notif0",
                      "notif1",
                      "null",
                      "or",
                      "output",
                      "package",
                      "packed",
                      "parameter",
                      "pmos",
                      "posedge",
                      "primitive",
                      "priority",
                      "program",
                      "property",
                      "protected",
                      "pull0",
                      "pull1",
                      "pulldown",
                      "pullup",
                      "pulsestyle_ondetect",
                      "pulsestyle_onevent",
                      "pure",
                      "rand",
                      "randc",
                      "randcase",
                      "randsequence",
                      "rcmos",
                      "real",
                      "realtime",
                      "ref",
                      "reg",
                      "reject_on",
                      "release",
                      "repeat",
                      "restrict",
                      "return",
                      "rnmos",
                      "rpmos",
                      "rtran",
                      "rtranif0",
                      "rtranif1",
                      "s_always",
                      "scalared",
                      "sequence",
                      "s_eventually",
                      "shortint",
                      "shortreal",
                      "showcancelled",
                      "signed",
                      "small",
                      "s_nexttime",
                      "solve",
                      "specify",
                      "specparam",
                      "static",
                      "string",
                      "strong",
                      "strong0",
                      "strong1",
                      "struct",
                      "s_until",
                      "super",
                      "supply0",
                      "supply1",
                      "sync_accept_on",
                      "sync_reject_on",
                      "table",
                      "tagged",
                      "task",
                      "this",
                      "throughout",
                      "time",
                      "timeprecision",
                      "timeunit",
                      "tran",
                      "tranif0",
                      "tranif1",
                      "tri",
                      "tri0",
                      "tri1",
                      "triand",
                      "trior",
                      "trireg",
                      "type",
                      "typedef",
                      "union",
                      "unique",
                      "unique0",
                      "unsigned",
                      "until",
                      "until_with",
                      "untypted",
                      "use",
                      "var",
                      "vectored",
                      "virtual",
                      "void",
                      "wait",
                      "wait_order",
                      "wand",
                      "weak",
                      "weak0",
                      "weak1",
                      "while",
                      "wildcard",
                      "wire",
                      "with",
                      "within",
                      "wor",
                      "xnor",
                      "xor"]

    def __init__(self, dep_file):
        DepParser.__init__(self, dep_file)
        self.preprocessor = VerilogPreprocessor()
        self.preprocessed = False

    def add_search_path(self, path):
        """Add a new candidate path to the Verilog preprocessor list
        containing the include dir candidates"""
        self.preprocessor.add_path(path)

    def parse(self, dep_file):
        """Parse the provided Verilog file and add to its properties
        all of the detected dependency relations"""
        if dep_file.is_parsed:
            return
        logging.debug("Parsing %s", dep_file.path)
        # assert isinstance(dep_file, DepFile), print("unexpected type: " +
        # str(type(dep_file)))
        buf = self.preprocessor.preprocess(dep_file)
        self.preprocessed = buf[:]
        # add includes as dependencies
        try:
            includes = self.preprocessor.vpp_filedeps[
                dep_file.path + dep_file.library]
            for file_aux in includes:
                dep_file.depends_on.add(
                    create_source_file(path=file_aux,
                                       module=dep_file.module))
            logging.debug("%s has %d includes.",
                          str(dep_file), len(includes))
        except KeyError:
            logging.debug(str(dep_file) + " has no includes.")
        # look for packages used inside in file
        # it may generate false dependencies as package in SV can be used by:
        #    import my_package::*;
        # or directly
        #    logic var = my_package::MY_CONST;
        # The same way constants and others can be imported directly from
        # other modules:
        #    logic var = my_other_module::MY_CONST;
        # and HdlMake will anyway create dependency marking my_other_module as
        # requested package
        import_pattern = re.compile(r"(\w+) *::(\w+|\\*)")

        def do_imports(text):
            """Function to be applied by re.subn to every match of the
            import_pattern in the Verilog code -- group() returns positive
            matches as indexed plain strings. It adds the found USE
            relations to the file"""
            logging.debug("file %s imports/uses %s.%s package",
                          dep_file.path, dep_file.library, text.group(1))
            dep_file.add_relation(
                DepRelation("%s.%s" % (dep_file.library, text.group(1)),
                            DepRelation.USE, DepRelation.PACKAGE))
        re.subn(import_pattern, do_imports, buf)
        # packages
        m_inside_package = re.compile(
            r"package\s+(\w+)\s*(?:\(.*?\))?\s*(.+?)endpackage",
            re.DOTALL | re.MULTILINE)

        def do_package(text):
            """Function to be applied by re.subn to every match of the
            m_inside_pattern in the Verilog code -- group() returns positive
            matches as indexed plain strings. It adds the found PROVIDE
            relations to the file"""
            logging.debug("found pacakge %s.%s", dep_file.library,
                          text.group(1))
            dep_file.add_relation(
                DepRelation("%s.%s" % (dep_file.library, text.group(1)),
                            DepRelation.PROVIDE, DepRelation.PACKAGE))
        re.subn(m_inside_package, do_package, buf)
        # modules and instatniations
        m_inside_module = re.compile(
            r"(?:module|interface)\s+(\w+)\s*(?:\(.*?\))?\s*(.+?)"
            r"(?:endmodule|endinterface)",
            re.DOTALL | re.MULTILINE)
        m_instantiation = re.compile(
            r"(?:\A|\s*)\s*(\w+)\s+(?:#\s*\(.*?\)\s*)?(\w+)\s*\(.*?\)\s*",
            re.DOTALL | re.MULTILINE)

        def do_module(text):
            """Function to be applied by re.sub to every match of the
            m_inside_module in the Verilog code -- group() returns
            positive  matches as indexed plain strings. It adds the found
            PROVIDE relations to the file"""
            logging.debug("found module %s.%s", dep_file.library,
                          text.group(1))
            dep_file.add_relation(
                DepRelation("%s.%s" % (dep_file.library, text.group(1)),
                            DepRelation.PROVIDE, DepRelation.MODULE))

            def do_inst(text):
                """Function to be applied by re.sub to every match of the
                m_instantiation in the Verilog code -- group() returns positive
                matches as indexed plain strings. It adds the found USE
                relations to the file"""
                mod_name = text.group(1)
                if mod_name in self.reserved_words:
                    return
                logging.debug("-> instantiates %s.%s as %s",
                              dep_file.library, text.group(1), text.group(2))
                dep_file.add_relation(
                    DepRelation("%s.%s" % (dep_file.library, text.group(1)),
                                DepRelation.USE, DepRelation.MODULE))
            re.subn(m_instantiation, do_inst, text.group(2))
        re.subn(m_inside_module, do_module, buf)
        dep_file.add_relation(
            DepRelation(
                dep_file.path,
                DepRelation.PROVIDE,
                DepRelation.INCLUDE))
        dep_file.is_parsed = True
