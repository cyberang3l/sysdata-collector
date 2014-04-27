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
import sys
import logging
import ConfigParser
import argparse
import traceback
import datetime
from libs import globalvars
import helperfuncs

LOG = logging.getLogger('default.' + __name__)
LOG_CONSOLE = logging.getLogger('console.' + __name__)

_quiet = False

def parse_all_conf():

    # Parse the command line options
    options = _command_Line_Options()

    # Configure logging
    _set_logging(options)

    # Read configuration from file
    _read_config_file(options)

    # Validate user input and perform any necessary actions
    # to the given command line options
    # If any command line options need to override certain configuration
    # read from the conf file, put the code in this function.
    _validate_command_Line_Options(options)

    return options



def _command_Line_Options():
    """
    Define the accepted command line arguments in this function

    Read the documentation of argparse for more advanced command line
    argument parsing examples
    http://docs.python.org/2/library/argparse.html
    """

    ########################################
    #### Add user defined options here #####
    ########################################

    parser = argparse.ArgumentParser(version=globalvars.VERSION,
                                     description=globalvars.PROGRAM_NAME + " version " + globalvars.VERSION)

    parser.add_argument("-a", "--append-file",
                        action="store_true",
                        default=False,
                        dest="append_file",
                        help="If the FILE exists, append to the end of the file. Otherwise, create a new one with an extended filename.")
    parser.add_argument("-b", "--output-file",
                        action="store",
                        dest="output_file",
                        metavar="FILE",
                        help="Filename to save the collected data file")
    parser.add_argument("-c", "--delimiter",
                        action="store",
                        dest="delimiter",
                        metavar="CHAR",
                        help="CHAR is a single character to be used for field separation in the output FILE")
    parser.add_argument("-d", "--list-available-plugins",
                        action="store_true",
                        default=False,
                        dest="list_available_plugins",
                        help="Prints a list of the available plugins and exit")
    parser.add_argument("-e", "--list-active-plugins",
                        action="store_true",
                        default=False,
                        dest="list_active_plugins",
                        help="Prints a list of the active plugins located under the chosen active-directory and exit")
    parser.add_argument("-f", "--active-plugins-dir",
                        action="store",
                        dest="active_plugins_dir",
                        metavar="DIR_ACTIVE",
                        help="Define the active-directory to load plugins from for this experiment.")
    parser.add_argument("-g", "--custom-plugins-dir",
                        action="store",
                        dest="custom_plugins_dir",
                        metavar="DIR_PLUGINS",
                        help="Define a directory containing more plugins to be loaded.")
    #  Don't use -h
    #     it is used by --help
    parser.add_argument("-i", "--interval-between-sampling",
                        action="store",
                        type=float,
                        dest="intervalBetweenSamples",
                        metavar="FLOAT",
                        help="A FLOAT number which is the sleeping time given in seconds between sampling. If the value is 0 or negative, instant sampling will be initiated after each previous one")
    parser.add_argument("-j", "--only-print-samples",
                        action="store_true",
                        dest="only_print_samples",
                        help="Enabling this flag, will disable saving samples in a file. They will only be printed instead.")
    parser.add_argument("-k", "--test-plugin",
                        action="store",
                        dest="test_plugin_filename",
                        metavar="PLUGIN.py",
                        help="Use this option for debugging newly created plugins")


    ########################################
    #### End user defined options here #####
    ########################################

    parser.add_argument("-C", "--conf-file",
                        action="store",
                        default=globalvars.conf_file,
                        dest="conffile",
                        metavar="CONF_FILE",
                        help="CONF_FILE where the configuration will be read from (Default: will search for file '" +
                        globalvars.DEFAULT_CONFIG_FILENAME +
                        "' in the known predefined locations")
    parser.add_argument("-D", "--daemon",
                        action="store_true",
                        default=globalvars.daemonMode,
                        dest="isDaemon",
                        help="run in daemon mode")

    ### Add logging options in a different options group
    loggingGroupOpts = parser.add_argument_group('Logging Options', 'List of optional logging options')
    loggingGroupOpts.add_argument("-Q", "--quiet",
                                  action="store_true",
                                  default=_quiet,
                                  dest="isQuiet",
                                  help="Disable logging in the console but still keep logs in a file. This options is forced when run in daemon mode.")
    loggingGroupOpts.add_argument("-L", "--loglevel",
                                  action="store",
                                  default="NOTSET",
                                  dest="loglevel",
                                  metavar="LOG_LEVEL",
                                  help="LOG_LEVEL might be set to: CRITICAL, ERROR, WARNING, INFO, DEBUG. (Default: INFO)")
    loggingGroupOpts.add_argument("-F", "--logfile",
                                  action="store",
                                  default=globalvars.log_file,
                                  dest="logfile",
                                  metavar="LOG_FILE",
                                  help="LOG_FILE where the logs will be stored. If the file exists, text will be appended," +
                                  " otherwise the file will be created (Default: " + globalvars.log_file + ")")

    return parser.parse_args();

