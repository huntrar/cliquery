import random
import requests
import sys

import lxml.html as lh


try:
    from urllib import quote_plus as url_quote
except ImportError:
    from urllib.parse import quote_plus as url_quote

try:
    from urllib import getproxies
except ImportError:
    from urllib.request import getproxies


USER_AGENTS = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
                'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100 101 Firefox/22.0',
                'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5',
                'Mozilla/5.0 (Windows; Windows NT 6.1) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5')


def get_proxies():
    proxies = getproxies()
    filtered_proxies = {}
    for k, v in proxies.items():
        if k.startswith('http://'):
            if not v.startswith('http://'):
                filtered_proxies[k] = 'http://{0}'.format(v)
            else:
                filtered_proxies[k] = v
    return filtered_proxies


def get_html(url):
    try:
        ''' Get HTML response as an lxml.html.HtmlElement object '''
        headers={'User-Agent' : random.choice(USER_AGENTS)}
        request = requests.get(url, headers=headers, proxies=get_proxies())
        return lh.fromstring(request.text.encode('utf-8'))
    except Exception as e:
        sys.stderr.write('Failed to retrieve {0}.\n'.format(url))
        sys.stderr.write('{0}\n'.format(str(e)))
        return None


def clean_query(url_args, open_flag, bookmark_flag):
    if bookmark_flag:
        return url_args
    elif not open_flag:
        ''' Replace special characters with hex encoded escapes '''
        return url_quote(url_args)
    else:
        ''' Arguments should be URLs '''
        urls = []
        for url_arg in url_args.split():
            if '.' not in url_arg and 'localhost:' not in url_arg:
                urls.append('{0}.com'.format(url_arg))
            else:
                urls.append(url_arg)
        return urls


def check_input(u_input, num = False, empty=False):
    if isinstance(u_input, list):
        u_input = ''.join(u_input)

    try:
        u_inp = u_input.lower().strip()
    except AttributeError:
        pass

    ''' Check for exit signal '''
    if u_inp == 'q' or u_inp == 'quit' or u_inp == 'exit':
        sys.exit()

    if num:
        return check_num(u_input)
    elif empty:
        if not u_input and not num:
            return True
        else:
            return False
    return True


def check_num(num):
    try:
        n = int(num)
        return True
    except ValueError:
        return False


def clean_url(urls):
    ''' Append scheme to urls if not present '''
    clean_urls = []
    if isinstance(urls, list):
        for url in urls:
            if not url.startswith('http://') and not url.startswith('https://'):
                clean_urls.append('http://{0}'.format(url))
            else:
                clean_urls.append(url)
        return clean_urls
    else:
        if urls.startswith('http://') or urls.startswith('https://'):
            return urls
        else:
            return 'http://{0}'.format(urls)


def reset_flags(args):
    ''' Set all boolean flags to False '''
    return {k: False if isinstance(v, bool) else v for k, v in args.items()}


def get_flags(args):
    ''' Returns dictionary containing flags with their first letter as the key '''
    return {k[0]: k for k, v in args.items() if isinstance(v, bool)}


