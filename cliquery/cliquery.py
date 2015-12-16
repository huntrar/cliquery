#!/usr/bin/env python
""" cliquery - a command-line browsing utility

    written by Hunter Hammond (huntrar@gmail.com)
"""

from __future__ import absolute_import, print_function
import argparse as argp
from collections import OrderedDict
import glob
import os
import re
from subprocess import call
from string import ascii_letters
import sys
import webbrowser

import requests_cache

from cliquery import utils, pyteaser
from .compat import SYS_VERSION, iteritems, uni, asc
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

LINK_HELP = ('Enter one of the following flags abbreviated or not,'
             'possibly followed by a link number:\n'
             '\th, help      show this help message\n'
             '\ts, search    search for links\n'
             '\to, open      directly open links\n'
             '\tw, wolfram   search WolframAlpha\n'
             '\td, describe  summarize links\n'
             '\tb, bookmark  view and modify bookmarks\n'
             '\tp, print     print links to stdout\n'
             '\tc, config    print config file location\n'
             '\tv, version   display current version\n')

BOOKMARK_HELP = ('Usage: '
                 '\nopen: [num or suburl or tag..]'
                 '\nadd: add [url..]'
                 '\ntag: tag [num or suburl] [tag..]'
                 '\nuntag: untag [num or suburl or tag] [subtag..]'
                 '\nmove: mv [num or suburl or tag] [num or suburl or tag]'
                 '\ndelete: rm [num or suburl or tag..]'
                 '\n')

CONTINUE = '[Press Enter to continue..] '
SEE_MORE = 'See more? {0}'.format(CONTINUE)


def get_parser():
    """Parse command-line arguments"""
    parser = argp.ArgumentParser(description='a command-line browsing utility')
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

        bkmarks = []
        cfg_bkmarks = cfg.read()
        if cfg_bkmarks.startswith('bookmarks:'):
            cfg_bkmarks = cfg_bkmarks[10:].split('\n')
            bkmarks = [b.strip() for b in cfg_bkmarks if b.strip()]

        if not api_key and not browser:
            try:
                api_key = lines[0].strip()
                browser = lines[1].strip()
                return api_key, browser, bkmarks
            except IndexError:
                return '', '', bkmarks
        else:
            return api_key, browser, bkmarks


