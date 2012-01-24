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

#include "of.hh"

#include "helper.hh"
#include <iostream>
#include <unistd.h>
#include <cstdlib>

#ifndef DROI
#include <error.h>
#else
void error(int exitval, int dontcare, const char* format, ...)
{
  va_list ap;
  fprintf(stderr, "fMBT error: ");
  va_start (ap, format);
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
    "Usage: fmbt-ucheck [options] logfile(s)\n"
    "Options:\n"
    "    -u<f>      specify usecase file\n"
    "    -p<prefix> specifies prefix to be printed into the testrun field\n"
    "    -f<fmt>    output format\n"
    "    -o<f>      output filename (defaults to standard output)\n"
    );
}

int main(int argc,char * const argv[])
{
  FILE* outfile=stdout;
  bool debug_enabled=false;
  int c;
  OutputFormat* of=NULL;

  static struct option long_opts[] = {
    {"help", no_argument, 0, 'h'},
    {0, 0, 0, 0}
  };

  while ((c = getopt_long (argc, argv, "hu:p:f:o:", long_opts, NULL)) != -1)
    switch (c)
    {
    case 'D': 
      debug_enabled=true;
      break;
    case 'u':
      // Usecase file

      break;
    case 'p':
      // prefix
      break;
    case 'f': {
      // output format
      if (of) {
	print_usage();
	return 1;
      }
      std::string s1;
      std::string s2;
      of=OutputFormatFactory::create(s1,s2);
    }
      break;
    case 'o':
      // outputfile
      if (outfile!=stdout) {
	print_usage();
	return 2;
      }
      outfile=fopen(optarg,"w");
      if (!outfile) {
	std::printf("Can't open outputfile \"%s\"\n",optarg);
	return 3;
      }
      break;
    case 'h':
      print_usage();
      return 0;
    default:
      return 4;
    }
 
  if (optind == argc) {
    print_usage();
    error(3, 0, "test configuration file missing.\n");
  }
  { 

  }

  return 0;
}
