# -*- coding: utf-8 -*-
"""
TODO: Do we need the XMLResponseObject????? - get rid of this if not and update
     the requirements
"""

#Standard Imports
#-----------
import pprint
import shlex
import inspect
from typing import Union, List, Optional


#Third Party Imports
#------------------------------
#from lxml import objectify
from bs4 import BeautifulSoup

# Local Imports
from . import utils
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

#---- EInfo
#===================================
def get_db_list(json):
    return json['einforesult']['dblist']
    
class PrettyDict(dict):

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


def _to_list_text(data):
    
    return [x.text for x in data]


def citation_match_parser(response_text, data_for_response):
    
    """
    Parameters
    ----------
    data_for_response : dict
        .query_lengths
        
        #TODO: Add on # of queries
    """

    d = data_for_response

    output = []
    lines = response_text.splitlines()  # split('\n')
    for line_text, query_length, cur_entry in zip(lines, d['query_lengths'], d['entries']):
        # The +1 is assuming we don't place a | character in the request
        # Current spec says this is required but currently it works without
        # it, and as such we are not placing it
        cur_response = line_text[query_length+1:]
        output.append(CitationMatchResult(cur_response, cur_entry))
        
    if d['is_single']:
        return output[0]
    else:
        return output

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

    def __init__(self,date_tag):
        #<!ELEMENT PubDate((Year, ((Month, Day?) | Season)?) | MedlineDate) >
        #<!ELEMENT	MedlineDate (#PCDATA) >


        self.year = date_tag.year.string
        self.month = _get_opt_soup_string(date_tag,'month')
        self.day = _get_opt_soup_string(date_tag,'day')
        self.season = _get_opt_soup_string(date_tag,'season')
        self.date = _get_opt_soup_string(date_tag,'medlinedate')

class JournalIssue(object):

    def __init__(self,journal_issue_tag):
        # <!ELEMENT	JournalIssue (Volume?, Issue?, PubDate) >
        # <!ATTLIST	JournalIssue
        #       CitedMedium (Internet | Print) #REQUIRED >

        self.volume = _get_opt_soup_string(journal_issue_tag,'volume')
        self.issue = _get_opt_soup_string(journal_issue_tag,'issue')
        self.pub_date = PubDate(journal_issue_tag.pubdate)
        self.cited_medium = journal_issue_tag['citedmedium']

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
                                 ['electronic_issn',self.electronic_issn,
                                'print_issn',self.print_issn,
                                'issue',cld(self.issue),
                                  'title',self.title,
                                  'iso_abbreviation',self.iso_abbreviation])

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

