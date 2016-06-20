"""cliquery cuts down on clicking through command-line web searching,
   page previewing, and page bookmarking, among other features.

   An interactive prompt allows users to easily make successive queries and
   enter program flags dynamically; simply typing help will list all possible
   flags to enter. Opening a link will invoke a browser supplied by the user
   or detected automatically.
"""

import sys


__version__ = '1.7.5'

SYS_VERSION = sys.version_info[0]
# Python 2.x and 3.x compatible builtins
if SYS_VERSION == 2:
    input = raw_input
    range = xrange
else:
    input = input
    range = range

CONTINUE = '[Press Enter to continue..] '
SEE_MORE = 'See more? {0}'.format(CONTINUE)
