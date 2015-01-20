#!/usr/bin/env python
# VERSION: 0.2.1
# AUTHOR: Hunter Hammond
# DEPENDENCIES: pip install lxml

import argparse
from collections import OrderedDict
import itertools
import os
import re
import sys
import urllib2
import webbrowser

import lxml.html as lh


class CLIQuery:
    def __init__(self, url_args, search_flag, first_flag, open_flag, wolfram_flag):
        self.api_key, self.br_name = self.ReadConfig()
        self.search_flag = search_flag
        self.first_flag = first_flag
        self.open_flag = open_flag
        self.wolfram_flag = wolfram_flag
        self.url_args = self.ProcessArgs(url_args)
        self.html = self.GetHTML()

    def ReadConfig(self):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        with open(script_dir + '/config.txt', 'r') as f:
            return f.readline().strip(), f.readline().strip() 

    def ProcessArgs(self, url_args):
        clean_args = []
        if url_args:
            for arg in url_args:
                try:
                    if " " in arg:
                        for split_arg in arg.split(" "):
                            clean_args.append(split_arg)
                    else:
                        clean_args.append(arg)
                except IndexError:
                    sys.stderr.write('No search terms entered.\n')
                    sys.exit()
        else:
            sys.stderr.write('No search terms entered.\n')
            sys.exit()

        # Further processing of args before they are added to base_url
        new_url_args = []
        if not self.open_flag:
            try:
                for url_arg in clean_args:
                    if "+" in url_arg:
                        url_arg = arg.replace('+', '%2B')
                    new_url_args.append(url_arg)
                if len(new_url_args) > 1:
                    new_url_args = '+'.join(new_url_args)
                else:
                    new_url_args = new_url_args[0]
            except IndexError:
                sys.stderr.write('No search terms entered.\n')
                sys.exit()
        else:
            for url_arg in clean_args:
                if ".com" not in url_arg:
                    new_url_args.append(url_arg + ".com")
                else:
                    new_url_args.append(url_arg)
        return new_url_args

    def GetHTML(self):
        if not self.open_flag:
            if not self.wolfram_flag:
                return self.GetBingHTML(self.url_args)
            else:
                return self.GetWolframHTML(self.url_args)
        else:
            return ''

    def GetBingHTML(self, url_args): 
        base_url = 'http://www.bing.com/search?q='
        url = base_url + url_args
        try:
            # Get HTML response
            request = urllib2.Request(url, headers={ 'User-Agent' : 'Mozilla/5.0' })
            return lh.parse(urllib2.urlopen(request))
        except urllib2.URLError:
            sys.stderr.write('Failed to retrieve webpage.\n')
            return ''

    def GetWolframHTML(self, url_args):
        base_url = 'http://api.wolframalpha.com/v2/query?input='
        url = base_url + url_args + '&appid=' + self.api_key
        try:
            # Get HTML response
            request = urllib2.Request(url, headers={ 'User-Agent' : 'Mozilla/5.0' })
            return lh.parse(urllib2.urlopen(request))
        except urllib2.URLError:
            sys.stderr.write('Failed to retrieve webpage.\n')
            return ''
    
    def BingSearch(self, html):
        # Parse Bing response and display link results
        unprocessed_links = html.xpath('//h2/a/@href')
        if not unprocessed_links:
            sys.stderr.write('Failed to retrieve webpage.\n')
            return False
        links = []
        link_descs = []
        for link in unprocessed_links:
            if not re.search('(ad|Ad|AD)(?=\W)', link): # Basic ad blocker
                if "http://" in link or "https://" in link: 
                    links.append(link)
                    ld_xpath = "//h2/a[@href='" + str(link) + "']//text()"
                    link_desc = html.xpath(ld_xpath)
                    if type(link_desc) == list:
                        link_desc = ''.join(link_desc)
                    link_descs.append(link_desc)
                elif '/images/' in link and "www.bing.com" not in link:
                    # Fix image links that are not prepended with www.bing.com
                    links.append('http://www.bing.com' + link)
                    ld_xpath = "//h2/a[@href='" + str(link) + "']//text()"
                    link_desc = html.xpath(ld_xpath)
                    if type(link_desc) == list:
                        link_desc = ''.join(link_desc)
                    link_descs.append(link_desc)

        if links and link_descs:
            for i in xrange(len(links)):
                print_desc = (str(i) + ". " + link_descs[i]).encode('ascii', 'ignore')
                print print_desc # Print link choices

            try:
                print ':',
                link_num = raw_input('')
                if link_num and int(link_num) >= 0 and int(link_num) < len(links):
                    self.OpenUrl(links[int(link_num)])
                    return True
            except (ValueError, IndexError):
                pass
        return False

    def WolframSearch(self, html):
        # Parse Wolfram|Alpha response for potential answers
        titles = list(OrderedDict.fromkeys(html.xpath("//pod[@title != '' and @title != 'Number line' and @title != 'Input' and @title != 'Visual representation' and @title != 'Image' and @title != 'Manipulatives illustration' and @title != 'Quotient and remainder']/@title")))
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
                        output_list.append(entry).encode('ascii', 'ignore')
                    else:
                        output_list.append(title + ': ' + entry).encode('ascii', 'ignore')
                except (AttributeError, UnicodeEncodeError):
                    pass
            if not output_list:
                return False
            elif len(output_list) > 2:
                print '\n'.join(output_list[:2]).encode('ascii', 'ignore')
                print 'See more? (y/n):',
                see_more = raw_input('')
                if see_more == 'y' or see_more == 'Y':
                    print '\n'.join(output_list[2:]).encode('ascii', 'ignore')
            else:
                print '\n'.join(output_list).encode('ascii', 'ignore')
            return True
        else:
            return False

    def BingCalculation(self, html):
        calc_result = html.xpath('//span[@id="rcTB"]/text()|//div[@class="b_focusTextMedium"]/text()|//p[@class="b_secondaryFocus df_p"]/text()|//div[@class="b_xlText b_secondaryText"]/text()|//input[@id="uc_rv"]/@value')
        define_result = html.xpath('//ol[@class="b_dList b_indent"]/li/div/text()')
        try:
            # Check if calculation result is present or age/date
            if calc_result:
                if len(calc_result) == 1:
                    print (calc_result[0]).encode('ascii', 'ignore')
                else:
                    print ('\n'.join(calc_result)).encode('ascii', 'ignore')
                return True
            # Check if calculation result is a definition
            elif define_result:
                if len(define_result) == 1:
                    print (define_result[0]).encode('ascii', 'ignore')
                else:
                    print ('\n'.join(define_result)).encode('ascii', 'ignore')
                return True
        except AttributeError:
            pass
        return False

    def OpenFirstLink(self, html):
        try:
            unprocessed_links = html.xpath('//h2/a/@href')
            for link in unprocessed_links:
                if not re.search('(ad|Ad|AD)(?=\W)', link): # Basic ad block
                    if "http://" in link or "https://" in link:
                        self.OpenUrl(link)
                        sys.exit()
                    elif '/images/' in link:
                        link = 'http://www.bing.com' + link
                        self.OpenUrl(link)
                        sys.exit()
        except IndexError:
            sys.stderr.write('Failed to retrieve webpage.\n')

    def OpenUrl(self, url_args):
        try:
            br = webbrowser.get(self.br_name)
        except webbrowser.Error:
            sys.stderr.write('Could not locate runnable browser, make sure the browser path in config is correct.\n')
            sys.exit()
        if type(url_args) == list:
            for arg in url_args:
                br.open(arg)
        else:
            br.open(url_args)

    def Search(self):
        continue_search = False
        if self.open_flag:
            self.OpenUrl(self.url_args)
        elif self.search_flag:
            self.BingSearch(self.html)
        elif self.first_flag:
            self.OpenFirstLink(self.html)        
        elif self.wolfram_flag:
            success = self.WolframSearch(self.html)
            if not success:
                continue_search = True
        else:
            continue_search = True

        if continue_search:
            # Defaults to BingCalculation, then WolframSearch, then BingSearch
            if self.wolfram_flag:
                bing_html = self.GetBingHTML(self.url_args) 
                wolf_html = self.html
            else:
                bing_html = self.html
            if not self.BingCalculation(bing_html):
                if not self.wolfram_flag:
                    wolf_html = self.GetWolframHTML(self.url_args)
                if not self.WolframSearch(wolf_html):
                    self.BingSearch(bing_html)


if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", help="Get Bing search results",
    action="store_true")
    parser.add_argument("-f", "--first", help="Open first link result",
    action="store_true")
    parser.add_argument("-o", "--open", help="Open url directly",
    action="store_true")
    parser.add_argument("-w", "--wolfram", help="Get Wolfram|Alpha search results",
    action="store_true")
    parser.add_argument("URL_ARGS", nargs='*', help="Search keywords")
    args = parser.parse_args()
    search = bool(args.search)
    first = bool(args.first)
    openurl = bool(args.open)
    wolfram = bool(args.wolfram)
    query = CLIQuery(args.URL_ARGS, search, first, openurl, wolfram)
    query.Search()

