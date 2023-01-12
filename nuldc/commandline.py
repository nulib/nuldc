"""NULDC

USAGE:
    nuldc works <id> [--as=<format>]
    nuldc collections <id> [--as=<format> --all] 
    nuldc search <query> [--model=<model>] [--as=<format>] [--all] [--fields=<fields> --csv <file>]

OPTIONS:
    --as=<format>      get results as [default: opensearch]
    --model=<model>    search model (works,collections,filesets) [default: works]
    --all              get all records from search
    --csv <outfile>    output to CSV, requied outfile
    --fields=<fields>  optional set of fields,e.g id,ark,test defaults to all
    -h --help          Show this screen

ARGUMENTS:
    as: opensearch
        iiif
"""


from docopt import docopt
from nuldc import helpers
import json
import sys


def main():
    args = docopt(__doc__)
    api_base_url = "https://dcapi.rdc.library.northwestern.edu/api/v2"
    params = {"as": args.get("--as"), "size": "250"}
    # work
    if args['works']:
        data = helpers.get_work_by_id(api_base_url, args.get("<id>"), params)
    # collection
    if args['collections']:
        data = helpers.get_collection_by_id(api_base_url,
                                            args.get("<id>"),
                                            params,
                                            all_results=args.get("--all-records"))
    # search
    if args['search']:
        
        # Smoke test. Let's verify that they didn't try to do csv AND iiif.
        if args["--csv"] and args["--as"]=="iiif":
            sys.exit("Can't convert iiif to csv, sorry! Try it without the --as=iiif")

        params = {"query": args.get("<query>"),
                  "as": args.get("--as"),
                  "size": "250"}
        # get the data from the search results helper
        data = helpers.get_search_results(api_base_url,
                                          args["--model"],
                                          params,
                                          all_results=args.get("--all"))
        # Only try to kick out csv if it's opensearch, otherwise return csv
        if args["--csv"] and args["--as"]=="opensearch":
            fields = args.get("--fields")
            if fields:
                fields = fields.split(",")
            headers, values = helpers.sort_fields_and_values(data, fields)
            helpers.save_as_csv(headers, values, args['--csv'])
            data = {"message": "saved csv to :" + args.get('--csv')}
        
    # if there's a user message, print it otherwise dump the data
    print(data.get("message") or json.dumps(data))


if __name__ == '__main__':
    main()
