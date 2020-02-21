# -*- coding: utf-8 -*-
"""

from pubmed import API, CitationMatcherEntry
api = API()

#TODO: CHeck this out:
https://www.ncbi.nlm.nih.gov/pmc/tools/developers/

Books
----------------------
Entrez Help
https://www.ncbi.nlm.nih.gov/books/NBK3837/

Entrez Programming Help
https://www.ncbi.nlm.nih.gov/books/NBK25501

DTD Elements List
https://www.nlm.nih.gov/bsd/licensee/elements_alphabetical.html

DTD Documentation
https://dtd.nlm.nih.gov/ncbi/pubmed/

Medline Elements
https://www.nlm.nih.gov/bsd/mms/medlineelements.html


JAH Status:
- add support for paging ...

1) Document status of each test
3) Add examples for query matcher
4) Add real-time search suggestions - espell?
5) mesh support
- add nlm support ...

------------------------------------------------------
                Entrez Endpoint Notes
------------------------------------------------------

EInfo
-------------------------------------------------------
Returns information on how to search each database.

Status: Needs documentation updates



ESearch
-------------------------------------------------------
Returns a list of IDs matching a query ...

Status: search() method needs to be updated ...


ESummary




"""

#Standard Library
from typing import Union, List, Optional
import re
import time


#Third Party
import requests

#Local
from . import models
from . import einfo_models
from . import esearch_models
from . import elink_models
from .einfo_models import DbInfo
CitationMatchResult = models.CitationMatchResult
from . import config
from . import utils
from .utils import get_truncated_display_string as td
from .utils import get_list_class_display as cld
from .utils import quotes, display_class

class CitationMatcherEntry(object):

    """
    Online Documentation:
    http://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ECitMatch

    Online implementations:
    -----------------------
    http://www.ncbi.nlm.nih.gov/pubmed/batchcitmatchs

    Attributes
    ----------
    jtitle : str
        TODO: How sensitive is this to style? J Urol vs the Journal of Urology?
    year : str
    volume : str
    page1 : str
        The first page of the publication
    name : str
        Author name.
        TODO: Can we split this field in some way????
    key : string
        Use for identifying this entry later on.
        TODO: It would be good to provide an example of this ...
    """
    
    def __init__(self,
                 journal:Optional[str]=None,
                 year:Union[int,str,None]=None,
                 volume=None,
                 page1=None,
                 author=None,
                 key=None,
                 autofix_author=True):
        """
        Constructs an entry for citation matching        

        Parameters
        ----------
        autofix_author : bool
            Tries to reverse incorrect names
            
        Questions
        ---------
        1) Can we provide multiple authors? NO
        2) Can we specify an author role? NO
    
        Examples
        --------
        from pubmed import API, CitationMatcherEntry
        api = API()
        c1 = CitationMatcherEntry(year=2012,author='Aizawa N',volume=62)
        result = api.match_citations(c1)

        """
        self.journal = journal
        self.year = year
        self.volume = volume
        self.page1 = page1
        self.author = author
        self.key = key

        if autofix_author:
            #AB CDEF
            #12345
            if len(author) > 5 and author[2] == ' ' and author[0:2].isupper():
                self.author = author[3:] + ' ' + author[0:2]
                #If name is like "AB Cdef" then we apparently
                #should change to Cdef AB
                #If However we have Ab Cdef, like Li John, then I don't think
                #we should switch - i.e. we need to be careful with initials
                #versus short last names

        
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
        
        key_order = ('journal', 'year', 'volume', 'page1', 'author', 'key')
        
        values = [getattr(self,key) for key in key_order]
        
        if values[-1] is None:
            values[-1] = alt_key
            
        #Let's also make sure that we are dealing with strings ....
        values = ["%s" % x if x is not None else '' for x in values]
             
        #Documentation says they should end with a | but it doesn't seem to matter
        temp =  '|'.join(values)
        return temp + '|'


    def __repr__(self):
        return display_class(self,
                             [  'journal',quotes(self.journal),
                                'year', quotes(self.year),
                                'volume',quotes(self.volume),
                                'page1',quotes(self.page1),
                                'author', quotes(self.author),
                                'key',quotes(self.key)])

