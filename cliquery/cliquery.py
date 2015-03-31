#!/usr/bin/env python

#############################################################
#                                                           #
# CLIQuery - a command line search engine and browsing tool #
# written by Hunter Hammond (huntrar@gmail.com)             #
#                                                           #
#############################################################

import argparse
from collections import OrderedDict
import itertools
import os
import random
import re
from subprocess import call
import sys
import time
import urllib2
import webbrowser
from . import __version__

import lxml.html as lh


USER_AGENTS = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
                'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100 101 Firefox/22.0',
                'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5',
                'Mozilla/5.0 (Windows; Windows NT 6.1) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5')

CONFIG = os.path.dirname(os.path.realpath(__file__)) + '/.cliqrc'

if not os.path.isfile(CONFIG):
    with open(CONFIG, 'w') as f:
        f.write('api_key:\n')
        f.write('browser:\n')
        f.write('bookmarks:\n')
    sys.stderr.write('Enter your WolframAlpha API Key and browser in %s' % CONFIG)
    sys.exit()


def read_config(args):
    with open(CONFIG, 'r') as f:
        lines = []
        # API key and browser name should be in first two lines of .cliqrc
        for i in xrange(2):
            line = f.readline()
            if 'api_key:' in line:
                API_KEY = line.replace('api_key:', '').strip()
            elif 'browser:' in line:
                BROWSER = line.replace('browser:', '').strip()
            else:
                lines.append(line)

        BOOKMARKS = []
        if args['bookmark']:
            bookmks = f.read()
            if 'bookmarks:' in bookmks:
                bookmks = bookmks.replace('bookmarks:', '').split('\n')
                for bookmk in bookmks:
                    if bookmk:
                        BOOKMARKS.append(bookmk.strip())
        if not API_KEY and not BROWSER:
            sys.stderr.write('API_KEY or browser missing in %s. Attempting anyways..\n' % CONFIG) 
            try:
                API_KEY = lines[0].strip()
                BROWSER = lines[1].strip() 
                return API_KEY, BROWSER, BOOKMARKS
            except IndexError:
                return '', '', ''
        else:
            return API_KEY, BROWSER, BOOKMARKS


def check_input(u_input):
    u_inp = u_input.lower()
    if u_inp == 'y' or u_inp == 'yes':
        return True
    elif u_inp == 'q' or u_inp == 'quit':
        sys.exit()
    else:
        try:
            u_inp = int(u_input)
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


def get_html(cfg, args):
    url_args = args['query']
    if args['bookmark']:
        return ''
    if not args['open']:
        if not args['wolfram']:
            return get_bing_html(url_args)
        else:
            return get_wolfram_html(cfg, url_args)
    else:
        return ''


def get_html_resp(url):
    try:
        # Get HTML response
        request = urllib2.Request(url, headers={'User-Agent' : random.choice(USER_AGENTS)})
        return lh.parse(urllib2.urlopen(request))
    except Exception as e:
        sys.stderr.write('Failed to retrieve ' + url + '\n')
        sys.stderr.write(str(e))
        return ''


def get_bing_html(url_args): 
    base_url = 'http://www.bing.com/search?q='
    url = base_url + url_args
    return get_html_resp(url)


def get_wolfram_html(cfg, url_args):
    base_url = 'http://api.wolframalpha.com/v2/query?input='
    url = base_url + url_args + '&appid=' + cfg['API_KEY']
    return get_html_resp(url)


