/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2012, Intel Corporation.
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

#include "heuristic_weight.hh"
#include "helper.hh"
#include <cstdlib>
#include <cstring>

#include "dparse.h"
extern "C" {
  extern D_ParserTables parser_tables_weight;
}

extern Heuristic_weight* Hw;

Heuristic_weight::Heuristic_weight(Log& l, std::string params) :
  Heuristic(l),prm(params)
{
}

float Heuristic_weight::getCoverage() {
  if (my_coverage==NULL) {
    return 0.0;
  }
  return my_coverage->getCoverage();
}

void Heuristic_weight::add(std::vector<std::string*> p,
			   std::vector<std::string*> a,
			   int w)
{
  std::vector<int> props;
  std::vector<int> actions;

  for(unsigned i=0;i<p.size();i++) {
    regexpmatch(*(p[i]),model->getSPNames(),props,false);
  }

  for(unsigned i=0;i<a.size();i++) {
    regexpmatch(*(a[i]),model->getActionNames(),actions,false);
  }

  // List of required propositions is empty =>
  // don't care about propositions, match all states
  if (p.empty())
    props.push_back(-1);

  if (actions.empty()) {
    return;
  }

  for(unsigned i=0;i<props.size();i++) {
    for(unsigned j=0;j<actions.size();j++) {
      weights[std::pair<int,int>(props[i],actions[j])]+=w;
    }
  }
}

int Heuristic_weight::weight_select(int i,int* actions)
{
  int* props;
  int p=model->getprops(&props);
  float total=0;
  std::vector<float> f;

  f.resize(i);

  // Go through props
  for(int j=0;j<p;j++) {
    // Go through actions
    for(int k=0;k<i;k++) {
      float ff=weights[std::pair<int,int>(props[j],actions[k])];
      f[k]+=ff;
      total+=ff;
    }
  }

  // And then without prop
  // Go through actions
  for(int k=0;k<i;k++) {
    float ff=weights[std::pair<int,int>(-1,actions[k])];
    f[k]+=ff;
    total+=ff;
  }

  // Total weight 0?
  if (total==0.0) {
    return (((float)random())/RAND_MAX)*i;
  }

  float cut=drand48()*total;
  int pos;
  for(pos=0;cut>f[pos];cut-=f[pos],pos++);

  return pos;
}

int Heuristic_weight::getAction()
{
  int* actions;
  int i;

  i=model->getActions(&actions);

  if (i==0) {
    // DEADLOCK
    return Alphabet::DEADLOCK;
  }

  int pos=weight_select(i,actions);

  return actions[pos];
}

int Heuristic_weight::getIAction()
{
  int* actions;
  int i;

  i=model->getIActions(&actions);

  if (i==0) {
    // Ok.. no output actions
    i=model->getActions(&actions);
    if (i==0) {
      return Alphabet::DEADLOCK;
    }
    return Alphabet::OUTPUT_ONLY;
  }

  int pos=weight_select(i,actions);

  return actions[pos];
}

void Heuristic_weight::set_model(Model* _model)
{
  Heuristic::set_model(_model);

  char* s=readfile(prm.c_str());
  if (s) {
    Heuristic_weight* h=Hw;
    Hw=this;
    D_Parser *p = new_D_Parser(&parser_tables_weight, 512);
    p->loc.pathname = prm.c_str();
    bool ret=dparse(p,s,std::strlen(s));
    ret=p->syntax_errors==0 && ret;
    free_D_Parser(p);
    free(s);
    status=ret;
    if (!ret) {
      errormsg="parse error";
    }
    Hw=h;
  } else {
    status=false;
    errormsg="Can't read inputfile";
  }
}

void Heuristic_weight::set_coverage(Coverage* c)
{
  Heuristic::set_coverage(c);
}

FACTORY_DEFAULT_CREATOR(Heuristic, Heuristic_weight, "weight")
