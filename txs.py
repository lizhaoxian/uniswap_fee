import requests

def query():
    url = [
'https://api.etherscan.io/api',
'?module=account',
'&action=tokentx',
'&contractaddress=0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2',
'&address=0x4e83362442b8d1bec281594cea3050c8eb01311c',
'&page=1',
'&offset=100',
'&startblock=0',
'&endblock=27025780',
'&sort=asc',
'&apikey=YourApiKeyToken',
    ]
    url = ''.join(url)

    requests.get(url)