class MESH(object):

    def __init__(self,parent):
        self.parent = parent

    def info(self):
        return self.parent._db_info('mesh')

    def search(self,query):
        if return_type == 'ids':
            fh = esearch_models.get_search_ids
            mode = 'json'
        elif return_type == 'object':
            fh = esearch_models.JSONSearchResult
            mode = 'json'
        elif return_type == 'object-xml':
            fh = esearch_models.XMLSearchResult
            mode = 'xml'
        elif return_type == 'text-json':
            fh = models.pass_through
            mode = 'json'
        elif return_type == 'text-xml':
            fh = models.pass_through
            mode = 'xml'
        elif return_type == 'xml':
            fh = models.get_xml
        elif return_type == 'json':
            fh = models.get_json
        else:
            raise ValueError('Unrecognized return type')


        return self.parent._esearch('pubmed',query,fh,start=start,max=max,mode=mode)

class PMC(object):

    def __init__(self,parent):
        self.parent = parent

    def info(self):
        return self.parent._db_info('pmc')

    def get_pmid(self,id_or_ids):
        """

        Examples
        --------
        >>> result = api.pmc.get_pmid(['PMC3475720', 'PMC3043805', 'PMC5751745'])
        ['22255275', '21068196', '28322213']

        #Shuffle order
        result = api.pmc.get_pmid(['PMC3043805', 'PMC5751745', 'PMC3475720'])
        ['21068196', '28322213', '22255275']

        #Added bad match
        result = api.pmc.get_pmid(['PMC3043805', 'PMC5751745', 'PMC347572012345'])
        ['21068196', '28322213', None]

        See Also
        --------
        Pubmed.get_pmcid
        """
        fh = elink_models.pmc_to_pmid_results
        return self.parent._id_convertor(id_or_ids, fh, id_type='pmcid')

    def search(self):
        pass

