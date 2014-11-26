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

#include "learn_action.hh"
#include "helper.hh"
#include "params.hh"

Learn_action::Learn_action(Log&l,std::string&s): Learning(l),
						 constructor_param(s){
}

bool Learn_action::add_action(std::string&s) {
  std::vector<std::string> alist;
  commalist(s,alist);
  std::vector<std::string>& names=alphabet->getActionNames();
  std::vector<int> result;
  for(unsigned i=0;i<alist.size();i+=2) {
    std::string action_name=alist[i].substr(1,alist[i].size()-2);
    std::string param;

    if (i+1<alist.size()) {
      param=alist[i+1];
    }

    Function* learning_multiplier = new_function(param);
    if (learning_multiplier==NULL) {
      learning_multiplier=new_function("0.5");
    }
    // function should be reffable...
    //learning_multiplier->ref();
    regexpmatch(action_name,names,result,true,1);

    if (result.empty()) {
      errormsg="No such action \""+action_name+"\"";
      status=false;
      return false;
    }

    for(unsigned j=0;j<result.size();j++) {
      action_map[result[j]]=Learn_action::as(learning_multiplier);
    }
    // learning_multiplier->unref();
  }
  return true;
}

void Learn_action::setAlphabet(Alphabet* a) {
  Learning::setAlphabet(a);
  add_action(constructor_param);
  constructor_param="";
  std::vector<std::string>& names=alphabet->getActionNames();
  unsigned actions=names.size();
  pvec.resize(actions);
  for(unsigned i=0;i<actions;i++) {
    pvec[i].resize(actions);
  }
}

void Learn_action::suggest(int action) {
  suggested=true;
  suggested_action=action;
}

void Learn_action::execute(int action) {
  if (suggested) {
    // called because something is suggested
    pvec[suggested_action][action]++;
    if (suggested_action==action) {
      // Adapter executed what we suggested
      // Nothing to do :)
    } else {
      // Adapter executed something else.
      std::map<int,struct as>::iterator i=action_map.find(suggested_action);
      if (i!=action_map.end()) {
	i->second.value=i->second.value*i->second.learning_multiplier->fval();
      }
    }
  } else {
    // called because of output action?
    pvec[action][action]++;
  }
  suggested=false;
}

float Learn_action::getF(int action) {
  std::map<int,struct as>::iterator i=action_map.find(action);

  if (i!=action_map.end()) {
    return i->second.value;
  }
  return 1.0;
}

float Learn_action::getC(int sug,int exe) {
  return pvec[sug][exe];
}

FACTORY_DEFAULT_CREATOR(Learning, Learn_action, "action")
