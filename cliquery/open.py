"""Contains cliquery functions to describe and open webpages"""

from __future__ import absolute_import, print_function
import sys

from six import PY2
from six.moves import input

from .config import CONFIG
from .pyteaser import summarize
from . import utils, CONTINUE


def get_google_query_url(query):
    """Get Google query URL."""
    base_url = 'www.google.com'
    if not query:
        return 'http://{0}'.format(base_url)
    return 'http://{0}/search?q={1}'.format(base_url, query)


def get_wolfram_query_url(query):
    """Get Wolfram query URL."""
    base_url = 'www.wolframalpha.com'
    if not query:
        return 'http://{0}'.format(base_url)
    return 'http://{0}/input/?i={1}'.format(base_url, query)


def describe_url(url):
    """Print a text preview of a given URL."""
    try:
        # Get title and text for summarization
        resp = utils.get_resp(url)
        title = utils.get_title(resp)
        text = utils.get_text(resp)
        if title and text:
            desc = utils.remove_whitespace(summarize(title, ' '.join(text)))
        else:
            desc = []
        if not desc:
            sys.stderr.write('Failed to describe {0}.\n'.format(url))
            return False

        clean_desc = [x.replace('\n', '').replace('\t', '') for x in desc]
        print('\n'.join(x if isinstance(x, str) else x.encode('utf-8') if PY2 else x
                        for x in clean_desc))
        utils.check_input(input(CONTINUE))
        return True
    except AttributeError:
        sys.stderr.write('Failed to describe {0}.\n'.format(url))
        return False


def open_browser(url):
    """Open a browser using webbrowser."""
    if 'browser_obj' in CONFIG and CONFIG['browser_obj']:
        CONFIG['browser_obj'].open(utils.add_scheme(url))
    else:
        sys.stderr.write('Failed to open browser.\n')


def open_url(args, urls, prompt_args=None):
    """Print, describe, or open URLs in the browser.

    Keyword arguments:
    args -- program arguments (dict)
    urls -- search URLs chosen (list)
    prompt_args -- temporary arguments from link prompt (list)
    """
    if urls:
        # Either opening URLs or searching for link prompt arguments, not both
        prompt_args = None
        if not isinstance(urls, list):
            urls = [urls]
    elif prompt_args and isinstance(prompt_args, list):
        prompt_args = ' '.join(prompt_args)
    if args['open']:
        if args['search']:
            open_browser(get_google_query_url(prompt_args or args['query']))
            return True
        elif args['wolfram']:
            open_browser(get_wolfram_query_url(prompt_args or args['query']))
            return True

    if args['print']:
        for url in urls:
            print(url)
        return urls
    elif args['describe']:
        for url in urls:
            describe_url(url)
            print('\n')
        return urls
    else:
        if not urls:
            open_browser('')
        else:
            for url in urls:
                open_browser(url)
        return True
