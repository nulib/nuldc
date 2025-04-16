import typer
from nuldc import helpers
import json

app = typer.Typer()

# Base API URL
api_base_url = "https://api.dc.library.northwestern.edu/api/v2"

# Shared options
as_option = typer.Option(
    "json", "--as", help="Output format: 'json', 'csv', 'xml', or 'iiif' [default: json]"
)

# Utility function to handle API requests and format output
def handle_request(command: str, id_or_query: str, as_format: str, **kwargs):
    # Map commands to helper functions
    helper_functions = {
        "works": helpers.get_work_by_id,
        "collections": helpers.get_collection_by_id,
        "search": helpers.get_search_results,
    }
    
    # Get the appropriate helper function
    helper_function = helper_functions.get(command)
    if not helper_function:
        typer.echo(f"Error: Unrecognized command '{command}'.")
        raise typer.Exit(code=1)

    # Build API parameters
    params = {"as": as_format, "size": "50"}
    if kwargs.get("all_records"):
        params["sort"] = "id:asc"
    if command == "search" and kwargs.get("model"):
        params["query"] = id_or_query
    else:
        params["id"] = id_or_query

    # Call the helper function
    data = helper_function(api_base_url, id_or_query, params)

    # Handle output format
    if as_format == "csv":
        if not kwargs.get("outfile"):
            typer.echo("Error: --outfile is required for CSV output.")
            raise typer.Exit(code=1)
        helpers.save_as_csv(data, kwargs["outfile"])
        typer.echo(f"Saved CSV to {kwargs['outfile']}")
    elif as_format == "xml":
        if not kwargs.get("outfile"):
            typer.echo("Error: --outfile is required for XML output.")
            raise typer.Exit(code=1)
        helpers.save_xml(data, kwargs["outfile"])
        typer.echo(f"Saved XML to {kwargs['outfile']}")
    elif as_format == "iiif":
        typer.echo(json.dumps(data, indent=2))
    else:  # Default to JSON
        typer.echo(json.dumps(data, indent=2))


@app.command()
def works(
    id: str,
    as_format: str = as_option,
    outfile: str = typer.Option(None, "--outfile", help="File to save output (required for 'csv' and 'xml')"),
    all_records: bool = typer.Option(False, "--all", help="Fetch all records"),
):
    """Fetch a work by ID"""
    handle_request("works", id, as_format, outfile=outfile, all_records=all_records)


@app.command()
def collections(
    id: str,
    as_format: str = as_option,
    outfile: str = typer.Option(None, "--outfile", help="File to save output (required for 'csv' and 'xml')"),
    all_records: bool = typer.Option(False, "--all", help="Fetch all records"),
):
    """Fetch a collection by ID"""
    handle_request("collections", id, as_format, outfile=outfile, all_records=all_records)


@app.command()
def search(
    query: str,
    model: str = typer.Option("works", "--model", help="Model to search (e.g., works, collections, filesets)"),
    as_format: str = as_option,
    outfile: str = typer.Option(None, "--outfile", help="File to save output (required for 'csv' and 'xml')"),
    all_records: bool = typer.Option(False, "--all", help="Fetch all records"),
):
    """Search for records"""
    handle_request("search", query, as_format, model=model, outfile=outfile, all_records=all_records)

def main():
    app()
if __name__ == "__main__":
    app()
