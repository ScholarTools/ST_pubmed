# -*- coding: utf-8 -*-
"""
Status:
    Slowly working on updating api and theses tests
"""

#import os
#import sys
#sys.path.insert(0, os.path.abspath('..'))

from pubmed import API, CitationMatcherEntry
api = API(verbose=True)

#---- ID Matching
#======================================
#Single DOI match
doi='10.1002/biot.201400046'
pmid = api.pubmed.doi_to_pmid(doi)
assert pmid == '25186301', "PMID returned for DOI is not as expected"

#Multiple DOI match
dois=['10.1002/biot.201400046','10.2106/JBJS.L.00252']
pmids = api.pubmed.doi_to_pmid(dois)
assert pmids == ['25186301', '23467867'], "PMIDs are not as expected"

#Reversed order, PMIDs should reverse
dois=['10.2106/JBJS.L.00252','10.1002/biot.201400046']
pmids = api.pubmed.doi_to_pmid(dois)
assert pmids == ['23467867', '25186301'], "PMIDs are not as expected"

#Missing a comma - single element that won't match
dois=['10.1002/biot.201400046' '10.2106/JBJS.L.00252']
pmids = api.pubmed.doi_to_pmid(dois)
assert pmids == [None], "PMID result not as expected"

#Removed 0 from leading 10
dois='1.1002/biot.201400046'
pmids = api.pubmed.doi_to_pmid(dois)
assert pmids == None, "PMID result not as expected"


#TODO: Need more DOIs to test


#---- DB Info (EInfo)
#======================================
db_list = api.db_list()
assert db_list[0] == 'pubmed', "Unexpected list result"
#Currently 50 databases! April 2018
#- ncbisearch
#- nlmcatalog
#- pmc
#- mesh

#Currently the raw JSON data are returned
db_info = api.db_stats('mesh')
#- header
#- einforesult
#   - dbinfo
#       - dbname - 'mesh'
#       - menuname - 'MeSH
#       - description - 'MeSH Database'
#       - dbbuild - Build180430-0310.1
#       - count - 276142
#       - lastupdate - '2018/04/30 03:42'
#       - fieldlist array of dicts
#       - linklist



#JAH: Currently at this point


#---- ESearch, Search Testing
#============================
#
#   Returns IDs that match the search
#http://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESearch
temp = api.search('Mountcastle') 

#TODO: More search examples

#---- ESummary, Summary Testing
#==============================
ids = ['25186301', '23467867']
summaries = api.pubmed.summary(ids)








#---- EFetch, Fetch detailed info
#------------------------------------
ids = ['11850928','11482001']
result = api.fetch(ids)
result.docs[0].parse()

#        text        null            asn.1
#        xml         null            xml
#        medline     medline         text
#        pmid_list   uilist          text
#        abstract    abstract        text
#
ids = ['25186301', '23467867']
result = api.fetch(ids,return_type='summary')
result = api.fetch(ids,return_type='text')
result = api.fetch(ids,return_type='xml') 
result = api.fetch(ids,return_type='pmid_list')
result = api.fetch(ids,return_type='abstract')



#Citaton Matching
#------------------
entry = CitationMatcherEntry(jtitle='Bioinformatics',year=2015,volume=31,page1=3897)
result = api.match_citations(entry)
print(result)    





#Link Testing
#------------
#ids = ['12964947','18164480']
#result = api.links.pmid_to_pmc(ids)



#,usehistory='n')

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
