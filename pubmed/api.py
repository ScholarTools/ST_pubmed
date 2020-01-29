# -*- coding: utf-8 -*-
"""
http://www.ncbi.nlm.nih.gov/books/NBK25499/

API Release Notes
http://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.Release_Notes

Additional API Features
-------------------------
IDs : https://www.ncbi.nlm.nih.gov/pmc/tools/id-converter-api/
    JAH: This endpoint doesn't work properly
    
Current Status:
    - Needs documentation, especially of optional features
    - working to 

"""

#Standard Library

#Third Party
import requests

#Local
from . import models
from . import config
from . import utils

from .utils import get_truncated_display_string as td
from .utils import get_list_class_display as cldc


class CitationMatcherEntry(object):
    
    def __init__(self,
                 jtitle=None,
                 year=None,
                 volume=None,
                 page1=None,
                 name=None,
                 key=None):
        """
        Constructs an entry for citation matching        
        
        Online Documentation:
        http://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ECitMatch     
        
        Online implementations:
        -----------------------
        http://www.ncbi.nlm.nih.gov/pubmed/batchcitmatch
        
        
        Parameters
        ----------
        jtitle : string
            TODO: How sensitive is this to style? J Urol vs the Journal of Urology?
        year : string
        volume : string
        page1 : string
            The first page of the publication
        name : string
            Author name. Currently this is not limited to a specific author
            although the ability to limit this to a specific author may be
            possible eventually
        key : string
            Use for identifying this entry later on.
            
        Questions
        ---------
        1) Can we provide multiple authors?
        2) Can we specify an author role
    
        Examples
        --------
            
            
        """
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


    def __repr__(self):
        pv = ['jtitle',self.journal_title,
              'key',self.key,
              'name',self.name,
              'page1',self.page1,
              'volume',self.volume,
              'year',self.year]
        return utils.property_values_to_string(pv)
        str = u'' + \
            'year: %s' % self.year
            
        return str


