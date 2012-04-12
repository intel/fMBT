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

#include "history_remote.hh"
#include <glib.h>
#include "helper.hh"
#include "conf.hh"

History_remote::History_remote(Log& l, std::string params) :
  History(l,params)
{
  cmd=params;
}

void History_remote::set_coverage(Coverage* cov,
				  Alphabet* alpha)
{
  a=alpha;
  c=cov;

  gchar* stdout=NULL;
  gchar* stderr=NULL;
  gint   exit_status=0;
  GError *ger=NULL;

  g_spawn_command_line_sync(cmd.c_str(),&stdout,&stderr,
			    &exit_status,&ger);

  /* Let's iterate over the actions and state props */

  std::vector<std::string> vec;
  std::string s(stdout);
  std::string separator("\n");
  strvec(vec,s,separator);

  for(unsigned i=0;i<vec.size();i++) {
    std::string act;
    std::string tmp;
    std::string separator(" ");
    std::vector<std::string> props;
    
    split(vec[i],act,tmp);
    unescape_string(act);

    strvec(props,tmp,separator);
    for(unsigned j=0;j<props.size();j++) {
      unescape_string(props[j]);
    }
    send_action(act,props);
  }
}

bool History_remote::send_action(std::string& act,
				 std::vector<std::string>& props)
{
  std::vector<int> p;

  if (c&&a) {
    if (act=="pass") {
      c->history(0,p,Verdict::PASS);
      return true;
    } 

    if (act=="fail") {
      c->history(0,p,Verdict::FAIL);
      return true;
    }

    if (act=="inconclusive") {
      c->history(0,p,Verdict::INCONCLUSIVE);
      return true;
    }

    if (act=="error") {
      c->history(0,p,Verdict::ERROR);
      return true;
    }

    if (act=="undefined") {
      c->history(0,p,Verdict::UNDEFINED);
      return true;
    }
    
    int action=find(a->getActionNames(),act);

    if (action>0) {

      for(unsigned i=0;i<props.size();i++) {
	p.push_back(find(a->getSPNames(),props[i]));
      }

      c->history(action,p,Verdict::UNDEFINED);
      return true;
    } else {
      // Tau?
    }
  }

  return false;
}

FACTORY_DEFAULT_CREATOR(History, History_remote, "remote")
