"""MCP capability mapping and resolution for Groww Weekly Review Pulse.

Guarantees:
- Send capabilities are forbidden (MCP-17). The app is draft-only.
- Required capabilities: docs.create and gmail.create_draft.
- Resolves abstract capabilities to concrete server/tool mappings.
"""

from pathlib import Path
from typing import Dict, List, Optional
import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class CapabilityTarget(BaseModel):
    server: str
    tool: str
    description: str
    required: bool = False
    fallback: Optional[str] = None


class MCPPolicyConfig(BaseModel):
    draft_only: bool = True
    allow_send_email: bool = False
    retry_on_network_error: bool = True
    max_retries: int = 3
    timeout_seconds: int = 30


class MCPConfigData(BaseModel):
    version: str = "1.0"
    allowed_capabilities: List[str]
    capabilities: Dict[str, CapabilityTarget]
    policy: MCPPolicyConfig = Field(default_factory=MCPPolicyConfig)

    @model_validator(mode="after")
    def validate_no_send_capabilities(self) -> "MCPConfigData":
        """Assert no send capabilities are allowed in the map (MCP-17)."""
        forbidden_terms = ["send", "send_email", "mail.send"]

        for cap in self.allowed_capabilities:
            for term in forbidden_terms:
                if term in cap.lower():
                    raise ValueError(
                        f"Forbidden capability '{cap}' detected! "
                        f"Send capabilities are strictly prohibited in the pulse pipeline (MCP-17)."
                    )

        for name, target in self.capabilities.items():
            for term in forbidden_terms:
                if term in name.lower() or term in target.tool.lower():
                    raise ValueError(
                        f"Forbidden tool mapping in capability '{name}' -> '{target.tool}'! "
                        f"Send actions are forbidden (MCP-17)."
                    )

        if not self.policy.draft_only or self.policy.allow_send_email:
            raise ValueError(
                "Policy violation: draft_only must be True and allow_send_email must be False."
            )

        return self


from src.config import resolve_project_path


def load_mcp_config(mcp_config_path: Path | str = "config/mcp.yaml") -> MCPConfigData:
    """Load and validate mcp.yaml, enforcing draft-only policy and forbidding send capabilities."""
    path = resolve_project_path(mcp_config_path)
    if not path.exists():
        raise FileNotFoundError(f"MCP configuration file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"MCP config in {path} must be a valid dictionary")

    return MCPConfigData.model_validate(data)


def resolve_capability(mcp_config: MCPConfigData, capability_name: str) -> CapabilityTarget:
    """Resolve a capability to its concrete tool target, or fail if missing or forbidden."""
    if capability_name not in mcp_config.capabilities:
        raise KeyError(
            f"Capability '{capability_name}' is not defined in the MCP capability map."
        )

    if capability_name not in mcp_config.allowed_capabilities:
        raise PermissionError(
            f"Capability '{capability_name}' is not in the allowed capabilities list."
        )

    return mcp_config.capabilities[capability_name]
