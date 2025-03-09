from os.path import dirname, realpath, join

MAIN_DIRECTORY = dirname(dirname(dirname(realpath(__file__))))
CONFIG = join(MAIN_DIRECTORY, "config.json")
TEST_SCENARIOS = join(MAIN_DIRECTORY, "test_scenarios")
TEST_SCRIPTS = join(MAIN_DIRECTORY, "test_scripts")