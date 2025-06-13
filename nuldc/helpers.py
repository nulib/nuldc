import requests
from requests.adapters import HTTPAdapter
import urllib3
import unicodecsv as csv
import tqdm
import dicttoxml
import sys
import os # For getenv
import json # For JSONDecodeError

api_base_url = "https://api.dc.library.northwestern.edu/api/v2"
HIT_LIMIT = 49999
retries = urllib3.Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=['GET', 'POST'])
session = requests.Session()
adapter = HTTPAdapter(max_retries=retries)
session.mount('https://', adapter)

# Shared tqdm disable logic
TQDM_DISABLED = os.getenv('DISABLE_TQDM_TESTS') == '1'

def get_all_iiif(start_manifest, total_pages, total_hits):
    if total_hits > HIT_LIMIT:
        print(f'{total_hits} total results! The API can only return less than 50,000 at a time. Try breaking it up by collection', file=sys.stderr)
        sys.exit(1)
    manifest = start_manifest
    if manifest.get('items') and manifest.get('items')[-1].get('type') == 'Collection': # Check if items exist
        next_url = manifest['items'].pop().get('id')
    else:
        next_url = None

    pbar = tqdm.tqdm(total=total_pages, initial=1, file=sys.stderr, disable=TQDM_DISABLED)
    while next_url:
        try:
            next_page_response = session.get(next_url)
            next_page_response.raise_for_status()
            next_results = next_page_response.json()

            current_items_list = next_results.get('items', []) # Default to empty list if 'items' is not present
            if current_items_list and current_items_list[-1].get('type') == 'Collection':
                next_url = current_items_list.pop().get('id')
            else:
                next_url = None
            pbar.update(1)
            if 'items' not in manifest: manifest['items'] = [] # Ensure manifest['items'] exists
            manifest['items'].extend(current_items_list) # Extend with potentially modified (popped) list
        except requests.exceptions.RequestException as e:
            print(f"Error fetching IIIF page {next_url}: {e}", file=sys.stderr)
            break
        except json.JSONDecodeError as e: # More specific exception
            print(f"Error decoding JSON from IIIF page {next_url}: {e}", file=sys.stderr)
            break
    pbar.close()
    return manifest

def get_all_search_results(start_results):
    results = start_results
    pagination = results.get('pagination', {})
    total_pages = pagination.get('total_pages')
    total_hits = pagination.get('total_hits')
    next_url = pagination.get('next_url')

    if total_hits is None :
        if not next_url:
             total_hits = 0
        else:
            print(f"Warning: total_hits missing. API limit check might be unreliable. Results ID: {results.get('id', 'Unknown')}", file=sys.stderr)
            total_hits = 0

    if total_pages is None and next_url:
        print(f"Warning: total_pages missing. TQDM progress bar may not be accurate. Results ID: {results.get('id', 'Unknown')}", file=sys.stderr)
        total_pages = 0

    # Removed DEBUG print statement that was going to stdout via runner
    if total_hits > HIT_LIMIT:
        print(f'{total_hits} total results! The API can only return less than 50,000 at a time. Try breaking it up by collection', file=sys.stderr)
        sys.exit(1)

    is_hits_structure = 'hits' in results and isinstance(results.get('hits'), dict) and 'hits' in results['hits']

    if is_hits_structure:
        aggregated_items = list(results['hits']['hits'])
    elif 'data' in results:
        aggregated_items = list(results['data'])
    else:
        if next_url:
            print(f"Warning: Unrecognized structure for pagination in start_results: {list(start_results.keys())}", file=sys.stderr)
        aggregated_items = []

    pbar = tqdm.tqdm(total=total_pages if total_pages else None, initial=1, file=sys.stderr, disable=TQDM_DISABLED)

    while next_url:
        next_page_data = None
        try:
            next_page_response = session.get(next_url)
            next_page_response.raise_for_status()
            next_page_data = next_page_response.json()
            new_items = None
            if is_hits_structure:
                new_items = next_page_data.get('hits', {}).get('hits')
            else:
                new_items = next_page_data.get('data')
            if new_items:
                aggregated_items.extend(new_items)
            next_url = next_page_data.get('pagination', {}).get('next_url')
            pbar.update(1)
        except requests.exceptions.RequestException as e:
            print(f'Request error fetching next page: {e}. URL: {next_url}', file=sys.stderr)
            break
        except json.JSONDecodeError as e:
            print(f'JSON decode error fetching next page: {e}. URL: {next_url}', file=sys.stderr)
            break
        except Exception as e:
            print(f'Generic error processing page: {e}. URL: {next_url}', file=sys.stderr)
            if next_page_data: print(f'Content (first 100 chars): {str(next_page_data)[:100]}', file=sys.stderr)
            break
    pbar.close()

    if is_hits_structure:
        results['hits']['hits'] = aggregated_items
    else:
        results['data'] = aggregated_items

    if 'pagination' in results:
        results['pagination']['next_url'] = ''
    else:
        results['pagination'] = {'next_url': ''}

    return results

