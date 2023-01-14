

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

#Third Party Imports
#------------------------------
#from lxml import objectify
from bs4.element import Tag

# Local Imports
from .utils import quotes, display_class
from .utils import get_truncated_display_string as td
from .utils import get_list_class_display as cld
from .utils import property_values_to_string as pv

from .model_helpers import _make_soup, XMLInfo, _list_cld_or_empty, _get_opt_list
from .model_helpers import _get_opt_soup_string, _get_opt_attr_value, _get_opt_class
from .model_helpers import _get_opt_soup_int

def get_search_ids(api:'API',response:'Response'):

    data = response.json()
    #TODO: How do we get an error????
    return data['esearchresult']['idlist']

class XMLSearchResult(object):

    #I'm curious as to how much slower this is than JSON

    def __init__(self, api: 'API', response: 'Response'):
        # < !ELEMENT
        # eSearchResult(
        #     (
        #             (
        #                 Count,
        #                 (RetMax,
        #                  RetStart,
        #                  QueryKey?,
        #                  WebEnv?,
        #                  IdList,
        #                  TranslationSet,
        #                  TranslationStack?,
        #                  QueryTranslation
        #                  )?
        #             ) | ERROR
        #     ),
        #     ErrorList?,
        #     WarningList?
        # ) >
        data = response.text
        soup = _make_soup(data)
        self.xml_info = XMLInfo(soup)

        self.count = int(soup.Count.string)
        self.ret_max = int(soup.RetMax.string)
        self.ret_start = int(soup.RetStart.string)
        self.query_key = _get_opt_soup_string(soup,'QueryKey')
        self.web_env = _get_opt_soup_string(soup,'WebEnv')
        id_list = soup.IdList
        self.ids = [x.string for x in id_list.find_all('Id',recursive=False)]

        #TODO: TranslationSet - may be an empty tag ...

        translation_stack = soup.TranslationStack
        stack = []
        if translation_stack:
            for tag in translation_stack.contents:
                name = tag.name
                if name == 'TermSet':
                    stack.append(TermSet(tag))
                elif name == 'OP':
                    stack.append(tag.string)

        self.translation_stack = stack

        self.query_translation = soup.QueryTranslation.string

        #< !ELEMENT ErrorList(PhraseNotFound *, FieldNotFound *) >
        error_list_tag = soup.ErrorList
        error_fields = []
        error_phrases = []
        if error_list_tag:
            for tag in error_list_tag.contents:
                name = tag.name
                if name == 'FieldNotFound':
                    error_fields.append(tag.string)
                elif name == 'PhraseNotFound':
                    error_phrases.append(tag.string)

        self.error_fields = error_fields
        self.error_phrases = error_phrases

        #TODO: WarningList

        #WarningList?
        #< !ELEMENT  WarningList(PhraseIgnored *,
        #            QuotedPhraseNotFound *,
        #            OutputMessage *) >

    def __repr__(self):
        #TODO: Hand
        return display_class(self,
                             [
                                 'xml_info', cld(self.xml_info),
                                 'count', self.count,
                                 'ret_max', self.ret_max,
                                 'ret_start', self.ret_start,
                                 'query_key', quotes(td(self.query_key)),
                                 'web_env',quotes(td(self.web_env)),
                                 'ids',quotes(td(str(self.ids))),
                                 'query_translation',quotes(td(self.query_translation)),
                             'error_fields',quotes(td(self.error_fields)),
                             'error_phrases',quotes(td(self.error_phrases))])

class JSONSearchResult(object):
    """
    Response to search()

    Attributes
    ----------


    Example Printout
    ----------------
          version: 0.3
            count: 183
              ids: [str] len(20)
  translation_set: []
        ret_start: 0
          ret_max: 20
translation_stack: [{'term': 'Amundsen[All Fields]', 'field': 'All Fields', 'count': '1156', 'explode': 'N'},
        {'term': 'Webster[All Fields]', 'field': 'All Fields', 'count': '20389', 'explode': 'N'}, 'AND', 'GROUP']
         querykey: None
           webenv: None
    """

    api: 'API'

    def __init__(self, api:'API', response:'Response'):

        data = response.json()

        self.api = api
        self.raw = data
        self.version = data['header']['version']
        root = data['esearchresult']

        self.count = int(root['count'])
        self.ret_max = int(root['retmax'])
        self.ret_start = int(root['retstart'])
        self.ids = root['idlist']
        self.query_key = root.get('querykey')
        self.query_translation = root['querytranslation']
        self.translation_set = root['translationset']
        
        self.translation_stack = root.get("translation_stack")


        #TODO:
        #translationset
        #errors
        #warnings



    def get_doc_info(self, indices):
        # TODO: Support index or indices ...
        pass
        # return self.api.

    def get_next_page(self):
        pass

    # TODO: Include navigation methods: Is this part

    def __repr__(self):
        return display_class(self,
                             ['version', self.version,
                              'count', self.count,
                              'ids', cld(self.ids),
                              'translation_set', self.translation_set,
                              'translation_stack',td(self.translation_stack),
                              'ret_start', self.ret_start,
                              'ret_max', self.ret_max,
                              'query_key', self.query_key,
                              'methods', '----------------------',
                              'get_doc_info', '(self,indices)',
                              'get_next_page', '(self)'])