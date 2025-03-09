// setup imports

#include <string>
#include "api/script_runner_api.hpp"
#include <vector>
#include <iostream>
#include "include/external/rapidjson/document.h"

// test script imports

#include <unistd.h>

using namespace std;

int main(int argc, char* argv[]) {
    
    // setup
    
    string id_ = argv[1];
    ScriptRunnerAPI api{id_};

    // test script

    // Parse args from JSON string
    int n = 10; // default value
    if (argc > 2) {
        rapidjson::Document args;
        args.Parse(argv[2]);
        if (args.HasMember("n") && args["n"].IsInt()) {
            n = args["n"].GetInt();
        }
    }

    api.log("Calculating fibonacci sequence for n=" + std::to_string(n));

    vector<long long> fibonacci_dp(n + 1, 0);  // Changed size to n+1
    fibonacci_dp[1] = 1;

    for(int i = 2; i <= n; i++) {  // Changed to <= n
        fibonacci_dp[i] = fibonacci_dp[i-1] + fibonacci_dp[i-2];
        api.log("Fibonacci[" + std::to_string(i) + "] = " + std::to_string(fibonacci_dp[i]));
        usleep(1000000);
    }

    api.log("Fibonacci sequence calculation completed!");
    api.submit_result(Result::PASS);
    return 0;
}