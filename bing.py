''' Python 2.7.3
AUTHOR: Hunter Hammond
VERSION: 1.8
DEPENDENCIES: lxml
'''

import sys
import urllib2
import re

import lxml.html as lh

# Only one flag may be found
flags = { 'found' : False,
          's' : False,
          'f' : False,
          'o' : False,
          'w' : False,
}

# Clean arguments
arg_list = list(sys.argv)
arg_list.pop(0) # Pop script name from list
clean_args = []
if arg_list:
    for arg in arg_list:
        try:
            if arg[0] == "-" and not flags['found']:
                try:
                    arg_flag = arg[1]
                    flags[arg_flag] = True
                    flags['found'] = True
                except IndexError:
                    pass
            else:
                if " " in arg:
                    clean_args = arg.split(" ")
                else:
                    clean_args.append(arg)
        except IndexError:
            print 'BingFail'
            sys.stderr.write('No search terms entered.\n')
            sys.exit(1)
    if flags['o']:
        print ' '.join(clean_args) + 'BingOpen'
        sys.exit(0)
else:
    print 'BingFail'
    sys.stderr.write('No search terms entered.\n')
    sys.exit(1)

if flags['w']:
    print 'WolfFlag'
    sys.exit(0)

# Further cleaning of args before they are added to base_url
url_args = []
try:
    for url_arg in clean_args:
        if "+" in url_arg:
            url_arg = arg.replace('+', '%2B')
        url_args.append(url_arg)
    if len(url_args) > 1:
        url_args = '+'.join(url_args)
    else:
        url_args = url_args[0]
except IndexError:
    print 'BingFail'
    sys.stderr.write('No search terms entered.\n')
    sys.exit(1)
    
base_url = 'http://www.bing.com/search?q='
url = base_url + url_args

# Retrieve webpage response
try:
    request = urllib2.Request(url, headers={ 'User-Agent': 'Mozilla/5.0' })
    html = lh.parse(urllib2.urlopen(request))
except urllib2.URLError:
    print 'BingFail'
    sys.stderr.write('Failed to retrieve webpage.\n')
    sys.exit(0)

# Parse webpage response
if flags['f']:
    try:
        unprocessed_links = html.xpath('//h2/a/@href')
        for link in unprocessed_links:
            if not re.search('(ad|Ad|AD)(?=\W)', link): # Ad check
                if "http://" in link or "https://" in link:
                    print link + 'BingFL'
                    sys.exit(0) # Exit once first valid link printed
                elif '/images/' in link:
                    link = 'http://www.bing.com' + link
                    print link + 'BingFL'
                    sys.exit(0) # Exit once first valid link printed
    except IndexError:
        print 'BingFail'
        sys.stderr.write('Failed to retrieve webpage.\n')
        sys.exit(1)

elif flags['s']:
    unprocessed_links = html.xpath('//h2/a/@href')
    if not unprocessed_links:
        print 'BingFail'
        sys.stderr.write('Failed to retrieve webpage.\n')
        sys.exit(1)
    links = []
    link_descs = []
    for link in unprocessed_links:
        if not re.search('(ad|Ad|AD)(?=\W)', link): # Check for advertisement
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
            sys.stderr.write(print_desc) # Prints link choices

        try:
            sys.stderr.write(": ")
            link_num = raw_input("")
            if(link_num):
                print(links[int(link_num)]) + 'BingPage'
                sys.exit(0)
        except (ValueError, IndexError):
            print 'qBingPage'
            sys.exit(1)

# Check for Bing calculation/definition result
calc_result = html.xpath('//span[@id="rcTB"]/text()|//div[@class="b_focusTextMedium"]/text()|//p[@class="b_secondaryFocus df_p"]/text()|//div[@class="b_xlText b_secondaryText"]/text()|//input[@id="uc_rv"]/@value') # Check if calculation result is present or age/date
define_result = html.xpath('//ol[@class="b_dList b_indent"]/li/div/text()') # Check if calculation result is a definition
try:
    if calc_result:
        if len(calc_result) == 1:
            print (calc_result[0] + 'BingCalc').encode('ascii', 'ignore')
        else:
            print ('\n'.join(calc_result) + 'BingCalc').encode('ascii', 'ignore')
        sys.exit(0)
    elif define_result:
        if len(define_result) == 1:
            print (define_result[0] + 'BingCalc').encode('ascii', 'ignore')
        else:
            print ('\n'.join(define_result) + 'BingCalc').encode('ascii', 'ignore')
        sys.exit(0)
    else:
        print 'BingNoMatch'
        sys.exit(0)
except AttributeError:
    print 'BingNoMatch'

