# -*- coding: utf-8 -*-
"""
"""

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from pubmed import API, CitationMatcherEntry

api = API()


#Citaton Matching
#------------------
entry = CitationMatcherEntry(jtitle='Bioinformatics',year=2015,volume=31,page1=3897)
result = api.match_citations(entry)

print(result)    

#Info fetching
#--------------
ids = ['11850928','11482001']
result = api.fetch(ids)

#Link Testing
#------------
#ids = ['12964947','18164480']
#result = api.links.pmid_to_pmc(ids)