def enable_cache():
    """Enable requests library cache"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    requests_cache.install_cache(CACHE_FILE)


def clear_cache():
    """Clear requests library cache"""
    for cache in glob.glob('{0}*'.format(CACHE_FILE)):
        os.remove(cache)


def get_search_html(args):
    """Get Bing or Wolfram HTML, or neither"""
    if args['bookmark']:
        return ''
    if not args['open']:
        if not args['wolfram']:
            return get_bing_html(args['query'])
        else:
            return get_wolfram_html(args['query'])
    else:
        return ''


def get_bing_query_url(query):
    """Get Bing query url"""
    base_url = 'www.bing.com'
    return 'http://{0}/search?q={1}'.format(base_url, query)


def get_bing_html(query):
    """Get HTML from Bing query"""
    return utils.get_html(get_bing_query_url(query))


def get_wolfram_query_url(query):
    """Get Wolfram query url"""
    base_url = 'www.wolframalpha.com'
    return 'http://{0}/input/?i={1}'.format(base_url, query)


def get_wolfram_html(query):
    """Get HTML from Wolfram API query"""
    base_url = 'http://api.wolframalpha.com/v2/query?input='
    api = CONFIG['api_key']
    return utils.get_html('{0}{1}&appid={2}'.format(base_url, query, api))


def open_link_range(args, urls, input_args):
    """Open a link number range

       Keyword arguments:
       args -- program arguments (dict)
       urls -- Bing URL's found (list)
       input_args -- command arguments entered in link prompt (list)
    """
    split_args = ''.join(input_args).split('-')
    start = split_args[0].strip()
    end = split_args[1].strip()

    start_is_num = utils.check_input(start, num=True)
    end_is_num = utils.check_input(end, num=True)
    if start_is_num and end_is_num:
        # Open close-ended range of urls
        if int(start) > 0 and int(end) <= len(urls)+1:
            for i in range(int(start), int(end)+1):
                open_url(args, urls[i-1])
    elif start_is_num:
        # Open open-ended range of urls
        if int(start) > 0:
            for i in range(int(start), len(urls)+1):
                open_url(args, urls[i-1])
    elif end_is_num:
        # Open open-ended range of urls
        if int(end) < len(urls)+1:
            for i in range(1, int(end)+1):
                open_url(args, urls[i-1])


def open_links(args, urls, input_args):
    """Open one or more links

       Keyword arguments:
       args -- program arguments (dict)
       urls -- Bing URL's found (list)
       input_args -- command arguments entered in link prompt (list)
    """
    if not isinstance(input_args, list):
        input_args = [input_args]

    for num in input_args:
        if not utils.check_input(num.strip(), num=True):
            return

    links = []
    for num in input_args:
        if int(num) > 0 and int(num) <= len(urls):
            links.append(urls[int(num)-1])
    open_url(args, links)


def exec_bkmark(args, urls, input_args):
    """Execute a bookmark command

       Keyword arguments:
       args -- program arguments (dict)
       urls -- Bing URL's found (list)
       input_args -- command arguments entered in link prompt (list)
    """
    if 'add' in input_args:
        # If adding a bookmark, must resolve URL first
        temp_args = []
        for i, arg in enumerate(input_args):
            if utils.check_input(arg, num=True):
                temp_args.append(urls[i-1])
            else:
                temp_args.append(arg)
        input_args = temp_args

    if utils.check_input(input_args):
        args['query'] = input_args
        search(args)


def exec_prompt_cmd(args, urls, input_cmd, input_args, display_prompt):
    """Execute a command in the link prompt

       Keyword arguments:
       args -- program arguments (dict)
       urls -- Bing URL's found (list)
       input_args -- command arguments entered in link prompt (list)
       display_prompt -- whether link prompt is being displayed (bool)

       Possible commands are listed under LINK_HELP.
    """
    reset_flags = True
    if input_cmd[0] not in ascii_letters:
        # Default command is open
        input_args = [input_cmd] + input_args
        input_cmd = 'o'
        reset_flags = False

    # get_lookup_flags is a dictionary containing possible flag inputs
    # Keys are the first letter of the flag name
    # Possible flag inputs are listed in LINK_HELP
    for key, value in iteritems(utils.get_lookup_flags(args)):
        if key == input_cmd or value == input_cmd:
            # Reset all flags and set chosen flag to True
            if reset_flags:
                args = utils.reset_flags(args)
                args[value] = True

            if key == 'b':
                exec_bkmark(args, urls, input_args)
            elif key == 'd' or key == 'o' or key == 'p':
                # Open/Print/Describe link(s)

                # Remove commas
                if any([',' in arg for arg in input_args]):
                    input_args = ''.join(input_args).split(',')
                    input_args = [arg for arg in input_args if arg]

                if any(['-' in arg for arg in input_args]):
                    # Open a link number range
                    open_link_range(args, urls, input_args)
                elif input_args and display_prompt:
                    # Open one or more links
                    open_links(args, urls, input_args)
            elif key == 'f':
                args['query'] = urls[0]
                search(args)
            elif key == 'v':
                print(__version__)
            elif key == 'c':
                print(CONFIG_FPATH)
            elif key == 's':
                args['query'] = input_args
                search(args)


def display_link_prompt(args, urls, url_descs):
    """Print URL's and their descriptions alongside a prompt

       Keyword arguments:
       args -- program arguments (dict)
       urls -- Bing URL's found (list)
       url_descs -- descriptions of Bing URL's found (list)
    """
    display_prompt = True
    while display_prompt:
        print('\n{0}'.format(BORDER))
        for i in range(len(urls)):
            print('{0}. {1}'.format(i+1, uni(url_descs[i])))
        print(BORDER)

        # Handle link prompt input
        try:
            link_input = [inp.strip() for inp in input(': ').split()]
            if not link_input:
                continue
            input_cmd = link_input[0]
            input_args = link_input[1:]
            while input_cmd == 'h' or input_cmd == 'help':
                print(LINK_HELP)
                link_input = [inp.strip() for inp in input(': ').split()]
                input_cmd = link_input[0]
                input_args = link_input[1:]
            print('\n')

            # Check input in case of quit
            utils.check_input(link_input)
            exec_prompt_cmd(args, urls, input_cmd, input_args, display_prompt)
        except (KeyboardInterrupt, ValueError, IndexError):
            return False


def bing_search(args, html):
    """Perform a Bing search"""
    if html is None:
        return open_url(args, 'https://www.google.com')
    elif args['open']:
        return open_url(args, args['query'])

    try:
        unprocessed_urls = html.xpath('//h2/a/@href')
    except AttributeError:
        raise AttributeError('Failed to retrieve data from lxml object!')
    if not unprocessed_urls:
        sys.stderr.write('Failed to retrieve links from Bing.\n')
        return None

    urls = []
    url_descs = []
    base_url = 'www.bing.com'
    for url in unprocessed_urls:
        if url.startswith('/') and base_url not in url:
            # Add missing base url
            urls.append('http://{0}{1}'.format(base_url, url))
            if "'" in url:
                ld_xpath = '//h2/a[@href="{0}"]//text()'.format(url)
            else:
                ld_xpath = "//h2/a[@href='{0}']//text()".format(url)
            url_descs.append(''.join(html.xpath(ld_xpath)))
        elif url.startswith('http://') or url.startswith('https://'):
            urls.append(url)
            if "'" in url:
                ld_xpath = '//h2/a[@href="{0}"]//text()'.format(url)
            else:
                ld_xpath = "//h2/a[@href='{0}']//text()".format(url)
            url_descs.append(''.join(html.xpath(ld_xpath)))

    if urls and url_descs:
        return display_link_prompt(args, urls, url_descs)
    return False


def reformat_wolfram_entries(titles, entries):
    """Reformat Wolfram entries"""
    output_list = []
    for title, entry in zip(titles, entries):
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


def wolfram_search(args, html):
    """Search WolframAlpha using their API, requires API key in .cliqrc"""
    if html is None:
        return open_url(args, 'http://www.wolframalpha.com')
    elif args['open']:
        return open_url(args, args['query'])

    try:
        # Filter unnecessary title fields
        titles = list(OrderedDict.fromkeys(
            html.xpath("//pod[@title != '' and "
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
            entry = html.xpath(entry_xpath)
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


def bing_instant(html):
    """Check for a Bing instant result"""
    try:
        inst_result = html.xpath('//span[@id="rcTB"]/text()'
                                 '|//div[@class="b_focusTextMedium"]/text()'
                                 '|//p[@class="b_secondaryFocus df_p"]'
                                 '/text()'
                                 '|//div[@class="b_xlText b_secondaryText"]'
                                 '/text()'
                                 '|//input[@id="uc_rv"]/@value'
                                 '|//ol[@class="b_dList b_indent"]'  # define
                                 '/li/div/text()')
    except AttributeError:
        raise AttributeError('Failed to retrieve data from lxml object!')

    try:
        if inst_result:
            if len(inst_result) == 1:
                print(uni(inst_result[0]))
            else:
                print(uni('\n'.join(inst_result)))
            return True
    except AttributeError:
        pass
    return False


def open_first(args, html):
    """Open the first Bing link available, `Feeling Lucky`"""
    try:
        bing_urls = html.xpath('//h2/a/@href')
        if not bing_urls:
            sys.stderr.write('Failed to retrieve links from Bing.\n')
            return None
        url = bing_urls[0]
    except AttributeError:
        raise AttributeError('Failed to retrieve data from lxml object!')

    if url.startswith('http://') or url.startswith('https://'):
        return open_url(args, url)
    else:
        return open_url(args, 'http://{0}'.format(url))


def reload_bookmarks():
    """Read in bookmarks again from .cliqrc"""
    CONFIG['bookmarks'] = read_config()[2]


def find_bookmark_idx(query):
    """Find the index of a bookmark given substrings"""
    bkmarks = CONFIG['bookmarks']
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


def tag_bookmark(bk_idx, tags):
    """Tag an existing bookmark with an alias"""
    bkmarks = CONFIG['bookmarks']
    if isinstance(tags, list):
        tags = ' '.join(tags)
    with open(CONFIG_FPATH, 'w') as cfg:
        cfg.write('api_key: {0}'.format(CONFIG['api_key']))
        cfg.write('\nbrowser: {0}'.format(CONFIG['browser']))
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
        cfg.write('\nbrowser: {0}'.format(CONFIG['browser']))
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


def mv_bookmarks(idx1, idx2):
    """Move bookmarks to the start, end, or at another bookmark's position"""
    if idx1 == idx2:
        sys.stderr.write('Bookmark indices equal!\n')
        sys.stderr.write(BOOKMARK_HELP)
        return True

    bkmarks = CONFIG['bookmarks']
    b_len = len(bkmarks)
    with open(CONFIG_FPATH, 'w') as cfg:
        cfg.write('api_key: {0}'.format(CONFIG['api_key']))
        cfg.write('\nbrowser: {0}'.format(CONFIG['browser']))
        cfg.write('\nbookmarks: ')

        # Pairs that are both out of range are incorrect
        if (idx1 < 0 or idx1 >= b_len) and (idx2 < 0 or idx2 >= b_len):
            sys.stderr.write('Bookmark indices out of range!\n')
            sys.stderr.write(BOOKMARK_HELP)
            return True

        # Move bookmark to the front or end, or insert at an index
        if idx1 < 0:
            # Move bookmark 2 to the front
            if idx2 >= 0 and idx2 < b_len:
                bkmarks.insert(0, bkmarks.pop(idx2))
        elif idx1 >= len(bkmarks):
            # Move bookmark 2 to the end
            if idx2 >= 0 and idx2 < b_len:
                bkmarks.append(bkmarks.pop(idx2))
        elif idx2 < 0:
            # Move bookmark 1 to the front
            if idx1 >= 0 and idx1 < b_len:
                bkmarks.insert(0, bkmarks.pop(idx1))
        elif idx2 >= len(bkmarks):
            # Move bookmark 1 to the end
            if idx1 >= 0 and idx1 < b_len:
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


