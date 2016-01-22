#!/usr/bin/env python
""" cliquery - a command-line browser interface

    written by Hunter Hammond (huntrar@gmail.com)
"""

from __future__ import absolute_import, print_function
import argparse as argp
from collections import OrderedDict
import glob
import itertools
import json
import os
import re
import sys
import webbrowser

from cliquery import utils, pyteaser
from .compat import SYS_VERSION, iteritems, itervalues, iterkeys, uni, asc
from . import __version__


if SYS_VERSION == 2:
    input = raw_input
    range = xrange

XDG_CACHE_DIR = os.environ.get('XDG_CACHE_HOME',
                               os.path.join(os.path.expanduser('~'), '.cache'))
CACHE_DIR = os.path.join(XDG_CACHE_DIR, 'cliquery')
CACHE_FILE = os.path.join(CACHE_DIR, 'cache{0}'.format(
    SYS_VERSION if SYS_VERSION == 3 else ''))


BORDER_LEN = 28  # The length of the link prompt border
BORDER = ' '.join(['+']*BORDER_LEN)

CONFIG_DIR = os.path.dirname(os.path.realpath(__file__))
if os.path.isfile('{0}/.local.cliqrc'.format(CONFIG_DIR)):
    CONFIG_FPATH = '{0}/.local.cliqrc'.format(CONFIG_DIR)
else:
    CONFIG_FPATH = '{0}/.cliqrc'.format(CONFIG_DIR)
CONFIG = {}

PARSER_HELP = ''
BOOKMARK_HELP = ('Usage: '
                 '\nopen: [num.. OR url/tag substr] [additional URL args..]'
                 '\nadd: add [url..]'
                 '\nremove: rm [num.. OR url/tag substr..]'
                 '\ntag: tag [num OR suburl] [tag..]'
                 '\nuntag: untag [num OR url/tag substr] [tag..]'
                 '\ndescribe: desc [num.. OR url/tag substr..]'
                 '\nmove: mv [num OR url/tag substr] [num OR url/tag substr]'
                 '\n')

CONTINUE = '[Press Enter to continue..] '
SEE_MORE = 'See more? {0}'.format(CONTINUE)

FLAGS_MODIFIED = False  # Set to True once user enters interactive flags


def get_parser():
    """Parse command-line arguments"""
    parser = argp.ArgumentParser(description='a command-line browser interface'
                                )
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


def read_config():
    """Read in .cliqrc or .local.cliqrc file"""
    with open(CONFIG_FPATH, 'r') as cfg:
        lines = []
        api_key = ''
        browser = ''

        # First two lines of .cliqrc should contain api_key: and browser:
        # If not, attempts to read the two in that order anyways
        for _ in range(2):
            line = cfg.readline()
            if line.startswith('api_key:'):
                api_key = line[8:].strip()
            if line.startswith('browser:'):
                browser = line[8:].strip()
            else:
                lines.append(line)
        if not api_key and not browser:
            try:
                api_key = lines[0].strip()
                browser = lines[1].strip()
            except IndexError:
                api_key = ''
                browser = ''

        # Read in bookmarks
        bkmarks = []
        cfg_bkmarks = cfg.read()
        if cfg_bkmarks.startswith('bookmarks:'):
            cfg_bkmarks = cfg_bkmarks[10:].split('\n')
            bkmarks = [b.strip() for b in cfg_bkmarks if b.strip()]

        return api_key, browser, bkmarks


def set_config():
    """Set WolframAlpha API key, browser, and bookmarks in CONFIG"""
    api_key, browser_name, bkmarks = read_config()
    CONFIG['api_key'] = api_key
    CONFIG['bookmarks'] = bkmarks

    # There may be multiple browser options given, pick the first which works
    if ',' in browser_name:
        browser_names = browser_name.split(',')
    else:
        browser_names = browser_name.split()

    if browser_names:
        for brow_name in browser_names:
            try:
                CONFIG['browser_name'] = brow_name
                CONFIG['browser'] = webbrowser.get(brow_name)
                return
            except webbrowser.Error:
                pass

    # If no valid browser found then use webbrowser to automatically detect one
    try:
        if sys.platform == 'win32':
            # Windows
            browser_name = 'windows-default'
            browser = webbrowser.get(browser_name)
        elif sys.platform == 'darwin':
            # Mac OSX
            browser_name = 'macosx'
            browser = webbrowser.get(browser_name)
        else:
            browser_name = 'Automatically detected'
            browser = webbrowser.get()
        CONFIG['browser_name'] = browser_name
        CONFIG['browser'] = browser
    except webbrowser.Error:
        pass


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


