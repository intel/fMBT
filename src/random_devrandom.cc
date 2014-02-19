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

#ifndef  __MINGW32__

#define _RANDOM_INTERNAL_
#include "function.hh"
#include "random_devrandom.hh"
#include "params.hh"
#include <cstdlib>

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <limits.h>

Random_DevRandom::Random_DevRandom(const std::string& param) {
  max_val = UINT_MAX;
  fd=open("/dev/random",O_RDONLY);
  if (!fd) {
    status=false;
    errormsg="Can't open /dev/random";
  }
}

Random_DevRandom::~Random_DevRandom()
{
  if (fd) {
    close(fd);
  }
}


std::string Random_DevRandom::stringify() {
  if (status) {
    return std::string("/dev/random");
  } 
  return Writable::stringify();
}


unsigned long Random_DevRandom::rand() {
  unsigned int ret=0;
  ssize_t len;

  do {
    len=read(fd,&ret,sizeof(ret));
  } while (len!=sizeof(ret));

  return ret;
}

FACTORY_DEFAULT_CREATOR(Random, Random_DevRandom, "/dev/random")
FACTORY_DEFAULT_CREATOR(Function, Random_DevRandomf, "/dev/random")

#endif /* __MINGW32__ */
