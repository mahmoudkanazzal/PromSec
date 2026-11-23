# -*- coding: utf-8 -*-
"""Server Density API wrapper module
Version: 2014.7.0
"""

import json
import logging
import os
import subprocess
import urllib.parse
import tempfile

import requests
from salt.exceptions import CommandExecutionError

log = logging.getLogger(__name__)

def get_sd_auth(val: str, sd_auth_pillar_name: str = 'serverdensity') -> str:
    """
    Retrieve a value from the Server Density authentication pillar.

    CLI Example::

        salt '*' serverdensity.get_sd_auth api_token

    Args:
        val: The key to retrieve from the pillar.
        sd_auth_pillar_name: Name of the pillar containing Server Density credentials.

    Returns:
        The requested value as a string.

    Raises:
        CommandExecutionError: If the pillar or the requested key is missing.
    """
    log.debug('Retrieving Server Density auth pillar "%s"', sd_auth_pillar_name)
    pillar = globals().get('__pillar__', {})
    auth_data = pillar.get(sd_auth_pillar_name)
    if not auth_data:
        raise CommandExecutionError(f'Pillar "{sd_auth_pillar_name}" not found')
    if val not in auth_data:
        raise CommandExecutionError(f'Key "{val}" not found in pillar "{sd_auth_pillar_name}"')
    return auth_data[val]

def _clean_salt_variables(params: dict, variable_prefix: str = '__') -> dict:
    """
    Return a new dict without keys that start with the given prefix.

    Args:
        params: Original parameters dictionary.
        variable_prefix: Prefix to filter out.

    Returns:
        A cleaned dictionary.
    """
    return {k: v for k, v in params.items() if not k.startswith(variable_prefix)}

def _auth_headers() -> dict:
    """
    Build the Authorization header for Server Density API calls.

    Returns:
        A dictionary with the Authorization header.
    """
    token = get_sd_auth('api_token')
    return {'Authorization': f'Bearer {token}'}

def create(name: str, **params) -> dict:
    """
    Create a new device in Server Density.

    CLI Example::

        salt '*' serverdensity.create my-device hostname=example.com

    Args:
        name: Name of the device to create.
        **params: Additional device attributes.

    Returns:
        Parsed JSON response from the API.

    Raises:
        CommandExecutionError: On request failure or unexpected response.
    """
    payload = _clean_salt_variables(params)
    payload['name'] = name
    url = 'https://api.serverdensity.io/inventory/devices/'
    headers = _auth_headers()
    log.debug('POST %s payload=%s headers=%s', url, payload, headers)
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        log.debug('Response status=%s text=%s', response.status_code, response.text)
        if response.status_code in (200, 201):
            try:
                return response.json()
            except ValueError as exc:
                raise CommandExecutionError(f'Invalid JSON response: {exc}') from exc
        raise CommandExecutionError(f'Error {response.status_code}: {response.text}')
    except requests.RequestException as exc:
        log.error('RequestException during create: %s', exc)
        raise CommandExecutionError(str(exc)) from exc

def delete(device_id: str) -> dict:
    """
    Delete a device from Server Density.

    CLI Example::

        salt '*' serverdensity.delete 12345

    Args:
        device_id: Identifier of the device to delete.

    Returns:
        Parsed JSON response or empty dict if no content.

    Raises:
        CommandExecutionError: On request failure or unexpected response.
    """
    encoded_id = urllib.parse.quote(device_id, safe='')
    url = f'https://api.serverdensity.io/inventory/devices/{encoded_id}'
    headers = _auth_headers()
    log.debug('DELETE %s headers=%s', url, headers)
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        log.debug('Response status=%s text=%s', response.status_code, response.text)
        if response.status_code in (200, 204):
            if response.content:
                try:
                    return response.json()
                except ValueError as exc:
                    raise CommandExecutionError(f'Invalid JSON response: {exc}') from exc
            return {}
        raise CommandExecutionError(f'Error {response.status_code}: {response.text}')
    except requests.RequestException as exc:
        log.error('RequestException during delete: %s', exc)
        raise CommandExecutionError(str(exc)) from exc

