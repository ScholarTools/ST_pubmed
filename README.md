# Pubmed

This is an implementation of the National Library of Medicine's [Entrez API](https://www.ncbi.nlm.nih.gov/books/NBK25499/) that is focused on providing functionality related to Pubmed. 

The provided gateway functions provide a way of programmatically interacting with Pubmed. 

The alternatives include:
1. Web scraping, which I discourage since the API is generally a better approach
2. A mix of web browsing and offline analysis of data
3. Direct usage of the Pubmed database, which can be downloaded from ... (TODO: Insert link)

## Current Status

This is currently a very slow work in progress. 

## Usage Examples

Examples are currently demonstrated in test_api.py

As the library stabilizes I'll move more examples here.

## Setup

- Copy `user_config.txt` to `user_config.py`
- Populate variables:
  - **email** : This is used to email you if you are causing problems. They are asking that you provide a valid email (honor system)
  - **api_key** :
     - instructions : https://support.nlm.nih.gov/knowledgebase/article/KA-05317/en-us
     - you don't need an API key but it can increase your request rate
  - **tool** : 
