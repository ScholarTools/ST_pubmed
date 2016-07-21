# -*- coding: utf-8 -*-
"""
"""

from pubmed import API, CitationMatcherEntry

api = API()

#temp = api.search('Mountcastle') #,usehistory='n')

#print(temp)

#(self,jtitle=None,year=None,volume=None,page1=None,name=None,key=None):

# temp = CitationMatcherEntry(jtitle='Bionformatics',year=2015,volume=31,page1=3897)
# temp2 = api.match_citations(temp)
#result: 'NOT_FOUND;INVALID_JOURNAL'

temp = CitationMatcherEntry(jtitle='Bioinformatics',year=2015,volume=31,page1=3897)
temp2 = api.match_citations(temp)
#result: 26315901

# temp = CitationMatcherEntry(jtitle='Bioinformatics',year=2015,volume=31)
# temp2 = api.match_citations(temp)
#'AMBIGUOUS (783 citations)'

#temp = CitationMatcherEntry(jtitle='Bioinformatics',year=2035,volume=31,page1=3897)
#temp2 = api.match_citations(temp)
#'NOT_FOUND'

import pdb
pdb.set_trace()