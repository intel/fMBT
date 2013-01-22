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
#include <algorithm>

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
#include <fcntl.h>
#include <unistd.h>

#include "helper.hh"
#include "log.hh"
#include "writable.hh"

bool human_readable=true;

void escape_free(const char* msg)
{
#ifdef DROI
  delete [] msg;
#else
  g_free((void*)msg);
#endif
}

void *load_lib(const std::string& libname,const std::string& model_filename)
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

int find(const std::vector<std::string> &v,const std::string s,int def)
{
  for(unsigned i=0;i<v.size();i++) {
    if (v[i]==s) {
      return i;
    }
  }
  return def;
}

int find(const std::vector<std::string*> &v,const std::string s,int def)
{
  for(unsigned i=0;i<v.size();i++) {
    if (*v[i]==s) {
      return i;
    }
  }
  return def;
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
  } else {
    s.erase(pos+1);
    pos=s.find_first_not_of(white);
    if (pos!=std::string::npos) {
      s=s.substr(pos);
    }
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

void remove_force(std::string& s)
{
  std::string ss("");
  for(unsigned i=0;i<s.size();i++) {
    switch (s[i]) {
    case '\\': {
      break;
    }
    default: {
      ss=ss+s[i];
    }
    }
  }
  s=ss;
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

void escape_string(std::string& msg)
{
  char* s=escape_string(msg.c_str());
  msg=std::string(s);
  escape_free(s);
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
    return readfile(filename);
  }

  std::string s(preprocess);

  s=s + " " + filename;

  if (!g_spawn_command_line_sync(s.c_str(),&out,NULL,&status,NULL)) {
    throw (int)(24);
  }
  return out;
 }
#endif

char* readfile(const char* filename)
{
  std::string fn(filename);
  unsigned long cutpos = fn.find_last_of("#");

  if (cutpos == fn.npos) {
    /* read file contents always without preprocessing when glib not
     * available */
    std::ifstream f;
    size_t file_len;
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

    /* drop all lines that start with # */
    char *cleaned_up_contents = (char*)malloc(file_len+1);
    if (!cleaned_up_contents) {
        free(contents);
        return NULL;
    }
    size_t clean_pos = 0; // position in "cleaned_up_contents"
    size_t cont_pos = 0; // position in "contents"
    char prev_char = '\n';
    while (cont_pos < file_len)
    {
        if (contents[cont_pos] == '#' && prev_char == '\n') {
            // skip comment line
            while (cont_pos < file_len && contents[cont_pos] != '\n')
                cont_pos++;
            if (cont_pos < file_len) cont_pos++; // skip new line char
        } else {
            prev_char = cleaned_up_contents[clean_pos] = contents[cont_pos];
            cont_pos++;
            clean_pos++;
        }
    }
    cleaned_up_contents[clean_pos] = '\0';
    free(contents);
    return cleaned_up_contents;
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

bool string2vector(Log& log,char* s,std::vector<int>& a,
		   int min,int max,Writable* w)
{
  int v;
  int i=0;
  char* endp;

  char* ss=s;
  v=strtol(ss,&endp,10);
  a.resize(0);
  while (endp!=ss) {
    if (v<min||v>max) {
      if (w) {
	w->status=false;
	w->errormsg="out of range";
      }
      return false;
    }
    a.push_back(v);
    ss=endp;
    v=strtol(ss,&endp,10);
    i++;
  }

  if (ss[0]!='\0' && ss[0]!='\n') {
    if (w) {
      w->status=false;
      w->errormsg=std::string("Illegal character \"")+ss[0]+"\"";
    }

    char *escaped_line = escape_string(ss);
    if (escaped_line) {
      static const char* m[] = { "<remote error=\"I/O error: integer expected, got: %s\"/>\n",
				 "Remote expected integer, got \"%s\"\n"};
      log.error(m, escaped_line);
      escape_free(escaped_line);
    }
    return false;
  }

  return true;
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

#include <iomanip>

std::string to_string(const struct timeval&t,bool minutes)
{
  std::stringstream ss;
  int sec=t.tv_sec%60;
  int min=t.tv_sec/60;
  if (min>0 && minutes) {
    ss << min << "min " << sec << "." << std::setfill('0') << std::setw(6) << t.tv_usec << "s";
  } else {
    ss << t.tv_sec << "." << std::setfill('0') << std::setw(6) << t.tv_usec;
  }
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

std::string to_string(const int cnt,const int* t,
		      const std::vector<std::string>& st)
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

void nonblock(int fd)
{
  int flags = fcntl(fd, F_GETFL, 0);
  fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

void block(int fd)
{
  int flags = fcntl(fd, F_GETFL, 0);
  fcntl(fd, F_SETFL, flags & (~O_NONBLOCK));
}

/*
 * nonblock_getline reads lines from the stream. Unlike with normal
 * getline, underlying fd can be non-blocking. The function returns
 * the number of bytes copied to lineptr, or -1 on error. If full line
 * does not fit into internal read buffer (line is longer than
 * MAX_LINE_LENGTH), the contents of the buffer is returned as a
 * line.
 */

ssize_t nonblock_getline(char **lineptr, size_t *n, FILE *stream,char* &read_buf, size_t &read_buf_pos, const char delimiter)
{
    int fd = fileno(stream);
    if (!read_buf) {
        read_buf = (char*)malloc(MAX_LINE_LENGTH);
        if (!read_buf) return -2;
        read_buf_pos = 0;
    }
    for (;;) {
        /* look for line breaks in buffered string */
        char *p = (char*)memchr(read_buf, delimiter, read_buf_pos);
        /* if read buffer is full but contains no line breaks, return
           contents of the buffer */
        if (!p && read_buf_pos == MAX_LINE_LENGTH)
            p = read_buf + read_buf_pos - 1;
        if (p) {
            size_t line_length = p - read_buf + 1;
            size_t needed_space = line_length + 1; // include \0
            if (*lineptr == NULL || *n < needed_space) {
                if (*lineptr == NULL &&
                    (*lineptr = (char*)std::malloc(needed_space)) == NULL) {
                    return -1;
                } else if ((*lineptr = (char*)std::realloc(*lineptr, needed_space)) == NULL) {
                    return -1;
                }
                *n = needed_space;
            }
            memcpy(*lineptr, read_buf, line_length);
            *((*lineptr) + line_length) = '\0';
            memmove(read_buf, p + 1, read_buf_pos - (p - read_buf));
            read_buf_pos -= line_length;
            return line_length;
        }
        /* nothing found, try reading more content to the buffer */
        ssize_t bytes_read = read(fd, read_buf + read_buf_pos,
                                  MAX_LINE_LENGTH - read_buf_pos);
        if (bytes_read == -1) {
            return -1;
        }
        if (bytes_read == 0) {
            return 0;
        }
        read_buf_pos += bytes_read;
    }
}

/* non-blocking getline, filter out log entries */
ssize_t agetline(char **lineptr, size_t *n, FILE *stream,
                 char* &read_buf,size_t &read_buf_pos,Log& log)
{
  ssize_t ret;
  bool log_redirect;
  do {
    log_redirect=false;
    ret=nonblock_getline(lineptr,n,stream,
                         read_buf,read_buf_pos);
    if (ret>0) {
      if (**lineptr=='d') {
        log.debug(*lineptr+1);
        std::free(*lineptr);
        *lineptr = NULL;
        log_redirect=true;
      }
      if (**lineptr=='l' || **lineptr=='e') {
        // remote log messages must be url encoded when sent through
        // the remote adapter protocol

        if (**lineptr == 'e') {
          static const char* m[] = {"<remote msg=\"%s\">\n","%s\n"};
          log.error(m, *lineptr+1);
        } else {
          log.print("<remote msg=\"%s\"/>\n",*lineptr+1);
        }
        std::free(*lineptr);
        *lineptr = NULL;
        log_redirect=true;
      }
    }
  } while (ret>0 && log_redirect);
  return ret;
}

/* blocking getline, filter out log entries */
ssize_t bgetline(char **lineptr, size_t *n, FILE *stream, Log& log)
{
  ssize_t ret;
  bool log_redirect;
  do {
    log_redirect = false;
    ret = getdelim(lineptr, n, '\n', stream);
    if (ret && ret != -1) {
      if (**lineptr == 'l' || **lineptr=='e') {
        // remote log messages must be url encoded when sent through
        // the remote adapter protocol
        *(*lineptr + ret - 1) = '\0';
        log.print("<remote msg=\"%s\"/>\n",*lineptr+1);
        if (**lineptr == 'e')
          fprintf(stderr, "%s\n", unescape_string(*lineptr+1));
        std::free(*lineptr);
        *lineptr = NULL;
        log_redirect = true;
      }
    }
  } while (log_redirect);
  return ret;
}

int getint(FILE* out,FILE* in,Log& log,int min,int max,Writable* w)
{
  if (out) {
    fflush(out);
  }
  char* line=NULL;
  size_t n;
  int ret=-42;
  ssize_t s=bgetline(&line,&n,in,log);
  if (s && s != -1) {
    ret=atoi(line);
    if (strspn(line,"-0123456789") != s-1 || (ret == 0 && line[0] != '0')) {
      char *escaped_line = escape_string(line);
      if (escaped_line) {
        static const char* m[] = { "<remote error=\"I/O error: integer expected, got: %s\"/>\n",
                                   "Remote expected integer, got \"%s\"\n"};
        log.error(m, escaped_line);
        escape_free(escaped_line);
	if (w) {
	  w->status=false;
	  w->errormsg="Remote expected integer, got \""+std::string(line)+"\"";
	}
      }
      ret=-42;
    }
  } else {
    static const char* m[] = { "<remote error=\"I/O error: integer expected, got nothing.\"/>\n",
                              "Remote expected integer, got nothing\n"};
    log.error(m);
    if (w) {
      w->status=false;
      w->errormsg="Remote expected integer, got nothing";
    }
  }
  if (line) {
    free(line);
  }

  if (w && (ret<min || ret>max)) {
    w->status=false;
    w->errormsg="Value out of range";
  }

  return ret;
}

int getact(int** act,std::vector<int>& vec,FILE* out,FILE* in,Log& log,
	   int min,int max,Writable* w)
{
  fflush(out);
  vec.resize(0);
  char* line=NULL;
  size_t n;
  int ret=-1;
  size_t s=bgetline(&line,&n,in,log);
  if (s != (size_t)-1 && s > 0 && line) {
    if (strspn(line, " -0123456789") != s-1) {
      char *escaped_line = escape_string(line);
      if (escaped_line) {
        static const char* m[] = {
          "<remote error=\"I/O error: list of actions expected, got: %s\"/>\n",
          "Remote expected list of actions (integers), got \"%s\"\n"};
        log.error(m, escaped_line);
        escape_free(escaped_line);
      }
    } else {
      string2vector(log,line,vec,min,max,w);
      if (act)
        *act = &vec[0];
      ret=vec.size();
    }
  }
  if (line) {
    free(line);
  }

  return ret;
}

void split(std::string val,std::string& name,
                 std::string& param, const char* s)
{
  unsigned long cutpos = val.find_first_of(s);

  if (cutpos == val.npos) {
    name  = val;
    param = std::string("");
  } else {
    name  = val.substr(0,cutpos);
    param = val.substr(cutpos+1);
  }
}

#ifndef DROI
#include <boost/regex.hpp>
#endif


void regexpmatch(const std::string& regexp,std::vector<std::string>& f,
                 std::vector<int>& result,bool clear,int a)
{
#ifndef DROI
  if (clear) {
    result.clear();
  }
  try {
    boost::regex expression(regexp);
    boost::cmatch what;
        
    for(unsigned int i=0;i<f.size();i++) {
      if (regexp == f[i] || boost::regex_match(f[i].c_str(), what, expression)) {
	result.push_back(a*i);
      }
    }
  } catch (...) {
    printf("Exception...\n");
    for(unsigned int i=0;i<f.size();i++) {
      if (regexp == f[i]) {
	result.push_back(a*i);
      }
    }
  }

#endif
}

int last(std::string& val,char c)
{
  int pos=val.length();
  for(;pos>0;pos--) {
    if (val[pos]==c && val[pos-1]!='\\') {
      return pos;
    }
  }
  return -1;
}

void param_cut(std::string val,std::string& name,
               std::string& option)
{
  unsigned pos=0;
  for(;pos<val.length();pos++) {
    switch (val[pos]) {
    case '\\': {
      pos++;
      break;
    }
    case '(':
      int lstpos = last(val,')');
      if (lstpos>0) {
        name = val.substr(0,pos);
        remove_force(name);
        option = val.substr(pos+1,lstpos-pos-1);
        //remove_force(option);
      } else {
        // ERROR
      }
      return;
      break;
    }
  }
  name=val;
}

void commalist(const std::string& s,std::vector<std::string>& vec, bool remove_whitespace) {
  int depth=0;
  int lastend=0;
  std::string pushme;
  unsigned pos=0;
  for(;pos<s.length();pos++) {
    switch (s[pos]) {
    case '\\':
      pos++;
      break;
    case '(':
      depth++;
      break;
    case ')':
      depth--;
      break;
    case ',':
      if (depth==0) {
        // COMMA!
        pushme=s.substr(lastend,pos-lastend);
        remove_force(pushme);
        vec.push_back(pushme);
        lastend=pos+1;
      }
      break;
    }
  }
  pushme=s.substr(lastend,pos);
  vec.push_back(pushme);

  if (remove_whitespace) {
    for_each(vec.begin(),vec.end(),clear_whitespace);
  }

}

void sdel(std::vector<std::string*>* strvec)
{
    for(unsigned i=0;i<strvec->size();i++) {
        delete (*strvec)[i];
    }
    delete strvec;
}

void gettime(struct timeval *tv)
{
  struct timespec tp;
  clock_gettime(CLOCK_REALTIME,&tp);
  TIMESPEC_TO_TIMEVAL(tv,&tp);
}
