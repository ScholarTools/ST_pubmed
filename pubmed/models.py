# -*- coding: utf-8 -*-
"""
TODO: Do we need the XMLResponseObject????? - get rid of this if not and update
     the requirements
"""

#Standard Imports
#-----------
import re
import pprint
import shlex
import inspect
from typing import Union, List, Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .api import CitationMatcherEntry
    from .api import API


#Third Party Imports
#------------------------------
#from lxml import objectify
from bs4 import BeautifulSoup
from bs4.element import Tag

# Local Imports
from . import utils
quotes = utils.quotes
display_class = utils.display_class
td = utils.get_truncated_display_string
cld = utils.get_list_class_display
pv = utils.property_values_to_string

#---- Common
#====================================
def pass_through(api,json):
    #This can be used to just pass the raw result back to the user
    #Mostly for debugging ...
    return json

    
class PrettyDict(dict):

    """
    This was for making a dictionary print pretty by default.

    """
    def __repr__(self):
        return '%s' % pprint.pformat(dict(self))


class XMLResponseObject(object):
    # I made this a property so that the user could change this processing
    # if they wanted. For example, this would allow the user to return authors
    # as just the raw json (from a document) rather than creating a list of
    # Persons
    object_fields = {}

    # Name mapping, keys are new, values are old
    renamed_fields = {}

    fields = []

    def __init__(self, xml):
        """
        This class stores the raw JSON in case an attribute from this instance
        is requested. The attribute is accessed via the __getattr__ method.

        This design was chosen instead of one which tranfers each JSON object
        key into an attribute. This design decision means that we don't spend
        time populating an object where we only want a single attribute.

        Note that the request methods should also support returning the raw JSON.
        """

        # TODO: Check count, ensure unique values
        # self.xml_dict = {x.tag:x for x in xml}
        self.xml = xml

    def __getattr__(self, name):

        """
        By checking for the name in the list of fields, we allow returning
        a "None" value for attributes that are not present in the JSON. By
        forcing each class to define the fields that are valid we ensure that
        spelling errors don't return none:
        e.g. document.yeear <= instead of document.year
        """

        # TODO: We need to support renaming
        # i.e.
        if name in self.fields:
            new_name = name
        elif name in self.renamed_fields:
            new_name = name  # Do we want to do object lookup on the new name?
            name = self.renamed_fields[name]
        else:
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))

        value = self.json.get(name)

        # We don't call object construction methods on None values
        if value is None:
            return None
        elif new_name in self.object_fields:
            # Here we return the value after passing it to a method
            # fh => function handle
            #
            # Only the value is explicitly passed in
            # Any other information needs to be explicitly bound
            # to the method
            method_fh = self.object_fields[new_name]
            return method_fh(value)
        else:
            return value

    @classmethod
    def __dir__(cls):
        d = set(dir(cls) + cls.fields())
        d.remove('fields')
        d.remove('object_fields')

        return sorted(d)

    @classmethod
    def fields(cls):
        """
        This should be overloaded by the subclass.
        """
        return []


class ResponseObject(object):
    # I made this a property so that the user could change this processing
    # if they wanted. For example, this would allow the user to return authors
    # as just the raw json (from a document) rather than creating a list of
    # Persons
    object_fields = {}
    
    # Name mapping, keys are new, values are old
    renamed_fields = {}
    
    fields = []

    def __init__(self, json):
        """
        This class stores the raw JSON in case an attribute from this instance
        is requested. The attribute is accessed via the __getattr__ method.

        This design was chosen instead of one which tranfers each JSON object
        key into an attribute. This design decision means that we don't spend
        time populating an object where we only want a single attribute.
        
        Note that the request methods should also support returning the raw JSON.
        """
        
        # TODO: Check count, ensure unique values
        # self.xml_dict = {x.tag:x for x in xml}
        self.json = json
        
    def __getattr__(self, name):

        """
        By checking for the name in the list of fields, we allow returning
        a "None" value for attributes that are not present in the JSON. By
        forcing each class to define the fields that are valid we ensure that
        spelling errors don't return none:
        e.g. document.yeear <= instead of document.year
        """
        
        # TODO: We need to support renaming
        # i.e.
        if name in self.fields:
            new_name = name
        elif name in self.renamed_fields:
            new_name = name  # Do we want to do object lookup on the new name?
            name = self.renamed_fields[name]
        else:
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))
          
        value = self.json.get(name)        
          
        # We don't call object construction methods on None values
        if value is None:
            return None
        elif new_name in self.object_fields:
            # Here we return the value after passing it to a method
            # fh => function handle
            #
            # Only the value is explicitly passed in
            # Any other information needs to be explicitly bound
            # to the method
            method_fh = self.object_fields[new_name]
            return method_fh(value)
        else:
            return value

    @classmethod
    def __dir__(cls):
        d = set(dir(cls) + cls.fields)
        d.remove('fields')
        d.remove('object_fields')

        return sorted(d)

    def fields(self):
        """
        This should be overloaded by the subclass.
        """
        return self.json.keys()


#==============================================================================
#==============================================================================


class CitationMatchResult(object):

    entry : 'CitationMatcherEntry'

    """
    See Also
    --------
    pubmed.api.CitationMatcherEntry
    pubmed.api.API.match_citations
    """

    def __init__(self, api:'API', raw_text:str, entry:'CitationMatcherEntry'):
        """

        Paramaters
        ----------

        :param response_text:
        :param entry:
        """

        #Initial logging
        #------------------------
        self.api
        self.entry = entry
        self.raw = raw_text

        #Example raw_text:
        #|2017|||Gaunt RA|key_000|AMBIGUOUS 29209023,28489913
        temp = raw_text.rsplit('|',1)
        #Note, I had originally been tracking the request length, but I found
        #out that the response doesn't always match what I sent, specifically
        #I sent out 'RA Gaunt' and got back nothing
        self.interpreted_request = temp[0]
        response_text = temp[1]
        self.response_text = response_text

        #defaults ...
        self.n_possible_matches = 0
        self.id = None
        self.is_ambiguous = False
        self.not_found = False
        self.invalid_journal = False
        self.possible_ids = None

        #Found?
        #--------------------------------------------
        #only thing returned will be PMID
        self.found = response_text[0].isdigit()
        if self.found:
            self.n_possible_matches = 1
            self.id = self.raw
            return

        #Ambiguous
        #----------------------------------------------
        self.is_ambiguous = len(response_text) > 8 and response_text[0:9] == 'AMBIGUOUS'
        if self.is_ambiguous:
            temp = re.search('(\d+) citations',response_text)
            if temp:
                self.n_possible_matches = int(temp.groups()[0])
            else:
                temp = response_text[10:].split(',')
                self.n_possible_matches = len(temp)
                self.possible_ids = temp
                #AMBIGUOUS 26315901, 25768914
                #AMBIGUOUS 30444217,30429772,30166583
                #??? What about 4?
                #AMBIGUOUS(5 citations)

            return


        #-----------------------------------------------
        self.not_found = len(response_text) > 8 and response_text[0:9] == 'NOT_FOUND'
        if self.not_found:
            self.invalid_journal = re.search('INVALID_JOURNAL',response_text) and True

    # EXAMPLE RESPONSES
    # - '26315901'
    # - 'NOT_FOUND;INVALID_JOURNAL'
    # - 'AMBIGUOUS (783 citations)'
    # - 'AMBIGUOUS 26315901,25768914
    # - 'NOT_FOUND'

    def fix_errors(self):
        raise Exception("Not yet implemented")
        # Could try and resolve a journal
        pass

    def get_possible_matches(self):
        pass

    def __repr__(self):
        return display_class(self,
                             [  'entry',cld(self.entry),
                                'raw', self.raw,
                                'interpreted_request',self.interpreted_request,
                                'response_text',self.response_text,
                                'found', self.found,
                                'is_ambiguous',self.is_ambiguous,
                                'n_possible_matches',self.n_possible_matches,
                                'possible_ids',self.possible_ids,
                                'not_found',self.not_found,
                                'invalid_journal',self.invalid_journal,
                                'id',self.id])

