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
from collections import OrderedDict
import logging
import platform
import subprocess
import datetime

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
        self.__stdout = None
        self.__stderr = None
        self.__returncode = None
        self.__timeStartedExecution = None
        self.__timeFinishedExecution = None
        self.__args = args
        self.isUtc = isUtc
        if(self.__args != None):
            self.execute()

    def execute(self, args=None):
        if(args != None):
            self.__args = args

        if(self.__args != None):
            if(self.isUtc):
                self.__timeStartedExecution = datetime.datetime.utcnow()
            else:
                self.__timeStartedExecution = datetime.datetime.now()
            p = subprocess.Popen(self.__args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if(self.isUtc):
                self.__timeFinishedExecution = datetime.datetime.utcnow()
            else:
                self.__timeFinishedExecution = datetime.datetime.now()
            self.__stdout, self.__stderr = p.communicate()
            self.__returncode = p.returncode
            return 1
        else:
            self.__stdout = None
            self.__stderr = None
            self.__returncode = None
            return 0

    def getStdout(self):
        """
        Get the standard output of the executed command
        """
        return self.__stdout

    def getStderr(self):
        """
        Get the error output of the executed command
        """
        return self.__stderr

    def getReturnCode(self):
        """
        Get the exit/return status of the command
        """
        return self.__returncode

    def getTimeStartedExecution(self, inMicroseconds=False):
        """
        Get the time when the execution started
        """
        if(isinstance(self.__timeStartedExecution, datetime.datetime)):
            if(inMicroseconds):
                return int(str(calendar.timegm(self.__timeStartedExecution.timetuple())) + str(self.__timeStartedExecution.strftime("%f")))
                #return self.__timeStartedExecution.strftime("%s%f")
        return self.__timeStartedExecution

    def getTimeFinishedExecution(self, inMicroseconds=False):
        """
        Get the time when the execution finished
        """
        if(isinstance(self.__timeFinishedExecution, datetime.datetime)):
            if(inMicroseconds):
                return int(str(calendar.timegm(self.__timeFinishedExecution.timetuple())) + str(self.__timeFinishedExecution.strftime("%f")))
                #return self.__timeStartedExecution.strftime("%s%f")
        return self.__timeFinishedExecution

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

    def search(self, pattern, string, flags=0):
        try:
            self.groups = re.search(pattern, string, flags).groups()
        except:
            self.groups = None
        return self.groups

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
                print_('{}{!r}:'.format(print_indent * spaces_per_indent * ' ', key))
                print_(value, print_indent + 1)
            else:
                print_('{}{!r}: {}'.format(print_indent * spaces_per_indent * ' ', key, value))
    else:
        string = ('{}{}{}'.format(print_indent * spaces_per_indent * ' ', value_to_be_printed, endl))
        sys.stdout.write(string)

#----------------------------------------------------------------------
def get_dict_keys_by_value(dictionary, value):
    """
    This function will return a dictionary key by passing a value
    Only the key of the first encountered value will be returned
    """
    if(isinstance(dictionary, dict)):
        #return dictionary.keys()[dictionary.values().index(value)]
        return {k:v for k, v in dictionary.items() if v == value}
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
            new_key = "{}_{}".format(parent_key, k) if parent_key else str(k)
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

    returns a list of the slipped stripped strings

    If the 'string' is not a string, -1 will be returned
    """
    if(isinstance(string, str)):
        return strip_string_list(string.split(separator))
    else:
        return -1
