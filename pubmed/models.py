# -*- coding: utf-8 -*-
"""
"""

from lxml import objectify
from bs4 import BeautifulSoup

#Local Imports
from . import utils
display_class = utils.display_class
td = utils.get_truncated_display_string
cld = utils.get_list_class_display

class ResponseObject(object):
    # I made this a property so that the user could change this processing
    # if they wanted. For example, this would allow the user to return authors
    # as just the raw json (from a document) rather than creating a list of
    # Persons
    object_fields = {}
    
    #Name mapping, keys are new, values are old
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
        
        #TODO: Check count, ensure unique values
        #self.xml_dict = {x.tag:x for x in xml} 
        self.json = json
        
    def __getattr__(self, name):

        """
        By checking for the name in the list of fields, we allow returning
        a "None" value for attributes that are not present in the JSON. By
        forcing each class to define the fields that are valid we ensure that
        spelling errors don't return none:
        e.g. document.yeear <= instead of document.year
        """
        
        #TODO: We need to support renaming
        #i.e. 
        if name in self.fields:
            new_name = name
        elif name in self.renamed_fields:
            new_name = name #Do we want to do object lookup on the new name?
            name = self.renamed_fields[name]
        else:
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))
          
        value = self.json.get(name)        
          
        #We don't call object construction methods on None values
        if value is None:
            return None
        elif new_name in self.object_fields:
            #Here we return the value after passing it to a method
            #fh => function handle
            #
            #Only the value is explicitly passed in
            #Any other information needs to be explicitly bound
            #to the method
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

def _to_list_text(data):
    
    return [x.text for x in data]


def citation_match_parser(response_text,data_for_response):
    
    """
    Parameters
    ----------
    data_for_response : dict
        .query_lengths
        
        #TODO: Add on # of queries
    """

    d = data_for_response

    output = []
    lines = response_text.splitlines() #split('\n')
    for line_text, query_length,cur_entry in zip(lines,d['query_lengths'],d['entries']):
        #The +1 is assuming we don't place a | character in the request
        #Current spec says this is required but currently it works without
        #it, and as such we are not placing it
        cur_response = line_text[query_length+1:]
        output.append(CitationMatchResult(cur_response,cur_entry))
        
    if d['is_single']:
        return output[0]
    else:
        return output

class DocumentSet(object):
    
    def __init__(self,data):
        
        temp = _make_soup(data)
        #-pubmed_article
        articles = temp.find_all('PubmedArticle')
        
        import pdb
        pdb.set_trace()
    
class CitationMatchResult(object):
    
    def __init__(self,response_text,entry):
        self.found = response_text[0].isdigit()
        self.entry = entry
        self.raw = response_text
        
        if self.found:
            self.id = self.raw
        else:
            self.id = None
            
        #self.is_ambiguous = ...
            
        #Could do a 

    #EXAMPLE RESPONSES
    #- '26315901'
    #- NOT_FOUND;INVALID_JOURNAL
    # 'AMBIGUOUS (783 citations)'
    #- 'NOT_FOUND'       
        
    def fix_errors():
        #Could try and resolve a journal
        pass
    
    def __repr__(self):
        return display_class(self,['found',self.found,'entry',cld(self.entry),
                   'raw',self.raw,'id',self.id])
    
class PMIDToPMCLinkSet(object):

    def __init__(self,response_text):
        import pdb
        pdb.set_trace()

class SearchResult(ResponseObject):
    
    """    
    Response to esearch()      
    
    Attributes
    ----------
        
    
    
    """
    
    #object_fields = {'ids':_to_list_text}    
    
    renamed_fields = {
    'ids':'idlist',
    'translation_set':'translationset',
    'ret_start':'retstart',
    'ret_max':'retmax',
    'query_translation':'querytranslation',
    'translation_stack':'translationstack'}
    
    fields = ['version','count','querykey','webenv']
    
    def __init__(self,json):
        
        #querykey
        #webenv
        
        #The input json has 2 things, header and esearchresult
        #The header only specifies the object type and version
        self.version = json['header']['version']        
        
        super(SearchResult, self).__init__(json['esearchresult'])       
        
    #TODO: Include navigation methods        
        
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
    
    return BeautifulSoup(data,'lxml')