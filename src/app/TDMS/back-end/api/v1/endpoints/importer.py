import asyncio
import contextlib
import json
import os
import sys
import tempfile
from typing import Any

from config.settings import settings
from fastapi import APIRouter, BackgroundTasks, File, Header, HTTPException, UploadFile, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from jose import JWTError, jwt

importer_router = APIRouter(prefix="/api/importer")


class ImporterStatusManager:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._run_lock = asyncio.Lock()
        self._is_running = False
        self._last_event: dict[str, Any] = {
            "event": "idle",
            "status": "idle",
            "message": "Importer is idle.",
        }

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._clients.add(websocket)
            last_event = dict(self._last_event)
        await websocket.send_json(last_event)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(websocket)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        async with self._lock:
            self._last_event = dict(payload)
            clients = list(self._clients)

        disconnected: list[WebSocket] = []
        for websocket in clients:
            try:
                await websocket.send_json(payload)
            except Exception:
                disconnected.append(websocket)

        if disconnected:
            async with self._lock:
                for websocket in disconnected:
                    self._clients.discard(websocket)

    async def try_start(self) -> bool:
        async with self._run_lock:
            if self._is_running:
                return False
            self._is_running = True
            return True

    async def finish(self) -> None:
        async with self._run_lock:
            self._is_running = False

    @property
    def last_event(self) -> dict[str, Any]:
        return dict(self._last_event)


status_manager = ImporterStatusManager()


def _validate_access_token(token: str | None) -> dict[str, Any]:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization token missing")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    return payload


def _extract_bearer_token(authorization: str | None) -> str | None:
    if authorization and authorization.startswith("Bearer "):
        return authorization[len("Bearer ") :]
    return None


def _resolve_importer_config(importer_dir: str) -> str:
    candidates = [
        os.path.join(importer_dir, "config.json"),
        os.path.abspath(os.path.join(importer_dir, "../../../config.json")),
        os.path.abspath(os.path.join(importer_dir, "../../config.json")),
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    raise HTTPException(
        status_code=404,
        detail=f"Config file not found. Checked: {', '.join(candidates)}",
    )


def _validate_testcases_seed_payload(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded testcases JSON must be an object like data/updated_datapoints.json.",
        )

    required_case_fields = ("PROMPT_ID", "SYSTEM_PROMPT", "PROMPT")
    for metric_id, metric_payload in payload.items():
        if not isinstance(metric_payload, dict) or not isinstance(metric_payload.get("cases"), list):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Metric '{metric_id}' must contain a cases array.",
            )

        for index, testcase in enumerate(metric_payload["cases"], start=1):
            if not isinstance(testcase, dict):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Metric '{metric_id}' case {index} must be a JSON object.",
                )

            missing_fields = [
                field
                for field in required_case_fields
                if not isinstance(testcase.get(field), str) or not testcase.get(field, "").strip()
            ]
            if missing_fields:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Metric '{metric_id}' case {index} is missing required field(s): {', '.join(missing_fields)}.",
                )


async def _build_importer_config_with_uploaded_testcases(
    config_path: str,
    upload: UploadFile | None,
) -> tuple[str, list[str]]:
    if upload is None:
        return config_path, []

    if not upload.filename or not upload.filename.lower().endswith(".json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a .json file.",
        )

    raw_upload = await upload.read()
    try:
        decoded_upload = raw_upload.decode("utf-8")
        uploaded_payload = json.loads(decoded_upload)
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded JSON file must be UTF-8 encoded.",
        ) from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}.",
        ) from exc

    _validate_testcases_seed_payload(uploaded_payload)

    with open(config_path, "r", encoding="utf-8") as config_file:
        importer_config = json.load(config_file)

    if not isinstance(importer_config.get("files"), dict):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Importer config is missing the files section.",
        )

    temp_paths: list[str] = []
    upload_temp = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".json",
        prefix="tdms-uploaded-testcases-",
        delete=False,
    )
    try:
        json.dump(uploaded_payload, upload_temp, ensure_ascii=False, indent=2)
        upload_temp.write("\n")
    finally:
        upload_temp.close()
    temp_paths.append(upload_temp.name)

    importer_config["files"]["testcases"] = upload_temp.name

    config_temp = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".json",
        prefix="tdms-importer-config-",
        delete=False,
    )
    try:
        json.dump(importer_config, config_temp, ensure_ascii=False, indent=2)
        config_temp.write("\n")
    finally:
        config_temp.close()
    temp_paths.append(config_temp.name)

    return config_temp.name, temp_paths


