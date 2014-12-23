''' Python 2.7.3
AUTHOR: Hunter Hammond
VERSION: 1.8
DEPENDENCIES: lxml
'''

import os
import sys
import urllib2
import itertools
from collections import OrderedDict

import lxml.html as lh

# Get API key from config.txt
cfg_path = os.path.dirname(os.path.abspath(__file__))
f = open(cfg_path + '/config.txt', 'r')
api_key = f.readline()
f.close()

# Clean arguments
arg_list = list(sys.argv)
arg_list.pop(0) # Pop script name from list
clean_args = []
if arg_list:
    for arg in arg_list:
        try:
            if arg[0] != "-":
                if " " in arg:
                    clean_args = arg.split(" ")
                else:
                    clean_args.append(arg)
        except IndexError:
            sys.exit(1)

# Add clean_args and api_key to base_url
base_url = 'http://api.wolframalpha.com/v2/query?input='
try:
    url_args = '+'.join(clean_args)
except AttributeError:
    sys.stderr.write("Argument list error! Expected list, got " + type(clean_args) + "\n")
    sys.exit(1)
url = base_url + url_args + '&appid=' + api_key

# Retrieve webpage response
try:
    request = urllib2.Request(url, headers={ 'User-Agent': 'Mozilla/5.0' })
    html = lh.parse(urllib2.urlopen(request))
except urllib2.URLError:
    print 'WolfFail'
    sys.stderr.write('Failed to retrieve webpage.\n')
    sys.exit(1)

# Parse webpage response
titles = list(OrderedDict.fromkeys(html.xpath("//pod[@title != '' and @title != 'Number line' and @title != 'Input' and @title != 'Visual representation']/@title")))
entries = []
if titles:
    for title in titles:
        entry_xpath = "//pod[@title='" + title + "']/subpod/plaintext/text()"
        entry = html.xpath(entry_xpath)
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

