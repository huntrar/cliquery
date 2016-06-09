#!/usr/bin/env python
""" cliquery - a command-line browser interface

    written by Hunter Hammond (huntrar@gmail.com)
"""

from __future__ import absolute_import, print_function
from argparse import ArgumentParser
from collections import OrderedDict
import glob
import itertools
import os
import sys

from cliquery import utils
from .bookmark import bookmarks, import_bookmarks
from .compat import unescape, iteritems, itervalues, iterkeys, uni, asc
from .config import CONFIG, CONFIG_FPATH, set_config
from .open import open_url
from . import __version__, cinput, crange, SYS_VERSION, CONTINUE, SEE_MORE


XDG_CACHE_DIR = os.environ.get('XDG_CACHE_HOME',
                               os.path.join(os.path.expanduser('~'), '.cache'))
CACHE_DIR = os.path.join(XDG_CACHE_DIR, 'cliquery')
CACHE_FILE = os.path.join(CACHE_DIR, 'cache{0}'.format(
    SYS_VERSION if SYS_VERSION == 3 else ''))


BORDER_LEN = 28  # The length of the link prompt border
BORDER = ' '.join(['+']*BORDER_LEN)

PARSER_HELP = ''

FLAGS_MODIFIED = False  # Set to True once user enters interactive flags


def get_parser():
    """Parse command-line arguments"""
    parser = ArgumentParser(description='a command-line browser interface')
    parser.add_argument('query', metavar='QUERY', type=str, nargs='*',
                        help='keywords to search')
    parser.add_argument('-b', '--bookmark', help='view and modify bookmarks',
                        action='store_true')
    parser.add_argument('-c', '--config', help='print config file location',
                        action='store_true')
    parser.add_argument('-C', '--clear-cache', help='clear the cache',
                        action='store_true')
    parser.add_argument('-d', '--describe', help='summarize links',
                        action='store_true')
    parser.add_argument('-f', '--first', help='open first link',
                        action='store_true')
    parser.add_argument('-i', '--import', help='import bookmarks from file',
                        type=str, nargs='?')
    parser.add_argument('-o', '--open', help='directly open links',
                        action='store_true')
    parser.add_argument('-p', '--print', help='print links to stdout',
                        action='store_true')
    parser.add_argument('-s', '--search', help='search for links',
                        action='store_true')
    parser.add_argument('-v', '--version', help='display current version',
                        action='store_true')
    parser.add_argument('-w', '--wolfram', help='search WolframAlpha',
                        action='store_true')
    return parser


def enable_cache():
    """Enable requests library cache"""
    try:
        import requests_cache
    except ImportError as err:
        sys.stderr.write('Failed to enable cache: {0}\n'.format(str(err)))
        return
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    requests_cache.install_cache(CACHE_FILE)


def clear_cache():
    """Clear requests library cache"""
    for cache in glob.glob('{0}*'.format(CACHE_FILE)):
        os.remove(cache)


def get_bing_resp(query):
    """Get response from Bing search (top 10 results)"""
    if not query:
        return None

    return utils.get_resp('http://www.bing.com/search?q={0}'.format(query))


def get_google_resp(query):
    """Get response from Google custom search API (top 10 results)

       Return response and True if Google was used (other option is Bing)
    """
    use_google = True
    if not query:
        return None, use_google

    try:
        from googleapiclient.discovery import build
    except ImportError:
        use_google = False

    if use_google:
        api_key = CONFIG['google_api_key']
        engine_key = CONFIG['google_engine_key']

        resp = ''
        if api_key and engine_key:
            service = build("customsearch", "v1", developerKey=api_key)
            resp = service.cse().list(q=query, cx=engine_key).execute()

        if resp and 'items' in resp:
            return resp['items'], use_google
        else:
            use_google = False

    # If no results from Google (or no API keys), use Bing
    return get_bing_resp(query), use_google


