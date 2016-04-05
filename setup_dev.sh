#!/bin/sh
./verify_venv.sh
./venv/bin/python2.7 -m materiality.util.setup_dev --app-name=dicpick
