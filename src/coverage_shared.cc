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

#include "coverage_shared.hh"

void Coverage_shared::receive_from_server()
{
  // Read number of active clients
  std::vector<std::string> tmp;

  char* s = NULL;
  char* ss;
  size_t si = 0;
  std::vector<int> clients;

  g_io_channel_flush(d_stdin,NULL);

  while(g_main_context_iteration(NULL,FALSE));

  if (getline(&s,&si,d_stdout)<0) {
    status=false;
    return;
  }

  ss=s;
  if (strlen(s)>2) {
    s[strlen(s)-2]='\0';
    s++;
  }

  if (!string2vector(log,s,clients,0,INT_MAX,this)) {
    g_free(s);
    status=false;
    return;
  }
  s=ss;

  // Read each client...
  for(unsigned i=0;i<clients.size();i++) {
    if (getline(&s,&si,d_stdout)<0) {
      status=false;
      if (s)
	g_free(s);
      return;
    }

    if (!status) {
      continue;
    }

    if (read_data) {
      
      // Prepare the 
      if (!child->set_instance(clients[i])) {
	status=false;
	continue;
      }
      
      std::string name,option;
      param_cut(std::string(s),name,option);
      std::vector<std::string> p;
      commalist(option,p);
      
      for(unsigned j=0;status&&(j<p.size());j++) {
	std::vector<std::string> at;
	param_cut(p[j],name,option);
	commalist(option,at);
	if (at.size()!=2) {
	  status=false;
	  continue;
	}
	int act=atoi(at[0].c_str());
	std::vector<int> tags;
	if (!string2vector(log,at[1].c_str(),tags,0,INT_MAX,this)) {
	  status=false;
	} else {
	  // We should pass tags...
	  model_cs->n=tags.size();
	  model_cs->pr=& tags[0];
	  child->execute(act);
	}
      }
    }
  }
  if (s)
    g_free(s);
  s=NULL;
  if (read_data) {
    child->set_instance(0);
  }
  model_cs->pr=NULL;
}

void Coverage_shared::communicate(int action)
{
  if (!status) {
    return;
  }
  if (write_data) {
    // First, send action
    int *pr;
    int n=model->getprops(&pr);
    
    if (n) {
      std::string tags;
      for(int i=0;i<n;i++) {
	if (i) {
	  tags=tags+" "+to_string(pr[i]);
	} else {
	  tags=to_string(pr[i]);
	}
      }
      fprintf(d_stdin,"(%i,%s)\n",action,tags.c_str());
    } else {
      fprintf(d_stdin,"(%i,)\n",action);
    }
  } else {
    fprintf(d_stdin,"()\n");
  }
  receive_from_server();
}

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_shared, "shared")
FACTORY_DEFAULT_CREATOR(Coverage, Coverage_shared_wo, "shared_wo")
FACTORY_DEFAULT_CREATOR(Coverage, Coverage_shared_poll, "shared_ro")
