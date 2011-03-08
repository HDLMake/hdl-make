"""cfgparse - a powerful, extensible, and easy-to-use configuration parser.

By Dan Gass <dan.gass@gmail.com>

If you have problems with this module, please file bugs through the Source
Forge project page:
  http://sourceforge.net/projects/cfgparse
"""

# @future use option note when get error
# @future print file/section/linenumber information when checks fail
# @future - check type='choice' and choices=[] one must have the other
# @future -- do we have a command line --cfgcheck option that expands all configuration and checks all possible keys?

__version__ = "1.00"

__all__ = []

__copyright__ = """
Copyright (c) 2004 by Daniel M. Gass.   All rights reserved.
Copyright (c) 2001-2004 Gregory P. Ward.  All rights reserved.
Copyright (c) 2002-2004 Python Software Foundation.  All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

  * Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

  * Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.

  * Neither the name of the author nor the names of its
    contributors may be used to endorse or promote products derived from
    this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import ConfigParser as _ConfigParser
import cStringIO
import os
import re
import sys
import textwrap

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#
# U T I L I T Y
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

# <borrowed file="Lib/optparse.py" version="python2.4" modified="yes">
try:
    from gettext import gettext as _
except ImportError:
    _ = lambda arg: arg

class HelpFormatter:
    """
    Abstract base class for formatting option help.  ConfigParser
    instances should use one of the HelpFormatter subclasses for
    formatting help; by default IndentedHelpFormatter is used.

    Instance attributes:
      parser : OptionParser
        the controlling OptionParser instance
      indent_increment : int
        the number of columns to indent per nesting level
      max_help_position : int
        the maximum starting column for option help text
      help_position : int
        the calculated starting column for option help text;
        initially the same as the maximum
      width : int
        total number of columns for output (pass None to constructor for
        this value to be taken from the $COLUMNS environment variable)
      level : int
        current indentation level
      current_indent : int
        current indentation level (in columns)
      help_width : int
        number of columns available for option help text (calculated)
      default_tag : str
        text to replace with each option's default value, "%default"
        by default.  Set to false value to disable default value expansion.
      option_strings : { Option : str }
        maps Option instances to the snippet of help text explaining
        the syntax of that option, e.g. "option=VALUE"
    """

    NO_DEFAULT_VALUE = "none"

    def __init__(self,
                 indent_increment,
                 max_help_position,
                 width,
                 short_first):
        self.parser = None
        self.indent_increment = indent_increment
        self.help_position = self.max_help_position = max_help_position
        if width is None:
            try:
                width = int(os.environ['COLUMNS'])
            except (KeyError, ValueError):
                width = 80
            width -= 2
        self.width = width
        self.current_indent = 0
        self.level = 0
        self.help_width = None          # computed later
        self.short_first = short_first
        self.default_tag = "%default"
        self.option_strings = {}
        self._short_opt_fmt = "%s %s"
        self._long_opt_fmt = "%s=%s"

    def set_parser(self, parser):
        self.parser = parser

    def indent(self):
        self.current_indent += self.indent_increment
        self.level += 1

    def dedent(self):
        self.current_indent -= self.indent_increment
        assert self.current_indent >= 0, "Indent decreased below 0."
        self.level -= 1

    def format_usage(self, usage):
        raise NotImplementedError, "subclasses must implement"

    def format_heading(self, heading):
        raise NotImplementedError, "subclasses must implement"

    def format_description(self, description):
        if not description:
            return ""
        desc_width = self.width - self.current_indent
        indent = " "*self.current_indent
        return textwrap.fill(description,
                             desc_width,
                             initial_indent=indent,
                             subsequent_indent=indent) + "\n"

    def expand_default(self, option):
        if self.parser is None or not self.default_tag:
            return option.help

        try:
            default_value = option.default
        except AttributeError:
            default_value = None

        if default_value is NO_DEFAULT or default_value is None:
            default_value = self.NO_DEFAULT_VALUE

        return option.help.replace(self.default_tag, str(default_value))

    def format_option(self, option):
        # The help for each option consists of two parts:
        #   * the opt strings and metavars
        #     eg. ("option=VALUE")
        #   * the user-supplied help string
        #     eg. ("turn on expert mode", "read data from FILENAME")
        #
        # If possible, we write both of these on the same line:
        #   option=VALUE  explanation of some option
        #
        # But if the opt string list is too long, we put the help
        # string on a second line, indented to the same column it would
        # start in if it fit on the first line.
        #   thisoption=WAY_TO_LONG
        #           explanation of the long option
        result = []
        opts = self.option_strings[option]
        opt_width = self.help_position - self.current_indent - 2
        if len(opts) > opt_width:
            opts = "%*s%s\n" % (self.current_indent, "", opts)
            indent_first = self.help_position
        else:                       # start help on same line as opts
            opts = "%*s%-*s  " % (self.current_indent, "", opt_width, opts)
            indent_first = 0
        result.append(opts)
        if option.help:
            help_text = self.expand_default(option)
            help_lines = textwrap.wrap(help_text, self.help_width)
            result.append("%*s%s\n" % (indent_first, "", help_lines[0]))
            result.extend(["%*s%s\n" % (self.help_position, "", line)
                           for line in help_lines[1:]])
        elif opts[-1] != "\n":
            result.append("\n")
        return "".join(result)

    def store_option_strings(self, parser):
        self.indent()
        max_len = 0
        for opt in parser.option_list:
            strings = self.format_option_strings(opt)
            self.option_strings[opt] = strings
            max_len = max(max_len, len(strings) + self.current_indent)
        self.indent()
        for group in parser.option_groups:
            for opt in group.option_list:
                strings = self.format_option_strings(opt)
                self.option_strings[opt] = strings
                max_len = max(max_len, len(strings) + self.current_indent)
        self.dedent()
        self.dedent()
        self.help_position = min(max_len + 2, self.max_help_position)
        self.help_width = self.width - self.help_position

    def format_option_strings(self, option):
        """Return a comma-separated list of option strings & metavariables."""
        metavar = option.metavar or option.dest.upper()
        return '%s=%s' % (option.name,metavar)

class IndentedHelpFormatter (HelpFormatter):
    """Format help with indented section bodies.
    """
    # NOTE optparse
    def __init__(self,
                 indent_increment=2,
                 max_help_position=24,
                 width=None,
                 short_first=1):
        HelpFormatter.__init__(
            self, indent_increment, max_help_position, width, short_first)

    def format_usage(self, usage):
        return _("usage: %s\n") % usage

    def format_heading(self, heading):
        return "%*s%s:\n" % (self.current_indent, "", heading)

class TitledHelpFormatter (HelpFormatter):
    """Format help with underlined section headers.
    """
    # NOTE optparse
    def __init__(self,
                 indent_increment=0,
                 max_help_position=24,
                 width=None,
                 short_first=0):
        HelpFormatter.__init__ (
            self, indent_increment, max_help_position, width, short_first)

    def format_usage(self, usage):
        return "%s  %s\n" % (self.format_heading(_("Usage")), usage)

    def format_heading(self, heading):
        return "%s\n%s\n" % (heading, "=-"[self.level] * len(heading))

SUPPRESS_HELP = "SUPPRESS"+"HELP"
NO_DEFAULT = ("NO", "DEFAULT")

def _repr(self):
    return "<%s at 0x%x: %s>" % (self.__class__.__name__, id(self), self)
# </borrowed>

NOTHING_FOUND = ("NOTHING","FOUND")

def split_keys(keys):
    """Returns list of keys resulting from keys argument.

        --- NO KEYS ---
        >>> split_keys( None )
        []
        >>> split_keys( [] )
        []

        --- STRINGS ---
        >>> split_keys( "key1" )
        ['key1']
        >>> split_keys( "key1,key2" )
        ['key1', 'key2']
        >>> split_keys( "key1.key2" )
        ['key1', 'key2']
        >>> split_keys( "key1.key2,key3" )
        ['key1', 'key2', 'key3']

        --- LISTS ---
        >>> split_keys( ['key1'] )          # single item
        ['key1']
        >>> split_keys( ['key1','key2'] )   # multiple items
        ['key1', 'key2']

        --- QUOTING ---
        These tests check that quotes can be used to protect '.' and ','.
        >>> split_keys( "'some.key1','some,key2'" )    # single ticks work 
        ['some.key1', 'some,key2']
        >>> split_keys( '"some,key1","some.key2"' )    # double ticks work
        ['some,key1', 'some.key2']
        >>> split_keys( '"some,key1",some.key2' )      # must quote everything
        Traceback (most recent call last):
        ConfigParserError: Keys not quoted properly.  Quotes must surround all keys.
        >>> split_keys( "some,key1,'some.key2'" )      # must quote everything
        Traceback (most recent call last):
        ConfigParserError: Keys not quoted properly.  Quotes must surround all keys.
        >>> split_keys( "key1,'some.key2'.key3" )      # must quote everything
        Traceback (most recent call last):
        ConfigParserError: Keys not quoted properly.  Quotes must surround all keys.
        >>> split_keys('DEFAULT')
        []
        >>> split_keys(['DEFAULT'])
        []
        """
    if (keys is None) or (keys == 'DEFAULT') or (keys == ['DEFAULT']):
        return []
    try:
        keys = keys.replace('"',"'")
        if "'" in keys:
            keys = keys.strip("'").split("','")
            for key in keys:
                if "'" in key:
                    IMPROPER_QUOTES = "Keys not quoted properly.  Quotes must surround all keys."
                    raise ConfigParserUserError(IMPROPER_QUOTES)
        else:
            keys = keys.replace('.',',').split(',')
    except AttributeError:
        pass
    return keys

def join_keys(keys,sep=','):
    """
    >>> join_keys(['key1'])
    'key1'
    >>> join_keys(['key1','key2'])
    'key1,key2'
    >>> join_keys(['key1','key2'],'.')
    'key1.key2'
    >>> join_keys(['key.1','key2'],'.')
    "'key.1','key2'"
    >>> join_keys(['key,1','key2'],'.')
    "'key,1','key2'"
    >>> join_keys([])
    'DEFAULT'
    """
    if not keys:
        return 'DEFAULT'
    mash = ''.join(keys)
    if '.' in mash or ',' in mash:
        quote = "'"
        sep = quote + ',' + quote
        return quote + sep.join(keys) + quote
    return sep.join(keys)

def split_paths(paths):
    """Returns list of paths resulting from paths argument.

        --- NO KEYS ---
        >>> split_paths( None )
        []
        >>> split_paths( [] )
        []

        --- STRINGS ---
        >>> split_paths( "path1" )
        ['path1']
        >>> split_paths( os.path.pathsep.join(["path1","path2"]) )
        ['path1', 'path2']
        >>> split_paths( "path.1,path.2" )
        ['path.1', 'path.2']

        --- LISTS ---
        >>> split_paths( ['path1'] )          # single item
        ['path1']
        >>> split_paths( ['path1','path2'] )   # multiple items
        ['path1', 'path2']
        """
    if paths is None:
        return []
    try:
        return paths.replace(',',os.path.pathsep).split(os.path.pathsep)
    except AttributeError:
        return paths

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#
#  E X C E P T I O N S
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

class ConfigParserError(Exception):
    """Exception associated with the cfgparse module"""
    pass
    
class ConfigParserAppError(Exception):
    """Exception due to application programming error"""
    pass
    
class ConfigParserUserError(Exception):
    """Exception due to user error"""
    pass
    
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#
#  K E Y S
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

class Keys(object):
    """Prioritizes and stores default configuration keys.
    
    This class is used to store default configuration keys for an instance
    of the Config class.  The different sources of keys are supported (stored)
    by the following methods of this class:

    add_cfg_keys -- configuration file specified default keys
    add_cmd_keys -- command line option keys
    add_env_keys -- environment variable keys
    
    The 'get' method returns a combined list of keys in the following order:
        application keys (passed when calling 'get' method)
        command line keys
        environment variable keys
        configuration file keys
        a 'DEFAULT' key (always present)

    Setup: modify os module to fake out environment variable gets
    >>> _getenv = os.getenv
    >>> def getenv(variable,default):
    ...     if variable == 'VAR12':
    ...         return 'env1,env2'
    ...     elif variable == 'VAR3':
    ...         return 'env3'
    ...     elif variable == 'VAR4':
    ...         return 'env4'
    ...     else:
    ...         return default
    >>> os.getenv = getenv

    Case 1: normal string lists of keys
    >>> k = Keys()
    >>> k.add_env_keys('VAR12,VAR3') # this has effect
    >>> k.add_env_keys('VAR_NONE')   # no effect
    >>> k.add_cfg_keys('cfg1,cfg2')
    >>> k.add_cmd_keys('cmd1.cmd2')
    >>> k.add_env_keys('VAR12')      # no effect (already read)
    >>> k.get('app1,app2')
    ['app1', 'app2', 'cmd1', 'cmd2', 'env1', 'env2', 'env3', 'cfg1', 'cfg2', 'DEFAULT']

    Case 2: extend lists using other key input flavors just to make sure each
            method uses split_keys()
    >>> k.add_env_keys(['VAR4'])     # this has effect
    >>> k.add_cfg_keys(['cfg3'])
    >>> k.add_cmd_keys(['cmd3'])
    >>> k.get(['app'])
    ['app', 'cmd1', 'cmd2', 'cmd3', 'env1', 'env2', 'env3', 'env4', 'cfg1', 'cfg2', 'cfg3', 'DEFAULT']

    Teardown: restore os module
    >>> os.getenv = _getenv
    """
    
    def __init__(self):
        """Initialize Keys Instance"""
        self.cmd_keys = []
        self.env_keys = []
        self.cfg_keys = []
        self.env_vars = []

    def __repr__(self):
        """Return string representation of object"""
        return ','.join(self.get([]))

    def add_cmd_keys(self,keys):
        """Store keys from command line interface

        keys -- list of keys (typically from the command line) to store.  May
            be a list of keys or a string with keys separated by commas.
            Use any value which evaluates False when no keys.
        """
        self.cmd_keys.extend(split_keys(keys))

    def add_env_keys(self,variables):
        """Store keys from invoking shell's environment variable

        variable -- (string) environment variable name from which to obtain
            keys to store
        """
        variables = split_keys(variables)
        for variable in variables:
            # only add keys from shell environment variable if we haven't already
            if variable not in self.env_vars:
                # save key variable name so we can't add same keys twice
                self.env_vars.append(variable)
                # if shell environment variable has a option save it
                keys = os.getenv(variable,None)
                if keys is not None:
                    self.env_keys.extend(split_keys(keys))

    def add_cfg_keys(self,keys):
        """Store keys from user's configuration file.

        keys -- list of keys (from user's configuration file) to store.  May
            be a list of keys or a string with keys separated by comma.
            Use any value which evaluates False when no keys.
        """
        self.cfg_keys.extend(split_keys(keys))

    def get(self,keys=None):
        """Return prioritized list of stored configuration keys

        keys -- list of differentiator keys.  May be a list of keys or a string
            with keys separated by commas.  Use any valid which evaluates
            False when no keys.
        """
        keys = split_keys(keys)
        return (keys + self.cmd_keys + self.env_keys + self.cfg_keys +
                ['DEFAULT'])

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#
#  O P T I O N   V A L U E
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

class Value(object):
    """Used to store option settings in the blended option dictionary.
    Needed to be able to tie the option setting back to the configuration
    file for better error reporting and for round trip get/set/write
    capability."""
    def __init__(self,value,parent,section_keys):
        """Initializes instance."""
        self.value = value
        self.parent = parent
        self.section_keys = section_keys

    def set(self,value):
        """Sets option setting to 'value' argument passed in.  
        
        By default configuration file parsers to do not support round trip.
        If they do they should subclass Value() and override this method
        """
        self.value = value

    def get_roots(self):
        return ["File: %s" % self.parent.get_filename(),
                "Section: [%s]" % join_keys(self.section_keys,'.')]
        
    def __str__(self):
        """Returns string representation of the setting."""
        return str(self.value)

    __repr__ = _repr

    def get(self):
        """Returns the option setting."""
        return self.value

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#
#  O P T I O N
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

class Option(object):
    """Options added to configuration parser are an instance of this class."""

    def __init__(self,**kwargs):
        """Instance initializer.
        Arguments:
        kwargs -- dictionary with keys parser,name,type,default,help,check,keys,
                  choices (see add_option of OptionContainer)
        """
        self.__dict__.update(kwargs)
        if self.dest is None:
            self.dest = self.name
        if self.type not in self.conversions:
            TYPE_DOES_NOT_EXIST = "type '%s' is not valid" % self.type
            raise ConfigParserAppError(TYPE_DOES_NOT_EXIST)
        # help cross reference for options partnered with OptionParser
        self._help_xref = ""
        self.note = None

    def __str__(self):
        """Returns string representation of the option."""
        return self.name

    __repr__ = _repr

    def add_note(self,note):
        """Adds 'note' argument text to configuration parser help text and 
        to error messages associated with this option."""
        self.parser.add_note(note)
        self.note = note

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #  Get
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def _get(self,keys):
        # Read any pending configuration files at the top level in order to
        # pick up user's default keys in those files.
        self.parser.parse_pending_cfg([])

        keys = split_keys(keys) + self.keys
        keys = self.parser.keys.get(keys)

        # Get the option's dictionary from the configuration parser so that
        # any pending configuration files that are needed are read.
        option = self.parser.get_option_dict(self.name,keys)

        # When keys are given as an argument, we don't have the constraints
        # of an exact match like a section.  Instead we use the default
        # key list (highest priority key first) to walk the option
        # dictionary.  At each level of the dictionary we look for the
        # highest priority key and if it exists we move down a level
        # otherwise the remaining keys are checked in order of priority.

        def walk_option(option):
            if option.__class__ is dict:
                for key in keys:
                    if key in option:
                        v = walk_option(option[key])
                        if v.__class__ is not dict:
                            return v
            if isinstance(option,Value):
                return option
            else:
                return NOTHING_FOUND

        return walk_option(option)
    
    def get(self,keys=[],errors=None):
        """Returns option value associated with 'keys' argument or options
        option value using 'keys' argument (in combination with other keys).

        keys -- name of keys to obtain option value from

        Note:
           If option is partnered with an optparse option and that option
           is present, the optparse option will take priority and be returned.
        """

        warnings = []
        option = NOTHING_FOUND

        def convert(value,option_help):
            # Do conversion to the type application specified
            value,warning = self.conversions[self.type](self,value)
            # Do final check using application check function if supplied
            if not warning and self.check is not None:
                value,warning = self.check(value)
            if warning:
                try:
                    warnings.extend(option_help.get_roots())
                except AttributeError:
                    warnings.append(option_help)
                warnings.append(warning)
            return value

        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
        # Priority 1: Get option from optparse partner (command line)
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

        if self.dest in self.parser.optpar_option_partners:
            option = getattr(self.parser.optparser_options,self.dest,None)
            if option is None:
                option = NOTHING_FOUND
            else:
                option = convert(option,'command line option')

        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
        # Priority 2: Get a default option
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

        if option is NOTHING_FOUND and not warnings:

            option = self._get(keys)
        
            if option is not NOTHING_FOUND:
                value = option.get()
                option = convert(value,option)

        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
        # Priority 3: Use default specified when adding the option
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

        if option is NOTHING_FOUND and not warnings:
            if self.default is not NO_DEFAULT:
                option = self.default
            else:
                warnings.append('No valid default found.')
                keys = split_keys(keys) + self.keys
                keys = self.parser.keys.get(keys)
                warnings.append('keys=%s' % ','.join(keys))
                    
        if warnings:
            lines = ['Option: %s' % self.name] + warnings
            lines = '\n'.join(lines) + '\n'
            if errors is not None:
                errors.append(lines)
            else:
                # not coming back
                self.parser.write_errors([lines])
        
        return option

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #  Conversions
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def convert_choice(self,value):
        if value in self.choices:
            return value,None
        else:
            choices = str(self.choices).strip('[]()')
            warning = "Invalid choice '%s', must be one of: %s" % (value,choices) 
            return None,warning

    def convert_complex(self,value):
        try:
            return complex(value),None
        except ValueError:
            return None,"Cannot convert '%s' to a complex number" % (value)

    def convert_float(self,value):
        try:
            return float(value),None
        except ValueError:
            return None,"Cannot convert '%s' to a float" % (value)

    def convert_int(self,value):
        try:
            return int(value),None
        except ValueError:
            return None,"Cannot convert '%s' to an integer" % (value)

    def convert_long(self,value):
        try:
            return long(value),None
        except ValueError:
            return None,"Cannot convert '%s' to a long" % (value)

    def convert_string(self,value):
        try:
            return str(value),None
        except ValueError:
            return None,"Cannot convert '%s' to a string" % (value)

    def convert_nothing(self,value):
        return value,None

    conversions = {
        'choice'  : convert_choice,
        'complex' : convert_complex,
        'float'   : convert_float,
        'int'     : convert_int,
        'long'    : convert_long,
        'string'  : convert_string,
        None      : convert_nothing,
        }
    
    def set(self,value,cfgfile=None,keys=None):
        value = str(value)
        if cfgfile:
            if keys is not None:
                keys = split_keys(keys)
            else:
                keys = self.keys
            cfgfile.set_option(self.name,value,keys,self.help)
        else:
            keys = split_keys(keys) + self.keys
            keys = self.parser.keys.get(keys)
    
            option = self._get(keys)
        
            if option is NOTHING_FOUND:
                NOTHING_TO_SET = '\n'.join([
                    'ERROR: No option found',
                    'option name: %s' % self.name,
                    'keys: %s' % keys])
                raise ConfigParserUserError(NOTHING_TO_SET)
            else:
                option.set(value)
            cfgfile = option.parent
        return cfgfile
    
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#
#  O P T I O N   C O N T A I N E R   B A S E   C L A S S E S
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

class OptionContainer(object):

    OptionClass = Option    

    def __init__(self,description):
        self.option_list = []
        self.set_description(description)

    def set_description(self, description):
        self.description = description

    def get_description(self):
        return self.description

    def add_option(self,name,help=None,type=None,choices=None,dest=None,metavar=None,default=NO_DEFAULT,check=None,keys=None):
        """
            name -- configuration file option name (used same as optparse)
            type -- choices similar to optparse (used same as optparse)
            default -- default value (used same as optparse)
            help -- help string (used same as optparse)
            dest -- option database attribute name (used same as optparse)
            check -- check function
            keys -- name of keys to obtain option from
            choices -- list of choices (used same as optparse)
            metavar -- FUTURE
        """
        if dest is None:
            dest = name

        kwargs = {
            'parser' : self.parser,
            'name' : name,
            'type' : type,
            'help' : help,
            'dest' : dest,
            'check' : check,
            'keys' : split_keys(keys),
            'choices' : choices,
            'metavar' : metavar,
            'default' : default}
        
        option = self.OptionClass(**kwargs)
        self.parser.master_option_list.append(option)
        self.parser.master_option_dict[dest] = option
        self.option_list.append(option)
        return option

    # <borrowed file="Lib/optparse.py" version="python2.4" modified="yes">
    
    def format_option_help(self, formatter):
        if not self.option_list:
            return ""
        result = []
        for option in self.option_list:
            if not option.help == SUPPRESS_HELP:
                result.append(formatter.format_option(option))
        return "".join(result)

    def format_description(self, formatter):
        return formatter.format_description(self.get_description())

    def format_help(self, formatter):
        result = []
        if self.description:
            result.append(self.format_description(formatter))
        if self.option_list:
            result.append(self.format_option_help(formatter))
        return "\n".join(result)
    # </borrowed>
    
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#
#  O P T I O N   G R O U P
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

class OptionGroup(OptionContainer):
    def __init__(self,parser,title,description):
        OptionContainer.__init__(self,description)
        self.parser = parser
        self.title = title

    # <borrowed file="Lib/optparse.py" version="python2.4" modified="yes">
    def set_title (self, title):
        self.title = title

    # -- Help-formatting methods ---------------------------------------

    def format_help (self, formatter):
        result = formatter.format_heading(self.title)
        formatter.indent()
        result += OptionContainer.format_help(self, formatter)
        formatter.dedent()
        return result
    # </borrowed>
        

class ConfigFile(object):
    def __init__(self,cfgfile,content,keys,parent,parser):
        
        p,n = os.path.split(cfgfile)
        try:
            p = os.path.join(parent.path,p)
        except AttributeError:
            pass
        p = os.path.abspath(p)
        
        self.path = p
        self.filename = n
        self.content = content
        self.underkeys = keys
        self.parent = parent
        self.parser = parser

        self.parsed = False

    def get_filename(self):
        return os.path.join(self.path,self.filename)
        
    def __str__(self):
        return os.path.join(self.path,self.filename)

    __repr__ = _repr

    def get_as_str(self):
        content = self.content
        if content is None:
            cfgfile = os.path.join(self.path,self.filename)
            f = open(cfgfile)
            content = f.read()
            f.close()
        else:
            try:
                content = self.content.read()
            except AttributeError:
                pass
        return content
      
    def parse_if_unparsed(self):
        if not self.parsed:

            # The parent is important in that it is used error messages but more
            # importantly when getting ready to read a configuration script we
            # must set the current directory of the parent so relative path
            # specification of any configuration file works out.
            try:
                parent_path = self.parent.path
            except AttributeError:
                parent_path = os.getcwd()
                                        
            # Save so we can restore after we are done
            cwd = os.getcwd()

            # Make sure file is present
            cfgfile = os.path.join(self.path,self.filename)
            if not self.content and not os.path.exists(cfgfile):
                lines = ["File not found: '%s'" % cfgfile]
                # remember, top level configuration file parent is just the
                # current working directory when ConfigParser was instantiated
                # FUTURE parent info in here too
                FILE_NOT_FOUND = '\n'.join(lines)
                raise ConfigParserUserError(FILE_NOT_FOUND)
                
            # Change the current working directory to where the configuration 
            # script is (to accomodate Python configuraton scripts so that it
            # can use os.getcwd() to determine its location).
            os.chdir(self.path)
                
            self.parse()
            
            # Restore
            os.chdir(cwd)

            # Mark it as done so it isn't parsed twice
            self.parsed = True


class ConfigFilePy(ConfigFile):

    def parse(self):

        underkeys = self.underkeys
        parser = self.parser

        # Parsing can be easy!
        options = {}
        if self.content is None:        
            cfgfile = os.path.join(self.path,self.filename)
            execfile(cfgfile,options)
        else:
            exec self.get_as_str() in options

        # Update the keys.  "KEYS_VARIABLE" option used to specify the
        # environment variable that holds additional default keys, if
        # present get keys from the environment using it.  If reading
        # configuration file that is being included under a key, don't
        # bother with its keys because it would get too confusing.
        if not underkeys:
            try:
                parser.keys.add_env_keys(options['KEYS_VARIABLE'])
                del options['KEYS_VARIABLE']
            except KeyError:
                pass
            try:
                parser.keys.add_cfg_keys(options['KEYS'])
                del options['KEYS']
            except KeyError:
                pass

        try:
            CONFIG_FILES = options['CONFIG_FILES']
            del options['CONFIG_FILES']
        except KeyError:
            CONFIG_FILES = None

        def merge_option(value,section_keys):
            if value.__class__ is dict:
                for key in value:
                    merge_option(value[key],section_keys+[key])
            else:
                valueobj = Value(value,self,section_keys)
                parser.merge_option(name,valueobj,underkeys+section_keys)
            
        # Merge all options that don't start with "_" into the options
        for name,value in options.items():
            if not name.startswith('_'):
                merge_option(value,[])

        # Process the "CONFIG_FILES" option used to merge in configuration
        # from other files. Users specify a comma separated (string)
        # listing of configuration file names or a dictionary of (and
        # optionally - of dictionaries of) file name strings.
        def add_files(value,under):
            if isinstance(value,dict):
                for k,v in value.iteritems():
                    add_files(v,under+[k])
            else:
                for cf in split_paths(value):
                    parser.add_file(cf,keys=under,parent=self)

        if CONFIG_FILES:
            add_files(CONFIG_FILES,underkeys)

class ConfigFileIni(ConfigFile):
  
    def _read(self):
    
        try:
            self._already_read
            return
        except AttributeError:
            self._already_read = True
                
        underkeys = self.underkeys
        option_parser = self.parser
        marker_fmt = '{{{%s-(?P<id>\d+)}}}'
        _self = self

        class BaseClass(object):
            def __init__(self,matchobj):
                self.text = matchobj.group('text')
                self.num = len(self.objects)
                self.objects.append(self)
            def restore(self):
                return self.text

        class Line(BaseClass):
            pass
                
        class Block(BaseClass):
            objects = []
            find_re = re.compile('<b>(?P<text>.*?)</b>',re.DOTALL)

        class Verbatim(BaseClass):
            objects = []
            find_re = re.compile('<v>(?P<text>.*?)</v>',re.DOTALL)

        class Comment(BaseClass):
            objects = []
            find_re = re.compile('(?P<text>[ \t]*[#;].*)')

        class OptionPair(Value):
            # OptionPair must subclass Value() because it is being submitted into  the
            # parser options dictionary (all options in the dictionary must be a 
            # subclass of Value).  All things equal this would subclass BaseClass()
            # but it implements all that functionality anyways.
            objects = []
            find_re = re.compile('(?P<indent>[ \t]*)(?P<name>.+?)(?P<sep>\s*=\s*)(?P<value>.*)')
            section = None
            def __init__(self,matchobj):
                section_keys = OptionPair.section.keys
                # get the name right            
                name = matchobj.group('name')
                self.extended_name = name
                if '[' in name:
                    name,keys = name.strip(']').split('[')
                    section_keys = section_keys + split_keys(keys)
                self.name = name
                self.indent = matchobj.group('indent')
                self.sep = matchobj.group('sep')
                value = matchobj.group('value')
                self.valueplus = value
                try:
                    value = restore(Comment,value)
                    value = restore(Block,value)
                    value = restore(Verbatim,value)
                    self.linenum = re.findall(marker_fmt % 'Line',value)[0]
                except IndexError:
                    self.linenum = 'new'
                self.num = len(self.objects)
                self.objects.append(self)
                self.section = OptionPair.section
                self.section.options[self.extended_name] = self
                # The following are needed for Value() functionality
                self.parent = _self
                self.section_keys = section_keys
                # self.value will be set later (can't now because value may contain
                # interpolations which cannot be expanded until all options are read
                # for this section
            def get_roots(self):
                return Value.get_roots(self) + ["Line: %s" % self.linenum]
            def set(self,value):
                Value.set(self,value)
                value = [value]
                def hit(matchobj):
                    value.append(matchobj.group(0))
                regexp = re.compile(marker_fmt % 'Comment')
                regexp.sub(hit,self.valueplus)
                self.valueplus = ''.join(value)
            def restore(self):
                return ''.join([self.extended_name,self.sep,self.valueplus])
            def expand(self,levellist=[]):
                levellist = levellist + [self.name]
                if len(levellist) > 10:
                    lines = self.get_roots()
                    lines.append("Interpolation: %s" % ' << '.join(levellist))
                    lines.append("Maximum nesting level exceeded.")
                    MAX_NESTING_LEVEL_EXCEEDED = '\n' + '\n'.join(lines)
                    raise ConfigParserUserError(MAX_NESTING_LEVEL_EXCEEDED)
                try:
                    return self.value
                except AttributeError:
                    pass
                value = remove(Comment,self.valueplus)
                value = remove(Line,value)
                value = restore(Block,value.strip(' \t'))
                value = remove(Line,value)
                # @future [ABSPATH] value = value.replace('%(ABSPATH(','%_(ABSPATH(')
                regexp = re.compile('%\((?P<name>.*?)\)s')
                def hit(matchobj):
                    name = matchobj.group('name')
                    try:
                        return self.section.options[name].expand(levellist)
                    except KeyError:
                        try:
                            return Section.default.options[name].expand(levellist)
                        except KeyError:
                            lines = self.get_roots()
                            lines.append("Interpolation: %s" % ' << '.join(levellist+[name]))
                            lines.append("'%s' not found in section or in [DEFAULT]." % name)
                            INTERPOLATION_ERROR = '\n' + '\n'.join(lines)
                            raise ConfigParserUserError(INTERPOLATION_ERROR)
                value = regexp.sub(hit,value)
                # @future [ABSPATH] regexp = re.compile(r'%_\(ABSPATH\((.*?)\)\)s')
                # def hit(matchobj):
                #     return os.path.abspath(matchobj.group(1))
                # value = regexp.sub(hit,value)
                self.value = remove(Line,restore(Verbatim,value))
                return self.value
                
        class Section(BaseClass):
            objects = []
            find_re = re.compile('(?P<text>\n\[(?P<name>.*?)\].*?(?=\n\[))',re.DOTALL)
            default = None
            def __init__(self,matchobj):
                self.options = {}
                name = matchobj.group('name')
                self.name = name
                keys = split_keys(name)
                if keys == ['DEFAULT']:
                    keys = []
                if not keys:
                    Section.default = self
                self.keys = keys
                OptionPair.section = self
                self.text =  collapse(OptionPair,matchobj.group(0))
                self.num = len(self.objects)
                self.objects.append(self)
            def add_option(self,name,value,help):
                if help:
                    helplines = textwrap.fill(help,77).split('\n')
                    lines = ['# %s' % line for line in helplines]
                else:
                    lines = []
                lines.append('%s = %s' % (name,value))
                OptionPair.section = self
                block = collapse(Comment,'\n'+'\n'.join(lines))
                self.text +=  collapse(OptionPair,block)
                option = OptionPair.objects[-1]
                underkeys = _self.underkeys + option.section_keys
                if not underkeys:
                    underkeys = ['DEFAULT']
                # submit new value to parser
                _self.parser.merge_option(name,option,underkeys)
                return option
                                                
        def collapse(SubClass,text):
            marker_fmt = '{{{%s-%%d}}}' % (SubClass.__name__)
            def hit(matchobj):
                return marker_fmt % SubClass(matchobj).num
            return SubClass.find_re.sub(hit,text)

        def remove(SubClass,text):
            return re.compile(marker_fmt % SubClass.__name__).sub('',text)

        def restore(SubClass,text):
            def hit(matchobj):
                return SubClass.objects[int(matchobj.group('id'))].restore()
            return re.compile(marker_fmt % SubClass.__name__).sub(hit,text)

        text = self.get_as_str()
        lines = []
        i = 1
        for line in text.split('\n'):
            lines.append(line + ('{{{Line-%d}}}' % i))
            i += 1
        text = '\n'.join(lines)
        text = '\n[DEFAULT]\n#_START_MARKER_\n%s\n[' % text
        text = collapse(Block,text)
        text = collapse(Verbatim,text)
        text = collapse(Comment,text)
        text = collapse(Section,text)
        
        self._OptionPair = OptionPair
        self._Line = Line
        self._Comment = Comment
        self._Block = Block
        self._Verbatim = Verbatim
        self._Section = Section
        self._collapse = collapse 
        self._restore = restore
        self._remove = remove
        self.text = text
            
    def parse(self):
        self._read()
        for option in self._OptionPair.objects:
            name = option.name
            underkeys = self.underkeys + option.section_keys
            value = option.expand()
            if name == '<include>':
                for cf in split_paths(value):
                    self.parser.add_file(cf,keys=underkeys,parent=self)
                continue
            if not underkeys:
                if name == '<keys>':
                    self.parser.keys.add_cfg_keys(split_keys(value))
                    continue
                if name == '<keys_variable>':
                    self.parser.keys.add_env_keys(value)
                    continue
                underkeys = ['DEFAULT']
            # call expand method to get .value attribute set
            self.parser.merge_option(name,option,underkeys)

    def set_option(self,name,value,keys=None,help=None):
        self._read()
        value = str(value)
        keys = split_keys(keys)
        found = False
        for option in self._OptionPair.objects:
            if name==option.name and keys == option.section_keys:
                option.set(value)
                found = True
        if not found:
            Section = self._Section
            for section in Section.objects:
                if keys == section.keys:
                    found = True
                    section.add_option(name,value,help)
            if not found:
                block = '\n\n[%s]\n\n[\n' % join_keys(keys,'.')
                self.text = '%s%s' % (self.text[:-2],self._collapse(Section,block))
                section = self._Section.objects[-1]
                section.add_option(name,value,help)
            
    def write(self,file):
        self._read()
        
        restore = self._restore
        content = self.text
        content = restore(self._Section,content)
        content = restore(self._OptionPair,content) + '\n'
        content = restore(self._Comment,content)
        content = restore(self._Block,content)
        content = restore(self._Verbatim,content)
        content = self._remove(self._Line,content)
        content = content.split('\n#_START_MARKER_\n')[1][:-3]
        
        try:
            file.write(content)
        except AttributeError:
            f = open(file,'w')
            f.write(content)
            f.close()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#
#  C O N F I G U R A T I O N   P A R S E R
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

class ConfigParser(OptionContainer):

    KeysClass = Keys
    OptionGroupClass = OptionGroup
    
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #  Initializer
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def __init__(self,description=None,allow_py=False,formatter=None,exception=False):
        """
        description -- Introductory text placed above configuration option
            help text.
        allow_py -- Set to True to allow Python based configuraton files
            to be executed.  Defaults to False.  Enabling this feature
            poses a potential security hole for your application.
        formatter -- Controls configuration option help text style.  Set
            to either the IndentedHelpFormatter or TitledHelpFormatter
            classes found in cfgparse module (or a subclass of either).
        exception -- set to True to raise ConfigParserUserError exception
            when configuration error occurs (due to user error).  Omitting
            or setting to False will write error message to sys.stderr.
            Set to an exception class to raise that exception when a user
            configuration file error occurs.
        """
        OptionContainer.__init__(self,description)

        self.exception = exception
        
        # Needed because shares same base class as an option group
        # (option group constructor initializes parser using an arg).
        self.parser = self

        self.option_dicts = {}

        self.option_groups = []
        self.optpar_option_partners = {}
        
        self.master_option_list = []
        self.master_option_dict = {}

        if formatter is None:
            formatter = IndentedHelpFormatter()
        self.formatter = formatter
        self.formatter.set_parser(self)

        self.notes = []
        
        # Set up database of option selection keys        
        self.keys = self.KeysClass()

        # Create database to store information on those configuration files
        # to be read later (configuration files under keys are not read until
        # all of the keys in which it is under are active.
        self._pending = []

        # Since it introduces a security risk, only allow Python based 
        # configuration files if application explicitly sets this True.
        self.allow_python_cfg = allow_py

        self.optparse_dests = {}

    def add_optparse_keys_option(self,option_group,switches=('-k','--keys'),dest='cfgparse_keys',help="Comma separated list of configuration keys."):
        """Adds configuration file keys list option to optparse object."""
        self.optparse_dests['keys'] = dest
        option_group.add_option(dest=dest,metavar='LIST',help=help,*switches)
        
    def add_optparse_files_option(self,option_group,switches=('--cfgfiles',),dest='cfgparse_files',help="Comma separated list of configuration files."):
        """Adds configuration file list option to optparse object."""
        self.optparse_dests['files'] = dest
        option_group.add_option(dest=dest,metavar='LIST',help=help,*switches)

    def add_optparse_help_option(self,option_group,switches=('--cfghelp',),dest='cfgparse_help',help="Show configuration file help and exit."):
        """Adds configuration file help option to optparse object."""
        self.optparse_dests['help'] = dest
        option_group.add_option(dest=dest,action='store_true',help=help,*switches)

    def add_env_file(self,var,keys=[]):
        """Adds configuration file specified by environment variable setting.
        Arguments:
        var -- name of environment variable holding configuration file name 
        keys -- section key list to place configuration file options settings under
        """
        # Add configuration files specified by an environment variable
        # if application script specified it.  (Don't read right away,
        # rather hold them in pending database until they are needed
        # because adding options causes option_dicts to be set with a 
        # default for the option destination.
        f = os.getenv(var,None)
        if f:
            f = self.add_file(cfgfile=f,keys=keys)
        else:
            f = None
        return f

    def get_option(self,dest):
        """Returns option object previously added.
        Arguments:
        dest -- destination attribute name of option
        """
        opt = self.master_option_dict.get(dest,None)
        if opt is None:
            OPTION_NOT_FOUND = '\n'.join([
                'ERROR: No option found',
                'option dest: %s' % dest])
            raise ConfigParserAppError(OPTION_NOT_FOUND)
        return opt

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #  Adding Option Groups (adding options handled by base class)
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def add_option_group(self,title,description=None):
        option_group = self.OptionGroupClass(self,title,description)
        self.option_groups.append(option_group)
        return option_group

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #  Pending Configuration
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def get_option_dict(self,name,keys):
        self.parse_pending_cfg(keys)
        return self.option_dicts.get(name,NOTHING_FOUND)

    def parse_pending_cfg(self,keys=[],read_all=False):
        """
        read_all -- Set to True to read all configuration files up front.  
            Defaults to reading "on the fly" as the configuration files are
            needed."""
        # Read any pending configuration files that could possibly effect the
        # setting about to be retrieved.  Note, it was decided that if the
        # pending configuration file's under keys are all in the key list
        # computed above it will be installed right away.  The other
        # alternative is to try retrieving the setting with the highest
        # priority key alone (first reading any pending configuration files
        # that are under that key), then if that fails try retrieving the
        # setting with the top two highest priority keys (again first reading
        # any pending configuration files that are under either or both of the
        # keys), and repeating this process for each key in the list until a
        # setting is found.  This would have the benefit of only reading
        # pending configuration files when it is absolutely necessary but at
        # cost of performance and more difficult to explain how it works.
        keys = split_keys(keys)
        d = []
        while self._pending:
            underkeys,cfgfileobj = self._pending.pop(0)
            underkeys = split_keys(underkeys)
            parse_it = read_all
            if not parse_it:
                for key in underkeys:
                    if key not in keys:
                        d.append((underkeys,cfgfileobj))
                        break
                else:
                    parse_it = True
            if parse_it:
                cfgfileobj.parse_if_unparsed()
        self._pending = d

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    FileClasses = {'py' : ConfigFilePy, 'ini': ConfigFileIni, 'default' : ConfigFileIni}

    def add_file(self,cfgfile=None,content=None,type=None,keys=[],parent=None):
        """
        Adds configuration file to parser.  Note, file is not read until parse 
        or get_option method is called (and even then it may not be read if any
        keys in the keys list are not in the keys being used to parse).
        
        cfgfile -- either the filename or a file stream, defaults to None (see table below)
        content -- either file contents string or file stream, defaults to None (see table below)
        type -- set to either 'py', 'ini', or None (default) to control file parser used.   
            When set to None, filename extension is used to determine parser to use.  'py'
            interprets the file as Python code.  Otherwise the 'ini' style parser is used.
        keys -- key list that all options in the configuration file will 
            be placed under when the file is read.
        parent -- Not intended to be used by the public

        The following table summarizes the legal combinations of the cfgfile and
        arguments and resulting file name and contents utilized.
                    
        cfgfile   content  result (when configuration is parsed)
        --------  -------  -----------------------------------------------------------
        filename  None     file is opened and contents read
        stream    None     stream contents are read, filename is stream name attribute
        filename  stream   stream contents are read, filename is cfgfile argument
        filename  string   both filename and content are used as is
        """

        if isinstance(cfgfile,str):
            n = cfgfile
            c = content
        elif hasattr(cfgfile,'name'):
            n = cfgfile.name
            c = cfgfile
        elif isinstance(content,str):
            n = 'heredoc'
            c = content
        elif hasattr(content,'read'):
            n = 'stream'
            c = content
        else:
            ARGUMENT_CONFICT = "Illegal combination of 'cfgfile' and 'content' arguments"
            raise ConfigParserAppError(ARGUMENT_CONFICT)
        
        uk = split_keys(keys)

        if type is None:
            # calculate type (lower case extension)
            type = os.path.splitext(n)[1][1:].lower()

        if type == 'py' and not self.allow_python_cfg:
            return None

        FileClass = self.FileClasses.get(type)
        if FileClass is None:
            FileClass = self.FileClasses['default']

        fileobj = FileClass(cfgfile=n,content=c,keys=uk,parent=parent,parser=self)
        self._pending.append((uk,fileobj))
        return fileobj

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #  Read Configuration File Utilities
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def merge_option(self,name,value,keys):
        """ Merge value (under keys) into options dictionary.

        name -- option name
        value -- value to assign option (may be a dictionary or a option)
        keys -- list of keys to place value in options dict under
        """
        
        # Add the option name to the key list so we can start walking at
        # the top level of the options dictionary.
        keys = [name] + keys
        option_dicts = self.option_dicts
        # Move through the options dictionary using the keys we are
        # supposed to place the value under creating dictionaries and keys 
        # that aren't already present.
        for key in keys[:-1]:
            if key in option_dicts:
                if option_dicts[key].__class__ is not dict:
                    option_dicts[key] = dict(DEFAULT=option_dicts[key])
            else:
                option_dicts[key]={}
            option_dicts = option_dicts[key]
        option_dicts[keys[-1]] = value

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #  Option Parsing (not configuration file parsing)
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def write_errors(self,errors):
        CFGPARSE_USER_ERROR = '\n' + '\n'.join(errors)
        if not self.exception:
            sys.stderr.write("ERROR: Configuration File Parser\n")           
            sys.stderr.write(CFGPARSE_USER_ERROR)
            self.system_exit()
        else:
            if self.exception is True:
                UserError = ConfigParserUserError
            else:
                UserError = self.exception
            raise UserError(CFGPARSE_USER_ERROR)

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #  Option Parsing
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def parse(self,optparser=None,args=None,read_all=False):
        """Partners the option parser and the configuration parser together
        read_all -- Set to True to read all configuration files up front.  
            Defaults to reading "on the fly" as the configuration files are
            needed.
        """

        if optparser:
            # Marry up type, help, choices attributes between option parser and
            # configuration parser options.
            self.marry_options(optparser)

            # Parse command line arguments
            options, args = optparser.parse_args(args)
            self.optparser_options = options

            # generate help if requested from the command line
            help_dest = self.optparse_dests.get('help')
            if help_dest and getattr(options,help_dest):
                self.print_help()
                self.system_exit()

            # add command line keys
            keys_dest = self.optparse_dests.get('keys')
            if keys_dest:
                self.keys.add_cmd_keys(getattr(options,keys_dest))

            # add command line configuration files (must hold it as other configuration
            # files may be pending that should be read first)
            files_dest = self.optparse_dests.get('files')
            if files_dest:
                cfgfiles = getattr(options,files_dest)
                for cf in split_paths(cfgfiles):
                    self.add_file(cfgfile=cf,keys=[])
        else:
            class ConfigOptions(object):
                pass
            options = ConfigOptions()

        self.parse_pending_cfg([],read_all)

        # Go through each option in the configuration options and add them
        # to options object.
        errors = []
        for option in self.master_option_list:
            setattr(options,option.dest,option.get(errors=errors))
        if errors:
            self.write_errors(errors)

        if optparser:
            return options, args
        else:
            return options

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def marry_options(self,optparser):
        # create mapping: dest -> [optpar options]
        optpar_lookup = {}
        for option in optparser.option_list:
            if option.dest:
                optpar_lookup.setdefault(option.dest,[]).append(option)
        for group in optparser.option_groups:
            for option in group.option_list:
                if option.dest:
                    optpar_lookup.setdefault(option.dest,[]).append(option)
        self.optpar_option_partners = optpar_lookup

        # we are guarenteed no duplicate destinations with a configuration parser
        for cfgpar_option in self.master_option_list:
            optpar_options = optpar_lookup.get(cfgpar_option.dest,[])
            for optpar_option in optpar_options:
                for attrname in ['metavar','type','choices','help']:
                    cfgpar_attr = getattr(cfgpar_option,attrname)
                    optpar_attr = getattr(optpar_option,attrname)
                    if cfgpar_attr is None:
                        cfgpar_attr = optpar_attr
                        setattr(cfgpar_option,attrname,cfgpar_attr)
                if cfgpar_option.help == SUPPRESS_HELP:
                    continue
                try:
                    # remove anything we've added previously
                    optpar_option.help = optpar_option.help.replace(optpar_option._cfgparse_help,'')
                except AttributeError:
                    # must not have modified it previously
                    pass
                help = "  See also '%s' option in configuration file help." % (cfgpar_option.name)
                if not optpar_option.help:
                    help = help.strip()
                    optpar_option.help = ''
                optpar_option.help = optpar_option.help + help
                optpar_option._cfgparse_help = help
            if cfgpar_option.help == SUPPRESS_HELP:
                continue
            if cfgpar_option.help is None:
                cfgpar_option.help = ''
            try:
                # remove anything we've added previously
                cfgpar_option.help = cfgpar_option.help.replace(cfgpar_option._help_xref,'')
            except AttributeError:
                # must not have modified it previously
                pass
            switches = '/'.join([str(o) for o in optpar_options])
            if switches:
                help = "  See also '%s' command line switch." % (switches)
                if not cfgpar_option.help:
                    help = help.strip()
                cfgpar_option.help = cfgpar_option.help + help
                cfgpar_option._help_xref = help
                            
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def marry_attribute(self,attrname,cfgpar_option,optpar_option):
        cfgpar_attr = getattr(cfgpar_option,attrname)
        optpar_attr = getattr(optpar_option,attrname)
        if cfgpar_attr is None:
            cfgpar_attr = optpar_attr
            setattr(cfgpar_option,attrname,cfgpar_attr)
            
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #  Help
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    # <borrowed file="Lib/optparse.py" version="python2.4" modified="yes">
    def format_option_help(self, formatter=None):
        if formatter is None:
            formatter = self.formatter
        formatter.store_option_strings(self)
        result = []
        result.append(formatter.format_heading(_("Configuration file options")))
        formatter.indent()
        if self.option_list:
            result.append(OptionContainer.format_option_help(self, formatter))
            result.append("\n")
        for group in self.option_groups:
            result.append(group.format_help(formatter))
            result.append("\n")
        formatter.dedent()
        # Drop the last "\n", or the header if no options or option groups:
        return "".join(result[:-1])

    def format_help(self, formatter=None):
        if formatter is None:
            formatter = self.formatter
        result = []
        if self.description:
            result.append(self.format_description(formatter) + "\n")
        result.append(self.format_option_help(formatter))
        return "".join(result)

    def print_help(self, file=None):
        """print_help(file : file = stdout)

        Print an extended help message, listing all options and any
        help text provided with them, to 'file' (default stdout).
        """
        if file is None:
            file = sys.stdout
        
        file.write(self.format_help())

        if self.notes:
            file.write('\nNotes:\n%s\n'%'\n'.join(self.notes))
    
    # </borrowed>
    
    def add_note(self,note):
        self.notes.append(note)

    def system_exit(self):
        sys.exit()


def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()

