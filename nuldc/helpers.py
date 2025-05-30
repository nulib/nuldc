import requests
from requests.adapters import HTTPAdapter
import urllib3
import unicodecsv as csv
import tqdm
import dicttoxml
import sys

api_base_url = "https://api.dc.library.northwestern.edu/api/v2"
HIT_LIMIT = 49999
# set retries for req
retries = urllib3.Retry(total=5,
                        backoff_factor=1,
                        status_forcelist=[429, 500, 502, 503, 504],
                        allowed_methods=['GET', 'POST'])

session = requests.Session()
adapter = HTTPAdapter(max_retries=retries)
session.mount('https://', adapter)


def get_all_iiif(start_manifest, total_pages, total_hits):
    """ takes items from a IIIF manifest and returns the next_page
    collection and items"""

    # check to see if there's too many pages, bail with message
    if total_hits > HIT_LIMIT:
        print(f'{total_hits} total results! The API can only return less than 50,000 at a time. Try breaking it up by collection')
        sys.exit(1)

    manifest = start_manifest

    if manifest.get('items')[-1].get('type') == 'Collection':
        # pop off the next
        next_url = manifest['items'].pop().get('id')
    else:
        next_url = None

    pbar = tqdm.tqdm(total=total_pages, initial=1)

    while next_url:
        next_results = session.get(next_url).json()
        if next_results.get('items')[-1].get('type') == 'Collection':
            next_url = next_results['items'].pop().get('id')
        else:
            next_url = None
        pbar.update(1)
        manifest['items'] = manifest['items'] + next_results['items']
    pbar.close()

    return manifest


def get_all_search_results(start_results):
    """Pages through json responses and grabs the next results returns them all
    together"""

    results = start_results
    total_pages = results['pagination']['total_pages']
    total_hits = results['pagination']['total_hits']
    next_url = results.get('pagination').get('next_url')

    # stop if there's too many results and bail
    if total_hits > HIT_LIMIT:
        print(f'{total_hits} total results! The API can only return less than 50,000 at a time. Try breaking it up by collection')
        sys.exit(1)

    # add a progress bar when you get a lot of results
    pbar = tqdm.tqdm(total=total_pages, initial=1)

    # loop through the results
    while next_url:
        next_results = None  # Initialize to avoid referencing an unassigned variable
        try:
            next_results = session.get(next_url).json()
            results['data'] = results['data'] + next_results.get('data')
            next_url = next_results.get('pagination').get('next_url')
            pbar.update(1)
        except Exception as e:
            print('error:', e)
            print('current_results:', next_results if next_results else 'No data retrieved')
            print('errored on: ', next_url)
            sys.exit(1)
    pbar.close()
    # set next url to blank
    results['pagination']['next_url'] = ''

    return results


def get_collection_by_id(api_base_url, identifier,
                         parameters, all_results=False):
    """returns a collection as IIIF or json"""

    url = f"{api_base_url}/collections/{identifier}"
    results = session.get(url, params=parameters).json()

    if all_results and parameters.get('as') == 'iiif':
        # fire off a search for total pagecount this powers the progressbar
        count_params = parameters
        count_params['as'] = 'opensearch'
        count_params['query'] = f'collection.id: {identifier}'
        url = f"{api_base_url}/search"
        req_for_totals = session.get(url, params=count_params).json()
        total_pages = req_for_totals['pagination']['total_pages']
        total_hits = req_for_totals['pagination']['total_hits']
        results = get_all_iiif(results, total_pages, total_hits)

    return results


def get_nested_field(field, source_dict):
    """Handles nested fields using dotted notation from the cli fields and
    flattens nested data"""

    # see if there's a dot notation
    field_metadata = source_dict

    for f in field.split('.'):
        if isinstance(field_metadata, dict):
            field_metadata = field_metadata.get(f)
        elif isinstance(field_metadata, list) and all(
                isinstance(d, dict) for d in field_metadata):
            field_metadata = [i.get(f) for i in field_metadata]
        else:
            # it's not a dict or a list of dicts, so there's no
            # field under it
            field_metadata = f"no field named {f}"
    return field_metadata


def get_search_results(api_base_url, model, parameters,
                       all_results=False):
    """iterates through and grabs the search results. Sets a default pagelimit
    to 200"""

    url = f"{api_base_url}/search/{model}"
    search_results = session.get(url, params=parameters).json()

    # Get all results as IIIF
    if all_results and parameters.get('as') == 'iiif':
        count_params = parameters
        count_params['as'] = 'opensearch'
        req_for_totals = session.get(url, params=count_params).json()
        total_pages = req_for_totals['pagination']['total_pages']
        total_hits = req_for_totals['pagination']['total_hits']
        search_results = get_all_iiif(search_results, total_pages, total_hits)
    elif all_results:
        search_results = get_all_search_results(search_results)

    return search_results


def get_work_by_id(api_base_url, identifier, parameters, **kwargs):
    """returns a work as IIIF or json"""

    url = f"{api_base_url}/works/{identifier}"
    return session.get(url, params=parameters).json()


def normalize_format(field):
    """Normalizes the fields for CSV output. This will favor label"""

    if isinstance(field, dict):
        # Try to get a label, fall back to URL, then Title
        field = field.get('label', field.get('url', field.get('title', field)))
    if isinstance(field, list) and all(isinstance(d, dict) for d in field):
        # try to get a label fall back to the field. Concat everything
        field = '|'.join([str(i.get('label', i)) for i in field])
    if isinstance(field, list) and all(isinstance(i, str) for i in field):
        # join a list of strings pipes for readability
        field = '|'.join(field)

    return str(field)


def save_as_csv(headers, values, output_file):
    """outputs a CSV using unicodecsv"""

    with open(output_file, 'wb') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for row in values:
            writer.writerow(row)


def save_xml(opensearch_results, output_file):
    """takes results as a list of dicts and writes them out to xml"""

    # TODO DRY up this bit and sort_fields_and_values

    # massage the data and remove the embeddings
    data = opensearch_results.get('data')
    data = [{key: value
             for (key, value) in sorted(d.items())
             } for d in data]
    opensearch_results['data'] = data
    xml = dicttoxml.dicttoxml(opensearch_results, attr_type=False)

    with open(output_file, 'wb') as xmlfile:
        xmlfile.write(xml)


def sort_fields_and_values(opensearch_results, fields=[]):
    """takes opensearch results and returns keys and values sorted O
    R an explicit set of fields It can handle infintely nested dot
    notation for digging deeper into metadta.
    """

    data = opensearch_results.get('data')

    if fields and data:
        # if fields are passed in, use them
        values = [[normalize_format(get_nested_field(f, i))
                   for f in fields] for i in data]
    elif data:
        # get only items not in ignore_fields and sort the dictionary
        data = [{key: normalize_format(value)
                 for (key, value) in sorted(d.items())
                 } for d in data]
        fields = list(data[0])
        values = [list(d.values()) for d in data]
    else:
        fields, values = ["no results"], ["no results"]

    return fields, values


def aggregate_by(search_url, query_string, agg, size):
    """ Takes a base url and a query string query and aggs on a single
    agg field"""

    query = {
        "size": "0",
        "query": {
            "query_string": {
                "query": query_string
            }
        },
        "aggs": {
            agg: {
                "terms": {
                    "field": agg,
                    "size": size
                }
            }
        }
    }

    return session.post(search_url, json=query)