def rm_bookmark(bk_idx):
    """Remove an existing bookmark from the list of saved bookmarks"""
    bkmarks = CONFIG['bookmarks']
    with open(CONFIG_FPATH, 'w') as cfg:
        cfg.write('api_key: {0}'.format(CONFIG['api_key']))
        cfg.write('\nbrowser: {0}'.format(CONFIG['browser']))
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


def print_bookmarks(bkmarks):
    """Print all saved bookmarks"""
    print('Bookmarks:')
    for i, bkmark in enumerate(bkmarks):
        if '(' in bkmark and ')' in bkmark:
            bkmark = bkmark.split('(')[1].rstrip(')')
        print('{0}. {1}'.format(str(i+1), bkmark))
    return True


def bkmark_add_cmd(query):
    """add: add [url..]"""
    query = query[3:].strip()
    queries = query.split()
    clean_bkmarks = []
    for arg in queries:
        arg = utils.append_scheme(arg)
        if '.' not in arg:
            if '(' in arg and ')' in arg:
                split_arg = arg.split('(')
                tag = split_arg[1].rstrip(')')
                bkmark = split_arg[0].strip()
                arg = '{0}.com ({1})'.format(bkmark, tag)
            else:
                arg = '{0}.com'.format(arg)
        clean_bkmarks.append(arg)
    return add_bookmark(clean_bkmarks)