def citation_match_parser(api, response_text, data_for_response):

    """
        :param api: Instance of the API (not currently used)
        :type api: API
        :param response_text:
        :param data_for_response:



        :return: Union[CitationMatchResult,List[CitationMatchResult]]
    """

    #api : 'API'
    #response_text : str
    #data_for_response : dict

    d = data_for_response

    output = []
    lines = response_text.splitlines()  # split('\n')
    for line_text, cur_entry in zip(lines, d['entries']):
        output.append(CitationMatchResult(api, line_text, cur_entry))
        
    if d['is_single']:
        return output[0]
    else:
        return output


#==============================================================================
#==============================================================================

#==============================================================================
#==============================================================================

class SummaryResult(object):
    
    """
    Response class for summary()
    """

    def __init__(self,api,data):

        #self.api = api
        
        self.raw = data
        #An error may yield:
        #   - esummaryresult
        self.result = data.get('result')
        if self.result is not None:
            #Result contains the following fields:
            #1) 'uids'
            #2) fields that are the uids
            self.ids = self.result.get('uids')
            self.docs = [self.result[x] for x in self.ids]
        else:
            self.ids = None
            self.docs = None

    #TODO: We could add a followup method that gets more detail ...

    def pprint_doc(self,index):
        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint(self.docs[index])

    def __repr__(self):
        return display_class(self,
                ['raw', td(str(self.raw)),
                 'result', td(str(self.result)),
                 'ids', td(str(self.ids)),
                 'docs', cld(self.docs),
                 'pprint_doc(index)','pretty print specified doc'])


#TODO: Have a lazy document set as well ...
class PubmedArticleSet(object):
    """

    For: doc_info

    See Also
    --------
    pubmed.api.API.fetch
    """
    
    def __init__(self, api, data):


        soup = _make_soup(data)

        doctype = soup.contents[1]

        parts = shlex.split(doctype)
        #1) PubmedArticleSet
        #2) PUBLIC
        #3)

        self.doc_type = parts[0]
        if self.doc_type != 'PubmedArticleSet':
            raise Exception('Unexpected document type')

        self.dtd_name = parts[2]
        self.dtd_url = parts[3]



        # Hierarchy:
        # ----------
        # pubmedarticleset
        #   - pubmedarticle
        #I don't know if we need to do this, might
        #be better to iterate over contents of the article set

        #articles = soup.find_all('pubmedarticle')

        pub_article_set = soup.contents[2]
        #TODO: DTD says PubmedArticleSet ((PubmedArticle | PubmedBookArticle)+, DeleteCitation?) >
        #   Book and Delete not handled ...
        self.docs = [PubmedArticle(x) for x in pub_article_set.contents]



    def __repr__(self):
        return display_class(self,
                             [
                            'docs','[<PubmedEntry>]'])


        # Retrieves child tags and ignores navigable strings (in these examples the strings are newlines)
        # children = articles[0].find_all(True, recursive=False)






#TODO: Allow a lazy object in addition to full object instantiation

class PubDate(object):

    __slots__ = ['year', 'month', 'day', 'season', 'date']

    def __init__(self,date_tag):
        #<!ELEMENT PubDate((Year, ((Month, Day?) | Season)?) | MedlineDate) >
        #<!ELEMENT MedlineDate (#PCDATA) >


        self.year = date_tag.year.string
        self.month = _get_opt_soup_string(date_tag,'month')
        self.day = _get_opt_soup_string(date_tag,'day')
        self.season = _get_opt_soup_string(date_tag,'season')
        self.date = _get_opt_soup_string(date_tag,'medlinedate')

    def __repr__(self):
        return display_class(self,
                                 ['year',quotes(self.year),
                                  'month', quotes(self.month),
                                  'day', quotes(self.day),
                                  'season', quotes(self.season),
                                  'date', quotes(self.date)])

class JournalIssue(object):

    __slots__ = ['volume','issue','pub_date','cited_medium']

    def __init__(self,journal_issue_tag):
        # <!ELEMENT	JournalIssue (Volume?, Issue?, PubDate) >
        # <!ATTLIST	JournalIssue
        #       CitedMedium (Internet | Print) #REQUIRED >

        self.volume = _get_opt_soup_string(journal_issue_tag,'volume')
        self.issue = _get_opt_soup_string(journal_issue_tag,'issue')
        self.pub_date = PubDate(journal_issue_tag.pubdate)
        self.cited_medium = journal_issue_tag['citedmedium']

    def __repr__(self):
        return display_class(self,
                                 ['volume',quotes(self.volume),
                                  'issue', quotes(self.issue),
                                  'pub_date', cld(self.pub_date),
                                  'cited_medium', quotes(self.cited_medium)])

class Journal(object):

    __slots__ = ['electronic_issn', 'print_issn', 'issue','title','iso_abbreviation']
    electronic_issn : Optional[str]
    print_issn : Optional[str]


    def __init__(self,journal_tag):
        # <!ELEMENT	Journal (ISSN?, JournalIssue, Title?, ISOAbbreviation?)>

        #ISSN?
        #----------------------
        #<!ELEMENT ISSN(  # PCDATA) >
        #<!ATTLIST ISSN
        #           IssnType(Electronic | Print)  # REQUIRED >

        # ?? Will we ever have more than 2 issn values?
        self.electronic_issn = None
        self.print_issn = None
        issn_values = journal_tag.find_all('issn',recursive=True)
        for issn in issn_values:
            if issn['issntype'] == 'Electronic':
                self.electronic_issn = issn.string
            elif issn['issntype'] == 'Print':
                self.print_issn = issn.string
            else:
                raise Exception('Unhandled issn type')

        self.issue = JournalIssue(journal_tag.journalissue)

        #   - Title, ISOAbbreviation
        # -----------------------------
        self.title = _get_opt_soup_string(journal_tag, 'title')
        self.iso_abbreviation = _get_opt_soup_string(journal_tag, 'isoabbreviation')

    def __repr__(self):
        return display_class(self,
                                 ['electronic_issn',quotes(self.electronic_issn),
                                'print_issn',quotes(self.print_issn),
                                'issue',cld(self.issue),
                                  'title',quotes(self.title),
                                  'iso_abbreviation',quotes(self.iso_abbreviation)])

class Pagination(object):

    __slots__ = ['start_page','end_page','medline_pgn']

    def __init__(self,page_tag):
        # <!ELEMENT	Pagination ((StartPage, EndPage?, MedlinePgn?) | MedlinePgn) >
        # <!ELEMENT	MedlinePgn (#PCDATA) >

        self.start_page = page_tag.string
        self.end_page = _get_opt_soup_string(page_tag,'endpage')
        self.medline_pgn = _get_opt_soup_string(page_tag,'medlinepgn')

    def __repr__(self):
        return display_class(self,
                                 ['start_page',self.start_page,
                                'end_page',self.end_page,
                                'medline_pgn',self.medline_pgn])

#TODO:
#- Grants
#- Pub_Types
#- Dates (for Article)

