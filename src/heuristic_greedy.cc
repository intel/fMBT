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
#include "helper.hh"
#include "heuristic_greedy.hh"
#include "alg_bdfs.hh"
#include <stdlib.h>
#include <string.h>
#include <vector>
#include <algorithm>
#include "random.hh"

extern int _g_simulation_depth_hint;

static Heuristic_greedy* hg=NULL;

#include "end_condition.hh"

class End_condition_bool: public End_condition_noprogress {
public:
  End_condition_bool(Conf* _conf,Verdict::Verdict v, const std::string& p):
    End_condition_noprogress(_conf,v,p) {

  }
  virtual ~End_condition_bool() {}
  virtual bool match(int step_count,int state, int action,int last_step_cov_growth,Heuristic& heuristic,std::vector<int>& mismatch_tags) {
    if (hg)
      return hg->end_condition;
    return false;
  }
};

Heuristic_greedy::Heuristic_greedy(Log& l,const std::string& params) :
  Heuristic(l), m_search_depth(0), m_burst(false),end_condition(false)
{
  hg=this;

  m_search_depth = atoi(params.c_str());
  if (strchr(params.c_str(), 'b')) {
    m_burst = true;
  }
  r = Random::default_random();
  r->ref();
}

Heuristic_greedy::~Heuristic_greedy()
{
  hg=NULL;

  if (r)
    r->unref();
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
  pos=r->drand48()*i;
  return actions[pos];
}

int Heuristic_greedy::getIAction()
{
  if (!status) {
    return 0;
  }

  int* actions = NULL;
  int input_action_count = model->getIActions(&actions);

  /* Copy actions to input_actions because next model->getIActions
   * call changes the data */
  int* input_actions = new int[input_action_count];
  memcpy(input_actions, actions, input_action_count * sizeof(int));
  int retval = -42;

  log.debug("greedy getIAction %i", input_action_count);

  for(int u = 0; u < input_action_count; u++) {
    log.debug("iaction %i %i", u, input_actions[u]);
  }

  if (input_action_count == 0) {
    // No input actions. See if there are output actions available.
    int output_action_count = model->getActions(&actions);
    if (output_action_count == 0) {
      retval = Alphabet::DEADLOCK;
      goto done;
    }
    retval = Alphabet::OUTPUT_ONLY;
    goto done;
  }

  if (m_search_depth < 1) {
    /* Do a very fast lookup */
    float* f = new float[input_action_count];
    int pos = my_coverage->fitness(input_actions, input_action_count, f);
    float score = f[pos];
    delete [] f;

    if (score > 0.0) {
      log.debug("Greedy selected %i (out of %i)\n",
                pos,input_action_count);
      retval = input_actions[pos];
      goto done;
    }
  } else {
    /* In burst mode new path is not searched before previosly found
     * path is fully consumed */
    if (!m_burst || m_path.empty() ) {
      /* Spend more time for better coverage */
      AlgPathToBestCoverage alg(m_search_depth);
      /* Use precalculated path (m_path) as a hint. */
      std::reverse(m_path.begin(), m_path.end());
      double current_score=my_coverage->getCoverage();
      double score = alg.search(*model, *my_coverage, m_path);

      end_condition=(score<=current_score);

      if (!alg.status) {
        status=false;
	errormsg = "Alg: " + alg.errormsg;
	retval = 0;
	goto done;
      }

      if (m_path.size() > 0) {
        std::reverse(m_path.begin(), m_path.end());
        log.debug("score: %f, path length: %d", score, m_path.size());
      }
    }
    if (m_path.size() > 0) {
      log.debug("path %i",m_path.back());
      bool broken = true;
      retval = m_path.back();
      for(int j = 0; j < input_action_count; j++) {
        if (input_actions[j] == retval) {
          broken=false;
          break;
        }
      }
      if (broken) {
        log.print("<ERROR msg=\"%s (%s)\"/>","suggesting disabled action",
                  model->getActionName(retval).c_str());
        abort();
      }
      goto done;
    }
  }

  /* Fall back to random selection. */
  retval = input_actions[(int)(r->drand48()*input_action_count)];

done:
  delete[] input_actions;
  return retval;
}

FACTORY_DEFAULT_CREATOR(Heuristic, Heuristic_greedy, "greedy")
FACTORY_DEFAULT_CREATOR(Heuristic, Heuristic_greedy, "lookahead")
FACTORY_DEFAULT_CREATOR(Heuristic, Heuristic_greedy, "action_fitness")

#undef FACTORY_CREATE_DEFAULT_PARAMS
#define FACTORY_CREATE_DEFAULT_PARAMS /* */

#undef FACTORY_CREATOR_PARAMS
#undef FACTORY_CREATOR_PARAMS2
#define FACTORY_CREATOR_PARAMS Verdict::Verdict v, std::string params,Conf* co
#define FACTORY_CREATOR_PARAMS2 co, v, params
FACTORY_DEFAULT_CREATOR(End_condition, End_condition_bool, "lookahead_noprogress");
