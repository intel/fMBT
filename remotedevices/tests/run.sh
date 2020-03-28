#!/bin/bash

cd "$(dirname "$0")"
TESTHOME=$(pwd)

cd ..
export PATH=$(pwd):$PATH
export PYTHONPATH=$(pwd):$PYTHONPATH
cd "$TESTHOME"

( fmbt smoke.conf | tee smoke.log ) && ( fmbt perms.conf | tee perms.log )
