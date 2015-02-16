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

#include "coverage_prop.hh"
#include "model.hh"
#include "helper.hh"

Coverage_Prop::Coverage_Prop(Log& l, std::string& _params) :
  Coverage(l),props_total(0),props_seen(0),params(_params)
{

}

void Coverage_Prop::history(int action,
			    std::vector<int>& props, 
			    Verdict::Verdict verdict)
{
  /* Not intrested about action or verdict. Just proposition */
  
  for(unsigned i=0;i<props.size();i++) {
    if (prop_included[props[i]] && !data[props[i]]) {
      props_seen++;
      data[props[i]]=true;
    }
  }  
}

void Coverage_Prop::push()
{
  std::pair<std::vector<bool>,int> p(data,props_seen);
  state_save.push_front(p);
}

void Coverage_Prop::pop()
{
  data=state_save.front().first;
  props_seen=state_save.front().second;
  state_save.pop_front();
}

bool Coverage_Prop::execute(int action)
{
  int* pro;
  int cnt=model->getprops(&pro);

  for(int i=0;i<cnt;i++) {
    if (prop_included[pro[i]] && !data[pro[i]]) {
      props_seen++;
      data[pro[i]]=true;
    }
  }

  return true;
}


float Coverage_Prop::getCoverage()
{
  if (props_total) {
    return (1.0*props_seen)/(1.0*props_total);
  }
  return 1.0;
}


int Coverage_Prop::fitness(int* action,int n,float* fitness)
{
  float m=-1;
  int pos=-1;

  if (props_total==0) {
    for(int i=0;i<n;i++) {
      fitness[i]=0.0;
    }
    return 0;
  }
  
  for(int i=0;i<n;i++) {
    model->push();
    model->execute(action[i]);
    fitness[i]=getCoverage();
    model->pop();

    if (m<fitness[i]) {
      pos=i;
      m=fitness[i];
    }
  }
  
  return pos;
}

void Coverage_Prop::regexp_try(std::string& s,std::vector<std::string>& sp) {
  std::vector<int> regexp_match;
  regexpmatch(s,sp,regexp_match,true);

  for(unsigned i=0;i<regexp_match.size();i++) {
    if (regexp_match[i]) {
      prop_included[regexp_match[i]]=true;
    }
  }
}

void Coverage_Prop::set_model(Model* _model) {
  Coverage::set_model(_model);
  /*
  props_total=model->getSPNames().size()-1; // let's ignore 0
  */
  if (params=="") {
    props_total=model->getSPNames().size()-1; // let's ignore 0
    if (props_total<0) {
      props_total=0;
    }
    for(unsigned i=1;i<model->getSPNames().size();i++) {
      prop_included[i]=true;
    }
  } else {
    // Only props in the params.
    std::vector<std::string> props;
    std::vector<std::string>& sp=model->getSPNames();
    commalist(params,props);
    strlist(props);
    for(unsigned i=0;i<props.size();i++) {
      int propnum = find(sp,props[i]);
      if (propnum) {
	prop_included[propnum]=true;
      } else {
	regexp_try(props[i],sp);
      }
    }
    props_total=prop_included.size();
  }
  data.resize(props_total+1);

  execute(0);
}

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_Prop, "tag")
