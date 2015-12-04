# -*- coding: utf-8 -*-

import random
import sys

import lxml.html as lh
import requests


try:
    from urllib import quote_plus as url_quote
except ImportError:
    from urllib.parse import quote_plus as url_quote

try:
    from urllib import getproxies
except ImportError:
    from urllib.request import getproxies

try:
    dict.iteritems
except AttributeError:
    def itervalues(dct):
        """Python 3 dictionary itervalues()"""
        return iter(dct.values())

    def iteritems(dct):
        """Python 3 dictionary iteritems()"""
        return iter(dct.items())
else:
    def itervalues(dct):
        """Python 2 dictionary itervalues()"""
        return dct.itervalues()

    def iteritems(dct):
        """Python 2 dictionary iteritems()"""
        return dct.iteritems()


USER_AGENTS = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) '
               'Gecko/20100101 Firefox/11.0',
               'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) '
               'Gecko/20100 101 Firefox/22.0',
               'Mozilla/5.0 (Windows NT 6.1; rv:11.0) '
               'Gecko/20100101 Firefox/11.0',
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) '
               'AppleWebKit/536.5 (KHTML, like Gecko) '
               'Chrome/19.0.1084.46 Safari/536.5',
               'Mozilla/5.0 (Windows; Windows NT 6.1) '
               'AppleWebKit/536.5 (KHTML, like Gecko) '
               'Chrome/19.0.1084.46 Safari/536.5')


def get_proxies():
    """Get available proxies to use with requests library"""
    proxies = getproxies()
    filtered_proxies = {}
    for key, value in iteritems(proxies):
        if key.startswith('http://'):
            if not value.startswith('http://'):
                filtered_proxies[key] = 'http://{0}'.format(value)
            else:
                filtered_proxies[key] = value
    return filtered_proxies


def get_html(url):
    """Get HTML response as an lxml.html.HtmlElement object"""
    try:
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        request = requests.get(url, headers=headers, proxies=get_proxies())
        return lh.fromstring(request.text.encode('utf-8'))
    except Exception:
        sys.stderr.write('Failed to retrieve {0}.\n'.format(url))
        raise


def split_title(title, delim):
    """Return largest title piece"""
    largest_len = 0
    largest_piece = None
    piece_len = 0

    for piece in title.split(delim):
        piece_len = len(piece)
        if piece_len > largest_len:
            largest_len = piece_len
            largest_piece = piece
    return largest_piece or title


def get_title(html):
    """Extract title from HTML"""
    title = html.xpath('//title/text()')
    if not title:
        return ''
    else:
        title = title[0]

    """Split title by common delimeters"""
    common_delim = ['|', '-', '–', '»', ':']
    for delim in common_delim:
        if delim in title:
            title = split_title(title, delim)
            break
    return title


def get_text(html):
    return html.xpath('//*[not(self::script) and not(self::style)]/text()')


def clean_query(query, open_flag, bookmark_flag):
    """Replace special characters/append URL extensions if necessary"""
    if bookmark_flag:
        return query
    elif not open_flag:
        # Replace special characters with hex encoded escapes
        return url_quote(query)
    else:
        # Arguments should be URLs
        urls = []
        for arg in query.split():
            if '.' not in arg and 'localhost:' not in arg:
                urls.append('{0}.com'.format(arg))
            else:
                urls.append(arg)
        return urls


def check_input(user_input, num=False, empty=False):
    """Check user input for empty, a number, or for an exit signal"""
    if isinstance(user_input, list):
        user_input = ''.join(user_input)

    try:
        u_inp = user_input.lower().strip()
    except AttributeError:
        u_inp = user_input

    # Check for exit signal
    if u_inp == 'q' or u_inp == 'quit' or u_inp == 'exit':
        sys.exit()

    if num:
        return is_num(user_input)
    elif empty:
        return not user_input
    return True


def is_num(num):
    """Return whether num can be an int"""
    try:
        num = int(num)
        return True
    except ValueError:
        return False


def append_scheme(urls):
    """Append scheme to URL's if not present"""
    if isinstance(urls, list):
        scheme_urls = []

        for url in urls:
            if not url.startswith('http://')\
                    and not url.startswith('https://'):
                scheme_urls.append('http://{0}'.format(url))
            else:
                scheme_urls.append(url)
        return scheme_urls
    else:
        if urls.startswith('http://') or urls.startswith('https://'):
            return urls
        else:
            return 'http://{0}'.format(urls)


def reset_flags(args):
    """Return a dictionary with all bool flags set to False"""
    return {k: False if isinstance(v, bool) else v for k, v in iteritems(args)}


def get_lookup_flags(args):
    """Return a dictionary with keys equal to first letter of their values"""
    return {k[0]: k for k, v in iteritems(args) if isinstance(v, bool)}
