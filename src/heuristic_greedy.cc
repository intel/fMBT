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

#include "heuristic_greedy.hh"
#include <stdlib.h>

float Heuristic_greedy::getCoverage() {
  if (my_coverage==NULL) {
    return 0.0;
  }
  return my_coverage->getCoverage();  
}

int Heuristic_greedy::getAction()
{
  int* actions;
  int i;

  i=model->getActions(&actions);

  if (i==0) {
    // DEADLOCK
    return DEADLOCK;
  }

  float* f=new float[i];

  int pos=my_coverage->fitness(actions,i,f);

  if (f[pos]==0.0) {
    pos=(((float)random())/RAND_MAX)*i;
  }

  delete [] f;

  log.debug("Greedy selected %i (out of %i)\n",
	 pos,i);

  return actions[pos]; // Quite bad greedy..
}

int Heuristic_greedy::getIAction()
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

  float* f=new float[i];

  int pos=my_coverage->fitness(actions,i,f);

  for(int j=0;j<i;j++) {
    log.debug("%i (%i:%s) %04f\n",j,actions[j],
	   getActionName(actions[j]).c_str(),f[j]);
  }

  if (f[pos]==0.0) {
    pos=(((float)random())/RAND_MAX)*i;
  }

  delete [] f;

  log.debug("Greedy selected %i (out of %i)\n",
	 pos,i);

  return actions[pos]; // Quite bad greedy..
}

namespace {
  Heuristic* heuristic_creator(Log&l) {
    return new Heuristic_greedy(l);
  }
  static Heuristic_Creator heuristic_foo("greedy",heuristic_creator);
};
