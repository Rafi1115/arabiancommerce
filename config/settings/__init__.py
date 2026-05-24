import os
import environ
from pathlib import Path

# Initialize environ
env = environ.Env()

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Read .env file
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    environ.Env.read_env(env_file)

# Get environment type
DEBUG = env("DEBUG", default="False")

print(f"🐉 DEBUG mode is set to: {DEBUG} 🚸")

if DEBUG == "False":
    from .production import *
else:
    from .development import *