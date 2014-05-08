####################################
# Sysdata-collector Usage Examples #
####################################

* [Print a help message](#print-a-help-message)
* [Collect data and print the output in STDOUT](#collect-data-and-print-the-output-in-stdout)
* [List the available plugins](#list-the-available-plugins)
* [List the active plugins](#list-the-active-plugins)





### Print a help message

A list of the available command line options
```
$ sysdata-collector.py --help
usage: sysdata-collector.py [-h] [-v] [-a] [-b FILE] [-c CHAR] [-d] [-e]
                            [-f DIR_ACTIVE] [-g DIR_PLUGINS] [-i FLOAT] [-j]
                            [-k PLUGIN_IDENTIFIER_NAME] [-C CONF_FILE] [-D]
                            [-Q] [-L LOG_LEVEL] [-F LOG_FILE]

sysdata-collector version 0.0.1

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -a, --append-file     If the FILE exists, append to the end of the file.
                        Otherwise, create a new one with an extended filename.
  -b FILE, --output-file FILE
                        Filename to save the collected data file
  -c CHAR, --delimiter CHAR
                        CHAR is a single character to be used for field
                        separation in the output FILE
  -d, --list-available-plugins
                        Prints a list of the available plugins and exit
  -e, --list-active-plugins
                        Prints a list of the active plugins located under the
                        chosen active-directory and exit
  -f DIR_ACTIVE, --active-plugins-dir DIR_ACTIVE
                        Define the active-directory to load plugins from for
                        this experiment.
  -g DIR_PLUGINS, --custom-plugins-dir DIR_PLUGINS
                        Define a directory containing more plugins to be
                        loaded.
  -i FLOAT, --interval-between-sampling FLOAT
                        A FLOAT number which is the sleeping time given in
                        seconds between sampling. If the value is 0 or
                        negative, instant sampling will be initiated after
                        each previous one
  -j, --only-print-samples
                        Enabling this flag, will disable saving samples in a
                        file. They will only be printed instead.
  -k PLUGIN_IDENTIFIER_NAME, --test-plugin PLUGIN_IDENTIFIER_NAME
                        Use this option for debugging newly created plugins.
                        Get the plugin identified name by using the '--list-
                        available-plugins' option
  -C CONF_FILE, --conf-file CONF_FILE
                        CONF_FILE where the configuration will be read from
                        (Default: will search for file 'sysdata-
                        collector.conf' in the known predefined locations
  -D, --daemon          run in daemon mode

Logging Options:
  List of optional logging options

  -Q, --quiet           Disable logging in the console but still keep logs in
                        a file. This options is forced when run in daemon
                        mode.
  -L LOG_LEVEL, --loglevel LOG_LEVEL
                        LOG_LEVEL might be set to: CRITICAL, ERROR, WARNING,
                        INFO, DEBUG. (Default: INFO)
  -F LOG_FILE, --logfile LOG_FILE
                        LOG_FILE where the logs will be stored. If the file
                        exists, text will be appended, otherwise the file will
                        be created (Default: ./sysdata-collector.log)
```
-------

### Collect data and print the output in STDOUT

Start collecting data and print the output in STDOUT.
When `-j` is used, there is no output redirected in a file.

An example printout of my system with the `CPU` and `NET` plugins activated:
```
$ ./sysdata-collector.py -j
datetime,timestamp,eth0_rx_bytes,eth0_tx_bytes,eth0_rx_packets,eth0_tx_packets,eth0_rx_errs,eth0_tx_errs,eth0_rx_drop,eth0_tx_drop,wlan0_rx_bytes,wlan0_tx_bytes,wlan0_rx_packets,wlan0_tx_packets,wlan0_rx_errs,wlan0_tx_errs,wlan0_rx_drop,wlan0_tx_drop,cpus_avg_user,cpus_avg_nice,cpus_avg_system,cpus_avg_idle,cpus_avg_iowait,cpus_avg_irq,cpus_avg_softirq,cpus_avg_steal,cpus_avg_guest,cpus_avg_guest_nice,cpus_avg_percent,cpu_0_user,cpu_0_nice,cpu_0_system,cpu_0_idle,cpu_0_iowait,cpu_0_irq,cpu_0_softirq,cpu_0_steal,cpu_0_guest,cpu_0_guest_nice,cpu_0_percent,cpu_1_user,cpu_1_nice,cpu_1_system,cpu_1_idle,cpu_1_iowait,cpu_1_irq,cpu_1_softirq,cpu_1_steal,cpu_1_guest,cpu_1_guest_nice,cpu_1_percent,cpu_2_user,cpu_2_nice,cpu_2_system,cpu_2_idle,cpu_2_iowait,cpu_2_irq,cpu_2_softirq,cpu_2_steal,cpu_2_guest,cpu_2_guest_nice,cpu_2_percent,cpu_3_user,cpu_3_nice,cpu_3_system,cpu_3_idle,cpu_3_iowait,cpu_3_irq,cpu_3_softirq,cpu_3_steal,cpu_3_guest,cpu_3_guest_nice,cpu_3_percent,ctxt,btime,processes,procs_running,procs_blocked
2014-04-23_23:15:50,1398287750134953,148694350,3233934013,1246709,2226310,0,0,0,0,0,0,0,0,0,0,0,0,343849,2212,92796,4472905,28768,39141,0,0,0,0,7.91,85024,623,27732,1112266,6934,11735,0,0,0,0,18.18,90917,524,17971,1111823,6897,17252,0,0,0,0,1.03,86517,440,28476,1117942,6087,5113,0,0,0,0,5.1,81389,624,18616,1130872,8849,5039,0,0,0,0,5.21,28844656,1398282476,19703,3,0
```

-------

### List the available plugins

List the available plugins located in the `plugins` folder.
Keep in mind, that the plugins located in the `plugins`
folder are not active by default.

```
$ sysdata-collector.py --list-available-plugins 
Getting available plugins in the system...
5 plugins available.
#######################################
List of available plugins:
    1: 'CPU Stats v0.6.1' located at '/home/cyber/.sysdata-collector/plugins/cpu.py'
         Module name: 'cpu.py'
         Identifier name: 'CPU_Stats_0.6.1'
    2: 'External Plugins v0.1' located at '/home/cyber/.sysdata-collector/plugins/external_plugins.py'
         Module name: 'external_plugins.py'
         Identifier name: 'External_Plugins_0.1'
    3: 'Kernel Version v1.0' located at '/home/cyber/.sysdata-collector/plugins/kernel_version.py'
         Module name: 'kernel_version.py'
         Identifier name: 'Kernel_Version_1.0'
    4: 'Net Stats v0.4.1' located at '/home/cyber/.sysdata-collector/plugins/net.py'
         Module name: 'net.py'
         Identifier name: 'Net_Stats_0.4.1'
    5: 'New plugin template v0.0.1' located at '/home/cyber/.sysdata-collector/plugins/new_plugin_template.py'
         Module name: 'new_plugin_template.py'
         Identifier name: 'New_plugin_template_0.0.1'
```

-------

### List the active plugins

List of the active active plugins located in the `active-plugins` folder.
To activate a plugin which is available in the `plugins` folder,
generate a symbolic link in the active-plugins folder (`ln -s plugins/`)

```
$ sysdata-collector.py --list-active-plugins 
Getting available plugins in the system...
6 plugins available.
Activating symlinked plugins located in 'active-plugins'
3 plugin(s) activated
#######################################
List of active plugins in directory 'active-plugins'
    1: 'Net Stats v0.4.1' located at '/home/cyber/Programming/Python/sysdata-collector/plugins/net.py'
         Module name: 'net.py'
         Symlink loading this instance: '/home/cyber/Programming/Python/sysdata-collector/active-plugins/net.py'
    2: 'External Plugins v0.1' located at '/home/cyber/Programming/Python/sysdata-collector/plugins/external_plugins.py'
         Module name: 'external_plugins.py'
         Symlink loading this instance: '/home/cyber/Programming/Python/sysdata-collector/active-plugins/external_plugins.py'
    3: 'CPU Stats v0.6' located at '/home/cyber/Programming/Python/sysdata-collector/plugins/cpu.py'
         Module name: 'cpu.py'
         Symlink loading this instance: '/home/cyber/Programming/Python/sysdata-collector/active-plugins/cpu.py'
```