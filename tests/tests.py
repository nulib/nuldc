import unittest
from nuldc.helpers import get_search_results 
from unittest.mock import patch
import json

class BasicTests(unittest.TestCase):
    """All the basic tests. Currently a placeholder for future work"""

    mock_os_response = {
                    "data": [
                        {"id":"1", "title":"1 title"},{"id":"2", "title": "2 title"}], 
                    "pagination": {
                        "query_url": "https://fake.com",
                        "current_page": 1,
                        "limit": "10",
                        "offset": 0,
                        "total_hits": 20,
                        "total_pages": 2,
                        "next_url": "https://fake.com/next"
                        },
                    "info": {}
                    }
                

    @patch('nuldc.helpers.requests.get')
    def test_get_work(self, mock_get):

        mock_get.return_value.json.return_value = self.mock_os_response 
        r = get_search_results('https://mock',{'query':'a search'})
        self.assertEqual(r['data'][0]['id'], '1') 

if __name__ == "__main__":
    unittest.main()
