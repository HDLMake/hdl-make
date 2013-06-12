#!/usr/bin/python

# A Verilog preprocessor. Still lots of stuff to be done, but it's already quite useful
# for calculating dependencies.

class VerilogPreprocessor:

# Reserved verilog preprocessor keywords. The list is certainly not full
	vpp_keywords = [ "define", "line", "include", "elsif", "ifdef", "endif", "else", "undef", "timescale" ];

# List of `include search paths
	vpp_searchdir = ["."];

# List of macro definitions
	vpp_macros = [];

# Dictionary of files sub-included by each file parsed
	vpp_filedeps = {}

  # Verilog `define class
	class VL_Define:
		def __init__(self, name, args, expansion):
			self.name = name
			self.args = args
			self.expansion = expansion
		
	# Simple binary stack, for nested `ifdefs	evaluation
	class VL_Stack:
		def __init__(self):
			self.stack = [];
		
		def push(self, v):
			self.stack.append(v);
		
		def pop(self):
			return self.stack.pop()
			
		def all_true(self):
			return (len(self.stack)==0 or all(self.stack))
	
		def flip(self):
			self.push(not self.pop())
	
	def __init__(self):
		self.vpp_stack = self.VL_Stack();

	def find_macro(self, name):
		for m in self.vpp_macros:
			if(m.name == name):
				return m
		return None
	
	def comment_remover(self, s):
		def replacer(match):
			s = match.group(0)
			if s.startswith('/'):
				return ""
			else:
				return s
		import re
		pattern = re.compile('//.*?$|/\*.*?\*/|"(?:\\.|[^\\"])*"', re.DOTALL | re.MULTILINE )
		return re.sub(pattern, replacer, s)

	def degapize(self, s):
		import re
		lempty=re.compile("^\s*$")
		cline = None;
		lines=[]
		for l in s.splitlines(False):
			if re.match(lempty, l) != None:
				continue
			if l.endswith('\\'):
				if cline==None:
					cline=""
				cline += l[:len(l)-1]
				continue
			elif cline:
				l = cline+l
				cline = None
			else:
				cline=None
			lines.append(l)
		return lines
			
	def search_include(self, filename, parent_dir=None):
		import os
#		print("Parent Dir %s" % parent_dir)
		n = parent_dir+"/"+filename
		if(os.path.isfile(n)):
			return n
		for prefix in self.vpp_searchdir:
			n = prefix+"/"+filename
			if(os.path.isfile(n)):
				return n
		raise Exception("Can't find %s in any of the include directories" % filename)

	def parse_macro_def(self, m):
		import re

		name=m.group(1)
		expansion=m.group(3)
		if(m.group(2)):
			params = m.group(2).split(",")
		else:
			params = []
		if name in self.vpp_keywords:
			raise Exception("Attempt to `define a reserved preprocessor keyword")
		mdef=self.VL_Define(name, params, expansion)
		self.vpp_macros.append(mdef)
		return mdef

	def preprocess_buf(self, buf, cur_file_name):
		
		import re

		exps = { "include" : re.compile("^\s*`include\s+\"(.+)\""),	
						 "define" : re.compile("^\s*`define\s+(\w+)(?:\(([\w\s,]*)\))?(.*)"),	
						 "ifdef_elsif" : re.compile("^\s*`(ifdef|ifndef|elsif)\s+(\w+)\s*$"),	
					   "endif_else" : re.compile("^\s*`(endif|else)\s*$") }

		vl_macro_expand = re.compile("`(\w+)(?:\(([\w\s,]*)\))?") 

		cur_iter = 0

#		print("PP %s" %cur_file_name)
#		print("BUF '%s'" %buf)
		while True:
			n_expansions = 0
			new_buf = ""
			cur_iter=cur_iter+1
			if(cur_iter > 30):
				raise Exception("Recursion level exceeded. Nested `includes?")
			nc= self.comment_remover(buf)
			for l in self.degapize(nc):
#				print("LL : '%s'" % l)
				matches = {}
				last = None
				for k in exps.iterkeys():
					matches[k] = re.match(exps[k], l)
					if(matches[k]):
						last = matches[k]
			
				if matches ["ifdef_elsif"]:
					cond_true = self.find_macro(last.group(2)) != None
					if(last.group(1)=="ifndef"):
						cond_true = not cond_true;
	# fixme: support `elsif construct
					elif(last.group(1)=="elsif"):
						self.vpp_stack.pop()
					self.vpp_stack.push(cond_true)

					continue
				elif matches ["endif_else"]:
					if(last.group(1) == "endif"):
						self.vpp_stack.pop()
					else: # `else
						self.vpp_stack.flip()
					continue
			
				if not self.vpp_stack.all_true():
					continue
			
				if matches["include"]:
					import os
					path = self.search_include(last.group(1), os.path.dirname(cur_file_name))
					parsed= self.preprocess_buf(open(path,"r").read(), path)
					print("Parsed cur %s inc %s" % (cur_file_name, path))
