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

#include "coverage_trace.hh"
#include "helper.hh"
#include "model.hh"
#include <cstdlib>
#include <cstring>

Coverage_trace::~Coverage_trace()
{
  for(unsigned i=0;i<h.size();i++) {
    delete h[i].second;
  }
}

Coverage_trace::Coverage_trace(Log& l, const std::string& _params) :
  Coverage(l), params(_params),pos(0)
{
}

float Coverage_trace::getCoverage() {
  if (act.size()==pos) {
    return 1.0;
  }
  return 0.0;
}

void Coverage_trace::push()
{
  st.push(pos);
}

void Coverage_trace::pop()
{
  pos=st.top();
  st.pop();
}

bool Coverage_trace::execute(int action)
{
  if (pos==act.size()) {
    pos=0;
  }

  if (act[pos]==action) {
    pos++;
  } else {
    pos=0;
  }

  return true;
}

int Coverage_trace::fitness(int* actions,int n, float* fitness)
{
  return 0;
}

void Coverage_trace::set_model(Model* _model) {
  Coverage::set_model(_model);

  if (params=="") {
    //What to do?
    status=false;
  } else {
    std::vector<std::string> acts;
    std::vector<std::string>& an=model->getActionNames();

    commalist(params,acts);

    for(unsigned i=0;i<acts.size();i++) {
      int pos=find(an,acts[i]);
      if (!pos) {
	std::string s=acts[i];
	remove_force(s);
	pos=find(an,acts[i]);
      }
      if (pos) {
	act.push_back(pos);
      } else {
	status=false;
	printf("No action %s\n",acts[i].c_str());
	//???
      }
    }
  }
}

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_trace, "trace")
