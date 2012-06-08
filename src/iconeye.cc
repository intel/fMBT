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

#include "image_helper.hh"
#include <math.h>
#include <algorithm>

#define MIN(a,b) (a<b?a:b)
#define COLORS 64

#include <sys/types.h>

extern "C" {
    typedef struct _bbox {
        int32_t left, top, right, bottom;
        int32_t error;
    } Bbox;
    
    int findSingleIcon(Bbox* retval,
                       const char* imagefile, const char* iconfile,
                       const int threshold);
}

long normdiag_error(int hayx,int neex,int neey,int x,int y,
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

    // Normalise and quantify colors on diagonal

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
        int hvalue = (*(hay_pixel+hayx*(nory+y)+norx+x)).green;
        if (hay_smallest == -1 || hvalue < hay_smallest) hay_smallest = hvalue;
        if (hay_greatest == -1 || hvalue > hay_greatest) hay_greatest = hvalue;
    }
    // If color ranges are too different, bail out.
    if (hay_greatest - hay_smallest > (nee_greatest - nee_smallest) * 2 ||
        nee_greatest - nee_smallest > (hay_greatest - hay_smallest) * 2)
        return 42424;

    long delta = 0;
    for(int checkx=xstart+1, checky=ystart+1;
        0 <= checkx && 0 <= checky &&
            0 <= checkx+xstep*2-1 && 0 <= checky+ystep*2-1 &&
            checkx+xstep*2+1 < neex && checky+ystep*2+1 < neey;
        checkx+=xstep, checky+=ystep) {
        
        int n1 = (((*(nee_pixel+neex*checky+checkx)).green - nee_smallest)*colors)
            /(nee_greatest-nee_smallest);
        int n2 = (((*(nee_pixel+neex*(checky+ystep*2)+(checkx+xstep*2))).green - nee_smallest)*colors)
            /(nee_greatest-nee_smallest);
        int bestdiff = 42424;

        int h1, h2;
        int diff;

#define GREEN(h1xoffset, h1yoffset, penalty)                            \
        do {                                                            \
            h2=((((*(hay_pixel+hayx*(checky+y+(h1yoffset))+checkx+x+(h1xoffset))).green - hay_smallest)*colors) / (hay_greatest-hay_smallest)); \
            diff = (n1-n2)-(h1-h2); diff = diff*diff + penalty;         \
            if (diff < bestdiff) bestdiff = diff;                       \
        } while (0);

        h1 = ((((*(hay_pixel+hayx*(checky+y)+checkx+x)).green - hay_smallest)*colors) / (hay_greatest-hay_smallest));

        GREEN(xstep*2, ystep*2, 0);
        for (int xi=xstep*2-1; xi<=xstep*2+1 && bestdiff > colors/4; xi++) {
            for (int yi=ystep*2-1; yi<=ystep*2+1 && bestdiff > colors/4; yi++) {
                GREEN(xi, yi, colors/4);
            }
        }
        delta += bestdiff;
    }

    return delta / MIN(neex,neey);
}

long diag_deltaerror(int hayx,int neex,int neey,int x,int y,
                     const PixelPacket *hay_pixel,
                     const PixelPacket *nee_pixel)
{
    /* Calculate color change throughout the diagonal axis, use 3+
       pixels If there's a change in needle, require change to the same
       direction in haystack, and vice versa.
    */
    return 0;
}


/*
 * singleiconsearch
 *
 * Parameters:
 *     retval    - bounding box of found icon (out-parameter)
 *     haystack  - image from which icon is searched from
 *     needle    - icon to be searched for
 *     threshold - maximal level of difference between
 *                 found icon and original icon.
 *                     0  - pixel perfect
 *                     10 - big differences allowed
 *                 The smaller the threshold the faster the search.
 *
 * Return value:
 *     1         - icon candidate found
 *     0         - icon not found
 */
int singleiconsearch(Bbox *retval, Image& haystack,
                     Image& needle, const int threshold)
{
    
    const int color_threshold = COLORS * threshold; /* depends on the number of quantified colors */
    typedef std::pair<long, std::pair<int,int> > Candidate;
    std::vector< Candidate > candidates;

    int hayx=haystack.columns(),hayy=haystack.rows();

    haystack.modifyImage();
    haystack.type(TrueColorType);
    const PixelPacket *hay_pixel=haystack.getConstPixels(0,0,hayx,hayy);

    int neex=needle.columns(),neey=needle.rows();
    needle.modifyImage();
    needle.type(TrueColorType);
    const PixelPacket *nee_pixel=needle.getConstPixels(0,0,neex,neey);

    /* sweep diagonal */
    for(int y=0;y<hayy-neey;y++) {
        for(int x=0;x<hayx-neex;x++) {
            long thisdelta = normdiag_error(hayx, neex, neey, x, y,
                                            hay_pixel, nee_pixel,
                                            0, 0, 1, 1);
            if (thisdelta <= color_threshold) {
                candidates.push_back( Candidate(thisdelta, std::pair<int,int>(x, y)) );
            }
        }
    }

    /*
      std::sort(candidates.begin(), candidates.end());
      printf("best candidates:\n");
      for (int i = 0; i < 20 && i < candidates.size(); i++) {
      printf(" %d: %d (%d x %d)\n", i, candidates[i].first, candidates[i].second.first, candidates[i].second.second);
      }
    */

    for (unsigned int ci=0; ci < candidates.size(); ci++) {
        int thisdelta = candidates[ci].first;
        int x = candidates[ci].second.first;
        int y = candidates[ci].second.second;
        thisdelta += 
            normdiag_error(hayx, neex, neey, x, y, hay_pixel, nee_pixel,
                           0, neey/2, 1, 0) +
            normdiag_error(hayx, neex, neey, x, y, hay_pixel, nee_pixel,
                           neex/2, 0, 0, 1) +
            normdiag_error(hayx, neex, neey, x, y, hay_pixel, nee_pixel,
                           neex-1, 0, -1, 1);

        candidates[ci].first = thisdelta;
    }


    if (candidates.size() > 0) {
        std::sort(candidates.begin(), candidates.end());
        /*
          printf("best candidates:\n");
          for (int i = 0; i < 20 && i < candidates.size(); i++) {
          printf(" %d: %d (%d x %d)\n", i, candidates[i].first, candidates[i].second.first, candidates[i].second.second);
          }
        */
        retval->left = candidates[0].second.first;
        retval->top = candidates[0].second.second;
        retval->right = retval->left + neex;
        retval->bottom = retval->top + neey;
        retval->error = candidates[0].first / COLORS / 4;
        return 1;
    }
    else return 0;
}

int findSingleIcon(Bbox* retval,
                   const char* imagefile, const char* iconfile,
                   const int threshold)
{
    /* TODO: another version with multiple versions of the same
     * icon. Clear, blurred, etc.
     */
    Image haystack(imagefile);
    Image needle(iconfile);
    return singleiconsearch(retval, haystack, needle, threshold) == 0;
}

// make library:
// g++ -fPIC -shared -o iconeye.so -O3 -Wall `pkg-config --cflags --libs Magick++` iconeye.cc


/*
 * g++ -o iconeye -O3 -Wall `pkg-config --cflags --libs Magick++` iconeye.cc
 */

int main(int argc,char** argv)
{
    Image i1(argv[1]);
    Image i2(argv[2]);

    Bbox box;

    singleiconsearch(&box,i1,i2,4);
  
    printf("%i %i %i %i %i\n", box.left, box.top, box.right, box.bottom, box.error);

    return 0;
}
