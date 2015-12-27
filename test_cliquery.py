#!/usr/bin/env python

"""Unit tests for cliquery"""
import os
import unittest

from cliquery import cliquery, pyteaser, compat


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


class TestSummarize(unittest.TestCase):
    def testText(self):
        article_title = compat.uni('Framework for Partitioning and Execution of Data Stream Applications in Mobile Cloud Computing')
        article_text = compat.uni('The contribution of cloud computing and mobile computing technologies lead to the newly emerging mobile cloud com- puting paradigm. Three major approaches have been pro- posed for mobile cloud applications: 1) extending the access to cloud services to mobile devices; 2) enabling mobile de- vices to work collaboratively as cloud resource providers; 3) augmenting the execution of mobile applications on portable devices using cloud resources. In this paper, we focus on the third approach in supporting mobile data stream applica- tions. More specifically, we study how to optimize the com- putation partitioning of a data stream application between mobile and cloud to achieve maximum speed/throughput in processing the streaming data. To the best of our knowledge, it is the first work to study the partitioning problem for mobile data stream applica- tions, where the optimization is placed on achieving high throughput of processing the streaming data rather than minimizing the makespan of executions as in other appli- cations. We first propose a framework to provide runtime support for the dynamic computation partitioning and exe- cution of the application. Different from existing works, the framework not only allows the dynamic partitioning for a single user but also supports the sharing of computation in- stances among multiple users in the cloud to achieve efficient utilization of the underlying cloud resources. Meanwhile, the framework has better scalability because it is designed on the elastic cloud fabrics. Based on the framework, we design a genetic algorithm for optimal computation parti- tion. Both numerical evaluation and real world experiment have been performed, and the results show that the par- titioned application can achieve at least two times better performance in terms of throughput than the application without partitioning.')

        summarised_article_text = ['The contribution of cloud computing and mobile computing technologies lead to the newly emerging mobile cloud com- puting paradigm.', 'Three major approaches have been pro- posed for mobile cloud applications: 1) extending the access to cloud services to mobile devices; 2) enabling mobile de- vices to work collaboratively as cloud resource providers; 3) augmenting the execution of mobile applications on portable devices using cloud resources.', 'In this paper, we focus on the third approach in supporting mobile data stream applica- tions.', 'More specifically, we study how to optimize the com- putation partitioning of a data stream application between mobile and cloud to achieve maximum speed/throughput in processing the streaming data.', 'We first propose a framework to provide runtime support for the dynamic computation partitioning and exe- cution of the application.']

        self.assertEqual(pyteaser.summarize(article_title, article_text),
                         [compat.uni(x) for x in summarised_article_text])


if __name__ == '__main__':
    unittest.main()