def bing_search(cfg, args, html):
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
            print('- - - - - - - - - - - - - - - - - - - - - - - - - - - -'
                 ' - - - - - - - - - - - -')
            for i in xrange(len(links)):
                print_desc = (str(i+1) + '. ' + link_descs[i]).encode('utf-8')
                print(print_desc) # Print link choices
            print('- - - - - - - - - - - - - - - - - - - - - - - - - - - -'
                 ' - - - - - - - - - - - -')
            try:
                print(':'),
                link_num = raw_input('').strip()
                override_desc = False
                override_search = False
                bookmk_page = False
                start_num = ''
                end_num = ''
                link_nums = []
                if 'b' in link_num:
                    link_num = link_num.replace('b', '').strip()
                    bookmk_page = True
                elif 'o' in link_num:
                    link_num = link_num.replace('o', '').strip()
                    override_desc = True
                elif 'd' in link_num:
                    link_num = link_num.replace('d', '').strip()
                    override_search = True
                if '-' in link_num and len(link_num) >= 2:
                    start_num = link_num.split('-')[0].strip()
                    end_num = link_num.split('-')[1].strip()
                if ',' in link_num and len(link_num) >= 3:
                    link_nums = link_num.split(',')
                    for num in link_nums:
                        if not check_input(num):
                            print_links = False

                print('\n')
                if bookmk_page:
                    add_bookmark(links, link_num)
                elif link_nums and print_links:
                    for num in link_nums:
                        if int(num) > 0 and int(num) <= len(links):
                            open_url(cfg, args, links[int(num)-1], override_desc, override_search) 
                elif check_input(start_num) and check_input(end_num):
                    if int(start_num) > 0 and int(end_num) <= len(links)+1:
                        for i in xrange(int(start_num), int(end_num)+1, 1):
                            open_url(cfg, args, links[i-1], override_desc, override_search) 
                elif check_input(start_num):
                    if int(start_num) > 0:
                        for i in xrange(int(start_num), len(links)+1, 1):
                            open_url(cfg, args, links[i-1], override_desc, override_search) 
                elif check_input(end_num):
                    if int(end_num) < len(links)+1:
                        for i in xrange(1, int(end_num)+1, 1):
                            open_url(cfg, args, links[i-1], override_desc, override_search) 
                else:
                    print_links = check_input(link_num)
                    if link_num and int(link_num) > 0 and int(link_num) < len(links)+1:
                        open_url(cfg, args, links[int(link_num)-1], override_desc, override_search)
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
        for title, entry in itertools.izip(titles, entries):
            try:
                if ' |' in entry:
                    entry = '\n\t' + entry.replace(' |', ':').replace('\n', '\n\t')
                if title == 'Result':
                    output_list.append(entry).encode('utf-8')
                else:
                    output_list.append(title + ': ' + entry).encode('utf-8')
            except (AttributeError, UnicodeEncodeError):
                pass
        if not output_list:
            return False
        elif len(output_list) > 2:
            print('\n'.join(output_list[:2]).encode('utf-8'))
            print('See more? (y/n):'),
            if check_input(raw_input('')):
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


def open_first(cfg, args, html):
    try:
        unprocessed_links = html.xpath('//h2/a/@href')
        for link in unprocessed_links:
            if not re.search('(ad|Ad|AD)(?=\W)', link): # Basic ad block
                if 'http://' in link or 'https://' in link:
                    if args['describe']:
                        describe_page(link)
                    else:
                        open_url(cfg, args, link)
                    sys.exit()
                elif '/images/' in link:
                    link = 'http://www.bing.com' + link
                    open_url(cfg, args, link)
                    sys.exit()
    except AttributeError:
        sys.exit()


def open_bookmark(cfg, args, link_arg):
    bookmarks = cfg['BOOKMARKS']
    if not link_arg:
        print('Bookmarks:')
        for i in xrange(len(bookmarks)):
            print(str(i+1) + '. ' + bookmarks[i])
    elif check_input(link_arg):
        try:
            open_url(cfg, args, bookmarks[int(link_arg) - 1])
        except IndexError:
            sys.stderr.write('Bookmark ' + link_arg + ' not found.\n')
    else:
        if 'del+' in link_arg:
            link_arg = link_arg.replace('del+', '').strip()
            del_bookmark(cfg, bookmarks, link_arg)
        else:
            if 'http://' not in link_arg or 'https://' not in link_arg:
                link_arg = 'http://' + link_arg
            if '.' not in link_arg:
                link_arg = link_arg + '.com'
            add_bookmark(link_arg)


def add_bookmark(links, link_num = []):
    with open(CONFIG, 'a') as f:
        if type(links) == list and link_num:
            f.write(links[int(link_num)] + '\n')
        elif type(links) == str:
            f.write(links + '\n')


def del_bookmark(cfg, link_num):
    bookmarks = cfg['BOOKMARKS']
    with open(CONFIG, 'w') as f:
        f.write('api_key: ' + cfg['API_KEY'])
        f.write('\nbrowser: ' + cfg['BROWSER'])
        f.write('\nbookmarks: ')
        for i in xrange(len(bookmarks)):
            if i != int(link_num)-1:
                f.write(bookmarks[i] + '\n')


def open_browser(cfg, link):
    if cfg['BROWSER'] == 'cygwin':
        call(['cygstart', link])
    else:
        if cfg['br']:
            cfg['br'].open(link)
        else:
            sys.stderr.write('Could not locate runnable browser, make sure '                    'you entered a valid browser in .cliqrc'
                ' Cygwin users use "cygwin"\n')


