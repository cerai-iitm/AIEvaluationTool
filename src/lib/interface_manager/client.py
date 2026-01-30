import requests
from typing import Any, List, Optional
from pydantic import BaseModel
from collections import defaultdict
import os, sys
import json 
from requests import Response

# Third-party model packages
from openai import OpenAI
from google import genai

# setup the relative import path for data module.
sys.path.append(os.path.dirname(__file__) + '/..')

from lib.utils import get_logger
from dotenv import load_dotenv
# Resolve the project root (two levels up from this file)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

# Construct full path to .env in project root
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(ENV_PATH)

class PromptCreate(BaseModel):
    chat_id: int
    prompt_list: List[str]

class InterfaceManagerClient:
    def __init__(self,
        base_url: str,
        application_type: str,
        agent_name: Optional[str] = "None",
        openui_email: Optional[str] = "None",
        openui_password: Optional[str] = "None",
        run_mode: Optional[str] = "None"):
        
        self.base_url = base_url.rstrip("/")
        self.application_type = application_type
        self.agent_name = agent_name

        # Normalize invalid placeholders
        if isinstance(self.agent_name, str) and self.agent_name.lower() in {"none", "", "null"}:
            self.agent_name = None
        
        self.local_llm_base_url: Optional[str] = None
        self.openui_email = openui_email
        self.openui_password = openui_password
        self.session = requests.Session()
        self.timeout = None
        self.run_mode = run_mode

        # Chat memory per chat_id
        self.conversations = defaultdict(list)

        self.logger = get_logger(__name__)

     # ---------------------------
    # Provider initialization
    # ---------------------------

    def _init_clients(self):
        self.openai_client = None
        self.gemini_client_ready = False

        if self.provider == "OPENAI":
            key = os.getenv("OPENAI_API_KEY")
            if not key:
                raise RuntimeError("Missing OPENAI_API_KEY in .env")
            self.openai_client = OpenAI(api_key=key)

        elif self.provider == "GEMINI":
            key = os.getenv("GEMINI_API_KEY")
            if not key:
                raise RuntimeError("Missing GEMINI_API_KEY in .env")
            self.gemini_client_ready = True

        elif self.provider == "LOCAL":
            if not getattr(self, "local_llm_base_url", None):
                raise RuntimeError(
                    "LOCAL provider selected but local_llm_base_url is not set. "
                    "Did you call apply_server_config()?"
                )

    # ---------------------------
    # Public API
    # ---------------------------

    def login(self) -> requests.Response:
        return self._get("login")

    def logout(self) -> requests.Response:
        return self._get("logout")

    def close(self) -> requests.Response:
        return self._get("close")

    def chat(self, chat_id: int, prompt_list: List[str]):
        prompt = " ".join(prompt_list)

        # Legacy flows
        if self.application_type in ["WHATSAPP_WEB", "WEBAPP"]:
            payload = PromptCreate(chat_id=chat_id, prompt_list=prompt_list).dict()
            return self._post("chat", json=payload)

        # Unified API flow
        if self.application_type == "API":
            payload = {
                "chat_id": chat_id,
                "prompt_list": prompt_list,
                "api_context": {
                    "provider": self._auto_detect_provider(),
                    "agent_name": self.agent_name,
                    "base_url": self.local_llm_base_url,
                    "run_mode": self.run_mode,
                }
            }
            return self._post("chat", json=payload)


        raise RuntimeError(f"Unsupported application type: {self.application_type}")

    def _wrap_dict_as_response(self, data: dict) -> Response:
        resp = Response()
        resp.status_code = 200
        resp._content = json.dumps(data).encode("utf-8")
        return resp

    # ---------------------------
    # Provider detection
    # ---------------------------

    def _auto_detect_provider(self):
        if not self.agent_name:
            raise RuntimeError(
                "agent_name (model) is not set. "
                "Please configure target.agent_name in config.json."
            )

        # If application_url is local → LOCAL provider
        if self.base_url.startswith("http://localhost") or self.base_url.startswith("http://127.0.0.1"):
            self.logger.info("Detected LOCAL provider via application_url")
            return "LOCAL"

        model = self.agent_name.lower()

        if model.startswith("gemini"):
            return "GEMINI"

        if model.startswith("gpt") or model.startswith("o"):
            return "OPENAI"

        raise RuntimeError(
            f"Unable to determine provider for model '{self.agent_name}'. "
            f"base_url='{self.base_url}'"
        )


    # ---------------------------
    # Chat dispatch
    # ---------------------------

    def _chat_api(self, chat_id: int, prompt: str):
        if self.provider == "GEMINI":
            return self._chat_gemini(chat_id, prompt)

        if self.provider == "LOCAL":
            return self._chat_local(chat_id, prompt)

        return self._chat_openai(chat_id, prompt)

    # ---------------------------
    # OpenAI
    # ---------------------------

    def _chat_openai(self, chat_id: int, prompt: str):
        self.logger.info("Using OpenAI client...")
        self.conversations[chat_id].append(
            {"role": "user", "content": prompt}
        )

        response = self.openai_client.chat.completions.create(
            model=self.agent_name,
            messages=self.conversations[chat_id]
        )

        assistant_text = response.choices[0].message["content"]
        self.logger.info(f"OpenAI response: {assistant_text}")
        self.conversations[chat_id].append(
            {"role": "assistant", "content": assistant_text}
        )

        return self._wrap_dict_as_response(
            {"response": [{"response": assistant_text}]}
        )

    # ---------------------------
    # Gemini
    # ---------------------------

    def _chat_gemini(self, chat_id: int, prompt: str):
        self.logger.info("Using Gemini client...")
        self.conversations[chat_id].append(
            {"role": "user", "content": prompt}
        )

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model=self.agent_name,
            contents=prompt
        )

        assistant_text = response.text
        self.logger.info(f"Gemini response: {assistant_text}")
        self.conversations[chat_id].append(
            {"role": "assistant", "content": assistant_text}
        )

        return self._wrap_dict_as_response(
            {"response": [{"response": assistant_text}]}
        )

    # ---------------------------
    # LOCAL (Ollama / vLLM / LM Studio)
    # ---------------------------

    def _chat_local(self, chat_id: int, prompt: str):
        self.logger.info("Using LOCAL Ollama server (OpenAI-compatible API)...")

        if not self.local_llm_base_url:
            raise RuntimeError("local_llm_base_url is not set")

        # Create OpenAI-compatible client pointing to Ollama
        client = OpenAI(
            base_url=f"{self.local_llm_base_url.rstrip('/')}/v1",
            api_key="ollama",  # required but unused
        )

        response = client.chat.completions.create(
            model=self.agent_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        
        assistant_text = response.choices[0].message.content

        return self._wrap_dict_as_response(
            {"response": [{"response": assistant_text}]}
        )

    def apply_server_config(self) -> None:
        """
        Pull server config and bind relevant fields to the client runtime.
        Assumes flat config (no 'target' nesting).
        """
        cfg = self.get_config()

        # Bind agent/model name (required)
        agent = cfg.get("agent_name")
        if not agent:
            raise RuntimeError("agent_name is missing from server config")

        self.agent_name = agent.lower()

        # Bind local LLM inference URL (optional but required for LOCAL)
        app_url = cfg.get("application_url")
        if app_url:
            self.local_llm_base_url = app_url.rstrip("/")

        self.logger.debug(
            "Applied server config → "
            f"agent_name={self.agent_name}, "
            f"local_llm_base_url={self.local_llm_base_url}"
        )

    def get_config(self) -> dict[str, Any]:
        response = self._get("config")
        try:
            return response.json()
        except ValueError:
            raise RuntimeError("Invalid JSON response from /config endpoint")

    def update_config(self, config: dict[str, Any]) -> None:
        response = self._post("config", json=config)
        if response.status_code == 200:
            self.logger.debug("Updating config.json on server")
        else:
            raise RuntimeError(f"Config update failed on server: {response.status_code} - {response.text}")

    def sync_config(self, overrides: dict[str, Any]) -> bool:
        try:
            server_config = self.get_config()
            self.logger.debug("Fetched server-side config.")
        except RuntimeError:
            self.logger.error("Could not fetch server config. Proceeding with empty config.")
            server_config = {}

        updated_config = server_config.copy()
        for key, value in overrides.items():
            if value is not None:
                updated_config[key] = value
        try:
            self.update_config(updated_config)
            self.logger.debug("Server config updated successfully.")
            return True
        except RuntimeError as e:
            self.logger.error(f"Failed to update server config: {e}")
            return False

    def _get(self, endpoint: str) -> requests.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response
        except requests.HTTPError as e:
            raise RuntimeError(
                f"GET request to {url} failed: {e.response.status_code} - {e.response.text}"
            ) from e
        except requests.RequestException as e:
            raise RuntimeError(f"GET request to {url} failed: {e}") from e

    def _post(self, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.post(url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response
        except requests.HTTPError as e:
            raise RuntimeError(
                f"POST request to {url} failed: {e.response.status_code} - {e.response.text}"
            ) from e
        except requests.RequestException as e:
            raise RuntimeError(f"POST request to {url} failed: {e}") from e
