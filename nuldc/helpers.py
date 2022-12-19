import json
from requests.compat import urljoin
import requests

api_base_url = "https://dcapi.rdc.library.northwestern.edu/api/v2/"
search =  urljoin(api_base_url, "search")
collections =  urljoin(api_base_url, "collections")

def get_all_iiif(start_manifest):
    """ takes items from a IIIF manifest and returns the next_page collection and items"""
    manifest = start_manifest 
    if manifest.get('items')[-1].get('type') == 'Collection':
        # pop off the next
        next = manifest['items'].pop().get('id')
    while next:
        next_results = requests.get(next).json()
        if next_results.get('items')[-1].get('type') == 'Collection':
            next = next_results['items'].pop().get('id')
        else:
            next = None
        manifest['items'] = manifest['items']+next_results['items']
    return manifest 

def get_all_search_results(start_results):
    """Pages through json responses and grabs the next results returns them all together"""
    results = start_results
    next = results.get('pagination').get('next_url')
    #loop through the results
    while next:
        next_results = requests.get(next).json()
        results['data'] = results['data']+next_results.get('data')
        next = next_results.get('pagination').get('next_url')
    return results 

def get_search_results(search_url, parameters, all_results=False):
    """iterates through and grabs the search results"""
    search_results = requests.get(search, params=parameters).json()
    # Get all results as IIIF
    if all_results and parameters.get('as')=='iiif':
        return get_all_iiif(search_results)
    if all_results and parameters.get('as')=='opensearch':
        return get_all_search_results(search_results)

def get_work_by_id(api_base_url, identifier, parameters):
    """returns a work as IIIF or json""" 
    return requests.get(urljoin(api_base_url, "works/"+identifier), params=parameters)


