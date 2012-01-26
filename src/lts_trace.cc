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
#include "lts_trace.hh"
#include "helper.hh"
#include "factory.hh"
#include <glib.h>
#include <string.h>
#include <stdlib.h>

bool Lts_trace::init()
{
  std::string& name = params;
  std::string model("trace.lts#");
  gchar* stdout=NULL;
  gchar* stderr=NULL;
  gint   exit_status=0;
  GError *ger=NULL;
  bool ret;
  std::string cmd("fmbt-log -f $sn:\"$as\" ");
  cmd+=(name.c_str()+strlen("lts_trace#"));
  g_spawn_command_line_sync(cmd.c_str(),&stdout,&stderr,
			    &exit_status,&ger);
  if (!stdout) {
    errormsg = std::string("Lts_trace cannot execute \"") + cmd + "\"";
    status = false;
    ret = false;
  } else {
    std::string m=trace2model(stdout);
    model+=m;
    if (exit_status || m=="") {
      ret=false;
    } else {
      ret=Lts::init();
    }
    g_free(stdout);
    g_free(stderr);
    g_free(ger);
  }
  return ret;
}

std::string Lts_trace::trace2model(char* str)
{
  std::string ret;
  int state_cnt=1;
  std::map<std::string,int> anames;
  int cnt;
  int prev_cnt=0;
  std::vector<int> tr;
  bool c=true;
  char* s=str;
  printf("Log %s\n\n",str);
  do {
    char* end;
    cnt=-1;
    cnt=strtol(s,&end,10);
    if (cnt>prev_cnt&&*end==':') {
      s=end+1;
      end=strchr(s,'\n');
      std::string tmp(s,end-s);
      if (tmp!="") {
	s=end+1;
	if (!anames[tmp]) {
	  anames[tmp]=anames.size();
	}
	int action=anames[tmp];
	tr.push_back(action);
	state_cnt++;
      }
    } else {
      c=false;
    }
    prev_cnt=cnt;
  } while (c && *s);
  ret=std::string("Begin Lsts\nBegin History\nEnd History\nBegin Header\n");
  
  ret+="\n State_cnt = "+to_string(state_cnt);
  ret+="\n Action_cnt = "+to_string(anames.size());
  ret+="\n Transition_cnt = "+to_string(state_cnt-1);
  ret+="\n State_prop_cnt = 0";
  ret+="\n Initial_states = 1;";

  ret+="\nBegin Action_names\n";

  for(std::map<std::string,int>::iterator i=anames.begin();i!=anames.end();i++) {
    ret+=" " + to_string(i->second) + " = \""+i->first.c_str()+"\"\n";
  }
  ret+="End Action_names\n";
  ret+="Begin Transitions\n";

  for(unsigned i=0;i<tr.size();i++) {
    ret+=to_string(i+1)+": "+to_string(i+2)+","+to_string(tr[i])
      +";\n";
  }
  ret+="End Transitions\n";
  ret+="End Lsts\n";
  printf("%s\n",ret.c_str());
  return ret;
}

FACTORY_DEFAULT_CREATOR(Model, Lts_trace, "lts_trace")
