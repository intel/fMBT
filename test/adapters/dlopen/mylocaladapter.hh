#include "adapter.hh"

class MyLocalAdapter: public Adapter {
public:
  MyLocalAdapter(Log& l, std::string params = "");
  virtual void execute(std::vector<int>& action);
  virtual bool readAction(std::vector<int> &action, bool block=false);
};
