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

#define _RANDOM_INTERNAL_
#include "function.hh"
#include "random_supported.hh"
#include "params.hh"
#include "helper.hh"

Random_Supported::Random_Supported(const std::string& param) {
  std::vector<std::string> s;
  commalist(param,s);
  r=NULL;
  for(unsigned i=0;i<s.size();i++) {
    r=new_random(s[i]);
    if (r) {
      if (!r->status) {
	delete r;
	r=NULL;
      } else {
	return;
      }
    }
  }
  if (r==NULL) {
    status=false;
  }
}

Random_Supported::~Random_Supported()
{
  if (r)
    delete r;
}


std::string Random_Supported::stringify() {
  if (status) {
    return r->stringify();
  } 
  return Writable::stringify();
}

double Random_Supported::drand48() {
  return r->drand48();
}

unsigned long Random_Supported::rand() {
  return r->rand();
}

FACTORY_DEFAULT_CREATOR(Random, Random_Supported, "supported")
