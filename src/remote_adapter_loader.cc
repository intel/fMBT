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
#include <stdio.h>
    
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <error.h>

#include <string.h>
#include <unistd.h>
#include <stdlib.h>

#include <stdio.h>

#include <string>
#include <vector>
#include "log_null.hh"
#include "adapter.hh"

int main(int argc,char** argv)
{
  int actions_size=0;
  char* s=NULL;
  size_t si=0;
  std::vector<std::string> anames;

  if (argc < 3)
    error(1, 0, "Invalid arguments.\n"
          "Usage: remote_adapter_loader adapter args");

  /* read number of all actions */
  if (getline(&s,&si,stdin) <= 1)
    error(2, 0, "Reading number of actions failed.");
  if ((actions_size=atoi(s)) < 1)
    error(3, 0, "Invalid number of actions.");
  free(s);

  /* read all actions */
  for(int i=0;i<actions_size;i++) {
    s=NULL;
    if (getline(&s,&si,stdin) < 0) {
      error(3, 0, "Reading list of actions failed.");
    }
    if (s[strlen(s)-1]=='\n') {
      s[strlen(s)-1]='\0';
    }
    anames.push_back(std::string(s));
    free(s);
  }

  /* create local adapter */
  Log_null l;
  Adapter* adapter = AdapterFactory::create(argv[1], anames, argv[2], l);
  if (adapter == NULL)
    error(10, 0, "Creating adapter \"%s:%s\" failed.", argv[1], argv[2]);
  s=NULL;
  if (!adapter->init())
    error(11, 0, "Initialising adapter \"%s:%s\" failed.", argv[1], argv[2]);

  /* adapter protocol loop: read suggested actions from stdin, report
     results to stderr, report asynchrous events to stdout. */
  while(!ferror(stdin)) {
    std::vector<int> action;
    while (adapter->readAction(action)) {
      for(unsigned i=0;i<action.size();i++) {
        fprintf(stdout, "%i ",action[i]);
      }
      fprintf(stdout, "\n");
      fflush(stdout);
    }
    if (getline(&s,&si,stdin)>1) {
      action.resize(1);
      action[0]=atoi(s);
      if (action[0]<1) {
	return 0;
      }
      if (action[0]>=actions_size) {
	fprintf(stderr,"-1\n");
        error(20, 0, "Execution of action number %d suggested (max. %d).",
              action[0], actions_size - 1);
      }
      adapter->execute(action);
      fprintf(stderr,"%i\n",action[0]);
    }
  }
  
  return 0;
}
