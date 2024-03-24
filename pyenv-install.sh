#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR

source environment/bin/activate

pip install -r requirements.txt

# pip3 install virtualenv
# virtualenv environment
# source environment/bin/activate
# python -m pip freeze > requirements.txt
# pip install -r requirements.txt
