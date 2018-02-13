/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2011,2012 Intel Corporation.
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

#include "test_engine.hh"
#include "log.hh"
#include "alg_bdfs.hh"
#include "coverage.hh"
#include "helper.hh"
#include <cstdio>
#include <algorithm>

time_t    Test_engine::end_time;

char* READLINE(const char* prompt,FILE* ostream);

#include <cstdlib>
#include <cstring>

#ifdef __MINGW32__
extern "C" {
size_t strnlen(const char *s, size_t maxlen)
{
  const char *end =(const char*) memchr (s, '\0', maxlen);
  return end ? (size_t) (end - s) : maxlen;
}
}
#endif


void Test_engine::print_time(struct timeval& start_time,
                             struct timeval& total_time)
{
  gettime(&Adapter::current_time);
  log.print("<current_time time=\"%i.%06i\"/>\n",Adapter::current_time.tv_sec,
            Adapter::current_time.tv_usec);
  timersub(&Adapter::current_time,&start_time,&total_time);
  log.print("<elapsed_time time=\"%i.%06i\"/>\n",total_time.tv_sec,
            total_time.tv_usec);
}

Test_engine::Test_engine(Heuristic& h,Adapter& a,Log& l,Policy& p,std::vector<End_condition*>& ecs,std::map<int,bool>& _disabled_tags)
  : step_count(0),
    heuristic(h),
    adapter(a),
    log(l),
    policy(p),
    end_conditions(ecs),
    last_step_cov_growth(0),
    m_verdict(Verdict::UNDEFINED),
    m_verdict_msg("undefined"),
    m_reason_msg("undefined"),
    break_check(false),
    disabled_tags(_disabled_tags)
{
  p.set_model(h.get_model());
  // Set rest of the models also..
}

Test_engine::~Test_engine()
{
}

namespace {
  /* logging helpers */
  void log_tag_type_name(Log& log, const char *tag, const char *type, const char *name) {
    gettime(&Adapter::current_time);
    log.print("<%s type=\"%s\" name=\"%s\" time=\"%i.%06i\"/>\n", tag, type,
	      name,Adapter::current_time.tv_sec,Adapter::current_time.tv_usec);
  }
  void log_adapter_suggest(Log& log, Adapter& adapter, int action, Model& m) {
    log_tag_type_name(log, "suggested_action", m.is_output(action)?"output":"input", adapter.getUActionName(action));
  }
  void log_adapter(Log& log, Adapter& adapter, int action, Model& m) {
    log_tag_type_name(log, "action", m.is_output(action)?"output":"input", adapter.getUActionName(action));
  }
  void log_status(Log& log, int step_count, float coverage) {
    log.print("<status steps=\"%d\" coverage=\"%f\" scov=\"%e\"/>\n",
              step_count, coverage,coverage);
  }
  void update_coverage(float curr_cov, int curr_step,
                       float *last_cov, int *last_step_cov_growth) {
    /* Compare volatiles instead of "curr_cov > *last_cov", because we
     * want to compare actual values in memory instead of possibly
     * more precise results that might have stayed in FPU register.
     */
    volatile float current = curr_cov;
    volatile float previous = *last_cov;
    if (current > previous) {
      *last_cov = current;
      *last_step_cov_growth = curr_step;
    }
  }
}

const std::string& Test_engine::verdict_msg()
{
  return m_verdict_msg;
}

const std::string& Test_engine::reason_msg()
{
  return m_reason_msg;
}

Verdict::Verdict Test_engine::verdict()
{
  return m_verdict;
}

Verdict::Verdict Test_engine::stop_test(Verdict::Verdict v, const char* _reason)
{
  m_verdict = v;
  m_reason_msg = _reason;
  m_verdict_msg = to_string(m_verdict);

  /*
    Just remember to encode the strings...
   */
  std::string me_reason_msg=m_reason_msg;
  escape_string(m_verdict_msg);
  escape_string(me_reason_msg);

  log.print("<stop verdict=\"%s\" reason=\"%s\"/>\n",
            m_verdict_msg.c_str(), me_reason_msg.c_str());
  print_time(start_time, total_time);
  log.pop();
  return m_verdict;
}

