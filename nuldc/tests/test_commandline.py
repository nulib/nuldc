import json
import os
import pytest
import requests_mock
from typer.testing import CliRunner
from unittest import mock
import csv as csv_parser # To parse the output CSV for assertions
import xml.etree.ElementTree as ET # For parsing XML output

from nuldc.commandline import app, api_base_url

runner = CliRunner()

@pytest.fixture(autouse=True)
def mock_tqdm_fixture():
    """Mocks tqdm.tqdm to prevent progress bar output during tests."""
    with mock.patch('tqdm.tqdm', autospec=True) as mock_tqdm_constructor:
        instance_mock = mock.MagicMock()
        instance_mock.__iter__.return_value = iter([])
        instance_mock.__enter__.return_value = instance_mock
        instance_mock.__exit__.return_value = None
        mock_tqdm_constructor.return_value = instance_mock
        yield mock_tqdm_constructor

# === Tests for main callback ===
def test_callback_no_subcommand():
    """Tests invoking the CLI with no subcommand."""
    result = runner.invoke(app, [])
    # Exit code 0 because Typer shows help by default when no command is given
    # and the callback `elif ctx.invoked_subcommand is None:` also leads to a clean exit (showing help).
    assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
    # Check if part of the help message or the default message is present
    assert "Usage: root [OPTIONS] COMMAND [ARGS]..." in result.stdout or \
           "NULDC - Python helpers consuming the DCAPI. Use --help for options." in result.stdout


def test_works_command_opensearch():
    work_id = "work_id_123"
    expected_api_response = {"id": work_id, "title": "Test Work Title", "description": "A description of the test work."}
    with requests_mock.Mocker() as m:
        mock_url = f"{api_base_url}/works/{work_id}?as=opensearch&size=200"
        m.get(mock_url, json=expected_api_response)
        result = runner.invoke(app, ["works", work_id])
        assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
        try:
            output_json = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output was not valid JSON: {result.stdout}\nError: {e}")
        assert output_json == expected_api_response

def test_works_command_iiif():
    work_id = "work_id_456"
    expected_api_response = {"@context": "http://iiif.io/api/presentation/2/context.json", "@id": f"{api_base_url}/works/{work_id}?as=iiif", "@type": "sc:Manifest", "label": "IIIF Manifest for Test Work"}
    with requests_mock.Mocker() as m:
        mock_url = f"{api_base_url}/works/{work_id}?as=iiif&size=200"
        m.get(mock_url, json=expected_api_response)
        result = runner.invoke(app, ["works", work_id, "--as", "iiif"])
        assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
        try:
            output_json = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output was not valid JSON: {result.stdout}\nError: {e}")
        assert output_json == expected_api_response

def test_works_command_api_error_404():
    work_id = "work_id_789_not_found"
    error_response_json = {"error": "Work not found", "status_code": 404}
    with requests_mock.Mocker() as m:
        mock_url = f"{api_base_url}/works/{work_id}?as=opensearch&size=200"
        m.get(mock_url, status_code=404, json=error_response_json)
        result = runner.invoke(app, ["works", work_id])
        assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
        try:
            output_json = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output was not valid JSON: {result.stdout}\nError: {e}")
        assert output_json == error_response_json

def test_works_command_api_error_500():
    work_id = "work_id_500_internal_error"
    error_response_json = {"error": "Internal Server Error", "status_code": 500}
    with requests_mock.Mocker() as m:
        mock_url = f"{api_base_url}/works/{work_id}?as=opensearch&size=200"
        m.get(mock_url, status_code=500, json=error_response_json)
        result = runner.invoke(app, ["works", work_id])
        assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
        try:
            output_json = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output was not valid JSON: {result.stdout}\nError: {e}")
        assert output_json == error_response_json

# === Tests for 'collections' command ===

def test_collections_command_opensearch():
    collection_id = "collection_id_123"
    expected_api_response = {"id": collection_id, "title": "Test Collection Title", "summary": "A summary of the test collection."}
    with requests_mock.Mocker() as m:
        mock_url = f"{api_base_url}/collections/{collection_id}?as=opensearch&size=200"
        m.get(mock_url, json=expected_api_response)
        result = runner.invoke(app, ["collections", collection_id])
        assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
        try:
            output_json = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output was not valid JSON: {result.stdout}\nError: {e}")
        assert output_json == expected_api_response

