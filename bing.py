''' Python 2.7.3
AUTHOR: Hunter Hammond
VERSION: 2.0
DEPENDENCIES: lxml
'''

import argparse
import sys
import urllib2
import re

import lxml.html as lh


class BingSearch:
    def __init__(self, url_args, search_flag, first_flag, open_flag, wolfram_flag, incog_flag):
       self.search_flag = search_flag
       self.first_flag = first_flag
       self.open_flag = open_flag
       self.wolfram_flag = wolfram_flag
       self.incog_flag = incog_flag
       self.url_args = self.ProcessArgs(url_args)
       self.html = self.GetBingHTML(self.url_args)

    def ProcessArgs(self, url_args):
        clean_args = []
        if url_args:
            for arg in url_args:
                try:
                    if " " in arg:
                        clean_args = arg.split(" ")
                    else:
                        clean_args.append(arg)
                except IndexError:
                    print 'BingFail'
                    sys.stderr.write('No search terms entered.\n')
                    sys.exit()
        else:
            print 'BingFail'
            sys.stderr.write('No search terms entered.\n')
            sys.exit()

        # Further cleaning of args before they are added to base_url
        new_url_args = []
        if not self.open_flag:
            try:
                for url_arg in clean_args:
                    if "+" in url_arg:
                        url_arg = arg.replace('+', '%2B')
                    new_url_args.append(url_arg)
                if len(new_url_args) > 1:
                    new_url_args = '+'.join(url_args)
                else:
                    new_url_args = url_args[0]
            except IndexError:
                print 'BingFail'
                sys.stderr.write('No search terms entered.\n')
                sys.exit()
        else:
            for url_arg in clean_args:
                if ".com" not in url_arg:
                    new_url_args.append(url_arg + ".com")
                else:
                    new_url_args.append(url_arg)
        return new_url_args
       
    def GetBingHTML(self, url_args): 
        if not self.open_flag:
            base_url = 'http://www.bing.com/search?q='
            url = base_url + url_args
            try:
                # Get HTML response
                request = urllib2.Request(url, headers={ 'User-Agent': 'Mozilla/5.0' })
                return lh.parse(urllib2.urlopen(request))
            except urllib2.URLError:
                print 'BingFail'
                sys.stderr.write('Failed to retrieve webpage.\n')
                sys.exit()
    
    def BingSearchResults(self, html):
        # Prints Bing search page links
        unprocessed_links = html.xpath('//h2/a/@href')
        if not unprocessed_links:
            print 'BingFail'
            sys.stderr.write('Failed to retrieve webpage.\n')
            sys.exit()
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
                print_desc = (str(i) + ". " + link_descs[i] + "\n").encode('ascii', 'ignore')
                sys.stderr.write(print_desc) # Prints link choices

            try:
                sys.stderr.write(": ")
                link_num = raw_input("")
                if(link_num):
                    if self.incog_flag:
                        print(links[int(link_num)]) + 'BingIncogPage'
                    else:
                        print(links[int(link_num)]) + 'BingPage'
                    sys.exit()
            except (ValueError, IndexError):
                print 'qBingPage'
                sys.exit()

    def BingCalculation(self, html):
        calc_result = html.xpath('//span[@id="rcTB"]/text()|//div[@class="b_focusTextMedium"]/text()|//p[@class="b_secondaryFocus df_p"]/text()|//div[@class="b_xlText b_secondaryText"]/text()|//input[@id="uc_rv"]/@value')
        define_result = html.xpath('//ol[@class="b_dList b_indent"]/li/div/text()')
        try:
            # Check if calculation result is present or age/date
            if calc_result:
                if len(calc_result) == 1:
                    print (calc_result[0] + 'BingCalc').encode('ascii', 'ignore')
                else:
                    print ('\n'.join(calc_result) + 'BingCalc').encode('ascii', 'ignore')
                sys.exit()
            # Check if calculation result is a definition
            elif define_result:
                if len(define_result) == 1:
                    print (define_result[0] + 'BingCalc').encode('ascii', 'ignore')
                else:
                    print ('\n'.join(define_result) + 'BingCalc').encode('ascii', 'ignore')
                sys.exit()
        except AttributeError:
            pass
        return False

    def OpenFirstLink(self, html):
        try:
            unprocessed_links = html.xpath('//h2/a/@href')
            for link in unprocessed_links:
                if not re.search('(ad|Ad|AD)(?=\W)', link): # Basic ad block
                    if "http://" in link or "https://" in link:
                        if self.incog_flag:
                            print link + 'BingIncogFL'
                        else:
                            print link + 'BingFL'
                        sys.exit() # Exit once first valid link printed
                    elif '/images/' in link:
                        link = 'http://www.bing.com' + link
                        if self.incog_flag:
                            print link + 'BingIncogFL'
                        else:
                            print link + 'BingFL'
                        sys.exit() # Exit once first valid link printed
        except IndexError:
            sys.stderr.write('Failed to retrieve webpage.\n')
            sys.exit()

    def OpenUrl(self):
        if self.incog_flag:
            print ' '.join(self.url_args) + 'BingIncogOpen'
        else:
            print ' '.join(self.url_args) + 'BingOpen'
        sys.exit()

    def CheckWolfram(self):
        print 'WolfFlag'
        sys.exit()

    def Search(self):
        if self.open_flag:
            self.OpenUrl()
        elif self.search_flag:
            self.BingSearchResults(self.html)
        elif self.first_flag:
            self.OpenFirstLink(self.html)        
        elif self.wolfram_flag:
            self.CheckWolfram()
        else:
            # Defaults to BingCalculation, then Wolfram, which if fails will
            # restart this program with search_flag set to True
            search_success = self.BingCalculation(self.html)
            if not search_success:
                self.CheckWolfram()


if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", help="get bing search results",
    action="store_true")
    parser.add_argument("-f", "--first", help="opens first link result",
    action="store_true")
    parser.add_argument("-o", "--openurl", help="open link directly",
    action="store_true")
    parser.add_argument("-w", "--wolfram", help="get wolfram search result",
    action="store_true")
    parser.add_argument("-i", "--incognito", help="open browser in incognito",
    action="store_true")
    parser.add_argument("URL_ARGS", nargs='*', help="Search keywords")
    args = parser.parse_args()
    search = bool(args.search)
    first = bool(args.first)
    openurl = bool(args.openurl)
    wolfram = bool(args.wolfram)
    incognito = bool(args.incognito)
    bing_search = BingSearch(args.URL_ARGS, search, first, openurl, wolfram, incognito)
    bing_search.Search()