Verdict::Verdict Test_engine::stop_test(End_condition* ec)
{
  return stop_test(ec->verdict,ec->end_reason().c_str());
}

void Test_engine::verify_tags(const std::vector<std::string>& tnames)
{
  Model* model=heuristic.get_model();
  int* tags;
  int cnt=model->getprops(&tags);

  mismatch_tags.clear();

  if (!model->status) {
    return;
  }

  for(int i=0;i<cnt;i++) {
    if (tags[i]>=(int)tnames.size() ||
        tags[i]<0) {
      model->errormsg="tag out of range";
      model->status=false;
      return;
    }
  }

  if (tagverify_disabled) {
    return;
  }

  std::string s=to_string(cnt,tags,tnames);
  log.print("<tags enabled=\"%s\"/>\n",s.c_str());

  std::vector<int> t;
  for(int i=0;i<cnt;i++) {
    if (!disabled_tags[tags[i]]) {
      t.push_back(tags[i]);
    }
  }

  cnt=t.size();
  if (!t.empty()) {
    tags=&t[0];
  }

  if (cnt) {
    adapter.check_tags(tags,cnt,mismatch_tags);
    /*
    if (mismatch_tags.size()) {
      m_verdict_msg = "verifying tags ";
    }
    for(int i=0;i<mismatch_tags.size();i++) {
      m_verdict_msg+="\""+heuristic.get_model()->getSPNames()[mismatch_tags[i]]+"\" ";
    }
    m_verdict_msg+="failed.";
    //return failing_tag;
    */
  }
  return;
}

void log_strarray(Log&l,
                  const char* tag,
                  std::vector<std::string>& array,
                  unsigned first_element=1);

void log_strarray(Log&l,
                  const char* tag,
                  std::vector<std::string>& array,
                  unsigned first_element) {
  for(unsigned i=first_element;i<array.size();i++) {
    char* s=array[i].c_str();
    l.print("<%s\"%s\"/>\n",tag,s);
    escape_free(s);
  }
}


