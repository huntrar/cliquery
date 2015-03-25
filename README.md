# CLIQuery

## a command line search engine and browsing tool
CLIQuery is an intermediary tool between the command line and any GUI based browser. It supports searching, browsing, bookmarking, and previewing webpages through a mix of command line output and browser invocation. It is **_NOT_** a command line browser (if that's what you are searching for, search for Lynx instead)!

The results? Less clicking, faster results, and *no limitations to normal browsing!*

## Installation
* Clone this git repository: `git clone https://github.com/huntrar/CLIQuery`
* [Sign up](https://developer.wolframalpha.com/portal/apisignup.html) for a WolframAlpha API key.
* Enter your API key and choice of browser in .cliqrc (cygwin users should enter `cygwin` as their browser)
* Resolve dependencies: `pip install lxml`

## Usage
    usage: cliquery.py [-h] [-s] [-f] [-o] [-w] [-d] [-b] [QUERY [QUERY ...]]

    positional arguments:
      QUERY           keywords to search

    optional arguments:
      -h, --help      show this help message and exit
      -s, --search    display search links
      -f, --first     open first link
      -o, --open      open link manually
      -w, --wolfram   display wolfram results
      -d, --describe  display page snippet
      -b, --bookmark  view and modify bookmarks

## Author
* Hunter Hammond 

## Notes
* A search may return immediate results, such as calculations or facts, or instead a page of search results comprised of descriptive links to follow.

* Interactive use is as easy as passing the regular flag arguments into the link prompt; this overrides any preexisting flags and allows for more even more flexibility
    ```
    $ cliq a simple example
    > - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    > 1. simple sentence - definition and examples of simple ...
    > 2. HTML Examples - W3Schools Online Web Tutorials
    > 3. A Simple Example | A Quick Rexx Tutorial | InformIT
    > 4. Leaflet.js - A Simple Example - CodeProject
    > 5. Using OpenGL on Windows: A Simple Example - Computer ??
    > 6. Simple HTML example - Java Tutorials - Learn Java Online ...
    > 7. Example of a simple HTML page
    > - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    > : d 5


    > http://www.cs.rit.edu/~ncs/Courses/570/UserGuide/OpenGLonWin-11.html


    > NextPrevUpTopContentsIndex Using OpenGL on Windows: A Simple Example
    > Any OpenGL program for Windows has to take care of some window-dependent
    > setup. There are several ways this setup can be done, for example, using
    > the GLUT library or using GDI and WGL directly. This guide focuses on
    > using the Windows OpenGL API directly.
    > See more? (y/n): n
    ```

* To choose multiple links at once, a range may be specified by separating the start and end range with a dash. Leaving one end of the range blank will choose all links until the other end of that range. For example, given 10 links, entering 5- would effectively be the same as entering 5-10.

* Using the bookmarks flag with empty arguments will list all current bookmarks in .cliqrc, ordered by time of entry. To add a new bookmark, simply enter the url you wish to add as an argument. To open an existing bookmark, enter the corresponding bookmark number as listed as an argument. Bookmarks may also be added interactively through the link prompt like all other flags.
