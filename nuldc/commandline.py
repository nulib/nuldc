import typer
from typing import Optional
from nuldc import helpers
import json
from importlib import metadata

app = typer.Typer()
api_base_url = "https://api.dc.library.northwestern.edu/api/v2"

# Define shared options once
as_format_option = typer.Option(
    "opensearch", "--as", help="Results format (opensearch, iiif)")
model_option = typer.Option(
    "works", "--model", help="Model (works, collections, filesets)")
fields_option = typer.Option(
    None, "--fields", help="Optional fields (id,ark,test)")
exclude_fields_option = typer.Option(
    "embedding*", "--exclude-fields", help="Fields to exclude")
all_records_option = typer.Option(False, "--all", help="Get all records")


def build_params(as_format, all_records, fields, exclude_fields):
    """Build API parameters dictionary"""
    params = {"as": as_format, "size": "200"}
    if all_records:
        params["sort"] = "id:asc"

    if fields:
        params["_source_includes"] = fields.split(",")
        # If there's include fields there shouldn't be excludes
        exclude_fields = None
    if exclude_fields:
        params["_source_excludes"] = exclude_fields.split(",")

    return params


def handle_search(query, model, as_format, fields, exclude_fields, all_records, outfile=None):
    """Centralized search function with different output formats"""
    # Build parameters
    params = build_params(as_format, all_records, fields, exclude_fields)
    params["query"] = query

    # Get data
    data = helpers.get_search_results(
        api_base_url, model, params, all_results=all_records)

    # Handle different output formats
    if outfile and as_format == "csv":
        headers, values = helpers.sort_fields_and_values(
            data, fields.split(",") if fields else None)
        helpers.save_as_csv(headers, values, outfile)
        print(f"saved csv to : {outfile}")
    elif outfile and as_format == "xml":
        helpers.save_xml(data, outfile)
        print(f"saved xml to : {outfile}")
    else:
        print(json.dumps(data))


@app.command()
def works(
    id: str,
    as_format: str = as_format_option
):
    """Fetch a work by ID."""
    params = build_params(as_format, False, None, None)
    data = helpers.get_work_by_id(api_base_url, id, params)
    print(json.dumps(data))


@app.command()
def collections(
    id: str,
    as_format: str = as_format_option,
    all_records: bool = all_records_option
):
    """Fetch collections by ID."""
    params = build_params(as_format, all_records, None, None)
    data = helpers.get_collection_by_id(
        api_base_url, id, params, all_results=all_records)
    print(json.dumps(data))


@app.command()
def search(
    query: str,
    model: str = model_option,
    as_format: str = as_format_option,
    fields: Optional[str] = fields_option,
    exclude_fields: str = exclude_fields_option,
    all_records: bool = all_records_option
):
    """Search records."""
    handle_search(query, model, as_format, fields, exclude_fields, all_records)


@app.command()
def csv(
    query: str,
    model: str = model_option,
    outfile: str = typer.Argument(..., help="Output file"),
    fields: Optional[str] = fields_option,
    exclude_fields: str = exclude_fields_option,
    all_records: bool = all_records_option
):
    """Save search results as CSV."""
    handle_search(query, model, "csv", fields,
                  exclude_fields, all_records, outfile)


@app.command()
def xml(
    query: str,
    outfile: str = typer.Argument(..., help="Output file"),
    fields: Optional[str] = fields_option,
    exclude_fields: str = exclude_fields_option,
    all_records: bool = all_records_option
):
    """Save search results as XML."""
    handle_search(query, "works", "xml", fields,
                  exclude_fields, all_records, outfile)


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", help="Show version and exit")
):
    """NULDC - Python helpers consuming the DCAPI."""
    if version:
        try:
            v = metadata.version("nuldc")
            typer.echo(f"NULDC Version: {v}")
            raise typer.Exit()
        except Exception:
            typer.echo("Version information not available")
            raise typer.Exit(1)


def main():
    """NULDC - Python helpers consuming the DCAPI. Entry point"""
    app()


if __name__ == "__main__":
    main()
