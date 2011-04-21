# -*- coding: utf-8 -*-

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
        
    Cleanup:
    >>> import os
    >>> os.remove("test.py")
    """
    
    class Option:
        def __init__(self, name, **others):
            self.name = name
            self.keys = []
            self.types = []

            for key in others:
                if key == "help":
                    self.help = others["help"]
                elif key == "default":
                    self.default = others["default"]
                elif key == "type":
                    self.add_type(others["type"]) 
                else:
                    raise ValueError("Option not recognized: " + key)

            if "default" in others:
                self.hasdefault = True
            else:
                self.hasdefault = False

        def add_type(self, type_obj):
            self.types.append(type(type_obj))


    def __init__(self, description = None):
        if description != None:
            if not isinstance(description, basestring):
                raise ValueError("Description should be a string!")
        self.description = description
        self.options = {}

    def add_option(self, name, **others):
        if name in self.options:
            raise ValueError("Option already added: " + name)
        self.options[name] = ConfigParser.Option(name, **others)

    def add_type(self, name, type):
        if name not in self.options:
            raise RuntimeError("Can't add type to a non-existing option")
        self.options[name].add_type(type_obj=type)

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
 
    def parse(self):
        options = {}
        ret = {}

        try:
            self.file
        except AttributeError:
            self.file = "/dev/null"

        execfile(self.file, options)
        for key, val in list(options.items()):
            if key.startswith('__'):
                continue
            if key not in self.options:
                raise NameError("Unrecognized option: " + key)
            opt = self.options[key]
            if type(val) not in opt.types:
                raise RuntimeError("Given option: "+str(type(val))+" doesn't match specified types:"+str(opt.types))
            ret[key] = val 
        for name, opt in self.options.items():
            if opt.hasdefault == True:
                if opt.name not in ret:
                    ret[opt.name] = opt.default
        return ret

            
        
def _test():
    import doctest
    doctest.testmod()
    
if __name__ == "__main__":
    _test()