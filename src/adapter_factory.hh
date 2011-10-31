#ifndef __adapter_factory_hh__
#define __adapter_factory_hh__

#define EXPORT __attribute__((visibility("default")))

#include <map>
#include <string>
#include <vector>
#include "factory.hh"

FACTORY_DECLARATION(Adapter)

/*
namespace AdapterFactory {

    typedef Adapter*(*creator)(std::vector<std::string>&,
                               std::string, Log& log);
    
    extern Adapter* create(std::string name,
                           std::vector<std::string>& actions,
                           std::string params, Log& log);
    
    extern void add_factory(std::string name, creator c);
    
    extern std::map<std::string, creator>* creators;

    class Register {
    public:
        Register(std::string name, AdapterFactory::creator c) {
            add_factory(name, c);
        }
    };
};
*/

#endif
