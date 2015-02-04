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

#include <algorithm>
#include <climits>
#include <map>
#include <math.h>
#include <string.h>
#include <vector>

#include <magick/MagickCore.h>

#include "eye4graphics.h"

#define COLORS 64

#define INCOMPARABLE -1

#define MIN(a,b) (((a)<(b))?(a):(b))

void initeye4graphics() {}

PixelPacket* getPixels(Image* image, size_t x1, size_t y1, size_t x2, size_t y2);

static int _ceil(float f) {
    int floor = int(f);
    static const float epsilon = 0.00001;
    if (f - floor > epsilon) return floor + 1;
    else return floor;
}

class Search_id {
public:
    Search_id(void* haystack_, void* needle_, int threshold_,
              double colorMatch_, double opacityLimit_,
              const BoundingBox &area_):
        haystack(haystack_), needle(needle_), threshold(threshold_),
        colorMatch(colorMatch_), opacityLimit(opacityLimit_),
        area(area_), hay_pixel(0), nee_pixel(0) {}
    void * haystack;
    void * needle;
    int threshold;
    double colorMatch;
    double opacityLimit;
    BoundingBox area;
    const PixelPacket* hay_pixel;
    const PixelPacket* nee_pixel;
};

class Search_id_less_comparator {
public:
    bool operator()(const Search_id &lhs, const Search_id &rhs) const {
        return (lhs.haystack < rhs.haystack ||
                lhs.needle < rhs.needle ||
                lhs.threshold < rhs.threshold ||
                lhs.colorMatch < rhs.colorMatch ||
                lhs.area.left < rhs.area.left ||
                lhs.area.right < rhs.area.right ||
                lhs.area.top < rhs.area.top ||
                lhs.area.bottom < rhs.area.bottom);
    }
};

static std::map<Search_id, bool, Search_id_less_comparator> imagePixels;
typedef std::map<Search_id, bool, Search_id_less_comparator>::iterator ImagePixelsIterator;
typedef std::vector<BoundingBox>::const_iterator BoundingBoxConstIterator;

inline bool same_color(const PixelPacket *p1, const PixelPacket *p2,
                       const int colorDiff, const unsigned char skipTransparency)
{
    /* do not compare transparent pixels */
    if (skipTransparency) {
        if (p1->opacity >= skipTransparency || p2->opacity >= skipTransparency) {
            return true;
        }
    }

    if ((unsigned char)(p1->red) + colorDiff   >= (unsigned char)(p2->red) &&
        (unsigned char)(p2->red) + colorDiff   >= (unsigned char)(p1->red) &&
        (unsigned char)(p1->green) + colorDiff >= (unsigned char)(p2->green) &&
        (unsigned char)(p2->green) + colorDiff >= (unsigned char)(p1->green) &&
        (unsigned char)(p1->blue) + colorDiff  >= (unsigned char)(p2->blue) &&
        (unsigned char)(p2->blue) + colorDiff  >= (unsigned char)(p1->blue)) {
        return true;
    } else {
        return false;
    }
}

inline bool same_rect(const int hayxsize,
                      const int neexsize,
                      const PixelPacket* hay_pixel,
                      const PixelPacket* nee_pixel,
                      const int colorDiff,
                      const unsigned char skipTransparency,
                      const int hayPixelSize,
                      const int neePixelSize)
{
    const int required_match_count = 1;
    int matching_pixel_count = 0;

    for (int nrx = 0; nrx < neePixelSize; ++nrx) {
        for (int nry = 0; nry < neePixelSize; ++nry) {

            for (int hrx = 0; hrx < hayPixelSize; ++hrx) {
                for (int hry = 0; hry < hayPixelSize; ++hry) {
                    if (same_color(hay_pixel + hry * hayxsize + hrx,
                                   nee_pixel + nry * neexsize + nry,
                                   colorDiff, skipTransparency)) {
                        ++matching_pixel_count;
                        if (matching_pixel_count >= required_match_count)
                            return true;
                    }
                }
            }
        }
    }
    return false;
}

