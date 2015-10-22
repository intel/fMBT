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
#include "learn_proxy.hh"
#include "helper.hh"

#include "function_array.hh"
#include "function_const.hh"

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
  Heuristic(l), m_search_depth(NULL), m_burst(false),adaptive(false),
  const_index(NULL),array_size(0),end_condition(false)
{
  hg=this;
  std::string s;

  std::vector<std::string> fa;
  commalist(params,fa);

  if (fa.size()>0) {
    s=fa[0];
  }

  // We have a potential problem. If function name ends with "b", this code 
  // thinks we mean <prefix> with burst mode on. So no functions ending with b :)
  if (g_str_has_suffix(s.c_str(), "b")) {
    m_burst = true;
    size_t found=s.find_last_of("b");
    s=s.substr(0,found);
  }

  if (s=="") {
    s="0";
  }

  m_search_depth = new_function(s);

  if (!m_search_depth) {
    errormsg="Can't create function \""+s+"\"";
    status=false;
    return;
  }

  if (!m_search_depth->status) {
    errormsg=m_search_depth->status;
    status=false;
  } else {
    Function_array* a=dynamic_cast<Function_array*>(m_search_depth);
    if (a) {
      const_index=dynamic_cast<Function_const*>(a->index);
      array_size=a->array.size();
    }
  }

  if (fa.size()>1) {
    randomise_function = new_function(fa[1]);
    if (randomise_function) {
      status=randomise_function->status;
      errormsg=randomise_function->errormsg;
    } else {
      status=false;
      errormsg="Can't create function \""+fa[1]+"\"";
    }
  } else {
    randomise_function=NULL;
  }

  if (fa.size()>2) {
    status=false;
    errormsg="Too many paramters. Expecting maxium of 2, got "+to_string((unsigned)fa.size());
  }

  r = Random::default_random();
}

Heuristic_greedy::~Heuristic_greedy()
{
  hg=NULL;

  if (r) 
    r->unref();

  if (randomise_function) {
    delete randomise_function;
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

  if (log.is_debug()) {
    log.debug("greedy getIAction %i", input_action_count);
    for(int u = 0; u < input_action_count; u++) {
      log.debug("iaction %i %i", u, input_actions[u]);
    }
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

  if (m_search_depth->val() < 1) {
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
      /* Use precalculated path (m_path) as a hint. */
      std::reverse(m_path.begin(), m_path.end());
      std::vector<int> tmp_path = m_path;

      double current_score=my_coverage->getCoverage();
      double score;
      AlgPathToBestCoverage* alg;

      /* Spend more time for better coverage */
      if (adaptive) {
	alg = new AlgPathToAdaptiveCoverage(m_search_depth->val(), learn, randomise_function);
      } else {
	alg = new AlgPathToBestCoverage(m_search_depth->val(), learn, randomise_function);
      }

      do {
	m_path = tmp_path;
	score = alg->search(*model,*my_coverage, m_path,m_search_depth->val());

	if (!alg->status) {
	  status=false;
	  errormsg = "Alg: " + alg->errormsg;
	  retval = 0;
	  delete alg;
	  goto done;
	}
	if (score<=current_score) {
	  log.print("<No improvement at depth %i/>\n",m_search_depth->val());
	}
      } while (const_index && score<=current_score && (const_index->stored_val++)<array_size);
      delete alg;

      end_condition=(score<=current_score);
      if (const_index) {
	log.print("<depth %i/>\n",m_search_depth->val());
	// Next time try a bit smaller value
	const_index->stored_val--;
	if (const_index->stored_val<0) {
	  const_index->stored_val=0;
	}
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

void Heuristic_adaptive_lookahead::set_learn(Learning* _learn) {
  Heuristic::set_learn(_learn);
  if (learn && ((Learn_proxy*)learn)->la) {
    // Ok. Something we need to do?
  } else {
    status=false;
    errormsg="adaptive_lookahead needs learning module action";
  }
}


FACTORY_DEFAULT_CREATOR(Heuristic, Heuristic_lookahead, "greedy")
FACTORY_DEFAULT_CREATOR(Heuristic, Heuristic_lookahead, "lookahead")
FACTORY_DEFAULT_CREATOR(Heuristic, Heuristic_lookahead, "action_fitness")
FACTORY_DEFAULT_CREATOR(Heuristic, Heuristic_adaptive_lookahead, "adaptive_lookahead")

#undef FACTORY_CREATE_DEFAULT_PARAMS
#define FACTORY_CREATE_DEFAULT_PARAMS /* */

#undef FACTORY_CREATOR_PARAMS
#undef FACTORY_CREATOR_PARAMS2
#define FACTORY_CREATOR_PARAMS Verdict::Verdict v, std::string params,Conf* co
#define FACTORY_CREATOR_PARAMS2 co, v, params

FACTORY_DEFAULT_CREATOR(End_condition, End_condition_bool, "lookahead_noprogress")
