/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2011,2012 Intel Corporation.
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

#include "lts.hh"
#include "log_null.hh"
#include "history_log.hh"
#include "coverage.hh"

#ifndef DROI
#include <glib-object.h>
#include <error.h>
#else
void error(int exitval, int dontcare, const char* format, ...)
{
  va_list ap;
  fprintf(stderr, "fMBT error: ");
  va_start(ap, format);
  vfprintf(stderr, format, ap);
  va_end(ap);
  exit(exitval);
}
#endif


class ltscoverage: public Coverage {
public:
  ltscoverage(Log&l,History_log& _h, bool _verd): Coverage(l), prop_count(0), verd(_verd), lts(l), hl(_h)
  {}
  virtual ~ltscoverage() {}
  virtual void push() {}
  virtual void pop() {}
  virtual bool execute(int action) {return true;}
  virtual float getCoverage() { return 0.0;}
  virtual int fitness(int* actions,int n, float* fitness) { return 0;}

  virtual void history(int action, std::vector<int>& props,
 		       Verdict::Verdict verdict)
  {
    // implementation....
    if (action) {
      trace.push_back(action);

      if (prop.size()<hl.tnames.size()) {
	prop.resize(hl.tnames.size());
      }

      for(unsigned i=0;i<props.size();i++) {
	log.debug("State %i, prop %i(%s)\n",
		  trace.size(),props[i],hl.tnames[props[i]].c_str());
	prop[props[i]].push_back(trace.size());
      }
    } else {
      // verdict. Let's create lts.
      // We might have props...

      for(unsigned i=0;i<props.size();i++) {
	log.debug("VState %i, prop %i(%s)\n",
		  trace.size()+1,props[i],hl.tnames[props[i]].c_str());
	prop[props[i]].push_back(trace.size()+1);
      }

      lts.set_state_cnt(trace.size()+1);
      lts.set_action_cnt(hl.anames.size()-1);
      lts.set_transition_cnt(trace.size());
      lts.set_prop_cnt(hl.tnames.size()-1+(verd?1:0));

      lts.set_initial_state(1);
      lts.header_done();

      for(unsigned i=1;i<hl.anames.size();i++) {
	lts.add_action(i,hl.anames[i]);
      }

      for(unsigned i=0;i<trace.size();i++) {
	std::vector<int> e;
	std::vector<int> a;
	std::vector<int> s;
	a.push_back(trace[i]);
	s.push_back(i+2);
	lts.add_transitions(i+1,a,e,s,e);
      }

      for(unsigned i=1;i<prop.size();i++) {
	log.debug("add prop %s, %i\n",hl.tnames[i].c_str(),prop[i].size());
	for(unsigned j=0;j<prop[i].size();j++) {
	  log.debug("state %i\n",prop[i][j]);
	}
	lts.add_prop(&hl.tnames[i],prop[i]);
      }

      if (verd) {
	std::vector<int> v;
	v.push_back(trace.size()+1);
	static std::string UNDEF("verdict::undefined");
	static std::string pass("verdict::pass");
	static std::string fail("verdict::fail");
	static std::string inco("verdict::inconclusive");
	static std::string err("verdict::error");
	std::string s;
	switch (verdict) {
	case Verdict::FAIL:
	  s=fail;
	  break;
	case Verdict::PASS:
	  s=pass;
	  break;
	case Verdict::INCONCLUSIVE:
	  s=inco;
	  break;
	case Verdict::W_ERROR:
	  s=err;
	  break;
	default:
	  s=UNDEF;
	}
	log.debug("verdict...\n");
 	lts.add_prop(&s,v);
      }
    }
  }

  std::vector<int> trace;
  std::vector<std::vector<int> > prop;
  int prop_count;
  bool verd;
  Lts lts;
  History_log& hl;
};

#include <getopt.h>
#include "config.h"

void print_usage()
{
  std::printf(
	      "Usage: fmbt-log2lsts [options] logfile\n"
	      "Options:\n"
	      "    -e     add test verdict to the end state as state proposition\n"
	      "    -V     print version ("VERSION FMBTBUILDINFO")\n"
	      "    -h     help\n"
	      );
}


int main(int argc,char * const argv[])
{
  Log_null log;
  int c;
  bool verd=false;
  FILE* outputfile=stdout;
  static struct option long_opts[] = {
    {"help", no_argument, 0, 'h'},
    {"version", no_argument, 0, 'V'},
    {0, 0, 0, 0}
  };

#ifndef DROI
#if !GLIB_CHECK_VERSION(2, 35, 0)
  g_type_init ();
#endif
#endif

  while ((c = getopt_long (argc, argv, "heVo:", long_opts, NULL)) != -1)
    switch (c)
      {
      case 'o':
	if (outputfile!=stdout) {
	  printf("more than one output file\n");
	  print_usage();
	  return 1;
	}
	outputfile=fopen(optarg,"w");
	if (!outputfile)
          error(1,0,"cannot open output file \"%s\".",optarg);
	break;
      case 'e':
	verd=true;
	break;
      case 'V':
	printf("Version: "VERSION FMBTBUILDINFO"\n");
	return 0;
	break;
      case 'h':
	print_usage();
	return 0;
      default:
	return 2;
      }

  if (optind == argc) {
    print_usage();
    error(32, 0, "logfile missing.\n");
  }

  std::string file(argv[optind]);

  History_log hl(log,file);

  ltscoverage cov(log,hl,verd);

  hl.set_coverage(&cov,NULL);

  fprintf(outputfile,"%s\n",cov.lts.stringify().c_str());
  return 0;
}
