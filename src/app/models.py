from pydantic import BaseModel, Field
from typing import List, Any, Optional

from uuid import UUID, uuid4
from enum import IntEnum

from utils import CONFIG

import json

with open(CONFIG, "r", encoding="utf-8") as f:
    config = json.load(f)

class TestScript(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    script_name: str
    script_path: str
    timeout: int = Field(default=500)
    args: Optional[Any] = Field(default=None)

class TestScenario(BaseModel):
    scenario_name: str
    scripts: List[TestScript] 

class Result(IntEnum):
    SCRIPT_FAILURE = config["result_codes"]["SCRIPT_FAILURE"]
    PASS = config["result_codes"]["PASS"]
    FAIL = config["result_codes"]["FAIL"]