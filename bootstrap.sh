#!/bin/sh

COMMONS_VERSION=0.1.23
COMMONS=materiality.commons-${COMMONS_VERSION}

if [ ! -e .bootstrap/src ]; then
    mkdir -p .bootstrap
    curl https://github.com/benjyw/materiality.commons/archive/v${COMMONS_VERSION}.zip \
      -o .bootstrap/${COMMONS}.zip -sSL
    unzip .bootstrap/${COMMONS}.zip -d .bootstrap
    ln -s ${COMMONS}/src .bootstrap/src
fi
