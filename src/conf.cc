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
#include "coverage_of.hh"
#include <cstring>
#include "heuristic_proxy.hh"
#include "coverage_proxy.hh"

#ifndef DROI
#include <glib.h>
#else

#endif

class EndHook;
#include "endhook.hh"
extern "C" {
  extern D_ParserTables parser_tables_conf;
}

extern Conf* conf_obj;
#define RETURN_ERROR_VOID(i,s) {		\
    log.pop();                                  \
    status=false;                               \
    if (i>0) {                                  \
      errormsg=name+":"+to_string(i)+" " + s;	\
    } else {					\
      errormsg=s;				\
    }						\
    return;                                     \
  }

#define RETURN_ERROR_VERDICT(s) {               \
    log.pop();                                  \
    status=false;                               \
    errormsg=s;                                 \
    exit_status=-1;                             \
    return Verdict::W_ERROR;                      \
  }


Conf::Conf(Log& l, bool debug_enabled)
  :log(l), exit_status(0), exit_interactive(false),
   heuristic_name("random"), coverage_name("perm"),
   adapter_name("dummy"), model_lineno(-1), heuristic_lineno(-1),
   coverage_lineno(-1),adapter_lineno(-1),
   end_time(-1),
   on_error("exit(1)"), on_fail("interactive"),
   on_pass("exit(0)"), on_inconc("exit(1)"),
   heuristic(NULL), model(NULL),
   adapter(NULL),coverage(NULL),
   disable_tagverify(false)
{
  // Reserve first slot for THE coverage
  set_model_callbacks.push_back(NULL);
  log.ref();
  log.push("fmbt_log");
  log.set_debug(debug_enabled);

  End_condition *ec = new End_status_error(this,Verdict::W_ERROR,"");
  add_end_condition(ec);

  set_on_error("exit(4)");
  set_on_fail("interactive");
  set_on_pass("exit(0)");
  set_on_inconc("exit(1)");
}

