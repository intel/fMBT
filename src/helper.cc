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
#include <string>
#include <vector>
#include <cstdio>
#include <cstring>
#include <cstdlib>

#ifndef DROI
#include <boost/regex.hpp>
#include <glib.h>
#include <glib-object.h>
#else
#include <cctype>
#include <cstdio>
#endif

#include <string>
#include <vector>
#include <sstream>
#include <fstream>

#include <dlfcn.h>

bool human_readable=true;

void escape_free(const char* msg)
{
#ifdef DROI
  delete [] msg;
#else
  g_free((void*)msg);
#endif
}

void *load_lib(const std::string& libname,std::string& model_filename)
{
  std::string name_candidate(libname);
  std::string errormessages;

  if (model_filename!="") {
    return dlopen(model_filename.c_str(),RTLD_NOW);
  }

  void* handle=dlopen(name_candidate.c_str(),RTLD_NOW);
  if (!handle) {
    errormessages += dlerror() + std::string("\n");
    name_candidate="./"+name_candidate;
    handle=dlopen(name_candidate.c_str(),RTLD_NOW);
  }
  if (!handle) {
    errormessages += dlerror() + std::string("\n");
    name_candidate=libname+".so";
    handle=dlopen(name_candidate.c_str(),RTLD_NOW);    
  }
  if (!handle) {
    errormessages += dlerror() + std::string("\n");
    name_candidate="./"+name_candidate;
    handle=dlopen(name_candidate.c_str(),RTLD_NOW);
  }
  if (!handle) {
    errormessages += dlerror() + std::string("\n");
    name_candidate="lib"+libname+".so";
    handle=dlopen(name_candidate.c_str(),RTLD_NOW);    
  }
  if (!handle) {
    errormessages += dlerror() + std::string("\n");
    name_candidate="./"+name_candidate;
    handle=dlopen(name_candidate.c_str(),RTLD_NOW);
  }
  if (!handle) {
    fprintf(stderr, "%s", errormessages.c_str());
  }
  return handle;
}

int find(const std::vector<std::string> &v,const std::string s)
{
  for(unsigned i=0;i<v.size();i++) {
    if (v[i]==s) {
      return i;
    }
  }
  return 0;
}

bool isOutputName(const std::string& name)
{
  return (name.c_str()[0]=='o');
}

bool isInputName(const std::string& name)
{
  return (name.c_str()[0]=='i') ||
    (name.c_str()[0]=='d');
}


void clear_whitespace(std::string& s){
  std::string white (" \t\f\v\n\r"); /* more whilespace? */
  size_t pos;
  
  pos=s.find_last_not_of(white);
  if (pos==std::string::npos) {
    s.clear();
    pos=s.find_first_not_of(white);
    if (pos!=std::string::npos) {
      s=s.substr(pos);      
    }
  } else {
    s.erase(pos+1);
  }
}


void clear_coding(std::string& s){
  std::string coding ("\"");
  size_t pos;
  
  pos=s.find_last_not_of(coding);
  if (pos==std::string::npos) {
    s.clear();
  } else {
    s.erase(pos+1);
    pos=s.find_first_not_of(coding);
    if (pos!=std::string::npos) {
      s=s.substr(pos);      
    }
  }
}

std::string removehash(std::string& s);

std::string filetype(std::string& _s)
{
  std::string s=removehash(_s);
  size_t found=s.find_last_of(".");
  std::string r=s.substr(found+1);
  found=r.find_last_of("#");
  if (found==r.npos) {
    return r;
  }
  return r.substr(0,found);
}

bool isxrules(std::string& s)
{
  std::string s1(".xrules");
  return (s.substr(s.size()-s1.size())==s1);
}

char* unescape_string(char* msg)
{
  int l=std::strlen(msg);
  int j=0;

  for(int i=0;i<l;i++) {
    if (msg[i]=='%') {
      char* endp;
      char s[] = {
	msg[i+1],msg[i+2],0 };
      char c=strtol(s,&endp,16);
      if (endp!=s) {
	msg[j]=c;
	i+=2;
      } else {
	msg[j]=msg[i];
      }
    } else {
      msg[j]=msg[i];
    }
    j++;
  }
  msg[j]=0;
  
  return msg;
}

void unescape_string(std::string& msg)
{
  char* tmp=strdup(msg.c_str());
  unescape_string(tmp);

  msg=tmp;
  free(tmp);
}


char* escape_string(const char* msg)
{
#ifdef DROI
  int len=std::strlen(msg);
  char* endp=new char[3*len+1];
  char* ret=endp;
  endp[0]=0;
  
  for(int i=0;i<len;i++) {
    char c=msg[i];
    if (isalnum(c)) {
      *endp=c;
      endp++;
    } else {
      endp+=std::sprintf(endp,"%%%X",c);
    }
  }
  *endp=0;
  
  return ret;  
#else
  return g_uri_escape_string(msg,NULL,TRUE);
#endif
}

