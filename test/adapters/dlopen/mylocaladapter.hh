#include "adapter.hh"

class MyLocalAdapter: public Adapter {
public:
  MyLocalAdapter(Log& l, std::string params = "");
  virtual ~MyLocalAdapter();
  virtual void execute(std::vector<int>& action);
  virtual int observe(std::vector<int> &action, bool block=false);
};
