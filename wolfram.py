''' Python 2.7.3
AUTHOR: Hunter Hammond
VERSION: 1.9
DEPENDENCIES: lxml
'''

import argparse
import os
import sys
import urllib2
import itertools
from collections import OrderedDict

import lxml.html as lh


class WolfSearch:
    def __init__(self, url_args):
        self.url_args = self.ProcessArgs(url_args)
        self.api_key = self.GetApiKey()
        self.html = self.GetWolfHTML(self.url_args)
    
    def GetApiKey(self):
        # Get API key from config.txt
        cfg_path = os.path.dirname(os.path.abspath(__file__))
        f = open(cfg_path + '/config.txt', 'r')
        api_key = f.readline()
        f.close()
        return api_key

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
                    sys.exit()
        return clean_args

    def GetWolfHTML(self, url_args):
        # Add clean_args and api_key to base_url
        base_url = 'http://api.wolframalpha.com/v2/query?input='
        try:
            clean_args = '+'.join(url_args)
        except AttributeError:
            sys.stderr.write("Argument list error! Expected list, got " + type(clean_args) + "\n")
            sys.exit()
        url = base_url + clean_args + '&appid=' + self.api_key

        # Retrieve webpage response
        try:
            request = urllib2.Request(url, headers={ 'User-Agent': 'Mozilla/5.0' })
            return lh.parse(urllib2.urlopen(request))
        except urllib2.URLError:
            print 'WolfFail'
            sys.stderr.write('Failed to retrieve webpage.\n')
            sys.exit()
    
    def Search(self):
        # Parse webpage response
        titles = list(OrderedDict.fromkeys(self.html.xpath("//pod[@title != '' and @title != 'Number line' and @title != 'Input' and @title != 'Visual representation']/@title")))
        entries = []
        if titles:
            for title in titles:
                entry_xpath = "//pod[@title='" + title + "']/subpod/plaintext/text()"
                entry = self.html.xpath(entry_xpath)
                if entry:
                    entries.append(entry[0])

            entries = list(OrderedDict.fromkeys(entries))
            output_list = []
            for title, entry in itertools.izip(titles, entries):
                try:
                    output_list.append(title + ': ' + entry).encode('ascii', 'ignore')
                except (AttributeError, UnicodeEncodeError):
                    pass
            print '\n'.join(output_list).encode('ascii', 'ignore')
        else:
            print 'WolfNoMatch'


if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", help="get bing search results",
    action="store_true")
    parser.add_argument("-f", "--flucky", help="feeling lucky result",
    action="store_true")
    parser.add_argument("-o", "--openurl", help="open link directly",
    action="store_true")
    parser.add_argument("-w", "--wolfram", help="get wolfram search result",
    action="store_true")
    parser.add_argument("URL_ARGS", nargs='*', help="Search URL arguments")
    args = parser.parse_args()
    wolf_search = WolfSearch(args.URL_ARGS)
    wolf_search.Search()


