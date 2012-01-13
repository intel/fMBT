%{
#include <iostream>
#include <fstream>
#include <list>
#include <map>
#include <cstring>

std::list<YY_BUFFER_STATE> istack;
std::map<std::string,bool> def;

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
      FILE* st=fopen( s.c_str(), "r" );
      if (st) {
	istack.push_back(YY_CURRENT_BUFFER);
	yy_switch_to_buffer(yy_create_buffer( st, YY_BUF_SIZE ) );
      } else {
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
  state=IF;
  BEGIN STR;
}

^[\ \t]*"^ifndef"[\ \t]+ {
  state=IFN;
  BEGIN STR;
}

^[\ \t]*"^endif" {
  echo=true;
  state=NONE;
  BEGIN 0;
}

[^\n] {
  if (echo) 
     fprintf(yyout,"%c",  yytext[0]);
}

"\n" {
  if (echo)
     fprintf(yyout,"%c",  yytext[0]);
}

<<EOF>> {
  if (yy_hold_char!='\n') {
     fprintf(yyout,"\n");
  }
  if (istack.empty()) {
    yyterminate();
  } else {
    delete yyin;
    yy_delete_buffer( YY_CURRENT_BUFFER );
    yy_switch_to_buffer(istack.back());
    istack.pop_back();
  }
}

%%

int main(int argc,char** argv)
	{
	  if (argc==2) {
	    yyset_in(fopen(argv[1], "r" ));
	  }
	  yylex();
	  return 0;
	}

int yywrap()
{
  return 1;
}