class Identifier(object):

    __slots__ = ['source', 'value']

    def __init__(self,tag):
        # <!ELEMENT Identifier(  # PCDATA) >
        # <!ATTLIST Identifier
        #           Source CDATA  # REQUIRED >

        self.source = tag['source']
        self.value = tag.string

    def __repr__(self):
        return display_class(self,
                             ['source', self.source,
                              'value', self.value])

class AffiliationInfo(object):

    __slots__ = ['value','identifiers']

    def __init__(self,tag):
        # <!ELEMENT Affiliation( % text;) * >
        # <!ELEMENT AffiliationInfo(Affiliation, Identifier *) >

        self.value = tag.affiliation.string
        self.identifiers = _get_opt_list(tag,'identifier',Identifier)

    def __repr__(self):
        return display_class(self,
                             ['value', td(self.value),
                              'identifiers', _list_cld_or_empty(self.identifiers)])


class Author(object):
    __slots__ = ['last_name','fore_name','initials','suffix','collective_name',
                 'identifiers','affiliations','is_valid','equal_contrib']

    def __init__(self,author_tag):
        # https://www.nlm.nih.gov/bsd/licensee/elements_descriptions.html#authorlist
        # <!ELEMENT AuthorList(Author +) >
        # <!ATTLIST AuthorList
        #       CompleteYN (Y | N) "Y"
        #       Type(authors | editors)  # IMPLIED >
        #
        # <!ELEMENT Author(((LastName, ForeName?, Initials?, Suffix?) | CollectiveName), Identifier *, AffiliationInfo *) >
        # <!ATTLIST Author
        #       ValidYN(Y | N) "Y"
        #       EqualContrib(Y | N)  # IMPLIED >
        #
        # <!ELEMENT	CollectiveName (%text;)*>




        """
        author = {
            'last_name': None,
            'fore_name': None,
            'initials': None,
            'suffix': None,
            'collective_name': None,
            'identifiers': None,
            'affiliations': None
        }
        """

        self.is_valid = _get_opt_attr_value(author_tag, 'validyn',
                                            default='Y') == 'Y'
        self.equal_contrib = _get_opt_attr_value(author_tag,
                                                 'equalcontrib',
                                                 default='N') == 'Y'

        last_name_tag = author_tag.lastname
        if last_name_tag is None:
            self.collective_name = author_tag.collectivename.string
            self.last_name = None
            self.fore_name = None
            self.initials = None
            self.suffix = None
        else:
            self.collective_name = None
            self.last_name = last_name_tag.string
            self.fore_name = _get_opt_soup_string(author_tag,'forename')
            self.initials = _get_opt_soup_string(author_tag, 'initials')
            self.suffix = _get_opt_soup_string(author_tag, 'suffix')

        # Identifier *
        # -----------------------------------------------
        self.identifiers = _get_opt_list(author_tag,'identifier',Identifier)

        #AffiliationInfo *
        #-----------------------------------------------
        self.affiliations = _get_opt_list(author_tag,'affiliationinfo',AffiliationInfo)

    def __repr__(self):
        return display_class(self,
                             ['collective_name', self.collective_name,
                              'last_name',self.last_name,
                              'fore_name',self.fore_name,
                              'initials',self.initials,
                              'suffix',self.suffix,
                              'identifiers', _list_cld_or_empty(self.identifiers),
                              'affiliations', _list_cld_or_empty(self.affiliations)])

class ArticleDate(object):

    __slots__ = ['year','month','day']

    def __init__(self,tag):
        #<!ELEMENT ArticleDate(Year, Month, Day) >
        #<!ATTLIST ArticleDate
        #   DateType CDATA  #FIXED "Electronic" >

        self.year = tag.year.string
        self.month = tag.month.string
        self.day = tag.day.string

    def __repr__(self):
        return display_class(self,
                             ['year',self.year,
                              'month',self.month,
                              'day',self.day])

class Grant(object):

    __slots__ = ['grant_id','acronym','agency','country']

    def __init__(self,tag):
        #<!ELEMENT Grant(GrantID?, Acronym?, Agency, Country) >
        #<!ELEMENT GrantID(#PCDATA) >
        #<!ELEMENT Acronym(#PCDATA) >
        #<!ELEMENT Agency(#PCDATA) >
        #<!ELEMENT Country(#PCDATA) >

       self.grant_id = _get_opt_soup_string(tag,'grantid')
       self.acronym = _get_opt_soup_string(tag,'acronym')
       self.agency = tag.agency.string
       self.country = tag.country.string

    def __repr__(self):
        return display_class(self,
                             ['grant_id',self.grant_id,
                              'acronym',self.acronym,
                              'agency',self.agency,
                              'country',self.country])

class DataBank(object):

    __slots__ = ['name','accession_numbers']

    def __init__(self,tag):
        # <!ELEMENT DataBank(DataBankName, AccessionNumberList?) >
        # <!ELEMENT DataBankName(#PCDATA) >
        # <!ELEMENT AccessionNumber(#PCDATA) >
        # <!ELEMENT AccessionNumberList(AccessionNumber +) >

        self.name = tag.databankname.string

        number_list_tag = tag.accessionnumberlist
        if number_list_tag is None:
            self.accession_numbers = None
        else:
            self.accession_numbers = [x.string for x in number_list_tag]

    def __repr__(self):
        return display_class(self,
                             ['name',self.name,
                              'accession_numbers',cld(self.accession_numbers)])

class PublicationType(object):

    __slots__ = ['ui','value']

    def __init__(self,tag):
        # <!ELEMENT PublicationType(  # PCDATA) >
        # <!ATTLIST PublicationType
        #           UI CDATA  # REQUIRED >


        self.ui = tag['ui']
        self.value = tag.string

    def __repr__(self):
        return display_class(self,
                             ['ui',self.ui,
                              'value',self.value])