static bool pixelperfect_match(const int hayxsize,
                               const int neexsize, const int neeysize,
                               const int x, const int y,
                               const PixelPacket *hay_pixel,
                               const PixelPacket *nee_pixel,
                               const int colorDiff,
                               const unsigned char skipTransparency,
                               const float xscale,
                               const float yscale,
                               const int neePixelSize,
                               const int hayPixelSize)
{
    /* try to fail fast, quick middle-row lookup */
    int samples = 16;
    int stepx = neexsize >= samples ? int(neexsize*xscale)/samples : 1;
    if (stepx < 1) stepx = 1;
    if (stepx > 8) stepx = 8;
    for (int _x=0, _y=int(neeysize*yscale)/2;
         _x + neePixelSize < int(neexsize*xscale);
         _x+=stepx) {
        if (!same_rect(hayxsize, neexsize,
                       (hay_pixel + hayxsize*(y+_y) + x+_x),
                       (nee_pixel + neexsize*int(_y/yscale) + int(_x/xscale)),
                       colorDiff,
                       skipTransparency,
                       neePixelSize, hayPixelSize)) {
            return false;
        }
    }

    /* next a quick diagonal sweep */
    samples = 8;
    stepx = neexsize >= samples ? int(neexsize*xscale)/samples : 1;
    int stepy = neeysize >= samples ? int(neeysize*yscale)/samples : 1;
    if (stepx < 1) stepx = 1;
    if (stepx > 16) stepx = 16;
    if (stepy < 1) stepy = 1;
    if (stepy > 16) stepy = 16;
    for (int _x=0, _y=0;
         _x + neePixelSize < int(neexsize*xscale) &&
         _y + neePixelSize < int(neeysize*yscale);
         _x+=stepx, _y+=stepy) {
        if (!same_rect(hayxsize, neexsize,
                       (hay_pixel + hayxsize*(y+_y) + x+_x),
                       (nee_pixel + neexsize*int(_y/yscale) + int(_x/xscale)),
                       colorDiff,
                       skipTransparency,
                       neePixelSize, hayPixelSize)) {
            return false;
        }
    }

    /* full check, pixel-by-pixel */
    for(int _y=0; _y+neePixelSize < int(neeysize*yscale); _y++) {
        for(int _x=0; _x+neePixelSize < int(neexsize*xscale); _x++) {
            if (!same_rect(hayxsize, neexsize,
                           (hay_pixel + hayxsize*(y+_y) + x+_x),
                           (nee_pixel + neexsize*int(_y/yscale) + int(_x/xscale)),
                           colorDiff,
                           skipTransparency,
                           neePixelSize, hayPixelSize)) {
                return false;
            }
        }
    }
    return true;
}

