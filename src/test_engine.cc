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

#include "test_engine.hh"
#include "log.hh"
#include <cstdio>
#include <algorithm>

#ifdef USE_GNU_READLINE
#include <readline/readline.h>
#include <readline/history.h>
#define READLINE(a) readline(a)
#else
#ifdef USE_EDITLINE
/* Let's use editline... */
extern "C" {
#include <editline.h>
};
#define READLINE(a)         \
  (__extension__            \
    ({ char* __result;      \
       printf("%s",a);      \
       __result=readline(); \
       __result;}))
#else
/* Defaults to BSD editline readline.. */
#include <editline/readline.h>
#define READLINE(a) readline(a)
#endif
#endif
#include <cstdlib>
#include <cstring>

Test_engine::Test_engine(Heuristic& h,Adapter& a,Log& l,Policy& p) : heuristic(h),adapter(a),log(l),policy(p) {}

namespace {
  void test_passed(bool pass, const char* reason, Log& log) {
    if (pass) log.print("<stop verdict=\"pass\" reason=\"%s\">\n", reason);
    else log.print("<stop verdict=\"fail\" reason=\"%s\">\n", reason);
  }
  void log_tag_type_name(Log& log, const char *tag, const char *type, const char *name) {
    log.print("<%s type=\"%s\" name=\"%s\">\n", tag, type, name);
  }
  void log_adapter_suggest(Log& log, Adapter& adapter, int action) {
#ifndef DROI
    log_tag_type_name(log, "suggested_action", "input", adapter.getUActionName(action));
#endif
  }
  void log_adapter_execute(Log& log, Adapter& adapter, int action) {
#ifndef DROI
    log_tag_type_name(log, "action", "input", adapter.getUActionName(action));
#endif
  }
  void log_adapter_output(Log& log, Adapter& adapter, int action) {
#ifndef DROI
    log_tag_type_name(log, "action", "output", adapter.getUActionName(action));
#endif
  }
  void log_status(Log& log, int step_count, float coverage) {
    log.print("<status steps=\"%d\" coverage=\"%f\"/>\n",
              step_count, coverage);
  }
}

bool Test_engine::run(float target_coverage,
		      int max_step_count)
{
  int action=0;
  std::vector<int> actions;
  int step_count=0;
  bool coverage_reached = false;
  bool step_limit_reached = false;
  log.push("test_engine");
  do {
    action=0;

    gettimeofday(&Adapter::current_time,NULL);
    while (adapter.observe(actions)) {
      step_count++;
      action = policy.choose(actions);
      log_adapter_output(log, adapter, action);

      if (!heuristic.execute(action)) {
        log.debug("Test_engine::run: Error: unexpected output from the SUT: %i '%s'\n",
		  action, heuristic.getActionName(action).c_str());

        test_passed(false, "unexpected output", log);

        log.pop(); // test_engine
	return false; // Error: Unexpected output
      }
      gettimeofday(&Adapter::current_time,NULL);
    }
    
    action = heuristic.getIAction();
    if (action >= 0)
      log.debug("Test_engine::run: test generator suggests executing %i '%s'\n",
		action, heuristic.getActionName(action).c_str());
    
    step_count++;

    log.debug("Step %i",step_count);

    switch(action) {
    case DEADLOCK: {
      log.print("<state type=\"deadlock\"/>\n");
      if (adapter.observe(actions,true)) {
        test_passed(false, "response on deadlock", log);
        log.pop(); // test_engine
	return false; // Error: Unexpected output
      }
      test_passed(true, "model cannot continue", log);
      log.pop(); // test_engine
      return true;
      break;
    }
    case OUTPUT_ONLY: {
      log.print("<state type=\"output only\"/>\n");

      bool value = adapter.observe(actions,true);
      if (!value) {
	actions.resize(1);
	actions[0] = SILENCE;
        log.debug("Test_engine::run: SUT remained silent (action %i).\n", action);
      } else {
        log.debug("Test_engine::run: SUT executed %i '%s'\n",
		  actions[0],heuristic.getActionName(actions[0]).c_str());
      }
      action = actions[0];
      if (!heuristic.execute(action)) {
        log.debug("Test_engine::run: ERROR: action %i not possible in the model.\n", action);
	log.write(action,heuristic.getActionName(action).c_str(),"broken response");
        test_passed(false, "unexpected output", log);
        log.pop();
	return false; // Error: Unexpected output
      }
      break;
    }
    default: { /* INPUT: suggest execution of an input action */
      log.debug("Test_engine::run: sending input action %i to the SUT.\n", action);
      actions.resize(1);
      actions[0]=action;
      log_adapter_suggest(log, adapter, actions[0]);
      adapter.execute(actions);
      if (actions.size()==0) {
        test_passed(false, "adapter communication failure", log);
        log.pop();
        return false;
      }
      int adapter_response = policy.choose(actions);
      log_adapter_execute(log, adapter, adapter_response);
      log.debug("Test_engine::run: passing adapter response action %i to test generation.\n",
		adapter_response);
      log.push("adapter_executed");
      log.pop(); // adapter_executed

      if (!heuristic.execute(adapter_response)) {
	log.debug("Test_engine::run: ERROR: SUT executed %i '%s', not allowed in the model.\n",
		  action, heuristic.getActionName(action).c_str());
	log.write(action,heuristic.getActionName(action).c_str(),"broken input acceptance");
        test_passed(false, "unexpected input", log);
        log.pop(); // test_engine
	return false; // Error: Unexpected input
      }
    }
    } // switch
    log_status(log, step_count, heuristic.getCoverage());

    coverage_reached = heuristic.getCoverage() >= target_coverage;
    step_limit_reached = (max_step_count != -1 && step_count >= max_step_count);
  } while ( !coverage_reached && !step_limit_reached );

  if (coverage_reached) test_passed(true, "coverage reached", log);
  else if (step_limit_reached) test_passed(true, "step limit reached", log);
  else abort();

  log.pop(); // test_engine
  return true;
}