def replaceVariablesInConfStrings(string):
    """
    Replace variables in configuration strings

    Acceptable conf variables are:
    %{ts}             Replaced with the current timestamp
    %{datetime}       Replaced wit Current date and time in
                       this format YYYYmmDD_HHMMSS
    """
    current_time = datetime.datetime.now()
    if(string.find('%{ts}') != -1):
        replacement = current_time.strftime('%s')
        return string.replace('%{ts}', replacement)
    elif(string.find('%{datetime}') != -1):
        replacement = current_time.strftime('%Y%m%d_%H%M%S')
        return string.replace('%{datetime}', replacement)

    return string


def _validate_command_Line_Options(opts):
    """
    Validate the passed arguments if needed
    """

    # Deamon, Quiet and Only Print Samples options are validated in _set_logging
    globalvars.list_available_plugins = opts.list_available_plugins
    globalvars.list_active_plugins = opts.list_active_plugins
    globalvars.append_file = opts.append_file

    if(globalvars.only_print_samples and globalvars.append_file):
        print("ERROR: You cannot combine '--only-print-samples' and '--append-file' switches. Please choose only one of them.")
        exit(globalvars.exitCode.INCORRECT_USAGE)
    elif(globalvars.only_print_samples and opts.output_file):
        print("ERROR: You cannot combine '--only-print-samples' and '--output-file' switches. Please choose only one of them.")
        exit(globalvars.exitCode.INCORRECT_USAGE)

    if(opts.test_plugin_filename):
        globalvars.test_plugin = opts.test_plugin_filename

    if(opts.output_file):
        globalvars.output_file = replaceVariablesInConfStrings(opts.output_file)

    if(opts.delimiter):
        escaped_string = opts.delimiter.decode('string-escape')
        if(len(escaped_string) > 1):
            LOG.error("Delimiter must be a single character.")
            exit(globalvars.exitCode.INCORRECT_USAGE)
        globalvars.delimiter = escaped_string

    if(opts.active_plugins_dir):
        globalvars.active_plugins_dir = opts.active_plugins_dir

    if(opts.custom_plugins_dir):
        globalvars.plugin_directories.insert(0, opts.custom_plugins_dir)

    if(helperfuncs.is_number(opts.intervalBetweenSamples)):
        if(opts.intervalBetweenSamples > 0):
            globalvars.intervalBetweenSamples = opts.intervalBetweenSamples
        else:
            globalvars.intervalBetweenSamples = 0

def _set_logging(opts):
    global _quiet

    globalvars.daemonMode = opts.isDaemon
    globalvars.only_print_samples = opts.only_print_samples
    _quiet = True if globalvars.daemonMode else opts.isQuiet

    if(globalvars.only_print_samples and globalvars.daemonMode):
        print("ERROR: You cannot combine '--only-print-samples' and '--daemon' switches. Please choose only one of them.")
        exit(globalvars.exitCode.INCORRECT_USAGE)
    elif(globalvars.only_print_samples and _quiet):
        print("ERROR: You cannot combine '--only-print-samples' and '--quiet' switches. Please choose only one of them.")
        exit(globalvars.exitCode.INCORRECT_USAGE)

    _set_log_file(opts.logfile)
    _set_log_level(opts.loglevel)

def _set_log_level(loglevel):
    # Get the numeric loglevel provided by user (if provided)
    numeric_log_level = getattr(logging, loglevel.upper(), None)

    # Validate if the loglevel provided is correct (accepted)
    try:
        if not isinstance(numeric_log_level, int):
            raise ValueError()
    except ValueError:
        LOG.error('Invalid log level: %s' % loglevel)
        LOG.info('\tLog level must be set to one of the following:')
        LOG.info('\t   CRITICAL <- Least verbose')
        LOG.info('\t   ERROR')
        LOG.info('\t   WARNING')
        LOG.info('\t   INFO')
        LOG.info('\t   DEBUG    <- Most verbose')
        exit(globalvars.exitCode.INCORRECT_USAGE)

    if(numeric_log_level != logging.NOTSET):
        # If logging is set from the command line
        # define the logging policy
        globalvars.FileLogLevel = numeric_log_level
        _configureLogging()

    if(globalvars.FileLogLevel == logging.DEBUG):
        LOG.info("Debug level logging is enabled: Very Verbose")

