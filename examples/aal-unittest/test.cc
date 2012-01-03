
#define ASSERT(x) if (!(x)) return 0;
#include "mycounter.h"
#include "aal.hh"

class _gen_mycountertest:public aal
{
private:
  //variables

  MyCounter * mycounter;
  int value;


//action1: "iCreate"
  bool action1_guard ()
  {
    return m == NULL;
  }
  void action1_body ()
  {
  }
  int action1_adapter ()
  {

    value = 0;
    mycounter = new MyCounter;

    return 1;
  }

//action2: "iDestroy"
  bool action2_guard ()
  {
    return m != NULL;
  }
  void action2_body ()
  {
  }
  int action2_adapter ()
  {

    delete m;
    m = NULL;

    return 2;
  }

//action3: "iIncrement"
  bool action3_guard ()
  {
    return m != NULL;
  }
  void action3_body ()
  {
  }
  int action3_adapter ()
  {

    mycounter->inc ();
    value += 1;

    return 3;
  }

//action4: "iReset"
  bool action4_guard ()
  {
    return m != NULL;
  }
  void action4_body ()
  {
  }
  int action4_adapter ()
  {

    mycounter->reset ();
    value = 0;

    return 4;
  }

//action5: "iCount"
  bool action5_guard ()
  {
    return m != NULL;
  }
  void action5_body ()
  {
  }
  int action5_adapter ()
  {

    ASSERT (m->count () == value);

    return 5;
  }

public:
  _gen_mycountertest ()
  {
    action_names.push_back ("");
    action_names.push_back ("iCreate");
    action_names.push_back ("iDestroy");
    action_names.push_back ("iIncrement");
    action_names.push_back ("iReset");
    action_names.push_back ("iCount");

    mycounter = NULL;
    value = 0;
  }
  virtual bool reset ()
  {

    mycounter = NULL;
    value = 0;
    return true;
  }

  virtual int adapter_execute (int action)
  {
    switch (action)
      {
      case 1:
	return action1_adapter ();
	break;
      case 2:
	return action2_adapter ();
	break;
      case 3:
	return action3_adapter ();
	break;
      case 4:
	return action4_adapter ();
	break;
      case 5:
	return action5_adapter ();
	break;
      default:
	return 0;
      };
  }
  virtual int model_execute (int action)
  {
    switch (action)
      {
      case 1:
	action1_body ();
	return 1;
	break;
      case 2:
	action2_body ();
	return 2;
	break;
      case 3:
	action3_body ();
	return 3;
	break;
      case 4:
	action4_body ();
	return 4;
	break;
      case 5:
	action5_body ();
	return 5;
	break;
      default:
	return 0;
      };
  }
  virtual int getActions (int **act)
  {
    actions.clear ();
    if (action1_guard ())
      {
	actions.push_back (1);
      }
    if (action2_guard ())
      {
	actions.push_back (2);
      }
    if (action3_guard ())
      {
	actions.push_back (3);
      }
    if (action4_guard ())
      {
	actions.push_back (4);
      }
    if (action5_guard ())
      {
	actions.push_back (5);
      }
    *act = &actions[0];
    return actions.size ();
  }
};

  /* factory register */

namespace
{
  static aal *a = NULL;

  Model *model_creator (Log & l, std::string params)
  {
    if (!a)
      {
	a = new _gen_mycountertest ();
      }
    return new Mwrapper (l, params, a);
  }

  static ModelFactory::Register me1 ("mycountertest", model_creator);

  Adapter *adapter_creator (Log & l, std::string params = "")
  {
    if (!a)
      {
	a = new _gen_mycountertest ();
      }
    return new Awrapper (l, params, a);
  }
  static AdapterFactory::Register me2 ("mycountertest", adapter_creator);
};