class Article(object):

    """
    Called from PubmedArticle

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
        page_tag = soup.pagination
        if page_tag is not None:
            self.pagination = Pagination(page_tag)
        else:
            self.pagination = None

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
        #                              AuthorList?
        #----------------------------------------------------------------------
        #https://www.nlm.nih.gov/bsd/licensee/elements_descriptions.html#authorlist
        #<!ELEMENT AuthorList(Author +) >
        #<!ATTLIST AuthorList
        #       CompleteYN (Y | N) "Y"
        #       Type(authors | editors)  # IMPLIED >

        #<!ELEMENT Author(((LastName, ForeName?, Initials?, Suffix?) | CollectiveName), Identifier *, AffiliationInfo *) >
        #<!ATTLIST Author
        #       ValidYN(Y | N) "Y"
        #       EqualContrib(Y | N)  # IMPLIED >

        #<!ELEMENT	CollectiveName (%text;)*>
        #<!ELEMENT Affiliation( % text;) * >
        #<!ELEMENT AffiliationInfo(Affiliation, Identifier *) >

        #<!ELEMENT Identifier(  # PCDATA) >
        #<!ATTLIST Identifier
        #           Source CDATA  # REQUIRED >

        author_list_tag = soup.authorlist
        authors = author_list_tag.find_all('author',recursive=False)
        all_authors = []
        for author_tag in authors:
            author = {
                'last_name':None,
                'fore_name':None,
                'initials':None,
                'suffix':None,
                'collective_name':None,
                'identifiers':None,
                'affiliations':None,
                'is_valid':_get_opt_attr_value(author_tag,'validyn',default='Y')=='Y',
                'equal_contrib':_get_opt_attr_value(author_tag,'equalcontrib',default='N')=='Y'
                }


            last_name_tag = author_tag.lastname
            if last_name_tag is None:
                author['collective_name'] = author_tag.collectivename.string
            else:
                author['last_name'] = last_name_tag.string
                author['fore_name'] = _get_opt_soup_string(author_tag,'forename')
                author['initials'] = _get_opt_soup_string(author_tag,'initials')
                author['suffix'] = _get_opt_soup_string(author_tag,'suffix')

            identifiers = author_tag.find_all('identifier',recursive=False)
            if identifiers is not None:
                author['identifiers'] = [{'source':x['source'],'value':x.string} for x in identifiers]

            affiliations = author_tag.find_all('affiliationinfo',recursive=False)
            if affiliations is not None:
                all_affiliations = []
                for affiliation_tag in affiliations:
                    identifiers = affiliation_tag.find_all('identifier',recursive=False)
                    if identifiers is not None:
                        ids = [{'source': x['source'], 'value': x.string} for x in identifiers]
                    else:
                        ids = None

                    affiliation = {'value':affiliation_tag.string,'identifiers':ids}
                    all_affiliations.append(affiliation)
                author['affiliations'] = all_affiliations

            all_authors.append(author)

        self.authors = all_authors

                #CollectiveName

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
        #<!ELEMENT DataBank(DataBankName, AccessionNumberList?) >
        #<!ATTLIST DataBankList
        #   CompleteYN(Y | N) "Y" >
        #<!ELEMENT DataBankName(#PCDATA) >
        #<!ELEMENT AccessionNumber(#PCDATA) >
        #<!ELEMENT AccessionNumberList(AccessionNumber +) >

        databank_list_tag = soup.databanklist
        all_databanks = []
        if databank_list_tag is not None:
            databank_tags = databank_list_tag.find_all('databank',recursive=False)
            for databank in databank_tags:
                databank_out = {'name': databank.databankname.string,
                                'accession_numbers': None}
                number_list_tag = databank.accessionnumberlist
                if number_list_tag is not None:
                    databank_out['accession_numbers'] = [x.string for x in number_list_tag]

                all_databanks.append(databank_out)

        self.databanks = all_databanks

        #----------------------------------------------------------------------
        #                           GrantList?
        #----------------------------------------------------------------------
        #<!ELEMENT GrantList(Grant+) >
        #<!ATTLIST GrantList
        #       CompleteYN(Y | N) "Y" >
        #<!ELEMENT Grant(GrantID?, Acronym?, Agency, Country) >
        #<!ELEMENT GrantID(#PCDATA) >
        #<!ELEMENT Acronym(#PCDATA) >
        #<!ELEMENT Agency(#PCDATA) >
        #<!ELEMENT Country(#PCDATA) >
        grant_list_tag = soup.grantlist
        all_grants = []
        if grant_list_tag is not None:
            grant_tags = grant_list_tag.find_all('grant',recursive=False)
            for grant in grant_tags:
                all_grants.append({
                    'grant_id':_get_opt_soup_string(grant,'grantid'),
                    'acronym':_get_opt_soup_string(grant,'acronym'),
                    'agency':grant.agency.string,
                    'country':grant.country.string
                })
        self.grants = all_grants


        #----------------------------------------------------------------------
        #                           PublicationTypeList
        #----------------------------------------------------------------------
        #<!ELEMENT PublicationTypeList (PublicationType+) >
        #<!ELEMENT PublicationType(  # PCDATA) >
        #<!ATTLIST PublicationType
        #           UI CDATA  # REQUIRED >


        publication_type_list = soup.publicationtypelist
        pub_type_tags = publication_type_list.find_all('publicationtype',recursive=False)
        pub_types = []
        for pub_type in pub_type_tags:
            pub_types.append({
                'ui':pub_type['ui'],
                'value':pub_type.string
            })
        self.pub_types = pub_types

        #----------------------------------------------------------------------
        #                           VernacularTitle?
        #----------------------------------------------------------------------
        #< !ELEMENT VernacularTitle( % text; | mml: math) * >
        self.vernacular_title = _get_opt_soup_string(soup,'vernaculartitle')

        #----------------------------------------------------------------------
        #                           ArticleDate*
        #----------------------------------------------------------------------
        #<!ELEMENT ArticleDate(Year, Month, Day) >
        #<!ATTLIST ArticleDate
        #   DateType CDATA  #FIXED "Electronic" >

        article_date_tag = soup.find_all('articledate',recursive=False)
        if len(article_date_tag) > 0:
            all_dates = []
            for date in article_date_tag:
                all_dates.append({
                    'year':date.year.string,
                    'month':date.month.string,
                    'day':date.day.string
                })
            self.dates = all_dates
        else:
            self.dates = []



    def __repr__(self):
        if len(self.grants) == 0:
            grant_string = '[]'
        else:
            grant_string = '[<dict>]'

        if len(self.databanks) == 0:
            databank_string = '[]'
        else:
            databank_string = '[<dict>]'

        if self.pagination is None:
            page_string = 'None'
        else:
            page_string = cld(self.pagination)

        if len(self.dates) == 0:
            date_string = '[]'
        else:
            date_string = '[<dict>]'

        return display_class(self,
                                 ['journal',cld(self.journal),
                                  'title',td(self.title),
                                  'abstract_copyright_info',td(self.abstract_copyright_info),
                                  'abstracts',td(str(self.abstracts)),
                                  'pagination',page_string,
                                  'doi',self.doi,
                                  'pii',self.pii,
                                  'authors','[<dict>]',
                                  'languages','[string]',
                                  'databanks',databank_string,
                                  'vernacular_title',td(self.vernacular_title),
                                  'pub_types','[dict]',
                                  'grants',grant_string,
                                  'dates',date_string])

    """
   
       <!ELEMENT	Article (
                    X Journal,
                    X ArticleTitle,
                    ((Pagination, ELocationID*) | ELocationID+),
                    X Abstract?,
                    X AuthorList?,
                     Language+,
                     DataBankList?,
                     GrantList?,
                     PublicationTypeList,
                     VernacularTitle?,
                     ArticleDate*) >
    """

class PubmedArticle(object):

    def __init__(self,soup):
        #<!ELEMENT	PubmedArticle (MedlineCitation, PubmedData?)>
        #<!ATTLIST  PubmedArticle
        self.citation = MedlineCitation(soup.medlinecitation)
        pubmed_data = soup.pubmeddata
        if pubmed_data is None:
            self.pubmed_data = None
        else:
            self.pubmed_data = PubmedData(pubmed_data)

    def __repr__(self):
        if self.pubmed_data is None:
            p_string = 'None'
        else:
            p_string = cld(self.pubmed_data)

        return display_class(self,
                             ['citation', cld(self.citation),
                              'pubmed_data', p_string])

class PubmedPubDate(object):

    def __init__(self,tag):
        #<!ELEMENT PubMedPubDate(Year, Month, Day, (Hour, (Minute, Second?)?)?) >
        #<!ATTLIST PubMedPubDate
        #   PubStatus(received | accepted | epublish |
        #          ppublish | revised | aheadofprint |
        #          retracted | ecollection | pmc | pmcr | pubmed | pubmedr |
        #          premedline | medline | medliner | entrez | pmc - release)  # REQUIRED >

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

    def __init__(self,tag):
        #< !ELEMENT Reference(Citation, ArticleIdList?) >
        #<!ELEMENT	Citation       (%text; | mml:math)*>

        self.citation = tag.citation.string
        self.article_ids = _get_opt_list(tag.articleidlist,'articleid',ArticleID)

        #TODO: Support doi, and PMID pull outs


    def __repr__(self):
        return display_class(self,
                             ['citation', self.citation,
                              'article_ids',_list_cld_or_empty(self.article_ids)])


class PubmedData(object):
    __slots__ = ['history','publication_status','doi','pii','pmcpid',
                 'pmpid','pmc','mid','sici','pubmed','medline','pmcid','pmcbook',
                 'bookaccession','ref_lists']

    #TODO: Document these properties ...

    def __init__(self,tag):
        #<!ELEMENT	PubmedData (History?, PublicationStatus, ArticleIdList, ObjectList?, ReferenceList*) >

        #History?
        #----------------------------------------
        #<!ELEMENT	History (PubMedPubDate+) >
        self.history = _get_opt_list(tag.history,'pubmedpubdate',PubmedPubDate)

        #PublicationStatus
        #----------------------------------------
        #<!ELEMENT	PublicationStatus (#PCDATA) >
        self.publication_status = tag.publicationstatus.string

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
        ids = id_list.find_all('articleid',recursive=False)
        for id in ids:
            type = _get_opt_attr_value(id,'idtype','pubmed')
            setattr(self,type,id.string)

        #ObjectList?
        #-------------------------
        #<!ELEMENT Object(Param *) >
        #<!ATTLIST Object
        #   Type CDATA  # REQUIRED >
        #<!ELEMENT ObjectList(Object +) >
        #
        #<!ELEMENT	Param  (%text;)*>
        #<!ATTLIST	Param
        #     Name CDATA #REQUIRED >
        object_list_tag = tag.objectlist
        if object_list_tag is not None:
            import pdb
            pdb.set_trace()

        #ReferenceList*
        #--------------------------------------------------
        self.ref_lists = _get_opt_list(tag,'referencelist',ReferenceList)

    def __repr__(self):
        return display_class(self,
                             ['history', _list_cld_or_empty(self.history),
                              'publication_status', self.publication_status,
                              'ref_lists',_list_cld_or_empty(self.ref_lists),
                              'doi',self.doi,
                              'pii',self.pii,
                              'pmcpid',self.pmcpid,
                              'pmpid', self.pmpid,
                              'pmc', self.pmc,
                              'mid', self.mid,
                              'sici', self.sici,
                              'pubmed', self.pubmed,
                              'medline', self.medline,
                              'pmcid', self.pmcid,
                              'pmcbook', self.pmcbook,
                              'bookaccession', self.bookaccession])

class DateCompleted(object):
    __slots__ = ['year','month','day']
    def __init__(self,tag):
        #<!ELEMENT DateCompleted(Year, Month, Day) >
        self.year = tag.year.string
        self.month = tag.month.string
        self.day = tag.day.string

    def __repr__(self):
        return display_class(self,
                             ['year', self.year,
                              'month', self.month,
                              'day',self.day])

class DateRevised(object):
    __slots__ = ['year', 'month', 'day']
    def __init__(self,tag):
        #<!ELEMENT DateRevised(Year, Month, Day) >
        self.year = tag.year.string
        self.month = tag.month.string
        self.day = tag.day.string

    def __repr__(self):
        return display_class(self,
                             ['year', self.year,
                              'month', self.month,
                              'day',self.day])

class MedlineJournalInfo(object):

    def __init__(self,tag):
        #<!ELEMENT	MedlineJournalInfo (Country?, MedlineTA, NlmUniqueID?, ISSNLinking?) >
        #<!ELEMENT	Country (#PCDATA) >
        #<!ELEMENT	MedlineTA (#PCDATA) >
        #<!ELEMENT	NlmUniqueID (#PCDATA) >
        #<!ELEMENT	ISSNLinking (#PCDATA) >

        self.country = _get_opt_soup_string(tag,'country')
        self.medline_ta = tag.medlineta.string
        """
        States the title abbreviation for the journal in which the article 
        appeared. These title abbreviations are designated by NLM. See <Title> 
        for the full journal title, or <ISOAbbreviation> for the standard ISO abbreviation.
        """

        self.nlm_unique_id = _get_opt_soup_string(tag,'nlmuniqueid')
        self.issn_linking = _get_opt_soup_string(tag,'issnlinking')

    def __repr__(self):
        return display_class(self,
                                 ['country', self.country,
                                  'medline_ta', self.medline_ta,
                                  'nlm_unique_id', self.nlm_unique_id,
                                  'issn_linking',self.issn_linking])


class Chemical(object):

    __slots__ = ['registry_number','substance_name','ui']

    def __init__(self,tag):
        #<!ELEMENT Chemical(RegistryNumber, NameOfSubstance) >
        #<!ELEMENT ChemicalList(Chemical +) >
        #<!ELEMENT	RegistryNumber (#PCDATA) >
        #<!ELEMENT	NameOfSubstance (#PCDATA) >
        #<!ATTLIST	NameOfSubstance
		#    UI CDATA #REQUIRED >

        self.registry_number = tag.registrynumber.string
        self.substance_name = tag.nameofsubstance.string
        self.ui = tag.nameofsubstance['ui']

    def __repr__(self):
        return display_class(self,
                                 ['registry_number', self.registry_number,
                                  'substance_name', self.substance_name,
                                  'ui', self.ui])

class MedlineCitation(object):

    """
    <!ELEMENT	MedlineCitation (
                X PMID,
                X DateCompleted?,
                X DateRevised?,
                X Article,
                MedlineJournalInfo,
                ChemicalList?,
                SupplMeshList?,
                CitationSubset*,
                CommentsCorrectionsList?,
                GeneSymbolList?,
                MeshHeadingList?,
                NumberOfReferences?,
                PersonalNameSubjectList?,
                OtherID*,
                OtherAbstract*,
                KeywordList*,
                CoiStatement?,
                SpaceFlightMission*,
                InvestigatorList?,
                GeneralNote*)>

    <!ATTLIST	MedlineCitation
            Owner  (NLM | NASA | PIP | KIE | HSR | HMD | NOTNLM) "NLM"
            Status (Completed | In-Process | PubMed-not-MEDLINE |  In-Data-Review | Publisher |
                    MEDLINE | OLDMEDLINE) #REQUIRED
            VersionID CDATA #IMPLIED
            VersionDate CDATA #IMPLIED
            IndexingMethod    CDATA  #IMPLIED >


    """

    def __init__(self, soup):

        #PMID
        #------------------------------
        self.pmid = soup.pmid.string

        #DateCompleted?
        #----------------------------------------------------------------------
        self.date_completed = _get_opt_class(soup,'datecompleted',DateCompleted)

        #DateRevised?
        #----------------------------------------------------------------------
        self.date_revised = _get_opt_class(soup, 'daterevised', DateRevised)

        #Article
        #----------------------------------------------------------------------
        self.article = Article(soup.article)

        #MedlineJournalInfo
        #----------------------------------------------------------------------
        self.journal_info = MedlineJournalInfo(soup.medlinejournalinfo)

        #ChemicalList?,
        #----------------------------------------------------------------------
        self.chemicals = _get_opt_list(soup.chemicallist,'chemical',Chemical)

        """
        temp = medline_citation.keywordlist
        if temp is not None:
            temp2 = []
            for kw in temp:
                if str(kw) != '\n':
                    temp3 = {
                        'value':kw.string,
                        'is_major':kw['majortopicyn']}
                    temp2.append(temp3)
            self.keywords = temp2
        else:
            self.keywords = None

        temp = medline_citation.meshheadinglist
        if temp is not None:
            temp2 = []
            mh_all = temp.find_all('meshheading')
            for mesh_head in mh_all:
                desc = mesh_head.descriptorname
                temp3 = {'descriptor':desc.string,
                         'is_major':desc['majortopicyn'] == 'Y',
                         'ui':desc['ui']}
                qual_all = mesh_head.find_all('qualifiername')
                temp2.append(temp3)
            self.mesh_headings = temp2
        else:
            self.mesh_headings = None




        #keywordlist
        #   keyword - list  attrs:majortopicyn


        pubmed_data = soup.pubmeddata
        for child in pubmed_data.contents:
            print(child.name)
        #history
        #publicationstatus
        #articleidlist
        #referencelist

        #history
        #   - pubmedpubdate list  attrs: pubstatus
        #       - year
        #       - month
        #       - day

        #children = soup.find_all(True, recursive=False)
        # [0] => medlinecitation
        # [1] => pubmeddata



        #medline_citation = children[0]

        #.name

        #import pdb
        #pdb.set_trace()
        """

    def __repr__(self):
        #TODO: How to do None or <dict>
        return display_class(self,
                             [
                            'pmid',self.pmid,
                            'date_completed', cld(self.date_completed),
                            'date_revised', cld(self.date_revised),
                            'medline_article',cld(self.article),
                            'medline_journal_info',cld(self.journal_info),
                            'chemicals',_list_cld_or_empty(self.chemicals)])
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



class CitationMatchResult(object):
    
    """
    
    See Also
    --------
    pubmed.api.CitationMatcherEntry
    pubmed.api.API.match_citations
    """
    
    def __init__(self,response_text,entry):
        self.found = response_text[0].isdigit()
        self.entry = entry
        self.raw = response_text
        
        if self.found:
            self.id = self.raw
        else:
            self.id = None
            
        # self.is_ambiguous = ...
            
        # Could do a

    # EXAMPLE RESPONSES
    # - '26315901'
    # - NOT_FOUND;INVALID_JOURNAL
    # 'AMBIGUOUS (783 citations)'
    # - 'NOT_FOUND'
        
    def fix_errors(self):
        # Could try and resolve a journal
        pass
    
    def __repr__(self):
        return display_class(self,
                ['found', self.found, 
                 'entry', cld(self.entry),
                 'raw', self.raw, 
                 'id', self.id])


def PMID_to_PMC_results(data):
    #TODO:

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
    
    # object_fields = {'ids':_to_list_text}
    
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
    return BeautifulSoup(data,'lxml')

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


def _cld_or_none(value):
    if value is None:
        return 'None'
    else:
        return cld(value)

def _list_cld_or_empty(value):
    if len(value) > 0:
        return cld(value)
    else:
        return '[]'