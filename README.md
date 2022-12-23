# nuldc


A simple CLI for consuming [Northwestern University Libraries Digital Collections API](https://dcapi.rdc.library.northwestern.edu/docs/v2/index.html). It also includes a set of python helpers for rolling your own scripts.

## Quickstart

### Install it

`pip install git+https://github.com/nulib/nuldc/`


```bash
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

### Get a work

Let's get a work's manifest

`nuldc works c1960aac-74f0-4ce8-a795-f713b2e3cc22`

Maybe we should grab that work as a IIIF manifest.

`nuldc works c1960aac-74f0-4ce8-a795-f713b2e3cc22 --as iiif`

### Get collection's metadata

`nuldc collections ecacd539-fe38-40ec-bbc0-590acee3d4f2`

or get metadata  as iiif

`nuldc collections ecacd539-fe38-40ec-bbc0-590acee3d4f2 --as iiif`

Get the whole collection as IIIF, stitching together all the pages

`nuldc collections ecacd539-fe38-40ec-bbc0-590acee3d4f2 --as iiif --all`

### Search for things

Simple search

`nuldc search 'berkeley AND guitars'`

Page through all the results and return one big list of items (limit 200 pages)

`nuldc search 'trains AND chicago' --all`

as iiif

`nuldc search 'trains AND chicago' --as iiif --all`

### Save to CSV

Dumping to CSV is simple. By default it dumps all the fields that are "label". If you need to dig into
specific fields you can do that as well. 

`nuldc search 'trains AND chicago' --all --csv example.csv`

Let's grab just a few fields. 

`nuldc search 'trains AND chicago' --all --fields id,title,ark --csv example_just_a_couple.csv`

It also supports "dot" notation for getting into nested, special purpose fields.

`nuldc search 'berkeley AND guitars' --all --fields id,title,subject.id --csv example_dotted.csv`

### Works great with jq!

All of this is pipe-able too, so if you want to do further analysis with JQ or pipe data through some other
processing pipeline, go for it! For instance, let's grab just a coupld of fields from the json and reformat it into 
a simplified shape.

`nuldc search 'berkeley AND guitars' --all | jq -r '.data[] | [.title,.id]`

