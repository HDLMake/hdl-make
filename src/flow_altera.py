#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 Pawel Szostek (pawel.szostek@cern.ch)
#
#    This source code is free software; you can redistribute it
#    and/or modify it in source code form under the terms of the GNU
#    General Public License as published by the Free Software
#    Foundation; either version 2 of the License, or (at your option)
#    any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA
#


class _QuartusProjectProperty:
    SET_GLOBAL_INSTANCE, SET_INSTANCE_ASSIGNMENT, SET_LOCATION_ASSIGNMENT, SET_GLOBAL_ASSIGNMENT = range(4)
    t = {"set_global_instance" : SET_GLOBAL_INSTANCE,
    "set_instance_assignment" : SET_INSTANCE_ASSIGNMENT,
    "set_location_assignment": SET_LOCATION_ASSIGNMENT,
    "set_global_assignment": SET_GLOBAL_ASSIGNMENT}

    def __init__(self, command, what=None, name=None, name_type=None, from_=None, to=None, section_id=None):
	self.command = command
	self.what = what
	self.name = name
	self.name_type = name_type
	self.from_ = from_
	self.to = to
	self.section_id = section_id

    def emit(self):
	words = []
	words.append(dict([(b,a) for a,b in self.t.items()])[self.command])

	if self.what != None:
	    words.append(self.what)
	if self.name != None:
	    words.append("-name")
	    words.append(self.name_type)
	    words.append(self.name)
	if self.from_ != None:
	    words.append("-from")
	    words.append(self.from_)
	if self.to != None:
	    words.append("-to")
	    words.append(self.to)
	if self.section_id != None:
	    words.append("-section_id")
	    words.append(self.section_id)
	return ' '.join(words)


class QuartusProject:
    def __init__(self, filename):
        self.properties = []
        self.files = []
        self.filename = filename
        self.preflow = None
        self.postflow = None

    def emit(self):
        f = open(self.filename+'.qsf', "w")
        for p in self.properties:
            f.write(p.emit()+'\n')
        f.write(self.__emit_files())
        f.write(self.__emit_scripts())
        f.close()
        f = open(self.filename+'.qpf', "w");
        f.write("PROJECT_REVISION = \"" + self.filename + "\"\n")
        f.close()

    def __emit_scripts(self):
        tmp = 'set_global_assignment -name {0} "quartus_sh:{1}"'
        pre = post = ""
        if self.preflow:
            pre = tmp.format("PRE_FLOW_SCRIPT_FILE", self.preflow.rel_path())
        if self.postflow:
            post = tmp.format("POST_FLOW_SCTIPT_FILE", self.postflow.rel_path())
        return pre+'\n'+post+'\n'
        
    def __emit_files(self):
        from srcfile import VHDLFile, VerilogFile, SignalTapFile, SDCFile, DPFFile
        tmp = "set_global_assignment -name {0} {1}"
        ret = []
        for f in self.files:
            if isinstance(f, VHDLFile):
                line = tmp.format("VHDL_FILE", f.rel_path())
            elif isinstance(f, VerilogFile):
                line = tmp.format("VERILOG_FILE", f.rel_path())
            elif isinstance(f, SignalTapFile):
                line = tmp.format("SIGNALTAP_FILE", f.rel_path())
            elif isinstance(f, SDCFile):
                line = tmp.format("SDC_FILE", f.rel_path())
            elif isinstance(f, DPFFile):
                line = tmp.format("MISC_FILE", f.rel_path())
            else:
                continue
            ret.append(line)
        return ('\n'.join(ret))+'\n'
 
    def add_property(self, val):
        #don't save files (they are unneeded)
        if val.name_type != None and "_FILE" in val.name_type:
            return
        self.properties.append(val)

    def add_files(self, fileset):
        for f in fileset:
            self.files.append(f)

    def read(self):
        def __gather_string(words, first_index):
            i = first_index
            ret = []
            if words[i][0] != '"':
                return (words[i],1)
            else:
                while True:
                    ret.append(words[i])
                    if words[i][len(words[i])-1] == '"':
                        return (' '.join(ret), len(ret))
                    i=i+1

        f = open(self.filename+'.qsf', "r")
        lines = [l.strip() for l in f.readlines()]
        lines = [l for l in lines if l != "" and l[0] != '#']
        QPP = _QuartusProjectProperty
        for line in lines:
            words = line.split()
            command = QPP.t[words[0]]
            what = name = name_type = from_ = to = section_id = None
            i = 1
            while True:
                if i >= len(words):
                    break

                if words[i] == "-name":
                    name_type = words[i+1]
                    name, add = __gather_string(words, i+2)
                    i = i+2+add
                    continue
                elif words[i] == "-section_id":
                    section_id, add = __gather_string(words, i+1)
                    i = i+1+add
                    continue
                elif words[i] == "-to":
                    to, add = __gather_string(words, i+1)
                    i = i+1+add
                    continue
                elif words[i] == "-from":
                    from_, add = __gather_string(words, i+1)
                    i = i+2
                    continue
                else:
                    what = words[i]
                    i = i+1
                    continue
            prop = QPP(command=command, what=what, name=name,
	      name_type=name_type, from_=from_, to=to, section_id=section_id)

            self.add_property(prop)
        f.close()

    def add_initial_properties(self, syn_device, syn_grade, syn_package, syn_top):
        import re
        family_names = {
            "^EP2AGX.*$" : "Arria II GX",
            "^EP3C.*$" : "Cyclone III"
            }

        for key in family_names:
            if re.match(key, syn_device.upper()):
                family = family_names[key];
                
        devstring = (syn_device +syn_package+syn_grade).upper()
        QPP =_QuartusProjectProperty
        self.add_property(QPP(QPP.SET_GLOBAL_ASSIGNMENT, name_type='FAMILY', name='"'+family+'"'))
        self.add_property(QPP(QPP.SET_GLOBAL_ASSIGNMENT, name_type='DEVICE', name=devstring))
        self.add_property(QPP(QPP.SET_GLOBAL_ASSIGNMENT, name_type='TOP_LEVEL_ENTITY', name=syn_top))
