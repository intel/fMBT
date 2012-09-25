
#include "model.hh"
#include <set>
#include "helper.hh"


class Model_filter : public Model {
public:
  Model_filter(Log&l,const std::string& param,bool _i): Model(l), cmp(_i)
  {
    commalist(param,fa);
  }
  virtual ~Model_filter() {}  

  int filter(int** actions,int r) {
    int pos=0;
    for(int i=0;i<r;i++) {
      (*actions)[pos]=(*actions)[i];
      if ((filteractions.find((*actions)[i])==filteractions.end())==cmp) {
	pos++;
      }
    }
    return pos;
  }

  virtual int getActions(int** actions) {
    return filter(actions,submodel->getActions(actions));
  }

  virtual int getIActions(int** actions) {
    return filter(actions,submodel->getIActions(actions));
  }

  virtual bool reset() {
    return true;
  }
  virtual int  execute(int action) {
    return submodel->execute(action);
  }
  virtual int getprops(int** props) {
    return submodel->getprops(props);
  }
  virtual void push() {
    submodel->push();
  }
  virtual void pop() {
    submodel->pop();
  }
  virtual bool init() {
    // init filter.
    std::vector<std::string>& n=submodel->getActionNames();    
    for(unsigned i=0;i<fa.size()-1;i++) {
      int p=find(n,fa[i]);
      if (p) {
	filteractions.insert(p);
      }
    }
    return true;
  }
  std::set<int> filteractions;
  Model* submodel;
  bool cmp;
  std::vector<std::string> fa;
};
