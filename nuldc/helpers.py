import json
from requests.compat import urljoin
import requests
import unicodecsv as csv

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
    field = field.get('label', field.get('url', field.get('title', field)))
  if isinstance(field, list) and all(isinstance(d, dict) for d in field):
    field = '|'.join([str(i.get('label', i)) for i in field])
  if isinstance(field, list):
    field = '|'.join(field)
  return str(field)  

def save_as_csv(opensearch_results, output_file):
    """outputs a CSV using unicodecsv"""
    data = opensearch_results.get('data')
    values = [[normalize_format(field) for field in dict(sorted(row.items())).values()] for row in data]
    headers = list(sorted(data[0].keys()))
    with open(output_file, 'wb') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for row in values:
            writer.writerow(row)

def aggregate_by(search_url, query, agg):
    """ Takes a base url and a query string query and aggs on a sing agg field"""
    pass

def get_fields():
    if fields:
        # grab the fields
    else:
        # just return all the thing
    ### slim = [i.get(f) for f in ['id', 'title','thumbnail'] for i in d]
    ### Allow for filtering based on explicit fields. 
    ### This would be a refactor that would require the save_as_csv to be slightly less generic. 

# TODO add formatters for csv
# TODO Add CSV output

