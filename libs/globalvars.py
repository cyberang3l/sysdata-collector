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

# Define default constants
PROGRAM_NAME = 'sysdata-collector'
VERSION = '0.0.1'
AUTHOR = 'Vangelis Tasoulas'

# Default config file location where the program should
# look for a configuration file
CONFIG_FILE_LOCATIONS = [".", "/etc/template"]

# The default config filename which might exist
# in CONFIG_FILE_LOCATIONS
DEFAULT_CONFIG_FILENAME = PROGRAM_NAME + ".conf"

# Console logging level (If you change this to DEBUG)
# text sent to STDOUT will be too much
# CRITICAL = 50
#    ERROR = 40
#  WARNING = 30
#     INFO = 20
#    DEBUG = 10
CONSOLE_LOG_LEVEL = 20

class exitCode():
    """
    Define static exit Codes
    """
    SUCCESS = 0
    FAILURE = 1
    INCORRECT_USAGE = 2

PRINT_SEPARATOR = "#######################################"


# Define AND set default values for the global variables here

# Default file logging level
# CRITICAL = 50
#    ERROR = 40
#  WARNING = 30
#     INFO = 20
#    DEBUG = 10
FileLogLevel = 20

# Default absolute path for the log file
log_file = "{0}/{1}".format(".", PROGRAM_NAME + ".log")

# Conf will be found on runtime (if any)
conf_file = ""

# If your program can run in daemon mode,
# check this variable in runtime if it is true
daemonMode = False

##################################################

list_available_plugins = False
list_active_plugins = False
only_print_samples = False
append_file = False
test_plugin = None
output_file = 'data_collected-%{ts}.dat'
delimiter = ","
active_plugins_dir = "active-plugins"
intervalBetweenSamples = 10
