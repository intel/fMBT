#!/bin/bash

# fMBT, free Model Based Testing tool
# Copyright (c) 2012, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU Lesser General Public License,
# version 2.1, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.

# GUI test for fmbt-editor

##########################################
# Setup test environment

cd "$(dirname "$0")"
LOGFILE=/tmp/fmbt.test.editor.log
export PATH=../../src:../../utils:$PATH
export PYTHONPATH=../../src:../../utils:$PYTHONPATH

source ../functions.sh

##########################################
# Check requirements

REQUIRED_BINARIES="Xephyr xwininfo xprop xwd convert tesseract xte"

for binary in $REQUIRED_BINARIES; do
    which $binary >/dev/null 2>&1 || {
        echo "This test requires binaries:"
        echo "$REQUIRED_BINARIES"
        echo ""
        echo "Debian/Ubuntu users can install them with command:"
        echo "sudo apt-get install xserver-xephyr x11-utils x11-apps imagemagick tesseract-ocr xautomation"
        echo ""
        echo "$binary missing"
        exit 1
    }
done

##########################################
# Start new X server for fmbt-editor

# Using 128 dpi (1024 pixels and 200 mm wide)
# to get a big font for OCR

Xephyr -screen 1024/200x768/150 :55 &
export DISPLAY=:55
sleep 1

xterm -geometry 640x512+0+0 &
sleep 0.5

fmbt test.conf