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

#include "coverage_exec_filter.hh"
#include "model.hh"
#include "helper.hh"
#include "history.hh"


// Coverage_exec_filter::Coverage_exec_filter(Log& l, std::string params):
//   Coverage(l),online(false) {
//   // Ok. Se need to parse the parameters ? 
//   // Or would it be better to do parsing in the factory create method?
// }


std::string Coverage_exec_filter::stringify()
{
  return std::string("");
}

void Coverage_exec_filter::set_model(Model* _model)
{
  Coverage::set_model(_model);

  printf("%s\n",__func__);

  std::vector<std::string>& sp(model->getSPNames());  

  printf("from size == %i\n",
	 from.size());

  for(unsigned i=0;i<from.size();i++) {
    int pos=find(sp,*from[i]);

    printf("Looking for %s (%i)\n",
	   from[i]->c_str(),pos);

    if (sp.size() && *from[i]!=sp[pos]) {
      pos=model->action_number(*from[i]);
      if (pos>0) {
	start_action.push_back(pos);
      } else {
	printf("\"%s\" not an tag or an action.\n",from[i]->c_str());
      }
    } else {
      start_tag.push_back(pos);
    }
  }

  for(unsigned i=0;i<to.size();i++) {
    int pos=find(sp,*to[i]);
    if (sp.size() && *to[i]!=sp[pos]) {
      pos=model->action_number(*to[i]);
      if (pos>0) {
	end_action.push_back(pos);
      } else {
	printf("\"%s\" not an tag or an action.\n",to[i]->c_str());
      }
    } else {
      end_tag.push_back(pos);
    }

  }

  for(unsigned i=0;i<drop.size();i++) {
    int pos=find(sp,*drop[i]);
    if (sp.size() && *drop[i]!=sp[pos]) {
      pos=model->action_number(*drop[i]);
      if (pos>0) {
	rollback_action.push_back(pos);
      } else {
	printf("\"%s\" not an tag or an action.\n",drop[i]->c_str());	
      }
    } else {
      rollback_tag.push_back(pos);
    }

  }

  
}

bool Coverage_exec_filter::prop_set(std::vector<int> p,int npro,
			       int* props)
{
  for(unsigned i=0;i<p.size();i++) {
    for(int j=0;j<npro;j++) {
      if (p[i]==props[j]) {
	return true;
      }
    }
  }
  return false;
}

bool Coverage_exec_filter::execute(int action)
{
  int* props;
  int npro;

  if (online) {
    executed.push_back(action);
    etime.push_back(History::current_time);
  }

  npro=model->getprops(&props);

  if (online) {
    /* Ok. Let's search for drop. */
    if (prop_set(rollback_tag,npro,props) || 
	prop_set(rollback_action,1,&action)) {
      on_drop();
      online=false;
      executed.clear();
      etime.clear();
    } else {
      /* No drop? Let's search for to */
      if (prop_set(end_tag,npro,props) || 
	  prop_set(end_action,1,&action)) {
	on_find();
	online=false;
	executed.clear();
	etime.clear();
      }
    }
  } 

  if (!online) {
    /* Let's search for from */
    if (prop_set(start_tag,npro,props) || 
	prop_set(start_action,1,&action)) {
      online=true;
      etime.push_back(History::current_time);
      on_start();
    }
  }

  return true;
}
