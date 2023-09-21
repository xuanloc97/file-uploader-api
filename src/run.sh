#!/bin/bash

source ../.venv/bin/activate

export FLASK_APP=file_uploader_api
export FLASK_ENV=development
# export FLASK_DEBUG=1

python3 file_uploader_api.py runserver