def get_collection_by_id(api_base_url, identifier, parameters, all_results=False):
    url = f"{api_base_url}/collections/{identifier}"
    results = session.get(url, params=parameters).json() # Initial fetch
    if all_results:
        if parameters.get('as') == 'iiif':
            # For IIIF, get_all_iiif handles pagination based on 'next' links within IIIF structure
            # but it needs total_pages and total_hits for tqdm.
            # This requires an initial OpenSearch query to get these counts.
            opensearch_query_params = parameters.copy()
            opensearch_query_params['as'] = 'opensearch'
            # This query might need to be specific, e.g., finding items *in* that collection.
            opensearch_query_params['query'] = f'collection.id:"{identifier}"'
            model_for_search = parameters.get('model', 'works') # Or determine model based on collection type
            search_api_url = f"{api_base_url}/search/{model_for_search}"

            req_for_totals = session.get(search_api_url, params=opensearch_query_params).json()
            total_pages = req_for_totals.get('pagination', {}).get('total_pages', 1)
            total_hits = req_for_totals.get('pagination', {}).get('total_hits', 0)
            results = get_all_iiif(results, total_pages, total_hits) # Pass the initial IIIF response
        else: # For 'opensearch' or other non-IIIF formats
              # Assumes the initial 'results' from /collections/{id} has 'data' and 'pagination' keys
              # if it's meant to be paginated further by get_all_search_results.
            if 'data' in results and 'pagination' in results and results.get('pagination', {}).get('next_url'):
                results = get_all_search_results(results)
            # If not, 'results' is returned as is (first page or non-paginated structure)
    return results

def get_nested_field(field, source_dict):
    field_metadata = source_dict
    for f_part in field.split('.'):
        if isinstance(field_metadata, dict):
            field_metadata = field_metadata.get(f_part)
        elif isinstance(field_metadata, list) and all(isinstance(d, dict) for d in field_metadata):
            # If we encounter a list of dicts, attempt to extract the field from each dict in the list
            # This will result in a list of values.
            new_metadata = [i.get(f_part) for i in field_metadata if isinstance(i, dict)]
            # If any item in the list was not a dict or didn't have the key, it might result in None values.
            # If all are None, or list is empty, it means the path wasn't fully found.
            field_metadata = new_metadata if any(i is not None for i in new_metadata) else None
        else:
            field_metadata = None
            break
    return field_metadata

def get_search_results(api_base_url, model, parameters, all_results=False):
    url = f"{api_base_url}/search/{model}"
    search_results = session.get(url, params=parameters).json()
    if all_results and parameters.get('as') == 'iiif':
        count_params = {k: v for k, v in parameters.items() if k != 'as'}
        count_params['as'] = 'opensearch'
        req_for_totals_url = f"{api_base_url}/search/{model}"
        req_for_totals = session.get(req_for_totals_url, params=count_params).json()
        total_pages = req_for_totals.get('pagination', {}).get('total_pages',1)
        total_hits = req_for_totals.get('pagination', {}).get('total_hits',0)
        search_results = get_all_iiif(search_results, total_pages, total_hits)
    elif all_results:
        search_results = get_all_search_results(search_results)
    return search_results

