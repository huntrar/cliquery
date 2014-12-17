''' Python 2.7.3
AUTHOR: Hunter Hammond
VERSION: 1.7
DEPENDENCIES: lxml
'''

import sys
import urllib2

import lxml.html as lh

search_flag = False
feelinglucky_flag = False
open_flag = False

argument_list = list(sys.argv) # Get cmd-line args
argument_list.pop(0) # Pop script name from list
if argument_list:
    if argument_list[0] == "-s":
        argument_list[0] = argument_list[0].replace("-s", "")
        search_flag = True 
    if argument_list[0] == "-f":
        argument_list[0] = argument_list[0].replace("-f", "")
        feelinglucky_flag = True
    if argument_list[0] == "-o":
        argument_list[0] = argument_list[0].replace("-o", "")
        open_flag = True 
    if len(argument_list) > 1:
        if open_flag:
            print argument_list[1] + 'BingOpenUrl'
            sys.exit(0)
        if " " in argument_list[1]:
            argument_list = argument_list[1].split(" ")

if not argument_list: # argument_list state might change in "if argument_list"
    sys.exit(0)

url_args = []
for arg in argument_list:
    url_arg = arg.replace('+', '%2B') # Bing interprets addition + as %2B
    url_args.append(url_arg)
if len(url_args) > 1:
    argument_list = '+'.join(url_args)
else:
    argument_list = url_args[0]
    
base_url = 'http://www.bing.com/search?q='
url = base_url + argument_list

request = urllib2.Request(url, headers={ 'User-Agent': 'Mozilla/5.0' })
html = lh.parse(urllib2.urlopen(request)) # Get HTML page

if feelinglucky_flag:
    first_link = html.xpath('//h2/a/@href')[0]
    sys.stderr.write('first_link: ' + first_link)
    if "http://" in first_link or "https://" in first_link:
        print first_link + 'BingFirstVal'
    elif '/images/' in first_link:
        first_link = 'http://www.bing.com' + first_link
        print first_link + 'BingFirstVal'
    sys.exit(0)

elif search_flag:
    unprocessed_links = html.xpath('//h2/a/@href')
    links = []
    link_descs = []
    for link in unprocessed_links:
        if "http://" in link or "https://" in link: 
            links.append(link)
            ld_xpath = "//h2/a[@href='" + str(link) + "']//text()"
            link_desc = html.xpath(ld_xpath)
            if type(link_desc) == list:
                link_desc = ''.join(link_desc)
            link_descs.append(link_desc)
        elif '/images/' in link:
            links.append('http://www.bing.com' + link)
            ld_xpath = "//h2/a[@href='" + str(link) + "']//text()"
            link_desc = html.xpath(ld_xpath)
            if type(link_desc) == list:
                link_desc = ''.join(link_desc)
            link_descs.append(link_desc)

    if links and link_descs:
        for i in xrange(len(links)):
            print_desc = (str(i) + ". " + link_descs[i] + "\n").encode('ascii', 'ignore')
            sys.stderr.write(print_desc) # DO NOT REMOVE!! Prints link choices

        try:
            sys.stderr.write(": ") # DO NOT REMOVE!! Colon for input entry
            link_num = raw_input("")
            if(link_num):
                if link_num == 'q':
                    print 'qBingReturnVal'
                    sys.exit(0)
                print(links[int(link_num)]) + 'BingReturnVal'
                sys.exit(0)
        except (ValueError, IndexError):
            print 'qBingReturnVal'
            sys.exit(0)

calc_result = html.xpath('//span[@id="rcTB"]/text()|//div[@class="b_focusTextMedium"]/text()|//p[@class="b_secondaryFocus df_p"]/text()|//div[@class="b_xlText b_secondaryText"]/text()|//input[@id="uc_rv"]/@value') # Check if calculation result is present or age/date
define_result = html.xpath('//ol[@class="b_dList b_indent"]/li/div/text()') # Check if calculation result is a definition
try:
    if calc_result:
        if len(calc_result) == 1:
            print (calc_result[0] + 'CalcReturnVal').encode('ascii', 'ignore')
        else:
            print ('\n'.join(calc_result) + 'CalcReturnVal').encode('ascii', 'ignore')
        sys.exit(0)
    elif define_result:
        if len(define_result) == 1:
            print (define_result[0] + 'CalcReturnVal').encode('ascii', 'ignore')
        else:
            print ('\n'.join(define_result) + 'CalcReturnVal').encode('ascii', 'ignore')
        sys.exit(0)
    else:
        print 'BingNoMatch'
        sys.exit(0)
except AttributeError:
    print 'BingNoMatch'

