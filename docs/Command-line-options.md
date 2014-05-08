Command line options and their behavior
---------------------------------------
> -h, --help

Get a complete list of the command line options with a short explanation.

---

```

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