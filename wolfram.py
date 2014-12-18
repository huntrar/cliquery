''' Python 2.7.3
AUTHOR: Hunter Hammond
VERSION: 1.8
DEPENDENCIES: lxml
'''

import sys
import urllib2
import itertools
from collections import OrderedDict

import lxml.html as lh

f = open('config.txt', 'r')
api_key = f.readline() # Get WolframAlpha API key

argument_list = list(sys.argv) # Get cmd-line args
argument_list.pop(0) # Pop script name from list
if len(argument_list) > 0: # If given as one input string then split into list
    if "-" in argument_list[0]:
        argument_list.pop(0)
    elif len(argument_list) > 1:
        if " " in argument_list[1]:
            argument_list = argument_list[1].split(" ")

try:
    url_args = '+'.join(argument_list)
except AttributeError:
    sys.stderr.write("Argument list error! Expected list, got " + type(argument_list) + "\n")
    
base_url = 'http://api.wolframalpha.com/v2/query?input='
url = base_url + url_args + '&appid=' + api_key

try:
    request = urllib2.Request(url, headers={ 'User-Agent': 'Mozilla/5.0' })
    html = lh.parse(urllib2.urlopen(request)) # Get HTML page
except urllib2.URLError:
    print 'WolfFail'
    sys.stderr.write('Failed to retrieve webpage.\n')
    sys.exit(0)

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
