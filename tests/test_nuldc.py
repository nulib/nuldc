import pytest
from nuldc.helpers import (get_search_results,
                           get_all_search_results,
                           get_all_iiif,
                           get_nested_field,
                           get_work_by_id, 
                           normalize_format,
                           sort_fields_and_values
                           )


@pytest.fixture
def mock_dcapi():
    """This is a factory, it's how you have to do reusable mocks in pytest
i   Pass in a 'next_url' if you want to fake a next page, otherwise pass in ''
    """

    def _mock_dcapi(next_url):
        data = {
            "data": [
                {"id": "1",
                 "title": "1 title",
                 "parent": {"child": "child value1",
                            "label": "parent1 label"},
                 "list": ["1", "2", "3"]},
                {"id": "2",
                 "title": "2 title",
                 'parent': {'child': 'child value2',
                            "label": "parent1 label"},
                 "list": ["1", "2", "3"]}
            ],
            "pagination": {
                "query_url": "https://fake.com",
                "current_page": 1,
                "limit": "10",
                "offset": 0,
                "total_hits": 4,
                "total_pages": 2,
                "next_url": next_url
            },
            "info": {}
        }
        return data
    return _mock_dcapi


@pytest.fixture
def mock_dcapi_iiif():
    """This is a factory, it's how you have to do reusable mocks in pytest
    Pass in a 'next_url' if you want to fake a next page, otherwise pass
    in ''"""

    def _mock_dcapi_iiif(next_url):
        data = {
            "data": [
                {"id": "1", "title": "1 title", "parent": {"child": "child value1"}},
                {"id": "2", "title": "2 title", 'parent': {'child': 'child value2'}}],
            "pagination": {
                "query_url": "https://fake.com",
                "current_page": 1,
                "limit": "10",
                "offset": 0,
                "total_hits": 4,
                "total_pages": 2,
                "next_url": next_url
            },
            "info": {}
        }
        return data
    return _mock_dcapi_iiif


def test_get_all_iiif():
    pass


def test_get_search_results(requests_mock, mock_dcapi):
    requests_mock.get(
        'http://test.com/search',
        json=mock_dcapi("http://test.com/next"))
    single_result = get_search_results('http://test.com', {"query": "test"})
    assert len(single_result['data']) == 2


def test_get_all_search_results(requests_mock, mock_dcapi):
    p1 = mock_dcapi("http://test.com/next")
    p2 = mock_dcapi("")
    requests_mock.get('http://test.com/next', json=p2)
    result = get_all_search_results(p1, 2)
    assert len(result['data']) == 4


def test_get_work_by_id(requests_mock):
    # Make sure it builds the style url and gets it
    requests_mock.get("http://test.com/works/1234", json={"data": "work"})
    work = get_work_by_id("http://test.com", "1234", {"as": "opensearch"})
    assert work['data'] == 'work'


def test_normalize_format(mock_dcapi):
    data = mock_dcapi('')["data"]
    normalized_dict = normalize_format(data[0]["parent"])
    normalized_list = normalize_format(data[0]["list"])
    assert all([normalized_dict == "parent1 label",
                normalized_list == "1|2|3"])


def test_sort_fields_and_values(mock_dcapi):
    all_fields, all_values = sort_fields_and_values(mock_dcapi(''))
    some_fields, some_values = sort_fields_and_values(mock_dcapi(''), fields=['id','title'])
    
    assert all([len(all_fields)==4, 
                len(all_values[0])==4,
                len(some_fields)==2, 
                len(some_values[0])==2, 
                "parent" in all_fields, 
                "parent" not in some_fields]
               )


def test_get_nested_field(mock_dcapi):
    # test grab a nested field
    data = mock_dcapi("")['data'][0]
    parent_assert = data['parent']
    parent = get_nested_field('parent', data)
    child_assert = data['parent']['child']
    child = get_nested_field('parent.child', data)
    # to green this up make if,elif, else: none
    # no_result = get_nested_field('parent.child.nothing.nothing.nothing', mock_dcapi_p1['data'][0])
    assert all([child == child_assert, parent == parent_assert])
