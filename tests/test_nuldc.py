import pytest
from unittest import mock
import os
import sys
import json # For JSONDecodeError and its use in tests
import unicodecsv as csv
import dicttoxml
import requests
import requests_mock

from nuldc import helpers
from nuldc.helpers import (get_search_results,
                           get_all_search_results,
                           get_all_iiif,
                           get_collection_by_id,
                           get_nested_field,
                           get_work_by_id,
                           normalize_format,
                           sort_fields_and_values,
                           save_as_csv,
                           save_xml,
                           aggregate_by
                           )

@pytest.fixture
def rich_mock_dcapi_data():
    """Provides a richer data structure for testing normalize_format and sort_fields_and_values."""
    return {
        "data": [
            {"id": "1", "title": "1 title", "parent": {"child": "child value1", "label": "parent1 label"}, "list": ["1", "2", "3"], "embedding": [0.9, 0.8, 0.7, 0.6]},
            {"id": "2", "title": "2 title", "parent": {"child": "child value2", "label": "parent2 label"}, "list": ["4", "5"], "embedding": [0.5, 0.4]}
        ],
        "pagination": {"total_hits": 2, "total_pages": 1, "next_url": ""},
        "info": {}
    }

@pytest.fixture
def mock_dcapi():
    """This is a factory for general API mock responses."""
    def _mock_dcapi(next_url, total_hits=2, total_pages=1, current_page=1,
                    data_content_list=None,
                    is_search_hits=False):

        items_to_embed = data_content_list
        if items_to_embed is None:
             items_to_embed = [
                {"id": f"item_pg{current_page}_1", "title": f"Title Page {current_page} Item 1"},
                {"id": f"item_pg{current_page}_2", "title": f"Title Page {current_page} Item 2"}
            ]

        response = {
            "pagination": {
                "query_url": "https://fake.com",
                "current_page": current_page,
                "limit": str(len(items_to_embed if items_to_embed else [])),
                "offset": (current_page - 1) * len(items_to_embed if items_to_embed else []),
                "total_hits": total_hits,
                "total_pages": total_pages,
                "next_url": next_url
            },
            "info": {}
        }
        if is_search_hits:
            response["hits"] = {"hits": [{"_source": item} for item in items_to_embed]}
        else:
            response["data"] = items_to_embed
        return response
    return _mock_dcapi

@pytest.fixture
def mock_dcapi_iiif():
    """This is a factory for IIIF mock responses."""
    def _mock_dcapi_iiif(next_page_id="https://example.org/iiif/paged-2.json", item_count=2, current_page_id="https://example.org/iiif/paged-1.json"):
        items = []
        for i in range(1, item_count + 1):
            items.append({
                "id": f"https://example.org/iiif/result-page{current_page_id.split('-')[-1].split('.')[0]}-{i}.json",
                "type": "Manifest",
                "label": {"none": [f"Result {i} on page {current_page_id.split('-')[-1].split('.')[0]}"]}
            })
        if next_page_id:
            items.append({ "id": next_page_id, "type": "Collection", "label": {"none": ["Next Page"]} })
        return {
            "@context": "http://iiif.io/api/presentation/3/context.json", "id": current_page_id,
            "type": "Collection", "label": {"none": [f"Paged Collection - {current_page_id}"]}, "items": items
        }
    return _mock_dcapi_iiif

def test_get_all_iiif(requests_mock, mock_dcapi_iiif):
    page1_id = "http://test.com/iiif/page1.json"; page2_id = "http://test.com/iiif/page2.json"
    p1 = mock_dcapi_iiif(next_page_id=page2_id, item_count=2, current_page_id=page1_id)
    p2 = mock_dcapi_iiif(next_page_id=None, item_count=1, current_page_id=page2_id)
    requests_mock.get(page2_id, json=p2)
    result = get_all_iiif(p1, total_pages=2, total_hits=3)
    assert len(result['items']) == 3
    assert all(item.get("type") == "Manifest" for item in result['items'])

