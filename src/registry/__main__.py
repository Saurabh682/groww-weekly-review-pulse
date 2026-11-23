import sys

from src.config import load_project_env
from src.registry.cli import run

load_project_env()
sys.exit(run())
