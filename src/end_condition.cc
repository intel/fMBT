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

#include "end_condition.hh"

#include <stdlib.h>

#include <stdio.h> // DEBUG

#ifndef DROI
#include <glib.h>
#endif

#include "helper.hh"

End_condition::End_condition(Verdict::Verdict v, Counter c,const std::string& p)
  : verdict(v), counter(c), param(p),
    param_float(-1.0), param_long(-1), param_time(-1)
{
    switch (counter) {

    case STEPS:
      param_long = atol(param.c_str());
      status = true;
      break;

    case COVERAGE:
      param_float = atof(param.c_str());
      status = true;
      break;

    case STATETAG:
      // param already contains the state tag string, but it cannot be
      // converted into index (param_long) because the model is not
      // initialized
      status = true;
      break;

    case DURATION:
    {
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
      break;
    }

    case NOPROGRESS:
      param_long = atol(param.c_str());
      status = true;
      break;

    case DEADLOCK:
      status = true;
      break;
    case ACTION:
      // param already contains the action string, but it cannot be
      // converted into index (param_long) because the model is not
      // initialized
      status = true;
      break;
    } /* switch (counter) ... */    
}

End_condition::~End_condition()
{

}

int convert(std::string& s)
{
  if (s=="steps") 
    return End_condition::STEPS;

  if (s=="coverage")
    return End_condition::COVERAGE;

  if (s=="statetag" || s=="tag") 
    return End_condition::STATETAG;

  if (s=="duration")
    return End_condition::DURATION;

  if (s=="no_progress")
    return  End_condition::NOPROGRESS;

  if (s=="deadlock")
    return  End_condition::DEADLOCK;


  return -1;
}

End_condition* new_end_condition(Verdict::Verdict v,const std::string& s)
{
  End_condition* ret=NULL;
  std::string name,option;
  param_cut(s,name,option);

  int i=convert(name);

  if (i<0) {
    split(s, name, option);
    i=convert(name);
    if (i>=0) {
      fprintf(stderr,
	      "DEPRECATED END CONDITION SYNTAX. %s\nNew syntax is %s(%s)\n",
	      s.c_str(),name.c_str(),option.c_str());
    }
  }

  if (i>=0) {
    ret = new End_condition(v,(End_condition::Counter)i,option);
  }

  return ret;
}
