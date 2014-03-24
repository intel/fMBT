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
					     bool _exclude): Coverage(l),alpha(NULL),submodel(NULL), child(NULL), exclude(_exclude)
{
  commalist(param,subs);
  if (subs.size()>1) {
    child=new_coverage(l,subs.back());
  }
  status&=(child!=NULL);
}

void Coverage_Include_base::set_mode_helper(std::vector<std::string>& n,
					    std::set<int>& filter,
					    std::vector<std::string>& Names,
					    std::vector<int>& map)
{
  for(unsigned i=0;i<subs.size()-1;i++) {
    int p=find(n,subs[i]);
    if (p) {
      log.debug("Action/tag %s %i\n",subs[i].c_str(),p);
      filter.insert(p);
    } else {
      // regexp?
      std::vector<int> r;
      if (subs[i][0]=='\'' || subs[i][0]=='\"') {
	// Let's remove first and the last character
	subs[i]=subs[i].substr(1,subs[i].length()-2);
      }
      regexpmatch(subs[i],n,r,false);
      for(unsigned j=0;j<r.size();j++) {
	log.debug("regexp %s %i\n",subs[i].c_str(),r[j]);
	filter.insert(r[j]);
      }
    }
  }

  Names.push_back(""); // TAU

  map.resize(n.size()+1); // TAU

  for(unsigned i=1;i<n.size();i++) {
    if ((filter.find(i)==filter.end())==exclude) {
      log.debug("N: %s\n",n[i].c_str());
      map[i]=Names.size();
      Names.push_back(n[i]);
    }
  }

}

void Coverage_Include_base::set_model(Model* _model)
{
  Coverage::set_model(_model);

  set_mode_helper(model->getActionNames(),filteractions,ActionNames,amap);
  set_mode_helper(model->getSPNames(),filtertags,SPNames,smap);

  alpha=new Alphabet_impl(ActionNames,SPNames);
  submodel=new Model_yes(log,"");
  submodel->set_model(alpha);
  child->set_model(submodel);
  status=child->status;
  errormsg=child->errormsg;
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