def bkmark_tag_cmd(query):
    """tag: tag [num or suburl] [tag..]"""
    split_args = query[3:].strip().split()
    query = split_args[0]
    tags = split_args[1:]
    if not utils.check_input(query, num=True):
        # If input is not a number then find the correct number
        bk_idx = find_bookmark_idx(query)
        if bk_idx > 0:
            query = bk_idx
    if utils.check_input(query, num=True):
        return tag_bookmark(query, tags)
    else:
        sys.stderr.write('Failed to tag bookmark {0}.\n'
                         .format(str(query)))


def bkmark_untag_cmd(query):
    """untag: untag [num or suburl or tag] [subtag..]"""
    split_args = query[5:].strip().split()
    tags_to_rm = split_args[1:]
    # Find the bookmark index
    bkmark_idx = 0
    if not utils.check_input(split_args[0], num=True):
        # If input is not a number then find the correct number
        bk_idx = find_bookmark_idx(split_args[0])
        if bk_idx > 0:
            bkmark_idx = bk_idx
    else:
        bkmark_idx = split_args[0]
    return untag_bookmark(bkmark_idx, tags_to_rm)


def bkmark_mv_cmd(query):
    """move: mv [num or suburl or tag] [num or suburl or tag]"""
    split_args = query[2:].strip().split()
    if len(split_args) != 2:
        sys.stderr.write(BOOKMARK_HELP)
        return True

    bk1 = bk1_idx = split_args[0]
    bk2 = bk2_idx = split_args[1]
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
    return mv_bookmarks(int(bk1_idx)-1, int(bk2_idx)-1)