class Pubmed(object):

    parent : 'API'

    def __init__(self, parent:'API'):
        """
        Accessible as: api.pubmed

        """
        self.parent = parent

    def info(self):
        """

        Example
        -------
        r = api.pubmed.info()
        df = r.fields_as_table()
        df.to_clipboard()
        """
        return self.parent._db_info('pubmed')

    def get_pmcid(self, id_or_ids):
        """

        Parameters
        ----------
        id_or_ids

        Examples
        --------
        #1 with PMC, 1 without
        result = api.pubmed.get_pmcid([1,31500373])

        #Multiple with PMCIDs
        >>> result = api.pubmed.get_pmcid([22255275,21068196,28322213])
        ['PMC3475720', 'PMC3043805', 'PMC5751745']

        See Also
        --------
        PMC.get_pmid

        """
        fh = elink_models.pmid_to_pmc_results
        return self.parent._id_convertor(id_or_ids,fh)

    def get_link_outs(self,id_or_ids,primary_only=True):
        """

        Example
        -------
        result =
        """

        #https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&id=19880848,19822630&cmd=prlinks

        fh = models.pass_through

        if primary_only:
            cmd = 'prlinks'
        else:
            cmd = 'llinks'

        return self.parent._elink('pubmed',fh,cmd=cmd)


    def get_related(self,id):
        """

        """
        return self.parent._elink('pubmed',cmd='neighbor_score')


    def pmid_to_doi(self,id_or_ids):
        """

        doi = api.pubmed.pmid_to_doi('31361061')
        """

        #Not working, emailed NLM
        pass


    def doi_to_pmid(self, doi_or_dois):
        """

        Examples
        --------
        #1) Working DOI
        pmid = api.pubmed.doi_to_pmid('10.1002/nau.24124')
        '31361061'

        #2) Made up DOI
        pmid = api.pubmed.doi_to_pmid('10.1002/nau.123456789')
        None

        #3) Working and made up DOIs
        pmids = api.pubmed.doi_to_pmid(['10.1002/nau.23483','10.1002/nau.234832222'])
        ['29336494', None]
        """

        # Implementation note, there is a utility called the ID Converter

        #esearch -db pubmed -query "31361061" | esummary | xtract -pattern
        #DocumentSummary -block ArticleId -sep "\t" -tab "\n" -element
        #IdType,Value | grep -E '^pubmed|doi'

        if isinstance(doi_or_dois,list):
            is_list = True
            temp = [x + '[DOI]' for x in doi_or_dois]
            query = " OR ".join(temp)
            # 10.1242/jeb.154609[DOI] OR 10.1038/s41467-018-03561-w[DOI]
        else:
            query = doi_or_dois + '[DOI]'
            is_list = False

        # Find the relevant PMIDs
        temp = self.search(query)

        if is_list:
            # We have the relevant PMIDs, but no mapping
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

            # This gives us info which maps
            # each PMID back to the DOI
            s = self.doc_summary(ids)

            d = {}
            for temp, temp_id in zip(s.docs, s.ids):
                doi_field = temp['elocationid']
                # 'doi: 10.1002/biot.201400046'
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
        # JAH: Note that using search will only return PMIDs, rather than other
        # identifiers through the broken API
        # We can then followup with getting info but this requires extra work

    def search(self,query,start=None,max=None,return_type='object'):
        """

        Parameters
        ----------
        start : default 0
        max : default 20
            Max value is 100000
        return_type :
            - 'ids'
            - 'count' - NYI
            - 'object'
            - 'object-xml'
            - 'text-json'
            - 'text-xml'
            - 'xml'
            - 'json'

        Examples
        --------
        result = api.pubmed.search('Amundsen Webster',max=100)

        #Invalid identifier
        result = api.pubmed.search('Amundsen AND 2018[Year]',max=100,return_type='object-xml')

        #Output type testing
        #---------------------------------------
        result = api.pubmed.search('Grill WM',max=400,return_type='ids')
        result = api.pubmed.search('Grill WM',max=400,return_type='object-xml')
        result = api.pubmed.search('Grill WM',max=400,return_type='object')

        """
        if return_type == 'ids':
            fh = esearch_models.get_search_ids
            mode = 'json'
        elif return_type == 'object':
            fh = esearch_models.JSONSearchResult
            mode = 'json'
        elif return_type == 'object-xml':
            fh = esearch_models.XMLSearchResult
            mode = 'xml'
        elif return_type == 'text-json':
            fh = models.pass_through
            mode = 'json'
        elif return_type == 'text-xml':
            fh = models.pass_through
            mode = 'xml'
        elif return_type == 'xml':
            fh = models.get_xml
        elif return_type == 'json':
            fh = models.get_json
        else:
            raise ValueError('Unrecognized return type')


        return self.parent._esearch('pubmed',query,fh,start=start,max=max,mode=mode)

    def get_info(self,id_or_ids,return_type='object'):
        """

        Parameters
        ----------
        id_or_ids : Union[List[str],List[int],str,int]
            ID or list of IDs to process
        return_type : str
            - 'object', default
            - 'text'
            - 'xml'

        Examples
        --------
        result = api.pubmed.get_info('30343668')


        """

        """
        TODO: We could also support the other return types ...
        text ASN.1	null	asn.1, default
        XML	        null	xml
        MEDLINE	    medline	text
        PMID list	uilist	text
        Abstract	abstract	text
        """

        if return_type == 'object':
            fh = models.PubmedArticleSet
        elif return_type == 'text':
            fh = models.pass_through
        else:
            fh = models.get_xml

        return self.parent._efetch('pubmed',id_or_ids,fh)

    def get_summary(self,id_or_ids,return_type='object'):
        """

        #TODO: for consistency we should support json & xml
        #with object from xml being default ...

        Parameters
        ----------
        id_or_ids : Union[List[str],List[int],str,int]
            ID or list of IDs to process
        return_type : str
            - 'object', default
            - 'text-xml'
            - 'text-json'
            - 'xml'
            - 'json'


        Examples
        --------
        result = api.pubmed.get_summary([32022941,31788552])

        result = api.pubmed.get_summary([32022941,31788552])
        """

        if return_type == 'object':
            fh = models.SummaryResult
        elif return_type == 'text-xml':
            fh = models.pass_through
            mode='xml'
        elif return_type == 'text-json':
            fh = models.pass_through
            mode='json'
        elif return_type == 'xml':
            fh = models.get_xml
        elif return_type == 'json':
            fh = models.get_json
        else:
            raise ValueError('Invalid return_type option')
            pass

        return self.parent._esummary('pubmed',id_or_ids,fh,mode)




    def pubmed(self):
        """

        See also the advanced Pubmed search:
        https://www.ncbi.nlm.nih.gov/pubmed/advanced



        """
        return self._db_info('pubmed')



