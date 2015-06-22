%{

#include "log_null.hh"
#include "aal.hh"
#include "config.h"
#include "log_aalremote.hh"
#include "verdict.hh"
#include "helper.hh"

class aal_loader {
public:
	virtual  aal* load(std::string& name,Log&);
};

//Log_aalremote lokki;

aal* Aal;
std::vector<int> act_vect;
void print_int(int i)
{
	fprintf(stdout,"fmbtmagic %i\n",i);
	fflush(stdout);
}

void print_vec(int* v,int len)
{
	fprintf(stdout,"fmbtmagic");
	for(int i=0;i<len;i++) {
		fprintf(stdout," %i",v[i]);
	}
	fprintf(stdout,"\n");
	fflush(stdout);
}

void print_int_vec(int rv,std::vector<int>&t)
{
	fprintf(stdout,"fmbtmagic %i",rv);
	for(int i=0;i<t.size();i++) {
	       fprintf(stdout," %i",t[i]);
	}
	fprintf(stdout,"\n");
	fflush(stdout);
}

void print_string(const std::string& str) {
     std::string s(str);
     escape_string(s);
     fprintf(stdout,"fmbtmagic%s\n",str.c_str());
}

void print_vec(const std::vector<std::string>& vec)
{
  for(std::vector<std::string>::const_iterator i=(vec.begin()+1);i!=vec.end();i++) {
    print_string(*i);
  }
  fflush(stdout);
}

std::string ap;
std::vector<int> act;
%}

%Start AP
%Start AE
%Start ACT

%%

^"ma" {
	int* v;
        int len;
	len=Aal->getActions(&v);
	print_vec(v,len);
	
}
^"mu" {
	Aal->push();
}

^"mo" {
	Aal->pop();
}
^"mp" {
        int *v;
	int len;
	len=Aal->getprops(&v);
	print_vec(v,len);
}

^"aop" {
       Aal->observe(act_vect,false);
}

^"aob" {
       Aal->observe(act_vect,true);
}

^"mr" {
      print_int(Aal->reset());
      }
^"ai" {
      print_int(Aal->init());
}

^"ae" {
      BEGIN AE;
}

^"lts" {
       print_int(-1);
      // Not supported
}

^"ap" {
      // Call arguments
      BEGIN AP;
}

^"a"[0-9]* {
	   int action=atoi(yytext+1);
	   print_int(Aal->adapter_execute(action,ap.c_str()));
	   ap="";
}

^"m"[0-9]* {
	   int action=atoi(yytext+1);
	   printf("executing %i\n",action);
	   print_int(Aal->model_execute(action));
}

^"act" {
       BEGIN ACT;
       }

<ACT>[^\n] {
       std::vector<int> tag;
       std::vector<int> t;
       int ret=Aal->check_tags(tag,t);
       print_int_vec(ret,t);
}

<AP>[^\n] {
      // Call arguments
    ap=std::string(yytext,strlen(yytext));
    BEGIN 0;
}

<AE>[^\n] {
    std::string ae(yytext,strlen(yytext));	  

    size_t cutpos;
    std::string separator=",";
    if ((cutpos=ae.find_first_of(separator))!=ae.npos) {
       std::string reason=ae.substr(cutpos+1);
       Verdict::Verdict v=Verdict::new_verdict(ae.substr(0,cutpos));
       Aal->adapter_exit(v,reason);
    }
    BEGIN 0;
}

"\n" {
}

<<EOF>> {
	if (Aal) {
	   Aal->adapter_exit(Verdict::W_ERROR,"");
	}
}

%%

int main(int argc,char** argv)
{

  if (argc != 2)
    return 1;
    /*
    error(1, 0, "Invalid arguments.\n"
          "Usage: remote_aal_loader name");
*/
  Log_null l; // Incorrect log. We need log, which writes to main fmbt
	      // log. This is a temporary 'sollution'
  std::string name(argv[1]);

  aal_loader loader;

  Aal=loader.load(name,l);

  if (Aal==NULL)
    return -1;

  print_vec(Aal->getActionNames());
  print_string("");
  print_vec(Aal->getSPNames());
  print_string("");

  yylex();
  yylex_destroy();

  return 0;
}

int yywrap()
{
  return 1;
}