Verdict::Verdict Test_engine::run(time_t _end_time,bool disable_tagverify)
{
  float last_coverage = heuristic.getCoverage();
  Model* m=heuristic.get_model();
  end_time=_end_time;

  tagverify_disabled=disable_tagverify;

  int condition_i = -1; /* index of end condition that is stopping the run */


  int action=0;
  std::vector<int> actions;

  std::vector<std::string> tags=m->getSPNames();
  ssize_t action_count = m->getActionNames().size();

  log_strarray(log,"action_name name=",
               m->getActionNames());
  log_strarray(log,"tag_name name=",
               tags);

  log.push("test_engine");
  gettime(&start_time);

  for(unsigned i=0;i<tags.size();i++) {
    escape_string(tags[i]);
  }

  verify_tags(tags);
  log_status(log, step_count, heuristic.getCoverage());
  int act=-1;
  while (-1 == (condition_i = matching_end_condition(step_count,0,act))) {
    action=0;
    act=-1;
    gettime(&Adapter::current_time);
    log.print("<current_time time=\"%i.%06i\"/>\n",Adapter::current_time.tv_sec,
              Adapter::current_time.tv_usec);

    while (adapter.observe(actions)>0) {

      if (!adapter.status) {
        return stop_test(Verdict::W_ERROR, ("adapter error: "+adapter.errormsg).c_str());
      }

      step_count++;
      action = policy.choose(actions);
      if ((action>0)&&((unsigned)action>=action_count)) {
        return stop_test(Verdict::W_ERROR, std::string("adapter communication failure. Adapter returned action "+to_string(action)+" which is out of range").c_str());
      }
      log_adapter(log, adapter, action,*m);

      if (!heuristic.execute(action)) {
        if (!heuristic.status) {
          return stop_test(Verdict::W_ERROR, heuristic.errormsg.c_str());
        }
        log.debug("Test_engine::run: Error: unexpected output from the SUT: %i '%s'\n",
                  action, heuristic.getActionName(action).c_str());

        return stop_test(Verdict::FAIL, "unexpected output");
      }

      verify_tags(tags);

      log_status(log, step_count, heuristic.getCoverage());
      update_coverage(heuristic.getCoverage(), step_count,
                      &last_coverage, &last_step_cov_growth);
      gettime(&Adapter::current_time);
      log.print("<current_time time=\"%i.%06i\"/>\n",Adapter::current_time.tv_sec,
                Adapter::current_time.tv_usec);
      if (-1 != (condition_i = matching_end_condition(step_count,0,action))) {
        goto out;
      }
    }

    action = heuristic.getIAction();

    if (!heuristic.status) {
      return stop_test(Verdict::W_ERROR, "Heuristic error");
    }

    if (action >= 0) {
      log.debug("Test_engine::run: test generator suggests executing %i '%s'\n",
                action, heuristic.getActionName(action).c_str());
    }

    // Check if end_condition matches. Might be because of the heuristics
    // tells to stop.
    if (-1 != (condition_i = matching_end_condition(step_count,0))) {
      goto out;
    }

    step_count++;

    log.debug("Step %i",step_count);

    switch(action) {
    case Alphabet::ERROR: {
      return stop_test(Verdict::W_ERROR, "Model error");
      break;
    }
    case Alphabet::DEADLOCK: {
      log.print("<state type=\"deadlock\"/>\n");

      if (-1 != (condition_i = matching_end_condition(step_count,Alphabet::DEADLOCK))) {
        goto out;
      }

      int ret=adapter.observe(actions,true);

      if (!adapter.status) {
        return stop_test(Verdict::W_ERROR, ("adapter error: "+adapter.errormsg).c_str());
      }

      if (ret!=Alphabet::SILENCE && ret!=Alphabet::TIMEOUT) {
        return stop_test(Verdict::FAIL, "response on deadlock");
      }
      return stop_test(Verdict::PASS, "end of model");
      break;
    }
    case Alphabet::OUTPUT_ONLY: {
      log.print("<state type=\"output only\"/>\n");

      int value = adapter.observe(actions,true);

      if (!adapter.status) {
        return stop_test(Verdict::W_ERROR, ("adapter error: "+adapter.errormsg).c_str());
      }

      log.print("<observe %i/>\n",value);

      if (value==Alphabet::TIMEOUT) {
        actions.resize(1);
        actions[0] = Alphabet::TIMEOUT;
        log.print("<TIMEOUT %i %i/>\n",Adapter::current_time.tv_sec,
                  end_time);
        if (-1 != (condition_i = matching_end_condition(step_count,actions[0])))
          goto out;

        // TIMEOUT means that testing has run out of time
        // before adapter observed output. There should have
        // been a matching end condition that defines the
        // verdict for this case.
        // If not, let's return an error.
        return stop_test(Verdict::W_ERROR,
                         "TIMEOUT while communicating with adapter");

      } else if (value==Alphabet::SILENCE) {
        actions.resize(1);
        actions[0] = Alphabet::SILENCE;
        log.debug("Test_engine::run: SUT remained silent (action %i).\n", action);
      } else {
        if (!actions.empty()) {
          log.debug("Test_engine::run: SUT executed %i '%s'\n",
                    actions[0],heuristic.getActionName(actions[0]).c_str());
        }
      }

      if (actions.empty()) {
        return stop_test(Verdict::W_ERROR, "adapter communication failure");
      }

      action = actions[0]; // TODO: add policy here when it works
      log_adapter(log, adapter, action,*m);
      if (!heuristic.execute(action)) {
        log.debug("Test_engine::run: ERROR: action %i not possible in the model.\n", action);
        log.debug("%s %s",action,heuristic.getActionName(action).c_str(),"broken response");
        return stop_test(Verdict::FAIL, "unexpected output");
      }
      break;
    }
    default: { /* INPUT: suggest execution of an input action */
      log.debug("Test_engine::run: sending input action %i to the SUT.\n", action);
      actions.resize(1);
      actions[0]=action;
      log_adapter_suggest(log, adapter, actions[0],*m);
      adapter.execute(actions);

      if (!adapter.status) {
        return stop_test(Verdict::W_ERROR, ("adapter error: "+adapter.errormsg).c_str());
      }

      if (actions.empty()) {
        return stop_test(Verdict::W_ERROR, "adapter communication failure");
      }
      int adapter_response = policy.choose(actions);

      // Let's chect that adapter_response is in the valid range.
      if ((adapter_response>0) && ((unsigned)adapter_response>=action_count)) {
        return stop_test(Verdict::W_ERROR, std::string("adapter communication failure. Adapter returned action "+to_string(adapter_response)+" which is out of range").c_str());
      }

      log_adapter(log, adapter, adapter_response,*m);

      log.debug("Test_engine::run: passing adapter response action %i to test generation.\n",
                adapter_response);
      log.push("adapter_executed");
      log.pop(); // adapter_executed

      if (!heuristic.execute(adapter_response)) {
        if (!heuristic.status) {
          return stop_test(Verdict::W_ERROR, heuristic.errormsg.c_str());
        }
        std::string msg = "unexpected response to input \"" +
          heuristic.getActionName(action) + "\": ";
        if (adapter_response == 0) msg += "unidentified result.";
        else msg +="\"" + heuristic.getActionName(adapter_response) + "\".";

        log.debug("Test_engine::run: ERROR: SUT executed %i '%s', not allowed in the model.\n",
                  action, heuristic.getActionName(action).c_str());
        log.debug("%i %s %s",action,heuristic.getActionName(action).c_str(),"broken input acceptance");
        return stop_test(Verdict::FAIL, msg.c_str());
      }

      // This is here on purpose. We want to check break condition after
      // checking if the response is 'correct'
      act=adapter_response;
      if (break_check && -1 != (condition_i = matching_end_condition(step_count,0,adapter_response))) {
        goto out;
      }

    }
    }// switch
    verify_tags(tags);
    log_status(log, step_count, heuristic.getCoverage());
    update_coverage(heuristic.getCoverage(), step_count,
                    &last_coverage, &last_step_cov_growth);

  }

 out:
  return stop_test(end_conditions[condition_i]);
}

