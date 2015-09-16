#!/usr/bin/env python

#############################################################
#                                                           #
# cliquery - a command-line browsing utility              #
# written by Hunter Hammond (huntrar@gmail.com)             #
#                                                           #
#############################################################


from __future__ import absolute_import
import argparse
from collections import OrderedDict
import glob
import os
import random
from subprocess import call
import sys
import time
import webbrowser

import lxml.html as lh
import requests
import requests_cache

from cliquery import utils
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
    '\tp, print     print link to stdout\n'
    '\tc, config    print location of config file\n'
    '\tv, version   display current version\n')

BORDER_LEN = 28
BORDER = ' '.join(['+' for i in range(BORDER_LEN)])

CONFIG_DIR = os.path.dirname(os.path.realpath(__file__))
if os.path.isfile('{0}/.local.cliqrc'.format(CONFIG_DIR)):
    CONFIG_FPATH = '{0}/.local.cliqrc'.format(CONFIG_DIR)
else:
    CONFIG_FPATH = '{0}/.cliqrc'.format(CONFIG_DIR)
CONFIG = {}

XDG_CACHE_DIR = os.environ.get('XDG_CACHE_HOME',
    os.path.join(os.path.expanduser('~'), '.cache'))
CACHE_DIR = os.path.join(XDG_CACHE_DIR, 'cliquery')
CACHE_FILE = os.path.join(CACHE_DIR, 'cache{0}'.format(
    sys.version_info[0] if sys.version_info[0] == 3 else ''))