def get_google_query_url(query):
    """Get Google query url"""
    base_url = 'www.google.com'
    if not query:
        return 'http://{0}'.format(base_url)
    return 'http://{0}/search?q={1}'.format(base_url, query)


def get_wolfram_query_url(query):
    """Get Wolfram query url"""
    base_url = 'www.wolframalpha.com'
    if not query:
        return 'http://{0}'.format(base_url)
    return 'http://{0}/input/?i={1}'.format(base_url, query)


def get_google_resp(query):
    """Get JSON response from Google API as a dict object (top 8 results)"""
    if not query:
        return None
    base_url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0'
    raw_resp = utils.get_raw_resp('{0}&q={1}&rsz=8'.format(base_url, query))
    return json.loads(raw_resp.decode('utf-8'))['responseData']


def get_wolfram_resp(query):
    """Get XML response from Wolfram API as an lxml.html.HtmlElement object"""
    if not query:
        return None
    base_url = 'http://api.wolframalpha.com/v2/query?input='
    api_key = CONFIG['api_key']
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
            utils.check_input(input('{0}\n{1}'.format(PARSER_HELP, CONTINUE)))
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


def display_link_prompt(args, urls, url_descs):
    """Print URL's and their descriptions alongside a prompt

       Keyword arguments:
       args -- program arguments (dict)
       urls -- search URL's found (list)
       url_descs -- descriptions of search URL's found (list)
    """
    while 1:
        print('\n{0}'.format(BORDER))
        for i in range(len(urls)):
            print('{0}. {1}'.format(i+1, uni(url_descs[i])))
        print(BORDER)

        # Handle link prompt input
        try:
            link_input = [inp.strip() for inp in input(': ').split()]
            if not link_input:
                continue
            utils.check_input(link_input)  # Check input in case of quit
            print('\n')
            exec_prompt_cmd(args, urls, link_input[0], link_input[1:])
        except (KeyboardInterrupt, EOFError, ValueError, IndexError):
            return False


def google_search(args, resp):
    """Perform a Google search and display link choice prompt"""
    if resp is None:
        return open_url(args, 'https://www.google.com')
    elif args['open']:
        return open_url(args, args['query'])

    results = resp['results']
    urls = [x['url'] for x in results]
    url_descs = [x['titleNoFormatting'] for x in results]
    if urls and url_descs:
        return display_link_prompt(args, urls, url_descs)
    return False


def open_first(args, resp):
    """Open the first Google link available, i.e. 'Feeling Lucky'"""
    return open_url(args, resp['results'][0]['url'])


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
            if utils.check_input(input(SEE_MORE), empty=True):
                print('\n'.join(output_list[2:]))
        else:
            print('\n'.join(output_list))
        return True
    else:
        return False


def reload_bookmarks():
    """Read in bookmarks again from .cliqrc"""
    CONFIG['bookmarks'] = read_config()[2]


def find_bookmark_idx(query):
    """Find the index of a bookmark given substrings"""
    bkmarks = CONFIG['bookmarks']
    if isinstance(query, str):
        query = query.strip().split()
    most_matches = 0
    matched_idx = 0
    for i, bkmark in enumerate(bkmarks):
        matches = 0
        for arg in query:
            if arg in bkmark:
                matches += 1
        if matches > most_matches:
            most_matches = matches
            matched_idx = i

    if most_matches > 0:
        return matched_idx+1
    return -1


