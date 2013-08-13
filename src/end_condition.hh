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

#ifndef __end_condition_hh__
#define __end_condition_hh__

#include "verdict.hh"
#include "writable.hh"
#include "heuristic.hh"
#include "model.hh"
#include <string>
#include "log_null.hh"

#ifndef DROI
#include <glib.h>
#endif

#include "coverage_const.hh"

class End_condition: public Writable {
public:
  typedef enum {
    STEPS = 0,
    COVERAGE,
    STATETAG,
    DURATION,
    NOPROGRESS,
    DEADLOCK,
    ACTION,
    STATUS,
    TAGVERIFY
  } Counter;

  End_condition(Verdict::Verdict v, const std::string& p);
  virtual ~End_condition();

  virtual std::string stringify() {
    if (!status) return Writable::stringify();
    std::string ret;
    switch (verdict) {
    case Verdict::PASS:
      ret="pass";
      break;
    case Verdict::FAIL:
      ret="fail";
      break;
    case Verdict::INCONCLUSIVE:
      ret="inconc";
      break;
    case Verdict::W_ERROR:
      ret="error";
      break;
    default:
      break;
    }
    std::string name;
    switch(counter) {
    case STEPS:
      name="steps";
      break;
    case COVERAGE:
      name="coverage";
      break;
    case STATETAG:
      name="tag";
      break;
    case DURATION:
      name="duration";
      break;
    case NOPROGRESS:
      name="noprogress";
      break;
    case DEADLOCK:
      name="deadlock";
      break;
    case TAGVERIFY:
      name="failing_tag";
      break;
    case ACTION:
    case STATUS:
    default:
      return "";
    }
    if (param!="") {
      ret=ret+"\t=\t"+name+"("+param+")";
    } else {
      ret=ret+"\t=\t"+name;
    }
    return ret;
  }

  virtual bool match(int step_count,int state, int action,int last_step_cov_growth,Heuristic& heuristic,std::vector<int>& mismatch_tags)=0;
  virtual const std::string& end_reason() {
    return er;
  }

  Verdict::Verdict verdict;
  Counter counter;
  std::string param;

  float param_float;
  long param_long;
  time_t param_time;

  std::string er;
  int  notify_step;
};

class End_condition_steps: public End_condition {
public:
  End_condition_steps(Verdict::Verdict v, const std::string& p):
    End_condition(v,p) {
    counter = STEPS;
    er="step limit reached";
    char* endp;

    param_long = strtol(param.c_str(),&endp,10);
    if (endp && endp[0]!=0) {
      status=false;
      errormsg=param+" not a valid step limit requirement";
      return;
    }
    if (param_long>=0 && endp[0]==0) {
      status = true;
    } else {
      errormsg=param+" is not a valid step count";
      status = false;
    }
  }
  virtual ~End_condition_steps() {}
  virtual bool match(int step_count,int state, int action,int last_step_cov_growth,Heuristic& heuristic,std::vector<int>& mismatch_tags) {
    if (param_long > -1 && step_count >= param_long) return true;
    return false;
  }
};

class End_condition_tag: public End_condition {
public:
  End_condition_tag(Verdict::Verdict v, const std::string& p):
    End_condition(v,p) {
    counter = STATETAG;
    er="tag reached";
    status = true;
  }
  virtual ~End_condition_tag() {}
  virtual bool match(int step_count,int state, int action,int last_step_cov_growth,Heuristic& heuristic,std::vector<int>& mismatch_tags);
};

class End_condition_duration: public End_condition {
public:
  End_condition_duration(Verdict::Verdict v, const std::string& p):
    End_condition(v,p) {
    counter = DURATION;
    er="time limit reached";
    status=true;
    param_time = -1;
#ifndef DROI
    char* out = NULL;
    int stat;
    std::string ss = "date --date='" + param + "' +%s.%N";

    if (g_spawn_command_line_sync(ss.c_str(), &out, NULL, &stat, NULL)) {
      if (!stat) {
	// Store seconds to param_time and microseconds to param_long
	param_time = atoi(out);
	param_long = (strtod(out, NULL) - param_time) * 1000000;
	status = true;
      } else {
	errormsg = "Parsing 'duration' parameter '" + param + "' failed.";
	errormsg += " Date returned an error when executing '" + ss + "'";
	status = false;
      }
    } else {
      errormsg = "Parsing 'duration' parameter '" + param + "' failed, could not execute '";
      errormsg += ss + "'";
      status = false;
    }
#else
    char* endp;
    long r = strtol(param.c_str(), &endp, 10);
    if (*endp == 0) {
      param_time = r;
      status = true;
    } else {
      // Error on str?
      errormsg = "Parsing duration '" + param + "' failed.";
      status = false;
    }
#endif
  }
  virtual ~End_condition_duration() {}
  virtual bool match(int step_count,int state, int action,int last_step_cov_growth,Heuristic& heuristic,std::vector<int>& mismatch_tags);
};