def _cleanup_temp_paths(temp_paths: list[str] | None) -> None:
    for temp_path in temp_paths or []:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temp_path)


async def _stream_importer_output(stream: asyncio.StreamReader | None) -> None:
    if stream is None:
        return

    while True:
        line = await stream.readline()
        if not line:
            break

        message = line.decode(errors="replace").strip()
        if not message:
            continue

        await status_manager.broadcast(
            {
                "event": "log",
                "status": "running",
                "message": message,
            }
        )


async def _run_importer_task(
    importer_path: str,
    config_path: str,
    python_executable: str,
    workspace_root: str,
    temp_paths: list[str] | None = None,
) -> None:
    try:
        await status_manager.broadcast(
            {
                "event": "running",
                "status": "running",
                "message": "Importer started. Streaming live updates...",
            }
        )

        process = await asyncio.create_subprocess_exec(
            python_executable,
            importer_path,
            "--config",
            config_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=workspace_root,
        )

        await _stream_importer_output(process.stdout)
        return_code = await process.wait()

        if return_code == 0:
            await status_manager.broadcast(
                {
                    "event": "success",
                    "status": "success",
                    "message": "Data imported successfully. The dashboard will refresh shortly.",
                }
            )
        else:
            await status_manager.broadcast(
                {
                    "event": "error",
                    "status": "error",
                    "message": f"Importer failed with exit code {return_code}.",
                }
            )
    except Exception as exc:
        await status_manager.broadcast(
            {
                "event": "error",
                "status": "error",
                "message": f"Importer failed: {exc}",
            }
        )
        print("Importer background task failed", file=sys.stderr)
    finally:
        _cleanup_temp_paths(temp_paths)
        await status_manager.finish()


@importer_router.websocket("/ws")
async def importer_status_websocket(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    try:
        _validate_access_token(token)
    except HTTPException:
        await websocket.close(code=4401)
        return

    await status_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await status_manager.disconnect(websocket)
    except Exception:
        await status_manager.disconnect(websocket)
        with contextlib.suppress(Exception):
            await websocket.close()


@importer_router.post("/run", summary="Run data importer", tags=["Importer"])
async def run_importer(
    background_tasks: BackgroundTasks,
    authorization: str | None = Header(default=None),
    file: UploadFile | None = File(default=None),
):
    """
    Starts the importer script in a background task so long-running imports can complete.
    """
    try:
        _validate_access_token(_extract_bearer_token(authorization))

        importer_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../../../importer/main.py")
        )

        if not os.path.exists(importer_path):
            raise HTTPException(
                status_code=404,
                detail=f"Importer script not found at {importer_path}",
            )

        importer_dir = os.path.dirname(importer_path)
        config_path = _resolve_importer_config(importer_dir)
        config_path, temp_paths = await _build_importer_config_with_uploaded_testcases(config_path, file)

        if not await status_manager.try_start():
            _cleanup_temp_paths(temp_paths)
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "status": "running",
                    "message": status_manager.last_event.get("message", "Importer is already running."),
                },
            )

        workspace_root = os.path.abspath(os.path.join(importer_dir, "../../.."))
        python_executable = sys.executable

        await status_manager.broadcast(
            {
                "event": "accepted",
                "status": "running",
                "message": "Importer request accepted. Waiting for process output...",
            }
        )

        background_tasks.add_task(
            _run_importer_task,
            importer_path,
            config_path,
            python_executable,
            workspace_root,
            temp_paths,
        )

        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted",
                "message": "Importer started in background. Live updates are available over websocket.",
            },
        )

    except HTTPException:
        raise
    except Exception as exc:
        await status_manager.finish()
        raise HTTPException(
            status_code=500,
            detail=f"Error running importer: {str(exc)}",
        ) from exc