def find_bookmark_indices(query_args):
    """Find all bookmark indices given indices or substrings"""
    bk_indices = []
    for arg in query_args:
        if utils.check_input(arg, num=True):
            # Substring is already a bookmark index
            bk_indices.append(arg)
        else:
            bk_idx = find_bookmark_idx(arg)
            if bk_idx > 0:
                bk_indices.append(bk_idx)
            else:
                sys.stderr.write('Could not find bookmark {0}.\n'.format(arg))
    return bk_indices


def bk_num_to_url(bkmarks, num, append_arg=None):
    """Convert a bookmark number to a URL

       Keyword arguments:
           bkmarks -- bookmarks read in from config file (list)
           num -- bookmark num to convert (str)
           append_arg -- additional args possibly found (str) (default: None)

       Return the URL found or None.
    """
    try:
        bkmark = bkmarks[int(num) - 1]
        if '(' in bkmark and ')' in bkmark:
            url = bkmark.split('(')[0].strip()
        else:
            url = bkmark
        if append_arg:
            url = '{0}/{1}'.format(url.rstrip('/'), append_arg)
        return url
    except IndexError:
        sys.stderr.write('Bookmark {0} not found.\n'.format(num))
        return None


def print_bookmarks():
    """Print all saved bookmarks"""
    bkmarks = CONFIG['bookmarks']
    print('Bookmarks:')
    for i, bkmark in enumerate(bkmarks):
        if '(' in bkmark and ')' in bkmark:
            bkmark = bkmark.split('(')[1].rstrip(')')
        print('{0}. {1}'.format(str(i+1), bkmark))
    return True


def add_bookmark(urls):
    """Add a bookmark to the list of saved bookmarks"""
    with open(CONFIG_FPATH, 'a') as cfg:
        if isinstance(urls, list):
            for url in urls:
                cfg.write('\n{0}'.format(url))
        elif isinstance(urls, str):
            cfg.write('\n{0}'.format(urls))
    reload_bookmarks()
    return True


def remove_bookmark(bk_idx):
    """Remove an existing bookmark from the list of saved bookmarks"""
    bkmarks = CONFIG['bookmarks']
    with open(CONFIG_FPATH, 'w') as cfg:
        cfg.write('api_key: {0}'.format(CONFIG['api_key']))
        cfg.write('\nbrowser: {0}'.format(CONFIG['browser_name']))
        cfg.write('\nbookmarks: ')
        if isinstance(bk_idx, list):
            bk_idx = [int(x)-1 for x in bk_idx]
            for i, bkmark in enumerate(bkmarks):
                if i not in bk_idx:
                    cfg.write('\n{0}'.format(bkmark))
        else:
            for i, bkmark in enumerate(bkmarks):
                if i != int(bk_idx)-1:
                    cfg.write('\n{0}'.format(bkmark))
    reload_bookmarks()
    return True


def tag_bookmark(bk_idx, tags):
    """Tag an existing bookmark with an alias"""
    bkmarks = CONFIG['bookmarks']
    if isinstance(tags, list):
        tags = ' '.join(tags)
    with open(CONFIG_FPATH, 'w') as cfg:
        cfg.write('api_key: {0}'.format(CONFIG['api_key']))
        cfg.write('\nbrowser: {0}'.format(CONFIG['browser_name']))
        cfg.write('\nbookmarks: ')

        for i, bkmark in enumerate(bkmarks):
            if i == int(bk_idx)-1:
                # Save previous tags if any, enclosed in parentheses
                prev_tags = re.search('(?<=\().*(?=\))', bkmark)
                if prev_tags:
                    tags = '{0} {1}'.format(prev_tags.group(), tags)

                cfg.write('\n{0} ({1})'
                          .format(bkmark.split('(')[0].strip(), tags))
            else:
                cfg.write('\n{0}'.format(bkmark))
    reload_bookmarks()
    return True


