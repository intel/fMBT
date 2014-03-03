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

Random_Dev::Random_Dev(const std::string& param): _param(param) {
  max_val = UINT_MAX;
  fd=open(param.c_str(),O_RDONLY);
  if (!fd) {
    status=false;
    errormsg="Can't open "+param;
  }
}

Random_Dev::~Random_Dev()
{
  if (fd) {
    close(fd);
  }
}


std::string Random_Dev::stringify() {
  if (status) {
    return _param;
  }
  return Writable::stringify();
}


unsigned long Random_Dev::rand() {
  unsigned int ret=0;
  ssize_t len;

  do {
    len=read(fd,&ret,sizeof(ret));
  } while (len!=sizeof(ret));

  return ret;
}

FACTORY_DEFAULT_CREATOR(Random, Random_DevRandom, "/dev/random")
FACTORY_DEFAULT_CREATOR(Function, Random_DevRandomf, "/dev/random")
FACTORY_DEFAULT_CREATOR(Random, Random_DevuRandom, "/dev/urandom")

#endif /* __MINGW32__ */
