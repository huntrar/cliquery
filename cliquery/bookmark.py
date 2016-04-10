"""Cliquery bookmark functions"""

from __future__ import absolute_import, print_function
from collections import OrderedDict
import re
import sys

import lxml.html as lh

from cliquery import utils
from .compat import iteritems, itervalues
from .config import CONFIG, CONFIG_FPATH, read_config
from .open import open_url
from . import crange


BOOKMARK_HELP = ('Usage: '
                 '\nopen: [num.. OR url/tag substr] [additional URL args..]'
                 '\nadd: add [url..]'
                 '\nremove: rm [num.. OR url/tag substr..]'
                 '\ntag: tag [num OR suburl] [tag..]'
                 '\nuntag: untag [num OR url/tag substr] [tag..]'
                 '\ndescribe: desc [num.. OR url/tag substr..]'
                 '\nmove: mv [num OR url/tag substr] [num OR url/tag substr]'
                 '\n')


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


def remove_bookmark(bk_idx=None):
    """Remove an existing bookmark from the list of saved bookmarks"""
    bkmarks = CONFIG['bookmarks']
    with open(CONFIG_FPATH, 'w') as cfg:
        cfg.write('api_key: {0}'.format(CONFIG['api_key']))
        cfg.write('\nbrowser: {0}'.format(CONFIG['browser_name']))
        cfg.write('\nbookmarks: ')
        if bk_idx is not None:
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
            for i in crange(start_range, end_range, range_inc):
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
    trimmed_query = query[3:].strip()
    if not trimmed_query:
        sys.stderr.write(BOOKMARK_HELP)
        return False

    if '(' in trimmed_query and ')' in trimmed_query:
        # Split by tag and space
        split_query = re.findall(r'\([^)]+\)|\S+', trimmed_query)
    else:
        # Split by space
        split_query = trimmed_query.split()

    new_bkmarks = []
    for arg in split_query:
        if '(' in arg and ')' in arg:
            # This is a tag, try to add it to the previous bookmark
            tag = arg.split('(')[1].rstrip(')')
            if len(new_bkmarks) > 0:
                new_bkmarks[-1] = '{0} ({1})'.format(new_bkmarks[-1], tag)
        else:
            arg = utils.append_scheme(arg)
            if '.' not in arg:
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


def import_bookmarks(filename):
    """Import bookmarks exported from browser as HTML"""
    def read_bookmarks(toolbar):
        """Read bookmarks from HTML in import_bookmarks"""
        with open(filename, 'r') as bkmark_file:
            html = lh.fromstring(bkmark_file.read().split(toolbar)[-1])

        imported_bookmarks = [x.xpath('//a') for x in html.xpath('//dt')]
        new_bookmarks = OrderedDict()
        if imported_bookmarks:
            for bkmark in imported_bookmarks[0]:
                url = bkmark.xpath('@href')[0]
                if utils.check_scheme(url):
                    new_bookmarks[url] = bkmark.xpath('text()')
        return new_bookmarks

    ff_tbar = 'Bookmarks Toolbar'
    gc_tbar = 'Bookmarks bar'
    toolbars = {'firefox': ff_tbar,
                'chrome': gc_tbar,
                'iceweasel': ff_tbar,
                'chromium': gc_tbar}

    # Try to find toolbar which matches to browser specified in configuration
    toolbar_found = False
    for browser, toolbar in iteritems(toolbars):
        if CONFIG['browser_name'] in browser:
            new_bookmarks = read_bookmarks(toolbar)
            if new_bookmarks:
                toolbar_found = True
                break
    if not toolbar_found:
        new_bookmarks = read_bookmarks(ff_tbar) or read_bookmarks(gc_tbar)

    if new_bookmarks:
        # Add and tag new bookmarks
        add_bookmark(list(new_bookmarks.keys()))
        for i, tag in enumerate(itervalues(new_bookmarks)):
            if tag:
                tag_bookmark(i, tag)
        return True
    return False


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
