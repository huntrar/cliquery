"""Read and initialize cliquery configuration"""

import os
import sys
import webbrowser


CONFIG_DIR = os.path.dirname(os.path.realpath(__file__))
if os.path.isfile('{0}/.local.cliqrc'.format(CONFIG_DIR)):
    CONFIG_FPATH = '{0}/.local.cliqrc'.format(CONFIG_DIR)
else:
    CONFIG_FPATH = '{0}/.cliqrc'.format(CONFIG_DIR)
CONFIG = {}


def read_config():
    """Read in .cliqrc or .local.cliqrc file"""
    with open(CONFIG_FPATH, 'r') as cfg:
        lines = []
        api_key = ''
        browser = ''

        # First two lines of .cliqrc should contain api_key: and browser:
        # If not, attempts to read the two in that order anyways
        for _ in range(2):
            line = cfg.readline()
            if line.startswith('api_key:'):
                api_key = line[8:].strip()
            if line.startswith('browser:'):
                browser = line[8:].strip()
            else:
                lines.append(line)
        if not api_key and not browser:
            try:
                api_key = lines[0].strip()
                browser = lines[1].strip()
            except IndexError:
                api_key = ''
                browser = ''

        # Read in bookmarks
        bkmarks = []
        cfg_bkmarks = cfg.read()
        if cfg_bkmarks.startswith('bookmarks:'):
            cfg_bkmarks = cfg_bkmarks[10:].split('\n')
            bkmarks = [b.strip() for b in cfg_bkmarks if b.strip()]

        return api_key, browser, bkmarks


def set_config():
    """Set WolframAlpha API key, browser, and bookmarks in CONFIG"""
    api_key, browser_name, bkmarks = read_config()
    CONFIG['api_key'] = api_key
    CONFIG['bookmarks'] = bkmarks

    # There may be multiple browser options given, pick the first which works
    if ',' in browser_name:
        browser_names = browser_name.split(',')
    else:
        browser_names = browser_name.split()

    if browser_names:
        for brow_name in browser_names:
            try:
                CONFIG['browser_name'] = brow_name
                CONFIG['browser'] = webbrowser.get(brow_name)
                return
            except webbrowser.Error:
                pass

    # If no valid browser found then use webbrowser to automatically detect one
    try:
        if sys.platform == 'win32':
            # Windows
            browser_name = 'windows-default'
            browser = webbrowser.get(browser_name)
        elif sys.platform == 'darwin':
            # Mac OSX
            browser_name = 'macosx'
            browser = webbrowser.get(browser_name)
        else:
            browser_name = 'Automatically detected'
            browser = webbrowser.get()
        CONFIG['browser_name'] = browser_name
        CONFIG['browser'] = browser
    except webbrowser.Error:
        pass
