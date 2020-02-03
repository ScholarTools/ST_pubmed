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
from .utils import get_list_class_display as cld


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
    
    def __init__(self,verbose=False,email=None,tool=None):


        self.email = email
        self.tool = tool
        if self.email is None:
            if config.email is not None:
                self.email = config.email
                self.tool = config.tool

        self.verbose = verbose

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

        if self.email is not None:
            if method.upper() == 'POST':
                data['email'] = self.email
                data['tool'] = self.tool
            else:
                params['email'] = self.email
                params['tool'] = self.tool

        response = self.session.request(method,url,params=params,data=data)

        self.last_response = response

        
        #resp = self.session.request(method,url,data=data)        

        #req = requests.Request(method,url,data=d2)
        #prepared = req.prepare()
        
        #resp = self.session.request('POST',url + '?db=pubmed',json='10.1002/biot.201400046[DOI]') 
        
        #TODO: Look for 200

        as_json_final = (params.get('retmode',None) is 'json' or 
                         as_json or data.get('retmode',None) is 'json')
        
        if as_json_final:
            if data_for_response is None:
                return handler(self,response.json())
            else:
                return handler(self,response.json(),data_for_response)
        else:
            if data_for_response is None:
                return handler(self,response.text)
            else:
                return handler(self,response.text,data_for_response)
            
    #---- IDs API --------------------
    def get_ids_from_dois(self,
                         doi_or_dois,
                         pmid_only=True):
        """

        Optional Parameters
        -------------------
        pmid_only : Bool (Default True)
            False is not yet implemented. I think the idea would be to
            provide other IDs, PMCID? others? ISSN?

        Examples
        --------
        #1) Working DOI
        pmid = api.get_ids_from_dois('10.1002/nau.24124')
        '31361061'

        #2) Made up DOI
        pmid = api.get_ids_from_dois('10.1002/nau.123456789')
        None

        #3) Working and made up DOIs
        pmids = api.get_ids_from_dois(['10.1002/nau.23483','10.1002/nau.234832222'])
        ['29336494', None]

        
        """

        #Implementation note, there is a utility called the ID Converter
        #
        #   https://www.ncbi.nlm.nih.gov/pmc/pmctopmid/#converter
        #
        #   But when I tried an example DOI it didn't work. So instead we
        #   use a generic search and specify that we are using DOIs, and this
        #   seems to work. Unfortunately this requires two calls if we search
        #   for multiple DOIs, one for getting the PMIDs and a second call
        #   to match each DOI with its particular PMID

        #URL =  "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"

        
        
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
                #
                #   The search above is basically:
                #   "give us PMIDs from any of these DOIs"
                #
                #   Now we get info on the returned IDs and dig into
                #   their info to get the corresponding DOIs
                ids = temp.ids
                if len(ids) == 0:
                    output = [None for x in doi_or_dois]
                    return output
                
                #This gives us info which maps
                #each PMID back to the DOI
                s = self.doc_summaries(ids)
                
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
    def search(self,
               query,
               db='Pubmed',
               use_history=None,
               web_env=None,
               query_key=None):
        """

        TODO:
        
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

        Examples
        --------
        result = api.search("Langdale Grill")

        """
        url = self._BASE_URL + 'esearch.fcgi'

        params = {'db':db,
                  'term':query,
                  'retmode':'json'}

        if web_env and web_env is not None:
            params['WebEnv'] = web_env
        if use_history and use_history is not None:
            params['usehistory'] = usehistory
        if query_key and query_key is not None:
            params['query_key'] = query_key


        #params.update(kwargs)
        
        #JAH: I tried to get the POST call to work but I couldn't
        #I would need to email them to figure out why not ...
        
        
               
        
        #TODO: "For very long queries (more than several hundred characters long), 
        #consider using an HTTP POST call."

        return self._make_request('GET',url,models.SearchResult,params=params)
    
    #---- EPost -------
    
    #https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.EPost
    #Not yet implemented

    """
    def post_data(self):
        pass
    """
    
    #---- ESummary ----------
    def doc_summaries(self,id_or_ids):
        """
        https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESummary

        Returns less information than the full doc_info() method but it still
        returns quite a bit of information ...

        - article ids
        - authors
        - title
        - issn
        - pages
        ... and many others
        
        Examples
        --------
        summary = api.doc_summaries(27738096)

        #TODO: test non-sense result ...

        #Test other input forms

        """

        if type(id_or_ids) is list:
            if isinstance(id_or_ids[0],int):
                id_or_ids = [str(x) for x in id_or_ids]
            id_string = ','.join(id_or_ids)
        elif isinstance(id_or_ids,int):
            id_string = str(id_or_ids)
        else:
            id_string = id_or_ids
        
        payload = {'retmode':'json',
                   'db':'pubmed',
                   'id':id_string}

        url = self._BASE_URL + 'esummary.fcgi'        
        
        return self._make_request('POST',url,models.SummaryResult,data=payload)
    
    
    #---- EFetch ------
    def doc_info(self,
                 id_or_ids,
                 return_type=None,
                 as_object=True):
        """
        Function documentation at:
        http://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.EFetch
        
        This function needs a lot of work
        - documentation
        - optional parameters
        
        Perhaps we want to break out into a Fetch class like Links????
        
        Optional Inputs
        ---------------
        return_type :
            - 'abstract'
                Abstract contains the title and authors and the abstract.
                TODO: We could parse out only the abstract ...
            - 'pmid_list' - not sure what this is since we are querying by
                    pmids ...


        Examples
        --------
        result = api.doc_info('30343668')
        #TODO: These don't work if as_object = true
        #TODO: make return_type = 'object' support
        result = api.doc_info('30343668',return_type='pmid_list')
        result = api.doc_info('30343668',return_type='abstract')
        result = api.doc_info('30343668',return_type='medline')
        result = api.doc_info('30343668',return_type='text')
        result = api.doc_info('30343668',return_type='xml')

        #medline
        #----------------------------
        #PMID- 30343668
        #OWN - NLM
        #STAT- MEDLINE
        #DCOM- 20190320
        #LR  - 20191101
        #IS  - 2042-6410 (Electronic)
        #IS  - 2042-6410 (Linking)

        #text
        #-----------------------
        #Pubmed-entry ::= {
        #  pmid 30343668,
        #  medent {
        #    em std {
        #      year 2018,
        #      month 10,
        #      day 23,
        #      hour 6,
        #      minute 0
        #    },

        #xml
        #------------------------



        """


        #The list of valid return types varies depending upon the database.
        #A full list can be seen at:
        #    https://www.ncbi.nlm.nih.gov/books/NBK25499/table/chapter4.T._valid_values_of__retmode_and/?report=objectonly

        
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

        if type(id_or_ids) is list:
            id_string = ','.join(id_or_ids)
        else:
            id_string = id_or_ids
        
        payload = {'db':'pubmed',
                   'id':id_string}

        if as_object:
            payload['rettype'] = ''
            payload['retmode'] = 'xml'
        elif return_type is None:
            pass
        elif return_type is 'text':
            #default ...
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
        if as_object:
            fh = models.PubmedArticleSet
        else:
            fh = models.pass_through
        return self._make_request('POST',url,fh,
                                  data=payload,as_json=False)
    
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
        
        return self._make_request('POST',url,models.citation_match_parser,
                                  data=payload,
                                  data_for_response=data_for_response)

    def __repr__(self):
        pv = ['email',self.email,
              'tool',self.tool,
              'links',cld(self.links),
              'db_info','Return info on a specific database',
              'db_list','Return a list of available databases'
              'doc_summaries','Returns summary info on specified Pubmed IDs']
        return utils.property_values_to_string(pv)

                