namespace interactive {
  void execute(Log &log,
               Adapter& adapter, Heuristic& heuristic, Model& model,
               int action, Policy& policy,
               bool skip_a, bool skip_m)
  {
    int adapter_response = 0;

    if (skip_m)
      fprintf(stderr,"executing: %s\n", adapter.getActionName(action).c_str());
    else
      fprintf(stderr,"executing: %s\n", heuristic.getActionName(action).c_str());

    if (skip_a) {
      fprintf(stderr,  "adapter:   [skipped]\n");
      adapter_response = action;
    } else if (model.up() != NULL) {
      fprintf(stderr,  "adapter:   [skipped] (submodel exec)\n");
      adapter_response = action;
    } else {
      std::vector<int> actions_v;
      actions_v.resize(1);
      actions_v[0] = action;
      log_adapter_suggest(log, adapter, actions_v[0],model);
      adapter.execute(actions_v);
      if (actions_v.empty()) {
        fprintf(stderr,"adapter:   [communication failure]\n");
        return;
      } else {
        if (skip_m) adapter_response = actions_v[0];
        else adapter_response = policy.choose(actions_v);

        if ((adapter_response>0) &&
            (adapter_response>=(int)heuristic.get_model()->getActionNames().size())) {
          fprintf(stderr,"adapter:   [communication failure %i]\n",adapter_response);
          return;
        } else {
          log_adapter(log, adapter, adapter_response,*heuristic.get_model());
          fprintf(stderr,"adapter:   %s\n", heuristic.getActionName(adapter_response).c_str());
        }
      }
    }

    if (skip_m)
      fprintf(stderr,                    "model:     [skipped]\n");
    else if (adapter.up() != NULL)
      fprintf(stderr,                    "model:     [skipped] (subadapter exec)\n");
    else {
      bool model_response;
      if (model.up()) model_response = model.execute(adapter_response);
      else model_response = heuristic.execute(adapter_response);
      if (model_response) fprintf(stderr,"model:     ok\n");
      else fprintf(stderr,               "model:     failed\n");
    }

    log_status(log, -1, heuristic.getCoverage());
  }
}

