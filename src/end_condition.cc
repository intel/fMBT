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

#include "end_condition.hh"
#include "adapter.hh"
#include "model.hh"
#include "coverage.hh"
#include <stdlib.h>

#include <stdio.h> // DEBUG

#include "helper.hh"

End_condition::End_condition(Conf* _conf,Counter _counter,
			     Verdict::Verdict v, const std::string& p)
  : verdict(v),counter(_counter), param(p), param_float(-1.0),
    param_long(-1), param_time(-1),notify_step(-1),conf(_conf)
{
}

std::string End_condition::stringify() {
  if (!status) return Writable::stringify();
  std::string ret;

  switch (verdict) {
  case Verdict::PASS:
    ret="pass";
    break;
  case Verdict::FAIL:
    ret="fail";
    break;
  case Verdict::INCONCLUSIVE:
    ret="inconc";
    break;
  case Verdict::W_ERROR:
    ret="error";
    break;
  default:
    break;
  }

  std::string name;
  switch(counter) {
  case STEPS:
    name="steps";
    break;
  case COVERAGE:
    name="coverage";
    break;
  case STATETAG:
    name="tag";
    break;
  case DURATION:
    name="duration";
    break;
  case NOPROGRESS:
    name="noprogress";
    break;
  case DEADLOCK:
    name="deadlock";
    break;
  case TAGVERIFY:
    name="failing_tag";
    break;
  case ACTION:
    name="ACTION";
  case STATUS:
    name="STATUS";
  default:
    return "";
  }

  if (param!="") {
    ret=ret+"\t= "+name+"("+param+")";
  } else {
    ret=ret+"\t= "+name;
  }
  return ret;
}

End_condition::~End_condition()
{

}

End_condition* new_end_condition(Verdict::Verdict v,const std::string& s,Conf* conf)
{
  End_condition* ret=NULL;
  std::string name,option;
  param_cut(s,name,option);

  ret = End_conditionFactory::create(v,name,option,conf);

  if (ret) {
    return ret;
  }

  //Let's try old thing.
  split(s, name, option);
  ret = End_conditionFactory::create(v,name,option,conf);

  if (ret) {
      fprintf(stderr,
	      "DEPRECATED END CONDITION SYNTAX. %s\nNew syntax is %s(%s)\n",
	      s.c_str(),name.c_str(),option.c_str());
  }


  return ret;
}

extern int date_node_size;

#include "dparse.h"

extern "C" {
  extern D_ParserTables parser_tables_date;
}

extern int d_verbose_level;

#include "date_node.h"

// We are leaking GTimeZone?

End_condition_duration::End_condition_duration
(Conf* _conf,Verdict::Verdict v, const std::string& p):
  End_condition(_conf,DURATION,v,p) {
  er="time limit reached";
  status=true;
  param_time = -1;

  D_Parser *parser = new_D_Parser(&parser_tables_date, date_node_size);
  parser->save_parse_tree=true;
  D_ParseNode *node=dparse(parser,(char*)p.c_str(),std::strlen(p.c_str()));
  GTimeVal tv;

  if (!node) {
    status=false;
    errormsg="Something wrong with date '"+p+"'";
    return;
  }

  date_node* unode = (date_node*) &node->user;

  if (parser->syntax_errors) {
    parser->free_node_fn(node);
    status=false;
    errormsg="Something wrong with date '"+p+"'";
    return;
  }

  if (unode->date) {
    if (g_date_time_to_timeval(unode->date,&tv)) {
      param_time = tv.tv_sec;
      param_long = tv.tv_usec;
      struct timeval ttv;
      gettime(&ttv);
      _conf->log.debug("Until %i,current %i",param_time,ttv.tv_sec);
    } else {
      status=false;
      errormsg="Something wrong with date '"+p+"'";
    }
    g_date_time_unref(unode->date);
  } else {
    status=false;
    errormsg="Something wrong with date '"+p+"'";
  }

  if (unode->zone) {
    g_time_zone_unref(unode->zone);
  }

  free_D_ParseNode(parser,node);
  free_D_Parser(parser);
}


End_condition_coverage::End_condition_coverage(Conf* _conf,Verdict::Verdict v, const std::string& p):
  End_condition(_conf,COVERAGE,v,p) {
  if (param.empty()) {
    er="coverage reached";
  } else {
    er="coverage "+param+" reached";
  }
  status = true;
  cconst=false;
  l.ref();
  c = new_coverage(l,param);
  if (c==NULL) {
    status=false;
    errormsg=param+" not valid coverage";
  } else {
    if (c->status) {
      if ((dynamic_cast<Coverage_Const*>(c))!=NULL) {
	cconst=true;
	param_float = strtod(param.c_str(),NULL);
      } else {
	cconst=false;
	_conf->set_model(c);
      }
    } else {
      status=false;
      errormsg=c->errormsg;
    }
  }
}

