                         sysdata-collector

Motivation
----------
Have you ever faced the need to quickly collect performance/system
data in a simple structured way which is easy to read and parse by
other programs?
 - For evaluating an experiment?
 - A prototype?
 - Your thesis maybe?
 - A newly developed project that you need to know its overhead or
   how it affects your whole system(s)?
 - Simply want to get some quick statistics for your system(s)?

If yes, how many times did you search for simple, lightweight
existing solutions to monitor CPU/Memory/Network or other statistics,
and eventually ended up writing your own scripts to fit your needs?

Many advanced system monitoring solutions exist out there, but
most of them use either cryptic/binary formats, or databases
to store the collected data. Furthermore, they have a bunch of
dependencies and installation overhead. Eventually it is really time
consuming to setup and use for a quick short/one time experiment.

So if you:
 - need something simple, without the need to invest too much time
   to setup a sophisticated infrastructure and learn how it works
   just to collect your data.
 - need to collect data in a structured, human readable format for
   quick evaluation.
 - don't want to write additional scripts to extract the collected
   data from databases or "weird" formats to simple readable formats
   like comma/tab separated files (which are supported by most of
   the plotting programs like spreadsheets, or programming languages
   like R [http://www.r-project.org/] and GNU Octave
   [https://www.gnu.org/software/octave/]).
 - need something reusable and modular (you might need only CPU
   statistics for one of your experiments, but both CPU and Network
   statistics for another one)

Then sysdata-collector should fit your needs.


What is it?
-----------

Sysdata-collector is a python program that uses plugins for data
collection and optionally save the output in a X (where X is a
character, usually comma, or tab) separated file.
A few plugins to collect commonly used statistics (CPU, Network)
come bundled, but you can easily write your own plugins to collect
any kind of data. sysdata-collector will aggregate the output
of the activated plugins, and save it in a file or print it in the
standard output (STDIO).
The purpose of this program is to remain simple so that one can
simply copy it in the system where data needs to be collected and
start collecting data immediately.
Just focus on the data collection and not on how to setup the system
which is going to collect your data.


The Latest Version
------------------

Details of the latest version can be found on the sysdata-collector
project page under http://.....github..../.


Documentation
-------------

The documentation can be found at
http://add_github_link/.


Installation
------------

Installation instructions


Usage Examples
------------

Add usage examples


Licensing
---------

Please see the file called LICENSE


Copyright (C)
-------------

2014
Vangelis Tasoulas <vangelis@tasoulas.net>