class API(object):
    
    _BASE_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'    
    
    def __init__(self,verbose=False):


        self.verbose = verbose
        
        #tool and email        
        
        self.session = requests.session()
        self.links = Links(self)

    def _make_request(self,
                      method,
                      url,
                      handler,
                      data=None,
                      params=None,
                      data_for_response=None,
                      as_json=False):
        """
        
        params - for URL
        data - for body
        
        """
        if params is None:
            params = {}
            
        if data is None:
            data = {}
            
        if config.email is not None:
            if method.upper() == 'POST':
                data['email'] = config.email
                data['tool'] = config.tool
            else:
                params['email'] = config.email
                params['tool'] = config.tool
        
        resp = self.session.request(method,url,params=params,data=data)  
        
        #resp = self.session.request(method,url,data=data)        

        #req = requests.Request(method,url,data=d2)
        #prepared = req.prepare()
        
        #resp = self.session.request('POST',url + '?db=pubmed',json='10.1002/biot.201400046[DOI]') 
        
        #TODO: Look for 200

        as_json_final = (params.get('retmode',None) is 'json' or 
                         as_json or data.get('retmode',None))
        
        if as_json_final:
            if data_for_response is None:
                return handler(resp.json())
            else:
                return handler(resp.json(),data_for_response)
        else:
            if data_for_response is None:
                return handler(resp.text)
            else:
                return handler(resp.text,data_for_response)
            
    #---- IDs API --------------------
    def get_ids_from_doi(self,
                         doi_or_dois,
                         pmid_only=True):
        """

        This is the web interface, not sure if it is documented somewhere:
        https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/



        The endpoint doesn't seem to be working properly:
        https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids=25186301
        
            So instead I'm using a workaround with seach()
        
        Optional Parameters
        -------------------
        pmid_only : Bool (Default True)
            False is not yet implemented

        Examples
        --------
        pmid = api.get_ids_from_doi('10.1002/nau.24124')
        
        """
        
        
        if type(doi_or_dois) is list:
            is_list = True
            temp = [x + '[DOI]' for x in doi_or_dois]
            query = " OR ".join(temp)
            #10.1242/jeb.154609[DOI] OR 10.1038/s41467-018-03561-w[DOI]
            
        else:
            query = doi_or_dois + '[DOI]'
            is_list = False
            
        #Find the relevant PMIDs
        temp = self.search(query)
        
        if pmid_only:
            if is_list:
                #We have the relevant PMIDs, but no mapping
                ids = temp.ids
                if len(ids) == 0:
                    output = [None for x in doi_or_dois]
                    return output
                
                #This gives us info which maps
                #each PMID back to the DOI
                s = self.summary(ids)
                
                d = {}
                for temp,temp_id in zip(s.docs,s.ids):
                    doi_field = temp['elocationid']
                    #'doi: 10.1002/biot.201400046'
                    if doi_field.startswith('doi: '):
                        doi = doi_field[5:]
                        d[doi] = temp_id
                
                output = [d.get(x) for x in doi_or_dois]
                return output
                
            else:
                #TODO: Support null match case
                value = temp.ids
                if len(value) == 0:
                    return None
                else:
                    return value[0]
        else:
            raise Exception("Returning other IDs is not yet implemented")
        
        #JAH: Note that using search will only return PMIDs, rather than other
        #identifiers through the broken API
        #We can then followup with getting info but this requires extrac work
    
    #---- EInfo ----------------------
    def db_list(self):
        """
        Return a list of available databases.
        
        Our support for these other databases in this codebase is minimal.
        https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.EInfo
        """
        
        params = {'retmode':'json'}
        
        url = self._BASE_URL + 'einfo.fcgi'        
        
        return self._make_request('GET',url,models.get_db_list,params=params)
    
    def db_info(self,db_name):
        """
        
        This looks like it might return information on how to query the 
        specified DB
        
        Info at:
        https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.EInfo
        
        This currently returns the raw JSON response without processing. This
        ideally would be changed ...
        
        Parameters
        ----------
        db_name : string
            Name of the DB to retrieve
        
        Partial Example from db_name='MESH'
        -----------------------------------
        'description': 'MeSH Database',
           'fieldlist': [{'description': 'All terms from all searchable fields',
             'fullname': 'All Fields',
             'hierarchy': 'N',
             'isdate': 'N',
             'ishidden': 'N',
             'isnumerical': 'N',
             'name': 'ALL',
             'singletoken': 'N',
             'termcount': '2359734'},
            {'description': 'Unique number assigned to publication',
             'fullname': 'UID',
             'hierarchy': 'N',
             'isdate': 'N',
             'ishidden': 'Y',
             'isnumerical': 'Y',
             'name': 'UID',
             'singletoken': 'Y',
             'termcount': '0'},
            {'descr
        
        """
        params = {'retmode':'json','db':db_name}
        
        url = self._BASE_URL + 'einfo.fcgi'        
        
        return self._make_request('GET',url,models.pass_through,params=params)
    
    #---- ESeach ----------
    def search(self,query,**kwargs):
        """
        
        Function documentation at:
        http://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESearch

        Provides a list of UIDs matching a text query.

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
            
        Returns
        -------
        models.SearchResult

        """
        
        url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
        params = {'db':'pubmed','term':query,'retmode':'json'}
        #params.update(kwargs)
        
        #JAH: I tried to get the POST call to work but I couldn't
        #I would need to email them to figure out why not ...
        
        
               
        
        #TODO: "For very long queries (more than several hundred characters long), 
        #consider using an HTTP POST call."
        #TODO: Switch to using make_request
        #response = requests.get(url,params=params)
        
        temp = self._make_request('GET',url,models.pass_through,params=params)

        #import pdb
        #pdb.set_trace()
        
        #TODO: Check for an error        
        
        #temp = lxml.etree.fromstring(response.content)
        return models.SearchResult(temp)
    
    #---- EPost -------
    
    #https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.EPost
    #Not yet implemented
    
    def post_data(self):
        pass
    
    #---- ESummary ----------
    def summary(self,id_or_ids,db='pubmed'):
        """
        https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESummary
        
        #TODO: Not yet documented ...
        This currently just passes the JSON through
        """
        
        
        id_string = ','.join(id_or_ids)
        
        payload = {'retmode':'json','db':db,'id':id_string}

        url = self._BASE_URL + 'esummary.fcgi'        
        
        return self._make_request('POST',url,models.SummaryResult,data=payload)
    
    
    #---- EFetch ------
    def fetch(self,id_list,db='pubmed',return_type=None,**kwargs):
        """
        Function documentation at:
        http://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.EFetch
        
        This function needs a lot of work
        - documentation
        - optional parameters
        
        Perhaps we want to break out into a Fetch class like Links????
        
        Return Types
        ------------
        The list of valid return types varies depending upon the database.
        A full list can be seen at:
            https://www.ncbi.nlm.nih.gov/books/NBK25499/table/chapter4.T._valid_values_of__retmode_and/?report=objectonly
        
        """
        
        #TODO: Support PMC
        
        #????
        #JAH: What are the diffences in these formats????
        """
        Document summary	docsum	xml, default
List of UIDs in XML	uilist	xml
List of UIDs in plain text	uilist	text
        null - empty string
        
                    rettype         retmode
                    -------         -------
        summary     docsum          xml
        uids        uilist          xml            
        text        null            asn.1
        xml         null            xml
        medline     medline         text
        pmid_list   uilist          text
        abstract    abstract        text
        
        
        
        """
        
        id_string = ','.join(id_list)
        
        payload = {'db':db,'id':id_string}
        
        if return_type is None:
            pass
        elif return_type is 'text':
            payload['rettype'] = ''
            payload['retmode'] = 'asn.1'
        elif return_type is 'xml':
            payload['rettype'] = ''
            payload['retmode'] = 'xml' 
        elif return_type is 'medline':
            payload['rettype'] = 'medline'
            payload['retmode'] = 'text'
        elif return_type is 'pmid_list':
            payload['rettype'] = 'uilist'
            payload['retmode'] = 'text'
        elif return_type is 'abstract':
            payload['rettype'] = 'abstract'
            payload['retmode'] = 'text'
        
        url = self._BASE_URL + 'efetch.cgi'  

        #return self._make_request('POST',url,models.DocumentSet,data=payload)
        return self._make_request('POST',url,models.pass_through,data=payload)
    
    #---- ELink
    #This section is complicated so instead we have .links which points
    #to the Links class which exposes numerous functions
    
    #---- ECQuery
    
    #---- ESpell
    
    #---- ECitMatch
    
    def match_citations(self,citation_entries):
        """
        Retrieves PubMed IDs (PMIDs) that correspond to a set of input 
        citation strings.

        Online Documentation:
        http://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ECitMatch
        
        Others:
        -------
        http://www.ncbi.nlm.nih.gov/pubmed/citmatch - supports only as first or last author matching
        
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
        
        Returns
        -------
        models.CitationMatchResult - a list of entries is returned if the input 
        to this function is a list
        """
        
        #TODO: 1) retmode not rettype- wrong documentation   
        #2 - post works (this isn't stated in documentation)
        #3) retype goes to batch matching gui with 200 
        #   http://www.ncbi.nlm.nih.gov/pubmed/batchcitmatch?status=0
        #4) xml - this isn't xml
        #5) end | not actually required, even though explicity stated as such
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

    def __repr__(self):
        pv = ['db_info','Return info on a specific database',
              'db_list','Return a list of available databases']
        return utils.property_values_to_string(pv)

                
class Links(object):
    
    """
    Attributes
    ----------
    parent : API
    """
    
    def __init__(self,parent):
        """
        
        """
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