def _set_log_file(logfile):
    # Get the absolute path
    globalvars.log_file = os.path.abspath(logfile)
    # If the path exists and it is NOT a file, exit with an error message
    if(os.path.exists(globalvars.log_file) and not os.path.isfile(globalvars.log_file)):
        # Using print here because the LOG will try to
        # write to a file which is not yet writable
        print("ERROR: " + globalvars.log_file + " exists but it is not a file.")
        exit(globalvars.exitCode.INCORRECT_USAGE)
    _configureLogging()



def _read_config_file(opts):
    """
    This function contains code to read from a configuration file
    """

    conffile = opts.conffile

    if(conffile !=  ""):
        # Get the absolute path
        globalvars.conf_file = os.path.abspath(conffile)
        # If the path exists and it is NOT a file, exit with an error message
        if(os.path.exists(globalvars.conf_file) and not os.path.isfile(globalvars.conf_file)):
            LOG.error(globalvars.conf_file + " exists but it is not a file.")
            exit(globalvars.exitCode.INCORRECT_USAGE)
    else:
        for confpath in globalvars.CONFIG_FILE_LOCATIONS:
            globalvars.conf_file = "{0}/{1}".format(confpath,globalvars.DEFAULT_CONFIG_FILENAME)
            if(os.path.isfile(globalvars.conf_file)):
                break
            else:
                globalvars.conf_file = ""
                LOG.debug("No configuration file found in: " + globalvars.conf_file)

    # If globalvars.conf_file var is still "" in this point, no configuration file is defined
    if(globalvars.conf_file ==  ""):
        LOG.debug("No configuration files found in the known paths")
        return


    try:
        with open(globalvars.conf_file):
            LOG.debug("Reading configuration from file " + globalvars.conf_file)
            config = ConfigParser.ConfigParser()
            config.read(globalvars.conf_file)
            ##################################################################################
            ##################################################################################
            ##################################################################################
            ##################################################################################
            ############### Add your code to read the configuration file here ################
            ##################################################################################
            ##################################################################################
            ##################################################################################
            ##################################################################################

            CurrentSection = "Default"
            if(config.has_section(CurrentSection)):
                if(config.has_option(CurrentSection, "output_file")):
                    globalvars.output_file = replaceVariablesInConfStrings(config.get(CurrentSection, "output_file"))
                    LOG.debug("output_file = " + globalvars.output_file)

                if(config.has_option(CurrentSection, "append_file")):
                    globalvars.append_file = config.getboolean(CurrentSection, "append_file")
                    LOG.debug("append_file = " + str(globalvars.append_file))

                if(config.has_option(CurrentSection, "delimiter")):
                    globalvars.delimiter = config.get(CurrentSection, "delimiter").decode('string-escape')
                    if(len(globalvars.delimiter) > 1):
                        LOG.error("Delimiter must be a single character. Make sure that you do not enclose the character in quotes.")
                        exit(globalvars.exitCode.INCORRECT_USAGE)
                    LOG.debug("delimiter = " + str(globalvars.delimiter))

                if(config.has_option(CurrentSection, "active_plugins_dir")):
                    globalvars.active_plugins_dir = config.get(CurrentSection, "active_plugins_dir")
                    LOG.debug("active_plugins_dir = " + globalvars.active_plugins_dir)

                if(config.has_option(CurrentSection, "custom_plugins_dir")):
                    globalvars.custom_plugins_dir = config.get(CurrentSection, "custom_plugins_dir")
                    LOG.debug("custom_plugins_dir = " + globalvars.custom_plugins_dir)

                if(config.has_option(CurrentSection, "intervalBetweenSamples")):
                    globalvars.intervalBetweenSamples = config.getfloat(CurrentSection, "intervalBetweenSamples")
                    LOG.debug("intervalBetweenSamples = " + str(globalvars.intervalBetweenSamples))

            ##################################################################################
            ##################################################################################
            ##################################################################################
            ##################################################################################
            ###############                    Until here                     ################
            ##################################################################################
            ##################################################################################
            ##################################################################################
            ##################################################################################

            LOG.debug("Finished reading configuration from file " + globalvars.conf_file)

            return
    except:
        LOG.error("\n" + traceback.format_exc())
        exit(globalvars.exitCode.FAILURE)

