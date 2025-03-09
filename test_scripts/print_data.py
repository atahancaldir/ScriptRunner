# setup

from api.script_runner_api import ScriptRunnerAPI, Result
import sys

id = sys.argv[1]
api = ScriptRunnerAPI(id)

# test script

args = api.get_args()

counter = 1
for i in range(args["line_count"]):
    string = f"{args["data"]}, count: {counter}"
    api.log(string)
    counter += 1

api.submit_result(Result.PASS)