class Article(object):

    __slots__ = ['abstract_copyright_info','abstracts','authors', 'databanks',
                 'dates','doi','grants','journal','languages','pagination','pii',
                 'pub_types','title','vernacular_title']

    """
    Called from MedlineCitation

    <!ELEMENT	Article (
                    X Journal,
                    X ArticleTitle,
                    X ((Pagination, ELocationID*) | ELocationID+),
                    X Abstract?,
                    X AuthorList?,
                    X Language+,
                    X DataBankList?,
                    X GrantList?,
                    X PublicationTypeList,
                    X VernacularTitle?,
                     ArticleDate*) >
    """

    def __init__(self, soup):

        self.journal = Journal(soup.journal)

        #ArticleTitle
        #-----------------------------------------------------
        #<!ELEMENT ArticleTitle( % text; | mml: math) * >
        #<!ATTLIST ArticleTitle % booklinkatts; >
        #<!ENTITY % text     "#PCDATA | b | i | sup | sub | u" >
        #<!ENTITY % booklinkatts
		#	 "book		CDATA			#IMPLIED
		#	  part		CDATA			#IMPLIED
		#	 sec		CDATA			#IMPLIED"  >
        self.title = soup.articletitle.string

        #((Pagination, ELocationID*) | ELocationID+)
        #--------------------------------------------
        self.pagination = _get_opt_class(soup,'pagination',Pagination)

        # <!ELEMENT	ELocationID (#PCDATA) >
        # <!ATTLIST	ELocationID
        #    EIdType (doi | pii) #REQUIRED
        #    ValidYN  (Y | N) "Y">

        self.doi = None
        self.pii = None
        elocation_ids = soup.find_all('elocationid',recursive=False)
        for elocation in elocation_ids:
            type = elocation['eidtype']
            #Note, I like having doi and pii as attributes
            #unfortunately we don't support logging these values
            #when they are invalid if we only record the value directly
            #
            #would need to add additional attributes ('is_valid_doi') or
            #make structure more complicated
            if _get_opt_attr_value(elocation,'validyn','Y') == 'Y':
                if type == 'doi':
                    self.doi = elocation.string
                elif type == 'pii':
                    self.pii = elocation.string

        #----------------------------------------------------------------------
        #                               Abstract?
        #----------------------------------------------------------------------
        #<!ELEMENT Abstract(AbstractText+, CopyrightInformation?) >
        #<!ELEMENT AbstractText( % text; | mml: math | DispFormula) * >
        #<!ATTLIST AbstractText
        #       Label CDATA  # IMPLIED
        #       NlmCategory(BACKGROUND | OBJECTIVE | METHODS | RESULTS | CONCLUSIONS | UNASSIGNED)  # IMPLIED >
        #
        #<!ELEMENT	CopyrightInformation (#PCDATA) >

        abstract_tag = soup.abstract

        self.abstract_copyright_info = None
        self.abstracts = None
        if abstract_tag is not None:
            abstract_text_tags = abstract_tag.find_all('abstracttext')
            self.abstracts = [x.string for x in abstract_text_tags]

            copy_tag = abstract_tag.copyrightinformation
            if copy_tag is not None:
                self.abstract_copyright_info = copy_tag.string


        #----------------------------------------------------------------------
        #                           AuthorList?
        #----------------------------------------------------------------------
        self.authors = _get_opt_list(soup.authorlist,'author',Author)

        #----------------------------------------------------------------------
        #                           Language+
        #----------------------------------------------------------------------
        #<!ELEMENT	Language (#PCDATA) >
        lang_tag = soup.find_all('language',recursive=False)
        self.languages = [x.string for x in lang_tag]

        #----------------------------------------------------------------------
        #                           DataBankList?
        #----------------------------------------------------------------------
        #<!ELEMENT DataBankList(DataBank+)>
        #<!ATTLIST DataBankList
        #   CompleteYN(Y | N) "Y" >

        self.databanks = _get_opt_list(soup.databanklist,'databank',DataBank)

        #----------------------------------------------------------------------
        #                           GrantList?
        #----------------------------------------------------------------------
        #<!ELEMENT GrantList(Grant+) >
        #<!ATTLIST GrantList
        #       CompleteYN(Y | N) "Y" >
        self.grants = _get_opt_list(soup.grantlist,'grant',Grant)

        #----------------------------------------------------------------------
        #                           PublicationTypeList
        #----------------------------------------------------------------------
        #<!ELEMENT PublicationTypeList (PublicationType+) >
        self.pub_types = _get_opt_list(soup.publicationtypelist,'publicationtype',PublicationType)

        #----------------------------------------------------------------------
        #                           VernacularTitle?
        #----------------------------------------------------------------------
        #< !ELEMENT VernacularTitle( % text; | mml: math) * >
        self.vernacular_title = _get_opt_soup_string(soup,'vernaculartitle')

        #----------------------------------------------------------------------
        #                           ArticleDate*
        #----------------------------------------------------------------------
        self.dates = _get_opt_list(soup,'articledate',ArticleDate)

    def __repr__(self):
        return display_class(self,
                                 ['journal',cld(self.journal),
                                  'title',quotes(td(self.title)),
                                  'abstract_copyright_info',td(self.abstract_copyright_info),
                                  'abstracts',cld(self.abstracts),
                                  'pagination',cld(self.pagination),
                                  'doi',self.doi,
                                  'pii',self.pii,
                                  'authors',_list_cld_or_empty(self.authors),
                                  'languages',td(self.languages),
                                  'databanks',_list_cld_or_empty(self.databanks),
                                  'vernacular_title',quotes(td(self.vernacular_title)),
                                  'pub_types',cld(self.pub_types),
                                  'grants',_list_cld_or_empty(self.grants),
                                  'dates',_list_cld_or_empty(self.dates)])

class PubmedArticle(object):

    __slots__ = ['soup','citation','pubmed_data']

    citation: 'MedlineCitation'
    pubmed_data: Optional['PubmedData']

    def __init__(self,soup):
        #<!ELEMENT	PubmedArticle (MedlineCitation, PubmedData?)>
        #<!ATTLIST  PubmedArticle

        #For debugging ...
        self.soup = soup

        self.citation = MedlineCitation(soup.medlinecitation)
        pubmed_data = soup.pubmeddata
        if pubmed_data is None:
            self.pubmed_data = None
        else:
            self.pubmed_data = PubmedData(pubmed_data)

    def __repr__(self):
        return display_class(self,
                             ['citation', cld(self.citation),
                              'pubmed_data', cld(self.pubmed_data)])

class PubmedPubDate(object):

    __slots__ = ['year','month','day','hour','minute','second','status']

    def __init__(self,tag):
        #<!ELEMENT PubMedPubDate(Year, Month, Day, (Hour, (Minute, Second?)?)?) >
        #<!ATTLIST PubMedPubDate
        #   PubStatus(received | accepted | epublish |
        #          ppublish | revised | aheadofprint |
        #          retracted | ecollection | pmc | pmcr | pubmed | pubmedr |
        #          premedline | medline | medliner | entrez | pmc - release)  # REQUIRED >

        #Called by PubmedData as part of the doc's history

        #TODO: Consider a date display

        self.year = tag.year.string
        self.month = tag.month.string
        self.day = tag.day.string
        self.hour = _get_opt_soup_string(tag,'hour')
        self.minute = _get_opt_soup_string(tag, 'minute')
        self.second = _get_opt_soup_string(tag, 'second')
        self.status = tag['pubstatus']

    def __repr__(self):
        return display_class(self,
                             ['year', self.year,
                              'month', self.month,
                              'day',self.day,
                              'hour',self.hour,
                              'minute',self.minute,
                              'second',self.second,
                              'status',self.status])

class ReferenceList(object):

    """
    https://www.ncbi.nlm.nih.gov/books/NBK3828/
    "How do I submit reference lists? We encourage publishers to include
    reference lists using the <ReferenceList> element. There can be multiple
    references lists and the lists can be nested. This structure
    accommodates reference lists with distinctly labeled sections (for
    example, references to articles cited followed by references to
    datasets). The XML tagging should reflect the way that the reference
    list is presented in the published journal article.

    The other tags used are <Title>, <Reference>, <Citation>, <PMID>,
    and <ArticleIdList>.

    Each parent or child reference list can include an optional title. The
    reference itself is comprised of either a citation string, or a PMID for
    a citation in PubMed. We recommend including any article identifiers
    associated with the cited item."

    """

    __slots__ = ['title','references','ref_lists']

    title : Optional['str']
    references : Optional[List['Reference']]
    ref_lists : Optional[List['ReferenceList']]

    """
    Note, unlike most other lists this has multiple potential properties
    """
    def __init__(self,tag):
        #< !ELEMENT ReferenceList(Title?, Reference *, ReferenceList *) >
        #<!ELEMENT	Citation       (%text; | mml:math)*>
        #<!ELEMENT	Title (#PCDATA) >
        self.title = _get_opt_soup_string(tag,'title')
        self.references = _get_opt_list(tag,'reference',Reference)
        self.ref_lists = _get_opt_list(tag,'referencelist',ReferenceList)

    def __repr__(self):
        return display_class(self,
                             ['title', self.title,
                              'references', _list_cld_or_empty(self.references),
                              'ref_lists',_list_cld_or_empty(self.ref_lists)])

