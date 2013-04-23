%{
#include <iostream>
#include <fstream>
#include <list>
#include <map>
#include <cstring>
#include <stack>
#include "config.h"
#include <getopt.h>

std::list<YY_BUFFER_STATE> istack;
std::list<int> lstack;
std::list<std::string> fstack;
std::map<std::string,bool> def;
int lineno=1;

using namespace std;
bool echo=true;
enum {
  NONE,
  INC,
  DEF,
  UND,
  IF,
  IFN,
  END
};

int state=NONE;
std::stack<bool> echo_stack;
%}

%Start STR

%%

^[\ \t]*"^include"[\ \t]+ {
// include
  if (echo) {
    state=INC;
    BEGIN STR;
  }
}

<STR>[^ \t\n]+ {
  if (echo) {
    switch (state) {
    case INC: {
      std::string s(yytext+1,strlen(yytext)-2);
      fprintf(yyout,"# 1 \"%s\"\x0A",s.c_str(),fstack.size()+1);
      FILE* st=fopen( s.c_str(), "r" );
      if (st) {
	istack.push_back(YY_CURRENT_BUFFER);
	lstack.push_back(lineno);
	fstack.push_back(s);
	lineno=1;
	yy_switch_to_buffer(yy_create_buffer( st, YY_BUF_SIZE ) );
      } else {
      	fprintf(stderr,"No such file \"%s\"\n",s.c_str());
	exit(-1);
      }
      break;
    }
    case DEF: {
      std::string s(yytext+1,strlen(yytext)-2);
      def[s]=true;
      break;
    }
    case UND: {
      std::string s(yytext+1,strlen(yytext)-2);
      def[s]=false;
      break;
    }
    case IF: {
      std::string s(yytext+1,strlen(yytext)-2);
      if (!def[s]) {
	echo=false;
      }
      break;
    }
    case IFN: {
      std::string s(yytext+1,strlen(yytext)-2);
      if (def[s]) {
	echo=false;
      }
      break;
    }
    }
    state=NONE;
  }
  BEGIN 0;
 }

^[\ \t]*"^define"[\ \t]+ {
  state=DEF;
  BEGIN STR;
}

^[\ \t]*"^undef"[\ \t]+ {
  state=UND;
  BEGIN STR;
}

^[\ \t]*"^ifdef"[\ \t]+ {
  echo_stack.push(echo);
  state=IF;
  BEGIN STR;
}

^[\ \t]*"^ifndef"[\ \t]+ {
  echo_stack.push(echo);
  state=IFN;
  BEGIN STR;
}

^[\ \t]*"^endif" {
  if (!echo_stack.empty()) {
    echo=echo_stack.top();
    echo_stack.pop();
  }
  state=NONE;
  BEGIN 0;
}

[^\n] {
  if (echo)
     fprintf(yyout,"%c",  yytext[0]);
}

"\n" {
  lineno++;
  if (echo)
     fprintf(yyout,"%c",  yytext[0]);
}

<<EOF>> {
  if (yy_hold_char!='\n') {
     lineno++;
     fprintf(yyout,"\n");
  }
  if (istack.empty()) {
    yyterminate();
  } else {
    yy_delete_buffer( YY_CURRENT_BUFFER );
    yy_switch_to_buffer(istack.back());
    lineno=lstack.back();
    istack.pop_back();
    lstack.pop_back();
    fstack.pop_back();
    fprintf(yyout,"# %i \"%s\"\x0A",lineno,fstack.back().c_str(),fstack.size());
  }
}

%%

void print_usage()
{
  std::printf(
    "Usage: fmbt-aalp [options] inputfile\n"
    "Options:\n"
    "    -D     define preprocessor flag\n"
    "    -h     print usage\n"
    "    -V     print version\n"
    );
}

int main(int argc,char** argv)
{
  static struct option long_opts[] = {
    {"help", no_argument, 0, 'h'},
    {"version", no_argument, 0, 'V'},
    {0, 0, 0, 0}
  };
  int c;
  while ((c = getopt_long (argc, argv, "hD:V", long_opts, NULL)) != -1) {
    switch (c)
    {
    case 'V':
      printf("Version: "VERSION"\n");
      return 0;
      break;
    case 'D':
      def[optarg] = true;
      break;
    case 'h':
      print_usage();
      return 0;
    default:
      return 2;
    }
  }

  if (optind + 1 < argc) { // too many arguments
    print_usage();
    return -1;
  }

  if (optind < argc) { // preprocessed file given on command line
    fstack.push_back(argv[optind]);
    yyset_in(fopen(argv[optind], "r" ));
  } else {
    fstack.push_back("/dev/stdin");
  }
  yylex();

  return 0;
}

int yywrap()
{
  return 1;
}
