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

#include <stack>

#include "conf.hh"
#include "log.hh"
#include "helper.hh"
#include <iostream>
#include <unistd.h>

/*
std::string read_req() {
  
  static FILE* f=fdopen(3,"r");
  char* s=NULL;
  size_t si=0;

  getline(&s,&si,f);

  if (s==NULL || feof(f)) {
    fclose(f);
    return std::string("");
  }

  std::string ret(s);
  free(s);
  return ret;
}
*/

void print_usage()
{
  printf(
    "Usage: fmbt [options] configfile\n"
    "Options:\n"
    "    -D     enable debug output (written to the log)\n"
    "    -E     print precompiled configuration in human readable form\n"
    "    -e     print precompiled configuration in machine readable form\n"
    "    -i     start in interactive mode\n"
    "    -L<f>  write log to file f (default: standard error)\n"
    );
}

int main(int argc,char * const argv[])
{
  try {
    FILE* logfile=stderr;
    bool interactive=false;
    bool debug_enabled=false;
    bool E=false;
    int c;

    while ((c = getopt (argc, argv, "DEL:ie")) != -1)
         switch (c)
           {
	   case 'D': 
	     debug_enabled=true;
	     break;
	   case 'E':
	     human_readable=true;
	     E=true;
	     break;
	   case 'L':
	     logfile=fopen(optarg,"a");
	     if (!logfile) {
	       printf("Can't open logfile \"%s\"\n",optarg);
	       return 1;
	     }
	     break;
	   case 'i':
	     interactive=true;
	     break;
	   case 'e':
	     human_readable=false;
	     E=true;
	     break;
           default:
             return 2;
           }
 
    if (optind == argc) {
      print_usage();
      printf("test configuration file missing.\n");
      return 3;
    }
    { 
      Log log(logfile);
      Conf c(log,debug_enabled);
      std::string conffilename(argv[optind]);
      c.load(conffilename);

      if (!c.status) {
	return 4;
      }
     
      if (E) {
	printf("%s\n",c.stringify().c_str());
      } else {
	c.execute(interactive);
      }
    }
  } catch (int i) {
    print_usage();
    std::printf("catched %i\n",i);
    return 5;
  }
  
  return 0;
}
