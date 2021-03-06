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

from libs.helperfuncs import quick_regexp
from libs.collector import DataCollector
import sys
import traceback
try:
    from collections import OrderedDict
except ImportError:
    # python 2.6 or earlier, use backport
    from ordereddict import OrderedDict

########################################################################
class cpu_stats(DataCollector):
    """
    Plugin to read the CPU statistics from Linux based hosts.

    --------------------------------------------------

    Read CPU Statistics from /proc/stat

    Minimun Linux kernel version supported is 2.6.0

    # More information/documentation on /proc/stat
    http://www.linuxhowtos.org/System/procstat.htm
    https://www.kernel.org/doc/Documentation/filesystems/proc.txt    #(Search for /proc/stat)

    # Calculation of the cpu percentage
    http://stackoverflow.com/questions/23367857/accurate-calculation-of-cpu-usage-in-linux/23376195#23376195
    """

    # Do not change the order of PROC_STAT_FIELDS!
    # First 10 fields are per CPU specific fields
    PROC_STAT_FIELDS = (
        'user', 'nice', 'system', 'idle', 'iowait',
        'irq', 'softirq', 'steal', 'guest', 'guest_nice',
        'ctxt', 'btime', 'processes', 'procs_running', 'procs_blocked'
    )

    # Store the CPU core names to collect data from
    cpu_cores_to_collect_data_from = []

    # Store the fields to collect data from.
    # All of the available fields can be seen in PROC_STAT_FIELDS
    fields_to_collect_data_from = []

    def __init__(self):
        super(cpu_stats, self).__init__()

        # If the kernel is older, some of the PROC_STAT_FIELDS needs
        # to be removed (they do not exist in older kernels)
        self.available_cpu_fields = self.PROC_STAT_FIELDS[0:10]
        if(self.runningKernelIsGLEthan('2.6.33', Less=True)):
            # guest_nice (supported since Linux 2.6.33)
            if('guest_nice' in self.PROC_STAT_FIELDS):
                fields_list = list(self.PROC_STAT_FIELDS)
                fields_list.remove('guest_nice')
                self.PROC_STAT_FIELDS = tuple(fields_list)
                self.available_cpu_fields = self.PROC_STAT_FIELDS[0:9]
        if(self.runningKernelIsGLEthan('2.6.24', Less=True)):
            # guest (supported since Linux 2.6.24)
            if('guest' in self.PROC_STAT_FIELDS):
                fields_list = list(self.PROC_STAT_FIELDS)
                fields_list.remove('guest')
                self.PROC_STAT_FIELDS = tuple(fields_list)
                self.available_cpu_fields = self.PROC_STAT_FIELDS[0:8]
        if(self.runningKernelIsGLEthan('2.6.11', Less=True)):
            # steal (supported since Linux 2.6.11)
            if('steal' in self.PROC_STAT_FIELDS):
                fields_list = list(self.PROC_STAT_FIELDS)
                fields_list.remove('steal')
                self.PROC_STAT_FIELDS = tuple(fields_list)
                self.available_cpu_fields = self.PROC_STAT_FIELDS[0:7]

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

        # Read parameters from the configuration file
        self.readConfParameter(self.options, 'calc_cpu_perc', self.BOOL)
        self.readConfParameter(self.options, 'include_cpu_cores', self.STR, True)
        self.readConfParameter(self.options, 'exclude_cpu_cores', self.STR, True)
        self.readConfParameter(self.options, 'fields_to_collect', self.STR, True)
        self.readConfParameter(self.options, 'fields_to_exclude', self.STR, True)
        self.readConfParameter(self.options, 'NA_value', self.STR)

        # Discover which cpu cores will be logged and log only these for the rest of the experiment
        # Store them in self.cpu_cores_to_collect_data_from
        try:
            available_cpu_cores = []
            r = quick_regexp()
            # Open /proc/stat for get all available cpu cores
            with open('/proc/stat') as f:
                for line in f.readlines():
                    if(r.search('cpu(\d+)?\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*(\d+)?\s*(\d+)?\s*(\d+)?', line)):
                        if(r.groups[0]):
                            # Each "cpuN" line holds statistics for this specific core/thread.
                            cpuName = 'cpu' + r.groups[0]
                        else:
                            # The very first "cpu" line aggregates the numbers in all of the other "cpuN" lines.
                            cpuName = 'cpu_all'
                        # Append the available cpu core in available_cpu_cores list
                        available_cpu_cores.append(cpuName)

            # remove or add the included or excluded cpu core names read from the configuration file.
            # store them in self.cpu_cores_to_collect_data_from
            self.cpu_cores_to_collect_data_from = self.include_exclude_fields(self.options['include_cpu_cores'],
                                                                              self.options['exclude_cpu_cores'],
                                                                              available_cpu_cores,
                                                                              strict=False)

            self.LOG.debug('CPU cores to be used for data collection: ' + str(self.cpu_cores_to_collect_data_from))
        except:
            self.LOG.debug(traceback.format_exc())

        # Get the fields which we should collect data for
        self.fields_to_collect_data_from = self.include_exclude_fields(self.options['fields_to_collect'],
                                                                       self.options['fields_to_exclude'],
                                                                       self.PROC_STAT_FIELDS)

        # If cpu percentage needs to be calculated,
        # at least 'user', 'nice', 'system' and 'idle' fields
        # need to be collected
        if self.options['calc_cpu_perc']:
            for needed_field in self.available_cpu_fields:
                if needed_field not in self.fields_to_collect_data_from:
                    self.fields_to_collect_data_from.append(needed_field)

        self.LOG.debug('/proc/stat fields to be used for data collection: ' + str(self.fields_to_collect_data_from))

    #----------------------------------------------------------------------
    def collect(self, prevResults = {}):
        # The returned numbers identify the amount of time the CPU has spent performing different kinds of work.
        # Time units are in USER_HZ or Jiffies (typically hundredths of a second).
        samples = OrderedDict()

        # Add all of the-cpu core names in self.cpu_cores_to_collect_data_from to the samples.
        # We do that here, because if any of the cores do not exist in the beginning of the
        # data collection, we still want to collect NA values (it might be hotplugged later)
        for cpuName in sorted(self.cpu_cores_to_collect_data_from):
            if cpuName not in samples.keys():
                samples[cpuName] = OrderedDict()
                for field in self.available_cpu_fields:
                    if field in self.fields_to_collect_data_from:
                        samples[cpuName][field] = self.options['NA_value']

        try:
            r = quick_regexp()
            with open('/proc/stat') as f:
                for line in f.readlines():
                    if(r.search('cpu(\d+)?\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*(\d+)?\s*(\d+)?\s*(\d+)?', line)):
                        if(r.groups[0]):
                            # Each "cpuN" line holds statistics for this specific core/thread.
                            cpuName = 'cpu' + r.groups[0]
                        else:
                            # The very first "cpu" line aggregates the numbers in all of the other "cpuN" lines.
                            # That's why we call it 'cpu_all'
                            cpuName = 'cpu_all'

                        # If the cpuName is listed in self.cpu_cores_to_collect_data_from
                        # then we need to collect data for this cpu core
                        if cpuName in self.cpu_cores_to_collect_data_from:
                            # r.groups[0] stores the cpu core name, so
                            # the fields start from r.groups[1]....r.groups[10]
                            for i in range(1, len(r.groups)):
                                field = self.PROC_STAT_FIELDS[i-1]
                                if field in self.fields_to_collect_data_from:
                                    samples[cpuName][field] = r.groups[i]
                    else:
                        # Read ctxt, btime, processes, procs_running, procs_blocked
                        if(r.search('^(\S+)\s+(\d+)$', line)):
                            if r.groups[0] in self.fields_to_collect_data_from:
                                samples[r.groups[0]] = r.groups[1]
        except:
            self.LOG.debug(traceback.format_exc())

        # cpu percentage (needs to be calculated) if self.options['calc_cpu_perc'] == True
        if self.options['calc_cpu_perc']:
            for key in samples:
                # Get only the values with a cpu* header
                if(r.search('(cpu\S+)', key)):
                    # Create the header with a 'Not calculated' value
                    samples[r.groups[0]]['pct_total_used'] = self.options['NA_value']
                    samples[r.groups[0]]['pct_total_idle'] = self.options['NA_value']
                    samples[r.groups[0]]['pct_user'] = self.options['NA_value']
                    samples[r.groups[0]]['pct_system'] = self.options['NA_value']
                    samples[r.groups[0]]['pct_nice'] = self.options['NA_value']
                    samples[r.groups[0]]['pct_idle'] = self.options['NA_value']
                    samples[r.groups[0]]['pct_iowait'] = self.options['NA_value']
                    samples[r.groups[0]]['pct_irq'] = self.options['NA_value']
                    samples[r.groups[0]]['pct_softirq'] = self.options['NA_value']
                    if(self.runningKernelIsGLEthan('2.6.33', Greater=True, Equal=True)):
                        samples[r.groups[0]]['pct_guest_nice'] = self.options['NA_value']
                    if(self.runningKernelIsGLEthan('2.6.24', Greater=True, Equal=True)):
                        samples[r.groups[0]]['pct_guest'] = self.options['NA_value']
                    if(self.runningKernelIsGLEthan('2.6.11', Greater=True, Equal=True)):
                        samples[r.groups[0]]['pct_steal'] = self.options['NA_value']

                    if prevResults:
                        # If prevResults are present, calculate the CPU usage percentage
                        try:
                            PrevSteal = PrevGuest = PrevGuest_nice = 0
                            Steal = Guest = Guest_nice = 0

                            if(self.runningKernelIsGLEthan('2.6.33', Greater=True, Equal=True)):
                                # guest_nice (supported since Linux 2.6.33)
                                PrevGuest_nice = float(prevResults[r.groups[0]]['guest_nice'])
                                Guest_nice = float(samples[r.groups[0]]['guest_nice'])
                            if(self.runningKernelIsGLEthan('2.6.24', Greater=True, Equal=True)):
                                # guest (supported since Linux 2.6.24)
                                PrevGuest = float(prevResults[r.groups[0]]['guest'])
                                Guest = float(samples[r.groups[0]]['guest'])
                            if(self.runningKernelIsGLEthan('2.6.11', Greater=True, Equal=True)):
                                # steal (supported since Linux 2.6.11)
                                PrevSteal = float(prevResults[r.groups[0]]['steal'])
                                Steal = float(samples[r.groups[0]]['steal'])

                            prevUser = float(prevResults[r.groups[0]]['user']) - PrevGuest
                            prevNice = float(prevResults[r.groups[0]]['nice']) - PrevGuest_nice
                            prevSystem = float(prevResults[r.groups[0]]['system'])
                            prevIrq = float(prevResults[r.groups[0]]['irq'])
                            prevSoftIrq = float(prevResults[r.groups[0]]['softirq'])
                            prevIdle = float(prevResults[r.groups[0]]['idle'])
                            prevIowait = float(prevResults[r.groups[0]]['iowait'])

                            prevTotalIdle = prevIdle + prevIowait
                            prevVirtual = PrevGuest + PrevGuest_nice
                            prevTotalSystem = prevSystem + prevIrq + prevSoftIrq
                            prevTotal = prevUser + prevNice + prevTotalSystem + prevVirtual + prevTotalIdle + PrevSteal


                            User = float(samples[r.groups[0]]['user']) - Guest
                            Nice = float(samples[r.groups[0]]['nice']) - Guest_nice
                            System = float(samples[r.groups[0]]['system'])
                            Irq = float(samples[r.groups[0]]['irq'])
                            SoftIrq = float(samples[r.groups[0]]['softirq'])
                            Idle = float(samples[r.groups[0]]['idle'])
                            Iowait = float(samples[r.groups[0]]['iowait'])

                            TotalIdle = Idle + Iowait
                            Virtual = Guest + Guest_nice
                            TotalSystem = System + Irq + SoftIrq
                            Total = User + Nice + TotalSystem + Virtual + TotalIdle + Steal

                            if Total - prevTotal > 0:
                                samples[r.groups[0]]['pct_total_used'] = str(round(100 * (( Total - prevTotal ) - ( TotalIdle - prevTotalIdle )) / ( Total - prevTotal ), 2))
                                samples[r.groups[0]]['pct_total_idle'] = str(round(100 * ( Idle - prevIdle ) / ( Total - prevTotal ), 2))
                                samples[r.groups[0]]['pct_user'] = str(round((100 * ( User - prevUser ) / ( Total - prevTotal )), 2))
                                samples[r.groups[0]]['pct_system'] = str(round((100 * ( System - prevSystem ) / ( Total - prevTotal )), 2))
                                samples[r.groups[0]]['pct_nice'] = str(round((100 * ( Nice - prevNice ) / ( Total - prevTotal )), 2))
                                samples[r.groups[0]]['pct_idle'] = str(round((100 * ( Idle - prevIdle ) / ( Total - prevTotal )), 2))
                                samples[r.groups[0]]['pct_iowait'] = str(round((100 * ( Iowait - prevIowait ) / ( Total - prevTotal )), 2))
                                samples[r.groups[0]]['pct_irq'] = str(round((100 * ( Irq - prevIrq ) / ( Total - prevTotal )), 2))
                                samples[r.groups[0]]['pct_softirq'] = str(round((100 * ( SoftIrq - prevSoftIrq ) / ( Total - prevTotal )), 2))
                                if(self.runningKernelIsGLEthan('2.6.33', Greater=True, Equal=True)):
                                    samples[r.groups[0]]['pct_guest_nice'] = str(round((100 * ( Guest_nice - PrevGuest_nice ) / ( Total - prevTotal )), 2))
                                if(self.runningKernelIsGLEthan('2.6.24', Greater=True, Equal=True)):
                                    samples[r.groups[0]]['pct_guest'] = str(round((100 * ( Guest - PrevGuest ) / ( Total - prevTotal )), 2))
                                if(self.runningKernelIsGLEthan('2.6.11', Greater=True, Equal=True)):
                                    samples[r.groups[0]]['pct_steal'] = str(round((100 * ( Steal - PrevSteal ) / ( Total - prevTotal )), 2))
                            else:
                                samples[r.groups[0]]['pct_total_used'] = str(0)
                                samples[r.groups[0]]['pct_total_idle'] = str(1)
                                samples[r.groups[0]]['pct_user'] = str(0)
                                samples[r.groups[0]]['pct_system'] = str(0)
                                samples[r.groups[0]]['pct_nice'] = str(0)
                                samples[r.groups[0]]['pct_idle'] = str(1)
                                samples[r.groups[0]]['pct_iowait'] = str(0)
                                samples[r.groups[0]]['pct_irq'] = str(0)
                                samples[r.groups[0]]['pct_softirq'] = str(0)
                                if(self.runningKernelIsGLEthan('2.6.33', Greater=True, Equal=True)):
                                    samples[r.groups[0]]['pct_guest_nice'] = str(0)
                                if(self.runningKernelIsGLEthan('2.6.24', Greater=True, Equal=True)):
                                    samples[r.groups[0]]['pct_guest'] = str(0)
                                if(self.runningKernelIsGLEthan('2.6.11', Greater=True, Equal=True)):
                                    samples[r.groups[0]]['pct_steal'] = str(0)

                        except ZeroDivisionError:
                            # If the calculation returns ZeroDivisionError
                            # continue quietly
                            pass
                        except ValueError:
                            # If the previous value is not available, a ValueError
                            # will be raised when the numbers are parsed
                            pass

        return samples
