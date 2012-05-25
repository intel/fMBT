#include "mylocaladapter.hh"
#include "log.hh"

MyLocalAdapter::MyLocalAdapter(Log& l, std::string params):
    Adapter(l)
{
    log.print("<adapter name=\"mylocal\" params=\"%s\" />\n", params.c_str());
}

void MyLocalAdapter::execute(std::vector<int>& action)
{
    log.push("mylocal_execute");
    log.print("<executing action_index=\"%d\" action_name=\"%s\"/>\n",
              action[0], getUActionName(action[0]));
    log.pop();
}

int MyLocalAdapter::observe(std::vector<int> &action, bool block)
{
    log.push("mylocal_reader");
    if (block) {
        action.resize(1);
        action[0] = 1;
        log.pop();
        return 1;
    }
    log.pop();
    return 0;
}

FACTORY_DEFAULT_CREATOR(Adapter, MyLocalAdapter, "mylocal");
