#!/bin/bash

cd "$(dirname "$0")"
TESTHOME=$(pwd)

cd ..
export PATH=$(pwd):$PATH
export PYTHONPATH=$(pwd):$PYTHONPATH
cd "$TESTHOME"

fmbt-trace-share -K
fmbt-trace-share -S

FMBT_PIDS=""

for RD_TEST_PORT in 64440 64441 64442 64443 64444 64445 64446 64447 64448 64449; do
    export RD_TEST_PORT
    export REMOTEDEVICES_SERVER=localhost:$RD_TEST_PORT
    fmbt \
        -o "model=aal_remote(remote_pyaal -l rd.aal.$RD_TEST_PORT.log rd.aal)" \
        -l perms-parallel.$RD_TEST_PORT.log \
        perms-parallel.conf &
    FMBT_PID=$!
    FMBT_PIDS="$FMBT_PIDS $FMBT_PID"
    echo "launched: $FMBT_PID"
    sleep 4
done

echo "waiting: $FMBT_PIDS"
eval wait $FMBT_PIDS
