#!/usr/bin/python
#
# Copyright (c) 2013 CERN
# Author: Tomasz Wlostowski
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

# A Verilog preprocessor. Still lots of stuff to be done, but it's already quite useful
# for calculating dependencies.

import logging
from new_dep_solver import DepRelation, DepFile


class VerilogPreprocessor:
# Reserved verilog preprocessor keywords. The list is certainly not full
    vpp_keywords = ["define", "line", "include", "elsif", "ifdef", "endif", "else", "undef", "timescale"]

# List of `include search paths
    vpp_searchdir = ["."]

# List of macro definitions
    vpp_macros = []

# Dictionary of files sub-included by each file parsed
    vpp_filedeps = {}

  # Verilog `define class
    class VL_Define:
        def __init__(self, name, args, expansion):
            self.name = name
            self.args = args
            self.expansion = expansion

    # Simple binary stack, for nested `ifdefs    evaluation
    class VL_Stack:
        def __init__(self):
            self.stack = []

        def push(self, v):
            self.stack.append(v)

        def pop(self):
            return self.stack.pop()

        def all_true(self):
            return (len(self.stack) == 0 or all(self.stack))

        def flip(self):
            self.push(not self.pop())

    def __init__(self):
        self.vpp_stack = self.VL_Stack()

    def _find_macro(self, name):
        for m in self.vpp_macros:
            if(m.name == name):
                return m
        return None

    def _remove_comment(self, s):
        def replacer(match):
            s = match.group(0)
            if s.startswith('/'):
                return ""
            else:
                return s
        import re
        pattern = re.compile('//.*?$|/\*.*?\*/|"(?:\\.|[^\\"])*"', re.DOTALL | re.MULTILINE)
        return re.sub(pattern, replacer, s)

    def _degapize(self, s):
        import re
        lempty = re.compile("^\s*$")
        cline = None
        lines = []
        for l in s.splitlines(False):
            if re.match(lempty, l) is not None:
                continue
            if l.endswith('\\'):
                if cline is None:
                    cline = ""
                cline += l[:len(l)-1]
                continue
            elif cline:
                l = cline+l
                cline = None
            else:
                cline = None
            lines.append(l)
        return lines

    def _search_include(self, filename, parent_dir=None):
        import os
#        print("Parent Dir %s" % parent_dir)
        if parent_dir is not None:
            possible_file = os.path.join(parent_dir, filename)
            if(os.path.isfile(possible_file)):
                return possible_file
        for searchdir in self.vpp_searchdir:
            probable_file = os.path.join(searchdir, filename)
            if(os.path.isfile(probable_file)):
                return probable_file
        raise RuntimeError("Can't find %s for %s in any of the include directories: %s"
                           % (filename, self.filename, ', '.join(self.vpp_searchdir)))

    def _parse_macro_def(self, m):
        name = m.group(1)
        expansion = m.group(3)
        if(m.group(2)):
            params = m.group(2).split(",")
        else:
            params = []
        if name in self.vpp_keywords:
            raise("Attempt to `define a reserved preprocessor keyword")
        mdef = self.VL_Define(name, params, expansion)
        self.vpp_macros.append(mdef)
        return mdef

    def _preprocess_file(self, file_content, file_name):
        import re
        exps = {"include": re.compile("^\s*`include\s+\"(.+)\""),
                "define": re.compile("^\s*`define\s+(\w+)(?:\(([\w\s,]*)\))?(.*)"),
                "ifdef_elsif": re.compile("^\s*`(ifdef|ifndef|elsif)\s+(\w+)\s*$"),
                "endif_else": re.compile("^\s*`(endif|else)\s*$")}

        vl_macro_expand = re.compile("`(\w+)(?:\(([\w\s,]*)\))?")

        cur_iter = 0

        logging.debug("preprocess file %s %d" % (file_name, len(file_content)))
#        print("BUF '%s'" %buf)
        buf = self._remove_comment(file_content)
        while True:
            new_buf = ""
            n_expansions = 0
            cur_iter += 1
            if cur_iter > 30:
                raise Exception("Recursion level exceeded. Nested `includes?")
            for line in self._degapize(buf):
                matches = {}
                last = None
                for k in exps.iterkeys():
                    matches[k] = re.match(exps[k], line)
                    if(matches[k]):
                        last = matches[k]

                if matches["ifdef_elsif"]:
                    cond_true = self._find_macro(last.group(2)) is not None
                    if(last.group(1) == "ifndef"):
                        cond_true = not cond_true
    # fixme: support `elsif construct
                    elif(last.group(1) == "elsif"):
                        self.vpp_stack.pop()
                    self.vpp_stack.push(cond_true)
                    continue

                elif matches["endif_else"]:
                    if(last.group(1) == "endif"):
                        self.vpp_stack.pop()
                    else:  # `else
                        self.vpp_stack.flip()
                    continue

                if not self.vpp_stack.all_true():
                    continue

                if matches["include"]:
                    import os
                    path = self._search_include(last.group(1), os.path.dirname(file_name))
                    logging.debug("Parsed cur. %s file includes %s" % (file_name, path))
                    line = self._preprocess_file(file_content=open(path, "r").read(),
                                                   file_name=path)
                    # print("IncBuf '%s'" % parsed)
                    if file_name in self.vpp_filedeps.iterkeys():
