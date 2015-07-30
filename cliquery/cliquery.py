#!/usr/bin/env python

#############################################################
#                                                           #
# cliquery - a command-line browsing interface              #
# written by Hunter Hammond (huntrar@gmail.com)             #
#                                                           #
#############################################################


import argparse
from collections import OrderedDict
import os
import random
from subprocess import call
import sys
import time
import webbrowser

import lxml.html as lh
import requests

import utils
from . import __version__


if sys.version < '3':
    try:
        input = raw_input
    except NameError:
        pass
    try:
        range = xrange
    except NameError:
        pass

LINK_HELP = ('Enter one of the following flags abbreviated or not, possibly followed by a link number:\n'
    '\th, help      show this help message\n'
    '\ts, search    display search links\n'
    '\to, open      open link manually\n'
    '\tw, wolfram   display wolfram results\n'
    '\td, describe  display page snippet\n'
    '\tb, bookmark  view and modify bookmarks\n'
    '\tc, config    print location of config file\n'
    '\tv, version   display current version\n')

BORDER_LEN = 28

BORDER = ' '.join(['+' for i in range(BORDER_LEN)])

CONFIG_FPATH = os.path.dirname(os.path.realpath(__file__)) + '/.cliqrc'

CONFIG = {}


def get_parser():
    parser = argparse.ArgumentParser(description='a command-line browsing interface')
    parser.add_argument('query', metavar='QUERY', type=str, nargs='*', 
                        help='keywords to search')
    parser.add_argument('-b', '--bookmark', help='view and modify bookmarks',
                        action='store_true')
    parser.add_argument('-c', '--config', help='print location of config file',
                        action='store_true')
    parser.add_argument('-d', '--describe', help='display page snippet',
                        action='store_true')
    parser.add_argument('-f', '--first', help='open first link',
                        action='store_true')
    parser.add_argument('-o', '--open', help='open link or browser manually',
                        action='store_true')
    parser.add_argument('-s', '--search', help='display search links',
                        action='store_true')
    parser.add_argument('-v', '--version', help='display current version',
                        action='store_true')
    parser.add_argument('-w', '--wolfram', help='display wolfram results',
                        action='store_true')
    return parser


def read_config(args):
    with open(CONFIG_FPATH, 'r') as f:
        lines = []
        api_key = ''
        browser = ''
        # api_key: and browser: must be in first two lines
        for i in range(2):
            line = f.readline()
            if 'api_key:' in line:
                api_key = line.replace('api_key:', '').strip()
            elif 'browser:' in line:
                browser = line.replace('browser:', '').strip()
            else:
                lines.append(line)

        bookmarks = []
        bookmks = f.read()
        if 'bookmarks:' in bookmks:
            bookmks = bookmks.replace('bookmarks:', '').split('\n')
            for bookmk in bookmks:
                if bookmk:
                    bookmarks.append(bookmk.strip())

        if not api_key and not browser:
            try:
                api_key = lines[0].strip()
                browser = lines[1].strip() 
                return api_key, browser, bookmarks
            except IndexError:
                return '', '', ''
        else:
            return api_key, browser, bookmarks


def get_search_html(args):
    url_args = args['query']
    if args['bookmark']:
        return ''
    if not args['open']:
        if not args['wolfram']:
            return get_bing_html(url_args)
        else:
            return get_wolfram_html(url_args)
    else:
        return ''


def get_bing_html(url_args): 
    base_url = 'http://www.bing.com/search?q='
    url = base_url + url_args
    return utils.get_html(url)


def get_wolfram_html(url_args):
    base_url = 'http://api.wolframalpha.com/v2/query?input='
    url = base_url + url_args + '&appid=' + CONFIG['api_key']
    return utils.get_html(url)


def bing_open(args, link):
    if args['describe']:
        describe(args, link)
    else:
        open_url(args, link)