def test_get_all_search_results(requests_mock, mock_dcapi):
    p1_data = mock_dcapi(next_url="http://test.com/next_data", total_hits=4, total_pages=2, current_page=1, data_content_list=[{"id":"d1"}, {"id":"d2"}])
    p2_data = mock_dcapi(next_url="", total_hits=4, total_pages=2, current_page=2, data_content_list=[{"id":"d3"}, {"id":"d4"}])
    requests_mock.get('http://test.com/next_data', json=p2_data)
    result_data = get_all_search_results(p1_data)
    assert len(result_data['data']) == 4
    assert result_data['pagination']['next_url'] == ""

    p1_hits = mock_dcapi(next_url="http://test.com/next_hits", total_hits=3, total_pages=2, current_page=1, data_content_list=[{"id":"h1"}], is_search_hits=True)
    p2_hits = mock_dcapi(next_url="", total_hits=3, total_pages=2, current_page=2, data_content_list=[{"id":"h2"}, {"id":"h3"}], is_search_hits=True)
    requests_mock.get('http://test.com/next_hits', json=p2_hits)
    result_hits = get_all_search_results(p1_hits)
    assert len(result_hits['hits']['hits']) == 3
    assert result_hits['pagination']['next_url'] == ""

def test_get_nested_field(rich_mock_dcapi_data):
    data = rich_mock_dcapi_data['data'][0]
    assert get_nested_field('parent', data) == data['parent']
    assert get_nested_field('parent.child', data) == data['parent']['child']
    assert get_nested_field('parent.child.nothing', data) is None
    assert get_nested_field('list', data) == data['list']
    assert get_nested_field('list.0', data) is None

def test_get_search_results(requests_mock, mock_dcapi):
    requests_mock.get('http://test.com/search/works', json=mock_dcapi(next_url="http://test.com/next"))
    single_result = get_search_results('http://test.com', 'works', {"query": "test"})
    assert len(single_result['data']) == 2

def test_get_work_by_id(requests_mock):
    requests_mock.get("http://test.com/works/1234", json={"id": "1234", "title": "work"})
    work = get_work_by_id("http://test.com", "1234", {"as": "opensearch"})
    assert work['title'] == 'work'

def test_get_collection_by_id(requests_mock):
    requests_mock.get("http://test.com/collections/1234", json={"id": "1234", "title": "collection"})
    collection = get_collection_by_id("http://test.com", "1234", {"as": "opensearch"})
    assert collection['title'] == 'collection'

def test_normalize_format(rich_mock_dcapi_data):
    data_item = rich_mock_dcapi_data["data"][0]
    assert normalize_format(data_item["parent"]) == "parent1 label"
    assert normalize_format(data_item["list"]) == "1|2|3"
    assert normalize_format(data_item["embedding"]) == "0.9|0.8|0.7|0.6"
    assert normalize_format(None) == ""
    assert normalize_format("simple string") == "simple string"
    assert normalize_format([{"label":"L1"}, {"no_label":"NL2"}]) == "L1|{'no_label': 'NL2'}"
    assert normalize_format([10, 20]) == "10|20"

def test_sort_fields_and_values(rich_mock_dcapi_data):
    api_response = rich_mock_dcapi_data
    all_fields, all_values = sort_fields_and_values(api_response)
    expected_fields = sorted(['id', 'title', 'parent', 'list', 'embedding'])
    assert all_fields == expected_fields; assert len(all_values) == 2
    first_item_map = {'embedding': "0.9|0.8|0.7|0.6", 'id': "1", 'list': "1|2|3", 'parent': "parent1 label", 'title': "1 title"}
    assert all_values[0] == [first_item_map[field] for field in expected_fields]

    api_response_hits = {"hits": {"hits": [{"_source": rich_mock_dcapi_data['data'][0]}, {"_source": rich_mock_dcapi_data['data'][1]}]}}
    all_fields_hits, all_values_hits = sort_fields_and_values(api_response_hits)
    assert all_fields_hits == expected_fields
    assert all_values_hits[0] == [first_item_map[field] for field in expected_fields]

