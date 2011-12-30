/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2011, Intel Corporation.
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

/* Video for Linux adapter. Takes video device path as a parameter. */

#include "adapter_v4l2.hh"
#include <cstdio>
    
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>

#include <sys/ioctl.h>
#include <linux/videodev2.h>
#include <string.h>

Adapter_v4l2::Adapter_v4l2(Log& l, std::string params)
  : Adapter::Adapter(l)
{
  if (params == "") filename=std::string("/dev/video");
  else filename = params;
}

void Adapter_v4l2::execute(std::vector<int>& action_list)
{
#define RETURN(x) { action_list[0] = x; return; }
  int action = action_list[0];
  
  struct v4l2_control control;
  struct v4l2_queryctrl queryctrl;
  memset (&queryctrl, 0, sizeof (queryctrl));
  memset (&control, 0, sizeof (control));
  
  log.debug("action size %i\n",
	 (int)actions->size());
  
  if ((*actions)[action]==std::string("iOpen")) {
    fd=open(filename.c_str(),O_RDWR);
    
    log.debug("Open %i\n",fd);
    
    if (fd<0) {
      RETURN(0);
    } 
    
    RETURN(action);
  }
  
  if ((*actions)[action]==std::string("iClose")) {
    if (close(fd)<0) {
      RETURN(0);
    }
    RETURN(action);
  }
  
  if ((*actions)[action]==std::string("iAnyBrightness")) {
    queryctrl.id = V4L2_CID_BRIGHTNESS;
    if (-1 != ioctl (fd, VIDIOC_QUERYCTRL, &queryctrl)) {
      RETURN(action);
    }
    RETURN(0);
  }

  if ((*actions)[action]==std::string("iAnyResolution")) {
    RETURN(true); // suspicious you are
  }
  if ((*actions)[action]==std::string("iSetBrightness<avg>")) {
    queryctrl.id = V4L2_CID_BRIGHTNESS;
    if (-1 == ioctl (fd, VIDIOC_QUERYCTRL, &queryctrl)) {
      RETURN(0);
    }

    control.id = V4L2_CID_BRIGHTNESS;
    control.value = queryctrl.default_value;
    if (-1 == ioctl (fd, VIDIOC_S_CTRL, &control)) {
      RETURN(0);
    }
    brightness = queryctrl.default_value;
    RETURN(action);

  }
  if ((*actions)[action]==std::string("iSetBrightness<max>")) {
    queryctrl.id = V4L2_CID_BRIGHTNESS;
    if (-1 == ioctl (fd, VIDIOC_QUERYCTRL, &queryctrl)) {
      RETURN(0);
    }

    control.id = V4L2_CID_BRIGHTNESS;
    control.value = queryctrl.maximum;
    if (-1 == ioctl (fd, VIDIOC_S_CTRL, &control)) {
      RETURN(0);
    }
    brightness = queryctrl.maximum;
    RETURN(action);
  }
  if ((*actions)[action]==std::string("iSetBrightness<min>")) {
    queryctrl.id = V4L2_CID_BRIGHTNESS;
    if (-1 == ioctl (fd, VIDIOC_QUERYCTRL, &queryctrl)) {
      RETURN(0);
    }

    control.id = V4L2_CID_BRIGHTNESS;
    control.value = queryctrl.minimum;
    if (-1 == ioctl (fd, VIDIOC_S_CTRL, &control)) {
      RETURN(0);
    }
    brightness = queryctrl.minimum;
    RETURN(action);
  }
  if ((*actions)[action]==std::string("iSetResolution<avg>")) {
    RETURN(action);
  }
  if ((*actions)[action]==std::string("iSetResolution<max>")) {
    RETURN(action);
  }
  if ((*actions)[action]==std::string("iSetResolution<min>")) {
    RETURN(action);
  }
  if ((*actions)[action]==std::string("iTakePicture")) {
    
    resolution.type=V4L2_BUF_TYPE_VIDEO_CAPTURE;
    if (ioctl(fd,VIDIOC_G_FMT,&resolution)<0) {
      RETURN(0);
    }
    unsigned int r;
    unsigned char buf[resolution.fmt.pix.sizeimage];
    
    while (((r=read(fd,buf,resolution.fmt.pix.sizeimage))<0) &&
	   (errno==EINTR)) {}
    
    
    if (r!=resolution.fmt.pix.sizeimage) {
      RETURN(0);
    }
    RETURN(action);
  }

  if ((*actions)[action]==std::string("iVerifyBrightness")) {
    control.id = V4L2_CID_BRIGHTNESS;
    if (-1 == ioctl (fd, VIDIOC_G_CTRL, &control)) {
      RETURN(0);
    }
    if (brightness != control.value) {
      RETURN(0);
    }
    RETURN(action);
  }

  if ((*actions)[action]==std::string("iVerifyResolution")) {
    RETURN(action);
  }

  RETURN(0);
}

int  Adapter_v4l2::observe(std::vector<int>& action, bool block)
{
  return false;
}

FACTORY_DEFAULT_CREATOR(Adapter, Adapter_v4l2, "v4l2");
