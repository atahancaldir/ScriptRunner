#pragma once

#include <string>

namespace zmq {
    class context_t;
    class socket_t;
}

// Define the Result struct
struct Result {
    static int PASS;
    static int FAIL;
};

class ScriptRunnerAPI {
public:
    ScriptRunnerAPI(const std::string& script_id);
    ~ScriptRunnerAPI();  // Add destructor declaration
    void log(const std::string& message);
    void submit_result(const int& result);

private:
    std::string script_id_;
    zmq::context_t* context_;
    zmq::socket_t* socket_;
};