def test_collections_command_iiif():
    collection_id = "collection_id_456"
    expected_api_response = {"@context": "http://iiif.io/api/presentation/2/context.json", "@id": f"{api_base_url}/collections/{collection_id}?as=iiif", "@type": "sc:Collection", "label": "IIIF Collection Data for Test Collection", "description": "Mock IIIF description"}
    with requests_mock.Mocker() as m:
        mock_url = f"{api_base_url}/collections/{collection_id}?as=iiif&size=200"
        m.get(mock_url, json=expected_api_response)
        result = runner.invoke(app, ["collections", collection_id, "--as", "iiif"])
        assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
        try:
            output_json = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output was not valid JSON: {result.stdout}\nError: {e}")
        assert output_json == expected_api_response

def test_collections_command_all_records_opensearch():
    collection_id = "collection_all_789"
    page1_url = f"{api_base_url}/collections/{collection_id}?as=opensearch&size=200&sort=id:asc"
    page2_url = f"{api_base_url}/collections/{collection_id}?as=opensearch&size=200&sort=id:asc&page=2"
    page1_response = {"data": [{"id": "item1", "title": "Item 1"}, {"id": "item2", "title": "Item 2"}], "pagination": {"next_url": page2_url, "total_pages": 2, "total_hits": 3}}
    page2_response = {"data": [{"id": "item3", "title": "Item 3"}], "pagination": {"next_url": None, "total_pages": 2, "total_hits": 3}}
    expected_aggregated_data = {"data": [{"id": "item1", "title": "Item 1"}, {"id": "item2", "title": "Item 2"}, {"id": "item3", "title": "Item 3"}], "pagination": {"next_url": "", "total_pages": 2, "total_hits": 3}}
    with requests_mock.Mocker() as m:
        m.get(page1_url, json=page1_response)
        m.get(page2_url, json=page2_response)
        result = runner.invoke(app, ["collections", collection_id, "--all"])
        assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
        try:
            output_json = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output was not valid JSON: {result.stdout}\nError: {e}")
        assert output_json == expected_aggregated_data

def test_collections_command_api_error_404():
    collection_id = "collection_id_not_found"
    error_response_json = {"error": "Collection not found", "status_code": 404}
    with requests_mock.Mocker() as m:
        mock_url = f"{api_base_url}/collections/{collection_id}?as=opensearch&size=200"
        m.get(mock_url, status_code=404, json=error_response_json)
        result = runner.invoke(app, ["collections", collection_id])
        assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
        try:
            output_json = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output was not valid JSON: {result.stdout}\nError: {e}")
        assert output_json == error_response_json

# === Tests for 'search' command ===

def test_search_command_default_opensearch():
    query = "test search query"
    expected_api_response = {"hits": {"hits": [{"_source": {"id": "work1", "title": "Test Work 1"}}]}}
    mock_url = f"{api_base_url}/search/works?as=opensearch&size=200&query={query}&_source_excludes=embedding%2A"
    with requests_mock.Mocker() as m:
        m.get(mock_url, json=expected_api_response)
        result = runner.invoke(app, ["search", query])
        assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
        output_json = json.loads(result.stdout)
        assert output_json == expected_api_response

def test_search_command_custom_model_iiif():
    query = "colonialism"
    model = "collections"
    expected_api_response = {"@context": "http://iiif.io/api/search/0/context.json", "resources": [{"@id": "col1"}]}
    mock_url = f"{api_base_url}/search/{model}?as=iiif&size=200&query={query}&_source_excludes=embedding%2A"
    with requests_mock.Mocker() as m:
        m.get(mock_url, json=expected_api_response)
        result = runner.invoke(app, ["search", query, "--model", model, "--as", "iiif"])
        assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
        output_json = json.loads(result.stdout)
        assert output_json == expected_api_response