class ArticleID(object):

    __slots__ = ['value','type']

    value : str
    type : str

    def __init__(self,tag):
        #<!ELEMENT	ArticleId (#PCDATA) >
        #<!ATTLIST   ArticleId
	    #    IdType (doi | pii | pmcpid | pmpid | pmc | mid |
        #           sici | pubmed | medline | pmcid | pmcbook | bookaccession) "pubmed" >
        #<!ELEMENT	ArticleIdList (ArticleId+)>
        self.value = tag.string
        self.type = tag['idtype']

    def __repr__(self):
        return display_class(self,
                             ['value', self.value,
                              'type',self.type])

class Reference(object):

    __slots__ = ['citation','article_ids']

    citation : str
    article_ids : Optional[List[ArticleID]]

    def __init__(self,tag):
        #< !ELEMENT Reference(Citation, ArticleIdList?) >
        #<!ELEMENT	Citation       (%text; | mml:math)*>

        self.citation = tag.citation.string
        self.article_ids = _get_opt_list(tag.articleidlist,'articleid',ArticleID)

        #for id in self.article_ids:
        #    if id.type == 'pmid'
        #TODO: Support doi, and PMID pull outs


    def __repr__(self):
        return display_class(self,
                             ['citation', self.citation,
                              'article_ids',_list_cld_or_empty(self.article_ids)])


class PubmedData(object):

    __slots__ = ['history','publication_status','doi','pii','pmcpid',
                 'pmpid','pmc','mid','sici','pubmed','medline','pmcid','pmcbook',
                 'bookaccession','ref_lists']

    history : List[PubmedPubDate]
    publication_status : str
    doi : str
    pii : str
    pmcpid : str
    pmpid : str
    pmc : str
    mid : str
    pmcbook : str
    bookacession : str
    #TODO: ObjectList
    ref_lists : List[ReferenceList]

    """
    https://dtd.nlm.nih.gov/ncbi/pubmed/el-PubmedData.html
    "Contains additional metadata that is not otherwise captured in journal 
    article, i.e. <PubMedArticle>, citations. These elements typically include 
    details regarding the item's publication history, its processing at NLM, 
    its publication status, and any article identifiers supplied by the 
    publisher."
    
    Attributes
    ----------
    history : List[PubmedPubDate]
        Dates of modifications to the entries along with a type specifiying
        what modification was made like date received or accepted for 
        publication
    publication_status : str
        "Indicates the publication status of the article, 
        i.e. whether the article is a ppublish, epublcih, or ahead of print, 
        as determined by the article's primary publication date."
    doi : str
        Digital Objeect Identifier
        https://en.wikipedia.org/wiki/Digital_object_identifier
    pii : str
        Publisher identifier. Used by the publisher to track the article.
        https://en.wikipedia.org/wiki/Publisher_Item_Identifier
    pmcpid : str
        Publisher Id supplied to PubMed Central
    pmpid : str
        Publisher Id supplied to PubMed
    pmc : str
    mid : str
    pmcbook : str
    bookacession : str
    #TODO: ObjectList
    ref_lists : List[ReferenceList]
    
    """


    #TODO: Document these properties ...

    def __init__(self,tag):
        #<!ELEMENT	PubmedData (History?, PublicationStatus, ArticleIdList, ObjectList?, ReferenceList*) >

        #History?
        #----------------------------------------
        #<!ELEMENT	History (PubMedPubDate+) >
        self.history = _get_opt_list(tag.History,'PubmedPubDate',PubmedPubDate)

        #PublicationStatus
        #----------------------------------------
        #<!ELEMENT	PublicationStatus (#PCDATA) >
        self.publication_status = tag.PublicationStatus.string

        #ArticleIdList
        #------------------------------------------
        # <!ELEMENT	ArticleIdList (ArticleId+)>
        #<!ELEMENT	ArticleId (#PCDATA) >
        #<!ATTLIST   ArticleId
	    #    IdType (doi | pii | pmcpid | pmpid | pmc | mid |
        #           sici | pubmed | medline | pmcid | pmcbook | bookaccession) "pubmed" >

        self.doi = None
        self.pii = None #Controlled Publisher Identifier
        self.pmcpid = None #Publisher Id supplied to PubMed Central
        self.pmpid = None #Publisher Id supplied to PubMed
        self.pmc = None
        self.mid = None #medline ID?
        self.sici = None
        #https://jats.nlm.nih.gov/archiving/tag-library/1.1d1/n-dga2.html
        #Serial Item and Contribution Identifier (An ANSI/NISO Z39.56 code to
        #uniquely identify volumes, articles, or other parts of a periodical.
        #A journal article may have more than one SICI, for example, one for
        #a print version and another for an electronic version.)
        self.pubmed = None
        self.medline = None
        self.pmcid = None
        self.pmcbook = None
        self.bookaccession = None

        id_list = tag.articleidlist
        ids = id_list.find_all('ArticleId',recursive=False)
        for id in ids:
            type = _get_opt_attr_value(id,'IdType','pubmed')
            setattr(self,type,id.string)

        #ObjectList?
        #-------------------------
        # <!ELEMENT ObjectList(Object +) >
        #
        #<!ELEMENT Object(Param *) >
        #<!ATTLIST Object
        #       Type CDATA  # REQUIRED >
        #
        #
        #<!ELEMENT	Param  (%text;)*>
        #<!ATTLIST	Param
        #       Name CDATA #REQUIRED >
        object_list_tag = tag.objectlist
        if object_list_tag is not None:
            #TODO: Fix this ...
            import pdb
            pdb.set_trace()

        #ReferenceList*
        #--------------------------------------------------
        self.ref_lists = _get_opt_list(tag,'ReferenceList',ReferenceList)

    def __repr__(self):
        return display_class(self,
                             ['history', _list_cld_or_empty(self.history),
                              'publication_status', quotes(self.publication_status),
                              'ref_lists',_list_cld_or_empty(self.ref_lists),
                              'doi',quotes(self.doi),
                              'pii',quotes(self.pii),
                              'pmcpid',quotes(self.pmcpid),
                              'pmpid', quotes(self.pmpid),
                              'pmc', quotes(self.pmc),
                              'mid', quotes(self.mid),
                              'sici', quotes(self.sici),
                              'pubmed', quotes(self.pubmed),
                              'medline', quotes(self.medline),
                              'pmcid', quotes(self.pmcid),
                              'pmcbook', quotes(self.pmcbook),
                              'bookaccession', quotes(self.bookaccession)])

class DateCompleted(object):

    """
    """

    __slots__ = ['year','month','day']

    year : str
    month : str
    day : str

    def __init__(self,tag:Tag):
        #<!ELEMENT DateCompleted(Year, Month, Day) >
        self.year = tag.year.string
        self.month = tag.month.string
        self.day = tag.day.string

    def __repr__(self):
        return display_class(self,
                             ['Year', self.year,
                              'Month', self.month,
                              'Day',self.day])

class DateRevised(object):

    """
    """

    __slots__ = ['year', 'month', 'day']

    def __init__(self,tag:Tag):
        #<!ELEMENT DateRevised(Year, Month, Day) >
        self.year = tag.Year.string
        self.month = tag.Month.string
        self.day = tag.Day.string

    def __repr__(self):
        return display_class(self,
                             ['year', self.year,
                              'month', self.month,
                              'day',self.day])