#                        self.vpp_filedeps[cur_file_name].append(path)
                        pass
                    else:
#                        pass
                        self.vpp_filedeps[file_name] = [path]
                    new_buf += line + '\n'
                    continue

                elif matches["define"]:
                    self._parse_macro_def(matches["define"])
                global n_repl
                n_repl = 0

# the actual macro expansions (no args/vargs support yet, though)
                def do_expand(what):
                    global n_repl
#                    print("Expand %s" % what.group(1))
                    if what.group(1) in self.vpp_keywords:
#                        print("GotReserved")
                        return '`'+what.group(1)
                    m = self._find_macro(what.group(1))
                    if m:
                        n_repl += 1
                        return m.expansion
                    else:
                        logging.error("No expansion for macro '`%s'" % what.group(1))

                line = re.sub(vl_macro_expand, do_expand, line)
                new_buf += line + '\n'
                n_expansions += n_repl
                buf = new_buf
            if n_expansions == 0:
                return new_buf

    def _define(self, name, expansion):
        mdef = self.VL_Define(name, [], expansion)
        self.vpp_macros.append(mdef)

    def add_path(self, path):
        self.vpp_searchdir.append(path)

    def preprocess(self, filename):
        self.filename = filename
        buf = open(filename, "r").read()
        return self._preprocess_file(file_content=buf, file_name=filename)

    def _find_first(self, f, l):
        x = filter(f, l)
        if x is not None:
            return x[0]
        else:
            return None

    def get_file_deps(self):
        deps = []
        for fs in self.vpp_filedeps.iterkeys():
            for f in self.vpp_filedeps[fs]:
                deps.append(f)
        return list(set(deps))


class VerilogParser:

    reserved_words = ["accept_on",
                    "alias",
                    "always",
                    "always_comb",
                    "always_ff",
                    "always_latch",
                    "and",
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

    def __init__(self):
        self.preproc = VerilogPreprocessor()

    def add_search_path(self, path):
        self.preproc.add_path(path)

    def remove_procedural_blocks(self, buf):
        buf = buf.replace("(", " ( ")
        buf = buf.replace(")", " ) ")
        block_level = 0
        paren_level = 0
        buf2 = ""

        for word in buf.split():
            drop_last = False

            if(word == "begin"):
                block_level += 1
            elif (word == "end"):
                drop_last = True
                block_level -= 1

            if(block_level > 0 and not drop_last):
                if (word == "("):
                    paren_level += 1
                elif (word == ")"):
                    paren_level -= 1
                    drop_last = True

#            print("w %s b %d p %d" % (word, block_level, paren_level))
            if drop_last:
                buf2 += ""
            if not block_level and not paren_level and not drop_last:
                buf2 += word + " "

        return buf2

    def parse(self, f_deps, filename):
        import copy
        buf = self.preproc.preprocess(filename)
        f = open("preproc.v", "w")
        f.write(buf)
        f.close()
        self.preprocessed = copy.copy(buf)

        import re
        m_inside_module = re.compile("(?:module|interface)\s+(\w+)\s*(?:\(.*?\))?\s*(.+?)(?:endmodule|endinterface)", re.DOTALL | re.MULTILINE)
        m_instantiation = re.compile("(?:\A|\\s*)\s*(\w+)\s+(?:#\s*\(.*?\)\s*)?(\w+)\s*\(.*?\)\s*", re.DOTALL | re.MULTILINE)

        def do_module(s):
#            print("module %s" %s.group(1))
            f_deps.add_relation(DepRelation(s.group(1), DepRelation.PROVIDE, DepRelation.ENTITY))

            def do_inst(s):
                mod_name = s.group(1)
                if(mod_name in self.reserved_words):
                    return
#                print("-> instantiates %s as %s" % (s.group(1), s.group(2)))
                f_deps.add_relation(DepRelation(s.group(1), DepRelation.USE, DepRelation.ENTITY))
            re.subn(m_instantiation, do_inst, s.group(2))
        re.subn(m_inside_module, do_module,  buf)

        for f in self.preproc.vpp_filedeps:
            f_deps.add_relation(DepRelation(f, DepRelation.USE, DepRelation.INCLUDE))
        f_deps.add_relation(DepRelation(filename, DepRelation.PROVIDE, DepRelation.INCLUDE))