def bing_search(args, html):
    # Parse Bing response and display link results
    try:
        unprocessed_links = html.xpath('//h2/a/@href')
    except AttributeError:
        sys.exit()
    if not unprocessed_links:
        sys.stderr.write('Failed to retrieve links from Bing.\n')
        return False

    links = []
    link_descs = []
    for link in unprocessed_links:
        if 'http://' in link or 'https://' in link: 
            links.append(link)
            if "'" in link:
                ld_xpath = '//h2/a[@href="' + link + '"]//text()'
            else:
                ld_xpath = "//h2/a[@href='" + link + "']//text()"

            link_desc = html.xpath(ld_xpath)
            if isinstance(link_desc, list):
                link_desc = ''.join(link_desc)
            link_descs.append(link_desc)
        elif '/images/' in link and 'www.bing.com' not in link:
            # Fix image links that are not prepended with www.bing.com
            links.append('http://www.bing.com' + link)
            if "'" in link:
                ld_xpath = '//h2/a[@href="' + str(link) + '"]//text()'
            else:
                ld_xpath = "//h2/a[@href='" + str(link) + "']//text()"

            link_desc = html.xpath(ld_xpath)
            if isinstance(link_desc, list):
                link_desc = ''.join(link_desc)
            link_descs.append(link_desc)
    
    if links and link_descs:
        print_links = True
        while print_links:
            print('\n' + BORDER)
            for i in range(len(links)):
                print_desc = (str(i+1) + '. ' + link_descs[i]).encode('utf-8')
                print(print_desc) # Print link choices
            print(BORDER)

            try:
                flag_lookup = utils.get_flags(args)

                link_input = input(': ').strip()
                link_cmd = link_input.split(' ')[0]
                link_args = link_input.strip().split(' ')[1:]
                while link_cmd == 'h' or link_cmd == 'help':
                    print(LINK_HELP)
                    link_input = input(': ').strip()
                    link_cmd = link_input.split(' ')[0]
                    link_args = link_input.strip().split(' ')[1:]
                print('\n')

                utils.check_input(link_input) # In case of quit
                continue_exec = True
                link_arg = ''.join(link_args)
                if not link_arg:
                    link_arg = link_input

                for k, v in flag_lookup.items():
                    if k == link_cmd or v == link_cmd:
                        args = utils.reset_flags(args)
                        args[v] = True
                        if k == 'b':
                            if utils.check_input(link_arg):
                                args['query'] = link_args
                                continue_exec = False
                                search(args)
                            break
                        elif k == 'd':
                            if not utils.check_input(link_arg, num=True):
                                continue_exec = False
                            break
                        elif k == 'f':
                            bing_open(args, links[0])
                            continue_exec = False
                            break
                        elif k == 'o':
                            # Default behavior, just leave continue_exec True
                            break
                        elif k == 'v':
                            print(__version__)
                            continue_exec = False
                            break
                        elif k == 'c':
                            print(CONFIG_FPATH)
                            continue_exec = False
                            break
                        else:
                            args['query'] = link_args
                            continue_exec = False
                            search(args)
                            break

                # Open links
                if continue_exec:
                    link_args = []
                    start_num = ''
                    end_num = ''

                    # Check for a number range
                    if '-' in link_arg and len(link_arg) > 1:
                        start_num = link_arg.split('-')[0].strip()
                        end_num = link_arg.split('-')[1].strip()

                    # Check for multiple numbers
                    if ',' in link_arg and len(link_arg) > 2:
                        link_args = link_arg.split(',')
                        for num in link_args:
                            if not utils.check_input(num.strip(), num=True):
                                print_links = False

                    # Handle the multiple numbers
                    if link_args and print_links:
                        for num in link_args:
                            if int(num) > 0 and int(num) <= len(links):
                                bing_open(args, links[int(num)-1]) 
                    else:
                        # Handle a range or a single number
                        start = utils.check_input(start_num, num=True)
                        end = utils.check_input(end_num, num=True)

                        if start and end:
                            if int(start_num) > 0 and int(end_num) <= len(links)+1:
                                for i in range(int(start_num), int(end_num)+1, 1):
                                    bing_open(args, links[i-1]) 
                        elif start:
                            if int(start_num) > 0:
                                for i in range(int(start_num), len(links)+1, 1):
                                    bing_open(args, links[i-1]) 
                        elif end:
                            if int(end_num) < len(links)+1:
                                for i in range(1, int(end_num)+1, 1):
                                    bing_open(args, links[i-1]) 
                        else:
                            # Handle single number
                            if link_arg and int(link_arg) > 0 and int(link_arg) < len(links)+1:
                                bing_open(args, links[int(link_arg)-1])
            except (ValueError, IndexError):
                pass
    return False


def wolfram_search(html):
    try:
        titles = list(OrderedDict.fromkeys(html.xpath("//pod[@title != '' and "
            "@title != 'Number line' and @title != 'Input' and "
            "@title != 'Visual representation' and @title != 'Image' and "
            "@title != 'Manipulatives illustration' and "
            "@title != 'Quotient and remainder']/@title")))
    except AttributeError:
        sys.exit()
    entries = []
    if titles:
        for title in titles:
            entry_xpath = "//pod[@title='" + title + "']/subpod/plaintext/text()"
            entry = html.xpath(entry_xpath)
            if entry:
                entries.append(entry[0])

        entries = list(OrderedDict.fromkeys(entries))
        output_list = []
        if len(entries) == 1 and entries[0] == '{}':
            return False

        for title, entry in zip(titles, entries):
            try:
                if ' |' in entry:
                    entry = '\n\t' + entry.replace(' |', ':').replace('\n', '\n\t')
                if title == 'Result':
                    output_list.append(entry.encode('utf-8'))
                else:
                    output_list.append(title + ': ' + entry).encode('utf-8')
            except (AttributeError, UnicodeEncodeError):
                pass

        if not output_list:
            return False
        elif len(output_list) > 2:
            print('\n'.join(output_list[:2]).encode('utf-8'))
            if utils.check_input(input('See more? [Press Enter] '), empty=True):
                print('\n'.join(output_list[2:]).encode('utf-8'))
        else:
            print('\n'.join(output_list).encode('utf-8'))
        return True
    else:
        return False


