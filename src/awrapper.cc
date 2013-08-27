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
#include <string>

std::string Awrapper::es("");

Awrapper::~Awrapper()
{
  if (ada) {
    ada->unref();
  }
}

Awrapper::Awrapper(Log&l, aal* _ada):
  Adapter(l), ada(_ada) {
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

void Awrapper::adapter_exit(Verdict::Verdict verdict,
				    const std::string& reason)
{
  if (ada)
    ada->adapter_exit(verdict,reason);
}


void Awrapper::set_tags(std::vector<std::string>* _tags)
{
  Adapter::set_tags(_tags);

  if (!status) {
    return;
  }

 std::vector<std::string>& wn=ada->getSPNames();

  for(unsigned i=1;i<tags->size();i++) {

    unsigned result=find(wn,(*tags)[i],-1);

    if (result==(unsigned)-1) {
      continue;
    }
    
    tagaal2ada[i]=result;
    tagada2aal[result]=i;

  }
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
#ifdef  NEEDS_MINGWHACK
      std::pair<int,std::string> 
#else
      std::pair<int,std::string&> 
#endif
	ind(result,parameters[i]);
      ada2aal[ind]=i;
    }

#ifdef  NEEDS_MINGWHACK
    std::pair<int,std::string>
#else
    std::pair<int,std::string&>
#endif
      r(result,es);

    ada2aal[r]=i;
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
  if (!status) {
      errormsg = ada->errormsg;
      return;
  }

  log.debug("return %i\n",tmp);
  int ret=0;
  if (tmp) {
#ifdef  NEEDS_MINGWHACK
    ret=ada2aal[std::pair<int,std::string>(tmp,prm)];
#else
    ret=ada2aal[std::pair<int,std::string&>(tmp,prm)];
#endif
    if (!ret) {
      // Let't try without parameter...
#ifdef  NEEDS_MINGWHACK
      ret=ada2aal[std::pair<int,std::string>(tmp,es)];
#else
      ret=ada2aal[std::pair<int,std::string&>(tmp,es)];
#endif
      if (!ret) {
        status=false;
        errormsg="returned action out of range";
        return;
      }
    }
  } else {
    // debug message?
  }
  action.resize(1);
  action[0]=ret;
}

int Awrapper::check_tags(int* tag,int len,std::vector<int>& t)
{
  std::vector<int> _tags;

  // Think about the mapping....
  for(int i=0;i<len;i++) {

    if (tagaal2ada.find(tag[i])!=tagaal2ada.end()) {
      _tags.push_back(tagaal2ada[tag[i]]);
    }
  }
  if (_tags.size()>0) {
    int ret=ada->check_tags(_tags,t);
    for(unsigned i=0;i<t.size();i++) {
      t[i]=tagada2aal[t[i]];
    }
    return ret;
  }
  return 0;
}

int  Awrapper::observe(std::vector<int> &action,
		       bool block) {
  int tmp=ada->observe(action,block);
  status=ada->status;
  if (!status) {
      errormsg = ada->errormsg;
      return 0;
  }
  std::vector<std::string>& wn=ada->getActionNames();
  for(int i=0;i<tmp;i++) {
#ifdef  NEEDS_MINGWHACK
    int t=ada2aal[action[i],std::pair<int,std::string>(action[i],es)];
#else
    int t=ada2aal[action[i],std::pair<int,std::string&>(action[i],es)];
#endif
    log.debug("observed %i (%s), converted %i (%s)\n",action[i],wn[action[i]].c_str(),t,(*actions)[t].c_str());
    action[i]=t;
  }
  return tmp;
}
