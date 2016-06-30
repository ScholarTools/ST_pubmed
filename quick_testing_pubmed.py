# -*- coding: utf-8 -*-
"""
"""

from pubmed.main import Pubmed, CitationMatcherEntry

api = Pubmed()

#temp = api.search('Mountcastle') #,usehistory='n')

#print(temp)

#(self,jtitle=None,year=None,volume=None,page1=None,name=None,key=None):
temp = CitationMatcherEntry(jtitle='Bionformatics',year=2015,volume=31,page1=3897)

temp2 = api.match_citations(temp)

import pdb
pdb.set_trace()