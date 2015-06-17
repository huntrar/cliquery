
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
import re
import requests
from subprocess import call
import sys
import time
import webbrowser
from . import __version__

import lxml.html as lh


USER_AGENTS = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
                'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100 101 Firefox/22.0',
                'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5',
                'Mozilla/5.0 (Windows; Windows NT 6.1) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5')

if sys.version < '3':
    try:
        input = raw_input
    except NameError:
        pass

CONFIG_FPATH = os.path.dirname(os.path.realpath(__file__)) + '/.cliqrc'

CONFIG = {}

def check_config():
    if not os.path.isfile(CONFIG_FPATH):
        with open(CONFIG_FPATH, 'w') as f:
            f.write('api_key:\n')
            f.write('browser:\n')
            f.write('bookmarks:\n')
        sys.stderr.write('Enter your WolframAlpha API Key and browser in %s' % CONFIG_FPATH)
        sys.exit()


def read_config(args):
    check_config()
    with open(CONFIG_FPATH, 'r') as f:
        lines = []
        # API key and browser name should be in first two lines of .cliqrc
        for i in range(2):
            line = f.readline()
            if 'api_key:' in line:
                api_key = line.replace('api_key:', '').strip()
            elif 'browser:' in line:
                browser = line.replace('browser:', '').strip()
            else:
                lines.append(line)

        bookmarks = []
        if args['bookmark']:
            bookmks = f.read()
            if 'bookmarks:' in bookmks:
                bookmks = bookmks.replace('bookmarks:', '').split('\n')
                for bookmk in bookmks:
                    if bookmk:
                        bookmarks.append(bookmk.strip())
        if not api_key and not browser:
            sys.stderr.write('api_key or browser missing in %s. Attempting anyways..\n' % CONFIG_FPATH) 
            try:
                api_key = lines[0].strip()
                browser = lines[1].strip() 
                return api_key, browser, bookmarks
            except IndexError:
                return '', '', ''
        else:
            return api_key, browser, bookmarks


def change_args(args, new_query, new_arg):
    for k in args.keys():
        args[k] = False
    args['query'] = new_query
    args[new_arg] = True
    return args


def check_input(u_input, num = False):
    try:
        u_inp = u_input.lower()
    except AttributeError:
        pass
    if u_inp == 'q' or u_inp == 'quit' or u_inp == 'exit':
        sys.exit()
    if not num:
        if u_inp == 'y' or u_inp == 'yes':
            return True
        return False
    return check_num(u_input)


def check_num(num):
    try:
        n = int(num)
        return True
    except ValueError:
        return False


def clean_url(urls):
    # Returns True if list, False otherwise
    clean_urls = []
    if type(urls) == list:
        for url in urls:
            if 'http://' not in url and 'https://' not in url:
                clean_urls.append('http://' + url)
            else:
                clean_urls.append(url)
        return clean_urls, True
    else:
        if 'http://' in urls or 'https://' in urls:
            return urls, False
        else:
            return ('http://' + urls), False


def process_args(args):
    # Process and returns only query arguments
    url_args = args['query']
    clean_args = []
    if url_args:
        for arg in url_args:
            if ' ' in arg:
                for split_arg in arg.split(' '):
                    clean_args.append(split_arg)
            else:
                clean_args.append(arg)

    # Further processing of url args before they are added to base_url
    new_url_args = []
    if not args['open']:
        symbol_dict = { '@' : '%40',
                        '$' : '%24',
                        '%' : '%25',
                        '&' : '%26',
                        '+' : '%2B',
                        '=' : '%3D' }
        try:
            for url_arg in clean_args:
                for sym in symbol_dict:
                    if sym in url_arg:
                        url_arg = url_arg.replace(sym, symbol_dict[sym])
                new_url_args.append(url_arg)
            new_url_args = '+'.join(new_url_args)
        except IndexError:
            sys.stderr.write('No search terms entered.\n')
            sys.exit()
    else:
        for url_arg in clean_args:
            if '.' not in url_arg and 'localhost' not in url_arg:
                new_url_args.append(url_arg + '.com')
            else:
                new_url_args.append(url_arg)
    return new_url_args


def get_html(args):
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


def get_html_resp(url):
    try:
        # Get HTML response
        headers={'User-Agent' : random.choice(USER_AGENTS)}
        request = requests.get(url, headers=headers)
        return lh.fromstring(request.text.encode('utf-8'))
    except Exception as e:
        sys.stderr.write('Failed to retrieve ' + url + '\n')
        sys.stderr.write(str(e))
        return ''


def get_bing_html(url_args): 
    base_url = 'http://www.bing.com/search?q='
    url = base_url + url_args
    return get_html_resp(url)


