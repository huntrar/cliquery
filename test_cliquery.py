#!/usr/bin/env python

"""Unit tests for cliquery"""
import os
import unittest

from cliquery import cliquery, pyteaser


class CliqueryTestCase(unittest.TestCase):

    def call_search(self, query):
        parser = cliquery.get_parser()
        args = vars(parser.parse_args(query.split()))
        return cliquery.search(args)

    def setUp(self):
        self.queries = ['testing one two three',
                        'sentence with $p3c!@l-chars',
                        'nospaces']
        self.inst_queries = ['how old is barack obama']

    def tearDown(self):
        pass

    def test_answer_links(self):
        """-fp returns the url of top link"""
        for query in self.queries:
            links = self.call_search(query + ' -fp')
            if isinstance(links, list):
                for link in links:
                    self.assertTrue(link.startswith('http://') or
                                    link.startswith('https://'))
            elif links is None:
                # None indicates an internet connection error
                pass
            elif not isinstance(links, bool):
                self.assertTrue(links.startswith('http://') or
                                links.startswith('https://'))

    def test_instant_resp(self):
        """instant response questions from Bing"""
        for query in self.inst_queries:
            self.assertTrue(self.call_search(query))


if __name__ == '__main__':
    unittest.main()
