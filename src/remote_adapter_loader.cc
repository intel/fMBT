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

  getline(&s,&si,stdin);
  actions_size=atoi(s);
  
  free(s);

  for(int i=0;i<actions_size;i++) {
    s=NULL;
    
    getline(&s,&si,stdin);
    if (s[strlen(s)-1]=='\n') {
      s[strlen(s)-1]='\0';
    }
    anames.push_back(std::string(s));
    free(s);
  }

  Log_null l;
  Adapter* adapter=Adapter::create(argv[1],anames,argv[2],l);
  s=NULL;
  adapter->init();

  while(!ferror(stdin)) {
    std::vector<int> action;
    while (adapter->readAction(action)) {
      for(unsigned i=0;i<action.size();i++) {
	printf("%i ",action[i]);
      }
      printf("\n");
    }
    if (getline(&s,&si,stdin)>1) {
      action.resize(1);
      action[0]=atoi(s);
      if (action[0]<1) {
	return 0;
      }
      if (action[0]>=actions_size) {
	fprintf(stderr,"-1\n");
	return -1;
      }
      adapter->execute(action);
      fprintf(stderr,"%i\n",action[0]);
    }
  }
  
  return 0;
}
