# cliquery

## a command-line browsing interface
cliquery is a command-line interface meant to bundle important features of a conventional browser and the quickness of the command-line. It supports previewing webpages, bookmarks, 'Feeling Lucky' searches, as well as regular web searches or simply entering URI's directly. cliquery is **_NOT_** a command-line browser such as Lynx, but it does have an interactive interface that makes it quick and easy to perform multiple searches and other operations. When a user decides to actually open a link, cliquery simply invokes their browser of choice! Supported in both Python 2.x and 3.x.

The results? Less clicking, faster results, and *no limitations to regular browsing!*

## Installation
* `pip install cliquery`
* [Sign up (optional)](https://developer.wolframalpha.com/portal/apisignup.html) for a WolframAlpha API key.
* Enter your API key and choice of browser in .cliqrc (cygwin users should enter `cygwin` as their browser). An example .rc file is available in cliquery/.cliqrc, or will be created after an initial run. The API key field may be left blank if you did not sign up for a key.

## Usage
usage: cliquery.py [-h] [-s] [-f] [-o] [-w] [-d] [-b] [-v] [QUERY [QUERY ...]]

a command-line browsing interface

&nbsp;&nbsp;positional arguments:

&nbsp;&nbsp;&nbsp;&nbsp;QUERY&nbsp;&nbsp;&nbsp;keywords to search


&nbsp;&nbsp;optional arguments:

&nbsp;&nbsp;&nbsp;&nbsp;-h, --help&nbsp;&nbsp;show this help message and exit

&nbsp;&nbsp;&nbsp;&nbsp;-s, --search&nbsp;&nbsp;display search links

&nbsp;&nbsp;&nbsp;&nbsp;-f, --first&nbsp;&nbsp;open first link

&nbsp;&nbsp;&nbsp;&nbsp;-o, --open&nbsp;&nbsp;open link or browser manually

&nbsp;&nbsp;&nbsp;&nbsp;-w, --wolfram&nbsp;display wolfram results

&nbsp;&nbsp;&nbsp;&nbsp;-d, --describe&nbsp;display page snippet

&nbsp;&nbsp;&nbsp;&nbsp;-b, --bookmark&nbsp;view and modify bookmarks

&nbsp;&nbsp;&nbsp;&nbsp;-c, --config&nbsp;print location of config file

&nbsp;&nbsp;&nbsp;&nbsp;-v, --version&nbsp;display current version


## Author
* Hunter Hammond (huntrar@gmail.com)

## Notes
* If you receive the following message when trying to add bookmarks:
    ```
    IOError: [Errno 13] Permission denied: '/usr/local/lib/python2.7/dist-packages/cliquery/.cliqrc'
    ```
Enter the following to fix:
    ```
    sudo chmod a+x /usr/local/lib/python2.7/dist-packages/cliquery/.cliqrc
    ```

* A search may return immediate results, such as calculations or facts, or instead a page of search results comprised of descriptive links to follow.

* Interactive use is as easy as passing the regular flag arguments into the link prompt; this overrides any preexisting flags and allows for more even more flexibility.
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
* Entering h or help will bring up the list of possible commands to pass to the prompt.

* To choose multiple links at once, a range may be specified by separating the start and end range with a dash. Leaving one end of the range blank will choose all links until the other end of that range. For example, given 10 links, entering 5- would effectively be the same as entering 5-10.

* Using the bookmarks flag with no arguments will list all current bookmarks in .cliqrc, ordered by time of entry. Adding and deleting bookmarks can be done using add [url] or del [num] or [suburl], where [suburl] is a substring of the url. Opening bookmarks is done through the bookmarks flag and either a [num] or [suburl] argument. Bookmarks may also be added interactively through the link prompt, like all other flags.