def bkmark_rm_cmd(query):
    """delete: rm [num or suburl or tag..]"""
    split_args = query[3:].strip().split()
    bkmark_idxs = []
    for u_arg in split_args:
        if not utils.check_input(u_arg, num=True):
            # If input is not a number then find the correct number
            bk_idx = find_bookmark_idx(u_arg)
            if bk_idx > 0:
                bkmark_idxs.append(bk_idx)
        else:
            bkmark_idxs.append(u_arg)
    return rm_bookmark(bkmark_idxs)


def bkmark_open_cmd(args, query, bkmarks):
    """open: [num or suburl or tag..]"""
    split_args = query.strip().split()
    bookmark_nums = [x for x in split_args if utils.check_input(x, num=True)]
    bookmark_kws = list(split_args)
    for num in bookmark_nums:
        bookmark_kws.remove(num)
    bookmark_kws = ' '.join(bookmark_kws)
    for num in bookmark_nums:
        # open: [num]
        try:
            bkmark = bkmarks[int(num) - 1]
            if '(' in bkmark and ')' in bkmark:
                open_url(args, bkmark.split('(')[0].strip())
            else:
                open_url(args, bkmark)
            return True
        except IndexError:
            sys.stderr.write('Bookmark {0} not found.\n'
                             .format(num))
            return False

    # open: [suburl or tag]
    bk_idx = find_bookmark_idx(bookmark_kws)
    if bk_idx > 0:
        try:
            bkmark = bkmarks[int(bk_idx)-1]
            if '(' in bkmark and ')' in bkmark:
                open_url(args, bkmark.split('(')[0].strip())
            else:
                open_url(args, bkmark)
            return True
        except IndexError:
            sys.stderr.write('Bookmark {0} not found.\n'
                             .format(bk_idx))
            return False
    else:
        sys.stderr.write(BOOKMARK_HELP)
        return True


def bookmarks(args, query):
    """Open, add, tag, untag, move, or delete bookmarks"""
    bkmarks = CONFIG['bookmarks']
    if isinstance(query, list):
        query = ' '.join(query)
    if not query:
        # Print bookmarks if no arguments provided
        return print_bookmarks(bkmarks)

    if query.startswith('add'):
        return bkmark_add_cmd(query)
    elif query.startswith('tag'):
        return bkmark_tag_cmd(query)
    elif query.startswith('untag'):
        return bkmark_untag_cmd(query)
    elif query.startswith('mv'):
        return bkmark_mv_cmd(query)
    elif query.startswith('rm'):
        return bkmark_rm_cmd(query)
    else:
        return bkmark_open_cmd(args, query, bkmarks)


def open_browser(url):
    """Open a browser using webbrowser (or for cygwin use a system call)"""
    if CONFIG['browser'] == 'cygwin':
        call(['cygstart', url])
    else:
        if CONFIG['br']:
            CONFIG['br'].open(url)
        else:
            sys.stderr.write('Failed to open browser.\n')


