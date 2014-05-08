#!/usr/bin/env python
#
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
import re
import yapsy
import logging
import time
import traceback
from datetime import datetime, timedelta
from yapsy.PluginFileLocator import PluginFileLocator, PluginFileAnalyzerWithInfoFile
from yapsy.PluginManager import PluginManager, IPluginLocator
from libs import globalvars
from libs import parseoptions
from libs.helperfuncs import *
from libs.collector import DataCollector
from threading import Thread
from ConfigParser import SafeConfigParser
from distutils.version import StrictVersion
try:
    from collections import OrderedDict
except ImportError:
    # python 2.6 or earlier, use backport
    from ordereddict import OrderedDict

# Anything printed with LOG, it will be logged in a log file and it may be printed
# (depending on the log level chosen) to the console as well.
LOG = logging.getLogger('default.' + __name__)

# Use LOG_CONSOLE mostly to print info that you do not want to spam your log files
# LOG_CONSOLE is used to print the collected data to stdout. The actual data is
# already collected in a separate file, so there is no need to spam your log file.
LOG_CONSOLE = logging.getLogger('console.' + __name__)

sys.dont_write_bytecode = True

class Main(object):

    plugin_manager = PluginManager()
    DataCollectors = OrderedDict()
    ActiveDataCollectors = OrderedDict()
    #----------------------------------------------------------------------
    def __init__(self):
        # Parse configuration files and command line options
        parseoptions.parse_all_conf()

        # Define the directories to be scanned for candidate plugins
        # First find plugins located in current directory
        this_dir = os.path.join(os.getcwd(), 'plugins')
        # Then find plugins located in the user's home directory
        home_dir = os.path.join(os.path.expanduser('~'), '.' + globalvars.PROGRAM_NAME + '/plugins')
        # Last find system wide plugins located in /etc
        system_dir = os.path.join('/etc/' + globalvars.PROGRAM_NAME + '/plugins')
        globalvars.plugin_directories.append(this_dir)
        globalvars.plugin_directories.append(home_dir)
        globalvars.plugin_directories.append(system_dir)

        # Create plugin analyzers for different types of plugins
        # Do not add a dot before the extension.
        DataCollectorsPA = PluginFileAnalyzerWithInfoFile('DataCollectors', extensions='metaconf')
        PluginAnalyzers = [DataCollectorsPA]

        # Configure Plugin Locator
        PL = PluginFileLocator(analyzers=PluginAnalyzers)
        PL.setPluginPlaces(globalvars.plugin_directories)

        # Create plugin manager
        self.plugin_manager.setPluginLocator(PL)
        self.plugin_manager.setCategoriesFilter({
            "DataCollectors": DataCollector
        })

        # Load available plugins
        LOG.debug('Locating plugins')
        candidates, num = self.plugin_manager.locatePlugins()
        self.plugin_manager.loadPlugins()

        # Check if any plugins were found
        if(num == 0):
            LOG.critical('No plugins found. The following directories were checked:')
            for dir_ in globalvars.plugin_directories:
                LOG.critical("'" + dir_ + "'")

            LOG.critical('for the following plugin extensions:')
            for PA in PluginAnalyzers:
                for ext in PA.expectedExtensions:
                    LOG.critical("'*" + ext + "'")

            LOG.critical('Please check if your plugins are placed in the proper directory and make sure they have the proper extension.')
            LOG.critical('The program will now exit.')
            exit(globalvars.exitCode.FAILURE)

        self.get_available_plugins()


    #----------------------------------------------------------------------
    def get_available_plugins(self):
        """
        Get the available plugins and store them in self.DataCollectors.

        Plugins are read in order from different directories (desribed below), and
        if a plugin with the same name and version is encountered in more than one
        of the directories, only the one loaded first will be loaded.

        Same plugins of different versions will always be loaded.

        Note that the plugin loading will only expose the available plugins to the
        program. It will not activate them as well! To activate certain plugins for
        a specific experiment, create symbolic links (ln -s) from the loaded
        plugins (get a list of the loaded plugins by running the program with the
        option --list-available-plugins) in the "active-directory" folder.
        To check which plugins are taking part in the data collection use the option
        --list-active-plugins

        The plugins will be read from the following directories in order:
            * User provided 'plugins' directory through the configuration
              file option custom_plugins_dir, or the option --custom-plugins-dir
            * The plugins folder located in the current directory (./plugins)
            * The user's home directory in ~/.sysdata-collector/plugins
            * The system directory /etc/sysdata-collector/plugins
        """

        LOG.info("Getting available plugins in the system...")
        for plugin in self.plugin_manager.getPluginsOfCategory("DataCollectors"):
            if(isinstance(plugin, yapsy.PluginInfo.PluginInfo)):
                plugin_key_name = (plugin.name + '_' + str(plugin.version)).replace(' ', '_')
                if(plugin_key_name not in self.DataCollectors.keys()):
                    # Store the plugin in self.DataCollectors
                    self.DataCollectors[plugin_key_name] = {}
                    self.DataCollectors[plugin_key_name]['plugin'] = plugin.plugin_object
                    # Pass the metaconf file in the plugin.config variable, so that the
                    # plugin can access the configuration file
                    self.DataCollectors[plugin_key_name]['plugin'].config = plugin.details
                    # Also name, version and path
                    self.DataCollectors[plugin_key_name]['plugin'].name = plugin.name
                    self.DataCollectors[plugin_key_name]['plugin'].version = plugin.version
                    self.DataCollectors[plugin_key_name]['plugin'].path = plugin.path
                    self.DataCollectors[plugin_key_name]['info'] = plugin
                    self.DataCollectors[plugin_key_name]['order'] = 0
                    LOG.debug(4 * ' ' + "Found plugin: '" + plugin.name + " Version " + str(plugin.version) + "': " + plugin.path)
                else:
                    LOG.debug("Duplicate plugin found and it will not be loaded: '" + plugin.name + " Version " + str(plugin.version) + "': " + plugin.path)
                    LOG.debug("Plugin already loaded from: '" + self.DataCollectors[plugin_key_name]['info'].path)
        LOG.info(str(len(self.DataCollectors)) + ' plugins available.')
        # Sort self.DataCollectors by plugin name and version
        self.DataCollectors = OrderedDict(sorted(self.DataCollectors.iteritems(), key=lambda x: (x[1]['info'].name, x[1]['info'].version)))

        counter = 0
        for plugin in self.DataCollectors.values():
            counter += 1
            plugin['order'] = counter


    #----------------------------------------------------------------------
    def list_available_plugins(self):
        """
        Prints a list with the available plugins to the user

        Do not use the LOG module since this is a short interactive operation
        which is not going to be used when the program is running in daemon mode
        """
        print_(globalvars.PRINT_SEPARATOR)
        print_("List of available plugins:")
        for key, plugin in self.DataCollectors.items():
            print_(4 * " " + str(plugin['order']) + ": '" + plugin['info'].name + " v" + str(plugin['info'].version) + "' located at '" + plugin['info'].path + "'")
            print_(8 * " " + " " * len(str(plugin['order'])) + "Module name: '" + os.path.basename(plugin['info'].path) + "'")
            print_(8 * " " + " " * len(str(plugin['order'])) + "Identifier name: '" + key + "'")


    #----------------------------------------------------------------------
    def list_active_plugins(self):
        """
        Prints a list with the active plugins to the user

        Do not use the LOG module since this is a short interactive operation
        which is not going to be used when the program is running in daemon mode
        """
        print_(globalvars.PRINT_SEPARATOR)
        print_("List of active plugins in directory '" + globalvars.active_plugins_dir + "'")
        for symlink_key in self.ActiveDataCollectors:
            plugin = self.ActiveDataCollectors[symlink_key]
            print_(4 * " " + str(plugin['order']) + ": '" + plugin['name'] + " v" + str(plugin['info'].version) + "' located at '" + plugin['info'].path + "'")
            print_(8 * " " + " " * len(str(plugin['order'])) + "Module name: '" + os.path.basename(plugin['info'].path) + "'")
            print_(8 * " " + " " * len(str(plugin['order'])) + "Symlink loading this instance: '" + symlink_key + "'")


    #----------------------------------------------------------------------
    def activate_plugins_in_active_dir(self):
        """
        Activate all plugins with symbolic links under the active directory
        """
        LOG.debug(globalvars.PRINT_SEPARATOR)
        LOG.info("Activating symlinked plugins located in '" + globalvars.active_plugins_dir + "'")
        activated_num = 0
        if(not os.path.isdir(globalvars.active_plugins_dir)):
            LOG.critical("'" + globalvars.active_plugins_dir + "' is not a valid directory. (Is the directory present?)")
            exit(globalvars.exitCode.FAILURE)

        for symlinked_plugin_name in os.listdir(globalvars.active_plugins_dir):
            symlinked_plugin = os.path.abspath(os.path.join(globalvars.active_plugins_dir, symlinked_plugin_name))
            if(os.path.islink(symlinked_plugin)):
                LOG.debug("Found symlink: '" + symlinked_plugin + "'")
                real_plugin_path = os.path.realpath(symlinked_plugin)
                for plugin in self.plugin_manager.getPluginsOfCategory("DataCollectors"):
                    if(isinstance(plugin, yapsy.PluginInfo.PluginInfo)):
                        if(real_plugin_path == plugin.path):
                            # TODO: check for duplicate headers and warn the user!
                            LOG.debug("Symlink is pointing on a valid plugin: '" + real_plugin_path + "'")
                            ConfigSection = 'SupportOptions'
                            # Check if the plugin requires a specific minimum kernel version to run properly
                            if(plugin.details.has_section(ConfigSection)):
                                ConfigSectionOption = 'Required_Kernel'
                                if(plugin.details.has_option(ConfigSection, ConfigSectionOption)):
                                    min_required_kernel = get_kernel_version(plugin.details.get(ConfigSection, ConfigSectionOption))[0]
                                    if(min_required_kernel is not None):
                                        current = get_kernel_version()[0]
                                        if (StrictVersion(current) < StrictVersion(min_required_kernel)):
                                            LOG.error("Failed to activate plugin '" + plugin.name + "'")
                                            LOG.error("The running kernel (" + current + ") version is older then the one required (" + min_required_kernel + ") by plugin '" + plugin.name + "'")
                                            LOG.error("Please remove the symbolic link '" + symlinked_plugin + "', or get a version of the plugin to support your running Linux Kernel")
                                            exit(globalvars.exitCode.FAILURE)
                                    else:
                                        LOG.error("Not a valid 'Required_Kernel' version number defined for plugin '" + plugin.name + "'")
                                        exit(globalvars.exitCode.FAILURE)

                            # The plugin needs to be activated.
                            # When a plugin is activated, the main configuration file will be read
                            # The main configuration file is the .metaconf for each plugin.
                            plugin.plugin_object.activate()
                            activated_num+=1
                            LOG.debug(4 * ' ' + "'" + plugin.name + " Version " + str(plugin.version) + "' activated")
                            if(plugin.author is not "None"):
                                LOG.debug(4 * ' ' + "Author: " + plugin.author)
                            if(plugin.website is not "None"):
                                LOG.debug(4 * ' ' + "Website: " + plugin.website)

                            # Get the filename of the potentially existing configuration file
                            # for this plugin. If this file exist in the active directory, it
                            # will override options already read by the main configuration file.
                            active_plugin_conf_file = os.path.abspath(os.path.join(globalvars.active_plugins_dir, symlinked_plugin_name[0:-3] + '.conf'))

                            # If a configuration file exists in the active directory
                            # load it and override existing options
                            if(os.path.exists(active_plugin_conf_file)):
                                LOG.debug('Additional configuration file found for ' + plugin.name + ': ' + active_plugin_conf_file)
                                validate_config = SafeConfigParser()
                                validate_config.read(active_plugin_conf_file)
                                # Validate if it is a valid conf file in the active directory
                                # A valid conf file in the active directory should contain a 'Plugin' section
                                if(not validate_config.has_section('Plugin')):
                                    LOG.error("The plugin configuration file '" + active_plugin_conf_file + "' doesn't have any 'Plugin' section.")
                                    LOG.error("'Plugin' section is necessary as long as you have a config file in the active directory")
                                    exit(globalvars.exitCode.FAILURE)
                                plugin.plugin_object.config.read(active_plugin_conf_file)
                                # Re-run readConfigVars() function since a new configuration has been loaded
                                # This is necessary to override configuration with directives from the newly
                                # loaded conf
                                plugin.plugin_object.readConfigVars()

                            self.ActiveDataCollectors[symlinked_plugin] = {}
                            self.ActiveDataCollectors[symlinked_plugin]['plugin'] = plugin.plugin_object
                            self.ActiveDataCollectors[symlinked_plugin]['order'] = activated_num
                            self.ActiveDataCollectors[symlinked_plugin]['info'] = plugin
                            self.ActiveDataCollectors[symlinked_plugin]['name'] = plugin.name

        if(activated_num):
            # Sort self.ActiveDataCollectors by ['order'] number
            self.ActiveDataCollectors = OrderedDict(sorted(self.ActiveDataCollectors.iteritems(), key=lambda x: x[1]['order']))
            LOG.info(str(activated_num) + " plugin(s) activated")
            LOG.debug(globalvars.PRINT_SEPARATOR)
        else:
            LOG.info("No plugins found to be activated")
            LOG.info("Place some symbolic links in '" + globalvars.active_plugins_dir + "'")
            LOG.info("Here is a list of the available plugins that you can activate: ")
            self.list_available_plugins()
            exit(globalvars.exitCode.FAILURE)


