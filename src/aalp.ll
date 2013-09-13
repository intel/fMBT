%{
#include <iostream>
#include <fstream>
#include <list>
#include <map>
#include <cstring>
#include <stack>
#include "config.h"
#include <getopt.h>
#include <string>
#include <vector>

#include <libgen.h> // dirname
#include <glib.h>

std::list<std::string> include_path;
std::list<YY_BUFFER_STATE> istack;
std::list<int> lstack;
std::list<std::string> fstack;
std::map<std::string,bool> def;
int lineno=1;
char* inc_prefix=NULL;
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

void clear_whitespace(std::string& s){
  std::string white (" \t\f\v\n\r"); /* more whilespace? */
  size_t pos;

  pos=s.find_last_not_of(white);
  if (pos==std::string::npos) {
    s.clear();
  } else {
    s.erase(pos+1);
    pos=s.find_first_not_of(white);
    if (pos!=std::string::npos) {
      s=s.substr(pos);
    }
  }
}

bool inc_split(std::string& s) {
  bool ret=true;
  size_t pos;
  pos=s.find_last_not_of("\"");
  if (pos!=std::string::npos) {
    s.erase(pos+1);
    pos=s.find_first_of("\"");
    if (pos!=std::string::npos) {
      std::string def_str;
      if (pos>1)
	def_str=s.substr(0,pos-1);
      s=s.substr(pos+1);
      clear_whitespace(def_str);
      if (!def_str.empty()) {
	ret=def[def_str];
      }
    }
  }

  return ret;
}

FILE* _include_search_open(std::string& f)
{
  FILE* st=fopen(f.c_str(), "r" );
  if (st) {
    return st;
  }

  if (inc_prefix) {
    std::string s(inc_prefix);
    s=s+"/"+f;
    st=fopen(f.c_str(), "r" );
    if (st) {
      f=s;
      return st;
    }
  }

  for(std::list<std::string>::iterator i=include_path.begin();
      i!=include_path.end();i++) {
    char* fname = g_build_filename(i->c_str(),f.c_str(),NULL);
    std::string s(fname);
    g_free(fname);
    st=fopen(s.c_str(), "r" );
    if (st) {
      f=s;
      return st;
    }
    if (inc_prefix) {
      fname = g_build_filename(inc_prefix,s.c_str(),NULL);
      s=std::string(fname);
      g_free(fname);
      st=fopen(s.c_str(), "r" );
      if (st) {
	f=s;
	return st;
      }
    }
  }

  return st;
}

FILE* include_search_open(std::string& f) {
  FILE* st=_include_search_open(f);
  if (st) {
    char* tmp=strdup(f.c_str());
    char* dname=dirname(tmp);
    free(tmp);
    std::string ss(dname);
    include_path.push_back(ss);
  }
  return st;
}

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

<STR>[^\n]+ {
  if (echo) {
    std::string s(yytext,strlen(yytext));
    clear_whitespace(s);
    switch (state) {
    case INC: {
      if (inc_split(s)) {
	FILE* st=include_search_open(s);
	fprintf(yyout,"# 1 \"%s\"\x0A",s.c_str(),fstack.size()+1);
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
      }
      break;
    }
    case DEF: {
      def[s]=true;
      break;
    }
    case UND: {
      def[s]=false;
      break;
    }
    case IF: {
      if (!def[s]) {
	echo=false;
      }
      break;
    }
    case IFN: {
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
    include_path.pop_back();
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
    "    -I     include path"
    "    -V     print version\n"
    );
}

void strvec(std::vector<std::string>& v,std::string& s,
            const std::string& separator)
{
  unsigned long cutpos;

  while ((cutpos=s.find_first_of(separator))!=s.npos) {
    std::string a=s.substr(0,cutpos);
    v.push_back(a);
    s=s.substr(cutpos+1);
  }

  v.push_back(s);
}

void include_path_append(const char* path) {
  if (path) {
    std::vector<std::string> vec;
    std::string s(path);
    strvec(vec,s,":");
    for(unsigned i=0;i<vec.size();i++) {
      include_path.push_back(vec[i]);
    }
  }
}

int main(int argc,char** argv)
{
  static struct option long_opts[] = {
    {"help", no_argument, 0, 'h'},
    {"version", no_argument, 0, 'V'},
    {0, 0, 0, 0}
  };
  int c;
  include_path.push_back("");
  while ((c = getopt_long (argc, argv, "hD:VI:", long_opts, NULL)) != -1) {
    switch (c)
    {
    case 'I': {
      std::string s(optarg);
      include_path.push_back(s);
      break;
    }
    case 'V':
      printf("Version: "VERSION FMBTBUILDINFO"\n");
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

  include_path_append(getenv("AAL_INCLUDE_PATH"));
  inc_prefix=getenv("AAL_INCLUDE_PREFIX");

  if (optind < argc) { // preprocessed file given on command line
    std::string filename(argv[optind]);
    FILE* st=include_search_open(filename);
    if (!st) {
      fprintf(stderr,"Can't open input file %s\n",argv[optind]);
      return -1;
    }
    yyset_in(st);
    if (!inc_prefix) {
    }
    fstack.push_back(filename.c_str());
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
