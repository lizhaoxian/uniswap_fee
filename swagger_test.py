import time
import sys
import requests
import logging

logger = logging.getLogger(__name__)


def test_get_by_ts(hostname='0.0.0.0'):
    logger.info('test_get_by_ts ...')

    r = requests.get(f'http://{hostname}:8080/api/v1/tx', params={'from_timestamp': '1'})
    if r.status_code == 200 and len(r.json()) == 100:
        pass
    else:
        raise Exception('failed @ test_get_by_ts')


def test_get_by_hash(hostname='0.0.0.0'):
    logger.info('test_get_by_hash ...')

    vhash = '0x9982b308dbbd76cea28e92ab886bca740bea9e303655ba98435d2d9f2d2e30e1'
    r = requests.get(f'http://{hostname}:8080/api/v1/tx/{vhash}')
    if r.status_code == 200 and len(r.json()) == 1:
        pass
    else:
        raise Exception('failed @ test_get_by_hash')


def main():
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1:
        boot_time_secs = int(sys.argv[1])
    else:
        boot_time_secs = 0
    time.sleep(boot_time_secs)

    if len(sys.argv) > 2:
        hostname = sys.argv[2]
    else:
        hostname = '0.0.0.0'

    test_get_by_ts(hostname=hostname)
    test_get_by_hash(hostname=hostname)

    logger.info('all test passed')


if __name__ == '__main__':
    main()
