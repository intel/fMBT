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

#include "history_log.hh"

#include <libxml/xmlreader.h>
#ifndef LIBXML_READER_ENABLED
#error "LIBXML_READER_ENABLED is needed"
#endif

#include "helper.hh"

History_log::History_log(Log& l, std::string params) :
  History(l,params), alphabet_done(false), act(NULL), tag(NULL), c(NULL), a(NULL), file(params)
{
  separator=std::string(" ");
  anames.push_back("");
  tnames.push_back("");
  a = new Alphabet_impl(anames,tnames);
}

void History_log::processNode(xmlTextReaderPtr reader)
{
  char* name =(char*) xmlTextReaderConstName(reader);
  if (name==NULL) return;

  if (xmlTextReaderDepth(reader)>2) {
    if (!alphabet_done) {
      alphabet_done=true;
      if (model_from_log) {
	l.ref();
	myes=new Model_yes(l,"");
	myes->set_model(a);
	c->set_model(myes);
      }
    }
  }
  
  if (!alphabet_done) {
    if ((xmlTextReaderDepth(reader)==2) &&
	(strcmp((const char*)name,"action_name")==0)) {
      char* aname=unescape_string((char*)xmlTextReaderGetAttribute(reader,(xmlChar*)"name"));
      if (aname!=NULL) {
	anames.push_back(aname);
	free(aname);
      }
    }

    if ((xmlTextReaderDepth(reader)==2) &&
	(strcmp((const char*)name,"tag_name")==0)) {
      char* tname=unescape_string((char*)xmlTextReaderGetAttribute(reader,(xmlChar*)"name"));
      if (tname!=NULL) {
	tnames.push_back(tname);
	free(tname);
      }
    }

  }

  if ((xmlTextReaderDepth(reader)==3) &&
      (strcmp((const char*)name,"current_time")==0)) {
    char* time=(char*)xmlTextReaderGetAttribute(reader,(xmlChar*)"time");
    char* endp;
    long sec = strtol(time, &endp, 10);
    if (*endp=='.') {
      long usec=strtol(endp+1, &endp, 10);
      current_time.tv_sec=sec;
      current_time.tv_usec=usec;
    }
    free(time);
  }

  if ((xmlTextReaderDepth(reader)==3) &&
      (strcmp((const char*)name,"action")==0)) {
    // action
    if (act) {
      send_action();
    }
    act=unescape_string((char*)xmlTextReaderGetAttribute(reader,(xmlChar*)"name"));
    log.debug("FOUND ACT %s\n",act);
    send_action();
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
    send_action(a,p,true);
  }
}

Alphabet* History_log::set_coverage(Coverage* cov,
				    Alphabet* alpha)
{
  c=cov;

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
	c->history(0,p,Verdict::ERROR);
	return true;
      }

      if (act=="undefined") {
	c->history(0,p,Verdict::UNDEFINED);
	return true;
      }
      return false;
    }
    int action=find(a->getActionNames(),act);

    if (action>0) {
      c->history(action,p,Verdict::UNDEFINED);
      return true;
    } else {
      // Tau?
    }
  }

  return false;  
}

FACTORY_DEFAULT_CREATOR(History, History_log, "log")
