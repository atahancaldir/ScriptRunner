# setup

from api.script_runner_api import ScriptRunnerAPI, Result
import sys

id = sys.argv[1]
api = ScriptRunnerAPI(id)

# test script

import requests
import time

api.log("Reading facebook data")
response = requests.get("https://www.facebook.com")

time.sleep(5)

if response.status_code == 200:
    api.log(f"Facebook data fetched successfully with status code {response.status_code}")
    api.log(f"Content length: {len(response.content)}")
else:
    api.log(f"Google data could not be fetched. status code: {response.status_code}")

api.submit_result(Result.PASS)