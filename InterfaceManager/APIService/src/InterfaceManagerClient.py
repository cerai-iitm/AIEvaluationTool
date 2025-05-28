# Interface Manager Client Library 

import requests
from pydantic import BaseModel
from typing import Any, Optional

class PromptCreate(BaseModel):
    prompt_str: str

class InterfaceManagerClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.application_type: Optional[str] = None
        self.timeout = None
        
    def initialize(self) -> None:
        """Fetch configuration and set application type from config."""
        config = self.get_config()
        app_type_str = config.get("application_type")
        if not app_type_str:
            raise RuntimeError("Config missing 'application_type' field")
        self.application_type = app_type_str

    def login(self) -> requests.Response:
        return self._get("login")

    def logout(self) -> requests.Response:
        return self._get("logout")

    def chat(self, prompt: str) -> requests.Response:
        payload = PromptCreate(prompt_str=prompt).dict()
        return self._post("chat", json=payload)

    def get_config(self) -> dict[str, Any]:
        response = self._get("config")
        try:
            return response.json()
        except ValueError:
            raise RuntimeError("Invalid JSON response from /config endpoint")

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
