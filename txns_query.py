import time
import sys
import shutil
import os
import pandas as pd
import requests
import sqlite3
import logging
import unittest

# Seconds between query made to etherscan.io
PER_QUERY_GAP_SEC = 6
PER_QUERY_GAP_SEC_BINANCE = 1
MAX_RETRY = 3

logger = logging.getLogger(__name__)


class TxnStore(object):
    """
    class for query and store txns.

    Txns are stored as a queue in DB, we can grow the
    queue by query at its head / tail, tail is the most
    recent txns, head is the least recent.
    """

    def __init__(self, dbpath, startup_block_no):

        """
        Parameters
        ----------
        dbpath : str
            The file location of the sqlite database
        startup_block_no : int
            The most recent block number, only used when db is empty
        """
        logger.info(f'open TxnStore... {dbpath}')

        # At empty DB, this no is used
        self.startup_block_no = startup_block_no

        # Setup DB connections
        self.con = sqlite3.connect(dbpath)
        sql = [
            'CREATE TABLE IF NOT EXISTS txns (',
            'ts INTEGER,',
            'blk_no INTEGER,',
            'hash TEXT,',
            'src TEXT,',
            'dst TEXT,',
            'value TEXT,',
            'token TEXT,',
            'gas_px TEXT,',
            'gas_used TEXT,',
            'eth_usd REAL',
            ');'
        ]
        sql = ''.join(sql)
        self.con.execute(sql)
        self.con.commit()

        # etherscan query rate limiter
        self.ts_next_query = None

        # binance spot price cache, to reduce query
        self.eth_usd_cache = {}

    def get_db_blk_head_tail_ts(self):
        """ Returns the TS for head and tail in txns queue """
        cur = self.con.execute(
            'SELECT ts FROM txns ORDER BY ts ASC LIMIT 1;')
        ts_head = cur.fetchone()
        ts_head = 0 if ts_head is None else int(ts_head[0])

        cur = self.con.execute(
            'SELECT ts FROM txns ORDER BY ts DESC LIMIT 1;')
        ts_tail = cur.fetchone()
        ts_tail = 0 if ts_tail is None else int(ts_tail[0]) + 1

        return ts_head, ts_tail

    def get_db_blk_head_tail(self):
        """ Returns the blockno for head and tail in txns queue """
        cur = self.con.execute(
            'SELECT blk_no FROM txns ORDER BY blk_no ASC LIMIT 1;')
        blk_no_head = cur.fetchone()
        blk_no_head = self.startup_block_no \
            if blk_no_head is None else int(blk_no_head[0])

        cur = self.con.execute(
            'SELECT blk_no FROM txns ORDER BY blk_no DESC LIMIT 1;')
        blk_no_tail = cur.fetchone()
        blk_no_tail = self.startup_block_no \
            if blk_no_tail is None else int(blk_no_tail[0]) + 1

        return blk_no_head, blk_no_tail

    def query_at_head(self, test_hold=False):
        """ Query and Store txns earlier than queue head """
        logger.info('query_at_head ...')
        blk_head, _ = self.get_db_blk_head_tail()
        self.query_from(blk_head - 100, blk_head, test_hold=test_hold)

    def query_at_tail(self, test_hold=False):
        """ Query and Store txns later than queue head """
        logger.info('query_at_tail ...')
        _, blk_tail = self.get_db_blk_head_tail()
        self.query_from(
            blk_tail, blk_tail + 100, test_hold=test_hold, max_retry=0)

    def query_from(
        self, blkno, before_block,
        test_hold=False, check_dup=False, max_retry=MAX_RETRY
    ):
        """ Query and Store txns from blkno till before_block (exclusive) """
        logger.info(f'query_from ... {blkno} {before_block}')

        query_from_blk = blkno
        page = 1
        txns = []
        hash_visited = set()
        error_cnt = 0

        if self.ts_next_query is None:
            self.ts_next_query = int(time.time())

        while True:
            if error_cnt > max_retry:
                break

            # Query freq guard
            ts_now = int(time.time())
            if ts_now < self.ts_next_query:
                time.sleep(self.ts_next_query - ts_now)
                continue
            self.ts_next_query += PER_QUERY_GAP_SEC

            url = _get_qurl_tx(sblk=query_from_blk, page=page, offset=100)

            logger.info(f'{time.time()} query : {url}')
            r = requests.get(url)
            data = r.json()

            if data['status'] != '1':
                error_cnt += 1
                logger.info(f'status : {data["status"]} ERROR_CNT:{error_cnt}')
                logger.info(f'message: {data["message"]}')
                logger.info(f'{query_from_blk} ~ {before_block} done')
                continue

            error_cnt = 0
            page += 1

            items = data['result']
            items = [x for x in items if int(x['blockNumber']) < before_block]
            items = [x for x in items if x['hash'] not in hash_visited]

            if len(items) == 0:
                logger.info(f'{query_from_blk} ~ {before_block} done')
                break

            if page == 10:
                query_from_blk = items[-1]['blockNumber']
                page = 1

            logger.info(f"inc {len(items)} next_page {query_from_blk}-{page}")
            txns += items
            hash_visited = hash_visited.union([x['hash'] for x in items])

        if len(txns) > 0:
            self._save(txns, check_dup)

        # when test, recreate obj will not follow the query gap,
        # we hold before exit
        if test_hold:
            time.sleep(PER_QUERY_GAP_SEC)

    def _is_hash_exists(self, vhash):
        cur = self.con.execute(
            f'SELECT * FROM txns WHERE hash = "{vhash}";')
        records = cur.fetchone()
        return records is not None

    def _save(self, txns, check_dup):
        values = []

        ts_next_query = int(time.time())
        for one in txns:
            vhash = one['hash']
            if check_dup and self._is_hash_exists(vhash):
                continue

            ts = int(one['timeStamp'])
            eth_usd_px, ts_next_query = get_px_eth_usd(
                ts, self.eth_usd_cache, ts_next_query)
            eth_usd_px = f'{eth_usd_px:.2f}'
            value = float(one['value']) / (10**float(one['tokenDecimal']))
            sql = ','.join([
                one['timeStamp'],
                one['blockNumber'],
                f"\"{vhash}\"",
                f"\"{one['from']}\"",
                f"\"{one['to']}\"",
                f"\"{value}\"",
                f"\"{one['tokenSymbol']}\"",
                f"\"{one['gasPrice']}\"",
                f"\"{one['gasUsed']}\"",
                eth_usd_px,
            ])

            sql = f'({sql})'
            values += [sql]

        logger.info(f'INSERT {len(values)} RECORDS ...')
        if len(values) > 0:
            values = ','.join(values)
            sql = f'INSERT INTO txns VALUES {values};'
            self.con.execute(sql)
            self.con.commit()


