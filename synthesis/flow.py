#!/usr/bin/python
# -*- coding: utf-8 -*-

import xml.dom.minidom as xml
import sys
from srcfile import *

xmlimpl = xml.getDOMImplementation()

class ISEProjectProperty:
        def __init__(self,  name, value, is_default = False):
                self.name = name
                self.value = value
                self.is_default = is_default

        def emit_xml(self, doc):
                prop = doc.createElement("property")
                prop.setAttribute("xil_pn:name", self.name)
                prop.setAttribute("xil_pn:value", self.value)
                if self.is_default:
                        prop.setAttribute("xil_pn:valueState", "default")
                else:
                        prop.setAttribute("xil_pn:valueState", "non-default")

                return prop


class ISEProject:
        def __init__(self, top_mod = None):
                self.props = []
                self.files = []
                self.libs = []
                self.xml_doc = None
                self.xml_files = []
                self.xml_props = []
                self.xml_libs = []
                self.top_mod = top_mod

        def add_files(self, files):
                self.files.extend(files);

        def add_libs(self, libs):
                self.libs.extend(libs);
                self.libs.remove('work')

        def add_property(self, prop):
                self.props.append(prop)

        def _parse_props(self):
                for p in self.xml_project.getElementsByTagName("properties")[0].getElementsByTagName("property"):
                        prop = ISEProjectProperty(
                                p.getAttribute("xil_pn:name"),
                                p.getAttribute("xil_pn:value"),
                                p.getAttribute("xil_pn:valueState") == "default"
                                )

                        self.props.append(prop)

        def load_xml(self, filename):
                f = open(filename)
                self.xml_doc = xml.parse(f) 
                self.xml_project =  self.xml_doc.getElementsByTagName("project")[0];
                self._parse_props()
                self.xml_files = self.__purge_dom_node(name="files", where=self.xml_doc.documentElement)
                f.close()

        def __purge_dom_node(self, name, where):
                node = where.getElementsByTagName(name)[0]
                where.removeChild(node)
                new = self.xml_doc.createElement(name)
                where.appendChild(new)
                return new

        def _output_files(self, node):

                for f in self.files:
                        import os
                        fp = self.xml_doc.createElement("file")
                        fp.setAttribute("xil_pn:name", os.path.relpath(f.path))
                        if (isinstance(f, VHDLFile)):
                                fp.setAttribute("xil_pn:type", "FILE_VHDL")
                        elif (isinstance(f, VerilogFile)):
                                fp.setAttribute("xil_pn:type", "FILE_VERILOG")
                        elif (isinstance(f, UCFFile)):
                                fp.setAttribute("xil_pn:type", "FILE_UCF")

                        assoc = self.xml_doc.createElement("association");
                        assoc.setAttribute("xil_pn:name", "Implementation");
                        assoc.setAttribute("xil_pn:seqID", str(self.files.index(f)+1));

                        if(f.library != "work"):
                                lib = self.xml_doc.createElement("library");
                                lib.setAttribute("xil_pn:name", f.library);
                                fp.appendChild(lib)

                        fp.appendChild(assoc)
                        node.appendChild(fp);

        def _output_props(self, node):
                for p in self.props:
                        node.appendChild(p.emit_xml(self.xml_doc))

        def _output_libs(self, node):
                for l in self.libs:
                        ll =  self.xml_doc.createElement("library")
                        ll.setAttribute("xil_pn:name", l);
                        node.appendChild(ll);


        def emit_xml(self, filename = None):
                if not self.xml_doc:
                        self.create_empty_project()

                self._output_files(self.xml_files)
                self._output_props(self.xml_props)
                self._output_libs(self.xml_libs)

                self.xml_doc.writexml(open(filename,"w"), newl="\n", addindent="\t")

        def create_empty_project(self):
                self.xml_doc = xmlimpl.createDocument("http://www.xilinx.com/XMLSchema", "project", None)
                top_element = self.xml_doc.documentElement
                top_element.setAttribute("xmlns", "http://www.xilinx.com/XMLSchema")
                top_element.setAttribute("xmlns:xil_pn", "http://www.xilinx.com/XMLSchema")

                version = self.xml_doc.createElement( "version")
                version.setAttribute("xil_pn:ise_version", "13.1");
                version.setAttribute("xil_pn:schema_version", "2");

                header = self.xml_doc.createElement("header")
                header.appendChild(self.xml_doc.createTextNode(""))

                self.xml_files = self.xml_doc.createElement("files")
                self.xml_props = self.xml_doc.createElement("properties")
                self.xml_libs = self.xml_doc.createElement("libraries")

                top_element.appendChild(header)
                top_element.appendChild(version)
                top_element.appendChild(self.xml_files)
                top_element.appendChild(self.xml_props)
                top_element.appendChild(self.xml_libs)
