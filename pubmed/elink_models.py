"""
https://www.ncbi.nlm.nih.gov/corehtml/query/static/entrezlinks.html

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

def pmc_to_pmid_results(api:'API', response:'Response', ids_in) -> List[str]:

    data = response.json()

    records = data['records']

    #Results may be in order, but I couldn't find a guarantee on this
    #so we'll process in order here
    #
    #Note: An invalid record will have a pmcid but no pmid
    temp = {x['pmcid']:x['pmid'] if 'pmid' in x else None for x in records}

    return [temp[x] for x in ids_in]

def pmid_to_pmc_results(api:'API', response:'Response', ids_in) -> List[str]:

    data = response.json()

    records = data['records']

    #Returned values are not matched to request order, so place in
    #dict and then order by request order below
    #
    ##Note: An invalid record will have a pmid but no pmcid
    temp = {x['pmid']:x['pmcid'] if 'pmcid' in x else None for x in records}

    return [temp[x] for x in ids_in]




class PMIDToPMCLinkSets(object):

    def __init__(self, api:'API', response:'Response'):

        import pdb
        pdb.set_trace()



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


def neighbor_score():
    import pdb
    pdb.set_trace()