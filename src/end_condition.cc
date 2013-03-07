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

End_condition::End_condition(Verdict::Verdict v, const std::string& p)
  : verdict(v), param(p),
    param_float(-1.0), param_long(-1), param_time(-1),notify_step(-1)
{
}

End_condition::~End_condition()
{

}

End_condition* new_end_condition(Verdict::Verdict v,const std::string& s)
{
  End_condition* ret=NULL;
  std::string name,option;
  param_cut(s,name,option);

  ret = End_conditionFactory::create(v,name,option);

  if (ret) {
    return ret;
  }

  //Let's try old thing.
  split(s, name, option);
  ret = End_conditionFactory::create(v,name,option);
  
  if (ret) {
      fprintf(stderr,
	      "DEPRECATED END CONDITION SYNTAX. %s\nNew syntax is %s(%s)\n",
	      s.c_str(),name.c_str(),option.c_str());
  }


  return ret;
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
    er="Heuristic error:"+heuristic.errormsg;
    return true;
  }
  if (!heuristic.get_model()->status) {
    er="Model error:"+heuristic.get_model()->errormsg;
    return true;
  }
  if (!heuristic.get_coverage()->status) {
    er="Coverage error:"+heuristic.get_coverage()->errormsg;
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

void find(std::vector<std::string>& from,std::vector<std::string>& what,std::vector<int>& result)
{
  for(unsigned i=0;i<what.size();i++) {
    int p=find(from,what[i]);

      if (p) {
	result.push_back(p);
      } else {
	std::vector<int> r;
	regexpmatch(what[i],from,r,false);
	for(unsigned j=0;j<r.size();j++) {
	  result.push_back(r[j]);
	}
      }
  }
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

#define FACTORY_CREATE_PARAMS Verdict::Verdict v,	               \
                       std::string name,                               \
                       std::string params

#define FACTORY_CREATOR_PARAMS Verdict::Verdict v, std::string params
#define FACTORY_CREATOR_PARAMS2 v, params

FACTORY_IMPLEMENTATION(End_condition)

FACTORY_DEFAULT_CREATOR(End_condition, End_condition_steps,     "steps")
FACTORY_DEFAULT_CREATOR(End_condition, End_condition_coverage,  "coverage")
FACTORY_DEFAULT_CREATOR(End_condition, End_condition_tag,       "tag")
FACTORY_DEFAULT_CREATOR(End_condition, End_condition_tag,       "statetag")
FACTORY_DEFAULT_CREATOR(End_condition, End_condition_duration,  "duration")
FACTORY_DEFAULT_CREATOR(End_condition, End_condition_noprogress,"noprogress")
FACTORY_DEFAULT_CREATOR(End_condition, End_condition_noprogress,"no_progress")
FACTORY_DEFAULT_CREATOR(End_condition, End_condition_deadlock,  "deadlock")
FACTORY_DEFAULT_CREATOR(End_condition, End_condition_tagverify, "tagverify")
FACTORY_DEFAULT_CREATOR(End_condition, End_condition_tagverify, "failing_tag")
