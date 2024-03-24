# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.txn import Txn  # noqa: E501
from swagger_server.test import BaseTestCase


class TestTxController(BaseTestCase):
    """TxController integration test stubs"""

    def test_tx_get(self):
        """Test case for tx_get

        List Txns
        """
        query_string = [('from_timestamp', 56)]
        response = self.client.open(
            '/api/v1/tx',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_tx_hash_get(self):
        """Test case for tx_hash_get

        Find Tx by Hash
        """
        response = self.client.open(
            '/api/v1/tx/{hash}'.format(hash='hash_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