#----------------------------------------------------------------------
def runCollectThreaded(toRun, result, key, prevResults):
    """
    Function ro run the collect jobs in threads.
    toRun:        The plugin to be executed
    results:      The dictionary to store the result
    key:          The key in dict results to store the result
    prevResults:  The previous results of this plugin
    """
    result[key] = toRun.collect(prevResults)


#----------------------------------------------------------------------
def main():
    # Load the main class
    main = Main()

    # if --plugin-test plugin.py option is passed, print the returned results and headers of the plugin
    if(globalvars.test_plugin):
        for name, datacollector in main.DataCollectors.items():
            if(isinstance(datacollector['info'], yapsy.PluginInfo.PluginInfo)):
                if(name == globalvars.test_plugin):
                    if(isinstance(datacollector['plugin'], DataCollector)):
                        print_("Testing plugin '" + datacollector['info'].name + " v" + str(datacollector['info'].version) + "' which is located in '" + datacollector['info'].path + "'" )
                        testPlugin(datacollector['plugin'])
                        exit(globalvars.exitCode.SUCCESS)
        # If this point of execution is reached, it means that the plugin was not found.
        print_("Plugin '" + globalvars.test_plugin + "' was not found. Make sure you typed the plugin module name correctly.")
        print_("Here is a list of the available plugins. Use the 'Module name' of the corresponding plugin to test it.")
        main.list_available_plugins()
        exit(globalvars.exitCode.FAILURE)

    # If the --list-available-plugins option is passed, list the available plugins and exit
    if(globalvars.list_available_plugins):
        main.list_available_plugins()
        exit(globalvars.exitCode.SUCCESS)

    # Activate the plugins in the given folder
    main.activate_plugins_in_active_dir()

    # If the --list-active-plugins option is passed, list the available plugins and exit
    if(globalvars.list_active_plugins):
        main.list_active_plugins()
        exit(globalvars.exitCode.SUCCESS)

    orig_output_file = globalvars.output_file
    counter = 1
    while(os.path.exists(globalvars.output_file)):
        if(not os.path.isdir(globalvars.output_file)):
            if(globalvars.append_file):
                # Use the existing file to append the data
                break
            else:
                # Generate a new filename
                LOG.debug("'" + globalvars.output_file + "' exists and it will not be appended")
                globalvars.output_file = orig_output_file + "-" + str(counter).zfill(3)
                LOG.debug("Trying '" + globalvars.output_file + "'...")
                counter += 1
        else:
            LOG.critical("The given output file '" + globalvars.output_file + "' is a directory. Please specify a file.")
            exit(globalvars.exitCode.FAILURE)
    del orig_output_file

    LOG.info(globalvars.PROGRAM_NAME + " " + globalvars.VERSION + " started...")

    # If we are writing in a file, print this information to the user
    if not globalvars.only_print_samples:
        if(globalvars.append_file):
            LOG.info("Appending data to file '" + globalvars.output_file + "'")
        else:
            LOG.info("Saving data to file '" + globalvars.output_file + "'")
    initDataCollection(main)


