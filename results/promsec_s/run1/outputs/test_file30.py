"""Secure wrapper for the Server Density API.

Version added: 2014.7.0
Provides functions to interact with Server Density inventory while handling
sensitive data securely.
"""

import json
import logging
import os
import tempfile
import subprocess

import requests
from salt.exceptions import CommandExecutionError

log = logging.getLogger(__name__)

def get_sd_auth(val, sd_auth_pillar_name='serverdensity'):
    """Retrieve authentication value from Salt pillar."""
    pillar = globals().get('__pillar__', {})
    log.debug("Retrieved pillar '%s': %s", sd_auth_pillar_name, pillar.get(sd_auth_pillar_name, '<missing>'))
    if sd_auth_pillar_name not in pillar:
        raise CommandExecutionError(f"Pillar '{sd_auth_pillar_name}' is missing.")
    auth_dict = pillar[sd_auth_pillar_name]
    if not isinstance(auth_dict, dict) or val not in auth_dict:
        raise CommandExecutionError(f"Key '{val}' not found in pillar '{sd_auth_pillar_name}'.")
    return auth_dict[val]

def _clean_salt_variables(params, variable_prefix="__"):
    """Remove Salt internal variables from a mapping."""
    return {k: v for k, v in params.items() if not k.startswith(variable_prefix)}

def _handle_response(response):
    """Process HTTP response, returning JSON or None."""
    content_len = response.headers.get('Content-Length', len(response.content))
    log.debug("Response status: %s, content length: %s", response.status_code, content_len)
    if response.status_code == 200:
        try:
            return response.json()
        except (ValueError, json.JSONDecodeError) as exc:
            log.error("JSON decode error: %s", exc)
            raise CommandExecutionError(f"Invalid JSON response: {response.text}")
    return None

def create(name, **params):
    """Create a new device."""
    log.debug("Create called for device '%s' with params keys: %s", name, list(params.keys()))
    cleaned = _clean_salt_variables(params)
    cleaned['name'] = name
    token = get_sd_auth('api_token')
    url = "https://api.serverdensity.io/inventory/devices/"
    try:
        response = requests.post(url, params={'token': token}, data=cleaned, timeout=30)
    except requests.RequestException as exc:
        raise CommandExecutionError(f"Network error during create: {exc}")
    return _handle_response(response)

def delete(device_id):
    """Delete a device by ID."""
    token = get_sd_auth('api_token')
    url = f"https://api.serverdensity.io/inventory/devices/{device_id}"
    try:
        response = requests.delete(url, params={'token': token}, timeout=30)
    except requests.RequestException as exc:
        raise CommandExecutionError(f"Network error during delete: {exc}")
    return _handle_response(response)

def ls(**params):
    """List devices or resources."""
    cleaned = _clean_salt_variables(params)
    endpoint = 'devices' if not cleaned else 'resources'
    token = get_sd_auth('api_token')
    url = f"https://api.serverdensity.io/inventory/{endpoint}"
    filter_param = json.dumps({k: str(v) for k, v in cleaned.items()})
    query = {'token': token, 'filter': filter_param}
    try:
        response = requests.get(url, params=query, timeout=30)
    except requests.RequestException as exc:
        raise CommandExecutionError(f"Network error during ls: {exc}")
    return _handle_response(response)

def update(device_id, **params):
    """Update a device."""
    cleaned = _clean_salt_variables(params)
    token = get_sd_auth('api_token')
    url = f"https://api.serverdensity.io/inventory/devices/{device_id}"
    try:
        response = requests.put(url, params={'token': token}, data=cleaned, timeout=30)
    except requests.RequestException as exc:
        raise CommandExecutionError(f"Network error during update: {exc}")
    return _handle_response(response)

def install_agent(agent_key):
    """Download and run the Server Density agent installer."""
    account_url = get_sd_auth('account_url')
    with tempfile.TemporaryDirectory(prefix="sd_agent_") as tmpdir:
        script_path = os.path.join(tmpdir, "install.sh")
        try:
            resp = requests.get("https://www.serverdensity.com/downloads/agent-install.sh", timeout=60)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise CommandExecutionError(f"Failed to download installer: {exc}")
        with open(script_path, "wb") as f:
            f.write(resp.content)
        os.chmod(script_path, 0o755)
        cmd = [script_path, "-a", account_url, "-k", agent_key]
        result = subprocess.run(
            cmd,
            cwd=tmpdir,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise CommandExecutionError(f"Installer failed: {result.stderr.strip()}")
        return result.stdout.strip()