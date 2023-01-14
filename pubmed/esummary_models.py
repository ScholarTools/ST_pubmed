"""
The ESummary is very generic ...

<Item Name="NlmUniqueID" Type="String">8303326</Item>
	<Item Name="ISSN" Type="String">0733-2467</Item>
	<Item Name="ESSN" Type="String">1520-6777</Item>
	<Item Name="PubTypeList" Type="List">
		<Item Name="PubType" Type="String">Journal Article</Item>
	</Item>
	<Item Name="RecordStatus" Type="String">PubMed - as supplied by publisher</Item>
	<Item Name="PubStatus" Type="String">aheadofprint</Item>
	<Item Name="ArticleIds" Type="List">
		<Item Name="pubmed" Type="String">32022941</Item>
		<Item Name="doi" Type="String">10.1002/nau.24300</Item>
		<Item Name="rid" Type="String">32022941</Item>
		<Item Name="eid" Type="String">32022941</Item>
	</Item>


"""
#Standard Imports
#-----------
import re
import pprint
import inspect
from typing import Union, List, Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .api import CitationMatcherEntry
    from .api import API
    from requests import Response
    
    
from datetime import datetime

#Third Party Imports
#------------------------------
#from lxml import objectify
from bs4.element import Tag

# Local Imports
#------------------------------
from .utils import quotes, display_class
from .utils import get_truncated_display_string as td
from .utils import get_list_class_display as cld
from .utils import property_values_to_string as pv

from .model_helpers import _make_soup, XMLInfo, _list_cld_or_empty, _get_opt_list
from .model_helpers import _get_opt_soup_string, _get_opt_attr_value, _get_opt_class
from .model_helpers import _get_opt_soup_int

class PubmedSummaryResult(object):
    
    """
    type : 'esummary'
    version : '0.3'
    """


    def __init__(self, api: 'API', response: 'Response'):

        #TODO: in the result, each entry is a key
        #??? What if there is only 1, is this still the case

        data = response.json()
        headers = data['header']
        result = data['result']
        
        self.raw = data
        
        self.type = headers['type']
        self.version = headers['version']
        self.ids = result['uids']
        self.docs = [PubmedSummary(result[x]) for x in self.ids]
        #dict_keys(['uids', '25186301', '23467867'])
        
    def __repr__(self):
        return display_class(self,
              ['raw','<raw JSON dict>',
               'type',self.type,
               'version',self.version,
               'ids',td(self.ids),
               'docs',cld(self.docs)])
        

class PubmedSummary(object):
    
    """
    TODO: Where is the DTD for this?
    
    Found optional thus far:
        - publisher_location
    """

    def __init__(self,data):
        self.raw = data
        self.article_ids = [PubmedArticleID(x) for x in data['articleids']]
        self.attributes = data['attributes']
        self.authors = [PubmedAuthor(x) for x in data['authors']]
        self.available_from_url = data['availablefromurl']
        self.book_name = data['bookname']
        self.book_title = data['booktitle']
        self.chapter = data['chapter']
        #??? What is this, empty in my example
        self.doc_contrib_list = data['doccontriblist']
        self.doc_date = data['docdate']
        self.doc_type = data['doctype']
        self.edition = data['edition']
        self.elocation_id = data['elocationid']
        self.epub_date = data['epubdate']
        self.essn = data['essn']
        self.full_journal_name = data['fulljournalname']
        self.history = data['history']
        self.issn = data['issn']
        self.issue = data['issue']
        self.lang = data['lang']
        #self.last_author = data['lastauthor']
        self.location_label = data['locationlabel']
        self.medium = data['medium']
        self.nlm_unique_id = data['nlmuniqueid']
        #Why are the pages not set???
        #epub ahead of print ...
        self.pages = data['pages']
        self.pmc_ref_count = data['pmcrefcount']
        
        #TODO: Format???
        self.pub_date = data['pubdate']
        
        
        self.publisher_location = data.get('publisher_location')

        #empty how no publisher?
        self.publisher_name = data['publishername']

        #'10' => what does this mean?
        self.pub_status = data['pubstatus']

        #List[str] 'pubtype': ['Journal Article'],
        self.pub_type = data['pubtype']
        self.record_status = data['recordstatus']
        self.references = data['references']
        self.report_number = data['reportnumber']

        #NYI
        #'sortfirstauthor': 'Gammie A',
        #'sortpubdate': '2020/02/05 00:00',
        #'sorttitle': 'what developments are needed to achieve less '
        #'invasive urodynamics ici rs 2019',

        self.sort_first_author = data['sortfirstauthor']
        #This is a nice date - TODO: Parse into datetime
        #'2014/11/01 00:00'
        temp_date = data['sortpubdate']
        self.sort_pub_date = datetime.strptime(temp_date,'%Y/%m/%d %H:%M')
        self.sorttitle = data['sorttitle']

        #'source': 'Neurourol Urodyn',
        self.source = data['source']
        self.src_contrib_list = data['srccontriblist']
        self.srcdate = data['srcdate']
        self.title = data['title']
        self.uid = data['uid']
        self.vernaculartitle = data['vernaculartitle']
        self.volume = data['volume']
        
        #TODO: Get attributes and display in loop
        

class PubmedAuthor(object):

    def __init__(self,data):
        self.raw = data
        self.type = data['authtype']
        self.cluster_id = data['clusterid']
        self.name = data['name']
        temp = self.name.split(" ")
        self.last = " ".join(temp[0:-1])
        #self.last = self.name.split(" ")[0]
        
    def __repr__(self):
        return display_class(self,
              ['type',self.type,
               'cluster_id',self.cluster_id,
               'name',self.name,
               'last',self.last])

class PubmedArticleID(object):

    def __init__(self,data):

        self.raw = data
        self.id_type = data['idtype']
        self.enumerated_id_type = data['idtypen']
        self.value = data['value']
        
        
    def __repr__(self):
        return display_class(self,
              ['id_type',self.id_type,
               'enumerated_id_type',self.enumerated_id_type,
               'value',self.value])    

    """
    {'articleids': [{'idtype': 'pubmed',
                              'idtypen': 1,
                              'value': '32022941'},
                             {'idtype': 'doi',
                              'idtypen': 3,
                              'value': '10.1002/nau.24300'},
                             {'idtype': 'rid',
                              'idtypen': 8,
                              'value': '32022941'},
                             {'idtype': 'eid',
                              'idtypen': 8,
                              'value': '32022941'}],
    
    """
