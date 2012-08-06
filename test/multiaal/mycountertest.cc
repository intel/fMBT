
        #include "mycounter.h"
    #include "aal.hh"

class _gen_mycountertest:public aal {
private:
	//variables

        MyCounter* mycounter;
        int value;
    

//action1: "iCreate"
bool action1_guard() {
 return mycounter == NULL; }
void action1_body() {
}
int action1_adapter(const char* param) {

            value = 0;
            mycounter = new MyCounter;
            ASSERT_NEQ((long)mycounter, 0);
        
	return 1;
}

//action2: "iDestroy"
bool action2_guard() {
 return mycounter != NULL; }
void action2_body() {
}
int action2_adapter(const char* param) {

            delete mycounter;
            mycounter = NULL;
        
	return 2;
}

//action3: "iIncrement"
bool action3_guard() {
 return mycounter != NULL; }
void action3_body() {
}
int action3_adapter(const char* param) {

            mycounter->inc();
            value += 1;
        
	return 3;
}

//action4: "iReset"
bool action4_guard() {
 return mycounter != NULL; }
void action4_body() {
}
int action4_adapter(const char* param) {

            mycounter->reset();
            value = 0;
        
	return 4;
}

//action5: "iCount"
bool action5_guard() {
 return mycounter != NULL; }
void action5_body() {
}
int action5_adapter(const char* param) {

            ASSERT_EQ(mycounter->count(), value);
        
	return 5;
}

public:
	_gen_mycountertest(Log& l, std::string& params): aal(l, params) {
	action_names.push_back("");
	action_names.push_back("iCreate");
	action_names.push_back("iDestroy");
	action_names.push_back("iIncrement");
	action_names.push_back("iReset");
	action_names.push_back("iCount");
	tag_names.push_back("");

        mycounter = NULL;
        value = 0;
    }
virtual bool reset() {

        mycounter = NULL;
        value = 0;
    return true;
}

virtual int observe(std::vector<int>&action, bool block){
	action.clear();
	do {
	int r;
	return SILENCE;
	} while(block);	return 0;
}
virtual int adapter_execute(int action,const char* param) {
	switch(action) {
		case 1:
		return action1_adapter(param);
		break;
		case 2:
		return action2_adapter(param);
		break;
		case 3:
		return action3_adapter(param);
		break;
		case 4:
		return action4_adapter(param);
		break;
		case 5:
		return action5_adapter(param);
		break;
		default:
		return 0;
	};
}
virtual int model_execute(int action) {
	switch(action) {
		case 1:
		action1_body();
		return 1;
		break;
		case 2:
		action2_body();
		return 2;
		break;
		case 3:
		action3_body();
		return 3;
		break;
		case 4:
		action4_body();
		return 4;
		break;
		case 5:
		action5_body();
		return 5;
		break;
		default:
		return 0;
	};
}
virtual int getActions(int** act) {
actions.clear();
	if (action1_guard()) {
		actions.push_back(1);
	}
	if (action2_guard()) {
		actions.push_back(2);
	}
	if (action3_guard()) {
		actions.push_back(3);
	}
	if (action4_guard()) {
		actions.push_back(4);
	}
	if (action5_guard()) {
		actions.push_back(5);
	}
	*act = &actions[0];
	return actions.size();
}
virtual int getprops(int** props) {
tags.clear();
	*props = &tags[0];
	return tags.size();
}
};
  /* factory register */

namespace {
static aal* a=NULL;

Model* model_creator(Log&l, std::string params) {
	if (!a) {
	  a=new _gen_mycountertest(l, params);
	}
	return new Mwrapper(l,params,a);
}

static ModelFactory::Register me1("mycountertest", model_creator);

Adapter* adapter_creator(Log&l, std::string params = "")
{
	if (!a) {
	  a=new _gen_mycountertest(l, params);
	}
	return new Awrapper(l,params,a);
}
static AdapterFactory::Register me2("mycountertest", adapter_creator);
}
