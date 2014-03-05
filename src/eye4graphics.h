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

#define ERROR_CANNOT_OPEN_IMAGEFILE -3
#define ERROR_CANNOT_OPEN_ICONFILE -4

#ifdef __MINGW32__

typedef signed int int32_t;

#endif

extern "C" {

    typedef struct _bbox {
        int32_t left, top, right, bottom;
        int32_t error;
    } BoundingBox;

    /*
     * findSingleIcon
     *
     * Parameters:
     *   - bbox (out)   - bounding box of matching area
     *   - imagefile    - name of image to be searched from (haystack)
     *   - iconfile     - name of icon to be search for (needle)
     *   - threshold    - max. acceptable error.
     *       0: perfect match
     *       9: big error allowed
     *   - colorMatch   - 0.0 - 1.0, required color match
     *   - opacityLimit - skip comparing pixels with opacity < opacityLimit
     *                    0.0 (default) compares all pixels without reading
     *                    opacity values
     *   - searchArea   - bounding box of area in the imagefile to be searched
     *
     * Return value:
     *    0: success
     *   -1: nothing like icon has been found
     *   -2: found an icon but it has too big error
     *   -3: cannot open imagefile
     *   -4: cannot open iconfile
     */

    int findSingleIcon(BoundingBox* bbox,
                       const char* imagefile,
                       const char* iconfile,
                       const int threshold,
                       const double colorMatch,
                       const double opacityLimit,
                       const BoundingBox* searchArea);

    /*
     * findNextIcon
     *
     * Parameters:
     * - bbox (in/out)  - in: bounding box of previously found icon
     *                    out: bounding box of next icon
     * - image          - opened image (returned by openImage)
     * - icon           - opened icon (returned by openImage)
     * - threshold, colorMatch, opacityLimit, searchArea - see findSingleIcon
     * - continueOpts   - if 0, find the first match (ignore bbox value)
     *                    if non-zero, find the next match
     * - xscale         - X axis scaling for icon
     * - yscale         - Y axis scaling for icon
     * - neeRectSize    - area on icon, counter part must be in image
     * - hayRectSize    - area on image, counter part for area in icon
     *
     * Return value:
     *     see findSingleIcon
     */

    int findNextIcon(BoundingBox* bbox,
                     void* image,
                     void* icon,
                     const int threshold,
                     const double colorMatch,
                     const double opacityLimit,
                     const BoundingBox* searchArea,
                     const int continueOpts,
                     const float xscale,
                     const float yscale,
                     const int neeRectSize,
                     const int hayRectSize);

    /*
     * imageDimensions
     *
     * Parameters:
     *   - bbox for returning dimensions of the image
     *   - imagefile - name of the image
     *
     * Return value:
     *    0: success
     *   -3: cannot open image file
     *
     *       on success, bbox.right is the width, and bbox.bottom is
     *       the height of the image.
     */
    int imageDimensions(BoundingBox* bbox,
                        const char* imagefile);

    int openedImageDimensions(BoundingBox* bbox, const void * image);

    int openedImageIsBlank(const void *image);

    void* openImage(const char* imagefile);

    void* openBlob(const void* blob, const char* pixelorder, int x, int y);

    void closeImage(void* image);

    /*
     * bgrx2rgb - convert 4-bytes-per-pixel bitmap data (BGRx) to RGB.
     *
     * Return value:
     *    0: all pixels are black
     *    > 0: there is at least one non-black pixel
     */
    int bgrx2rgb(char* data, int width, int height);

    /*
     * wbgr2rgb - convert Windows GetDIBits (BGR, mirrored Y) image to RGB.
     */
    int wbgr2rgb(char* data, int width, int height);
}
