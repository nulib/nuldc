"""NULDC

USAGE:
    nuldc works <id> [--as=<format>]
    nuldc collections <id> [--as=<format> --all]
    nuldc search <query> [--model=<model>] [--as=<format>] [--all]
    nuldc csv <query> [--fields=<fields>] [--all] <outfile>
    nuldc xml <query> [--all] <outfile>
    nuldc --version

OPTIONS:
    --as=<format>      get results as [default: opensearch]
    --model=<model>    model (works,collections,filesets) [default: works]
    --all              get all records from search
    --fields=<fields>  optional set of fields,e.g id,ark,test defaults to all
    -h --help          Show this screen

ARGUMENTS:
    as: opensearch
        iiif
"""


from docopt import docopt
from nuldc import helpers
import json
from importlib import metadata


def main():
    args = docopt(__doc__, version=metadata.version('nuldc'))
    api_base_url = "https://api.dc.library.northwestern.edu/api/v2"
    # sort on id if it's all records
    if args['--all']:
        params = {"as": args.get("--as"), "size": "250", "sort": "id:asc"}
    else:
        params = {"as": args.get("--as"), "size": "250"}
    # work
    if args['works']:
        data = helpers.get_work_by_id(api_base_url, args.get("<id>"), params)
    # collection
    elif args['collections']:
        data = helpers.get_collection_by_id(api_base_url,
                                            args.get("<id>"),
                                            params,
                                            all_results=args.get(
                                                "--all"))
    # search and csv use the same helper, grab data
    else:
        params["query"] = args.get("<query>")
        # get the data from the search results helper
        data = helpers.get_search_results(api_base_url,
                                          args["--model"],
                                          params,
                                          all_results=args.get("--all"))
    # if it's csv pipe the data out and return a nice message
    if args["csv"]:
        fields = args.get("--fields")
        if fields:
            fields = fields.split(",")
        headers, values = helpers.sort_fields_and_values(data, fields)
        helpers.save_as_csv(headers, values, args['<outfile>'])
        data = {"message": "saved csv to :" + args['<outfile>']}

    if args["xml"]:
        # saving xml
        helpers.save_xml(data, args['<outfile>'])
        data = {"message": "saved xml to :" + args['<outfile>']}

    # if there's a user message, print it otherwise dump the data
    print(data.get("message") or json.dumps(data))


if __name__ == '__main__':
    main()
