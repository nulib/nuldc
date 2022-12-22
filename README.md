# nuldc


A simple CLI for consuming [Northwestern University Libraries Digital Collections API](https://dcapi.rdc.library.northwestern.edu/docs/v2/index.html). It also includes a set of python helpers for rolling your own scripts.

## Quickstart

### Install it

`pip install git+https://github.com/nulib/nuldc/`


```
nuldc --help

NULDC

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
```

## Examples

### Get collection's metadata

`nuldc collections <id>`

or get metadata  as iiif

`nuldc collections <id> --as iiif`

Get the whole collection as IIIF

`nuldc collections <id> --as iiif --all`

### Get a work

`nuldc works <id>`

as iiif? Sure!

`nuldc works <id> --as iiif`

### Search for things

Simple search

`nuldc search 'berkeley AND guitars'`

as iiif

`nuldc search 'berkeley AND guitars' --as iiif --all`

### Save to CSV

get all the fields that are labels

`nuldc search 'berkeley AND guitars' --all --csv <outfile>`

get just a few fields

`nuldc search 'berkeley AND guitars' --all --fields id,title,ark --csv <outfile>`


### Works great with jq!

`nuldc search 'berkeley AND guitars' --all |jq -r '.data[] | [.title,.id]`