def bing_instant(html):
    try:
        inst_result = html.xpath('//span[@id="rcTB"]/text()'
            '|//div[@class="b_focusTextMedium"]/text()'
            '|//p[@class="b_secondaryFocus df_p"]/text()'
            '|//div[@class="b_xlText b_secondaryText"]/text()'
            '|//input[@id="uc_rv"]/@value')
        def_result = html.xpath('//ol[@class="b_dList b_indent"]/li/div/text()')
    except AttributeError:
        sys.exit()
    try:
        # Check if calculation result is present or age/date
        if inst_result:
            if len(inst_result) == 1:
                print(inst_result[0].encode('utf-8'))
            else:
                print('\n'.join(inst_result).encode('utf-8'))
            return True
        # Check if definition is present
        elif def_result:
            if len(def_result) == 1:
                print(def_result[0].encode('utf-8'))
            else:
                print('\n'.join(def_result).encode('utf-8'))
            return True
    except AttributeError:
        pass
    return False


def describe(args, link):
    try:
        if 'http://' in link or 'https://' in link:
            query = args['query']
            if '.' not in query:
                describe_link(link)
            else:
                if 'http://' not in query or 'https://' not in query:
                    describe_link('http://' + query)
                else:
                    describe_link(query)
        elif '/images/' in link:
            sys.stderr.write('Link was an image, could not describe.\n')
            if not args['first']:
                print(LINK_HELP)
    except AttributeError:
        sys.stderr.write('Failed to describe link {}\n.'.format(link))


def open_first(args, html):
    try:
        link = html.xpath('//h2/a/@href')[0]
        if 'http://' in link or 'https://' in link:
            open_url(args, link)
        elif '/images/' in link:
            link = 'http://www.bing.com' + link
            open_url(args, link)
    except AttributeError:
        sys.stderr.write('Failed to open first link.\n')


def search_bookmark(link_arg):
    bookmarks = CONFIG['bookmarks']
    link_arg = link_arg.strip()
    for i in range(len(bookmarks)):
        if link_arg in bookmarks[i]:
            return i+1
    return -1


def open_bookmark(args, link_arg, link_num = []):
    bookmarks = CONFIG['bookmarks']
    bk_idx = search_bookmark(link_arg)
    if not link_arg:
        print('Bookmarks:')
        for i in range(len(bookmarks)):
            print(str(i+1) + '. ' + bookmarks[i])
    elif 'del+' in link_arg:
        link_arg = link_arg.replace('del+', '').strip()
        if not utils.check_input(link_arg, num=True):
            bk_idx = search_bookmark(link_arg)
            if bk_idx > 0:
                link_arg = bk_idx

        if utils.check_input(link_arg, num=True):
            del_bookmark(link_arg)
        else:
            sys.stderr.write('Could not delete bookmark {}.\n'.format(str(link_arg)))
    elif 'add+' in link_arg:
        link_arg = link_arg.replace('add+', '').strip()
        if 'http://' not in link_arg or 'https://' not in link_arg:
            link_arg = 'http://' + link_arg

        if '.' not in link_arg:
            link_arg = link_arg + '.com'
        add_bookmark(link_arg, link_num)
    elif utils.check_input(link_arg, num=True):
        try:
            open_url(args, bookmarks[int(link_arg) - 1])
        except IndexError:
            sys.stderr.write('Bookmark {} not found.\n'.format(link_arg))
    elif bk_idx > 0:
        link_arg = bk_idx
        try:
            open_url(args, bookmarks[int(link_arg) - 1])
        except IndexError:
            sys.stderr.write('Bookmark {} not found.\n'.format(link_arg))
    else:
        sys.stderr.write('Usage: '
                        '\nopen: [num] or [suburl]'
                        '\nadd: add [url]'
                        '\ndelete: del [num] or [suburl]'
                        '\n')


