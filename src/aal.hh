
#include <vector>

class aal {
public:
  int adapter_execute(int action)=0;
  int model_execute(int action)  =0;
  int getActions(int** act)      =0;
  std::vector<std::string>& getActionNames() {
    return action_names;
  }
private:
  std::vector<int> actions;
  std::vector<std::string> action_names; /* action names.. */
}
