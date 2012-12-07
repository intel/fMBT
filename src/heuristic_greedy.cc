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
#include <string.h>
#include <vector>
#include <algorithm>

extern int _push_pop;

Heuristic_greedy::Heuristic_greedy(Log& l, std::string params) :
  Heuristic(l), m_search_depth(0), m_burst(false)
{
  m_search_depth = atoi(params.c_str());
  if (strchr(params.c_str(), 'b')) {
    m_burst = true;
  }
}

bool Heuristic_greedy::execute(int action)
{
  if (m_path.size() > 0) {
    int planned_action = m_path.back();
    if (planned_action != action) // invalidate planned path
      m_path.resize(0);
    else
      m_path.pop_back();
  }
  return Heuristic::execute(action);
}

int Heuristic_greedy::getAction()
{
  int* actions;
  int i = model->getActions(&actions);

  if (i==0) {
    return Alphabet::DEADLOCK;      
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
  if (!status) {
    return 0;
  }

  int* actions;
  int i = model->getIActions(&actions);
  int pos = -1;

  log.debug("greedy getIACtion %i",i);

  for(int u=0;u<i;u++) {
    log.debug("iaction %i %i",u,actions[u]);
  }
  
  if (i==0) {
    // No input actions. See if there are output actions available.
    i=model->getActions(&actions);
    if (i==0) {
      return Alphabet::DEADLOCK;
    }
    return Alphabet::OUTPUT_ONLY;
  }

  if (m_search_depth < 1) {
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
    /* In burst mode new path is not searched before previosly found
     * path is fully consumed */
    if (!m_burst || m_path.empty() ) {
      /* Spend more time for better coverage */
      _push_pop=m_search_depth;
      AlgPathToBestCoverage alg(m_search_depth);
      /* Use precalculated path (m_path) as a hint. */
      std::reverse(m_path.begin(), m_path.end());
      double score = alg.search(*model, *my_coverage, m_path);

      if (!alg.status) {
	status=false;
      }

      if (m_path.size() > 0) {
        std::reverse(m_path.begin(), m_path.end());
        log.debug("score: %f, path length: %d", score, m_path.size());
      }
    }
    if (m_path.size() > 0) {
      log.debug("path %i",m_path.back());
      i = model->getIActions(&actions);
      if (i==0) {
	return Alphabet::ERROR;
      }
      bool broken=true;
      int ret=m_path.back();
      for(int j=0;j<i;j++) {
	if (actions[j]==ret) {
	  broken=false;
	}
      }
      if (broken) {
	log.print("<ERROR msg=\"%s %i\"/>","trying to return action %i, which is not executable in the model",ret);
	abort();
      }
      return m_path.back();
    }
  }

  /* Fall back to random selection. Input actions table might not be
   * valid anymore (execute might have happened), ask it again. */
  i = model->getIActions(&actions);
  pos=(((float)random())/RAND_MAX)*i;

  return actions[pos];
}

FACTORY_DEFAULT_CREATOR(Heuristic, Heuristic_greedy, "greedy")
FACTORY_DEFAULT_CREATOR(Heuristic, Heuristic_greedy, "lookahead")
FACTORY_DEFAULT_CREATOR(Heuristic, Heuristic_greedy, "action_fitness")
