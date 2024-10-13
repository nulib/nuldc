"""
This script is an opinionated dump of the nuldc metadata.
It should be run from the folder in which you want to create
an archive of nul's digital collection metadata. It is run
with no arguments. First it looks to see if there's files
for each type:

    - json
    - xml
    - csv

It then looks for an `_updated_at.txt` file. If one does not
exist it starts a clean dump. If one does exist it reads the first
line and performs a date-based search with it on `indexed_at`.
After the run is complete it updates the _updated_at.txt file.

If you want to start from a specific date, simply tweak
_updated_at.txt.
"""


from nuldc import helpers
import json
import re
import datetime
import os
import sys


API = "https://api.dc.library.northwestern.edu/api/v2"


def slugify(s):
    """takes string and removes special characters,
    lowercases, and dashes it"""

    s = s.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s)
    s = re.sub(r'^-+|-+$', '', s)
    return s


def save_files(basename, data):
    """takes a base filename and saves json, csv, and xml"""

    # make the directories if they don't exist
    for d in ['json', 'xml', 'csv']:
        if not os.path.isdir(d):
            os.mkdir(d)

    with open(f"json/{basename}.json", 'w', encoding='utf-8') as f:
        json.dump(data.get('data'), f)

    helpers.save_xml(data, f'xml/{basename}.xml')

    headers, values = helpers.sort_fields_and_values(data)
    helpers.save_as_csv(headers, values, f'csv/{basename}.csv')


def dump_collection(col_id):
    """ Takes a collection id and grabs metadata then dumps into
    json, xml, and csv files"""

    params = {
        "query": f"collection.id:{col_id}",
        "size": "25",
        "sort": "id:asc",
        "_source_excludes": "embedding"}
    try:
        data = helpers.get_search_results(API,
                                          "works",
                                          params,
                                          all_results=True,
                                          page_limit=5000)
        col_title = data['data'][0]['collection']['title']
        filename = f"{slugify(col_title)}-{col_id}"
        save_files(filename, data)
    except Exception as e:
        sys.exit(f"Error with collection {col_id}: {e} ")


def dump_collections(query_string):
    """This dumps collections from a collectionlist."""

    search_url = f'{API}/search'
    # get collections list
    collections = helpers.aggregate_by(search_url,
                                       query_string,
                                       "collection.id",
                                       1000)
    # grab data for each collection and dump
    collections = collections.json(
    )['aggregations']['collection.id']['buckets']

    for c in collections:
        dump_collection(c['key'])

    with open('_updated_at.txt', 'w') as f:
        f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d')}")


def main():
    """ Grabs all metadata. If there is an _updated_at.txt file it will
    only get collections containign works updated since its modified
    date. """

    if os.path.isfile("_updated_at.txt"):
        with open('_updated_at.txt') as f:
            updated = f.readline().strip()

        query = f"indexed_at: >={updated}"
        print(f"looking for collections with works updated since {query}")
    else:
        print("can't find updated since file, rebuilding all collections")
        query = "*"

    dump_collections(query)