def _configureLogging():
    # Configure a defaultLogger
    defaultLogger = logging.getLogger('default')
    onlyConsoleLogger = logging.getLogger('console')

    # Define the format of file log output
    logFileFormatter = DefaultLoggingFormatter("%(asctime)s, [%(levelname)8s], [%(module)18s:%(lineno)-5d] %(message)s", "%Y-%m-%d %H:%M:%S.%f, %s%f")

    # Define the format of console log output
    logConsoleFormatter = VisualFormatter()

    # Set default logging level
    defaultLogger.setLevel(logging.DEBUG)
    onlyConsoleLogger.setLevel(logging.INFO)

    # Enable logging in a file
    defaultFileHandler = logging.FileHandler(globalvars.log_file)
    defaultFileHandler.setLevel(globalvars.FileLogLevel)
    defaultFileHandler.setFormatter(logFileFormatter)

    # Enable logging to the console
    defaultConsoleHandler = logging.StreamHandler()
    defaultConsoleHandler.setLevel(globalvars.CONSOLE_LOG_LEVEL)
    defaultConsoleHandler.setFormatter(logConsoleFormatter)

    onlyConsoleHandler = logging.StreamHandler()
    onlyConsoleHandler.setLevel(globalvars.CONSOLE_LOG_LEVEL)
    onlyConsoleHandler.setFormatter(logConsoleFormatter)

    # Remove existing handlers if present
    defaultLogger.handlers = []
    onlyConsoleLogger.handlers = []

    if(globalvars.only_print_samples):
        # If only_print_samples, print only ERRORS or CRITICAL messages
        defaultConsoleHandler.setLevel(40)

    # If quiet, set the level very high to suppress all
    # messages in the console handlers.
    if(_quiet):
        defaultConsoleHandler.setLevel(1000)
        onlyConsoleHandler.setLevel(1000)

    # Add the handlers to the loggers
    defaultLogger.addHandler(defaultFileHandler)
    defaultLogger.addHandler(defaultConsoleHandler)
    onlyConsoleLogger.addHandler(onlyConsoleHandler)

class DefaultLoggingFormatter(logging.Formatter):
    """
    The logging.Formatter does not accept %f argument
    which returns microseconds because it is using
    struct_time.

    This class, uses datetime instead, to provide microsecond
    precision in logging time.
    """

    converter=datetime.datetime.fromtimestamp
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime("%Y-%m-%d %H:%M:%S")
            s = "%s,%03d" % (t, record.msecs)
        return s

class VisualFormatter(DefaultLoggingFormatter):
    """
    This visual formatter allows the user to
    Define different formats and date formats
    for different Log Levels

    fmt sets the global format

    datefmt sets the global date format

    xxx_fmt sets the format for each xxx level

    xxx_datefmt set the date format for each xxx level
    """
    def __init__(self, fmt=None, datefmt=None,
                 dbg_fmt=None, dbg_datefmt=None,
                 info_fmt=None, info_datefmt=None,
                 warn_fmt=None, warn_datefmt=None,
                 err_fmt=None, err_datefmt=None,
                 crit_fmt=None, crit_datefmt=None):

        # If fmt is set, instantiate the format
        # for each level to this of fmt
        # Otherwise set the default values
        if(fmt is not None):
            self._dbg_fmt = fmt
            self._info_fmt = fmt
            self._warn_fmt = fmt
            self._err_fmt = fmt
            self._crit_fmt = fmt
        else:
            self._dbg_fmt = "[{0}] {1}".format("%(levelname)8s", "%(message)s")
            self._info_fmt = "%(message)s"
            self._warn_fmt = self._dbg_fmt
            self._err_fmt = self._dbg_fmt
            self._crit_fmt = self._dbg_fmt

        # If each individual format has been set
        # then choose this one for each specific level
        if(dbg_fmt):
            self._dbg_fmt = dbg_fmt
        if(info_fmt):
            self._info_fmt = info_fmt
        if(warn_fmt):
            self._warn_fmt = warn_fmt
        if(err_fmt):
            self._err_fmt = err_fmt
        if(crit_fmt):
            self._crit_fmt = crit_fmt

        # instantiate the date format for each level
        # to this of datefmt
        self._dbg_datefmt = datefmt
        self._info_datefmt = datefmt
        self._warn_datefmt = datefmt
        self._err_datefmt = datefmt
        self._crit_datefmt = datefmt

        # If each individual date format has been set
        # then choose this one for each specific level
        if(dbg_datefmt):
            self._dbg_datefmt = dbg_datefmt
        if(info_datefmt):
            self._info_datefmt = info_datefmt
        if(warn_datefmt):
            self._warn_datefmt = warn_datefmt
        if(err_datefmt):
            self._err_datefmt = err_datefmt
        if(crit_datefmt):
            self._crit_datefmt = crit_datefmt


    def format(self, record):

        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            self.datefmt = self._dbg_datefmt
            self._fmt = self._dbg_fmt
        elif record.levelno == logging.INFO:
            self.datefmt = self._info_datefmt
            self._fmt = self._info_fmt
        elif record.levelno == logging.WARNING:
            self.datefmt = self._warn_datefmt
            self._fmt = self._warn_fmt
        elif record.levelno == logging.ERROR:
            self.datefmt = self._err_datefmt
            self._fmt = self._err_fmt
        elif record.levelno == logging.CRITICAL:
            self.datefmt = self._crit_datefmt
            self._fmt = self._crit_fmt

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        return result
