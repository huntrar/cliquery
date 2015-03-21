#!/usr/bin/env python
# -*- coding: utf-8 -*-
# VERSION: 0.2.2
# AUTHOR: Hunter Hammond
# DEPENDENCIES: pip install lxml

import argparse
from collections import OrderedDict
import itertools
import os
import re
from subprocess import call
import sys
import time
import urllib2
import webbrowser

import lxml.html as lh


class CLIQuery:
    def __init__(self, url_args, search_flag, first_flag, open_flag, wolfram_flag, desc_flag, bookmk_flag):
        self.bookmarks = []
        self.bookmk_flag = bookmk_flag
        self.config = os.path.dirname(os.path.realpath(__file__)) + '/.cliqrc'
        self.api_key, self.browser = self.read_config()
        self.search_flag = search_flag
        self.first_flag = first_flag
        self.open_flag = open_flag
        self.wolfram_flag = wolfram_flag
        self.desc_flag = desc_flag
        self.url_args = self.process_args(url_args)
        self.html = self.get_html()
        try:
            if self.browser:
                self.br = webbrowser.get(self.browser)
            else:
                self.br = ''
        except webbrowser.Error:
            self.br = ''

    def read_config(self):
        with open(self.config, 'r') as f:
            api_key = ''
            browser = ''
            lines = []
            # API key and browser name should be in first two lines of .cliqrc
            for i in xrange(2):
                line = f.readline()
                if 'api_key:' in line:
                    api_key = line.replace('api_key:', '').strip()
                elif 'browser:' in line:
                    browser = line.replace('browser:', '').strip()
                else:
                    lines.append(line)
            if self.bookmk_flag:
                bookmarks = f.read()
                if 'bookmarks:' in bookmarks:
                    bookmarks = bookmarks.replace('bookmarks:', '').split('\n')
                    for bookmk in bookmarks:
                        if bookmk:
                            self.bookmarks.append(bookmk.strip())
            if api_key and browser:
                return api_key, browser
            else:
                try:
                    return lines[0].strip(), lines[1].strip() 
                except IndexError:
                    return '', ''

    def check_input(self, u_input):
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

    def clean_url(self, urls):
        # Returns True if list, False otherwise
        clean_urls = []
        if type(urls) == list:
            for url in urls:
                if 'http://' not in url and 'https://' not in url:
                    clean_urls.append('http://' + url)
            return clean_urls, True
        else:
            if 'http://' in urls or 'https://' in urls:
                return urls, False
            else:
                return ('http://' + urls), False

    def process_args(self, url_args):
        clean_args = []
        if url_args:
            for arg in url_args:
                if ' ' in arg:
                    for split_arg in arg.split(' '):
                        clean_args.append(split_arg)
                else:
                    clean_args.append(arg)
        else:
            if not self.bookmk_flag:
                sys.stderr.write('No search terms entered.\n')
                sys.exit()

        # Further processing of args before they are added to base_url
        new_url_args = []
        if not self.open_flag:
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
                if '.' not in url_arg and ':' not in url_arg:
                    new_url_args.append(url_arg + '.com')
                else:
                    new_url_args.append(url_arg)
        return new_url_args

    def get_html(self):
        if self.bookmk_flag:
            return ''
        if not self.open_flag:
            if not self.wolfram_flag:
                return self.get_bing_html(self.url_args)
            else:
                return self.get_wolfram_html(self.url_args)
        else:
            return ''

    def get_html_resp(self, url):
        try:
            # Get HTML response
            request = urllib2.Request(url, headers={ 'User-Agent' : 'Mozilla/5.0' })
            return lh.parse(urllib2.urlopen(request))
        except Exception as e:
            sys.stderr.write('Failed to retrieve ' + url + '\n')
            sys.stderr.write(str(e))
            return ''

    def get_bing_html(self, url_args): 
        base_url = 'http://www.bing.com/search?q='
        url = base_url + url_args
        return self.get_html_resp(url)

    def get_wolfram_html(self, url_args):
        base_url = 'http://api.wolframalpha.com/v2/query?input='
        url = base_url + url_args + '&appid=' + self.api_key
        return self.get_html_resp(url)
    
    def bing_search(self, html):
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
                print '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -'
                for i in xrange(len(links)):
                    print_desc = (str(i+1) + '. ' + link_descs[i]).encode('utf-8')
                    print print_desc # Print link choices
                print '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -'
                try:
                    print ':',
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
                            if not self.check_input(num):
                                print_links = False

                    print '\n'
                    if bookmk_page:
                        self.add_bookmark(links, link_num)
                    elif link_nums and print_links:
                        for num in link_nums:
                            if int(num) > 0 and int(num) <= len(links):
                                self.open_url(links[int(num)-1], override_desc, override_search) 
                    elif self.check_input(start_num) and self.check_input(end_num):
                        if int(start_num) > 0 and int(end_num) <= len(links)+1:
                            for i in xrange(int(start_num), int(end_num)+1, 1):
                                self.open_url(links[i-1], override_desc, override_search) 
                    elif self.check_input(start_num):
                        if int(start_num) > 0:
                            for i in xrange(int(start_num), len(links)+1, 1):
                                self.open_url(links[i-1], override_desc, override_search) 
                    elif self.check_input(end_num):
                        if int(end_num) < len(links)+1:
                            for i in xrange(1, int(end_num)+1, 1):
                                self.open_url(links[i-1], override_desc, override_search) 
                    else:
                        print_links = self.check_input(link_num)
                        if link_num and int(link_num) > 0 and int(link_num) < len(links)+1:
                            self.open_url(links[int(link_num)-1], override_desc, override_search)
                except (ValueError, IndexError):
                    pass

        return False

    def wolfram_search(self, html):
        # Parse Wolfram|Alpha response for potential answers
        try:
            titles = list(OrderedDict.fromkeys(html.xpath("//pod[@title != '' and @title != 'Number line' and @title != 'Input' and @title != 'Visual representation' and @title != 'Image' and @title != 'Manipulatives illustration' and @title != 'Quotient and remainder']/@title")))
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
                print '\n'.join(output_list[:2]).encode('utf-8')
                print 'See more? (y/n):',
                if self.check_input(raw_input('')):
                    print '\n'.join(output_list[2:]).encode('utf-8')
            else:
                print '\n'.join(output_list).encode('utf-8')
            return True
        else:
            return False

    def bing_calculate(self, html):
        try:
            calc_result = html.xpath('//span[@id="rcTB"]/text()|//div[@class="b_focusTextMedium"]/text()|//p[@class="b_secondaryFocus df_p"]/text()|//div[@class="b_xlText b_secondaryText"]/text()|//input[@id="uc_rv"]/@value')
            define_result = html.xpath('//ol[@class="b_dList b_indent"]/li/div/text()')
        except AttributeError:
            sys.exit()
        try:
            # Check if calculation result is present or age/date
            if calc_result:
                if len(calc_result) == 1:
                    print (calc_result[0]).encode('utf-8')
                else:
                    print ('\n'.join(calc_result)).encode('utf-8')
                return True
            # Check if calculation result is a definition
            elif define_result:
                if len(define_result) == 1:
                    print (define_result[0]).encode('utf-8')
                else:
                    print ('\n'.join(define_result)).encode('utf-8')
                return True
        except AttributeError:
            pass
        return False

    def open_first(self, html):
        try:
            unprocessed_links = html.xpath('//h2/a/@href')
            for link in unprocessed_links:
                if not re.search('(ad|Ad|AD)(?=\W)', link): # Basic ad block
                    if 'http://' in link or 'https://' in link:
                        self.open_url(link)
                        sys.exit()
                    elif '/images/' in link:
                        link = 'http://www.bing.com' + link
                        self.open_url(link)
                        sys.exit()
        except AttributeError:
            sys.exit()

    def open_bookmark(self, link_num):
        if not link_num:
            print 'Bookmarks:'
            for i in xrange(len(self.bookmarks)):
                print str(i+1) + '. ' + self.bookmarks[i]
        elif self.check_input(link_num):
            try:
                self.open_url(self.bookmarks[int(link_num) - 1])
            except IndexError:
                sys.stderr.write('Bookmark ' + link_num + ' not found.\n')
        else:
            if 'del+' in link_num:
                link_num = link_num.replace('del+', '').strip()
                self.del_bookmark(link_num)
            if '.' in link_num:
                if 'http://' in link_num or 'https://' in link_num:
                    self.add_bookmark(link_num)
                else:
                    self.add_bookmark('http://' + link_num)

    def add_bookmark(self, links, link_num = []):
        with open(self.config, 'a') as f:
            if type(links) == list and link_num:
                f.write(links[int(link_num)] + '\n')
            elif type(links) == str:
                f.write(links + '\n')

    def del_bookmark(self, link_num):
        with open(self.config, 'w') as f:
            f.write('api_key: ' + self.api_key)
            f.write('\nbrowser: ' + self.browser)
            f.write('\nbookmarks: ')
            for i in xrange(len(self.bookmarks)):
                if i != int(link_num)-1:
                    f.write(self.bookmarks[i] + '\n')

    def open_browser(self, link):
        if self.browser == 'cygwin':
            call(['cygstart', link])
        else:
            if self.br:
                self.br.open(link)
            else:
                sys.stderr.write('Could not locate runnable browser, make sure the browser path in config is correct. Cygwin users use "cygwin"\n')

    def open_url(self, links, override_desc = False, override_search = False):
        if override_desc:
            links, is_list = self.clean_url(links)
            if is_list:
                for link in links:
                    self.open_browser(link)
            else:
                self.open_browser(links)
        elif override_search or self.desc_flag:
            links, is_list = self.clean_url(links)
            if is_list:
                for link in links:
                    self.describe_page(link)
            else:
                self.describe_page(links)
        else:
            links, is_list = self.clean_url(links)
            if is_list:
                for link in links:
                    self.open_browser(link)
            else:
                self.open_browser(links)

    def describe_page(self, url):
        html = self.get_html_resp(url)
        body = ''.join(html.xpath('//body//*[not(self::script) and not(self::style)]/text()')).split('\n')
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
            print url.encode('utf-8') + '\n'
            see_more = False
            for msg in print_body:
                print '\n' + msg.encode('utf-8')
                print 'See more? (y/n):',
                ans = raw_input('')
                if not self.check_input(ans):
                    break
                see_more = True
        else:
            sys.stderr.write('Description not found.\n')
            return False
        if not see_more: 
            time.sleep(1)
        print ''
        return True

    def search(self):
        continue_search = False
        if self.bookmk_flag:
            self.open_bookmark(self.url_args) 
        elif self.open_flag:
            self.open_url(self.url_args)
        elif self.search_flag:
            self.bing_search(self.html)
        elif self.first_flag:
            self.open_first(self.html)        
        elif self.wolfram_flag:
            success = self.wolfram_search(self.html)
            if not success:
                continue_search = True
        else:
            continue_search = True

        if continue_search:
            # Defaults to bing_calculate, then wolfram_search, then bing_search
            if self.wolfram_flag:
                bing_html = self.get_bing_html(self.url_args) 
                wolf_html = self.html
            else:
                bing_html = self.html
            if not self.bing_calculate(bing_html):
                if not self.wolfram_flag:
                    wolf_html = self.get_wolfram_html(self.url_args)
                if not self.wolfram_search(wolf_html):
                    self.bing_search(bing_html)


if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--search', help='Get Bing search results',
    action='store_true')
    parser.add_argument('-f', '--first', help='Open first link result',
    action='store_true')
    parser.add_argument('-o', '--open', help='Open url directly',
    action='store_true')
    parser.add_argument('-w', '--wolfram', help='Get Wolfram|Alpha search results',
    action='store_true')
    parser.add_argument('-d', '--describe', help='Return a snippet of a page',
    action='store_true')
    parser.add_argument('-b', '--bookmark', help='Open add and delete bookmarks',
    action='store_true')
    parser.add_argument('URL_ARGS', nargs='*', help='Search keywords')
    args = parser.parse_args()
    search = bool(args.search)
    first = bool(args.first)
    openurl = bool(args.open)
    wolfram = bool(args.wolfram)
    describe = bool(args.describe)
    bookmk = bool(args.bookmark)
    query = CLIQuery(args.URL_ARGS, search, first, openurl, wolfram, describe, bookmk)
    query.search()

