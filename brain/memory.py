import json
import os
from datetime import datetime
from loguru import logger

MEMORY_FILE = "friday_memory.json"

def _load() -> dict:
    """Load memory from disk."""
    if not os.path.exists(MEMORY_FILE):
        return {"facts": [], "preferences": {}, "created": str(datetime.now())}
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Memory load failed: {e}")
        return {"facts": [], "preferences": {}, "created": str(datetime.now())}

def _save(memory: dict):
    """Save memory to disk."""
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=2)
    except Exception as e:
        logger.error(f"Memory save failed: {e}")

def remember(fact: str):
    """
    Save a fact to long-term memory.
    Usage: remember("User's name is Yash")
    """
    memory = _load()
    entry = {
        "fact": fact,
        "timestamp": str(datetime.now())
    }
    memory["facts"].append(entry)
    _save(memory)
    logger.success(f"Remembered: {fact}")

def recall_all() -> str:
    """
    Returns all stored facts as a formatted string.
    Injected into the brain's system prompt so FRIDAY always knows them.
    """
    memory = _load()
    facts = memory.get("facts", [])

    if not facts:
        return ""

    lines = "\n".join(f"- {f['fact']}" for f in facts[-20:])  # last 20 facts
    return f"\nThings you know about the user:\n{lines}\n"

def forget_all():
    """Wipe long-term memory."""
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)
    logger.info("Long-term memory wiped.")