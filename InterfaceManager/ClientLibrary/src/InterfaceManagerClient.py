import requests
from typing import Any, List
from pydantic import BaseModel

class PromptCreate(BaseModel):
    chat_id: int
    prompt_list: List[str]

class InterfaceManagerClient:
    def __init__(
        self,
        base_url: str,
        application_type: str = "None",
        model_name: str = "None",
        openui_email: str = "None",
        openui_password: str = "None",
        run_mode: str = "None"
    ):
        self.base_url = base_url.rstrip("/")
        self.application_type = application_type
        self.model_name = model_name
        self.openui_email = openui_email
        self.openui_password = openui_password
        self.session = requests.Session()
        self.timeout = None
        self.run_mode = run_mode

    def initialize(self) -> None:
        if not self.application_type:
            raise RuntimeError("Config missing 'application_type' field")
        print(f"Initialized with application_type: {self.application_type}")

    def login(self) -> requests.Response:
        return self._get("login")

    def logout(self) -> requests.Response:
        return self._get("logout")

    def chat(self, chat_id: int, prompt_list: List[str]) -> requests.Response:
        payload = PromptCreate(chat_id=chat_id, prompt_list=prompt_list).dict()
        return self._post("chat", json=payload)

    def get_config(self) -> dict[str, Any]:
        response = self._get("config")
        try:
            return response.json()
        except ValueError:
            raise RuntimeError("Invalid JSON response from /config endpoint")

    def update_config(self, config: dict[str, Any]) -> None:
        response = self._post("config", json=config)
        if response.status_code == 200:
            print("Updating config.json on server")
        else:
            raise RuntimeError(f"Config update failed on server: {response.status_code} - {response.text}")

    def sync_config(self, overrides: dict[str, Any]) -> bool:
        try:
            server_config = self.get_config()
            print("Fetched server-side config.")
        except RuntimeError:
            print("Could not fetch server config. Proceeding with empty config.")
            server_config = {}

        updated_config = server_config.copy()
        for key, value in overrides.items():
            if value is not None:
                updated_config[key] = value
        try:
            self.update_config(updated_config)
            print("Server config updated successfully.")
            return True
        except RuntimeError as e:
            print(f"Failed to update server config: {e}")
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
