# cliquery

## a command-line browsing interface
cliquery bundles the more important features of a browser and the quickness of the command-line, supporting web searches, page previewing, bookmarking, and other useful features. An interactive interface allows users to make successive queries, eliminating the need to reinvoke the program each time. Simply typing help within the prompt lists all possibilities available to the user. When a link is finally chosen to be open, cliquery simply invokes the browser listed in its configuration file (or will attempt to find a default browser if none listed).

cliquery reduces needless clicking thus giving faster results, all without eliminating the use of a conventional browser!

## Installation
`pip install cliquery`

or

`pip install git+https://github.com/huntrar/cliquery.git#egg=cliquery`

or

`git clone https://github.com/huntrar/cliquery`
`cd cliquery`
`python setup.py install`

It is recommended you also [sign up](https://developer.wolframalpha.com/portal/apisignup.html) for a WolframAlpha API key and enter that and your preferred browser in your .cliqrc file (cygwin users *MUST* enter `cygwin` as their browser to avoid cross-platform conflicts).

## Usage
    usage: cliquery.py [-h] [-b] [-c] [-C] [-d] [-f] [-o] [-p] [-s] [-v] [-w]
                       [QUERY [QUERY ...]]
    
    a command-line browsing interface
    
    positional arguments:
      QUERY              keywords to search
    
    optional arguments:
      -h, --help         show this help message and exit
      -b, --bookmark     view and modify bookmarks
      -c, --config       print location of config file
      -C, --clear-cache  clear the cache
      -d, --describe     display page snippet
      -f, --first        open first link
      -o, --open         open link or browser manually
      -p, --print        print link to stdout
      -s, --search       display search links
      -v, --version      display current version
      -w, --wolfram      display wolfram results

## Author
* Hunter Hammond (huntrar@gmail.com)

## Notes
* Supports both Python 2.x and Python 3.x.
* If you receive the following message when trying to add bookmarks:
    ```
    IOError: [Errno 13] Permission denied: '/usr/local/lib/python2.7/dist-packages/cliquery/.cliqrc'
    ```
Enter the following to fix:
    ```
    sudo chmod a+x /usr/local/lib/python2.7/dist-packages/cliquery/.cliqrc
    ```
* A search may return immediate results, such as calculations or facts, or instead a page of search results comprised of descriptive links to follow.
* Interactive use is as easy as passing the regular flag arguments into the link prompt; this overrides any preexisting flags and allows for more even more flexibility. Entering h or help will list all possible prompt commands.
    ```
    + + + + + + + + + + + + + + + + + + + + + + + + + + + +
    1. A Simple Makefile Tutorial
    2. simple sentence - definition and examples of simple ...
    3. HTML Examples - W3Schools
    4. A Simple Guide to HTML - Welcome
    5. What Is Simple Future Tense With Example - Askives Docs
    6. A Simple Example: After Cache - How Caching Works
    7. Basic HTML Sample Page - Sheldon Brown
    8. ENG 1001: Sentences: Simple, Compound, and Complex
    + + + + + + + + + + + + + + + + + + + + + + + + + + + +
    : d 4


    http://www.simplehtmlguide.com/

    A Simple Guide to HTML
    html cheat sheet
    Welcome to my HTML Guide -- I hope you find it useful :)
    This easy guide for beginners covers several topics, with short and basic descriptions of the HTML tags you are likely to need when learning how to make your own website.
    See more? [Press Enter] 
    ```
* To choose multiple links at once, a range may be specified by separating the start and end range with a dash. Leaving one end of the range blank will choose all links until the other end of that range. For example, given 10 links, entering 5- would effectively be the same as entering 5-10.
* Using the bookmarks flag with no arguments will list all current bookmarks in .cliqrc, ordered by time of entry. Adding and deleting bookmarks can be done using add [url] or del [num] or [suburl], where [suburl] is a substring of the url. Opening bookmarks is done through the bookmarks flag and either a [num] or [suburl] argument. Bookmarks may also be added interactively through the link prompt by entering b [num].
