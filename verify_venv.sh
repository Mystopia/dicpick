#!/bin/sh
# Note: On osx you may need to run this script thus:
# env CRYPTOGRAPHY_OSX_NO_LINK_FLAGS=1 LDFLAGS="$(brew --prefix openssl)/lib/libssl.a $(brew --prefix openssl)/lib/libcrypto.a" CFLAGS="-I$(brew --prefix openssl)/include"
# in order to get cryptography to build properly.
PYTHONPATH=.bootstrap/src/python python2.7 -m materiality.util.verify_venv
