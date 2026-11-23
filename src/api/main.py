import os

from src.api.app import create_app
from src.api.auth import auth_from_env
from src.config import get_project_root
from src.registry.cli import default_service

app = create_app(
    service=default_service(),
    auth=auth_from_env(),
    outputs_root=get_project_root() / "outputs",
    cors_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()],
)
