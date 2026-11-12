"""Configuration models and loader for Groww Weekly Review Pulse.

Enforces hard architectural constraints at startup:
- max_themes <= 5 (CFG-01)
- max_words <= 250 (CFG-02)
- quotes == 3 and actions == 3 (CFG-03)
- automated collection blocked by default (ING-14, SEC-05)
- App Store source rejected (ING-15)
- safe secret handling without leaking values (CFG-05, CFG-06)
"""

import os
import re
import warnings
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AppConfig(BaseModel):
    name: str = "Groww"
    play_store_id: str = "com.nextbillion.groww"
    region: str = "in"


class WindowConfig(BaseModel):
    weeks: int = Field(default=12, ge=8, le=12)


class AppStoreSourceConfig(BaseModel):
    enabled: bool = False

    @field_validator("enabled")
    @classmethod
    def reject_app_store_enabled(cls, v: bool) -> bool:
        if v:
            raise ValueError(
                "App Store source is not supported in this build. "
                "Only Google Play Store is active."
            )
        return v


class PlayStoreSourceConfig(BaseModel):
    mode: str = "csv_import"
    path: Path = Path("data/imports/play_reviews.csv")
    allow_automated: bool = False

    @model_validator(mode="after")
    def validate_automated_guard(self) -> "PlayStoreSourceConfig":
        env_allowed = os.getenv("ALLOW_AUTOMATED_PLAY_COLLECTION", "false").lower() == "true"
        if self.mode == "automated" or self.allow_automated:
            if not env_allowed:
                raise ValueError(
                    "Automated Google Play collection is disabled by default. "
                    "A recorded compliance approval and ALLOW_AUTOMATED_PLAY_COLLECTION=true are required."
                )
        return self


class SourcesConfig(BaseModel):
    app_store: AppStoreSourceConfig = Field(default_factory=AppStoreSourceConfig)
    play_store: PlayStoreSourceConfig = Field(default_factory=PlayStoreSourceConfig)


class ThemesConfig(BaseModel):
    max_themes: int = Field(default=5)
    min_cluster_share: float = Field(default=0.03, ge=0.0, le=1.0)
    top_n: int = Field(default=3)

    @field_validator("max_themes")
    @classmethod
    def validate_max_themes(cls, v: int) -> int:
        if v > 5:
            raise ValueError(f"max_themes cannot exceed 5 (CFG-01 hard constraint, got {v})")
        if v < 1:
            raise ValueError("max_themes must be at least 1")
        return v


class NoteConfig(BaseModel):
    max_words: int = Field(default=250)
    quotes: int = Field(default=3)
    actions: int = Field(default=3)

    @field_validator("max_words")
    @classmethod
    def validate_max_words(cls, v: int) -> int:
        if v > 250:
            raise ValueError(f"max_words cannot exceed 250 (CFG-02 hard constraint, got {v})")
        if v < 50:
            raise ValueError("max_words must be at least 50")
        return v

    @field_validator("quotes")
    @classmethod
    def validate_quotes(cls, v: int) -> int:
        if v != 3:
            raise ValueError(f"quotes count must be exactly 3 (CFG-03 constraint, got {v})")
        return v

    @field_validator("actions")
    @classmethod
    def validate_actions(cls, v: int) -> int:
        if v != 3:
            raise ValueError(f"actions count must be exactly 3 (CFG-03 constraint, got {v})")
        return v


class LLMConfig(BaseModel):
    provider: str = "gemini"
    model: str = "gemini-2.5-flash"
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)


class EmailConfig(BaseModel):
    to: str = "self@groww-pulse.local"


class MCPConfig(BaseModel):
    config: Path = Path("config/mcp.yaml")


class PulseConfig(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    window: WindowConfig = Field(default_factory=WindowConfig)
    sources: SourcesConfig = Field(default_factory=SourcesConfig)
    themes: ThemesConfig = Field(default_factory=ThemesConfig)
    note: NoteConfig = Field(default_factory=NoteConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)

    model_config = ConfigDict(extra="allow")


def _expand_env_vars(data: Any) -> Any:
    """Recursively expand ${VAR} or $VAR in strings."""
    if isinstance(data, dict):
        return {k: _expand_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_expand_env_vars(item) for item in data]
    elif isinstance(data, str):
        pattern = re.compile(r"\$\{([A-Za-z0-9_]+)\}")
        matches = pattern.findall(data)
        for var in matches:
            val = os.getenv(var, "")
            data = data.replace(f"${{{var}}}", val)
        return data
    return data


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_project_root() -> Path:
    """Return the absolute path to the groww-weekly-review-pulse root directory."""
    return PROJECT_ROOT


def resolve_project_path(path_input: Path | str) -> Path:
    """Resolve a path against cwd first, then against PROJECT_ROOT (CFG-09)."""
    p = Path(path_input)
    if p.is_absolute():
        return p
    if p.exists():
        return p.resolve()
    candidate = PROJECT_ROOT / p
    if candidate.exists() or (PROJECT_ROOT / p.parent).exists():
        return candidate.resolve()
    return candidate.resolve()


def load_pulse_config(config_path: Path | str = "config/pulse.yaml") -> PulseConfig:
    """Load and validate pulse.yaml configuration.
    
    Warns on unknown top-level keys (CFG-07).
    Fails fast with clear errors on missing or invalid YAML (CFG-04).
    """
    path = resolve_project_path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)
    except Exception as exc:
        raise ValueError(f"Failed to parse YAML from {path}: {exc}") from exc

    if not isinstance(raw_data, dict):
        raise ValueError(f"Config in {path} must be a YAML dictionary")

    # Expand environment variables
    expanded_data = _expand_env_vars(raw_data)

    known_keys = {"app", "window", "sources", "themes", "note", "llm", "email", "mcp"}
    unknown_keys = set(expanded_data.keys()) - known_keys
    if unknown_keys:
        warnings.warn(
            f"Unknown configuration keys found in {path}: {sorted(unknown_keys)}",
            UserWarning,
            stacklevel=2,
        )

    return PulseConfig.model_validate(expanded_data)


def require_secret(env_var_name: str) -> str:
    """Retrieve required secret from environment, failing clearly without leaking value (CFG-05)."""
    val = os.getenv(env_var_name)
    if not val:
        raise ValueError(f"Missing required secret in environment variable: {env_var_name}")
    return val
