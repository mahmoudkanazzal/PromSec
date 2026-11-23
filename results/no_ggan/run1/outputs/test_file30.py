import json
import logging
import os
import subprocess
import tempfile
import hashlib
from typing import Dict, Any
import requests
from salt.exceptions import CommandExecutionError

log = logging.getLogger(__name__)

_MAX_SCRIPT_SIZE = 10 * 1024 * 1024

def get_sd_auth(val: str, sd_auth_pillar_name: str = "serverdensity") -> str:
    if not isinstance(__pillar__, dict):
        raise CommandExecutionError("Global __pillar__ is not a dictionary")
    pillar = __pillar__.get(sd_auth_pillar_name)
    if not isinstance(pillar, dict):
        raise CommandExecutionError(f"Pillar '{sd_auth_pillar_name}' is missing or not a dictionary")
    if val not in pillar:
        raise CommandExecutionError(f"Key '{val}' not found in pillar '{sd_auth_pillar_name}'")
    return str(pillar[val])

def _clean_salt_variables(params: Dict[str, Any], variable_prefix: str = "__") -> Dict[str, Any]:
    return {k: v for k, v in params.items() if not k.startswith(variable_prefix)}

def _auth_headers() -> Dict[str, str]:
    token = get_sd_auth("api_token")
    if not token:
        raise CommandExecutionError("API token is missing or empty")
    return {"Authorization": f"Bearer {token}"}

def _handle_response(response: requests.Response) -> Dict[str, Any]:
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        snippet = response.text[:200]
        log.error(
            "HTTP error %s for %s %s: %s",
            response.status_code,
            response.request.method,
            response.url,
            snippet,
        )
        raise CommandExecutionError(f"HTTP error {response.status_code}: {e}") from e
    try:
        return response.json()
    except ValueError as e:
        log.error("Failed to parse JSON response: %s", e)
        raise CommandExecutionError("Invalid JSON response") from e

def create(name: str, **params) -> Dict[str, Any]:
    payload = _clean_salt_variables(params)
    payload["name"] = name
    url = "https://api.serverdensity.io/inventory/devices/"
    try:
        resp = requests.post(
            url,
            json=payload,
            headers=_auth_headers(),
            timeout=30,
        )
    except requests.RequestException as e:
        log.error("Network error during device creation: %s", e)
        raise CommandExecutionError(f"Network error: {e}") from e
    return _handle_response(resp)

def delete(device_id: str) -> Dict[str, Any]:
    url = f"https://api.serverdensity.io/inventory/devices/{device_id}"
    try:
        resp = requests.delete(
            url,
            headers=_auth_headers(),
            timeout=30,
        )
    except requests.RequestException as e:
        log.error("Network error during device deletion: %s", e)
        raise CommandExecutionError(f"Network error: {e}") from e
    return _handle_response(resp)

def ls(**params) -> Dict[str, Any]:
    cleaned = _clean_salt_variables(params)
    endpoint = "devices" if not cleaned else "resources"
    url = f"https://api.serverdensity.io/inventory/{endpoint}"
    query: Dict[str, str] = {}
    if cleaned:
        filter_dict = {k: str(v) for k, v in cleaned.items()}
        query["filter"] = json.dumps(filter_dict)
    try:
        resp = requests.get(
            url,
            headers=_auth_headers(),
            params=query,
            timeout=30,
        )
    except requests.RequestException as e:
        log.error("Network error during listing: %s", e)
        raise CommandExecutionError(f"Network error: {e}") from e
    return _handle_response(resp)

def update(device_id: str, **params) -> Dict[str, Any]:
    payload = _clean_salt_variables(params)
    url = f"https://api.serverdensity.io/inventory/devices/{device_id}"
    try:
        resp = requests.put(
            url,
            json=payload,
            headers=_auth_headers(),
            timeout=30,
        )
    except requests.RequestException as e:
        log.error("Network error during device update: %s", e)
        raise CommandExecutionError(f"Network error: {e}") from e
    return _handle_response(resp)

def install_agent(agent_key: str) -> str:
    account_url = get_sd_auth("account_url")
    script_url = "https://www.serverdensity.com/downloads/agent-install.sh"
    expected_hash = os.getenv("SD_AGENT_SCRIPT_SHA256")
    if not expected_hash:
        raise CommandExecutionError("Environment variable SD_AGENT_SCRIPT_SHA256 is not set")
    try:
        response = requests.get(script_url, timeout=30, stream=True)
        response.raise_for_status()
    except requests.RequestException as e:
        log.error("Failed to download agent script: %s", e)
        raise CommandExecutionError(f"Failed to download script: {e}") from e
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "install.sh")
        hasher = hashlib.sha256()
        total_bytes = 0
        try:
            with open(script_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    total_bytes += len(chunk)
                    if total_bytes > _MAX_SCRIPT_SIZE:
                        raise CommandExecutionError("Downloaded script exceeds maximum allowed size")
                    f.write(chunk)
                    hasher.update(chunk)
        except OSError as e:
            log.error("Error writing script file: %s", e)
            raise CommandExecutionError(f"File write error: {e}") from e
        actual_hash = hasher.hexdigest()
        if not hashlib.compare_digest(actual_hash, expected_hash):
            log.error("Script hash mismatch: expected %s, got %s", expected_hash, actual_hash)
            raise CommandExecutionError("Downloaded script hash does not match expected value")
        os.chmod(script_path, 0o700)
        env = {"PATH": "/usr/bin:/bin"}
        try:
            result = subprocess.run(
                [script_path, "-a", account_url, "-k", agent_key],
                cwd=tmpdir,
                check=True,
                capture_output=True,
                text=True,
                timeout=300,
                env=env,
                close_fds=True,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
            stdout = getattr(e, "stdout", "")
            stderr = getattr(e, "stderr", "")
            log.error(
                "Agent installation failed: %s\nstdout: %s\nstderr: %s",
                e,
                stdout,
                stderr,
            )
            raise CommandExecutionError(f"Agent installation failed: {e}") from e
        log.debug("Agent install stdout: %s", result.stdout)
        log.debug("Agent install stderr: %s", result.stderr)
        return result.stdout.strip()