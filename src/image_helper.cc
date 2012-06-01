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

bool ishere(int hayx,int neex,int neey,int x,int y,
	    const PixelPacket *hay_pixel,
	    const PixelPacket *nee_pixel)
{
  // Check diagonal first. Seems to speed up things.

  for(int i=0;i<neey&&i<neex;i++) {
      if (*(hay_pixel+hayx*(y+i)+x+i) != 
	  *(nee_pixel+neex*i+i)) {
	return false;
      }
  }

  for(int _y=0;_y<neey;_y++) {
    for(int _x=0;_x<neex;_x++) {
      if (*(hay_pixel+hayx*(y+_y)+x+_x) != 
	  *(nee_pixel+neex*_y+_x)) {
	return false;
      }
    }
  }
  return true;
}

void img_search(std::vector<std::pair<int,int> >& res,Image& haystack,
		Image& needle)
{
  int hayx=haystack.columns(),hayy=haystack.rows();
  haystack.modifyImage();
  haystack.type(TrueColorType);
  const PixelPacket *hay_pixel=haystack.getConstPixels(0,0,hayx,hayy);

  int neex=needle.columns(),neey=needle.rows();
  needle.modifyImage();
  needle.type(TrueColorType);
  const PixelPacket *nee_pixel=needle.getConstPixels(0,0,neex,neey);

  for(int y=0;y<hayy-neey;y++) {
    for(int x=0;x<hayx-neex;x++) {
      if (ishere(hayx,neex,neey,x,y,hay_pixel,nee_pixel)) {
	res.push_back(std::pair<int,int>(x,y));
      }
    }
  }
}

/*
 * g++ -o image_helper -O3 -Wall `pkg-config --cflags --libs Magick++` image_helper.cc
 */

int main(int argc,char** argv)
{
  Image i1(argv[1]);
  Image i2(argv[2]);

  std::vector<std::pair<int,int> > r;

  img_search(r,i1,i2);

  for(unsigned i=0;i<r.size();i++) {
    printf("%i %i\n",r[i].first,r[i].second);
  }

  
  return 0;
}