class API(object):
    """

    Attributes
    -----------
    email : str
    tool : str
    key : str
    rate : int

    """

    authentication : 'Authentication'
    query_logger : 'QueryLogger'
    
    _BASE_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'    
    
    def __init__(self,verbose=False,
                 email:Optional[str]=None,
                 tool:Optional[str]=None,
                 api_key:Optional[str]=None,
                 rate:Optional[int]=None):

        """

        Parameters
        ----------
        email :
        api_key : str
            TODO: Link to authentication
        rate : int
            This should really only be passed in when you've negotiated a rate
            with NCBI
        """

        self.authentication = Authentication(email,tool,api_key,rate)
        self.query_logger = QueryLogger()

        self.verbose = verbose

        self.session = requests.session()

        #Method Links
        #-----------------------------
        self.pubmed = Pubmed(self)
        self.pmc = PMC(self)
        self.mesh = MESH(self)

    def __repr__(self):
        return display_class(self,
              ['authentication',cld(self.authentication),
              'query_logger',cld(self.query_logger),
              'pubmed','Pubmed functions holder',
              'db_list','Return a list of available databases',
              'doc_summary','Returns summary info on specified Pubmed IDs',
              'doc_info',"Get's detailed info on specific IDs"])


    def _make_request(self,
                      method,
                      url,
                      handler,
                      params,
                      data_for_response=None,
                      key_ok=True):
        """

        Parameters
        ----------
        method : str
            e.g., 'GET', 'POST'
        url : str
            URL to request
        handler : function handle
            The handler gets called with the request passed in
        data : dict
            Parameters that will go into the body or url
        
        """
        if params is None:
            params = {}

        params = self.authentication.add_auth(params,key_ok)

        self.authentication.limit_rate()

        #Making the request
        #----------------------------------------------------
        start_time = time.monotonic()
        if method == 'POST':
            response = self.session.request(method,url,data=params)
        else:
            response = self.session.request(method,url,params=params)
        elapsed_time = time.monotonic() - start_time
        #Logging ...
        #----------------------------------------------------
        self.query_logger.log_query(method,url,params,response,elapsed_time)

        #Handle the response
        #--------------------------------------------------------
        start_time = time.monotonic()
        if data_for_response is None:
            output =  handler(self,response)
        else:
            output =  handler(self,response,data_for_response)
        elapsed_time = time.monotonic() - start_time
        self.query_logger.log_parse_time(elapsed_time)

        return output

    def _db_info(self, db_name=None) -> Union['DbInfo', List[str]]:
        """

        List of databases with descriptions at:
        https://www.ncbi.nlm.nih.gov/books/NBK3837/

        Our support for these other databases in this codebase is minimal.
        https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.EInfo

        Returns information on how to query the specified DB.

        Parameters
        ----------
        db_name : string
            Name of the DB to retrieve

        Examples
        --------
        all_dbs = api._db_info()

        Returns
        -------
        Union['DbInfo', List[str]]
        """
        url = self.parent._BASE_URL + 'einfo.fcgi'

        if db_name is None:
            params = {'retmode': 'json'}
            response = self.parent._make_request('GET', url, models.pass_through,
                                          params=params)
            return sorted(response['einforesult']['dblist'])
        else:
            params = {'retmode': 'xml', 'db': db_name}

        return self.parent._make_request('GET', url,
                                         einfo_models.parse_db_info,
                                        params=params)

    #---- ELink ---------
    def _elink(self,function_handle,id_or_ids,db=None,cmd=None,dbfrom=None,mode='json'):
        """
        https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ELink

        Parameters
        ----------
        db : default 'pubmed'
        dbfrom : default 'pubmed'
        cmd : default 'neighbor'

        """

        url = self._BASE_URL + 'elink.fcgi'
        ids = _get_id_str(id_or_ids)
        params = {
                  'id': ids,
                  'db': db,
                  'dbfrom': dbfrom,
                  'cmd': cmd,
                  'retmode':mode}

        return self._make_request('GET',url,function_handle,params=params)

    #---- ESearch ----------
    def _esearch(self,
                db_name,
                query,
                function_handle,
                mode='xml',
                start=None,
                max=None):
        """
        Function documentation at:
        http://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESearch

        Provides a list of UIDs matching a text query.

        Parameters
        ----------
        query : str
            Can use markup - e.g. asthma[title]
        start : Optional[int], default 0
            Index of the first UID to be retrieved (0 is first)
        max : Optional[int], default 20
            # of UIDs to return (max is 100000)
        mode :
            - 'xml'
            - 'json'



        See Also
        --------
        Pubmed.search

        """

        #TODO: Implement sort ...

        url = self._BASE_URL + 'esearch.fcgi'

        params = {'db':db_name,
                  'term':query,
                  'retmode':mode,
                  'retstart':start,
                  'retmax':max}

        return self._make_request('GET',url,function_handle,params=params)
    
    #---- EPost -------
    
    #https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.EPost
    #Not yet implemented

    #---- ESummary ----------
    def _esummary(self,
                    db_name,
                    id_or_ids:Union[List[int],List[str],int,str],
                    function_handle,
                    mode='xml')\
        ->models.SummaryResult:
        """
        https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESummary

        Returns less information than the full doc_info() method but it still
        returns quite a bit of information ...


        See Also
        --------

        """

        #TODO: Used to specify version 2.0 ESummary XML.
        # The only supported value is ‘2.0’. When present,
        # ESummary will return version 2.0 DocSum XML that is
        # unique to each Entrez database and that often contains
        # more data than the default DocSum XML.

        ids = _get_id_str(id_or_ids)
        
        params = {'retmode':'json',
                   'db':db_name,
                   'id':ids,
                  'retmode':mode}

        url = self._BASE_URL + 'esummary.fcgi'

        return self._make_request('POST',url,function_handle,params)


    def _efetch(self,
                 db_name,
                 id_or_ids,
                 function_handle,
                 type='',
                 mode='xml'):
        """
        Function documentation at:
        http://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.EFetch

        See Also
        --------
        pubmed.api.Pubmed.

        """


        #The list of valid return types varies depending upon the database.
        #A full list can be seen at:
        #    https://www.ncbi.nlm.nih.gov/books/NBK25499/table/chapter4.T._valid_values_of__retmode_and/?report=objectonly


        if isinstance(id_or_ids,list):
            id_string = ','.join(id_or_ids)
        else:
            id_string = id_or_ids
        
        params = {'db':db_name,
                   'id':id_string,
                   'rettype':type,
                   'retmode':mode}

        url = self._BASE_URL + 'efetch.cgi'  

        return self._make_request('POST',url,function_handle,params)
    
    #ID Convertor ---------------------------
    def _id_convertor(self,id_or_ids,function_handle,id_type='pmid'):
        """
        https://www.ncbi.nlm.nih.gov/pmc/tools/id-converter-api/
        """

        #todo: ask about api support

        URL = ' https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/'

        #Validvaluesare "pmcid", "pmid", "mid", and "doi"
        #idtype = pmcid

        ids = _get_id_str(id_or_ids)

        params = {'idtype': id_type,
                  'ids': ids,
                  'versions': 'no',
                  'format': 'json'}

        ids2 = ids.split(',')

        return self._make_request('POST', URL, function_handle,
                                  params, key_ok=False, data_for_response=ids2)


        pass

    #---- ELink
    #This section is complicated so instead we have .links which points
    #to the Links class which exposes numerous functions
    
    #---- ECQuery
    
    #---- ESpell
    
    #---- ECitMatch
    
    def match_citations(self,citation_entries:CitationMatcherEntry)\
            ->Union[CitationMatchResult,List[CitationMatchResult]]:
        """
        Retrieves PubMed IDs (PMIDs) that correspond to a set of input 
        citation strings.

        Online Documentation:
        http://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ECitMatch
        
        Others:
        -------
        http://www.ncbi.nlm.nih.gov/pubmed/citmatch - this endpoint
        supports selecting that the specified author should be a first author
        or last author only - but this returns a web page, not
        machine readable info
        
        Parameters
        ----------
        citation_entries : [CitationMatcherEntry] or CitationMatcherEntry        
            An instance or list of instances of CitationMatcherEntry
            
        Examples
        --------
        #Valid entry  --------
        from pubmed import API, CitationMatcherEntry
        api = API()
        citation = CitationMatcherEntry(jtitle='Bioinformatics',year=2015,volume=31,page1=3897)
        match = api.match_citations(citation)

        #Ambiguous entry --------
        citation = CitationMatcherEntry(journal='Bioinformatics',year=2015,volume=31)
        match = api.match_citations(citation)

        #Invalid Journal --------
        citation = CitationMatcherEntry(journal='Bioinfo',year=2015,volume=31)
        match = api.match_citations(citation)

        #Missing Journal - Ambiguous --------
        citation = CitationMatcherEntry(year=2015,volume=31,page1=3897)
        match = api.match_citations(citation)


        citation = CitationMatcherEntry(author='RA Gaunt',year=2017)
        match = api.match_citations(citation)


        Returns
        -------
        models.CitationMatchResult - a list of entries is returned if the input 
        to this function is a list
        """

        if citation_entries is list:
            is_single = False
        else:
            is_single = True
            citation_entries = [citation_entries]

        #"key_{:03d}".format(i)
        temp_strings = [x.get_serialized("key_{:03d}".format(i)) for i,x in enumerate(citation_entries)]
        query = '\n'.join(temp_strings)
        query_lengths = [len(x) for x in temp_strings]
        
        params = {'db':'pubmed','retmode':'xml','bdata':query}
        
        data_for_response = {
            'query_lengths':query_lengths,
            'entries':citation_entries,
            'is_single':is_single}
        
        url = self._BASE_URL + 'ecitmatch.cgi'        
        
        return self._make_request('POST',url,
                                  models.citation_match_parser,
                                  params,
                                  data_for_response=data_for_response)



