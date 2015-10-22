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
#ifndef __MINGW32__

#include "history_log.hh"

#include <libxml/xmlreader.h>
#ifndef LIBXML_READER_ENABLED
#error "LIBXML_READER_ENABLED is needed"
#endif

#include "helper.hh"
#include <glib.h>
#include <glib/gprintf.h>

void History_log::handle_time(xmlTextReaderPtr reader) {
    char* time=(char*)xmlTextReaderGetAttribute(reader,(xmlChar*)"time");
    char* endp;
    long sec = strtol(time, &endp, 10);
    if (*endp=='.') {
      long usec=strtol(endp+1, &endp, 10);
      current_time.tv_sec=sec;
      current_time.tv_usec=usec;
      Adapter::current_time=current_time;
    }
    free(time);
    time=NULL;

}

History_log::History_log(Log& l, std::string params) :
  History(l,params),alphabet_started(false), alphabet_done(false), act(NULL), tag(NULL), c(NULL), a(NULL), myes(NULL), learn(NULL), ada(NULL)
{
  std::vector<std::string> prm;
  commalist(params,prm);

  if (prm.size()>0) {
    file=prm[0];
  }
  for(unsigned i=1;i<prm.size();i++) {
    switch (prm[i][0]) {
    case 'a':
      if (g_strrstr(prm[i].c_str()+1,"g")) {
	model_getactions=true;
      }
      if (g_strrstr(prm[i].c_str()+1,"a")) {
	adapter_execute=true;
      }
      if (g_strrstr(prm[i].c_str()+1,"b")) {
	model_execute=true;
      }
      break;
    case 't':
      if (g_strrstr(prm[i].c_str()+1,"g")) {
	tag_getprops=true;
      }
      if (g_strrstr(prm[i].c_str()+1,"a")) {
	tag_checktags=true;
      }
      break;
    case 'C':
      coverage_execute=false;
      break;
    }
  }
  separator=std::string(" ");
  anames.push_back("");
  tnames.push_back("");
  a = new Alphabet_impl(anames,tnames);
}

History_log::~History_log()
{
  if (act)
    free(act);
  if (tag)
    free(tag);
  if (a)
    delete a;
  // This should be deleted by someone else...
  /*
  if (myes)
    delete myes;
  */
}


void History_log::processNode(xmlTextReaderPtr reader)
{
  char* name =(char*) xmlTextReaderConstName(reader);
  if (name==NULL) return;

  if (xmlTextReaderDepth(reader)>2) {
    if (alphabet_started && !alphabet_done) {
      alphabet_done=true;
      if (model_from_log) {
	log.ref();
	myes=new Model_yes(log,"");
	myes->set_model(a);
	c->set_model(myes);
      }
    }
  }

  if (!alphabet_done) {
    if ((xmlTextReaderDepth(reader)==2) &&
	(strcmp((const char*)name,"action_name")==0)) {
      char* aname=unescape_string((char*)xmlTextReaderGetAttribute(reader,(xmlChar*)"name"));
      alphabet_started=true;
      if (aname!=NULL) {
	anames.push_back(aname);
	free(aname);
	aname=NULL;
      }
    }

    if ((xmlTextReaderDepth(reader)==2) &&
	(strcmp((const char*)name,"tag_name")==0)) {
      char* tname=unescape_string((char*)xmlTextReaderGetAttribute(reader,(xmlChar*)"name"));
      alphabet_started=true;
      if (tname!=NULL) {
	tnames.push_back(tname);
	free(tname);
	tname=NULL;
      }
    }

  }

  if ((xmlTextReaderDepth(reader)==3) &&
      (strcmp((const char*)name,"current_time")==0)) {
    handle_time(reader);
  }

  if ((xmlTextReaderDepth(reader)==3) &&
      (strcmp((const char*)name,"action")==0)) {
    // action
    if (act) {
      send_action();
    }
    handle_time(reader);
    act=unescape_string((char*)xmlTextReaderGetAttribute(reader,(xmlChar*)"name"));
    log.debug("FOUND ACT %s\n",act);
    send_action();
  }

  if ((xmlTextReaderDepth(reader)==3) &&
      (strcmp((const char*)name,"suggested_action")==0)) {
    if (learn) {
      char* suggested_act=unescape_string((char*)xmlTextReaderGetAttribute(reader,(xmlChar*)"name"));
      handle_time(reader);
      if (suggested_act) {
	int action=find(a->getActionNames(),suggested_act);
	if (learn && action) {
	  learn->suggest(action);
	}
	free(suggested_act);
      }
    }
  }
  if ((xmlTextReaderDepth(reader)==3) &&
      (strcmp((const char*)name,"tags")==0)) {
    // tags
    if (tag) {
      free(tag);
    }
    tag=(char*)xmlTextReaderGetAttribute(reader,(xmlChar*)"enabled");
    log.debug("FOUND TAG %s\n",tag);
  }

  if ((xmlTextReaderDepth(reader)==3) &&
      (strcmp((const char*)name,"stop")==0)) {
    log.debug("STOP\n");
    if (act) {
      send_action();
    }
    // verdict
    char* ver=(char*)xmlTextReaderGetAttribute(reader,(xmlChar*)"verdict");
    std::vector<std::string> p;

    if (tag!=NULL) {
      std::string t(tag);
      strvec(p,t,separator);
      for(unsigned i=0;i<p.size();i++) {
	unescape_string(p[i]);
      }
    }

    std::string a(ver);
    test_verdict=ver;
    free(ver);
    ver=NULL;
    send_action(a,p,true);
  }
}

