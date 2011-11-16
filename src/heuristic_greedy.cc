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
#include "alg_bdfs.hh"
#include <stdlib.h>
#include <vector>

Heuristic_greedy::Heuristic_greedy(Log& l, std::string params) :
  Heuristic(l)
{
  m_search_depth = atoi(params.c_str());
}


float Heuristic_greedy::getCoverage() {
  if (my_coverage==NULL) {
    return 0.0;
  }
  return my_coverage->getCoverage();  
}

int Heuristic_greedy::getAction()
{
  int* actions;
  int i = model->getActions(&actions);

  if (i==0) {
    return DEADLOCK;      
  }

  float* f=new float[i];
  int pos=my_coverage->fitness(actions,i,f);
  float score = f[pos];
  delete [] f;

  if (score > 0.0) {
    log.debug("Greedy selected %i (out of %i)\n",
              pos,i);
    return actions[pos];
  }

  /* Fall back to random selection */
  pos=(((float)random())/RAND_MAX)*i;
  return actions[pos];
}

int Heuristic_greedy::getIAction()
{
  int* actions;
  int i = model->getIActions(&actions);
  int pos = -1;

  if (i==0) {
    // No input actions. See if there are output actions available.
    i=model->getActions(&actions);
    if (i==0) {
      return DEADLOCK;      
    }
    return OUTPUT_ONLY;
  }

  if (m_search_depth <= 1) {
    /* Do a very fast lookup */
    float* f=new float[i];
    pos=my_coverage->fitness(actions,i,f);
    float score = f[pos];
    delete [] f;

    if (score > 0.0) {
      log.debug("Greedy selected %i (out of %i)\n",
                pos,i);
      return actions[pos];
    }
  } else {
    /* Spend more time for better coverage */
    AlgPathToBestCoverage alg(m_search_depth);
    std::vector<int> path;
    double score = alg.search(*model, *my_coverage, path);
    if (path.size() > 0) {
      fprintf(stderr, "\nactions:");
      for (unsigned int u = 0; u < path.size(); u++) fprintf(stderr, " %d ", path[u]);
      fprintf(stderr, "\nscore: %f\n", score);
      return path[0];
    }
  }

  /* Fall back to random selection */
  pos=(((float)random())/RAND_MAX)*i;
  return actions[pos];
}

FACTORY_DEFAULT_CREATOR(Heuristic, Heuristic_greedy, "greedy");