@mock.patch("builtins.open", new_callable=mock.mock_open)
@mock.patch("unicodecsv.writer")
def test_save_as_csv(mock_csv_writer, mock_file_open):
    h = ["h1","h2"]; v = [["v1","v2"]]; fn = "f.csv"
    save_as_csv(h,v,fn); mock_file_open.assert_called_with(fn,'wb')
    mock_csv_writer.return_value.writerow.assert_has_calls([mock.call(h),mock.call(v[0])])

@mock.patch("builtins.open", new_callable=mock.mock_open)
@mock.patch("nuldc.helpers.dicttoxml.dicttoxml")
def test_save_xml(mock_d2x, mock_open):
    d = {"k":"v"}; fn="f.xml"; x = b"<r/>"; mock_d2x.return_value = x
    save_xml(d,fn); mock_open.assert_called_with(fn,'wb'); mock_d2x.assert_called_with(d,custom_root='results',attr_type=False); mock_open().write.assert_called_with(x)

def test_aggregate_by(requests_mock):
    url="http://a.b/s"; q="q"; f="f"; s=10; pay={"size":"0","query":{"query_string":{"query":q}},"aggs":{f:{"terms":{"field":f,"size":s}}}}; resp={"aggs":{}}
    requests_mock.post(url,json=resp); r=aggregate_by(url,q,f,s); assert r.json()==resp; assert requests_mock.last_request.json()==pay

# === Coverage Improvement Tests ===
@mock.patch('nuldc.helpers.session.get')
def test_get_all_search_results_network_error(mock_get, mock_dcapi, capsys):
    p1 = mock_dcapi(next_url="http://err.next", data_content_list=[{"id":"1"}], total_pages=2)
    mock_get.side_effect = requests.exceptions.RequestException("Network Error")
    res = get_all_search_results(p1);
    assert len(res.get('data', res.get('hits', {}).get('hits', []))) == 1
    assert "Network Error" in capsys.readouterr().err

@mock.patch('nuldc.helpers.session.get')
def test_get_all_search_results_json_error(mock_get, mock_dcapi, capsys):
    p1 = mock_dcapi(next_url="http://err.json", data_content_list=[{"id":"1"}], total_pages=2)
    mock_resp = mock.Mock(); mock_resp.raise_for_status=mock.Mock(); mock_resp.json.side_effect=json.JSONDecodeError("JSON Error","doc",0)
    mock_get.return_value = mock_resp
    res = get_all_search_results(p1);
    assert len(res.get('data', res.get('hits', {}).get('hits', []))) == 1
    assert "JSON decode error" in capsys.readouterr().err

@mock.patch('sys.exit')
@mock.patch('builtins.print')
def test_gass_hit_limit(mock_print, mock_exit, mock_dcapi):
    d = mock_dcapi(None, total_hits=helpers.HIT_LIMIT + 1)
    get_all_search_results(d);
    mock_print.assert_any_call(f'{helpers.HIT_LIMIT+1} total results! The API can only return less than 50,000 at a time. Try breaking it up by collection', file=sys.stderr)
    mock_exit.assert_called_with(1)

@mock.patch('builtins.print')
def test_gass_missing_pagination(mock_print, mock_dcapi, requests_mock):
    d_no_hits = mock_dcapi("http://n.h", total_hits=None, data_content_list=[{"id":"1"}])
    requests_mock.get("http://n.h", json=mock_dcapi(None, total_hits=0, data_content_list=[{"id":"2"}]))
    get_all_search_results(d_no_hits);
    mock_print.assert_any_call(f"Warning: total_hits missing. API limit check might be unreliable. Results ID: Unknown", file=sys.stderr)

    mock_print.reset_mock()
    d_no_pages = mock_dcapi("http://n.p", total_pages=None, data_content_list=[{"id":"3"}])
    requests_mock.get("http://n.p", json=mock_dcapi(None, total_pages=0, data_content_list=[{"id":"4"}]))
    get_all_search_results(d_no_pages);
    mock_print.assert_any_call(f"Warning: total_pages missing. TQDM progress bar may not be accurate. Results ID: Unknown", file=sys.stderr)

