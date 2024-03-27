#!/usr/bin/env python3

import connexion
from waitress import serve
import logging

from swagger_server import encoder


def main():
    logging.basicConfig(level=logging.DEBUG)

    app = connexion.App(__name__, specification_dir='./swagger/')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('swagger.yaml', arguments={'title': 'Uniswap V3 USDC/ETH Pool Tx Fee API Server'}, pythonic_params=True)
    serve(app, host="0.0.0.0", port=8080)


if __name__ == '__main__':
    main()