long normdiag_error(int hayxsize,int neex,int neey,int x,int y,
                    const PixelPacket *hay_pixel,
                    const PixelPacket *nee_pixel,
                    const int xstart, const int ystart,
                    const int xstep, const int ystep, int debug=0)
{
    /*
      +--+      +--+
      |n1|      |h1|           minimise
      +--+--+   +--+--+--+--+  ((n1-n2) - (h1-h2))^2 + penalty
         |  |      | ?| ?| ?|
         +--+--+   +--+--+--+
            |n2|   | ?|h2| ?|
            +--+   +--+--+--+
                   | ?| ?| ?|
                   +--+--+--+
    */

    // Normalise and quantify colors on searched area

    const int colors = COLORS; // Quantify to this number of colors
    int nee_greatest = -1;
    int nee_smallest = -1;
    int hay_greatest = -1;
    int hay_smallest = -1;
    for(int norx=xstart, nory=ystart;
        0 <= norx && 0 <= nory && norx < neex && nory < neey;
        norx+=xstep, nory+=ystep) {
        int nvalue = (*(nee_pixel+neex*nory+norx)).green;
        if (nee_smallest == -1 || nvalue < nee_smallest) nee_smallest = nvalue;
        if (nee_greatest == -1 || nvalue > nee_greatest) nee_greatest = nvalue;
        int hvalue = (*(hay_pixel+hayxsize*(nory+y)+norx+x)).green;
        if (hay_smallest == -1 || hvalue < hay_smallest) hay_smallest = hvalue;
        if (hay_greatest == -1 || hvalue > hay_greatest) hay_greatest = hvalue;
    }
    // If color ranges are too different, bail out.
    if (hay_greatest - hay_smallest > (nee_greatest - nee_smallest) * 2 ||
        nee_greatest - nee_smallest > (hay_greatest - hay_smallest) * 2) {
        return INCOMPARABLE;
    }
    const int nee_colorscale = nee_greatest == nee_smallest ?  1 : nee_greatest - nee_smallest;
    const int hay_colorscale = hay_greatest == hay_smallest ?  1 : hay_greatest - hay_smallest;

    long delta = 0;
    int checked_steps = 0;
    for(int checkx=xstart+1, checky=ystart+1;
        (0 <= checkx &&
         0 <= checky &&
         0 <= checkx+xstep*2-1 &&
         0 <= checky+ystep*2-1 &&
         checkx+xstep*2+1 < neex &&
         checky+ystep*2+1 < neey);
        checkx+=xstep, checky+=ystep) {

        int n1 = (((*(nee_pixel+neex*checky+checkx)).green - nee_smallest)*colors)
            / nee_colorscale;
        int n2 = (((*(nee_pixel+neex*(checky+ystep*2)+(checkx+xstep*2))).green - nee_smallest)*colors)
            / nee_colorscale;
        int bestdiff = -1;

        int h1, h2;
        int diff;

#define GREEN(h1xoffset, h1yoffset, penalty)                            \
        do {                                                            \
            h2=((((*(hay_pixel+hayxsize*(checky+y+(h1yoffset))+checkx+x+(h1xoffset))).green - hay_smallest)*colors) / hay_colorscale); \
            diff = (n1-n2)-(h1-h2); diff = diff*diff + penalty;         \
            if (bestdiff == -1 || diff < bestdiff) bestdiff = diff;     \
        } while (0);

        h1 = ((((*(hay_pixel+hayxsize*(checky+y)+checkx+x)).green - hay_smallest)*colors) / hay_colorscale);

        GREEN(xstep*2, ystep*2, 0);
        for (int xi=xstep*2-1; xi<=xstep*2+1 && bestdiff > colors/4; xi++) {
            for (int yi=ystep*2-1; yi<=ystep*2+1 && bestdiff > colors/4; yi++) {
                GREEN(xi, yi, colors/4);
            }
        }
        delta += bestdiff;
        checked_steps += 1;
    }

    return delta / checked_steps;
}

/*
 * iconsearch
 *
 * Parameters:
 *     retval    - vector of bounding boxes of found icons (out-parameter)
 *     haystack  - image from which icon is searched from
 *     needle    - icon to be searched for
 *     threshold - maximal level of difference between
 *                 found icon and original icon.
 *                     0  - pixel perfect
 *                     10 - big differences allowed
 *                 The smaller the threshold the faster the search.
 *
 *     xscale     - default: 1.0
 *     yscale     - default: 1.0
 *     neePixelSize - size of pixel rectangle on needle, default:
 *                  1 for xscale 1.0, 2 for xscale > 1.0
 *     hayPixelSize - size of pixel rectangle on haystack, default:
 *                  ceil(neePixelSize * xscale)
 *
 * Return value:
 *     1         - icon candidate found
 *     0         - icon not found
 */