def get_wolfram_html(url_args):
    base_url = 'http://api.wolframalpha.com/v2/query?input='
    url = base_url + url_args + '&appid=' + CONFIG['api_key']
    return get_html_resp(url)


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
        if not re.search('(ad|Ad|AD)(?=\W)', link): # Basic ad blocker
            if 'http://' in link or 'https://' in link: 
                links.append(link)
                if "'" in link:
                    ld_xpath = '//h2/a[@href="' + link + '"]//text()'
                else:
                    ld_xpath = "//h2/a[@href='" + link + "']//text()"
                link_desc = html.xpath(ld_xpath)
                if type(link_desc) == list:
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
                if type(link_desc) == list:
                    link_desc = ''.join(link_desc)
                link_descs.append(link_desc)
    
    if links and link_descs:
        print_links = True
        while print_links:
            print('+ + + + + + + + + + + + + + + + + + + + + + + + + + + +'
                 ' + + + + + + + + + + + +')
            for i in range(len(links)):
                print_desc = (str(i+1) + '. ' + link_descs[i]).encode('utf-8')
                print(print_desc) # Print link choices
            print('+ + + + + + + + + + + + + + + + + + + + + + + + + + + +'
                 ' + + + + + + + + + + + +')
            try:
                link_num = input(': ').strip()
                flag_lookup = { 's' : 'search',
                                'o' : 'open',
                                'w' : 'wolfram',
                                'd' : 'describe',
                                'b' : 'bookmark',
                }

                link_cmd = link_num.split(' ')[0]
                while link_cmd == 'h' or link_cmd == 'help':
                    print('Enter one of the following flags abbreviated or not, possibly followed by a link number:\n'
                        '\th, help      show this help message\n'
                        '\ts, search    display search links\n'
                        '\to, open      open link manually\n'
                        '\tw, wolfram   display wolfram results\n'
                        '\td, describe  display page snippet\n'
                        '\tb, bookmark  view and modify bookmarks\n')
                    link_num = input(': ').strip()
                    link_cmd = link_num.split(' ')[0]

                print('\n')

                open_override = False
                desc_override = False
                continue_exec = True
                for k,v in flag_lookup.items():
                    if k == link_cmd or v == link_cmd:
                        if k == 'o':
                            link_num = ''.join(link_num.strip().split(' ')[1:])
                            open_override = True
                        elif k == 'd':
                            link_num = ''.join(link_num.strip().split(' ')[1:])
                            desc_override = True
                        else:
                            link_num = link_num.strip().split(' ')[1:]
                            args = change_args(args, link_num, v)
                            continue_exec = False
                            search(args)

                if continue_exec:
                    link_nums = []
                    start_num = ''
                    end_num = ''
                    if '-' in link_num and len(link_num) >= 2:
                        start_num = link_num.split('-')[0].strip()
                        end_num = link_num.split('-')[1].strip()
                    if ',' in link_num and len(link_num) >= 3:
                        link_nums = link_num.split(',')
                        for num in link_nums:
                            if not check_input(num, num=True):
                                print_links = False

                    if link_nums and print_links:
                        for num in link_nums:
                            if int(num) > 0 and int(num) <= len(links):
                                open_url(args, links[int(num)-1], open_override, desc_override) 
                    else:
                        start = check_input(start_num, num=True)
                        end = check_input(end_num, num=True)

                        if start and end:
                            if int(start_num) > 0 and int(end_num) <= len(links)+1:
                                for i in range(int(start_num), int(end_num)+1, 1):
                                    open_url(args, links[i-1], open_override, desc_override) 
                        elif start:
                            if int(start_num) > 0:
                                for i in range(int(start_num), len(links)+1, 1):
                                    open_url(args, links[i-1], open_override, desc_override) 
                        elif end:
                            if int(end_num) < len(links)+1:
                                for i in range(1, int(end_num)+1, 1):
                                    open_url(args, links[i-1], open_override, desc_override) 
                        else:
                            print_links = check_input(link_num, num=True)
                            if link_num and int(link_num) > 0 and int(link_num) < len(links)+1:
                                open_url(args, links[int(link_num)-1], open_override, desc_override)
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
            if check_input(input('See more? (y/n): ')):
                print ('\n'.join(output_list[2:]).encode('utf-8'))
        else:
            print ('\n'.join(output_list).encode('utf-8'))
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


