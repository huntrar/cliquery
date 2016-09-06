cliquery |PyPI Version| |Build Status| |PyPI Monthly downloads|
===============================================================

a command-line browser interface
--------------------------------

cliquery cuts down on clicking through command-line web searching, page
previewing, and page bookmarking, among other features. An interactive
prompt allows users to easily make successive queries and enter program
flags dynamically; simply typing help will list all possible flags to
enter. Opening a link will invoke a browser supplied by the user or
detected automatically across Windows, OSX, and Linux platforms.

Installation
------------

::

    pip install cliquery

or

::

    pip install git+https://github.com/huntrar/cliquery.git#egg=cliquery

or

::

    git clone https://github.com/huntrar/cliquery
    cd cliquery
    python setup.py install

If you encounter issues installing lxml, see
`here <http://lxml.de/installation.html>`__.

Recommended setup
-----------------

Sign up for a `Google Custom Search API
key <https://code.google.com/apis/console>`__ to access Google results,
otherwise search results will come from Bing.

Upon signing into Google, click on API Manager, then Credentials, and
create an API key. Enter this under the 'google\_api\_key' field in
.cliqrc.

Next, `create a custom search engine <https://cse.google.com/all>`__.
You must choose at least one site to search during creation (I chose
stackoverflow.com), but to search the entire web you must click on this
new search engine, go to Setup, then Basics, and select 'Search the
entire web but emphasize included sites.' Then you may choose to keep or
delete the site you originally provided.

After creating a custom search engine, click on the engine, go to Setup,
and under Details click Search engine ID. Enter this under the
'google\_engine\_key' field in .cliqrc.

To use cliquery for scientific computations, sign up for a `WolframAlpha
API key <https://developer.wolframalpha.com/portal/apisignup.html>`__
and enter this under the 'wolfram\_api\_key' field in .cliqrc.

A browser may be explicitly chosen by entering the executable name under
the 'browser' field in .cliqrc (if you do not set a browser, one will be
detected automatically). An alternative method of setting your browser
is with the BROWSER environment variable.

It is advised to copy the blank .cliqrc into .local.cliqrc, as .cliqrc
will be emptied after a program update. To do this, enter the following:

::

    cd "$(dirname "$(cliquery -c)")"
    sudo cp .cliqrc .local.cliqrc

Users may also import Firefox or Chrome bookmarks into .cliqrc by
exporting the bookmarks to HTML and importing to cliquery with the -i
flag. The imported bookmarks will be added to your existing bookmarks,
which may result in duplicates.

Usage
-----

::

    usage: cliquery.py [-h] [-b] [-c] [-C] [-d] [-e] [-f] [-i [IMPORT]] [-o] [-p]
                       [-s] [-v] [-w]
                       [QUERY [QUERY ...]]

    a command-line browser interface

    positional arguments:
      QUERY                 keywords to search

    optional arguments:
      -h, --help            show this help message and exit
      -b, --bookmark        view and modify bookmarks
      -c, --config          print config file location
      -C, --clear-cache     clear the cache
      -d, --describe        summarize links
      -e, --edit            edit config file
      -f, --first           open first link
      -i [IMPORT], --import [IMPORT]
                            import bookmarks from file
      -o, --open            directly open links
      -p, --print           print links to stdout
      -s, --search          search for links
      -v, --version         display current version
      -w, --wolfram         search WolframAlpha

Author
------

-  Hunter Hammond (huntrar@gmail.com)

Notes
-----

-  Supports both Python 2.x and Python 3.x.
-  NOTE: If you receive the following message (or similar) when trying
   to modify bookmarks:

   ::

       IOError: [Errno 13] Permission denied: '/usr/local/lib/python2.7/dist-packages/cliquery/.cliqrc'

   Then you have two options:

   ::

       1. (recommended) Change file ownership from root to user by entering the following:

               sudo chown $USER "$(cliquery -c)" 

       2. Execute cliquery as root, using su or sudo.

-  A search may return immediate results, such as calculations or facts
   made possible by WolframAlpha, or instead a page of Google search
   results comprised of links and their descriptions.
-  Interactive usage allows the user to continue making new queries by
   dynamically executing new program flags and/or queries. Entering h or
   help will list all possible prompt commands.

   ::

       + + + + + + + + + + + + + + + + + + + + + + + + + + + +
       1. Guido van Rossum - Official Site
       2. Images of python guido   
       3. Guido van Rossum - Wikipedia, the free encyclopedia
       4. Guido van Rossum (@gvanrossum) | Twitter
       5. Guido van Rossum Wants to Bring Type Annotations to Python
       6. The Python Tutorial — Python 2.7.10 documentation
       7. Python (programming language) - Wikipedia, the free ...
       8. Van Rossum: Python is not too slow | InfoWorld
       + + + + + + + + + + + + + + + + + + + + + + + + + + + +
       : d 1

       Guido's Personal Home Page     Guido van Rossum - Personal Home Page  "Gawky and proud of it."
       Dutch spelling rules dictate that when used in combination with myfirst name, "van" is not capitalized: "Guido van Rossum".
       But when mylast name is used alone to refer to me, it is capitalized, forexample: "As usual, Van Rossum was right."
       More Hyperlinks   Here's a collection of  essays  relating to Pythonthat I've written, including the foreword I wrote for Mark Lutz' book"Programming Python".
       The Audio File Formats FAQ  I was the original creator and maintainer of the Audio File FormatsFAQ.  It is now maintained by Chris Bagwellat  http://www.cnpbagwell.com/audio-faq .
       [Press Enter to continue..]

-  To choose multiple links at once, a range may be specified by
   separating the start and end range with a dash. Leaving one end of
   the range blank will choose all links until the other end of that
   range. For example, given 10 links, entering 5- would effectively be
   the same as entering 5-10.
-  Requests cache is enabled by default to cache webpages, it can be
   disabled by setting the environment variable CLIQ\_DISABLE\_CACHE.
-  Using the bookmark flag with no arguments will list all current
   bookmarks in .cliqrc, naturally ordered by time of entry. Entering
   help with the flag will list all possible commands including open,
   add, remove, tag/untag (for aliasing), describe, and move. Bookmarks
   like other flags may be entered during runtime in the link prompt.
-  Additional arguments may be appended to bookmarks while opening them.
   These are interpreted as any non-integer arguments which are not
   found in any bookmarks (URLs or tags).

.. |PyPI Version| image:: https://img.shields.io/pypi/v/cliquery.svg
   :target: https://pypi.python.org/pypi/cliquery
.. |Build Status| image:: https://travis-ci.org/huntrar/cliquery.svg?branch=master
   :target: https://travis-ci.org/huntrar/cliquery
.. |PyPI Monthly downloads| image:: https://img.shields.io/pypi/dm/cliquery.svg?style=flat
   :target: https://pypi.python.org/pypi/cliquery
