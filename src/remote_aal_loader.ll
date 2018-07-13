%{
#include <set>
#include <vector>
#include <map>
#include <sstream>
#include <cstring>
#define DROI
#include "log_null.hh"
#include "aal.hh"
#include "config.h"
#include "log_aalremote.hh"
#include "verdict.hh"

class aal_loader {
public:
	virtual  aal* load(std::string& name,Log&);
};
void print_lts(const std::string& str);

Log_aalremote lokki;

aal* Aal;
std::vector<int> act_vect;
bool nomagic=false;
int state_cnt=0;
// Map source to map which maps action to destination state
std::map<int,std::map<int,int> > lts;
// map[state][prop]
std::map<int,std::set<int> > props;
void lts_generator(int depth,int current_state)
{
  int* current_props;
  int prop_len = Aal->getprops(&current_props);

  for(int i=0;i<prop_len;i++) {
    props[current_props[i]].insert(current_state);
  }

  if (depth==0)
    return;

  int* v;
  int len;
  len=Aal->getActions(&v);
  if (len==0)
    return;
  std::vector<int> actions(v,v+len);

  for(int i=0;i<len;i++) {
    Aal->push();
    Aal->model_execute(actions[i]);
    Aal->push();
    int dest_state = Aal->lts_save_state(false);
    if (dest_state>state_cnt)
      state_cnt=dest_state;
    Aal->pop();
    lts[current_state][actions[i]]=dest_state;
    lts_generator(depth-1,dest_state);
    Aal->pop();
  }  
}

void generate_lts(int initial_state,int depth)
{
    std::vector<std::string> anames=Aal->getActionNames();
    std::vector<std::string> spnames=Aal->getSPNames();
    int transition_cnt=0;

    // We could generate lts!
    // Let's try that. Now we have saved our 'initial' state.
    lts_generator(depth,initial_state); // Hardcoded lts depth :)

    std::map<int,std::map<int,int> >::iterator i1;
    std::map<int,int>               ::iterator i2;
    for(i1=lts.begin();i1!=lts.end();i1++) {
      transition_cnt+=i1->second.size();
    }

    std::ostringstream t(std::ios::out | std::ios::binary);

    t << "Begin Lsts\nBegin Header\n";
    t << "State_cnt = "      << state_cnt      << std::endl;
    t << "Action_cnt = "     << anames.size()-1 << std::endl;
    t << "Transition_cnt = " << transition_cnt << std::endl;
    if (spnames.size()>1) {
      t << "State_prop_cnt = " << spnames.size()-1 << std::endl;
    }
    
    t << "Initial_states = " << initial_state;
    t << ";\nEnd Header\n";
    
    t << "Begin Action_names\n";
    for(int i=1;i<anames.size();i++) {
      t << i << " = \"" << anames[i] << "\"\n";      
    }
    t << "End Action_names\n";

    if (spnames.size()>1) {
      t << "Begin State_props" << std::endl;

      for(int i=1;i<spnames.size();i++) {
        t << "\"" << spnames[i] << "\" : ";
	bool c;
	for(std::set<int>::iterator j=props[i].begin();
	    j!=props[i].end();j++) {
	  if (c) {
	    t << " ";
	  }
	  t << *j;
	  c=true;
	}
	t << ";" << std::endl;
      }
      t << "End State_props" << std::endl;
    }

    t << "Begin Transitions\n";
    for(i1=lts.begin();i1!=lts.end();i1++) {
      t << " " << i1->first << ":";
      for(i2=i1->second.begin();i2!=i1->second.end();i2++) {
	t << " " << i2->second << "," << i2->first;
      }
      t << ";" << std::endl;	
    }
    t << "End Transitions\n";

    t << "End Lsts\n";
    lts.clear();
    props.clear();    
    print_lts(t.str());
}
 
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

void print_lts(const std::string& str) {
        if (nomagic) {
	        fprintf(stdout,"%s\n",str.c_str());
	} else {
	        fprintf(stdout,"fmbtmagic %i\n%s",(int)str.size(),str.c_str());
		fflush(stdout);
	}
}
 

void print_string(const std::string& str) {
     std::string s(str);
     escape_string(s);
     fprintf(stdout,"fmbtmagic %s\n",str.c_str());
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

^"lts"[0-9]* {
  Aal->push();
  int initial_state=Aal->lts_save_state(true);
  if (initial_state==0) {
    initial_state=Aal->lts_save_state(false);
    state_cnt=initial_state;
    if (initial_state>0) {
      generate_lts(initial_state,atoi(yytext+3));
      Aal->lts_save_state(true);
      Aal->pop();
    } else {
      print_int(-1);
      // Not supported
      Aal->pop();
    }
  } else {
    print_int(-1);
    // Not supported
    Aal->pop();
  }
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
	return -1;
}

%%

int main(int argc,char** argv)
{
  
  if (argc != 2 && argc != 3)
    return 1;

  std::string name(argv[1]);

  aal_loader loader;

  Aal=loader.load(name,lokki);

  if (Aal==NULL)
    return 2;

  if (argc==3) {
    nomagic=true;
    Aal->reset();

    Aal->push();
    int initial_state=Aal->lts_save_state(true);
    if (initial_state!=0) {
      return 3;
    }
    initial_state=Aal->lts_save_state(false);
    if (initial_state>0) {
      state_cnt=initial_state;
      generate_lts(initial_state,atoi(argv[2]));
    } else {
      return 4;
    }
  } else {
    print_vec(Aal->getActionNames());
    print_string("");
    print_vec(Aal->getSPNames());
    print_string("");
    fflush(stdout);
    
    yyin = stdin;
    yy_set_interactive(true);
    yylex();
    yylex_destroy();
  }
  return 0;
}

int yywrap()
{
  return 1;
}
