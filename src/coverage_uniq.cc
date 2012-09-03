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

#include "coverage_uniq.hh"
#include <algorithm>

Coverage_uniq::Coverage_uniq(Log& l,std::string params) :Coverage(l)
{
  std::string lens,sub;
  // Hmm. Parameters?
  std::vector<std::string> s;
  commalist(params,s);

  if (s.size()!=2) {
    // FIX errormsg
    status=false;
    return;
  }

  len=atoi(s[0].c_str());
  if (len<2) {
    len=2;
  }

  Coverage* c = new_coverage(l,s[1]);

  if (c==NULL) {
    // FIX errormsg
    status=false;
  } else {
    status=c->status;
    covs.push_back(c);
  }
}

Coverage_uniq::~Coverage_uniq()
{
  for(unsigned i=0;i<covs.size();i++) {
    delete covs[i];
  }  
}

std::string Coverage_uniq::stringify()
{
  return std::string("");
}

bool Coverage_uniq::execute(int action)
{
  if (find(v.begin(),v.end(),action)!=v.end()) {
    for(unsigned i=0;i<covs.size();i++) {
      covs[i]->execute(action);
    }
  }
  v.push_back(action);
  if (v.size()>len) {
    v.pop_front();
  }
  return true;
}

void Coverage_uniq::history(int action,std::vector<int>& props,
			  Verdict::Verdict verdict)
{

  /* This doesn't work! */

  for(unsigned i=0;i<covs.size();i++) {
    covs[i]->history(action,props,verdict);
  }
}

void Coverage_uniq::set_model(Model* _model) {

  Coverage::set_model(_model);
  for(unsigned i=0;i<covs.size();i++) {
    covs[i]->set_model(_model);
  }
}


FACTORY_DEFAULT_CREATOR(Coverage, Coverage_uniq, "uniq")