class MedlineJournalInfo(object):

    """"
    "Contains additional journal metadata, supplmental to the metadata in the
    Journal wrapper element. Some elements are particular to NLM records, as
    developed for MEDLINE journals, e.g. NLM ID and MEDLINE TA."
    """

    def __init__(self,tag:Tag):
        #<!ELEMENT	MedlineJournalInfo (Country?, MedlineTA, NlmUniqueID?, ISSNLinking?) >
        #<!ELEMENT	Country (#PCDATA) >
        #<!ELEMENT	MedlineTA (#PCDATA) >
        #<!ELEMENT	NlmUniqueID (#PCDATA) >
        #<!ELEMENT	ISSNLinking (#PCDATA) >

        self.country = _get_opt_soup_string(tag,'Country')
        self.medline_ta = tag.MedlineTA.string
        """
        States the title abbreviation for the journal in which the article 
        appeared. These title abbreviations are designated by NLM. See <Title> 
        for the full journal title, or <ISOAbbreviation> for the standard ISO abbreviation.
        """

        self.nlm_unique_id = _get_opt_soup_string(tag,'NlmUniqueID')
        self.issn_linking = _get_opt_soup_string(tag,'ISSNLinking')

    def __repr__(self):
        return display_class(self,
                                 ['country', self.country,
                                  'medline_ta', self.medline_ta,
                                  'nlm_unique_id', self.nlm_unique_id,
                                  'issn_linking',self.issn_linking])


class Chemical(object):

    __slots__ = ['registry_number','substance_name','ui']

    """
    https://www.nlm.nih.gov/bsd/licensee/elements_descriptions.html#chemicallist
    """

    def __init__(self,tag:Tag):
        #<!ELEMENT Chemical(RegistryNumber, NameOfSubstance) >
        #<!ELEMENT ChemicalList(Chemical +) >
        #<!ELEMENT	RegistryNumber (#PCDATA) >
        #<!ELEMENT	NameOfSubstance (#PCDATA) >
        #<!ATTLIST	NameOfSubstance
		#    UI CDATA #REQUIRED >

        self.registry_number = tag.RegistryNumber.string
        self.substance_name = tag.NameOfSubstance.string
        self.ui = tag.NameOfSubstance['ui']

    def __repr__(self):
        return display_class(self,
                                 ['registry_number', quotes(self.registry_number),
                                  'substance_name', quotes(self.substance_name),
                                  'ui', quotes(self.ui)])

class SupplMeshName(object):

    __slots__ = ['type','ui','value']

    def __init__(self,tag:Tag):
        # <!ELEMENT	SupplMeshName (#PCDATA) >
        # <!ATTLIST	SupplMeshName
        #    Type (Disease | Protocol | Organism) #REQUIRED
        #    UI CDATA #REQUIRED >
        self.type = tag['Type']
        self.ui = tag['UI']
        self.value = tag.string

    def __repr__(self):
        return display_class(self,
                                 ['type', quotes(self.type),
                                  'value', quotes(self.value),
                                  'ui', quotes(self.ui)])

class CommentsCorrections(object):

    __slots__ = ['note','type','source','pmid','pmid_version']

    def __init__(self,tag):
        # < !ELEMENT CommentsCorrections(RefSource, PMID?, Note?) >
        # < !ATTLIST CommentsCorrections
        # RefType(AssociatedDataset |
        #        AssociatedPublication |
        #        CommentIn | CommentOn |
        #        CorrectedandRepublishedIn | CorrectedandRepublishedFrom |
        #        ErratumIn | ErratumFor |
        #        ExpressionOfConcernIn | ExpressionOfConcernFor |
        #        RepublishedIn | RepublishedFrom |
        #        RetractedandRepublishedIn | RetractedandRepublishedFrom |
        #        RetractionIn | RetractionOf |
        #        UpdateIn | UpdateOf |
        #        SummaryForPatientsIn |
        #        OriginalReportIn |
        #        ReprintIn | ReprintOf |
        #        Cites)  # REQUIRED    >
        #<!ELEMENT	RefSource (#PCDATA) >
        #<!ELEMENT PMID(  # PCDATA) >
        #<!ATTLIST PMID
        #   Version CDATA  # REQUIRED >
        #<!ELEMENT	Note (#PCDATA) >

        self.note = _get_opt_soup_string(tag,'Note')
        self.type = tag['RefType']
        self.source = tag.RefSource.string
        self.pmid = tag.PMID.string
        self.pmid_version = tag.pmid['Version']

    def __repr__(self):
        return display_class(self,
                                 ['note', quotes(self.note),
                                  'type', quotes(self.type),
                                  'source', quotes(self.source),
                                  'pmid', quotes(self.pmid),
                                  'pmid_version', quotes(self.pmid_version)])

class QualifierName(object):

    __slots__ = ['name','is_major','ui']

    def __init__(self,tag):
        # <!ELEMENT QualifierName(  # PCDATA) >
        # <!ATTLIST QualifierName
        #   MajorTopicYN(Y | N) "N"
        #   UI CDATA  # REQUIRED >

        self.name = tag.string
        self.is_major = _get_opt_attr_value(d_name,'MajorTopicYN','N')
        self.ui = tag['UI']

    def __repr__(self):
        return display_class(self,
                                 ['name', quotes(self.name),
                                  'is_major', self.is_major,
                                  'ui', quotes(self.ui)])

class Keyword(object):

    __slots__ = ['value','is_major']

    def __init__(self,tag):
        #< !ELEMENT Keyword( % text; | mml: math) * >
        #< !ATTLIST Keyword
        #   MajorTopicYN(Y | N) "N" >

        self.value = tag.string
        self.is_major = _get_opt_attr_value(tag,'MajorTopicYN','N') == 'Y'

    def __repr__(self):
        return display_class(self,
                                 ['value', quotes(self.value),
                                  'is_major', self.is_major])

class KeywordList(object):

    __slots__ = ['owner','keywords']

    def __init__(self,tag):
        #<!ELEMENT KeywordList(Keyword +) >
        #<!ATTLIST KeywordList
        #   Owner(NLM | NLM - AUTO | NASA | PIP | KIE | NOTNLM | HHS) "NLM" >

        self.owner = _get_opt_attr_value(tag,'Owner','NLM')
        #Technically this isn't optional, but it works ....
        self.keywords = _get_opt_list(tag,'Keyword',Keyword)

    def __repr__(self):
        return display_class(self,
                                 ['owner', quotes(self.owner),
                                  'keywords', _list_cld_or_empty(self.keywords)])

class MeshHeading(object):

    __slots__ = ['name','is_major','ui','qualifiers']

    """
    https://www.nlm.nih.gov/bsd/licensee/elements_descriptions.html#meshheadinglist
    """

    def __init__(self,tag):
    #<!ELEMENT	MeshHeading (DescriptorName, QualifierName*)>
    #<!ELEMENT	DescriptorName (#PCDATA) >
    #<!ATTLIST	DescriptorName
	#	    MajorTopicYN (Y | N) "N"
	#	    Type (Geographic) #IMPLIED
	#	     UI CDATA #REQUIRED >

        d_name = tag.DescriptorName
        self.name = d_name.string
        self.is_major = _get_opt_attr_value(d_name,'MajorTopicYN','N')
        self.ui = tag['UI']
        self.qualifiers = _get_opt_list(tag,'QualifierName',QualifierName)

    def __repr__(self):
        return display_class(self,
                                 ['name', quotes(self.name),
                                  'is_major', self.is_major,
                                  'ui', quotes(self.ui),
                                  'qualifiers',_list_cld_or_empty(self.qualifiers)])

class OtherID(object):

    __slots__ = ['value','source']

    """
    https://www.nlm.nih.gov/bsd/licensee/elements_descriptions.html#otherid
    """

    def __init__(self,tag):
        #< !ELEMENT OtherID(  # PCDATA) >
        #<!ATTLIST OtherID
        #   Source(NASA | KIE | PIP | POP | ARPL | CPC | IND | CPFH | CLML |
        #      NRCBL | NLM | QCIM)  # REQUIRED >
        self.value = tag.string
        self.source = tag['Source']

    def __repr__(self):
        return display_class(self,
                                 ['value', quotes(self.value),
                                  'source', quotes(self.source)])

