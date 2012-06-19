/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2012, Intel Corporation.
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms and conditions of the GNU Lesser General Public License,
 * version 2.1, as published by the Free Software Foundation.
 *
 * This program is distributed in the hope it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
 * more details.
 *
 * You should have received a copy of the GNU Lesser General Public License along with
 * this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.
 *
 */

#include <sys/types.h>

extern "C" {

    typedef struct _bbox {
        int32_t left, top, right, bottom;
        int32_t error;
    } BoundingBox;

    /*
     * findSingleIcon
     *
     * Parameters:
     *   - bbox for returning found icon's bounding box
     *   - imagefile - name of image to be searched from (haystack)
     *   - iconfile - name of icon to be search for (needle)
     *   - threshold - max. acceptable error.
     *       0: perfect match
     *       9: big error allowed
     *
     * Return value:
     *    0: success
     *   -1: found an icon but it has too big error
     *   -2: nothing like icon has been found
     *   -3: cannot open imagefile
     *   -4: cannot open iconfile
     */

    int findSingleIcon(BoundingBox* bbox,
                       const char* imagefile,
                       const char* iconfile,
                       const int threshold);
}
