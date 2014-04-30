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

import traceback
from libs.helperfuncs import *
from libs.collector import DataCollector
try:
    from collections import OrderedDict
except ImportError:
    # python 2.6 or earlier, use backport
    from ordereddict import OrderedDict

########################################################################
class uptime(DataCollector):
    """
    Copy this plugin as a starting point to create your own plugins
    """

    #----------------------------------------------------------------------
    def readConfigVars(self):
        """
        No configuration needs to be read for this simple plugin.
        """
        pass

    #----------------------------------------------------------------------
    def collect(self, prevResults = None):
        """
        Very simple plugin which parses the uptime from /proc/uptime,
        by using a regular expression.

        Check the CPU plugin for a more advanced starting point.
        """

        samples = OrderedDict()
        try:
            r = quick_regexp()
            with open('/proc/uptime') as f:
                for line in f.readlines():
                    if(r.search('(\S+)\s+(\d+)', line)):
                        samples['uptime'] = r.groups[0]

        except:
            traceback.print_exc()

        return samples