class End_condition_noprogress: public End_condition {
public:
  End_condition_noprogress(Verdict::Verdict v, const std::string& p):
    End_condition(v,p) {
    counter = NOPROGRESS;
    er="no progress limit reached";
    param_long = atol(param.c_str());
    status = true;
  }
  virtual ~End_condition_noprogress() {}
  virtual bool match(int step_count,int state, int action,int last_step_cov_growth,Heuristic& heuristic,std::vector<int>& mismatch_tags) {
    if (step_count - last_step_cov_growth >= param_long) return true;

    return false;
  }
};


class End_condition_deadlock: public End_condition {
public:
  End_condition_deadlock(Verdict::Verdict v, const std::string& p):
    End_condition(v,p) {
    counter = DEADLOCK;
    er="deadlock reached";
    status = true;
  }
  virtual ~End_condition_deadlock() {}
  virtual bool match(int step_count,int state, int action,int last_step_cov_growth,Heuristic& heuristic,std::vector<int>& mismatch_tags) {
    if (state==Alphabet::DEADLOCK) {
      return true;
    }

    return false;
  }
};

class End_status_error: public End_condition {
public:
  End_status_error(Verdict::Verdict v, const std::string& p):
    End_condition(v,p) {
    counter = STATUS;
    status = true;
  }

  virtual ~End_status_error() {}
  virtual bool match(int step_count,int state, int action,int last_step_cov_growth,Heuristic& heuristic,std::vector<int>& mismatch_tags);
};

class End_condition_action: public End_condition {
public:
  End_condition_action(Verdict::Verdict v, const std::string& p):
    End_condition(v,p) {
    counter = ACTION;
    er="executed break action";
    status = true;
  }
  virtual ~End_condition_action() {}
  virtual bool match(int step_count,int state, int action,int last_step_cov_growth,Heuristic& heuristic,std::vector<int>& mismatch_tags) {
    if ((action>=0) && (action==param_long)) return true;

    return false;
  }
};


class End_condition_coverage: public End_condition {
public:
  End_condition_coverage(Verdict::Verdict v, const std::string& p):
    End_condition(v,p) {
    counter = COVERAGE;
    er="coverage reached";
    status = true;
    l.ref();
    c = new_coverage(l,p);
    if (c==NULL) {
      status=false;
      errormsg=param+" not valid coverage";
    } else {
      if ((dynamic_cast<Coverage_Const*>(c))!=NULL) {
	cconst=true;
	param_float = strtod(param.c_str(),NULL);
      } else {
	cconst=false;
      }
    }
    set_model_done=false;
  }
  virtual ~End_condition_coverage() {
    if (c)
      delete c;
  }
  virtual bool match(int step_count,int state, int action,int last_step_cov_growth,Heuristic& heuristic,std::vector<int>& mismatch_tags) {
    if (!set_model_done) {
      c->set_model(heuristic.get_model());
      set_model_done=true;
    }

    if (cconst) {
      return (heuristic.getCoverage() >= c->getCoverage());
    }

    if (action) {
      c->execute(action);
    }
    return (c->getCoverage()==1.0);
  }
  Log_null l;
  Coverage* c;
  bool set_model_done;
  bool cconst;
};

class End_condition_tagverify: public End_condition {
public:
  End_condition_tagverify(Verdict::Verdict v, const std::string& p):
    End_condition(v,p) {
    counter = TAGVERIFY;
    status = true;
  }
  bool evaluate_filter(std::vector<std::string>& tags);
  bool evaluate_filter(std::vector<std::string>& tags,std::string& s);
  virtual ~End_condition_tagverify() {}
  virtual bool match(int step_count,int state, int action,int last_step_cov_growth,Heuristic& heuristic,std::vector<int>& mismatch_tags);
  std::vector<int> filter;
};

#undef FACTORY_CREATE_PARAMS
#undef FACTORY_CREATOR_PARAMS
#undef FACTORY_CREATOR_PARAMS2

#define FACTORY_CREATE_PARAMS Verdict::Verdict v,	               \
                       std::string name,                               \
                       std::string params

#define FACTORY_CREATOR_PARAMS Verdict::Verdict v, std::string params
#define FACTORY_CREATOR_PARAMS2 v, params

FACTORY_DECLARATION(End_condition)

#undef FACTORY_CREATE_PARAMS
#undef FACTORY_CREATOR_PARAMS
#undef FACTORY_CREATOR_PARAMS2

#define FACTORY_CREATE_PARAMS Log& log,                                \
                       std::string name,                               \
                       std::string params

#define FACTORY_CREATOR_PARAMS Log& log, std::string params
#define FACTORY_CREATOR_PARAMS2 log, params


End_condition* new_end_condition(Verdict::Verdict,const std::string&);

#endif
