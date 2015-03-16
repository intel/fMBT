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

#include "learn_time.hh"
#include "helper.hh"
#include "adapter.hh"
#include "function_export.hh"

Learn_time::Learn_time(Log&l,std::string s): Learning(l),learning_multiplier(NULL),
					     default_value(NULL) {

  std::vector<std::string> fa;
  commalist(s,fa);

  Export_double _exp("duration",&_duration);

  switch (fa.size()) {
  case 2:
    default_value=new_function(fa[1]);
    if (!default_value) {
      status=false;
      errormsg="Can't create function \""+fa[1]+"\"";
      break;
    }

  case 1:
    learning_multiplier=new_function(fa[0]);
    if (!learning_multiplier) {
      status=false;
      errormsg="Can't create function \""+fa[0]+"\"";
    }

  case 0:
    break;

  default:
    status=false;
    errormsg="Expecting 0,1 or 2 parameters. Got "+to_string((unsigned)fa.size());
  }

  if (!learning_multiplier) {
    learning_multiplier=new_function("0.5");
  }

  if (!default_value) {
    default_value=new_function("0.0");
  }
}

void Learn_time::suggest(int action) {
  suggested=true;
  last_time=Adapter::current_time;
}

float Learn_time::getE(int action) {
  float retval = time_map[action];
  if (std::isnan(retval))
    retval = default_value->fval();

  return retval;
}

void Learn_time::execute(int action) {
  struct timeval duration;
  if (suggested) {
    // called because something is suggested
  } else {
    // called because of output action?
  }
  timersub(&Adapter::current_time,&last_time,&duration);
  _duration = (duration.tv_sec+duration.tv_usec/1000000.0);
  if (std::isnan(time_map[action])) {
    time_map[action] = _duration;
  } else {
    float f=learning_multiplier->fval();
    time_map[action]=time_map[action]*(1.0-f)+f*_duration;
  }
}

FACTORY_DEFAULT_CREATOR(Learning, Learn_time, "time")
