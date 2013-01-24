/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2011-2013 Intel Corporation.
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

#include "coverage_short.hh"
#include "model.hh"
#include "helper.hh"

Coverage_Short::Coverage_Short(Log& l, std::string& _params) :
  Coverage(l), params(_params),props_total(0)
{
  
}

void Coverage_Short::history(int action,
			    std::vector<int>& props, 
			    Verdict::Verdict verdict)
{
}

void Coverage_Short::push()
{
  model->push();
}

void Coverage_Short::pop()
{
  model->pop();
}

bool Coverage_Short::execute(int action)
{
  log.print("<short execute_action=\"%s\"/>\n",
	    model->getActionName(action).c_str());
  return true;
}


float Coverage_Short::getCoverage()
{
  int* pro;
  int cnt=model->getprops(&pro);
  if (props_total && cnt) {
    return 1.0/(1.0+atoi(model->getSPNames()[pro[0]].c_str()));
  }
  return 1.0;
}


int Coverage_Short::fitness(int* action,int n,float* fitness)
{
  float m=-1;
  int pos=-1;

  if (props_total==0) {
    for(int i=0;i<n;i++) {
      fitness[i]=0.0;
    }
    return 0;
  }

  int* tags;
  int cnt=model->getprops(&tags);
  std::string s=to_string(cnt,tags,model->getSPNames());

  log.print("<fitness tags enabled=\"%s\"/>\n",s.c_str());

  for(int i=0;i<n;i++) {
    model->push();
    model->execute(action[i]);
    fitness[i]=getCoverage();
    cnt=model->getprops(&tags);
    model->pop();
    log.print("<fitness name=\"%s\" value=\"%f\"/>\n",
	      model->getActionName(action[i]).c_str(),
	      fitness[i]);
    std::string s=to_string(cnt,tags,model->getSPNames());
    log.print("<fitness action tags=\"%s\"/>\n",s.c_str());

    if (m<fitness[i] ||
	(m==fitness[i] && (((float)random())/RAND_MAX)>0.2)) {
      pos=i;
      m=fitness[i];
    }

  }

  log.print("<suggesting action=\"%s\" id=\"%i\" pos=\"%i\">\n",
	    model->getActionName(action[pos]).c_str(),action[pos],pos);

  return pos;
}

void Coverage_Short::set_model(Model* _model) {
  Coverage::set_model(_model);
  props_total=model->getSPNames().size()-1;
}

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_Short, "short")
