import random
import requests
import sys

import lxml.html as lh


USER_AGENTS = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
                'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100 101 Firefox/22.0',
                'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5',
                'Mozilla/5.0 (Windows; Windows NT 6.1) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5')


def get_html(url):
    try:
        # Get HTML response
        headers={'User-Agent' : random.choice(USER_AGENTS)}
        request = requests.get(url, headers=headers)
        return lh.fromstring(request.text.encode('utf-8'))
    except Exception as e:
        sys.stderr.write('Failed to retrieve {}.\n'.format(url))
        sys.stderr.write(str(e))
        return None


def process_args(args):
    # Process and returns only query arguments
    url_args = args['query']
    clean_args = []
    if url_args:
        for arg in url_args:
            if ' ' in arg:
                for split_arg in arg.split(' '):
                    clean_args.append(split_arg)
            else:
                clean_args.append(arg)

    # Further processing of url args before they are added to base_url
    new_url_args = []
    if not args['open']:
        symbol_dict = { '@' : '%40',
                        '$' : '%24',
                        '%' : '%25',
                        '&' : '%26',
                        '+' : '%2B',
                        '=' : '%3D' }
        try:
            for url_arg in clean_args:
                for sym in symbol_dict:
                    if sym in url_arg:
                        url_arg = url_arg.replace(sym, symbol_dict[sym])
                new_url_args.append(url_arg)
            new_url_args = '+'.join(new_url_args)
        except IndexError:
            sys.stderr.write('No search terms entered.\n')
            sys.exit()
    else:
        for url_arg in clean_args:
            if '.' not in url_arg and 'localhost' not in url_arg:
                new_url_args.append(url_arg + '.com')
            else:
                new_url_args.append(url_arg)
    return new_url_args


def check_input(u_input, num = False, empty=False):
    if isinstance(u_input, list):
        u_input = ''.join(u_input)

    try:
        u_inp = u_input.lower().strip()
    except AttributeError:
        pass

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
    # Returns True if list, False otherwise
    clean_urls = []
    if isinstance(urls, list):
        for url in urls:
            if 'http://' not in url and 'https://' not in url:
                clean_urls.append('http://' + url)
            else:
                clean_urls.append(url)
        return clean_urls, True
    else:
        if 'http://' in urls or 'https://' in urls:
            return urls, False
        else:
            return ('http://' + urls), False


def reset_flags(args):
    return {k: False if isinstance(v, bool) else v for k, v in args.items()}


def get_flags(args):
    return {k[0]: k for k, v in args.items() if isinstance(v, bool)}