void Conf::load(std::string& name,std::string& content)
{
  D_Parser *p = new_D_Parser(&parser_tables_conf, 512);
  p->loc.pathname = name.c_str();
  char *s;

  Conf* tmp=conf_obj;
  log.push("conf_load");
  {
      std::string escaped_fname = name;
      escape_string(escaped_fname);
      log.print("<conf_file name=\"%s\"/>\n", escaped_fname.c_str());
  }
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

  gchar* t1=g_path_get_dirname(name.c_str());
  std::string dirname(t1);
  g_free(t1);

  if (dirname!=".") {
    g_setenv("AAL_INCLUDE_PREFIX",dirname.c_str(),TRUE);
  }

  std::string ss(s);
  free(s);
  ss=ss+"\n"+content;
  if ((name!="" && s==NULL))
    RETURN_ERROR_VOID(-1,"Loading \"" + name + "\" failed.");

  if (ss=="")
    RETURN_ERROR_VOID(-1,"Empty configuration");

  bool ret=dparse(p,(char*)ss.c_str(),std::strlen(ss.c_str()));

  ret=p->syntax_errors==0 && ret;

  free_D_Parser(p);

  if (!ret) {
    RETURN_ERROR_VOID(-1,"Parsing \"" + name + "\" failed.");
  }

  conf_obj=tmp;

  if ((heuristic=new_heuristic(log,heuristic_name)) == NULL)
    RETURN_ERROR_VOID(heuristic_lineno,"Creating heuristic \"" +
		      heuristic_name + "\" failed.");

  heuristic->lineno = heuristic_lineno;

  if (heuristic->status==false)
    RETURN_ERROR_VOID(heuristic_lineno,"Error in heuristic \"" +
		      heuristic_name + "\":" +
                      heuristic->errormsg);

  heuristic=new Heuristic_proxy(log,heuristic,heuristic_name);
  heuristic->lineno = heuristic_lineno;

  if ((model=new_model(log, model_name)) == NULL) {
    RETURN_ERROR_VOID(model_lineno,"Creating model \"" +
                      filetype(model_name)
                      + "\" failed.");
  }

  coverage = new_coverage(log,coverage_name);

  if (coverage == NULL)
    RETURN_ERROR_VOID(coverage_lineno,
		      "Creating coverage \"" +
		      coverage_name + "\" failed.");

  coverage->lineno=coverage_lineno;

  if (!coverage->status)
    RETURN_ERROR_VOID(coverage->lineno,
		      "Error in coverage \"" +
		      coverage_name + "\": " + coverage->errormsg);

  coverage = new Coverage_proxy(log,coverage,coverage_name);
  coverage->lineno=coverage_lineno;

  if (!model->status || !model->init() || !model->reset())
    RETURN_ERROR_VOID(model->lineno,"Error in model: " + model->stringify());

  heuristic->set_coverage(coverage);

  heuristic->set_model(model);

  set_model_callbacks[0]=coverage;

  // Handle post set_model calls.

  for(std::vector<Coverage*>::iterator i=set_model_callbacks.begin();i!=set_model_callbacks.end();++i) {
    (*i)->set_model(model);
    if (!((*i)->status)) {
      RETURN_ERROR_VOID((*i)->lineno,"Coverage error: " + (*i)->stringify());
    }
  }

  adapter = new_adapter(log, adapter_name);

  if (adapter == NULL)
    RETURN_ERROR_VOID(adapter_lineno,
		      "Creating adapter \"" + adapter_name + "\" failed.");

  adapter->lineno = adapter_lineno;

  if (!adapter->status) {
    status=false;
    errormsg=adapter->errormsg;
    return;
  }

  adapter->set_tags(&model->getSPNames());

  if (!adapter->status) {
    status=false;
    errormsg=adapter->errormsg;
    return;
  }

  // Parse adapter-tags filter (if any)
  for(unsigned i=0;i<disable_tags.size();i++) {
    std::vector<std::string>& tags=model->getSPNames();
    std::vector<std::string> f;
    commalist(disable_tags[i],f);
    std::vector<int> tmp;
    find(tags,f,tmp);
    for(unsigned i=0;i<tags.size();i++) {
      if (std::find(tmp.begin(),tmp.end(),i)==tmp.end()) {
	disabled_tags[i]=true;
      }
    }

  }

  // Free some memory.
  disable_tags.clear();

  /* handle history */
  for(unsigned i=0;i<history.size();i++) {
    History* h=new_history(log,* (history[i].first));
    Coverage_of cof(log,set_model_callbacks);

    if (h) {
      h->lineno=history[i].second;
      h->set_coverage(&cof,model);
      if (!h->status) {
	errormsg=h->errormsg;
	delete h;
	RETURN_ERROR_VOID(h->lineno,errormsg);
      }
      delete h;
    } else {
      RETURN_ERROR_VOID(history[i].second,"Creating history \""+ *(history[i].first) + "\" failed.");
    }
  }

  adapter->set_actions(&model->getActionNames());

  if (!adapter->status)
    RETURN_ERROR_VOID(adapter->lineno,"Adapter error: " + adapter->stringify());

  log.pop();
}

void Conf::disable_tagchecking(std::string& s) {
  disable_tags.push_back(s);
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

  // end conditions
  for(size_t i=0;i<end_conditions.size();i++) {
    t << end_conditions[i]->stringify() << std::endl;
  }

  // exit-hooks
  stringify_hooks(t,pass_hooks ,"on_pass"  );
  stringify_hooks(t,fail_hooks ,"on_fail"  );
  stringify_hooks(t,inc_hooks  ,"on_inconc");
  stringify_hooks(t,error_hooks,"on_error" );

  return t.str();
}