@mock.patch('nuldc.helpers.get_all_iiif')
@mock.patch('nuldc.helpers.session.get')
def test_get_collection_by_id_all_iiif(mock_get, mock_gaiiif, mock_dcapi_iiif):
    id="c1"; p={'as':'iiif','model':'works'}; first=mock_dcapi_iiif(); cnt={"pagination":{"total_pages":3,"total_hits":30}}
    mock_get.side_effect = [mock.Mock(json=lambda:first), mock.Mock(json=lambda:cnt)]
    get_collection_by_id(helpers.api_base_url,id,p,all_results=True)
    search_params = mock_get.call_args_list[1][1]['params']
    assert search_params['query'] == f'collection.id:"{id}"'
    mock_gaiiif.assert_called_with(first,3,30)

@mock.patch('nuldc.helpers.get_all_iiif')
@mock.patch('nuldc.helpers.session.get')
def test_get_search_results_all_iiif(mock_get, mock_gaiiif, mock_dcapi_iiif):
    q="q"; m="works"; p={'as':'iiif','query':q}; first=mock_dcapi_iiif(); cnt={"pagination":{"total_pages":5,"total_hits":50}}
    mock_get.side_effect = [mock.Mock(json=lambda:first), mock.Mock(json=lambda:cnt)]
    get_search_results(helpers.api_base_url,m,p,all_results=True)
    count_params = mock_get.call_args_list[1][1]['params']
    assert count_params['as'] == 'opensearch'; assert count_params['query'] == q
    mock_gaiiif.assert_called_with(first,5,50)

@mock.patch("builtins.open",new_callable=mock.mock_open)
@mock.patch("nuldc.helpers.dicttoxml.dicttoxml")
@mock.patch("builtins.print")
def test_save_xml_invalid_input(mock_print, mock_d2x, mock_open):
    fn="e.xml"; inp=[]; err_xml=b"<r/>"; mock_d2x.return_value=err_xml
    save_xml(inp,fn);
    mock_print.assert_any_call(f"Warning: save_xml expected a dict, got {type(inp)}. XML output might be incorrect or empty.", file=sys.stderr)
    mock_d2x.assert_called_with({'error':'Invalid data type for XML conversion','type':str(type(inp))}, custom_root='results',attr_type=False)
    mock_open().write.assert_called_with(err_xml)

def test_sort_fields_and_values_edge_cases():
    assert sort_fields_and_values({"data":[]}) == (["no results"], [["no results"]])
    assert sort_fields_and_values({"hits":{"hits":[]}}) == (["no results"], [["no results"]])
    assert sort_fields_and_values({}) == (["no results"], [["no results"]])
    assert sort_fields_and_values({"data": None}) == (["no results"], [["no results"]])

    response_data_mixed = {"data": [{"id": "1", "val": "a"}, "string_item", {"id": "2", "val": "b", "extra":"foo"}]}
    fields, values = sort_fields_and_values(response_data_mixed, fields=[])
    assert sorted(fields) == sorted(["id", "val", "extra", "error_value"])
    actual_values_as_dicts = [dict(zip(fields, v)) for v in values]
    assert {"id": "1", "val": "a", "extra": "", "error_value": ""} in actual_values_as_dicts
    assert {"id": "", "val": "", "extra": "", "error_value": "string_item"} in actual_values_as_dicts
    assert {"id": "2", "val": "b", "extra": "foo", "error_value": ""} in actual_values_as_dicts
    assert len(values) == 3

    fields_specified_input = ["id", "val"]
    returned_headers, values_spec = sort_fields_and_values(response_data_mixed, fields=fields_specified_input)
    assert returned_headers == fields_specified_input
    assert values_spec[0] == ["1", "a"]
    assert values_spec[1] == ["", ""]
    assert values_spec[2] == ["2", "b"]

def test_sort_fields_and_values_empty_fields_list_with_data(rich_mock_dcapi_data):
    api_response = rich_mock_dcapi_data
    derived_fields, _ = sort_fields_and_values(api_response, fields=[])
    expected_derived_fields = sorted(['id', 'title', 'parent', 'list', 'embedding'])
    assert derived_fields == expected_derived_fields
