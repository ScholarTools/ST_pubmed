import shlex

from bs4 import BeautifulSoup




from . import utils
quotes = utils.quotes
display_class = utils.display_class
td = utils.get_truncated_display_string
cld = utils.get_list_class_display
pv = utils.property_values_to_string

def _make_soup(data):
    #TODO: Is there a fallback if lxml is not installed?
    return BeautifulSoup(data,'lxml-xml')

class XMLInfo(object):

    def __init__(self,soup):
        # EXAMPLE
        # ------------------------
        # 'PubmedArticleSet PUBLIC "-//NLM//DTD PubMedArticle, 1st January 2019//EN" "https://dtd.nlm.nih.gov/ncbi/pubmed/out/pubmed_190101.dtd"'

        # We'll assume it is the first element ...
        doctype = soup.contents[0]

        parts = shlex.split(doctype)
        # 1) PubmedArticleSet
        # 2) PUBLIC
        # 3) Name
        # 4) URL

        self.doc_type = parts[0]
        self.dtd_name = parts[2]
        self.dtd_url = parts[3]

    def __repr__(self):
        return display_class(self,
                                 ['doc_type', quotes(self.doc_type),
                                  'dtd_name', quotes(self.dtd_name),
                                  'dtd_url', quotes(self.dtd_url)])

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