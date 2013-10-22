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

#include <boost/regex.hpp>
#include <glib.h>
#include <glib-object.h>
#include <glib/gprintf.h>

#include <string>
#include <vector>
#include <sstream>
#include <fstream>

#ifndef __MINGW32__
#include <dlfcn.h>
#else
#include <windows.h>
extern "C" {

// For Dparse
char *strndup(const char *s, size_t n)
{
  return g_strndup(s,n);
}
}
#endif
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
#ifndef __MINGW32__
  std::string name_candidate(libname);
  std::string errormessages;

  if (model_filename!="") {
    return dlopen(model_filename.c_str(),RTLD_NOW);
  }

  // clear error..
  dlerror();
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
  // clear error..
  dlerror();
  return handle;
#else
  return NULL;
#endif
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

std::string removehash(const std::string& s);

std::string filetype(const std::string& _s)
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
    if (msg[i]=='%' && i+2<l) {
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

std::string removehash(const std::string& s)
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
  int status;
  return readfile(filename,preprocess,status);
}

char* readfile(const char* filename,const char* preprocess,int& status)
{
  char* out=NULL;

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

char* _readfile(const char* filename)
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
	    cleaned_up_contents[clean_pos] = '\n';
	    clean_pos++;
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

char* readfile(const char* filename) {
  char* ret=_readfile(filename);
  if (!ret) {
    const char* prefix=g_getenv("AAL_INCLUDE_PREFIX");
    if (prefix) {
      gchar* fname = g_build_filename(prefix,filename,NULL);
      ret=_readfile(fname);
      g_free(fname);
    }
  }
  return ret;
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

bool string2vector(Log& log,const char* s,std::vector<int>& a,
		   int min,int max,Writable* w)
{
  int v;
  int i=0;
  char* endp;

  const char* ss=s;
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
#ifndef __MINGW32__
  int flags = fcntl(fd, F_GETFL, 0);
  fcntl(fd, F_SETFL, flags | O_NONBLOCK);
#endif
}

void block(int fd)
{
#ifndef __MINGW32__
  int flags = fcntl(fd, F_GETFL, 0);
  fcntl(fd, F_SETFL, flags & (~O_NONBLOCK));
#endif
}

/*
 * nonblock_getline reads lines from the stream. Unlike with normal
 * getline, underlying fd can be non-blocking. The function returns
 * the number of bytes copied to lineptr, or -1 on error. If full line
 * does not fit into internal read buffer (line is longer than
 * MAX_LINE_LENGTH), the contents of the buffer is returned as a
 * line.
 */

ssize_t nonblock_getline(char **lineptr, size_t *n,
			 GIOChannel *stream, char* &read_buf,
			 size_t &read_buf_pos)
{

  gsize si;
  g_io_channel_set_flags(stream,(GIOFlags)(G_IO_FLAG_NONBLOCK|(int)g_io_channel_get_flags(stream)),NULL);

  g_io_channel_set_line_term(stream,NULL,-1);

  if (*lineptr) {
    g_free(*lineptr);
    *lineptr=NULL;
    *n=0;
  }

  GIOStatus st=
    g_io_channel_read_line(stream,lineptr,&si,NULL,NULL);

  if (st==G_IO_STATUS_AGAIN) {
    return 0;
  }

  if (st==G_IO_STATUS_ERROR) {
    return -1;
  }

  if (n)
    *n=si;

  return si;
}

ssize_t getline(char **lineptr, size_t *n, GIOChannel *stream)
{
  gsize si;
  gsize ret;
  GIOStatus status;

  if (*lineptr) {
    g_free(*lineptr);
    *lineptr=NULL;
    *n=0;
  }

  do {
    status=g_io_channel_read_line(stream,lineptr,&si,&ret,NULL);
    *n=si;
  } while (status==G_IO_STATUS_AGAIN);

  if (status==G_IO_STATUS_ERROR) {
    return -1;
  }

  if (*n==0) {
    return -1;
  }

  return *n;
}

/* non-blocking getline, filter out log entries */
ssize_t agetline(char **lineptr, size_t *n, GIOChannel *stream,
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

Verdict::Verdict from_string(const std::string& s)
{
  if (s=="pass") {
    return Verdict::PASS;
  }
  if (s=="fail") {
    return Verdict::FAIL;
  }
  if (s=="inconclusive") {
    return Verdict::INCONCLUSIVE;
  }
  if (s=="error") {
    return Verdict::W_ERROR;
  }
  return Verdict::UNDEFINED;
}

std::string to_string(Verdict::Verdict verdict)
{
  switch (verdict) {
  case Verdict::PASS:
    return "pass";
    break;
  case Verdict::FAIL:
    return "fail";
    break;
  case Verdict::INCONCLUSIVE:
    return "inconclusive";
    break;
  case Verdict::W_ERROR:
    return "error";
    break;
  default:
    return "unknown";
  }
  // Not reached
  return "unknown";
}

/* blocking getline, filter out log entries */
ssize_t bgetline(char **lineptr, size_t *n, GIOChannel* stream, Log& log,bool magic)
{
  ssize_t ret;
  int loopc=0;
  bool log_redirect;
  bool sensible_line;

  g_io_channel_set_line_term(stream,NULL,-1);


  do {

    if (*lineptr) {
      g_free(*lineptr);
      *lineptr=NULL;
      *n=0;
    }

    log_redirect = false;
    sensible_line = false;
    GIOStatus status;
    gsize si;
    do {
      loopc++;
      status=g_io_channel_read_line(stream,lineptr,&si,(gsize*)&ret,NULL);
      *n=si;
    } while (status==G_IO_STATUS_AGAIN);

    log.debug("just read %s",*lineptr);

    if (status==G_IO_STATUS_ERROR) {
      ret=-1;
    } else {
      if (si) {
        sensible_line = true;
	log.debug("We have %s",*lineptr);

	if ((*lineptr)[si-1]==0x0d || (*lineptr)[si-1]==0x0a) {
	  si--;
	  (*lineptr)[si]=0;
	}
      }
      if (si) {
	if ((*lineptr)[si-1]==0x0d || (*lineptr)[si-1]==0x0a) {
	  si--;
	  (*lineptr)[si]=0;
	}
      }
      *n=si;
      ret=si;
    }


    if (sensible_line) {
      if (magic && strncmp(*lineptr,"fmbtmagic",9)!=0) {
	// We have something to stdout
	fprintf(stdout,"%s\n",*lineptr);
	g_free(*lineptr);
	*lineptr = NULL;
	log_redirect = true;
      } else {
	if (magic && strncmp(*lineptr,"fmbtmagic",9)==0) {
          const int magic_length = 10;
          if (*(*lineptr + magic_length-1) == 'l' || *(*lineptr + magic_length-1) == 'e') {
            // remote log messages must be url encoded when sent through
            // the remote adapter protocol
            *(*lineptr + ret) = '\0';
            log.print("<remote msg=\"%s\"/>\n",*lineptr+magic_length);
            if (*(*lineptr + magic_length-1) == 'e')
              fprintf(stderr, "%s\n", unescape_string(*lineptr+magic_length));
            g_free(*lineptr);
            *lineptr = NULL;
            log_redirect = true;
          } else {
            // Remove magic
            ret -= magic_length;
            memmove(*lineptr,*lineptr + magic_length,ret);
            (*lineptr)[ret] = '\0';
          }
        }
      }
    }
  } while (log_redirect);

  if (ret>=0)
    log.debug("bgetline got string %s\n",*lineptr);

  return ret;
}


/* blocking getline, filter out log entries */

int getact(int** act,std::vector<int>& vec,GIOChannel* out,GIOChannel* in,
	   Log& log,int min,int max,Writable* w,bool magic)
{
  g_io_channel_flush(out,NULL);
  vec.resize(0);
  char* line=NULL;
  size_t n;
  int ret=-1;
  size_t s=bgetline(&line,&n,in,log,magic);

  if (s != (size_t)-1 && s >= 0 && line) {
    if (strspn(line, " -0123456789") != s) {
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

#ifndef DROI
#include <boost/regex.hpp>
#endif


void regexpmatch(const std::string& regexp,std::vector<std::string>& f,
                 std::vector<int>& result,bool clear,int a,int min)
{
#ifndef DROI
  if (clear) {
    result.clear();
  }
  try {
    boost::regex expression(regexp);
    boost::cmatch what;
    for(unsigned int i=min;i<f.size();i++) {
      if (regexp == f[i] || boost::regex_match(f[i].c_str(), what, expression)) {
	result.push_back(a*i);
      }
    }
  } catch (...) {
    for(unsigned int i=min;i<f.size();i++) {
      if (regexp == f[i]) {
	result.push_back(a*i);
      }
    }
  }
#endif
}

void strlist(std::vector<std::string>& s)
{
  for(unsigned i=0;i<s.size();i++) {
    size_t len=s[i].length();
    if (len>2) {
      if ((s[i][0]=='"' &&
	   s[i][len-1]=='"') ||
	  (s[i][0]=='\'' &&
	   s[i][len-1]=='\'')) {
	s[i]=s[i].substr(1,len-2);
      }
    }
    remove_force(s[i]);
  }
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
        //remove_force(pushme);
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
  if (strvec==NULL) {
    return;
  }
  for(unsigned i=0;i<strvec->size();i++) {
    delete (*strvec)[i];
  }
  delete strvec;
}

void gettime(struct timeval *tv)
{
#ifndef __MINGW32__
  struct timespec tp;
  clock_gettime(CLOCK_REALTIME,&tp);
#ifdef TIMESPEC_TO_TIMEVAL
  TIMESPEC_TO_TIMEVAL(tv,&tp);
#else
  tv->tv_sec=tp.tv_sec;
  tv->tv_usec=tp.tv_nsec/1000;
#endif
#else
  FILETIME ft; /*time since 1 Jan 1601 in 100ns units */
  GetSystemTimeAsFileTime( &ft );
  tv->tv_sec = (ft.dwHighDateTime-(116444736000000000LL))/10000000LL ;
  tv->tv_usec  = (ft.dwLowDateTime/10LL) % 1000000LL ;
#endif
}

void find(std::vector<std::string>& from,std::vector<std::string>& what,std::vector<int>& result)
{
  for(unsigned i=0;i<what.size();i++) {
    int p=find(from,what[i]);

      if (p) {
	result.push_back(p);
      } else {
	std::vector<int> r;
	regexpmatch(what[i],from,r,false);
	for(unsigned j=0;j<r.size();j++) {
	  result.push_back(r[j]);
	}
      }
  }
}

std::string envstr(const char* name)
{
  return envstr(name,name);
}

std::string envstr(const char* name,const char* default_str)
{
  char *_val=getenv(name);
  if (_val) {
    return std::string(_val);
  }
  return std::string(default_str);
}

void envstr(const char* name,std::string& val)
{
  char *_val=getenv(name);

  if (_val) {
    val=_val;
  }

}

int fprintf(GIOChannel* stream, const char *format, ...)
{
  va_list ap;
  gchar* buf=NULL;
  int ret=0;
  gsize bytes_written;
  va_start(ap, format);
  ret=g_vasprintf(&buf,format,ap);
  if (buf) {
    g_io_channel_write_chars(stream,buf,ret,&bytes_written,NULL);
    g_free(buf);
  }
  va_end(ap);
  return ret;
}

int getint(GIOChannel* out,GIOChannel* in,Log& log,
	   int min,int max,Writable* w,bool magic)
{
  if (out) {
    g_io_channel_flush(out,NULL);
  }
  char* line=NULL;
  size_t n;
  int ret=-42;
  ssize_t s=bgetline(&line,&n,in,log,magic);
  if (s && s != -1) {
    ret=atoi(line);
    log.debug("ret%i,s%i,strspn%i\n",ret,s,
	      (int)strspn(line,"-0123456789"));
    if ((int)strspn(line,"-0123456789") != s || (ret == 0 && line[0] != '0')) {
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

  log.debug("getint %i",ret);

  return ret;
}