def test_search_command_with_fields():
    query = "architecture"
    fields = "id,title,ark"
    expected_api_response = {"hits": {"hits": [{"_source": {"id": "work2", "title": "Arches", "ark": "ark:/123/def"}}]}}
    fields_query_string = "&".join([f"_source_includes={f}" for f in fields.split(',')])
    mock_url = f"{api_base_url}/search/works?as=opensearch&size=200&query={query}&{fields_query_string}"
    with requests_mock.Mocker() as m:
        m.get(mock_url, json=expected_api_response)
        result = runner.invoke(app, ["search", query, "--fields", fields])
        assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
        output_json = json.loads(result.stdout)
        assert output_json == expected_api_response

def test_search_command_with_exclude_fields():
    query = "manuscripts"
    exclude_fields = "full_text,transcript"
    expected_api_response = {"hits": {"hits": [{"_source": {"id": "work3", "title": "Old Scroll"}}]}}
    exclude_fields_query_string = "&".join([f"_source_excludes={f}" for f in exclude_fields.split(',')])
    mock_url = f"{api_base_url}/search/works?as=opensearch&size=200&query={query}&{exclude_fields_query_string}"
    with requests_mock.Mocker() as m:
        m.get(mock_url, json=expected_api_response)
        result = runner.invoke(app, ["search", query, "--exclude-fields", exclude_fields])
        assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
        output_json = json.loads(result.stdout)
        assert output_json == expected_api_response

def test_search_command_all_records_opensearch():
    query = "everything"
    model = "works"
    page1_url = f"{api_base_url}/search/{model}?as=opensearch&size=200&sort=id:asc&query={query}&_source_excludes=embedding%2A"
    page2_url = f"{api_base_url}/search/{model}?as=opensearch&size=200&sort=id:asc&query={query}&_source_excludes=embedding%2A&page=2"
    page1_response = {"hits": {"hits": [{"_source":{"id":"item1"}}]}, "pagination": {"next_url": page2_url, "total_pages": 2, "total_hits": 3}}
    page2_response = {"hits": {"hits": [{"_source":{"id":"item2"}}, {"_source":{"id":"item3"}}]}, "pagination": {"next_url": None, "total_pages": 2, "total_hits": 3}}
    expected_aggregated_data = {"hits": {"hits": [{"_source":{"id":"item1"}}, {"_source":{"id":"item2"}}, {"_source":{"id":"item3"}}]}, "pagination": {"next_url": "", "total_pages": 2, "total_hits": 3}}
    with requests_mock.Mocker() as m:
        m.get(page1_url, json=page1_response)
        m.get(page2_url, json=page2_response)
        result = runner.invoke(app, ["search", query, "--model", model, "--all"])
        assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
        output_json = json.loads(result.stdout)
        assert output_json == expected_aggregated_data

def test_search_command_api_error():
    query = "problem_query"
    error_response_json = {"error": "Search failed", "status_code": 500}
    mock_url = f"{api_base_url}/search/works?as=opensearch&size=200&query={query}&_source_excludes=embedding%2A"
    with requests_mock.Mocker() as m:
        m.get(mock_url, status_code=500, json=error_response_json)
        result = runner.invoke(app, ["search", query])
        assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
        output_json = json.loads(result.stdout)
        assert output_json == error_response_json

# === Tests for 'csv' command ===

def test_csv_command_basic():
    query = "csv_query"
    outfile = "output.csv"
    api_response = {"hits": {"hits": [ {"_source": {"id": "1", "title": "CSV Title 1", "author": "AuthA"}}, {"_source": {"id": "2", "title": "CSV Title 2", "subject": "SubjB"}} ]}}
    mock_url = f"{api_base_url}/search/works?as=csv&size=200&query={query}&_source_excludes=embedding%2A"
    with runner.isolated_filesystem():
        with requests_mock.Mocker() as m:
            m.get(mock_url, json=api_response)
            result = runner.invoke(app, ["csv", query, outfile])
            assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
            assert f"saved csv to : {outfile}" in result.stdout
            assert os.path.exists(outfile)
            with open(outfile, 'r', newline='') as f:
                reader = csv_parser.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert reader.fieldnames == sorted(['id', 'title', 'author', 'subject'])
                assert rows[0]['id'] == '1'; assert rows[0]['title'] == 'CSV Title 1'; assert rows[0]['author'] == 'AuthA'; assert rows[0]['subject'] == ''
                assert rows[1]['id'] == '2'; assert rows[1]['title'] == 'CSV Title 2'; assert rows[1]['subject'] == 'SubjB'; assert rows[1]['author'] == ''

