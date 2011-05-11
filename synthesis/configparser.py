# -*- coding: utf-8 -*-
import msg as p

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
            if not isinstance(description, basestring):
                raise ValueError("Description should be a string!")
        self.description = description
        self.options = {}
        self.arbitrary_code = ""

    def help(self):
        p.rawprint("Variables available in a manifest:")
        for key in self.options:
            opt = self.options[key]
            line = '  {0:10}; {1:15}; {2:40}{3}{4:10}'
            try:
                tmp_def = opt.default
                if tmp_def == "":
                    tmp_def = '""'
                line = line.format(key, str(opt.types), opt.help,', default=', tmp_def)
            except AttributeError: #no default value
                line = line.format(key, str(opt.types), opt.help, "","")
            p.rawprint(line)

    def add_option(self, name, **others):
        if name in self.options:
            raise ValueError("Option already added: " + name)
        self.options[name] = ConfigParser.Option(name, **others)

    def add_type(self, name, type):
        if name not in self.options:
            raise RuntimeError("Can't add type to a non-existing option")
        self.options[name].add_type(type_obj=type)

    def add_allowed_key(self, name, key):
        if not isinstance(key, basestring):
            raise ValueError("Allowed key must be a string")
        try:
            self.options[name].allowed_keys.append(key)
        except AttributeError:
            if type(dict()) not in self.options[name].types:
                raise RuntimeError("Allowing a key makes sense for dictionaries only")
            self.options[name].allowed_keys = [key]

        self.options[name].allowed_keys.append(key)

    def add_config_file(self, config_file):
        try:
            self.file #check if there is such attribute
        except AttributeError: #no file was added
            import os
            if not os.path.exists(config_file):
                raise RuntimeError("Config file doesn't exists: " + config_file)
            self.file = config_file
            return

        raise RuntimeError("Config file should be added only once")

    def add_arbitrary_code(self, code):
        self.arbitrary_code += code + '\n'

    def parse(self):
        options = {}
        ret = {}

        try:
            file = open(self.file, "r")
            content = file.readlines()
            content = ''.join(content)
        except AttributeError:
            content = ''
        content = self.arbitrary_code + '\n' + content

        #now the trick:
        #I take the arbitrary code and parse it
        #the values are not important, but thanks to it I can check
        #if a variable came from the arbitrary code.
        #This is important because in the manifests only certain group
        #of variables is allowed. In arbitrary code all of them can be used.
        arbitrary_options = {}
        exec(self.arbitrary_code, arbitrary_options)
        exec(content, options)

        for opt_name, val in list(options.items()): #check delivered options
            if opt_name.startswith('__'):
                continue
            if opt_name not in self.options:
                if opt_name in arbitrary_options:
                    continue
                else:
                    raise NameError("Unrecognized option: " + opt_name)
            opt = self.options[opt_name]
            if type(val) not in opt.types:
                raise RuntimeError("Given option: "+str(type(val))+" doesn't match specified types:"+str(opt.types))
            ret[opt_name] = val
            if type(val) == type(dict()):
                try:
                    for key in val:
                        if key not in self.options[opt_name].allowed_keys:
                            raise RuntimeError("Encountered unallowed key: " +key+ " for options '"+opt_name+"'")
                except AttributeError: #no allowed_keys member - don't perform any check
                    pass

        for name, opt in self.options.items(): #set values for not listed items with defaults
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