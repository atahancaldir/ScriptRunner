from pydantic import BaseModel
from enum import IntEnum

import json
import zmq
import time
import sys

from os.path import dirname, realpath, join

MAIN_DIRECTORY = dirname(dirname(dirname(realpath(__file__))))
CONFIG = join(MAIN_DIRECTORY, "config.json")

with open(CONFIG, "r", encoding="utf-8") as f:
    config = json.load(f)

class Result(IntEnum):
    PASS = config["result_codes"]["PASS"]
    FAIL = config["result_codes"]["FAIL"]

class ScriptRunnerAPI:
    def __init__(self, script_id: str) -> None:
        self.script_id = script_id
        
        # Initialize ZMQ
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        
        # Connect to the socket (the main app binds)
        port = config["zmq_port"]
        self.socket.connect(f"tcp://localhost:{port}")
        time.sleep(0.01) # Giving time for the socket to get ready

    def log(self, message: str) -> None:
        # Prepare the topic (script ID)
        topic = self.script_id.encode('utf-8')
        
        # Convert message to string if it's not already
        if not isinstance(message, str):
            message = str(message)
            
        # Encode the message
        msg = message.encode('utf-8')
        
        # Send the message
        self.socket.send_multipart([topic, msg])

    def get_args(self) -> dict:
        if len(sys.argv) < 3:
            return None
        return json.loads(sys.argv[2])

    def submit_result(self, result: Result):
        sys.exit(result)