def get_wolfram_resp(query):
    """Get XML response from Wolfram API as an lxml.html.HtmlElement object"""
    if not query:
        return None
    base_url = 'http://api.wolframalpha.com/v2/query?input='
    api_key = CONFIG['wolfram_api_key']
    return utils.get_resp('{0}{1}&appid={2}'.format(base_url, query, api_key))


def open_link_range(args, urls, prompt_args):
    """Open a link number range

       Keyword arguments:
       args -- program arguments (dict)
       urls -- search URL's found (list)
       prompt_args -- temporary arguments from link prompt (list)
    """
    split_args = ''.join(prompt_args).split('-')
    start = split_args[0].strip()
    end = split_args[1].strip()
    start_is_num = utils.check_input(start, num=True)
    if start_is_num:
        start = int(start)-1
    end_is_num = utils.check_input(end, num=True)
    if end_is_num:
        end = int(end)-1

    if start_is_num and end_is_num:
        # Open close-ended range of urls (like #-#)
        if utils.in_range(len(urls), start, end):
            open_url(args, urls[start:end+1])
        else:
            sys.stderr.write('{0}-{1} is out of range.\n'
                             .format(start+1, end+1))
    elif start_is_num:
        # Open open-ended range of urls (like #-)
        if utils.in_range(len(urls), start):
            open_url(args, urls[start:])
        else:
            sys.stderr.write('{0}- is out of range.\n'.format(start+1))
    elif end_is_num:
        # Open open-ended range of urls (like -#)
        if utils.in_range(len(urls), end):
            open_url(args, urls[:end+1])
        else:
            sys.stderr.write('-{0} is out of range.\n'.format(end+1))
    else:
        sys.stderr.write('{0} is not a number.\n'.format(start or end))


def open_links(args, urls, prompt_args):
    """Open one or more links

       Keyword arguments:
       args -- program arguments (dict)
       urls -- search URL's found (list)
       prompt_args -- temporary arguments from link prompt (list)
    """
    if not isinstance(prompt_args, list):
        prompt_args = [prompt_args]
    link_num = 0
    links = []
    for num in prompt_args:
        if utils.check_input(num.strip(), num=True):
            link_num = int(num.strip()) - 1
            if utils.in_range(len(urls), link_num):
                links.append(urls[link_num])
            else:
                sys.stderr.write('{0} is out of range.\n'.format(num))
        else:
            sys.stderr.write('{0} is not a number.\n'.format(num))
    if links:
        open_url(args, links, prompt_args)


def process_prompt_cmds(args, urls, prompt_args):
    """Special processing for link prompt commands

       Keyword arguments:
       args -- program arguments (dict)
       urls -- search URL's found (list)
       prompt_args -- command arguments entered in link prompt (list)

       Return whether to call search as well as possibly modified prompt_args
    """
    for flag in iterkeys(args):
        if args[flag]:
            # Special flag cases where preprocessing is necessary
            if flag == 'bookmark' and 'add' in prompt_args:
                # Resolve URL before adding bookmark
                temp_args = []
                for i, arg in enumerate(prompt_args):
                    if utils.check_input(arg, num=True):
                        temp_args.append(urls[i-1])
                    else:
                        temp_args.append(arg)
                if utils.check_input(temp_args):
                    prompt_args = temp_args
            elif flag in ('describe', 'open', 'print'):
                if any([',' in arg for arg in prompt_args]):
                    # Remove commas
                    prompt_args = ''.join(prompt_args).split(',')
                    prompt_args = [arg for arg in prompt_args if arg]

                if any(['-' in arg for arg in prompt_args]):
                    # Open a range of links
                    open_link_range(args, urls, prompt_args)
                    return False, prompt_args
                else:
                    # Open one or more links
                    open_links(args, urls, prompt_args)
                    return False, prompt_args
            elif flag == 'first':
                open_url(args, urls[0])
                return False, prompt_args
    return True, prompt_args


