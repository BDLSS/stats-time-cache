stats-time-cache
================

Abstract method of caching statistical "event" so you can quickly generate comparisons  over multiple years, with tests to compare different collation options.

Initial Aims
============
1. To create a set of unit tests that can be used to time
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