#					print("IncBuf '%s'" % parsed)
					new_buf += parsed
					if(cur_file_name in self.vpp_filedeps.iterkeys()):
#						self.vpp_filedeps[cur_file_name].append(path)
						pass
					else:
#						pass
						self.vpp_filedeps[cur_file_name] = [path]
					
					continue
				elif matches ["define"]:
					macro = self.parse_macro_def(last)
					continue
				global n_repl
				n_repl=0
# the actual macro expansions (no args/vargs support yet, though)			
				def do_expand(what):
					global n_repl
#					print("Expand %s" % what.group(1))
					if what.group(1) in self.vpp_keywords:
#						print("GotReserved")
						return '`'+what.group(1)
					m=self.find_macro(what.group(1))
					if m:
						n_repl += 1
						return m.expansion
					else:
						print("ERROR: No expansion for macro '`%s'\n" % what.group(1))
						pass
						#print("ignoring macro: %s" % what.group(1)) 

				l=re.sub(vl_macro_expand, do_expand, l)
				n_expansions+=n_repl
				new_buf+=l+"\n"
			if(n_expansions==0):
				return new_buf
			buf=new_buf

	def define(self, name, expansion):
		mdef=self.VL_Define(name, [], expansion)
		self.vpp_macros.append(mdef)

	def add_path(self, path):
		self.vpp_searchdir.append(path)
			
	def preprocess(self, filename):
		self.filename= filename
		buf = open(filename,"r").read()
		return self.preprocess_buf(buf, filename)

	def find_first(self, f, l):
		x=filter(f, l)
		if x != None:
			return x[0]
		else:
			return None

	def get_file_deps(self):
		deps=[]
		for fs in self.vpp_filedeps.iterkeys():
			for f in self.vpp_filedeps[fs]: 
				deps.append(f)
		return list(set(deps))
			
from new_dep_solver import DepRelation, DepFile

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
		buf = buf.replace("("," ( ")
		buf = buf.replace(")"," ) ")
		block_level = 0
		paren_level = 0
		buf2 = ""
		prev_block_level = 0
		prev_paren_level = 0
		
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
			
#			print("w %s b %d p %d" % (word, block_level, paren_level))
			if(drop_last):
				buf2 += ";";
			if(not block_level and not paren_level and not drop_last):
				buf2 += word + " ";
		
		return buf2
	
	
	

	def parse(self, f_deps, filename):
		import copy
		buf= self.preproc.preprocess(filename)
		f=open("preproc.v","w")
		f.write(buf);
		f.close()
		self.preprocessed = copy.copy(buf)
		includes = self.preproc.get_file_deps()

		import re
		m_inside_module = re.compile("(?:module|interface)\s+(\w+)\s*(?:\(.*?\))?\s*;(.+?)(?:endmodule|endinterface)",re.DOTALL | re.MULTILINE)
		m_instantiation = re.compile("(?:\A|\;\s*)\s*(\w+)\s+(?:#\s*\(.*?\)\s*)?(\w+)\s*\(.*?\)\s*", re.DOTALL | re.MULTILINE)

		def do_module(s):
#			print("module %s" %s.group(1))
			f_deps.add_relation(DepRelation(s.group(1), DepRelation.PROVIDE, DepRelation.ENTITY))
			def do_inst(s):
				mod_name = s.group(1)
				if(mod_name in self.reserved_words):
					return
#				print("-> instantiates %s as %s" % (s.group(1), s.group(2)))
				f_deps.add_relation(DepRelation(s.group(1), DepRelation.USE, DepRelation.ENTITY))
			re.subn(m_instantiation, do_inst, s.group(2))
		re.subn(m_inside_module, do_module,  buf)

		for f in self.preproc.vpp_filedeps:
			f_deps.add_relation(DepRelation(f, DepRelation.USE, DepRelation.INCLUDE))
		f_deps.add_relation(DepRelation(filename, DepRelation.PROVIDE, DepRelation.INCLUDE))
