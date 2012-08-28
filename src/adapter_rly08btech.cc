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
#include "adapter_rly08btech.hh"
#include "helper.hh"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <sstream>
#include <time.h>
#include <math.h>

Adapter_rly08btech::Adapter_rly08btech(Log& l,std::string params): 
  Adapter::Adapter(l), fd(0) 
{
  devname=params;
}

bool Adapter_rly08btech::init(){
  fd=open(devname.c_str(),O_RDWR);

  if (fd<0) {
    return false;
  }

  char buf[] = { 0x5A, 0x0 };

  if (write(fd,buf,1)!=1) {
    return false;
  }

  if (read(fd,buf,2)!=2) {
    return false;
  }

  log.debug("rly08btech %i %i",buf[0],buf[1]);

  command["iAllOn"] =0x64;
  command["iOn1"]   =0x65;
  command["iOn2"]   =0x66;
  command["iOn3"]   =0x67;
  command["iOn4"]   =0x68;
  command["iOn5"]   =0x69;
  command["iOn6"]   =0x6a;
  command["iOn7"]   =0x6b;
  command["iOn8"]   =0x6c;

  command["iOn(1)"]   =0x65;
  command["iOn(2)"]   =0x66;
  command["iOn(3)"]   =0x67;
  command["iOn(4)"]   =0x68;
  command["iOn(5)"]   =0x69;
  command["iOn(6)"]   =0x6a;
  command["iOn(7)"]   =0x6b;
  command["iOn(8)"]   =0x6c;


  command["iAllOff"]=0x6e;
  
  command["iOff1"]  =0x6f;
  command["iOff2"]  =0x70;
  command["iOff3"]  =0x71;
  command["iOff4"]  =0x72;
  command["iOff5"]  =0x73;
  command["iOff6"]  =0x74;
  command["iOff7"]  =0x75;
  command["iOff8"]  =0x76;

  command["iOff(1)"]  =0x6f;
  command["iOff(2)"]  =0x70;
  command["iOff(3)"]  =0x71;
  command["iOff(4)"]  =0x72;
  command["iOff(5)"]  =0x73;
  command["iOff(6)"]  =0x74;
  command["iOff(7)"]  =0x75;
  command["iOff(8)"]  =0x76;

  return true;
}


void Adapter_rly08btech::set_actions(std::vector<std::string>* _actions)
{
  /* handle actions... */
  Adapter::set_actions(_actions);
}


std::string Adapter_rly08btech::stringify()
{
  std::ostringstream t(std::ios::out | std::ios::binary);

  t << "rly08btech:" << devname;

  return t.str();
}

/* adapter can execute.. */
void Adapter_rly08btech::execute(std::vector<int>& action)
{
  log.push("rly08btech");
  action.resize(1);

  unsigned char cmd=command[(*actions)[action[0]]];

  if (cmd) {
    if (write(fd,&cmd,1)!=1) {
      action[0]=0;
    }
  } else {
    action.resize(1);
    action[0]=0;
  }

  log.pop();
}

int  Adapter_rly08btech::observe(std::vector<int> &action,
			    bool block)
{
  int ret=SILENCE;

  return ret;
}

FACTORY_DEFAULT_CREATOR(Adapter, Adapter_rly08btech, "rly08btech")