def untag_bookmark(bk_idx, tags_to_rm):
    """Remove a tag from a bookmark"""
    bkmarks = CONFIG['bookmarks']
    with open(CONFIG_FPATH, 'w') as cfg:
        cfg.write('api_key: {0}'.format(CONFIG['api_key']))
        cfg.write('\nbrowser: {0}'.format(CONFIG['browser_name']))
        cfg.write('\nbookmarks: ')

        for i, bkmark in enumerate(bkmarks):
            if i == int(bk_idx)-1 and '(' in bkmark and ')' in bkmark:
                # Remove tags
                split_bkmark = bkmark.split('(')
                if tags_to_rm:
                    curr_tags = split_bkmark[1].rstrip(')').split()
                    new_tags = list(curr_tags)
                    # Match current tags by substrings of tags to remove
                    for tag in curr_tags:
                        for rm_tag in tags_to_rm:
                            if rm_tag in tag:
                                new_tags.remove(tag)
                    if new_tags:
                        cfg.write('\n{0} ({1})'.format(split_bkmark[0],
                                                       ' '.join(new_tags)))
                    else:
                        cfg.write('\n{0}'.format(split_bkmark[0]))
                else:
                    cfg.write('\n{0}'.format(split_bkmark[0]))
            else:
                cfg.write('\n{0}'.format(bkmark))
    reload_bookmarks()
    return True


def describe_bookmark(bk_indices):
    """Print the URL behind a tagged bookmark"""
    bkmarks = CONFIG['bookmarks']
    for bk_idx in bk_indices:
        print(bk_num_to_url(bkmarks, bk_idx))
    return True


def move_bookmark(idx1, idx2):
    """Move bookmarks to the start, end, or at another bookmark's position"""
    bkmarks = CONFIG['bookmarks']
    b_len = len(bkmarks)
    if idx1 == idx2:
        sys.stderr.write('Bookmark indices equal.\n')
        sys.stderr.write(BOOKMARK_HELP)
        return True
    elif not utils.in_range(b_len, idx1) and not utils.in_range(b_len, idx2):
        sys.stderr.write('Bookmark indices out of range.\n')
        sys.stderr.write(BOOKMARK_HELP)
        return True

    with open(CONFIG_FPATH, 'w') as cfg:
        cfg.write('api_key: {0}'.format(CONFIG['api_key']))
        cfg.write('\nbrowser: {0}'.format(CONFIG['browser_name']))
        cfg.write('\nbookmarks: ')

        # Move bookmark to the front or end, or insert at an index
        if idx1 < 0:
            # Move bookmark 2 to the front
            if utils.in_range(b_len, idx2):
                bkmarks.insert(0, bkmarks.pop(idx2))
        elif idx1 >= b_len:
            # Move bookmark 2 to the end
            if utils.in_range(b_len, idx2):
                bkmarks.append(bkmarks.pop(idx2))
        elif idx2 < 0:
            # Move bookmark 1 to the front
            if utils.in_range(b_len, idx1):
                bkmarks.insert(0, bkmarks.pop(idx1))
        elif idx2 >= b_len:
            # Move bookmark 1 to the end
            if utils.in_range(b_len, idx1):
                bkmarks.append(bkmarks.pop(idx1))
        else:
            # Insert bookmark 1 in bookmark 2's position
            prev = bkmarks[idx2]
            bkmarks[idx2] = bkmarks[idx1]
            if idx1 > idx2:
                # Move entries down
                start_range = idx2+1
                end_range = idx1+1
                range_inc = 1
            else:
                # Move entries up
                start_range = idx2-1
                end_range = idx1-1
                range_inc = -1
            for i in range(start_range, end_range, range_inc):
                temp = bkmarks[i]
                bkmarks[i] = prev
                prev = temp

        for bkmark in bkmarks:
            cfg.write('\n{0}'.format(bkmark))
    reload_bookmarks()
    return True