class TestTxnStore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.INFO)

    def test_get_db_blk_head_tail_ts(self):
        logger.info('test_get_db_blk_head_tail_ts ...')

        shutil.copyfile('data_test/db.db', 'data_test/db.db.temp')

        store = TxnStore('data_test/db.db.temp', 0)
        ts0, ts1 = store.get_db_blk_head_tail_ts()
        self.assertEqual(ts0, 1711252715)
        self.assertEqual(ts1, 1711347840)

        os.remove('data_test/db.db.temp')

    def test_get_db_blk_head_tail(self):
        logger.info('test_get_db_blk_head_tail ...')

        shutil.copyfile('data_test/db.db', 'data_test/db.db.temp')

        store = TxnStore('data_test/db.db.temp', 0)
        blkno0, blkno1 = store.get_db_blk_head_tail()
        self.assertEqual(blkno0, 19501891)
        self.assertEqual(blkno1, 19509702)

        os.remove('data_test/db.db.temp')

    def test_query_at_head(self):
        logger.info('test_query_at_head ...')

        shutil.copyfile('data_test/db.db', 'data_test/db.db.temp')

        store = TxnStore('data_test/db.db.temp', 0)

        blkno0, blkno1 = store.get_db_blk_head_tail()
        self.assertEqual(blkno0, 19501891)
        self.assertEqual(blkno1, 19509702)

        store.query_at_head(test_hold=True)

        blkno0, blkno1 = store.get_db_blk_head_tail()
        self.assertEqual(blkno0, 19501791)
        self.assertEqual(blkno1, 19509702)

        os.remove('data_test/db.db.temp')

    def test_query_at_tail(self):
        logger.info('test_query_at_tail ...')

        shutil.copyfile('data_test/db.db', 'data_test/db.db.temp')

        store = TxnStore('data_test/db.db.temp', 0)

        blkno0, blkno1 = store.get_db_blk_head_tail()
        self.assertEqual(blkno0, 19501891)
        self.assertEqual(blkno1, 19509702)

        store.query_at_tail(test_hold=True)

        blkno0, blkno1 = store.get_db_blk_head_tail()
        self.assertEqual(blkno0, 19501891)
        self.assertEqual(blkno1, 19509795)

        os.remove('data_test/db.db.temp')