class Links(object):
    
    """
    https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ELink

    Note, ELink has a TON of endpoints but I don't use them so this really
    isn't flushed out ...

    Attributes
    ----------
    parent : API
    """
    
    def __init__(self,parent):
        """
        
        """
        self.parent = parent


    #TODO: This needs to be rewritten to specifically give
    #a single PMC value for a PMCID
    def pmid_to_pmc(self,pmids):
        """
        What happens when

        :param pmids:
        :return:

        Examples
        --------
        result = api.links.pmid_to_pmc([28929910,29141938])

        """

        data_for_response = {'pmids':pmids}

        if isinstance(pmids, list):
            if isinstance(pmids[0], int):
                str_list = [str(x) for x in pmids]
            else:
                str_list = pmids

            id_param = ','.join(str_list)
        else:
            if isinstance(pmids, int):
                id_param = str(pmids)
            else:
                id_param = pmids

        params = {'dbfrom':'pubmed',
                  'db':'pmc',
                  'id':id_param,
                  'retmode':'json'}
        return self._make_link_request(params,models.PMIDToPMCLinkSets,data_for_response=data_for_response)
    
    def pmc_to_pmid(self,pmc_ids):
        pass
    
    def _make_link_request(self,params,handler,data_for_response=None):
        
        url = self.parent._BASE_URL + 'elink.fcgi'
        return self.parent._make_request('POST',url,handler,data=params,data_for_response=data_for_response)

    def __repr__(self):
        pv = ['pmid_to_pmc','Given a PMID, get a PMCID',
              'db_list','Return a list of available databases']
        return utils.property_values_to_string(pv)