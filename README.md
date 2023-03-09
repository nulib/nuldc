# nuldc


A simple CLI for consuming [Northwestern University Libraries Digital Collections API](https://api.dc.library.northwestern.edu/). It also includes a set of python helpers for rolling your own scripts.

## Quickstart

### Install it

`pip install nuldc`


```
❯ nuldc --help

NULDC

USAGE:
    nuldc works <id> [--as=<format>]
    nuldc collections <id> [--as=<format> --all]
    nuldc search <query> [--model=<model>] [--as=<format>] [--all]
    nuldc csv <query> [--fields=<fields>] [--all] <outfile>
    nuldc xml <query> [--all] <outfile>
    nuldc --version

OPTIONS:
    --as=<format>      get results as [default: opensearch]
    --model=<model>    search model (works,collections,filesets) [default: works]
    --all              get all records from search
    --fields=<fields>  optional set of fields,e.g id,ark,test defaults to all
    -h --help          Show this screen

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

`nuldc search "berkeley AND guitars"`

Page through all the results and return one big list of items (limit 200 pages)

`nuldc search "trains AND chicago" --all`

as iiif

`nuldc search "trains AND chicago" --as iiif --all`

### Save to CSV

Dumping to CSV is simple. By default it dumps all the fields that are "label". If you need to dig into
specific fields you can do that as well. 

`nuldc csv "trains AND chicago" --all example.csv`

Let's grab just a few fields. 

`nuldc csv "trains AND chicago" --all --fields id,title,ark example.csv`

It also supports "dot" notation for getting into nested, special purpose fields.

`nuldc csv "trains AND chicago" --all --fields id,title,ark,subject.id example.csv`

### Save to xml

You can export search results to an xml serialization of the data structure as well.

`nuldc xml "trains AND chicago" out.xml`

Or get all the records

`nuldc xml "trains AND chicago" --all all.xml`

### Pipeable and Works great with jq!

All of this is pipe-able too, so if you want to do further analysis with JQ or pipe data through some other
processing pipeline, go for it! For instance, let's grab just a coupld of fields from the json and reformat it into 
a simplified shape.

`nuldc search "berkeley AND guitars" --all | jq -r '.data[] | [.title,.id]`


### Advanced Search

You can search within specific fields and perform complex searches using the opensearch/elasticsearch [query-string-query syntax](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-query-string-query.html#query-string-syntax). The query syntax is valid for all "search" operations: search, csv, xml. 

#### Examples:

Get a csv file of all works that have a fileset label including "recto"

`nuldc csv "file_sets.label:Recto*" ~/Desktop/rectos.csv`

Look at results that have a subject that includes "Chicago"

`nuldc search "subject.label:*Chicago*"`

Get Results that have a subject of "Chicago" AND a title of "Bus"

`nuldc search "subject.label:*Chicago* AND title:bus"`

Get results from a known collection that were modified before a certain date:

`nuldc search "modified_date:<2022-10-01 AND collection.title:Berkeley*"`


## Development

This project is built using [POETRY](https://python-poetry.org/). Follow the latest install instructions, clone the repository and `poetry install`.

### Tests

This project uses pytest and has a very small set of tests to ensure things are running as expected.

From a `poetry shell` run `pytest`.
