/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2012,2013, Intel Corporation.
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

#include "model.hh"
#include <set>
#include "helper.hh"

class Model_filter : public Model {
public:
  Model_filter(Log&l,const std::string& param,bool _i): Model(l,param), cmp(_i)
  {
    commalist(param,fa);
  }
  virtual ~Model_filter() {}  

  int filter(int** actions,int r) {
    int pos=0;
    for(int i=0;i<r;i++) {
      a[pos]=(*actions)[i];
      if ((filteractions.find((*actions)[i])==filteractions.end())==cmp) {
	pos++;
      }
    }
    *actions = &a[0];
    return pos;
  }

  virtual int getActions(int** actions) {
    return filter(actions,submodel->getActions(actions));
  }

  virtual int getIActions(int** actions) {
    return filter(actions,submodel->getIActions(actions));
  }

  virtual bool reset() {
    return true;
  }
  virtual int  execute(int action) {
    return submodel->execute(action);
  }
  virtual int getprops(int** props) {
    return submodel->getprops(props);
  }
  virtual void push() {
    submodel->push();
  }
  virtual void pop() {
    submodel->pop();
  }
  virtual bool init() {
    // init filter.
    std::vector<std::string>& n=submodel->getActionNames();
    action_names=n;
    prop_names=submodel->getSPNames();
    a.resize(action_names.size());

    for(unsigned i=0;i<fa.size()-1;i++) {
      int p=find(n,fa[i]);
      if (p) {
	filteractions.insert(p);
      } else {
	// regexp?
	std::vector<int> r;
	if (fa[i][0]=='\'' || fa[i][0]=='\"') {
	  // Let's remove first and the last charaster
	  fa[i]=fa[i].substr(1,fa[i].length()-2);
	}
	regexpmatch(fa[i],n,r,false);
	for(unsigned j=0;j<r.size();j++) {
	  filteractions.insert(r[j]);
	}
      }
    }
    return true;
  }
  std::vector<int> a;
  std::set<int> filteractions;
  Model* submodel;
  bool cmp;
  std::vector<std::string> fa;
};
