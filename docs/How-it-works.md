The working logic of sysdata-collector
--------------------------------------

##### 1. Parse configuration files and command line options

* All of the command line options have default values
* The default values are overridden if a `sysdata-collector.conf` file is found, or provided by `--conf-file` option
* Command line parameters are always overriding the default, or values read from a configuration file

##### 2. Find available plugins in the system

Plugins are read in order from different directories (desribed below), and if a plugin with the same name and version is encountered in more than one of the directories, only the one loaded first will be made available (so the order that the plugins are loaded is important).

Same plugins of different versions will always be loaded.

Note that the plugin loading will only expose the available plugins to the program. It will not activate them as well! To activate certain plugins for a specific experiment, create symbolic links (`ln -s`) from the loaded plugins (get a list with the paths of the loaded plugins by running the program with the option `--list-available-plugins`) into the **active-directory** folder.

The plugins will be read from the following directories in order:

* User provided 'plugins' directory through the configuration file option `custom_plugins_dir`, or command line option `--custom-plugins-dir`
* The plugins folder located in the current directory (`./plugins`)
* The user's home directory in `~/.sysdata-collector/plugins`
* The system directory `/etc/sysdata-collector/plugins`

##### 3. Activate plugins found under the "active-directory"

The active plugins will take part in the data collection.

You might have many plugins in the system, but you might not need all of them to collect data for a specific experiment. For this reason, you need to activate the plugins you want to be used by placing a symbolic link of each plugin, under the "**active-directory**". The active directory can be set by using the configuration file option  `active_plugins_dir` or command line option `--active-plugins-dir`.

To check which plugins are activated and take part in the data collection, use the option `--list-active-plugins`.

##### 4. Start data collection

Eventually the data collection will be started, and the data will be saved by default in the file `data_collected-%{ts}.csv`. `%{ts}` will be replaced with the current timestamp, when the data collection was started.

Sysdata-collector will not overwrite output files in any case. If the file exists, a new one with the same filename and a trailing '*-ddd*' (where *-ddd* is an incremented number) string will be created. If you want to overwrite a file, delete it or move it in a different folder manually, and then run the program.

However, you can append data to an existing file by using the option `--append-file`, and choosing the file you want to append to, by using the option `--output-file FILE`.

If you do not want to save the collected data in a file, you can use the command line option `--only-print-samples`.