def test_csv_command_with_fields():
    query = "specific_fields"
    outfile = "specific.csv"
    fields_arg = "id,title,non_existent_field"
    expected_headers = ["id", "title", "non_existent_field"]
    api_response = {"hits": {"hits": [ {"_source": {"id": "doc1", "title": "Document 1", "creator": "Creator X"}}, {"_source": {"id": "doc2", "title": "Document 2", "non_existent_field": "This actually exists in source"}} ]}}
    fields_query_string = "&".join([f"_source_includes={f}" for f in fields_arg.split(',')])
    mock_url = f"{api_base_url}/search/works?as=csv&size=200&query={query}&{fields_query_string}"
    with runner.isolated_filesystem():
        with requests_mock.Mocker() as m:
            m.get(mock_url, json=api_response)
            result = runner.invoke(app, ["csv", query, outfile, "--fields", fields_arg])
            assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
            assert os.path.exists(outfile)
            with open(outfile, 'r', newline='') as f:
                reader = csv_parser.reader(f)
                headers = next(reader); assert headers == expected_headers
                rows = list(reader); assert len(rows) == 2
                assert rows[0] == ["doc1", "Document 1", ""]
                assert rows[1] == ["doc2", "Document 2", "This actually exists in source"]

def test_csv_command_all_records():
    query = "all_the_csv"
    outfile = "all_items.csv"; model = "works"; fields_arg = "id,title"; expected_headers = ["id", "title"]
    fields_query_string = "&".join([f"_source_includes={f}" for f in fields_arg.split(',')])
    page1_url = f"{api_base_url}/search/{model}?as=csv&size=200&sort=id:asc&query={query}&{fields_query_string}"
    page2_url = f"{api_base_url}/search/{model}?as=csv&size=200&sort=id:asc&query={query}&{fields_query_string}&page=2"
    page1_response = {"hits": {"hits": [{"_source":{"id":"csv1","title":"CSV Page 1 Item 1"}}, {"_source":{"id":"csv2","title":"CSV Page 1 Item 2"}}]}, "pagination": {"next_url": page2_url, "total_pages": 2, "total_hits": 3}}
    page2_response = {"hits": {"hits": [{"_source":{"id":"csv3","title":"CSV Page 2 Item 1"}}]}, "pagination": {"next_url": None, "total_pages": 2, "total_hits": 3}}
    with runner.isolated_filesystem():
        with requests_mock.Mocker() as m:
            m.get(page1_url, json=page1_response); m.get(page2_url, json=page2_response)
            result = runner.invoke(app, ["csv", query, outfile, "--model", model, "--all", "--fields", fields_arg])
            assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
            assert os.path.exists(outfile)
            with open(outfile, 'r', newline='') as f:
                reader = csv_parser.reader(f)
                headers = next(reader); assert headers == expected_headers
                rows = list(reader); assert len(rows) == 3
                assert rows[0] == ["csv1", "CSV Page 1 Item 1"]
                assert rows[1] == ["csv2", "CSV Page 1 Item 2"]
                assert rows[2] == ["csv3", "CSV Page 2 Item 1"]

def test_csv_command_no_results():
    query = "no_results_query"; outfile = "no_results.csv"
    api_response = {"hits": {"hits": []}}
    mock_url = f"{api_base_url}/search/works?as=csv&size=200&query={query}&_source_excludes=embedding%2A"
    with runner.isolated_filesystem():
        with requests_mock.Mocker() as m:
            m.get(mock_url, json=api_response)
            result = runner.invoke(app, ["csv", query, outfile])
            assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
            assert os.path.exists(outfile)
            with open(outfile, 'r', newline='') as f:
                reader = csv_parser.reader(f)
                headers = next(reader); assert headers == ["no results"]
                rows = list(reader); assert len(rows) == 1
                assert rows[0] == ["no results"]

# === Tests for 'xml' command ===

