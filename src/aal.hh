#include "factory.hh"
#include <vector>
#include <string>

class aal {
public:
  virtual int adapter_execute(int action)=0;
  virtual int model_execute(int action)  =0;
  virtual int getActions(int** act)      =0;
  virtual std::vector<std::string>& getActionNames() {
    return action_names;
  }
protected:
  std::vector<int> actions;
  std::vector<std::string> action_names; /* action names.. */
};
