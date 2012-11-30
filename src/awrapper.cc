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

#include "awrapper.hh"
#include <algorithm>
#include "helper.hh"

std::string Awrapper::es("");

Awrapper::~Awrapper()
{
  if (ada) {
    ada->unref();
  }
}

Awrapper::Awrapper(Log&l, std::string params, aal* _ada):
  Adapter(l, params), ada(_ada) {
  if (ada==NULL) {
    status=false;
  } else {
    ada->ref();
    status=ada->status;
  }
}

bool Awrapper::init()
{
  return ada->init();
}

void Awrapper::set_actions(std::vector<std::string>* _actions)
{
  Adapter::set_actions(_actions);

  if (!status) {
    return;
  }

  std::vector<std::string>& wn=ada->getActionNames();

  std::vector<std::string> splitted_actions;

  splitted_actions.push_back(std::string(""));

  for(unsigned i=1;i<actions->size();i++) {
    std::string name,paramname;
    split((*actions)[i],name,paramname,"(");

    if (paramname!="") {
      paramname=paramname.substr(0,paramname.length()-1);
      parameters[i]=paramname;
      log.debug("action \"%s\" param %s\n",
		(*actions)[i].c_str(),paramname.c_str());

    }
    splitted_actions.push_back(name);

    unsigned result=find(wn,(*actions)[i],-1);

    if (result==(unsigned)-1) {
      // Let's try it without parameters
      result=find(wn,splitted_actions[i],-1);
      if (result==(unsigned)-1) {
	//Nope....
	continue;
      }
      // With parameters :)
      std::pair<int,std::string&> ind(result,parameters[i]);
      ada2aal[ind]=i;
    }

    ada2aal[std::pair<int,std::string&>(result,es)]=i;
    aal2ada[i]=result;
  }
}

void Awrapper::execute(std::vector<int>& action)
{
  /* We need to map.. */

  log.debug("Executing action %i (%i(\"%s\"))\n",
	    action[0],aal2ada[action[0]],
	    parameters[action[0]].c_str());

  std::string& prm=parameters[action[0]];

  int tmp=ada->adapter_execute(aal2ada[action[0]],parameters[action[0]].c_str());
  status=ada->status;
  log.debug("return %i\n",tmp);
  int ret=0;
  if (tmp) {
    ret=ada2aal[std::pair<int,std::string&>(tmp,prm)];
    if (!ret) {
      // Let't try without parameter...
      ret=ada2aal[std::pair<int,std::string&>(tmp,es)];
    }
  } else {
    // debug message?
  }
  action.resize(1);
  action[0]=ret;
}

int  Awrapper::observe(std::vector<int> &action,
		       bool block) {
  int tmp=ada->observe(action,block);
  status=ada->status;
  std::vector<std::string>& wn=ada->getActionNames();
  for(int i=0;i<tmp;i++) {
    int t=ada2aal[action[i],std::pair<int,std::string&>(action[i],es)];
    log.debug("observed %i (%s), converted %i (%s)\n",action[i],wn[action[i]].c_str(),t,(*actions)[t].c_str());
    action[i]=t;
  }
  return tmp;
}
