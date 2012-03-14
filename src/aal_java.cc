/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2011, 2012 Intel Corporation.
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

#include "config.h"
#ifdef WITH_JVM
#include "aal_java.hh"

void jobjectArraytovector(JNIEnv *env,jintArray array,
			  std::vector<int> &vec) {
  vec.clear();
  jsize alen=env->GetArrayLength(array);
  jint buf[alen];
  env->GetIntArrayRegion(array,0,alen,buf);
  for(int i=0;i<alen;i++) {
    vec.push_back(buf[i]);
  }
}

void jobjectArraytovector(JNIEnv *env,jobjectArray array,
			  std::vector<std::string> &vec) {
  
  jsize alen=env->GetArrayLength(array);
  for(int i=0;i<alen;i++) {
    jobject ae=env->GetObjectArrayElement(array,i);
    jstring jstr=(jstring)ae;
    const char* str=env->GetStringUTFChars(jstr,NULL);
    std::string s(str);
    vec.push_back(s);
    env->ReleaseStringUTFChars(jstr, str);
  }
}

aal_java::aal_java(Log&l,std::string& s) 
  : aal(l), env(NULL),jvm(NULL) {
  vm_args.version = JNI_VERSION_1_6;
  vm_args.nOptions = 0;
  vm_args.ignoreUnrecognized = 0;

  int ret = JNI_CreateJavaVM(&jvm, (void**)&env, &vm_args);
  if (ret<0) {
    env=NULL;
    ok=false;
  } else {
    wclass = env->FindClass(s.c_str());
    if (wclass) {
      constructor=env->GetMethodID(wclass, "<init>", "()V");
      if (constructor) {
	obj=env->NewObject(wclass, constructor);
	if (obj) {
	  aexec=env->GetMethodID(wclass,"adapter_execute","(I)I");
	  mexec=env->GetMethodID(wclass,"model_execute","(I)I");
	  obs  =env->GetMethodID(wclass,"adapter_observe","()I");
	  Reset=env->GetMethodID(wclass,"reset","()Z");
	  Push =env->GetMethodID(wclass,"push","()V");
	  Pop  =env->GetMethodID(wclass,"pop","()V");
	  geta =env->GetMethodID(wclass,"getActions","()[I");
	  if (!aexec || !mexec || !geta) {
	    ok=false;
	  } else {
	    Getprops=env->GetMethodID(wclass,"getprops","()[I");
	    
	    jfieldID field=env->GetFieldID(wclass,"action_names",
					   "[Ljava/lang/String;");
	    jobjectArray array=(jobjectArray)
	      env->GetObjectField(obj, field);
	    
	    jobjectArraytovector(env,array,action_names);
	    
	    field=env->GetFieldID(wclass,"tag_names",
				  "[Ljava/lang/String;");
	    array=(jobjectArray)env->GetObjectField(obj, field);
	    jobjectArraytovector(env,array,tag_names);
	  }
	} else {
	  ok=false;
	}
      } else {
	ok=false;
      }
    } else {
      ok=false;
    }
  }
}

int aal_java::adapter_execute(int action) {
  return env->CallIntMethod(obj,aexec,action);
}

int aal_java::model_execute(int action) {
  return env->CallIntMethod(obj,mexec,action);
}

int  aal_java::observe(std::vector<int> &action,
		       bool block) {
  int ret=0;
  if (obs) {
    do {
      ret=env->CallIntMethod(obj,obs);
    } while (!ret && block);
  } else {
    return SILENCE;
  }
  if (ret) {
    action.resize(1);
    action[0]=ret;
    return 1;
  } else {
    action.clear();
    return 0;
  }
}


void aal_java::push() {
  if (Push) {
    env->CallVoidMethod(obj,Push);
  }
}

void aal_java::pop() {
  if (Pop) {
    env->CallVoidMethod(obj,Pop);
  }
}

bool aal_java::reset() {
  if (Reset) {
    return env->CallBooleanMethod(obj,Reset);
  }
  return true;
}

int aal_java::getActions(int** act) {
  jobject retobj = 
    env->CallObjectMethod(obj,geta);
  jintArray array=(jintArray) retobj;
  jobjectArraytovector(env,array,actions);
  *act=&actions[0];
  return actions.size();
}

int aal_java::getprops(int** pro) {
  if (Getprops) {
    jobject retobj = 
      env->CallObjectMethod(obj,Getprops);
    jintArray array=(jintArray) retobj;
    jobjectArraytovector(env,array,tags);
  } else {
    tags.clear();
  }
  if (pro) {
    *pro=&tags[0];
  }
  return tags.size();
}

#include <cstring>
#include "helper.hh"

namespace {

  std::map<std::string,aal_java*> storage;

  Adapter* adapter_creator(Log& l, std::string params = "") {
    std::string classname(unescape_string(strdup(params.c_str())));
    aal_java* al=storage[classname];
    if (!al) {
      al=new aal_java(l,classname);
      if (al->ok) {
	storage[classname]=al;
      } else {
	delete al;
	al=NULL;
      }
    }

    if (al) {
      return new Awrapper(l,params,al);
    }
    return NULL;
  }

  Model* model_creator(Log& l, std::string params) {
    std::string classname(unescape_string(strdup(params.c_str())));
    aal_java* al=storage[classname];
    if (!al) {
      al=new aal_java(l,classname);
      if (al->ok) {
	storage[classname]=al;
      } else {
	delete al;
	al=NULL;
      }
    }

    if (al) {
      return new Mwrapper(l,params,al);
    }
    return NULL;
  }

  static ModelFactory  ::Register Mo("java", model_creator);
  static AdapterFactory::Register Ad("java", adapter_creator);
}

#endif
