

#Standard Library
from typing import Union, List, Optional
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

class Link(object):

    __slots__ = ['name','menu','description','db_to']

    def __init__(self,tag):
        #< !ELEMENT Link	(Name ,Menu ,Description ,DbTo )>

        self.name = tag.find('Name').string
        self.menu = tag.Menu.string
        self.description = tag.Description.string
        self.db_to = tag.DbTo.string

    def __repr__(self):
        return display_class(self,
                                 ['name', quotes(self.name),
                                  'menu', quotes(self.menu),
                                  'description', quotes(self.description),
                                  'db_to',quotes(self.db_to)])

class Field(object):

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
        self.is_rangeable = _get_opt_soup_string(tag,'IsRangable')
        self.is_truncatable = _get_opt_soup_string(tag,'IsTruncatable')

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
                              'link_list',_list_cld_or_empty(self.link_list)])

def _make_soup(data):
    #TODO: Is there a fallback if lxml is not installed?
    return BeautifulSoup(data,'lxml-xml')

def _get_opt_soup_int(soup,field_name):
    temp_tag = getattr(soup,field_name)
    if temp_tag is None:
        return None
    else:
        return int(temp_tag.string)

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