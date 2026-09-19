#!/usr/bin/env bash

if ! pip3 install -r requirements.txt --user; then
    echo "ERROR: pip3 failed"
    exit 1
fi

exit 0
