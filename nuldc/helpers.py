import json
from requests.compat import urljoin
import requests
import unicodecsv as csv

api_base_url = "https://dcapi.rdc.library.northwestern.edu/api/v2/"

def get_all_iiif(start_manifest):
    """ takes items from a IIIF manifest and returns the next_page 
    collection and items"""

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

def get_search_results(api_base_url, parameters, all_results=False):
    """iterates through and grabs the search results"""
    search =  urljoin(api_base_url, "search")
    search_results = requests.get(search, params=parameters).json()
    # Get all results as IIIF
    if all_results and parameters.get('as')=='iiif':
        search_results = get_all_iiif(search_results)
    elif all_results:
        search_results = get_all_search_results(search_results)
    return search_results

def get_work_by_id(api_base_url, identifier, parameters):
    """returns a work as IIIF or json""" 
    return requests.get(urljoin(api_base_url, "works/"+identifier), params=parameters).json()

def get_collection_by_id(api_base_url, identifier, parameters, all_results=False):
    """returns a collection as IIIF or json"""
    results = requests.get(urljoin(api_base_url, "collections/"+identifier), params=parameters).json()
    
    if all_results and parameters.get('as')=='iiif':
        results = get_all_iiif(results) 
    return results 

def normalize_format(field):
    """Normalizes the fields for CSV output. This will favor label"""
    if isinstance(field, dict):
        # Try to get a label, fall back to URL, then Title
        field = field.get('label', field.get('url', field.get('title', field)))
    if isinstance(field, list) and all(isinstance(d, dict) for d in field):
        # try to get a label fall back to the field. Concat everything  
        field = '|'.join([str(i.get('label', i)) for i in field])
    if isinstance(field, list):
        # join a list with pipes for readability
        field = '|'.join(field)
    return str(field)  

def save_as_csv(headers, values, output_file):
    """outputs a CSV using unicodecsv"""
    with open(output_file, 'wb') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for row in values:
            writer.writerow(row)

def sort_fields_and_values(opensearch_results, fields=[]):
    """takes opensearch results and returns keys and values sorted OR an explicit set of fields"""

    data = opensearch_results.get('data')

    if fields:
        fields = fields
        values = [[i.get(f) for f in fields] for i in data]

    else:
        values = [[normalize_format(field) 
                  for field in dict(sorted(row.items())).values()] 
                  for row in data]

        fields = list(sorted(data[0].keys()))
    return fields, values

def aggregate_by(search_url, query, agg):
    """ Takes a base url and a query string query and aggs on a sing agg field"""
    pass