class Authentication(object):

    """
    TODO: Link to authentication in docs
    """

    __slots__ = ['email','tool','api_key','rate','last_request_time']

    email : Optional[str]
    tool : Optional[str]
    api_key : Optional[str]
    rate : int
    last_request_time : float


    def __init__(self,email,tool,api_key,rate):


        self.email = email
        self.tool = tool
        self.api_key = api_key

        #I'm putting these two in here for now :/
        self.rate = rate
        self.last_request_time = 0.0

        if self.email is None:
            if config.email is not None:
                self.email = config.email
                self.tool = config.tool

        if self.api_key is None:
            if config.api_key is not None:
                self.api_key = config.api_key

        # https://www.ncbi.nlm.nih.gov/books/NBK25497/#_chapter2_Usage_Guidelines_and_Requiremen_
        if self.rate is None:
            if self.api_key is not None:
                self.rate = 10
            else:
                self.rate = 3

    def add_auth(self,params,key_ok):
        # Authentication
        # -------------------------------------------------
        if key_ok and self.api_key is not None:
            params['api_key'] = self.api_key
        elif self.email is not None:
            params['email'] = self.email
            params['tool'] = self.tool

        return params

    def limit_rate(self):
        dt = time.monotonic() - self.last_request_time
        min_dt = 1/self.rate
        if dt < min_dt:
            wait_time = min_dt-dt
            time.sleep(wait_time)
        self.last_request_time = time.monotonic()

    def __repr__(self):
        return display_class(self,
                         ['email', quotes(self.email),
                          'tool', quotes(self.tool),
                          'api_key', quotes(self.api_key),
                          'rate', self.rate])

