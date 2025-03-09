import subprocess

import json
import zmq
import os
import time
from colorama import Fore

from utils import TEST_SCRIPTS, CONFIG
from models import TestScript, Result

import threading
from datetime import datetime

with open(CONFIG, "r", encoding="utf-8") as f:
    config = json.load(f)

class ScriptRunner:
    def __init__(self) -> None:
        self.processes = []
        
        # Initialize ZMQ context
        self.context = zmq.Context()

    def __start_process(self, path: str, id: str, script_name: str, timeout=300, test_args=[]) -> Result:
        # Create a SUB socket for this specific process
        socket = self.context.socket(zmq.SUB)
        # Bind to the socket (the script will connect)
        port = config["zmq_port"]
        socket.bind(f"tcp://*:{port}")
        
        # Subscribe to messages with this ID
        socket.setsockopt_string(zmq.SUBSCRIBE, id)
        
        # Set socket to non-blocking mode with timeout
        socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1000 ms timeout

        # Start the log reading thread
        log_thread_stop_event = threading.Event()
        log_thread = threading.Thread(target=self.__read_process_logs, 
                                      args=[script_name, socket, log_thread_stop_event, id])
        log_thread.daemon = True  # Make thread daemon so it exits when main thread exits
        log_thread.start()
        
        start_time = time.time()

        # Run the process with proper environment and capture output
        try:
            args = ["python3", path, id]
            if test_args:
                args.append(json.dumps(test_args))
            result = subprocess.run(
                args=args,
                timeout=timeout,
                capture_output=True,
                check=False
            )
        except subprocess.TimeoutExpired:
            print(Fore.RED + f"Script timed out" + Fore.RESET)
            result = None

        if result:
            if result.returncode == 1:
                print(Fore.RED + f"\nScript failed:\n{result.stderr}" + Fore.RESET)
            elif result.returncode == Result.PASS:
                print(Fore.GREEN + f"\nTest passed!" + Fore.RESET)
            elif result.returncode == Result.FAIL:
                print(Fore.RED + f"\nTest failed!" + Fore.RESET)
            else:
                print(Fore.YELLOW + "\nTest finished with unknown result" + Fore.RESET)

            print("\nTotal run time: {:.2f} secs".format(time.time()-start_time))
            print("\n" + ". " * 50)
        
        # Signal the log thread to stop and wait for it to finish
        log_thread_stop_event.set()
        log_thread.join(timeout=5)  # Wait for the log thread to finish, with a timeout

        # Only close the socket after the thread has finished or timed out
        socket.close()
        
        return result.returncode
    
    def __read_process_logs(self, script_name: str, 
                            socket: zmq.SyncSocket, 
                            stop_event: threading.Event, 
                            id: str):
        
        while not stop_event.is_set():
            try:
                # Receive topic and message separately with timeout
                topic, message = socket.recv_multipart()
                
                # Convert bytes to string
                topic_str = topic.decode('utf-8')
                message_str = message.decode('utf-8')
                
                # Try to parse as JSON if possible, otherwise use as string
                try:
                    data = json.loads(message_str)
                except json.JSONDecodeError:
                    data = message_str

                print_string = Fore.GREEN + f"{datetime.now()} " + f"[{script_name}]: "
                print_string += Fore.CYAN + f"{data}" + Fore.RESET
                    
                print(print_string, flush=True)

            except zmq.Again:
                # Timeout occurred, just continue the loop
                continue
            except zmq.ZMQError:
                 # Socket might be closed or in an error state
                break
    
    def __get_processes(self):
        pass

    def __kill_process(self):
        pass
    
    def run_script(self, test_script: TestScript) -> Result:
        print(f"\n{Fore.YELLOW}{test_script.script_name.upper()}{Fore.RESET} ")

        script_path = os.path.join(TEST_SCRIPTS, test_script.script_path)

        result = self.__start_process(path=script_path, 
                             id=str(test_script.id), 
                             script_name=test_script.script_name,
                             timeout=test_script.timeout,
                             test_args=test_script.args)    
        
        return result