def ls(**params) -> dict:
    """
    List devices or resources from Server Density.

    CLI Example::

        salt '*' serverdensity.ls
        salt '*' serverdensity.ls hostname=example.com

    Args:
        **params: Filter parameters.

    Returns:
        Parsed JSON response from the API.

    Raises:
        CommandExecutionError: On request failure or unexpected response.
    """
    cleaned = _clean_salt_variables(params)
    endpoint = 'devices' if not cleaned else 'resources'
    filter_dict = {k: str(v) for k, v in cleaned.items()}
    query = {'filter': json.dumps(filter_dict)} if filter_dict else {}
    url = f'https://api.serverdensity.io/inventory/{endpoint}'
    headers = _auth_headers()
    log.debug('GET %s params=%s headers=%s', url, query, headers)
    try:
        response = requests.get(url, headers=headers, params=query, timeout=30)
        log.debug('Response status=%s text=%s', response.status_code, response.text)
        if response.status_code == 200:
            try:
                return response.json()
            except ValueError as exc:
                raise CommandExecutionError(f'Invalid JSON response: {exc}') from exc
        raise CommandExecutionError(f'Error {response.status_code}: {response.text}')
    except requests.RequestException as exc:
        log.error('RequestException during ls: %s', exc)
        raise CommandExecutionError(str(exc)) from exc

def update(device_id: str, **params) -> dict:
    """
    Update an existing device in Server Density.

    CLI Example::

        salt '*' serverdensity.update 12345 hostname=new.example.com

    Args:
        device_id: Identifier of the device to update.
        **params: Fields to update.

    Returns:
        Parsed JSON response from the API.

    Raises:
        CommandExecutionError: On request failure or unexpected response.
    """
    payload = _clean_salt_variables(params)
    encoded_id = urllib.parse.quote(device_id, safe='')
    url = f'https://api.serverdensity.io/inventory/devices/{encoded_id}'
    headers = _auth_headers()
    log.debug('PUT %s payload=%s headers=%s', url, payload, headers)
    try:
        response = requests.put(url, json=payload, headers=headers, timeout=30)
        log.debug('Response status=%s text=%s', response.status_code, response.text)
        if response.status_code == 200:
            try:
                return response.json()
            except ValueError as exc:
                raise CommandExecutionError(f'Invalid JSON response: {exc}') from exc
        raise CommandExecutionError(f'Error {response.status_code}: {response.text}')
    except requests.RequestException as exc:
        log.error('RequestException during update: %s', exc)
        raise CommandExecutionError(str(exc)) from exc

def install_agent(agent_key: str) -> str:
    """
    Download and install the Server Density agent.

    CLI Example::

        salt '*' serverdensity.install_agent <agent_key>

    Args:
        agent_key: The agent key to register the installation.

    Returns:
        Standard output from the installer script.

    Raises:
        CommandExecutionError: On download, write, or execution failure.
    """
    account_url = get_sd_auth('account_url')
    if not isinstance(account_url, str) or not account_url.startswith('https://'):
        raise CommandExecutionError('Invalid account_url retrieved from pillar')
    installer_url = 'https://www.serverdensity.com/downloads/agent-install.sh'
    log.debug('Downloading installer from %s', installer_url)
    try:
        resp = requests.get(installer_url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        log.error('Failed to download installer: %s', exc)
        raise CommandExecutionError(f'Failed to download installer: {exc}') from exc
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, 'install.sh')
        try:
            with open(script_path, 'wb') as script_file:
                script_file.write(resp.content)
            os.chmod(script_path, 0o700)
        except OSError as exc:
            log.error('Failed to write installer script: %s', exc)
            raise CommandExecutionError(f'Failed to write installer script: {exc}') from exc
        cmd = [script_path, '-a', account_url, '-k', agent_key]
        log.debug('Executing installer script: %s', cmd)
        try:
            result = subprocess.run(
                cmd,
                cwd=tmpdir,
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout
        except subprocess.CalledProcessError as exc:
            log.error('Installer script failed: %s', exc)
            raise CommandExecutionError(f'Installer script failed: {exc.stderr}') from exc
           

# End of module.