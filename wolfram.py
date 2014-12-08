''' Python 2.7.3
AUTHOR: Hunter Hammond
VERSION: 1.6
DEPENDENCIES: pip install scrapy
'''

import sys
import urllib2
import itertools
from collections import OrderedDict

from scrapy.selector import Selector
from scrapy.http import XmlResponse

api_key = '' # Enter WolframAlpha API key here

argument_list = list(sys.argv) # Get cmd-line args
argument_list.pop(0) # Pop script name from list
if len(argument_list) > 0: # If given as one input string then split into list
    if "-s" in argument_list[0]:
        argument_list = argument_list[0].replace("-s", "")
    elif len(argument_list) > 1:
        if " " in argument_list[1]:
            argument_list = argument_list[1].split(" ")
try:
    url_args = '+'.join(argument_list)
except AttributeError:
    sys.stderr.write("Argument list error! Expected list, got " + type(argument_list) + "\n")
    
base_url = 'http://api.wolframalpha.com/v2/query?input='
url = base_url + url_args + '&appid=' + api_key

request = urllib2.Request(url, headers={ 'User-Agent': 'Mozilla/5.0' })
html = urllib2.urlopen(request).read() # Get HTML page
response = XmlResponse(url=url, body=html)

sel = Selector(response)

titles = list(OrderedDict.fromkeys(sel.xpath("//pod[@title != '' and @title != 'Number line' and @title != 'Input' and @title != 'Visual representation']/@title").extract()))
entries = []
if titles:
    for title in titles:
        entry_xpath = "//pod[@title='" + title + "']/subpod/plaintext/text()"
        entry = sel.xpath(entry_xpath).extract()
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