static int iconsearch(std::vector<BoundingBox>& retval,
                      const std::vector<BoundingBox>& ignore,
                      const BoundingBox& searchArea,
                      Image* haystack,
                      Image* needle,
                      const int threshold,
                      const double colorMatch,
                      const double opacityLimit,
                      int startX,
                      int startY,
                      const float xscale,
                      const float yscale,
                      const int neePixelSize,
                      const int hayPixelSize)
{
    const int color_threshold = COLORS * threshold;

    const int colorDiff = 256 - (256 * colorMatch);

    const unsigned char skipTransparency = 255 * opacityLimit;

    const bool ignoreBoxes = ignore.size() > 0;

    typedef std::pair<long, std::pair<int,int> > Candidate;
    std::vector< Candidate > candidates;

    int _neePixelSize = xscale > 1.0 ? 2 : 1;
    if (neePixelSize > 0) _neePixelSize = neePixelSize;
    int _hayPixelSize = hayPixelSize > 0 ? hayPixelSize : _ceil(_neePixelSize * xscale);

    if (startX == 0) startX = searchArea.left;
    if (startY == 0) startY = searchArea.top;
    if (startX < searchArea.left ||
        startX > searchArea.right ||
        startY < searchArea.top ||
        startY > searchArea.bottom)
        return -1;

    if (startX > _hayPixelSize/2) startX -= _hayPixelSize/2;
    if (startY > _hayPixelSize/2) startY -= _hayPixelSize/2;
    if (startX < searchArea.left) startX = searchArea.left;
    if (startY < searchArea.top) startY = searchArea.top;

    int hayx = haystack->columns;
    int hayy = haystack->rows;
    int neex = needle->columns;
    int neey = needle->rows;
    hayx = MIN(hayx, searchArea.right - searchArea.left);
    hayy = MIN(hayy, searchArea.bottom - searchArea.top);

    const PixelPacket *hay_pixel;
    const PixelPacket *nee_pixel;

    Search_id search_id(static_cast<void*>(haystack),
                        static_cast<void*>(needle),
                        threshold, colorMatch, opacityLimit, searchArea);

    ImagePixelsIterator it;
    if ((it = imagePixels.find(search_id)) != imagePixels.end()) {
        hay_pixel = it->first.hay_pixel;
        nee_pixel = it->first.nee_pixel;
    } else {
        hay_pixel = getPixels(haystack, searchArea.left, searchArea.top, hayx, hayy);
        nee_pixel = getPixels(needle, 0, 0, neex, neey);

        search_id.hay_pixel = hay_pixel;
        search_id.nee_pixel = nee_pixel;
        imagePixels[search_id] = true;
    }

    if (threshold == 0) {
        /* Pixel-perfect match */
        int startXinArea = startX - searchArea.left;
        int startYinArea = startY - searchArea.top;
        for (int y=startYinArea; y+hayPixelSize <= hayy-int(neey*yscale); y++) {
            for (int x=startXinArea; x+hayPixelSize <= hayx-int(neex*xscale); x++) {
                if (ignoreBoxes) {
                    bool skipCoordinates = false;
                    BoundingBoxConstIterator it = ignore.begin();
                    while (it != ignore.end() && !skipCoordinates) {
                        skipCoordinates |= (x > it->left && x < it->right &&
                                            y > it->top && y < it->bottom);
                        ++it;
                    }
                    if (skipCoordinates) continue;
                }
                if (pixelperfect_match(hayx, neex, neey, x, y,
                                       hay_pixel, nee_pixel,
                                       colorDiff,
                                       skipTransparency,
                                       xscale, yscale,
                                       _neePixelSize, _hayPixelSize)) {
                    BoundingBox bbox;
                    bbox.left = x + searchArea.left + _hayPixelSize/2;
                    bbox.top = y + searchArea.top + _hayPixelSize/2;
                    bbox.right = bbox.left + int(neex*xscale) +_hayPixelSize/2;
                    bbox.bottom = bbox.top + int(neey*yscale) +_hayPixelSize/2;
                    bbox.error = 0;
                    retval.push_back(bbox);
                    return 1;
                }
            }
            startXinArea = 0;
        }
        return 0;
    }

    /* Fuzzy match */
    /* sweep diagonal */
    int samples = 16;
    int stepx = neex >= samples ? neex/samples : 1;
    int stepy = neey >= samples ? neey/samples : 1;
    for (int y=0;y<hayy-neey;y++) {
        for (int x=0;x<hayx-neex;x++) {
            long thisdelta = normdiag_error(hayx, neex, neey, x, y,
                                            hay_pixel, nee_pixel,
                                            0, 0, stepx, stepy);
            if (thisdelta != INCOMPARABLE && thisdelta <= color_threshold) {
                candidates.push_back( Candidate(thisdelta, std::pair<int,int>(x, y)) );
            }
        }
    }

    /* sweep more lines, take samples on every pixel */
    for (unsigned int ci=0; ci < candidates.size(); ci++) {
        if (candidates[ci].first == LONG_MAX) continue;

        int thisdelta;
        int x = candidates[ci].second.first;
        int y = candidates[ci].second.second;

        thisdelta = normdiag_error(hayx, neex, neey, x, y, hay_pixel, nee_pixel,
                                   0, neey/2, 1, 0);
        if (thisdelta == INCOMPARABLE) {
            candidates[ci].first = LONG_MAX; continue;
        }
        candidates[ci].first += thisdelta;

        thisdelta = normdiag_error(hayx, neex, neey, x, y, hay_pixel, nee_pixel,
                                  neex/2, 0, 0, 1);
        if (thisdelta == INCOMPARABLE) {
            candidates[ci].first = LONG_MAX; continue;
        }
        candidates[ci].first += thisdelta;
        thisdelta = normdiag_error(hayx, neex, neey, x, y, hay_pixel, nee_pixel,
                                    neex-1, 0, -1, 1);
        if (thisdelta == INCOMPARABLE) {
            candidates[ci].first = LONG_MAX; continue;
        }
        candidates[ci].first += thisdelta;
    }

    if (candidates.size() > 0) {
        std::sort(candidates.begin(), candidates.end());
        BoundingBox bbox;
        bbox.left = candidates[0].second.first;
        bbox.top = candidates[0].second.second;
        bbox.right = bbox.left + neex;
        bbox.bottom = bbox.top + neey;
        bbox.error = candidates[0].first / COLORS / 4;
        retval.push_back(bbox);
        return 1;
    }
    else return 0;
}

