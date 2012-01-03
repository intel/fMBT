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

#include "dparse.h"
#include "helper.hh"
#include <getopt.h>
#include <glib.h>
#include <errno.h>

#include <sys/types.h>
#include <sys/wait.h>

#include <unistd.h>
#include <fcntl.h>

#include "aalang.hh"

extern "C" {
extern D_ParserTables parser_tables_lang;
}

void block(int fd)
{
  int flags = fcntl(fd, F_GETFL, 0);
  fcntl(fd, F_SETFL, flags & (~O_NONBLOCK));
}

void nonblock(int fd)
{
  int flags = fcntl(fd, F_GETFL, 0);
  fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

void print_usage()
{
  std::printf(
    "Usage: fmbt-aalc [options] inputfile\n"
    "Options:\n"
    "    -h     print usage\n"
    "    -o     output to a file (defaults to stdout)\n"
    "    -c     compile (needs to have output file)\n"
    "    -D     define preprocessor flag\n"
    );
}

std::vector<std::string> prep;
std::string pstr;
extern std::string result;
extern aalang* obj;
std::string compile_command("g++ -fPIC -shared -x c++  - -I /usr/include/fmbt -o ");

int main(int argc,char** argv) {
  int c;
  bool lib=false;
  FILE* outputfile=stdout;
  static struct option long_opts[] = {
    {"help", no_argument, 0, 'h'},
    {0, 0, 0, 0}
  };

  while ((c = getopt_long (argc, argv, "b:hco:D:", long_opts, NULL)) != -1) {
    switch (c)
      {
      case 'b':
	compile_command=optarg;
	compile_command+=" ";
	break;
      case 'c':
	lib=true;
	break;
      case 'D':
	prep.push_back(optarg);
	pstr=pstr+" -D"+optarg+" ";
	break;
      case 'o':
	outputfile=fopen(optarg,"w");
	compile_command=compile_command+optarg;
	if (!outputfile) {
	  std::printf("Can't open output file \"%s\"\n",optarg);
	  return 1;
	}
	break;
      case 'h':
	print_usage();
	return 0;
      default:
	return 2;
      }
  }

  if (optind == argc || (lib && outputfile==stdout)) {
    print_usage();
    return -1;
  }

  char *s;
  D_Parser *p = new_D_Parser(&parser_tables_lang, 5120);

  p->loc.pathname = argv[optind];
  s=readfile(argv[optind],false);
  if (!s) {
    std::printf("Can't read input file \"%s\"\n",argv[optind]);
    return 3;
  }
  dparse(p,s,std::strlen(s));
  if (!obj) {
    fprintf(stderr,"Failure...\n");
    return 4;
  }

  result=obj->stringify();

  if (lib) {
    int _stdin,_stdout;//,_stder;
    GPid pid;
    int argc;
    char b[512];
    gchar **argv=(gchar**)malloc(42*sizeof(gchar*));
    GError *gerr=NULL;

    compile_command+=pstr;

    g_shell_parse_argv(compile_command.c_str(),
		       &argc,&argv,&gerr);

    g_spawn_async_with_pipes(NULL,argv,NULL,G_SPAWN_SEARCH_PATH,NULL,&pid,NULL,&_stdin,&_stdout,NULL,&gerr);

    nonblock(_stdout);

    unsigned int pos=0;
    unsigned int wrote=0;
    do {
      size_t ignore;
      wrote=TEMP_FAILURE_RETRY(write(_stdin,result.c_str()+pos,result.length()-pos));
      pos+=wrote;
      ignore=read(_stdout,b,512);
    } while (wrote>0 && pos<result.length());
    close(_stdin);
    block(_stdout);

    while(read(_stdout,b,512)) {}

  } else {
    fprintf(outputfile,"%s",result.c_str());
  }

  free_D_Parser(p);
  free(s);
  return 0;
}