def open_url(args, urls):
    """Print, describe, or open URL's in the browser"""
    if args['open']:
        if args['search']:
            open_browser(get_bing_query_url(args['query']))
            return True
        elif args['wolfram']:
            open_browser(get_wolfram_query_url(args['query']))
            return True

    base_url = 'www.bing.com'
    urls = utils.append_scheme(urls)
    if isinstance(urls, list):
        urls = ['http://{0}{1}'.format(base_url, x) if x.startswith('/') else x
                for x in urls]
        if args['print']:
            for url in urls:
                print(url)
            return urls
        elif args['describe']:
            for url in urls:
                describe_url(url)
            return urls
        else:
            if not urls:
                open_browser('')
            else:
                for url in urls:
                    open_browser(url)
            return True
    else:
        if urls.startswith('/'):
            urls = 'http://{0}{1}'.format(base_url, urls)
        if args['print']:
            print(urls)
            return urls
        elif args['describe']:
            describe_url(urls)
            return urls
        else:
            if not urls:
                open_browser('')
            else:
                open_browser(urls)
            return True


def describe_url(url):
    """Print a text preview of a given URL"""
    try:
        # Get title and text for summarization
        html = utils.get_html(url)
        title = utils.get_title(html)
        text = utils.get_text(html)
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
    if not any([args['query'], args['open'], args['bookmark'],
                args['search'], args['wolfram']]):
        sys.stderr.write('No search terms entered.\n')
        return False

    if args['query']:
        args['query'] = utils.clean_query(args, ' '.join(args['query']))
        # Get response from Bing or WolframAlpha based on program flags
        html = get_search_html(args)
    else:
        html = None
    # Default search if no flags provided or Wolfram search fails
    default_search = False
    if args['open']:
        # Open a link directly
        return open_url(args, args['query'])
    elif args['bookmark']:
        # Add, delete, or open bookmarks
        return bookmarks(args, args['query'])
    elif args['search']:
        # Perform a Bing search and show an interactive prompt
        return bing_search(args, html)
    elif args['first']:
        # Open the first Bing link available, 'Feeling Lucky'
        return open_first(args, html)
    elif args['wolfram']:
        # Search WolframAlpha and continues search if failed
        success = wolfram_search(args, html)
        if not success:
            default_search = True
        else:
            return success
    else:
        default_search = True

    if default_search:
        # Default program behavior
        #    1. Check Bing for an instant result
        #    2. Check WolframAlpha for a result
        #    3. Check Bing for search results
        result = None
        if args['wolfram']:
            bing_html = get_bing_html(args['query'])
            wolf_html = html
        else:
            bing_html = html

        result = bing_instant(bing_html)
        if not result:
            if not args['wolfram']:
                wolf_html = get_wolfram_html(args['query'])
            result = wolfram_search(args, wolf_html)
            if not result:
                return bing_search(args, bing_html)
        return result


def command_line_runner():
    """Handle command-line interaction"""
    parser = get_parser()
    args = vars(parser.parse_args())

    api_key, browser, bkmarks = read_config()
    CONFIG['api_key'] = api_key
    CONFIG['browser'] = browser
    CONFIG['bookmarks'] = bkmarks
    try:
        if browser and browser != 'cygwin':
            CONFIG['br'] = webbrowser.get(browser)
        else:
            CONFIG['br'] = webbrowser.get()
    except webbrowser.Error as err:
        sys.stderr.write('{0}: {1}\n'.format(str(err), browser))

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

    # Enable cache unless user sets environ variable CLIQ_DISABLE_CACHE
    if not os.getenv('CLIQ_DISABLE_CACHE'):
        enable_cache()
    if not api_key and args['wolfram']:
        args['wolfram'] = False
        sys.stderr.write('Missing WolframAlpha API key in .cliqrc!\n')
    if not any([args['query'], args['open'], args['bookmark'],
                args['search'], args['wolfram']]):
        parser = get_parser()
        parser.print_help()
    else:
        search(args)


if __name__ == '__main__':
    command_line_runner()
