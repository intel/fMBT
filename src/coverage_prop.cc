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
  Coverage(l), params(_params),props_total(0),props_seen(0)
{

}

void Coverage_Prop::history(int action,
			    std::vector<int>& props, 
			    Verdict::Verdict verdict)
{
  /* Not intrested about action or verdict. Just proposition */
  
  for(unsigned i=0;i<props.size();i++) {
    int pos=map[props[i]];
    if (pos && !data[pos]) {
      props_seen++;
      data[pos]=true;
    }
  }  
}

void Coverage_Prop::push()
{
  model->push();
  std::pair<std::vector<bool>,int> p(data,props_seen);
  state_save.push_front(p);
}

void Coverage_Prop::pop()
{
  model->pop();
  data=state_save.front().first;
  props_seen=state_save.front().second;
  state_save.pop_front();
}

bool Coverage_Prop::execute(int action)
{
  int* pro;
  int cnt=model->getprops(&pro);

  for(int i=0;i<cnt;i++) {
    int pos=map[pro[i]];
    if (pos && !data[pos]) {
      props_seen++;
      data[pos]=true;
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
      map[i]=i;
    }
  } else {
    // Only props in the params.
    std::vector<std::string> props;
    static const std::string separator(":");
    std::vector<std::string>& sp=model->getSPNames();
    strvec(props,params,separator);
    for(unsigned i=1;i<sp.size();i++) {
      int pos=find(props,sp[i]);
      if (pos) 
	map[i]=pos;
    }
    props_total=map.size();
  }
  data.resize(props_total+1);
}

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_Prop, "tag")
