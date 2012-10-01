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

#include "coverage_join.hh"
#include "helper.hh"

Coverage_Join::Coverage_Join(Log& l,const std::string& param)
  : Coverage(l), child(NULL)
{
  commalist(param,subs);
  if (subs.size()>1) {
    child=new_coverage(l,subs.back());
  }
  status&=(child!=NULL);
}

void Coverage_Join::handle_sub(const std::string& sub)
{
  std::string mapped_to;
  std::string tmp;
  std::vector<std::string> mapped_from;
  
  param_cut(sub,mapped_to,tmp);
  commalist(tmp,mapped_from);
  // mapped_to is the _new_ alphabet
  // mapped_from is the alphas found in the current alphabet
  // Let's check that mapped_to doesn't exist in the ActionNames
  if (find(ActionNames,mapped_to)) {
    status=false;
    errormsg=mapped_to+" found twice";
  }

  log.debug("Mapping action %s\n",mapped_to.c_str());

  ActionNames.push_back(mapped_to);
  for(unsigned i=0;i<mapped_from.size();i++) {
    int pos=find(ActionNames_from,mapped_from[i]);
    log.debug("Handling mapping at %i (%s) pos %i\n",i,mapped_from[i].c_str(),pos);
    if (!pos) {
      // No luck? RegExp?
      log.debug("No luck... %s\n",mapped_from[i].c_str());
    } else {
      int m=ActionNames.size()-1;
      action_mapper[pos]=m;
      ActionNames_from[pos]=""; // Only one map....
    }
  }
}

void Coverage_Join::set_model(Model* _model)
{
  Coverage::set_model(_model);
  ActionNames.push_back(""); // TAU

  ActionNames_from=model->getActionNames();

  for(unsigned i=0;i<subs.size()-1;i++) {
    if (!status) {
      return;
    }
    handle_sub(subs[i]);
  }

  log.debug("action_names count %i\n",ActionNames.size());

  // Let's handle not mapped actions

  for(unsigned i=0;i<ActionNames_from.size();i++) {
    if (ActionNames_from[i]!="") {
      int m=ActionNames.size();

      log.debug("Action %i (%s) not mapped. Mapping to %i\n",
	     i,ActionNames_from[i].c_str(),m);

      ActionNames.push_back(ActionNames_from[i]);
      action_mapper[i]=m;
    }
  }

  ActionNames_from.clear();

  alpha=new Alphabet_impl(ActionNames,SPNames);
  submodel=new Model_yes(log,"");
  submodel->set_model(alpha);
  child->set_model(submodel);
}

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_Join, "join")