def exec_prompt_cmd(args, urls, prompt_cmd, prompt_args):
    """Execute a command in the link prompt

       Keyword arguments:
       args -- program arguments (dict)
       urls -- search URL's found (list)
       prompt_cmd -- command entered in link prompt (str)
       prompt_args -- command arguments entered in link prompt (list)

       If there are no preexisting flags, the prompt command defaults to open.
    """
    # lookup_flags (dict)
    #   key: abbreviated flag name (first letter of flag)
    #   value: full flag name
    lookup_flags = utils.get_lookup_flags(args)

    global FLAGS_MODIFIED
    if not FLAGS_MODIFIED:
        # Some program flags will exhibit different behavior depending on
        # whether they were entered dynamically or not.
        #
        # The following flags are guaranteed to have the same behavior
        # and thus their state is retained, while others are reset.
        desc, opn, prnt = args['describe'], args['open'], args['print']
    else:
        # If flags have been modified then all flags are reset regardless.
        desc, opn, prnt = False, False, False
    args = utils.reset_flags(args)
    args['describe'], args['open'], args['print'] = desc, opn, prnt

    # A command is not valid if it meets one of the following criteria:
    #
    # 1. It is a full command name and is not found in list of full commands
    # 2. It is one or more abbreviated commands and they do not all exist in
    #    the list of abbreviated commands
    if prompt_cmd not in itervalues(lookup_flags):
        cmd_not_valid = not all(flag in iterkeys(lookup_flags)
                                for flag in prompt_cmd)
    else:
        cmd_not_valid = False

    if cmd_not_valid or prompt_cmd == 'help':
        if prompt_cmd[0] == '-' or utils.check_input(prompt_cmd[0], num=True):
            # No explicit command, either a number or number range (hence dash)
            # If user did not choose describe, open, or print, then
            # default command is open.
            prompt_args = [prompt_cmd] + prompt_args
            if not any((args['describe'], args['open'], args['print'])):
                prompt_cmd = 'open'
            else:
                prompt_cmd = [key for key, value in
                              iteritems({'describe': args['describe'],
                                         'open': args['open'],
                                         'print': args['print']}) if value][0]
        else:
            # Print help message and check for quit
            utils.check_input(cinput('{0}\n{1}'.format(PARSER_HELP, CONTINUE)))
            return
    elif not FLAGS_MODIFIED:
        # Reset args again because flags were modified
        FLAGS_MODIFIED = True
        args = utils.reset_flags(args)

    # Set new flags if flags were modified or none are currently set
    no_flags_set = not any(x for x in itervalues(args) if isinstance(x, bool))
    if prompt_cmd in itervalues(lookup_flags):
        if FLAGS_MODIFIED or no_flags_set:
            args[prompt_cmd] = True
        call_search, prompt_args = process_prompt_cmds(args, urls, prompt_args)
    else:
        for cmd in prompt_cmd:
            if cmd in iterkeys(lookup_flags):
                if FLAGS_MODIFIED or no_flags_set:
                    args[lookup_flags[cmd]] = True
        call_search, prompt_args = process_prompt_cmds(args, urls, prompt_args)

    if call_search:
        args['query'] = prompt_args
        search(args)


def display_link_prompt(args, urls, titles):
    """Print URL's and their descriptions alongside a prompt

       Keyword arguments:
       args -- program arguments (dict)
       urls -- search URL's found (list)
       titles -- descriptions of search URL's found (list)
    """
    while 1:
        print('\n{0}'.format(BORDER))
        for i in crange(len(urls)):
            print('{0}. {1}'.format(i+1, uni(unescape(titles[i]))))
        print(BORDER)

        # Handle link prompt input
        try:
            link_input = [inp.strip() for inp in cinput(': ').split()]
            if not link_input:
                continue
            utils.check_input(link_input)  # Check input in case of quit
            print('\n')
            exec_prompt_cmd(args, urls, link_input[0], link_input[1:])
        except (KeyboardInterrupt, EOFError, ValueError, IndexError):
            return False


