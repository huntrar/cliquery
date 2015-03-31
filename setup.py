#!/usr/bin/env python

from setuptools import setup, find_packages
import cliquery
import os

def read(*names):
    values = dict()
    extensions = ['.txt', '.md']
    for name in names:
        value = ''
        for extension in extensions:
            filename = name + extension
            if os.path.isfile(filename):
                value = open(name + extension).read()
                break
        values[name] = value
    return values

long_description = """
%(README)s

News
====

%(CHANGES)s

""" % read('README', 'CHANGES')

setup(
    name='cliquery',
    version=cliquery.__version__,
    description='a command line search engine and browsing tool',
    long_description=long_description,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
    ],
    keywords='cliquery command line open bookmark console search answer',
    author='Hunter Hammond',
    author_email='huntrar@gmail.com',
    maintainer='Hunter Hammond',
    maintainer_email='huntrar@gmail.com',
    url='https://github.com/huntrar/CLIQuery',
    license='MIT',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'cliquery = cliquery.cliquery:command_line_runner',
        ]
    },
    install_requires=[
        'lxml'
    ]
)
