from nuldc import helpers
import json
import re

def slugify(s):
  s = s.lower().strip()
  s = re.sub(r'[^\w\s-]', '', s)
  s = re.sub(r'[\s_-]+', '-', s)
  s = re.sub(r'^-+|-+$', '', s)
  return s

def save_files(basename, data):
    """takes a base filename and saves json, csv, and xml"""

    with open(f"json/{basename}.json", 'w', encoding='utf-8') as f:
        json.dump(data.get('data'), f)

    helpers.save_xml(data.get('data'), f'xml/{basename}.xml')

    headers, values  = helpers.sort_fields_and_values(data) 

    helpers.save_as_csv(headers, values, f'csv/{basename}.csv')


def dump_collections():
    """This dumps collections from a collectionlist. TODO agg on collection
    so  that a search could include --since and only return collections 
    changed"""

    api = "https://api.dc.library.northwestern.edu/api/v2"

    collections = helpers.get_search_results(api, 
                                             "collections", 
                                             {"query":"*", "size":1000}, 
                                             page_limit=1000)
 
    for col in collections.get('data'):
        identifier = col.get('id')
        title = col.get('title')
        query = {"query":"collection.id:"+identifier}
        data = helpers.get_search_results(api, 
                                   "works", 
                                   query, all_results=False)
        filename = f"{slugify(col['title'])}-{col['id']}"
        save_files(filename, data)
