import os, sys, unittest, logging

from hca.query import DCPQueryClient
from hca.util.exceptions import SwaggerAPIException

logging.basicConfig()


class TestDCPQueryClient(unittest.TestCase):
    def setUp(self):
        self.client = DCPQueryClient()

    def test_dcpquery_client(self):
        query = "select count(*) from files"
        res = self.client.post_query(query=query)
        self.assertEqual(res["query"], query)
        self.assertGreater(res["results"][0]["count"], 0)

        invalid_queries = ["select count(*) from nonexistent_table", "*", "", None]
        for query in invalid_queries:
            with self.assertRaises(SwaggerAPIException):
                self.client.post_query(query=query)


if __name__ == "__main__":
    unittest.main()