def get_px_eth_usd(ts, cache, ts_next_query):
    """
    Query Binance API for price at ts.

    Parameters
    ----------
    ts : int
        timestamp in seconds
    cache : dict
        key-value cache for milliseconds to price
        milliseconds are gapped with 15 minutes
        (to fit with binance data structure)
    """
    ts_query = int(ts / (15 * 60)) * 15 * 60 * 1000
    if ts_query in cache:
        return ts_next_query, cache[ts_query]

    ts_query_early = ts_query - (29 * 15 * 60 * 1000)
    url = 'https://api.binance.com/api/v3/klines?' + \
          f'symbol=ETHUSDT&interval=15m&startTime={ts_query_early}&limit=30'
    try:
        ts_now = int(time.time())
        if ts_now < ts_next_query:
            time.sleep(ts_next_query - ts_now)
        ts_next_query += PER_QUERY_GAP_SEC_BINANCE

        r = requests.get(url)
        logger.info(f'query binance {ts} {ts_query_early} ...')
        for item in r.json():
            k = item[0]
            v = float(item[4])
            if k not in cache:
                cache[k] = v
        return ts_next_query, cache[ts_query]
    except Exception as _:
        return ts_next_query, -1


def _get_base_url():
    return 'https://api.etherscan.io/api'


def _get_qurl_tx(
    contract_address=None,
    address='0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640',
    sblk=0,
    eblk=99999999,
    page=1,
    offset=100
):
    url = [
        _get_base_url(),
        '?module=account',
        '&action=tokentx',
        f'&contractaddress={contract_address}'
        if contract_address is not None else '',
        f'&address={address}',
        f'&page={page}',
        f'&offset={offset}',
        f'&startblock={sblk}',
        f'&endblock={eblk}',
        '&sort=asc',
        '&apikey=YourApiKeyToken',
    ]
    url = ''.join(url)
    return url


def get_qurl_blk_direct(ts):
    url = [
        _get_base_url(),
        '?module=block',
        '&action=getblocknobytime',
        f'&timestamp={ts}',
        '&closest=before',
        '&apikey=YourApiKeyToken',
    ]
    url = ''.join(url)
    return url


def get_qurl_latest_blk_direct(ts):
    return get_qurl_blk_direct(ts)


def query_blkno(ts):
    logger.info('query_blkno ...')

    url = get_qurl_latest_blk_direct(ts)

    error_cnt = 0
    while True:
        try:
            r = requests.get(url)
            data = r.json()

            # make sure the outer query is not exceeding threshold
            time.sleep(PER_QUERY_GAP_SEC)

            logger.info(data['result'])

            return int(data['result'])
        except Exception as _:
            error_cnt += 1

        if error_cnt > 3:
            raise Exception(f'unable to get blkno for {ts}')


def query_blkno_latest():
    ts = int(time.time())
    return query_blkno(ts)


def store_specified_ts_range(dbpath, ts0, ts1):
    store = TxnStore(dbpath, 0)
    blkno0 = query_blkno(ts0)
    blkno1 = query_blkno(ts1)

    blkno2 = blkno0
    blkno3 = blkno2 + 1000
    while True:
        if blkno3 > blkno1:
            blkno3 = blkno1

        if blkno2 > blkno3:
            break

        store.query_from(blkno2, blkno3, check_dup=True)

        if blkno3 == blkno1:
            break

        blkno2 = blkno3
        blkno3 = blkno2 + 1000


def main():
    logging.basicConfig(level=logging.INFO)

    dbpath = sys.argv[1]

    if len(sys.argv) >= 4:
        ts0 = int(sys.argv[2])
        ts1 = int(sys.argv[3])

        store_specified_ts_range(dbpath, ts0, ts1)

        ts0 = pd.Timestamp(float(ts0), unit='s').strftime('%Y%m%d %H:%M:%S')
        ts1 = pd.Timestamp(float(ts1), unit='s').strftime('%Y%m%d %H:%M:%S')
        logger.info(f"query txns period: {ts0} ~ {ts1} UTC")

        return None

    startup_block_no = query_blkno_latest()
    store = TxnStore(dbpath, startup_block_no)

    while True:
        store.query_at_head()
        store.query_at_tail()
        ts0, ts1 = store.get_db_blk_head_tail_ts()
        ts0 = pd.Timestamp(float(ts0), unit='s').strftime('%Y%m%d %H:%M:%S')
        ts1 = pd.Timestamp(float(ts1), unit='s').strftime('%Y%m%d %H:%M:%S')
        logger.info(f"covered txns period: {ts0} ~ {ts1} UTC")


if __name__ == '__main__':
    main()