class QueryLogger(object):

    __slots__ = ['method','url','params','response','prepped_params',
                 'request_duration','parse_time','next_index','request_count']

    def __init__(self):
        self.request_count = 0
        self.next_index = 0
        self.parse_time = [0 for x in range(5)]
        self.request_duration = [0 for x in range(5)]

    def log_query(self,method,url,params,response,elapsed_time):
        self.request_count += 1
        self.method = method
        self.url = url
        self.params = params
        self.response = response
        self.request_duration[self.next_index] = elapsed_time

        if method == 'POST':
            self.prepped_params = response.request.body
        else:
            partial_url = response.request.path_url
            r = re.search('\?', partial_url)
            self.prepped_params = partial_url[r.start()+1:]

    def log_parse_time(self,elapsed_time):
        #
        self.parse_time[self.next_index] = elapsed_time

        #Could simplify ...
        self.next_index += 1
        if self.next_index == len(self.request_duration):
            self.next_index = 0


    def __repr__(self):
        return display_class(self,
                         ['method', quotes(self.method),
                          'url', quotes(td(self.url)),
                          'params',td(str(self.params)),
                          'response', cld(self.response),
                          'prepped_params', td(self.prepped_params),
                          'request_duration',self.request_duration,
                          'parse_time',self.parse_time])
                
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

        id_param = _get_id_str(pmids)

        params = {'dbfrom':'pubmed',
                  'db':'pmc',
                  'id':id_param,
                  'retmode':'json'}
        return self._make_link_request(params,models.PMIDToPMCLinkSets,data_for_response=data_for_response)
    


    def __repr__(self):
        pv = ['pmid_to_pmc','Given a PMID, get a PMCID',
              'db_list','Return a list of available databases']
        return utils.property_values_to_string(pv)

def _get_id_str(id_or_ids):

    if isinstance(id_or_ids, list):
        if isinstance(id_or_ids[0], int):
            str_list = [str(x) for x in id_or_ids]
        else:
            str_list = id_or_ids

        id_param = ','.join(str_list)
    else:
        if isinstance(id_or_ids, int):
            id_param = str(id_or_ids)
        else:
            id_param = id_or_ids

    return id_param