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
#include "conf.hh"
#include "dparse.h"
#include "helper.hh"
#include "history.hh"
#include <cstring>

#ifndef DROI
#include <glib.h>
#else

#endif

class EndHook;

extern "C" {
  extern D_ParserTables parser_tables_conf;
}

extern Conf* conf_obj;

#define RETURN_ERROR_VOID(s) {			\
    log.pop();					\
    status=false;				\
    errormsg=s;					\
    return;					\
  }

#define RETURN_ERROR_VERDICT(s) {		\
    log.pop();					\
    status=false;				\
    errormsg=s;					\
    exit_status=-1;                             \
    return Verdict::ERROR;			\
  }

void Conf::load(std::string& name,std::string& content)
{
  D_Parser *p = new_D_Parser(&parser_tables_conf, 512);
  p->loc.pathname = name.c_str();
  char *s;
  
  Conf* tmp=conf_obj;
  log.push("conf_load");
  log.debug("Conf::load %s",name.c_str());
  conf_obj=this;

  s=readfile(name.c_str());

  if (s==NULL) {
    status=false;
    errormsg=std::string("Can't read configuration file \"")+name+"\"";
    log.pop();
    free_D_Parser(p);
    return;
  }

  std::string ss(s);
  ss=ss+"\n"+content;
  if ((name!="" && s==NULL))
    RETURN_ERROR_VOID("Loading \"" + name + "\" failed.");

  if (ss=="")
    RETURN_ERROR_VOID("Empthy configuration");

  bool ret=dparse(p,(char*)ss.c_str(),std::strlen(ss.c_str()));

  ret=p->syntax_errors==0 && ret;

  if (!ret)
    RETURN_ERROR_VOID("Parsing \"" + name + "\" failed.");

  free(s);

  free_D_Parser(p);

  conf_obj=tmp;

  if ((heuristic=new_heuristic(log,heuristic_name)) == NULL)
    RETURN_ERROR_VOID("Creating heuristic \"" + heuristic_name + "\" failed.");

  if (heuristic->status==false)
    RETURN_ERROR_VOID("Error in heuristic \"" + heuristic_name + "\":" +
		      heuristic->errormsg);

  if ((model=new_model(log, model_name)) == NULL) {
    RETURN_ERROR_VOID("Creating model loader \"" +
		      filetype(model_name)
		      + "\" failed.");
  }

  coverage = new_coverage(log,coverage_name);

  if (coverage == NULL)
    RETURN_ERROR_VOID("Creating coverage \"" + coverage_name + "\" failed.");

  if (!coverage->status) 
    RETURN_ERROR_VOID("Coverage error on \"" + coverage_name + "\":" + coverage->errormsg);

  if (!model->status || !model->init() || !model->reset())
    RETURN_ERROR_VOID("Model error: " + model->stringify());

  heuristic->set_coverage(coverage);

  heuristic->set_model(model);

  coverage->set_model(model);

  adapter = new_adapter(log, adapter_name);

  if (adapter && !adapter->status) {
    status=false;
    errormsg=adapter->errormsg;
    return;
  }

  /* handle history */
  for(unsigned i=0;i<history.size();i++) {
    History* h=new_history(log,*history[i]);
    
    if (h) {
      h->set_coverage(coverage,model);
      if (!h->status) {
	RETURN_ERROR_VOID(h->errormsg);
      }
    } else {
      RETURN_ERROR_VOID("Creating history \""+ *history[i] + "\" failed");
    }
  }

  if (adapter == NULL)
    RETURN_ERROR_VOID("Creating adapter \"" + adapter_name + "\" failed.");

  adapter->set_actions(&model->getActionNames());

  if (!coverage->status)
    RETURN_ERROR_VOID("Coverage error: " + coverage->stringify());

  if (!adapter->status)
    RETURN_ERROR_VOID("Adapter error: " + adapter->stringify());

  log.pop();
}

#include <sstream>

std::string Conf::stringify() {
  std::ostringstream t(std::ios::out | std::ios::binary);

  if (!status) {
    return errormsg;
  }

  t << "model = \"" << removehash(model_name) << capsulate(model->stringify()) << std::endl;
  t << "heuristic = \"" << heuristic_name << "\"" << std::endl;
  t << "coverage = \"" <<  coverage_name << "\"" << std::endl;
  t << "adapter = \"" << adapter_name
    << capsulate(adapter->stringify()) << std::endl;

  /* TODO: stringify end conditions */

  return t.str();
}