#----------------------------------------------------------------------
def testPlugin(plugin):
    plugin.activate()
    plugin.getHeaders(globalvars.delimiter)
    plugin.print_()
    print_(globalvars.PRINT_SEPARATOR)
    print_("The flattened headers of your plugin will look like this:")
    print_("")
    plugin.print_(headers=True)


#----------------------------------------------------------------------
def initDataCollection(main):
    # Open the file for writing/appending
    handle = sys.stdout
    try:
        f = open(globalvars.output_file, mode='a') if not globalvars.only_print_samples else sys.stdout

        # Collect the header line and the 'prevResults'
        Sample, line = collectHeaders(main)

        # If we write in a file....
        if not globalvars.only_print_samples:
            # If f.tell() == 0, it means that the file has nothing in it.
            # So we need to print the headers
            if(f.tell() == 0):
                f.write(line + "\n")
                LOG_CONSOLE.info(line)
            # TODO: When appending an existing file (if(f.tell() != 0)),
            # check if the columns match (check the number of columns and
            # existing headers)
        else:
            f.write(line + "\n")

        # Sleep only for one second for the very first time
        # The first run is only here for header printing and for initilizing the prevResults
        # in case any of the plugins need it
        time.sleep(1)

        # Enter in an infinite data collection loop
        while 1:
            Sample, line, datetime_started_collection = collectData(main, Sample)

            timestamp_for_next_execution = (datetime_started_collection + timedelta(seconds=globalvars.intervalBetweenSamples)).strftime('%s%f')

            f.write(line + "\n")
            # If file descriptor is sys.stdout, there is no need to reprint the output
            if not globalvars.only_print_samples:
                LOG_CONSOLE.info(line)

            # Get the sleeping time until next execution
            sleep_for = (float(timestamp_for_next_execution) - float(datetime.utcnow().strftime('%s%f'))) / 1000000

            # sleep_for is less or equal to 0, continue with the execution. No need to wait.
            if(sleep_for > 0):
                time.sleep(sleep_for)
    except KeyboardInterrupt:
        print("\n")
        LOG.info("Collection stopped")
        exit(globalvars.exitCode.FAILURE)
    except:
        LOG.critical(traceback.format_exc())
        exit(globalvars.exitCode.FAILURE)
    finally:
        if handle is not sys.stdout:
            handle.close()