std::string removehash(std::string& s)
{
  unsigned long cutpos = s.find_last_of("#");
  if (cutpos == s.npos) {
    return s;
  } else {
    return s.substr(0,cutpos);
  }
  return "";
}

#ifndef DROI
char* readfile(const char* filename,const char* preprocess)
{
  char* out=NULL;
  int status;

  if (preprocess==NULL) {
    return readfile(filename,false);
  }

  std::string s(preprocess);

  s=s + " " + filename;
  
  if (!g_spawn_command_line_sync(s.c_str(),&out,NULL,&status,NULL)) {
    throw (int)(24);
  }
  return out;  
 }
#endif

char* readfile(const char* filename,bool preprocess)
{
  std::string fn(filename);
  unsigned long cutpos = fn.find_last_of("#");

  if (cutpos == fn.npos) {
#ifndef DROI
    if (preprocess) {
      GString *gs=g_string_new("");
      
      g_string_printf(gs,"/bin/sh -c \"cat '%s'|grep -v ^#\"",filename);

      char* out=readfile(filename,gs->str);
      //g_free(gs);

      return out;
    } else {
      char* out=NULL;
      g_file_get_contents(filename,&out,NULL,NULL);
      return out;
    }
#else
    /* read file contents always without preprocessing when glib not
     * available */
    std::ifstream f;
    int file_len;
    f.open(filename, std::fstream::in | std::fstream::ate);
    if (!f.is_open())
      return NULL;
    file_len = f.tellg();
    f.seekg(0, std::ios::beg);
    char *contents = (char*)malloc(file_len+1);
    if (!contents) {
      f.close();
      return NULL;
    }
    f.read(contents, file_len);
    f.close();
    contents[file_len] = '\0';
    return contents;

#endif
  } else {
    return unescape_string(strdup(fn.substr(cutpos+1).c_str()));
  }
}

std::string capsulate(std::string s) {

  if (s=="") {
    return "\"";
  }

  std::ostringstream t(std::ios::out | std::ios::binary);
  
  if (human_readable) {
    t << ":" << s.length() << ":" << s << "\"";
  } else {
    char* sesc=escape_string(s.c_str());
    t << "#" << sesc << "\"";
    escape_free(sesc);
  }

  return t.str();
}

void string2vector(char* s,std::vector<int>& a)
{
  int v;
  int i=0;
  char* endp;

  char* ss=s;
  v=strtol(ss,&endp,10);
  a.resize(0);
  while (endp!=ss) {
    a.push_back(v);
    ss=endp;
    v=strtol(ss,&endp,10);
    i++;
  } 
}

#ifndef DROI
std::string replace(boost::regex& expression,
		    const char* format_string,
		    std::string::iterator first,
		    std::string::iterator last)
{
  std::ostringstream t(std::ios::out | std::ios::binary);
  std::ostream_iterator<char> oi(t);
  std::string s;
  boost::regex_replace(oi,first,last,expression,format_string,
		       boost::match_default | boost::format_all
		       | boost::format_first_only);

  s=t.str();
  return s;
}

#endif

void print_vectors(int* v,unsigned size,std::vector<std::string>& s,const char* prefix,int add)
{
  for(unsigned i=0;i<size;i++) {
    if (s[v[i]]!="")
      printf("%s%i:%s\n",prefix,i+add,s[v[i]].c_str());
  }
}

void print_vector(std::vector<std::string>& s,const char* prefix,int add)
{
  for(unsigned i=0;i<s.size();i++) {
    if (s[i]!="") {
      printf("%s%i:%s\n",prefix,i+add,s[i].c_str());
    }
  }
}

std::string to_string(const float f)
{
  std::stringstream ss;
  ss << f;
  return ss.str();
}


std::string to_string(const unsigned t)
{
  std::stringstream ss;
  ss << t;
  return ss.str();
}

std::string to_string(const int t)
{
  std::stringstream ss;
  ss << t;
  return ss.str();
}

std::string to_string(const int cnt, int* t, std::vector<std::string>& st)
{
  std::string ret;
  
  if (cnt==0) {
    return ret;
  }

  ret=st[t[0]];
  
  for(int i=1;i<cnt;i++) {
    ret+=" "+st[t[i]];
  }

  return ret;
}

void strvec(std::vector<std::string>& v,std::string& s,
	    std::string& separator)
{
  unsigned long cutpos;

  while ((cutpos=s.find_first_of(separator))!=s.npos) {
    std::string a=s.substr(0,cutpos);
    v.push_back(a);
    s=s.substr(cutpos+1);
  }

  v.push_back(s);
}
