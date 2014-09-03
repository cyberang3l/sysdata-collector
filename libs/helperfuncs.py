# Copyright (C) 2014  Vangelis Tasoulas <vangelis@tasoulas.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import sys
import traceback
import logging
import platform
import subprocess
import datetime
try:
    from collections import OrderedDict
except ImportError:
    # python 2.6 or earlier, use backport
    from ordereddict import OrderedDict

__all__ = [
    'quick_regexp', 'print_', 'get_dict_keys_by_value',
    'flatten_nested_dicts', 'is_number', 'get_kernel_version',
    'trim_list', 'strip_string_list', 'split_strip',
    'executeCommand', 'LOG'
]

LOG = logging.getLogger('default.' + __name__)

#----------------------------------------------------------------------
class executeCommand(object):
    """
    Custom class to execute a shell command and
    provide to the user, access to the returned
    values
    """

    def __init__(self, args=None, isUtc=True):
        self._stdout = None
        self._stderr = None
        self._returncode = None
        self._timeStartedExecution = None
        self._timeFinishedExecution = None
        self._args = args
        self.isUtc = isUtc
        if(self._args != None):
            self.execute()

    def execute(self, args=None):
        if(args != None):
            self._args = args

        if(self._args != None):
            if(self.isUtc):
                self._timeStartedExecution = datetime.datetime.utcnow()
            else:
                self._timeStartedExecution = datetime.datetime.now()
            p = subprocess.Popen(self._args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if(self.isUtc):
                self._timeFinishedExecution = datetime.datetime.utcnow()
            else:
                self._timeFinishedExecution = datetime.datetime.now()
            self._stdout, self._stderr = p.communicate()
            self._returncode = p.returncode
            return 1
        else:
            self._stdout = None
            self._stderr = None
            self._returncode = None
            return 0

    def getStdout(self, getList=True):
        """
        Get the standard output of the executed command

        getList: If True, return a list of lines.
                 Otherwise, return the result as one string
        """

        if getList:
            return self._stdout.split('\n')

        return self._stdout

    def getStderr(self, getList=True):
        """
        Get the error output of the executed command

        getList: If True, return a list of lines.
                 Otherwise, return the result as one string
        """

        if getList:
            return self._stderr.split('\n')

        return self._stderr

    def getReturnCode(self):
        """
        Get the exit/return status of the command
        """
        return self._returncode

    def getTimeStartedExecution(self, inMicroseconds=False):
        """
        Get the time when the execution started
        """
        if(isinstance(self._timeStartedExecution, datetime.datetime)):
            if(inMicroseconds):
                return int(str(calendar.timegm(self._timeStartedExecution.timetuple())) + str(self._timeStartedExecution.strftime("%f")))
                #return self._timeStartedExecution.strftime("%s%f")
        return self._timeStartedExecution

    def getTimeFinishedExecution(self, inMicroseconds=False):
        """
        Get the time when the execution finished
        """
        if(isinstance(self._timeFinishedExecution, datetime.datetime)):
            if(inMicroseconds):
                return int(str(calendar.timegm(self._timeFinishedExecution.timetuple())) + str(self._timeFinishedExecution.strftime("%f")))
                #return self._timeStartedExecution.strftime("%s%f")
        return self._timeFinishedExecution

#----------------------------------------------------------------------
class quick_regexp(object):
    """
    Quick regular expression class, which can be used directly in if() statements in a perl-like fashion.

    #### Sample code ####
    r = quick_regexp()
    if(r.search('pattern (test) (123)', string)):
        print(r.groups[0]) # Prints 'test'
        print(r.groups[1]) # Prints '123'
    """
    def __init__(self):
        self.groups = None
        self.matched = False

    def search(self, pattern, string, flags=0):
        match = re.search(pattern, string, flags)
        if match:
            self.matched = True
            if(match.groups()):
                self.groups = re.search(pattern, string, flags).groups()
            else:
                self.groups = True
        else:
            self.matched = False
            self.groups = None

        return self.matched

#----------------------------------------------------------------------
def print_(value_to_be_printed, print_indent=0, spaces_per_indent=4, endl="\n"):
    """
    This function, among anything else, it will print dictionaries (even nested ones) in a good looking way

    # value_to_be_printed: The only needed argument and it is the
                           text/number/dictionary to be printed
    # print_indent: indentation for the printed text (it is used for
                    nice looking dictionary prints) (default is 0)
    # spaces_per_indent: Defines the number of spaces per indent (default is 4)
    # endl: Defines the end of line character (default is \n)

    More info here:
    http://stackoverflow.com/questions/19473085/create-a-nested-dictionary-for-a-word-python?answertab=active#tab-top
    """

    if(isinstance(value_to_be_printed, dict)):
        for key, value in value_to_be_printed.iteritems():
            if(isinstance(value, dict)):
                print_('{0}{1!r}:'.format(print_indent * spaces_per_indent * ' ', key))
                print_(value, print_indent + 1)
            else:
                print_('{0}{1!r}: {2}'.format(print_indent * spaces_per_indent * ' ', key, value))
    else:
        string = ('{0}{1}{2}'.format(print_indent * spaces_per_indent * ' ', value_to_be_printed, endl))
        sys.stdout.write(string)

#----------------------------------------------------------------------
def get_dict_keys_by_value(dictionary, value):
    """
    This function will return a dictionary key by passing a value
    Only the key of the first encountered value will be returned
    """
    if(isinstance(dictionary, dict)):
        #return dictionary.keys()[dictionary.values().index(value)]
        return OrderedDict((k, v) for (k, v) in dictionary.items() if v == value)
    else:
        raise KeyError


#----------------------------------------------------------------------
def flatten_nested_dicts(d, parent_key=None):
    """
    Will flatten the keys of a nested dictionary.
    If there is no nesting, the dictionary is returned as is.
    """
    if(isinstance(d, dict)):
        items = []
        for k, v in d.items():
            new_key = "{0}_{1}".format(parent_key, k) if parent_key else str(k)
            if isinstance(v, dict):
                items.extend(flatten_nested_dicts(v, new_key).items())
            else:
                items.append((new_key, v))
    return OrderedDict(items)

def is_number(s):
    """
    Returns True if it's a valid number (int or float, positive or negative)
    Returns False if it is not a valid number
    Returns None on any other case
    """
    try:
        float(s)
        return True
    except ValueError:
        return False
    except:
        return None

def get_kernel_version(Version=None):
    """
    Returns a tuple with the first 3 linux kernel "Version" numbers
    Examples:
    Version=2.6.32-358.18.1.el6.x86_64
    (2, 6, 32)

    Version=3.8.0-35-generic
    (3, 8, 0)

    If no "Version" is provided, returns the current
    running kernel version of the system

    If "Version" is incorrect, return None
    """
    if Version is None:
        Version = platform.release()

    r = quick_regexp()
    ret_tuple = ()
    ret_string = ""
    if(r.search('^(\d+)(\.(\d+)?(\.(\d+)?)?)?', Version)):
        count = 0
        for num in r.groups:
            if(count in [0, 2, 4]):
                if(count == 0):
                    ret_string = str(num)
                    ret_tuple = (num,)
                else:
                    if(num):
                        ret_string += str("." + num)
                        ret_tuple = ret_tuple + (num,)
                    else:
                        ret_string += str(".0")
                        ret_tuple = ret_tuple + ('0',)
            count+=1
        return ret_string, ret_tuple
    else:
        return None, None

def trim_list(string_list):
    """
    An alias function of the function strip_string_list()
    """
    return strip_string_list(string_list)

def strip_string_list(string_list):
    """
    This function will parse all the elements from a list of strings (string_list),
    and trim leading or trailing white spaces and/or new line characters
    """
    return [s.strip() for s in string_list]

def split_strip(string, separator=","):
    """
    splits the given string in 'sep' and trims the whitespaces or new lines

    returns a list of the splitted stripped strings

    If the 'string' is not a string, -1 will be returned
    """
    if(isinstance(string, str)):
        return strip_string_list(string.split(separator))
    else:
        return -1
