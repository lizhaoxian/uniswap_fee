#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR

mkdir -p log

source environment/bin/activate

SUFFIX=$(TZ=Asia/Singapore date +'%Y%m%d_%H%M%S_SG')

python -u txs.py \
2>&1 | tee -a log/run_txs.log.$SUFFIX