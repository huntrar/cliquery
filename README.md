# cliquery [![PyPI Version](https://img.shields.io/pypi/v/cliquery.svg)](https://pypi.python.org/pypi/cliquery) [![Build Status](https://travis-ci.org/huntrar/cliquery.svg?branch=master)](https://travis-ci.org/huntrar/cliquery) [![PyPI Monthly downloads](https://img.shields.io/pypi/dm/cliquery.svg?style=flat)](https://pypi.python.org/pypi/cliquery)


## a command-line browsing utility

cliquery cuts down on clicking through command-line web searching, page previewing, and page bookmarking, among other features. An interactive prompt allows users to easily make successive queries and enter program flags dynamically; simply typing help will list all possible flags to enter. Opening a link will invoke a browser supplied by the user or detected automatically.

## Installation
    pip install cliquery

or

    pip install git+https://github.com/huntrar/cliquery.git#egg=cliquery

or

    git clone https://github.com/huntrar/cliquery
    cd cliquery
    python setup.py install

It is recommended to [sign up](https://developer.wolframalpha.com/portal/apisignup.html) for a WolframAlpha API key and enter that and your preferred browser in .cliqrc (cygwin users *MUST* enter `cygwin` as their browser to avoid cross-platform conflicts).

It is also recommended to create a .local.cliqrc file to use in place of .cliqrc, as .cliqrc is overwritten when updating the program.

Do the following to copy .cliqrc to .local.cliqrc:

    cd "$(dirname "$(cliquery -c)")"
    sudo cp .cliqrc .local.cliqrc

## Usage
    usage: cliquery.py [-h] [-b] [-c] [-C] [-d] [-f] [-o] [-p] [-s] [-v] [-w]
                       [QUERY [QUERY ...]]
    
    a command-line browsing utility
    
    positional arguments:
      QUERY              keywords to search
    
    optional arguments:
      -h, --help         show this help message and exit
      -b, --bookmark     view and modify bookmarks
      -c, --config       print config file location
      -C, --clear-cache  clear the cache
      -d, --describe     summarize links
      -f, --first        open first link
      -o, --open         directly open links
      -p, --print        print links to stdout
      -s, --search       search for links
      -v, --version      display current version
      -w, --wolfram      search WolframAlpha

## Author
* Hunter Hammond (huntrar@gmail.com)

## Notes
* Supports both Python 2.x and Python 3.x.
* If you receive the following message (or similar) when trying to add or delete bookmarks:

    IOError: [Errno 13] Permission denied: '/usr/local/lib/python2.7/dist-packages/cliquery/.cliqrc'

Try entering the following to fix:

    sudo chmod a+x "$(cliquery -c)" && sudo chown $USER "$(cliquery -c)" 
* A search may return immediate results, such as calculations or facts, or instead a page of search results comprised of descriptive links to follow.
* Interactive use is as easy as passing the regular flag arguments into the link prompt; this overrides any preexisting flags and allows for more even more flexibility. Entering h or help will list all possible prompt commands.
    ```
    + + + + + + + + + + + + + + + + + + + + + + + + + + + +
    1. Guido van Rossum - Official Site
    2. Images of python guido   
    3. Guido van Rossum - Wikipedia, the free encyclopedia
    4. Guido van Rossum (@gvanrossum) | Twitter
    5. Guido van Rossum Wants to Bring Type Annotations to Python
    6. The Python Tutorial — Python 2.7.10 documentation
    7. Python (programming language) - Wikipedia, the free ...
    8. Van Rossum: Python is not too slow | InfoWorld
    9. GuiProgramming - Python Wiki
    + + + + + + + + + + + + + + + + + + + + + + + + + + + +
    : d 1

    Guido's Personal Home Page     Guido van Rossum - Personal Home Page  "Gawky and proud of it."
    Dutch spelling rules dictate that when used in combination with myfirst name, "van" is not capitalized: "Guido van Rossum".
    But when mylast name is used alone to refer to me, it is capitalized, forexample: "As usual, Van Rossum was right."
    More Hyperlinks   Here's a collection of  essays  relating to Pythonthat I've written, including the foreword I wrote for Mark Lutz' book"Programming Python".
    The Audio File Formats FAQ  I was the original creator and maintainer of the Audio File FormatsFAQ.  It is now maintained by Chris Bagwellat  http://www.cnpbagwell.com/audio-faq .
    [Press Enter to continue..]
    ```
* To choose multiple links at once, a range may be specified by separating the start and end range with a dash. Leaving one end of the range blank will choose all links until the other end of that range. For example, given 10 links, entering 5- would effectively be the same as entering 5-10.
* Using the bookmark flag with no arguments will list all current bookmarks in .cliqrc, ordered by time of entry. Entering help with the flag will list all possible commands including add, delete, tag/untag (for aliasing), move, and open. Bookmarks like other flags may be entered during runtime in the link prompt.
