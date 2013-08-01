#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 CERN
# Author: Tomasz Wlostowski (tomasz.wlostowski@cern.ch)
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


def remove_gaps(buf, delims, gap_chars, lower_strings=False):
    da={}
    for d in delims:
        da[d]=False
    prev_is_gap = False
    buf2=""
    lines=[]
    for c in buf:
        for d in delims:
            if(c==d):
                da[d]=not da[d]
        
        within_string = any(da.values()) and not (c in delims)
            
        if(not within_string):
            if(c in gap_chars):
                if(not prev_is_gap):
                    prev_is_gap = True
                    buf2+=" "
            else:
                prev_is_gap = False
                buf2+=c
                if(c==";" or c=="\n"):
                    lines.append(buf2);
                    buf2=""
        else:
            buf2+=c;
            prev_is_gap = False

    return lines

from dep_solver import DepParser, DepRelation, DepFile
        
class VHDLParser(DepParser):
    def parse(self, f_deps, filename):
        f = open(filename,"r")
        buf = ""
        # stage 1: strip comments
        for l in f:
            ci = l.find("--")
            if(ci==0):
                continue
                
            while(ci>0): 
                nquotes = l[:ci].count('"') # ignore comments in strings
                if(nquotes % 2 == 0):
                    l=l[:ci-1];
                    break
                ci= l.find("--", ci+1)
            buf+=l
            
        # stage 2: remove spaces, crs, lfs, strip strings (we don't need them)
        buf2=""
        string_literal = char_literal = False
        prev_is_gap = False
        gap_chars = " \r\n\t"
        lines=[]
        
        for c in buf:
            if(c == '"' and not char_literal):
                string_literal = not string_literal
            if(c == "'" and not string_literal)-:
                char_literal = not char_literal
        
            within_string = (string_literal or char_literal) and (c != '"') and (c != "'")
            
            if(not within_string):
                if(c in gap_chars):
                    if(not prev_is_gap):
                        prev_is_gap = True
                        buf2+=" "
                else:
                    prev_is_gap = False
                    buf2+=c.lower()
                    if(c==";"):
                        lines.append(buf2);
                        buf2=""
            else:
                prev_is_gap = False

        import re


        patterns = {
            "use" : "^ *use *(\w+) *\. *(\w+) *. *\w+ *;",
            "entity" : "^ *entity +(\w+) +is +(port|generic)",
            "package" : "^ *package +(\w+) +is",
            "arch_begin" : "^ *architecture +(\w+) +of +(\w+) +is +",
            "arch_end" : "^ *end +(\w+) +;",
            "instance" : "^ *(\w+) *\: *(\w+) *(port|generic) *map"
        }
        
        compiled_patterns = map(lambda p: (p,re.compile(patterns[p])), patterns)

        within_architecture = False
            
        for l in lines:
            matches = filter(lambda(k,v): v!=None, map(lambda (k,v): (k,re.match(v,l)), compiled_patterns))
            if(not len(matches)):
                continue
                    
            what,g=matches[0]
            
            if(what == "use"):
                f_deps.add_relation(DepRelation(g.group(1)+"."+g.group(2), DepRelation.USE, DepRelation.PACKAGE))
            if(what == "package"):
                f_deps.add_relation(DepRelation(g.group(1), DepRelation.PROVIDE, DepRelation.PACKAGE))
            elif(what == "entity"):
                f_deps.add_relation(DepRelation(g.group(1), DepRelation.PROVIDE, DepRelation.ENTITY))
            elif(what == "package"):
                f_deps.add_relation(DepRelation(g.group(1), DepRelation.PROVIDE, DepRelation.PACKAGE))
            elif(what == "arch_begin"):
                arch_name = g.group(1)
                within_architecture = True
            elif(what == "arch_end" and within_architecture and g.group(1) == arch_name):
                within_architecture = False
            elif(what == "instance" and within_architecture):
                f_deps.add_relation(DepRelation(g.group(1), DepRelation.USE, DepRelation.ENTITY))


