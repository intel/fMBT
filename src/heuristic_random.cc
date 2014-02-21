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
#include "function.hh"
#include "random.hh"
#undef FACTORY_CREATOR_PARAMS
#undef FACTORY_CREATOR_PARAMS2 
#undef FACTORY_CREATE_PARAMS

#define FACTORY_CREATOR_PARAMS Log& log,std::string params
#define FACTORY_CREATOR_PARAMS2 log, params
#define FACTORY_CREATE_PARAMS Log& log,                                \
                       std::string name,                               \
                       std::string params

#include "helper.hh"
#include "heuristic_random.hh"
#include <stdlib.h>

Heuristic_random::Heuristic_random(Log& l,const std::string& _params) :
  Heuristic(l)
{
  std::string params(_params);
  if (params == "") {
    r = Random::default_random();
    r->ref();
  } else {
    r = new_random(params);
    if (!r) {
      // Ok. Let's check if it's a function?
      params=std::string("c(")+params+")";
      r = new_random(params);
      if (!r) {
	status=false;
	errormsg="Can't create random "+_params;
	return;
      }
    }
    r->ref();
    if (!r->status) {
      status=false;
      errormsg=r->errormsg;
    } else {
      log.push(params.c_str());
      log.print("<random init==\"%s\"/>\n",r->stringify().c_str());
      log.pop();
    }
  }
}

Heuristic_random::~Heuristic_random() {
  if (r)
    r->unref();
}

float Heuristic_random::getCoverage() {
  if (my_coverage==NULL) {
    return 0.0;
  }
  return my_coverage->getCoverage();  
}

int Heuristic_random::getAction()
{
  int* actions;
  int i;

  i=model->getActions(&actions);

  if (i==0) {
    // DEADLOCK
    return Alphabet::DEADLOCK;
  }

  return select(i,actions);
}

int Heuristic_random::select(int i,int* actions)
{
  int pos=r->drand48()*i;

  return actions[pos];
}

int Heuristic_random::getIAction()
{
  int* actions;
  int i;

  i=model->getIActions(&actions);

  if (i==0) {
    // Ok.. no output actions
    i=model->getActions(&actions);
    if (i==0) {
      return Alphabet::DEADLOCK;      
    }
    return Alphabet::OUTPUT_ONLY;
  }

  return select(i,actions);
}

FACTORY_DEFAULT_CREATOR(Heuristic, Heuristic_random, "random")
