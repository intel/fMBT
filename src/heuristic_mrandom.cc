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

#include "heuristic_mrandom.hh"
#include "helper.hh"
#include <cstdlib>
#include <cstring>

#include "random.hh"

Heuristic_mrandom::~Heuristic_mrandom()
{
  for(unsigned i=0;i<h.size();i++) {
    delete h[i].second;
  }
  if (r) {
    r->unref();
  }
}

Heuristic_mrandom::Heuristic_mrandom(Log& l,const std::string& params) :
  Heuristic(l)
{
  float total=0;
  std::vector<std::string> s;

  r = Random::default_random();

  commalist(params,s);

  for(unsigned i=0;i+1<s.size();i+=2) {
    float f=atof(s[i].c_str());
    if (f<=0.0) {
      f=1.0;
    }

    Heuristic* heu=new_heuristic(log,s[i+1]);

    if (heu==NULL) {
      status=false;
      errormsg=std::string("Can't create heuristic \"")+s[i+1]+
        std::string("\"");
      return;
    }
    if (heu->status==false) {
      status=false;
      errormsg=heu->errormsg;
      return;
    }
    total+=f;
    h.push_back(std::pair<float,Heuristic*>(total,heu));
  }

  if (h.empty()) {
    status=false;
    errormsg=std::string("no subheuristics?");
  }

  for(unsigned i=0;i<h.size();i++) {
    h[i].first=h[i].first/total;
  }

}

float Heuristic_mrandom::getCoverage() {
  if (my_coverage==NULL) {
    return 0.0;
  }
  return my_coverage->getCoverage();
}

int Heuristic_mrandom::getAction()
{
  float cut=r->drand48();

  for(unsigned i=0;i<h.size();i++) {
    if (cut<h[i].first) {
      return h[i].second->getAction();
    }
  }
  return h[0].second->getAction();
}

int Heuristic_mrandom::getIAction()
{
  float cut=r->drand48();

  for(unsigned i=0;i<h.size();i++) {
    if (cut<h[i].first) {
      return h[i].second->getIAction();
    }
  }
  return h[0].second->getIAction();
}

void Heuristic_mrandom::set_model(Model* _model)
{
  Heuristic::set_model(_model);
  for(unsigned i=0;i<h.size();i++) {
    h[i].second->set_model(_model);
    if (h[i].second->status==false) {
      status=false;
      errormsg=h[i].second->errormsg;
      return;
    }
  }
}

bool Heuristic_mrandom::execute(int action)
{
  bool ret=true;
  for(unsigned i=0;i<h.size();i++) {
    model->push();
    my_coverage->push();
    ret&=h[i].second->execute(action);
    my_coverage->pop();
    model->pop();
  }
  ret&=Heuristic::execute(action);
  return ret;
}

void Heuristic_mrandom::set_coverage(Coverage* c)
{
  Heuristic::set_coverage(c);
  for(unsigned i=0;i<h.size();i++) {
    h[i].second->set_coverage(c);
  }
}

FACTORY_DEFAULT_CREATOR(Heuristic, Heuristic_mrandom, "mrandom")