def bing_search(args, resp):
    """Perform a Bing search and display link choice prompt"""
    if resp is None:
        return open_url(args, 'https://www.google.com')
    elif args['open']:
        return open_url(args, args['query'])

    try:
        unprocessed_urls = resp.xpath('//h2/a/@href')
    except AttributeError:
        raise AttributeError('Failed to retrieve data from lxml object!')
    if not unprocessed_urls:
        sys.stderr.write('Failed to retrieve links from Bing.\n')
        return None

    urls = []
    titles = []
    base_url = 'www.bing.com'
    for url in unprocessed_urls:
        if url.startswith('/') and base_url not in url:
            # Add missing base url
            urls.append('http://{0}{1}'.format(base_url, url))
            if "'" in url:
                ld_xpath = '//h2/a[@href="{0}"]//text()'.format(url)
            else:
                ld_xpath = "//h2/a[@href='{0}']//text()".format(url)
            titles.append(''.join(resp.xpath(ld_xpath)))
        elif url.startswith('http://') or url.startswith('https://'):
            urls.append(url)
            if "'" in url:
                ld_xpath = '//h2/a[@href="{0}"]//text()'.format(url)
            else:
                ld_xpath = "//h2/a[@href='{0}']//text()".format(url)
            titles.append(''.join(resp.xpath(ld_xpath)))

    if urls and titles:
        return display_link_prompt(args, urls, titles)
    return False


def google_search(args, resp):
    """Perform a Google search and display link choice prompt"""
    if resp is None:
        return open_url(args, 'https://www.google.com')
    elif args['open']:
        return open_url(args, args['query'])

    raw_urls = [x['formattedUrl'] for x in resp]
    urls = [utils.add_scheme(x) if not utils.check_scheme(x) else x
            for x in raw_urls]
    titles = [x['title'] for x in resp]
    if urls and titles:
        return display_link_prompt(args, urls, titles)
    return False


def bing_open_first(args, resp):
    """Open the first Bing link available, i.e. 'Feeling Lucky'"""
    if resp is not None:
        bing_urls = resp.xpath('//h2/a/@href')
        if bing_urls:
            url = bing_urls[0]
            if url.startswith('http://') or url.startswith('https://'):
                return open_url(args, url)
            else:
                return open_url(args, 'http://{0}'.format(url))
    print('Results not found.')


def google_open_first(args, resp):
    """Open the first Google link available, i.e. 'Feeling Lucky'"""
    if resp:
        raw_url = resp[0]['formattedUrl']
        if not utils.check_scheme(raw_url):
            url = utils.add_scheme(raw_url)
        else:
            url = raw_url

        return open_url(args, url)
    print('Results not found.')


def reformat_wolfram_entries(titles, entries):
    """Reformat Wolfram entries"""
    output_list = []
    for title, entry in itertools.izip(titles, entries):
        try:
            if ' |' in entry:
                entry = '\n\t{0}'.format(entry.replace(' |', ':')
                                         .replace('\n', '\n\t'))
            if title == 'Result':
                output_list.append(uni(entry))
            else:
                output_list.append(uni(title + ': ' + entry))
        except (AttributeError, UnicodeEncodeError):
            pass
    return output_list


