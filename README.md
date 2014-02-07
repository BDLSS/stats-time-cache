stats-time-cache
================

Abstract method of caching statistical "event" so you can quickly generate comparisons  over multiple years, with tests to compare different collation options.

Initial Aims
============
1. To create a set of tests that can be used to time
how long a system takes to return results of certain summaries.

2. Create or load a test data set containing at least 4-10 years
worth of data.

3. An abstract front-end so you can use a single HTTP GET request to
query an underlying system which might require multiple requests.

4. Use 1 - 3 to test performance of Piwik API.

5. Enable 3 so it can run against various configuration of Piwik to
measure effects of adding indexes, etc. Changing Mysql setup.

6. Auto-generate a cache of data that can be generated at any time from
the raw data collected by Piwik which is read optimised for
time-based queries over multiple years and enable 3 to use it.

7. Enable logging of usage (processor/IO etc.) on the server during
tests, in addition to visual checks.

Summaries
=========
Task 1 will test:
A. Total views and downloads for a random selection of "objects".
B. Test certain "objects" where high usage is known to exist meaning
they are likely to be stored in various caches Piwik creates.
C. For a particular "object" extract total downloads for each month
over at least 1-10 years.

What are events?
================
This work originated with relation to obtaining summaries of views 
and downloads "events" of particular "objects" in an open access
repository. It is the main focus of this project.

However, if you redefine "events" there is the potential to use the
same collection and reporting method to automate production of
"library enquiry" statistics. So, an aim is to keep "events" generic.

How library staff record such "enquiry events" is out of the scope
of this project. (Previous work used a desktop application installed
on 100+ desktops to collect the data but you could use an intranet web
pages, a VLE or plugin to Intergrated Library System instead.)
