#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR

mkdir -p log

source environment/bin/activate

cd api/server

SUFFIX=$(TZ=Asia/Singapore date +'%Y%m%d_%H%M%S_SG')

DBPATH="${SCRIPT_DIR}/data/db.db" \
python -u -m swagger_server \
2>&1 | tee -a ../../log/loop_swagger.log.$SUFFIX