#----------------------------------------------------------------------
def collectHeaders(main):
    # Store the samples from all plugins in the Sample dict
    Sample = {}

    # Declare a 'threads' dict to store the threads
    threads = {}

    # Read the headers and collect samples once for the prevResults
    for symlink in main.ActiveDataCollectors:
        Sample[symlink] = {}
        Sample[symlink]['headers'] = main.ActiveDataCollectors[symlink]['plugin'].getHeaders(globalvars.delimiter)
        # Collect data from each plugin in a separate thread
        threads[symlink] = Thread(target=runCollectThreaded, args=(main.ActiveDataCollectors[symlink]['plugin'], Sample[symlink], 'prevResults', None))
        threads[symlink].start()

    line = ''
    last_value_in_dict = len(main.ActiveDataCollectors) - 1
    # Join the threads and generate the output line
    for i, symlink in enumerate(main.ActiveDataCollectors):
        # Wait for all of the threads to finish execution
        threads[symlink].join()
        del threads[symlink]

        # If it is the very first iteration, print the datetine and unix timestamp
        if i == 0:
            line += 'datetime' + globalvars.delimiter + 'timestamp' + globalvars.delimiter

        if Sample[symlink]['headers']:
            if i == last_value_in_dict:
                line += Sample[symlink]['headers']
            else:
                line += Sample[symlink]['headers'] + globalvars.delimiter

    return Sample, line


