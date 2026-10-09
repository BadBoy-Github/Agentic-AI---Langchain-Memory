"""Configuration loader for the Gemini ReAct Agent."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from current directory or parent directory
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# Retrieve API key (accepts either GEMINI_API_KEY or GOOGLE_API_KEY)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# Synchronize into environment variables for underlying libraries
if GEMINI_API_KEY:
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

# Model settings
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))


def validate_api_key() -> bool:
    """Validates that a valid Gemini API key is configured.
    
    Returns:
        bool: True if key is present and not a dummy placeholder, False otherwise.
    """
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key or key.strip() in ("", "your_gemini_api_key_here", "your_api_key_here"):
        return False
    return True


def get_api_key_or_exit() -> str:
    """Returns the Gemini API key or terminates with a user-friendly instruction."""
    if not validate_api_key():
        print("\n" + "=" * 65)
        print("[!] ERROR: Gemini API key is missing or not configured!")
        print("=" * 65)
        print("Please configure your Gemini API key in the `.env` file:")
        print(f"File location: {ENV_PATH}")
        print("\nExample line:")
        print("  GEMINI_API_KEY=AIzaSy...")
        print("\nYou can get a free API key at: https://aistudio.google.com/")
        print("=" * 65 + "\n")
        sys.exit(1)
    return GEMINI_API_KEY
