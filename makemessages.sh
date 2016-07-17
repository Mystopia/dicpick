#!/usr/bin/env bash

pushd dicpick

../venv/bin/python ../manage.py makemessages --all

popd