#----------------------------------------------------------------------
def collectData(main, Sample):
    # Get the current time (it will be used to provide timestamps)
    dt = datetime.utcnow()
    timestamp_started_collection = dt.strftime('%s%f')
    datetime_started_collection = dt.strftime('%Y-%m-%d_%H:%M:%S')

    # Declare a 'threads' dict to store the threads
    threads = {}

    # Start all of the data collection jobs in parallel threads
    for symlink in main.ActiveDataCollectors:
        threads[symlink] = Thread(target=runCollectThreaded, args=(main.ActiveDataCollectors[symlink]['plugin'], Sample[symlink], 'currentResults', Sample[symlink]['prevResults']))
        threads[symlink].start()

    line = ''
    last_value_in_dict = len(main.ActiveDataCollectors) - 1
    # Join the threads and generate the output line
    for i, symlink in enumerate(main.ActiveDataCollectors):
        threads[symlink].join()
        del threads[symlink]
        # If it is the very first iteration, print the datetine and unix timestamp
        if i == 0:
            line += datetime_started_collection + globalvars.delimiter + timestamp_started_collection + globalvars.delimiter

        flat_dict = flatten_nested_dicts(Sample[symlink]['currentResults'])
        last_value_in_flat_dict = len(flat_dict) - 1
        for j, key in enumerate(flat_dict):
            if flat_dict[key]:
                if i == last_value_in_dict and j == last_value_in_flat_dict:
                    line += str(flat_dict[key])
                else:
                    line += str(flat_dict[key]) + globalvars.delimiter
                Sample[symlink]['prevResults'] = Sample[symlink]['currentResults']

    return Sample, line, dt


#----------------------------------------------------------------------
if __name__ == '__main__':
    main()
