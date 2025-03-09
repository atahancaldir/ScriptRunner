import os, sys

from utils import TEST_SCENARIOS
from scenario_manager import ScenarioManager

dialogues = {
    "initial" : "\nWelcome to script Runner. Select a scenario from below to run by typing scenario number:\n",
    "invalid_selection" : "Selection is invalid, try again: ",
}

while True:
    scenario_list = os.listdir(TEST_SCENARIOS)
    print(dialogues["initial"])
    for index, test_scenario in enumerate(scenario_list, start=1):
        print(index, "-", os.path.split(test_scenario)[-1])
    print("\nType 'q' to quit\n")
    print("Selection: ", end="")

    while True:
        scenario_index = input()
        if scenario_index == "q":
            sys.exit()
        if not scenario_index.isdigit() or int(scenario_index) not in range(len(scenario_list)+1):
            print(dialogues["invalid_selection"], end="")
            continue
        break
    
    scenario_path = os.path.join(TEST_SCENARIOS, scenario_list[int(scenario_index)-1])
    scenario_manager = ScenarioManager(scenario_path)
    scenario_manager.run_scenario()
    
