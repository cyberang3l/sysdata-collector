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
from collections import OrderedDict
import fnmatch

########################################################################
class cpu_stats(DataCollector):
    """
    Plugin to read the CPU statistics from Linux based hosts

    The CPU plugin can be used as a guideline to create more advanced
    plugins. Nested dict values are used (because each CPU core has different
    metrics to be collected), the prevResults is used to calculate
    some values, it supports multiple kernels (by checking the running
    kernel version and collecting data if supported), it reads configuration
    variables from the metaconf and logs debug output in the log file using
    LOG.debug().

    --------------------------------------------------

    Read CPU Statistics from /proc/stat

    Minimun Linux kernel version supported is 2.6.0

    # More information/documentation on /proc/stat
    http://www.linuxhowtos.org/System/procstat.htm
    http://www.linuxhowtos.org/manpages/5/proc.htm    #(Search for /proc/stat)
    http://www.mjmwired.net/kernel/Documentation/filesystems/proc.txt#1202

    # Simple calculation of the cpu percentage
    http://unix.stackexchange.com/questions/27076/how-can-i-receive-top-like-cpu-statistics-from-the-shell?answertab=active#tab-top
    """

    # Do not change the order of PROC_STAT_FIELDS!
    PROC_STAT_FIELDS = (
        'user', 'nice', 'system', 'idle', 'iowait',
        'irq', 'softirq', 'steal', 'guest', 'guest_nice',
        'ctxt', 'btime', 'processes', 'procs_running', 'procs_blocked'
    )

    cpu_cores_to_collect_data_from = []
    fields_to_collect_data_from = []

    #----------------------------------------------------------------------
    def readConfigVars(self):
        # Default is to calculate CPU usage percentage
        self.options = {
            'include_cpu_cores': ['*'],
            'exclude_cpu_cores': [],
            'fields_to_collect': ['*'],
            'fields_to_exclude': [],
            'NA_value': 'NA',
            'calc_cpu_perc': True
        }
        self.calc_cpu_perc = True

        Section = 'Plugin'
        if(self.config.has_section(Section)):
            VarToRead = 'calc_cpu_perc'
            if(self.config.has_option(Section, VarToRead)):
                LOG.debug("Reading value for " + VarToRead)
                self.options[VarToRead] = self.config.getboolean(Section, VarToRead)
                LOG.debug(VarToRead + ' = ' + str(self.options[VarToRead]))

            VarToRead = 'NA_value'
            if(self.config.has_option(Section, VarToRead)):
                LOG.debug("Reading value for " + VarToRead)
                self.options[VarToRead] = self.config.get(Section, VarToRead)
                LOG.debug(VarToRead + ' = ' + str(self.options[VarToRead]))

            VarToRead = 'include_cpu_cores'
            if(self.config.has_option(Section, VarToRead)):
                LOG.debug("Reading value for " + VarToRead)
                self.options[VarToRead] = split_strip(self.config.get(Section, VarToRead))
                LOG.debug(VarToRead + ' = ' + str(self.options[VarToRead]))

            VarToRead = 'exclude_cpu_cores'
            if(self.config.has_option(Section, VarToRead)):
                LOG.debug("Reading value for " + VarToRead)
                self.options[VarToRead] = split_strip(self.config.get(Section, VarToRead))
                LOG.debug(VarToRead + ' = ' + str(self.options[VarToRead]))

            VarToRead = 'fields_to_collect'
            if(self.config.has_option(Section, VarToRead)):
                LOG.debug("Reading value for " + VarToRead)
                self.options[VarToRead] = split_strip(self.config.get(Section, VarToRead))
                LOG.debug(VarToRead + ' = ' + str(self.options[VarToRead]))

            VarToRead = 'fields_to_exclude'
            if(self.config.has_option(Section, VarToRead)):
                LOG.debug("Reading value for " + VarToRead)
                self.options[VarToRead] = split_strip(self.config.get(Section, VarToRead))
                LOG.debug(VarToRead + ' = ' + str(self.options[VarToRead]))

        # Discover which cpu cores will be logged and log only these for the rest of the experiment
        # Store them in self.cpu_cores_to_collect_data_from
        try:
            available_cpu_cores = []
            r = quick_regexp()
            with open('/proc/stat') as f:
                for line in f.readlines():
                    if(r.search('cpu(\d+)?\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*(\d+)?\s*(\d+)?\s*(\d+)?', line)):
                        if(r.groups[0]):
                            # Each "cpuN" line holds statistics for this specific core/thread.
                            cpuName = 'cpu' + r.groups[0]
                        else:
                            # The very first "cpu" line aggregates the numbers in all of the other "cpuN" lines.
                            cpuName = 'cpu_avg_all'
                        available_cpu_cores.append(cpuName)

            self.cpu_cores_to_collect_data_from = self.include_exclude_fields(self.options['include_cpu_cores'],
                                                                              self.options['exclude_cpu_cores'],
                                                                              available_cpu_cores,
                                                                              strict=False)

            LOG.debug('CPU cores to be used for data collection: ' + str(self.cpu_cores_to_collect_data_from))
        except:
            LOG.debug(traceback.format_exc())

        self.fields_to_collect_data_from = self.include_exclude_fields(self.options['fields_to_collect'],
                                                                       self.options['fields_to_exclude'],
                                                                       self.PROC_STAT_FIELDS)

        LOG.debug('/proc/stat fields to be used for data collection: ' + str(self.fields_to_collect_data_from))

        # If cpu percentage needs to be calculated,
        # at least 'user', 'nice', 'system' and 'idle' fields
        # need to be collected
        if self.options['calc_cpu_perc']:
            if 'user' not in self.fields_to_collect_data_from:
                self.fields_to_collect_data_from.append('user')
            if 'nice' not in self.fields_to_collect_data_from:
                self.fields_to_collect_data_from.append('nice')
            if 'system' not in self.fields_to_collect_data_from:
                self.fields_to_collect_data_from.append('system')
            if 'idle' not in self.fields_to_collect_data_from:
                self.fields_to_collect_data_from.append('idle')

    #----------------------------------------------------------------------
    def collect(self, prevResults = {}):
        # The returned numbers identify the amount of time the CPU has spent performing different kinds of work.
        # Time units are in USER_HZ or Jiffies (typically hundredths of a second).
        samples = OrderedDict()
        try:
            # TODO: Need to consider the cpu cores not present, and add them in the final sample collected
            r = quick_regexp()
            with open('/proc/stat') as f:
                for line in f.readlines():
                    if(r.search('cpu(\d+)?\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*(\d+)?\s*(\d+)?\s*(\d+)?', line)):
                        if(r.groups[0]):
                            # Each "cpuN" line holds statistics for this specific core/thread.
                            cpuName = 'cpu' + r.groups[0]
                        else:
                            # The very first "cpu" line aggregates the numbers in all of the other "cpuN" lines.
                            # That's why we call it 'cpu_avg_all'
                            cpuName = 'cpu_avg_all'

                        if cpuName in self.cpu_cores_to_collect_data_from:
                            samples[cpuName] = OrderedDict()
                            for i in range(1, len(r.groups)):
                                field = self.PROC_STAT_FIELDS[i-1]
                                if field in self.fields_to_collect_data_from:
                                    samples[cpuName][field] = r.groups[i]

                            ## This is the old, more readable version...
                            ## In the new version, kernel version checks are not needed
                            ## because the group is completely dynamic (due to the for/range loop)
                            #samples[cpuName] = OrderedDict()
                            ## user: Time spent in user mode.
                            #samples[cpuName]['user'] = r.groups[1]
                            ## nice: Time spent in user mode with low priority (nice)
                            #samples[cpuName]['nice'] = r.groups[2]
                            ## system: Time spent in system mode
                            #samples[cpuName]['system'] = r.groups[3]
                            ## idle: Time spent in the idle task. This value should be USER_HZ times the second entry in the /proc/uptime pseudo-file.
                            #samples[cpuName]['idle'] = r.groups[4]
                            ## iowait: Time waiting for I/O to complete.
                            #samples[cpuName]['iowait'] = r.groups[5]
                            ## irq: Time servicing interrupts.
                            #samples[cpuName]['irq'] = r.groups[6]
                            ## softirq: Time servicing softirqs.
                            #samples[cpuName]['softirq'] = r.groups[7]
                            #if(self.runningKernelIsGEthan('2.6.11')):
                                ## steal (since Linux 2.6.11): Stolen time, which is the time spent in other operating systems when running in a virtualized environment
                                #samples[cpuName]['steal'] = r.groups[8]
                            #if(self.runningKernelIsGEthan('2.6.24')):
                                ## guest (since Linux 2.6.24): Time spent running a virtual CPU for guest operating systems under the control of the Linux kernel.
                                #samples[cpuName]['guest'] = r.groups[9]
                            #if(self.runningKernelIsGEthan('2.6.33')):
                                ## guest_nice (since Linux 2.6.33): Time spent running a niced guest (virtual CPU for guest operating systems under the control of the Linux kernel).
                                #samples[cpuName]['guest_nice'] = r.groups[10]
                    else:
                        # Read ctxt, btime, processes, procs_running, procs_blocked
                        if(r.search('^(\S+)\s+(\d+)$', line)):
                            if r.groups[0] in self.fields_to_collect_data_from:
                                samples[r.groups[0]] = r.groups[1]

            # cpu percentage (needs to be calculated) if self.options['calc_cpu_perc'] == True
            if self.options['calc_cpu_perc']:
                for key in samples:
                    # Get only the values with a cpu* header
                    if(r.search('(cpu\S+)', key)):
                        # Create the header with a 'Not calculated' value
                        samples[r.groups[0]]['percent'] = self.options['NA_value']
                        if prevResults:
                            # If prevResults are present, calculate the CPU usage percentage
                            prevUser = float(prevResults[r.groups[0]]['user'])
                            prevNice = float(prevResults[r.groups[0]]['nice'])
                            prevSystem = float(prevResults[r.groups[0]]['system'])
                            prevIdle = float(prevResults[r.groups[0]]['idle'])
                            prevTotal = prevUser + prevNice + prevSystem + prevIdle

                            User = float(samples[r.groups[0]]['user'])
                            Nice = float(samples[r.groups[0]]['nice'])
                            System = float(samples[r.groups[0]]['system'])
                            Idle = float(samples[r.groups[0]]['idle'])
                            Total = User + Nice + System + Idle

                            try:
                                samples[r.groups[0]]['percent']=round(100 * (( Total - prevTotal ) - ( Idle - prevIdle )) / ( Total - prevTotal ), 2)
                            except ZeroDivisionError:
                                pass

        except:
            LOG.debug(traceback.format_exc())

        return samples
