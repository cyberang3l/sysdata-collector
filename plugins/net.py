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

from libs.helperfuncs import *
from libs.collector import DataCollector
import sys
import time
import traceback
import fnmatch
try:
    from collections import OrderedDict
except ImportError:
    # python 2.6 or earlier, use backport
    from ordereddict import OrderedDict

########################################################################
class net_stats(DataCollector):
    """
    Plugin to read the Network statistics from Linux based hosts

    --------------------------------------------------

    Read Network Statistics from /proc/net/dev

    # More information/documentation on /proc/stat
    http://www.linuxhowtos.org/manpages/5/proc.htm    #(Search for /proc/net/dev)
    """

    # Do not change the order of NETDEV_FIELDS!
    NETDEV_FIELDS = (
        'rx_bytes', 'rx_packets', 'rx_errs', 'rx_drop',
        'rx_fifo', 'frame', 'rx_compressed', 'multicast',
        'tx_bytes', 'tx_packets', 'tx_errs', 'tx_drop',
        'tx_fifo', 'colls', 'carrier', 'tx_compressed'
    )

    # Store the network interface names to collect data from
    interfaces_to_collect_data_from = []

    # Store the fields to collect data from.
    # All of the available fields can be seen in NETDEV_FIELDS
    fields_to_collect_data_from = []

    #----------------------------------------------------------------------
    def readConfigVars(self):
        # Default is to include all of the interfaces
        self.options = {
            'include_interfaces': ['*'],
            'exclude_interfaces': [],
            'fields_to_collect': ['bytes', 'packets', 'errs', 'drop'],
            'fields_to_exclude': [],
            'calculate_totals': True,
            'NA_value': 'NA'
        }

        self.readConfParameter(self.options, 'include_interfaces', self.STR, True)
        self.readConfParameter(self.options, 'exclude_interfaces', self.STR, True)
        self.readConfParameter(self.options, 'fields_to_collect', self.STR, True)
        self.readConfParameter(self.options, 'fields_to_exclude', self.STR, True)
        self.readConfParameter(self.options, 'NA_value', self.STR)
        self.readConfParameter(self.options, 'calculate_totals', self.BOOL)

        # Discover which network interfaces will be logged and log only these interfaces for the rest of the experiment
        # Store them in self.interface_to_collect_data_from
        try:
            available_interfaces = []
            r = quick_regexp()
            with open('/proc/net/dev') as f:
                for line in f.readlines():
                    if(r.search('(\S+):\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)', line)):
                        ifName = r.groups[0]
                        available_interfaces.append(ifName)

            self.interfaces_to_collect_data_from = sorted(
                self.include_exclude_fields(
                    self.options['include_interfaces'],
                    self.options['exclude_interfaces'],
                    available_interfaces, strict=False
                )
            )

            LOG.debug('Network interfaces to be used for data collection: ' + str(self.interfaces_to_collect_data_from))
        except:
            LOG.debug(traceback.format_exc())

        self.fields_to_collect_data_from = self.include_exclude_fields(
            self.options['fields_to_collect'],
            self.options['fields_to_exclude'],
            self.NETDEV_FIELDS
        )

        self.LOG.debug('/proc/net/dev fields to be used for data collection: ' + str(self.fields_to_collect_data_from))


    #----------------------------------------------------------------------
    def collect(self, prevResults = {}):
        """
        /proc/net/dev
            The dev pseudo-file contains network device status information. This gives the number of received and sent packets, the number of errors and collisions and other basic statistics. These are used by the ifconfig(8) program to report device status. The format is:

            Inter-|   Receive                                                |  Transmit
             face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
                lo: 2776770   11307    0    0    0     0          0         0  2776770   11307    0    0    0     0       0          0
              eth0: 1215645    2751    0    0    0     0          0         0  1782404    4324    0    0    0   427       0          0
              ppp0: 1622270    5552    1    0    0     0          0         0   354130    5669    0    0    0     0       0          0
              tap0:    7714      81    0    0    0     0          0         0     7714      81    0    0    0     0       0          0
        """
        samples = OrderedDict()

        # Initiate the samples dict for all the interfaces that we will
        # collect data from
        for ifName in self.interfaces_to_collect_data_from:
            samples[ifName] = OrderedDict()
            for field in self.NETDEV_FIELDS:
                if field in self.fields_to_collect_data_from:
                    samples[ifName][field] = self.options['NA_value']

        try:
            r = quick_regexp()
            with open('/proc/net/dev') as f:
                for line in f.readlines():
                    if(r.search('(\S+):\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)', line)):
                        ifName = r.groups[0]
                        if ifName in self.interfaces_to_collect_data_from:
                            for i in range(1, len(r.groups)):
                                field = self.NETDEV_FIELDS[i-1]
                                if field in self.fields_to_collect_data_from:
                                    samples[ifName][field] = r.groups[i]
        except:
            LOG.debug(traceback.format_exc())

        # If totals are to be calculated, find which values have their pairs
        if self.options['calculate_totals']:
            for ifName in samples:
                for key in samples[ifName]:
                    if r.search('(r|t)x_(\w+)', key):
                        if r.groups[0] == 'r':
                            pair='tx_' + r.groups[1]
                        elif r.groups[0] == 't':
                            pair='rx_' + r.groups[1]

                        if pair in samples[ifName].keys():
                            try:
                                samples[ifName]['total_' + r.groups[1]] = str(int(samples[ifName][key]) + int(samples[ifName][pair]))
                            except ValueError:
                                # If you get a ValueError, most likely the collected
                                # value is NA, so continue quietly
                                samples[ifName]['total_' + r.groups[1]] = self.options['NA_value']

        ## TODO: Add an option to calculate speed/second from previous collection
                    ## Similar to the way
                    ## cpu percentage (needs to be calculated) if self.calc_cpu_perc == True
                    #if self.calc_cpu_perc:
                        #for key in samples:
                            ## Get only the values with a cpu* header
                            #if(r.search('(cpu\S+)', key)):
                                ## Create the header with a 'Not calculated' value
                                #samples[r.groups[0]]['percent'] = 'Not calculated'
                                #if prevResults:
                                    ## If prevResults are present, calculate the CPU usage percentage
                                    #prevUser = float(prevResults[r.groups[0]]['user'])
                                    #prevNice = float(prevResults[r.groups[0]]['nice'])
                                    #prevSystem = float(prevResults[r.groups[0]]['system'])
                                    #prevIdle = float(prevResults[r.groups[0]]['idle'])
                                    #prevTotal = prevUser + prevNice + prevSystem + prevIdle

                                    #User = float(samples[r.groups[0]]['user'])
                                    #Nice = float(samples[r.groups[0]]['nice'])
                                    #System = float(samples[r.groups[0]]['system'])
                                    #Idle = float(samples[r.groups[0]]['idle'])
                                    #Total = User + Nice + System + Idle

                                    #try:
                                        #samples[r.groups[0]]['percent']=round(100 * (( Total - prevTotal ) - ( Idle - prevIdle )) / ( Total - prevTotal ), 2)
                                    #except ZeroDivisionError:
                                        #pass

        return samples
