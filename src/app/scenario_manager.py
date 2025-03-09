from typing import List
import json

from script_runner import ScriptRunner
from models import TestScenario, Result

from collections import Counter

class ScenarioManager:
    def __init__(self, path: str) -> None:
        self.scenario = None
        self.__parse_scenario(path)

    def __parse_scenario(self, path: str) -> TestScenario:
        try:
            with open(path, "r", encoding="utf-8") as f:
                scenario_content = json.load(f)
            self.scenario = TestScenario(**scenario_content)
            return self.scenario
        except Exception as e:
            print("Scenario could not be parsed:", str(e))
    
    def run_scenario(self) -> None:
        if not self.scenario:
            return
        
        script_runner = ScriptRunner()
        results = []
        
        print(f"\nScenario started: {self.scenario.scenario_name}")
        for test_script in self.scenario.scripts:
            result = script_runner.run_script(test_script)
            results.append(result)

        print("\nScenario results:")
        counter = Counter(results)

        for i, j in counter.items():
            try:
                name = Result(i).name
            except:
                name = "UNKNOWN"
            print(f"{name}: {j}")

        print("\n" + "=" * 50)