Verdict::Verdict Conf::execute(bool interactive) {

  Policy policy;
  log.push("conf_execute");

  if (!status) {
    errormsg = "cannot start executing test due to earlier errors: " + errormsg;
    return Verdict::W_ERROR;
  }

  if (!adapter->init())
    RETURN_ERROR_VERDICT("Initialising adapter failed: " + adapter->stringify());

  // Validate and finish existing end_conditions
  {
    bool end_by_tagverify = false;
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
      if (e->counter == End_condition::TAGVERIFY) {
        end_by_tagverify = true;
	((End_condition_tagverify*) e)
	  ->evaluate_filter(model->getSPNames());
      }
      if ((e->verdict==Verdict::PASS) &&
	  (e->counter == End_condition::COVERAGE)) {
        end_by_coverage = true;
      }
      if (e->counter == End_condition::DURATION) {
	end_time = e->param_time;
      }
    }
    // Add default end conditions (if coverage is reached, test is passed)
    if (!end_by_coverage) {
      end_conditions.push_back(new End_condition_coverage(this,Verdict::PASS, "1.0"));
    }
    if (!end_by_tagverify && !disable_tagverify) {
      end_conditions.push_back(new End_condition_tagverify(this,Verdict::FAIL, ""));
    }
  }

  Test_engine engine(*heuristic,*adapter,log,policy,end_conditions,disabled_tags);

  if (interactive) {
    engine.interactive();
  } else {
    Verdict::Verdict v = engine.run(end_time,disable_tagverify);

    if (!heuristic->status) {
      fprintf(stderr,"heuristic error: %s\n",heuristic->errormsg.c_str());
    }

    if (!model->status) {
      fprintf(stderr,"model error: %s\n",model->errormsg.c_str());
    }

    if (!adapter->status) {
      fprintf(stderr,"adapter error: %s\n",adapter->errormsg.c_str());
    }

    if (!coverage->status) {
      fprintf(stderr,"coverage error: %s\n",coverage->errormsg.c_str());
    }
    handle_hooks(v);
  }
  log.pop();
  status = true;
  errormsg = engine.verdict_msg() + ": " + engine.reason_msg();

  if (adapter->status) {
    adapter->adapter_exit(engine.verdict(),engine.reason_msg());
  }

  return engine.verdict();
}

void Conf::handle_hooks(Verdict::Verdict v)
{
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
  case Verdict::W_ERROR: {
    hooklist=&error_hooks;
    break;
  }
  case Verdict::NOTIFY: {
    abort();
    break;
  }
  default: {
    // unknown verdict?
  }
  }
  if (hooklist) {
    std::list<EndHook*>::iterator b,e;
    b=hooklist->begin();
    e=hooklist->end();
    if (v==Verdict::FAIL && b++ != e) {
      for_each(b++,e,hook_runner);
    } else {
      for_each(b,e,hook_runner);
    }
  }
}

void Conf::set_observe_sleep(std::string &s)
{
  Adapter::sleeptime=atoi(s.c_str());
}

void Conf::add_end_condition(Verdict::Verdict v,std::string& s,int line)
{
  End_condition *ec = new_end_condition(v,s,this);

  if (ec==NULL) {
    status=false;
    errormsg=errormsg+"Creating end condition \""+s+"\" failed.\n";
  } else {
    ec->lineno=line;
    add_end_condition(ec);
  }
}

void Conf::set_on_error(const std::string &s,int line) {
  EndHook* e=new_endhook(this,s,line);
  error_hooks.push_back(e);
}

void Conf::set_on_fail(const std::string &s,int line) {
  EndHook* e=new_endhook(this,s,line);
  fail_hooks.push_back(e);
}

void Conf::set_on_pass(const std::string &s,int line) {
  EndHook* e=new_endhook(this,s,line);
  pass_hooks.push_back(e);
}

void Conf::set_on_inconc(const std::string &s,int line) {
  EndHook* e=new_endhook(this,s,line);
  inc_hooks.push_back(e);
}


void Conf::set_model(Coverage* _c)
{
  set_model_callbacks.push_back(_c);
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
    if (history[i].first) {
      delete history[i].first;
    }
  }

  for_each(pass_hooks.begin(),pass_hooks.end(),hook_delete);
  for_each(fail_hooks.begin(),fail_hooks.end(),hook_delete);
  for_each(inc_hooks.begin(),inc_hooks.end(),hook_delete);
  for_each(error_hooks.begin(),error_hooks.end(),hook_delete);
  log.unref();
}
