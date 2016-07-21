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
from . import config

#TODO: Ask about class name calling methods

class CitationMatcherEntry(object):
    
    def __init__(self,jtitle=None,year=None,volume=None,page1=None,name=None,key=None):
        self.jtitle = jtitle
        self.year = year
        self.volume = volume
        self.page1 = page1
        self.name = name
        self.key = key
        
        #TODO: We could distinguish between those that are not found due
        #to a high liklihood vs those not found due to bad meta
        #
        #i.e. need page1 or name, otherwise finding answer is unlikely
        #
        #This would require a lot of logic ...
        #
        #   def enough_info() => could be used to display a warning to the user
        #
        #   LOW PRIORITY
    
    def get_serialized(self,alt_key=None):
        
        key_order = ('jtitle', 'year', 'volume', 'page1', 'name', 'key')
        
        values = [getattr(self,key) for key in key_order]
        
        if values[-1] is None:
            values[-1] = alt_key
            
        #Let's also make sure that we are dealing with strings ....
        values = ["%s" % x if x is not None else '' for x in values]
             
        #Documentation says they should end with a | but it doesn't seem to matter
        return '|'.join(values)

    """
    def __repr__(self):
        str = u'' + \
            'year: %s' % self.year
            
        return str
    """

class API(object):
    
    _BASE_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'    
    
    def __init__(self):
        
        #tool and email        
        
        self.session = requests.session()
        self.links = Links(self)

    def _make_request(self,method,url,handler,data=None,params=None,as_json=False,data_for_response=None): 
        
        if config.email is not None:
            if method.upper() == 'POST':
                data['email'] = config.email
                data['tool'] = config.tool
            else:
                params['email'] = config.email
                params['tool'] = config.tool
        
        resp = self.session.request(method,url,params=params,data=data)        

        #TODO: Check response state - what are we expecting ?????

        if as_json:
            if data_for_response is None:
                return handler(resp.json())
            else:
                return handler(resp.json(),data_for_response)
        else:
            if data_for_response is None:
                return handler(resp.text)
            else:
                return handler(resp.text,data_for_response)

    def match_citations(self,citation_entries):
        """
        Retrieves PubMed IDs (PMIDs) that correspond to a set of input 
        citation strings.

        Online Documentation:
        http://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ECitMatch
        
        Parameters
        ----------
        citation_entries : [CitationMatcherEntry] or CitationMatcherEntry        
            An instance or list of instances of CitationMatcherEntry
            
        Example
        -------
        from pubmed import Pubmed, CitationMatcherEntry
        api = Pubmed()        
        citation = CitationMatcherEntry(jtitle='Bioinformatics',year=2015,volume=31,page1=3897)
        matches = api.match_citations(citation)
        """
        
        #TODO: 1) termode not rettype- wrong documentation   
        #2 - post works
        #3) retype goes to batch matching gui with 200 
        #http://www.ncbi.nlm.nih.gov/pubmed/batchcitmatch?status=0
        #4) xml - no
        #5) end | required
        #6) no need to escape |, but you can
        
        
        if citation_entries is list:
            is_single = False
            pass
        else:
            is_single = True
            citation_entries = [citation_entries]
            
        #import pdb
        #pdb.set_trace()
        
        #"key_{:03d}".format(i)
        temp_strings = [x.get_serialized("key_{:03d}".format(i)) for i,x in enumerate(citation_entries)]
        query = '\n'.join(temp_strings)
        query_lengths = [len(x) for x in temp_strings]
        
        payload = {'db':'pubmed','retmode':'xml','bdata':query}     
        
        data_for_response = {
            'query_lengths':query_lengths,
            'entries':citation_entries,
            'is_single':is_single}
        
        url = self._BASE_URL + 'ecitmatch.cgi'        
        
        return self._make_request('POST',url,models.citation_match_parser,data=payload,data_for_response=data_for_response)

    def fetch(self,id_list,db='pubmed'):
        """
        Function documentation at:
        http://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.EFetch
        """
        
        #TODO: Support PMC
        
        """
             rettype retmode
        text       null   asn.1
        xml         null   xml
        medline    medline text
        pmid list  uilist text
        abstract   abstract text
        """
        
        id_string = ','.join(id_list)
        
        payload = {'db':'pubmed','id':id_string,'retmode':'xml'}

        url = self._BASE_URL + 'efetch.cgi'  

        return self._make_request('POST',url,models.DocumentSet,data=payload)
        
    
    def links(self,ids):
        
        """
        http://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ELink
        """
    
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
        
class Links(object):
    
    def __init__(self,parent):
        self.parent = parent
        
    def pmid_to_pmc(self,pmids):
        id_param = ','.join(pmids)
        params = {'dbfrom':'pubmed','db':'pmc','id':id_param}
        return self._make_link_request(params,models.PMIDToPMCLinkSet)
    
    def pmc_to_pmid(self,pmc_ids):
        pass
    
    def _make_link_request(self,params,handler):
        
        url = self.parent._BASE_URL + 'elink.fcgi'
        return self.parent._make_request('POST',url,handler,data=params)