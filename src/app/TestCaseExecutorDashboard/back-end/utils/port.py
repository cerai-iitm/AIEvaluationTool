import json
import socket
import threading
from urllib.parse import urlparse
import psutil
import requests
from fastapi import HTTPException
from lib.utils import get_logger, get_logger_verbosity
from services.ws_manager import ws_manager

logger = get_logger(__name__)


_active_watchers: dict[str, threading.Event] = {}
_active_stop_lock = threading.Lock()

def set_active_stop_watcher(event, run_id=None):
    """Registers (or removes, if event is None) the stop watcher for one run_id."""
    global _active_watchers
    with _active_stop_lock:
        if event is None:
            if run_id is not None:
                _active_watchers.pop(str(run_id), None)
            return
        _active_watchers[str(run_id)] = event

def stop_active_run(run_id, config_path) -> bool:
    """Signal the requested run to stop and close its own Interface Manager browser session."""
    with _active_stop_lock:
        watcher = _active_watchers.get(str(run_id))
        if watcher is None or watcher.is_set():
            return False
        watcher.set()

    logger.info(f"🛑 Stop requested for test run {run_id}")
    close_run_driver(run_id, config_path)
    return True

def reset_frontend_disconnect_state():
    ws_manager.disconnected_by_frontend = False

def is_frontend_disconnect_requested(stop_event: threading.Event | None = None) -> bool:
    """
    Whether THIS run should stop. Deliberately does not consult the shared
    ws_manager.disconnected_by_frontend flag — that flag flips whenever ANY
    browser tab disconnects (even one unrelated to this run), which would
    otherwise abort every concurrently running test whenever any one user's
    tab closes. This run's own stop_event is the only correct signal.
    """
    return bool(stop_event and stop_event.is_set())

def on_frontend_disconnect(config_path, run_ids=None):
    """
    A browser tab disconnected. Only close the browser session(s) for the
    run(s) that tab was subscribed to — never the shared Interface Manager
    service, which other concurrent runs still depend on.
    """
    ws_manager.disconnected_by_frontend = True
    run_ids = run_ids or []
    with _active_stop_lock:
        watchers = [(rid, _active_watchers.get(str(rid))) for rid in run_ids]

    any_active = False
    for rid, watcher in watchers:
        if watcher is None:
            continue
        any_active = True
        watcher.set()

    if not any_active:
        logger.info("👀 Frontend disconnected, but no active run for that tab — nothing to close")
        return

    logger.info(f"🛑 Frontend tab closed — closing browser session(s) for run(s): {run_ids}")
    for rid, watcher in watchers:
        if watcher is None:
            continue
        try:
            close_run_driver(rid, config_path)
        except Exception as e:
            logger.error(f"Failed to close browser session for run {rid} on tab close: {e}")


def check_service(url: str, name: str):
    try:
        response = requests.get(url, timeout=3)
        logger.info(f"Health check for {name} service at {url} returned status code {response.status_code}")
        if response.status_code < 400:
            return f"{name} service is reachable at {url}"
        if response.status_code >= 400:
            raise HTTPException(
                status_code=503,
                detail=f"{name} service is not healthy at {url}"
            )
    except requests.exceptions.RequestException:
        raise HTTPException(
            status_code=503,
            detail=f"{name} service is not reachable at {url}"
        )
    

def ensure_interface_manager_port_running(
    config_path: str,
    timeout: float = 1.5
):
    # 1️⃣ Read config.json
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read Interface Manager config: {str(e)}"
        )

    # 2️⃣ Extract base_url
    config_interface_manager = config.get("interface_manager", {})
    if config_interface_manager.get("docker"):
        base_url = config_interface_manager.get("base_url")
    else:
        base_url = config_interface_manager.get("base_url_local")
        
    if not base_url:
        raise HTTPException(
            status_code=500,
            detail="base_url missing in Interface Manager config"
        )

    # 3️⃣ Parse host & port
    parsed = urlparse(base_url)
    host = parsed.hostname
    port = parsed.port

    if not host or not port:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid base_url in Interface Manager config: {base_url}"
        )

    # 4️⃣ TCP port check
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)

    try:
        result = sock.connect_ex((host, port))
        if result != 0:
            raise HTTPException(
                status_code=503,
                detail=f"Interface Manager is not running at {host}:{port}"
            )
    finally:
        sock.close()    


def close_run_driver(run_id, config_path: str):
    """
    Close only this run's own browser session on the (shared) Interface
    Manager service, by session_key=run_id — never the whole service, since
    other concurrent runs may still be using it.
    """
    try:
        with open(config_path, "r") as f:
            config = json.load(f)

        im_config = config.get("interface_manager", {})
        is_docker = bool(im_config.get("docker"))
        base_url = im_config.get("base_url") if is_docker else im_config.get("base_url_local")
        if not base_url:
            return

        try:
            requests.get(f"{base_url}/close", params={"session_key": str(run_id)}, timeout=3)
            logger.info(f"Interface Manager /close called for run {run_id}")
        except Exception as e:
            logger.error(f"/close failed for run {run_id} (IM may already be dead): {e}")
    except Exception as e:
        logger.error(f"Failed to close browser session for run {run_id}: {e}")