int findSingleIcon(BoundingBox* bbox,
                   const char* imagefile,
                   const char* iconfile,
                   const int threshold,
                   const double colorMatch,
                   const double opacityLimit,
                   const BoundingBox* searchArea)
{
    void* haystack = openImage(imagefile);
    if (haystack == NULL)
        return ERROR_CANNOT_OPEN_IMAGEFILE;

    void* needle = openImage(iconfile);
    if (needle == NULL) {
        closeImage(haystack);
        return ERROR_CANNOT_OPEN_ICONFILE;
    }

    int retval = findNextIcon(bbox,
                              haystack,
                              needle,
                              threshold,
                              colorMatch,
                              opacityLimit,
                              searchArea, 0,
                              1.0, 1.0,
                              0, 0);

    closeImage(needle);
    closeImage(haystack);
    return retval;
}

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
                 const int neePixelSize,
                 const int hayPixelSize)
{
    /* TODO: another version with multiple versions of the same
     * icon. Clear, blurred, etc.
     */
    int retval = 0;

    int startX = 0;
    int startY = 0;
    std::vector<BoundingBox> found;
    std::vector<BoundingBox> ignore;

    if (continueOpts != 0) {
        startX = bbox->left + 1;
        startY = bbox->top;
        if (hayPixelSize > 1 ||
            (hayPixelSize == 0 && xscale != 1.0)) {
            /* bbox passes last hit to iconsearch */
            ignore.push_back(*bbox);
        }
    } else {
        bbox->left   = -1;
        bbox->top    = -1;
        bbox->right  = -1;
        bbox->bottom = -1;
    }
    bbox->error  = -1;

    if (iconsearch(found, ignore,
                   *searchArea,
                   static_cast<Image*>(image),
                   static_cast<Image*>(icon),
                   threshold,
                   colorMatch, opacityLimit,
                   startX, startY,
                   xscale, yscale,
                   neePixelSize, hayPixelSize) > 0
        && found.size() > 0) {
        *bbox = found[0];
        if (bbox->error > threshold)
            retval = -2;
        else
            retval = 0;
    } else {
        retval = -1;
    }
    return retval;
}

