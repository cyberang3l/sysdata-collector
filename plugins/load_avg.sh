#!/bin/bash

print_load_avg () {
    for i in 1 5 15; do
        echo $i $1
	shift
    done
}

print_load_avg $(cat /proc/loadavg)
