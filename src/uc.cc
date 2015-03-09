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

#include "log_null.hh"

Log* l=NULL;

#include "of.hh"
#include "of_null.hh"

#include "helper.hh"
#include <iostream>
#include <unistd.h>
#include <cstdlib>
#include "dparse.h"
#include "history_log.hh"
#include "config.h"

extern "C" {
extern D_ParserTables parser_tables_uconf;
}
extern OutputFormat* uconf_obj;

#ifndef DROI
#include <glib-object.h>
#endif

#include "error.hh"

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

extern int uconf_node_size;

int main(int argc,char * const argv[])
{
  FILE* outfile=stdout;
  char* usecasefile=NULL;
  int c;
  OutputFormat* of=NULL;

#ifndef DROI
#if !GLIB_CHECK_VERSION(2, 35, 0)
  g_type_init ();
#endif
#endif

  static struct option long_opts[] = {
    {"help", no_argument, 0, 'h'},
    {"version", no_argument, 0, 'V'},
    {0, 0, 0, 0}
  };

  while ((c = getopt_long (argc, argv, "hu:p:f:o:V", long_opts, NULL)) != -1)
    switch (c)
    {
    case 'v':
      printf("Version: "VERSION FMBTBUILDINFO"\n");
      return 0;
      break;
    case 'u':
      // Usecase file
      if (usecasefile) {
	print_usage();
	return 1;
      }
      usecasefile=optarg;
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
      std::string s1(optarg);
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

  if (of==NULL) {
    printf("of==NULL\n");
    of=new OutputFormat_Null("");
  }

  if (!of->status) {
    delete of;
    return -1;
  }

  if (usecasefile==NULL) {
    delete of;
    print_usage();
    return 5;
  }

  uconf_obj=of;

  char* s=readfile(usecasefile);
  if (!s) {
    std::printf("Can't read input file \"%s\"\n",usecasefile);
    return 3;
  }
  D_Parser *p = new_D_Parser(&parser_tables_uconf,uconf_node_size);
  p->loc.pathname = usecasefile;
  dparse(p,s,std::strlen(s));

  free(s);
  s=NULL;

  if (p->syntax_errors) {
    free_D_Parser(p);
    p=NULL;
    delete of;
    return -1;
  }
  free_D_Parser(p);
  p=NULL;

  if (optind == argc) {
    print_usage();
    error(3, 0, "No logfile?\n");
  }

  if (!of->status) {
    std::printf("Error %s\n",of->errormsg.c_str());
    return -1;
  }

  std::string o=of->header();
  fwrite(o.c_str(),1,o.size(),outfile);

  l=new Log_null();

  for (int i=optind;i<argc;i++) {
    fprintf(stderr,"Handling log %s\n",argv[i]);
    std::string s(argv[i]);
    o=of->handle_history(*l,s);

    if (!of->status) {
      return -1;
    }
    fwrite(o.c_str(),1,o.size(),outfile);
  }

  if (!of->status) {
    return -1;
  }

  o=of->footer();
  fwrite(o.c_str(),1,o.size(),outfile);

  o=of->report();
  fwrite(o.c_str(),1,o.size(),outfile);

  fflush(outfile);

  if (outfile!=stdout)
    fclose(outfile);

  delete of;
  l->unref();



  return 0;
}
