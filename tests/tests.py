import unittest
from nuldc.helpers import get_search_results, get_all_search_results, get_nested_field

from unittest.mock import patch
import json

mock_os_response = {
                "data": [
                    {"id":"1", "title":"1 title", "parent":{"child":"child value1"}},
                    {"id":"2", "title": "2 title", 'parent':{'child':'child value2'}}], 
                "pagination": {
                    "query_url": "https://fake.com",
                    "current_page": 1,
                    "limit": "10",
                    "offset": 0,
                    "total_hits": 2,
                    "total_pages": 2,
                    "next_url": "https://fake.com/next"
                    },
                "info": {}
                }
            

mock_os_response_page2 = {
                "data": [
                    {"id":"3", 
                        "title":"1 title"},
                    {"id":"4", 
                        "title": "2 title"}], 
                "pagination": {
                    "query_url": "https://fake.com",
                    "current_page": 1,
                    "limit": "10",
                    "offset": 0,
                    "total_hits": 2,
                    "total_pages": 2,
                    "next_url": ""
                    },
                "info": {}
                }

class BasicTests(unittest.TestCase):
    """All the basic tests. Currently a placeholder for future work"""

    def test_get_search_results(self):
        with patch('nuldc.helpers.requests.get') as mock_get:
            mock_get.return_value.json.return_value = dict(mock_os_response) 
            single_result = get_search_results('https://mock',{'query':'a search'})
            self.assertEqual(len(single_result['data']), 2)

    def test_get_all_search_results(self):
        with patch('nuldc.helpers.requests.get') as mock_get:
            mock_get.return_value.json.return_value = mock_os_response_page2
            start = dict(mock_os_response)
            all_results = get_all_search_results(start, 2)
            self.assertEqual(len(all_results['data']), 4)

    def test_get_all_search_results_over_limit(self):
        with patch('nuldc.helpers.requests.get') as mock_get:
            mock_get.return_value.json.return_value = mock_os_response_page2
            start = dict(mock_os_response)
            #fire off an all results with small limit
            all_results = get_all_search_results(start, 1)
            self.assertEqual(all_results['message'], "2 pages! Let's keep it under 2. Refine your search")
    
    def test_get_nested_field(self):
        field1 = get_nested_field('title', mock_os_response['data'][0]) 
        field2 = get_nested_field('parent.child', mock_os_response['data'][1])
        self.assertEqual(field1, '1 title')
        self.assertEqual(field2, 'child value2')


if __name__ == "__main__":
    unittest.main()
