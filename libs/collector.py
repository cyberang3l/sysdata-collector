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

import os
import logging
from libs.helperfuncs import print_, flatten_nested_dicts
from yapsy.IPlugin import IPlugin
from abc import ABCMeta, abstractmethod
from time import sleep
from platform import release
from ConfigParser import ConfigParser
from libs.helperfuncs import get_kernel_version
from distutils.version import StrictVersion
import fnmatch

# You can use the LOG for debugging purposes.
# Use like this: LOG.debug("My plugin's message!")
# Then check the sysdata-collector's log file to
# find this message
LOG = logging.getLogger('default.' + __name__)

class DataCollector(IPlugin):
    """
    DataCollector abstract superclass
    """

    def __init__(self):
        """
        Call the parent class (`IPlugin`) methods when
        overriding them.
        """
        super(DataCollector, self).__init__()

        # Get the headers when the plugin is initialized
        self.headers = ''

        # A configParser instance with the contents of the plugin's metaconf file
        # This is useful whenever you want to parse some configuration to create
        # more intelligent plugins
        self.config = ConfigParser()

        # Get the current Linux kernel version
        self.running_kernel_version = get_kernel_version(release())[0]

    def activate(self):
        """
        Call `activate()` on the parent class to ensure that the
        `is_activated` property gets set.
        """
        super(DataCollector, self).activate()

        # Initialize any user defined configuration
        self.readConfigVars()

    def deactivate(self):
        """
        Call `deactivate()` on the parent class to ensure that
        the `is_activated` property gets set.
        """
        super(DataCollector, self).deactivate()

    def readConfigVars(self):
        """
        Initialize your user configuration variables existing in
        the 'Plugin' section of your metaconf file.

        If your plugin doesn't read any configuration from the
        metaconf file, you do not need to add any content in
        this method.

        --------------------------------------------------------------
        Sample code to read a boolean 'myvar':

        # Default value of myvar equals to False
        self.myvar = False
        if(self.config.has_section('Plugin')):
            if(self.config.has_option('myvar')):
                self.myvar = self.config.getboolean('Plugin', 'myvar')
        """
        raise NotImplementedError()

    def collect(self, prevResults={}):
        """
        The collect() method must be implemented by all DataCollector
        plugins and should return an OrderedDict like this one:

        OD = {
        '1st_sample_header':'1st_sample_value',
        '2nd_sample_header':'2nd_sample_value',
        ...,
        ...,
        'Nth_sample_header':'Nth_sample_value'

        prevResults: holds the results of this plugin from the previous
        run. This is particularly useful when your plugin needs to do
        some calculations based on the previous results. For instance,
        if you measure network counters and you want to get the bytes per second (Bps)
        transmitted since the last measurement, you could do something
        like this:
          Bps = (currentTxBytes - previousTxBytes)/(currentTimestamp - prevTimestamp)

        --------------------------------------------------------------
        Sample code:

            from collections import OrderedDict

            results = OrderedDict()
            results['1st_sample'] = 0.3
            results['2nd_sample'] = 0.12
            return results
        }
        """
        raise NotImplementedError()

    def getHeaders(self, delimiter=","):
        """
        Get the headers of this plugin.
        """
        self.headers = ''
        for k in flatten_nested_dicts(self.collect()):
            self.headers += k + delimiter
        self.headers = self.headers[0:-1]
        return self.headers

    def print_(self, headers=False):
        """
        this function is useful to test newly generated plugins.

        It will print the headers of each collected metric
        or the returned dictionary after two iteratetions. Two
        Iterations are needed for testing plugins that need
        to calculate values based on their results from the
        previous run.
        """
        if(headers):
            if(self.headers == ''):
                self.getHeaders()
            print_(self.headers)
        else:
            prevResults = self.collect()
            print_("################## Iteration 1 ##################")
            print_(prevResults)
            sleep(0.5)
            print_("################## Iteration 2 ##################")
            print_(self.collect(prevResults))

    def runningKernelIsGEthan(self, kernel):
        """
        Use this function to check if the running kernel is Greater or Equal to "kernel"

        Returns True if it is Greater or Equal to "kernel"
        Returns False otherwise
        """
        if(StrictVersion(self.running_kernel_version) >= StrictVersion(kernel)):
            return True
        else:
            return False

    def include_exclude_fields(self, fields_to_be_included, fields_to_be_excluded, all_accepted_fields, strict=True):
        """
        When it is needed to include/exclude fields, this function will do the job.

        fields_to_be_included: a list of fields to be included
        fields_to_be_excluded: a list of fields to be excluded
        all_available_fields: a list with all of the available fields which is
                              possible to use
        strict: if strict is True, and a field to be included or excluded is
                not present in all_available_fields, and error will be raised.
                Otherwise, the field will be added for data collection.
                In the latter case, you have to make sure that NA (Not Available)
                values are taken into consideration, in case that the script
                cannot collect values for the specified field. (This is useful
                if you want to collect data for fields that are not present
                at the time when data collection started. i.e. a device
                might be hot plugged or unplugged)
        """
        store_final_fields = []

        # First include all of the fields defined in fields_to_be_included
        for include in fields_to_be_included:
            match = fnmatch.filter(all_accepted_fields, include)
            # If there is a match, the field to be included is accepted
            # is present in all_accepted_fields.
            # Since we accept POSIX style regular expressions, the match
            # might contain more than one fields to be included
            if match:
                for field in match:
                    if field not in store_final_fields:
                        store_final_fields.append(field)
            else:
                # If there is no match, the field is not present at the moment,
                # however, if strict is false, we still want to collect data for it
                if not strict:
                    if include not in store_final_fields:
                        store_final_fields.append(include)

        store_final_fields = sorted(store_final_fields)

        # Then start the exclusion.
        # Since we accept POSIX style regular expressions, the match
        # might contain more than one fields to be excluded
        for exclude in fields_to_be_excluded:
            match = fnmatch.filter(store_final_fields, exclude)
            if match:
                for field in match:
                    if field in store_final_fields:
                        store_final_fields.remove(field)

        return store_final_fields