def wolfram_search(args, resp):
    """Perform a WolframAlpha search, may require an API key in .cliqrc"""
    if resp is None:
        return open_url(args, 'http://www.wolframalpha.com')
    elif args['open']:
        return open_url(args, args['query'])

    try:
        # Filter unnecessary title fields
        titles = list(OrderedDict.fromkeys(
            resp.xpath("//pod[@title != '' and "
                       "@title != 'Number line' and "
                       "@title != 'Input' and "
                       "@title != 'Visual representation' and "
                       "@title != 'Image' and "
                       "@title != 'Manipulatives illustration' and "
                       "@title != 'Quotient and remainder']"
                       "/@title")))
    except AttributeError:
        raise AttributeError('Failed to retrieve data from lxml object!')

    entries = []
    if titles:
        for title in titles:
            title = asc(title)  # Encode to ascii-ignore
            entry_xpath = ("//pod[@title='{0}']/subpod/plaintext/text()"
                           .format(title))
            entry = resp.xpath(entry_xpath)
            if entry:
                entries.append(entry[0])

        entries = list(OrderedDict.fromkeys(entries))
        # Return False if results were empty
        if len(entries) == 1 and entries[0] == '{}':
            return False

        output_list = reformat_wolfram_entries(titles, entries)
        if not output_list:
            return False
        elif len(output_list) > 2:
            print('\n'.join(output_list[:2]))
            if utils.check_input(cinput(SEE_MORE), empty=True):
                print('\n'.join(output_list[2:]))
        else:
            print('\n'.join(output_list))
        return True
    else:
        return False


def search(args):
    """Handle web searching, page previewing, and bookmarks"""
    if args['version']:
        print(__version__)
        return
    if args['config']:
        print(CONFIG_FPATH)
        return
    if args['clear_cache']:
        clear_cache()
        print('Cleared {0}.'.format(CACHE_DIR))
        return

    # Set WolframAlpha API key, browser, and bookmarks in CONFIG
    if not CONFIG:
        set_config()

    # Check for bookmark import
    if args['import']:
        print('Importing {0}. This will append to existing bookmarks.'
              .format(args['import']))
        try:
            if utils.confirm_input(cinput('Confirm import (yes/no): ')):
                if import_bookmarks(args['import']):
                    print('Import was successful.')
        except (KeyboardInterrupt, EOFError):
            pass
        return

    # Cannot search WolframAlpha without an API key in .cliqrc
    if args['wolfram'] and not CONFIG['wolfram_api_key']:
        args['wolfram'] = False
        sys.stderr.write('Missing WolframAlpha API key in .cliqrc file.\n')

    # Print help message if none of the following conditions are true
    if not any([args['query'], args['open'], args['bookmark'],
                args['search'], args['wolfram']]):
        print(PARSER_HELP)
        return False

    if args['query']:
        args['query'] = utils.clean_query(args, ' '.join(args['query']))

    try:
        if args['bookmark']:
            # Open, add, tag, untag, move, or delete bookmarks
            return bookmarks(args, args['query'])
        if args['first']:
            # Open the first Google link available, i.e. 'Feeling Lucky'
            resp, google = get_google_resp(args['query'])
            if google:
                return google_open_first(args, resp)

            return bing_open_first(args, resp)
        if args['open']:
            # Print, describe, or open URL's in the browser
            return open_url(args, args['query'])
        if args['search']:
            # Perform a Google search and display link choice prompt
            resp, google = get_google_resp(args['query'])
            if google:
                return google_search(args, resp)

            return bing_search(args, resp)
        if args['wolfram']:
            # Perform a WolframAlpha search, may require an API key in .cliqrc
            result = wolfram_search(args, get_wolfram_resp(args['query']))
            if not result:
                print('No answer available from WolframAlpha.')
            return result

        # Default behavior is to check WolframAlpha, then Google.
        result = wolfram_search(args, get_wolfram_resp(args['query']))
        if not result:
            resp, google = get_google_resp(args['query'])
            if google:
                result = google_search(args, resp)
            else:
                result = bing_search(args, resp)

        return result
    except (KeyboardInterrupt, EOFError):
        return False


def command_line_runner():
    """Handle command-line interaction"""
    parser = get_parser()
    global PARSER_HELP
    PARSER_HELP = parser.format_help()
    args = vars(parser.parse_args())

    # Enable cache unless user sets environ variable CLIQ_DISABLE_CACHE
    if not os.getenv('CLIQ_DISABLE_CACHE'):
        enable_cache()
    search(args)


if __name__ == '__main__':
    command_line_runner()