void Test_engine::interactive()
{
  int action=0;
  std::vector<int> actions_v;
  bool run=true;

  bool skip_adapter_execute   = false;
  bool skip_model_execute     = false;

  Adapter* current_adapter=&adapter;
  Model* current_model=heuristic.get_model();

  std::vector<End_condition*> etags;
  std::vector<End_condition*> atags;
  std::string breakstr("breakpoint");

  while (run) {

    while (adapter.observe(actions_v)>0) {
      action=actions_v[0];
      fprintf(stderr,"Action %i:%s\n",action,heuristic.getActionName(action).c_str());
      interactive::execute(log, adapter, heuristic, *heuristic.get_model(),
			   action, policy,
			   true, skip_model_execute);

      actions_v.resize(0);
    }

    char* s=READLINE("fMBT> ",stderr);

    if (s==NULL) {
      run=false;
    } else {
      unsigned int num = 0;

      switch (*s) {
      case 'h': {
	// heuristic
	Heuristic* h;
	std::string tmp(s+1);
	clear_whitespace(tmp);
	if (tmp!="") {
	  h=new_heuristic(log,tmp);
	  if (h!=NULL) {
	    if (h->status) {
	      h->set_coverage(heuristic.get_coverage());
	      h->set_model(heuristic.get_model());
	    } else {
	      printf("Heuristic error %s\n",h->errormsg.c_str());
	    }
	  } else {
	    printf("Can't create heuristic %s\n",s+1);
	    break;
	  }
	} else {
	  h=&heuristic;
	}

	printf("%s\n",h->getActionName(h->getIAction()).c_str());

	if (h!=&heuristic) {
	  delete h;
	}
	break;
      }
      case 'c': {
        // Feel free to improve.
        End_condition* e=NULL;
        size_t count=end_conditions.size();
        end_conditions.insert(end_conditions.begin()+count,
                              etags.begin(),etags.end());
        end_conditions.insert(end_conditions.begin()+count+etags.size(),
                              atags.begin(),atags.end());

        num=atoi(s+1);
        if (num>0) {
	  // Configuration not needed in the steps end condition
          e=new End_condition_steps(NULL,Verdict::INCONCLUSIVE,breakstr);
          e->param_long=step_count+num;
          end_conditions.push_back(e);
        }

        break_check=true;
        this->run(-1,tagverify_disabled);
        break_check=false;

        end_conditions.erase(end_conditions.begin()+count,end_conditions.end());
        break;
      }
      case 'd': {
        num=std::atoi(s+1);
        if (num>0 && num<=atags.size()) {
          atags.erase(atags.begin()+num-1);
        }
        if (s[1]=='d') {
          atags.clear();
        }
        break;
      }
      case 'D': {
        num=std::atoi(s+1);
        if (num>0 && num<=etags.size()) {
          etags.erase(etags.begin()+num-1);
        }
        if (s[1]=='D') {
          etags.clear();
        }
        break;
     }
      case 'b': {
        std::vector<std::string>& ana=heuristic.get_model()->getActionNames();
        num=std::atoi(s+1);
        if (num>0 && num<=ana.size()) {
          // Add breakpoint
          End_condition* e=new End_condition_action(NULL,Verdict::INCONCLUSIVE,
                                                    breakstr);
          e->param_long=num;
          atags.push_back(e);
        } else {
          // print action breakpoints
          if (s[1]=='b') {
            // print numbers
            printf("Action breakpoints (%i)\n",(int)atags.size());
            for(unsigned i=0;i<atags.size();i++) {
              if (atags[i]>0)
                printf(" %i: %i\n",i+1,(int)atags[i]->param_long);
            }
          } else {
            // print names
            printf("Action breakpoints (%i)\n",(int)atags.size());
            for(unsigned i=0;i<atags.size();i++) {
              if (atags[i]>0)
                printf(" %i: %s\n",i+1,ana[atags[i]->param_long].c_str());
            }
          }
        }
        break;
      }

      case 'B': {
        num=std::atoi(s+1);
        std::vector<std::string>& ana=heuristic.get_model()->getSPNames();
        unsigned int tag_count=ana.size();
        if (num>0 && num<=tag_count) {
          // Add breakpoint
          End_condition* e=new End_condition_tag(NULL,Verdict::INCONCLUSIVE,
                                                 breakstr);
          e->param_long=num;
          etags.push_back(e);
        } else {
          // print tag breakpoints
          if (s[1]=='B') {
            // print numbers
            printf("Tag breakpoints (%i)\n",(int)etags.size());
            for(unsigned i=0;i<etags.size();i++) {
              if (etags[i]>0)
                printf(" %i: %i\n",i+1,(int)etags[i]->param_long);
            }
          } else {
            // print names
            printf("Tag breakpoints (%i)\n",(int)etags.size());
            for(unsigned i=0;i<etags.size();i++) {
              if (etags[i]>0)
                printf(" %i: %s\n",i+1,ana[etags[i]->param_long].c_str());
            }
          }
        }
        break;
      }

      case 's': { // commands "s", "s<num>": execute action at current state
        int* actions = 0;
        unsigned int action_count=current_model->getActions(&actions);
        num=std::atoi(s+1);
        if (num>0 && num<=action_count) {
          // sm<num> command: execute the nth action at the current
          // state of the model. Always use the top-level adapter.
          interactive::execute(log, adapter, heuristic, *current_model,
                               actions[num-1], policy,
                               skip_adapter_execute, skip_model_execute);
          // state might have changed, update available actions
          action_count=current_model->getActions(&actions);
        }
        // print actions available at current state
        print_vectors(actions,action_count,
                      current_model->getActionNames(),"s",1);
      }
        break;
      case 'C': { // print coverage
        printf("coverage %05f\n",heuristic.getCoverage());
        break;
      }

      case 'e': { // commands "e", "e<num>": execute any action at current adapter
        num=std::atoi(s+1);
        std::vector<std::string>& ca_anames=current_adapter->getAllActions();
        std::vector<std::string> sca_anames=ca_anames; /* copy for sorted actions */
        sort(sca_anames.begin(), sca_anames.end());
        if (num>0 && num<sca_anames.size()) {
          unsigned action_num=0;
          for (action_num=1; action_num<sca_anames.size(); action_num++)
            if (ca_anames[action_num]==sca_anames[num]) break;

          interactive::execute(log, *current_adapter, heuristic, *current_model,
                               action_num, policy,
                               skip_adapter_execute, skip_model_execute);

        }
        else {
          for(unsigned i=1;i<sca_anames.size();i++){
            fprintf(stderr,"e%i:%s\n",i,sca_anames[i].c_str());
          }
        }
      }
        break;

      case 'i': { // starts an input action name?
        std::vector<std::string>& ca_anames=current_adapter->getAllActions();
        unsigned int action_num;
        for (action_num=1;action_num<ca_anames.size();action_num++) {
          if (ca_anames[action_num]==std::string(s)) {

            interactive::execute(log, *current_adapter, heuristic, *current_model,
                                 action_num, policy,
                                 skip_adapter_execute, skip_model_execute);
            break;
          }
        }
        if (action_num==ca_anames.size()) {
          fprintf(stderr,"action \"%s\" not found in the adapter\n", s);
        }
      }
        break;

      case 'a': // commands "a", "a<num>" and "aup"
	if (strncmp(s,"ae",2)==0) {
	  std::string name,option;
	  std::vector<std::string> p;
	  param_cut(s,name,option);
	  commalist(option,p);
	  if (p.size()<1||p.size()>2) {
	    goto unknown_command;
	  }
	  adapter.adapter_exit(from_string(p[0]),
			       p.size()==2?p[1]:"");
	  break;
	}
	if (strncmp(s,"at",2)==0) {
	  num=std::atoi(s+2);
	  int cnt=1;
	  mismatch_tags.clear();
	  adapter.check_tags((int*)&num,cnt,mismatch_tags);

	  for(unsigned i=0;i<mismatch_tags.size();i++) {
	    fprintf(stderr,"Tag %s (%i) fails\n",
		    heuristic.get_model()
		    ->getSPNames()[mismatch_tags[i]].c_str(),
		    mismatch_tags[i]);
	  }
	} else {
	  if (strncmp(s,"aup",3)==0) {
	    // do up in the adapter tree
	    if (!current_adapter->up()) {
	      fprintf(stderr,"Can't go up in adapter tree\n");
	    } else {
	      current_adapter=current_adapter->up();
	    }
	  } else if (strnlen(s,2)==1) {
	    std::vector<std::string>& adapter_names=current_adapter->getAdapterNames();
	    for(unsigned int i=0;i<adapter_names.size();i++) {
	      if (adapter_names[i]!=std::string("")) {
		fprintf(stderr,"a%i:%s\n",i,adapter_names[i].c_str());
	      }
	    }
	  } else {
	    num=std::atoi(s+1);
	    if (!current_adapter->down(num)) {
	      fprintf(stderr,"Can't change to adapter %i\n",num);
	    } else {
	      current_adapter=current_adapter->down(num);
	    }
	  }
	}
	break;
      case 'q': // command "q": quit
        std::free(s);
        return;

      case 'm':
        num = std::atoi(s+1);
        if (strncmp(s,"ma",2)==0) {
          /* List actions in the current model */
          print_vector(current_model->getActionNames(), "", 0);
          break;
        } else
        if (strncmp(s,"mt",2)==0) {
          /* List model tags */
          print_vector(current_model->getSPNames(),"tag ",0);
          break;
        } else
        if (strncmp(s,"mc",2)==0) {
          /* Show tags at current state */
          int* tags = 0;
          unsigned int tag_count=current_model->getprops(&tags);
          print_vectors(tags,tag_count,
                        current_model->getSPNames(),"t",0);
          break;
        } else
          if (strncmp(s,"mpush",5)==0) {
            current_model->push();
            break;
          } else
          if (strncmp(s,"mpop",4)==0) {
            current_model->pop();
            break;
          } else
        if (strncmp(s,"mup",3)==0) {
          /* up */
          if (!current_model->up()) {
            fprintf(stderr,"Can't go up in model tree\n");
          } else {
            current_model=current_model->up();
          }
          break;
        } else
        if (strlen(s)==1) {
          /* print */
          std::vector<std::string>& model_names=current_model->getModelNames();
          for(unsigned int i=0;i<model_names.size();i++) {
            if (model_names[i]!=std::string("")) {
              fprintf(stderr,"m%i:%s\n",i,model_names[i].c_str());
            }
          }
          break;
        } else
        if (num>0) {
          /* switch to <num> */
          /* down */
          if (!current_model->down(num)) {
            fprintf(stderr,"Can't go down in model tree\n");
          } else {
            current_model=current_model->down(num);
          }
          break;
        }
        goto unknown_command;
      case 'o':
        if (strncmp(s,"oea",3) == 0) {
          if (strnlen(s,4) == 4) {
            if (!atoi(s+3)) skip_adapter_execute = true;
            else skip_adapter_execute = false;
          }
          fprintf(stderr,"execute action in adapter: ");
          if (skip_adapter_execute) fprintf(stderr,"no\n");
          else fprintf(stderr,"yes\n");
        }
        else if (strncmp(s,"oem",3) == 0) {
          if (strnlen(s,4) == 4) {
            if (!atoi(s+3)) skip_model_execute = true;
            else skip_model_execute = false;
          }
          fprintf(stderr,"execute action in model: ");
          if (skip_model_execute) fprintf(stderr,"no\n");
          else fprintf(stderr,"yes\n");
        }
        else goto unknown_command;
        break;
      case 't': // TODO
        fprintf(stderr,"t <+diff>\n");
        fprintf(stderr,"not implemented: advance Adapter::current_time");
        break;
      case '?':
        if (strncmp(s,"?a",2) == 0) {
          int num = std::atoi(s+2);
          int search_depth = 7;
          std::vector<int> path;
          AlgPathToAction alg(search_depth);
          double score = alg.search(*current_model, num, path);
          if (score != 1.0) {
              fprintf(stderr,"No path found to action %d within search depth %d\n", num, search_depth);
          } else {
              fprintf(stderr,"Path to execute action %s:\n", current_model->getActionName(num).c_str());
              for (unsigned int i = 0; i < path.size(); i++) {
                  fprintf(stderr,"%s\n", current_model->getActionName(path[i]).c_str());
              }
          }
          break;
        } else
        if (strncmp(s,"?c",2) == 0) {
          int num = std::atoi(s+2);
          std::vector<int> path;
          AlgPathToBestCoverage alg(num);
          Coverage* coverage = heuristic.get_coverage();
          double score = alg.search(*current_model, *coverage, path);
          fprintf(stderr,"Coverage %f achievable with path:\n", score);
          for (unsigned int i = 0; i < path.size(); i++) {
            fprintf(stderr,"%s\n", current_model->getActionName(path[i]).c_str());
          }
          break;
        }
        goto unknown_command;

      default:
      unknown_command:
        fprintf(stderr,"Execute actions:\n"
               "    s       - list executable actions at current state\n"
               "    s<num>  - exec action <num> of current state\n"
               "    e       - list executable actions at current adapter\n"
               "    e<num>  - exec action <num> of current adapter\n"
               "    <iname> - exec input action iname (starts with \"i\")\n"
               "    b       - print break actions (bb for numerical)\n"
               "    b<num>  - break at action <num>\n"
               "    d<num>  - delete action break <num>\n"
               "    dd      - delete all action breaks\n"
               "    B       - print break tags (BB for numerical)\n"
               "    B<num>  - break at tag <num>\n"
               "    D<num>  - delete tag break <num>\n"
               "    DD      - delete all tag breaks\n"
               "    c<num>  - run (max num iterations) until break or test exit\n"
               "Change adapters/models:\n"
               "    a      - list low-level adapters of current adapter\n"
	       "    ae(verdict<,reason>) - call adapter_exit\n"
               "    a<num> - move down to adapter <num>\n"
               "    aup    - move up to parent adapter\n"
               "    m      - list model subcomponents\n"
               "    m<num> - move down to model subcomponent <num>\n"
               "    mup    - move up to parent model\n"
               "    mpush  - push current model state to a stack\n"
               "    mpop   - pop model state from a stack\n"
               "Properties of the current model:\n"
               "    ma     - list all actions\n"
               "    mc     - list tags at current state\n"
               "    mt     - list all state tags\n"
               "Options:\n"
               "    oea[0|1]- get/set executing action in adapter\n"
               "    oem[0|1]- get/set executing action in model\n"
               "Other:\n"
               "    C      - print coverage\n"
	       "    h[heuristic] - print action what heuristic would suggest. If heuristic not specified, use heuristic specified in configuration file\n"
               "Search:\n"
               "    ?a<num>- search shortest path to execute action <num>\n"
               "    ?c<num>- search path of length <num> for maximal coverage\n"
               "    q      - quit\n");
        fprintf(stderr,"Unknown command \"%s\"\n",s);
      }
    }
    std::free(s);
  }
}

int Test_engine::matching_end_condition(int step_count,int state, int action)
{
  for (unsigned int cond_i = 0; cond_i < end_conditions.size(); cond_i++) {

    End_condition* e = end_conditions[cond_i];

    if (e->match(step_count,state,action,last_step_cov_growth,heuristic,
		 mismatch_tags)) {
      if (e->verdict == Verdict::NOTIFY) {
	if (e->notify_step<step_count) {
	  e->notify_step=step_count;
	  std::string me_reason_msg=e->end_reason().c_str();
	  escape_string(me_reason_msg);
	  log.print("<notice reason=\"%s\"/>\n",
		    me_reason_msg.c_str());
	}
      } else {
	return cond_i;
      }
    }
  }
  return -1;
}
