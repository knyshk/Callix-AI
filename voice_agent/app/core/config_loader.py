"""
Config Loader
Loads JSON configuration files for intents, FSM states, and response prompts.
Supports organization-specific config profiles.
"""
import json
import os
from pathlib import Path
from functools import lru_cache


CONFIG_BASE = Path(__file__).resolve().parent.parent.parent / "configs"


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=8)
def load_intents_config(profile: str = "default") -> dict:
    """Load intents configuration for a given organization profile."""
    path = CONFIG_BASE / profile / "intents.json"
    return _load_json(path)


@lru_cache(maxsize=8)
def load_fsm_config(profile: str = "default") -> dict:
    """Load FSM state machine configuration."""
    path = CONFIG_BASE / profile / "fsm.json"
    return _load_json(path)


@lru_cache(maxsize=8)
def load_prompts_config(profile: str = "default") -> dict:
    """Load response prompt templates."""
    path = CONFIG_BASE / profile / "prompts.json"
    return _load_json(path)
