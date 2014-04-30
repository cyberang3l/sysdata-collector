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
from platform import release
try:
    from collections import OrderedDict
except ImportError:
    # python 2.6 or earlier, use backport
    from ordereddict import OrderedDict

########################################################################
class kernel_version(DataCollector):
    """
    This plugin will only collect the running kernel version (the output of uname -r)
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
        Just return the running kernel version which is given by platform.release()
        This string is the same as the one returned by the command 'uname -r'
        """

        samples = OrderedDict()
        try:
            samples['running_kernel_version'] = release()
        except:
            traceback.print_exc()

        return samples