def test_xml_command_basic():
    """Tests basic 'xml' command functionality."""
    query = "xml_query"
    outfile = "output.xml"
    api_response = {"hits": {"hits": [ {"_source": {"id": "xml1", "title": "XML Title 1", "creator": "CreatorC"}}, {"_source": {"id": "xml2", "title": "XML Title 2", "description": "DescD"}} ]}}
    mock_url = f"{api_base_url}/search/works?as=xml&size=200&query={query}&_source_excludes=embedding%2A"
    with runner.isolated_filesystem():
        with requests_mock.Mocker() as m:
            m.get(mock_url, json=api_response)
            result = runner.invoke(app, ["xml", query, outfile])
            assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
            assert f"saved xml to : {outfile}" in result.stdout
            assert os.path.exists(outfile)
            tree = ET.parse(outfile)
            root = tree.getroot()
            assert root.tag == "results"
            hits_element = root.find("hits/hits")
            assert hits_element is not None
            items = hits_element.findall("item")
            assert len(items) == 2
            assert items[0].find("_source/id").text == "xml1"
            assert items[0].find("_source/title").text == "XML Title 1"
            assert items[1].find("_source/description").text == "DescD"

def test_xml_command_with_fields():
    query = "xml_fields_query"
    outfile = "fields.xml"
    fields_arg = "id,title"
    api_response = {"hits": {"hits": [ {"_source": {"id": "xmlf1", "title": "XML Fields 1"}} ]}}
    fields_query_string = "&".join([f"_source_includes={f}" for f in fields_arg.split(',')])
    mock_url = f"{api_base_url}/search/works?as=xml&size=200&query={query}&{fields_query_string}"
    with runner.isolated_filesystem():
        with requests_mock.Mocker() as m:
            m.get(mock_url, json=api_response)
            result = runner.invoke(app, ["xml", query, outfile, "--fields", fields_arg])
            assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
            assert os.path.exists(outfile)
            tree = ET.parse(outfile)
            root = tree.getroot()
            assert root.tag == "results"
            item = root.find("hits/hits/item/_source")
            assert item is not None
            assert item.find("id").text == "xmlf1"
            assert item.find("title").text == "XML Fields 1"
            assert item.find("unwanted_field") is None

def test_xml_command_all_records():
    query = "all_the_xml"; outfile = "all_items.xml"; model = "works"
    page1_url = f"{api_base_url}/search/{model}?as=xml&size=200&sort=id:asc&query={query}&_source_excludes=embedding%2A"
    page2_url = f"{api_base_url}/search/{model}?as=xml&size=200&sort=id:asc&query={query}&_source_excludes=embedding%2A&page=2"
    page1_response = {"hits": {"hits": [{"_source":{"id":"xml_all1","title":"XML All Page 1"}}]}, "pagination": {"next_url": page2_url, "total_pages": 2, "total_hits": 2}}
    page2_response = {"hits": {"hits": [{"_source":{"id":"xml_all2","title":"XML All Page 2"}}]}, "pagination": {"next_url": None, "total_pages": 2, "total_hits": 2}}
    with runner.isolated_filesystem():
        with requests_mock.Mocker() as m:
            m.get(page1_url, json=page1_response); m.get(page2_url, json=page2_response)
            result = runner.invoke(app, ["xml", query, outfile, "--model", model, "--all"])
            assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
            assert os.path.exists(outfile)
            tree = ET.parse(outfile)
            root = tree.getroot()
            assert root.tag == "results"
            hits_element = root.find("hits/hits")
            assert hits_element is not None
            items = hits_element.findall("item")
            assert len(items) == 2
            assert items[0].find("_source/id").text == "xml_all1"
            assert items[1].find("_source/id").text == "xml_all2"
            pagination_next_url = root.find("pagination/next_url")
            assert pagination_next_url is not None and pagination_next_url.text is None

def test_xml_command_no_results():
    query = "no_xml_results"; outfile = "no_results.xml"
    api_response = {"hits": {"hits": []}}
    mock_url = f"{api_base_url}/search/works?as=xml&size=200&query={query}&_source_excludes=embedding%2A"
    with runner.isolated_filesystem():
        with requests_mock.Mocker() as m:
            m.get(mock_url, json=api_response)
            result = runner.invoke(app, ["xml", query, outfile])
            assert result.exit_code == 0, f"CLI Error: {result.stdout} \nException: {result.exception}"
            assert os.path.exists(outfile)
            tree = ET.parse(outfile)
            root = tree.getroot()
            assert root.tag == "results"
            hits_element = root.find("hits/hits")
            assert list(hits_element) == []
