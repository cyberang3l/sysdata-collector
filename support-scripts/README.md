# sysdata-collector.bash-completion #
-------------------------------------
Script to provide bash completion for sysdata-collector. A prerequisite
for this script to work, is that the package `bash-completion` is already
installed in the system and bash completion is enabled for the user.

For debian based systems (if bash-completion is not already installed and
configured), you need to do the following steps:

`apt-get install bash-completion`

Add the following line in `~/.bashrc`
    
`. /etc/bash_completion`

### How to use ###
------------------
- If you have root access to the system, place the script in `/etc/bash_completion.d/`.

- If you do not have root access, place the script in the folder `~/.bash_completion/`
  (if the folder doesn't exist, create it) and add this line:

  `. ~/.bash_completion/sysdata-collector.bash-completion`

  at the end of the file `~/.bashrc`.