def bookmark_open_cmd(args, query):
    """open: [num.. OR url/tag substr] [additional URL args..]

       Keyword arguments:
           args -- program arguments (dict)
           query -- query containing phrase to match/additional args (str)

       Keywords that do not exist in bookmarks are interpreted to be additional
       URL args, and are appended to the end of any matched bookmark URL's.
    """
    if not query:
        sys.stderr.write(BOOKMARK_HELP)
        return False
    if isinstance(query, str):
        split_query = query.strip().split()
    else:
        split_query = query

    bkmarks = CONFIG['bookmarks']
    bookmark_nums = [x for x in split_query if utils.check_input(x, num=True)]
    bookmark_words = [x for x in split_query if x not in bookmark_nums]
    append_args = [x for x in bookmark_words
                   if not any(x in bk for bk in bkmarks)]

    urls = []
    bk_idx = None
    for i, keyword in enumerate(split_query):
        if keyword in bookmark_words and bk_idx is None:
            # open: [suburl or tag]
            # Only need to resolve this once as words are grouped together
            bk_idx = find_bookmark_idx(bookmark_words)
            if bk_idx > 0:
                append_arg = ''
                if i+1 < len(split_query) and split_query[i+1] in append_args:
                    # If the next query is an append arg, add it to the url
                    append_arg = split_query[i+1]
                urls.append(bk_num_to_url(bkmarks, str(bk_idx), append_arg))
        elif keyword in bookmark_nums:
            # open: [num..]
            append_arg = ''
            if i+1 < len(split_query) and split_query[i+1] in append_args:
                # If the next query is an append arg, add it to the url
                append_arg = split_query[i+1]
            urls.append(bk_num_to_url(bkmarks, keyword, append_arg))

    valid_urls = [x for x in urls if x]
    if not valid_urls:
        sys.stderr.write(BOOKMARK_HELP)
        return False
    else:
        open_url(args, valid_urls)
        return True


def bookmark_add_cmd(query):
    """add: add [url..]"""
    split_query = query[3:].strip().split()
    if not split_query:
        sys.stderr.write(BOOKMARK_HELP)
        return False

    new_bkmarks = []
    for arg in split_query:
        arg = utils.append_scheme(arg)
        if '.' not in arg:
            if '(' in arg and ')' in arg:
                split_arg = arg.split('(')
                tag = split_arg[1].rstrip(')')
                bkmark = split_arg[0].strip()
                arg = '{0}.com ({1})'.format(bkmark, tag)
            else:
                arg = '{0}.com'.format(arg)
        new_bkmarks.append(arg)
    return add_bookmark(new_bkmarks)


def bookmark_rm_cmd(query):
    """remove: rm [num.. OR url/tag substr..]"""
    split_query = query[3:].strip().split()
    if not split_query:
        sys.stderr.write(BOOKMARK_HELP)
        return False

    bk_indices = find_bookmark_indices(split_query)
    if bk_indices:
        return remove_bookmark(bk_indices)
    return False


def bookmark_tag_cmd(query):
    """tag: tag [num OR suburl] [tag..]"""
    split_query = query[3:].strip().split()
    if not split_query:
        sys.stderr.write(BOOKMARK_HELP)
        return False

    tags = split_query[1:]
    bk_indices = find_bookmark_indices([split_query[0]])
    if bk_indices:
        return tag_bookmark(bk_indices[0], tags)
    return False


def bookmark_untag_cmd(query):
    """untag: untag [num OR url/tag substr] [tag..]"""
    split_query = query[5:].strip().split()
    if not split_query:
        sys.stderr.write(BOOKMARK_HELP)
        return False

    tags_to_rm = split_query[1:]
    bk_indices = find_bookmark_indices([split_query[0]])
    if bk_indices:
        return untag_bookmark(bk_indices[0], tags_to_rm)
    return False


def bookmark_desc_cmd(query):
    """describe: desc [num.. OR url/tag substr..]"""
    split_query = query[4:].strip().split()
    if not split_query:
        sys.stderr.write(BOOKMARK_HELP)
        return False

    bk_indices = find_bookmark_indices(split_query)
    if bk_indices:
        return describe_bookmark(bk_indices)
    return False


def bookmark_mv_cmd(query):
    """move: mv [num OR url/tag substr] [num OR url/tag substr]"""
    split_query = query[2:].strip().split()
    if not split_query or len(split_query) != 2:
        sys.stderr.write(BOOKMARK_HELP)
        return False

    bk1 = bk1_idx = split_query[0]
    bk2 = bk2_idx = split_query[1]
    if not utils.check_input(bk1, num=True):
        bk1_idx = find_bookmark_idx(bk1)
    if not utils.check_input(bk2, num=True):
        bk2_idx = find_bookmark_idx(bk2)
    if bk1_idx < 0:
        sys.stderr.write('Failed to find bookmark {0}.\n'.format(bk1))
        return False
    if bk2_idx < 0:
        sys.stderr.write('Failed to find bookmark {0}.\n'.format(bk2))
        return False
    # Account for zero-indexed list
    return move_bookmark(int(bk1_idx)-1, int(bk2_idx)-1)


