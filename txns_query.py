import time
import pandas as pd
import requests


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


def get_qurl_latest_blk():
    url = [
        get_base_url(),
        '?module=block',
        '&action=getblockcountdown',
        '&blockno=99999999',
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
    url = get_qurl_latest_blk()
    r = requests.get(url)
    data = r.json()
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


query()