def get_parser():
    parser = argparse.ArgumentParser(description='a command-line browsing utility')
    parser.add_argument('query', metavar='QUERY', type=str, nargs='*', 
                        help='keywords to search')
    parser.add_argument('-b', '--bookmark', help='view and modify bookmarks',
                        action='store_true')
    parser.add_argument('-c', '--config', help='print location of config file',
                        action='store_true')
    parser.add_argument('-C', '--clear-cache', help='clear the cache',
                        action='store_true')
    parser.add_argument('-d', '--describe', help='display page snippet',
                        action='store_true')
    parser.add_argument('-f', '--first', help='open first link',
                        action='store_true')
    parser.add_argument('-o', '--open', help='open link or browser manually',
                        action='store_true')
    parser.add_argument('-p', '--print', help='print link to stdout and exit',
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
        ''' first two lines of .cliqrc must contain api_key: and browser: '''
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
                return '', '', bookmarks 
        else:
            return api_key, browser, bookmarks


def enable_cache():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    requests_cache.install_cache(CACHE_FILE)


def clear_cache():
    for cache in glob.glob('{0}*'.format(CACHE_FILE)):
        os.remove(cache)


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
    return utils.get_html('http://www.bing.com/search?q={0}'.format(url_args))


def get_wolfram_html(url_args):
    base_url = 'http://api.wolframalpha.com/v2/query?input='
    api = CONFIG['api_key']
    return utils.get_html('{0}{1}&appid={2}'.format(base_url, url_args, api))


def bing_search(args, html):
    ''' Perform a Bing search and show an interactive prompt '''

    try:
        unprocessed_urls = html.xpath('//h2/a/@href')
    except AttributeError:
        raise AttributeError('Failed to retrieve links from Bing lxml.html.HtmlElement object!')

    if not unprocessed_urls:
        sys.stderr.write('Failed to retrieve links from Bing.\n')
        return None

    urls = []
    url_descs = []
    for url in unprocessed_urls:
        if url.startswith('http://') or url.startswith('https://'): 
            urls.append(url)
            if "'" in url:
                ld_xpath = '//h2/a[@href="{0}"]//text()'.format(url)
            else:
                ld_xpath = "//h2/a[@href='{0}']//text()".format(url)

            url_desc = html.xpath(ld_xpath)
            if isinstance(url_desc, list):
                url_desc = ''.join(url_desc)
            url_descs.append(url_desc)
        elif (url.startswith('/images/') or url.startswith('/videos/')) and 'www.bing.com' not in url:
            ''' Add missing base url to image links '''
            urls.append('http://www.bing.com{0}'.format(url))
            if "'" in url:
                ld_xpath = '//h2/a[@href="{0}"]//text()'.format(url)
            else:
                ld_xpath = "//h2/a[@href='{0}']//text()".format(url)

            url_desc = html.xpath(ld_xpath)
            if isinstance(url_desc, list):
                url_desc = ''.join(url_desc)
            url_descs.append(url_desc)
    
    if urls and url_descs:
        print_links = True
        while print_links:
            print('\n{0}'.format(BORDER))
            for i in range(len(urls)):
                print_desc = (str(i+1) + '. ' + url_descs[i]).encode('utf-8')
                print(print_desc) # Print url choices
            print(BORDER)

            ''' Get link prompt input '''
            try:
                ''' A dictionary containing all boolean arguments
                    The key is the first letter of the extended arg name
                '''
                flag_lookup = utils.get_flags(args)

                link_input_num = input(': ').strip()
                link_input_cmd = link_input_num.split(' ')[0]
                url_args = link_input_num.strip().split(' ')[1:]
                while link_input_cmd == 'h' or link_input_cmd == 'help':
                    print(LINK_HELP)
                    link_input_num = input(': ').strip()
                    link_input_cmd = link_input_num.split(' ')[0]
                    url_args = link_input_num.strip().split(' ')[1:]
                print('\n')

                utils.check_input(link_input_num) # Checks for quit
                continue_exec = True
                url_arg = ''.join(url_args)
                if not url_arg:
                    url_arg = link_input_num

                for k, v in flag_lookup.items():
                    if k == link_input_cmd or v == link_input_cmd:
                        ''' Reset all flags and set chosen flag to True '''
                        args = utils.reset_flags(args)
                        args[v] = True

                        ''' Handle the different link prompt flags '''
                        if k == 'b':
                            if utils.check_input(url_arg):
                                args['query'] = url_args
                                continue_exec = False
                                return search(args)
                            break
                        elif k == 'd' or k == 'o' or k == 'p':
                            ''' continue_exec remains True '''
                            break
                        elif k == 'f':
                            return open_url(args, urls[0])
                            continue_exec = False
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
                            args['query'] = url_args
                            continue_exec = False
                            return search(args)
                            break

                ''' Open link number(s) ''' 
                if continue_exec:
                    url_args = []
                    start_num = ''
                    end_num = ''

                    ''' Check for a link number range (contains dash) '''
                    if '-' in url_arg and len(url_arg) > 1:
                        start_num = url_arg.split('-')[0].strip()
                        end_num = url_arg.split('-')[1].strip()

                    ''' Check for multiple link numbers and validate them '''
                    if ',' in url_arg and len(url_arg) > 2:
                        url_args = url_arg.split(',')
                        for num in url_args:
                            if not utils.check_input(num.strip(), num=True):
                                print_links = False

                    ''' Open multiple links if validation succeeded '''
                    if url_args and print_links:
                        for num in url_args:
                            if int(num) > 0 and int(num) <= len(urls):
                                return open_url(args, urls[int(num)-1]) 
                    else:
                        ''' Open range of link or a single link '''
                        start = utils.check_input(start_num, num=True)
                        end = utils.check_input(end_num, num=True)

                        if start and end:
                            if int(start_num) > 0 and int(end_num) <= len(urls)+1:
                                for i in range(int(start_num), int(end_num)+1, 1):
                                    return open_url(args, urls[i-1]) 
                        elif start:
                            if int(start_num) > 0:
                                for i in range(int(start_num), len(urls)+1, 1):
                                    return open_url(args, urls[i-1]) 
                        elif end:
                            if int(end_num) < len(urls)+1:
                                for i in range(1, int(end_num)+1, 1):
                                    return open_url(args, urls[i-1]) 
                        else:
                            ''' Open a single link '''
                            if url_arg and int(url_arg) > 0 and int(url_arg) < len(urls)+1:
                                return open_url(args, urls[int(url_arg)-1])
            except (ValueError, IndexError):
                pass
    return False


def wolfram_search(html):
    ''' Searches WolframAlpha using their API, requires API key in .cliqrc '''

    try:
        ''' Filter unnecessary title fields '''
        titles = list(OrderedDict.fromkeys(
            html.xpath("//pod[@title != '' and "
            "@title != 'Number line' and @title != 'Input' and "
            "@title != 'Visual representation' and @title != 'Image' and "
            "@title != 'Manipulatives illustration' and "
            "@title != 'Quotient and remainder']/@title")))
    except AttributeError:
        raise AttributeError('Failed to retrieve titles from Wolfram lxml.html.HtmlElement object!')

    entries = []
    if titles:
        for title in titles:
            entry_xpath = "//pod[@title='{0}']/subpod/plaintext/text()".format(title)
            entry = html.xpath(entry_xpath)
            if entry:
                entries.append(entry[0])

        entries = list(OrderedDict.fromkeys(entries))
        output_list = []

        ''' Return False if results were empty '''
        if len(entries) == 1 and entries[0] == '{}':
            return False

        for title, entry in zip(titles, entries):
            try:
                ''' Clean formatting '''
                if ' |' in entry:
                    entry = '\n\t{0}'.format(entry.replace(' |', ':').replace('\n', '\n\t'))
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
    ''' Checks for a Bing instant result '''

    try:
        inst_result = html.xpath('//span[@id="rcTB"]/text()'
            '|//div[@class="b_focusTextMedium"]/text()'
            '|//p[@class="b_secondaryFocus df_p"]/text()'
            '|//div[@class="b_xlText b_secondaryText"]/text()'
            '|//input[@id="uc_rv"]/@value'
            '|//ol[@class="b_dList b_indent"]/li/div/text()') # a definition
    except AttributeError:
        raise AttributeError('Failed to retrieve instant results from Bing lxml.html.HtmlElement object!')

    try:
        if inst_result:
            if len(inst_result) == 1:
                print(inst_result[0].encode('utf-8'))
            else:
                print('\n'.join(inst_result).encode('utf-8'))
            return True
    except AttributeError:
        pass
    return False


def open_first(args, html):
    ''' Open the first Bing link available, `Feeling Lucky` '''

    try:
        unprocessed_urls = html.xpath('//h2/a/@href')

        if not unprocessed_urls:
            sys.stderr.write('Failed to retrieve links from Bing.\n')
            return None

        if args['describe']:
            url = filter(lambda x: not x.startswith('/images/') and not x.startswith('/videos/'), unprocessed_urls)[0]
        else:
            url = unprocessed_urls[0]
    except (AttributeError, IndexError):
        raise AttributeError('Failed to retrieve first link from Bing lxml.html.HtmlElement object!')

    if url.startswith('/images/') or url.startswith('/videos/'):
        url = 'http://www.bing.com{0}'.format(url)

    if url.startswith('http://') or url.startswith('https://'):
        return open_url(args, url)
    else:
        return open_url(args, 'http://{0}'.format(url))


def search_bookmark(url_arg):
    bookmarks = CONFIG['bookmarks']
    url_arg = url_arg.strip()
    for i in range(len(bookmarks)):
        if url_arg in bookmarks[i]:
            return i+1
    return -1


def bookmarks(args, url_arg, url_num = []):
    ''' Add, delete, or open bookmarks '''

    bookmarks = CONFIG['bookmarks']
    bk_idx = search_bookmark(url_arg)
    if not url_arg:
        print('Bookmarks:')
        for i in range(len(bookmarks)):
            print('{0}. {1}'.format(str(i+1), bookmarks[i]))
        return True
    elif 'del' in url_arg:
        url_arg = url_arg.replace('del', '').strip()
        if not utils.check_input(url_arg, num=True):
            bk_idx = search_bookmark(url_arg)
            if bk_idx > 0:
                url_arg = bk_idx

        if utils.check_input(url_arg, num=True):
            return del_bookmark(url_arg)
        else:
            sys.stderr.write('Could not delete bookmark {0}.\n'.format(str(url_arg)))
            return False
    elif 'add' in url_arg:
        url_arg = url_arg.replace('add', '').strip()
        if not url_arg.startswith('http://') and not url_arg.startswith('https://'):
            url_arg = 'http://{0}'.format(url_arg)

        if '.' not in url_arg:
            url_arg = '{0}.com'.format(url_arg)
        return add_bookmark(url_arg, url_num)
    elif utils.check_input(url_arg, num=True):
        try:
            open_url(args, bookmarks[int(url_arg) - 1])
            return True
        except IndexError:
            sys.stderr.write('Bookmark {0} not found.\n'.format(url_arg))
            return False
    elif bk_idx > 0:
        url_arg = bk_idx
        try:
            open_url(args, bookmarks[int(url_arg) - 1])
            return True
        except IndexError:
            sys.stderr.write('Bookmark {0} not found.\n'.format(url_arg))
            return False
    else:
        sys.stderr.write('Usage: '
                        '\nopen: [num] or [suburl]'
                        '\nadd: add [url]'
                        '\ndelete: del [num] or [suburl]'
                        '\n')
        return True


def add_bookmark(urls, url_arg):
    try:
        with open(CONFIG_FPATH, 'a') as f:
            if isinstance(urls, list) and url_arg:
                f.write('{0}\n'.format(urls[int(url_arg)]))
            elif isinstance(urls, str):
                f.write('{0}\n'.format(urls))
        return True
    except Exception as e:
        sys.stderr.write('Error adding bookmark: {0}\n'.format(str(e)))
        return False


def del_bookmark(url_arg):
    try:
        bookmarks = CONFIG['bookmarks']
        with open(CONFIG_FPATH, 'w') as f:
            f.write('api_key: {0}'.format(CONFIG['api_key']))
            f.write('\nbrowser: {0}'.format(CONFIG['browser']))
            f.write('\nbookmarks: ')
            for i in range(len(bookmarks)):
                if i != int(url_arg)-1:
                    f.write('{0}\n'.format(bookmarks[i]))
        return True
    except Exception as e:
        sys.stderr.write('Error deleting bookmark: {0}\n'.format(str(e)))
        return False


def open_browser(url):
    if CONFIG['browser'] == 'cygwin':
        call(['cygstart', url])
    else:
        if CONFIG['br']:
            CONFIG['br'].open(url)
        else:
            sys.stderr.write('Failed to open browser.\n')


def open_url(args, urls):
    if args['print']:
        urls = utils.clean_url(urls)
        if isinstance(urls, list):
            for url in urls:
                print(url)
        else:
            print(urls)
        return urls
    elif args['describe']:
        urls = utils.clean_url(urls)
        if isinstance(urls, list):
            for url in urls:
                describe_url(url)
        else:
            describe_url(urls)
        return urls
    else:
        if not urls:
            open_browser('')
        else:
            urls = utils.clean_url(urls)
            if isinstance(urls, list):
                for url in urls:
                    open_browser(url)
            else:
                open_browser(urls)
        return True


def describe_url(url):
    ''' Print the text of a given url
        Printed lines must be greater than the average length / qualifier
    '''

    try:
        if url.startswith('/images/') or url.startswith('/videos/'):
            sys.stderr.write('Link was an image/video, could not describe.\n')
            return False
        elif not url.startswith('http://') and not url.startswith('https://'):
            desc_url = 'http://{0}'.format(url)
        else:
            desc_url = url
    except AttributeError:
        sys.stderr.write('Failed to describe link {0}\n.'.format(url))
        return False 

    qualifier = 5

    html = utils.get_html(desc_url)
    body = ''.join(html.xpath('//body//*[not(self::script) and '
         'not(self::style)]/text()')).split('\n')
    if not body:
        print(('{0}\n'.format(desc_url)).encode('utf-8'))
        print('Extended description not found.\n')
        return False

    stripped_body = []
    for b in body:
        stripped_body.append(b.strip())

    filtered_body = list(filter(None, stripped_body))
    if not filtered_body:
        print(('{0}\n'.format(desc_url)).encode('utf-8'))
        print('Extended description not found.\n')
        return False

    body_sum = 0
    for b in filtered_body:
        body_sum += len(b)
    body_avg_sum = body_sum / len(filtered_body)+1
    print_body = []

    ''' Print lines greater than the average length / qualifier '''
    for b in filtered_body:
        if len(b) > (body_avg_sum / qualifier): 
            print_body.append(b)

    if print_body:
        print(('{0}\n'.format(desc_url)).encode('utf-8'))

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
                print('')
    else:
        print(('{0}\n'.format(desc_url)).encode('utf-8'))
        print('Extended description not found.\n')
        return False

    if not see_more: 
        time.sleep(1)

    print('')
    return True
    

def search(args):
    ''' A query may only be blank if opening an empty browser or checking bookmarks '''
    if not args['query'] and not args['open'] and not args['bookmark']:
        sys.stderr.write('No search terms entered.\n')
        return False

    args['query'] = utils.clean_query(' '.join(args['query']), args['open'], args['bookmark'])
    url_args = args['query']
    html = get_search_html(args)

    ''' Default search if no flags provided or Wolfram search fails '''
    default_search = False

    if args['open']:
        ''' Open a link manually '''
        return open_url(args, url_args)
    elif args['bookmark']:
        ''' Add, delete, or open bookmarks '''
        return bookmarks(args, url_args) 
    elif args['search']:
        ''' Perform a Bing search and show an interactive prompt '''
        return bing_search(args, html)
    elif args['first']:
        ''' Open the first Bing link available, `Feeling Lucky` '''
        return open_first(args, html)   
    elif args['wolfram']:
        ''' Searches WolframAlpha and continues search if failed '''
        success = wolfram_search(html)
        if not success:
            default_search = True
        else:
            return success
    else:
        default_search = True

    if default_search:
        ''' Default program behavior
            1. Check Bing for an instant result
            2. Check WolframAlpha for a result
            3. Check Bing for search results
        '''
        result = None

        if args['wolfram']:
            bing_html = get_bing_html(url_args) 
            wolf_html = html
        else:
            bing_html = html

        result = bing_instant(bing_html)
        if not result:
            if not args['wolfram']:
                wolf_html = get_wolfram_html(url_args)
            result = wolfram_search(wolf_html)
            if not result:
                return bing_search(args, bing_html)
        return result


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
        sys.stderr.write('{0}: {1}\n'.format(str(w), browser))
    
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

    ''' Enable cache unless user sets environment variable CLIQ_DISABLE_CACHE '''
    if not os.getenv('CLIQ_DISABLE_CACHE'):
        enable_cache()

    if not api_key and args['wolfram']:
        args['wolfram'] = False
        sys.stderr.write('Missing WolframAlpha API key in .cliqrc!\n')
        
    if not args['query'] and not args['bookmark'] and not args['open']:
        parser = get_parser()
        parser.print_help()
        return 
    else:
        search(args)



if __name__ == '__main__':
    command_line_runner()