def open_first(args, html):
    try:
        unprocessed_links = html.xpath('//h2/a/@href')
        for link in unprocessed_links:
            if not re.search('(ad|Ad|AD)(?=\W)', link): # Basic ad block
                if 'http://' in link or 'https://' in link:
                    if args['describe']:
                        query = args['query']
                        if not '.' in query:
                            describe_page(link)
                        else:
                            if 'http://' not in query or 'https://' not in query:
                                describe_page('http://' + query)
                            else:
                                describe_page(query)
                    else:
                        open_url(args, link)
                    sys.exit()
                elif '/images/' in link:
                    link = 'http://www.bing.com' + link
                    open_url(args, link)
                    sys.exit()
    except AttributeError:
        sys.exit()


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
        if not check_input(link_arg, num=True):
            bk_idx = search_bookmark(link_arg)
            if bk_idx > 0:
                link_arg = bk_idx
        if check_input(link_arg, num=True):
            del_bookmark(link_arg)
        else:
            sys.stderr.write('Could not delete bookmark ' + str(link_arg))
    elif 'add+' in link_arg:
        link_arg = link_arg.replace('add+', '').strip()
        if 'http://' not in link_arg or 'https://' not in link_arg:
            link_arg = 'http://' + link_arg
        if '.' not in link_arg:
            link_arg = link_arg + '.com'
        add_bookmark(link_arg, link_num)
    elif check_input(link_arg, num=True):
        try:
            open_url(args, bookmarks[int(link_arg) - 1])
        except IndexError:
            sys.stderr.write('Bookmark ' + link_arg + ' not found.\n')
    elif bk_idx > 0:
        link_arg = bk_idx
        try:
            open_url(args, bookmarks[int(link_arg) - 1])
        except IndexError:
            sys.stderr.write('Bookmark ' + link_arg + ' not found.\n')
    else:
        sys.stderr.write('Usage: '
                        '\nopen: [num] or [suburl]'
                        '\nadd: add [url]'
                        '\ndelete: del [num] or [suburl]'
                        '\n')


def add_bookmark(links, link_num):
    with open(CONFIG_FPATH, 'a') as f:
        if type(links) == list and link_num:
            f.write(links[int(link_num)] + '\n')
        elif type(links) == str:
            f.write(links + '\n')


def del_bookmark(link_num):
    bookmarks = CONFIG['bookmarks']
    with open(CONFIG_FPATH, 'w') as f:
        f.write('api_key: ' + CONFIG['api_key'])
        f.write('\nbrowser: ' + CONFIG['browser'])
        f.write('\nbookmarks: ')
        for i in range(len(bookmarks)):
            if i != int(link_num)-1:
                f.write(bookmarks[i] + '\n')


def open_browser(link):
    if CONFIG['browser'] == 'cygwin':
        call(['cygstart', link])
    else:
        if CONFIG['br']:
            CONFIG['br'].open(link)
        else:
            sys.stderr.write('Could not locate runnable browser, make sure '
                'you entered a valid browser in .cliqrc'
                ' Cygwin users use "cygwin"\n')


def open_url(args, links, open_override = False, desc_override = False):
    if open_override:
        links, is_list = clean_url(links)
        if is_list:
            for link in links:
                open_browser(link)
        else:
            open_browser(links)
    elif desc_override or args['describe']:
        links, is_list = clean_url(links)
        if is_list:
            for link in links:
                describe_page(link)
        else:
            describe_page(links)
    else:
        if not links:
            open_browser('')
        else:
            links, is_list = clean_url(links)
            if is_list:
                for link in links:
                    open_browser(link)
            else:
                open_browser(links)



def describe_page(url):
    html = get_html_resp(url)
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
                if not check_input(input('See more? (y/n): ')):
                    break
                see_more = True
                msg_count = 0
                print('\n+ + + + + + + + + + + + + + + + + + + + + + + + + + + +'
                 ' + + + + + + + + + + + +')
    else:
        print(url.encode('utf-8') + '\n'.encode('ascii'))
        print('Extended description not found.\n')
        return False
    if not see_more: 
        time.sleep(1)
    print('')
    return True
    

def search(args):
    args['query'] = process_args(args)
    html = get_html(args)
    url_args = args['query']
    continue_search = False

    if args['bookmark']:
        open_bookmark(args, url_args) 
    elif args['open']:
        open_url(args, url_args)
    elif args['search']:
        bing_search(args, html)
    elif args['describe'] or args['first']:
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


def get_parser():
    parser = argparse.ArgumentParser(description='a command-line browsing interface')
    parser.add_argument('query', metavar='QUERY', type=str, nargs='*', 
                        help='keywords to search')
    parser.add_argument('-s', '--search', help='display search links',
                        action='store_true')
    parser.add_argument('-f', '--first', help='open first link',
                        action='store_true')
    parser.add_argument('-o', '--open', help='open link or browser manually',
                        action='store_true')
    parser.add_argument('-w', '--wolfram', help='display wolfram results',
                        action='store_true')
    parser.add_argument('-d', '--describe', help='display page snippet',
                        action='store_true')
    parser.add_argument('-b', '--bookmark', help='view and modify bookmarks',
                        action='store_true')
    parser.add_argument('-c', '--config', help='print location of config file',
                        action='store_true')
    parser.add_argument('-v', '--version', help='display current version',
                        action='store_true')
    return parser


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
            CONFIG['br'] = ''
    except webbrowser.Error as w:
        sys.stderr.write(str(w) + ': ' + browser)
    

    if args['version']:
        print(__version__)
        return

    if args['config']:
        print(CONFIG_FPATH)
        return
        
    if not args['query'] and not args['bookmark'] and not args['open']:
        parser = get_parser()
        parser.print_help()
        return 
    else:
        search(args)
        

if __name__ == '__main__':
    command_line_runner()


