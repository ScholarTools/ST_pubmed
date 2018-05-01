#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
See
https://www.ncbi.nlm.nih.gov/pmc/tools/id-converter-api/

Goal is to support interfacing with the csv file

The file appears to be incomplete ...

"""


#Testing

"""
DtypeWarning: Columns (4,5,10) have mixed types. Specify dtype option 
on import or set low_memory=False.
  interactivity=interactivity, compiler=compiler, result=result)
"""

import pandas

csv_path = '/Users/jim/Documents/repos/orgs/scholar_tools/pubmed/PMC-ids.csv'

wtf = pandas.read_csv(csv_path)

wtf.columns