import connexion
import six
import os
import sqlite3

from swagger_server.models.txn import Txn  # noqa: E501
from swagger_server import util


def tx_get(from_timestamp):  # noqa: E501
    """List Txns

     # noqa: E501

    :param from_timestamp:
    :type from_timestamp: int

    :rtype: List[Txn]
    """
    dbpath = os.environ['DBPATH']
    con = sqlite3.connect(dbpath)
    sql = f'SELECT * FROM txns WHERE ts > {from_timestamp} ORDER BY ts ASC LIMIT 100;'
    cur = con.execute(sql)
    items = cur.fetchall()
    txn_list = []
    for one in items:
        ts = one[0]
        gas_px = float(one[7]) / 1_000_000_000
        gas_used = float(one[8]) / 1_000_000_000
        fee_eth = gas_px * gas_used
        fee_usd = fee_eth * float(one[9])
        txn_list.append(
            Txn(
                timestamp=ts,
                hash=one[2],
                address_from=one[3],
                address_to=one[4],
                value=one[5],
                token=one[6],
                fee_eth=fee_eth,
                fee_usd=fee_usd if fee_usd > 0 else 0,
            )
        )
    return txn_list


def tx_hash_get(hash_):  # noqa: E501
    """Find Tx by Hash

     # noqa: E501

    :param hash_:
    :type hash_: str

    :rtype: List[Txn]
    """
    dbpath = os.environ['DBPATH']
    con = sqlite3.connect(dbpath)
    sql = f'SELECT * FROM txns WHERE hash = "{hash_}" LIMIT 1;'
    cur = con.execute(sql)
    items = cur.fetchall()
    txn_list = []
    for one in items:
        ts = one[0]
        gas_px = float(one[7]) / 1_000_000_000
        gas_used = float(one[8]) / 1_000_000_000
        fee_eth = gas_px * gas_used
        fee_usd = fee_eth * float(one[9])
        txn_list.append(
            Txn(
                timestamp=ts,
                hash=one[2],
                address_from=one[3],
                address_to=one[4],
                value=one[5],
                token=one[6],
                fee_eth=fee_eth,
                fee_usd=fee_usd if fee_usd > 0 else 0,
            )
        )
    return txn_list