bool End_condition_tag::match(int step_count,int state, int action,int last_step_cov_growth,Heuristic& heuristic,std::vector<int>& mismatch_tags) {
  int *t;
  int s = heuristic.get_model()->getprops(&t);
  for(int i=0; i<s; i++) {
    if (t[i] == param_long) return true;
  }
  return false;
}

bool End_condition_duration::match(int step_count,int state, int action,int last_step_cov_growth,Heuristic& heuristic,std::vector<int>& mismatch_tags) {
  if (Adapter::current_time.tv_sec > param_time + 1 ||
      (Adapter::current_time.tv_sec == param_time
       && Adapter::current_time.tv_usec >= param_long)
      ) return true;

  return false;
}

bool End_status_error::match(int step_count,int state, int action,
			     int last_step_cov_growth,Heuristic& heuristic,std::vector<int>& mismatch_tags)
{
  if (!heuristic.status) {
    er="Heuristic error: "+heuristic.errormsg;
    return true;
  }
  if (!heuristic.get_model()->status) {
    er="Model error: "+heuristic.get_model()->errormsg;
    return true;
  }
  if (!heuristic.get_coverage()->status) {
    er="Coverage error: "+heuristic.get_coverage()->errormsg;
    return true;
  }
  return false;
}

bool End_condition_tagverify::match(int step_count,int state, int action,
				    int last_step_cov_growth,Heuristic&
				    heuristic,std::vector<int>& mismatch_tags)
{
  bool rv=false;
  er="verifying tags ";
  for(unsigned i=0;i<mismatch_tags.size();i++) {
    if (std::find(filter.begin(),filter.end(),mismatch_tags[i])==filter.end()) {
      er=er+"\""+heuristic.get_model()->getSPNames()[mismatch_tags[i]]+"\" ";
      rv=true;
    }
  }
  er=er+"failed.";
  return rv;
}

bool End_condition_tagverify::evaluate_filter(std::vector<std::string>& tag)
{
  return evaluate_filter(tag,param);
}

std::string End_condition_dummy::stringify() {
  if (!status) {
    if (!c) {
      return "Can't create coverage " + param;
    }
    if (!c->status) {
      return "Coverage error " + c->errormsg;
    }
    return "????";
  }
  return errormsg;
}

bool End_condition_tagverify::evaluate_filter(std::vector<std::string>& tags,std::string& s)
{
  if (s=="") {
    return true;
  }
  std::string name,option;
  std::vector<std::string> f;
  param_cut(s,name,option);
  commalist(option,f);

  if (name=="include") {
    std::vector<int> tmp;
    strlist(f);
    find(tags,f,tmp);
    for(unsigned i=0;i<tags.size();i++) {
      if (std::find(tmp.begin(),tmp.end(),i)==tmp.end()) {
	filter.push_back(i);
      }
    }
    return true;
  }

  if (name=="exclude") {
    strlist(f);
    find(tags,f,filter);
    return true;
  }
  return false;
}

#undef FACTORY_CREATE_PARAMS
#undef FACTORY_CREATOR_PARAMS
#undef FACTORY_CREATOR_PARAMS2
#undef FACTORY_CREATE_DEFAULT_PARAMS

#define FACTORY_CREATE_DEFAULT_PARAMS /* */

#define FACTORY_CREATE_PARAMS Verdict::Verdict v,	               \
                       std::string name,                               \
                       std::string params,                             \
                       Conf* co

#define FACTORY_CREATOR_PARAMS Verdict::Verdict v, std::string params,Conf* co
#define FACTORY_CREATOR_PARAMS2 v, params,co

FACTORY_IMPLEMENTATION(End_condition)
#undef FACTORY_CREATOR_PARAMS2
#define FACTORY_CREATOR_PARAMS2 co, v, params

FACTORY_DEFAULT_CREATOR(End_condition, End_condition_steps,     "steps")
FACTORY_DEFAULT_CREATOR(End_condition, End_condition_coverage,  "coverage")
FACTORY_DEFAULT_CREATOR(End_condition, End_condition_tag,       "tag")
FACTORY_DEFAULT_CREATOR(End_condition, End_condition_tag,       "statetag")
FACTORY_DEFAULT_CREATOR(End_condition, End_condition_duration,  "duration")
FACTORY_DEFAULT_CREATOR(End_condition, End_condition_noprogress,"noprogress")
FACTORY_DEFAULT_CREATOR(End_condition, End_condition_noprogress,"no_progress")
FACTORY_DEFAULT_CREATOR(End_condition, End_condition_deadlock,  "deadlock")
FACTORY_DEFAULT_CREATOR(End_condition, End_condition_tagverify, "failing_tag")
