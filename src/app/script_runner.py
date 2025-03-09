import subprocess

import json
import zmq
import os
import time
import platform
import sys

from pathlib import Path

from typing import List

from colorama import Fore

from utils import TEST_SCRIPTS, CONFIG, TEST_SCRIPTS_API
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

    def __build_cpp_scripts(self, path: str) -> str:
        # Creating build directory under test_scripts/api to store build file, if it doesnt exist
        build_dir = os.path.join(TEST_SCRIPTS_API, "build")
        Path(build_dir).mkdir(exist_ok=True)  # Create Path instance first

        current_dir = os.getcwd()
        script_name = os.path.split(os.path.splitext(path)[0])[1]  # Get just the filename without extension

        try:
            # Change to build directory
            os.chdir(build_dir)
            
            try:
                # Run CMake
                subprocess.run(["cmake", ".."], 
                             check=True,
                             capture_output=True,
                             text=True)
                
                # Run build
                if platform.system() == "Windows":
                    subprocess.run(["cmake", "--build", ".", "--config", "Release"],
                                 check=True,
                                 capture_output=True,
                                 text=True)
                    executable_path = os.path.join(build_dir, "Release", f"{script_name}.exe")
                else:
                    subprocess.run(["make"],
                                 check=True,
                                 capture_output=True,
                                 text=True)
                    executable_path = os.path.join(build_dir, script_name)
                
                return executable_path

            except subprocess.CalledProcessError as e:
                print(Fore.RED + f"Build failed: {e.stderr}" + Fore.RESET)
                raise ValueError("Failed to build C++ script")

        finally:
            # Returning to original directory
            os.chdir(current_dir)

    def __get_subprocess_args(self, path: str, id: str, test_args=[]) -> List[object]:
        args = None
        
        if os.path.splitext(path)[1] == ".py":
            args = ["python3", path, id]
        elif os.path.splitext(path)[1] == ".cpp":
            executable_path = self.__build_cpp_scripts(path)
            args = [executable_path, id]

        if test_args:
            args.append(json.dumps(test_args))

        return args

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
            args = self.__get_subprocess_args(path, id, test_args)
            if not args:
                raise ValueError()
            result = subprocess.run(
                args=args,
                timeout=timeout,
                capture_output=True,
                check=False
            )
        except subprocess.TimeoutExpired:
            print(Fore.RED + f"Script timed out" + Fore.RESET)
            result = None
        except ValueError:
            print(Fore.RED + f"Subprocess args could not be created" + Fore.RESET)
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
        
        return result.returncode if result else 1
    
    def __read_process_logs(self, script_name: str, 
                            socket: zmq.Socket, 
                            stop_event: threading.Event, 
                            id: str):
        
        while not stop_event.is_set():
            try:
                # Receive topic and message with a timeout
                topic = socket.recv_string(flags=zmq.NOBLOCK)
                message = socket.recv_string(flags=zmq.NOBLOCK)
                
                # Verify the topic matches our script ID
                if topic == id:
                    print_string = (
                        f"{Fore.GREEN}{datetime.now()} [{script_name}]: "
                        f"{Fore.CYAN}{message}{Fore.RESET}"
                    )
                    print(print_string, flush=True)
                    
            except zmq.Again:
                # Timeout occurred, just continue the loop
                time.sleep(0.01)  # Add a small delay to prevent CPU spinning
                continue
            except zmq.ZMQError as e:
                print(f"ZMQ Error in log reader: {e}", file=sys.stderr)
                break
            except Exception as e:
                print(f"Unexpected error in log reader: {e}", file=sys.stderr)
                break
    
    def __get_processes(self):
        pass

    def __kill_process(self):
        pass
    
    def run_script(self, test_script: TestScript) -> Result:
        print(f"\n{Fore.YELLOW}{test_script.script_name.upper()} ({os.path.split(test_script.script_path)[-1]}){Fore.RESET}")

        script_path = os.path.join(TEST_SCRIPTS, test_script.script_path)

        result = self.__start_process(path=script_path, 
                             id=str(test_script.id), 
                             script_name=test_script.script_name,
                             timeout=test_script.timeout,
                             test_args=test_script.args)    
        
        return result