#include "script_runner_api.hpp"
#include <iostream>
#include "zmq.hpp"
#include <string>
#include <unistd.h>
#include <unordered_map>

#include <filesystem>

#include "include/external/rapidjson/document.h"
#include "include/external/rapidjson/filereadstream.h"

std::filesystem::path MAIN_DIRECTORY = std::filesystem::path(__FILE__).parent_path().parent_path().parent_path();
std::filesystem::path CONFIG = MAIN_DIRECTORY / "config.json";

// Initialize static members
int Result::PASS = 0;
int Result::FAIL = 0;

// Function to read JSON from a file
bool readConfigFile(rapidjson::Document& document) {
    FILE* fp = fopen(CONFIG.string().c_str(), "rb");
    if (!fp) {
        std::cerr << "Error opening file: " << CONFIG.string() << std::endl;
        return false;
    }
    
    char readBuffer[65536];
    rapidjson::FileReadStream is(fp, readBuffer, sizeof(readBuffer));
    document.ParseStream(is);
    fclose(fp);
    
    if (document.HasParseError()) {
        std::cerr << "Error parsing JSON: " << document.GetParseError() << std::endl;
        return false;
    }
    
    return true;
}

ScriptRunnerAPI::ScriptRunnerAPI(const std::string& script_id) : script_id_(script_id) {
    // Reading config JSON file
    rapidjson::Document readDoc;
    if (readConfigFile(readDoc)) {
        // Initialize result values
        Result::PASS = readDoc["result_codes"]["PASS"].GetInt();
        Result::FAIL = readDoc["result_codes"]["FAIL"].GetInt();

        // Initialize ZMQ
        context_ = new zmq::context_t(1);
        socket_ = new zmq::socket_t(*context_, ZMQ_PUB);

        // Connect to socket
        int port = readDoc["zmq_port"].GetInt();
        std::string connection_string = "tcp://localhost:" + std::to_string(port);
        socket_->connect(connection_string);
        usleep(10000); // Sleep 0.01 sec to give time for socket to get ready
    }
}

ScriptRunnerAPI::~ScriptRunnerAPI() {
    if (socket_) {
        delete socket_;
    }
    if (context_) {
        delete context_;
    }
}

void ScriptRunnerAPI::log(const std::string& message) {
    try {
        // Create the topic message (script ID)
        zmq::message_t topic(script_id_.data(), script_id_.size());
        
        // Create the actual message
        zmq::message_t msg(message.data(), message.size());
        
        // Send the topic first with SNDMORE flag
        socket_->send(topic, zmq::send_flags::sndmore);
        
        // Then send the actual message
        socket_->send(msg, zmq::send_flags::none);
        
        // Add a small delay to prevent message loss
        usleep(10000);  // 10ms delay
    } catch(const zmq::error_t& e) {
        std::cerr << "ZMQ error in log: " << e.what() << std::endl;
    }
}

void ScriptRunnerAPI::submit_result(const int& result) {
    exit(result);
}