class Investigator(object):

    __slots__ = ['last_name','fore_name','initials','suffix','identifiers',
                 'affiliations']

    def __init__(self,tag):
        #<!ELEMENT	Investigator (LastName, ForeName?, Initials?, Suffix?, Identifier*, AffiliationInfo*) >
        #<!ATTLIST	Investigator
		#    ValidYN (Y | N) "Y" >
        #<!ELEMENT	LastName (#PCDATA) >
        #<!ELEMENT	ForeName (#PCDATA) >
        #<!ELEMENT	Initials (#PCDATA) >
        #<!ELEMENT	Suffix (%text;)*>

        #TODO: is_valid - why wouldn't it be valid???
        self.last_name = tag.LastName
        self.fore_name = _get_opt_soup_string(tag,'ForeName')
        self.initials = _get_opt_soup_string(tag,'Initials')
        self.suffix = _get_opt_soup_string(tag,'Suffix')
        self.identifiers = _get_opt_list(tag,'Identifier',Identifier)
        self.affiliations = _get_opt_list(tag,'AffiliationInfo',AffiliationInfo)

    def __repr__(self):
        return display_class(self,
                                 ['last_name', quotes(self.last_name),
                                  'fore_name', quotes(self.fore_name),
                                  'initials', quotes(self.initials),
                                  'suffix', quotes(self.suffix),
                                  'identifiers',cld(self.identifiers),
                                  'affiliations',cld(self.affiliations)])

class GeneralNote(object):

    __slots__ = ['value','owner']

    def __init__(self,tag):
        #< !ELEMENT GeneralNote(  # PCDATA) >
        #<!ATTLIST GeneralNote
        #       Owner(NLM | NASA | PIP | KIE | HSR | HMD) "NLM" >

        self.value = tag.string
        self.owner = _get_opt_attr_value(tag,'Owner','NLM')

    def __repr__(self):
        return display_class(self,
                                 ['value', quotes(self.value),
                                  'owner', quotes(self.owner)])

class PersonalNameSubject(object):

    __slots__ = ['last_name','fore_name','initials','suffix']

    """
    Individuals' names appear in <PersonalNameSubject> for citations that
    contain a biographical note or obituary, or are entirely about the
    life or work of an individual or individuals. Data is entered in the
    same format as author names in <AuthorList> including <LastName>,
    <ForeName>, <Suffix>, and <Initials>. See <AuthorList> for details of
    format. <PersonalNameSubjectList> is always complete; there is no
    attribute to indicate completeness.

    Additional information/background:
    An anonymous biography or obituary has the person's name in this element
    but the <AuthorList> is absent.

    """

    def __init__(self,tag):
        #<!ELEMENT	PersonalNameSubject (LastName, ForeName?, Initials?, Suffix?) >

        self.last_name = tag.LastName
        self.fore_name = _get_opt_soup_string(tag, 'ForeName')
        self.initials = _get_opt_soup_string(tag, 'Initials')
        self.suffix = _get_opt_soup_string(tag, 'Suffix')

    def __repr__(self):
        return display_class(self,
                             ['last_name', quotes(self.last_name),
                              'fore_name', quotes(self.fore_name),
                              'initials', quotes(self.initials),
                              'suffix', quotes(self.suffix)])

class MedlineCitation(object):

    __slots__ = ['pmid',
                 'date_completed',
                 'date_revised',
                 'article',
                 'journal_info',
                 'chemicals',
                 'suppl_mesh_list',
                 'citation_subsets',
                 'comments_corrections',
                 'gene_symbols',
                 'mesh_headings',
                 'n_references',
                 'personal_names',
                 'other_ids',
                 'keyword_lists',
                 'coi_statement',
                 'space_missions',
                 'investigators',
                 'general_notes']

    """
    <!ELEMENT	MedlineCitation (
                X PMID,
                X DateCompleted?,
                X DateRevised?,
                X Article,
                X MedlineJournalInfo,
                X ChemicalList?,
                X SupplMeshList?,
                X CitationSubset*,
                X CommentsCorrectionsList?,
                X GeneSymbolList?,
                X MeshHeadingList?,
                X NumberOfReferences?,
                X PersonalNameSubjectList?,
                X OtherID*,
                  OtherAbstract*,
                X KeywordList*,
                X CoiStatement?,
                X SpaceFlightMission*,
                X InvestigatorList?,
                X GeneralNote*)>
                
                
     Citation Subset:
     https://www.nlm.nih.gov/bsd/licensee/elements_descriptions.html#citationsubset
     
                
                

    <!ATTLIST	MedlineCitation
            Owner  (NLM | NASA | PIP | KIE | HSR | HMD | NOTNLM) "NLM"
            Status (Completed | In-Process | PubMed-not-MEDLINE |  In-Data-Review | Publisher |
                    MEDLINE | OLDMEDLINE) #REQUIRED
            VersionID CDATA #IMPLIED
            VersionDate CDATA #IMPLIED
            IndexingMethod CDATA  #IMPLIED >


    """

    def __init__(self, soup):

        #TODO: Attritbutes ...

        #PMID
        #------------------------------
        self.pmid = soup.PMID.string

        #DateCompleted?
        #----------------------------------------------------------------------
        self.date_completed = _get_opt_class(soup,'DateCompleted',DateCompleted)

        #DateRevised?
        #----------------------------------------------------------------------
        self.date_revised = _get_opt_class(soup, 'DateRevised', DateRevised)

        #Article
        #----------------------------------------------------------------------
        self.article = Article(soup.Article)

        #MedlineJournalInfo
        #----------------------------------------------------------------------
        self.journal_info = MedlineJournalInfo(soup.MedlineJournalInfo)

        #ChemicalList?,
        #----------------------------------------------------------------------
        self.chemicals = _get_opt_list(soup.ChemicalList,'Chemical',Chemical)

        #SupplMeshList?
        #----------------------------------------------------------------------
        #<!ELEMENT	SupplMeshList (SupplMeshName+)>
        self.suppl_mesh_list = _get_opt_list(soup.SupplMeshList,'SupplMeshName',SupplMeshName)

        #CitationSubset*
        #----------------------------------------------------------------------
        #<!ELEMENT	CitationSubset (#PCDATA) >
        #https: // www.nlm.nih.gov / bsd / licensee / elements_descriptions.html  # citationsubset
        tags = soup.find_all('CitationSubset',recursive=False)
        self.citation_subsets = [x.string for x in tags]

        #https://www.nlm.nih.gov/bsd/licensee/elements_descriptions.html#citationsubset

        #CommentsCorrectionsList?
        #----------------------------------------------------------------------
        # <!ELEMENT CommentsCorrectionsList(CommentsCorrections +) >
        self.comments_corrections = _get_opt_list(soup.CommentsCorrectionsList,
                                                  'CommentsCorrections',
                                                  CommentsCorrections)

        #GeneSymbolList?
        #----------------------------------------------------------------------
        #<!ELEMENT GeneSymbolList(GeneSymbol +) >
        #<!ELEMENT	GeneSymbol (#PCDATA) >
        gene_symbols = soup.find_all('GeneSymbol',recursive=False)
        if len(gene_symbols) == 0:
            self.gene_symbols = []
        else:
            self.gene_symbols = [x.string for x in gene_symbols]


        #MeshHeadingList?
        #----------------------------------------------------------------------
        #<!ELEMENT MeshHeadingList(MeshHeading +) >
        self.mesh_headings = _get_opt_list(soup.MeshHeadingList,'MeshHeading',MeshHeading)

        #NumberOfReferences?,
        #----------------------------------------------------------------------
        #<!ELEMENT	NumberOfReferences (#PCDATA) >
        self.n_references = _get_opt_soup_string(soup,'NumberOfReferences')

        #PersonalNameSubjectList?,
        #----------------------------------------------------------------------
        #<!ELEMENT	PersonalNameSubjectList (PersonalNameSubject+) >
        self.personal_names = _get_opt_list(soup.PersonalNameSubjectList,
                                            'PersonalNameSubject',PersonalNameSubject)

        #OtherID *,
        #----------------------------------------------------------------------
        self.other_ids = _get_opt_list(soup,'OtherID',OtherID)

        #OtherAbstract *,
        #----------------------------------------------------------------------
        #<!ELEMENT	OtherAbstract (AbstractText+, CopyrightInformation?) >
        #<!ATTLIST OtherAbstract
        #Type(AAMC | AIDS | KIE | PIP | NASA | Publisher |
        #     plain - language - summary)  # REQUIRED
        #Language CDATA "eng" >

        #KeywordList *,
        #----------------------------------------------------------------------
        self.keyword_lists = _get_opt_list(soup,'KeywordList',KeywordList)

        #CoiStatement?,
        #----------------------------------------------------------------------
        #<!ELEMENT   CoiStatement   (%text;)*>
        #https://www.nlm.nih.gov/bsd/licensee/elements_descriptions.html#coistatement
        self.coi_statement = _get_opt_soup_string(soup,'CoiStatement')

        #SpaceFlightMission *,
        #----------------------------------------------------------------------
        #<!ELEMENT	SpaceFlightMission (#PCDATA) >
        space_missions = soup.find_all('SpaceFlightMission',recursive=False)
        if len(space_missions) == 0:
            self.space_missions = []
        else:
            self.space_missions = [x.string for x in space_missions]

        #InvestigatorList?,
        #----------------------------------------------------------------------
        #<!ELEMENT	InvestigatorList (Investigator+) >
        self.investigators = _get_opt_list(soup.InvestigatorList,
                                           'Investigator',
                                           Investigator)

        #GeneralNote *
        #----------------------------------------------------------------------
        self.general_notes = _get_opt_list(soup,'GeneralNote',GeneralNote)



    def __repr__(self):
        return display_class(self,
                             [
                            'pmid',quotes(self.pmid),
                            'date_completed', cld(self.date_completed),
                            'date_revised', cld(self.date_revised),
                            'article',cld(self.article),
                            'journal_info',cld(self.journal_info),
                            'chemicals',_list_cld_or_empty(self.chemicals),
                            'suppl_mesh_list',_list_cld_or_empty(self.suppl_mesh_list),
                            'citation_subsets',_list_cld_or_empty(self.citation_subsets),
                            'comments_corrections',_list_cld_or_empty(self.comments_corrections),
                            'gene_symbols',_list_cld_or_empty(self.gene_symbols),
                            'mesh_headings',_list_cld_or_empty((self.mesh_headings)),
                            'n_references',quotes(self.n_references),
                            'personal_names',_list_cld_or_empty(self.personal_names),
                            'other_ids',_list_cld_or_empty(self.other_ids),
                            'keyword_lists',_list_cld_or_empty(self.keyword_lists),
                            'coi_statement',quotes(self.coi_statement),
                            'space_missions',_list_cld_or_empty(self.space_missions),
                            'investigators',_list_cld_or_empty(self.investigators),
                            'general_notes',_list_cld_or_empty(self.general_notes)])
                            #'keywords',td(str(self.keywords)),
                            #'mesh_headings',td(str(self.mesh_headings))])