def bookmarks(args, query):
    """Open, add, tag, untag, describe, move, or delete bookmarks"""
    if not query:
        return print_bookmarks()
    elif isinstance(query, list):
        query_cmd = query[0]
        query = ' '.join(query)
    else:
        query_cmd = query.split()[0]

    bookmark_commands = {'add': bookmark_add_cmd,
                         'rm': bookmark_rm_cmd,
                         'tag': bookmark_tag_cmd,
                         'untag': bookmark_untag_cmd,
                         'desc': bookmark_desc_cmd,
                         'mv': bookmark_mv_cmd}
    if query_cmd not in bookmark_commands:
        # Default command is to open a bookmark
        return bookmark_open_cmd(args, query)
    else:
        # Execute a bookmark command
        return bookmark_commands[query_cmd](query)


def open_browser(url):
    """Open a browser using webbrowser"""
    if CONFIG['browser']:
        CONFIG['browser'].open(url)
    else:
        sys.stderr.write('Failed to open browser.\n')


def open_url(args, urls, prompt_args=None):
    """Print, describe, or open URL's in the browser

       Keyword arguments:
           args -- program arguments (dict)
           urls -- search URL's chosen (list)
           prompt_args -- temporary arguments from link prompt (list)
    """
    if urls:
        # Either opening URL's or searching for link prompt arguments, not both
        prompt_args = None
        if not isinstance(urls, list):
            urls = [urls]
    elif prompt_args and isinstance(prompt_args, list):
        prompt_args = ' '.join(prompt_args)
    if args['open']:
        if args['search']:
            open_browser(get_google_query_url(prompt_args or args['query']))
            return True
        elif args['wolfram']:
            open_browser(get_wolfram_query_url(prompt_args or args['query']))
            return True

    if args['print']:
        for url in urls:
            print(url)
        return urls
    elif args['describe']:
        for url in urls:
            describe_url(url)
            print('\n')
        return urls
    else:
        if not urls:
            open_browser('')
        else:
            for url in urls:
                open_browser(url)
        return True


def describe_url(url):
    """Print a text preview of a given URL"""
    try:
        # Get title and text for summarization
        resp = utils.get_resp(url)
        title = utils.get_title(resp)
        text = utils.get_text(resp)
        if title and text:
            desc = utils.remove_whitespace(
                pyteaser.summarize(title, ' '.join(text)))
        else:
            desc = ''
        if not desc:
            sys.stderr.write('Failed to describe {0}.\n'.format(url))
            return False

        clean_desc = [x.replace('\n', '').replace('\t', '') for x in desc]
        print('\n'.join(x if isinstance(x, str) else uni(x)
                        for x in clean_desc))
        utils.check_input(input(CONTINUE))
        return True
    except AttributeError:
        sys.stderr.write('Failed to describe {0}.\n'.format(url))
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

    # Cannot search WolframAlpha without an API key in .cliqrc
    if args['wolfram'] and not CONFIG['api_key']:
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
            return open_first(args, get_google_resp(args['query']))
        if args['open']:
            # Print, describe, or open URL's in the browser
            return open_url(args, args['query'])
        if args['search']:
            # Perform a Google search and display link choice prompt
            return google_search(args, get_google_resp(args['query']))
        if args['wolfram']:
            # Perform a WolframAlpha search, may require an API key in .cliqrc
            result = wolfram_search(args, get_wolfram_resp(args['query']))
            if not result:
                print('No answer available from WolframAlpha.')
            return result

        # Default behavior is to check WolframAlpha, then Google.
        result = wolfram_search(args, get_wolfram_resp(args['query']))
        if not result:
            result = google_search(args, get_google_resp(args['query']))
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