Alphabet* History_log::set_coverage(Coverage* cov,
				    Alphabet* alpha,
				    Learning* _learn)
{
  c=cov;
  alp=alpha;
  learn=_learn;

  if (alpha) {
    model_from_log=false;
  } else {
    model_from_log=true;
  }

  LIBXML_TEST_VERSION

    xmlTextReaderPtr reader =
    xmlReaderForFile(file.c_str(), NULL, 0);

  if (reader != NULL) {
    int ret;
    ret = xmlTextReaderRead(reader);
    while (ret == 1) {
      processNode(reader);
      ret = xmlTextReaderRead(reader);
    }
    xmlFreeTextReader(reader);
  }
  xmlCleanupParser();
  xmlMemoryDump();

  return myes;
}

void History_log::send_action()
{
  std::string a(act);
  std::string t(tag);

  std::vector<std::string> props;

  if (t!="") {
    strvec(props,t,separator);
    for(unsigned i=0;i<props.size();i++) {
      unescape_string(props[i]);
    }
  }
  send_action(a,props);
  free(tag);
  free(act);
  tag=NULL;
  act=NULL;
}

bool History_log::send_action(std::string& act,
			      std::vector<std::string>& props,
			      bool verdict)
{
  std::vector<int> p;

  log.debug("SEND_ACTION (%i)\n",props.size());

  for(unsigned i=0;i<props.size();i++) {
    int j=find(a->getSPNames(),props[i]);
    log.debug("TAG %i(%s) %i\n",
	      i,props[i].c_str(),j);
    p.push_back(j);
  }

  if (c&&a) {
    if (verdict) {
      if (coverage_execute) {
	if (act=="pass") {
	  c->history(0,p,Verdict::PASS);
	  return true;
	}

	if (act=="fail") {
	  c->history(0,p,Verdict::FAIL);
	  return true;
	}

	if (act=="inconclusive") {
	  c->history(0,p,Verdict::INCONCLUSIVE);
	  return true;
	}

	if (act=="error") {
	  c->history(0,p,Verdict::W_ERROR);
	  return true;
	}

	if (act=="undefined") {
	  c->history(0,p,Verdict::UNDEFINED);
	  return true;
	}
	return false;
      }
      return true;
    }
    int action=find(a->getActionNames(),act);

    if (action>0) {
      if (learn) {
	learn->execute(action);
      }
      if (coverage_execute) {
	c->history(action,p,Verdict::UNDEFINED);
      }
      if (ada) {
	if (tag_checktags) {
	  std::vector<int> mismatch_tags;
	  ada->check_tags(& p[0],p.size(),mismatch_tags);
	  /*
	    ada->check_tags(int* tag,int len,std::vector<int>& t);
	  */
	}
	if (adapter_execute) {
	  std::vector<int> a;
	  a.push_back(action);
	  ada->execute(a);
	}
      }
      if (!model_from_log) {
	Model* m=(Model*)alp;
	if (model_getactions) {
	  int** act = 0;
	  m->getActions(act);
	}

	if (model_execute) {
	  m->execute(action);
	}
	if (tag_getprops) {
          int* tags = 0;
	  m->getprops(&tags);
	}
      }
      return true;
    } else {
      // Tau?
    }
  }

  return false;
}

FACTORY_DEFAULT_CREATOR(History, History_log, "log")
#endif
