# -*- coding: utf-8 -*-
"""
"""

#Standard Library Imports
import os
import importlib.machinery #Python 3.3+

from .errors import InvalidConfig

try:
    from . import user_config as config
except ImportError:
    config = {}
    #raise errors.InvalidConfig('user_config.py not found')
        
      
if hasattr(config,'config_location'):
    #In this case the config is really only a pointer to another config  
    config_location = config.config_location
    
    if not os.path.exists(config_location):
        raise InvalidConfig('Specified configuration path does not exist')
    
    loader = importlib.machinery.SourceFileLoader('config', config_location)    
    config = loader.load_module()
    

class Config(object):
    
    def __init__(self):        
        self.email = config.get('email',None)
        self.tool = config.get('tool',None)