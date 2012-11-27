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
#ifndef __coverage_if_hh__
#define __coverage_if_hh__

#include "coverage.hh"
#include "helper.hh"
#include <stack>

class Coverage_compare: public Coverage {
public:
  Coverage_compare(Log&l, std::string& params): Coverage(l) {
    std::vector<std::string> subs;
    commalist(params,subs);
    if (subs.size()==2) {
      left=new_coverage(l,subs[0]);
      right=new_coverage(l,subs[1]);

      if (left==NULL) {
	status=false;
	errormsg="Can't create left coverage ("+subs[0]+")";
      } else if (left->status==false) {
	status=false;
	errormsg="Error in left coverage:"+left->errormsg;
      }

      if (right==NULL) {
	status=false;
	errormsg="Can't create right coverage ("+subs[1]+")";
      } else if (right->status==false) {
	status=false;
	errormsg="Error in right coverage:"+right->errormsg;
      }
    } else {
      status=false;
      errormsg=cmp+"(left,right)";
    }
  }

  virtual ~Coverage_compare() {
    if (left) {
      delete left;
    }
    if (right) {
      delete right;
    }
  }
  
  virtual std::string stringify() {
    return errormsg;
  }

  virtual void push() { left->push();right->push(); }
  virtual void pop() { left->pop();right->pop(); }

  virtual int fitness(int* actions,int n, float* fitness) {
    return 0;
  }

  virtual void set_model(Model* _model) {
    if (status) {
      Coverage::set_model(_model);
      left->set_model(model);
      right->set_model(model);
    }
  }

  virtual bool execute(int action) {
    return left->execute(action) &&
      right->execute(action);
    
  }
protected:
  std::string cmp;
  Coverage *left,*right;
};

class Coverage_skip: public Coverage_compare {
public:
  Coverage_skip(Log&l, std::string& params): Coverage_compare(l,params) {
    cmp="skip";
  }

  virtual float getCoverage() {
    return right->getCoverage();
  }

  virtual bool execute(int action) {
    left->execute(action);
    if (left->getCoverage()>=1.0) {
      right->execute(action);
    }
    return true;
  }

};

class Coverage_lt: public Coverage_compare {
public:
  Coverage_lt(Log&l, std::string& params): Coverage_compare(l,params) {
    cmp="lt";
  }

  virtual ~Coverage_lt() { }

  virtual float getCoverage() {
    float l=left->getCoverage(),r=right->getCoverage();
    if (l<r) {
      return 1.0+(r-l);
    }
    return (r-l);
  }
};

class Coverage_le: public Coverage_compare {
public:
  Coverage_le(Log&l, std::string& params): Coverage_compare(l,params) {
    cmp="le";
  }

  virtual ~Coverage_le() { }

  virtual float getCoverage() {
    float l=left->getCoverage(),r=right->getCoverage();
    if (l<=r) {
      return 1.0+(r-l);
    }
    return (r-l);
  }
};


class Coverage_gt: public Coverage_compare {
public:
  Coverage_gt(Log&l, std::string& params): Coverage_compare(l,params) {
    cmp="gt";
  }

  virtual ~Coverage_gt() { }

  virtual float getCoverage() {
    float l=left->getCoverage(),r=right->getCoverage();
    if (l>r) {
      return 1.0+(l-r);
    }
    return (l-r);
  }

};

class Coverage_ge: public Coverage_compare {
public:
  Coverage_ge(Log&l, std::string& params): Coverage_compare(l,params) {
    cmp="ge";
  }

  virtual ~Coverage_ge() { }

  virtual float getCoverage() {
    float l=left->getCoverage(),r=right->getCoverage();
    if (l>=r) {
      return 1.0+(l-r);
    }
    return (l-r);
  }
};



class Coverage_if: public Coverage {
public:
  Coverage_if(Log&l, std::string& params): Coverage(l),condition(NULL),then_c(NULL),else_c(NULL) {
    std::vector<std::string> subs;
    commalist(params,subs);
    if (subs.size()>=2 && subs.size()<=3) {
      condition=new_coverage(l,subs[0]);
      then_c   =new_coverage(l,subs[1]);
      if (subs.size()==3) {
	else_c   =new_coverage(l,subs[2]);
      }

      if (condition==NULL) {
	status=false;
	errormsg="Can't create condition coverage ("+subs[0]+")";
      } else if (condition->status==false) {
	status=false;
	errormsg="Error in condition coverage:"+condition->errormsg;
      }

      if (then_c==NULL) {
	status=false;
	errormsg="Can't create then coverage ("+subs[1]+")";
      } else if (then_c->status==false) {
	status=false;
	errormsg="Error in then coverage:"+then_c->errormsg;
      }

      if (subs.size()==3) {
	if (else_c==NULL) {
	  status=false;
	  errormsg="Can't create else coverage ("+subs[2]+")";
	} else if (else_c->status==false) {
	  status=false;
	  errormsg="Error in else coverage:"+else_c->errormsg;
	}
      }
    } else {
      status=false;
      errormsg="Not a valid if. if(condition,then,else)";
    }
  }

  virtual ~Coverage_if() {
    if (condition) {
      delete condition;
    }
    if (then_c) {
      delete then_c;
    }
    if (else_c) {
      delete else_c;
    }
  }
  virtual std::string stringify() {
    if (status) {
      return std::string("if(")+condition->stringify()+","+then_c->stringify()+","+else_c->stringify()+")";
    }
    return errormsg;
  }

  virtual void push() { condition->push();then_c->push();if (else_c) else_c->push(); }
  virtual void pop() { condition->pop();then_c->pop();if (else_c) else_c->pop(); }

  virtual float getCoverage() {
    float cc=condition->getCoverage();
    if (cc>=1.0) {
      if (else_c) {
	return then_c->getCoverage();
      }
      return cc+then_c->getCoverage();
    }

    if (else_c) {
      return else_c->getCoverage();
    }

    return cc;
  }

  virtual int fitness(int* actions,int n, float* fitness) {
    if (condition->getCoverage()>=1.0) {
      return then_c->fitness(actions,n,fitness);
    }
    if (else_c) {
      return else_c->fitness(actions,n,fitness);
    }
    return condition->fitness(actions,n,fitness);
  }

  virtual void set_model(Model* _model) {
    if (status) {
      Coverage::set_model(_model);
      condition->set_model(model);
      then_c->set_model(model);
      if (else_c) else_c->set_model(model);
    }
  }

  virtual bool execute(int action) {
    return condition->execute(action) &&
      then_c->execute(action) &&
      (else_c==NULL || else_c->execute(action));
  }


protected:
  Coverage* condition;
  Coverage* then_c;
  Coverage* else_c;
};

#endif
