#include "log.hh"
#include "aal.hh"
#include "config.h"
#include "log_aalremote.hh"
#include "verdict.hh"
#include "helper.hh"

class aal_loader {
public:

 virtual aal* load(std::string& name,Log& l);
};
aal* aal_loader::load(std::string& name,Log& l)
{

  Model* _model = new_model(l,name);
  
  if (_model == NULL)
    return NULL;

  if (!_model->status)
    return NULL;

  Adapter* _adapter = new_adapter(l,"aal");

  if (_adapter == NULL)
    return NULL;

  // We know that aal needs to be not null
  return aal::storage->begin()->second;
}

