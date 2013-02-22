#!/usr/bin/python


class DepRelation:
	PROVIDE = 1
	USE = 2
	
	ENTITY = 1
	PACKAGE = 2
	INCLUDE = 3

	def __init__(self, obj_name, direction, rel_type):
		self.direction = direction
		self.rel_type = rel_type
		self.obj_name = obj_name
	
	def satisfies(self, rel_b):
		if(rel_b.direction == self.USE):
			return True
		elif(self.direction == self.PROVIDE and rel_b.rel_type == self.rel_type and rel_b.obj_name == self.obj_name):
			return True
		return False	

	def __str__(self):
		dstr = { self.USE : "Use", self.PROVIDE : "Provide" }
		ostr = { self.ENTITY : "entity/module", self.PACKAGE : "package", self.INCLUDE : "include/header" }
		return "%s %s '%s'" % (dstr[self.direction], ostr[self.rel_type], self.obj_name)

class DepFile:
	def __init__(self, filename, search_path=[]):
		self.rels = [];
		self.filename = filename
		parser = ParserFactory().create(self.filename, search_path)
		parser.parse(self, self.filename)

	def add_relation(self, rel):
		self.rels.append(rel);		
		
	def satisfies(self, rels_b):
		for r_mine in self.rels:
				if not any(map(rels_b, lambda x: x.satisfies(r_mine))):
					return False
	
	def show_relations(self):
		for r in self.rels:
			print(str(r))

class DepParser:
	def __init__(self):
		pass
	
	def parse(f, filename):
		pass

class ParserFactory:
	def create(self, filename, search_path):
		import re
		from vlog_parser import VerilogParser
		from vhdl_parser import VHDLParser

		extension=re.match(re.compile(".+\.(\w+)$"), filename)
		if(not extension):
			throw ("Unecognized file format : %s" % filename);
		extension = extension.group(1).lower()
		if(extension in ["vhd", "vhdl"]):
			return VHDLParser();
		elif(extension in ["v", "sv"]):
			vp = VerilogParser();
			for d in search_path:
				vp.add_search_path(d)
			return vp
