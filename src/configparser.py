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

import msg as p
import sys
import StringIO
import contextlib

@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO.StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old

class ConfigParser(object):
    """Class for parsing python configuration files

    Case1: Normal usage
    >>> f = open("test.py", "w")
    >>> f.write('modules = {"local":"/path/to/local", "svn":"path/to/svn"}; ')
    >>> f.write('fetchto = ".."' )
    >>> f.close()
    >>> p = ConfigParser()
    >>> p.add_option("modules", type={})
    >>> p.add_option("fetchto", type='')
    >>> p.add_config_file("test.py")
    >>> p.parse()
    {'modules': {'svn': 'path/to/svn', 'local': '/path/to/local'}, 'fetchto': '..'}

    Case2: Default value and lack of a variable
    >>> f = open("test.py", "w")
    >>> f.write('a="123"')
    >>> f.close()
    >>> p = ConfigParser()
    >>> p.add_option("a", type='')
    >>> p.add_option("b", type='', default='borsuk')
    >>> p.add_config_file("test.py")
    >>> p.parse()
    {'a': '123', 'b': 'borsuk'}

    Case3: Multiple types for a variable
    >>> f = open("test.py", "w")
    >>> f.write('a=[1,2,3]')
    >>> f.close()
    >>> p = ConfigParser()
    >>> p.add_option("a", type=1, default=12)
    >>> p.add_type("a", type=[])
    >>> p.add_config_file("test.py")
    >>> p.parse()
    {'a': [1, 2, 3]}

    Case4: Unrecognized options
    >>> f = open("test.py", "w")
    >>> f.write('a = 123')
    >>> f.close()
    >>> p = ConfigParser()
    >>> p.add_option("b", type='')
    >>> p.add_config_file("test.py")
    >>> p.parse()
    Traceback (most recent call last):
        File "<stdin>", line 1, in <module>
        File "configparser.py", line 107, in parse
        raise NameError("Unrecognized option: " + key)
    NameError: Unrecognized option: a

    Case5: Invalid parameter type
    >>> f = open("test.py","w")
    >>> f.write('a="123"')
    >>> f.close()
    >>> p = ConfigParser()
    >>> p.add_option("a", type=0)
    >>> p.add_config_file("test.py")
    >>> p.parse()
    Traceback (most recent call last):
        File "<stdin>", line 1, in <module>
        File "configparser.py", line 110, in parse
        raise RuntimeError("Given option: "+str(type(val))+" doesn't match specified types:"+str(opt.types))
    RuntimeError: Given option: <type 'str'> doesn't match specified types:[<type 'int'>]

    Case6:
    >>> f = open("test.py","w")
    >>> f.write('a={"zupa":1}')
    >>> f.close()
    >>> p = ConfigParser()
    >>> p.add_option("a", type={})
    >>> p.add_allowed_key("a", "zupa")
    >>> p.add_config_file("test.py")
    >>> p.parse()
    {'a': {'zupa': 1}}

    Case7
    >>> f = open("test.py","w")
    >>> f.write('a={"kot":1}')
    >>> f.close()
    >>> p = ConfigParser()
    >>> p.add_option("a", type={})
    >>> p.add_allowed_key("a", "kniaz")
    >>> p.add_config_file("test.py")
    >>> p.parse()
    Traceback (most recent call last):
        File "<stdin>", line 1, in <module>
        File "configparser.py", line 184, in parse
        raise RuntimeError("Encountered unallowed key: " +key+ " for options '"+opt_name+"'")
    RuntimeError: Encountered unallowed key: kot for options 'a'

    Cleanup:
    >>> import os
    >>> os.remove("test.py")
    """

    class Option:
        def __init__(self, name, **others):
            self.name = name
            self.keys = []
            self.types = []
            self.help = ""
            self.arbitrary_code = ""
            self.global_code = ""

            for key in others:
                if key == "help":
                    self.help = others["help"]
                elif key == "default":
                    self.default = others["default"]
                elif key == "type":
                    self.add_type(type_obj=others["type"]) 
                else:
                    raise ValueError("Option not recognized: " + key)

        def add_type(self, type_obj):
            self.types.append(type(type_obj))


    def __init__(self, description = None):
        if description != None:
            if not isinstance(description, str):
                raise ValueError("Description should be a string!")
        self.description = description
        self.options = []
        self.arbitrary_code = ""
        self.config_file = None

    def __setitem__(self, name, value):
        if name in self.__names():
            filter(lambda x: x.name == name, self.options)[0] = value
        else:
            self.options.append(value)

    def __getitem__(self, name):
        if name in self.__names():
            return [x for x in self.options if x!= None and x.name == name][0]
        else:
            raise RuntimeError("No such option as " + str(name))

    def help(self):
        p.rawprint("Variables available in a manifest:")
        for opt in self.options:
            if opt == None:
                p.rawprint("")
                continue

            line = '  {0:15}; {1:29}; {2:45}{3}{4:10}'
            try:
                tmp_def = opt.default
                if tmp_def == "":
                    tmp_def = '""'
                line = line.format(opt.name, str(opt.types), opt.help,', default=', tmp_def)
            except AttributeError: #no default value
                line = line.format(opt.name, str(opt.types), opt.help, "","")
            p.rawprint(line)

    def add_option(self, name, **others):
        if name in self.__names():
            raise ValueError("Option already added: " + name)
        self.options.append(ConfigParser.Option(name, **others))

    def add_type(self, name, type):
        if name not in self.__names():
            raise RuntimeError("Can't add type to a non-existing option")
        self[name].add_type(type)

    def add_delimiter(self):
        self.options.append(None)

    def add_allowed_key(self, name, key):
        if not isinstance(key, str):
            raise ValueError("Allowed key must be a string")
        try:
            self[name].allowed_keys.append(key)
        except AttributeError:
            if type(dict()) not in self[name].types:
                raise RuntimeError("Allowing a key makes sense for dictionaries only")
            self[name].allowed_keys = [key]

        self[name].allowed_keys.append(key)

    def add_config_file(self, config_file):
        if self.config_file is not None:
            raise RuntimeError("Config file should be added only once")
        
        import os
        if not os.path.exists(config_file):
            raise RuntimeError("Config file doesn't exists: " + config_file)
        self.config_file = config_file
        return

    def add_arbitrary_code(self, code):
        self.arbitrary_code += code + '\n'

    def __names(self):
        return [o.name for o in self.options if o != None]

    def parse(self):
        options = {}
        ret = {}

        if self.config_file is not None: 
	    with open(self.config_file, "r") as config_file:
	        content = open(self.config_file, "r").readlines()
            content = ''.join(content)
        else:
            content = ''
        content = self.arbitrary_code + '\n' + content

        #now the trick:
        #I take the arbitrary code and parse it
        #the values are not important, but thanks to it I can check
        #if a variable came from the arbitrary code.
        #This is important because in the manifests only certain group
        #of variables is allowed. In arbitrary code all of them can be used.
        arbitrary_options = {}
        import sys
        try:
            with stdoutIO() as s:
                exec(self.arbitrary_code, arbitrary_options)
            printed = s.getvalue()
            if printed:
                print(printed)
        except SyntaxError as e:
            p.error("Invalid syntax in the arbitraty code:\n" + str(e))
            quit()
        except:
            p.error("Unexpected error while parsing arbitrary code:")
            p.rawprint(str(sys.exc_info()[0])+':'+str(sys.exc_info()[1]))
            quit()

        try:
            with stdoutIO() as s:
                exec(content, options)
            printed = s.getvalue()
            if len(printed) > 0:
                p.info("The manifest inside " + self.config_file + " tried to print something:")
                for line in printed.split('\n'):
                    p.rawprint("> " + line)
            #print "out:", s.getvalue()
        except SyntaxError as e:
            p.error("Invalid syntax in the manifest file " + self.config_file+ ":\n" + str(e))
            quit()
        except:
            p.error("Encountered unexpected error while parsing " + self.config_file)
            p.rawprint(str(sys.exc_info()[0]) +':'+ str(sys.exc_info()[1]))
            quit()

        for opt_name, val in list(options.items()): #check delivered options
            if opt_name.startswith('__'):
                continue
            if opt_name not in self.__names():
                if opt_name in arbitrary_options:
                    continue
                else:
                    #if opt_name.startswith("global_"):
                    #    continue
                    raise NameError("Unrecognized option: " + opt_name)
            opt = self[opt_name]
            if type(val) not in opt.types:
                raise RuntimeError("Given option: "+str(type(val))+" doesn't match specified types:"+str(opt.types))
            ret[opt_name] = val
#            print("Opt_name ", opt_name)
            if type(val) == type(dict()):
                try:
                    for key in val:
                        if key not in self[opt_name].allowed_keys:
                            raise RuntimeError("Encountered unallowed key: " +key+ " for options '"+opt_name+"'")
                except AttributeError: #no allowed_keys member - don't perform any check
                    pass

        for opt in self.options: #set values for not listed items with defaults
            try:
                if opt.name not in ret:
                    ret[opt.name] = opt.default
            except AttributeError: #no default value in the option
                pass
        return ret


def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()