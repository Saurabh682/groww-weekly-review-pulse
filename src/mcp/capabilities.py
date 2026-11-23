from pathlib import Path
from typing import Dict, List, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.config import resolve_project_path
from src.mcp.errors import MCPToolRefused

REQUIRED_CAPABILITIES = (
    "docs.create",
    "docs.get",
    "docs.clear",
    "docs.write",
    "gmail.create_draft",
    "gmail.update_draft",
)
MANDATORY_DENIED_PATTERNS = ("SEND", "DELETE", "TRASH")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CapabilityTarget(StrictModel):
    tool: str = Field(min_length=1)
    toolkit: str = Field(min_length=1)
    description: str


class ServerSettings(StrictModel):
    url_env: str = Field(min_length=1)
    api_key_env: str = Field(min_length=1)


class MCPPolicyConfig(StrictModel):
    draft_only: bool = True
    allow_send_email: bool = False
    max_retries: int = Field(default=3, ge=1, le=10)
    timeout_seconds: float = Field(default=30, gt=0)
    backoff_seconds: float = Field(default=0.5, ge=0)


class MCPConfigData(StrictModel):
    version: str
    provider: Literal["composio"]
    server: ServerSettings
    accounts: Dict[str, str]
    capabilities: Dict[str, CapabilityTarget]
    denied_tool_patterns: List[str]
    policy: MCPPolicyConfig = Field(default_factory=MCPPolicyConfig)

    @model_validator(mode="after")
    def _enforce_draft_only_allowlist(self) -> "MCPConfigData":
        if not self.policy.draft_only or self.policy.allow_send_email:
            raise ValueError("Policy violation: draft_only must be true and allow_send_email must be false.")
        patterns = {p.upper() for p in self.denied_tool_patterns}
        missing_patterns = [p for p in MANDATORY_DENIED_PATTERNS if p not in patterns]
        if missing_patterns:
            raise ValueError(f"denied_tool_patterns must include {', '.join(missing_patterns)} (CMP-01).")
        missing = [c for c in REQUIRED_CAPABILITIES if c not in self.capabilities]
        if missing:
            raise ValueError(f"Required capability missing from the map (MCP-01): {', '.join(missing)}.")
        for name, target in self.capabilities.items():
            if "send" in name.lower():
                raise ValueError(f"Forbidden capability '{name}': the pipeline is draft-only (MCP-17).")
            if name not in REQUIRED_CAPABILITIES:
                raise ValueError(f"Capability '{name}' is not part of the Composio allowlist (CMP-01).")
            if denied_pattern(self, target.tool):
                raise ValueError(f"Forbidden tool '{target.tool}' mapped to '{name}' (CMP-01, MCP-17).")
            if target.toolkit not in self.accounts:
                raise ValueError(f"Capability '{name}' uses toolkit '{target.toolkit}' with no account variable in 'accounts'.")
        return self


def denied_pattern(config: MCPConfigData, tool_slug: str) -> str | None:
    slug = tool_slug.upper()
    return next((p for p in config.denied_tool_patterns if p.upper() in slug), None)


def refuse_unlisted_tool(config: MCPConfigData, tool_slug: str) -> None:
    pattern = denied_pattern(config, tool_slug)
    if pattern:
        raise MCPToolRefused(f"Tool '{tool_slug}' matches the denied pattern '{pattern}' (CMP-01). Nothing was called.")
    if tool_slug not in {t.tool for t in config.capabilities.values()}:
        raise MCPToolRefused(f"Tool '{tool_slug}' is not in the Composio allowlist (CMP-01). Nothing was called.")


def resolve_capability(config: MCPConfigData, capability_name: str) -> CapabilityTarget:
    target = config.capabilities.get(capability_name)
    if target is None:
        raise MCPToolRefused(f"Capability '{capability_name}' is not in the Composio allowlist (CMP-01). Nothing was called.")
    refuse_unlisted_tool(config, target.tool)
    return target


def load_mcp_config(mcp_config_path: Path | str = "config/mcp.yaml") -> MCPConfigData:
    path = resolve_project_path(mcp_config_path)
    if not path.exists():
        raise FileNotFoundError(f"MCP configuration file not found at: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"MCP config in {path} must be a mapping")
    return MCPConfigData.model_validate(data)