int findNextHighErrorBlock(
    BoundingBox* bbox,
    void* image,
    const int columns,
    const int rows,
    const double threshold,
    const BoundingBox* searchArea)
{
    Image* haystack = static_cast<Image*>(image);
    int hayx = haystack->columns;
    int hayy = haystack->rows;
    const int dataWidth = hayx / columns;
    const int dataHeight = hayy / rows;
    const PixelPacket* hay_pixel = getPixels(haystack, 0, 0, hayx, hayy);
    const double max_sqerr = (QuantumRange / 2.0) * (QuantumRange / 2.0);
    int next_left = bbox->left + dataWidth;
    for (int y = bbox->top; y < hayy - dataHeight; y += dataHeight) {
        for (int x = next_left; x < hayx - dataWidth; x += dataWidth) {
            double avg_green = 0;
            double avg_sqerr = 0;
            int count = 0;
            for (int yd = 0; yd < dataHeight; yd++) {
                for (int xd = 0; xd < dataWidth; xd++) {
                    int green = (hay_pixel + ((y + yd) * hayx) + (x + xd))->green;
                    avg_green = (avg_green * count + green) / (count+1);
                    count++;
                }
            }
            count = 0;
            for (int yd = 0; yd < dataHeight; yd++) {
                double prev_sqerr = 0.0;
                for (int xd = 0; xd < dataWidth; xd++) {
                    int green = (hay_pixel + ((y + yd) * hayx) + (x + xd))->green;
                    double sqerr = (avg_green - green) * (avg_green - green);
                    avg_sqerr = ((avg_sqerr * count) + abs(prev_sqerr - sqerr)) / (count + 1);
                    prev_sqerr = sqerr;
                    count++;
                }
            }
            if (sqrt(avg_sqerr) / sqrt(max_sqerr) > threshold) {
                bbox->left = x;
                bbox->top = y;
                bbox->right = x + dataWidth;
                bbox->bottom = y + dataHeight;
                bbox->error = sqrt(avg_sqerr);
                return 1;
            }
        }
        next_left = 0;
    }
    return 0;
}


int imageDimensions(BoundingBox* bbox,
                    const char* imagefile)
{
    void *image = openImage(imagefile);
    if (image == NULL) return ERROR_CANNOT_OPEN_IMAGEFILE;

    openedImageDimensions(bbox, image);

    closeImage(image);

    return 0;
}

int openedImageDimensions(BoundingBox* bbox, void* image)
{
    bbox->left   = 0;
    bbox->top    = 0;
    bbox->right = static_cast<Image*>(image)->columns;
    bbox->bottom = static_cast<Image*>(image)->rows;
    bbox->error  = 0;
    return 0;
}

int openedImageIsBlank(void* image)
{
    Image* im = static_cast<Image*>(image);
    int xsize = im->columns;
    int ysize = im->rows;

    const PixelPacket* pp = getPixels(im, 0, 0, xsize, ysize);
    for (int i = 0; i < xsize * ysize; ++i) {
        if (! (pp[i].red == 0 &&
               pp[i].green == 0 &&
               pp[i].blue == 0)) {
            return 0;
        }
    }
    return 1;
}

void* openBlob(const void* blob, const char* pixelorder, int x, int y)
{
    // Image* image = new Image(x,y,pixelorder,CharPixel,blob);
    Image* image = NULL;
    return static_cast<void*>(image);
}


