/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2013, Intel Corporation.
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

#include "coverage_report_filter.hh"

FACTORY_CREATORS(Coverage_report_filter)
FACTORY_ADD_FACTORY(Coverage_report_filter)
FACTORY_CREATE(Coverage_report_filter)

class Coverage_report_filter_last: public Coverage_report_filter {
public:
  Coverage_report_filter_last(Log&l,std::string param): Coverage_report_filter(l,param) {
  }
  virtual ~Coverage_report_filter_last() {
  }

  virtual bool execute(int action) {
    if (sub) {
      sub->execute(action);

      if (sub->traces.size()>len) {
        traces.resize(len);
        times .resize(len);
        copy(sub->traces.end() -len ,sub->traces.end() ,traces.begin());
        copy(sub->times. end() -len ,sub->times .end() ,times. begin());
      } else {
        traces=sub->traces;
        times=sub->times;
      }
    }
    return true;
  }
};

class Coverage_report_filter_first: public Coverage_report_filter {
public:
  Coverage_report_filter_first(Log&l,std::string param):
    Coverage_report_filter(l,param)
  {
  }

  virtual ~Coverage_report_filter_first() {
  }

  virtual bool execute(int action) {
    if (sub) {
      sub->execute(action);

      if (sub->traces.size()>len) {
        traces.resize(len);
        times .resize(len);
        copy(sub->traces.begin() ,sub->traces.begin()+len ,traces.begin());
        copy(sub->times. begin() ,sub->times .begin()+len ,times. begin());
      } else {
        traces=sub->traces;
        times =sub->times ;
      }
    }
    return true;
  }
};


class Coverage_report_filter_longer: public Coverage_report_filter {
public:
  Coverage_report_filter_longer(Log&l,std::string param):
    Coverage_report_filter(l,param)
  {
  }

  virtual ~Coverage_report_filter_longer() {
  }

  virtual bool execute(int action) {
    if (sub) {
      sub->execute(action);
      traces.clear();
      times .clear();

      for(unsigned i=0;i<sub->traces.size();i++) {
        if (sub->traces[i].size()>=len) {
          traces.push_back(sub->traces[i]);
          times .push_back(sub->times [i]);
        }
      }

    }
    return true;
  }

};

class Coverage_report_filter_shorter: public Coverage_report_filter {
public:
  Coverage_report_filter_shorter(Log&l,std::string param):
    Coverage_report_filter(l,param)
  {
  }

  virtual ~Coverage_report_filter_shorter() {
  }

  virtual bool execute(int action) {
    if (sub) {
      sub->execute(action);
      traces.clear();
      times .clear();

      for(unsigned i=0;i<sub->traces.size();i++) {
        if (sub->traces[i].size()<len) {
          traces.push_back(sub->traces[i]);
          times .push_back(sub->times [i]);
        }
      }

    }
    return true;
  }

};


Coverage_report_filter* new_coveragereportfilter(Log& l, std::string& s) {
  std::string name,option;
  param_cut(s,name,option);
  Coverage_report_filter* ret=Coverage_report_filterFactory::create(l, name, option);

  if (ret) {
    return ret;
  }

  //Let's try old thing.
  split(s, name, option);
  ret=Coverage_report_filterFactory::create(l, name, option);

  if (ret) {
    fprintf(stderr,"DEPRECATED COVERAGE SYNTAX. %s\nNew syntax is %s(%s)\n",
            s.c_str(),name.c_str(),option.c_str());
  }
  return ret;
}


FACTORY_DEFAULT_CREATOR(Coverage_report_filter, Coverage_report_filter_first, "first" )
FACTORY_DEFAULT_CREATOR(Coverage_report_filter, Coverage_report_filter_last , "last"  )

FACTORY_DEFAULT_CREATOR(Coverage_report_filter, Coverage_report_filter_longer, "longer" )
FACTORY_DEFAULT_CREATOR(Coverage_report_filter, Coverage_report_filter_shorter, "shorter" )
