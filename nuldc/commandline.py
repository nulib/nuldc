"""NULDC

USAGE:
    nuldc works <id> [--as <format>]
    nuldc collections <id> [--as <format>]
    nuldc collections <id> [--as <format>] [--all]
    nuldc search <query_string> [--as <format>] [--all]
    nuldc search <query_string> [--csv <outfile>] [--all]
    nuldc search <query_string> [--csv <outfile> --fields <fields>] [--all]

OPTIONS:
    --as <format>       get results as [default: opensearch]
    --all               get all records from search
    --csv <outfile>     output to CSV, requied outfile
    --fields <fields>   optional set of fields,e.g id,ark,test defaults to all
    -h --help           Show this screen

ARGUMENTS:
    as: opensearch
        iiif
"""


from docopt import docopt
from nuldc import helpers
import json


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
                                            all_results=args.get("--all"))
    # search
    if args['search']:
        params = {"query": args.get('<query_string>'),
                  "as": args.get("--as"),
                  "size": "250"}

        data = helpers.get_search_results(api_base_url,
                                          params,
                                          all_results=args.get("--all"))

        if args['--csv']:
            if args.get('--fields'):
                fields = args.get('--fields').split(',')
            else:
                fields = args.get('--fields')

            headers, values = helpers.sort_fields_and_values(data, fields)
            helpers.save_as_csv(headers, values, args['--csv'])
            data = {"message": "saved csv to :" + args.get('--csv')}

    print(json.dumps(data))


if __name__ == '__main__':
    main()
