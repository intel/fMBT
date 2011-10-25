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
#ifndef __coverage_market_hh__
#define __coverage_market_hh__

#include <stack>

#include "model.hh"
#include "coverage.hh"

#include <regex.h>

#include <map>
#include <vector>

#include <cstdlib>

#define max(a,b) (((a)>(b))?(a):(b))
#define min(a,b) (((a)<(b))?(a):(b))

class Coverage_Market;
extern Coverage_Market* cobj;

class Coverage_Market: public Coverage {

public:
  class unit;
  Coverage_Market(Log& l): Coverage(l) {}
  ~Coverage_Market() {
    for(size_t i=0;i<Units.size();i++) {
      delete Units[i];
    }
  }

  virtual void push() {};
  virtual void pop() {};

  virtual bool execute(int action);
  virtual float getCoverage();

  virtual int fitness(int* actions,int n, float* fitness);

  virtual void addmodel(Model* model) { // for coverage
    models.push_back(model);
  }

  virtual void setmodel(Model* _model)
  {
    model=_model;
  }

  void addrequirement(std::string& req);

  unit* req_rx_action(const char m,const char* action);

  void add_unit(unit* u) {
    Units.push_back(u);
  }

  /**
   * coveragerequirement
   *
   * (a action1 or e action2) and action3 then ((action4 or action5) not action1)
   *
   */


  typedef std::pair<int, int> val;


  class unit {
  public:
    val& get_value() { 
      return value;
    }
    virtual ~unit() {}
    virtual void execute(int action)=0;
    virtual void update()=0;
    virtual void push()=0;
    virtual void pop()=0;
  protected:
    val value;
  };

  class unit_dual: public unit {
  public:
    unit_dual(unit* l,unit* r):left(l),right(r) {
    }

    virtual void push() {
      left->push();
      right->push();
    }

    virtual void pop() {
      left->pop();
      right->pop();
    }

    virtual ~unit_dual() {
      delete left;
      delete right;
    }

    virtual void execute(int action) {
      left->execute(action);
      right->execute(action);
    }

  protected:
    unit* left,*right;

  };

  class unit_and: public unit_dual {
  public:
    unit_and(unit* l,unit* r) : unit_dual(l,r) {}
    virtual void update() {
      left->update();
      right->update();
      val vl=left->get_value();
      val vr=right->get_value();
      value.first = vl.first+vr.first;
      value.second=vl.second+vr.second;
    }
  protected:
  };
  
  class unit_or: public unit_dual {
  public:
    unit_or(unit* l,unit* r) : unit_dual(l,r) {}
    virtual void update() {
      left->update();
      right->update();
      val vl=left->get_value();
      val vr=right->get_value();
      /* ???? */
      value.first = 
	max(vl.first/vl.second,
	    vr.first/vr.second)*(vl.second+vr.second);
      value.second=vl.second+vr.second;
    }
  protected:
    
  };

  class unit_not: public unit {
  public:
    unit_not(unit *c):child(c) {
    }
    virtual void push() {
      child->push();
    }
    
    virtual void pop() {
      child->pop();
    }
    virtual ~unit_not() {
      delete child;
    }
    virtual void execute(int action) {
      child->execute(action);
    }

    virtual void update() {
      val v=child->get_value();
      value.first=v.second-v.first;
      value.second=v.second;
    }
  protected:
    unit* child;
  };

  class unit_then: public unit_dual {
  public:
    unit_then(unit* l,unit* r) : unit_dual(l,r) {}
    virtual void execute(int action) {
      // if left, then right
      val v=left->get_value();
      if (v.first==v.second) {
	right->execute(action);
      }
      left->execute(action);
    }

    virtual void update() {
      left->update();
      right->update();
      val vl=left->get_value();
      val vr=right->get_value();
      /* ???? */
      value.first=vl.first+vr.first;
      value.second=vl.second+vr.second;      
    }
  protected:
    
  };

  class unit_leaf: public unit {
  public:    
    unit_leaf(int action, int count=1) : my_action(action) {
      value.second=count;
    }

    virtual void push() {
      st.push(value);
    }

    virtual void pop() {
      value=st.top();
      st.pop();
    }


    virtual void execute(int action) {
      if (action==my_action) {
	if (value.first<value.second) {
	  value.first++;
	}
      }
    }
    virtual void update() {
      
    }
  protected:
    int my_action;
    std::stack<val> st;
  };

protected:
  
  std::vector<Model*> models;

  std::vector<unit*> Units;

  std::multimap<int,char*> map;

};


#endif
