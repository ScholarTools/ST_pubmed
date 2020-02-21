"""
This module holds objects that get returned from "einfo" calls.

"""

#Standard Library
from typing import Union, List, Optional, Dict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .api import CitationMatcherEntry
    from .api import API

#Third Party
#----------------------
from bs4 import BeautifulSoup


#Local Imports
#--------------------
from . import utils
quotes = utils.quotes
display_class = utils.display_class
td = utils.get_truncated_display_string
cld = utils.get_list_class_display
pv = utils.property_values_to_string

from . import model_helpers
_make_soup = model_helpers._make_soup
_list_cld_or_empty = model_helpers._list_cld_or_empty
_get_opt_list = model_helpers._get_opt_list
_get_opt_soup_string = model_helpers._get_opt_soup_string
_get_opt_attr_value = model_helpers._get_opt_attr_value
_get_opt_class = model_helpers._get_opt_class
_get_opt_soup_int = model_helpers._get_opt_soup_int

class Link(object):

    __slots__ = ['name','menu','description','db_to']

    def __init__(self,tag):
        #< !ELEMENT Link	(Name ,Menu ,Description ,DbTo )>

        self.name = tag.find('Name').string
        self.menu = tag.Menu.string
        self.description = tag.Description.string
        self.db_to = tag.DbTo.string

    def get_as_dict(self)->Dict:
        return {'name':self.name,
                'menu':self.menu,
                'description':self.description,
                'db_to':self.db_to}

    def __repr__(self):
        return display_class(self,
                                 ['name', quotes(self.name),
                                  'menu', quotes(self.menu),
                                  'description', quotes(self.description),
                                  'db_to',quotes(self.db_to)])

class Field(object):

    """

    Attributes
    ----------
    name : str
        This seems to work for querying
    full_name : str
        This is what the web interface will use for searching.
    description : str

    term_count :
        I think this is the number of unique values in the database
    is_date :
    is_numerical :
    single_token :

    hierarchy :
    is_hidden :
    is_rangeable :
        This doesn't seem to be getting returned ...
    is_truncatable :

    Example Printouts
    -----------------



    """

    __slots__ = ['name','full_name','description','term_count','is_date',
                 'is_numerical','single_token','hierarchy','is_hidden',
                 'is_rangeable','is_truncatable']

    def __init__(self,tag):
        #< !ELEMENT Field	(Name,
        #                    FullName,
        #                    Description,
        #                    TermCount,
        #                    IsDate,
        #                    IsNumerical,
        #                    SingleToken,
        #                    Hierarchy,
        #                    IsHidden,
        #                    IsRangable?,
        #                    IsTruncatable? )>

        #https://stackoverflow.com/questions/14435268/how-to-access-a-tag-called-name-in-beautifulsoup
        self.name = tag.find('Name').string
        self.full_name = tag.FullName.string
        self.description = tag.Description.string
        self.term_count = tag.TermCount.string
        self.is_date = tag.IsDate.string
        self.is_numerical = tag.IsNumerical.string
        self.single_token = tag.SingleToken.string
        self.hierarchy = tag.Hierarchy.string
        self.is_hidden = tag.IsHidden.string
        #import pdb
        #pdb.set_trace()
        self.is_rangeable = _get_opt_soup_string(tag,'IsRangable')
        self.is_truncatable = _get_opt_soup_string(tag,'IsTruncatable')

    def get_as_dict(self)->Dict:
        return {'name':self.name,
                'full_name':self.full_name,
                'description':self.description,
                'term_count':self.term_count,
                'is_date':self.is_date,
                'is_numerical':self.is_numerical,
                'single_token':self.single_token,
                'hierarchy':self.hierarchy,
                'is_hidden':self.is_hidden,
                'is_rangeable':self.is_rangeable,
                'is_truncatable':self.is_truncatable}

    def __repr__(self):
        return display_class(self,
                                 ['name', quotes(self.name),
                                  'full_name', quotes(self.full_name),
                                  'description', quotes(self.description),
                                  'term_count',quotes(self.term_count),
                                  'is_date',self.is_date,
                                  'is_numerical',self.is_numerical,
                                  'single_token',self.single_token,
                                  'hierarchy',self.hierarchy,
                                  'is_hidden',self.is_hidden,
                                  'is_rangeable',self.is_rangeable,
                                  'is_truncatable',self.is_truncatable])

def parse_db_info(api,data):

    soup = _make_soup(data)

    #TODO: Check for an error

    return DbInfo(soup)

class DbInfo(object):

    """
    Result object for EInfo endpoint
    https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.EInfo

    Attributes
    ----------
    db_name
    menu_name
    """

    __slots__ = ['soup','db_name','menu_name','description','db_build',
                 'warning','count','last_update','field_list','link_list']

    def __init__(self,tag):
        # < !ELEMENT DbInfo	(DbName,
        #                   MenuName,
        #                   Description,
        #                   DbBuild?,
        #                   Warning?,
        #                   Count?,
        #                   LastUpdate?,
        #                   FieldList?,
        #                   LinkList? )>
        # < !ELEMENT DbName	(# PCDATA)>	<!-- \S+ -->

        self.soup = tag
        self.db_name = tag.DbName.string
        self.menu_name = tag.MenuName.string
        self.description = tag.Description.string
        self.db_build = _get_opt_soup_string(tag,'DbBuild')
        self.warning = _get_opt_soup_string(tag,'Warning')
        self.count = _get_opt_soup_int(tag,'Count')
        self.last_update = _get_opt_soup_string(tag,'LastUpdate')
        self.field_list = _get_opt_list(tag.FieldList,'Field',Field)
        self.link_list = _get_opt_list(tag.LinkList,'Link',Link)

    def fields_as_table(self):
        #TODO: How to type hint this when optional import
        #TODO: Wrap with failure notice ...
        import pandas

        rows_list = [x.get_as_dict() for x in self.field_list]
        return pandas.DataFrame(rows_list)

    def links_as_table(self):
        import pandas

        rows_list = [x.get_as_dict() for x in self.link_list]
        return pandas.DataFrame(rows_list)

    def __repr__(self):
        return display_class(self,
                             ['db_name',quotes(self.db_name),
                            'menu_name', quotes(self.menu_name),
                            'description', quotes(self.description),
                              'db_build',quotes(self.db_build),
                              'warning',quotes(self.warning),
                              'count',self.count,
                              'last_update',quotes(self.last_update),
                              'field_list',_list_cld_or_empty(self.field_list),
                              'link_list',_list_cld_or_empty(self.link_list),
                              'methods','-------------------------',
                              'fields_as_table',' ',
                              'links_as_table',' '])