def open_url(cfg, args, links, override_desc = False, override_search = False):
    if override_desc:
        links, is_list = clean_url(links)
        if is_list:
            for link in links:
                open_browser(cfg, link)
        else:
            open_browser(cfg, links)
    elif override_search or args['describe']:
        links, is_list = clean_url(links)
        if is_list:
            for link in links:
                describe_page(link)
        else:
            describe_page(links)
    else:
        links, is_list = clean_url(links)
        if is_list:
            for link in links:
                open_browser(cfg, link)
        else:
            open_browser(cfg, links)


def describe_page(url):
    html = get_html_resp(url)
    body = ''.join(html.xpath('//body//*[not(self::script) and '
         'not(self::style)]/text()')).split('\n')
    if not body:
        sys.stderr.write('Description not found.\n')
        return False
    stripped_body = []
    for b in body:
        stripped_body.append(b.strip())
    filtered_body = filter(None, stripped_body)
    if not filtered_body:
        sys.stderr.write('Description not found.\n')
        return False
    body_sum = 0
    for b in filtered_body:
        body_sum += len(b)
    body_avg_sum = body_sum / len(filtered_body)
    print_body = []
    for b in filtered_body:
        # Qualifying describe statements are at least half the average statement length
        if len(b) > (body_avg_sum / 2): 
            print_body.append(b)
    if print_body:
        print(url.encode('utf-8') + '\n')
        see_more = False
        for msg in print_body:
            print('\n' + msg.encode('utf-8'))
            print('See more? (y/n):'),
            ans = raw_input('')
            if not check_input(ans):
                break
            see_more = True
    else:
        sys.stderr.write('Description not found.\n')
        return False
    if not see_more: 
        time.sleep(1)
    print('')
    return True
    

def search(cfg, args):
    html = get_html(cfg, args)
    url_args = args['query']
    continue_search = False

    if args['bookmark']:
        open_bookmark(cfg, args, url_args) 
    elif args['open']:
        open_url(cfg, args, url_args)
    elif args['search']:
        bing_search(cfg, args, html)
    elif args['describe']:
        if '.' in url_args:
            open_first(cfg, args, html)   
        else:
            describe_page(url_args)
    elif args['first']:
        open_first(cfg, args, html)
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
                wolf_html = get_wolfram_html(cfg, url_args)
            if not wolfram_search(wolf_html):
                bing_search(cfg, args, bing_html)


def cliquery(args):
    args['query'] = process_args(args)
    try:
        cfg = {}
        API_KEY, BROWSER, BOOKMARKS = read_config(args)
        cfg['API_KEY'] = API_KEY
        cfg['BROWSER'] = BROWSER
        cfg['BOOKMARKS'] = BOOKMARKS
        try:
            if BROWSER:
                cfg['br'] = webbrowser.get(BROWSER)
            else:
                cfg['br'] = ''
        except webbrowser.Error as w:
            sys.stderr.write('Error loading browser object\n')
            sys.stderr.write(str(w))
        search(cfg, args)
    except Exception as e:
        sys.stderr.write('Search failed, see error below:\n')
        sys.stderr.write(str(e)) 


def get_parser():
    parser = argparse.ArgumentParser(description='a command line search engine and browsing tool')
    parser.add_argument('query', metavar='QUERY', type=str, nargs='*', 
                        help='keywords to search')
    parser.add_argument('-s', '--search', help='display search links',
                        action='store_true')
    parser.add_argument('-f', '--first', help='open first link',
                        action='store_true')
    parser.add_argument('-o', '--open', help='open link manually',
                        action='store_true')
    parser.add_argument('-w', '--wolfram', help='display wolfram results',
                        action='store_true')
    parser.add_argument('-d', '--describe', help='display page snippet',
                        action='store_true')
    parser.add_argument('-b', '--bookmark', help='view and modify bookmarks',
                        action='store_true')
    parser.add_argument('-v', '--version', help='display current version',
                        action='store_true')
    return parser


def command_line_runner():
    parser = get_parser()
    args = vars(parser.parse_args()) 
    
    if args['version']:
        print(__version__)
        return
        
    if not args['query'] and not args['bookmark']:
        parser.print_help()
        return 
    else:
        cliquery(args)
        

if __name__ == '__main__':
    command_line_runner()