"""
class PubmedEntryLazyAttributes(XMLResponseObject):


    def __init__(self, soup):
        super().__init__(soup)
        import pdb
        pdb.set_trace()

        children = soup.find_all(True, recursive=False)

        # medlinecitation
        # pubmeddata
"""






def PMID_to_PMC_results(data):
    #TODO:

    import pdb
    pdb.set_trace()

    #Note, in my experience there is only ever 1 linkset
    linksets = data['linksets'][0]
    linkset_dbs = linksets['linksetdbs']


    pass

#Status: Not used ...
#This ended up not being the best way of going from
#PMIDs to PMCIDs
#
#This link() endpoint is useful for getting some cited by
#information but is not the best ...
class PMIDToPMCLinkSets(object):

    def __init__(self, data, input_data):
        #header
        #linksets

        #Header
        #------------
        header = data['header']
        self.type = header['type']
        self.version = header['version']

        linksets = data['linksets']

        #This appears to always be of length 1?

        #TODO: Need to hold onto user's request so that
        #we can make that the key ...

        #list of dictionaries
        #.dbfrom - 'pubmed'
        #.ids - ['20363814']
        #.linksetdbs
        #      [0]
        #          .dbto : 'pmc'
        #          .linkname : 'pubmed_pmc'
        #          .links : [PMCID value as string'
        #      [1]
        #          .dbto : 'pmc'
        #          .linkname : 'pubmed_pmc_refs'
        #          .links : ['pmcs of references'
        #
        #       This looks like it may be PMCs of papers citing this paper
        #
        #
        #      [2]
        #      #    pubmed_pmc_local

        #TODO: Do multiple values, is length of linksets
        #increased or length of ids???
        import pdb
        pdb.set_trace()


class SearchResult(ResponseObject):
    
    """    
    Response to search()
    
    Attributes
    ----------
    """

    renamed_fields = {
        'ids': 'idlist',
        'translation_set': 'translationset',
        'ret_start': 'retstart',
        'ret_max': 'retmax',
        'query_translation': 'querytranslation',
        'translation_stack': 'translationstack'}
    
    fields = ['version', 'count', 'querykey', 'webenv']
    
    def __init__(self,api,json):
        # The input json has 2 things, header and esearchresult
        # The header only specifies the object type and version
        self.api = api
        self.version = json['header']['version']        
        
        super(SearchResult, self).__init__(json['esearchresult'])       

    def get_doc_info(self,index):
        pass
    # TODO: Include navigation methods: Is this part
        
    def __repr__(self):
        return pv([
        'version',self.version,
        'count',self.count,
        'ids',cld(self.ids),
        'translation_set',self.translation_set,
        'ret_start',self.ret_start,
        'ret_max',self.ret_max,
        'translation_stack',self.translation_stack,
        'querykey',self.querykey,
        'webenv',self.webenv])


def _make_soup(data):
    #TODO: Is there a fallback if lxml is not installed?
    return BeautifulSoup(data,'lxml-xml')

def _get_opt_soup_string(soup,field_name):
    temp_tag = getattr(soup,field_name)
    if temp_tag is None:
        return None
    else:
        return temp_tag.string

def _get_opt_attr_value(tag,attr_name,default=None):
    if attr_name in tag.attrs:
        return tag[attr_name]
    else:
        return default

def _get_opt_class(tag,name,function_handle):
    #if tags exists - create class, otherwise none
    temp_tag = getattr(tag,name)
    if temp_tag is None:
        return None
    else:
        return function_handle(temp_tag)

def _get_opt_list(list_or_None,child_tag_name,function_handle):
    if list_or_None is None:
        return []
    else:
        temp = list_or_None.find_all(child_tag_name,recursive=False)
        return [function_handle(x) for x in temp]

def _list_cld_or_empty(value):
    if len(value) > 0:
        return cld(value)
    else:
        return '[]'