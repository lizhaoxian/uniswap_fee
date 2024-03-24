import connexion
import six

from swagger_server.models.txn import Txn  # noqa: E501
from swagger_server import util


def tx_get(from_timestamp):  # noqa: E501
    """List Txns

     # noqa: E501

    :param from_timestamp: 
    :type from_timestamp: int

    :rtype: List[Txn]
    """
    return 'do some magic!'


def tx_hash_get(hash):  # noqa: E501
    """Find Tx by Hash

     # noqa: E501

    :param hash: 
    :type hash: str

    :rtype: List[Txn]
    """
    return 'do some magic!'
