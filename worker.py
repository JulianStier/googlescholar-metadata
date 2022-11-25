#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3' #Based on B&N plugin by Grant Drake
__copyright__ = '2013, Benjamin Behringer <mail at benjamin-behringer.de>'
__docformat__ = 'en'

import re
import datetime
import logging
import time
import random
from threading import Thread
from calibre.ebooks.metadata.book.base import Metadata
import calibre_plugins.googlescholar_metadata.gscholar as gs
from .bib import Bibparser

AVAILABLE_HEADERS = [
    {"User-Agent": "Mozilla/5.0"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0"},
    {"User-Agent": "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)"},
    {"User-Agent": "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2)"},
    {"User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)"},
    {"User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322)"},
    {"User-Agent": "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729)"},
    {"User-Agent": "Mozilla/4.0 (compatible; MSIE 5.23; Mac_PowerPC)"},
    {"User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.1; .NET CLR 3.0.04506.30)"},
    {"User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727; .NET CLR 3.0.30729; .NET CLR 3.5.30729; Tablet PC 2.0; Zoom 3.6.0)"},
    {"User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.3; WOW64; Trident/7.0; .NET4.0E; .NET4.0C; .NET CLR 3.5.30729; .NET CLR 2.0.50727; .NET CLR 3.0.30729; Zoom 3.6.0)"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; ASU2JS; rv:11.0) like Gecko"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0"},
    {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0"},
    {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:102.0) Gecko/20100101 Firefox/102.0"},
]

class Worker(Thread): # Get details
    '''
    Download paper information from google scholar in separate thread.
    '''

    def __init__(self, result_queue, log, query_title, query_authors, plugin, num=1):
        Thread.__init__(self)
        self.daemon = True
        self.result_queue = result_queue
        self.log = log
        self.count = num
        self.plugin = plugin
        self.query_title, self.query_authors = query_title, query_authors
        
        logger = logging.getLogger('gscholar')
        logging.basicConfig(
            format='%(asctime)s %(levelname)s %(name)s %(message)s',
            level=logging.WARNING
        )

    def run(self):
        try:
            self._get_results()
        except:
            self.log.exception('_get_results failed')

    def _get_results(self):
        """ Download Information from Google Scholar """
        """# author=self.query_authors[0], count=self.count
        querier = ScholarQuerier()
        
        settings = ScholarSettings()
        settings.set_citation_format(ScholarSettings.CITFORM_BIBTEX)
        querier.apply_settings(settings)
        
        query = SearchScholarQuery()
        query.set_author(self.query_authors[0])
        query.set_num_page_results(self.count)
        #querier.query(self.query_title, bibtex=True)
        query.set_words_some(self.query_title)

        querier.send_query(query)"""
        
        
        #search_query = scholarly.search_pubs(self.query_title)
        outformat = gs.FORMAT_BIBTEX
        tokens_title = self.query_title.split(" ")
        biblist = None
        cur_end_ix = len(tokens_title)
        while (biblist is None or len(biblist) < 1) and cur_end_ix > 2:
            if cur_end_ix < len(tokens_title):
                time.sleep(min(0.3, random.random()))
            text_query = " ".join(tokens_title[:cur_end_ix])
            print(f"Googlescholar-Metadata requesting for '{text_query}'")
            biblist = gs.query(text_query, outformat, allresults=True, header=AVAILABLE_HEADERS[random.randint(0, len(AVAILABLE_HEADERS)-1)])
            cur_end_ix -= 1

        #articles = querier.articles
        #if self.count > 0:
        #    articles = articles[:self.count]
        for num, art in enumerate(biblist):
            bibtex_string = art
            #bibtex_string = art.as_citation()

            bib = Bibparser(bibtex_string)
            bib.parse()
            slug = bib.records.keys()[0]
            bib_dict = bib.records[slug]

            title = bib_dict.get('title')

            authors = []

            for author in bib_dict.get('author', []):
                # Ignore non existant given names
                given_name = '%s ' % author.get('given') if 'given' in author else ''
                # Add full stops after abbreviated name parts
                given_name = re.sub(r'(^| +)([A-Z])( +|$)', r'\1\2.\3', given_name)

                authors.append('%s%s' % (given_name, author['family']))

            mi = Metadata(title, authors)

            mi.set_identifier('googlescholar', slug)
            mi.source_relevance = 100-num

            if 'publisher' in bib_dict:
                mi.publisher = bib_dict['publisher']

            if 'issued' in bib_dict:
                if 'literal' in bib_dict['issued']:
                    year = int(bib_dict['issued']['literal'])

                    from calibre.utils.date import utc_tz
                    # We only have the year, so let's use Jan 1st
                    mi.pubdate = datetime.datetime(year, 1, 1, tzinfo=utc_tz)

            self.plugin.clean_downloaded_metadata(mi)
            self._log_metadata(mi)
            self.result_queue.put(mi, True)
            self.log.info(self.result_queue.qsize())

    def _log_metadata(self, mi):
        self.log.info('-'*70)
        self.log.info(mi)
        self.log.info('-'*70)

