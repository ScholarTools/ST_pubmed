# -*- coding: utf-8 -*-
"""
http://www.ncbi.nlm.nih.gov/books/NBK25499/
"""

#Standard Library
import xml

#Third Party
import requests
import lxml

#Local
from . import models


class CitationMatcherEntry(object):
    
    def __init__(self,jtitle=None,year=None,volume=None,page1=None,name=None,key=None):
        pass
    
    def get_serialized(self,key_number=None):
        pass

class Pubmed(object):
    
    def __init__(self):
        pass

    def match_citations(self,citation_entries):
        #http://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ECitMatch
        
        #journal_title|year|volume|first_page|author_name|your_key|
        pass

    def fetch(self):
        pass
    
    def search(self,query,**kwargs):
        """
        
        Function documentation at:
        http://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESearch

        Required parameters
        query : string
            Can use markup - e.g. asthma[title]
          
        Optional Parameters – History Server
        ------------------------------------
        usehistory : 
            If 'y', resulting IDs wil saved for subsequent call
        WebEnv : ????
        query_key :    
        
        Optional Parameters – Retrieval
        -------------------------------
        retstart :
           Index of the first UID to be retrieved (0 is first)
        retmax :
            # of UIDs to return (max is 100000)
        rettype : AVAIBLE BUT NOT SUPPORTED
        sort :
            - 'first_author' :
            - 'pub+date' :
        field :
            If specified, entire search will be limited to the specified field
        
        Optional Parameters – Dates
        ---------------------------
        datetype : TODO: Verify types for pubmed
            - 'mdat' : modification date
            - 'pdat' : publication date
        reldate : integer string
            Datetype within the last n days
        mindate, maxdate :
            Range, allowed formats include YYYY/MM/DD, YYYY, YYYY/mm

        """
        
        url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
        params = {'db':'pubmed','term':query,'retmode':'json'}
        #params.update(kwargs)       
        
        response = requests.get(url,params=params)
        
        #TODO: Check for an error        
        
        #temp = lxml.etree.fromstring(response.content)
        return models.SearchResult(response.json())