def get_work_by_id(api_base_url, identifier, parameters, **kwargs):
    url = f"{api_base_url}/works/{identifier}"
    return session.get(url, params=parameters).json()

def normalize_format(field):
    if field is None: return ""
    if isinstance(field, dict):
        field = field.get('label', field.get('url', field.get('title', str(field))))
    if isinstance(field, list): # Check if it's a list before specific list comprehensions
        if all(isinstance(d, dict) for d in field):
            field = '|'.join([str(i.get('label', i)) for i in field])
        elif all(isinstance(i, str) for i in field):
            field = '|'.join(field)
        # If it's a list of other types (e.g., numbers, or mixed), convert to string
        else:
            field = '|'.join([str(i) for i in field])
    return str(field)

def save_as_csv(headers, values, output_file):
    with open(output_file, 'wb') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for row in values:
            writer.writerow(row)

def save_xml(opensearch_results, output_file):
    if not isinstance(opensearch_results, dict):
        print(f"Warning: save_xml expected a dict, got {type(opensearch_results)}. XML output might be incorrect or empty.", file=sys.stderr)
        xml_data_to_convert = {'error': 'Invalid data type for XML conversion', 'type': str(type(opensearch_results))}
    else:
        xml_data_to_convert = opensearch_results
    xml = dicttoxml.dicttoxml(xml_data_to_convert, custom_root='results', attr_type=False)
    with open(output_file, 'wb') as xmlfile:
        xmlfile.write(xml)

def sort_fields_and_values(opensearch_results, fields=[]):
    data_list = None
    # Determine the actual list of records from the API response structure
    if 'data' in opensearch_results: # Common for collection-like direct data
        data_list = opensearch_results.get('data')
    elif 'hits' in opensearch_results and isinstance(opensearch_results.get('hits'), dict) and 'hits' in opensearch_results['hits']: # Common for search results
        data_list = [item.get('_source', item) for item in opensearch_results['hits']['hits']] # Extract from _source
    elif isinstance(opensearch_results, list): # If the input is already a list of records
        data_list = opensearch_results

    if not isinstance(data_list, list):
        return ["no results"], [["no results"]]

    if fields:
        headers = fields
        values = []
        for i in data_list:
            row = []
            for f in fields:
                # Ensure 'i' is a dict before calling get_nested_field, default to empty dict if not
                item_dict = i if isinstance(i, dict) else {}
                val = get_nested_field(f, item_dict)
                row.append(normalize_format(val))
            values.append(row)
    elif data_list:
        # Create a union of all keys from all record dicts for headers
        header_set = set()
        temp_processed_data = [] # To store dicts for value extraction
        for d_item in data_list:
            if isinstance(d_item, dict):
                # Normalize values first before getting keys for headers, or get raw keys?
                # For now, get raw keys, then normalize when building rows.
                header_set.update(d_item.keys())
                temp_processed_data.append(d_item) # Store original dict for processing
            else: # Handle non-dict items in data_list if any
                temp_processed_data.append({'error_value': d_item})
                header_set.add('error_value')

        if not temp_processed_data : return ["no results"], [["no results"]]

        headers = sorted(list(header_set))
        values = []
        for item_dict in temp_processed_data:
            values.append([normalize_format(item_dict.get(header, "")) for header in headers])
    else:
        headers = ["no results"]
        values = [["no results"]]
    return headers, values

def aggregate_by(search_url, query_string, agg, size):
    query = {
        "size": "0",
        "query": {"query_string": {"query": query_string}},
        "aggs": {agg: {"terms": {"field": agg, "size": size}}}
    }
    return session.post(search_url, json=query)
