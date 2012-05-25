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

#include "heuristic_random.hh"
#include <stdlib.h>

Heuristic_random::Heuristic_random(Log& l, std::string params) :
  Heuristic(l)
{
  unsigned int random_seed = 0;
  if (params == "") {
    random_seed = time(NULL);
  } else {
    random_seed = atoi(params.c_str());
  }
  log.print("<heuristic_random seed=\"%d\"/>\n", random_seed);
  srandom(random_seed);
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
    return DEADLOCK;
  }

  return select(i,actions);
}

int Heuristic_random::select(int i,int* actions)
{
  int pos=(((float)random())/RAND_MAX)*i;

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
      return DEADLOCK;      
    }
    return OUTPUT_ONLY;
  }

  return select(i,actions);
}

FACTORY_DEFAULT_CREATOR(Heuristic, Heuristic_random, "random")
