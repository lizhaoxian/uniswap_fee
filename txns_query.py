import time
import sys
import os
import pandas as pd
import requests
import sqlite3

BLK_NO = 19503561

class TxnStore(object):
    def __init__(self, dbpath):
        print(f'open TxnStore... {dbpath}')

        self.con = sqlite3.connect(dbpath)
        sql = ['CREATE TABLE IF NOT EXISTS txns ('
            'ts INTEGER,',
            'blk_no INTEGER,',
            'hash TEXT,',
            'src TEXT,',
            'dst TEXT,',
            'value TEXT,',
            'token TEXT,',
            'gas_px TEXT,',
            'gas_used TEXT',
        ');']
        sql = ''.join(sql)
        self.con.execute(sql)
        self.con.commit()

        self.ts_next_query = int(time.time())

    def get_cache_blk_head_tail(self):
        cur = self.con.execute('SELECT blk_no FROM txns ORDER BY blk_no ASC LIMIT 1;');
        blk_no_head = cur.fetchone()
        blk_no_head = BLK_NO if blk_no_head is None else int(blk_no_head[0])

        cur = self.con.execute('SELECT blk_no FROM txns ORDER BY blk_no DESC LIMIT 1;');
        blk_no_tail = cur.fetchone()
        blk_no_tail = BLK_NO if blk_no_tail is None else int(blk_no_tail[0]) + 1

        return blk_no_head, blk_no_tail

    def query_at_head(self):
        blk_head, _ = self.get_cache_blk_head_tail()

        query_from_blk = blk_head - 100
        page = 1
        txns = []

        while True:
            # Query freq guard
            ts_now = int(time.time())
            if ts_now < self.ts_next_query:
                time.sleep(self.ts_next_query - ts_now + 1)
                continue
            self.ts_next_query += 6

            url = get_qurl_tx(sblk=query_from_blk, page=page, offset=100)
            page += 1

            r = requests.get(url)
            data = r.json()

            if data['status'] != '1':
                print('status :', data['status'])
                print('message:', data['message'])
                print(f'{query_from_blk} done')
                break

            items = data['result']
            items = [x for x in items if int(x['blockNumber']) < blk_head]

            if len(items) == 0:
                print(f'{query_from_blk} done')
                break

            print(f"inc {len(items)} next_page {page}")
            pdata(items)
            txns += items

        if len(txns) > 0:
            self.save(txns)

    def save(self, txns):
        values = []

        for one in txns:
            sql = ','.join([
                one['timeStamp'],
                one['blockNumber'],
                f"\"{one['hash']}\"",
                f"\"{one['from']}\"",
                f"\"{one['to']}\"",
                f"\"{one['value']}\"",
                f"\"{one['tokenSymbol']}\"",
                f"\"{one['gasPrice']}\"",
                f"\"{one['gasUsed']}\"",
            ])

            sql = f'({sql})'
            values += [sql]

        values = ','.join(values)
        sql = f'INSERT INTO txns VALUES {values};'
        self.con.execute(sql)
        self.con.commit()


def get_base_url():
    return 'https://api.etherscan.io/api'


def get_qurl_tx(
    contract_address=None,  #'0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2'
    address='0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640',
    sblk=0,
    eblk=99999999,
    page=1,
    offset=100
):
    url = [
        get_base_url(),
        '?module=account',
        '&action=tokentx',
        f'&contractaddress={contract_address}' if contract_address is not None else '',
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


def get_qurl_latest_blk(blockno=18999999):
    url = [
        get_base_url(),
        '?module=block',
        '&action=getblockcountdown',
        f'&blockno={blockno}',
        '&apikey=YourApiKeyToken',
    ]
    url = ''.join(url)
    return url


def pdata(lst):
    for one in lst:
        ts = pd.Timestamp(float(one['timeStamp']), unit='s')
        ts = ts.strftime('%Y%m%d %H:%M:%S UTC')
        nodigit = float(one['tokenDecimal'])
        blkno = one['blockNumber']
        src = one['from']
        dst = one['to']
        qty = float(one['value']) / (10**nodigit)
        tok = one['tokenSymbol']
        gas = float(one['gas']) / 1_000_000_000
        gaspx = float(one['gasPrice']) / 1_000_000_000
        print(ts, blkno, src, '>>>', dst, f'{qty:.2f}{tok} ({gas*gaspx:.2f}ETH)')


def query_first_blk():
    url = get_qurl_tx(offset=3)
    r = requests.get(url)
    data = r.json()
    sblk = data['result']['blockNumber']
    return sblk


def query_latest_blk():
    blockno = 18999999

    while True:
        url = get_qurl_latest_blk(blockno=blockno)
        blockno += 1_000_000
        r = requests.get(url)
        data = r.json()
        if data['status'] == '1':
            break

    return data['result']['CurrentBlock']


def query():
    txns = []
    page = 1
    ts_next_query = int(time.time())

    while True:
        # Query freq guard
        ts_now = int(time.time())
        if ts_now < ts_next_query:
            time.sleep(ts_next_query - ts_now + 1)
            continue
        ts_next_query += 6

        # per page
        url = get_qurl_tx(page=page)
        page += 1

        r = requests.get(url)
        data = r.json()

        if data['status'] != '1':
            print('status :', data['status'])
            print('message:', data['message'])
            break

        if len(data['result']) == 0:
            break

        print(f"inc {len(data['result'])}")
        pdata(data['result'])
        txns += data['result']


dbpath = sys.argv[1]
store = TxnStore(dbpath)

print(store.get_cache_blk_head_tail())

while True:
    store.query_at_head()
