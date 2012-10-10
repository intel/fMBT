/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2012 Intel Corporation.
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

#include "coverage_include.hh"
#include "helper.hh"

Coverage_Include_base::Coverage_Include_base(Log& l,
					     const std::string& param,
					     bool _exclude): Coverage(l), child(NULL), exclude(_exclude)
{
  commalist(param,subs);
  if (subs.size()>1) {
    child=new_coverage(l,subs.back());
  }
  status&=(child!=NULL);
}

void Coverage_Include_base::set_model(Model* _model)
{
  Coverage::set_model(_model);

  std::vector<std::string>& n=model->getActionNames();
  for(unsigned i=0;i<subs.size()-1;i++) {
    int p=find(n,subs[i]);
    if (p) {
      log.debug("Action %s %i\n",subs[i].c_str(),p);
      filteractions.insert(p);
    } else {
      // regexp?
      std::vector<int> r;
      if (subs[i][0]=='\'' || subs[i][0]=='\"') {
	// Let's remove first and the last charaster
	subs[i]=subs[i].substr(1,subs[i].length()-2);
      }
      regexpmatch(subs[i],n,r,false);
      for(unsigned j=0;j<r.size();j++) {
	log.debug("regexp %s %i\n",subs[i].c_str(),r[j]);
	filteractions.insert(r[j]);
      }
    }
  }
  
  ActionNames.push_back(""); // TAU
  
  for(unsigned i=1;i<n.size();i++) {
    if ((filteractions.find(i)==filteractions.end())==exclude) {
      log.debug("N: %s\n",n[i].c_str());
      ActionNames.push_back(n[i]);
    }
  }

  alpha=new Alphabet_impl(ActionNames,SPNames);
  submodel=new Model_yes(log,"");
  submodel->set_model(alpha);
  child->set_model(submodel);
}

class Coverage_Include: public Coverage_Include_base {
public:
  Coverage_Include(Log&l, const std::string& param):
    Coverage_Include_base(l,param,false) {
  }
  virtual ~Coverage_Include() {  }
};

class Coverage_Exclude: public Coverage_Include_base {
public:
  Coverage_Exclude(Log&l, const std::string& param):
    Coverage_Include_base(l,param,true) {
  }
  virtual ~Coverage_Exclude() {  }
};


FACTORY_DEFAULT_CREATOR(Coverage, Coverage_Include, "include")
FACTORY_DEFAULT_CREATOR(Coverage, Coverage_Exclude, "exclude")