void Test_engine::interactive()
{
  int action=0;
  std::vector<int> actions_v;
  bool run=true;

  Adapter* current_adapter=&adapter;
  Model* current_model=heuristic.get_model();

  while (run) {

    while (adapter.observe(actions_v)) {
      printf("Action %i:%s\n",action,heuristic.getActionName(action).c_str());
      actions_v.resize(0);
    }
    
    char* s=READLINE("fMBT> ");

    if (s==NULL) {
      run=false;
    } else {
      unsigned int num = 0;

      switch (*s) {
      case 's': { // commands "s", "s<num>", "sm<num>": execute action at current state
        int* actions = 0;
        unsigned int action_count=current_model->getActions(&actions);
        bool tell_adapter = true;
        if (*(s+1)=='m') {
          num=std::atoi(s+2);
          tell_adapter = false;
        }
        else num=std::atoi(s+1);
        if (num>0 && num<=action_count) {
          // sm<num> command: execute the nth action at the current
          // state of the model. Always use the top-level adapter.
          int adapter_response = 0;
          printf("executing: %s\n", heuristic.getActionName(actions[num-1]).c_str());
          if (tell_adapter && current_adapter==&adapter) {
	    actions_v.resize(1);
	    actions_v[0]=actions[num-1];
            log_adapter_suggest(log, adapter, actions_v[0]);
	    adapter.execute(actions_v);
	    adapter_response = policy.choose(actions_v);
            log_adapter_execute(log, adapter, adapter_response);
            printf("adapter:   %s\n", heuristic.getActionName(adapter_response).c_str());
          } else {
            printf("adapter:   [skipped]\n");
            adapter_response = actions[num-1];
          }
	  bool model_response;
	  if (current_model->up()) {
	    model_response = current_model->execute(adapter_response);
	  } else {
	    model_response = heuristic.execute(adapter_response);
	  }
          printf("model:     ");
          if (model_response) {
            printf("ok\n");
            // state might have changed, update available actions
            action_count=current_model->getActions(&actions);
          }
          else printf("failed\n");
        }
        log_status(log, -1, 0.0);
        // print actions available at current state
        for(unsigned int i=0;i<action_count;i++) {
          // printf("s%i:%s\n",i+1,names[actions[i]].c_str());
          printf("s%i:%s\n",i+1,current_model->getActionName(actions[i]).c_str());
        }
      }
        break;
        
      case 'e': { // commands "e", "e<num>", "em<num>": execute any action at current adapter
        bool tell_adapter = true;
        if (*(s+1)=='m') {
          num=std::atoi(s+2);
          tell_adapter = false;
        }
        else num=std::atoi(s+1);
        std::vector<std::string>& ca_anames=current_adapter->getAllActions();
        std::vector<std::string> sca_anames=ca_anames; /* copy for sorted actions */
        sort(sca_anames.begin(), sca_anames.end());
        if (num>0 && num<sca_anames.size()) {
          unsigned action_num=0;
          for (action_num=1; action_num<sca_anames.size(); action_num++)
            if (ca_anames[action_num]==sca_anames[num]) break;
          printf("executing: %s\n", ca_anames[action_num].c_str());
          if (tell_adapter) {
	    actions_v.resize(1);
	    actions_v[0]=action_num;
            log_adapter_suggest(log, *current_adapter, actions_v[0]);
	    current_adapter->execute(actions_v);
            if (actions_v.size()==0) {
              printf("adapter:   [communication failure]\n");
            } else {
              int adapter_response = policy.choose(actions_v);
              log_adapter_execute(log, *current_adapter, adapter_response);
              printf("adapter:   %s\n", ca_anames[adapter_response].c_str());
              printf("model:     [skipped]\n");
            }
          } else {
            printf("adapter:   [skipped]\n");
            if (current_adapter->up()==NULL) {
              if (heuristic.execute(action_num)) printf("model:     ok\n");
              else printf("model:     failed\n");
            } else printf("model:     not updated (not topmost adapter)\n");
          }
          log_status(log, -1, 0.0);
        }
        if (strnlen(s,2)==1) {
          for(unsigned i=1;i<sca_anames.size();i++){
            printf("e%i:%s\n",i,sca_anames[i].c_str());
          }
        }
      }
        break;

      case 'i': { // starts an input action name?
        std::vector<std::string>& ca_anames=current_adapter->getAllActions();
        unsigned int action_num;
        for (action_num=1;action_num<ca_anames.size();action_num++) {
          if (ca_anames[action_num]==std::string(s)) {
            // action found in adapter, execute it!
            printf("executing: %s\n", ca_anames[action_num].c_str());
	    actions_v.resize(1);
	    actions_v[0]=action_num;
            log_adapter_suggest(log, *current_adapter, actions_v[0]);
	    current_adapter->execute(actions_v);
            int adapter_response = policy.choose(actions_v);
            log_adapter_execute(log, *current_adapter, adapter_response);
            printf("adapter:   %s\n", ca_anames[adapter_response].c_str());
            printf("model:     [skipped]\n");
            log_status(log, -1, 0.0);
            break;
          }
        }
        if (action_num==ca_anames.size()) {
          printf("action \"%s\" not found in the adapter\n", s);
        }
      }
        break;
        
      case 'a': // commands "a", "a<num>" and "aup"
        num = std::atoi(s+1);
        if (strncmp(s,"aup",3)==0) {
          // do up in the adapter tree
          if (!current_adapter->up()) {
            printf("Can't go up in adapter tree\n");
          } else {
            current_adapter=current_adapter->up();
          }
        } else if (strnlen(s,2)==1) {
          std::vector<std::string>& adapter_names=current_adapter->getAdapterNames();
          for(unsigned int i=0;i<adapter_names.size();i++) {
            if (adapter_names[i]!=std::string("")) {
              printf("a%i:%s\n",i,adapter_names[i].c_str());
            }
          }
        } else {
          num=std::atoi(s+1);
          if (!current_adapter->down(num)) {
            printf("Can't change to adapter %i\n",num);
          } else {
            current_adapter=current_adapter->down(num);
          }
        }
        break;

      case 'q': // command "q": quit
        std::free(s);
        return;

      case 'm':
        num = std::atoi(s+1);
        if (strncmp(s,"mup",3)==0) {
	  /* up */
          if (!current_model->up()) {
            printf("Can't go up in model tree\n");
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
		printf("m%i:%s\n",i,model_names[i].c_str());
	      }
	    }
	    break;
	  } else 
	    if (num>0) {
	      /* switch to <num> */
	      /* down */
	      if (!current_model->down(num)) {
		printf("Can't go down in model tree\n");
	      } else {
		current_model=current_model->down(num);
	      }
	      break;
	    }
      case 't': // TODO
          printf("t <+diff>\n");
          printf("not implemented: advance Adapter::current_time");
          break;
      default:
        printf("Execute actions:\n"
               "    s       - list executable actions at current state\n"
               "    s<num>  - exec action <num> of current state in adapter and model\n"
               "    sm<num> - exec action <num> of current state in model (skip adapter)\n"
               "    e       - list executable actions at current adapter\n"
               "    e<num>  - exec action <num> of current adapter in adapter (skip model)\n"
               "    em<num> - exec action <num> of current adapter in model (skip adapter)\n"
               "    <iname> - exec input action iname (starts with \"i\", skip model)\n"
               "Change adapters/models:\n"
               "    a      - list low-level adapters of current adapter\n"
               "    a<num> - move down to adapter <num>\n"
               "    aup    - move up to parent adapter\n"
               "    m      - list model subcomponents\n"
               "    m<num> - move down to model subcomponent <num>\n"
               "    mup    - move up to parent model\n"
               "    q      - quit\n");
        printf("Unknown command \"%s\"\n",s);
      }
    }
    std::free(s);
  }
}
