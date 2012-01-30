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
#include <cstdlib>

#include "verdict.hh"

#ifndef DROI
#include <error.h>
#else
void error(int exitval, int dontcare, const char* format, ...)
{
  va_list ap;
  fprintf(stderr, "fMBT error: ");
  va_start(ap, format);
  vfprintf(stderr, format, ap);
  va_end(ap);
  exit(exitval);
}
#endif

#include <cstdio>
#include <getopt.h>

void print_usage()
{
  std::printf(
    "Usage: fmbt [options] configfile\n"
    "Options:\n"
    "    -D     enable debug output (written to the log)\n"
    "    -E     print precompiled configuration in human readable form\n"
    "    -e     print precompiled configuration in machine readable form\n"
    "    -h     help\n"
    "    -i     start in interactive mode\n"
    "    -L<f>  append log to file f (default: standard output)\n"
    "    -l<f>  overwrite log to file f (default: standard output)\n"
    "    -q     quiet, do not print test verdict\n"
    );
}

int main(int argc,char * const argv[])
{
  FILE* logfile=stdout;
  bool interactive=false;
  bool debug_enabled=false;
  bool E=false;
  bool quiet=false;
  int c;

  static struct option long_opts[] = {
    {"help", no_argument, 0, 'h'},
    {0, 0, 0, 0}
  };

  while ((c = getopt_long (argc, argv, "DEL:heil:q", long_opts, NULL)) != -1)
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
    case 'l':
      if (logfile!=stdout) {
        std::printf("Only one logfile\n");
        return 3;
      }
      logfile=fopen(optarg,c=='L'?"a":"w");
      if (!logfile) {
        std::printf("Can't open logfile \"%s\"\n",optarg);
        return 1;
      }
      break;
    case 'e':
      human_readable=false;
      E=true;
      break;
    case 'i':
      interactive=true;
      break;
    case 'q':
      quiet=true;
      break;
    case 'h':
      print_usage();
      return 0;
    default:
      return 2;
    }
 
  if (optind == argc) {
    print_usage();
    error(3, 0, "test configuration file missing.\n");
  }
  { 
    Log log(logfile);
    Conf c(log,debug_enabled);
    std::string conffilename(argv[optind]);
    c.load(conffilename);

    if (!c.status)
      error(4, 0, "%s\n", c.stringify().c_str());
     
    if (E) {
      std::printf("%s\n",c.stringify().c_str());
    } else {
      Verdict::Verdict v = c.execute(interactive);
      if (!c.status) {
        std::printf("%s\n",c.stringify().c_str());
      } else if (!quiet && v != Verdict::UNDEFINED) {
        std::printf("%s\n",c.errormsg.c_str());
      }
      return c.exit_status;
    }
  }

  return 0;
}
