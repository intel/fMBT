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
  if (m_burst && m_path.size() > 0) {
    int planned_action = m_path.back();
    if (planned_action != action) // invalidate planned path
      m_path.resize(0);
    else
      m_path.pop_back();
  }
  return Heuristic::execute(action);
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
    if (!m_burst || m_path.size() == 0) {
      /* Spend more time for better coverage */
      AlgPathToBestCoverage alg(m_search_depth);
      double score = alg.search(*model, *my_coverage, m_path);
      if (m_path.size() > 0) {
        std::reverse(m_path.begin(), m_path.end());
        log.debug("score: %f, path length: %d", score, m_path.size());
      }
    }
    if (m_path.size() > 0) {
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

namespace {
  Heuristic* creator_func2(Log& log, std::string params = "")
  {
    return new Heuristic_greedy(log, params);
  }
  static HeuristicFactory::Register me2("lookahead", creator_func2);
}

namespace {
  Heuristic* creator_func3(Log& log, std::string params = "")
  {
    std::string p("");
    return new Heuristic_greedy(log, p);
  }
  static HeuristicFactory::Register me3("action_fitness", creator_func3);
}
