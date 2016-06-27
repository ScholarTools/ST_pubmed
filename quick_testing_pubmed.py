# -*- coding: utf-8 -*-
"""
"""

from pubmed.main import Pubmed

api = Pubmed()

temp = api.search('Mountcastle') #,usehistory='n')

print(temp)

import pdb
pdb.set_trace()