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

#include <stdio.h>
    
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>

char* filename="/dev/video";

#include <sys/ioctl.h>
#include <linux/videodev2.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>

char** actions;
int actions_size=0;

int fd=-1;
int brightness;
struct v4l2_format resolution;

#include <stdio.h>

int execute(int action);

int main()
{
  int i;
  char* s=NULL;
  size_t si=0;

  getline(&s,&si,stdin);
  actions_size=atoi(s);
  
  free(s);
  actions=(char**)malloc(sizeof(char*)*actions_size);
  
  for(i=0;i<actions_size;i++) {
    s=NULL;
    
    getline(&s,&si,stdin);
    if (s[strlen(s)-1]=='\n') {
      s[strlen(s)-1]='\0';
    }
    actions[i]=s;
  }

  s=NULL;
  
  while (getline(&s,&si,stdin)>1) {
    int action=atoi(s);
    if (action<1) {
      return 0;
    }
    if (action>=actions_size) {
      fprintf(stderr,"-1\n");
      return -1;
    }
    action=execute(action);
    fprintf(stderr,"%i\n",action);
  }
  
  return 0;
}


int isaction(const char* a,const char* b)
{
  return (strcmp(a,b)==0);
}

/* adapter can execute.. */
int execute(int action)
{
  struct v4l2_control control;
  struct v4l2_queryctrl queryctrl;
  memset (&queryctrl, 0, sizeof (queryctrl));
  memset (&control, 0, sizeof (control));
  
  if (isaction(actions[action],"iOpen")) {
    fd=open(filename,O_RDWR);
    
    if (fd<0) {
      return 0;
    } 
    
    return action;
  }
  
  if (isaction(actions[action],"iClose")) {
    if (close(fd)<0) {
      return 0;
    }
    return action;
  }
  
  if (isaction(actions[action],"iAnyBrightness")) {
    queryctrl.id = V4L2_CID_BRIGHTNESS;
    if (-1 != ioctl (fd, VIDIOC_QUERYCTRL, &queryctrl)) {
      return action;
    }
    return 0;
  }

  if (isaction(actions[action],"iAnyResolution")) {
    return action;
  }

  if (isaction(actions[action],"iSetBrightness<avg>")) {
    queryctrl.id = V4L2_CID_BRIGHTNESS;
    if (-1 == ioctl (fd, VIDIOC_QUERYCTRL, &queryctrl)) {
      return 0;
    }

    control.id = V4L2_CID_BRIGHTNESS;
    control.value = queryctrl.default_value;
    if (-1 == ioctl (fd, VIDIOC_S_CTRL, &control)) {
      return 0;
    }
    brightness = queryctrl.default_value;
    return action;

  }
  if (isaction(actions[action],"iSetBrightness<max>")) {
    queryctrl.id = V4L2_CID_BRIGHTNESS;
    if (-1 == ioctl (fd, VIDIOC_QUERYCTRL, &queryctrl)) {
      return 0;
    }

    control.id = V4L2_CID_BRIGHTNESS;
    control.value = queryctrl.maximum;
    if (-1 == ioctl (fd, VIDIOC_S_CTRL, &control)) {
      return 0;
    }
    brightness = queryctrl.maximum;
    return action;
  }
  if (isaction(actions[action],"iSetBrightness<min>")) {
    queryctrl.id = V4L2_CID_BRIGHTNESS;
    if (-1 == ioctl (fd, VIDIOC_QUERYCTRL, &queryctrl)) {
      return 0;
    }

    control.id = V4L2_CID_BRIGHTNESS;
    control.value = queryctrl.minimum;
    if (-1 == ioctl (fd, VIDIOC_S_CTRL, &control)) {
      return 0;
    }
    brightness = queryctrl.minimum;
    return action;
  }
  if (isaction(actions[action],"iSetResolution<avg>")) {
    return action;
  }
  if (isaction(actions[action],"iSetResolution<max>")) {
    return action;
  }
  if (isaction(actions[action],"iSetResolution<min>")) {
    return action;
  }
  if (isaction(actions[action],"iTakePicture")) {
    
    resolution.type=V4L2_BUF_TYPE_VIDEO_CAPTURE;
    if (ioctl(fd,VIDIOC_G_FMT,&resolution)<0) {
      return action;
      return 0;
    }
    int r;
    unsigned char buf[resolution.fmt.pix.sizeimage];
    
    while (((r=read(fd,buf,resolution.fmt.pix.sizeimage))<0) &&
	   (errno==EINTR)) {}
    
    
    if (r!=resolution.fmt.pix.sizeimage) {
      return action;
      return 0;
    }
    return action;
  }

  if (isaction(actions[action],"iVerifyBrightness")) {
    control.id = V4L2_CID_BRIGHTNESS;
    if (-1 == ioctl (fd, VIDIOC_G_CTRL, &control)) {
      return 0;
    }
    if (brightness != control.value) {
      return 0;
    }
    return action;
  }

  if (isaction(actions[action],"iVerifyResolution")) {
    return action;
  }

  return 0;
}

int observe(int *action,int block)
{
  return 0;
}