Verdict::Verdict Conf::execute(bool interactive) {

  Policy policy;
  log.push("conf_execute");

  if (!status) {
    errormsg = "cannot start executing test due to earlier errors: " + errormsg;
    return Verdict::ERROR;
  }

  if (!adapter->init())
    RETURN_ERROR_VERDICT("Initialising adapter failed: " + adapter->stringify());

  // Validate and finish existing end_conditions
  {
    bool end_by_coverage = false;
    for (unsigned int i = 0; i < end_conditions.size(); i++) {
      End_condition* e = end_conditions[i];
      if (e->status == false)
        RETURN_ERROR_VERDICT("Error in end condition: " + e->stringify());
      if (e->counter == End_condition::ACTION) {
        // avoid string comparisons, fetch the index of the tag
        e->param_long = find(model->getActionNames(), (e->param),-1);
	if (e->param_long==-1) {
	  RETURN_ERROR_VERDICT("Error in end condition: " + e->stringify());
	}
      }
      if (e->counter == End_condition::STATETAG) {
        // avoid string comparisons, fetch the index of the tag
        e->param_long = find(model->getSPNames(), (e->param),-1);
	if (e->param_long==-1) {
	  RETURN_ERROR_VERDICT("Error in end condition: " + e->stringify());
	}
      }
      if (e->counter == End_condition::COVERAGE) {
        end_by_coverage = true;
      }
      if (e->counter == End_condition::DURATION) {
        end_time = e->param_time;
      }
    }
    // Add default end conditions (if coverage is reached, test is passed)
    if (!end_by_coverage) {
      end_conditions.push_back(new End_condition_coverage(Verdict::PASS, "1.0"));
    }
  }

  Test_engine engine(*heuristic,*adapter,log,policy,end_conditions);

  if (interactive) {
    engine.interactive();
  } else {
    Verdict::Verdict v = engine.run(end_time);
    std::list<EndHook*>* hooklist=NULL;
    switch (v) {
    case Verdict::FAIL: {
      hooklist=&fail_hooks;
      break;
    }
    case Verdict::PASS: { 
      hooklist=&pass_hooks;
      break;
    }
    case Verdict::INCONCLUSIVE: {
      hooklist=&inc_hooks;
      break;
    }
    case Verdict::ERROR: {
      hooklist=&error_hooks;
      break;
    }
    default: {
      // unknown verdict?
    }
    }
    if (hooklist) 
      for_each(hooklist->begin(),hooklist->end(),hook_runner);
  }
  log.pop();
  status = true;
  errormsg = engine.verdict_msg() + ": " + engine.reason_msg();
  return engine.verdict();
}
/*
  void Conf::set_exitvalue(std::string& s)
  {
  std::string cmd;
  std::string value;
  split(s,cmd,value);
  exit_status=atoi(value.c_str());
  }
*/

void Conf::set_observe_sleep(std::string &s)
{
  Adapter::sleeptime=atoi(s.c_str());
}

void Conf::add_end_condition(Verdict::Verdict v,std::string& s)

{
  End_condition *ec = new_end_condition(v,s);

  if (ec==NULL) {
    status=false;
    errormsg=errormsg+"Can't create end condition \""+s+"\"\n";
  } else {
    add_end_condition(ec);
  }
}

void hook_delete(EndHook* e);

Conf::~Conf() {
  for (unsigned int i = 0; i < end_conditions.size(); i++)
    delete end_conditions[i];
  log.pop();
  if (heuristic) 
    delete heuristic;

  if (adapter)
    delete adapter;

  if (model)
    delete model;

  if (coverage)
    delete coverage;

  adapter=NULL;
  heuristic=NULL;
  model=NULL;
  coverage=NULL;

  for(unsigned i=0;i<history.size();i++) {
    if (history[i]) {
      delete history[i];
    }
  }

  for_each(pass_hooks.begin(),pass_hooks.end(),hook_delete);
  for_each(fail_hooks.begin(),fail_hooks.end(),hook_delete);
  for_each(inc_hooks.begin(),inc_hooks.end(),hook_delete);
  for_each(error_hooks.begin(),error_hooks.end(),hook_delete);

}