def add_bookmark(links, link_arg):
    with open(CONFIG_FPATH, 'a') as f:
        if isinstance(links, list) and link_arg:
            f.write(links[int(link_arg)] + '\n')
        elif isinstance(links, str):
            f.write(links + '\n')


def del_bookmark(link_arg):
    bookmarks = CONFIG['bookmarks']
    with open(CONFIG_FPATH, 'w') as f:
        f.write('api_key: ' + CONFIG['api_key'])
        f.write('\nbrowser: ' + CONFIG['browser'])
        f.write('\nbookmarks: ')
        for i in range(len(bookmarks)):
            if i != int(link_arg)-1:
                f.write(bookmarks[i] + '\n')


def open_browser(link):
    if CONFIG['browser'] == 'cygwin':
        call(['cygstart', link])
    else:
        if CONFIG['br']:
            CONFIG['br'].open(link)
        else:
            sys.stderr.write('Failed to open browser.\n')


def open_url(args, links):
    if args['describe']:
        links, is_list = utils.clean_url(links)
        if is_list:
            for link in links:
                describe_link(link)
        else:
            describe_link(links)
    else:
        if not links:
            open_browser('')
        else:
            links, is_list = utils.clean_url(links)
            if is_list:
                for link in links:
                    open_browser(link)
            else:
                open_browser(links)


def describe_link(url):
    html = utils.get_html(url)
    body = ''.join(html.xpath('//body//*[not(self::script) and '
         'not(self::style)]/text()')).split('\n')
    if not body:
        print(url.encode('utf-8') + '\n'.encode('ascii'))
        print('Extended description not found.\n')
        return False

    stripped_body = []
    for b in body:
        stripped_body.append(b.strip())
    filtered_body = list(filter(None, stripped_body))
    if not filtered_body:
        print(url.encode('utf-8') + '\n'.encode('ascii'))
        print('Extended description not found.\n')
        return False

    body_sum = 0
    for b in filtered_body:
        body_sum += len(b)
    body_avg_sum = body_sum / len(filtered_body)+1
    print_body = []

    for b in filtered_body:
        # Qualifying describe statements are at least half the average statement length
        if len(b) > (body_avg_sum / 2): 
            print_body.append(b)
    if print_body:
        print(url.encode('utf-8') + '\n'.encode('ascii'))
        see_more = False
        MAX_MSG = 200
        msg_count = 0
        for msg in print_body:
            msg_count += len(msg)
            print(msg.encode('utf-8'))
            if msg_count > MAX_MSG:
                if not utils.check_input(input('See more? [Press Enter] '), empty=True):
                    break
                see_more = True
                msg_count = 0
                print('\n' + BORDER)
    else:
        print(url.encode('utf-8') + '\n'.encode('ascii'))
        print('Extended description not found.\n')
        return False
    if not see_more: 
        time.sleep(1)
    print('')
    return True
    

def search(args):
    args['query'] = utils.process_args(args)
    html = get_search_html(args)
    url_args = args['query']
    continue_search = False

    if args['bookmark']:
        open_bookmark(args, url_args) 
    elif args['open']:
        open_url(args, url_args)
    elif args['search']:
        bing_search(args, html)
    elif args['describe']:
        bing_search(args, html)
    elif args['first']:
        open_first(args, html)   
    elif args['wolfram']:
        success = wolfram_search(html)
        if not success:
            continue_search = True
    else:
        continue_search = True

    if continue_search:
        # Default behavior is check Bing for a calculation result, then
        # check WolframAlpha, then to Bing search results
        if args['wolfram']:
            bing_html = get_bing_html(url_args) 
            wolf_html = html
        else:
            bing_html = html
        if not bing_instant(bing_html):
            if not args['wolfram']:
                wolf_html = get_wolfram_html(url_args)
            if not wolfram_search(wolf_html):
                bing_search(args, bing_html)


def command_line_runner():
    parser = get_parser()
    args = vars(parser.parse_args()) 

    api_key, browser, bookmarks = read_config(args)
    CONFIG['api_key'] = api_key
    CONFIG['browser'] = browser
    CONFIG['bookmarks'] = bookmarks
    try:
        if browser and browser != 'cygwin':
            CONFIG['br'] = webbrowser.get(browser)
        else:
            CONFIG['br'] = webbrowser.get()
    except webbrowser.Error as w:
        sys.stderr.write(str(w) + ': ' + browser)
    
    if args['version']:
        print(__version__)
        return

    if args['config']:
        print(CONFIG_FPATH)
        return

    if not api_key:
        args['wolfram'] = False
        
    if not args['query'] and not args['bookmark'] and not args['open']:
        parser = get_parser()
        parser.print_help()
        return 
    else:
        search(args)



if __name__ == '__main__':
    command_line_runner()


