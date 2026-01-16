from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from interface_manager.logger import get_logger

logger = get_logger("api_context")


@dataclass
class APIRuntimeContext:
    """
    Execution context for a single API chat run.
    This is created in the router and passed to the api_handler.
    """

    provider: str                 # OPENAI | GEMINI | LOCAL
    agent_name: str               # model name

    base_url: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None

    run_mode: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    # -----------------------------
    # Construction helpers
    # -----------------------------
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APIRuntimeContext":
        ctx = cls(
            provider=data.get("provider"),
            agent_name=data.get("agent_name"),
            base_url=data.get("base_url"),
            temperature=data.get("temperature"),
            max_tokens=data.get("max_tokens"),
            top_p=data.get("top_p"),
            run_mode=data.get("run_mode"),
            extra=data.get("extra", {}),
        )
        ctx._validate()
        return ctx

    # -----------------------------
    # Validation
    # -----------------------------
    def _validate(self) -> None:
        if not self.provider:
            raise ValueError("provider is required in api_context")

        if not self.agent_name:
            raise ValueError("agent_name is required in api_context")

        self.provider = self.provider.upper().strip()
        self.agent_name = self.agent_name.strip()

        logger.info(
            "API Context validated | provider=%s model=%s",
            self.provider,
            self.agent_name,
        )

    # -----------------------------
    # Convenience
    # -----------------------------
    def is_openai(self) -> bool:
        return self.provider == "OPENAI"

    def is_gemini(self) -> bool:
        return self.provider == "GEMINI"

    def is_local(self) -> bool:
        return self.provider == "LOCAL"