def stop_interface_manager(config_path: str, profile_path: str = "/home/varun/test_profile"):
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        
        im_config = config.get("interface_manager", {})
        is_docker = bool(im_config.get("docker"))
        if is_docker:
            base_url = im_config.get("base_url")
        else:
            base_url = im_config.get("base_url_local")  # 👈 this is "http://localhost:8000"
        parsed = urlparse(base_url)
        port = parsed.port
        
        if not port:
            return

        # 1️⃣ Try /close first
        try:
            requests.get(f"{base_url}/close", timeout=3)
            logger.info("Interface Manager /close called successfully")
        except Exception as e:
            logger.error(f"/close failed (IM may already be dead): {e}")

        if is_docker:
            logger.info("Docker mode detected; /close requested, skipping local PID cleanup")
            return

        # 2️⃣ Kill ALL python processes on that port
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for conn in proc.net_connections(kind='inet'):
                    if conn.laddr.port == port:
                        logger.info(f"Killing PID {proc.pid} ({proc.name()}) on port {port}")
                        proc.kill()
                        proc.wait(timeout=3)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # 3️⃣ Kill ONLY Chrome with the IM profile — not all Chrome!
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'chrome' in (proc.info['name'] or '').lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if f'user-data-dir={profile_path}' in cmdline:  # 👈 only IM's Chrome
                        logger.info(f"Killing IM Chrome PID {proc.pid} with profile {profile_path}")
                        proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        logger.info("✅ IM and IM Chrome killed — other Chrome windows untouched!")

    except Exception as e:
        logger.error(f"Failed to stop interface manager: {e}")

def get_chrome_pids_on_port(port: int) -> set:
    """Get Chrome PIDs that are children of the IM process on this port"""
    chrome_pids = set()
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for conn in proc.net_connections(kind='inet'):
                    if conn.laddr.port == port:
                        # Found the IM process — now get its children
                        im_proc = psutil.Process(proc.pid)
                        for child in im_proc.children(recursive=True):
                            if 'chrome' in child.name().lower():
                                chrome_pids.add(child.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        logger.error(f"Error getting chrome pids: {e}")
    return chrome_pids   

def watch_chrome_and_kill_im(config_path: str):
    import time

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        base_url = config.get("base_url")
        parsed = urlparse(base_url)
        port = parsed.port

        # 1️⃣ Wait for Chrome to actually launch first
        logger.info("👀 Watcher waiting for Chrome to launch...")
        chrome_pids = set()
        for _ in range(15):  # wait up to 15 seconds for Chrome to appear
            chrome_pids = get_chrome_pids_on_port(port)
            if chrome_pids:
                logger.info(f"👀 Watching specific Chrome PIDs: {chrome_pids}")
                break
            time.sleep(1)

        if not chrome_pids:
            logger.info("👀 No Chrome found — watcher exiting")
            return

        # 2️⃣ Now watch ONLY those specific Chrome PIDs
        while True:
            time.sleep(2)
            any_alive = False
            for pid in chrome_pids:
                try:
                    proc = psutil.Process(pid)
                    if proc.is_running():
                        any_alive = True
                        break
                except psutil.NoSuchProcess:
                    continue

            if not any_alive:
                logger.info("💀 IM Chrome is dead — killing IM!")
                stop_interface_manager(config_path)
                break

        logger.info("👀 Chrome watcher stopped")

    except Exception as e:
        logger.error(f"Watcher error: {e}")

def watch_im_process(config_path: str, profile_path: str, stop_event: threading.Event):
    import time

    def is_im_chrome_open() -> bool:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'chrome' in (proc.info['name'] or '').lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if f'user-data-dir={profile_path}' in cmdline:
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    logger.info("👀 Waiting for IM Chrome to open...")

    # 1️⃣ Wait for Chrome with this profile to open
    for _ in range(30):
        if stop_event.is_set():
            logger.info("👀 Run finished — watcher exiting")
            return
        if is_im_chrome_open():
            logger.info(f"👀 IM Chrome is open — watching profile {profile_path}")
            break
        time.sleep(1)
    else:
        logger.info("👀 IM Chrome never opened — watcher exiting")
        

    # 2️⃣ Now watch if it closes
    while True:
        time.sleep(2)
        if stop_event.is_set():
            if ws_manager.disconnected_by_frontend:  # 👈 check why it stopped
                logger.info("🛑 Frontend disconnected — killing IM")
                stop_interface_manager(config_path)
        else:
            logger.info("👀 Run completed normally — NOT killing IM ✅")
        return
        if not is_im_chrome_open():
            logger.info("💀 IM Chrome closed — killing IM!")
            stop_interface_manager(config_path)
            break

           

             