void* openImage(const char* imagefile)
{
    Image* image;
    ExceptionInfo *exception;
    ImageInfo *image_info;
    exception = AcquireExceptionInfo();
    image_info = CloneImageInfo((ImageInfo *) NULL);
    strcpy(image_info->filename, imagefile);
    image = ReadImage(image_info, exception);
    if (image == NULL) {
        char* debug = getenv("EYE4GRAPHICS_DEBUG");
        if (debug != NULL)
            CatchException(exception);
    }
    DestroyExceptionInfo(exception);
    DestroyImageInfo(image_info);
    return static_cast<void*>(image);
}

PixelPacket* getPixels(Image* image, size_t x1, size_t y1, size_t x2, size_t y2)
{
    ExceptionInfo *exception = AcquireExceptionInfo();
    PixelPacket* p = GetAuthenticPixels(image, x1, y1, x2, y2, exception);
    DestroyExceptionInfo(exception);
    return p;
}



void closeImage(void* image)
{
    ImagePixelsIterator it = imagePixels.begin();
    while (it != imagePixels.end()) {
        if (it->first.haystack == image ||
            it->first.needle == image)
        {
            imagePixels.erase(it++);
        } else {
            ++it;
        }
    }
    if (image != NULL)
        DestroyImage(static_cast<Image*>(image));
}

int bgrx2rgb(char* data, int width, int height)
{
    int has_nonblack_pixels = 0;
    for (int i = 0; i < height * width; ++i) {
        char tmp = data[4*i];
        if (tmp != '\0') has_nonblack_pixels = 1;
        data[3*i] = data[4*i + 2];
        data[3*i + 1] = data[4*i + 1];
        data[3*i + 2] = tmp;
    }
    return has_nonblack_pixels;
}

int rgbx2rgb(char* data, int width, int height)
{
    int has_nonblack_pixels = 0;
    for (int i = 0; i < height * width; ++i) {
        data[3*i] = data[4*i];
        data[3*i + 1] = data[4*i + 1];
        data[3*i + 2] = data[4*i + 2];
        if (data[3*i] || data[3*i+1] || data[3*i+2])
            has_nonblack_pixels = 1;
    }
    return has_nonblack_pixels;
}

int bgr2rgb(char* data, int width, int height)
{
    int has_nonblack_pixels = 0;
    for (int i = 0; i < height * width; ++i) {
        char tmp = data[3*i];
        if (tmp != '\0') has_nonblack_pixels = 1;
        data[3*i] = data[3*i + 2];
        data[3*i + 2] = tmp;
    }
    return has_nonblack_pixels;
}

int wbgr2rgb(char* data, const int width, const int height)
{
    int has_nonblack_pixels = 0;
    char *orig_data;
    orig_data = (char*)malloc(height * (width * 3 + 3));
    if (!orig_data) abort();

    memcpy(orig_data, data, height * ((width * 3 + 3) & -4));

    for (int y = 0; y < height; ++y) {
        // scanline: start location of scanline in BGR data
        const int scanline = (height - y - 1) * ((width * 3 + 3) & -4);
        for (int x = 0; x < width; ++x) {
            const int rgb = y * (width * 3) + x * 3;
            data[rgb]     = orig_data[scanline + x * 3 + 2]; // red
            data[rgb + 1] = orig_data[scanline + x * 3 + 1]; // green
            data[rgb + 2] = orig_data[scanline + x * 3];     // blue
            if (!has_nonblack_pixels &&
                (data[rgb] || data[rgb + 1] || data[rgb + 2]))
                has_nonblack_pixels = 1;
        }
    }

    free(orig_data);
    return has_nonblack_pixels;
}

// make library:
// g++ -fPIC -shared -o eye4graphics.so -O3 -Wall `pkg-config --cflags --libs Magick++` eye4graphics.cc


/*
 * g++ -o eye4graphics -O3 -Wall `pkg-config --cflags --libs Magick++` eye4graphics.cc
 */

/*
int main(int argc,char** argv)
{
    BoundingBox box;

    int retval = findSingleIcon(&box, argv[1], argv[2], 4);

    printf("%i %i %i %i %i retval=%i\n", box.left, box.top, box.right, box.bottom, box.error, retval);

    return 0;
}
*/
